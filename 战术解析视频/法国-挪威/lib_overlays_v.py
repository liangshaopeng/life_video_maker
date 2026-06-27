# -*- coding: utf-8 -*-
"""
竖屏(1080x1920)战术解析叠加层库 —— 为「足球战术解析视频」新写。
和原 skill 的 lib_overlays.py 区别:
  - 原生竖屏 1080x1920(不是 16:9 转竖)。
  - 画面以「带状」嵌在中间(由 assemble_v 合成),本库负责上/下面板的文字 + 画面带上的 telestrator 标注。
  - 新增 telestrator 标注层:在真实画面帧上画 圈(球员)/箭头(传球·跑动)/高亮空当(空间)/决策点标签。

为什么仍用 Pillow 烧帧而非 ffmpeg drawtext/字幕:本机 ffmpeg 多半没 libass/drawtext(见原 skill gotchas #1)。

布局(overlay.layout):
  title        开场/分章大标题(全屏)              title, subtitle, sup
  beat         三段式的「导火索/终结」头(画面在播)  phase, idx, title, kicker, points[]
  telestrator  三段式的「决策点」(画面定格+标注)    phase, idx, title, kicker, points[], marks[]
  end          收尾(全屏)                          title, subtitle

画面带几何:BAND_TOP..BAND_BOT,宽 1080。marks 的坐标用「画面带内坐标」(0..1080 x, 0..BAND_H y),
渲染时自动加 BAND_TOP 偏移,所见即所得。
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BAND_TOP = 384            # 画面带上沿
BAND_H   = 608            # 1080 宽的 16:9 画面高(1280x720 -> 1080x607.5≈608)
BAND_BOT = BAND_TOP + BAND_H

# ---- 主题(由 project.json 的 theme 覆盖)----
THEME = {
    "sky":  (96, 178, 240),
    "gold": (252, 209, 50),
    "navy": (8, 16, 34),
    "white":(255, 255, 255),
    "warn": (244, 86, 80),
    "good": (74, 210, 140),
    "ink":  (10, 18, 38),
    "chip_text": (14, 22, 44),
    "line": (120, 200, 255),     # telestrator 默认线色
}
F_CN  = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F_NUM = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
_fc = {}
def font(kind, size):
    k=(kind,size)
    if k in _fc: return _fc[k]
    if kind=="b":   f=ImageFont.truetype(F_CN,size,index=2)   # W6 粗
    elif kind=="r": f=ImageFont.truetype(F_CN,size,index=0)   # W3 常规
    else:           f=ImageFont.truetype(F_NUM,size,index=0)  # 大号拉丁数字
    _fc[k]=f; return f
def C(name):
    v=THEME.get(name,name)
    return tuple(v) if isinstance(v,(list,tuple)) else v

# ---- 缓动 ----
def clamp(x,a=0.,b=1.): return max(a,min(b,x))
def lerp(a,b,t): return a+(b-a)*t
def e_out(t): t=clamp(t); return 1-(1-t)**3
def e_io(t): t=clamp(t); return .5-.5*math.cos(math.pi*t)
def e_back(t):
    t=clamp(t); c1=1.70158; c3=c1+1
    return 1+c3*(t-1)**3+c1*(t-1)**2
def appear(tt,s,d):
    if tt<s: return 0.,0.
    p=clamp((tt-s)/d); return p,p
def seg_alpha(tt,dur,fin=0.3,fout=0.32):
    a=1.
    if tt<fin: a=min(a,tt/fin)
    if tt>dur-fout: a=min(a,(dur-tt)/fout)
    return clamp(a)

# ---- 基础绘制助手 ----
def _txt_layer(s,fnt,fill,stroke=0,sfill=(0,0,0)):
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
def apply_alpha(f,A):
    if A>=.999: return f
    r,g,b,al=f.split(); al=al.point(lambda v:int(v*A)); return Image.merge("RGBA",(r,g,b,al))

# ---- 上/下面板压暗(让画面带之外的文字区有底,且画面带不糊)----
_SCRIM=None
def _scrim():
    global _SCRIM
    if _SCRIM is not None: return _SCRIM
    col=Image.new("RGBA",(1,H),(0,0,0,0)); p=col.load()
    nav=C("navy")
    for y in range(H):
        a=0
        if y<BAND_TOP:                       # 顶部面板:越往上越暗
            a=int(150*clamp((BAND_TOP-y)/BAND_TOP))
        elif y>BAND_BOT:                     # 底部面板:越往下越暗
            a=int(180*clamp((y-BAND_BOT)/(H-BAND_BOT)))
        else:                                # 画面带:轻微上下羽化,不挡画面
            edge=min(y-BAND_TOP,BAND_BOT-y)
            a=int(70*clamp((18-edge)/18)) if edge<18 else 0
        p[0,y]=(nav[0],nav[1],nav[2],a)
    _SCRIM=col.resize((W,H)); return _SCRIM
def base_frame():
    f=Image.new("RGBA",(W,H),(0,0,0,0)); f.alpha_composite(_scrim()); return f

# ---- 圆角标签 ----
def pill(text,fnt,pad_x=26,h=64,bg=(255,255,255,235),tcol=None,bar=None):
    tcol=tcol or C("chip_text")
    tmp=ImageDraw.Draw(Image.new("RGBA",(8,8)))
    tw=tmp.textlength(text,font=fnt); w=int(tw)+pad_x*2+(18 if bar else 0)
    c=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(c)
    d.rounded_rectangle([0,0,w-1,h-1],radius=h//2,fill=bg)
    x0=pad_x
    if bar:
        d.rounded_rectangle([10,10,10+10,h-10],radius=5,fill=bar+(255,)); x0=pad_x+18
    ctext(d,(x0+tw/2,h//2),text,fnt,tcol)
    return c

# ================= 顶部面板:phase + 标题 + kicker =================
def draw_header(f,tt,spec):
    d=ImageDraw.Draw(f)
    phase=spec.get("phase"); idx=spec.get("idx")
    accent=C(spec.get("accent","gold"))
    # phase 胶囊(导火索/决策点/终结)
    if phase:
        p,a=appear(tt,0.10,0.4)
        if a>0:
            lbl=f"{idx}  {phase}" if idx else phase
            pl=pill(lbl,font("b",40),h=70,bg=C("navy")+(225,),tcol=C("white"),bar=accent)
            blit(f,pl,70+pl.size[0]//2,150,lerp(.85,1,e_out(p)),a)
    # 大标题(支持 \n 两行)
    title=spec.get("title")
    if title:
        lines=title.split("\n")
        ty=232 if len(lines)==1 else 210
        for li,ln in enumerate(lines):
            p,a=appear(tt,0.28+li*0.12,0.5)
            L=_txt_layer(ln,font("b",spec.get("title_size",76)),C("white"),stroke=4,sfill=C("navy"))
            blit(f,L,W//2,ty+li*86,lerp(.9,1,e_back(p)),a)
    # kicker(标题下方一行,accent 色)
    kick=spec.get("kicker")
    if kick:
        ky=312 if (title and len(title.split("\n"))>1) else 300
        p,a=appear(tt,0.55,0.5)
        L=_txt_layer(kick,font("b",38),accent,stroke=3,sfill=C("navy"))
        blit(f,L,W//2,ky,1.,a*0.96)

# ================= 底部面板:要点 chips(① ② ③ 竖排)=================
def draw_points(f,tt,spec,y0=1050):
    pts=spec.get("points",[]); accent=C(spec.get("accent","gold"))
    gap=128
    for i,pt in enumerate(pts):
        p,a=appear(tt,0.9+i*0.55,0.5)
        if a<=0: continue
        y=y0+i*gap; dx=int(lerp(-70,0,e_out(p)))
        # 序号徽标
        bw=84
        badge=Image.new("RGBA",(bw,bw),(0,0,0,0)); bd=ImageDraw.Draw(badge)
        bd.rounded_rectangle([0,0,bw-1,bw-1],radius=22,fill=accent+(255,))
        ctext(bd,(bw//2,bw//2),str(i+1),font("n",46),C("navy"))
        f.alpha_composite(apply_alpha(badge,a),(70+dx,y-bw//2))
        # 文本(可能两行,按 \n)
        tx=70+bw+30+dx
        lns=pt.split("\n")
        for li,ln in enumerate(lns):
            yy=y-(len(lns)-1)*30+li*60
            L=_txt_layer(ln,font("b",46),C("white"),stroke=3,sfill=C("navy"))
            lw,lh=L.size
            if a<.999: L=apply_alpha(L,a)
            f.alpha_composite(L,(tx,int(yy-lh/2)))

# ================= telestrator:画面带上的标注 =================
def _B(x,y):  # 画面带内坐标 -> 全画布坐标
    return x, BAND_TOP+y
def _arrowhead(d,x,y,ang,size,col):
    a1=ang+math.radians(150); a2=ang-math.radians(150)
    p=[(x,y),(x+size*math.cos(a1),y+size*math.sin(a1)),(x+size*math.cos(a2),y+size*math.sin(a2))]
    d.polygon(p,fill=col)
def _qbez(p0,p1,p2,t):
    x=(1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0]
    y=(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]
    return x,y

def draw_marks(f,tt,spec):
    """marks: list of dicts. 坐标=画面带内(0..1080, 0..608)。
       circle {x,y,r,color?,label?,t?}      圈球员
       zone   {x,y,rx,ry,color?,t?}         高亮空当(椭圆,半透明填充+虚线)
       rect   {x,y,w,h,color?,t?}           高亮矩形空当
       arrow  {x1,y1,x2,y2,cx?,cy?,color?,style?,t?,width?}  传球/跑动箭头(可弯)
       tag    {x,y,text,color?,t?,anchor?}  小标签(决策点说明)
    """
    marks=spec.get("marks",[])
    # 先画 zone(底),再 arrow,再 circle,最后 tag(顶)
    order={"zone":0,"rect":0,"arrow":1,"circle":2,"tag":3}
    for m in sorted(marks,key=lambda x:order.get(x.get("type"),9)):
        typ=m.get("type"); t0=m.get("t",0.5)
        p,a=appear(tt,t0,m.get("dur",0.5))
        if a<=0: continue
        col=C(m.get("color","line"))
        if typ=="zone":
            x,y=_B(m["x"],m["y"]); rx,ry=m["rx"],m["ry"]
            ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            grow=lerp(.6,1,e_out(p))
            bb=[x-rx*grow,y-ry*grow,x+rx*grow,y+ry*grow]
            od.ellipse(bb,fill=col+(int(70*a),))
            # 虚线描边
            _dash_ellipse(od,bb,col+(int(235*a),),width=5,dash=26,gap=16)
            f.alpha_composite(ov)
        elif typ=="rect":
            x,y=_B(m["x"],m["y"]); w_,h_=m["w"],m["h"]
            ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            od.rectangle([x,y,x+w_,y+h_],fill=col+(int(60*a),))
            _dash_rect(od,[x,y,x+w_,y+h_],col+(int(235*a),),5,26,14)
            f.alpha_composite(ov)
        elif typ=="circle":
            x,y=_B(m["x"],m["y"]); r=m.get("r",40)
            ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            rr=r*lerp(1.25,1.0,e_out(p))         # 收缩聚焦
            od.ellipse([x-rr,y-rr,x+rr,y+rr],outline=col+(int(255*a),),width=7)
            od.ellipse([x-rr-7,y-rr-7,x+rr+7,y+rr+7],outline=C("navy")+(int(150*a),),width=2)
            f.alpha_composite(ov)
            if m.get("label"):
                L=_txt_layer(m["label"],font("b",34),col,stroke=3,sfill=C("navy"))
                blit(f,L,x,y-rr-30,1.,a)
        elif typ=="arrow":
            p0=_B(m["x1"],m["y1"]); p2=_B(m["x2"],m["y2"])
            pc=_B(m.get("cx",(m["x1"]+m["x2"])/2),m.get("cy",(m["y1"]+m["y2"])/2))
            ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
            wdt=m.get("width",9); dashed=m.get("style")=="dashed"
            prog=e_io(p)                          # 箭身随时间画出
            N=42; pts=[_qbez(p0,pc,p2,i/N*prog) for i in range(N+1)]
            for i in range(len(pts)-1):
                if dashed and (i//3)%2==1: continue
                od.line([pts[i],pts[i+1]],fill=col+(int(255*a),),width=wdt)
            # 箭头(描边底+亮线已画),收尾画箭头
            if prog>0.96:
                ex,ey=pts[-1]; bx,by=pts[-4]
                ang=math.atan2(ey-by,ex-bx)
                _arrowhead(od,ex,ey,ang,m.get("head",30),col+(int(255*a),))
            f.alpha_composite(ov)
        elif typ=="tag":
            x,y=_B(m["x"],m["y"])
            anc=m.get("anchor","mm")
            pl=pill(m["text"],font("b",36),h=66,bg=col+(int(240*a),),tcol=C("navy"))
            pw,ph=pl.size
            ax = x if anc[0]=="m" else (x-pw//2 if anc[0]=="l" else x+pw//2)
            blit(f,pl,ax,y,lerp(.8,1,e_back(p)),a)

def _dash_ellipse(d,bb,col,width=4,dash=24,gap=14):
    x0,y0,x1,y1=bb; cx,cy=(x0+x1)/2,(y0+y1)/2; rx,ry=(x1-x0)/2,(y1-y0)/2
    if rx<=0 or ry<=0: return
    per=math.pi*(3*(rx+ry)-math.sqrt((3*rx+ry)*(rx+3*ry)))
    n=max(8,int(per/(dash+gap))); on=True; step=2*math.pi/n
    for i in range(n):
        a0=i*step; a1=a0+step*dash/(dash+gap)
        if on:
            seg=[(cx+rx*math.cos(a0+ (a1-a0)*j/6),cy+ry*math.sin(a0+(a1-a0)*j/6)) for j in range(7)]
            d.line(seg,fill=col,width=width)
        on=not on if gap>0 else on
def _dash_rect(d,bb,col,width=4,dash=24,gap=14):
    x0,y0,x1,y1=bb
    edges=[((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]
    for (sx,sy),(ex,ey) in edges:
        L=math.hypot(ex-sx,ey-sy); n=max(1,int(L/(dash+gap)))
        for i in range(n):
            t0=i*(dash+gap)/L; t1=min(1,(i*(dash+gap)+dash)/L)
            d.line([(sx+(ex-sx)*t0,sy+(ey-sy)*t0),(sx+(ex-sx)*t1,sy+(ey-sy)*t1)],fill=col,width=width)

# ================= 字幕(底部)=================
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
_capd=ImageDraw.Draw(Image.new("RGBA",(8,8)))
def _wrap(text,fnt,maxw):
    lines=[]; cur=""
    for ch in text:
        if _capd.textlength(cur+ch,font=fnt)>maxw and cur: lines.append(cur); cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return lines
def draw_caption(f,text,y=1690):
    if not text: return
    d=ImageDraw.Draw(f); fnt=font("b",50)
    lines=_wrap(text,fnt,980); n=len(lines); lh=64
    for k,ln in enumerate(lines):
        ctext(d,(W//2,y-(n-1-k)*lh),ln,fnt,C("white"),stroke=5,sfill=(6,10,20))

# ================= 水印 =================
def draw_watermark(f,text="思考的我",margin=40):
    if not text: return
    side=118; r=20
    x1,y1=W-margin-side,H-margin-side-70
    bg=Image.new("RGBA",(side,side),(0,0,0,0)); bd=ImageDraw.Draw(bg)
    bd.rounded_rectangle([0,0,side-1,side-1],radius=r,fill=(0,0,12,120))
    bd.rounded_rectangle([0,0,side-1,side-1],radius=r,outline=C("gold")+(235,),width=3)
    f.alpha_composite(bg,(x1,y1))
    d=ImageDraw.Draw(f); chars=list(text)
    if len(chars)==4:
        fnt=font("b",40); cx,cy=x1+side//2,y1+side//2; off=27
        for ch,(dx,dy) in zip(chars,[(-1,-1),(1,-1),(-1,1),(1,1)]):
            ctext(d,(cx+dx*off,cy+dy*off),ch,fnt,C("white"),stroke=3,sfill=C("navy"))
    else:
        ctext(d,(x1+side//2,y1+side//2),text,font("b",34),C("white"),stroke=3,sfill=C("navy"))

# ================= 全屏 标题 / 收尾 =================
def layout_title(f,tt,dur,A,s):
    d=ImageDraw.Draw(f)
    if s.get("sup"):
        p,a=appear(tt,0.2,0.5)
        if a>0: ctext(d,(W//2,560),s["sup"],font("r",44),C("sky"),stroke=2,sfill=C("navy"))
    lines=s.get("title","").split("\n")
    for li,ln in enumerate(lines):
        p,a=appear(tt,0.45+li*0.18,0.55)
        L=_txt_layer(ln,font("b",s.get("title_size",128)),C("white"),stroke=6,sfill=C("navy"))
        blit(f,L,W//2,720+li*150,lerp(.7,1,e_back(p)),a*A)
    if s.get("subtitle"):
        p2,a2=appear(tt,1.0,0.55)
        L2=_txt_layer(s["subtitle"],font("b",s.get("sub_size",60)),C("gold"),stroke=5,sfill=C("navy"))
        blit(f,L2,W//2,720+len(lines)*150+40,lerp(.85,1,e_out(p2)),a2*A)

def layout_end(f,tt,dur,A,s):
    lines=s.get("title","").split("\n")
    for li,ln in enumerate(lines):
        p,a=appear(tt,0.2+li*0.16,0.5)
        L=_txt_layer(ln,font("b",s.get("title_size",104)),C("white"),stroke=6,sfill=C("navy"))
        blit(f,L,W//2,700+li*130,lerp(.75,1,e_back(p)),a*A)
    if s.get("subtitle"):
        p2,a2=appear(tt,1.0,0.55)
        L2=_txt_layer(s["subtitle"],font("b",56),C("gold"),stroke=5,sfill=C("navy"))
        blit(f,L2,W//2,700+len(lines)*130+50,lerp(.85,1,e_out(p2)),a2*A)

def layout_story(f,tt,dur,A,s):
    """短视频叙事层:少卡片,让真实画面和大字幕主导。"""
    accent=C(s.get("accent","gold"))
    if s.get("phase"):
        p,a=appear(tt,0.08,0.35)
        chip=pill(s["phase"],font("b",38),h=68,bg=C("navy")+(218,),tcol=C("white"),bar=accent)
        blit(f,chip,68+chip.size[0]//2,138,lerp(.88,1,e_out(p)),a*A)

    title=s.get("title","")
    if title:
        lines=title.split("\n")
        base_y=228 if len(lines)==1 else 202
        size=s.get("title_size",68 if len(lines)==1 else 62)
        for li,ln in enumerate(lines):
            p,a=appear(tt,0.22+li*0.08,0.42)
            L=_txt_layer(ln,font("b",size),C("white"),stroke=5,sfill=C("navy"))
            blit(f,L,W//2,base_y+li*(size+16),lerp(.88,1,e_back(p)),a*A)

    if s.get("kicker"):
        p,a=appear(tt,0.62,0.35)
        L=_txt_layer(s["kicker"],font("b",38),accent,stroke=4,sfill=C("navy"))
        blit(f,L,W//2,332,1.,a*A)

    if s.get("stamp"):
        p,a=appear(tt,0.55,0.35)
        st=pill(s["stamp"],font("b",38),h=66,bg=accent+(232,),tcol=C("navy"))
        blit(f,st,W-76-st.size[0]//2,BAND_BOT-56,lerp(.82,1,e_back(p)),a*A)

# ================= 主入口 =================
def render_overlay_frame(spec,tt,dur):
    f=base_frame(); A=seg_alpha(tt,dur)
    lay=spec.get("layout","beat")
    if lay=="title":
        layout_title(f,tt,dur,A,spec)
    elif lay=="end":
        layout_end(f,tt,dur,A,spec)
    elif lay=="story":
        layout_story(f,tt,dur,A,spec)
    else:  # beat / telestrator
        draw_header(f,tt,spec)
        if spec.get("points"): draw_points(f,tt,spec,y0=spec.get("points_y",1052))
        if lay=="telestrator": draw_marks(f,tt,spec)
    return apply_alpha(f,A)
