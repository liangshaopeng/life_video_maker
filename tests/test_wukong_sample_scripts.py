import importlib.util
import json
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "神话短剧" / "孙悟空大战二郎神-样片"
PROJECT_JSON = PROJECT_DIR / "project.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_assets_reports_missing_keyframes_before_generation(tmp_path):
    module = load_module(PROJECT_DIR / "scripts" / "check_assets.py", "wukong_check_assets")
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    project["shots"][0]["keyframe"] = "assets/keyframes/definitely_missing.png"
    broken = tmp_path / "project.json"
    broken.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
    errors = module.check_keyframes(broken)
    assert any("missing keyframe" in err for err in errors)


def test_generated_keyframes_are_ready():
    module = load_module(PROJECT_DIR / "scripts" / "check_assets.py", "wukong_check_assets")
    errors = module.check_keyframes(PROJECT_JSON)
    assert errors == []


def test_keyframes_are_portrait_images():
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    for shot in project["shots"]:
        img_path = PROJECT_DIR / shot["keyframe"]
        with Image.open(img_path) as img:
            width, height = img.size
        assert height > width
        assert width >= 1080
        assert height >= 1920


def test_check_keyframes_rejects_small_keyframe(tmp_path):
    module = load_module(PROJECT_DIR / "scripts" / "check_assets.py", "wukong_check_assets_small")
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    shot_id = project["shots"][0]["id"]
    small_keyframe = tmp_path / "small.png"
    Image.new("RGB", (1080, 1440), "white").save(small_keyframe, format="PNG")
    project["shots"][0]["keyframe"] = str(small_keyframe.relative_to(tmp_path))
    tmp_project = tmp_path / "project.json"
    tmp_project.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
    errors = module.check_keyframes(tmp_project)
    assert any(
        shot_id in err and "keyframe too small" in err and "1080x1440" in err
        for err in errors
    )


def test_check_keyframes_rejects_non_png_with_png_suffix(tmp_path):
    module = load_module(PROJECT_DIR / "scripts" / "check_assets.py", "wukong_check_assets_non_png")
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    shot_id = project["shots"][0]["id"]
    jpg_as_png = tmp_path / "fake.png"
    Image.new("RGB", (1080, 1920), "white").save(jpg_as_png, format="JPEG")
    project["shots"][0]["keyframe"] = str(jpg_as_png.relative_to(tmp_path))
    tmp_project = tmp_path / "project.json"
    tmp_project.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
    errors = module.check_keyframes(tmp_project)
    assert any(
        shot_id in err and "not PNG" in err
        for err in errors
    )


def ffprobe_duration(path: Path) -> float:
    return float(
        subprocess.check_output([
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ]).decode().strip()
    )


def test_generated_subtitles_respect_caption_width():
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    maxlen = int(project["caption_maxlen"])
    for srt in sorted((PROJECT_DIR / "build" / "subs").glob("*.srt")):
        for line in srt.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text or text.isdigit() or "-->" in text:
                continue
            assert len(text) <= maxlen, f"{srt.name}: {text!r}"


def test_narration_outputs_exist_after_generation():
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    for index, shot in enumerate(project["shots"], 1):
        audio = PROJECT_DIR / "build" / "audio" / f"seg{index}.mp3"
        srt = PROJECT_DIR / "build" / "subs" / f"seg{index}.srt"
        assert audio.exists(), f"missing audio for {shot['id']}"
        assert srt.exists(), f"missing srt for {shot['id']}"
        assert ffprobe_duration(audio) > 0.5
    assert (PROJECT_DIR / "build" / "subs" / "global.srt").exists()
    assert (PROJECT_DIR / "build" / "timeline.json").exists()


def test_timeline_uses_shot_durations_and_keeps_audio_within_clip():
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    timeline = json.loads((PROJECT_DIR / "build" / "timeline.json").read_text(encoding="utf-8"))

    shot_durations = [float(shot["duration"]) for shot in project["shots"]]
    assert 28.0 <= float(timeline["total"]) <= 32.0
    assert len(timeline["segs"]) == len(shot_durations)

    for index, (seg, expected_clip) in enumerate(zip(timeline["segs"], shot_durations), 1):
        audio = PROJECT_DIR / "build" / "audio" / f"seg{index}.mp3"
        audio_duration = ffprobe_duration(audio)
        assert abs(float(seg["clip"]) - expected_clip) < 0.01
        assert float(seg["end"]) - float(seg["start"]) == float(seg["clip"])
        assert audio_duration <= float(seg["clip"]) + 0.02


def test_bgm_exists_and_is_long_enough():
    bgm = PROJECT_DIR / "assets" / "bgm" / "dark_myth_bgm.wav"
    assert bgm.exists()
    assert ffprobe_duration(bgm) >= 31.0


def test_overlay_frames_exist_after_render():
    project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    timeline = json.loads((PROJECT_DIR / "build" / "timeline.json").read_text(encoding="utf-8"))
    for item in timeline["segs"]:
        seg_dir = PROJECT_DIR / "build" / "overlays" / f"seg{item['seg']}"
        first = seg_dir / "0001.png"
        last_index = max(1, int(round(item["clip"] * project["canvas"]["fps"])))
        last = seg_dir / f"{last_index:04d}.png"
        assert first.exists()
        assert last.exists()
        with Image.open(first) as img:
            assert img.size == (1080, 1920)
            assert img.mode == "RGBA"
