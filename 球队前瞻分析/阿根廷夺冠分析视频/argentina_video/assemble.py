# -*- coding: utf-8 -*-
"""
合成实战版:每段 = 实战画面(裁切/调色) + 透明叠加层 + 烧入字幕 + 云健解说。
再拼接6段 -> 最终 mp4。FOOTAGE_PLAN 决定每段取素材的哪一段。
用法: python3 assemble.py
"""
import os, json, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(ROOT, "build")
TL = json.load(open(os.path.join(B, "timeline.json"), encoding="utf-8"))
SEGS = TL["segs"]
OUTCLIPS = os.path.join(B, "clips_v2"); os.makedirs(OUTCLIPS, exist_ok=True)
FINAL = os.path.join(os.path.dirname(ROOT), "argentina_2026_v2.mp4")

# ── 镜头计划:每段从哪个素材文件、哪个起点取画面 ──
# src: footage 下的文件名;start: 起始秒;speed: 可选播放倍速(<1 慢动作)
FOOTAGE_DEFAULT = "final720.mp4"
# 镜头计划:从《阿根廷vs法国决赛》(2099s)挑的最贴题片段(避开法国特写)
FOOTAGE_PLAN = {
 1: {"src": FOOTAGE_DEFAULT, "start": 520,  "speed": 1.0},   # 决赛攻防(冠军在场上)
 2: {"src": FOOTAGE_DEFAULT, "start": 1920, "speed": 1.0},   # 阿根廷球员夺冠拥抱
 3: {"src": FOOTAGE_DEFAULT, "start": 1940, "speed": 1.0},   # 全队草皮狂欢
 4: {"src": FOOTAGE_DEFAULT, "start": 2030, "speed": 1.0},   # 梅西特写(配"39岁/最后一届")
 5: {"src": FOOTAGE_DEFAULT, "start": 340,  "speed": 0.5},   # 迪马利亚射门骗洛里·弹地破门回放(重度慢放)
 6: {"src": FOOTAGE_DEFAULT, "start": 1740, "speed": 1.0},   # 马丁内斯点球大战
 7: {"src": FOOTAGE_DEFAULT, "start": 2090, "speed": 0.85},  # 举杯+烟花(略慢放,史诗感)
}

# 字幕样式(libass):白字黑边,底部居中,避开叠加层
SUB_STYLE = ("FontName=Hiragino Sans GB,Fontsize=19,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00101820,BorderStyle=1,Outline=3,Shadow=1,"
             "Alignment=2,MarginV=46,Bold=1")

def srt_to_ass(srt_path, ass_path):
    """把全局SRT转成带样式的ASS(样式内嵌,烧制时用 ass 滤镜,免去转义问题)"""
    import re
    def to_cs(t):  # h:mm:ss.cs
        h=int(t//3600); t-=h*3600; m=int(t//60); t-=m*60; s=int(t); cs=int(round((t-s)*100))
        if cs==100: s+=1; cs=0
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    cues=[]
    for blk in re.split(r"\n\s*\n", open(srt_path,encoding="utf-8").read().strip()):
        ls=[l for l in blk.splitlines() if l.strip()]
        if len(ls)<2: continue
        mm=re.search(r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)",blk)
        if not mm: continue
        g=list(map(int,mm.groups()))
        st=g[0]*3600+g[1]*60+g[2]+g[3]/1000.0
        en=g[4]*3600+g[5]*60+g[6]+g[7]/1000.0
        cues.append((st,en,ls[-1]))
    head=("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n"
          "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
          "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
          "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
          "Alignment,MarginL,MarginR,MarginV,Encoding\n"
          "Style: Default,Hiragino Sans GB,58,&H00FFFFFF,&H00FFFFFF,&H00141820,&H64000000,"
          "1,0,0,0,100,100,0,0,1,3.5,1.2,2,120,120,54,1\n\n[Events]\n"
          "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    with open(ass_path,"w",encoding="utf-8") as f:
        f.write(head)
        for st,en,t in cues:
            f.write(f"Dialogue: 0,{to_cs(st)},{to_cs(en)},Default,,0,0,0,,{t}\n")

def build_clip(i):
    seg = SEGS[i-1]; clip = seg["clip"]
    plan = FOOTAGE_PLAN[i]
    src = os.path.join(ROOT, "footage", plan["src"])
    if not os.path.exists(src):
        sys.exit(f"❌ 素材不存在: {src}")
    ov = os.path.join(B, "overlays", f"seg{i}", "%04d.png")
    aud = os.path.join(B, "audio_v2", f"seg{i}.mp3")
    speed = plan.get("speed", 1.0)
    fin, fout = 0.18, 0.18
    # 视频链:取素材 -> 倍速 -> 填满裁切1080p -> 调色 -> 进出淡 -> 叠加层(字幕最后统一烧)
    spd = f"setpts={1.0/speed:.4f}*PTS," if abs(speed-1.0)>1e-3 else ""
    vfilter = (
        f"[0:v]trim=start={plan['start']}:duration={clip*speed:.3f},setpts=PTS-STARTPTS,"
        f"{spd}"
        f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
        f"eq=contrast=1.08:saturation=1.18:brightness=-0.015,"
        f"fade=t=in:st=0:d={fin},fade=t=out:st={clip-fout:.3f}:d={fout}[v0];"
        f"[v0][1:v]overlay=0:0:shortest=0[v]"
    )
    afilter = f"[2:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"
    out = os.path.join(OUTCLIPS, f"clip{i}.mp4")
    cmd = ["ffmpeg","-y","-hide_banner","-loglevel","error",
        "-i", src,
        "-framerate","30","-i", ov,
        "-i", aud,
        "-filter_complex", vfilter+";"+afilter,
        "-map","[v]","-map","[a]","-r","30",
        "-c:v","libx264","-profile:v","high","-pix_fmt","yuv420p","-preset","medium",
        "-c:a","aac","-b:a","192k","-t",f"{clip:.3f}", out]
    print(f"→ clip{i} (素材 {plan['src']} @{plan['start']}s, 时长 {clip:.2f}s)")
    subprocess.run(cmd, check=True)
    return out

def main():
    listfile = os.path.join(B, "concat_v2.txt")
    with open(listfile,"w") as f:
        for i in range(1, len(FOOTAGE_PLAN)+1):
            c = build_clip(i)
            f.write(f"file '{c}'\n")
    print("→ 拼接(字幕已烧进叠加层)")
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
        "-f","concat","-safe","0","-i",listfile,"-c","copy",FINAL], check=True)
    print(f"✅ 成片: {FINAL}")
    subprocess.run(["ffprobe","-v","error","-show_entries",
        "format=duration,size","-of","default=noprint_wrappers=1",FINAL])

if __name__=="__main__":
    main()
