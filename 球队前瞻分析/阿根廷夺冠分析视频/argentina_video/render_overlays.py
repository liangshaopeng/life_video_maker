# -*- coding: utf-8 -*-
"""
渲染6段【透明叠加层】(RGBA, 1920x1080 @30fps),叠在实战画面之上。
含: 上下压暗渐变(scrim) + 标题/数据卡/球员名条/大数字39/概率12-16%条形图/收尾标题。
字幕由 ffmpeg 烧 global.srt,不在此处。帧 -> build/overlays/segN/####.png
"""
import os, math, json
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "build", "overlays")
TL = json.load(open(os.path.join(ROOT, "build", "timeline.json"), encoding="utf-8"))
DUR = [s["clip"] for s in TL["segs"]]   # 每段时长(含pad)

# 配色(阿根廷天蓝白 + 金 + 警示红)
SKY   = (117, 188, 240)
SKYd  = (40, 110, 180)
WHITE = (255, 255, 255)
NAVY  = (10, 22, 50)
GOLD  = (252, 209, 50)
REDW  = (240, 90, 84)
INK   = (12, 22, 46)

F_CN  = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F_NUM = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
_fc = {}
def font(kind, size):
    k=(kind,size)
    if k in _fc: return _fc[k]
    if kind=="b":  f=ImageFont.truetype(F_CN,size,index=2)
    elif kind=="r":f=ImageFont.truetype(F_CN,size,index=0)
    else:          f=ImageFont.truetype(F_NUM,size,index=0)
    _fc[k]=f; return f

def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def lerp(a,b,t): return a+(b-a)*t
def e_io(t): t=clamp(t); return .5-.5*math.cos(math.pi*t)
def e_out(t): t=clamp(t); return 1-(1-t)**3
def e_back(t):
    t=clamp(t); c1=1.70158; c3=c1+1
    return 1+c3*(t-1)**3+c1*(t-1)**2
def appear(tt,s,d):
    if tt<s: return 0.0,0.0
    p=clamp((tt-s)/d); return p,p
def seg_alpha(tt,dur,fin=0.3,fout=0.35):
    """段内整体淡入淡出(让叠加层柔和出现/消失)"""
    a=1.0
    if tt<fin: a=min(a,tt/fin)
    if tt>dur-fout: a=min(a,(dur-tt)/fout)
    return clamp(a)

# ---- 上下压暗渐变,提升画面上文字可读性 ----
def make_scrim():
    s=Image.new("RGBA",(W,H),(0,0,0,0))
    px=s.load()
    topH, botH = 230, 380
    for y in range(topH):
        a=int(120*(1-y/topH));
        for x in range(0,W,1): px[x,y]=(0,0,12,a)
    for y in range(H-botH,H):
        t=(y-(H-botH))/botH; a=int(175*t)
        for x in range(0,W,1): px[x,y]=(0,0,12,a)
    return s
# 用 1 列加速
def make_scrim_fast():
    col=Image.new("RGBA",(1,H),(0,0,0,0)); p=col.load()
    topH, botH=230,380
    for y in range(H):
        a=0
        if y<topH: a=int(120*(1-y/topH))
        elif y>H-botH: a=int(175*((y-(H-botH))/botH))
        p[0,y]=(0,0,12,a)
    return col.resize((W,H))
SCRIM=make_scrim_fast()

def txt_layer(s,fnt,fill,stroke=0,sfill=(0,0,0)):
    tmp=Image.new("RGBA",(8,8)); d=ImageDraw.Draw(tmp)
    bb=d.textbbox((0,0),s,font=fnt,stroke_width=stroke)
    w,h=bb[2]-bb[0],bb[3]-bb[1]; pad=stroke+6
    L=Image.new("RGBA",(w+pad*2,h+pad*2),(0,0,0,0))
    ImageDraw.Draw(L).text((pad-bb[0],pad-bb[1]),s,font=fnt,fill=fill,
        stroke_width=stroke,stroke_fill=sfill)
    return L
def blit(base,L,cx,cy,scale=1.0,alpha=1.0):
    if alpha<=.001 or scale<=.001: return
    lw,lh=L.size; nw,nh=max(1,int(lw*scale)),max(1,int(lh*scale))
    R=L.resize((nw,nh))
    if alpha<.999:
        R.putalpha(R.split()[3].point(lambda v:int(v*alpha)))
    base.alpha_composite(R,(int(cx-nw/2),int(cy-nh/2)))
def ctext(d,xy,s,fnt,fill,stroke=0,sfill=(0,0,0),anchor="mm"):
    d.text(xy,s,font=fnt,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=sfill)

# 小标签条(lower-third chip)
def chip(text, fnt, w, h, accent=GOLD, fill=(255,255,255,235), tcol=INK):
    c=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(c)
    d.rounded_rectangle([0,0,w-1,h-1],radius=h//2,fill=fill)
    d.rounded_rectangle([6,6,6+12,h-6],radius=6,fill=accent+(255,))
    ctext(d,(w//2+8,h//2),text,fnt,tcol)
    return c

def base_frame():
    f=Image.new("RGBA",(W,H),(0,0,0,0))
    f.alpha_composite(SCRIM)
    return f

# ---- 字幕(烧进叠加层,因本机 ffmpeg 无 libass)----
import re as _re
def parse_cues(path):
    cues=[]
    if not os.path.exists(path): return cues
    for blk in _re.split(r"\n\s*\n", open(path,encoding="utf-8").read().strip()):
        ls=[l for l in blk.splitlines() if l.strip()]
        if len(ls)<2: continue
        mm=_re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)",blk)
        if not mm: continue
        g=list(map(int,mm.groups()))
        st=g[0]*3600+g[1]*60+g[2]+g[3]/1000.0
        en=g[4]*3600+g[5]*60+g[6]+g[7]/1000.0
        cues.append((st,en,ls[-1]))
    return cues

_capd=ImageDraw.Draw(Image.new("RGBA",(8,8)))
def wrap_cn(text,fnt,maxw):
    lines=[]; cur=""
    for ch in text:
        if _capd.textlength(cur+ch,font=fnt)>maxw and cur:
            lines.append(cur); cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return lines

def draw_caption(f,text):
    if not text: return
    d=ImageDraw.Draw(f); fnt=font("b",52)
    lines=wrap_cn(text,fnt,1560); n=len(lines); lh=66
    for k,ln in enumerate(lines):
        cy=1014-(n-1-k)*lh
        ctext(d,(W//2,cy),ln,fnt,WHITE,stroke=4,sfill=(8,12,22))

# 顶部小标题(贯穿:左上角栏目感)
def kicker(f, tt, text):
    p,a=appear(tt,0.15,0.4)
    if a<=0: return
    d=ImageDraw.Draw(f)
    L=txt_layer(text,font("b",40),WHITE,stroke=3,sfill=NAVY)
    # 左上,带金色竖条
    x=90; y=80
    d.rectangle([x,y+6,x+10,y+54],fill=GOLD)
    blit(f,L,x+24+L.size[0]//2,y+30,1.0,a)

# ================= 段落 =================
def seg1(tt,dur):
    f=base_frame()
    A=seg_alpha(tt,dur)
    d=ImageDraw.Draw(f)
    # 小标
    p,a=appear(tt,0.2,0.5)
    if a>0:
        ctext(d,(W//2,300),"2026 世界杯 · 夺冠概率分析",font("r",44),WHITE,stroke=2,sfill=NAVY)
    # 主标题 阿根廷·能卫冕吗
    L=txt_layer("阿 根 廷",font("b",170),WHITE,stroke=6,sfill=NAVY)
    p,a=appear(tt,0.45,0.5); blit(f,L,W//2,470,lerp(.7,1,e_back(p)),a*A)
    L2=txt_layer("还 能 再 次 封 王 吗 ?",font("b",92),GOLD,stroke=5,sfill=NAVY)
    p2,a2=appear(tt,1.15,0.5); blit(f,L2,W//2,620,lerp(.8,1,e_back(p2)),a2*A)
    # 半透明整体
    return apply_alpha(f,A)

def seg2(tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur)
    kicker(f,tt,"王 朝 的 底 气")
    chips=[("FIFA 世界第一",GOLD),("美洲杯卫冕",SKY),("体系攻守均衡",GOLD)]
    xs=[W//2-470,W//2,W//2+470]; t0=[0.5,1.1,1.7]
    for (txt,ac),x,s in zip(chips,xs,t0):
        p,a=appear(tt,s,0.45)
        c=chip(txt,font("b",46),420,96,accent=ac)
        blit(f,c,x,820,lerp(.6,1,e_back(p)),a*A)
    return apply_alpha(f,A)

def seg3(tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur)
    kicker(f,tt,"新 一 代 · 扛 起 大 旗")
    names=["劳塔罗","J. 阿尔瓦雷斯","恩佐","麦卡利斯特"]
    t0=[0.5,1.2,1.9,2.6]; ys=[470,560,650,740]
    for nm,s,y in zip(names,t0,ys):
        p,a=appear(tt,s,0.4)
        c=chip(nm,font("b",50),470,80,accent=GOLD)
        dx=int(lerp(-90,0,e_out(p)))
        blit(f,c,300+dx,y,1.0,a*A)
    return apply_alpha(f,A)

def seg4(tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur)
    d=ImageDraw.Draw(f)
    p,a=appear(tt,0.2,0.4)
    if a>0:
        L=txt_layer("时 间 的 隐 忧",font("b",54),REDW,stroke=3,sfill=NAVY)
        x=90;y=80; d.rectangle([x,y+6,x+10,y+58],fill=REDW)
        blit(f,L,x+24+L.size[0]//2,y+32,1.0,a)
    # 大数字 39 计数(右侧)
    cuS,cuD=0.9,1.3; pc=clamp((tt-cuS)/cuD); val=int(round(lerp(30,39,e_out(pc))))
    pa,aa=appear(tt,0.8,0.4); cx=1360
    if aa>0:
        ctext(d,(cx,300),"梅 西 · 2026",font("r",46),SKY,stroke=2,sfill=NAVY)
        L=txt_layer(str(val),font("n",300),WHITE,stroke=6,sfill=(0,0,0))
        blit(f,L,cx,470,lerp(.6,1,e_back(pa)),aa*A)
        ctext(d,(cx,650),"岁",font("b",60),WHITE,stroke=3,sfill=NAVY)
    # 隐忧标签
    pts=["卫冕核心 渐老","新老交替","谁来接棒?"]
    t0=[3.2,3.8,4.4]; xs=[W//2-470,W//2,W//2+470]
    for s,tt0,x in zip(pts,t0,xs):
        p,a=appear(tt,tt0,0.4)
        c=chip(s,font("r",40),420,80,accent=REDW,fill=(20,28,52,215),tcol=(235,240,250))
        blit(f,c,x,830,lerp(.7,1,e_back(p)),a*A)
    return apply_alpha(f,A)

def seg5(tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur); d=ImageDraw.Draw(f)
    kicker(f,tt,"夺 冠 概 率 综 合 判 断")
    # 顶部变量 chips
    for i,(s,x) in enumerate(zip(["48队新赛制","北美酷暑","强敌环伺"],
                                 [W//2-430,W//2,W//2+430])):
        p,a=appear(tt,0.3+i*0.2,0.4)
        c=chip(s,font("r",38),360,72,accent=SKY)
        blit(f,c,x,210,1.0,a*A)
    # 大号概率 0->16 计数 然后 12-16%
    cuS,cuD=1.2,1.1; pc=clamp((tt-cuS)/cuD)
    pa,aa=appear(tt,1.1,0.4)
    if aa>0:
        s="12–16%" if pc>=.999 else f"{int(round(lerp(0,16,e_out(pc))))}%"
        L=txt_layer(s,font("n",200),GOLD,stroke=5,sfill=NAVY)
        blit(f,L,W//2,400,lerp(.7,1,e_back(pa)),aa*A)
    # 对比条形图(紧凑,下方)
    bars=[("西班牙",16),("阿根廷",15),("法国",14),("英格兰",12),("巴西",10)]
    bp,ba=appear(tt,2.8,0.5)
    if ba>0:
        bx,by,bw,gap,mh=W//2-430,760,120,95,170
        for i,(nm,v) in enumerate(bars):
            x=bx+i*(bw+gap-35)
            g=e_out(clamp((tt-2.8-i*0.1)/0.5)); bh=int(mh*(v/16)*g)
            hi=(nm=="阿根廷"); col=GOLD if hi else (95,125,170)
            d.rounded_rectangle([x,by-bh,x+bw,by],radius=8,fill=col+(int(255*A),))
            if g>.6:
                ctext(d,(x+bw//2,by-bh-24),f"{v}%",font("n",28),
                      GOLD if hi else (205,215,230))
                ctext(d,(x+bw//2,by+24),nm,font("b" if hi else "r",28),
                      GOLD if hi else (210,220,235))
    # 概率出处说明
    pc2,ac2=appear(tt,3.8,0.6)
    if ac2>0:
        ctext(d,(W//2,868),"* 夺冠概率由 DeepSeek 谨慎推算",font("r",30),
              (180,196,216),anchor="mm")
    return apply_alpha(f,A)

def seg6(tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur)
    L=txt_layer("2026 · 最 后 一 舞",font("b",140),WHITE,stroke=6,sfill=NAVY)
    p,a=appear(tt,0.2,0.5); blit(f,L,W//2,440,lerp(.75,1,e_back(p)),a*A)
    L2=txt_layer("你 敢 赌 他 笑 到 最 后 吗 ?",font("b",72),GOLD,stroke=5,sfill=NAVY)
    p2,a2=appear(tt,0.9,0.5); blit(f,L2,W//2,600,lerp(.85,1,e_out(p2)),a2*A)
    return apply_alpha(f,A)

def apply_alpha(f,A):
    if A>=.999: return f
    r,g,b,al=f.split()
    al=al.point(lambda v:int(v*A)); f=Image.merge("RGBA",(r,g,b,al))
    return f

def seg_dimaria(tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur); d=ImageDraw.Draw(f)
    p,a=appear(tt,0.2,0.4)
    if a>0:
        L=txt_layer("锋 线 隐 患 · 天 使 退 役",font("b",48),REDW,stroke=3,sfill=NAVY)
        x=90;y=80; d.rectangle([x,y+6,x+10,y+58],fill=REDW)
        blit(f,L,x+24+L.size[0]//2,y+32,1.0,a)
    pa,aa=appear(tt,0.7,0.5)
    if aa>0:
        L=txt_layer("决 赛 先 生",font("b",148),GOLD,stroke=6,sfill=NAVY)
        blit(f,L,W//2,330,lerp(.7,1,e_back(pa)),aa*A)
        ctext(d,(W//2,452),"天 使 · 迪 马 利 亚",font("b",54),WHITE,stroke=3,sfill=NAVY)
    pts=["2021美洲杯 决赛进球","2022世界杯 决赛进球","脚头硬 · 大赛爆破手"]
    t0=[1.8,2.5,3.2]; xs=[W//2-490,W//2,W//2+490]
    for s,tt0,x in zip(pts,t0,xs):
        p,a=appear(tt,tt0,0.4)
        c=chip(s,font("r",36),470,80,accent=REDW,fill=(20,28,52,215),tcol=(235,240,250))
        blit(f,c,x,835,lerp(.7,1,e_back(p)),a*A)
    return apply_alpha(f,A)

FUNCS=[seg1,seg2,seg3,seg4,seg_dimaria,seg5,seg6]

def active_caption(cues,tt):
    for st,en,t in cues:
        if st<=tt<en: return t
    return ""

def render():
    for si,(fn,dur) in enumerate(zip(FUNCS,DUR),start=1):
        od=os.path.join(OUT,f"seg{si}"); os.makedirs(od,exist_ok=True)
        cues=parse_cues(os.path.join(ROOT,"build","subs",f"seg{si}.vtt"))
        n=round(dur*FPS)
        for fi in range(n):
            tt=fi/FPS
            fr=fn(tt,dur)
            draw_caption(fr, active_caption(cues,tt))
            fr.save(os.path.join(od,f"{fi:04d}.png"))
        print(f"seg{si}: {n} 帧 -> {od}")
    print("OVERLAYS DONE")

if __name__=="__main__":
    render()
