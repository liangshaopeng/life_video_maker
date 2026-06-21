# -*- coding: utf-8 -*-
"""
只重做开场 seg1:重 TTS(新文案、一口气不断句)→ 量新时长 → 级联更新 timeline.json
→ seg1 字幕写成单条(不拆)→ 重建 global.srt。其余段音频/时长不动。
用法: python3 update_intro.py
"""
import os, json, re, subprocess

PROJ = "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
BUILD = cfg.get("build_dir", "build")
AUD, SUB = os.path.join(BUILD, "audio"), os.path.join(BUILD, "subs")
V = cfg.get("voice", {})
VOICE = V.get("name", "zh-CN-YunjianNeural"); RATE = V.get("rate", "+24%")
PITCH = V.get("pitch", "+20Hz"); VOLUME = V.get("volume", "+32%")
PAD = cfg.get("pad", 0.22)

seg1 = cfg["segments"][0]
text = seg1["text"]
mp3 = os.path.join(AUD, "seg1.mp3")
raw = os.path.join(SUB, "seg1_raw.srt")

# 1) 重 TTS 开场
print(f"re-TTS seg1: 「{text}」  voice={VOICE} rate={RATE} pitch={PITCH} vol={VOLUME}")
subprocess.run(["python3", "-m", "edge_tts", "--voice", VOICE, "--rate", RATE,
    "--pitch", PITCH, "--volume", VOLUME, "--text", text,
    "--write-media", mp3, "--write-subtitles", raw], check=True, stderr=subprocess.DEVNULL)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=nk=1:nw=1", p]).decode().strip())

d = dur(mp3)
clip = d + PAD
print(f"seg1 新时长: audio={d:.3f}s clip={clip:.3f}s (旧 clip≈3.292s)")

# 2) seg1 字幕单条不拆,整段显示
def fmt(t):
    h = int(t // 3600); t -= h * 3600; m = int(t // 60); t -= m * 60
    s = int(t); ms = int(round((t - s) * 1000))
    if ms == 1000: s += 1; ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

disp = text.strip()
with open(os.path.join(SUB, "seg1.srt"), "w", encoding="utf-8") as f:
    f.write(f"1\n{fmt(0.1)} --> {fmt(max(0.1, d - 0.03))}\n{disp}\n\n")
print(f"seg1.srt: 单条 → {disp}")

# 3) 级联更新 timeline.json(seg1 变,后续段 clip 不变,仅 start/end 顺移)
TL = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))
TL["segs"][0]["audio"] = round(d, 3)
TL["segs"][0]["clip"] = round(clip, 3)
cum = 0.0
for s in TL["segs"]:
    s["start"] = round(cum, 3)
    s["end"] = round(cum + s["clip"], 3)
    cum += s["clip"]
TL["total"] = round(cum, 3)
json.dump(TL, open(os.path.join(BUILD, "timeline.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"timeline 总时长: {TL['total']:.3f}s")

# 4) 重建 global.srt(按新偏移级联)
def parse(p):
    cues = []
    for b in re.split(r"\n\s*\n", open(p, encoding="utf-8").read().strip()):
        ls = [l for l in b.splitlines() if l.strip()]
        if len(ls) < 2: continue
        m = re.search(r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)", b)
        if not m: continue
        g = list(map(int, m.groups()))
        cues.append((g[0]*3600+g[1]*60+g[2]+g[3]/1000., g[4]*3600+g[5]*60+g[6]+g[7]/1000., ls[-1]))
    return cues

g = []
for s in TL["segs"]:
    off = s["start"]
    for st, en, t in parse(os.path.join(SUB, f"seg{s['seg']}.srt")):
        g.append((off + st, off + en, t))
with open(os.path.join(SUB, "global.srt"), "w", encoding="utf-8") as f:
    for n, (st, en, t) in enumerate(g, 1):
        f.write(f"{n}\n{fmt(st)} --> {fmt(en)}\n{t}\n\n")
print(f"global.srt 重建: {len(g)} 条")
print("DONE")
