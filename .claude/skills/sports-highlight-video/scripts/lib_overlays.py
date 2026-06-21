# -*- coding: utf-8 -*-
"""
体育剪辑叠加层组件库(Pillow,输出带alpha的RGBA帧)。
为什么用Pillow烧叠加层而不用ffmpeg字幕/绘图滤镜?——很多精简版ffmpeg(如homebrew某些bottle)
没编译 libass / drawtext / ass 滤镜,subtitles/ass/drawtext 全部不可用。用Pillow自己画+烧进
透明叠加层,既绕开依赖,又能精确控制中文字体与动画。详见 reference/gotchas.md。

布局组件(由 project.json 每段的 overlay.layout 选择):
  title      大标题+副标(开场/收尾)        参数: title, subtitle, sup, kicker?
  chips      一行标签卡(实力/底气)          参数: kicker, chips[]
  namelist   左侧滑入的名字卡(新生代/名单)  参数: kicker, names[]
  stat       右侧大数字计数(年龄/身价/数据) 参数: kicker, count_to, unit, label, label_sup, chips[]
  spotlight  人物聚光(决赛先生/MVP)         参数: kicker, big, name, chips[]
  bars       概率/数据条形图                 参数: kicker, top_chips[], big, bars[[name,val]], highlight, note
  end        收尾大标题+反问                 参数: title, subtitle
所有组件都画了上下压暗渐变(scrim)保证画面上文字可读;字幕由 render_overlays 统一画在底部。
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30

# ---- 主题(由调用方用 project.json 的 theme 覆盖)----
THEME = {
    "sky":  (117, 188, 240),
    "gold": (252, 209, 50),
    "navy": (10, 22, 50),
    "white":(255, 255, 255),
    "warn": (240, 90, 84),
    "ink":  (12, 22, 46),
    "chip_text": (12, 22, 46),
}
# 字体:macOS自带。Hiragino Sans GB ttc索引 0=W3(常规) 2=W6(粗);Arial Black 大号拉丁数字。
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
def C(name): return tuple(THEME[name])

# ---- 缓动 ----
def clamp(x,a=0.,b=1.): return max(a,min(b,x))
def lerp(a,b,t): return a+(b-a)*t
def e_io(t): t=clamp(t); return .5-.5*math.cos(math.pi*t)
def e_out(t): t=clamp(t); return 1-(1-t)**3
def e_back(t):
    t=clamp(t); c1=1.70158; c3=c1+1
    return 1+c3*(t-1)**3+c1*(t-1)**2
def appear(tt,s,d):
    if tt<s: return 0.,0.
    p=clamp((tt-s)/d); return p,p
def seg_alpha(tt,dur,fin=0.3,fout=0.35):
    a=1.
    if tt<fin: a=min(a,tt/fin)
    if tt>dur-fout: a=min(a,(dur-tt)/fout)
    return clamp(a)

# ---- 压暗渐变(提升画面上文字可读性)----
def _scrim():
    col=Image.new("RGBA",(1,H),(0,0,0,0)); p=col.load()
    topH,botH=230,380
    for y in range(H):
        a=0
        if y<topH: a=int(120*(1-y/topH))
        elif y>H-botH: a=int(175*((y-(H-botH))/botH))
        p[0,y]=(0,0,12,a)
    return col.resize((W,H))
SCRIM=None
def base_frame():
    global SCRIM
    if SCRIM is None: SCRIM=_scrim()
    f=Image.new("RGBA",(W,H),(0,0,0,0)); f.alpha_composite(SCRIM); return f

# ---- 绘制助手 ----
def txt_layer(s,fnt,fill,stroke=0,sfill=(0,0,0)):
    tmp=Image.new("RGBA",(8,8)); d=ImageDraw.Draw(tmp)
    bb=d.textbbox((0,0),s,font=fnt,stroke_width=stroke)
    w,h=bb[2]-bb[0],bb[3]-bb[1]; pad=stroke+6
    L=Image.new("RGBA",(w+pad*2,h+pad*2),(0,0,0,0))
    ImageDraw.Draw(L).text((pad-bb[0],pad-bb[1]),s,font=fnt,fill=fill,stroke_width=stroke,stroke_fill=sfill)
    return L
def blit(base,L,cx,cy,scale=1.,alpha=1.):
    if alpha<=.001 or scale<=.001: return
    lw,lh=L.size; nw,nh=max(1,int(lw*scale)),max(1,int(lh*scale))
    R=L.resize((nw,nh))
    if alpha<.999: R.putalpha(R.split()[3].point(lambda v:int(v*alpha)))
    base.alpha_composite(R,(int(cx-nw/2),int(cy-nh/2)))
def ctext(d,xy,s,fnt,fill,stroke=0,sfill=(0,0,0),anchor="mm"):
    d.text(xy,s,font=fnt,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=sfill)
def chip(text,fnt,w,h,accent=None,fill=(255,255,255,235),tcol=None):
    accent=accent or C("gold"); tcol=tcol or C("chip_text")
    c=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(c)
    d.rounded_rectangle([0,0,w-1,h-1],radius=h//2,fill=fill)
    d.rounded_rectangle([6,6,6+12,h-6],radius=6,fill=accent+(255,))
    ctext(d,(w//2+8,h//2),text,fnt,tcol)
    return c
def apply_alpha(f,A):
    if A>=.999: return f
    r,g,b,al=f.split(); al=al.point(lambda v:int(v*A)); return Image.merge("RGBA",(r,g,b,al))
def kicker(f,tt,text,color=None):
    color=color or C("white")
    p,a=appear(tt,0.15,0.4)
    if a<=0: return
    L=txt_layer(text,font("b",46),color,stroke=3,sfill=C("navy"))
    lw,lh=L.size
    # 深色底板:上移并左扩,盖住左上角转播台标/比分牌角标,保证标题可读
    x,y=64,18; barw=10; gap=16; pl=22; pad_r=26
    pw=(x-pl)+barw+gap+lw+pad_r; ph=64
    plate=Image.new("RGBA",(pw,ph),(0,0,0,0))
    ImageDraw.Draw(plate).rounded_rectangle([0,0,pw-1,ph-1],radius=14,fill=C("navy")+(212,))
    f.alpha_composite(apply_alpha(plate,a),(pl,y))
    d=ImageDraw.Draw(f)
    d.rectangle([x,y+12,x+barw,y+ph-12],fill=C("gold") if color==C("white") else color)
    blit(f,L,x+barw+gap+lw//2,y+ph//2,1.,a)

# ---- 字幕(烧进叠加层底部)----
import re as _re
def parse_cues(path):
    cues=[]
    if not path or not os.path.exists(path): return cues
    for blk in _re.split(r"\n\s*\n",open(path,encoding="utf-8").read().strip()):
        ls=[l for l in blk.splitlines() if l.strip()]
        if len(ls)<2: continue
        m=_re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)",blk)
        if not m: continue
        g=list(map(int,m.groups()))
        st=g[0]*3600+g[1]*60+g[2]+g[3]/1000.; en=g[4]*3600+g[5]*60+g[6]+g[7]/1000.
        cues.append((st,en,ls[-1]))
    return cues
def active_caption(cues,tt):
    for st,en,t in cues:
        if st<=tt<en: return t
    return ""
_cap=ImageDraw.Draw(Image.new("RGBA",(8,8)))
def _wrap(text,fnt,maxw):
    lines=[]; cur=""
    for ch in text:
        if _cap.textlength(cur+ch,font=fnt)>maxw and cur: lines.append(cur); cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return lines
def draw_caption(f,text):
    if not text: return
    d=ImageDraw.Draw(f); fnt=font("b",52)
    lines=_wrap(text,fnt,1560); n=len(lines); lh=66
    for k,ln in enumerate(lines):
        ctext(d,(W//2,1014-(n-1-k)*lh),ln,fnt,C("white"),stroke=4,sfill=(8,12,22))

def draw_watermark(f,text="思考的我",margin=40):
    """右下角方形水印(频道署名),全片持续。4字按2x2排布。"""
    if not text: return
    side=132; r=22
    x1,y1=W-margin-side,H-margin-side
    bg=Image.new("RGBA",(side,side),(0,0,0,0))
    bd=ImageDraw.Draw(bg)
    bd.rounded_rectangle([0,0,side-1,side-1],radius=r,fill=(0,0,12,120))
    bd.rounded_rectangle([0,0,side-1,side-1],radius=r,outline=C("gold")+(235,),width=3)
    f.alpha_composite(bg,(x1,y1))
    d=ImageDraw.Draw(f)
    chars=list(text)
    if len(chars)==4:  # 2x2 网格
        fnt=font("b",46)
        cx,cy=x1+side//2,y1+side//2; off=30
        pos=[(-1,-1),(1,-1),(-1,1),(1,1)]
        for ch,(dx,dy) in zip(chars,pos):
            ctext(d,(cx+dx*off,cy+dy*off),ch,fnt,C("white"),stroke=3,sfill=C("navy"))
    else:
        fnt=font("b",38)
        ctext(d,(x1+side//2,y1+side//2),text,fnt,C("white"),stroke=3,sfill=C("navy"))

# ================= 布局组件 =================
def _accent(spec,key,default="gold"):
    return C(spec.get(key,default))

def layout_title(f,tt,dur,A,s):
    d=ImageDraw.Draw(f)
    if s.get("sup"):
        p,a=appear(tt,0.2,0.5)
        if a>0: ctext(d,(W//2,300),s["sup"],font("r",44),C("white"),stroke=2,sfill=C("navy"))
    L=txt_layer(s["title"],font("b",s.get("title_size",170)),C("white"),stroke=6,sfill=C("navy"))
    p,a=appear(tt,0.45,0.5); blit(f,L,W//2,s.get("title_y",470),lerp(.7,1,e_back(p)),a*A)
    if s.get("subtitle"):
        L2=txt_layer(s["subtitle"],font("b",s.get("sub_size",92)),C("gold"),stroke=5,sfill=C("navy"))
        p2,a2=appear(tt,1.15,0.5); blit(f,L2,W//2,s.get("sub_y",620),lerp(.8,1,e_back(p2)),a2*A)
    return f

def layout_end(f,tt,dur,A,s):
    L=txt_layer(s["title"],font("b",s.get("title_size",140)),C("white"),stroke=6,sfill=C("navy"))
    p,a=appear(tt,0.2,0.5); blit(f,L,W//2,440,lerp(.75,1,e_back(p)),a*A)
    if s.get("subtitle"):
        L2=txt_layer(s["subtitle"],font("b",72),C("gold"),stroke=5,sfill=C("navy"))
        p2,a2=appear(tt,0.9,0.5); blit(f,L2,W//2,600,lerp(.85,1,e_out(p2)),a2*A)
    return f

def layout_chips(f,tt,dur,A,s):
    if s.get("kicker"): kicker(f,tt,s["kicker"])
    chips=s["chips"]; n=len(chips); gap=470
    xs=[W//2+(i-(n-1)/2)*gap for i in range(n)]
    for i,(txt,x) in enumerate(zip(chips,xs)):
        p,a=appear(tt,0.5+i*0.6,0.45)
        c=chip(txt,font("b",46),s.get("chip_w",420),96,accent=_accent(s,"accent"))
        blit(f,c,x,s.get("y",820),lerp(.6,1,e_back(p)),a*A)
    return f

def layout_namelist(f,tt,dur,A,s):
    if s.get("kicker"): kicker(f,tt,s["kicker"])
    names=s["names"]; ys=[470+i*90 for i in range(len(names))]
    for i,(nm,y) in enumerate(zip(names,ys)):
        p,a=appear(tt,0.5+i*0.7,0.4)
        c=chip(nm,font("b",50),s.get("chip_w",470),80,accent=_accent(s,"accent"))
        dx=int(lerp(-90,0,e_out(p)))
        blit(f,c,s.get("x",300)+dx,y,1.,a*A)
    return f

def layout_stat(f,tt,dur,A,s):
    d=ImageDraw.Draw(f)
    if s.get("kicker"): kicker(f,tt,s["kicker"],color=_accent(s,"kicker_color","warn") if s.get("kicker_color") else None)
    cx=s.get("x",1360); frm=s.get("count_from",0); to=s["count_to"]
    cuS,cuD=0.9,1.3; pc=clamp((tt-cuS)/cuD); val=int(round(lerp(frm,to,e_out(pc))))
    pa,aa=appear(tt,0.8,0.4)
    if aa>0:
        if s.get("label_sup"): ctext(d,(cx,300),s["label_sup"],font("r",46),C("sky"),stroke=2,sfill=C("navy"))
        L=txt_layer(str(val),font("n",s.get("num_size",300)),C("white"),stroke=6,sfill=(0,0,0))
        blit(f,L,cx,470,lerp(.6,1,e_back(pa)),aa*A)
        if s.get("unit"): ctext(d,(cx,650),s["unit"],font("b",60),C("white"),stroke=3,sfill=C("navy"))
    for i,(txt,x) in enumerate(zip(s.get("chips",[]),
            [W//2+(i-(len(s.get("chips",[]))-1)/2)*470 for i in range(len(s.get("chips",[])))])):
        p,a=appear(tt,3.2+i*0.6,0.4)
        c=chip(txt,font("r",40),420,80,accent=C("warn"),fill=(20,28,52,215),tcol=(235,240,250))
        blit(f,c,x,830,lerp(.7,1,e_back(p)),a*A)
    return f

def layout_spotlight(f,tt,dur,A,s):
    d=ImageDraw.Draw(f)
    if s.get("kicker"): kicker(f,tt,s["kicker"],color=C(s.get("kicker_color","warn")))
    pa,aa=appear(tt,0.7,0.5)
    if aa>0:
        L=txt_layer(s["big"],font("b",s.get("big_size",148)),C("gold"),stroke=6,sfill=C("navy"))
        blit(f,L,W//2,330,lerp(.7,1,e_back(pa)),aa*A)
        if s.get("name"): ctext(d,(W//2,452),s["name"],font("b",54),C("white"),stroke=3,sfill=C("navy"))
    chips=s.get("chips",[]); xs=[W//2+(i-(len(chips)-1)/2)*490 for i in range(len(chips))]
    for i,(txt,x) in enumerate(zip(chips,xs)):
        p,a=appear(tt,1.8+i*0.7,0.4)
        c=chip(txt,font("r",36),470,80,accent=C("warn"),fill=(20,28,52,215),tcol=(235,240,250))
        blit(f,c,x,835,lerp(.7,1,e_back(p)),a*A)
    return f

def layout_bars(f,tt,dur,A,s):
    d=ImageDraw.Draw(f)
    if s.get("kicker"): kicker(f,tt,s["kicker"])
    tc=s.get("top_chips",[]); xs=[W//2+(i-(len(tc)-1)/2)*430 for i in range(len(tc))]
    for i,(txt,x) in enumerate(zip(tc,xs)):
        p,a=appear(tt,0.3+i*0.2,0.4)
        c=chip(txt,font("r",38),360,72,accent=C("sky")); blit(f,c,x,210,1.,a*A)
    if s.get("big"):
        pa,aa=appear(tt,1.1,0.4)
        if aa>0:
            L=txt_layer(s["big"],font("n",200),C("gold"),stroke=5,sfill=C("navy"))
            blit(f,L,W//2,400,lerp(.7,1,e_back(pa)),aa*A)
    bars=s.get("bars",[]); hi=s.get("highlight")
    bp,ba=appear(tt,2.8,0.5)
    if ba>0 and bars:
        maxv=max(v for _,v in bars); n=len(bars)
        bx,by,bw,gap,mh=W//2-430,760,120,95,170
        for i,(nm,v) in enumerate(bars):
            x=bx+i*(bw+gap-35); g=e_out(clamp((tt-2.8-i*0.1)/0.5)); bh=int(mh*(v/maxv)*g)
            on=(nm==hi); col=C("gold") if on else (95,125,170)
            d.rounded_rectangle([x,by-bh,x+bw,by],radius=8,fill=col+(int(255*A),))
            if g>.6:
                ctext(d,(x+bw//2,by-bh-24),f"{v}%",font("n",28),C("gold") if on else (205,215,230))
                ctext(d,(x+bw//2,by+24),nm,font("b" if on else "r",28),C("gold") if on else (210,220,235))
    if s.get("note"):
        p2,a2=appear(tt,3.8,0.6)
        if a2>0: ctext(d,(W//2,868),s["note"],font("r",30),(180,196,216))
    return f

LAYOUTS={"title":layout_title,"end":layout_end,"chips":layout_chips,"namelist":layout_namelist,
         "stat":layout_stat,"spotlight":layout_spotlight,"bars":layout_bars}

def render_overlay_frame(spec,tt,dur):
    """画一帧叠加层(不含字幕)。spec=segment.overlay dict。"""
    f=base_frame(); A=seg_alpha(tt,dur)
    fn=LAYOUTS.get(spec.get("layout","title"))
    if fn: fn(f,tt,dur,A,spec)
    return apply_alpha(f,A)
