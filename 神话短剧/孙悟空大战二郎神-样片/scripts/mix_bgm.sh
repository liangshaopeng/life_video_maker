#!/bin/bash
set -euo pipefail
IN="${1:-wukong_erlang_sample_vertical.mp4}"
BGM="${2:-assets/bgm/dark_myth_bgm.wav}"
OUT="${3:-wukong_erlang_sample_final.mp4}"
DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$IN")
FOUT=$(python3 -c "print(f'{$DUR-1.4:.2f}')")
ffmpeg -y -hide_banner -loglevel error -i "$IN" -i "$BGM" -filter_complex "
[0:a]aformat=channel_layouts=stereo:sample_rates=44100,asplit=2[vocal][side];
[1:a]atrim=0:${DUR},asetpts=N/SR/TB,volume=0.38,afade=t=in:st=0:d=0.7,afade=t=out:st=${FOUT}:d=1.4,aformat=channel_layouts=stereo:sample_rates=44100[bgm];
[bgm][side]sidechaincompress=threshold=0.045:ratio=8:attack=10:release=260[ducked];
[vocal][ducked]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]
" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k "$OUT"
echo "$OUT"
