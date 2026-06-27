#!/bin/bash
# 混入BGM:解说一开口自动压低音乐(sidechain ducking),整体响度标准化到 -15 LUFS。
# 用法: mix_bgm.sh <输入16x9.mp4> <bgm.mp3> <输出.mp4> [bgm起始秒=45] [bgm音量=0.42]
# 注意:本机 ffmpeg 需含 sidechaincompress/loudnorm(精简版可能缺,用 ffmpeg -filters 确认)。
set -euo pipefail
IN="$1"; BGM="$2"; OUT="$3"; BSTART="${4:-45}"; BVOL="${5:-0.42}"
DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$IN")
FOUT=$(python3 -c "print(f'{$DUR-2.8:.2f}')")
ffmpeg -y -hide_banner -loglevel error -i "$IN" -ss "$BSTART" -i "$BGM" -filter_complex "
[0:a]aformat=channel_layouts=stereo:sample_rates=44100,asplit=2[v1][v2];
[1:a]atrim=0:${DUR},asetpts=N/SR/TB,volume=${BVOL},afade=t=in:st=0:d=1.8,afade=t=out:st=${FOUT}:d=2.8,aformat=channel_layouts=stereo:sample_rates=44100[bg];
[bg][v1]sidechaincompress=threshold=0.05:ratio=9:attack=12:release=350[duck];
[v2][duck]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]
" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k "$OUT"
echo "✅ $OUT"
