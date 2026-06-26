# -*- coding: utf-8 -*-
"""
竖屏(1080x1920)合成器 —— 为战术解析视频新写。
每段:真实画面缩成 1080 宽的「带」嵌在中间(y=384),上下用本段画面的模糊压暗版填满(无黑边),
再叠加透明叠加层(顶部/底部文字面板 + 画面带上的 telestrator 标注 + 字幕),配解说音。

支持:
  footage.start  素材秒数(动态画面用)
  footage.speed  <1 慢放(终结镜头突出细节)
  footage.freeze 给定秒数 -> 定格该帧 hold 整段(决策点 telestrator beat 用)
  footage.blur   [[x,y,w,h],...] 画面带内坐标(0..1080,0..608)局部高斯模糊(糊台标等)

用法: python3 assemble_v.py [project.json]  产出 <name>_vertical.mp4(纯解说,无BGM)
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
FINAL=os.path.join(OUTDIR,f"{NAME}_vertical.mp4")
GRADE=cfg.get("grade","eq=contrast=1.07:saturation=1.16:brightness=-0.01")
FOOT_DEF=cfg.get("footage_default")
BLUR_SIGMA=cfg.get("blur_sigma",16)
BAND_TOP=384

def src_of(seg): return os.path.join(ROOT, seg.get("footage",{}).get("src") or FOOT_DEF)

def compose(vsrc, fp, clip, ovlabel, fin=0.2, fout=0.2):
    """[vsrc] 已是 fps=30 的全分辨率画面流 -> 合成 band+模糊bg+叠加层,产出 [v]。
       ovlabel = 叠加层序列的输入标签(如 '1:v' / '2:v')。"""
    s =f"[{vsrc}]split=2[bsrc][bgsrc];"
    s+=f"[bsrc]scale=1080:-2,crop=1080:608,{GRADE}[bnd0];"
    cur="bnd0"
    for bi,rect in enumerate(fp.get("blur",[])):
        bx,by,bw,bh=rect; nb=f"bnd{bi+1}"
        s+=(f"[{cur}]split=2[{cur}m][{cur}s];[{cur}s]crop={bw}:{bh}:{bx}:{by},"
            f"gblur=sigma={BLUR_SIGMA}[{cur}b];[{cur}m][{cur}b]overlay={bx}:{by}[{nb}];")
        cur=nb
    s+=f"[{cur}]null[band];"
    s+=("[bgsrc]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "gblur=sigma=30,eq=brightness=-0.30:saturation=1.02[bg];")
    s+=f"[bg][band]overlay=0:{BAND_TOP}[base];"
    s+=(f"[base][{ovlabel}]overlay=0:0:shortest=0,trim=duration={clip:.3f},setpts=PTS-STARTPTS,"
        f"fade=t=in:st=0:d={fin},fade=t=out:st={clip-fout:.3f}:d={fout}[v]")
    return s

def build_clip(seg,tl):
    i=tl["seg"]; clip=tl["clip"]; fp=seg.get("footage",{})
    src=src_of(seg)
    if not os.path.exists(src): sys.exit(f"素材不存在: {src}")
    ov=os.path.join(BUILD,"overlays",f"seg{i}","%04d.png")
    aud=os.path.join(BUILD,"audio",f"seg{i}.mp3")
    out=os.path.join(CLIPS,f"clip{i}.mp4")
    freeze=fp.get("freeze")

    if freeze is not None:                       # 定格:抽一帧 loop;输入 0=still 1=audio 2=overlay
        frpng=os.path.join(BUILD,f"freeze_seg{i}.png")
        subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(freeze),
            "-i",src,"-frames:v","1","-q:v","2",frpng],check=True)
        vf="[0:v]fps=30[vs];"+compose("vs",fp,clip,"2:v")
        af=f"[1:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"
        cmd=["ffmpeg","-y","-hide_banner","-loglevel","error",
             "-loop","1","-framerate","30","-t",f"{clip:.3f}","-i",frpng,
             "-i",aud,"-framerate","30","-i",ov,
             "-filter_complex",vf+";"+af,
             "-map","[v]","-map","[a]","-r","30","-c:v","libx264","-profile:v","high",
             "-pix_fmt","yuv420p","-preset","medium","-c:a","aac","-b:a","192k","-t",f"{clip:.3f}",out]
        print(f"→ clip{i}({tl['id']}) FREEZE@{freeze}s {clip:.1f}s")
    else:                                        # 动态:输入 0=src 1=overlay 2=audio
        start=fp.get("start",0); speed=fp.get("speed",1.0)
        spd=f"setpts={1.0/speed:.4f}*PTS," if abs(speed-1.0)>1e-3 else ""
        pre=(f"[0:v]trim=start={start}:duration={clip*speed:.3f},setpts=PTS-STARTPTS,{spd}fps=30[vs];")
        vf=pre+compose("vs",fp,clip,"1:v")
        af=f"[2:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"
        cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-i",src,
             "-framerate","30","-i",ov,"-i",aud,
             "-filter_complex",vf+";"+af,
             "-map","[v]","-map","[a]","-r","30","-c:v","libx264","-profile:v","high",
             "-pix_fmt","yuv420p","-preset","medium","-c:a","aac","-b:a","192k","-t",f"{clip:.3f}",out]
        nb=len(fp.get("blur",[]))
        print(f"→ clip{i}({tl['id']}) {os.path.basename(src)}@{start}s x{speed} {clip:.1f}s"+(f" blur×{nb}" if nb else ""))
    subprocess.run(cmd,check=True)
    return out

listf=os.path.join(BUILD,"concat.txt")
with open(listf,"w") as f:
    for seg,tl in zip(cfg["segments"],TL["segs"]):
        f.write(f"file '{build_clip(seg,tl)}'\n")
print("→ 拼接")
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0",
    "-i",listf,"-c","copy",FINAL],check=True)
print(f"✅ 竖屏成片: {FINAL}")
