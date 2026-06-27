# -*- coding: utf-8 -*-
"""
读 build/cues.json + 原片时长 → 渲染底部中文字幕的透明叠加帧序列 build/ovl/#####.png
本机 ffmpeg 无 libass/drawtext,故用 Pillow 画字幕再 overlay(沿用现有项目做法)。
相同字幕的帧用硬链接去重,真正渲染的图≈不同字幕条数。
字幕带半透明压暗(scrim)只在有字幕时出现,保证亮画面上也清晰。
用法: python3 render_subs.py
"""
import os, json, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

ROOT=os.path.dirname(os.path.abspath(__file__)); BUILD=os.path.join(ROOT,"build")
W,H = 1920,1080
FPS = 25
F_CN="/System/Library/Fonts/Hiragino Sans GB.ttc"
FNT=ImageFont.truetype(F_CN,52,index=2)   # W6 粗
MAXW=1560; LH=66; BASEY=1014; STROKE=4

def vdur():
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","default=nk=1:nw=1",os.path.join(ROOT,"source","original.mp4")]).decode().strip())

# 底部 scrim(只在有字幕时贴)
def make_scrim():
    col=Image.new("RGBA",(1,H),(0,0,0,0)); p=col.load(); botH=300
    for y in range(H):
        a=int(165*((y-(H-botH))/botH)) if y>H-botH else 0
        p[0,y]=(0,0,10,max(0,a))
    return col.resize((W,H))
SCRIM=make_scrim()

_md=ImageDraw.Draw(Image.new("RGBA",(8,8)))
def wrap(text):
    lines=[]; cur=""
    for ch in text:
        if _md.textlength(cur+ch,font=FNT)>MAXW and cur: lines.append(cur); cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return lines
def ctext(d,cx,cy,s):
    w=d.textlength(s,font=FNT)
    d.text((cx-w/2,cy),s,font=FNT,fill=(255,255,255,255),stroke_width=STROKE,stroke_fill=(8,12,22,255))

def render_caption(text,path):
    f=Image.new("RGBA",(W,H),(0,0,0,0))
    f.alpha_composite(SCRIM)
    d=ImageDraw.Draw(f)
    lines=wrap(text); n=len(lines)
    for k,ln in enumerate(lines):
        ctext(d,W//2,BASEY-(n-1-k)*LH,ln)
    f.save(path)

def main():
    cues=json.load(open(os.path.join(BUILD,"cues.json"),encoding="utf-8"))
    dur=vdur(); N=round(dur*FPS)
    OUT=os.path.join(BUILD,"ovl")
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)

    # 空帧(全透明)
    empty=os.path.join(OUT,"_empty.png")
    Image.new("RGBA",(W,H),(0,0,0,0)).save(empty)
    # 每条不同字幕渲染一张
    cache={}   # text -> png path
    def img_for(text):
        if not text: return empty
        if text not in cache:
            p=os.path.join(OUT,f"_c{len(cache):04d}.png"); render_caption(text,p); cache[text]=p
        return cache[text]

    # 逐帧:二分定位当前 cue
    cues_s=sorted(cues,key=lambda c:c[0])
    def active(t):
        for st,en,tx in cues_s:
            if st<=t<en: return tx
            if st>t: break
        return ""

    prev=None
    for fi in range(N):
        t=fi/FPS; tx=active(t); src=img_for(tx)
        dst=os.path.join(OUT,f"{fi:05d}.png")
        os.link(src,dst)
        if fi%2000==0: print(f"frame {fi}/{N}",flush=True)
    print(f"OVL DONE: {N} 帧, 唯一字幕图 {len(cache)} 张")

if __name__=="__main__":
    main()
