---
name: national-topic-video
description: Use when making a researched Chinese country/region feature video (国家专题/地区专题/人文地理/发展情况/文化介绍/体育热点) with HyperFrames, real web or YouTube footage, sharp narration, synced captions, source notes, and final render verification. Especially for requests like "做一期某国家视频", "结合世界杯表现讲国家", "横屏 5-8 分钟", "搜视频资料剪切成片".
---

# 国家专题视频制作

## Core Idea

Turn a country or region into a fast, opinionated feature video: real footage first, Chinese commentary as the spine, and geography/culture/development/sports facts serving one clear thesis. Do not make a slow encyclopedia intro.

**Required sub-skills:** Use `hyperframes:hyperframes` and `hyperframes:hyperframes-cli` for composition, captions, preview, inspection, and rendering. Use the sports video skills only when the request is primarily match highlights or tactical analysis.

Read `references/production-checklist.md` before starting a full production or substantial revision.

## Choose This Skill

Use this skill for:
- A country/region explainer with a current hook: World Cup, Olympics, conflict, economy, tourism, culture, migration, or underdog sports story.
- Horizontal B站/YouTube-style videos or short-form cuts that need research + narration + footage montage.
- Workflows where the user asks to search YouTube/web, collect knowledge, cut footage, add subtitles, and render a finished MP4.

Do not use it as the main skill for:
- Pure football/basketball highlight ranking videos: use `sports-highlight-video`.
- Per-goal tactical mechanism breakdowns: use `football-tactical-analysis-video`.
- Foreign interview/documentary dubbing: use `sports-doc-dubbing`.

## Production Workflow

1. **Lock the brief.** Infer or confirm aspect ratio, runtime, tone, hook, platform, and language.
2. **Research current facts.** Browse for unstable facts and keep source URLs in project data or delivery notes.
3. **Search footage deliberately.** Use clear real footage as the main image; collect geography, culture, development, sports, fan, and closing-emotion shots.
4. **Write a thesis-led spine.** Build 6-9 scenes: hook -> geography -> culture -> development pressure -> sports system -> current stakes -> payoff.
5. **Write fast Chinese narration.** Use short claims, creator voice, and sharper观点. If pacing feels slow, tighten text and TTS rate before speeding the final video.
6. **Build in HyperFrames.** Place projects under `国家专题视频/<topic>/`; include `DESIGN.md`, `data/`, `scripts/`, `assets/`, `renders/`, and package scripts for captions, lint, inspect, render, and verification.
7. **Cut footage as footage, not wallpaper.** Preassemble crisp full-screen clips into a main video bed. Avoid blurred low-resolution backgrounds.
8. **Keep captions player-safe.** Use short synced captions. If bottom controls or lower-thirds collide, move captions to top-center.
9. **Verify before delivery.** Run data/asset checks, HyperFrames lint/inspect, render verification, and visual QA frames. Update delivery notes.

## Delivery Contract

Before saying the video is done, provide:
- Final MP4 path.
- Runtime, resolution, audio-stream verification, and file size.
- A representative QA frame or contact sheet path.
- Source/fact notes and any usage-rights caveat.
- Commands run for verification.
