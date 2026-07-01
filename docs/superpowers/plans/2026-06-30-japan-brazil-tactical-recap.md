# Japan Brazil Tactical Recap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce and publish a 4-5 minute vertical Chinese tactical recap for Japan vs Brazil, ending with `关注思考的我，AI看世界！`.

**Architecture:** Reuse the established vertical football tactical-analysis pipeline from `战术解析视频/突尼斯-日本`. Create a new `战术解析视频/日本-巴西` project, download FOX highlights and captions, de-roll commentary into an event map, write `project.json`, render narration/overlays/video, verify every goal, then upload to Xiaohongshu.

**Tech Stack:** `yt-dlp`, `ffmpeg/ffprobe`, Python scripts copied from the existing tactical projects, `edge-tts`, Pillow overlay rendering, Chrome browser automation for Xiaohongshu.

## Global Constraints

- Use official or high-quality FOX Sports highlights from `https://www.youtube.com/@foxsports/videos`.
- Final format: 1080x1920 vertical, 30fps.
- Target length: 4-5 minutes unless source limitations require a tighter cut.
- Style: neutral professional recap, tactical chess framing plus per-play mechanism breakdown.
- Must de-roll English commentary before final narration.
- Must verify every goal segment shows the scoring process, not only celebration.
- Final narration and visible caption must end exactly with `关注思考的我，AI看世界！`.
- User authorized direct Xiaohongshu publishing after successful verification.

---

### Task 1: Create Project And Download Sources

**Files:**
- Create: `战术解析视频/日本-巴西/`
- Copy: tactical scripts from `战术解析视频/突尼斯-日本/`
- Create: `战术解析视频/日本-巴西/prep-notes.md`

**Interfaces:**
- Consumes: FOX video IDs found from the channel scan.
- Produces: source MP4 files and VTT captions for event mapping.

- [ ] **Step 1: Create project directory and copy scripts**

Run:

```bash
mkdir -p "战术解析视频/日本-巴西/footage" "战术解析视频/日本-巴西/build"
cp 战术解析视频/突尼斯-日本/{add_watermark.sh,assemble_v.py,deroll_vtt.py,lib_overlays_v.py,make_narration.py,make_watermark.py,mix_bgm.sh,render_overlays_v.py} "战术解析视频/日本-巴西/"
cp -R 战术解析视频/突尼斯-日本/bgm "战术解析视频/日本-巴西/"
```

Expected: the new directory contains the vertical tactical scripts.

- [ ] **Step 2: Inspect FOX metadata and subtitles**

Run:

```bash
python3 -m yt_dlp --list-subs "https://www.youtube.com/watch?v=QgUSOlN0Tt0"
python3 -m yt_dlp --print "%(title)s || %(duration_string)s || %(webpage_url)s" "https://www.youtube.com/watch?v=QgUSOlN0Tt0"
```

Expected: the main highlights metadata is available, with English captions or auto captions if YouTube provides them.

- [ ] **Step 3: Download captions and video**

Run:

```bash
cd "战术解析视频/日本-巴西"
python3 -m yt_dlp --write-auto-subs --sub-langs "en.*" --skip-download --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -o "build/%(id)s.%(ext)s" "https://www.youtube.com/watch?v=QgUSOlN0Tt0"
python3 -m yt_dlp -f "bv*[height<=1080]+ba/b[height<=1080]/best" --merge-output-format mp4 --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -o "footage/bra_jpn.%(ext)s" "https://www.youtube.com/watch?v=QgUSOlN0Tt0"
```

Expected: `build/*.vtt` and `footage/bra_jpn.mp4` exist.

### Task 2: Build Event Map

**Files:**
- Create: `战术解析视频/日本-巴西/build/commentary_clean.txt`
- Create: `战术解析视频/日本-巴西/build/event_map.md`

**Interfaces:**
- Consumes: VTT captions and source MP4.
- Produces: confirmed event timestamps used by `project.json`.

- [ ] **Step 1: De-roll captions**

Run:

```bash
cd "战术解析视频/日本-巴西"
python3 deroll_vtt.py build/*.vtt > build/commentary_clean.txt
```

Expected: `build/commentary_clean.txt` contains readable timestamped commentary.

- [ ] **Step 2: Map goals and key chances**

Run frame walls around likely events:

```bash
ffmpeg -ss 0 -i footage/bra_jpn.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 build/wall_000.png
ffmpeg -ss 60 -i footage/bra_jpn.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 build/wall_060.png
ffmpeg -ss 120 -i footage/bra_jpn.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 build/wall_120.png
ffmpeg -ss 180 -i footage/bra_jpn.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 build/wall_180.png
```

Expected: wall images identify lineup, Japan goal, Casemiro goal, Martinelli goal, and any major replay windows.

- [ ] **Step 3: Write `event_map.md`**

Record:

```markdown
# Brazil vs Japan Event Map

- Source:
- Final score:
- Tactical spine:
- G1 Japan:
- G2 Brazil:
- G3 Brazil:
- Key adjustment:
- Closing slogan:
```

Expected: the event map contains timestamps, scorers, mechanisms, and replay starts.

### Task 3: Write Project Configuration

**Files:**
- Create: `战术解析视频/日本-巴西/project.json`

**Interfaces:**
- Consumes: event map and source video.
- Produces: renderable tactical video configuration.

- [ ] **Step 1: Write `project.json`**

Use:

- `name`: `bra-jpn-tactical-recap`
- `footage_default`: `footage/bra_jpn.mp4`
- `voice`: `zh-CN-YunjianNeural`, `rate +20%`, `pitch +3Hz`, `volume +12%`
- `caption_maxlen`: `16`
- `watermark`: `思考的我`
- `segments`: hook, setup_jpn, setup_bra, phase_one, each goal pair, adjustment, ending.

Expected: every segment has `text`, `footage`, and `overlay`.

- [ ] **Step 2: Validate JSON**

Run:

```bash
cd "战术解析视频/日本-巴西"
python3 -m json.tool project.json >/tmp/bra_jpn_project_check.json
```

Expected: command exits 0.

### Task 4: Render And Verify Video

**Files:**
- Create: `战术解析视频/日本-巴西/bra-jpn-tactical-recap_vertical.mp4`
- Create: `战术解析视频/日本-巴西/bra-jpn-tactical-recap_final.mp4`
- Create: `战术解析视频/日本-巴西/build/gverify/WALL_goals.png`

**Interfaces:**
- Consumes: `project.json`, source MP4, BGM.
- Produces: final video ready for publishing.

- [ ] **Step 1: Generate narration and captions**

Run:

```bash
cd "战术解析视频/日本-巴西"
python3 make_narration.py project.json
```

Expected: `build/audio`, `build/subs`, and `build/timeline.json` are created.

- [ ] **Step 2: Render overlays and assemble**

Run:

```bash
cd "战术解析视频/日本-巴西"
python3 render_overlays_v.py project.json
python3 assemble_v.py project.json
```

Expected: `bra-jpn-tactical-recap_vertical.mp4` exists.

- [ ] **Step 3: Mix BGM**

Run:

```bash
cd "战术解析视频/日本-巴西"
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 bra-jpn-tactical-recap_vertical.mp4
bash mix_bgm.sh bra-jpn-tactical-recap_vertical.mp4 bgm/taiko_sengoshin.mp3 bra-jpn-tactical-recap_final.mp4 0 0.18
```

Expected: `bra-jpn-tactical-recap_final.mp4` exists.

- [ ] **Step 4: Verify goals, subtitles, and format**

Run:

```bash
cd "战术解析视频/日本-巴西"
python3 verify_goals.py project.json
rg "关注思考的我，AI看世界" build/subs
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of default=nk=1:nw=1 bra-jpn-tactical-recap_final.mp4
```

Expected: every goal row visibly shows the scoring process, the slogan appears in subtitles, and video is 1080x1920 at 30fps.

### Task 5: Publish To Xiaohongshu

**Files:**
- Use: `战术解析视频/日本-巴西/bra-jpn-tactical-recap_final.mp4`

**Interfaces:**
- Consumes: final verified video.
- Produces: published Xiaohongshu post or a clear blocker.

- [ ] **Step 1: Prepare post copy**

Create title/body/tags in `prep-notes.md`.

Expected: title, body, and hashtags are ready.

- [ ] **Step 2: Upload and publish**

Open `https://creator.xiaohongshu.com/publish/publish?source=official` in logged-in Chrome, upload the final MP4, fill title/body/tags, select normal required fields, and publish.

Expected: post publishes successfully, or execution stops only for login, verification, upload failure, or platform blocking.
