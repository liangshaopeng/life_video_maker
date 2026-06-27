# -*- coding: utf-8 -*-
"""读 project.json + build/timeline.json,对每个含 'pitch' 的段逐帧渲染全屏背景帧
   -> build/pitch/segN/####.png (1080x1920, 30fps)。用法: python3 render_pitch.py [project.json]"""
import os, json, sys, shutil
import lib_pitch as P

PROJ = sys.argv[1] if len(sys.argv) > 1 else "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir", "build"))
TL = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))

for seg, tl in zip(cfg["segments"], TL["segs"]):
    spec = seg.get("pitch")
    if not spec:
        continue
    i = tl["seg"]; clip = tl["clip"]; n = max(1, round(clip * P.FPS))
    outdir = os.path.join(BUILD, "pitch", f"seg{i}")
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)
    for fi in range(n):
        tt = fi / P.FPS
        fr = P.render_pitch_frame(spec, tt)
        fr.convert("RGB").save(os.path.join(outdir, f"{fi:04d}.png"))
    print(f"→ pitch seg{i}({tl['id']}) {n} 帧 ({clip:.1f}s)")
print("✅ 战术板背景帧渲染完成")
