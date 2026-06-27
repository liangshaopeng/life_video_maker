# -*- coding: utf-8 -*-
"""
读 project.json + timeline.json → 用 lib_overlays 渲染每段透明叠加层帧(含底部字幕)。
用法: python3 render_overlays.py [project.json]
产出: <build>/overlays/seg{i}/####.png  (RGBA)
注意:每次渲染前会清空 overlays 目录,避免旧帧残留污染(段时长变短会留下多余高位帧)。
"""
import os, json, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_overlays as L

PROJ = sys.argv[1] if len(sys.argv)>1 else "project.json"
cfg=json.load(open(PROJ,encoding="utf-8"))
ROOT=os.path.dirname(os.path.abspath(PROJ))
BUILD=os.path.join(ROOT,cfg.get("build_dir","build"))
if cfg.get("theme"): L.THEME.update({k:tuple(v) for k,v in cfg["theme"].items()})
TL=json.load(open(os.path.join(BUILD,"timeline.json"),encoding="utf-8"))
OUT=os.path.join(BUILD,"overlays")
if os.path.isdir(OUT): shutil.rmtree(OUT)
os.makedirs(OUT,exist_ok=True)

for seg,tl in zip(cfg["segments"],TL["segs"]):
    i=tl["seg"]; dur=tl["clip"]; spec=seg.get("overlay",{"layout":"title","title":seg.get("id","")})
    od=os.path.join(OUT,f"seg{i}"); os.makedirs(od,exist_ok=True)
    cues=L.parse_cues(os.path.join(BUILD,"subs",f"seg{i}.srt"))
    n=round(dur*L.FPS)
    WM=cfg.get("watermark")
    for fi in range(n):
        tt=fi/L.FPS
        fr=L.render_overlay_frame(spec,tt,dur)
        L.draw_caption(fr, L.active_caption(cues,tt))
        if WM: L.draw_watermark(fr, WM)
        fr.save(os.path.join(od,f"{fi:04d}.png"))
    print(f"seg{i}({tl['id']}): {n} 帧")
print("OVERLAYS DONE")
