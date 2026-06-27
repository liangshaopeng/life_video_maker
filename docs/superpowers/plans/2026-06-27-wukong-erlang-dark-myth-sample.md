# Wukong Erlang Dark Myth Sample Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 28-32 second vertical dark-myth sample video for “孙悟空大战二郎神”, using original AI keyframes, Chinese narration, burned subtitles, cinematic motion, procedural dark BGM, and a final mixed export.

**Architecture:** Create a self-contained data-driven project under `神话短剧/孙悟空大战二郎神-样片/`. `project.json` is the source of truth for shots, timing, narration, captions, keyframe paths, and prompt paths; scripts validate the manifest, generate narration/subtitles, render overlays, create BGM, assemble clips, and verify the final video. The first sample uses AI-generated still keyframes animated with slow push/zoom motion; each shot can later be replaced by generated video clips without changing narration or timing.

**Tech Stack:** Python 3, pytest, Pillow, edge-tts, ffmpeg/ffprobe 8.1.1, macOS font `/System/Library/Fonts/Hiragino Sans GB.ttc`, AI raster image generation via the imagegen skill/tool during the asset-generation task.

## Global Constraints

- Output format: 9:16 vertical, 1080x1920.
- Target duration: 28 to 32 seconds.
- Style: dark myth trailer, not light explainer, comedy remix, 86 TV replica, movie replica, or existing Douyin work clone.
- Main colors: black-gold, cold blue, iron gray, thunder-fire white.
- Required story beats: Heavenly siege in first 3 seconds, Erlang’s heavenly eye opens, at least one weapon clash, clone-breaking eye scan, final “未完待续” hook.
- Captions: single visible line should not exceed 14 Chinese characters.
- Avoid concrete film/game names, actor faces, recognizable existing shots, modern buildings, malformed text watermarks, and obvious hand/finger artifacts.
- Final deliverables: no-BGM vertical file and final BGM-mixed file.
- Do not touch existing sports-video project scripts except copying a local narration script into the new project directory.
- Keep all generated project files inside `神话短剧/孙悟空大战二郎神-样片/` and tests under `tests/`.

---

## File Structure

Create this structure:

```text
神话短剧/孙悟空大战二郎神-样片/
  project.json
  prompts/
    shot01_heavenly_siege.md
    shot02_heavenly_eye.md
    shot03_weapon_clash.md
    shot04_clone_break.md
    shot05_final_staff.md
    shot06_afterimage_hook.md
  assets/
    keyframes/
      shot01_heavenly_siege.png
      shot02_heavenly_eye.png
      shot03_weapon_clash.png
      shot04_clone_break.png
      shot05_final_staff.png
      shot06_afterimage_hook.png
    bgm/
      dark_myth_bgm.wav
  scripts/
    validate_project.py
    check_assets.py
    make_narration.py
    make_dark_bgm.py
    render_overlays.py
    assemble_sample.py
    mix_bgm.sh
  build/
    audio/
    overlays/
    subs/
    clips/
    qa/
```

Create these tests:

```text
tests/test_wukong_sample_project.py
tests/test_wukong_sample_prompts.py
tests/test_wukong_sample_scripts.py
```

Responsibility boundaries:

- `project.json`: timing, captions, narration, keyframe paths, prompt paths, visual motion settings, and output names.
- `prompts/*.md`: exact positive and negative prompts used to generate each keyframe.
- `scripts/validate_project.py`: manifest-only checks, no media decoding.
- `scripts/check_assets.py`: checks required generated images and audio assets exist with correct dimensions/duration.
- `scripts/make_narration.py`: local copy of the existing TTS/subtitle generator, pointed at this project manifest.
- `scripts/make_dark_bgm.py`: creates copyright-free low drum/rumble music.
- `scripts/render_overlays.py`: renders transparent subtitle/title PNG overlays per shot.
- `scripts/assemble_sample.py`: converts keyframes plus overlays plus narration into the no-BGM vertical MP4.
- `scripts/mix_bgm.sh`: mixes generated BGM under the no-BGM MP4.

---

### Task 1: Project Manifest And Validation

**Files:**
- Create: `神话短剧/孙悟空大战二郎神-样片/project.json`
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py`
- Create: `tests/test_wukong_sample_project.py`

**Interfaces:**
- Consumes: none.
- Produces: `load_project(path: Path) -> dict` and `validate_project(project: dict, root: Path) -> list[str]` in `scripts/validate_project.py`.

- [ ] **Step 1: Write the failing manifest tests**

Create `tests/test_wukong_sample_project.py`:

```python
import importlib.util
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_wukong_sample_project.py -v
```

Expected: FAIL because `神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py` does not exist.

- [ ] **Step 3: Create the validator**

Create `神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py`:

```python
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
```

- [ ] **Step 4: Create the manifest**

Create `神话短剧/孙悟空大战二郎神-样片/project.json`:

```json
{
  "name": "wukong-erlang-dark-myth-sample",
  "output_dir": ".",
  "build_dir": "build",
  "canvas": { "width": 1080, "height": 1920, "fps": 30 },
  "voice": { "name": "zh-CN-YunjianNeural", "rate": "+8%", "pitch": "-2Hz", "volume": "+8%" },
  "pad": 0.18,
  "caption_maxlen": 14,
  "font": "/System/Library/Fonts/Hiragino Sans GB.ttc",
  "watermark": "思考的我",
  "grade": "eq=contrast=1.12:saturation=1.08:brightness=-0.03",
  "bgm": "assets/bgm/dark_myth_bgm.wav",
  "final_no_bgm": "wukong_erlang_sample_vertical.mp4",
  "final_mixed": "wukong_erlang_sample_final.mp4",
  "shots": [
    {
      "id": "shot01_heavenly_siege",
      "duration": 4.0,
      "beat": "天庭围猎齐天大圣",
      "narration": "那一天，天庭终于派出了真正能看穿他的神。",
      "caption": "天庭围猎\\n齐天大圣",
      "prompt": "prompts/shot01_heavenly_siege.md",
      "keyframe": "assets/keyframes/shot01_heavenly_siege.png",
      "motion": { "zoom_start": 1.0, "zoom_end": 1.06, "pan_x": 0.50, "pan_y": 0.46 }
    },
    {
      "id": "shot02_heavenly_eye",
      "duration": 5.0,
      "beat": "天眼开",
      "narration": "三界万法，皆可藏形。",
      "caption": "天眼开",
      "prompt": "prompts/shot02_heavenly_eye.md",
      "keyframe": "assets/keyframes/shot02_heavenly_eye.png",
      "motion": { "zoom_start": 1.0, "zoom_end": 1.08, "pan_x": 0.50, "pan_y": 0.38 }
    },
    {
      "id": "shot03_weapon_clash",
      "duration": 6.0,
      "beat": "兵器硬碰",
      "narration": "可他偏要用一根棍子，打穿天命。",
      "caption": "金箍棒\\n对三尖两刃刀",
      "prompt": "prompts/shot03_weapon_clash.md",
      "keyframe": "assets/keyframes/shot03_weapon_clash.png",
      "motion": { "zoom_start": 1.0, "zoom_end": 1.10, "pan_x": 0.52, "pan_y": 0.50 }
    },
    {
      "id": "shot04_clone_break",
      "duration": 7.0,
      "beat": "真身被锁定",
      "narration": "分身万千，也逃不过这一眼。",
      "caption": "真身\\n被锁定",
      "prompt": "prompts/shot04_clone_break.md",
      "keyframe": "assets/keyframes/shot04_clone_break.png",
      "motion": { "zoom_start": 1.0, "zoom_end": 1.07, "pan_x": 0.48, "pan_y": 0.48 }
    },
    {
      "id": "shot05_final_staff",
      "duration": 6.0,
      "beat": "压不住的齐天大圣",
      "narration": "但他们忘了，看穿他，不等于能压住他。",
      "caption": "压不住的\\n齐天大圣",
      "prompt": "prompts/shot05_final_staff.md",
      "keyframe": "assets/keyframes/shot05_final_staff.png",
      "motion": { "zoom_start": 1.0, "zoom_end": 1.12, "pan_x": 0.50, "pan_y": 0.52 }
    },
    {
      "id": "shot06_afterimage_hook",
      "duration": 2.0,
      "beat": "未完待续",
      "narration": "这一战，才刚刚开始。",
      "caption": "未完待续",
      "prompt": "prompts/shot06_afterimage_hook.md",
      "keyframe": "assets/keyframes/shot06_afterimage_hook.png",
      "motion": { "zoom_start": 1.0, "zoom_end": 1.02, "pan_x": 0.50, "pan_y": 0.50 }
    }
  ],
  "_note": "30秒暗黑神话样片。公版人物和原创视觉, 不复刻影视剧/游戏/抖音现有作品。"
}
```

- [ ] **Step 5: Run tests and validator**

Run:

```bash
pytest tests/test_wukong_sample_project.py -v
python3 神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py 神话短剧/孙悟空大战二郎神-样片/project.json
```

Expected: all 3 tests PASS and validator prints `OK: 神话短剧/孙悟空大战二郎神-样片/project.json`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_wukong_sample_project.py 神话短剧/孙悟空大战二郎神-样片/project.json 神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py
git commit -m "feat: scaffold wukong erlang sample manifest"
```

---

### Task 2: Prompt Pack Contract

**Files:**
- Create: `神话短剧/孙悟空大战二郎神-样片/prompts/shot01_heavenly_siege.md`
- Create: `神话短剧/孙悟空大战二郎神-样片/prompts/shot02_heavenly_eye.md`
- Create: `神话短剧/孙悟空大战二郎神-样片/prompts/shot03_weapon_clash.md`
- Create: `神话短剧/孙悟空大战二郎神-样片/prompts/shot04_clone_break.md`
- Create: `神话短剧/孙悟空大战二郎神-样片/prompts/shot05_final_staff.md`
- Create: `神话短剧/孙悟空大战二郎神-样片/prompts/shot06_afterimage_hook.md`
- Create: `tests/test_wukong_sample_prompts.py`

**Interfaces:**
- Consumes: `project.json` shot `prompt` paths.
- Produces: six prompt documents with `Positive prompt`, `Motion prompt`, and `Negative prompt` sections.

- [ ] **Step 1: Write failing prompt tests**

Create `tests/test_wukong_sample_prompts.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_wukong_sample_prompts.py -v
```

Expected: FAIL because prompt files do not exist.

- [ ] **Step 3: Create prompt documents**

Create each file with this exact content pattern and shot-specific body.

`prompts/shot01_heavenly_siege.md`:

```markdown
# Shot 01 Heavenly Siege

## Positive prompt

Vertical 9:16 cinematic dark Chinese myth fantasy frame. A storm-black heavenly gate towers above an ocean of clouds, cold blue lightning behind it, iron-gray celestial soldiers stand in layered silhouettes with spears raised, a lone mythic monkey king warrior stands far away on a cracked cloud platform, battle-worn golden staff in hand, black-gold rim light, cold blue fog, thunder-fire white highlights, epic scale, high detail, dramatic low angle, no text, no watermark, original character design, original costume design.

## Motion prompt

Slow forward push through clouds toward the lone warrior. Clouds roll left to right, lightning pulses behind the gate, soldier silhouettes remain heavy and still. Keep the monkey king small but readable.

## Negative prompt

Modern city, sci-fi armor, cartoon style, comedy expression, cute mascot, actor likeness, TV drama frame, game screenshot, existing film composition, readable text, watermark, logo, distorted hands, extra limbs, melted weapon, bright cheerful palette, beige palette, red festive palace.
```

`prompts/shot02_heavenly_eye.md`:

```markdown
# Shot 02 Heavenly Eye

## Positive prompt

Vertical 9:16 close-up portrait of a three-eyed celestial warrior judge in dark iron armor and black-gold cloak, calm cold expression, the third eye on his forehead opening with a vertical golden beam, cold blue smoke around his shoulders, subtle divine halo shaped like broken thunder, cinematic dark myth realism, sharp facial structure, original character design, original armor pattern, no text, no watermark.

## Motion prompt

Very slow push toward the face. The third eye opens from a thin golden crack into a bright vertical beam. Smoke drifts downward, background thunder flickers, the warrior does not blink.

## Negative prompt

Friendly smile, comedy expression, modern haircut, sci-fi visor, laser robot, actor likeness, TV drama frame, game screenshot, existing film composition, readable text, watermark, logo, extra eyes outside the forehead, deformed face, asymmetrical pupils, soft romantic lighting.
```

`prompts/shot03_weapon_clash.md`:

```markdown
# Shot 03 Weapon Clash

## Positive prompt

Vertical 9:16 action frame. A mythic monkey king warrior with battle-damaged dark-gold armor swings a glowing golden staff into the three-pointed double-edged spear of a three-eyed celestial warrior. The weapons collide at the center of frame, huge sparks, white thunder, cold blue shockwave, fragments of cloud and stone flying toward camera, dynamic low angle, motion blur on weapons, faces partially visible and intense, original cinematic dark myth design, no text, no watermark.

## Motion prompt

Fast impact beat. Camera shakes slightly on weapon contact, sparks burst outward toward viewer, blue shockwave expands for half a second, then the two warriors hold pressure against each other.

## Negative prompt

Modern weapons, guns, neon cyberpunk, comedy, cute monkey, actor likeness, TV drama frame, game screenshot, existing film composition, readable text, watermark, logo, bent staff, melted spear, duplicate heads, extra arms, unclear weapon contact, flat lighting.
```

`prompts/shot04_clone_break.md`:

```markdown
# Shot 04 Clone Break

## Positive prompt

Vertical 9:16 dark myth battle scene above a shattered cloud battlefield. Many ghostly afterimages of a mythic monkey king warrior circle through smoke, each holding a golden staff, while a three-eyed celestial warrior stands centered and sweeps a golden heavenly-eye beam across them. False clones dissolve into ash and blue smoke, one real figure is half-revealed at the edge of the light, black-gold and cold-blue palette, epic cinematic lighting, original character and costume design, no text, no watermark.

## Motion prompt

Heavenly-eye beam sweeps from right to left. Clone afterimages burst into ash one after another. The true body becomes more visible for the final second.

## Negative prompt

Comedy clones, cute cartoon, modern city, sci-fi scanner UI, actor likeness, TV drama frame, game screenshot, existing film composition, readable text, watermark, logo, too many unreadable bodies, extra limbs, deformed hands, bright daylight, colorful festival smoke.
```

`prompts/shot05_final_staff.md`:

```markdown
# Shot 05 Final Staff

## Positive prompt

Vertical 9:16 extreme cinematic action frame. The mythic monkey king warrior, wounded but furious, flips forward from shattered clouds and smashes a glowing golden staff toward the camera. Broken stone, cloud waves, sparks, and cold blue lightning explode around him. His eyes burn gold, armor torn, posture defiant, black-gold rim light, thunder-fire white highlights, dark myth trailer style, original design, no text, no watermark.

## Motion prompt

Camera pulls back for a fraction, then the staff rushes toward lens. Add impact shake as the cloud sea cracks open below. Keep the face readable and heroic.

## Negative prompt

Cute monkey face, comedy pose, modern clothes, sci-fi armor, actor likeness, TV drama frame, game screenshot, existing film composition, readable text, watermark, logo, tiny staff, rubber weapon, extra hands, distorted face, bright cheerful sky.
```

`prompts/shot06_afterimage_hook.md`:

```markdown
# Shot 06 Afterimage Hook

## Positive prompt

Vertical 9:16 dark final hook frame. Almost black cloud void with a burning golden staff lying diagonally in the foreground, a faint vertical golden heavenly-eye afterimage floating in the distance, cold blue smoke, tiny sparks drifting upward, black-gold and cold-blue color contrast, cinematic silence after battle, original visual design, no text, no watermark.

## Motion prompt

Hold nearly still. Sparks drift upward slowly, the heavenly-eye afterimage pulses once, the burning staff glows and fades slightly.

## Negative prompt

Modern floor, city street, comedy prop, actor likeness, TV drama frame, game screenshot, existing film composition, readable text, watermark, logo, bright colorful background, full character close-up, cluttered objects, malformed weapon.
```

- [ ] **Step 4: Run prompt tests**

Run:

```bash
pytest tests/test_wukong_sample_prompts.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_wukong_sample_prompts.py 神话短剧/孙悟空大战二郎神-样片/prompts
git commit -m "feat: add wukong erlang keyframe prompts"
```

---

### Task 3: Keyframe Asset Generation And Checks

**Files:**
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py`
- Create: generated image files under `神话短剧/孙悟空大战二郎神-样片/assets/keyframes/`
- Modify: `tests/test_wukong_sample_scripts.py`

**Interfaces:**
- Consumes: `project.json` shot `keyframe` paths and prompt documents.
- Produces: `check_keyframes(project_path: Path) -> list[str]` in `scripts/check_assets.py`; six 1080x1920 or larger portrait PNG keyframes.

- [ ] **Step 1: Write failing asset-check tests**

Create `tests/test_wukong_sample_scripts.py` with the first test:

```python
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


def test_check_assets_reports_missing_keyframes_before_generation():
    module = load_module(PROJECT_DIR / "scripts" / "check_assets.py", "wukong_check_assets")
    errors = module.check_keyframes(PROJECT_JSON)
    assert any("missing keyframe" in err for err in errors)
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
pytest tests/test_wukong_sample_scripts.py::test_check_assets_reports_missing_keyframes_before_generation -v
```

Expected: FAIL because `scripts/check_assets.py` does not exist.

- [ ] **Step 3: Create the asset checker**

Create `神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py`:

```python
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
                width, height = img.size
        except Exception as exc:
            errors.append(f"{shot['id']}: unreadable image {img_path}: {exc}")
            continue
        if width < 1080 or height < 1440:
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
```

- [ ] **Step 4: Run the missing-keyframes test**

Run:

```bash
pytest tests/test_wukong_sample_scripts.py::test_check_assets_reports_missing_keyframes_before_generation -v
```

Expected: PASS because missing keyframes are reported.

- [ ] **Step 5: Generate six keyframes**

Use the imagegen skill/tool. For each prompt file, generate one portrait cinematic image and save the chosen result to the exact path in `project.json`:

```text
神话短剧/孙悟空大战二郎神-样片/assets/keyframes/shot01_heavenly_siege.png
神话短剧/孙悟空大战二郎神-样片/assets/keyframes/shot02_heavenly_eye.png
神话短剧/孙悟空大战二郎神-样片/assets/keyframes/shot03_weapon_clash.png
神话短剧/孙悟空大战二郎神-样片/assets/keyframes/shot04_clone_break.png
神话短剧/孙悟空大战二郎神-样片/assets/keyframes/shot05_final_staff.png
神话短剧/孙悟空大战二郎神-样片/assets/keyframes/shot06_afterimage_hook.png
```

For each image, verify visually before saving:

- Shot 01: distant Wukong figure is visible against the heavenly siege.
- Shot 02: Erlang-like warrior has a single third eye on the forehead and no actor likeness.
- Shot 03: staff and three-pointed spear visibly collide.
- Shot 04: clones dissolve and the eye beam is readable.
- Shot 05: staff drives toward camera and Wukong reads as defiant.
- Shot 06: no full character close-up; it is a quiet hook frame with staff and eye afterimage.

- [ ] **Step 6: Add positive asset tests**

Append to `tests/test_wukong_sample_scripts.py`:

```python
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
```

- [ ] **Step 7: Run asset tests**

Run:

```bash
pytest tests/test_wukong_sample_scripts.py::test_generated_keyframes_are_ready tests/test_wukong_sample_scripts.py::test_keyframes_are_portrait_images -v
```

Expected: 2 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add tests/test_wukong_sample_scripts.py 神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py
git add -f 神话短剧/孙悟空大战二郎神-样片/assets/keyframes
git commit -m "feat: add wukong erlang generated keyframes"
```

---

### Task 4: Narration, Subtitles, And Procedural BGM

**Files:**
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/make_narration.py`
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/make_dark_bgm.py`
- Modify: `tests/test_wukong_sample_scripts.py`
- Generate: `神话短剧/孙悟空大战二郎神-样片/build/audio/*.mp3`
- Generate: `神话短剧/孙悟空大战二郎神-样片/build/subs/*.srt`
- Generate: `神话短剧/孙悟空大战二郎神-样片/assets/bgm/dark_myth_bgm.wav`

**Interfaces:**
- Consumes: `project.json` shot `narration` values and voice config.
- Produces: `build/timeline.json`, `build/subs/global.srt`, per-shot narration MP3 files, and a 31+ second WAV BGM.

- [ ] **Step 1: Extend tests for narration and BGM outputs**

Append to `tests/test_wukong_sample_scripts.py`:

```python
def ffprobe_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nk=1:nw=1", str(path)
    ]).decode().strip())


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


def test_bgm_exists_and_is_long_enough():
    bgm = PROJECT_DIR / "assets" / "bgm" / "dark_myth_bgm.wav"
    assert bgm.exists()
    assert ffprobe_duration(bgm) >= 31.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_wukong_sample_scripts.py::test_narration_outputs_exist_after_generation tests/test_wukong_sample_scripts.py::test_bgm_exists_and_is_long_enough -v
```

Expected: FAIL because narration and BGM files do not exist.

- [ ] **Step 3: Copy narration script**

Run:

```bash
cp 战术解析视频/突尼斯-日本/make_narration.py 神话短剧/孙悟空大战二郎神-样片/scripts/make_narration.py
```

Modify the copied script in one place: when iterating segments, read from `cfg.get("segments", cfg.get("shots", []))`, and when getting text use `seg.get("text") or seg["narration"]`.

The modified loop header and text line should be:

```python
segments = cfg.get("segments", cfg.get("shots", []))
for i,seg in enumerate(segments,1):
    text=seg.get("text") or seg["narration"]; spoken=to_spoken(text); mp3=os.path.join(AUD,f"seg{i}.mp3")
```

- [ ] **Step 4: Create procedural BGM generator**

Create `神话短剧/孙悟空大战二郎神-样片/scripts/make_dark_bgm.py`:

```python
# -*- coding: utf-8 -*-
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "bgm" / "dark_myth_bgm.wav"
SR = 44100
DURATION = 32.0


def clamp(v: float) -> float:
    return max(-0.98, min(0.98, v))


def envelope(t: float, start: float, length: float) -> float:
    if t < start or t > start + length:
        return 0.0
    x = (t - start) / length
    return math.exp(-5.0 * x) * math.sin(math.pi * min(1.0, x * 4.0))


def sample(t: float) -> float:
    rumble = 0.18 * math.sin(2 * math.pi * 44 * t) + 0.08 * math.sin(2 * math.pi * 66 * t)
    pulse = 0.0
    for beat in [0.0, 3.9, 8.8, 14.9, 21.8, 27.8]:
        pulse += 0.55 * envelope(t, beat, 1.2) * math.sin(2 * math.pi * (68 - 20 * (t - beat)) * t)
    shimmer = 0.025 * random.uniform(-1.0, 1.0)
    fade_in = min(1.0, t / 1.2)
    fade_out = min(1.0, max(0.0, (DURATION - t) / 2.4))
    return clamp((rumble + pulse + shimmer) * fade_in * fade_out)


def main() -> int:
    random.seed(42)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = int(SR * DURATION)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        for i in range(frames):
            value = int(sample(i / SR) * 32767)
            packed = struct.pack("<hh", value, value)
            w.writeframesraw(packed)
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Generate narration and BGM**

Run:

```bash
cd 神话短剧/孙悟空大战二郎神-样片
python3 scripts/make_narration.py project.json
python3 scripts/make_dark_bgm.py
```

Expected: `make_narration.py` prints six `segN` lines and a total duration; `make_dark_bgm.py` prints `assets/bgm/dark_myth_bgm.wav`.

- [ ] **Step 6: Run narration/BGM tests**

Run from repository root:

```bash
pytest tests/test_wukong_sample_scripts.py::test_narration_outputs_exist_after_generation tests/test_wukong_sample_scripts.py::test_bgm_exists_and_is_long_enough -v
python3 神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py 神话短剧/孙悟空大战二郎神-样片/project.json
```

Expected: tests PASS and asset checker prints `OK: assets ready`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_wukong_sample_scripts.py 神话短剧/孙悟空大战二郎神-样片/scripts/make_narration.py 神话短剧/孙悟空大战二郎神-样片/scripts/make_dark_bgm.py
git add -f 神话短剧/孙悟空大战二郎神-样片/build/audio 神话短剧/孙悟空大战二郎神-样片/build/subs 神话短剧/孙悟空大战二郎神-样片/build/timeline.json 神话短剧/孙悟空大战二郎神-样片/assets/bgm/dark_myth_bgm.wav
git commit -m "feat: add wukong erlang narration and bgm"
```

---

### Task 5: Overlay Rendering

**Files:**
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py`
- Modify: `tests/test_wukong_sample_scripts.py`
- Generate: `神话短剧/孙悟空大战二郎神-样片/build/overlays/segN/*.png`

**Interfaces:**
- Consumes: `project.json`, `build/timeline.json`, and `build/subs/segN.srt`.
- Produces: transparent 1080x1920 PNG overlay frame sequences at 30fps.

- [ ] **Step 1: Add overlay output test**

Append to `tests/test_wukong_sample_scripts.py`:

```python
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
```

- [ ] **Step 2: Run overlay test to verify it fails**

Run:

```bash
pytest tests/test_wukong_sample_scripts.py::test_overlay_frames_exist_after_render -v
```

Expected: FAIL because overlay frames do not exist.

- [ ] **Step 3: Create overlay renderer**

Create `神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py`:

```python
# -*- coding: utf-8 -*-
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("project.json")
ROOT = PROJECT.resolve().parent
cfg = json.loads(PROJECT.read_text(encoding="utf-8"))
timeline = json.loads((ROOT / cfg.get("build_dir", "build") / "timeline.json").read_text(encoding="utf-8"))

W = cfg["canvas"]["width"]
H = cfg["canvas"]["height"]
FPS = cfg["canvas"]["fps"]
FONT_PATH = cfg.get("font", "/System/Library/Fonts/Hiragino Sans GB.ttc")
BUILD = ROOT / cfg.get("build_dir", "build")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def parse_srt(path: Path):
    if not path.exists():
        return []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    cues = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        m = re.search(r"(\d+):(\d+):(\d+),(\d+)\s+-->\s+(\d+):(\d+):(\d+),(\d+)", block)
        if not m:
            continue
        g = list(map(int, m.groups()))
        st = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        en = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append((st, en, lines[-1]))
    return cues


def draw_centered(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, stroke_fill=(0, 0, 0, 220), stroke_width=4):
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=8, stroke_width=stroke_width)
    tw = bbox[2] - bbox[0]
    x, y = xy
    draw.multiline_text((x - tw / 2, y), text, font=fnt, fill=fill, spacing=8, align="center", stroke_width=stroke_width, stroke_fill=stroke_fill)


def cue_at(cues, t: float) -> str:
    for st, en, text in cues:
        if st <= t <= en:
            return text
    return ""


def render_segment(shot: dict, item: dict):
    out_dir = BUILD / "overlays" / f"seg{item['seg']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cues = parse_srt(BUILD / "subs" / f"seg{item['seg']}.srt")
    frames = max(1, int(round(float(item["clip"]) * FPS)))
    title_font = font(72)
    caption_font = font(60)
    small_font = font(32)

    for n in range(1, frames + 1):
        t = (n - 1) / FPS
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)

        draw.rectangle((0, 0, W, 150), fill=(0, 0, 0, 88))
        draw.text((44, 44), "孙悟空大战二郎神", font=small_font, fill=(230, 222, 204, 235))
        draw.text((W - 210, 44), "AI 样片", font=small_font, fill=(130, 190, 255, 225))

        if t < 1.25:
            draw_centered(draw, (W / 2, 214), shot["caption"], title_font, fill=(255, 214, 116, 255), stroke_width=5)

        current = cue_at(cues, t)
        if current:
            draw.rounded_rectangle((80, 1544, W - 80, 1716), radius=18, fill=(0, 0, 0, 150), outline=(255, 214, 116, 90), width=2)
            draw_centered(draw, (W / 2, 1584), current, caption_font, fill=(255, 255, 244, 255), stroke_width=5)

        if shot["id"] == "shot06_afterimage_hook":
            draw_centered(draw, (W / 2, 1336), "未完待续", font(86), fill=(255, 214, 116, 255), stroke_width=6)

        im.save(out_dir / f"{n:04d}.png")


def main() -> int:
    for shot, item in zip(cfg["shots"], timeline["segs"]):
        render_segment(shot, item)
        print(f"rendered overlay seg{item['seg']} {shot['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Render overlays**

Run:

```bash
cd 神话短剧/孙悟空大战二郎神-样片
python3 scripts/render_overlays.py project.json
```

Expected: six render lines, one for each segment, ending with the shot id.

- [ ] **Step 5: Run overlay tests**

Run from repository root:

```bash
pytest tests/test_wukong_sample_scripts.py::test_overlay_frames_exist_after_render -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_wukong_sample_scripts.py 神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py
git add -f 神话短剧/孙悟空大战二郎神-样片/build/overlays
git commit -m "feat: render wukong erlang subtitle overlays"
```

---

### Task 6: Vertical Assembly, Mixing, And QA

**Files:**
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py`
- Create: `神话短剧/孙悟空大战二郎神-样片/scripts/mix_bgm.sh`
- Modify: `tests/test_wukong_sample_scripts.py`
- Generate: `神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_vertical.mp4`
- Generate: `神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_final.mp4`
- Generate: `神话短剧/孙悟空大战二郎神-样片/build/qa/*.jpg`

**Interfaces:**
- Consumes: keyframes, overlays, narration audio, BGM, and `build/timeline.json`.
- Produces: final no-BGM and mixed MP4s plus QA thumbnails.

- [ ] **Step 1: Add final media tests**

Append to `tests/test_wukong_sample_scripts.py`:

```python
def ffprobe_stream(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-show_entries", "format=duration",
        "-of", "json", str(path)
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


def test_qa_thumbnails_exist():
    qa = PROJECT_DIR / "build" / "qa"
    for name in ["qa_0003.jpg", "qa_0011.jpg", "qa_0020.jpg", "qa_0029.jpg"]:
        path = qa / name
        assert path.exists()
        with Image.open(path) as img:
            assert img.size[1] > img.size[0]
```

- [ ] **Step 2: Run final tests to verify they fail**

Run:

```bash
pytest tests/test_wukong_sample_scripts.py::test_final_exports_match_contract tests/test_wukong_sample_scripts.py::test_qa_thumbnails_exist -v
```

Expected: FAIL because final MP4s and QA thumbnails do not exist.

- [ ] **Step 3: Create vertical assembler**

Create `神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py`:

```python
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
    concat_file.write_text("".join(f"file '{clip}'\\n" for clip in clips), encoding="utf-8")
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
```

- [ ] **Step 4: Create BGM mixer**

Create `神话短剧/孙悟空大战二郎神-样片/scripts/mix_bgm.sh`:

```bash
#!/bin/bash
set -euo pipefail
IN="${1:-wukong_erlang_sample_vertical.mp4}"
BGM="${2:-assets/bgm/dark_myth_bgm.wav}"
OUT="${3:-wukong_erlang_sample_final.mp4}"
DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$IN")
FOUT=$(python3 -c "print(f'{$DUR-1.4:.2f}')")
ffmpeg -y -hide_banner -loglevel error -i "$IN" -i "$BGM" -filter_complex "
[0:a]aformat=channel_layouts=stereo:sample_rates=44100,asplit=2[vocal][side];
[1:a]atrim=0:${DUR},asetpts=N/SR/TB,volume=0.38,afade=t=in:st=0:d=0.7,afade=t=out:st=${FOUT}:d=1.4,aformat=channel_layouts=stereo:sample_rates=44100[bgm];
[bgm][side]sidechaincompress=threshold=0.045:ratio=8:attack=10:release=260[ducked];
[vocal][ducked]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]
" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k "$OUT"
echo "$OUT"
```

Run:

```bash
chmod +x 神话短剧/孙悟空大战二郎神-样片/scripts/mix_bgm.sh
```

- [ ] **Step 5: Assemble no-BGM video and mixed final**

Run:

```bash
cd 神话短剧/孙悟空大战二郎神-样片
python3 scripts/assemble_sample.py project.json
./scripts/mix_bgm.sh wukong_erlang_sample_vertical.mp4 assets/bgm/dark_myth_bgm.wav wukong_erlang_sample_final.mp4
```

Expected: assembler prints the absolute path to `wukong_erlang_sample_vertical.mp4`; mixer prints `wukong_erlang_sample_final.mp4`.

- [ ] **Step 6: Run full verification**

Run from repository root:

```bash
pytest tests/test_wukong_sample_project.py tests/test_wukong_sample_prompts.py tests/test_wukong_sample_scripts.py -v
python3 神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py 神话短剧/孙悟空大战二郎神-样片/project.json
python3 神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py 神话短剧/孙悟空大战二郎神-样片/project.json
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -show_entries format=duration -of default=nw=1 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_final.mp4
```

Expected:

- pytest reports all tests PASS.
- validator prints `OK: 神话短剧/孙悟空大战二郎神-样片/project.json`.
- asset checker prints `OK: assets ready`.
- ffprobe output includes `width=1080`, `height=1920`, and a duration from 28.0 to 32.5 seconds.

- [ ] **Step 7: Visual QA**

Open these QA images and inspect them:

```text
神话短剧/孙悟空大战二郎神-样片/build/qa/qa_0003.jpg
神话短剧/孙悟空大战二郎神-样片/build/qa/qa_0011.jpg
神话短剧/孙悟空大战二郎神-样片/build/qa/qa_0020.jpg
神话短剧/孙悟空大战二郎神-样片/build/qa/qa_0029.jpg
```

Pass criteria:

- `qa_0003.jpg`: heavenly siege and Wukong silhouette are readable.
- `qa_0011.jpg`: weapon clash is central and not hidden by captions.
- `qa_0020.jpg`: clone-breaking eye beam is readable.
- `qa_0029.jpg`: “未完待续” hook appears on a quiet final frame.

- [ ] **Step 8: Commit**

```bash
git add tests/test_wukong_sample_scripts.py 神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py 神话短剧/孙悟空大战二郎神-样片/scripts/mix_bgm.sh
git add -f 神话短剧/孙悟空大战二郎神-样片/build/clips 神话短剧/孙悟空大战二郎神-样片/build/qa 神话短剧/孙悟空大战二郎神-样片/build/concat.txt 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_vertical.mp4 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_final.mp4
git commit -m "feat: assemble wukong erlang dark myth sample"
```

---

## Self-Review

Spec coverage:

- 30 second 9:16 sample: Tasks 1 and 6 validate duration and dimensions.
- Dark myth style and original visual constraints: Tasks 1 and 2 encode the style in manifest and prompts; Task 3 includes visual selection criteria.
- Required beats: Task 1 validates beat text; Task 2 provides exact prompts; Task 6 QA checks the resulting frames.
- Chinese narration and subtitles: Task 4 generates narration/subtitles; Task 5 renders overlays.
- BGM and final export: Task 4 creates procedural BGM; Task 6 mixes final video.
- No-BGM and mixed deliverables: Task 6 exports both files.
- Expansion-ready structure: file structure keeps timing, prompts, assets, overlays, and assembly separate.

Red-flag scan:

- The plan uses exact file paths and exact media filenames throughout.
- Code-changing steps include concrete code blocks, commands, and expected outcomes.
- Media-generation steps name the required output files and visual acceptance checks.

Type and interface consistency:

- `project.json` uses `shots`, and copied narration script modification reads `cfg.get("segments", cfg.get("shots", []))`.
- `check_assets.py` functions are called by tests with `Path` arguments.
- `render_overlays.py` and `assemble_sample.py` both consume `build/timeline.json` segment entries as `timeline["segs"]`.
- Final exports use `final_no_bgm` and `final_mixed` names from `project.json`.
