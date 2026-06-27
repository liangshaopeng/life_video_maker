# Wukong Erlang Motion Enhancement Design

## Goal

Turn the current 30-second `孙悟空大战二郎神` sample from a lightly zooming keyframe montage into a stronger dark-myth trailer cut that feels alive on Douyin/video-channel playback.

## Root Cause

The first export uses six generated keyframes as looped still images. `project.json` contains `pan_x` and `pan_y`, but `scripts/assemble_sample.py` centers every `zoompan` frame and ignores those pan targets. `scripts/render_overlays.py` renders text overlays only, so action notes such as weapon impact, lightning, sparks, and shockwave exist in the prompts but not in the final video layer. The result feels like image slices rather than animated action.

## Chosen Approach

Use a mixed strong-motion pass before any external image-to-video workflow:

- Keep the six original AI keyframes and existing narration/BGM.
- Add data-driven camera motion per shot: stronger zooms, directional pan start/end, and controlled impact shake.
- Add frame-level cinematic overlays: blue heavenly-eye scan, amber sparks, white impact flash, shockwave rings, smoke/fog streaks, clone-break shards, speed lines, and vignette pulses.
- Keep subtitles and title text readable by drawing dynamic effects behind text overlays.
- Re-export the same final contract: `wukong_erlang_sample_vertical.mp4` and `wukong_erlang_sample_final.mp4`, 1080x1920, about 30 seconds, with audio.

## Scope

This pass does not make character limbs truly articulate frame by frame. It creates a dynamic trailer-style motion comic from the existing keyframes. If the user likes the style, the next iteration can replace 2-3 hero shots with external image-to-video clips.

## Files

- Modify `神话短剧/孙悟空大战二郎神-样片/project.json` to add optional motion metadata.
- Modify `神话短剧/孙悟空大战二郎神-样片/scripts/assemble_sample.py` to use directional pan and shake in the `zoompan` filter.
- Modify `神话短剧/孙悟空大战二郎神-样片/scripts/render_overlays.py` to render frame-varying action effects.
- Modify `tests/test_wukong_sample_scripts.py` with regression tests for motion parsing, ffmpeg filter generation, and dynamic overlay variation.

## Verification

- Run targeted tests for the new motion helpers and overlay effects.
- Run the full Wukong sample test suite.
- Re-render overlays, assemble the no-BGM vertical video, mix BGM, and inspect final stream metadata.
- Generate QA thumbnails and verify the final video is portrait, about 30 seconds, and includes audio.
