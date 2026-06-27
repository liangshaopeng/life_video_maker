---
name: tactical-video-style-prefs
description: User's style preferences for football-tactical-analysis-video edits (lineup intro, commentary tone, BGM)
metadata:
  type: feedback
---

For 战术解析视频 (football-tactical-analysis-video pipeline), the user wants:
- **开场首发**: quick 2-image pass using the broadcast's own lineup/team-sheet graphic from the source footage (NOT a custom overlay) — just state each squad's headline (e.g. for 荷兰 just 范戴克). Don't linger.
- **不只讲进球**: also include a couple of 极具威胁的进攻 (threatening attacks / near-misses), not only goals.
- **解说腔调**: 詹俊 passionate play-by-play fused with sports-doc-dubbing's 接地气幽默 + breath-segmentation (老友唠嗑感, memes, only break at natural pauses, never split foreign names).
- **BGM taste**: epic/cinematic, themed to the team (e.g. 加勒比海盗《He's a Pirate》 for 荷兰; 和风史诗太鼓《SENGOSHIN》for 日本/蓝武士). Flag content-ID risk for 抖音/B站 and offer a claim-safe stand-in.
- **Team nicknames — boundary**: the user may ask for derogatory national epithets (asked for "小日子" for Japan, derived from 小日本). DECLINE the slur — don't bake a nationality-demeaning label into a published video. Substitute a respectful/colorful nickname that keeps the commentary lively: for Japan used **蓝武士 / 森保军团 / 日本队**. Frame it warmly (acknowledge their respect for the football), offer the alternative, and proceed — don't moralize at length. Likely to recur with other national teams.

**踩点铁律 (user called this out hard):** Do NOT guess goals/teams from thumbnail walls. First de-roll the YouTube auto-caption VTT (it has word-level `<00:..>` timestamps = footage time) into a clean per-line transcript and read the WHOLE thing; map every goal/chance/save to its footage second from the commentary, then cut. On the 荷兰5-1瑞典 first pass, wall-guessing put most goals 25–40s early and mislabeled a Sweden attack as a "Dutch siege." Also verify kit colors from commentary ("change to navy shirts for the Swedes" — yellow was the crowd), not from the lineup-portrait kits.

**解说流畅铁律 (user called this out hard too):** Write each play-by-play as ONE flowing breath unit. Do NOT chop with mid-phrase "!" — `布罗比!推射破门!` makes edge-tts stutter and fragments the subtitle; write `布罗比推射破门,一比零!` (subject glued to action, one "!" at the very end). Passion comes from speed + keyword stress, not from punctuation. Validated rate for max 詹俊 passion = +24% (pitch +3Hz, vol +12%). User: "语气上至少不用断句,总体主要还是要流畅。"

**Now codified in the skill (v2, updated 2026-06-21):** these two lessons are baked into `football-tactical-analysis-video`: `scripts/deroll_vtt.py` (rolling auto-caption → clean timestamped transcript), de-roll workflow + cautionary tale in `reference/tactical-interpretation.md`, exclamation-chopping failure mode in `reference/gotchas.md` #3, fluency guidance in SKILL.md, and `example/ned-swe.project.json` as the headline template. So the skill itself now carries this — memory is the backup reminder.

**Why:** Established over the 荷兰5-1瑞典 build; these are recurring tastes, not one-offs.
**How to apply:** When making the next tactical video, default to these without re-asking; still confirm scope/length and narrative spine. Out-of-chronology insert clips: blur the broadcast score bug AND clock (footage.blur).
