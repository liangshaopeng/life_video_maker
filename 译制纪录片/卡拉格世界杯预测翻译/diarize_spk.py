# -*- coding: utf-8 -*-
"""
声纹分段(diarization)→ 给每段中文每个 '——' 切片定说话人(主持 H / 卡拉格 C)。
不裁静音,保持原片时间轴。输出:
  build/diar_windows.json   每个声纹窗 {t0,t1,spk}（调试用）
  build/chunks_spk.json     每个英文 chunk 的说话人（自检/调试）
  build/segments_spk.json   [{start,end,turns:[{spk,text,conf}]}]  ← 配音真源
  build/speaker_review.txt  人读复核稿，低置信度标 ⚠
用法: python3 diarize_spk.py
"""
import json, os, re
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
WAV = os.path.join(ROOT, "source", "audio16k.wav")
SR = 16000
PUNC = "，,。！!？?、；;：:…—"

# ---------- 1) 读音频 + 连续声纹嵌入 ----------
import librosa
from resemblyzer import VoiceEncoder

print("加载音频…", flush=True)
wav, _ = librosa.load(WAV, sr=SR, mono=True)
# 振幅归一(不裁静音,保持时间轴)
m = np.max(np.abs(wav))
if m > 0:
    wav = wav * (0.95 / m)

print(f"音频 {len(wav)/SR:.1f}s,计算声纹嵌入(rate=4,可能要1~2分钟)…", flush=True)
encoder = VoiceEncoder()  # CPU
_, cont_embeds, wav_splits = encoder.embed_utterance(
    wav, return_partials=True, rate=4)
# 每个窗的时间中心 / 区间
win_t0 = np.array([s.start / SR for s in wav_splits])
win_t1 = np.array([s.stop / SR for s in wav_splits])
win_tc = (win_t0 + win_t1) / 2.0
print(f"声纹窗 {len(cont_embeds)} 个", flush=True)

# ---------- 2) KMeans(2) 聚类 ----------
from scipy.cluster.vq import kmeans2
X = cont_embeds.astype(np.float64)
X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
# 多次初始化取簇内距离最小的,稳一点
best = None
for seed in range(8):
    cen, lab = kmeans2(X, 2, minit="++", seed=seed)
    if len(set(lab)) < 2:
        continue
    inertia = sum(np.sum((X[lab == k] - cen[k]) ** 2) for k in range(2))
    if best is None or inertia < best[0]:
        best = (inertia, cen, lab)
labels = best[2].copy()

# ---------- 3) 中值滤波去抖 ----------
def medfilt(a, k=5):
    k = k | 1
    pad = k // 2
    ap = np.pad(a, pad, mode="edge")
    return np.array([np.median(ap[i:i + k]) for i in range(len(a))]).astype(int)

labels = medfilt(labels, 5)

# ---------- 4) 哪个簇是主持 H:用开场 [0,8s] 判定 ----------
intro = labels[(win_tc >= 0.5) & (win_tc <= 8.0)]
host_cluster = int(np.round(np.mean(intro))) if len(intro) else 0
def spk_of_cluster(c):  # H=主持, C=卡拉格
    return "H" if c == host_cluster else "C"

# 落到时间轴:给定 [a,b] 返回各窗投票
def vote(a, b):
    sel = (win_t1 > a) & (win_t0 < b)
    labs = labels[sel]
    if len(labs) == 0:  # 落在静音/无窗,取最近窗
        j = int(np.argmin(np.abs(win_tc - (a + b) / 2.0)))
        return spk_of_cluster(int(labels[j])), 0.5
    nH = int(np.sum(labs == host_cluster)); nC = len(labs) - nH
    spk = "H" if nH >= nC else "C"
    conf = max(nH, nC) / len(labs)
    return spk, round(conf, 2)

# ---------- 5) 英文 chunk 自检 ----------
chunks = json.load(open(os.path.join(BUILD, "chunks_en.json"), encoding="utf-8"))
chunk_spk = []
for c in chunks:
    spk, conf = vote(c["start"], c["end"])
    chunk_spk.append({"id": c["id"], "start": c["start"], "end": c["end"],
                      "spk": spk, "conf": conf, "en": c["en"][:60]})
json.dump(chunk_spk, open(os.path.join(BUILD, "chunks_spk.json"), "w",
          encoding="utf-8"), ensure_ascii=False, indent=1)

expect = {0: "H", 2: "C", 3: "H", 5: "H", 6: "C", 28: "H", 40: "H", 169: "C"}
print("\n=== 自检(英文 chunk:预期 vs 声纹)===")
ok = 0
for cid, exp in expect.items():
    got = next(x for x in chunk_spk if x["id"] == cid)
    mark = "✅" if got["spk"] == exp else "❌"
    if got["spk"] == exp:
        ok += 1
    print(f" chunk{cid:>3} 预期{exp} 声纹{got['spk']}(conf {got['conf']}) {mark}  {got['en']}")
print(f"自检 {ok}/{len(expect)} 一致" +
      ("" if ok >= len(expect) - 1 else "  ⚠ 可能聚类标反,检查!"))

win_t0c = [round(float(x), 2) for x in win_t0]
diar = [{"t0": round(float(win_t0[i]), 2), "t1": round(float(win_t1[i]), 2),
         "spk": spk_of_cluster(int(labels[i]))} for i in range(len(labels))]
json.dump(diar, open(os.path.join(BUILD, "diar_windows.json"), "w",
          encoding="utf-8"), ensure_ascii=False)

# ---------- 6) 映射到中文每段的 '——' 切片 ----------
segs = json.load(open(os.path.join(BUILD, "segments_cn.json"), encoding="utf-8"))

def vis_len(s):  # 可见字数(剥标点)
    return max(1, len(s.strip(PUNC + " ")))

out = []
review = []
low = 0
for i, s in enumerate(segs):
    st, en = s["start"], s["end"]
    pieces = [p for p in re.split(r"—+", s["cn"]) if p.strip()]
    if not pieces:
        continue
    ws = [vis_len(p) for p in pieces]; wt = sum(ws)
    # 每片按字数比例落到 [st,en] 的子区间 → 投票
    tagged = []
    t = st
    for p, w in zip(pieces, ws):
        a = t; b = t + (en - st) * w / wt; t = b
        spk, conf = vote(a, b)
        tagged.append({"spk": spk, "text": p.strip(), "conf": conf})
        if conf < 0.6:
            low += 1
    # 合并相邻同说话人片(用 —— 重接,保留同人停顿给字幕断行)
    turns = []
    for tg in tagged:
        if turns and turns[-1]["spk"] == tg["spk"]:
            turns[-1]["text"] += "——" + tg["text"]
            turns[-1]["conf"] = min(turns[-1]["conf"], tg["conf"])
        else:
            turns.append(dict(tg))
    out.append({"start": st, "end": en, "turns": turns})
    # 复核稿
    review.append(f"#{i:03d} [{st:.1f}-{en:.1f}]")
    for tr in turns:
        name = "主持" if tr["spk"] == "H" else "卡拉"
        warn = " ⚠" if tr["conf"] < 0.6 else ""
        review.append(f"   {name}({tr['conf']}){warn}  {tr['text']}")

json.dump(out, open(os.path.join(BUILD, "segments_spk.json"), "w",
          encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(BUILD, "speaker_review.txt"), "w", encoding="utf-8").write(
    "\n".join(review))

nturn = sum(len(s["turns"]) for s in out)
print(f"\nsegments_spk.json: {len(out)} 段 / {nturn} 轮次 | 低置信度切片 {low} 处(复核稿里标 ⚠)")
print("复核稿: build/speaker_review.txt")
