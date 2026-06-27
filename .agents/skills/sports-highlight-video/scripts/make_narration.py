# -*- coding: utf-8 -*-
"""
读 project.json → 用 edge-tts 生成每段激情解说 + 逐句细分字幕 + 时间轴。
用法: python3 make_narration.py [project.json]
产出: <build>/audio/seg{i}.mp3, <build>/subs/seg{i}.srt, <build>/subs/global.srt, <build>/timeline.json
依赖: pip3 install edge-tts ; ffmpeg/ffprobe
体育解说音色推荐 zh-CN-YunjianNeural(Male/Sports/Passion);rate/pitch/volume 上调=更燃。
"""
import subprocess, os, json, re, sys

PROJ = sys.argv[1] if len(sys.argv)>1 else "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir","build"))
AUD, SUB = os.path.join(BUILD,"audio"), os.path.join(BUILD,"subs")
os.makedirs(AUD,exist_ok=True); os.makedirs(SUB,exist_ok=True)

V = cfg.get("voice",{})
VOICE=V.get("name","zh-CN-YunjianNeural"); RATE=V.get("rate","+20%")
PITCH=V.get("pitch","+16Hz"); VOLUME=V.get("volume","+15%")
PAD=cfg.get("pad",0.35); CAP_MAXLEN=cfg.get("caption_maxlen",12)
PUNC="，,。！!？?、；;：:"

def dur(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","default=nk=1:nw=1",p]).decode().strip())
def parse_srt(p):
    cues=[]
    for b in re.split(r"\n\s*\n",open(p,encoding="utf-8").read().strip()):
        ls=[l for l in b.splitlines() if l.strip()]
        if len(ls)<2: continue
        m=re.search(r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)",b)
        if not m: continue
        g=list(map(int,m.groups()))
        cues.append([g[0]*3600+g[1]*60+g[2]+g[3]/1000., g[4]*3600+g[5]*60+g[6]+g[7]/1000., ls[-1]])
    return cues
def _ascii_safe_cut(c,maxlen):
    """硬切字幕时,切点不要落在连续 ASCII 词中间(如 DeepSeek/FIFA/PSG 被切成 'DeepSe'+'ek')。
    落在 ASCII 词内就回退到词首。纯中文不受影响(切点两侧不是 ASCII 字母数字)。"""
    k=maxlen
    while 0<k<len(c) and c[k-1].isascii() and c[k-1].isalnum() and c[k].isascii() and c[k].isalnum():
        k-=1
    return max(1,k)

def split_fine(st,en,text,maxlen=CAP_MAXLEN):
    pieces=[]; cur=""
    for ch in text:
        cur+=ch
        if ch in PUNC: pieces.append(cur); cur=""
    if cur.strip(): pieces.append(cur)
    merged=[]
    for p in pieces:
        if merged and len(merged[-1].rstrip(PUNC))+len(p.rstrip(PUNC))<=maxlen: merged[-1]+=p
        else: merged.append(p)
    final=[]
    for m in merged:
        c=m
        while len(c)>maxlen+3:
            k=_ascii_safe_cut(c,maxlen); final.append(c[:k]); c=c[k:]
        final.append(c)
    weights=[max(1,len(x.strip(PUNC+" "))) for x in final]; tot=sum(weights)
    out=[]; t=st
    for x,w in zip(final,weights):
        dd=(en-st)*w/tot; disp=x.strip().rstrip("，,、；;：: ")
        if disp: out.append((t,t+dd,disp))
        t+=dd
    return out
def fmt(t):
    h=int(t//3600); t-=h*3600; m=int(t//60); t-=m*60; s=int(t); ms=int(round((t-s)*1000))
    if ms==1000: s+=1; ms=0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
def write_srt(p,cues):
    with open(p,"w",encoding="utf-8") as f:
        for n,(st,en,t) in enumerate(cues,1): f.write(f"{n}\n{fmt(st)} --> {fmt(en)}\n{t}\n\n")

timeline=[]; gcues=[]; cum=0.
for i,seg in enumerate(cfg["segments"],1):
    text=seg["text"]; mp3=os.path.join(AUD,f"seg{i}.mp3")
    raw=os.path.join(SUB,f"seg{i}_raw.srt"); vtt=os.path.join(SUB,f"seg{i}.srt")
    subprocess.run(["python3","-m","edge_tts","--voice",VOICE,"--rate",RATE,"--pitch",PITCH,
        "--volume",VOLUME,"--text",text,"--write-media",mp3,"--write-subtitles",raw],
        check=True,stderr=subprocess.DEVNULL)
    d=dur(mp3); clip=d+PAD
    fine=[]
    for st,en,t in parse_srt(raw): fine.extend(split_fine(st,en,t))
    fine=[(st,min(en,d),t) for st,en,t in fine]
    write_srt(vtt,fine)
    for st,en,t in fine: gcues.append((cum+st,min(cum+en,cum+d),t))
    timeline.append({"seg":i,"id":seg.get("id",str(i)),"audio":round(d,3),"clip":round(clip,3),
                     "start":round(cum,3),"end":round(cum+clip,3)})
    cum+=clip
    print(f"seg{i}({seg.get('id','')}): audio={d:.2f}s clip={clip:.2f}s 字幕{len(fine)}条")

write_srt(os.path.join(SUB,"global.srt"),gcues)
json.dump({"total":round(cum,3),"pad":PAD,"segs":timeline},
          open(os.path.join(BUILD,"timeline.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(f"\n总时长(含pad): {cum:.2f}s | 字幕 {len(gcues)} 条")
