#!/bin/bash
# 双 BGM 混音:开场一首,指定时间点切到第二首,再对解说做 sidechain ducking。
# 用法: mix_two_bgm.sh <input.mp4> <intro.mp3> <main.mp3> <out.mp4> [switch=12.60] [intro_start=0] [main_start=0] [intro_vol=0.20] [main_vol=0.16]
set -euo pipefail

IN="$1"
INTRO="$2"
MAIN="$3"
OUT="$4"
SWITCH="${5:-12.60}"
INTRO_START="${6:-0}"
MAIN_START="${7:-0}"
INTRO_VOL="${8:-0.20}"
MAIN_VOL="${9:-0.16}"

DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$IN")
read -r TAIL INTRO_FADE_OUT MAIN_FADE_OUT SWITCH_MS <<<"$(python3 - "$DUR" "$SWITCH" <<'PY'
import sys
dur=float(sys.argv[1]); switch=float(sys.argv[2])
tail=max(0.1,dur-switch)
intro_fade=max(0.0,switch-0.45)
main_fade=max(0.0,tail-2.8)
print(f"{tail:.3f} {intro_fade:.3f} {main_fade:.3f} {int(round(switch*1000))}")
PY
)"

ffmpeg -y -hide_banner -loglevel error \
  -i "$IN" -i "$INTRO" -i "$MAIN" \
  -filter_complex "
[0:a]aformat=channel_layouts=stereo:sample_rates=44100,asplit=2[v1][v2];
[1:a]atrim=start=${INTRO_START}:duration=${SWITCH},asetpts=PTS-STARTPTS,volume=${INTRO_VOL},afade=t=in:st=0:d=0.6,afade=t=out:st=${INTRO_FADE_OUT}:d=0.45,aformat=channel_layouts=stereo:sample_rates=44100[bg_intro];
[2:a]atrim=start=${MAIN_START}:duration=${TAIL},asetpts=PTS-STARTPTS,volume=${MAIN_VOL},afade=t=in:st=0:d=0.55,afade=t=out:st=${MAIN_FADE_OUT}:d=2.8,aformat=channel_layouts=stereo:sample_rates=44100,adelay=${SWITCH_MS}|${SWITCH_MS}[bg_main];
[bg_intro][bg_main]amix=inputs=2:duration=longest:dropout_transition=0,atrim=0:${DUR},asetpts=PTS-STARTPTS[music];
[music][v1]sidechaincompress=threshold=0.05:ratio=9:attack=12:release=350[duck];
[v2][duck]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]
" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k "$OUT"

echo "✅ $OUT"
