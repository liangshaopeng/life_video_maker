# -*- coding: utf-8 -*-
"""抽指定秒的帧,缩成画面带尺寸(1080x608),叠 band 坐标网格,供肉眼读 telestrator 坐标。
用法: python3 gridframe.py <src> <sec> <out.png>"""
import sys, subprocess, os
from PIL import Image, ImageDraw, ImageFont
src,sec,out=sys.argv[1],sys.argv[2],sys.argv[3]
tmp=out+".raw.png"
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",sec,"-i",src,
    "-frames:v","1","-vf","scale=1080:608","-q:v","2",tmp],check=True)
im=Image.open(tmp).convert("RGB"); d=ImageDraw.Draw(im)
fnt=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf",20)
for x in range(0,1081,90):
    d.line([(x,0),(x,608)],fill=(255,80,80) if x%180==0 else (90,90,90),width=1)
    if x%180==0: d.text((x+2,2),str(x),font=fnt,fill=(255,255,0))
for y in range(0,609,76):
    d.line([(0,y),(1080,y)],fill=(255,80,80) if y%152==0 else (90,90,90),width=1)
    if y%152==0: d.text((2,y+2),str(y),font=fnt,fill=(0,255,255))
im.save(out); os.remove(tmp)
print("saved",out)
