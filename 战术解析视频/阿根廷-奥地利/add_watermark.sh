#!/bin/bash
# 把水印 PNG 叠到成片角落(默认右下),保留音轨。本机 ffmpeg 无 drawtext,所以水印走 PNG overlay。
# 用法: add_watermark.sh <输入.mp4> <水印.png> <输出.mp4> [位置=br] [边距=40:30]
#   位置: br=右下 bl=左下 tr=右上 tl=左上
# 注意:在 16:9 成片上叠水印,再做 make_vertical.sh,水印会跟着内容带走(竖版也带)。
set -euo pipefail
IN="$1"; WM="$2"; OUT="$3"; POS="${4:-br}"; MARGIN="${5:-40:30}"
MX="${MARGIN%%:*}"; MY="${MARGIN##*:}"
case "$POS" in
  br) XY="W-w-${MX}:H-h-${MY}";;
  bl) XY="${MX}:H-h-${MY}";;
  tr) XY="W-w-${MX}:${MY}";;
  tl) XY="${MX}:${MY}";;
  *)  XY="W-w-${MX}:H-h-${MY}";;
esac
ffmpeg -y -hide_banner -loglevel error -i "$IN" -i "$WM" \
  -filter_complex "[0:v][1:v]overlay=${XY}[v]" -map "[v]" -map 0:a \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -preset medium -c:a copy "$OUT"
echo "✅ $OUT"
