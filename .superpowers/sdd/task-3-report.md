Status: DONE

Commit: c5c17d4

Test summary: `python3 -m pytest tests/test_wukong_sample_scripts.py::test_check_assets_reports_missing_keyframes_before_generation -v` → 1 passed

Concerns: Step 6 positive tests were intentionally not added in this worker because keyframe assets are not generated here (per your scope adjustment).

## Controller Completion

Status: DONE

Tests run:
- python3 -m pytest tests/test_wukong_sample_scripts.py -v -> 3 passed

Results:
- Generated six project-bound keyframes with the built-in image_gen tool.
- Copied processed assets into `神话短剧/孙悟空大战二郎神-样片/assets/keyframes/`.
- Standardized every keyframe to 1080x1920 PNG with ffmpeg.
- Added positive tests for ready keyframes and portrait image dimensions.
- Visually checked a six-frame contact sheet: the heavenly siege, heavenly eye, weapon clash, clone break, final staff strike, and hook frame all map to the intended shot order.

## Fix Review Findings

Changes made:
- Updated `check_keyframes` to require keyframe dimensions `width >= 1080` and `height >= 1920`.
- Updated `check_keyframes` to verify image format is `PNG` via `Image.open(...).format`.
- Added focused negative tests in `tests/test_wukong_sample_scripts.py` for:
  - rejecting a `1080x1440` PNG as too small
  - rejecting a JPEG file with `.png` extension as non-PNG
- Updated existing positive keyframe dimension test to require `height >= 1920`.

Tests run:
- `python3 -m pytest tests/test_wukong_sample_scripts.py -v`

Results:
- 5 passed
