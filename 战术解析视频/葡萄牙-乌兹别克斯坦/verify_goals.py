#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_goals.py —— 进球切片"解说↔画面"对齐自检（出一张总览墙，逐球肉眼过）

目的：把"每个进球切片到底拍到没拍到进球过程"从"靠记性逐个抽帧"变成"一条命令出一张墙"。
做法：读 project.json + build/timeline.json，对每个进球段，从最终合成切片 build/clips/clipN.mp4
      里**沿整段时间轴均匀抽 6 帧**（开头→结尾），拼成一行并贴上段名；所有进球竖向叠成 WALL_goals.png。
看墙时只问一句：**这一行里，看得见"射门→球进网"的过程吗？还是只有庆祝/远景回放？**
看不见进球过程 = 这粒球切错了，回去调 footage.start/speed（只重跑 4→5）。

用法:  python3 scripts/verify_goals.py project.json
       python3 scripts/verify_goals.py project.json --frames 6 --width 220 --all
输出:  build/gverify/WALL_goals.png
依赖:  ffmpeg/ffprobe + Pillow（本机 ffmpeg 无 drawtext，文字一律用 Pillow 烧，见 gotchas #2）。
"""
import json, os, sys, subprocess, argparse
from PIL import Image, ImageDraw, ImageFont

# 中文标签字体（同 lib_overlays_v.py；换机器改这里）
CJK_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

def ffprobe_dur(p):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","default=nk=1:nw=1", p], capture_output=True, text=True)
    try: return float(out.stdout.strip())
    except: return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--frames", type=int, default=6, help="每段沿整段均匀抽几帧")
    ap.add_argument("--width", type=int, default=220, help="单帧缩放宽度")
    ap.add_argument("--all", action="store_true", help="连 intro/ending 也出(默认只出进球 beat 段)")
    args = ap.parse_args()

    cfg = json.load(open(args.project))
    bdir = cfg.get("build_dir","build")
    tl = json.load(open(os.path.join(bdir,"timeline.json")))
    segs_tl = {s["id"]: s for s in tl["segs"]}
    clips_dir = os.path.join(bdir,"clips")
    out_dir = os.path.join(bdir,"gverify"); os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".png"): os.remove(os.path.join(out_dir,f))
    try: label_font = ImageFont.truetype(CJK_FONT, 20)
    except Exception: label_font = ImageFont.load_default()

    fr = max(2, args.frames); W = args.width
    rows = []
    for i, seg in enumerate(cfg["segments"], start=1):
        sid = seg["id"]
        if not args.all and seg.get("overlay",{}).get("layout","") != "beat":
            continue
        clip = os.path.join(clips_dir, f"clip{i}.mp4")
        if not os.path.exists(clip):
            print(f"!! 缺切片 {clip}（先跑 assemble_v.py）", file=sys.stderr); continue
        dur = segs_tl.get(sid,{}).get("clip") or ffprobe_dur(clip)
        idx = seg.get("overlay",{}).get("idx",""); kick = seg.get("overlay",{}).get("kicker","")
        imgs = []
        for k in range(fr):
            t = dur*(0.06 + 0.90*k/(fr-1))
            fp = os.path.join(out_dir, f"f_{i:02d}_{k}.png")
            subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-ss",f"{t:.2f}","-i",clip,
                            "-frames:v","1","-vf",f"scale={W}:-1", fp], capture_output=True)
            if os.path.exists(fp): imgs.append(Image.open(fp).convert("RGB"))
        if not imgs: continue
        # 拼一行（左侧留标签栏）
        h = max(im.height for im in imgs); pad=4; lab_w=150
        row = Image.new("RGB", (lab_w + sum(im.width+pad for im in imgs)+pad, h), (18,18,18))
        d = ImageDraw.Draw(row)
        d.text((6,6), f"seg{i}", font=label_font, fill=(255,210,64))
        d.text((6,30), f"{idx}", font=label_font, fill=(150,210,255))
        d.text((6,54), sid, font=label_font, fill=(180,180,180))
        x = lab_w
        for im in imgs:
            row.paste(im, (x, (h-im.height)//2)); x += im.width+pad
        rp = os.path.join(out_dir, f"row_seg{i:02d}_{sid}.png"); row.save(rp)
        rows.append(row); print(f"  row: seg{i} {sid} {idx}  ({kick})")

    if not rows:
        print("没生成任何行——确认已跑过 assemble_v.py、build/clips/ 有切片。", file=sys.stderr); sys.exit(1)
    # 竖向堆叠成总览墙
    Wmax = max(r.width for r in rows); gap=6
    wall = Image.new("RGB", (Wmax, sum(r.height+gap for r in rows)+gap), (8,8,8))
    y=gap
    for r in rows:
        wall.paste(r,(0,y)); y += r.height+gap
    wp = os.path.join(out_dir,"WALL_goals.png"); wall.save(wp)
    print(f"\n✅ 总览墙: {wp}")
    print("逐行看：每行能看见『射门→球进网』的过程吗？只有庆祝/远景=切错,回去调该段 footage.start/speed(只重跑 4→5)。")

if __name__ == "__main__":
    main()
