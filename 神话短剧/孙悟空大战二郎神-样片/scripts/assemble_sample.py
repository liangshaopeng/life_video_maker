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


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def motion_params(shot: dict, frames: int) -> dict:
    motion = shot["motion"]
    frame_count = max(1, int(frames))
    pan_end_x = clamp01(float(motion.get("pan_end_x", motion["pan_x"])))
    pan_end_y = clamp01(float(motion.get("pan_end_y", motion["pan_y"])))
    pan_start_x = clamp01(float(motion.get("pan_start_x", pan_end_x)))
    pan_start_y = clamp01(float(motion.get("pan_start_y", pan_end_y)))
    impact_at = clamp01(float(motion.get("impact_at", 0.50)))

    return {
        "zoom_start": float(motion["zoom_start"]),
        "zoom_end": float(motion["zoom_end"]),
        "pan_start_x": pan_start_x,
        "pan_start_y": pan_start_y,
        "pan_end_x": pan_end_x,
        "pan_end_y": pan_end_y,
        "shake": max(0.0, float(motion.get("shake", 0.0))),
        "impact_frame": round(impact_at * frame_count, 3),
    }


def zoompan_filter(shot: dict, frames: int) -> str:
    frame_count = max(1, int(frames))
    params = motion_params(shot, frame_count)
    zoom_start = params["zoom_start"]
    zoom_end = params["zoom_end"]
    zoom_delta = (zoom_end - zoom_start) / frame_count
    progress = f"min(1,on/{max(1, frame_count - 1)})"
    pan_x = (
        f"({params['pan_start_x']:.5f}+"
        f"({params['pan_end_x']:.5f}-{params['pan_start_x']:.5f})*{progress})"
    )
    pan_y = (
        f"({params['pan_start_y']:.5f}+"
        f"({params['pan_end_y']:.5f}-{params['pan_start_y']:.5f})*{progress})"
    )
    impact = int(round(params["impact_frame"]))
    window = max(2, int(round(frame_count * 0.10)))
    impact_start = max(0, impact - window)
    impact_end = min(frame_count, impact + window)
    shake_x = params["shake"] * W
    shake_y = params["shake"] * H * 0.45
    shake_gate = f"between(on,{impact_start},{impact_end})"
    x_expr = (
        f"min(max(0,(iw-iw/zoom)*{pan_x}+"
        f"{shake_x:.5f}*sin(on*2.70000)*{shake_gate}),iw-iw/zoom)"
    )
    y_expr = (
        f"min(max(0,(ih-ih/zoom)*{pan_y}+"
        f"{shake_y:.5f}*cos(on*3.10000)*{shake_gate}),ih-ih/zoom)"
    )

    return (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,"
        f"zoompan=z='min({zoom_end:.5f},{zoom_start:.5f}+on*{zoom_delta:.8f})':"
        f"x='{x_expr}':y='{y_expr}':d={frame_count}:s={W}x{H}:fps={FPS}[base];"
    )


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

    vf = (
        zoompan_filter(shot, frames) +
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
