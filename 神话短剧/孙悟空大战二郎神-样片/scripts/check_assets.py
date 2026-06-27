# -*- coding: utf-8 -*-
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


def _project_root(project_path: Path) -> Path:
    return Path(project_path).resolve().parent


def _load(project_path: Path) -> dict:
    with Path(project_path).open(encoding="utf-8") as f:
        return json.load(f)


def check_keyframes(project_path: Path) -> list[str]:
    project = _load(project_path)
    root = _project_root(project_path)
    errors = []
    for shot in project["shots"]:
        img_path = root / shot["keyframe"]
        if not img_path.exists():
            errors.append(f"{shot['id']}: missing keyframe {img_path}")
            continue
        try:
            with Image.open(img_path) as img:
                if img.format != "PNG":
                    errors.append(f"{shot['id']}: keyframe is not PNG, got {img.format}")
                    continue
                width, height = img.size
        except Exception as exc:
            errors.append(f"{shot['id']}: unreadable image {img_path}: {exc}")
            continue
        if width < 1080 or height < 1920:
            errors.append(f"{shot['id']}: keyframe too small {width}x{height}")
        if height <= width:
            errors.append(f"{shot['id']}: keyframe must be portrait, got {width}x{height}")
    return errors


def check_bgm(project_path: Path) -> list[str]:
    project = _load(project_path)
    root = _project_root(project_path)
    bgm_path = root / project["bgm"]
    if not bgm_path.exists():
        return [f"missing bgm {bgm_path}"]
    try:
        duration = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1", str(bgm_path)
        ]).decode().strip())
    except Exception as exc:
        return [f"unreadable bgm {bgm_path}: {exc}"]
    if duration < 31.0:
        return [f"bgm duration {duration:.2f}s shorter than 31s"]
    return []


def main() -> int:
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("project.json")
    errors = check_keyframes(project_path) + check_bgm(project_path)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print("OK: assets ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
