# 佛得角世界杯快评专题交付说明

## Final Render

- File: `renders/cape-verde-final.mp4`
- Format: horizontal 16:9, 1920x1080, 30fps
- Duration: 225.02 seconds
- Audio: faster Chinese male narration + locally generated BGM
- Size: 349,057,006 bytes

## Revision Focus

- Recut from a slower 5+ minute documentary tone into a 3:45 sports-feature commentary.
- Rewrote narration with sharper claims: small country survival logic, diaspora player network, three-draw tournament math, Argentina pressure transfer.
- Rebuilt visuals as clear primary video cuts: 8 scene clips are preassembled into `assets/footage/clips/main-cut.mp4`, then overlaid with title/data/caption layers.
- Replaced generated fallback textures with real higher-resolution footage where possible, including live Morna performance and 1080p football/fan clips.
- Generated captions from Edge TTS VTT timing, capped at 22 characters for faster narration.

## Footage Sources

See `assets/footage/manifest.json` for clip-level source URLs and notes.

- YouTube travel/island footage: `https://www.youtube.com/watch?v=n518CDsVG4w`
- YouTube DW Cabo Verde tourism/economy footage: `https://www.youtube.com/watch?v=4wjlZ_RKHk8`
- YouTube football underdog footage: `https://www.youtube.com/watch?v=JreiAoc6HFk`
- YouTube fan celebration footage: `https://www.youtube.com/watch?v=GpjhEESO1gI`
- YouTube Morna live performance footage: `https://www.youtube.com/watch?v=R_o9oekNf7c`

Before publishing publicly, review usage rights for YouTube-derived footage against the target platform policy.

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
- Euronews: Pico Lopes and LinkedIn recruitment context
  `https://www.euronews.com/2026/06/16/who-is-pico-lopes-the-unlikely-cape-verde-world-cup-hero-recruited-through-linkedin`

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

- Data: 8 scenes, 92 captions, 10 sources
- Assets: 9 footage assets
- HyperFrames lint: 0 errors, 0 warnings
- HyperFrames inspect: 0 layout issues across 15 samples
- Render: 225.02s, 1920x1080, 1 audio stream
- Visual QA: contact sheet and full-resolution samples generated in `renders/`
