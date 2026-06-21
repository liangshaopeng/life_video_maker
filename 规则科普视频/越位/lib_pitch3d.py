# -*- coding: utf-8 -*-
"""主看台视角·积木风足球动画引擎(横版 1920x1080)。
俯视场坐标 fx:0左门..1右门(进攻向右), fy:0远边线..1近边线(主看台侧)。
render_frame(spec, tt) 按关键帧插值出球员/球/越位线位置,逐帧返回全屏 RGBA。"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (24, 38, 28)

# ---- 主看台透视(梯形:远窄近宽) ----
Y_FAR, Y_NEAR = 150, 1006
HW_FAR, HW_NEAR = 770, 952
def project(fx, fy):
    fx = max(0.0, min(1.0, fx))
    y = Y_FAR + (Y_NEAR - Y_FAR) * fy
    hw = HW_FAR + (HW_NEAR - HW_FAR) * fy
    return W/2 + (fx - 0.5) * 2 * hw, y, hw / HW_NEAR
def _p(fx, fy):
    x, y, _ = project(fx, fy); return (x, y)

# ---- 关键帧线性插值 ----
def lerp(a, b, t): return a + (b - a) * t
def interp(keys, t):
    if t <= keys[0][0]: return list(keys[0][1:])
    if t >= keys[-1][0]: return list(keys[-1][1:])
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            span = b[0] - a[0]; r = 0.0 if span <= 1e-9 else (t - a[0]) / span
            return [lerp(a[1+i], b[1+i], r) for i in range(len(a) - 1)]
    return list(keys[-1][1:])

COLORS = {"red": (196,46,42), "blue": (46,108,200),
          "red_gk": (246,128,116), "blue_gk": (122,190,248)}   # 门将=本队亮色
_fc = {}
def F(sz):
    if sz in _fc: return _fc[sz]
    try: f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", sz)
    except: f = None
    _fc[sz] = f; return f
def _hi(c, f=1.25): return tuple(min(255, int(v*f)) for v in c[:3])
def _sh(c, f=0.72): return tuple(int(v*f) for v in c[:3])

def draw_grass(base):
    d = ImageDraw.Draw(base)
    d.polygon([_p(0,0), _p(1,0), _p(1,1), _p(0,1)], fill=(46,128,52))
    n = 12
    for i in range(n):
        fy0, fy1 = i/n, (i+1)/n
        c = (54,142,60) if i % 2 == 0 else (42,118,48)
        d.polygon([_p(0,fy0), _p(1,fy0), _p(1,fy1), _p(0,fy1)], fill=c)

def _dashed(d, a, b, col, dash, gap, w):
    x1,y1=a; x2,y2=b; tot=math.hypot(x2-x1,y2-y1) or 1; n=int(tot//(dash+gap))+1
    for k in range(n):
        t0=k*(dash+gap)/tot; t1=min(1,(k*(dash+gap)+dash)/tot)
        d.line([(x1+(x2-x1)*t0,y1+(y2-y1)*t0),(x1+(x2-x1)*t1,y1+(y2-y1)*t1)],fill=col,width=w)

def draw_offside(base, fx_line):
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(ov).polygon([_p(fx_line,0), _p(1,0), _p(1,1), _p(fx_line,1)], fill=(228,58,40,140))
    base.alpha_composite(ov)
    _dashed(ImageDraw.Draw(base), _p(fx_line,0), _p(fx_line,1), (95,165,250), 22, 13, 6)

def draw_lines(base):
    d = ImageDraw.Draw(base); w = (236,244,236)
    d.polygon([_p(0,0), _p(1,0), _p(1,1), _p(0,1)], outline=w, width=5)
    d.line([_p(0.5,0), _p(0.5,1)], fill=w, width=5)
    cx,cy,cs = project(0.5,0.5); rw=150*cs
    d.ellipse([cx-rw, cy-rw*0.42, cx+rw, cy+rw*0.42], outline=w, width=5)
    d.ellipse([cx-6*cs, cy-6*cs, cx+6*cs, cy+6*cs], fill=w)
    for fx0, fx1 in ((0.0,0.15),(0.85,1.0)):
        d.polygon([_p(fx0,0.26),_p(fx1,0.26),_p(fx1,0.74),_p(fx0,0.74)], outline=w, width=4)
        gx0,gx1=(0.0,0.06) if fx0==0 else (0.94,1.0)
        d.polygon([_p(gx0,0.38),_p(gx1,0.38),_p(gx1,0.62),_p(gx0,0.62)], outline=w, width=3)

def draw_goal(base, side):
    d = ImageDraw.Draw(base, "RGBA")
    fx = 1.0 if side == 'right' else 0.0; sgn = 1 if side == 'right' else -1
    xL,yL,s = project(fx, 0.438); xR,yR,_ = project(fx, 0.562)
    GH = 162*s; DX = sgn*74*s; DY = -30*s
    post=(250,251,253); net=(202,212,222,225)
    FLb=(xL,yL); FRb=(xR,yR); FLt=(xL,yL-GH); FRt=(xR,yR-GH)
    BLb=(xL+DX,yL+DY); BRb=(xR+DX,yR+DY); BLt=(xL+DX,yL+DY-GH); BRt=(xR+DX,yR+DY-GH)
    def mix(a,b,t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
    N=7
    for k in range(N+1):
        t=k/N; d.line([mix(FLt,FRt,t), mix(BLt,BRt,t)], fill=net, width=1)
    for k in range(N+1):
        t=k/N; d.line([mix(BLt,BRt,t), mix(BLb,BRb,t)], fill=net, width=1)
    for k in range(5):
        t=k/4; d.line([mix(BLt,BLb,t), mix(BRt,BRb,t)], fill=net, width=1)
    for k in range(5):
        t=k/4
        d.line([mix(FLt,FLb,t), mix(BLt,BLb,t)], fill=net, width=1)
        d.line([mix(FRt,FRb,t), mix(BRt,BRb,t)], fill=net, width=1)
    pw=int(max(2,5*s))
    for a,b in [(BLb,BLt),(BRb,BRt),(BLt,BRt)]:
        d.line([a,b], fill=(206,214,222), width=max(1,pw-2))
    for a,b in [(FLb,FLt),(FRb,FRt),(FLt,FRt)]:
        d.line([a,b], fill=post, width=pw)

def draw_ball(base, fx, fy):
    x,y,s = project(fx,fy); r=16*s; d = ImageDraw.Draw(base, "RGBA")
    d.ellipse([x-r*1.1,y+r*0.5,x+r*1.1,y+r*0.9], fill=(0,0,0,70))
    d.ellipse([x-r,y-r,x+r,y+r], fill=(255,255,255), outline=(20,20,20), width=max(1,int(r*0.14)))
    pts=[(x+r*0.4*math.cos(-math.pi/2+k*2*math.pi/5), y+r*0.4*math.sin(-math.pi/2+k*2*math.pi/5)) for k in range(5)]
    d.polygon(pts, fill=(22,22,22))
    for k in range(5):
        a=-math.pi/2+k*2*math.pi/5
        d.line([(x+r*0.4*math.cos(a),y+r*0.4*math.sin(a)),(x+r*0.96*math.cos(a),y+r*0.96*math.sin(a))],
               fill=(22,22,22), width=max(1,int(r*0.16)))

def draw_lego(base, fx, fy, shirt, pants=(34,34,42), skin=(247,206,60), num="", fnt=None):
    x, y, s = project(fx, fy); d = ImageDraw.Draw(base, "RGBA")
    d.ellipse([x-32*s, y-7*s, x+32*s, y+10*s], fill=(0,0,0,95))
    legW, legH = 48*s, 46*s; legTop=y-legH
    d.rectangle([x-legW/2, legTop, x-2*s, y], fill=pants)
    d.rectangle([x+2*s, legTop, x+legW/2, y], fill=pants)
    d.rectangle([x-legW/2, legTop, x-legW/2+5*s, y], fill=_hi(pants))
    hipH=13*s; d.rectangle([x-legW/2, legTop-hipH, x+legW/2, legTop], fill=_sh(pants,0.85))
    torsoH=52*s; tTop=legTop-hipH-torsoH; twT, twB = 40*s, 52*s
    d.polygon([(x-twT/2,tTop),(x+twT/2,tTop),(x+twB/2,legTop-hipH),(x-twB/2,legTop-hipH)], fill=shirt)
    d.polygon([(x-twT/2,tTop),(x-twT/2+6*s,tTop),(x-twB/2+6*s,legTop-hipH),(x-twB/2,legTop-hipH)], fill=_hi(shirt))
    armW=int(max(2,15*s))
    d.line([(x-twT/2+3*s,tTop+8*s),(x-twB/2-7*s,legTop-hipH)], fill=_sh(shirt,0.9), width=armW)
    d.line([(x+twT/2-3*s,tTop+8*s),(x+twB/2+7*s,legTop-hipH)], fill=_sh(shirt,0.9), width=armW)
    hr=8*s
    for hx in (x-twB/2-7*s, x+twB/2+7*s):
        d.ellipse([hx-hr, legTop-hipH-hr, hx+hr, legTop-hipH+hr], fill=skin)
    if num and fnt:
        d.text((x, tTop+torsoH*0.5), num, font=fnt, fill=(255,255,255,240), anchor="mm",
               stroke_width=max(1,int(s)), stroke_fill=_sh(shirt,0.55))
    hw, hh = 42*s, 40*s; hBot=tTop-1*s; hTop=hBot-hh
    try: d.rounded_rectangle([x-hw/2,hTop,x+hw/2,hBot], radius=int(10*s), fill=skin)
    except: d.rectangle([x-hw/2,hTop,x+hw/2,hBot], fill=skin)
    d.ellipse([x-hw/2, hTop, x-hw/2+6*s, hBot], fill=_hi(skin))
    sr=10*s; d.ellipse([x-sr, hTop-sr*1.3, x+sr, hTop+sr*0.5], fill=skin)
    d.ellipse([x-sr, hTop-sr*1.3, x+sr, hTop-sr*0.2], fill=_hi(skin))
    eyeY=hTop+hh*0.40; er=3.2*s
    for ex in (x-hw*0.20, x+hw*0.20):
        d.ellipse([ex-er, eyeY-er, ex+er, eyeY+er], fill=(40,26,18))
    d.arc([x-hw*0.26, eyeY+1*s, x+hw*0.26, eyeY+hh*0.34], 18, 162, fill=(40,26,18), width=max(1,int(2.4*s)))

def render_frame(spec, tt):
    """spec: {offside_line:{keys:[[t,fx]]}, players:[{team,num,keys:[[t,fx,fy]]}], ball:{keys:[[t,fx,fy]]}}"""
    img = Image.new("RGB", (W, H), BG).convert("RGBA")
    draw_grass(img)
    ol = spec.get("offside_line")
    if ol: draw_offside(img, interp(ol["keys"], tt)[0])
    draw_lines(img); draw_goal(img, 'left'); draw_goal(img, 'right')
    items = []
    for pl in spec.get("players", []):
        fx, fy = interp(pl["keys"], tt); items.append((fy, "P", fx, pl))
    b = spec.get("ball")
    if b:
        bfx, bfy = interp(b["keys"], tt); items.append((bfy, "B", bfx, None))
    for fy, kind, fx, pl in sorted(items, key=lambda z: z[0]):
        if kind == "P":
            pants = (30,30,40) if "gk" in pl["team"] else (34,34,42)
            draw_lego(img, fx, fy, COLORS[pl["team"]], pants=pants,
                      num=pl.get("num",""), fnt=F(int(26*project(fx,fy)[2])))
        else:
            draw_ball(img, fx, fy)
    return img
