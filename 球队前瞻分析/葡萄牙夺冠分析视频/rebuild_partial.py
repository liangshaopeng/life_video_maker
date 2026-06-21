# -*- coding: utf-8 -*-
"""
局部重建:只重切受影响的 clip(字幕断句修正),其余 clip 沿用现有文件,
clip10(自定义C罗特写定格+电眼结尾)原样保留,最后整体重拼。
build_clip 逻辑与 skill 的 assemble.py 完全一致(编码参数必须一致才能 -c copy 拼接)。
用法: python3 rebuild_partial.py
"""
import os, json, subprocess, sys

REBUILD = {1}                   # 仅重切开场 clip1(新文案/新时长),其余沿用
PROJ = "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir", "build"))
TL = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))
OUTDIR = os.path.join(ROOT, cfg.get("output_dir", "."))
NAME = cfg.get("name", "video")
CLIPS = os.path.join(BUILD, "clips"); os.makedirs(CLIPS, exist_ok=True)
FINAL = os.path.join(OUTDIR, f"{NAME}_16x9.mp4")
GRADE = cfg.get("grade", "eq=contrast=1.08:saturation=1.18:brightness=-0.015")
FOOT_DEF = cfg.get("footage_default")
BLUR_SIGMA = cfg.get("blur_sigma", 16)

def build_clip(seg, tl):
    i = tl["seg"]; clip = tl["clip"]; fp = seg.get("footage", {})
    src = os.path.join(ROOT, fp.get("src") or FOOT_DEF)
    if not os.path.exists(src): sys.exit(f"素材不存在: {src}")
    ov = os.path.join(BUILD, "overlays", f"seg{i}", "%04d.png")
    aud = os.path.join(BUILD, "audio", f"seg{i}.mp3")
    start = fp.get("start", 0); speed = fp.get("speed", 1.0); fin = fout = 0.18
    spd = f"setpts={1.0/speed:.4f}*PTS," if abs(speed - 1.0) > 1e-3 else ""
    vf = (f"[0:v]trim=start={start}:duration={clip*speed:.3f},setpts=PTS-STARTPTS,{spd}"
          f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,{GRADE},"
          f"fade=t=in:st=0:d={fin},fade=t=out:st={clip-fout:.3f}:d={fout}[v0];")
    cur = "v0"
    for bi, rect in enumerate(fp.get("blur", [])):
        bx, by, bw, bh = rect; nb = f"vb{bi}"
        vf += (f"[{cur}]split=2[{cur}m][{cur}s];"
               f"[{cur}s]crop={bw}:{bh}:{bx}:{by},gblur=sigma={BLUR_SIGMA}[{cur}b];"
               f"[{cur}m][{cur}b]overlay={bx}:{by}[{nb}];")
        cur = nb
    vf += f"[{cur}][1:v]overlay=0:0:shortest=0[v]"
    af = f"[2:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"
    out = os.path.join(CLIPS, f"clip{i}.mp4")
    print(f"→ 重切 clip{i}({tl['id']}) {os.path.basename(src)}@{start}s x{speed} {clip:.1f}s")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
        "-framerate", "30", "-i", ov, "-i", aud, "-filter_complex", vf + ";" + af,
        "-map", "[v]", "-map", "[a]", "-r", "30", "-c:v", "libx264", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{clip:.3f}", out], check=True)
    return out

# 重切受影响段;其余沿用现有 clip 文件
for seg, tl in zip(cfg["segments"], TL["segs"]):
    i = tl["seg"]
    out = os.path.join(CLIPS, f"clip{i}.mp4")
    if i in REBUILD:
        build_clip(seg, tl)
    else:
        if not os.path.exists(out): sys.exit(f"缺少现有 clip: {out}")
        print(f"· 保留 clip{i}({tl['id']})")

# 整体重拼(含 clip10 自定义结尾)
listf = os.path.join(BUILD, "concat.txt")
with open(listf, "w") as f:
    for tl in TL["segs"]:
        cp = os.path.join(CLIPS, "clip%d.mp4" % tl["seg"])
        f.write("file '%s'\n" % cp)
print("→ 拼接")
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
    "-safe", "0", "-i", listf, "-c", "copy", FINAL], check=True)
print(f"✅ 16:9 成片: {FINAL}")
