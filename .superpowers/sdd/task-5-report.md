status: complete
commit_hashes: c724e7385621ff37f523981cdd861bd47166e2c6
test_summary: python3 -m pytest tests/test_wukong_sample_scripts.py -v (10 passed)
concerns: none

## Fix Review Findings

- Updated `parse_srt(path)` in `神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py` to raise `FileNotFoundError` or `ValueError` for missing, empty, malformed, or cue-less subtitle files.
- Preserved multi-line cue text by joining cue lines with `\n`.
- Added direct parser tests in `tests/test_wukong_sample_scripts.py` for missing-file failure and multi-line cue preservation.

Tests run:
- `cd 神话短剧/孙悟空大战二郎神-样片 && python3 scripts/render_overlays.py project.json` - passed, regenerated overlays.
- `python3 -m pytest tests/test_wukong_sample_scripts.py -v` - passed, 12/12 tests.
