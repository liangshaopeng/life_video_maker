#!/bin/bash
# 生成一小段预览(检查口型对位/字幕/混音),不做整片渲染。
# 用法: bash preview.sh <起始秒> <时长秒> [输出名]
set -euo pipefail
cd "$(dirname "$0")"
T0="${1:-628}"; D="${2:-90}"; OUT="${3:-preview.mp4}"
F0=$(python3 -c "print(round($T0*25))")
ffmpeg -y -hide_banner -loglevel error \
  -ss "$T0" -t "$D" -i source/original.mp4 \
  -framerate 25 -start_number "$F0" -i build/ovl/%05d.png \
  -ss "$T0" -t "$D" -i build/dub.wav \
  -filter_complex "
    [0:v][1:v]overlay=0:0:eof_action=pass:format=auto[v];
    [0:a]aformat=channel_layouts=stereo:sample_rates=48000,volume=0.09[bed];
    [2:a]aformat=channel_layouts=stereo:sample_rates=48000[dub];
    [bed][dub]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mx];
    [mx]loudnorm=I=-15:TP=-1.5:LRA=11[a]
  " \
  -map "[v]" -map "[a]" -t "$D" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -preset veryfast -crf 20 -r 25 \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "✅ 预览: $OUT (${T0}s +${D}s)"
