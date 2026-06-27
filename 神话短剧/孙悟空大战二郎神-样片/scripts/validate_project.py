# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

PROJECT_FIELDS_PATHS = ("bgm", "final_no_bgm", "final_mixed")
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
MOTION_KEYS = ("zoom_start", "zoom_end", "pan_x", "pan_y")


def _path_in_project(root: Path, rel_path: object) -> bool:
    if not isinstance(rel_path, str):
        return False

    path = Path(rel_path)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    candidate = (root / path).resolve()
    project_root = root.resolve()
    try:
        candidate.relative_to(project_root)
        return True
    except ValueError:
        return False


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_project(path: Path) -> dict:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def caption_visible_len(text: str) -> int:
    return max((len(part.strip()) for part in text.split("\\n")), default=0)


def validate_project(project: dict, root: Path) -> list[str]:
    errors = []
    if project.get("canvas") != {"width": 1080, "height": 1920, "fps": 30}:
        errors.append("canvas must be exactly 1080x1920 at 30fps")

    caption_maxlen = project.get("caption_maxlen", 14)
    if not isinstance(caption_maxlen, int) or isinstance(caption_maxlen, bool) or caption_maxlen < 1:
        errors.append("caption_maxlen must be a positive integer")
        caption_maxlen = 14
    elif caption_maxlen > 14:
        errors.append("caption_maxlen must not exceed 14")

    effective_caption_maxlen = min(caption_maxlen, 14)
    shots = project.get("shots")
    if not isinstance(shots, list) or len(shots) != 6:
        errors.append("project must contain exactly 6 shots")
        return errors

    project_root = root.resolve()
    for project_path_key in PROJECT_FIELDS_PATHS:
        value = project.get(project_path_key)
        if value is not None and not _path_in_project(project_root, value):
            errors.append(f"{project_path_key} must be inside project root: {value}")

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
        if caption_visible_len(shot["caption"]) > effective_caption_maxlen:
            errors.append(f"{shot_id} caption exceeds {effective_caption_maxlen} Chinese characters on one line")
        for rel_key in ("prompt", "keyframe"):
            path_value = shot[rel_key]
            if not _path_in_project(project_root, path_value):
                errors.append(f"{shot_id} {rel_key} must be inside project root: {path_value}")
        motion = shot["motion"]
        if not isinstance(motion, dict):
            errors.append(f"{shot_id} motion must be a dict")
            continue
        for motion_key in MOTION_KEYS:
            if motion_key not in motion:
                errors.append(f"{shot_id} motion missing key: {motion_key}")
        if any(key not in motion for key in MOTION_KEYS):
            continue
        for motion_key in ("zoom_start", "zoom_end", "pan_x", "pan_y"):
            if not _is_number(motion[motion_key]):
                errors.append(f"{shot_id} {motion_key} must be numeric")
        if not _is_number(motion["zoom_start"]) or not _is_number(motion["zoom_end"]):
            continue
        if motion["zoom_start"] < 1.0:
            errors.append(f"{shot_id} zoom_start must be >= 1.0")
        if motion["zoom_end"] < motion["zoom_start"]:
            errors.append(f"{shot_id} zoom_end must be >= zoom_start")
        if not _is_number(motion["pan_x"]) or not 0.0 <= motion["pan_x"] <= 1.0:
            errors.append(f"{shot_id} pan_x must be between 0.0 and 1.0")
        if not _is_number(motion["pan_y"]) or not 0.0 <= motion["pan_y"] <= 1.0:
            errors.append(f"{shot_id} pan_y must be between 0.0 and 1.0")

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
