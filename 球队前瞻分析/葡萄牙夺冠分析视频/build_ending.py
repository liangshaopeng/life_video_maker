# -*- coding: utf-8 -*-
"""
自定义结尾段(clip9):庆祝慢镜(C罗 205-211)→ 硬切到坚毅特写(C罗 411-413.25),
最后一帧定格在 C罗脸上 —— "把那个男人焊死到最后一帧"。
覆盖 assemble 产出的 clip9.mp4,编码参数与其它 clip 完全一致以便 -c copy 拼接。
"""
import os, json, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
SRC = os.path.join(ROOT, "footage/ronaldo_wc_goals.mp4")
GRADE = "eq=contrast=1.08:saturation=1.18:brightness=-0.015"

TL = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))
seg9 = [s for s in TL["segs"] if s["id"] == "ending"][0]
i = seg9["seg"]
clip = seg9["clip"]

# Part B (特写收尾):close-up 411.0 -> 413.25 (2.25s) @0.5x = 4.5s,末帧定格在坚毅脸
B_IN, B_OUT, B_SPEED = 411.0, 413.25, 0.5
partB = (B_OUT - B_IN) / B_SPEED            # 4.5s
partA = clip - partB                          # 其余给庆祝
# Part A (庆祝慢镜):celebration 205.0 -> 211.0 (6s),拉伸填满 partA
A_IN, A_OUT = 205.0, 211.0
A_SPEED = (A_OUT - A_IN) / partA              # <1 = 慢放

ov = os.path.join(BUILD, "overlays", f"seg{i}", "%04d.png")
aud = os.path.join(BUILD, "audio", f"seg{i}.mp3")
out = os.path.join(BUILD, "clips", f"clip{i}.mp4")
fin = 0.18

vf = (
    f"[0:v]split=2[s1][s2];"
    f"[s1]trim={A_IN}:{A_OUT},setpts={1.0/A_SPEED:.4f}*(PTS-STARTPTS),"
    f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,{GRADE},fps=30[a0];"
    f"[s2]trim={B_IN}:{B_OUT},setpts={1.0/B_SPEED:.4f}*(PTS-STARTPTS),"
    f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,{GRADE},fps=30[b0];"
    f"[a0][b0]concat=n=2:v=1:a=0[cat];"
    f"[cat]fade=t=in:st=0:d={fin}[v0];"  # 不做尾部淡出:最后一帧定格在C罗脸上
    f"[v0][1:v]overlay=0:0:shortest=0[v]"
)
af = f"[2:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"

print(f"clip{i}(ending) clip={clip:.2f}s | partA庆祝={partA:.2f}s(x{A_SPEED:.2f}) partB特写={partB:.2f}s(x{B_SPEED}) 末帧={B_OUT}s")
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",SRC,
    "-framerate","30","-i",ov,"-i",aud,"-filter_complex",vf+";"+af,
    "-map","[v]","-map","[a]","-r","30","-c:v","libx264","-profile:v","high",
    "-pix_fmt","yuv420p","-preset","medium","-c:a","aac","-b:a","192k","-t",f"{clip:.3f}",out],
    check=True)
print(f"✅ 覆盖结尾 clip: {out}")
