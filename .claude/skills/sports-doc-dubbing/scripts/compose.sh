#!/bin/bash
# 合成成片:原片画面 + 烧录中文字幕(叠加帧) + 中文配音(原声压低垫底) + 响度标准化。
# 用法: bash compose.sh
set -euo pipefail
cd "$(dirname "$0")"
SRC=source/original.mp4
OVL=build/ovl/%05d.png
DUB=build/dub.wav
OUT=卡拉格世界杯预测_中文配音.mp4
BEDVOL="${BEDVOL:-0.09}"   # 英文原声垫底音量(8~10%)

DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$SRC")

# 音频:原声压低做环境垫底 + 中文配音叠加 → loudnorm 到 -15 LUFS
# amix normalize=0 保持各自音量(不被平均压低)
ffmpeg -y -hide_banner -loglevel error \
  -i "$SRC" -framerate 25 -i "$OVL" -i "$DUB" \
  -filter_complex "
    [0:v][1:v]overlay=0:0:eof_action=pass:format=auto[v];
    [0:a]aformat=channel_layouts=stereo:sample_rates=48000,volume=${BEDVOL}[bed];
    [2:a]aformat=channel_layouts=stereo:sample_rates=48000[dub];
    [bed][dub]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mx];
    [mx]loudnorm=I=-15:TP=-1.5:LRA=11[a]
  " \
  -map "[v]" -map "[a]" -t "$DUR" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -preset medium -crf 19 -r 25 \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "✅ 成片: $OUT"
