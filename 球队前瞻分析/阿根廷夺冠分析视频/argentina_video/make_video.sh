#!/bin/bash
# 合成:每段(帧序列+配音)→ clip,再 concat → 最终 mp4
set -euo pipefail
cd "$(dirname "$0")"

ROOT="$(pwd)"
FR="$ROOT/build/frames"
AU="$ROOT/build/audio"
OUT_CLIPS="$ROOT/build/clips"
FINAL="/Users/liangshaopeng_backup/code/life/argentina_2026.mp4"
mkdir -p "$OUT_CLIPS"

LIST="$ROOT/build/concat.txt"
: > "$LIST"

for i in 1 2 3 4 5 6; do
  echo "==> encoding clip $i"
  # 视频时长由帧数决定;音频用 apad 补静音到视频长度(-shortest 在视频结束处截断)
  ffmpeg -y -hide_banner -loglevel error \
    -framerate 30 -i "$FR/seg$i/%04d.jpg" \
    -i "$AU/seg$i.aiff" \
    -filter_complex "[1:a]apad,aresample=44100[a]" \
    -map 0:v -map "[a]" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -shortest \
    "$OUT_CLIPS/clip$i.mp4"
  echo "file '$OUT_CLIPS/clip$i.mp4'" >> "$LIST"
done

echo "==> concatenating"
# 各 clip 编码参数一致,可无损 concat
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$FINAL"

echo "==> done: $FINAL"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$FINAL"
