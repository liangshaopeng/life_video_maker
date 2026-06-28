#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p assets/footage/clips

clip() {
  local src="$1"
  local start="$2"
  local dur="$3"
  local out="$4"
  ffmpeg -y -ss "$start" -i "assets/footage/$src" -t "$dur" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1" \
    -an -c:v libx264 -pix_fmt yuv420p -crf 20 -preset veryfast "assets/footage/$out"
}

ffmpeg -y -f lavfi -i "color=c=0x061B2E:s=1920x1080:r=30:d=8" \
  -vf "format=yuv420p,noise=alls=8:allf=t+u,eq=contrast=1.12:saturation=1.08" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset veryfast "assets/footage/clips/stadium-lights.mp4"

ffmpeg -y -f lavfi -i "color=c=0x111217:s=1920x1080:r=30:d=15" \
  -vf "format=yuv420p,noise=alls=10:allf=t+u,eq=contrast=1.2:saturation=0.75" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset veryfast "assets/footage/clips/fogo-volcano.mp4"

ffmpeg -y -f lavfi -i "color=c=0x0B3558:s=1920x1080:r=30:d=18" \
  -vf "format=yuv420p,noise=alls=6:allf=t+u,eq=contrast=1.05:saturation=1.15" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset veryfast "assets/footage/clips/morna-performance.mp4"

clip "raw/cape-verde-travel.mp4" 0 18 "clips/atlantic-drone.mp4"
clip "raw/dw-cape-verde.mp4" 0 18 "clips/sal-tourism.mp4"
clip "raw/cape-verde-underdog.mp4" 0 20 "clips/blue-sharks-team.mp4"
clip "raw/fans-celebration.mp4" 0 15 "clips/fans-celebration.mp4"
