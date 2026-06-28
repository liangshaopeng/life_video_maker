#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p assets/audio

python3 -m pip install --user edge-tts
python3 -m edge_tts \
  --voice zh-CN-YunjianNeural \
  --rate=-30% \
  --pitch=+4Hz \
  --file scripts/narration.txt \
  --write-media assets/audio/narration.mp3

ffmpeg -y -i assets/audio/narration.mp3 -ar 48000 -ac 2 assets/audio/narration.wav
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 assets/audio/narration.wav
