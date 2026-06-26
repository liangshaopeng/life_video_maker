# Tunisia vs Netherlands Tactical Analysis Design

## Goal

Create a vertical Chinese tactical-analysis short video from the FOX Sports YouTube extended highlights:

- Source: `https://www.youtube.com/watch?v=o0AmHN-XnOs`
- Title observed: `Tunisia vs Netherlands Extended Highlights | 2026 FIFA World Cup`
- Duration observed: 829 seconds
- Format: 1080x1920 vertical, with match footage in the center band, blurred fill, burned captions, overlay panels, watermark, narration, and BGM ducking.

The video should feel like the existing `战术解析视频` projects, especially `突尼斯-日本`, `荷兰-瑞典`, and `葡萄牙-乌兹别克斯坦`: energetic Chinese narration, clear tactical labels, and every goal segment aligned to visible goal action.

## Core Angle

Recommended theme: **Netherlands did not simply overpower Tunisia; they repeatedly opened the defense through width, timing, and off-ball movement.**

The video should not become a generic highlight reel. Each important goal or chance should answer one tactical question: why did this chance become available?

Likely mechanism labels, to be confirmed after English-caption de-roll and frame checks:

- Wide overload or right-side/left-side progression
- Half-space penetration
- Cutback or low cross into the scoring lane
- Off-ball run behind a fixed defensive line
- Second-ball or transition punishment

The final labels must be based on the English commentary and verified frames, not guessed from the thumbnail wall.

## Structure

Use the standard tactical pipeline structure:

1. `hook`
   - Introduce the thesis: Netherlands used width and running lanes to pull Tunisia apart.
   - Show an energetic goal or pressure sequence from the highlights.

2. `lineup_ned`
   - Briefly establish Netherlands shape and the attacking reference points.
   - Keep this short unless the source contains a useful lineup graphic.

3. `lineup_tun`
   - Briefly establish Tunisia defensive setup and what they were trying to protect.
   - Avoid overexplaining because the source is highlights, not full match footage.

4. Per-goal tactical pairs
   - For each confirmed Netherlands goal:
     - `gNa`: `拆解·导火索`, real-time build-up at speed `1.0`
     - `gNb`: `进球`, slow-motion or best replay at speed around `0.5` to `0.6`
   - If Tunisia has a goal or major chance, include it only if it helps explain the tactical balance.

5. `ending`
   - Return to the thesis: the result came from repeated attacking routes, not isolated moments.

Target length: around 90 to 150 seconds, depending on the confirmed number of goals and usable replays.

## Production Pipeline

Create a new project directory:

`战术解析视频/突尼斯-荷兰/`

Reuse the mature local tactical-analysis scripts from the latest compatible vertical project. Prefer `战术解析视频/突尼斯-日本/` as the nearest template, then copy in improvements from `战术解析视频/葡萄牙-乌兹别克斯坦/` if needed, especially `verify_goals.py`.

Required steps:

1. Download English auto captions with `python3 -m yt_dlp`.
2. Run `deroll_vtt.py` to create `build/commentary_clean.txt`.
3. Read the clean commentary fully and create an event map with goal/chance timestamps.
4. Download the 829-second highlight video into `footage/`.
5. Use thumbnail walls and still-frame checks to adjust segment starts.
6. Write `project.json` with smooth Chinese narration and `no_split` names.
7. Run narration, overlay rendering, vertical assembly, and BGM mix.
8. Run `verify_goals.py project.json` and inspect every goal row.

## Script And Caption Rules

Narration should follow the existing house style:

- Voice: `zh-CN-YunjianNeural`
- Rate: `+18%` to `+24%`; use `+24%` if the script is compact and energetic.
- Pitch: around `+3Hz`
- Volume: around `+12%`
- Captions: `caption_maxlen: 16`

Writing constraints:

- Use fluent sentences; do not split player names or actions with excessive exclamation marks.
- Use commas for breath, one exclamation mark at the end of a true climax.
- Put all foreign names in `no_split`, using the display spelling that appears in Chinese script.
- Keep overlay `points` short, usually 1 to 3 lines and no more than about 12 Chinese characters per line.

## Verification Gates

Completion requires evidence, not just successful rendering:

- `build/commentary_clean.txt` exists and was used to map the events.
- `project.json` `_note` records the factual map and chosen tactical spine.
- All goal segments are verified with `verify_goals.py`.
- Every goal row must visibly include the scoring action, not only celebration or a distant replay.
- Inspect generated `build/subs/seg*.srt` for broken foreign names or awkward fragments.
- Final output should include a no-BGM vertical file and a BGM-mixed final file.

## Risks And Mitigations

- Risk: The source is extended highlights, not full match footage.
  - Mitigation: Keep the analysis focused on visible attacking sequences and avoid unsupported full-match claims.

- Risk: Auto captions may contain noisy names or repeated rolling text.
  - Mitigation: Always de-roll first, then use the clean commentary as the event map.

- Risk: Goal segment starts can land on celebration or replay filler.
  - Mitigation: Prefer close replay starts for `进球` segments and verify all goals with the wall image.

- Risk: Existing workspace is dirty with unrelated files.
  - Mitigation: Keep this project in a new directory and stage only intentional files.

## Approval Criteria

The result is acceptable when it plays as a tactical short, not a highlight dump: the viewer should understand the repeated attacking mechanism behind the Netherlands goals, the narration should be smooth and energetic, and the footage should visibly match each described action.
