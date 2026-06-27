---
name: narrative-football-analysis-video
description: 'Use when creating a 叙事性足球解析 video from real match footage: Chinese self-owned commentary, a story hook or misdirection, punchline/reversal, music-as-narrative BGM switching, synced subtitles, vertical 9:16 output, and match-event analysis under about 3 minutes. Trigger for requests like "按抖音范例思路做足球解析", "不要强调原解说/FOX", "BGM 有梗", "抬错音响/金球先生音响", "把比赛讲成一个故事". Distinct from pure tactical mechanism breakdowns (football-tactical-analysis-video) and data/highlight ranking edits (sports-highlight-video).'
---

# 叙事性足球解析视频

## Core Idea

Make the match feel like a short story, not a neutral highlight reel. Use real football footage and accurate match facts, but let the commentary sound like the creator's own voice: set an expectation, reveal a twist, ride the best match events, and use BGM changes as part of the joke or emotional turn.

For a concrete example, read `references/france-norway-case.md` when the user asks for a similar "Haaland song -> wrong speaker -> Ballon d'Or speaker -> Attraction" style.

## Choose This Skill

Use this when the user wants:
- A short football video driven by narrative, irony, rivalry, or a running gag.
- Real match footage with key goals/chances, but not a dense tactics-board explanation.
- Chinese commentary that references the match as "my/our" interpretation, not "FOX said" or "the original commentator said".
- BGM design with meaning: intro song, punchline switch, character theme, or emotional pivot.
- Vertical 9:16 output for short-video platforms or private viewing.

Do not use this as the main skill for:
- Pure "how did the goal happen tactically" videos with per-goal mechanism diagrams: use `football-tactical-analysis-video`.
- Pure ranking/data/season recap videos with charts and big stats: use `sports-highlight-video`.

## Narrative Spine

Before writing `project.json`, write the spine in one or two lines:

1. **Expectation**: what the viewer expects before kick-off.
   Example: "姆巴佩对 Haaland, 双神对决."
2. **Reversal**: what breaks that expectation.
   Example: "挪威十人轮换, Haaland 和厄德高都不首发."
3. **Punchline**: the creator's angle.
   Example: "抬错音响了, 把金球先生的音响抬上来."
4. **Proof**: the actual match events that make the story true.
   Example: Mbappe creates pressure, Dembele scores, Maignan saves, Doue finishes.
5. **Payoff**: a final sentence that turns events into a theme.
   Example: "法国最可怕的不是一个人, 而是每条线都有人站出来."

Keep the story honest. Use commentary/transcript only to verify facts and timing; do not make "FOX/original commentary" the on-screen or spoken authority unless the user explicitly asks for that.

## Project Pattern

Use the existing vertical project scripts when present (`make_narration.py`, `render_overlays_v.py`, `assemble_v.py`, `mix_bgm.sh`). If the project needs a two-track BGM switch, use `scripts/mix_two_bgm.sh` from this skill or adapt it into the working video folder.

Recommended config choices:
- Native output: 1080x1920 vertical, real footage band plus blurred background.
- Source quality: prefer at least 720p; verify with `ffprobe`.
- Runtime: aim for 2:00-2:45, hard cap around 3:00 unless user asks otherwise.
- Speed: default all cuts to x1.0. Do not use accelerated footage unless the user explicitly approves it. Slow motion is optional only when it clarifies a goal replay.
- Footage: use `cuts[]` inside a segment when one story beat needs live angle + replay + reaction.
- Captions: `caption_maxlen` around 16, add `no_split` names for foreign players and Latin spellings.

## Commentary Rules

Write in the creator's own口吻:
- Say "我先把..." / "这场最狠的是..." / "问题来了..." when it fits.
- Avoid phrases like "FOX 原话", "原解说说", "原解说强调" in final narration.
- Use outside commentary as fact-checking only.
- Make jokes brief and functional; the joke should explain the edit, not pause the match.
- For TTS pronunciation problems, use Latin spellings when better, such as `Haaland`, and add them to `no_split`.
- Keep sentences fluent. Do not overuse exclamation marks or hard punctuation; TTS rhythm should feel like one wave.

Useful line patterns:
- "开场我先把 X 之歌抬出来, 准备看 A 对 B."
- "结果阵容一亮, B 不首发。抬错音响了。把 Y 的音响抬上来。"
- "这不是一个人的压制, 是整条线都能接管比赛."
- "你知道他要走这一步, 但你就是挡不住."

## Music-As-Narrative

Treat BGM as a storytelling layer:
- Start with the expected character/theme song.
- Switch on the punchline or reversal line, not randomly at the next segment.
- After the switch, keep the new track as the main bed unless another story turn deserves a new cue.
- Use short fades around the switch; keep sidechain ducking so commentary stays clear.

Typical two-track flow:

```bash
bash scripts/mix_two_bgm.sh \
  <vertical.mp4> <intro_theme.mp3> <main_bgm.mp3> <final.mp4> \
  <switch_seconds> 0 0 0.20 0.16
```

Find `switch_seconds` from the generated SRT, not by guessing. For example, if the subtitle line "把金球先生的音响抬上来。" starts at `00:00:12,600`, use `12.60`.

## Build Workflow

1. Research the match and collect/verify footage.
   - Confirm score, starters, scorers, key chances, penalties/saves.
   - Verify source resolution with `ffprobe`; upgrade low-quality footage when possible.
2. Write the narrative spine and segment list.
   - Opening expectation/reversal.
   - Key early signal.
   - Goals/chances/saves as proof.
   - Payoff ending.
3. Write or update `project.json`.
   - Keep every spoken sentence aligned with visible footage.
   - Avoid `speed` fields unless deliberately using slow replay.
4. Generate narration and subtitles.
   ```bash
   python3 make_narration.py project.json
   ```
5. Sweep SRT files.
   - Fix broken phrases like `兜远 / 角`.
   - Keep punchline captions clean.
   - Do not split foreign names or Latin words.
6. Render overlays and assemble.
   ```bash
   python3 render_overlays_v.py project.json
   python3 assemble_v.py project.json
   ```
7. Mix BGM.
   - Use `mix_two_bgm.sh` for narrative music switches.
   - Use `mix_bgm.sh` for one continuous bed.

## Verification Gate

Before saying the video is done, run fresh checks:

```bash
ffprobe -v error -show_entries format=duration,bit_rate \
  -show_entries stream=codec_type,width,height,r_frame_rate,duration,bit_rate,channels \
  -of json <final.mp4>

ffmpeg -hide_banner -nostats -i <final.mp4> -af volumedetect -f null -

rg '"speed"|FOX|原解说|原话' project.json build*/subs/global.srt
```

Also extract and inspect frames:
- Opening hook/title.
- Music-switch punchline.
- Every goal or key chance.
- Any user-corrected fact, such as left/right foot.
- A dense thumbnail wall across the whole video.

Pass criteria:
- Final video is vertical 1080x1920 or intentionally chosen target.
- Source footage is at least the requested quality, usually 720p+.
- Runtime is within the user target.
- No accidental accelerated shots.
- Spoken claim, subtitle, and visible footage match.
- BGM supports the story and does not cover commentary.
