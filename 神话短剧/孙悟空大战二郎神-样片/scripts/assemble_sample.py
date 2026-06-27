# -*- coding: utf-8 -*-
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("project.json")
ROOT = PROJECT.resolve().parent
cfg = json.loads(PROJECT.read_text(encoding="utf-8"))
BUILD = ROOT / cfg.get("build_dir", "build")
timeline = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
W = cfg["canvas"]["width"]
H = cfg["canvas"]["height"]
FPS = cfg["canvas"]["fps"]
CLIPS = BUILD / "clips"
CLIPS.mkdir(parents=True, exist_ok=True)


def run(cmd):
    print(" ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def build_clip(shot: dict, item: dict) -> Path:
    index = item["seg"]
    duration = float(item["clip"])
    frames = max(1, int(round(duration * FPS)))
    keyframe = ROOT / shot["keyframe"]
    overlay_pattern = BUILD / "overlays" / f"seg{index}" / "%04d.png"
    audio = BUILD / "audio" / f"seg{index}.mp3"
    out = CLIPS / f"clip{index:02d}.mp4"
    zoom_start = float(shot["motion"]["zoom_start"])
    zoom_end = float(shot["motion"]["zoom_end"])
    zoom_delta = (zoom_end - zoom_start) / frames

    vf = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,"
        f"zoompan=z='min({zoom_end:.5f},{zoom_start:.5f}+on*{zoom_delta:.8f})':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}[base];"
        f"[base][1:v]overlay=0:0:shortest=1[v];"
        f"[2:a]apad,atrim=duration={duration:.3f},afade=t=out:st={max(0.0, duration - 0.18):.3f}:d=0.18[a]"
    )

    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-t", f"{duration:.3f}", "-i", keyframe,
        "-framerate", str(FPS), "-i", overlay_pattern,
        "-i", audio,
        "-filter_complex", vf,
        "-map", "[v]", "-map", "[a]",
        "-r", str(FPS), "-c:v", "libx264", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{duration:.3f}", out
    ])
    return out


def concat(clips):
    concat_file = BUILD / "concat.txt"
    concat_file.write_text("".join(f"file '{clip}'\n" for clip in clips), encoding="utf-8")
    out = ROOT / cfg["final_no_bgm"]
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", out
    ])
    return out


def qa_thumbnails(video: Path):
    qa = BUILD / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    for second in [3, 11, 20, 29]:
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(second), "-i", video, "-frames:v", "1",
            "-q:v", "2", qa / f"qa_{second:04d}.jpg"
        ])


def main() -> int:
    clips = [build_clip(shot, item) for shot, item in zip(cfg["shots"], timeline["segs"])]
    final = concat(clips)
    qa_thumbnails(final)
    print(f"vertical={final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
