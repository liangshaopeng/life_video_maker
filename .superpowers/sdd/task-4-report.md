status: complete
commit_hashes: 7760b4e
test_summary: python3 -m pytest tests/test_wukong_sample_scripts.py tests/test_wukong_sample_project.py -v -> 15 passed
concerns: none

## Fix Review Findings

Resolved the shot-based narration timing issue in `神话短剧/孙悟空大战二郎神-样片/scripts/make_narration.py` so timeline clip lengths now use `shot["duration"]` when present, while legacy `segments` projects still fall back to `audio + PAD`.

Verification:
- `cd 神话短剧/孙悟空大战二郎神-样片 && python3 scripts/make_narration.py project.json` -> regenerated `build/timeline.json`, audio, and subtitles; total duration now `30.00s`
- `python3 -m pytest tests/test_wukong_sample_scripts.py tests/test_wukong_sample_project.py -v` -> `16 passed`
- `python3 神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py 神话短剧/孙悟空大战二郎神-样片/project.json` -> `OK: assets ready`
