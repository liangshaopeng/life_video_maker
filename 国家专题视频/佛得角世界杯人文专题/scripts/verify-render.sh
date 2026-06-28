#!/usr/bin/env bash
set -euo pipefail

video="${1:-}"

if [[ -z "$video" ]]; then
  echo "usage: bash scripts/verify-render.sh <video.mp4>" >&2
  exit 2
fi

if [[ ! -f "$video" ]]; then
  echo "missing render: $video" >&2
  exit 1
fi

duration="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$video")"
dimensions="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$video")"
audio_streams="$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$video" | wc -l | tr -d ' ')"
size_bytes="$(wc -c < "$video" | tr -d ' ')"

awk -v duration="$duration" 'BEGIN {
  if (duration < 180 || duration > 300) {
    printf "duration %.2fs is outside under-five-minute target\n", duration > "/dev/stderr";
    exit 1;
  }
}'

if [[ "$dimensions" != "1920x1080" ]]; then
  echo "expected 1920x1080, got $dimensions" >&2
  exit 1
fi

if [[ "$audio_streams" -lt 1 ]]; then
  echo "expected at least one audio stream" >&2
  exit 1
fi

if [[ "$size_bytes" -lt 10000000 ]]; then
  echo "render is unexpectedly small: ${size_bytes} bytes" >&2
  exit 1
fi

printf "Verified %s: %.2fs, %s, %s audio stream(s), %s bytes\n" "$video" "$duration" "$dimensions" "$audio_streams" "$size_bytes"
