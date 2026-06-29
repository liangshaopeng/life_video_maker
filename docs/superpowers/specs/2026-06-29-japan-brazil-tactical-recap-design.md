# Japan vs Brazil Tactical Recap Design

## Goal

Create a 4-5 minute vertical Chinese tactical recap for the 2026 World Cup Round of 32 match between Japan and Brazil.

The video should use the `football-tactical-analysis-video` pipeline: native 1080x1920 vertical output, real match footage in the center band, blurred fill, burned Chinese captions, tactical overlay panels, Chinese narration, watermark, and BGM ducking under narration.

The approved format is a complete recap, not a fast highlight reel. It should combine:

- **Tactical chess framing**: explain the match as a contest between Japan's disciplined collective structure and Brazil's wide individual threat plus Carlo Ancelotti's in-game problem solving.
- **Per-play mechanism breakdown**: for every goal and decisive chance, explain the build-up, the decision point, and the visible finishing action.

Target length: 4-5 minutes. The video may land closer to 5 minutes if the match includes extra time, penalties, or several decisive tactical shifts.

## Approved Creative Direction

Stance: **neutral professional recap**.

Working thesis:

> This is not simply "Brazil's talent against Japan's discipline". The real value of the match is the tactical negotiation: Japan try to keep the game inside a disciplined structure while still threatening through individual quality and transitions; Brazil try to create one-on-ones on the wings, then use Ancelotti's adjustments to attack the spaces Japan's defensive shifts leave behind.

Tone:

- Serious, sharp, and energetic.
- Avoid fan-tribe language, national mockery, or predetermined winner logic.
- Praise both teams when the footage supports it.
- Let the result and event map decide the final emphasis after the match.

## Source And Fact Rules

This design is written before the match has been played. Implementation must not invent match facts from pre-match expectations.

Required source order after the match:

1. Use official or high-quality extended highlights when available.
2. Download the original English captions or commentary subtitles with `yt-dlp`.
3. Run `scripts/deroll_vtt.py` to produce a clean commentary map.
4. Build an event map from the clean commentary before writing final narration.
5. Use frame walls and still checks to confirm each goal, chance, replay, lineup graphic, and substitution moment.

The final `project.json` `_note` must record:

- Final score and whether the match ended in 90 minutes, extra time, or penalties.
- Source video path and caption source.
- Confirmed scorers, assists or pre-assists when identifiable, and key chances.
- Confirmed substitutions or shape changes that support the "Ancelotti adjustment" section.
- Tactical spine selected from real events, not from the pre-match thesis alone.

## Narrative Structure

### 1. Cold Open, 0:00-0:25

Purpose:

- Stop the scroll with the main tactical tension.
- Establish that Japan are not being treated as a passive underdog and Brazil are not being reduced to isolated stars.

Visual priority:

1. A decisive goal or major chance.
2. A lineup or walkout graphic if the broadcast gives a strong visual.
3. A close-up of both teams' key players or coaches if the match starts slowly.

Narration idea:

> 日本和巴西这场球,真正好看的不是强弱,而是解题。日本把阵型距离、二点保护和反击第一脚做到极致;巴西要做的,就是把比赛从棋盘里拉到边路一对一。

### 2. Match Setup And Shapes, 0:25-1:05

Purpose:

- Explain each side's starting plan in one compact pass.
- Give viewers the tactical keys they need before the first breakdown.

Japan points to confirm from footage:

- Defensive block height and compactness.
- How the wide players protect the half-spaces.
- Who carries the first transition pass.
- Whether Japan use a back three, back four, or asymmetric rest-defense shape.

Brazil points to confirm from footage:

- Which wing receives the most isolation.
- How the fullback, number eight, or striker supports the winger.
- Whether Brazil overload one side before switching to the weak side.
- How Ancelotti positions the midfield to protect counters.

Overlay shape:

- `lineup_jpn`: "日本结构" with 1-2 short tactical points.
- `lineup_bra`: "巴西解法" with 1-2 short tactical points.

### 3. First Tactical Phase, 1:05-1:50

Purpose:

- Show the initial balance before the first decisive event.
- Use one or two non-goal sequences if they explain the match's pattern.

Possible patterns:

- Japan force Brazil outside, then protect the box and second ball.
- Brazil pin Japan's wide defender and create a 1v1.
- Japan escape pressure through a clean first pass and immediate forward run.
- Brazil's first pressing adjustment prevents Japan from turning out.

This section should not become generic punditry. Every claim must sit over a visible sequence.

### 4. Goals And Decisive Chances, 1:50-3:45

Purpose:

- Break down every goal and the most important chances with the standard two-part tactical structure.

For each goal:

- `gNa`: `拆解·导火索`, real-time build-up at speed `1.0`.
- `gNb`: `进球`, close replay or best visible finish at speed `0.5` to `0.6`.

For decisive non-goal chances:

- Use a single `beat` segment if it changes the tactical story.
- Include only chances that explain the match: a post, major save, missed overload, transition warning, VAR moment, or penalty incident.

Mechanism labels should be selected after de-roll and frame checks. Likely label pool:

- Japan: compact block, half-space cover, transition first pass, second-ball protection, third-man run, cutback defense, counter-press escape.
- Brazil: wide isolation, overload-to-isolate, weak-side arrival, fullback underlap, winger-to-striker cutback, midfield rest defense, late-box occupation.

The labels must describe what actually happened, not what the preview expected.

### 5. Coaching Adjustments, 3:45-4:35

Purpose:

- Explain the match's key tactical shift after the opening phase.
- Give Ancelotti's in-game deployment a concrete visual basis.
- Include Japan's response if Moriyasu adjusts the block, personnel, or transition route.

Valid adjustment evidence:

- Substitution timing and role changes.
- A winger switching sides or a new wide support pattern.
- A midfield player dropping deeper or arriving higher.
- Fullback height changing.
- Pressing trigger changing.
- Japan changing block height, marking responsibility, or counter route.

If the match has no obvious coaching shift, replace this section with "why the original plan held" and show repeated evidence.

### 6. Ending, 4:35-5:00

Purpose:

- Return to the central thesis and explain why the result happened.
- Keep the conclusion analytical rather than tribal.

Ending logic depends on the result:

- Brazil win: emphasize how Brazil eventually created enough wing/box advantages, and whether Ancelotti's adjustments changed the access points.
- Japan win: emphasize how Japan kept the game in their preferred structure and converted disciplined moments into attacking value.
- Draw decided by penalties: separate the tactical match from the penalty lottery; explain which side controlled more of the repeatable mechanisms before penalties.

## Production Pipeline

Create a new project directory:

`战术解析视频/日本-巴西/`

Use the latest vertical tactical projects as templates:

- Primary template: `战术解析视频/突尼斯-日本/project.json`
- Style reference: `战术解析视频/荷兰-瑞典/project.json`

Expected files:

- `project.json`
- `prep-notes.md` for event mapping and source notes
- `footage/` for downloaded or provided source video
- `build/commentary_clean.txt` after de-roll
- final no-BGM and BGM-mixed vertical videos

Required workflow:

1. Download captions and source footage after the match.
2. Run de-roll before writing any final tactical narration.
3. Build an event map with goals, chances, substitutions, and replay windows.
4. Select the tactical spine from the event map.
5. Write `project.json` with smooth narration and `no_split` names.
6. Run narration, overlay rendering, vertical assembly, and BGM mix.
7. Run full goal verification and subtitle inspection before delivery.

## Script And Caption Rules

Voice settings:

- `zh-CN-YunjianNeural`
- `rate`: `+18%` to `+24%`; use `+20%` if the script is denser than usual.
- `pitch`: around `+3Hz`
- `volume`: around `+12%`
- `caption_maxlen`: `16`

Writing rules:

- Use fluent Chinese sentences; do not break names or actions with excessive punctuation.
- Build excitement through pace and emphasis, not chopped exclamation marks.
- Keep player names in natural Chinese display form and add every recurring name to `no_split`.
- Avoid unsupported claims such as "best in the tournament" unless the narration frames them as pre-match reputation and the source supports it.
- Use neutral labels: "日本", "蓝武士", "巴西", "桑巴军团", "安切洛蒂", "森保一".

Overlay rules:

- `title` for the cold open.
- `beat` for lineup, phase, goal build-up, goal replay, and adjustment segments.
- `end` for the final thesis.
- Keep `points` short: 1-3 lines, about 12 Chinese characters per line.
- Do not use `telestrator` or frame-accurate drawn circles unless a later implementation plan explicitly revives and verifies them.

## Extra Time And Penalties

Because this is a knockout match, the video must handle non-90-minute outcomes.

If the match goes to extra time:

- Keep 90-minute tactical structure first.
- Add only the extra-time event that changes the match or the fatigue pattern.
- Trim earlier non-goal chances if total length exceeds 5 minutes.

If the match goes to penalties:

- Do not turn the tactical video into a penalty montage.
- Use penalties as the ending context.
- Keep the main analysis focused on the repeatable tactical mechanisms before the shootout.

If the match has very few goals:

- Use high-quality chances, pressing traps, wide isolations, and coaching shifts as the main analysis beats.
- Maintain the two-part structure only for actual goals; use compact one-part beats for chances.

## Verification Gates

Completion requires concrete checks:

- `build/commentary_clean.txt` exists and is used for the event map.
- `prep-notes.md` records the confirmed event map and selected tactical spine.
- `project.json` `_note` contains final factual summary and source alignment.
- `python3 scripts/verify_goals.py project.json` is run after assembly.
- Every goal row in `build/gverify/WALL_goals.png` visibly shows the scoring process, not only celebration.
- `build/subs/seg*.srt` is inspected for broken foreign names, awkward fragments, and isolated single characters.
- Opening frame is checked so the first second has a strong match signal.
- Final output is verified as 1080x1920, 30fps, and within the 4-5 minute target unless extra time requires a slightly longer cut.

## Risks And Mitigations

- Risk: The pre-match thesis overpowers the real match.
  - Mitigation: Treat this design as a frame, then let the de-rolled commentary and visible sequences decide the final story.

- Risk: Official highlights omit the build-up needed for tactical analysis.
  - Mitigation: Prefer extended highlights or full-match footage; if unavailable, only analyze visible mechanisms and state less.

- Risk: A low-scoring match leaves too little goal material.
  - Mitigation: Use chances, pressing traps, and coaching adjustments as tactical beats while keeping actual goals in the two-part format.

- Risk: Brazil or Japan player names are mistranslated or split in captions.
  - Mitigation: Check common Chinese names after the final lineups are known and add all recurring names to `no_split`.

- Risk: Goal replay starts on celebration or a distant angle.
  - Mitigation: Prefer close replays for `进球` segments and verify every goal row with the goal wall.

## Approval Criteria

The final video is successful when it feels like a complete tactical recap rather than a highlight dump:

- The viewer understands the main tactical contest between Japan's structure and Brazil's wing/adjustment routes.
- Every goal and decisive chance is explained through visible actions.
- The stance stays neutral and professional.
- Narration is energetic but smooth.
- Captions, overlays, and footage align cleanly.
- The final cut preserves both match drama and tactical clarity across 4-5 minutes.
