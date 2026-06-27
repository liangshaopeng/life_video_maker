# Wukong Erlang Motion Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-export the Wukong vs Erlang sample with stronger camera motion and frame-level action effects so it no longer feels like static slices.

**Architecture:** Keep the existing project layout and render pipeline. Add optional motion metadata in `project.json`, expose testable motion/filter helpers in `assemble_sample.py`, and add deterministic PIL overlay effects in `render_overlays.py` before subtitle/title drawing.

**Tech Stack:** Python 3, ffmpeg/ffprobe, Pillow, pytest, existing shell scripts.

## Global Constraints

- Final videos stay 1080x1920 vertical at 30 fps.
- Final duration stays about 30 seconds.
- Existing narration, subtitles, BGM, and output filenames remain unchanged.
- Dynamic effects must not cover subtitle readability.
- No external image-to-video API is required for this pass.
- Preserve existing generated keyframes.

---

### Task 1: Camera Motion Contract

**Files:**
- Modify: `tests/test_wukong_sample_scripts.py`
- Modify: `神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py`
- Modify: `神话短剧/孙悟空大战二郎神-样片/project.json`

**Interfaces:**
- Consumes: shot dictionaries from `project.json`.
- Produces: `motion_params(shot: dict, frames: int) -> dict[str, float]` and `zoompan_filter(shot: dict, frames: int) -> str`.

- [ ] **Step 1: Write the failing test**

Add these tests to `tests/test_wukong_sample_scripts.py`:

```python
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
```

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_wukong_sample_scripts.py::test_motion_params_supports_directional_pan_and_shake tests/test_wukong_sample_scripts.py::test_zoompan_filter_uses_directional_pan_expression -v
```

Expected: FAIL because `motion_params` and `zoompan_filter` do not exist.

- [ ] **Step 3: Implement motion helpers**

In `assemble_sample.py`, add `clamp01`, `motion_params`, `zoompan_filter`, and use `zoompan_filter` inside `build_clip`. `motion_params` reads optional `pan_start_x`, `pan_start_y`, `pan_end_x`, `pan_end_y`, `shake`, and `impact_at`; missing values fall back to existing `pan_x` and `pan_y`. `zoompan_filter` returns the same scale/crop/zoompan prefix, but uses interpolated pan expressions and a short impact shake window.

- [ ] **Step 4: Strengthen shot metadata**

Update each shot in `project.json` with optional motion metadata. Example shape:

```json
"motion": {
  "zoom_start": 1.0,
  "zoom_end": 1.18,
  "pan_x": 0.58,
  "pan_y": 0.52,
  "pan_start_x": 0.42,
  "pan_start_y": 0.40,
  "shake": 0.010,
  "impact_at": 0.55
}
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_wukong_sample_scripts.py::test_motion_params_supports_directional_pan_and_shake tests/test_wukong_sample_scripts.py::test_zoompan_filter_uses_directional_pan_expression -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_wukong_sample_scripts.py 神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py 神话短剧/孙悟空大战二郎神-样片/project.json
git commit -m "feat: add strong camera motion for wukong sample"
```

### Task 2: Cinematic Overlay Effects

**Files:**
- Modify: `tests/test_wukong_sample_scripts.py`
- Modify: `神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py`

**Interfaces:**
- Consumes: shot dictionaries and segment timing from `project.json`/`timeline.json`.
- Produces: `draw_cinematic_effects(draw: ImageDraw.ImageDraw, shot: dict, t: float, duration: float) -> None`.

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_wukong_sample_scripts.py`:

```python
def test_cinematic_effects_change_overlay_pixels_over_time():
    module = load_module(
        PROJECT_DIR / "scripts" / "render_overlays.py",
        "wukong_render_cinematic_effects",
        argv=["render_overlays.py", str(PROJECT_JSON)],
    )
    shot = {"id": "shot03_weapon_clash"}
    early = Image.new("RGBA", (module.W, module.H), (0, 0, 0, 0))
    late = Image.new("RGBA", (module.W, module.H), (0, 0, 0, 0))

    module.draw_cinematic_effects(ImageDraw.Draw(early), shot, t=0.18, duration=6.0)
    module.draw_cinematic_effects(ImageDraw.Draw(late), shot, t=0.82, duration=6.0)

    assert early.getbbox() is not None
    assert late.getbbox() is not None
    assert early.tobytes() != late.tobytes()
```

Also add `from PIL import Image, ImageDraw` at the top of the test file.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_wukong_sample_scripts.py::test_cinematic_effects_change_overlay_pixels_over_time -v
```

Expected: FAIL because `draw_cinematic_effects` does not exist.

- [ ] **Step 3: Implement deterministic effects**

In `render_overlays.py`, add helpers that draw before text:

- `draw_flash` for short white/amber impact pulses.
- `draw_particles` for deterministic sparks/smoke using `math.sin` and `math.cos`.
- `draw_shockwave` for expanding rings around weapon contact.
- `draw_scan_beam` for the heavenly-eye shot.
- `draw_speed_lines` for final-staff and siege shots.
- `draw_clone_shards` for the clone-break shot.

Call `draw_cinematic_effects(draw, shot, t, item["clip"])` near the top of `render_segment`, before top-bar, shot title, and subtitles.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_wukong_sample_scripts.py::test_cinematic_effects_change_overlay_pixels_over_time -v
```

Expected: PASS.

- [ ] **Step 5: Render overlays and inspect dimensions**

Run:

```bash
python3 神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py 神话短剧/孙悟空大战二郎神-样片/project.json
python3 -m pytest tests/test_wukong_sample_scripts.py::test_overlay_frames_exist_after_render tests/test_wukong_sample_scripts.py::test_shot06_overlay_does_not_draw_duplicate_hook -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_wukong_sample_scripts.py 神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py 神话短剧/孙悟空大战二郎神-样片/build/overlays
git commit -m "feat: add cinematic overlay effects"
```

### Task 3: Re-export And Verify

**Files:**
- Modify generated media under `神话短剧/孙悟空大战二郎神-样片/`
- Modify generated QA report files if hashes or screenshots change.

**Interfaces:**
- Consumes: `project.json`, generated overlays, existing audio, existing BGM.
- Produces: `wukong_erlang_sample_vertical.mp4`, `wukong_erlang_sample_final.mp4`, and QA thumbnails.

- [ ] **Step 1: Run full tests before export**

```bash
python3 -m pytest tests/test_wukong_sample_project.py tests/test_wukong_sample_prompts.py tests/test_wukong_sample_scripts.py -v
```

Expected: PASS.

- [ ] **Step 2: Assemble no-BGM video**

```bash
python3 神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py 神话短剧/孙悟空大战二郎神-样片/project.json
```

Expected: writes `wukong_erlang_sample_vertical.mp4` and QA thumbnails.

- [ ] **Step 3: Mix BGM**

```bash
bash 神话短剧/孙悟空大战二郎神-样片/scripts/mix_bgm.sh 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_vertical.mp4 神话短剧/孙悟空大战二郎神-样片/assets/bgm/dark_myth_bgm.wav 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_final.mp4
```

Expected: writes `wukong_erlang_sample_final.mp4`.

- [ ] **Step 4: Verify final export**

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration,nb_frames -of default=noprint_wrappers=1 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_final.mp4
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,duration -of default=noprint_wrappers=1 神话短剧/孙悟空大战二郎神-样片/wukong_erlang_sample_final.mp4
python3 -m pytest tests/test_wukong_sample_project.py tests/test_wukong_sample_prompts.py tests/test_wukong_sample_scripts.py -v
```

Expected: video is 1080x1920, 30 fps, about 30 seconds, AAC audio exists, and tests PASS.

- [ ] **Step 5: Commit**

```bash
git add 神话短剧/孙悟空大战二郎神-样片
git commit -m "chore: export strong-motion wukong sample"
```
