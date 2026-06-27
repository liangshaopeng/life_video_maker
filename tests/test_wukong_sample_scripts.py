import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "神话短剧" / "孙悟空大战二郎神-样片"
PROJECT_JSON = PROJECT_DIR / "project.json"


def load_module(path: Path, name: str, argv=None):
    old_argv = sys.argv[:]
    if argv is not None:
        sys.argv = argv
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.argv = old_argv
    return module


def test_parse_srt_missing_file_raises(tmp_path):
    module = load_module(
        PROJECT_DIR / "scripts" / "render_overlays.py",
        "wukong_render_overlays",
        argv=["render_overlays.py", str(PROJECT_JSON)],
    )
    missing = tmp_path / "missing.srt"
    with pytest.raises((FileNotFoundError, ValueError)):
        module.parse_srt(missing)


def test_parse_srt_preserves_multiline_cue_text(tmp_path):
    module = load_module(
        PROJECT_DIR / "scripts" / "render_overlays.py",
        "wukong_render_overlays_multiline",
        argv=["render_overlays.py", str(PROJECT_JSON)],
    )
    srt = tmp_path / "multiline.srt"
    srt.write_text(
        "\n".join(
            [
                "1",
                "00:00:00,000 --> 00:00:02,000",
                "第一行",
                "第二行",
                "",
            ]
        ),
        encoding="utf-8",
    )
    cues = module.parse_srt(srt)
    assert len(cues) == 1
    assert cues[0][2] == "第一行\n第二行"


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


def test_motion_params_supports_directional_pan_and_shake():
    module = load_module(
        PROJECT_DIR / "scripts" / "assemble_sample.py",
        "wukong_assemble_motion_params",
        argv=["assemble_sample.py", str(PROJECT_JSON)],
    )
    shot = {
        "motion": {
            "zoom_start": 1.03,
            "zoom_end": 1.21,
            "pan_x": 0.62,
            "pan_y": 0.44,
            "pan_start_x": 0.41,
            "pan_start_y": 0.58,
            "shake": 0.018,
            "impact_at": 0.35,
        }
    }

    params = module.motion_params(shot, frames=120)

    assert params["zoom_start"] == 1.03
    assert params["zoom_end"] == 1.21
    assert params["pan_start_x"] == 0.41
    assert params["pan_start_y"] == 0.58
    assert params["pan_end_x"] == 0.62
    assert params["pan_end_y"] == 0.44
    assert params["shake"] == 0.018
    assert params["impact_frame"] == 42.0


def test_zoompan_filter_uses_directional_pan_expression():
    module = load_module(
        PROJECT_DIR / "scripts" / "assemble_sample.py",
        "wukong_assemble_zoompan_filter",
        argv=["assemble_sample.py", str(PROJECT_JSON)],
    )
    shot = {
        "motion": {
            "zoom_start": 1.0,
            "zoom_end": 1.18,
            "pan_x": 0.60,
            "pan_y": 0.42,
            "pan_start_x": 0.38,
            "pan_start_y": 0.55,
            "shake": 0.012,
            "impact_at": 0.50,
        }
    }

    vf = module.zoompan_filter(shot, frames=150)

    assert "(0.38000+(0.60000-0.38000)*min(1,on/149))" in vf
    assert "(0.55000+(0.42000-0.55000)*min(1,on/149))" in vf
    assert "sin(on*2.70000)" in vf
    assert "between(on,60,90)" in vf
    assert "iw/2-(iw/zoom/2)" not in vf


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


def test_shot06_overlay_does_not_draw_duplicate_hook(tmp_path):
    module = load_module(
        PROJECT_DIR / "scripts" / "render_overlays.py",
        "wukong_render_overlays_hook",
        argv=["render_overlays.py", str(PROJECT_JSON)],
    )
    module.BUILD = tmp_path
    subs_dir = tmp_path / "subs"
    subs_dir.mkdir(parents=True)
    (subs_dir / "seg6.srt").write_text(
        "\n".join(
            [
                "1",
                "00:00:00,100 --> 00:00:01,956",
                "这一战，才刚刚开始。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    shot = {
        "id": "shot06_afterimage_hook",
        "caption": "未完待续",
    }
    item = {
        "seg": 6,
        "clip": 2.0,
    }

    module.render_segment(shot, item)

    overlay = tmp_path / "overlays" / "seg6" / "0001.png"
    with Image.open(overlay) as img:
        hook_band = img.crop((160, 1200, 920, 1480))
        assert hook_band.getchannel("A").getbbox() is None


def ffprobe_stream(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-show_entries", "format=duration",
        "-of", "json", str(path)
    ]).decode()
    return json.loads(raw)


def ffprobe_media(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]).decode()
    return json.loads(raw)


def test_final_exports_match_contract():
    for name in ["wukong_erlang_sample_vertical.mp4", "wukong_erlang_sample_final.mp4"]:
        path = PROJECT_DIR / name
        assert path.exists()
        info = ffprobe_stream(path)
        stream = info["streams"][0]
        duration = float(info["format"]["duration"])
        assert stream["width"] == 1080
        assert stream["height"] == 1920
        assert 28.0 <= duration <= 32.5


def test_final_exports_include_audio_streams():
    for name in ["wukong_erlang_sample_vertical.mp4", "wukong_erlang_sample_final.mp4"]:
        path = PROJECT_DIR / name
        info = ffprobe_media(path)
        audio_streams = [stream for stream in info["streams"] if stream["codec_type"] == "audio"]
        assert audio_streams, f"{name} is missing audio stream"
        assert float(audio_streams[0]["duration"]) > 0.0


def test_final_mix_audio_stream_uses_aac_and_has_duration():
    info = ffprobe_media(PROJECT_DIR / "wukong_erlang_sample_final.mp4")
    audio_streams = [stream for stream in info["streams"] if stream["codec_type"] == "audio"]
    assert audio_streams, "final mix is missing audio stream"
    audio_stream = audio_streams[0]
    assert audio_stream["codec_name"] == "aac"
    assert float(audio_stream["duration"]) > 0.0


def test_qa_thumbnails_exist():
    qa = PROJECT_DIR / "build" / "qa"
    for name in ["qa_0003.jpg", "qa_0011.jpg", "qa_0020.jpg", "qa_0029.jpg"]:
        path = qa / name
        assert path.exists()
        with Image.open(path) as img:
            assert img.size[1] > img.size[0]
