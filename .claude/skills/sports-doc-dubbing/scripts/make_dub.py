# -*- coding: utf-8 -*-
"""
读 build/segments_spk.json([{start,end,turns:[{spk,text}]}],时间为原片时间轴) →
  1) 用 edge-tts 逐"轮次"生成中文配音:主持H=云希、卡拉格C=云健(双音色对话)
  2) 段仍是对齐单位:把每段"锚定"到原片对应时刻(能放下就放原 start,放不下限幅 atempo 压缩),
     段内多个轮次依次拼接(同段统一 tempo)
  3) 拼出与原片等长的整轨 build/dub.wav
  4) 生成实际显示用的中文字幕 build/cues.json(逐轮次按配音时长分配子窗,再按字数细分换行)
用法: python3 make_dub.py   (换音色后请先清空 build/tts/)
"""
import json, os, subprocess, math, re, time

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
TTS = os.path.join(BUILD, "tts"); os.makedirs(TTS, exist_ok=True)

# 双音色:H=主持(詹俊位,年轻有活力) C=卡拉格(张璐指导位,成熟沉稳)
VOICE = {"H": "zh-CN-YunxiNeural", "C": "zh-CN-YunjianNeural"}
RATE  = os.environ.get("DUB_RATE", "+12%")  # 成熟但利落:匹配原片偏快的节奏,信息量大
PITCH = "+0Hz"
VOLUME= "+0%"
MAX_TEMPO = 1.5         # 落后时最大压缩倍率(降到1.5更丝滑,不发"赶")
MIN_GAP   = 0.0         # 不加人工间隔(会随段累积漂移);停顿来自TTS尾静音+锚点空档
LOOKBACK  = 3.0         # 密集句可提前开口、借用前面静音的最大秒数(配音略超前听感自然)
SR = 48000
CAP_MAXLEN = 17         # 单行字幕最大字数
PUNC = "，,。！!？?、；;：:…—"   # 含破折号:字幕在此断开,显示时再剥掉首尾破折号

def dur(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","default=nk=1:nw=1",p]).decode().strip())

def valid_mp3(p):
    # 文件存在且能被 ffprobe 解析出正时长才算有效(edge-tts 偶尔写坏文件)
    if not os.path.exists(p) or os.path.getsize(p)==0:
        return False
    try:
        return dur(p) > 0.05
    except Exception:
        return False

def tts(text, mp3, voice, tries=5):
    # edge-tts 偶发 403/空音频:重试+退避;清掉 0 字节残file 以免被当缓存跳过
    last=None
    for k in range(tries):
        if os.path.exists(mp3):
            os.remove(mp3)   # 清掉上次的残/坏文件再重生成
        try:
            subprocess.run(["python3","-m","edge_tts","--voice",voice,"--rate",RATE,
                "--pitch",PITCH,"--volume",VOLUME,"--text",text,"--write-media",mp3],
                check=True, stderr=subprocess.PIPE, timeout=90)
            if valid_mp3(mp3):
                time.sleep(0.1)   # 轻微限速,降低 edge-tts 触发 403 的概率
                return
            last="invalid/empty mp3"
        except Exception as e:
            last=getattr(e,"stderr",b"") or e
        time.sleep(1.5*(k+1))
    raise RuntimeError(f"edge-tts 连续{tries}次失败: {text[:24]!r} | {last}")

def to_wav(src, dst, tempo=1.0):
    af = "aresample=%d" % SR
    if tempo > 1.001:
        # atempo 单次范围 0.5~2.0;>2 需串联,这里 MAX_TEMPO<2 故单次即可
        af = "atempo=%.4f,%s" % (tempo, af)
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",src,
        "-af",af,"-ac","2","-ar",str(SR),dst], check=True)

def silence(d, dst):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","lavfi",
        "-t","%.3f"%max(d,0.001),"-i","anullsrc=r=%d:cl=stereo"%SR,dst], check=True)

# ---- 子句内:按标点+字数细分成不超长的字幕条 ----
def _fine_clause(clause, maxlen):
    pieces=[]; cur=""
    for ch in clause:
        cur+=ch
        if ch in PUNC: pieces.append(cur); cur=""
    if cur.strip(): pieces.append(cur)
    merged=[]
    for p in pieces:
        if merged and len(merged[-1].strip(PUNC))+len(p.strip(PUNC))<=maxlen: merged[-1]+=p
        else: merged.append(p)
    final=[]
    for m in merged:
        c=m
        while len(c.strip(PUNC+" "))>maxlen+3:   # 按"可见字数"硬切,破折号已不在此处
            final.append(c[:maxlen]); c=c[maxlen:]
        final.append(c)
    return [x for x in final if x.strip().strip(PUNC+" ")]

# ---- 字幕细分:先按破折号(同一人停顿)切成子句,再子句内细分 ----
def split_fine(st, en, text, maxlen=CAP_MAXLEN):
    clauses=[c for c in re.split(r'—+', text) if c.strip().strip(PUNC+" ")]
    if not clauses: return []
    cw=[max(1,len(c.strip(PUNC+" "))) for c in clauses]; ctot=sum(cw)
    out=[]; t=st
    for clause,w in zip(clauses,cw):
        c_st=t; c_en=t+(en-st)*w/ctot; t=c_en
        finals=_fine_clause(clause,maxlen)
        ww=[max(1,len(x.strip(PUNC+" "))) for x in finals]; wt=sum(ww) or 1
        tt=c_st
        for x,k in zip(finals,ww):
            dd=(c_en-c_st)*k/wt; disp=x.strip().strip(PUNC+" ")
            if disp: out.append([round(tt,3),round(tt+dd,3),disp])
            tt+=dd
    return out

def main():
    segs = json.load(open(os.path.join(BUILD,"segments_spk.json"),encoding="utf-8"))
    vdur = dur(os.path.join(ROOT,"source","original.mp4"))

    # 1) 逐轮次生成配音,测原始时长(已存在则跳过);raw[i]=该段各轮次时长之和
    raw=[]; turninfo=[]
    for i,s in enumerate(segs):
        tr=[]
        for j,t in enumerate(s["turns"]):
            mp3=os.path.join(TTS,f"s{i:03d}_{j}.mp3")
            if not valid_mp3(mp3):   # 缺失或损坏都重生成(坏缓存不会再卡死)
                tts(t["text"], mp3, VOICE[t["spk"]])
                print(f"tts {i:03d}.{j} [{t['spk']}] {dur(mp3):5.2f}s  {t['text'][:22]}", flush=True)
            tr.append({"spk":t["spk"],"text":t["text"],"mp3":mp3,"raw":dur(mp3)})
        turninfo.append(tr)
        raw.append(sum(x["raw"] for x in tr))

    # 2) 锚定对齐:把"下一句锚点"当作绝对截止时间;落后就压缩追赶(可达 MAX_TEMPO)
    cursor=0.0; place=[]
    for i,s in enumerate(segs):
        start=s["start"]
        nxt = segs[i+1]["start"] if i+1<len(segs) else min(vdur, s["end"]+2.0)
        a_start=max(cursor, start)
        avail=nxt - a_start          # 到下一锚点的可用时间(落后时可能<=0)
        r=raw[i]; tempo=1.0
        if r>avail:                  # 放不下:先借用前面的静音提前开口,仍不够再压缩
            a_start=max(cursor, start-LOOKBACK)
            avail=nxt - a_start
            if r>avail:
                tempo=min(r/max(avail,0.05), MAX_TEMPO)
        ndur=r/tempo
        place.append({"i":i,"start":round(a_start,3),"dur":round(ndur,3),
                      "tempo":round(tempo,3),"raw":round(r,3),"drift":round(a_start-start,2)})
        cursor=a_start+ndur+MIN_GAP

    # 3) 拼整轨:静音 + 段(段内各轮次依次) + 静音 ...
    parts=[]; prev_end=0.0
    for p in place:
        i=p["i"]; gap=p["start"]-prev_end
        if gap>0.005:
            sp=os.path.join(TTS,f"gap{i:03d}.wav"); silence(gap,sp); parts.append(sp)
        for j,x in enumerate(turninfo[i]):
            wv=os.path.join(TTS,f"s{i:03d}_{j}.wav"); to_wav(x["mp3"],wv,p["tempo"])
            parts.append(wv)
        prev_end=p["start"]+p["dur"]
    if vdur-prev_end>0.01:
        sp=os.path.join(TTS,"gap_tail.wav"); silence(vdur-prev_end,sp); parts.append(sp)

    listf=os.path.join(TTS,"concat.txt")
    with open(listf,"w") as f:
        for p in parts: f.write("file '%s'\n"%p)
    dubwav=os.path.join(BUILD,"dub.wav")
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0",
        "-i",listf,"-ac","2","-ar",str(SR),dubwav],check=True)

    # 4) 字幕 cues:逐轮次按配音时长分配子窗(真实显示时段)
    cues=[]
    for p,tr in zip(place,turninfo):
        tcur=p["start"]
        for x in tr:
            vd=x["raw"]/p["tempo"]
            cues.extend(split_fine(tcur, tcur+vd, x["text"]))
            tcur+=vd
    json.dump(cues, open(os.path.join(BUILD,"cues.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(place, open(os.path.join(BUILD,"placements.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=1)

    od=dur(dubwav); maxdrift=max(p["drift"] for p in place)
    comp=[p for p in place if p["tempo"]>1.01]
    nturn=sum(len(t) for t in turninfo)
    print(f"\n配音轨 {od:.2f}s (原片 {vdur:.2f}s) | {len(place)}段/{nturn}轮次 | 字幕 {len(cues)} 条 | "
          f"压缩段 {len(comp)}/{len(place)} | 最大漂移 {maxdrift:.2f}s")

if __name__=="__main__":
    main()
