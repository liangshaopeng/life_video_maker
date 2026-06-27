import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "神话短剧" / "孙悟空大战二郎神-样片"
BANNED = ["86版", "黑神话悟空", "杨洁", "六小龄童", "央视", "电视剧截图", "游戏截图", "电影截图"]


def test_prompt_files_exist_and_have_required_sections():
    project = json.loads((PROJECT_DIR / "project.json").read_text(encoding="utf-8"))
    for shot in project["shots"]:
        prompt_path = PROJECT_DIR / shot["prompt"]
        text = prompt_path.read_text(encoding="utf-8")
        assert "# " in text
        assert "## Positive prompt" in text
        assert "## Motion prompt" in text
        assert "## Negative prompt" in text
        assert len(text) > 700


def test_prompts_do_not_reference_existing_adaptations():
    for prompt_path in (PROJECT_DIR / "prompts").glob("*.md"):
        text = prompt_path.read_text(encoding="utf-8")
        for banned in BANNED:
            assert banned not in text
