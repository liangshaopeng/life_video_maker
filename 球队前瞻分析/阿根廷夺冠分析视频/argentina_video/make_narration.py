# -*- coding: utf-8 -*-
"""生成7段云健·詹俊范儿激情配音 + 细分短句字幕,合成全局SRT,导出时间轴JSON。"""
import subprocess, os, json, re

ROOT = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(ROOT, "build", "audio_v2")
SUB = os.path.join(ROOT, "build", "subs")
os.makedirs(AUD, exist_ok=True); os.makedirs(SUB, exist_ok=True)

VOICE  = "zh-CN-YunjianNeural"
RATE   = "+20%"
PITCH  = "+16Hz"
VOLUME = "+15%"
PAD = 0.35
CAP_MAXLEN = 12   # 单条字幕最大字数

# 7段:开场/实力/新生代/梅西39/迪马利亚(决赛先生)/概率/收尾
SEGS = [
 "二零二二,卢塞尔的夜晚!梅西,高高举起大力神杯,阿根廷,封王啦!可是朋友们,四年之后,卫冕冠军卷土重来,这一次,他们还能不能,笑到最后?",
 "先看底气!国际足联排名,世界第一!美洲杯,成功卫冕!斯卡洛尼的体系,攻守平衡,几乎挑不出毛病。这,就是冠军的成色!",
 "更重要的是,这支阿根廷,早就不止一个梅西!劳塔罗、阿尔瓦雷斯、恩佐、麦卡利斯特,新一代,已经扛起了大旗!",
 "但是朋友们,隐忧,同样真实!二零二六,梅西就要满三十九岁,这,几乎是他最后一届世界杯!核心一旦老去,谁来接棒?",
 "还有一个更大的隐患,在锋线!常务副球王,天使迪马利亚,退出了国家队!你看决赛这一球,大心脏!假意一推,骗得洛里提前倒地,实则一记刁钻的弹地脚法,高级!从美洲杯到世界杯,大赛决赛,他总能一锤定音!天使一走,阿根廷前场,就少了那个,脚头最硬的大赛爆破手!",
 "再加上四十八队的全新赛制,北美的酷暑,还有西班牙、法国虎视眈眈!根据DeepSeek的谨慎推算,阿根廷的夺冠概率,大约百分之十二到十六,第一集团,稳稳的!但绝不是唯一的热门!",
 "所以,如果这真的是,梅西的最后一舞,朋友们,你,敢不敢赌他,笑到最后?",
]

PUNC = "，,。！!？?、；;：:"

def dur(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","default=nk=1:nw=1", path]).decode().strip())

def parse_srt(path):
    txt=open(path,encoding="utf-8").read(); cues=[]
    for block in re.split(r"\n\s*\n", txt.strip()):
        lines=[l for l in block.splitlines() if l.strip()]
        if len(lines)<2: continue
        m=re.search(r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)",block)
        if not m: continue
        h1,m1,s1,ms1,h2,m2,s2,ms2=map(int,m.groups())
        st=h1*3600+m1*60+s1+ms1/1000.0; en=h2*3600+m2*60+s2+ms2/1000.0
        cues.append([st,en,lines[-1]])
    return cues

def split_fine(st,en,text,maxlen=CAP_MAXLEN):
    """把整句拆成≤maxlen字的短句,按字数比例分配时间窗"""
    pieces=[]; cur=""
    for ch in text:
        cur+=ch
        if ch in PUNC:
            pieces.append(cur); cur=""
    if cur.strip(): pieces.append(cur)
    # 合并过短的相邻片段;过长的硬拆
    merged=[]
    for p in pieces:
        if merged and len(merged[-1].rstrip(PUNC))+len(p.rstrip(PUNC))<=maxlen:
            merged[-1]+=p
        else:
            merged.append(p)
    final=[]
    for m in merged:
        c=m
        while len(c)>maxlen+3:
            final.append(c[:maxlen]); c=c[maxlen:]
        final.append(c)
    weights=[max(1,len(x.strip(PUNC+" "))) for x in final]; tot=sum(weights)
    out=[]; t=st
    for x,w in zip(final,weights):
        d=(en-st)*w/tot
        disp=x.strip().rstrip("，,、；;：: ")
        if disp: out.append((t,t+d,disp))
        t+=d
    return out

def fmt(t):
    h=int(t//3600); t-=h*3600; m=int(t//60); t-=m*60; s=int(t); ms=int(round((t-s)*1000))
    if ms==1000: s+=1; ms=0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def write_srt(path,cues):
    with open(path,"w",encoding="utf-8") as f:
        for n,(st,en,t) in enumerate(cues,start=1):
            f.write(f"{n}\n{fmt(st)} --> {fmt(en)}\n{t}\n\n")

timeline=[]; global_cues=[]; cum=0.0
for i,text in enumerate(SEGS,start=1):
    mp3=os.path.join(AUD,f"seg{i}.mp3"); raw=os.path.join(SUB,f"seg{i}_raw.srt")
    seg_vtt=os.path.join(SUB,f"seg{i}.vtt")
    subprocess.run(["python3","-m","edge_tts","--voice",VOICE,"--rate",RATE,
        "--pitch",PITCH,"--volume",VOLUME,"--text",text,
        "--write-media",mp3,"--write-subtitles",raw],check=True,stderr=subprocess.DEVNULL)
    d=dur(mp3); clip=d+PAD
    # 句级cue -> 细分短句cue(段内相对时间)
    fine=[]
    for st,en,t in parse_srt(raw):
        fine.extend(split_fine(st,en,t))
    fine=[(st,min(en,d),t) for st,en,t in fine]
    write_srt(seg_vtt, fine)             # 供 render_overlays 烧字幕
    for st,en,t in fine:
        global_cues.append((cum+st, min(cum+en,cum+d), t))
    timeline.append({"seg":i,"audio":round(d,3),"clip":round(clip,3),
                     "start":round(cum,3),"end":round(cum+clip,3),"text":text})
    cum+=clip
    print(f"seg{i}: audio={d:.2f}s clip={clip:.2f}s start={timeline[-1]['start']:.2f}s 细分字幕={len(fine)}条")

write_srt(os.path.join(SUB,"global.srt"), global_cues)
json.dump({"total":round(cum,3),"pad":PAD,"segs":timeline},
          open(os.path.join(ROOT,"build","timeline.json"),"w",encoding="utf-8"),
          ensure_ascii=False,indent=2)
print(f"\n总时长(含pad): {cum:.2f}s | 全局字幕 {len(global_cues)} 条")
