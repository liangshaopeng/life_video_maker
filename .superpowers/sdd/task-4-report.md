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

## Fix Review Findings

Updated `神话短剧/孙悟空大战二郎神-样片/scripts/make_narration.py` so the final wrapping path measures visible subtitle width with punctuation included and splits any overlong cue before writing SRT output. Added a regression test that scans the regenerated final subtitle files under `build/subs/` and asserts every caption line stays within `caption_maxlen`.

Verification:
- `cd 神话短剧/孙悟空大战二郎神-样片 && python3 scripts/make_narration.py project.json` -> regenerated subtitles and timeline; total duration remained `30.00s`
- `python3 -m pytest tests/test_wukong_sample_scripts.py tests/test_wukong_sample_project.py -v` -> `17 passed`
- `python3 神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py 神话短剧/孙悟空大战二郎神-样片/project.json` -> `OK: assets ready`
- Direct scan of regenerated final `.srt` files -> no caption line exceeded `14` visible characters

## Cleanup Findings

Task-4 cleanup removed generated `segN_raw.srt` artifacts and broadened subtitle line-length coverage.

Changes:
- `神话短剧/孙悟空大战二郎神-样片/scripts/make_narration.py`: remove `segN_raw.srt` after writing wrapped `segN.srt`.
- `tests/test_wukong_sample_scripts.py`: subtitle line-length test now scans all `build/subs/*.srt` files.

Checks:
- `cd 神话短剧/孙悟空大战二郎神-样片 && python3 scripts/make_narration.py project.json`
  - result: regenerated with wrapped captions and timeline (`总时长(含pad): 30.00s`)
- `python3 -m pytest tests/test_wukong_sample_scripts.py tests/test_wukong_sample_project.py -v`
  - result: `17 passed`
- `python3 神话短剧/孙悟空大战二郎神-样片/scripts/check_assets.py 神话短剧/孙悟空大战二郎神-样片/project.json`
  - result: `OK: assets ready`
- `find 神话短剧/孙悟空大战二郎神-样片/build/subs -name '*_raw.srt' -print`
  - result: no matches
