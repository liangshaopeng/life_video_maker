import importlib.util
import json
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
        assert height >= 1440
