# -*- coding: utf-8 -*-
"""横版全片渲染:逐章 lib_pitch3d 动画背景 + 烧字幕/章节标题/水印 + 配音 -> clip -> 拼接。
用法: python3 render_h.py [project_h.json] [仅渲染的seg_id]"""
import os, sys, json, subprocess, re
from PIL import Image, ImageDraw, ImageFont
import lib_pitch3d as P

PROJ = sys.argv[1] if len(sys.argv) > 1 else "project_h.json"
ONLY = sys.argv[2] if len(sys.argv) > 2 else None
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir", "build_h"))
TL = json.load(open(os.path.join(BUILD, "timeline.json")))
NAME = cfg.get("name", "video")
CLIPS = os.path.join(BUILD, "clips"); os.makedirs(CLIPS, exist_ok=True)
WM = cfg.get("watermark", "思考的我")
F_CN = "/System/Library/Fonts/Hiragino Sans GB.ttc"
_ff = {}
def fcn(sz, bold=True):
    k = (sz, bold)
    if k not in _ff: _ff[k] = ImageFont.truetype(F_CN, sz, index=2 if bold else 0)
    return _ff[k]

def parse_srt(path):
    cues = []
    if not os.path.exists(path): return cues
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        ls = b.strip().split("\n")
        if len(ls) >= 3:
            m = re.search(r'(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)', ls[1])
            if not m: continue
            st = int(m[1])*3600+int(m[2])*60+int(m[3])+int(m[4])/1000
            en = int(m[5])*3600+int(m[6])*60+int(m[7])+int(m[8])/1000
            cues.append((st, en, "".join(ls[2:])))
    return cues
def active(cues, tt):
    for st, en, t in cues:
        if st <= tt <= en: return t
    return ""

def draw_caption(img, text):
    if not text: return
    d = ImageDraw.Draw(img, "RGBA"); f = fcn(46)
    bb = d.textbbox((0, 0), text, font=f); tw = bb[2]-bb[0]
    x, y = P.W/2, P.H-66
    d.rectangle([x-tw/2-26, y-40, x+tw/2+26, y+40], fill=(8,14,24,160))
    d.text((x, y), text, font=f, fill=(255,255,255,255), anchor="mm", stroke_width=2, stroke_fill=(0,0,0,210))
def draw_title(img, title, sub=""):
    if not title: return
    d = ImageDraw.Draw(img, "RGBA")
    d.text((P.W/2, 72), title, font=fcn(60), fill=(252,209,50,255), anchor="mm", stroke_width=3, stroke_fill=(0,0,0,200))
    if sub:
        d.text((P.W/2, 126), sub, font=fcn(32), fill=(245,248,250,240), anchor="mm", stroke_width=2, stroke_fill=(0,0,0,170))
def draw_wm(img):
    ImageDraw.Draw(img, "RGBA").text((P.W-28, P.H-26), WM, font=fcn(28), fill=(255,255,255,150), anchor="rs")

FPS = 30
listf = os.path.join(BUILD, "concat.txt")
clips_for_concat = []
for seg, tl in zip(cfg["segments"], TL["segs"]):
    i = tl["seg"]; clip = tl["clip"]
    if ONLY and seg["id"] != ONLY: continue
    n = int(round(clip * FPS)); spec = seg.get("pitch", {})
    cues = parse_srt(os.path.join(BUILD, "subs", f"seg{i}.srt"))
    fdir = os.path.join(BUILD, "frames", f"seg{i}"); os.makedirs(fdir, exist_ok=True)
    for fi in range(n):
        tt = fi/FPS
        fr = P.render_frame(spec, tt)
        draw_title(fr, seg.get("title", ""), seg.get("subtitle", ""))
        draw_caption(fr, active(cues, tt))
        draw_wm(fr)
        fr.convert("RGB").save(os.path.join(fdir, f"{fi:04d}.png"))
    aud = os.path.join(BUILD, "audio", f"seg{i}.mp3")
    out = os.path.join(CLIPS, f"clip{i}.mp4")
    vf = f"fade=t=in:st=0:d=0.3,fade=t=out:st={clip-0.3:.2f}:d=0.3"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-framerate","30",
        "-i", os.path.join(fdir, "%04d.png"), "-i", aud, "-vf", vf,
        "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","-t",f"{clip:.3f}", out], check=True)
    clips_for_concat.append(out)
    print(f"→ clip{i}({tl['id']}) {clip:.1f}s {n}帧")

if ONLY:
    print(f"✅ 单章: {clips_for_concat[0] if clips_for_concat else '无'}")
else:
    with open(listf, "w") as lf:
        for c in clips_for_concat: lf.write(f"file '{c}'\n")
    final = os.path.join(ROOT, f"{NAME}.mp4")
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",listf,"-c","copy",final], check=True)
    print(f"✅ 全片: {final}")
