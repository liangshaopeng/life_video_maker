# -*- coding: utf-8 -*-
"""快速核验 telestrator 圈位:对每个 telestrator 段,抽 freeze 帧→拼成画面带→在 tt=3.6 叠加标注→存 PNG。
不跑配音/全渲染,几秒出图,放大看圈是否落在梅西身上。
用法: python3 verify_marks.py [project.json]"""
import os, json, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_overlays_v as L
from PIL import Image

PROJ=sys.argv[1] if len(sys.argv)>1 else "project.json"
cfg=json.load(open(PROJ,encoding="utf-8"))
ROOT=os.path.dirname(os.path.abspath(PROJ))
BUILD=os.path.join(ROOT,cfg.get("build_dir","build"))
if cfg.get("theme"): L.THEME.update({k:tuple(v) for k,v in cfg["theme"].items()})
src_def=os.path.join(ROOT,cfg.get("footage_default"))
os.makedirs(os.path.join(BUILD,"vchk"),exist_ok=True)
out_list=[]
for seg in cfg["segments"]:
    ov=seg.get("overlay",{})
    if ov.get("layout")!="telestrator": continue
    i=seg["id"]; fr=seg["footage"]["freeze"]
    _s=seg.get("footage",{}).get("src"); src=os.path.join(ROOT,_s) if _s else src_def
    raw=os.path.join(BUILD,"vchk",f"{i}_raw.png")
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(fr),"-i",src,
        "-frames:v","1","-vf","scale=1080:608","-q:v","2",raw],check=True)
    canvas=Image.new("RGBA",(L.W,L.H),(28,28,34,255))
    band=Image.open(raw).convert("RGBA"); canvas.alpha_composite(band,(0,L.BAND_TOP))
    spec=dict(ov); spec.setdefault("idx", i)
    fr_ov=L.render_overlay_frame(spec, 3.6, 8.0)   # tt=3.6 所有标注已出
    canvas.alpha_composite(fr_ov)
    outp=os.path.join(BUILD,"vchk",f"{i}.png")
    canvas.convert("RGB").save(outp)
    out_list.append(outp); print("wrote",outp)
# 拼一张总览(band 区裁出放大看圈)
if out_list:
    crops=[]
    for p in out_list:
        im=Image.open(p).crop((0,L.BAND_TOP-10,L.W,L.BAND_BOT+10))  # 只看画面带
        crops.append(im)
    Wt=max(c.width for c in crops); Ht=sum(c.height for c in crops)
    big=Image.new("RGB",(Wt,Ht),(0,0,0)); y=0
    for c in crops: big.paste(c,(0,y)); y+=c.height
    big.save(os.path.join(BUILD,"vchk_all.png")); print("wrote",os.path.join(BUILD,"vchk_all.png"))
