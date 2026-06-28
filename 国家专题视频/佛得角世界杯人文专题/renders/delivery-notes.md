# 佛得角世界杯人文专题交付说明

## Final Render

- File: `renders/cape-verde-final.mp4`
- Format: horizontal 16:9, 1920x1080, 30fps
- Duration: 317.03 seconds
- Audio: Chinese male narration + locally generated documentary BGM
- Size: 210,310,954 bytes

## Story Shape

- Cold open: "佛的脚下凡，挑战世界冠军"
- Scope: geography, culture, development reality, football diaspora, Blue Sharks' World Cup breakthrough, Argentina challenge
- Narration pace: medium, fluent Chinese voiceover

## Footage Sources

See `assets/footage/manifest.json` for clip-level source URLs and notes.

- YouTube travel/island footage: `https://www.youtube.com/watch?v=n518CDsVG4w`
- YouTube DW Cabo Verde tourism/economy footage: `https://www.youtube.com/watch?v=4wjlZ_RKHk8`
- YouTube football underdog footage: `https://www.youtube.com/watch?v=JreiAoc6HFk`
- YouTube fan celebration footage: `https://www.youtube.com/watch?v=GpjhEESO1gI`
- Generated fallback visuals: stadium texture, Fogo volcano texture, Morna culture texture

Before publishing publicly, review usage rights for the YouTube-derived footage against the target platform policy.

## Fact Sources

- Al Jazeera, 2026-06-27: Cape Verde reaching the World Cup Round of 32 and drawing Argentina
  `https://www.aljazeera.com/sports/2026/6/27/cape-verde-qualify-for-world-cup-round-of-32-set-up-date-with-argentina`
- Al Jazeera, 2026-06-28: last-32 schedule context
  `https://www.aljazeera.com/sports/2026/6/28/which-teams-are-in-world-cup-last-32-knockouts-and-what-is-the-schedule`
- FIFA team profile: Cabo Verde football context
  `https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/cabo-verde-team-profile-history`
- UNESCO: Morna, musical practice of Cabo Verde
  `https://ich.unesco.org/en/RL/morna-musical-practice-of-cabo-verde-01469`
- World Bank: Cabo Verde country overview
  `https://www.worldbank.org/ext/en/country/caboverde`
- Visit Cabo Verde: island geography and tourism context
  `https://www.visit-caboverde.com/en/islands`
- World Factbook: country profile
  `https://theworldfactbook.org/country/cabo-verde.html`

## Verification

Run from this project directory:

```bash
npm run verify:data
npm run check:assets
npm run lint
npm run inspect
npm run verify:render
```

Latest verification:

- Data: 6 scenes, 70 captions, 10 sources
- Assets: 7 footage assets
- HyperFrames lint: 0 errors, 0 warnings
- HyperFrames inspect: 0 layout issues across 15 samples
- Render: 317.03s, 1920x1080, 1 audio stream
