# -*- coding: utf-8 -*-
import json
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
        return []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    cues = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        m = re.search(
            r"(\d+):(\d+):(\d+),(\d+)\s+-->\s+(\d+):(\d+):(\d+),(\d+)",
            block,
        )
        if not m:
            continue
        g = list(map(int, m.groups()))
        st = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        en = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append((st, en, lines[-1]))
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


def render_segment(shot: dict, item: dict):
    out_dir = BUILD / "overlays" / f"seg{item['seg']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cues = parse_srt(BUILD / "subs" / f"seg{item['seg']}.srt")
    frames = max(1, int(round(float(item["clip"]) * FPS)))
    title_font = font(72)
    caption_font = font(60)
    small_font = font(32)
    hook_font = font(86)

    for n in range(1, frames + 1):
        t = (n - 1) / FPS
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)

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

        if shot["id"] == "shot06_afterimage_hook":
            draw_centered(
                draw,
                (W / 2, 1336),
                "未完待续",
                hook_font,
                fill=(255, 214, 116, 255),
                stroke_width=6,
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
