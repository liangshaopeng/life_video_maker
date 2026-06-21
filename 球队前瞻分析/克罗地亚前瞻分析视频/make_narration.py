# -*- coding: utf-8 -*-
"""
读 project.json → 用 edge-tts 生成每段激情解说 + 流畅细分字幕 + 时间轴。
用法: python3 make_narration.py [project.json]
产出: <build>/audio/seg{i}.mp3, <build>/subs/seg{i}.srt, <build>/subs/global.srt, <build>/timeline.json
依赖: pip3 install edge-tts ; ffmpeg/ffprobe
体育解说音色推荐 zh-CN-YunjianNeural(Male/Sports/Passion);rate/pitch/volume 上调=更燃。
字幕断句:fine_cues 整段重切(跨 edge-tts cue 合并、消碎片、人名保护),配 project.json 的
caption_maxlen(16)与 no_split(外国人名列表)。详见 memory: video-caption-fluency。
"""
import subprocess, os, json, re, sys, time as _time

PROJ = sys.argv[1] if len(sys.argv)>1 else "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir","build"))
AUD, SUB = os.path.join(BUILD,"audio"), os.path.join(BUILD,"subs")
os.makedirs(AUD,exist_ok=True); os.makedirs(SUB,exist_ok=True)

V = cfg.get("voice",{})
VOICE=V.get("name","zh-CN-YunjianNeural"); RATE=V.get("rate","+20%")
PITCH=V.get("pitch","+16Hz"); VOLUME=V.get("volume","+15%")
PAD=cfg.get("pad",0.35); CAP_MAXLEN=cfg.get("caption_maxlen",16)
NO_SPLIT=cfg.get("no_split",[])            # 外国人名等原子词:字幕绝不从中间切开
PUNC="，,。！!？?、；;：:"
STRONG="。！？!?"                            # 句末强停顿
SOFT="，,、；;：:"                            # 句中软停顿
GLUE_HEAD="就是的了吧呢吗啊呀和与跟也都还把被对向给"   # 这些承接字不宜作为一行开头

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
    """硬切字幕时,切点不要落在连续 ASCII 词中间(如 FIFA/PSG 被切成两半)。
    落在 ASCII 词内就回退到词首。纯中文不受影响。"""
    k=maxlen
    while 0<k<len(c) and c[k-1].isascii() and c[k-1].isalnum() and c[k].isascii() and c[k].isalnum():
        k-=1
    return max(1,k)

def _clauses(text):
    """按标点切成小句(保留标点),拼接后==原文。"""
    out=[]; cur=""
    for ch in text:
        cur+=ch
        if ch in PUNC: out.append(cur); cur=""
    if cur: out.append(cur)
    return out

def _merge_lines(clauses,maxlen):
    """贪心把小句并成更完整的字幕行:句末强停顿处尽量断,但把过短碎块(<4字)吸进相邻行,避免碎片。"""
    lines=[]
    for p in clauses:
        if not lines: lines.append(p); continue
        prev=lines[-1]; cl=len(prev.rstrip(PUNC)); al=len(p.rstrip(PUNC))
        tiny=cl<4 or al<4
        prev_strong=prev.rstrip()[-1:] in STRONG
        if prev_strong and not tiny:          # 句子边界:两边都够长就断开
            lines.append(p)
        elif cl+al<=maxlen or (tiny and cl+al<=maxlen+4):
            lines[-1]+=p                       # 合得下,或为了消碎片略微超长
        else:
            lines.append(p)
    return lines

def _protect_cut(c,k,names):
    """把硬切点 k 调离外国人名内部(回退到名字词首),且承接字不留行首。"""
    for nm in names:
        i=0
        while True:
            j=c.find(nm,i)
            if j<0: break
            if j<k<j+len(nm): k=j
            i=j+1
    while 1<k<len(c) and c[k] in GLUE_HEAD: k-=1
    return max(1,k)

def _hardwrap(line,maxlen,names):
    """单行仍超长(无标点可断)时,做人名感知 + 承接字感知的软换行。"""
    out=[]; c=line
    while len(c.rstrip(PUNC))>maxlen+4:
        k=_protect_cut(c,_ascii_safe_cut(c,maxlen),names)
        if k<2: k=_ascii_safe_cut(c,maxlen)   # 兜底,防死循环
        out.append(c[:k]); c=c[k:]
    out.append(c)
    return out

def fine_cues(cues,maxlen=CAP_MAXLEN,names=NO_SPLIT):
    """用整段文本重切字幕(跨 edge-tts 原始 cue 边界,消除孤字/碎片),按字符插值还原时间。"""
    full="".join(t for _,_,t in cues)
    char_t=[]                                  # 每个字符的 (起,止) 时间
    for st,en,t in cues:
        n=max(1,len(t))
        for i in range(len(t)):
            char_t.append((st+(en-st)*i/n, st+(en-st)*(i+1)/n))
    if not char_t: return []
    N=len(char_t)
    lines=[]
    for ln in _merge_lines(_clauses(full),maxlen):
        lines.extend(_hardwrap(ln,maxlen,names))
    out=[]; idx=0
    for ln in lines:
        L=len(ln); a=char_t[min(idx,N-1)][0]; b=char_t[min(idx+L-1,N-1)][1]
        disp=ln.strip().rstrip(SOFT+" ")
        if disp: out.append((a,b,disp))
        idx+=L
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
    for _try in range(6):                       # edge-tts 偶发网络失败 -> 重试
        r=subprocess.run(["python3","-m","edge_tts","--voice",VOICE,"--rate",RATE,"--pitch",PITCH,
            "--volume",VOLUME,"--text",text,"--write-media",mp3,"--write-subtitles",raw],
            stderr=subprocess.DEVNULL)
        if r.returncode==0 and os.path.exists(mp3) and os.path.getsize(mp3)>1200: break
        print(f"  seg{i} edge-tts 第{_try+1}次失败,重试…"); _time.sleep(2.0)
    else:
        sys.exit(f"seg{i} edge-tts 多次失败")
    d=dur(mp3); clip=d+PAD
    fine=fine_cues(parse_srt(raw))             # 整段重切:跨 cue 合并 + 人名保护 + 消碎片
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
