#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p assets/footage/clips

clip() {
  local src="$1"
  local dur="$2"
  local out="$3"
  ffmpeg -y -stream_loop -1 -i "assets/footage/$src" -t "$dur" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1" \
    -an -r 30 -c:v libx264 -pix_fmt yuv420p -crf 23 -preset veryfast \
    -g 30 -keyint_min 30 -sc_threshold 0 -movflags +faststart "assets/footage/$out"
}

texture() {
  local color="$1"
  local dur="$2"
  local out="$3"
  local filter="$4"
  ffmpeg -y -f lavfi -i "color=c=${color}:s=1920x1080:r=30:d=${dur}" \
    -vf "format=yuv420p,noise=alls=2:allf=t+u,${filter}" \
    -an -r 30 -c:v libx264 -pix_fmt yuv420p -crf 24 -preset veryfast \
    -g 30 -keyint_min 30 -sc_threshold 0 -movflags +faststart "assets/footage/$out"
}

texture "0x061B2E" 30 "clips/stadium-lights.mp4" \
  "eq=contrast=1.12:saturation=1.08,vignette=PI/5"

texture "0x111217" 23 "clips/fogo-volcano.mp4" \
  "eq=contrast=1.2:saturation=0.75,vignette=PI/4"

texture "0x0B3558" 60 "clips/morna-performance.mp4" \
  "eq=contrast=1.05:saturation=1.15,vignette=PI/5"

clip "raw/cape-verde-travel.mp4" 51 "clips/atlantic-drone.mp4"
clip "raw/dw-cape-verde.mp4" 51 "clips/sal-tourism.mp4"
clip "raw/cape-verde-underdog.mp4" 81 "clips/blue-sharks-team.mp4"
clip "raw/fans-celebration.mp4" 44 "clips/fans-celebration.mp4"
