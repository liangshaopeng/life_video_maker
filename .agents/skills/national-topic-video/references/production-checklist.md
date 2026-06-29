# National Topic Video Production Checklist

Use this after `national-topic-video` triggers for a real production or a substantial revision.

## Brief

- Aspect ratio: default horizontal 16:9 unless the user asks for vertical.
- Runtime: honor the user target, but avoid padding. A strong 3:30-5:00 video is better than a slow 8:00 one.
- Tone: start with the user's hook, then sharpen into a thesis.
- Output: final MP4 plus source notes and verification evidence.

## Research

- Browse for any current sports/news/economic facts. Do not trust memory for current tournaments, schedules, presidents, rankings, or player status.
- Keep a source list with URL, publisher, date, and why it supports the claim.
- Use primary sources when possible: FIFA/IOC/confederation, World Bank/IMF/UNESCO/CIA Factbook, official tourism or government sites.
- For web video references, record source URL, clip role, downloaded filename, and resolution.

## Story Structure

Use 6-9 scenes. Each scene needs one visible idea and one spoken claim.

1. Hook: meme or surprise, within 8 seconds.
2. Position: where this country sits geographically and strategically.
3. Culture: language, music, migration, food, religion, or identity.
4. Development: how the economy actually works and what pressure it faces.
5. Sports system: player pool, leagues, diaspora, youth pipeline, or tactical identity.
6. Current event: why the topic matters now.
7. Stakes: the next opponent, tournament, policy, market, or social question.
8. Payoff: one sentence that makes the country feel newly legible.

## Narration

- Use a dense Chinese creator voice: short clauses, decisive verbs, and观点句.
- Avoid neutral textbook intros such as "某国位于..." unless immediately turned into an angle.
- For TTS, generate captions from the actual audio timing, then manually scan for broken names and awkward splits.
- If the user says the voice is too slow, tighten text and increase TTS rate; do not only speed up the final video.

## Footage

- Prefer real footage at 1080p or better. Verify with `ffprobe`.
- Use footage as the main image. Avoid low-res clips as blurred wallpaper.
- Cut between different visual categories: aerial/place, street/people, culture, economy, sport, fan emotion.
- If using YouTube material, keep the usage-rights caveat in delivery notes.
- If footage contains watermarks or irrelevant score bugs, crop, blur locally, or choose another clip.

## HyperFrames Build

Recommended scripts:

```json
{
  "captions": "node scripts/generate-captions.mjs",
  "verify:data": "node scripts/verify-story-data.mjs",
  "check:assets": "node scripts/check-assets.mjs",
  "lint": "npx hyperframes lint",
  "inspect": "npx hyperframes inspect --samples 15 --timeout 20000",
  "render:final": "npx hyperframes render --quality high --fps 30 --output renders/<topic>-final.mp4",
  "verify:render": "bash scripts/verify-render.sh renders/<topic>-final.mp4"
}
```

Layout rules:
- Put scene headlines and chips away from captions.
- Use top-center captions when bottom player controls or lower-third overlays would collide.
- Keep caption text under roughly 22 Chinese characters per line for fast commentary.
- Do not let UI cards nest inside other cards. For video overlays, use flat bands, chips, and labels.

## Verification

Run fresh checks before delivery:

```bash
npm run verify:data
npm run check:assets
npm run lint
npm run inspect
npm run render:final
npm run verify:render
```

Extract QA frames:

```bash
ffmpeg -y -ss 00:00:08 -i renders/<topic>-final.mp4 -frames:v 1 renders/frame-hook.jpg
ffmpeg -y -ss 00:00:40 -i renders/<topic>-final.mp4 -frames:v 1 renders/frame-layout.jpg
```

Pass criteria:
- Final video has expected runtime, resolution, and audio stream.
- Captions are readable and not covered by player controls.
- Footage is crisp enough for publishing.
- Scene claims match narration, subtitles, and visible overlays.
- Delivery notes include source URLs, verification results, and usage-rights caveat.

## Common Fixes

- **Subtitle covered by controls:** move captions to top-center safe band and rerender.
- **Video feels blurry:** replace low-resolution sources; use clip switching rather than a blurred background.
- **Too slow:** rewrite narration into shorter claims and raise TTS rate before rendering.
- **Looks like a travel ad:** add development pressure, contradiction, or sports stakes.
- **Too much football:** restore geography/culture/development scenes so the country remains the protagonist.
