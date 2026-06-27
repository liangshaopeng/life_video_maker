import importlib.util
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "神话短剧" / "孙悟空大战二郎神-样片"
PROJECT_JSON = PROJECT_DIR / "project.json"
VALIDATOR = PROJECT_DIR / "scripts" / "validate_project.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("wukong_validate_project", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_manifest_is_valid():
    module = load_validator()
    project = module.load_project(PROJECT_JSON)
    errors = module.validate_project(project, PROJECT_DIR)
    assert errors == []


def test_sample_duration_and_shape_contract():
    module = load_validator()
    project = module.load_project(PROJECT_JSON)
    assert project["canvas"] == {"width": 1080, "height": 1920, "fps": 30}
    total = sum(float(shot["duration"]) for shot in project["shots"])
    assert 28.0 <= total <= 32.0
    assert len(project["shots"]) == 6


def test_required_story_beats_are_present():
    module = load_validator()
    project = module.load_project(PROJECT_JSON)
    beat_text = " ".join(shot["beat"] for shot in project["shots"])
    for required in ["天庭围猎", "天眼开", "兵器硬碰", "真身被锁定", "未完待续"]:
        assert required in beat_text


def test_relative_project_paths_stay_in_tree():
    module = load_validator()
    project = copy.deepcopy(module.load_project(PROJECT_JSON))
    project["shots"][0]["prompt"] = "../outside/secret.md"

    errors = module.validate_project(project, PROJECT_DIR)
    assert any("prompt must be inside project root" in err for err in errors)

    project["bgm"] = "/tmp/outside.wav"
    errors = module.validate_project(project, PROJECT_DIR)
    assert any("bgm must be inside project root" in err for err in errors)


def test_missing_motion_key_is_invalid():
    module = load_validator()
    project = copy.deepcopy(module.load_project(PROJECT_JSON))
    del project["shots"][0]["motion"]["pan_y"]

    errors = module.validate_project(project, PROJECT_DIR)
    assert any("motion missing key: pan_y" in err for err in errors)


def test_caption_maxlen_is_honored():
    module = load_validator()
    project = copy.deepcopy(module.load_project(PROJECT_JSON))
    project["caption_maxlen"] = 3
    project["shots"][0]["caption"] = "齐天大圣降临"

    errors = module.validate_project(project, PROJECT_DIR)
    assert any("caption exceeds 3 Chinese characters on one line" in err for err in errors)


def test_caption_maxlen_higher_than_hard_cap_is_rejected():
    module = load_validator()
    project = copy.deepcopy(module.load_project(PROJECT_JSON))
    project["caption_maxlen"] = 20
    project["shots"][0]["caption"] = "齐天大圣降临"

    errors = module.validate_project(project, PROJECT_DIR)
    assert any("caption_maxlen must not exceed 14" in err for err in errors)


def test_caption_uses_hard_cap_even_with_higher_maxlen():
    module = load_validator()
    project = copy.deepcopy(module.load_project(PROJECT_JSON))
    project["caption_maxlen"] = 20
    project["shots"][0]["caption"] = "齐天大圣降临天庭大战猴王降生光明顶"

    errors = module.validate_project(project, PROJECT_DIR)
    assert any("caption exceeds 14 Chinese characters on one line" in err for err in errors)
