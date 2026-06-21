#!/bin/bash
# 16:9 → 9:16 竖版:画面居中,上下用本帧模糊+压暗填满(无黑边)。保留全部图形字幕。
# 用法: make_vertical.sh <输入16x9.mp4> <输出竖版.mp4>
# 这是"保内容"的稳妥做法;若要真·满屏铺开,需把 W,H 改 1080x1920 重排叠加层(见 SKILL.md)。
set -euo pipefail
IN="$1"; OUT="$2"
ffmpeg -y -hide_banner -loglevel error -i "$IN" -filter_complex "
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.20:saturation=1.05[bg];
[0:v]scale=1080:-2[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[v]
" -map "[v]" -map 0:a -c:v libx264 -profile:v high -pix_fmt yuv420p -preset medium -c:a copy "$OUT"
echo "✅ $OUT"
