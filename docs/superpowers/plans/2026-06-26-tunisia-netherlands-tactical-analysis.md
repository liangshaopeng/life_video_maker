# Tunisia Netherlands Tactical Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a vertical Chinese tactical-analysis video from the FOX Sports Tunisia vs Netherlands 829-second extended highlights.

**Architecture:** Create a new isolated video project under `战术解析视频/突尼斯-荷兰/` by copying the proven vertical tactical pipeline from `战术解析视频/突尼斯-日本/`. Use YouTube English auto captions as the factual map, then drive the whole video through `project.json`: narration, overlay frames, vertical clip assembly, BGM mix, and goal-wall verification.

**Tech Stack:** Python 3.9, `python3 -m yt_dlp`, `edge-tts`, Pillow, ffmpeg/ffprobe, local tactical scripts (`deroll_vtt.py`, `make_narration.py`, `render_overlays_v.py`, `assemble_v.py`, `verify_goals.py`, `mix_bgm.sh`).

## Global Constraints

- Source URL: `https://www.youtube.com/watch?v=o0AmHN-XnOs`
- Observed source title: `Tunisia vs Netherlands Extended Highlights | 2026 FIFA World Cup`
- Observed source duration: 829 seconds
- Output format: 1080x1920 vertical, match footage in the center band, blurred fill, burned captions, overlay panels, watermark, narration, and BGM ducking.
- Project directory: `战术解析视频/突尼斯-荷兰/`
- Keep claims tied to visible highlights; do not imply this is a full 90-minute tactical review.
- Always de-roll English auto captions before writing the Chinese script.
- Each goal segment must visibly show the scoring action, not only celebration or a distant replay.
- Use fluent Chinese narration; avoid breaking player names or action phrases with excessive punctuation.
- Do not modify unrelated dirty workspace files.

---

## File Structure

- Create: `战术解析视频/突尼斯-荷兰/project.json`
  - Owns the whole video timeline, Chinese narration, source clip starts, overlay text, names protected from subtitle splitting, theme, output name, and factual `_note`.
- Create: `战术解析视频/突尼斯-荷兰/build/commentary_clean.txt`
  - De-rolled English commentary used as the factual event map.
- Create: `战术解析视频/突尼斯-荷兰/build/event_map.md`
  - Human-readable event map: lineups, goals, major chances, candidate footage starts, and selected tactical mechanism per event.
- Create: `战术解析视频/突尼斯-荷兰/footage/tun_ned.mp4`
  - Downloaded 829-second FOX Sports source video.
- Create by copying from template: `战术解析视频/突尼斯-荷兰/deroll_vtt.py`, `make_narration.py`, `render_overlays_v.py`, `lib_overlays_v.py`, `assemble_v.py`, `mix_bgm.sh`, `make_watermark.py`, `add_watermark.sh`
  - Keep the known-good vertical pipeline close to the project, matching existing repo convention.
- Create by copying from `战术解析视频/葡萄牙-乌兹别克斯坦/verify_goals.py`: `战术解析视频/突尼斯-荷兰/verify_goals.py`
  - Produces `build/gverify/WALL_goals.png`.
- Create: `战术解析视频/突尼斯-荷兰/build/subs/*.srt`, `build/audio/*.mp3`, `build/overlays/`, `build/clips/`, `build/timeline.json`
  - Generated intermediates.
- Create: `战术解析视频/突尼斯-荷兰/tun-ned-tactics_vertical.mp4`
  - Pure narration vertical output without BGM.
- Create: `战术解析视频/突尼斯-荷兰/tun-ned-tactics_final.mp4`
  - BGM-mixed final output.

---

### Task 1: Scaffold The Project Directory And Tools

**Files:**
- Create: `战术解析视频/突尼斯-荷兰/`
- Create by copy: `战术解析视频/突尼斯-荷兰/deroll_vtt.py`
- Create by copy: `战术解析视频/突尼斯-荷兰/make_narration.py`
- Create by copy: `战术解析视频/突尼斯-荷兰/render_overlays_v.py`
- Create by copy: `战术解析视频/突尼斯-荷兰/lib_overlays_v.py`
- Create by copy: `战术解析视频/突尼斯-荷兰/assemble_v.py`
- Create by copy: `战术解析视频/突尼斯-荷兰/mix_bgm.sh`
- Create by copy: `战术解析视频/突尼斯-荷兰/make_watermark.py`
- Create by copy: `战术解析视频/突尼斯-荷兰/add_watermark.sh`
- Create by copy: `战术解析视频/突尼斯-荷兰/verify_goals.py`
- Create directories: `战术解析视频/突尼斯-荷兰/build/`, `战术解析视频/突尼斯-荷兰/footage/`, `战术解析视频/突尼斯-荷兰/bgm/`

**Interfaces:**
- Consumes: Existing template scripts from `战术解析视频/突尼斯-日本/` and `战术解析视频/葡萄牙-乌兹别克斯坦/`.
- Produces: A runnable project shell that later tasks can use from inside `战术解析视频/突尼斯-荷兰/`.

- [ ] **Step 1: Create the project folders**

```bash
mkdir -p '战术解析视频/突尼斯-荷兰/build' '战术解析视频/突尼斯-荷兰/footage' '战术解析视频/突尼斯-荷兰/bgm'
```

Expected: command exits with status 0.

- [ ] **Step 2: Copy the known-good vertical tactical scripts**

```bash
cp '战术解析视频/突尼斯-日本/deroll_vtt.py' '战术解析视频/突尼斯-荷兰/deroll_vtt.py'
cp '战术解析视频/突尼斯-日本/make_narration.py' '战术解析视频/突尼斯-荷兰/make_narration.py'
cp '战术解析视频/突尼斯-日本/render_overlays_v.py' '战术解析视频/突尼斯-荷兰/render_overlays_v.py'
cp '战术解析视频/突尼斯-日本/lib_overlays_v.py' '战术解析视频/突尼斯-荷兰/lib_overlays_v.py'
cp '战术解析视频/突尼斯-日本/assemble_v.py' '战术解析视频/突尼斯-荷兰/assemble_v.py'
cp '战术解析视频/突尼斯-日本/mix_bgm.sh' '战术解析视频/突尼斯-荷兰/mix_bgm.sh'
cp '战术解析视频/突尼斯-日本/make_watermark.py' '战术解析视频/突尼斯-荷兰/make_watermark.py'
cp '战术解析视频/突尼斯-日本/add_watermark.sh' '战术解析视频/突尼斯-荷兰/add_watermark.sh'
cp '战术解析视频/葡萄牙-乌兹别克斯坦/verify_goals.py' '战术解析视频/突尼斯-荷兰/verify_goals.py'
chmod +x '战术解析视频/突尼斯-荷兰/mix_bgm.sh' '战术解析视频/突尼斯-荷兰/add_watermark.sh'
```

Expected: all destination files exist.

- [ ] **Step 3: Verify copied tools are present**

```bash
find '战术解析视频/突尼斯-荷兰' -maxdepth 1 -type f | sort
```

Expected output includes `assemble_v.py`, `deroll_vtt.py`, `make_narration.py`, `render_overlays_v.py`, `verify_goals.py`, and `mix_bgm.sh`.

- [ ] **Step 4: Commit the scaffold**

```bash
git add '战术解析视频/突尼斯-荷兰'
git commit -m "feat: scaffold tunisia netherlands tactical video"
```

Expected: commit succeeds and includes only the new project scaffold.

---

### Task 2: Download Captions And Build The Event Map

**Files:**
- Create: `战术解析视频/突尼斯-荷兰/build/o0AmHN-XnOs.en.vtt`
- Create: `战术解析视频/突尼斯-荷兰/build/commentary_clean.txt`
- Create: `战术解析视频/突尼斯-荷兰/build/event_map.md`

**Interfaces:**
- Consumes: `战术解析视频/突尼斯-荷兰/deroll_vtt.py`
- Produces: Event timestamps and tactical labels that `project.json` will encode in `_note` and segment `footage.start` fields.

- [ ] **Step 1: Download English auto captions only**

Run from the new project directory:

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 -m yt_dlp --write-auto-subs --sub-langs 'en.*' --skip-download --extractor-args 'youtube:player_client=tv_embedded,web_embedded,android_vr,mweb' -o 'build/o0AmHN-XnOs.%(ext)s' 'https://www.youtube.com/watch?v=o0AmHN-XnOs'
```

Expected: a file matching `build/o0AmHN-XnOs*.en*.vtt` exists.

- [ ] **Step 2: Normalize the downloaded VTT filename**

```bash
cd '战术解析视频/突尼斯-荷兰'
ls build/*en*.vtt
cp "$(ls build/*en*.vtt | head -n 1)" build/o0AmHN-XnOs.en.vtt
```

Expected: `build/o0AmHN-XnOs.en.vtt` exists.

- [ ] **Step 3: De-roll the auto captions**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 deroll_vtt.py build/o0AmHN-XnOs.en.vtt > build/commentary_clean.txt
sed -n '1,220p' build/commentary_clean.txt
```

Expected: clean timestamped English commentary lines with no rolling duplication.

- [ ] **Step 4: Write the event map**

Read all of `build/commentary_clean.txt`, then create `build/event_map.md` with this exact structure:

```markdown
# Tunisia vs Netherlands Event Map

Source: https://www.youtube.com/watch?v=o0AmHN-XnOs
Duration: 829 seconds

## Thesis

Netherlands repeatedly used width, timing, and off-ball runs to open Tunisia, based only on the visible FOX extended highlights.

## Confirmed Lineups And Shapes

- Netherlands:
- Tunisia:

## Goals And Major Chances

| Event | Clean-commentary time | Candidate footage start | Scorer / chance | Mechanism | Notes for footage |
|---|---:|---:|---|---|---|
| G1 | 00:00 | 0.0 |  |  |  |

## Segment Plan

| Segment id | Purpose | Footage start | Speed | Tactical point |
|---|---|---:|---:|---|
| hook | Thesis opener | 0.0 | 1.0 | Width and timing |
```

Replace the sample row values with the confirmed timestamps, scorers, mechanisms, and notes found in the commentary.

- [ ] **Step 5: Verify event map has no empty tactical rows**

```bash
cd '战术解析视频/突尼斯-荷兰'
rg -n '\| G[0-9].*\|\s*\|\s*\|' build/event_map.md && exit 1 || true
```

Expected: command exits 0, meaning no goal row has consecutive empty cells.

- [ ] **Step 6: Commit captions and event map**

```bash
git add '战术解析视频/突尼斯-荷兰/build/o0AmHN-XnOs.en.vtt' '战术解析视频/突尼斯-荷兰/build/commentary_clean.txt' '战术解析视频/突尼斯-荷兰/build/event_map.md'
git commit -m "feat: map tunisia netherlands tactical events"
```

Expected: commit succeeds with caption map artifacts.

---

### Task 3: Download Footage And Confirm Visual Timestamps

**Files:**
- Create: `战术解析视频/突尼斯-荷兰/footage/tun_ned.mp4`
- Create: `战术解析视频/突尼斯-荷兰/build/verify/*.jpg`
- Modify: `战术解析视频/突尼斯-荷兰/build/event_map.md`

**Interfaces:**
- Consumes: Candidate timestamps from `build/event_map.md`.
- Produces: Frame-confirmed `footage.start` values for `project.json`.

- [ ] **Step 1: Download the source video**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 -m yt_dlp -f 'bv*[height<=720]+ba/b[height<=720]/best[height<=720]' --merge-output-format mp4 --extractor-args 'youtube:player_client=tv_embedded,web_embedded,android_vr,mweb' -o 'footage/tun_ned.%(ext)s' 'https://www.youtube.com/watch?v=o0AmHN-XnOs'
```

Expected: `footage/tun_ned.mp4` exists.

- [ ] **Step 2: Verify source duration**

```bash
cd '战术解析视频/突尼斯-荷兰'
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 footage/tun_ned.mp4
```

Expected: duration is close to `829` seconds.

- [ ] **Step 3: Generate thumbnail walls around each candidate event**

For each candidate event time in `build/event_map.md`, run this command with `<time_minus_8>` replaced by eight seconds before the candidate:

```bash
cd '战术解析视频/突尼斯-荷兰'
mkdir -p build/verify
ffmpeg -y -ss <time_minus_8> -i footage/tun_ned.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 build/verify/<event>_wall.jpg
```

Expected: one wall image per goal or major chance.

- [ ] **Step 4: Inspect walls and update event_map.md**

Open each wall image and adjust `Candidate footage start` and `Notes for footage` so the chosen start captures the described build-up or best close replay. Use absolute starts in seconds.

- [ ] **Step 5: Commit footage timestamp verification artifacts**

```bash
git add '战术解析视频/突尼斯-荷兰/build/event_map.md' '战术解析视频/突尼斯-荷兰/build/verify'
git commit -m "feat: verify tunisia netherlands footage timestamps"
```

Expected: commit succeeds. Do not stage the large `footage/tun_ned.mp4` unless the repository normally tracks footage files for these projects and `git status --short` shows it as intended.

---

### Task 4: Write The Tactical Project Configuration

**Files:**
- Create: `战术解析视频/突尼斯-荷兰/project.json`

**Interfaces:**
- Consumes: `build/event_map.md`, `footage/tun_ned.mp4`, template style from `战术解析视频/突尼斯-日本/project.json`.
- Produces: Full video configuration consumed by narration, overlay, assemble, and verification scripts.

- [ ] **Step 1: Draft project.json**

Create `战术解析视频/突尼斯-荷兰/project.json` with this skeleton, replacing segment text and timestamps with the confirmed event map:

```json
{
  "name": "tun-ned-tactics",
  "output_dir": ".",
  "build_dir": "build",
  "footage_default": "footage/tun_ned.mp4",
  "voice": { "name": "zh-CN-YunjianNeural", "rate": "+24%", "pitch": "+3Hz", "volume": "+12%" },
  "pad": 0.24,
  "caption_maxlen": 16,
  "no_split": ["荷兰", "突尼斯", "范戴克", "德容", "加克波", "邓弗里斯"],
  "grade": "eq=contrast=1.07:saturation=1.16:brightness=-0.01",
  "blur_sigma": 18,
  "theme": { "sky": [96,178,240], "gold": [252,164,52], "navy": [10,16,32], "warn": [244,86,80], "good": [74,210,140], "line": [120,200,255], "chip_text": [14,22,44] },
  "watermark": "思考的我",
  "_note": "Facts and starts are based on build/commentary_clean.txt and build/event_map.md. Source is FOX Sports extended highlights, 829 seconds, not full-match footage.",
  "segments": []
}
```

Add segment objects using the existing pattern:

```json
{
  "id": "g1a",
  "text": "一段完整、顺口、不卡名字的中文解说。",
  "footage": { "start": 0.0, "speed": 1.0 },
  "overlay": {
    "layout": "beat",
    "phase": "拆解·导火索",
    "idx": "G1",
    "accent": "sky",
    "title": "短标题",
    "kicker": "机制说明",
    "points": ["短要点一", "短要点二"]
  }
}
```

- [ ] **Step 2: Validate JSON syntax**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 -m json.tool project.json >/tmp/tun_ned_project_check.json
```

Expected: command exits 0.

- [ ] **Step 3: Check protected names cover all obvious foreign names**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 - <<'PY'
import json
p=json.load(open('project.json',encoding='utf-8'))
print('\n'.join(p.get('no_split',[])))
PY
```

Expected: output includes every player/team/coach name used in `segments[].text`.

- [ ] **Step 4: Commit project.json**

```bash
git add '战术解析视频/突尼斯-荷兰/project.json'
git commit -m "feat: script tunisia netherlands tactical video"
```

Expected: commit succeeds.

---

### Task 5: Generate Narration, Captions, Overlays, And Vertical Assembly

**Files:**
- Create: `战术解析视频/突尼斯-荷兰/build/audio/*.mp3`
- Create: `战术解析视频/突尼斯-荷兰/build/subs/*.srt`
- Create: `战术解析视频/突尼斯-荷兰/build/timeline.json`
- Create: `战术解析视频/突尼斯-荷兰/build/overlays/`
- Create: `战术解析视频/突尼斯-荷兰/build/clips/*.mp4`
- Create: `战术解析视频/突尼斯-荷兰/tun-ned-tactics_vertical.mp4`

**Interfaces:**
- Consumes: `project.json`, `footage/tun_ned.mp4`, local scripts.
- Produces: First complete no-BGM vertical render.

- [ ] **Step 1: Generate narration and subtitles**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 make_narration.py project.json
```

Expected: prints one line per segment and creates `build/timeline.json`.

- [ ] **Step 2: Inspect subtitle fragments**

```bash
cd '战术解析视频/突尼斯-荷兰'
for f in build/subs/seg*.srt; do echo "=== $f"; sed -n '1,80p' "$f"; done
```

Expected: no foreign names split across lines, no isolated one-character subtitle fragments, and narration reads smoothly.

- [ ] **Step 3: Render overlays**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 render_overlays_v.py project.json
```

Expected: creates `build/overlays/seg*/0001.png` files.

- [ ] **Step 4: Assemble the vertical no-BGM video**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 assemble_v.py project.json
```

Expected: creates `tun-ned-tactics_vertical.mp4`.

- [ ] **Step 5: Verify output duration**

```bash
cd '战术解析视频/突尼斯-荷兰'
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 tun-ned-tactics_vertical.mp4
```

Expected: duration is close to the `total` field in `build/timeline.json`.

---

### Task 6: Verify Goal Alignment And Iterate Starts

**Files:**
- Create: `战术解析视频/突尼斯-荷兰/build/gverify/WALL_goals.png`
- Modify if needed: `战术解析视频/突尼斯-荷兰/project.json`
- Recreate if needed: `战术解析视频/突尼斯-荷兰/tun-ned-tactics_vertical.mp4`

**Interfaces:**
- Consumes: assembled clips in `build/clips/`.
- Produces: verified footage starts where each goal row visibly contains the scoring action.

- [ ] **Step 1: Generate the goal verification wall**

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 verify_goals.py project.json
```

Expected: creates `build/gverify/WALL_goals.png`.

- [ ] **Step 2: Inspect every goal row**

Open `战术解析视频/突尼斯-荷兰/build/gverify/WALL_goals.png`. For every goal row, answer: does this row show the scoring process from action to ball entering the net?

Expected: every goal row passes. If a row shows only celebration, a distant dead frame, or the wrong sequence, edit only that segment's `footage.start` and/or `footage.speed` in `project.json`.

- [ ] **Step 3: Reassemble after footage-only edits**

If `footage.start` or `footage.speed` changed, rerun:

```bash
cd '战术解析视频/突尼斯-荷兰'
python3 assemble_v.py project.json
python3 verify_goals.py project.json
```

Expected: updated `WALL_goals.png` passes every goal row.

- [ ] **Step 4: Commit verified configuration and wall**

```bash
git add '战术解析视频/突尼斯-荷兰/project.json' '战术解析视频/突尼斯-荷兰/build/gverify'
git commit -m "fix: align tunisia netherlands goal footage"
```

Expected: commit succeeds after all goal rows pass.

---

### Task 7: Mix BGM And Final QA

**Files:**
- Create or reuse: `战术解析视频/突尼斯-荷兰/bgm/static_bed.mp3`
- Create: `战术解析视频/突尼斯-荷兰/tun-ned-tactics_final.mp4`

**Interfaces:**
- Consumes: verified `tun-ned-tactics_vertical.mp4`.
- Produces: final BGM-mixed video.

- [ ] **Step 1: Provide or copy a BGM bed**

If `bgm/static_bed.mp3` is not already present in the new project, copy the known bed from an existing tactical project:

```bash
cp '战术解析视频/荷兰-瑞典/bgm/static_bed.mp3' '战术解析视频/突尼斯-荷兰/bgm/static_bed.mp3'
```

Expected: `战术解析视频/突尼斯-荷兰/bgm/static_bed.mp3` exists.

- [ ] **Step 2: Mix BGM with narration ducking**

```bash
cd '战术解析视频/突尼斯-荷兰'
bash mix_bgm.sh tun-ned-tactics_vertical.mp4 bgm/static_bed.mp3 tun-ned-tactics_final.mp4 0 0.18
```

Expected: creates `tun-ned-tactics_final.mp4`.

- [ ] **Step 3: Check final technical metadata**

```bash
cd '战术解析视频/突尼斯-荷兰'
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of default=nk=1:nw=1 tun-ned-tactics_final.mp4
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 tun-ned-tactics_final.mp4
```

Expected: width `1080`, height `1920`, frame rate `30/1` or equivalent, and duration close to the no-BGM render.

- [ ] **Step 4: Final visual/audio spot checks**

Run this command to generate a final contact sheet:

```bash
cd '战术解析视频/突尼斯-荷兰'
ffmpeg -y -i tun-ned-tactics_final.mp4 -vf "fps=1/10,scale=216:-1,tile=5x4" -frames:v 1 build/final_contact.jpg
```

Open `build/final_contact.jpg` and check that text is not overlapping, the center band is filled, and the video is not blank.

- [ ] **Step 5: Commit final artifacts**

```bash
git add '战术解析视频/突尼斯-荷兰/project.json' '战术解析视频/突尼斯-荷兰/build/event_map.md' '战术解析视频/突尼斯-荷兰/build/gverify' '战术解析视频/突尼斯-荷兰/build/final_contact.jpg'
git commit -m "feat: complete tunisia netherlands tactical analysis video"
```

Expected: commit succeeds with lightweight verification/config artifacts. Large video files may remain untracked unless the repository convention for this workspace is to track final media.

---

## Self-Review

- Spec coverage: This plan covers source handling, the 829-second highlights constraint, project directory creation, English-caption de-roll, event mapping, `project.json`, narration, overlays, vertical assembly, BGM, subtitle inspection, and goal-wall verification.
- Placeholder scan: The plan intentionally contains replaceable command parameters only where the implementer must use values discovered from `event_map.md`, such as `<time_minus_8>` and `<event>` for thumbnail-wall generation. These are not unknown design requirements; they are loop variables derived during execution.
- Type and interface consistency: The produced files match the scripts' existing interfaces: `project.json` feeds `make_narration.py`, `render_overlays_v.py`, `assemble_v.py`, and `verify_goals.py`; `build/timeline.json` is produced before assembly and goal verification.
- Scope check: The plan produces one tactical short video from one source URL and does not add new reusable code or unrelated refactors.
