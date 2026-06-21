# -*- coding: utf-8 -*-
"""
交叉校正:英文原文(逐 chunk 人工标的说话人)为准、声纹(diar_windows.json)兜底。
复用 diarize_spk.py 已存的 build/diar_windows.json,不重算嵌入。
为每段中文每个 '——' 切片定 H(主持)/C(卡拉格):
  - 切片按可见字数比例落到该段 [start,end] 时间窗
  - 英文 chunk 在该窗有覆盖 → 用英文(按重叠时长加权多数票)
  - 英文无覆盖(静音/空档) → 用声纹
  - 英文与声纹冲突处:取英文,复核稿标 ✎
输出 build/segments_spk.json + build/speaker_review.txt
用法: python3 relabel_spk.py
"""
import json, os, re
ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
PUNC = "，,。！!？?、；;：:…—"

# ★★ 每个英文 chunk 的说话人,对照 build/chunks_en.json 逐句人工标注。★★
# 这是本脚本唯一需要按视频改的地方:拼一个长度 == chunk 数的 H/C 串
# (H=开场那位/主持,C=另一位/嘉宾)。混说 chunk 取主导方,过渡靠相邻 chunk 时间自动切。
#
# 别从零标!先跑 diarize_spk.py,它已把声纹对每个 chunk 的判定写进 build/chunks_spk.json。
# 用它当草稿、只改错的:
#   python3 -c "import json;print(''.join(c['spk'] for c in json.load(open('build/chunks_spk.json'))))"
# 把打印的串贴到下面,再对着 chunks_en.json 修快问答区/低置信处即可。
# 下面是示例格式(请整体替换成你自己的标注):
CHUNK_SEM = list(
 "HHCHHHCCCC"  # 0-9   (示例:开场 H 介绍→C 应话→H 报内容…)
 "CHCHHHHHCH"  # 10-19
 # … 继续到覆盖全部 chunk …
)
# 校验:len(CHUNK_SEM) 必须等于 chunks_en.json 的条数(下方 assert 会拦)。
# 嫌人工标注重,可跳过本脚本,只用 diarize_spk.py 的结果 + 复核稿人工修少量 ⚠。

diar = json.load(open(os.path.join(BUILD, "diar_windows.json"), encoding="utf-8"))
chunks = json.load(open(os.path.join(BUILD, "chunks_en.json"), encoding="utf-8"))
segs = json.load(open(os.path.join(BUILD, "segments_cn.json"), encoding="utf-8"))
assert len(CHUNK_SEM) == len(chunks), f"chunk标注数 {len(CHUNK_SEM)} != chunk数 {len(chunks)}"

import numpy as np
dt0 = np.array([d["t0"] for d in diar]); dt1 = np.array([d["t1"] for d in diar])
dsp = np.array([1 if d["spk"] == "H" else 0 for d in diar])  # 1=H
dtc = (dt0 + dt1) / 2

def diar_vote(a, b):
    sel = (dt1 > a) & (dt0 < b)
    s = dsp[sel]
    if len(s) == 0:
        j = int(np.argmin(np.abs(dtc - (a + b) / 2)))
        return "H" if dsp[j] else "C", 0.5
    nH = int(s.sum()); nC = len(s) - nH
    return ("H" if nH >= nC else "C"), round(max(nH, nC) / len(s), 2)

def sem_vote(a, b):
    # 英文 chunk 按重叠时长加权
    wH = wC = 0.0
    for c in chunks:
        ov = min(b, c["end"]) - max(a, c["start"])
        if ov > 0:
            if CHUNK_SEM[c["id"]] == "H": wH += ov
            else: wC += ov
    if wH == 0 and wC == 0:
        return None, 0.0
    return ("H" if wH >= wC else "C"), round(max(wH, wC) / (wH + wC), 2)

def vis_len(s):
    return max(1, len(s.strip(PUNC + " ")))

out, review = [], []
n_override = n_turn = 0
for i, s in enumerate(segs):
    st, en = s["start"], s["end"]
    pieces = [p for p in re.split(r"—+", s["cn"]) if p.strip()]
    if not pieces:
        continue
    ws = [vis_len(p) for p in pieces]; wt = sum(ws); t = st
    tagged = []
    for p, w in zip(pieces, ws):
        a = t; b = t + (en - st) * w / wt; t = b
        sv, sc = sem_vote(a, b)
        dv, dc = diar_vote(a, b)
        if sv is None:                       # 英文无覆盖 → 声纹
            spk, conf, src = dv, dc, "声"
        elif sv == dv:                        # 一致
            spk, conf, src = sv, max(sc, dc), "✓"
        else:                                 # 冲突 → 英文为准
            spk, conf, src = sv, sc, "✎"
            n_override += 1
        tagged.append({"spk": spk, "text": p.strip(), "src": src, "sv": sv, "dv": dv})
    # 合并相邻同说话人
    turns = []
    for tg in tagged:
        if turns and turns[-1]["spk"] == tg["spk"]:
            turns[-1]["text"] += "——" + tg["text"]
            turns[-1]["_srcs"].append(tg["src"])
        else:
            turns.append({"spk": tg["spk"], "text": tg["text"], "_srcs": [tg["src"]]})
    n_turn += len(turns)
    review.append(f"#{i:03d} [{st:.1f}-{en:.1f}]")
    for tr in turns:
        name = "主持" if tr["spk"] == "H" else "卡拉"
        flag = " ✎英文校正" if "✎" in tr["_srcs"] else (" (声纹)" if "声" in tr["_srcs"] else "")
        review.append(f"   {name}{flag}  {tr['text']}")
    for tr in turns:
        del tr["_srcs"]
    out.append({"start": st, "end": en, "turns": turns})

json.dump(out, open(os.path.join(BUILD, "segments_spk.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
open(os.path.join(BUILD, "speaker_review.txt"), "w", encoding="utf-8").write("\n".join(review))
print(f"segments_spk.json: {len(out)} 段 / {n_turn} 轮次 | 英文校正声纹 {n_override} 处(复核稿标 ✎)")
print("复核稿: build/speaker_review.txt")
