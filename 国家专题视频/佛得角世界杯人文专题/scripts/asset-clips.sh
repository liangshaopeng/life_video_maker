#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

raw_dir="assets/footage/raw-hq"
clip_dir="assets/footage/clips"
work_dir="assets/footage/work"

mkdir -p "$clip_dir" "$work_dir"

encode_segment() {
  local src="$1"
  local start="$2"
  local duration="$3"
  local out="$4"

  if [[ ! -f "$raw_dir/$src" ]]; then
    echo "missing source clip: $raw_dir/$src" >&2
    exit 1
  fi

  ffmpeg -y -ss "$start" -i "$raw_dir/$src" -t "$duration" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,eq=contrast=1.06:saturation=1.08:brightness=0.015" \
    -an -r 30 -c:v libx264 -pix_fmt yuv420p -crf 18 -preset veryfast \
    -g 30 -keyint_min 30 -sc_threshold 0 -movflags +faststart "$out"
}

scene_clip() {
  local out="$1"
  shift

  local base="${out%.mp4}"
  local list="$work_dir/${base}.txt"
  rm -f "$list"

  local index=0
  for spec in "$@"; do
    IFS=":" read -r src start duration <<< "$spec"
    local segment="$work_dir/${base}-${index}.mp4"
    encode_segment "$src" "$start" "$duration" "$segment"
    printf "file '%s/%s'\n" "$(pwd)" "$segment" >> "$list"
    index=$((index + 1))
  done

  ffmpeg -y -f concat -safe 0 -i "$list" -c copy -movflags +faststart "$clip_dir/$out"
}

scene_clip "hook-main.mp4" \
  "underdog-a.mp4:0:8" \
  "fans-celebration-hq.mp4:0:6" \
  "travel-a.mp4:0:7" \
  "underdog-a.mp4:18:5" \
  "fans-b.mp4:0:4"

scene_clip "geography-main.mp4" \
  "travel-a.mp4:5:10" \
  "travel-b.mp4:0:10" \
  "dw-a.mp4:0:6"

scene_clip "culture-main.mp4" \
  "morna-live.mp4:0:16" \
  "travel-b.mp4:10:7" \
  "morna-live.mp4:18:5"

scene_clip "development-main.mp4" \
  "dw-a.mp4:2:10" \
  "dw-b.mp4:0:10" \
  "travel-b.mp4:20:7"

scene_clip "football-network-main.mp4" \
  "underdog-a.mp4:5:10" \
  "underdog-b.mp4:0:10" \
  "fans-b.mp4:0:5" \
  "underdog-a.mp4:20:5"

scene_clip "football-system-main.mp4" \
  "underdog-b.mp4:8:9" \
  "fans-celebration-hq.mp4:5:7" \
  "underdog-a.mp4:15:6" \
  "fans-b.mp4:9:5"

scene_clip "argentina-main.mp4" \
  "fans-b.mp4:5:8" \
  "underdog-b.mp4:18:10" \
  "fans-celebration-hq.mp4:10:10"

scene_clip "close-main.mp4" \
  "travel-a.mp4:16:6" \
  "travel-b.mp4:18:8" \
  "fans-b.mp4:13:8" \
  "underdog-b.mp4:25:7"

master_list="$work_dir/main-cut.txt"
rm -f "$master_list"
for clip in \
  "hook-main.mp4" \
  "geography-main.mp4" \
  "culture-main.mp4" \
  "development-main.mp4" \
  "football-network-main.mp4" \
  "football-system-main.mp4" \
  "argentina-main.mp4" \
  "close-main.mp4"; do
  printf "file '%s/%s/%s'\n" "$(pwd)" "$clip_dir" "$clip" >> "$master_list"
done

ffmpeg -y -f concat -safe 0 -i "$master_list" -c copy -movflags +faststart "$clip_dir/main-cut.mp4"
