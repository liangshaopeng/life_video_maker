# France 4-1 Norway Case

Use this reference when recreating the France-Norway narrative style.

## Story Spine

- Expected story: Mbappe vs Haaland.
- Twist: Norway rotated ten players; Haaland and Odegaard did not start.
- Punchline: "抬错音响了。把金球先生的音响抬上来。"
- Proof: Mbappe pressures and creates; Dembele finishes repeatedly; Maignan saves the penalty; Doue scores late.
- Payoff: France is not scary because of one superstar, but because every line has someone who can decide the game.

## Music Design

- Intro: `Haaland Song (Ha Ha Ha)` for the expectation.
- Switch line: `把金球先生的音响抬上来。`
- Main bed after switch: `Attraction / Masazumi Ozawa`.
- In the final case, the switch line started at `00:00:12,600`, so the mix used `12.60`.

## Commentary Lessons

- Do not say "FOX 原话" or "原解说"; use the source commentary only for fact checking.
- The creator voice is allowed to be playful, but the joke must serve the match story.
- Use `Haaland` in TTS text to avoid wrong Chinese tone on "哈".
- Keep the correction "登贝莱第二球是左脚" explicit in both audio and subtitle.
- If the auto SRT splits "兜远角" into `兜远 / 角`, patch `segN.srt` and `global.srt` before overlay rendering.

## Verification Lessons

- User strongly dislikes accelerated footage in this format. Confirm no `"speed"` fields and check assemble logs for `x1.0`.
- Check source quality with `ffprobe`; upgrade to 720p+ when the user complains about clarity.
- Extract punchline frames and corrected-fact frames, not only a generic thumbnail wall.
- Search final project/subtitles for forbidden framing words: `FOX`, `原解说`, `原话`.
