# -*- coding: utf-8 -*-
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("project.json")
ROOT = PROJECT.resolve().parent
cfg = json.loads(PROJECT.read_text(encoding="utf-8"))
timeline = json.loads((ROOT / cfg.get("build_dir", "build") / "timeline.json").read_text(encoding="utf-8"))

W = cfg["canvas"]["width"]
H = cfg["canvas"]["height"]
FPS = cfg["canvas"]["fps"]
FONT_PATH = cfg.get("font", "/System/Library/Fonts/Hiragino Sans GB.ttc")
BUILD = ROOT / cfg.get("build_dir", "build")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def parse_srt(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise ValueError(f"empty SRT file: {path}")

    blocks = re.split(r"\n\s*\n", raw.strip())
    cues = []
    for block in blocks:
        lines = [line.rstrip("\r") for line in block.splitlines()]
        if len(lines) < 3:
            raise ValueError(f"malformed SRT block in {path}: {block!r}")
        if not lines[0].strip().isdigit():
            raise ValueError(f"malformed SRT cue index in {path}: {lines[0]!r}")
        m = re.fullmatch(
            r"\s*(\d+):(\d+):(\d+),(\d+)\s+-->\s+(\d+):(\d+):(\d+),(\d+)\s*",
            lines[1],
        )
        if not m:
            raise ValueError(f"malformed SRT timestamp in {path}: {lines[1]!r}")
        g = list(map(int, m.groups()))
        st = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        en = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        text_lines = [line.strip() for line in lines[2:] if line.strip()]
        if not text_lines:
            raise ValueError(f"empty SRT cue text in {path}: {block!r}")
        cues.append((st, en, "\n".join(text_lines)))
    if not cues:
        raise ValueError(f"no cues found in SRT file: {path}")
    return cues


def draw_centered(
    draw: ImageDraw.ImageDraw,
    xy,
    text: str,
    fnt,
    fill,
    stroke_fill=(0, 0, 0, 220),
    stroke_width=4,
):
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=8, stroke_width=stroke_width)
    tw = bbox[2] - bbox[0]
    x, y = xy
    draw.multiline_text(
        (x - tw / 2, y),
        text,
        font=fnt,
        fill=fill,
        spacing=8,
        align="center",
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def cue_at(cues, t: float) -> str:
    for st, en, text in cues:
        if st <= t <= en:
            return text
    return ""


def pulse(t: float, center: float, width: float) -> float:
    if width <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(t - center) / width)


def draw_flash(draw: ImageDraw.ImageDraw, t: float, center: float, color, width: float = 0.18):
    strength = pulse(t, center, width)
    if strength <= 0:
        return
    r, g, b = color
    alpha = int(145 * strength)
    draw.rectangle((0, 0, W, H), fill=(r, g, b, alpha))


def draw_vignette(draw: ImageDraw.ImageDraw, strength: int = 70):
    for i in range(9):
        alpha = max(0, strength - i * 8)
        inset_x = i * 28
        inset_y = i * 46
        draw.rectangle(
            (inset_x, inset_y, W - inset_x, H - inset_y),
            outline=(0, 0, 0, alpha),
            width=18,
        )


def draw_shockwave(draw: ImageDraw.ImageDraw, t: float, center: float, origin, color):
    progress = (t - center) / 0.95
    if not 0.0 <= progress <= 1.0:
        return
    cx, cy = origin
    r, g, b = color
    radius = 120 + progress * 760
    alpha = int((1.0 - progress) * 190)
    for ring in range(3):
        pad = ring * 46
        draw.ellipse(
            (cx - radius - pad, cy - radius * 0.55 - pad, cx + radius + pad, cy + radius * 0.55 + pad),
            outline=(r, g, b, max(0, alpha - ring * 40)),
            width=max(2, 8 - ring * 2),
        )


def draw_particles(draw: ImageDraw.ImageDraw, t: float, duration: float, origin, color, count: int, speed: float):
    progress = min(1.0, max(0.0, t / max(0.001, duration)))
    cx, cy = origin
    r, g, b = color
    for i in range(count):
        seed = i * 12.9898
        angle = -2.75 + (i % 23) * 0.245 + math.sin(seed) * 0.22
        drift = (progress * speed + (math.sin(seed * 1.7) + 1) * 0.5) % 1.0
        dist = 80 + drift * 980 + (i % 7) * 18
        x = cx + math.cos(angle) * dist + math.sin(t * 2.1 + seed) * 24
        y = cy + math.sin(angle) * dist * 0.52 + math.cos(t * 1.8 + seed) * 18
        length = 18 + (i % 5) * 9
        alpha = int((1.0 - drift * 0.72) * 150)
        if alpha <= 0:
            continue
        x2 = x - math.cos(angle) * length
        y2 = y - math.sin(angle) * length * 0.52
        draw.line((x, y, x2, y2), fill=(r, g, b, alpha), width=2 + (i % 3 == 0))
        if i % 4 == 0:
            size = 2 + i % 3
            draw.ellipse((x - size, y - size, x + size, y + size), fill=(255, 242, 196, alpha))


def draw_scan_beam(draw: ImageDraw.ImageDraw, t: float, duration: float):
    progress = min(1.0, max(0.0, t / max(0.001, duration)))
    y = int(H * (0.25 + 0.38 * progress))
    alpha = int(110 + 70 * math.sin(progress * math.pi))
    draw.polygon(
        [(0, y - 82), (W, y - 12), (W, y + 42), (0, y + 98)],
        fill=(82, 178, 255, max(0, alpha // 3)),
    )
    draw.line((0, y, W, y + 64), fill=(174, 228, 255, alpha), width=7)
    draw.line((0, y + 34, W, y + 94), fill=(36, 120, 255, max(0, alpha - 35)), width=3)


def draw_speed_lines(draw: ImageDraw.ImageDraw, t: float, duration: float, color, reverse: bool = False):
    progress = min(1.0, max(0.0, t / max(0.001, duration)))
    r, g, b = color
    for i in range(26):
        phase = (progress * 1.9 + i * 0.061) % 1.0
        y = int(260 + phase * 1180 + math.sin(i * 1.3) * 80)
        length = 150 + (i % 6) * 42
        alpha = int((1.0 - phase * 0.45) * 92)
        if reverse:
            x1 = W - 40 - (i % 9) * 54
            x2 = x1 - length
        else:
            x1 = 40 + (i % 9) * 54
            x2 = x1 + length
        draw.line((x1, y, x2, y - 90), fill=(r, g, b, alpha), width=3)


def draw_clone_shards(draw: ImageDraw.ImageDraw, t: float, duration: float):
    progress = min(1.0, max(0.0, t / max(0.001, duration)))
    for i in range(18):
        seed = i * 9.37
        x = W * (0.18 + (i % 6) * 0.13) + math.sin(seed + t * 2.5) * 42
        y = H * (0.22 + (i // 6) * 0.18) + progress * 360 + math.cos(seed) * 54
        alpha = int(95 + 70 * pulse(progress, 0.48 + (i % 5) * 0.04, 0.28))
        draw.polygon(
            [(x, y), (x + 34 + i % 5 * 8, y + 16), (x + 8, y + 70 + i % 4 * 11)],
            outline=(116, 198, 255, alpha),
            fill=(120, 160, 255, max(18, alpha // 5)),
        )
        draw.line((x - 18, y + 8, x + 72, y + 44), fill=(230, 245, 255, alpha), width=2)


def draw_cinematic_effects(draw: ImageDraw.ImageDraw, shot: dict, t: float, duration: float) -> None:
    shot_id = shot.get("id", "")
    if shot_id != "shot06_afterimage_hook":
        draw_vignette(draw)

    if shot_id == "shot02_heavenly_eye":
        draw_scan_beam(draw, t, duration)
        draw_flash(draw, t, 1.10, (110, 205, 255), width=0.24)
        draw_particles(draw, t, duration, (W * 0.50, H * 0.36), (96, 184, 255), 34, 1.35)
    elif shot_id == "shot03_weapon_clash":
        draw_flash(draw, t, 0.22, (255, 238, 190), width=0.20)
        draw_shockwave(draw, t, 0.32, (W * 0.52, H * 0.48), (130, 210, 255))
        draw_particles(draw, t, duration, (W * 0.54, H * 0.48), (255, 182, 72), 58, 2.45)
    elif shot_id == "shot04_clone_break":
        draw_flash(draw, t, 2.20, (120, 184, 255), width=0.18)
        draw_clone_shards(draw, t, duration)
        draw_particles(draw, t, duration, (W * 0.46, H * 0.44), (100, 170, 255), 36, 1.70)
    elif shot_id == "shot05_final_staff":
        draw_flash(draw, t, 3.35, (255, 214, 116), width=0.22)
        draw_shockwave(draw, t, 3.50, (W * 0.50, H * 0.42), (255, 202, 88))
        draw_speed_lines(draw, t, duration, (255, 218, 132), reverse=True)
        draw_particles(draw, t, duration, (W * 0.48, H * 0.43), (255, 196, 88), 42, 2.10)
    elif shot_id == "shot06_afterimage_hook":
        draw_flash(draw, t, 0.25, (112, 170, 255), width=0.15)
    else:
        draw_speed_lines(draw, t, duration, (255, 214, 116), reverse=False)
        draw_particles(draw, t, duration, (W * 0.52, H * 0.50), (236, 192, 94), 28, 1.25)


def render_segment(shot: dict, item: dict):
    out_dir = BUILD / "overlays" / f"seg{item['seg']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cues = parse_srt(BUILD / "subs" / f"seg{item['seg']}.srt")
    frames = max(1, int(round(float(item["clip"]) * FPS)))
    title_font = font(72)
    caption_font = font(60)
    small_font = font(32)
    for n in range(1, frames + 1):
        t = (n - 1) / FPS
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)

        draw_cinematic_effects(draw, shot, t, float(item["clip"]))

        draw.rectangle((0, 0, W, 150), fill=(0, 0, 0, 88))
        draw.text((44, 44), "孙悟空大战二郎神", font=small_font, fill=(230, 222, 204, 235))
        draw.text((W - 210, 44), "AI 样片", font=small_font, fill=(130, 190, 255, 225))

        if t < 1.25:
            draw_centered(
                draw,
                (W / 2, 214),
                shot["caption"],
                title_font,
                fill=(255, 214, 116, 255),
                stroke_width=5,
            )

        current = cue_at(cues, t)
        if current:
            draw.rounded_rectangle(
                (80, 1544, W - 80, 1716),
                radius=18,
                fill=(0, 0, 0, 150),
                outline=(255, 214, 116, 90),
                width=2,
            )
            draw_centered(
                draw,
                (W / 2, 1584),
                current,
                caption_font,
                fill=(255, 255, 244, 255),
                stroke_width=5,
            )

        im.save(out_dir / f"{n:04d}.png")


def main() -> int:
    overlay_root = BUILD / "overlays"
    if overlay_root.exists():
        for path in sorted(overlay_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    overlay_root.mkdir(parents=True, exist_ok=True)

    for shot, item in zip(cfg["shots"], timeline["segs"]):
        render_segment(shot, item)
        print(f"rendered overlay seg{item['seg']} {shot['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
