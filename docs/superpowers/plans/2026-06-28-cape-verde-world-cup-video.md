# Cape Verde World Cup Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 5-8 minute horizontal HyperFrames video titled "佛的脚下凡，挑战世界冠军" about Cabo Verde's 2026 World Cup knockout run and the country's geography, culture, development, and football rise.

**Architecture:** Create one HyperFrames project under `国家专题视频/佛得角世界杯人文专题/`, with `index.html` as the 1920x1080 source of truth. Keep editorial data in small JavaScript modules, source material in `assets/`, and verification scripts in `scripts/` so each production phase can be checked independently.

**Tech Stack:** HyperFrames CLI `0.7.17`, Node.js `22.22.3`, HTML/CSS/GSAP, FFmpeg/ffprobe, yt-dlp for source collection when available, HyperFrames TTS or Edge TTS fallback for Chinese narration.

## Global Constraints

- Format: 16:9 horizontal, 1920x1080.
- Duration: about 6 minutes, acceptable range 5-8 minutes.
- Language: Chinese narration and burned-in Chinese subtitles.
- Voice: fluent male Chinese voice, medium pace; opening and football sections more energetic, country/culture sections calmer.
- Opening hook: "佛的脚，真的来人间比赛了。一个大西洋上的群岛国家，第一次杀进世界杯淘汰赛。下一站，挑战世界冠军阿根廷。"
- Use the pun only as the opening trigger; shift to documentary authority after the first 20-30 seconds.
- Current football fact snapshot is dated 2026-06-28 and must be re-checked immediately before final render.
- Visual style: Atlantic Epic Sports Dossier.
- Palette: `#061B2E`, `#0B3558`, `#111217`, `#1A4FB3`, `#D71920`, `#F7D117`, `#F6F2E8`, `#E7B84A`.
- Avoid purple/blue tech gradients, decorative orbs, bokeh, long paragraphs on screen, cartoon shark mascots, and long unmodified match broadcasts.
- External footage must be muted unless a short ambient moment is deliberately scripted.
- Multi-scene HyperFrames compositions must use transitions between scenes and entrance animations on every scene.

---

## File Structure

Create this project tree during implementation:

```text
国家专题视频/佛得角世界杯人文专题/
  DESIGN.md
  index.html
  package.json
  hyperframes.json
  data/
    sources.js
    storyboard.js
    captions.js
  scripts/
    narration.txt
    verify-story-data.mjs
    check-assets.mjs
    asset-clips.sh
    make-narration.sh
    verify-render.sh
  assets/
    footage/
      README.md
      manifest.json
      raw/
      clips/
    audio/
      README.md
    images/
      README.md
  renders/
```

Responsibilities:

- `DESIGN.md`: Visual identity required by HyperFrames before composition HTML exists.
- `index.html`: Root composition with timed video, audio, captions, scene graphics, and GSAP timeline.
- `data/sources.js`: Source URLs, source roles, and editorial fact claims.
- `data/storyboard.js`: Scene timings, narration blocks, visual beats, and expected asset IDs.
- `data/captions.js`: Timed caption chunks derived from the narration.
- `scripts/narration.txt`: Full Chinese narration for TTS.
- `scripts/verify-story-data.mjs`: Node checks for scene timing, source IDs, caption timing, and required facts.
- `scripts/check-assets.mjs`: Node checks that the selected footage/audio files exist and can be probed.
- `scripts/asset-clips.sh`: FFmpeg clip extraction into normalized 1920x1080 MP4 assets.
- `scripts/make-narration.sh`: TTS command wrapper and audio duration check.
- `scripts/verify-render.sh`: Final ffprobe checks for duration, video stream, and audio stream.
- `assets/footage/manifest.json`: Local filenames, source URL, role, clip ranges, and license/editorial notes.

---

### Task 1: Scaffold Project And Editorial Data

**Files:**
- Create: `国家专题视频/佛得角世界杯人文专题/package.json`
- Create: `国家专题视频/佛得角世界杯人文专题/hyperframes.json`
- Create: `国家专题视频/佛得角世界杯人文专题/DESIGN.md`
- Create: `国家专题视频/佛得角世界杯人文专题/data/sources.js`
- Create: `国家专题视频/佛得角世界杯人文专题/data/storyboard.js`
- Create: `国家专题视频/佛得角世界杯人文专题/data/captions.js`
- Create: `国家专题视频/佛得角世界杯人文专题/scripts/verify-story-data.mjs`
- Create: `国家专题视频/佛得角世界杯人文专题/assets/footage/README.md`
- Create: `国家专题视频/佛得角世界杯人文专题/assets/audio/README.md`
- Create: `国家专题视频/佛得角世界杯人文专题/assets/images/README.md`
- Create directory: `国家专题视频/佛得角世界杯人文专题/renders/`

**Interfaces:**
- Produces: `sources`, `storyboard`, and `captions` named exports consumed by `index.html` and verification scripts.
- Produces: `npm run verify:data`, `npm run lint`, `npm run inspect`, `npm run render:draft`, and `npm run render:final` commands.

- [ ] **Step 1: Create directories**

Run:

```bash
mkdir -p 国家专题视频/佛得角世界杯人文专题/{data,scripts,assets/footage/raw,assets/footage/clips,assets/audio,assets/images,renders}
```

Expected: command exits with code 0.

- [ ] **Step 2: Create `package.json`**

Create `国家专题视频/佛得角世界杯人文专题/package.json`:

```json
{
  "name": "cape-verde-world-cup-human-interest-video",
  "private": true,
  "type": "module",
  "scripts": {
    "verify:data": "node scripts/verify-story-data.mjs",
    "check:assets": "node scripts/check-assets.mjs",
    "lint": "npx hyperframes lint",
    "inspect": "npx hyperframes inspect --samples 15",
    "preview": "npx hyperframes preview --port 3028",
    "render:draft": "npx hyperframes render --quality draft --output renders/cape-verde-draft.mp4",
    "render:final": "npx hyperframes render --quality high --fps 30 --output renders/cape-verde-final.mp4",
    "verify:render": "bash scripts/verify-render.sh renders/cape-verde-final.mp4"
  }
}
```

- [ ] **Step 3: Create `hyperframes.json`**

Create `国家专题视频/佛得角世界杯人文专题/hyperframes.json`:

```json
{
  "name": "佛得角世界杯人文专题",
  "entry": "index.html"
}
```

- [ ] **Step 4: Create `DESIGN.md`**

Create `国家专题视频/佛得角世界杯人文专题/DESIGN.md`:

```markdown
# Atlantic Epic Sports Dossier

## Style Prompt

Build a cinematic horizontal sports-humanities documentary about Cabo Verde. The surface should feel like a dark Atlantic match dossier: ocean depth, volcanic texture, Cabo Verde flag accents, stadium light, warm documentary inserts, and crisp data panels. The opening can hit hard with oversized kinetic Chinese type, then the middle should breathe with maps, archival-style cards, travel footage, and restrained motion.

## Colors

- Atlantic navy: `#061B2E`
- Deep ocean: `#0B3558`
- Volcanic black: `#111217`
- Cabo Verde blue: `#1A4FB3`
- Flag red: `#D71920`
- Flag yellow: `#F7D117`
- Warm white: `#F6F2E8`
- Data gold: `#E7B84A`

## Typography

- Chinese: `Noto Sans SC`, `Source Han Sans SC`, `Hiragino Sans GB`, sans-serif.
- Latin and numbers: `Inter`, `Arial`, sans-serif.
- Use heavy display weight only for cold-open impact words and chapter cards.

## Motion

- Opening: smash cuts, fast map zoom, flag color wipes, title scale hits.
- Geography: island route lines draw across the Atlantic map.
- Culture: slow parallax, warm lower-thirds, softer dissolves.
- Development: dashboard cards slide and count in cleanly.
- Football: bracket lines, player cards, route maps, and blue shark trace.
- Transitions: ocean-wave wipes, pitch-line reveals, and flag-color slashes.

## What NOT To Do

- Do not use purple tech gradients, decorative orbs, or bokeh blobs.
- Do not make the Blue Sharks motif a cartoon mascot.
- Do not put long paragraphs on screen.
- Do not keep the entire piece in meme mode after the first 30 seconds.
- Do not use long unmodified match broadcasts as the visual backbone.
```

- [ ] **Step 5: Create `data/sources.js`**

Create `国家专题视频/佛得角世界杯人文专题/data/sources.js`:

```js
export const sources = [
  {
    id: "aljazeera-cpv-argentina",
    title: "Cape Verde qualify for World Cup Round of 32, set up date with Argentina",
    publisher: "Al Jazeera",
    date: "2026-06-27",
    url: "https://www.aljazeera.com/sports/2026/6/27/cape-verde-qualify-for-world-cup-round-of-32-set-up-date-with-argentina",
    role: "current-football-fact"
  },
  {
    id: "aljazeera-last32-schedule",
    title: "Which teams are in World Cup last 32 knockouts and what is the schedule?",
    publisher: "Al Jazeera",
    date: "2026-06-28",
    url: "https://www.aljazeera.com/sports/2026/6/28/which-teams-are-in-world-cup-last-32-knockouts-and-what-is-the-schedule",
    role: "current-football-fact"
  },
  {
    id: "olympics-cpv-round32",
    title: "Cabo Verde fairytale continues as Blue Sharks reach Round of 32",
    publisher: "Olympics.com",
    date: "2026-06-27",
    url: "https://www.olympics.com/en/news/fifa-world-cup-2026-cabo-verde-football-round-of-32",
    role: "current-football-context"
  },
  {
    id: "fifa-cpv-profile",
    title: "Cabo Verde team profile",
    publisher: "FIFA",
    date: "2026",
    url: "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/cabo-verde-team-profile-history",
    role: "team-profile"
  },
  {
    id: "worldbank-cabo-verde",
    title: "Cabo Verde country overview",
    publisher: "World Bank",
    date: "2026",
    url: "https://www.worldbank.org/ext/en/country/caboverde",
    role: "economy-development"
  },
  {
    id: "unesco-morna",
    title: "Morna, musical practice of Cabo Verde",
    publisher: "UNESCO Intangible Cultural Heritage",
    date: "2019",
    url: "https://ich.unesco.org/en/RL/morna-musical-practice-of-cabo-verde-01469",
    role: "culture"
  },
  {
    id: "visit-caboverde-islands",
    title: "The islands of Cabo Verde",
    publisher: "Visit Cabo Verde",
    date: "2026",
    url: "https://www.visit-caboverde.com/en/islands",
    role: "geography-tourism"
  },
  {
    id: "factbook-cabo-verde",
    title: "Cabo Verde country profile",
    publisher: "World Factbook",
    date: "2026",
    url: "https://theworldfactbook.org/country/cabo-verde.html",
    role: "country-data"
  },
  {
    id: "cntraveler-soccer-roots",
    title: "To understand Cape Verde's soccer roots, head to the beach",
    publisher: "Conde Nast Traveler",
    date: "2026-05",
    url: "https://www.cntraveler.com/story/to-understand-cape-verdes-soccer-roots-head-to-the-beach",
    role: "human-interest-context"
  },
  {
    id: "euronews-pico-lopes",
    title: "Who is Pico Lopes, the unlikely Cape Verde World Cup hero recruited through LinkedIn?",
    publisher: "Euronews",
    date: "2026-06-16",
    url: "https://www.euronews.com/2026/06/16/who-is-pico-lopes-the-unlikely-cape-verde-world-cup-hero-recruited-through-linkedin",
    role: "football-diaspora-context"
  }
];

export const claims = [
  {
    id: "snapshot-date",
    text: "截至2026年6月28日，佛得角已经进入2026世界杯32强淘汰赛。",
    sourceIds: ["aljazeera-cpv-argentina", "aljazeera-last32-schedule"]
  },
  {
    id: "argentina-opponent",
    text: "佛得角32强对手是卫冕冠军阿根廷。",
    sourceIds: ["aljazeera-cpv-argentina"]
  },
  {
    id: "three-draws",
    text: "佛得角以三场平局、小组第二身份出线。",
    sourceIds: ["aljazeera-cpv-argentina", "olympics-cpv-round32"]
  },
  {
    id: "morna-unesco",
    text: "Morna 是佛得角标志性音乐实践，并被列入联合国教科文组织非遗名录。",
    sourceIds: ["unesco-morna"]
  },
  {
    id: "tourism-economy",
    text: "旅游是佛得角经济的重要支柱，国家也面临耕地有限和资源有限的现实。",
    sourceIds: ["worldbank-cabo-verde", "factbook-cabo-verde"]
  }
];
```

- [ ] **Step 6: Create `data/storyboard.js`**

Create `国家专题视频/佛得角世界杯人文专题/data/storyboard.js`:

```js
export const storyboard = [
  {
    id: "cold-open",
    title: "佛的脚下凡",
    start: 0,
    duration: 35,
    assetIds: ["stadium-lights", "cape-verde-map", "cape-verde-flag"],
    keywords: ["佛的脚", "挑战阿根廷", "世界杯淘汰赛"],
    narration:
      "佛的脚，真的来人间比赛了。不是段子。这个大西洋上的群岛国家，第一次站上世界杯淘汰赛。而它下一场要挑战的，是世界冠军阿根廷。"
  },
  {
    id: "geography",
    title: "不是一个角，是一片群岛",
    start: 35,
    duration: 60,
    assetIds: ["atlantic-drone", "island-coast", "fogo-volcano"],
    keywords: ["大西洋", "十座主岛", "普拉亚"],
    narration:
      "但如果你只把它当成一个冷门比分，那就太小看这个故事了。佛得角不是突然被世界杯照亮。它本来就是非洲西岸外的大西洋群岛，是海风、火山、港口和迁徙连起来的国家。"
  },
  {
    id: "culture",
    title: "海风里的文化",
    start: 95,
    duration: 70,
    assetIds: ["mindelo-street", "morna-performance", "harbor-life"],
    keywords: ["葡语世界", "Kriolu", "Morna", "Morabeza"],
    narration:
      "这里说葡萄牙语，也有自己的克里奥尔语。非洲、欧洲和大西洋移民的记忆，混在街头音乐、港口生活和海边日常里。Morna 不是背景音乐，它像这片群岛的心跳。"
  },
  {
    id: "development",
    title: "美丽和现实",
    start: 165,
    duration: 60,
    assetIds: ["sal-tourism", "boa-vista-beach", "dry-land", "port-economy"],
    keywords: ["旅游", "侨汇", "水资源", "服务业"],
    narration:
      "当然，岛屿的浪漫背后，也有现实。旅游是经济支柱，侨汇连接着世界各地的佛得角人。可耕地有限，资源有限，干旱和气候压力一直存在。这个国家的发展，从来不是躺在海边等风来。"
  },
  {
    id: "football-rise",
    title: "蓝鲨队为什么能游到这里",
    start: 225,
    duration: 95,
    assetIds: ["blue-sharks-team", "fans-celebration", "training", "diaspora-map"],
    keywords: ["蓝鲨队", "旅欧球员", "三场平局", "国家认同"],
    narration:
      "所以足球在这里，不只是运动。人口不大，但网络很大。球员从岛上走向欧洲，也从欧洲回到国家队。蓝鲨队把分散在世界各地的身份，拧成了一件球衣。三场平局出线，看起来惊险，其实背后是多年积累。"
  },
  {
    id: "argentina-challenge",
    title: "挑战世界冠军",
    start: 320,
    duration: 50,
    assetIds: ["argentina-matchup", "cape-verde-flag", "ocean-stadium"],
    keywords: ["阿根廷", "世界冠军", "地图上的小国"],
    narration:
      "现在，佛得角站到了阿根廷面前。它不需要被说成夺冠热门，因为奇迹已经发生。佛的脚，不一定能踢翻世界冠军。但它已经告诉世界，地图上最小的名字，也能走到最大的球场中央。"
  }
];

export const targetDuration = 370;
```

- [ ] **Step 7: Create `data/captions.js`**

Create `国家专题视频/佛得角世界杯人文专题/data/captions.js`:

```js
export const captions = [
  { start: 1.0, end: 4.0, text: "佛的脚，真的来人间比赛了" },
  { start: 4.1, end: 6.0, text: "不是段子" },
  { start: 6.1, end: 10.4, text: "这个大西洋上的群岛国家" },
  { start: 10.5, end: 14.5, text: "第一次站上世界杯淘汰赛" },
  { start: 14.6, end: 19.5, text: "下一场，挑战世界冠军阿根廷" },
  { start: 36.0, end: 40.8, text: "如果你只把它当成一个冷门比分" },
  { start: 40.9, end: 43.4, text: "那就太小看这个故事了" },
  { start: 96.0, end: 101.0, text: "这里有葡语世界的影子" },
  { start: 101.1, end: 106.4, text: "也有大西洋移民的记忆" },
  { start: 166.0, end: 171.5, text: "岛屿的浪漫背后，也有现实" },
  { start: 226.0, end: 231.0, text: "足球在这里，不只是运动" },
  { start: 231.1, end: 236.0, text: "人口不大，但网络很大" },
  { start: 321.0, end: 326.5, text: "现在，佛得角站到了阿根廷面前" },
  { start: 356.0, end: 363.5, text: "地图上最小的名字，也能走到最大的球场中央" }
];
```

- [ ] **Step 8: Create asset README files**

Create `国家专题视频/佛得角世界杯人文专题/assets/footage/README.md`:

```markdown
# Footage

Put downloaded originals in `raw/` and normalized clips in `clips/`.

The final composition should read from `clips/`, not from `raw/`.
Each selected asset must be documented in `manifest.json` with source URL, role, local filename, and editorial note.
```

Create `国家专题视频/佛得角世界杯人文专题/assets/audio/README.md`:

```markdown
# Audio

Store narration and BGM here.

Required final files:

- `narration.wav`
- `bgm.mp3`
```

Create `国家专题视频/佛得角世界杯人文专题/assets/images/README.md`:

```markdown
# Images

Store still reference frames, generated maps, flags, and source screenshots here.
```

- [ ] **Step 9: Create `scripts/verify-story-data.mjs`**

Create `国家专题视频/佛得角世界杯人文专题/scripts/verify-story-data.mjs`:

```js
import { captions } from "../data/captions.js";
import { claims, sources } from "../data/sources.js";
import { storyboard, targetDuration } from "../data/storyboard.js";

const errors = [];
const sourceIds = new Set(sources.map((source) => source.id));

if (targetDuration < 300 || targetDuration > 480) {
  errors.push(`targetDuration must be between 300 and 480 seconds, got ${targetDuration}`);
}

for (let i = 0; i < storyboard.length; i += 1) {
  const scene = storyboard[i];
  if (!scene.id || !scene.title) errors.push(`scene ${i} is missing id or title`);
  if (typeof scene.start !== "number" || typeof scene.duration !== "number") {
    errors.push(`scene ${scene.id} start and duration must be numbers`);
  }
  if (scene.duration <= 0) errors.push(`scene ${scene.id} has non-positive duration`);
  if (!scene.narration || scene.narration.length < 20) {
    errors.push(`scene ${scene.id} narration is too short`);
  }
  if (i > 0 && scene.start !== storyboard[i - 1].start + storyboard[i - 1].duration) {
    errors.push(`scene ${scene.id} does not start after previous scene`);
  }
}

const computedDuration = storyboard.at(-1).start + storyboard.at(-1).duration;
if (computedDuration !== targetDuration) {
  errors.push(`storyboard duration ${computedDuration} does not equal targetDuration ${targetDuration}`);
}

for (const caption of captions) {
  if (caption.start < 0 || caption.end <= caption.start) {
    errors.push(`caption has invalid timing: ${JSON.stringify(caption)}`);
  }
  if (!caption.text || caption.text.length > 28) {
    errors.push(`caption text must be 1-28 chars: ${JSON.stringify(caption)}`);
  }
}

for (const claim of claims) {
  for (const sourceId of claim.sourceIds) {
    if (!sourceIds.has(sourceId)) {
      errors.push(`claim ${claim.id} references missing source ${sourceId}`);
    }
  }
}

if (!claims.some((claim) => claim.id === "argentina-opponent")) {
  errors.push("missing current Argentina opponent claim");
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Verified ${storyboard.length} scenes, ${captions.length} captions, ${sources.length} sources.`);
```

- [ ] **Step 10: Run data verification**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run verify:data
```

Expected output includes:

```text
Verified 6 scenes, 14 captions, 10 sources.
```

- [ ] **Step 11: Commit scaffold**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题
git commit -m "feat: scaffold cape verde video project"
```

Expected: commit succeeds with the new project files.

---

### Task 2: Finalize Narration And Caption Timing

**Files:**
- Create: `国家专题视频/佛得角世界杯人文专题/scripts/narration.txt`
- Modify: `国家专题视频/佛得角世界杯人文专题/data/storyboard.js`
- Modify: `国家专题视频/佛得角世界杯人文专题/data/captions.js`

**Interfaces:**
- Consumes: `storyboard` and `targetDuration` from Task 1.
- Produces: complete narration text used by `scripts/make-narration.sh` in Task 4.
- Produces: final `captions` array used by `index.html` in Task 5.

- [ ] **Step 1: Replace narration with full script**

Create `国家专题视频/佛得角世界杯人文专题/scripts/narration.txt`:

```text
佛的脚，真的来人间比赛了。
不是段子。
这个大西洋上的群岛国家，第一次站上世界杯淘汰赛。
而它下一场要挑战的，是世界冠军阿根廷。

但如果你只把它当成一个冷门比分，那就太小看这个故事了。
佛得角不是突然被世界杯照亮。
它本来就是非洲西岸外的大西洋群岛。
一串被海风、火山、港口和迁徙连起来的岛。
中文叫佛得角，听起来像一个梗。
可在世界地图上，它更像大西洋的一座中转站。

从非洲西岸往外看，你会看到十座主岛散在海上。
首都普拉亚在圣地亚哥岛。
圣维森特有明德卢，有港口，也有音乐。
福戈有火山。
萨尔和博阿维斯塔，有游客熟悉的海滩和风。
所以佛得角不是一个角。
它是一片群岛。
也是一条海上的路。

这里的文化，也不像一条直线。
官方语言是葡萄牙语，日常生活里还有克里奥尔语。
非洲的节奏，葡萄牙的记忆，大西洋移民的乡愁，都混在一起。
如果要找一个声音代表佛得角，那就是 Morna。
它不是单纯的背景音乐。
它像海风吹过港口之后，留下来的叹息。
温柔、漂泊，也骄傲。
你能在这类音乐里听到离开，也能听到回家。

但岛屿的浪漫背后，也有现实。
佛得角不靠大片耕地吃饭，也没有丰富矿产。
旅游是经济支柱之一，侨汇也把世界各地的佛得角人，重新连回这些岛。
海滩、机场、酒店和港口，是发展的一面。
干旱、水资源压力、进口依赖和气候风险，是另一面。
这个国家不是躺在海边等风来。
它一直在有限的条件里，寻找自己的出路。

所以足球在这里，不只是运动。
它是一种连接。
人口不大，但网络很大。
有人从岛上出发，去欧洲踢球。
也有人在葡萄牙、荷兰、法国、爱尔兰成长，然后把血缘和身份穿回国家队球衣上。
蓝鲨队这个名字，听起来很凶。
可它真正厉害的地方，是把分散在世界各地的人，拧成同一个方向。

这届世界杯，佛得角没有用大比分碾压谁。
他们是三场平局，小组第二出线。
听起来不够传奇？
恰恰相反。
对一个第一次站上世界杯淘汰赛的小国来说，每一分都像在海浪里抢下来的。
他们不是靠运气突然冒出来。
非洲杯的经验，旅欧球员的成熟，国家队体系的积累，还有球迷对这件球衣的投入，最后都汇到了这一刻。

现在，佛得角站到了阿根廷面前。
对面是世界冠军，是梅西的阿根廷，是所有小球队都会仰头看的名字。
佛得角当然不是热门。
也没有必要把它说成童话里一定会赢的主角。
真正震撼的地方，是他们已经走到了这里。
从大西洋群岛，到世界杯淘汰赛。
从地图上很小的名字，到全世界都要念出来的对手。

佛的脚，不一定能踢翻世界冠军。
但它已经告诉世界：
地图上最小的名字，也能走到最大的球场中央。
```

- [ ] **Step 2: Update `storyboard.js` narration from the script**

Replace `国家专题视频/佛得角世界杯人文专题/data/storyboard.js` with:

```js
export const storyboard = [
  {
    id: "cold-open",
    title: "佛的脚下凡",
    start: 0,
    duration: 35,
    assetIds: ["stadium-lights", "cape-verde-flag"],
    keywords: ["佛的脚", "挑战阿根廷", "世界杯淘汰赛"],
    narration:
      "佛的脚，真的来人间比赛了。不是段子。这个大西洋上的群岛国家，第一次站上世界杯淘汰赛。而它下一场要挑战的，是世界冠军阿根廷。"
  },
  {
    id: "geography",
    title: "不是一个角，是一片群岛",
    start: 35,
    duration: 60,
    assetIds: ["atlantic-drone", "fogo-volcano"],
    keywords: ["大西洋", "十座主岛", "普拉亚"],
    narration:
      "但如果你只把它当成一个冷门比分，那就太小看这个故事了。佛得角不是突然被世界杯照亮。它本来就是非洲西岸外的大西洋群岛。一串被海风、火山、港口和迁徙连起来的岛。中文叫佛得角，听起来像一个梗。可在世界地图上，它更像大西洋的一座中转站。从非洲西岸往外看，你会看到十座主岛散在海上。首都普拉亚在圣地亚哥岛。圣维森特有明德卢，有港口，也有音乐。福戈有火山。萨尔和博阿维斯塔，有游客熟悉的海滩和风。所以佛得角不是一个角。它是一片群岛。也是一条海上的路。"
  },
  {
    id: "culture",
    title: "海风里的文化",
    start: 95,
    duration: 70,
    assetIds: ["morna-performance"],
    keywords: ["葡语世界", "Kriolu", "Morna", "Morabeza"],
    narration:
      "这里的文化，也不像一条直线。官方语言是葡萄牙语，日常生活里还有克里奥尔语。非洲的节奏，葡萄牙的记忆，大西洋移民的乡愁，都混在一起。如果要找一个声音代表佛得角，那就是 Morna。它不是单纯的背景音乐。它像海风吹过港口之后，留下来的叹息。温柔、漂泊，也骄傲。你能在这类音乐里听到离开，也能听到回家。"
  },
  {
    id: "development",
    title: "美丽和现实",
    start: 165,
    duration: 60,
    assetIds: ["sal-tourism"],
    keywords: ["旅游", "侨汇", "水资源", "服务业"],
    narration:
      "但岛屿的浪漫背后，也有现实。佛得角不靠大片耕地吃饭，也没有丰富矿产。旅游是经济支柱之一，侨汇也把世界各地的佛得角人，重新连回这些岛。海滩、机场、酒店和港口，是发展的一面。干旱、水资源压力、进口依赖和气候风险，是另一面。这个国家不是躺在海边等风来。它一直在有限的条件里，寻找自己的出路。"
  },
  {
    id: "football-rise",
    title: "蓝鲨队为什么能游到这里",
    start: 225,
    duration: 95,
    assetIds: ["blue-sharks-team", "fans-celebration"],
    keywords: ["蓝鲨队", "旅欧球员", "三场平局", "国家认同"],
    narration:
      "所以足球在这里，不只是运动。它是一种连接。人口不大，但网络很大。有人从岛上出发，去欧洲踢球。也有人在葡萄牙、荷兰、法国、爱尔兰成长，然后把血缘和身份穿回国家队球衣上。蓝鲨队这个名字，听起来很凶。可它真正厉害的地方，是把分散在世界各地的人，拧成同一个方向。这届世界杯，佛得角没有用大比分碾压谁。他们是三场平局，小组第二出线。听起来不够传奇？恰恰相反。对一个第一次站上世界杯淘汰赛的小国来说，每一分都像在海浪里抢下来的。他们不是靠运气突然冒出来。非洲杯的经验，旅欧球员的成熟，国家队体系的积累，还有球迷对这件球衣的投入，最后都汇到了这一刻。"
  },
  {
    id: "argentina-challenge",
    title: "挑战世界冠军",
    start: 320,
    duration: 50,
    assetIds: ["fans-celebration", "cape-verde-flag"],
    keywords: ["阿根廷", "世界冠军", "地图上的小国"],
    narration:
      "现在，佛得角站到了阿根廷面前。对面是世界冠军，是梅西的阿根廷，是所有小球队都会仰头看的名字。佛得角当然不是热门。也没有必要把它说成童话里一定会赢的主角。真正震撼的地方，是他们已经走到了这里。从大西洋群岛，到世界杯淘汰赛。从地图上很小的名字，到全世界都要念出来的对手。佛的脚，不一定能踢翻世界冠军。但它已经告诉世界：地图上最小的名字，也能走到最大的球场中央。"
  }
];

export const targetDuration = 370;
```

- [ ] **Step 3: Expand `captions.js` to cover the full script**

Replace `国家专题视频/佛得角世界杯人文专题/data/captions.js` with:

```js
export const captions = [
  { start: 1.0, end: 4.0, text: "佛的脚，真的来人间比赛了" },
  { start: 4.3, end: 6.0, text: "不是段子" },
  { start: 6.3, end: 10.3, text: "这个大西洋上的群岛国家" },
  { start: 10.6, end: 14.5, text: "第一次站上世界杯淘汰赛" },
  { start: 14.8, end: 19.5, text: "下一场，挑战世界冠军阿根廷" },
  { start: 20.6, end: 25.6, text: "这不是冷门比分那么简单" },
  { start: 26.0, end: 33.0, text: "这是一个国家被世界看见的瞬间" },

  { start: 36.0, end: 40.7, text: "如果你只把它当成冷门比分" },
  { start: 41.0, end: 43.5, text: "那就太小看这个故事了" },
  { start: 44.0, end: 48.4, text: "佛得角不是突然被世界杯照亮" },
  { start: 48.8, end: 53.0, text: "它在非洲西岸外的大西洋上" },
  { start: 53.4, end: 57.4, text: "由海风、火山和港口连接" },
  { start: 57.8, end: 62.4, text: "中文叫佛得角，听起来像梗" },
  { start: 62.8, end: 67.7, text: "但地图上，它是大西洋中转站" },
  { start: 68.2, end: 72.3, text: "十座主岛，散在海上" },
  { start: 72.8, end: 76.9, text: "首都普拉亚在圣地亚哥岛" },
  { start: 77.4, end: 82.2, text: "明德卢有港口，也有音乐" },
  { start: 82.8, end: 87.0, text: "福戈有火山，萨尔有海风" },
  { start: 87.5, end: 91.5, text: "佛得角不是一个角" },
  { start: 91.8, end: 94.2, text: "它是一片群岛" },

  { start: 96.0, end: 99.8, text: "这里的文化，也不像一条直线" },
  { start: 100.2, end: 104.0, text: "官方语言是葡萄牙语" },
  { start: 104.4, end: 108.5, text: "日常生活里还有克里奥尔语" },
  { start: 109.0, end: 113.8, text: "非洲节奏，葡萄牙记忆" },
  { start: 114.2, end: 118.8, text: "大西洋移民的乡愁，都混在一起" },
  { start: 119.4, end: 124.1, text: "代表佛得角的声音，就是 Morna" },
  { start: 124.7, end: 128.6, text: "它不是单纯的背景音乐" },
  { start: 129.0, end: 134.2, text: "它像海风吹过港口后的叹息" },
  { start: 134.8, end: 139.0, text: "温柔，漂泊，也骄傲" },
  { start: 139.6, end: 145.2, text: "你能听到离开，也能听到回家" },
  { start: 146.0, end: 152.0, text: "这就是海岛性格里的柔软" },
  { start: 152.6, end: 160.0, text: "也是蓝鲨队后来凝聚起来的底色" },

  { start: 166.0, end: 170.0, text: "岛屿的浪漫背后，也有现实" },
  { start: 170.4, end: 174.6, text: "佛得角不靠大片耕地吃饭" },
  { start: 175.0, end: 179.0, text: "也没有丰富矿产" },
  { start: 179.5, end: 184.4, text: "旅游是经济支柱之一" },
  { start: 184.8, end: 190.4, text: "侨汇把世界各地的人连回群岛" },
  { start: 191.0, end: 196.2, text: "海滩、机场、酒店和港口" },
  { start: 196.7, end: 200.5, text: "是发展的一面" },
  { start: 201.0, end: 206.8, text: "干旱、水资源和进口依赖" },
  { start: 207.3, end: 211.6, text: "是另一面" },
  { start: 212.2, end: 216.2, text: "它不是躺在海边等风来" },
  { start: 216.8, end: 223.0, text: "它一直在有限条件里寻找出路" },

  { start: 226.0, end: 229.8, text: "所以足球在这里，不只是运动" },
  { start: 230.3, end: 233.4, text: "它是一种连接" },
  { start: 233.9, end: 237.4, text: "人口不大，但网络很大" },
  { start: 238.0, end: 242.8, text: "有人从岛上出发去欧洲踢球" },
  { start: 243.4, end: 249.8, text: "也有人在欧洲成长后回到国家队" },
  { start: 250.4, end: 255.4, text: "把血缘和身份穿回同一件球衣" },
  { start: 256.0, end: 260.2, text: "蓝鲨队这个名字，听起来很凶" },
  { start: 260.7, end: 266.4, text: "真正厉害的是把分散的人拧在一起" },
  { start: 267.0, end: 271.2, text: "这届世界杯，他们没有碾压谁" },
  { start: 271.8, end: 276.2, text: "三场平局，小组第二出线" },
  { start: 276.8, end: 279.2, text: "听起来不够传奇？" },
  { start: 279.7, end: 282.2, text: "恰恰相反" },
  { start: 282.8, end: 288.4, text: "每一分都像在海浪里抢下来" },
  { start: 289.0, end: 294.0, text: "他们不是靠运气突然冒出来" },
  { start: 294.6, end: 300.0, text: "非洲杯经验，旅欧球员成熟" },
  { start: 300.6, end: 306.8, text: "国家队体系和球迷投入" },
  { start: 307.4, end: 317.0, text: "最后都汇到了这一刻" },

  { start: 321.0, end: 326.0, text: "现在，佛得角站到了阿根廷面前" },
  { start: 326.6, end: 331.0, text: "对面是世界冠军" },
  { start: 331.5, end: 336.6, text: "是所有小球队都会仰头看的名字" },
  { start: 337.2, end: 341.4, text: "佛得角当然不是热门" },
  { start: 342.0, end: 347.5, text: "但震撼的是，他们已经走到这里" },
  { start: 348.0, end: 352.2, text: "从大西洋群岛，到世界杯淘汰赛" },
  { start: 352.8, end: 357.2, text: "从地图上的小名字" },
  { start: 357.7, end: 361.5, text: "到全世界都要念出的对手" },
  { start: 362.0, end: 365.0, text: "佛的脚，不一定能踢翻世界冠军" },
  { start: 365.4, end: 369.2, text: "但小名字，也能站上最大球场" }
];
```

- [ ] **Step 4: Verify story data**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run verify:data
```

Expected: PASS. The exact caption count may differ from Task 1, but the output must say `Verified 6 scenes`.

- [ ] **Step 5: Commit narration and captions**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/scripts/narration.txt 国家专题视频/佛得角世界杯人文专题/data/storyboard.js 国家专题视频/佛得角世界杯人文专题/data/captions.js
git commit -m "feat: add cape verde narration script"
```

Expected: commit succeeds.

---

### Task 3: Collect And Normalize Source Footage

**Files:**
- Create: `国家专题视频/佛得角世界杯人文专题/assets/footage/manifest.json`
- Create: `国家专题视频/佛得角世界杯人文专题/scripts/check-assets.mjs`
- Create: `国家专题视频/佛得角世界杯人文专题/scripts/asset-clips.sh`
- Modify: `国家专题视频/佛得角世界杯人文专题/data/storyboard.js`

**Interfaces:**
- Consumes: `storyboard[*].assetIds`.
- Produces: normalized MP4 clips under `assets/footage/clips/` used by `index.html`.
- Produces: `npm run check:assets` command used before composition work.

- [ ] **Step 1: Install or verify yt-dlp**

Run:

```bash
python3 -m pip install --user yt-dlp
python3 -m yt_dlp --version
```

Expected: a yt-dlp version string prints. If `python3 -m pip install --user yt-dlp` reports that yt-dlp is already installed, continue.

- [ ] **Step 2: Create `manifest.json` with chosen assets**

Create `国家专题视频/佛得角世界杯人文专题/assets/footage/manifest.json`:

```json
{
  "assets": [
    {
      "id": "stadium-lights",
      "role": "cold open stadium texture",
      "sourceUrl": "generated-ffmpeg-lavfi",
      "rawFile": "",
      "clipFile": "clips/stadium-lights.mp4",
      "start": 0,
      "duration": 8,
      "note": "Generated dark Atlantic stadium texture for the cold open."
    },
    {
      "id": "atlantic-drone",
      "role": "country geography aerial",
      "sourceUrl": "https://www.youtube.com/watch?v=n518CDsVG4w",
      "rawFile": "raw/cape-verde-travel.mp4",
      "clipFile": "clips/atlantic-drone.mp4",
      "start": 30,
      "duration": 18,
      "note": "Use clean island coastline or aerial shot."
    },
    {
      "id": "fogo-volcano",
      "role": "volcanic island identity",
      "sourceUrl": "https://www.youtube.com/watch?v=0rENxjIK898",
      "rawFile": "raw/fogo-hiking.mp4",
      "clipFile": "clips/fogo-volcano.mp4",
      "start": 40,
      "duration": 15,
      "note": "Use mountain/volcano landscape shot."
    },
    {
      "id": "morna-performance",
      "role": "culture and music",
      "sourceUrl": "https://www.youtube.com/watch?v=2e0wCkWeoVs",
      "rawFile": "raw/morna-unesco.mp4",
      "clipFile": "clips/morna-performance.mp4",
      "start": 12,
      "duration": 18,
      "note": "Use UNESCO morna visual excerpt."
    },
    {
      "id": "sal-tourism",
      "role": "tourism economy",
      "sourceUrl": "https://www.youtube.com/watch?v=4wjlZ_RKHk8",
      "rawFile": "raw/dw-cape-verde.mp4",
      "clipFile": "clips/sal-tourism.mp4",
      "start": 80,
      "duration": 18,
      "note": "Use tourism or beach economy visuals."
    },
    {
      "id": "blue-sharks-team",
      "role": "football national team",
      "sourceUrl": "https://www.youtube.com/watch?v=JreiAoc6HFk",
      "rawFile": "raw/cape-verde-underdog.mp4",
      "clipFile": "clips/blue-sharks-team.mp4",
      "start": 20,
      "duration": 20,
      "note": "Use transformed short excerpt; avoid long match broadcast."
    },
    {
      "id": "fans-celebration",
      "role": "fan emotion",
      "sourceUrl": "https://www.youtube.com/watch?v=GpjhEESO1gI",
      "rawFile": "raw/fans-celebration.mp4",
      "clipFile": "clips/fans-celebration.mp4",
      "start": 5,
      "duration": 15,
      "note": "Use celebration shot if downloadable and clean."
    }
  ]
}
```

- [ ] **Step 3: Download raw candidates**

Run one command per YouTube source after checking the URL opens:

```bash
cd 国家专题视频/佛得角世界杯人文专题/assets/footage
python3 -m yt_dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -f "137/298/136/18/bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]" --merge-output-format mp4 -o "raw/cape-verde-travel.%(ext)s" "https://www.youtube.com/watch?v=n518CDsVG4w"
python3 -m yt_dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -f "137/298/136/18/bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]" --merge-output-format mp4 -o "raw/fogo-hiking.%(ext)s" "https://www.youtube.com/watch?v=0rENxjIK898"
python3 -m yt_dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -f "137/298/136/18/bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]" --merge-output-format mp4 -o "raw/morna-unesco.%(ext)s" "https://www.youtube.com/watch?v=2e0wCkWeoVs"
python3 -m yt_dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -f "137/298/136/18/bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]" --merge-output-format mp4 -o "raw/dw-cape-verde.%(ext)s" "https://www.youtube.com/watch?v=4wjlZ_RKHk8"
python3 -m yt_dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -f "137/298/136/18/bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]" --merge-output-format mp4 -o "raw/cape-verde-underdog.%(ext)s" "https://www.youtube.com/watch?v=JreiAoc6HFk"
python3 -m yt_dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" -f "137/298/136/18/bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]" --merge-output-format mp4 -o "raw/fans-celebration.%(ext)s" "https://www.youtube.com/watch?v=GpjhEESO1gI"
```

Expected: these six raw MP4 files exist in `assets/footage/raw/`:

```text
cape-verde-travel.mp4
fogo-hiking.mp4
morna-unesco.mp4
dw-cape-verde.mp4
cape-verde-underdog.mp4
fans-celebration.mp4
```

- [ ] **Step 4: Create `asset-clips.sh`**

Create `国家专题视频/佛得角世界杯人文专题/scripts/asset-clips.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p assets/footage/clips

clip() {
  local src="$1"
  local start="$2"
  local dur="$3"
  local out="$4"
  ffmpeg -y -ss "$start" -i "assets/footage/$src" -t "$dur" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1" \
    -an -c:v libx264 -pix_fmt yuv420p -crf 20 -preset veryfast "assets/footage/$out"
}

ffmpeg -y -f lavfi -i "color=c=0x061B2E:s=1920x1080:r=30:d=8" \
  -vf "format=yuv420p,noise=alls=8:allf=t+u,eq=contrast=1.12:saturation=1.08" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset veryfast "assets/footage/clips/stadium-lights.mp4"

clip "raw/cape-verde-travel.mp4" 30 18 "clips/atlantic-drone.mp4"
clip "raw/fogo-hiking.mp4" 40 15 "clips/fogo-volcano.mp4"
clip "raw/morna-unesco.mp4" 12 18 "clips/morna-performance.mp4"
clip "raw/dw-cape-verde.mp4" 80 18 "clips/sal-tourism.mp4"
clip "raw/cape-verde-underdog.mp4" 20 20 "clips/blue-sharks-team.mp4"
clip "raw/fans-celebration.mp4" 5 15 "clips/fans-celebration.mp4"
```

Run:

```bash
chmod +x 国家专题视频/佛得角世界杯人文专题/scripts/asset-clips.sh
cd 国家专题视频/佛得角世界杯人文专题
bash scripts/asset-clips.sh
```

Expected: MP4 files are created in `assets/footage/clips/`.

- [ ] **Step 5: Create `check-assets.mjs`**

Create `国家专题视频/佛得角世界杯人文专题/scripts/check-assets.mjs`:

```js
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const manifest = JSON.parse(readFileSync("assets/footage/manifest.json", "utf8"));
const errors = [];

for (const asset of manifest.assets) {
  const clipPath = path.join("assets/footage", asset.clipFile);
  if (!existsSync(clipPath)) {
    errors.push(`missing clip ${clipPath}`);
    continue;
  }
  const durationRaw = execFileSync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    clipPath
  ], { encoding: "utf8" }).trim();
  const duration = Number.parseFloat(durationRaw);
  if (!Number.isFinite(duration) || duration < 4) {
    errors.push(`clip ${clipPath} has invalid duration ${durationRaw}`);
  }
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Verified ${manifest.assets.length} footage assets.`);
```

- [ ] **Step 6: Run asset verification**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run check:assets
```

Expected output:

```text
Verified 7 footage assets.
```

- [ ] **Step 7: Commit assets metadata and scripts**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/assets/footage/manifest.json 国家专题视频/佛得角世界杯人文专题/scripts/check-assets.mjs 国家专题视频/佛得角世界杯人文专题/scripts/asset-clips.sh
git commit -m "feat: add cape verde footage manifest"
```

Expected: metadata and scripts are committed. Do not commit large raw video files unless the repository policy allows media files.

---

### Task 4: Generate Narration And Select BGM

**Files:**
- Create: `国家专题视频/佛得角世界杯人文专题/scripts/make-narration.sh`
- Create: `国家专题视频/佛得角世界杯人文专题/assets/audio/narration.wav`
- Create: `国家专题视频/佛得角世界杯人文专题/assets/audio/bgm.mp3`
- Modify: `国家专题视频/佛得角世界杯人文专题/assets/audio/README.md`

**Interfaces:**
- Consumes: `scripts/narration.txt`.
- Produces: `assets/audio/narration.wav` and `assets/audio/bgm.mp3` consumed by `index.html`.

- [ ] **Step 1: Create `make-narration.sh`**

Create `国家专题视频/佛得角世界杯人文专题/scripts/make-narration.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p assets/audio

if npx hyperframes tts --list >/tmp/hyperframes-tts-voices.txt 2>/dev/null; then
  npx hyperframes tts scripts/narration.txt --voice zh-CN-YunjianNeural --output assets/audio/narration.wav
else
  python3 -m pip install --user edge-tts
  python3 -m edge_tts --voice zh-CN-YunjianNeural --rate=+8% --pitch=+8Hz --file scripts/narration.txt --write-media assets/audio/narration.mp3
  ffmpeg -y -i assets/audio/narration.mp3 -ar 48000 -ac 2 assets/audio/narration.wav
fi

ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 assets/audio/narration.wav
```

Run:

```bash
chmod +x 国家专题视频/佛得角世界杯人文专题/scripts/make-narration.sh
cd 国家专题视频/佛得角世界杯人文专题
bash scripts/make-narration.sh
```

Expected: `assets/audio/narration.wav` exists, and ffprobe prints a duration between 300 and 480 seconds.

- [ ] **Step 2: Add BGM**

Use Kevin MacLeod's `Crossing the Chasm` as the first BGM pass:

```bash
cd 国家专题视频/佛得角世界杯人文专题
curl -L "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Crossing%20the%20Chasm.mp3" -o assets/audio/bgm.mp3
```

Expected: `assets/audio/bgm.mp3` exists and plays. Publishing notes must include: `Music: Crossing the Chasm by Kevin MacLeod, CC BY`.

- [ ] **Step 3: Update audio README**

Modify `国家专题视频/佛得角世界杯人文专题/assets/audio/README.md`:

```markdown
# Audio

Store narration and BGM here.

Required final files:

- `narration.wav`: Chinese male narration generated from `scripts/narration.txt`.
- `bgm.mp3`: Licensed or royalty-free background music.

Publishing attribution for the planned BGM: `Music: Crossing the Chasm by Kevin MacLeod, CC BY`.
```

- [ ] **Step 4: Verify audio durations**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 assets/audio/narration.wav
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 assets/audio/bgm.mp3
```

Expected: narration duration is between 300 and 480 seconds; BGM duration is at least 120 seconds and can be looped by HyperFrames or replaced by a longer track.

- [ ] **Step 5: Commit audio script and README**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/scripts/make-narration.sh 国家专题视频/佛得角世界杯人文专题/assets/audio/README.md
git commit -m "feat: add narration generation workflow"
```

Expected: script and README are committed. Do not commit generated audio if repository policy excludes media outputs.

---

### Task 5: Build HyperFrames Composition Skeleton

**Files:**
- Create: `国家专题视频/佛得角世界杯人文专题/index.html`

**Interfaces:**
- Consumes: `storyboard`, `captions`, `assets/audio/narration.wav`, `assets/audio/bgm.mp3`, and selected footage clips.
- Produces: root composition `cape-verde-main` for HyperFrames lint, inspect, preview, and render.

- [ ] **Step 1: Create `index.html` base**

Create `国家专题视频/佛得角世界杯人文专题/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>佛的脚下凡，挑战世界冠军</title>
  <style>
    :root {
      --atlantic-navy: #061B2E;
      --deep-ocean: #0B3558;
      --volcanic-black: #111217;
      --cv-blue: #1A4FB3;
      --flag-red: #D71920;
      --flag-yellow: #F7D117;
      --warm-white: #F6F2E8;
      --data-gold: #E7B84A;
      --font-cn: "Noto Sans SC", "Source Han Sans SC", "Hiragino Sans GB", sans-serif;
      --font-latin: "Inter", Arial, sans-serif;
    }

    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      background: var(--volcanic-black);
      overflow: hidden;
      font-family: var(--font-cn);
      color: var(--warm-white);
    }

    [data-composition-id="cape-verde-main"] {
      position: relative;
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      background: var(--atlantic-navy);
    }

    video.background-video,
    .scene,
    .transition,
    .caption-layer {
      position: absolute;
      inset: 0;
    }

    video.background-video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: saturate(0.95) contrast(1.05);
    }

    .scene {
      display: flex;
      flex-direction: column;
      justify-content: center;
      box-sizing: border-box;
      padding: 84px 110px;
      gap: 28px;
      opacity: 0;
      z-index: 5;
    }

    .scene::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 22% 18%, rgba(26, 79, 179, 0.26), transparent 30%),
        linear-gradient(90deg, rgba(6, 27, 46, 0.88), rgba(6, 27, 46, 0.38), rgba(17, 18, 23, 0.78));
      z-index: -1;
    }

    .kicker {
      width: fit-content;
      max-width: 980px;
      padding: 10px 18px;
      border-left: 6px solid var(--flag-yellow);
      background: rgba(6, 27, 46, 0.72);
      color: var(--flag-yellow);
      font: 700 30px/1.2 var(--font-cn);
    }

    .headline {
      max-width: 1120px;
      margin: 0;
      font: 900 86px/1.05 var(--font-cn);
      letter-spacing: 0;
      text-wrap: balance;
      text-shadow: 0 12px 34px rgba(0, 0, 0, 0.45);
    }

    .body {
      max-width: 980px;
      font: 500 36px/1.45 var(--font-cn);
      color: rgba(246, 242, 232, 0.92);
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      max-width: 1180px;
    }

    .chip {
      padding: 12px 20px;
      border: 1px solid rgba(247, 209, 23, 0.46);
      background: rgba(11, 53, 88, 0.74);
      color: var(--warm-white);
      font: 700 28px/1.2 var(--font-cn);
    }

    .map-board,
    .data-board,
    .match-board {
      width: min(1180px, 72vw);
      min-height: 280px;
      padding: 34px;
      box-sizing: border-box;
      border: 1px solid rgba(246, 242, 232, 0.18);
      background: rgba(6, 27, 46, 0.78);
      box-shadow: 0 22px 60px rgba(0, 0, 0, 0.32);
    }

    .caption-layer {
      z-index: 20;
      pointer-events: none;
      display: flex;
      align-items: flex-end;
      justify-content: center;
      padding: 0 180px 66px;
      box-sizing: border-box;
    }

    .caption {
      min-width: 420px;
      max-width: 1240px;
      padding: 14px 28px 18px;
      background: rgba(17, 18, 23, 0.78);
      border-bottom: 5px solid var(--flag-yellow);
      color: var(--warm-white);
      text-align: center;
      font: 800 42px/1.2 var(--font-cn);
      opacity: 0;
      transform: translateY(24px);
    }

    .transition {
      z-index: 18;
      pointer-events: none;
      transform: translateX(-105%);
      background: linear-gradient(90deg, var(--flag-red), var(--flag-yellow), var(--cv-blue));
    }
  </style>
</head>
<body>
  <div data-composition-id="cape-verde-main" data-width="1920" data-height="1080">
    <video class="background-video" id="bg-cold" data-start="0" data-duration="35" data-track-index="0" src="assets/footage/clips/stadium-lights.mp4" muted playsinline></video>

    <audio id="narration" data-start="0" data-duration="370" data-track-index="30" src="assets/audio/narration.wav" data-volume="1"></audio>
    <audio id="bgm" data-start="0" data-duration="370" data-track-index="31" src="assets/audio/bgm.mp3" data-volume="0.18"></audio>

    <section class="scene" id="scene-cold" data-start="0" data-duration="35" data-track-index="10">
      <div class="kicker">2026 世界杯 · 32 强</div>
      <h1 class="headline">佛的脚下凡，挑战世界冠军</h1>
      <div class="chips">
        <span class="chip">佛得角 Cabo Verde</span>
        <span class="chip">蓝鲨队</span>
        <span class="chip">下一站：阿根廷</span>
      </div>
    </section>

    <div class="transition" id="transition-bar"></div>
    <div class="caption-layer"><div class="caption" id="caption"></div></div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script type="module">
    import { captions } from "./data/captions.js";

    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    tl.from("#scene-cold", { opacity: 0, y: 45, duration: 0.7, ease: "power3.out" }, 0.2);
    tl.from("#scene-cold .kicker", { opacity: 0, x: -60, duration: 0.5, ease: "expo.out" }, 0.45);
    tl.from("#scene-cold .headline", { opacity: 0, scale: 0.92, duration: 0.65, ease: "back.out(1.4)" }, 0.65);
    tl.from("#scene-cold .chip", { opacity: 0, y: 30, stagger: 0.12, duration: 0.45, ease: "power2.out" }, 1.1);

    for (const caption of captions) {
      tl.set("#caption", { textContent: caption.text }, caption.start);
      tl.to("#caption", { opacity: 1, y: 0, duration: 0.18, ease: "power2.out" }, caption.start);
      tl.to("#caption", { opacity: 0, y: 24, duration: 0.16, ease: "power2.in" }, Math.max(caption.start, caption.end - 0.16));
    }

    window.__timelines["cape-verde-main"] = tl;
  </script>
</body>
</html>
```

- [ ] **Step 2: Run HyperFrames lint**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run lint
```

Expected: no lint errors.

- [ ] **Step 3: Run visual inspect**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run inspect
```

Expected: no text overflow errors for the cold open and captions.

- [ ] **Step 4: Commit composition skeleton**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/index.html
git commit -m "feat: add cape verde hyperframes skeleton"
```

Expected: commit succeeds.

---

### Task 6: Implement Geography, Culture, And Development Scenes

**Files:**
- Modify: `国家专题视频/佛得角世界杯人文专题/index.html`

**Interfaces:**
- Consumes: normalized footage clips `atlantic-drone.mp4`, `fogo-volcano.mp4`, `morna-performance.mp4`, and `sal-tourism.mp4`.
- Produces: visible scenes `scene-geography`, `scene-culture`, and `scene-development`.

- [ ] **Step 1: Add background video layers for scenes 2-4**

In `index.html`, after `#bg-cold`, add:

```html
<video class="background-video" id="bg-geography" data-start="35" data-duration="60" data-track-index="0" src="assets/footage/clips/atlantic-drone.mp4" muted playsinline></video>
<video class="background-video" id="bg-culture" data-start="95" data-duration="70" data-track-index="0" src="assets/footage/clips/morna-performance.mp4" muted playsinline></video>
<video class="background-video" id="bg-development" data-start="165" data-duration="60" data-track-index="0" src="assets/footage/clips/sal-tourism.mp4" muted playsinline></video>
```

- [ ] **Step 2: Add scene HTML**

In `index.html`, after `#scene-cold`, add:

```html
<section class="scene" id="scene-geography" data-start="35" data-duration="60" data-track-index="10">
  <div class="kicker">不是一个角，是一片群岛</div>
  <h2 class="headline">大西洋上的十座主岛</h2>
  <div class="map-board">
    <div class="body">非洲西岸外，海风、火山、港口和迁徙连起来的国家。</div>
    <div class="chips">
      <span class="chip">首都：普拉亚</span>
      <span class="chip">圣维森特 · 明德卢</span>
      <span class="chip">福戈火山</span>
    </div>
  </div>
</section>

<section class="scene" id="scene-culture" data-start="95" data-duration="70" data-track-index="10">
  <div class="kicker">海风里的文化</div>
  <h2 class="headline">Morna 像群岛的心跳</h2>
  <div class="map-board">
    <div class="body">葡语、Kriolu、非洲节奏、葡萄牙记忆和大西洋移民乡愁，混在同一条街上。</div>
    <div class="chips">
      <span class="chip">Kriolu</span>
      <span class="chip">Morabeza</span>
      <span class="chip">UNESCO 非遗</span>
    </div>
  </div>
</section>

<section class="scene" id="scene-development" data-start="165" data-duration="60" data-track-index="10">
  <div class="kicker">美丽和现实</div>
  <h2 class="headline">不是躺在海边等风来</h2>
  <div class="data-board">
    <div class="chips">
      <span class="chip">旅游经济</span>
      <span class="chip">侨汇连接</span>
      <span class="chip">耕地有限</span>
      <span class="chip">水资源压力</span>
    </div>
  </div>
</section>
```

- [ ] **Step 3: Add entrance animations and transitions**

In the module script, after cold-open animations, add:

```js
const sceneStarts = [35, 95, 165];
for (const start of sceneStarts) {
  tl.to("#transition-bar", { x: "205%", duration: 0.48, ease: "power3.inOut" }, start - 0.28);
  tl.set("#transition-bar", { x: "-105%" }, start + 0.32);
}

tl.from("#scene-geography", { opacity: 0, y: 38, duration: 0.7, ease: "power3.out" }, 35.25);
tl.from("#scene-geography .kicker", { opacity: 0, x: -42, duration: 0.5, ease: "expo.out" }, 35.45);
tl.from("#scene-geography .headline", { opacity: 0, y: 36, duration: 0.6, ease: "power2.out" }, 35.7);
tl.from("#scene-geography .map-board", { opacity: 0, scale: 0.96, duration: 0.55, ease: "back.out(1.2)" }, 36.05);

tl.from("#scene-culture", { opacity: 0, y: 34, duration: 0.7, ease: "power2.out" }, 95.25);
tl.from("#scene-culture .kicker", { opacity: 0, x: -36, duration: 0.5, ease: "circ.out" }, 95.45);
tl.from("#scene-culture .headline", { opacity: 0, scale: 0.95, duration: 0.62, ease: "expo.out" }, 95.72);
tl.from("#scene-culture .map-board", { opacity: 0, y: 28, duration: 0.55, ease: "power3.out" }, 96.08);

tl.from("#scene-development", { opacity: 0, y: 36, duration: 0.7, ease: "power3.out" }, 165.25);
tl.from("#scene-development .kicker", { opacity: 0, x: -46, duration: 0.5, ease: "expo.out" }, 165.45);
tl.from("#scene-development .headline", { opacity: 0, y: 34, duration: 0.62, ease: "back.out(1.1)" }, 165.72);
tl.from("#scene-development .chip", { opacity: 0, y: 24, stagger: 0.1, duration: 0.42, ease: "power2.out" }, 166.12);
```

- [ ] **Step 4: Run lint and inspect**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run lint
npm run inspect
```

Expected: no HyperFrames errors and no text overflow errors.

- [ ] **Step 5: Commit scenes 2-4**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/index.html
git commit -m "feat: add cape verde geography culture scenes"
```

Expected: commit succeeds.

---

### Task 7: Implement Football Rise And Argentina Challenge Scenes

**Files:**
- Modify: `国家专题视频/佛得角世界杯人文专题/index.html`

**Interfaces:**
- Consumes: normalized footage clips `blue-sharks-team.mp4`, `fans-celebration.mp4`, and the graphic/audio assets already wired in.
- Produces: visible scenes `scene-football-rise` and `scene-argentina-challenge`.

- [ ] **Step 1: Add football background layers**

In `index.html`, after `#bg-development`, add:

```html
<video class="background-video" id="bg-football" data-start="225" data-duration="95" data-track-index="0" src="assets/footage/clips/blue-sharks-team.mp4" muted playsinline></video>
<video class="background-video" id="bg-argentina" data-start="320" data-duration="50" data-track-index="0" src="assets/footage/clips/fans-celebration.mp4" muted playsinline></video>
```

- [ ] **Step 2: Add scene HTML**

In `index.html`, after `#scene-development`, add:

```html
<section class="scene" id="scene-football-rise" data-start="225" data-duration="95" data-track-index="10">
  <div class="kicker">蓝鲨队为什么能游到这里</div>
  <h2 class="headline">人口不大，但网络很大</h2>
  <div class="data-board">
    <div class="body">岛屿、欧洲联赛、移民家庭和国家队球衣，汇成同一个方向。</div>
    <div class="chips">
      <span class="chip">旅欧球员</span>
      <span class="chip">Diaspora</span>
      <span class="chip">三场平局出线</span>
      <span class="chip">蓝鲨队</span>
    </div>
  </div>
</section>

<section class="scene" id="scene-argentina-challenge" data-start="320" data-duration="50" data-track-index="10">
  <div class="kicker">32 强 · ARG vs CPV</div>
  <h2 class="headline">挑战世界冠军</h2>
  <div class="match-board">
    <div class="chips">
      <span class="chip">阿根廷 · 卫冕冠军</span>
      <span class="chip">佛得角 · 蓝鲨队</span>
      <span class="chip">地图上的小国</span>
      <span class="chip">世界最大的球场中央</span>
    </div>
  </div>
</section>
```

- [ ] **Step 3: Add transitions and animations**

In the module script, update the `sceneStarts` array:

```js
const sceneStarts = [35, 95, 165, 225, 320];
```

Then add:

```js
tl.from("#scene-football-rise", { opacity: 0, y: 44, duration: 0.72, ease: "power3.out" }, 225.25);
tl.from("#scene-football-rise .kicker", { opacity: 0, x: -52, duration: 0.48, ease: "expo.out" }, 225.48);
tl.from("#scene-football-rise .headline", { opacity: 0, scale: 0.94, duration: 0.64, ease: "back.out(1.25)" }, 225.76);
tl.from("#scene-football-rise .data-board", { opacity: 0, y: 30, duration: 0.55, ease: "power2.out" }, 226.12);
tl.from("#scene-football-rise .chip", { opacity: 0, y: 24, stagger: 0.1, duration: 0.42, ease: "circ.out" }, 226.48);

tl.from("#scene-argentina-challenge", { opacity: 0, y: 40, duration: 0.72, ease: "power3.out" }, 320.25);
tl.from("#scene-argentina-challenge .kicker", { opacity: 0, x: -46, duration: 0.48, ease: "expo.out" }, 320.48);
tl.from("#scene-argentina-challenge .headline", { opacity: 0, scale: 0.92, duration: 0.64, ease: "back.out(1.4)" }, 320.76);
tl.from("#scene-argentina-challenge .match-board", { opacity: 0, y: 32, duration: 0.55, ease: "power2.out" }, 321.1);
tl.to("#scene-argentina-challenge", { opacity: 0, y: -30, duration: 0.9, ease: "power2.in" }, 368.7);
```

- [ ] **Step 4: Run lint and inspect**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run lint
npm run inspect
```

Expected: no HyperFrames errors and no text overflow errors.

- [ ] **Step 5: Commit football scenes**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/index.html
git commit -m "feat: add cape verde football climax scenes"
```

Expected: commit succeeds.

---

### Task 8: Integrate Media Timing, Render Draft, And Fix Layout

**Files:**
- Modify: `国家专题视频/佛得角世界杯人文专题/index.html`
- Modify: `国家专题视频/佛得角世界杯人文专题/data/captions.js`
- Modify: `国家专题视频/佛得角世界杯人文专题/data/storyboard.js`

**Interfaces:**
- Consumes: all previous project files and media assets.
- Produces: `renders/cape-verde-draft.mp4`.

- [ ] **Step 1: Verify data and assets**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run verify:data
npm run check:assets
```

Expected: both commands pass.

- [ ] **Step 2: Run HyperFrames lint and inspect**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run lint
npm run inspect
```

Expected: no errors. If `inspect` reports text overflow, reduce the offending `.headline`, `.body`, `.chip`, or `.caption` font size in `index.html` and rerun this step.

Use these exact reductions before trying any other layout change:

```css
.headline { font-size: 76px; }
.body { font-size: 32px; }
.chip { font-size: 24px; }
.caption { font-size: 38px; }
```

- [ ] **Step 3: Render draft**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run render:draft
```

Expected: `renders/cape-verde-draft.mp4` exists.

- [ ] **Step 4: Probe draft duration and streams**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 renders/cape-verde-draft.mp4
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 renders/cape-verde-draft.mp4
ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=s=x:p=0 renders/cape-verde-draft.mp4
```

Expected:

```text
370.x
audio
1920x1080
```

- [ ] **Step 5: Extract QA frames**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
mkdir -p renders/qa
ffmpeg -y -ss 5 -i renders/cape-verde-draft.mp4 -frames:v 1 renders/qa/005-cold-open.jpg
ffmpeg -y -ss 35 -i renders/cape-verde-draft.mp4 -frames:v 1 renders/qa/035-map.jpg
ffmpeg -y -ss 105 -i renders/cape-verde-draft.mp4 -frames:v 1 renders/qa/105-culture.jpg
ffmpeg -y -ss 185 -i renders/cape-verde-draft.mp4 -frames:v 1 renders/qa/185-development.jpg
ffmpeg -y -ss 250 -i renders/cape-verde-draft.mp4 -frames:v 1 renders/qa/250-football.jpg
ffmpeg -y -ss 345 -i renders/cape-verde-draft.mp4 -frames:v 1 renders/qa/345-argentina.jpg
```

Expected: six JPG files exist. Open them visually and confirm no obvious overlap, blank frame, unreadable caption, or mismatched scene.

- [ ] **Step 6: Commit draft-ready source**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/index.html 国家专题视频/佛得角世界杯人文专题/data/captions.js 国家专题视频/佛得角世界杯人文专题/data/storyboard.js
git commit -m "feat: prepare cape verde draft render"
```

Expected: commit succeeds.

---

### Task 9: Final Fact Check, Final Render, And Delivery Notes

**Files:**
- Create: `国家专题视频/佛得角世界杯人文专题/scripts/verify-render.sh`
- Create: `国家专题视频/佛得角世界杯人文专题/renders/delivery-notes.md`
- Modify: `国家专题视频/佛得角世界杯人文专题/data/sources.js` if the final fact check changes the current football facts.
- Modify: `国家专题视频/佛得角世界杯人文专题/scripts/narration.txt` and `data/captions.js` if the final fact check changes narration.

**Interfaces:**
- Consumes: `renders/cape-verde-final.mp4`.
- Produces: final MP4 and delivery notes with attribution and caveats.

- [ ] **Step 1: Re-check current football facts**

Open and verify these sources in a browser or with web search:

```text
https://www.aljazeera.com/sports/2026/6/28/which-teams-are-in-world-cup-last-32-knockouts-and-what-is-the-schedule
https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026
```

Expected: Cabo Verde vs Argentina remains accurate. If the opponent, schedule, or result has changed, update narration, captions, and source notes before rendering.

- [ ] **Step 2: Create `verify-render.sh`**

Create `国家专题视频/佛得角世界杯人文专题/scripts/verify-render.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

video="${1:-renders/cape-verde-final.mp4}"

duration="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$video")"
width_height="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$video")"
audio_streams="$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$video" | wc -l | tr -d ' ')"

python3 - "$duration" "$width_height" "$audio_streams" <<'PY'
import sys
duration = float(sys.argv[1])
width_height = sys.argv[2]
audio_streams = int(sys.argv[3])
errors = []
if not 300 <= duration <= 480:
    errors.append(f"duration {duration:.2f} is outside 300-480 seconds")
if width_height != "1920x1080":
    errors.append(f"resolution {width_height} is not 1920x1080")
if audio_streams < 1:
    errors.append("final render has no audio stream")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Render verified: {duration:.2f}s, {width_height}, {audio_streams} audio stream(s)")
PY
```

Run:

```bash
chmod +x 国家专题视频/佛得角世界杯人文专题/scripts/verify-render.sh
```

- [ ] **Step 3: Render final**

Run:

```bash
cd 国家专题视频/佛得角世界杯人文专题
npm run lint
npm run inspect
npm run render:final
npm run verify:render
```

Expected:

- `lint` passes.
- `inspect` has no text overflow errors.
- `renders/cape-verde-final.mp4` exists.
- `verify:render` prints `Render verified`.

- [ ] **Step 4: Create delivery notes**

Create `国家专题视频/佛得角世界杯人文专题/renders/delivery-notes.md`:

```markdown
# Delivery Notes

## Output

- Final video: `renders/cape-verde-final.mp4`
- Format: 1920x1080 horizontal MP4
- Duration: verified with `scripts/verify-render.sh`

## Editorial Snapshot

- Football facts checked on 2026-06-28 before final render.
- Cabo Verde are presented as a Round of 32 team facing defending champions Argentina.
- If publishing after another matchday, re-check the bracket and update the description.

## Music Attribution

- Add the BGM attribution required by the selected music source.

## Source Footage Notes

- The video uses short transformed excerpts with Chinese narration, subtitles, and editorial graphics.
- Long unmodified match broadcast sequences are avoided.
```

- [ ] **Step 5: Commit final source and notes**

Run:

```bash
git add 国家专题视频/佛得角世界杯人文专题/scripts/verify-render.sh 国家专题视频/佛得角世界杯人文专题/renders/delivery-notes.md 国家专题视频/佛得角世界杯人文专题/data/sources.js 国家专题视频/佛得角世界杯人文专题/scripts/narration.txt 国家专题视频/佛得角世界杯人文专题/data/captions.js
git commit -m "chore: verify cape verde final render"
```

Expected: commit succeeds. Do not commit `renders/cape-verde-final.mp4` unless the repository is intended to track rendered videos.

---

## Self-Review

Spec coverage:

- 16:9 horizontal HyperFrames project is covered by Tasks 1 and 5.
- "佛的脚下凡，挑战世界冠军" hook and tone shift are covered by Tasks 2, 5, 6, and 7.
- Country geography, culture, development, football rise, and Argentina challenge are covered by Tasks 2, 6, and 7.
- Source research and current-fact snapshot are covered by Tasks 1, 3, and 9.
- Chinese narration, captions, BGM, and audio clarity are covered by Tasks 2, 4, 5, and 8.
- Verification requirements are covered by Tasks 1, 3, 5, 6, 7, 8, and 9.

Placeholder scan:

- No `TBD`, `TODO`, `FIXME`, or "implement later" placeholders are present.
- Steps that modify files include concrete content or exact rules and commands.

Type consistency:

- `sources`, `claims`, `storyboard`, `targetDuration`, and `captions` exports are defined before use.
- `npm run verify:data`, `npm run check:assets`, `npm run lint`, `npm run inspect`, `npm run render:draft`, `npm run render:final`, and `npm run verify:render` are all defined in `package.json`.
