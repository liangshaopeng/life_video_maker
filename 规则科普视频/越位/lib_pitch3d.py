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
          "lebron": (85,37,130),
          "red_gk": (246,128,116), "blue_gk": (122,190,248)}   # 门将=本队亮色
AVATARS = {
    "messi": {"hair": (72, 45, 26), "beard": (92, 55, 31), "skin": (235, 184, 126), "style": "beard"},
    "mbappe": {"hair": (26, 22, 18), "skin": (120, 78, 54), "style": "close"},
    "haaland": {"hair": (238, 205, 102), "skin": (244, 199, 138), "style": "long"},
    "bellingham": {"hair": (28, 22, 18), "skin": (111, 72, 52), "style": "fade"},
    "kdb": {"hair": (224, 126, 48), "beard": (190, 92, 42), "skin": (242, 188, 130), "style": "beard"},
    "vvd": {"hair": (34, 25, 18), "skin": (132, 84, 58), "style": "bun"},
    "rodri": {"hair": (40, 28, 22), "skin": (226, 168, 114), "style": "short"},
    "walker": {"hair": (22, 18, 15), "skin": (116, 74, 52), "style": "close"},
    "alisson": {"hair": (76, 42, 24), "beard": (92, 50, 28), "skin": (230, 174, 118), "style": "beard"},
    "lebron": {"hair": (24, 19, 16), "beard": (38, 26, 20), "skin": (104, 64, 42), "style": "headband"},
}
_fc = {}
def F(sz):
    if sz in _fc: return _fc[sz]
    try: f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", sz)
    except: f = None
    _fc[sz] = f; return f
_fcn = {}
def fcn(sz):
    if sz not in _fcn:
        _fcn[sz] = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", sz, index=2)
    return _fcn[sz]
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

def draw_battle_zone(base, fx_lo, fx_hi, label="对抗 · 博弈区"):
    """越位线附近的对抗带(金色高亮+边界虚线+标注)——强调'对抗全压在这条窄带上'。"""
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(ov).polygon([_p(fx_lo,0),_p(fx_hi,0),_p(fx_hi,1),_p(fx_lo,1)], fill=(252,209,50,70))
    base.alpha_composite(ov)
    d = ImageDraw.Draw(base, "RGBA")
    _dashed(d, _p(fx_lo,0), _p(fx_lo,1), (252,216,80,255), 18, 10, 5)
    _dashed(d, _p(fx_hi,0), _p(fx_hi,1), (252,216,80,255), 18, 10, 5)
    if label:
        cx = (_p(fx_lo,0)[0] + _p(fx_hi,0)[0]) / 2
        d.text((cx, Y_FAR + 34), label, font=fcn(40), fill=(255,233,120,255),
               anchor="mm", stroke_width=3, stroke_fill=(0,0,0,205))

def draw_space_zone(base, fx0, fy0, fx1, fy1, label="", color=(252,209,50)):
    """画一个随透视变形的空间口袋,用于突出身后、肋部、传球窗口等博弈空间。"""
    x0, x1 = min(fx0, fx1), max(fx0, fx1)
    y0, y1 = min(fy0, fy1), max(fy0, fy1)
    pts = [_p(x0, y0), _p(x1, y0), _p(x1, y1), _p(x0, y1)]
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(ov, "RGBA")
    od.polygon(pts, fill=color + (78,))
    base.alpha_composite(ov)
    d = ImageDraw.Draw(base, "RGBA")
    for a, b in zip(pts, pts[1:] + pts[:1]):
        _dashed(d, a, b, color + (240,), 18, 10, 4)
    if label:
        cx = sum(p[0] for p in pts) / 4
        cy = sum(p[1] for p in pts) / 4
        d.text((cx, cy), label, font=fcn(34), fill=color + (255,),
               anchor="mm", stroke_width=3, stroke_fill=(0,0,0,210))

def draw_arrow(base, start, end, color=(252,209,50), width=8, dashed=True, label=""):
    x1, y1 = _p(*start); x2, y2 = _p(*end)
    d = ImageDraw.Draw(base, "RGBA")
    if dashed:
        _dashed(d, (x1,y1), (x2,y2), color + (255,), 24, 14, width)
    else:
        d.line([(x1,y1),(x2,y2)], fill=color + (255,), width=width)
    ang = math.atan2(y2-y1, x2-x1)
    head = 28
    pts = [(x2,y2),
           (x2-head*math.cos(ang+2.55), y2-head*math.sin(ang+2.55)),
           (x2-head*math.cos(ang-2.55), y2-head*math.sin(ang-2.55))]
    d.polygon(pts, fill=color + (255,))
    if label:
        d.text(((x1+x2)/2, (y1+y2)/2-28), label, font=fcn(30), fill=color + (255,),
               anchor="mm", stroke_width=3, stroke_fill=(0,0,0,210))

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

def draw_lego(base, fx, fy, shirt, pants=(34,34,42), skin=(247,206,60), num="", fnt=None, avatar=None, name="", scale=1.0):
    x, y, s0 = project(fx, fy); s = s0 * scale; d = ImageDraw.Draw(base, "RGBA")
    av = AVATARS.get(avatar or "", {})
    skin = av.get("skin", skin)
    hair = av.get("hair", (68, 45, 24))
    beard = av.get("beard")
    style = av.get("style", "short")
    d.ellipse([x-32*s, y-7*s, x+32*s, y+10*s], fill=(0,0,0,95))
    legW, legH = 48*s, 46*s; legTop=y-legH
    d.rectangle([x-legW/2, legTop, x-2*s, y], fill=pants)
    d.rectangle([x+2*s, legTop, x+legW/2, y], fill=pants)
    d.rectangle([x-legW/2, legTop, x-legW/2+5*s, y], fill=_hi(pants))
    hipH=13*s; d.rectangle([x-legW/2, legTop-hipH, x+legW/2, legTop], fill=_sh(pants,0.85))
    torsoH=52*s; tTop=legTop-hipH-torsoH; twT, twB = 40*s, 52*s
    d.polygon([(x-twT/2,tTop),(x+twT/2,tTop),(x+twB/2,legTop-hipH),(x-twB/2,legTop-hipH)], fill=shirt)
    d.polygon([(x-twT/2,tTop),(x-twT/2+6*s,tTop),(x-twB/2+6*s,legTop-hipH),(x-twB/2,legTop-hipH)], fill=_hi(shirt))
    if avatar == "lebron":
        gold = (253,185,39)
        d.line([(x-twT/2+9*s,tTop+5*s),(x-twB/2+12*s,legTop-hipH-3*s)], fill=gold, width=max(2,int(4*s)))
        d.line([(x+twT/2-9*s,tTop+5*s),(x+twB/2-12*s,legTop-hipH-3*s)], fill=gold, width=max(2,int(4*s)))
        d.line([(x-twT/2+5*s,tTop+7*s),(x+twT/2-5*s,tTop+7*s)], fill=gold, width=max(2,int(4*s)))
    armW=int(max(2,15*s))
    d.line([(x-twT/2+3*s,tTop+8*s),(x-twB/2-7*s,legTop-hipH)], fill=_sh(shirt,0.9), width=armW)
    d.line([(x+twT/2-3*s,tTop+8*s),(x+twB/2+7*s,legTop-hipH)], fill=_sh(shirt,0.9), width=armW)
    hr=8*s
    for hx in (x-twB/2-7*s, x+twB/2+7*s):
        d.ellipse([hx-hr, legTop-hipH-hr, hx+hr, legTop-hipH+hr], fill=skin)
    if num and fnt:
        num_fill = (253,185,39,255) if avatar == "lebron" else (255,255,255,240)
        d.text((x, tTop+torsoH*0.5), num, font=fnt, fill=num_fill, anchor="mm",
               stroke_width=max(1,int(s)), stroke_fill=_sh(shirt,0.45))
    hw, hh = 42*s, 40*s; hBot=tTop-1*s; hTop=hBot-hh
    try: d.rounded_rectangle([x-hw/2,hTop,x+hw/2,hBot], radius=int(10*s), fill=skin)
    except: d.rectangle([x-hw/2,hTop,x+hw/2,hBot], fill=skin)
    d.ellipse([x-hw/2, hTop, x-hw/2+6*s, hBot], fill=_hi(skin))
    if style in ("close", "fade"):
        d.rounded_rectangle([x-hw/2+2*s, hTop-3*s, x+hw/2-2*s, hTop+11*s],
                            radius=int(7*s), fill=hair)
    elif style == "headband":
        d.rounded_rectangle([x-hw/2+1*s, hTop-4*s, x+hw/2-1*s, hTop+12*s],
                            radius=int(7*s), fill=hair)
        d.rectangle([x-hw/2+1*s, hTop+4*s, x+hw/2-1*s, hTop+12*s], fill=(245,245,245,250))
        d.rectangle([x-hw/2+1*s, hTop+11*s, x+hw/2-1*s, hTop+15*s], fill=hair)
    elif style == "long":
        d.rounded_rectangle([x-hw/2-4*s, hTop-8*s, x+hw/2+4*s, hTop+18*s],
                            radius=int(12*s), fill=hair)
        d.rectangle([x-hw*0.32, hTop+10*s, x+hw*0.32, hTop+23*s], fill=hair)
    elif style == "bun":
        d.rounded_rectangle([x-hw/2-3*s, hTop-5*s, x+hw/2+3*s, hTop+15*s],
                            radius=int(10*s), fill=hair)
        d.ellipse([x-10*s, hTop-19*s, x+10*s, hTop+1*s], fill=hair)
    else:
        d.pieslice([x-hw/2, hTop-10*s, x+hw/2, hTop+23*s], 180, 360, fill=hair)
    sr=10*s
    d.ellipse([x-sr, hTop-sr*1.3, x+sr, hTop+sr*0.15], fill=_hi(skin))
    eyeY=hTop+hh*0.40; er=3.2*s
    for ex in (x-hw*0.20, x+hw*0.20):
        d.ellipse([ex-er, eyeY-er, ex+er, eyeY+er], fill=(40,26,18))
    if beard:
        if avatar == "lebron":
            d.rounded_rectangle([x-hw*0.34, eyeY+2*s, x+hw*0.34, hBot+8*s],
                                radius=int(10*s), fill=beard)
            d.rectangle([x-hw*0.16, eyeY-1*s, x+hw*0.16, eyeY+11*s], fill=skin)
        else:
            d.pieslice([x-hw*0.34, eyeY+2*s, x+hw*0.34, hBot+5*s], 0, 180, fill=beard)
            d.arc([x-hw*0.18, eyeY+6*s, x+hw*0.18, hBot-3*s], 18, 162, fill=(245,222,185), width=max(1,int(2*s)))
    d.arc([x-hw*0.26, eyeY+1*s, x+hw*0.26, eyeY+hh*0.34], 18, 162, fill=(40,26,18), width=max(1,int(2.4*s)))
    if name:
        d.text((x, y + 30*s), name, font=fcn(max(12, int(20*s))), fill=(255,255,255,230),
               anchor="mm", stroke_width=max(1,int(2*s)), stroke_fill=(0,0,0,190))

def draw_callout(base, spec, tt):
    t0 = spec.get("t", 0)
    if tt < t0 or tt > t0 + spec.get("dur", 99):
        return
    avatar = spec.get("avatar", "lebron")
    x, y = spec.get("pos", [1510, 250])
    title = spec.get("title", "紫金23号")
    sub = spec.get("subtitle", "提前占空间")
    w, h = spec.get("size", [330, 156])
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle([x, y, x+w, y+h], radius=22, fill=(20,18,35,205), outline=(253,185,39,245), width=4)
    # 大号半身头像:白发带、浓胡子、紫金23号,让梗在缩略图里也能读出来。
    cx, cy = x + 74, y + 78
    skin = AVATARS[avatar]["skin"]; hair = AVATARS[avatar]["hair"]; beard = AVATARS[avatar]["beard"]
    d.ellipse([cx-54, cy+48, cx+54, cy+70], fill=(0,0,0,80))
    d.polygon([(cx-42,cy+8),(cx+42,cy+8),(cx+54,cy+80),(cx-54,cy+80)], fill=COLORS["lebron"])
    d.line([(cx-36,cy+18),(cx+36,cy+18)], fill=(253,185,39,255), width=6)
    d.text((cx, cy+48), "23", font=F(38), fill=(253,185,39,255), anchor="mm",
           stroke_width=2, stroke_fill=(38,18,70,255))
    d.rounded_rectangle([cx-34,cy-50,cx+34,cy+8], radius=14, fill=skin)
    d.rounded_rectangle([cx-36,cy-56,cx+36,cy-34], radius=10, fill=hair)
    d.rectangle([cx-36,cy-38,cx+36,cy-27], fill=(248,248,248,255))
    d.rectangle([cx-36,cy-27,cx+36,cy-20], fill=hair)
    for ex in (cx-14, cx+14):
        d.ellipse([ex-4,cy-16,ex+4,cy-8], fill=(28,20,16,255))
    d.rounded_rectangle([cx-25,cy-5,cx+25,cy+22], radius=12, fill=beard)
    d.rectangle([cx-10,cy-8,cx+10,cy+8], fill=skin)
    d.arc([cx-14,cy+4,cx+14,cy+20], 18, 162, fill=(245,222,185,255), width=3)
    d.text((x+160, y+50), title, font=fcn(36), fill=(253,185,39,255),
           anchor="lm", stroke_width=3, stroke_fill=(0,0,0,230))
    d.text((x+160, y+104), sub, font=fcn(28), fill=(255,255,255,242),
           anchor="lm", stroke_width=2, stroke_fill=(0,0,0,220))

def render_frame(spec, tt):
    """spec: {offside_line:{keys:[[t,fx]]}, players:[{team,num,keys:[[t,fx,fy]]}], ball:{keys:[[t,fx,fy]]}}"""
    img = Image.new("RGB", (W, H), BG).convert("RGBA")
    draw_grass(img)
    ol = spec.get("offside_line")
    if ol: draw_offside(img, interp(ol["keys"], tt)[0])
    bz = spec.get("battle_zone")
    if bz:
        k = interp(bz["keys"], tt); draw_battle_zone(img, k[0], k[1], bz.get("label", "对抗 · 博弈区"))
    for z in spec.get("spaces", []):
        k = interp(z["keys"], tt)
        col = tuple(z.get("color", (252,209,50)))
        draw_space_zone(img, k[0], k[1], k[2], k[3], z.get("label", ""), col)
    for ar in spec.get("arrows", []):
        t0 = ar.get("t", 0)
        if t0 <= tt <= t0 + ar.get("dur", 99):
            draw_arrow(img, ar["from"], ar["to"], tuple(ar.get("color", (252,209,50))),
                       ar.get("width", 8), ar.get("style", "dashed") == "dashed", ar.get("label", ""))
    draw_lines(img); draw_goal(img, 'left'); draw_goal(img, 'right')
    items = []
    for pl in spec.get("players", []):
        fx, fy = interp(pl["keys"], tt); items.append((fy, "P", fx, pl))
    b = spec.get("ball")
    if b:
        bfx, bfy = interp(b["keys"], tt); items.append((bfy, "B", bfx, None))
    for fy, kind, fx, pl in sorted(items, key=lambda z: z[0]):
        if kind == "P":
            if pl.get("avatar") == "lebron":
                pants = tuple(pl.get("pants", [253,185,39]))
            else:
                pants = tuple(pl.get("pants", (30,30,40) if "gk" in pl["team"] else (34,34,42)))
            shirt = tuple(pl.get("shirt", COLORS[pl["team"]]))
            draw_lego(img, fx, fy, shirt, pants=pants,
                      num=pl.get("num",""), fnt=F(int(26*project(fx,fy)[2]*pl.get("scale",1.0))),
                      avatar=pl.get("avatar"), name=pl.get("name",""), scale=pl.get("scale",1.0))
        else:
            draw_ball(img, fx, fy)
    for co in spec.get("callouts", []):
        draw_callout(img, co, tt)
    return img
