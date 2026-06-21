# -*- coding: utf-8 -*-
"""
读 project.json + timeline.json + overlays → 逐段(实战画面+调色+叠加层+解说)合成,再拼接。
用法: python3 assemble.py [project.json]
产出: <output_dir>/<name>_16x9.mp4 (无BGM,纯解说;BGM由 mix_bgm.sh 处理)
关键点:
  - 段数动态(len(segments)),不要写死循环范围(曾因 range(1,7) 漏掉第7段收尾)。
  - 字幕已烧进叠加层,这里不再处理字幕(本机 ffmpeg 多无 libass)。
  - footage.speed<1 = 慢放:截取 clip*speed 秒素材,用 setpts 拉长回 clip 秒。
  - 各 clip 编码参数必须一致,才能 -c copy 无损拼接。
  - footage.blur=[[x,y,w,h],...] = 局部虚化:在烧字幕"之前"对画面这些矩形做高斯模糊,
    用来糊掉素材自带的台标/比分牌/转播水印(1920x1080 输出坐标)。强度由 blur_sigma 控。
    经验:别整条全宽虚化(中间留空更通透),按"左上比分牌 + 右上对阵标"分两个角块;
    框要盖全文字、sigma 要够大(粗体台标 ~18)才糊得不可读。详见 reference/gotchas.md #11。
"""
import os, json, subprocess, sys

PROJ=sys.argv[1] if len(sys.argv)>1 else "project.json"
cfg=json.load(open(PROJ,encoding="utf-8"))
ROOT=os.path.dirname(os.path.abspath(PROJ))
BUILD=os.path.join(ROOT,cfg.get("build_dir","build"))
TL=json.load(open(os.path.join(BUILD,"timeline.json"),encoding="utf-8"))
OUTDIR=os.path.join(ROOT,cfg.get("output_dir","."))
NAME=cfg.get("name","video")
CLIPS=os.path.join(BUILD,"clips"); os.makedirs(CLIPS,exist_ok=True)
FINAL=os.path.join(OUTDIR,f"{NAME}_16x9.mp4")
GRADE=cfg.get("grade","eq=contrast=1.08:saturation=1.18:brightness=-0.015")
FOOT_DEF=cfg.get("footage_default")
BLUR_SIGMA=cfg.get("blur_sigma",16)   # 局部虚化强度;粗体台标用 ~18

def build_clip(seg,tl):
    i=tl["seg"]; clip=tl["clip"]; fp=seg.get("footage",{})
    src=os.path.join(ROOT, fp.get("src") or FOOT_DEF)
    if not os.path.exists(src): sys.exit(f"素材不存在: {src}")
    ov=os.path.join(BUILD,"overlays",f"seg{i}","%04d.png")
    aud=os.path.join(BUILD,"audio",f"seg{i}.mp3")
    start=fp.get("start",0); speed=fp.get("speed",1.0); fin=fout=0.18
    spd=f"setpts={1.0/speed:.4f}*PTS," if abs(speed-1.0)>1e-3 else ""
    vf=(f"[0:v]trim=start={start}:duration={clip*speed:.3f},setpts=PTS-STARTPTS,{spd}"
        f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,{GRADE},"
        f"fade=t=in:st=0:d={fin},fade=t=out:st={clip-fout:.3f}:d={fout}[v0];")
    cur="v0"                                            # 局部虚化:逐块 split→crop→gblur→overlay
    for bi,rect in enumerate(fp.get("blur",[])):
        bx,by,bw,bh=rect; nb=f"vb{bi}"
        vf+=(f"[{cur}]split=2[{cur}m][{cur}s];"
             f"[{cur}s]crop={bw}:{bh}:{bx}:{by},gblur=sigma={BLUR_SIGMA}[{cur}b];"
             f"[{cur}m][{cur}b]overlay={bx}:{by}[{nb}];")
        cur=nb
    vf+=f"[{cur}][1:v]overlay=0:0:shortest=0[v]"        # 叠加层(图形+字幕)烧在虚化之后
    af=f"[2:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"
    out=os.path.join(CLIPS,f"clip{i}.mp4")
    nb=len(fp.get("blur",[]))
    print(f"→ clip{i}({tl['id']}) {os.path.basename(src)}@{start}s x{speed} {clip:.1f}s"+(f" blur×{nb}" if nb else ""))
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",src,
        "-framerate","30","-i",ov,"-i",aud,"-filter_complex",vf+";"+af,
        "-map","[v]","-map","[a]","-r","30","-c:v","libx264","-profile:v","high",
        "-pix_fmt","yuv420p","-preset","medium","-c:a","aac","-b:a","192k","-t",f"{clip:.3f}",out],
        check=True)
    return out

listf=os.path.join(BUILD,"concat.txt")
with open(listf,"w") as f:
    for seg,tl in zip(cfg["segments"],TL["segs"]):   # 动态段数
        f.write(f"file '{build_clip(seg,tl)}'\n")
print("→ 拼接")
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0",
    "-i",listf,"-c","copy",FINAL],check=True)
print(f"✅ 16:9 成片: {FINAL}")
