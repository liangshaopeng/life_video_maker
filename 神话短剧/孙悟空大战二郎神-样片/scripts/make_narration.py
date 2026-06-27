# -*- coding: utf-8 -*-
"""
读 project.json → 用 edge-tts 生成每段激情解说 + 逐句细分字幕 + 时间轴。
用法: python3 make_narration.py [project.json]
产出: <build>/audio/seg{i}.mp3, <build>/subs/seg{i}.srt, <build>/subs/global.srt, <build>/timeline.json
依赖: pip3 install edge-tts ; ffmpeg/ffprobe
"""
import json
import os
import re
import subprocess
import sys


PROJ = sys.argv[1] if len(sys.argv) > 1 else "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir", "build"))
AUD, SUB = os.path.join(BUILD, "audio"), os.path.join(BUILD, "subs")
os.makedirs(AUD, exist_ok=True)
os.makedirs(SUB, exist_ok=True)

V = cfg.get("voice", {})
VOICE = V.get("name", "zh-CN-YunjianNeural")
RATE = V.get("rate", "+20%")
PITCH = V.get("pitch", "+16Hz")
VOLUME = V.get("volume", "+15%")
PAD = cfg.get("pad", 0.35)
CAP_MAXLEN = cfg.get("caption_maxlen", 16)
NO_SPLIT = cfg.get("no_split", [])
HOMO = cfg.get("tts_homophones", {})
PUNC = "，,。！!？?、；;：:"
STRONG = "。！？!?"
SOFT = "，,、；;：:"
GLUE_HEAD = "就是的了吧呢吗啊呀和与跟也都还把被对向给"


def _parse_rate_percent(rate):
    m = re.fullmatch(r"([+-]?)(\d+(?:\.\d+)?)%", str(rate).strip())
    if not m:
        return None
    sign = -1 if m.group(1) == "-" else 1
    return sign * float(m.group(2))


def _format_rate_percent(rate):
    rate = int(round(rate))
    sign = "+" if rate >= 0 else "-"
    return f"{sign}{abs(rate)}%"


def to_spoken(s):
    for disp, spk in HOMO.items():
        s = s.replace(disp, spk)
    return s


def to_display(s):
    for disp, spk in HOMO.items():
        s = s.replace(spk, disp)
    return s


def dur(p):
    return float(
        subprocess.check_output([
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            p,
        ]).decode().strip()
    )


def parse_srt(p):
    cues = []
    for b in re.split(r"\n\s*\n", open(p, encoding="utf-8").read().strip()):
        ls = [l for l in b.splitlines() if l.strip()]
        if len(ls) < 2:
            continue
        m = re.search(
            r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)",
            b,
        )
        if not m:
            continue
        g = list(map(int, m.groups()))
        cues.append([
            g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0,
            g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0,
            ls[-1],
        ])
    return cues


def _ascii_safe_cut(c, maxlen):
    k = maxlen
    while 0 < k < len(c) and c[k - 1].isascii() and c[k - 1].isalnum() and c[k].isascii() and c[k].isalnum():
        k -= 1
    return max(1, k)


def _clauses(text):
    out = []
    cur = ""
    for ch in text:
        cur += ch
        if ch in PUNC:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def _visible_len(text):
    return len(text.strip())


def _merge_lines(clauses, maxlen):
    lines = []
    for p in clauses:
        if not lines:
            lines.append(p)
            continue
        prev = lines[-1]
        cl = _visible_len(prev)
        al = _visible_len(p)
        tiny = cl < 4 or al < 4
        prev_strong = prev.rstrip()[-1:] in STRONG
        if prev_strong and not tiny:
            lines.append(p)
        elif _visible_len(prev + p) <= maxlen or (tiny and _visible_len(prev + p) <= maxlen + 4):
            lines[-1] += p
        else:
            lines.append(p)
    return lines


def _protect_cut(c, k, names):
    for nm in names:
        i = 0
        while True:
            j = c.find(nm, i)
            if j < 0:
                break
            if j < k < j + len(nm):
                k = j
            i = j + 1
    while 1 < k < len(c) and c[k] in GLUE_HEAD:
        k -= 1
    return max(1, k)


def _hardwrap(line, maxlen, names):
    out = []
    c = line.strip()
    while _visible_len(c) > maxlen:
        k = _protect_cut(c, _ascii_safe_cut(c, maxlen), names)
        if k < 2:
            k = _ascii_safe_cut(c, maxlen)
        part = c[:k].strip()
        if not part:
            k = min(len(c), maxlen)
            part = c[:k].strip()
        out.append(part)
        c = c[k:].lstrip()
    if c:
        out.append(c)
    return out


def fine_cues(cues, maxlen=CAP_MAXLEN, names=NO_SPLIT):
    full = "".join(t for _, _, t in cues)
    char_t = []
    for st, en, t in cues:
        n = max(1, len(t))
        for i in range(len(t)):
            char_t.append((st + (en - st) * i / n, st + (en - st) * (i + 1) / n))
    if not char_t:
        return []
    N = len(char_t)
    lines = []
    for ln in _merge_lines(_clauses(full), maxlen):
        lines.extend(_hardwrap(ln, maxlen, names))
    out = []
    idx = 0
    for ln in lines:
        L = len(ln)
        disp = ln.strip().rstrip(SOFT + " ")
        if disp:
            a = char_t[min(idx, N - 1)][0]
            b = char_t[min(idx + L - 1, N - 1)][1]
            out.append((a, b, disp))
        idx += L
    return out


def fmt(t):
    h = int(t // 3600)
    t -= h * 3600
    m = int(t // 60)
    t -= m * 60
    s = int(t)
    ms = int(round((t - s) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(p, cues):
    with open(p, "w", encoding="utf-8") as f:
        for n, (st, en, t) in enumerate(cues, 1):
            f.write(f"{n}\n{fmt(st)} --> {fmt(en)}\n{t}\n\n")


timeline = []
gcues = []
cum = 0.0
segments = cfg.get("segments", cfg.get("shots", []))
for i, seg in enumerate(segments, 1):
    text = seg.get("text") or seg["narration"]
    spoken = to_spoken(text)
    mp3 = os.path.join(AUD, f"seg{i}.mp3")
    raw = os.path.join(SUB, f"seg{i}_raw.srt")
    vtt = os.path.join(SUB, f"seg{i}.srt")
    import time as _time

    clip = float(seg["duration"]) if "duration" in seg else None
    base_rate = _parse_rate_percent(RATE)
    rate = base_rate
    d = None
    for _try in range(6):
        if clip is not None and d is not None and d > clip and rate is not None:
            bump = max(10.0, ((d / clip) - 1.0) * 100.0 + 8.0)
            rate = base_rate + bump
        rate_arg = _format_rate_percent(rate) if rate is not None else RATE
        r = subprocess.run([
            "python3",
            "-m",
            "edge_tts",
            f"--voice={VOICE}",
            f"--rate={rate_arg}",
            f"--pitch={PITCH}",
            f"--volume={VOLUME}",
            f"--text={spoken}",
            f"--write-media={mp3}",
            f"--write-subtitles={raw}",
        ], stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(mp3) and os.path.getsize(mp3) > 1200:
            d = dur(mp3)
            if clip is None or d <= clip:
                break
        print(f"  seg{i} edge-tts 第{_try + 1}次失败,重试…")
        _time.sleep(2.0)
    else:
        sys.exit(f"seg{i} edge-tts 多次失败")
    clip = d + PAD if clip is None else clip
    fine = fine_cues(parse_srt(raw))
    fine = [(st, min(en, d), to_display(t)) for st, en, t in fine]
    write_srt(vtt, fine)
    for st, en, t in fine:
        gcues.append((cum + st, min(cum + en, cum + d), t))
    timeline.append({
        "seg": i,
        "id": seg.get("id", str(i)),
        "audio": round(d, 3),
        "clip": round(clip, 3),
        "start": round(cum, 3),
        "end": round(cum + clip, 3),
    })
    cum += clip
    print(f"seg{i}({seg.get('id', '')}): audio={d:.2f}s clip={clip:.2f}s 字幕{len(fine)}条")

write_srt(os.path.join(SUB, "global.srt"), gcues)
json.dump(
    {"total": round(cum, 3), "pad": PAD, "segs": timeline},
    open(os.path.join(BUILD, "timeline.json"), "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=2,
)
print(f"\n总时长(含pad): {cum:.2f}s | 字幕 {len(gcues)} 条")
