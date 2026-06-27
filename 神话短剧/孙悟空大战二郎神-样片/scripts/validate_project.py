# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

REQUIRED_SHOT_KEYS = {
    "id",
    "duration",
    "beat",
    "narration",
    "caption",
    "prompt",
    "keyframe",
    "motion",
}


def load_project(path: Path) -> dict:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def caption_visible_len(text: str) -> int:
    return max((len(part.strip()) for part in text.split("\\n")), default=0)


def validate_project(project: dict, root: Path) -> list[str]:
    errors = []
    if project.get("canvas") != {"width": 1080, "height": 1920, "fps": 30}:
        errors.append("canvas must be exactly 1080x1920 at 30fps")

    shots = project.get("shots")
    if not isinstance(shots, list) or len(shots) != 6:
        errors.append("project must contain exactly 6 shots")
        return errors

    total = 0.0
    seen_ids = set()
    for index, shot in enumerate(shots, 1):
        missing = REQUIRED_SHOT_KEYS - set(shot)
        if missing:
            errors.append(f"shot {index} missing keys: {sorted(missing)}")
            continue
        shot_id = shot["id"]
        if shot_id in seen_ids:
            errors.append(f"duplicate shot id: {shot_id}")
        seen_ids.add(shot_id)
        duration = float(shot["duration"])
        total += duration
        if duration < 2.0 or duration > 7.5:
            errors.append(f"{shot_id} duration outside 2.0-7.5 seconds")
        if caption_visible_len(shot["caption"]) > 14:
            errors.append(f"{shot_id} caption exceeds 14 Chinese characters on one line")
        for rel_key in ("prompt", "keyframe"):
            rel = Path(shot[rel_key])
            if rel.is_absolute():
                errors.append(f"{shot_id} {rel_key} must be relative: {rel}")
            if ".." in rel.parts:
                errors.append(f"{shot_id} {rel_key} must not contain parent traversal: {rel}")
        motion = shot["motion"]
        if motion.get("zoom_start", 1.0) < 1.0:
            errors.append(f"{shot_id} zoom_start must be >= 1.0")
        if motion.get("zoom_end", 1.0) < motion.get("zoom_start", 1.0):
            errors.append(f"{shot_id} zoom_end must be >= zoom_start")

    if not (28.0 <= total <= 32.0):
        errors.append(f"total duration {total:.2f}s outside 28-32 seconds")

    return errors


def main() -> int:
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("project.json")
    root = project_path.resolve().parent
    errors = validate_project(load_project(project_path), root)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print(f"OK: {project_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
