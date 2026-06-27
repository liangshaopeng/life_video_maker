Status: DONE

Commit: 83afddb

Tests: python3 -m pytest tests/test_wukong_sample_project.py -v -> 3 passed

Concerns: None

## Fix Review Findings

Status: DONE

Tests run:
- python3 -m pytest tests/test_wukong_sample_project.py -v -> 6 passed
- python3 神话短剧/孙悟空大战二郎神-样片/scripts/validate_project.py 神话短剧/孙悟空大战二郎神-样片/project.json -> OK

Results:
- Added root-bound path validation for shot `prompt`/`keyframe` and project `bgm`, `final_no_bgm`, `final_mixed` entries, rejecting absolute paths, `..` traversal, and any resolved path outside project root.
- Enforced strict `motion` schema: must be dict with numeric `zoom_start`, `zoom_end`, `pan_x`, and `pan_y`; numeric range checks for zoom and pan are applied.
- Replaced hard-coded caption length check with project-level `caption_maxlen` (fallback to 14).
