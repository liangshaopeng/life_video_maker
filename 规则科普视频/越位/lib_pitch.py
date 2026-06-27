# -*- coding: utf-8 -*-
"""战术板俯视图动画库:竖向足球场 + 球员(关键帧插值)+ 越位线 + 球。
复用 lib_overlays_v 的画布常量/配色/字体/缓动。输出全屏 1080x1920 背景帧。"""
import math
from PIL import Image, ImageDraw
from lib_overlays_v import W, H, FPS, C, font, lerp

# 球场绘制区(竖向)
X0, Y0, FW, FH = 90, 320, 900, 1280

def to_px(nx, ny):
    """归一化(0..1)坐标 -> 画布像素。ny=0 顶部(对方门),ny=1 底部。"""
    return (X0 + nx * FW, Y0 + ny * FH)

def interp(keys, t):
    """keys=[[t, v...], ...] 按 t 升序;返回 t 处各分量的分段线性插值(list)。
    t 在范围外则钳到首/末 key。"""
    if t <= keys[0][0]:
        return list(keys[0][1:])
    if t >= keys[-1][0]:
        return list(keys[-1][1:])
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            span = b[0] - a[0]
            r = 0.0 if span <= 1e-9 else (t - a[0]) / span
            return [lerp(a[1 + i], b[1 + i], r) for i in range(len(a) - 1)]
    return list(keys[-1][1:])

def _line(d, p1, p2, col, w=4):
    d.line([p1, p2], fill=col, width=w)

def draw_pitch(img):
    """在 img(RGBA 1080x1920)上画暗色极简竖向球场:边界/中线/中圈/上下禁区/球门。"""
    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 150)
    L, T, R, B = X0, Y0, X0 + FW, Y0 + FH
    # 边界
    d.rectangle([L, T, R, B], outline=white, width=4)
    # 中线 + 中圈
    midy = (T + B) // 2
    _line(d, (L, midy), (R, midy), white, 4)
    cr = 130
    d.ellipse([ (L+R)//2 - cr, midy - cr, (L+R)//2 + cr, midy + cr ], outline=white, width=4)
    d.ellipse([ (L+R)//2 - 8, midy - 8, (L+R)//2 + 8, midy + 8 ], fill=white)
    # 上下禁区 + 球门(顶=对方,底=本方)
    paw, pah = 460, 200          # 禁区宽/高
    gw, gh = 200, 40             # 球门宽/高
    cx = (L + R) // 2
    for yy, sgn in ((T, 1), (B, -1)):
        d.rectangle([cx - paw//2, min(yy, yy + sgn*pah), cx + paw//2, max(yy, yy + sgn*pah)], outline=white, width=4)
        d.rectangle([cx - gw//2, min(yy, yy+sgn*gh), cx + gw//2, max(yy, yy+sgn*gh)],
                    outline=(255,255,255,200), width=5)
    return img

def new_frame():
    """全屏 navy 底帧(RGBA)。"""
    return Image.new("RGBA", (W, H), tuple(C("navy")) + (255,))

def draw_player(img, nx, ny, team="red", label=""):
    """在归一化坐标处画一名球员:实心圆点+白描边,可选标签。team: red(进攻)/blue(防守)。"""
    d = ImageDraw.Draw(img)
    px, py = to_px(nx, ny)
    r = 26
    col = tuple(C("warn")) if team == "red" else tuple(C("sky"))
    d.ellipse([px-r, py-r, px+r, py+r], fill=col + (255,), outline=(255,255,255,255), width=4)
    if label:
        fnt = font("b", 30)
        d.text((px, py), label, font=fnt, fill=(255,255,255,255), anchor="mm")
    return img

def draw_offside_line(img, ny, col=None, dash=34, gap=22, w=7):
    """横跨球场的虚线越位线(gold)。ny: 归一化纵向位置。"""
    d = ImageDraw.Draw(img)
    col = col or (tuple(C("gold")) + (255,))
    y = Y0 + ny * FH
    x = X0
    while x < X0 + FW:
        d.line([(x, y), (min(x + dash, X0 + FW), y)], fill=col, width=w)
        x += dash + gap
    return img

def draw_offside_zone(img, ny, label="越位区"):
    """把越位线身后的投机空间染红:ny 以上是提前蹲门口的区域。"""
    y = Y0 + ny * FH
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([X0, Y0, X0 + FW, y], fill=tuple(C("warn")) + (54,))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    d.text((X0 + FW - 24, Y0 + 44), label, font=font("b", 34),
           fill=tuple(C("warn")) + (235,), anchor="ra",
           stroke_width=3, stroke_fill=tuple(C("navy")) + (220,))
    return img

def draw_battle_zone(img, ny0, ny1, label="对抗博弈区"):
    """高亮越位线附近的窄带,强调进攻和防守被压到同一条线附近。"""
    top = Y0 + min(ny0, ny1) * FH
    bot = Y0 + max(ny0, ny1) * FH
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([X0, top, X0 + FW, bot], fill=tuple(C("gold")) + (64,))
    img.alpha_composite(ov)
    draw_offside_line(img, min(ny0, ny1), col=tuple(C("gold")) + (235,), dash=26, gap=16, w=5)
    draw_offside_line(img, max(ny0, ny1), col=tuple(C("gold")) + (235,), dash=26, gap=16, w=5)
    ImageDraw.Draw(img).text((W // 2, top - 34), label, font=font("b", 36),
                             fill=tuple(C("gold")) + (255,), anchor="mm",
                             stroke_width=3, stroke_fill=tuple(C("navy")) + (230,))
    return img

def draw_ball(img, nx, ny):
    d = ImageDraw.Draw(img)
    px, py = to_px(nx, ny)
    r = 12
    d.ellipse([px-r, py-r, px+r, py+r], fill=(255,255,255,255), outline=(20,20,20,255), width=2)
    return img

def draw_arrow(img, p_from, p_to, col=None, w=8, dashed=True):
    """归一化两点间画箭头(直线+箭头头)。零长箭头(起=止)直接跳过。"""
    d = ImageDraw.Draw(img)
    col = col or (tuple(C("gold")) + (255,))
    x1, y1 = to_px(*p_from); x2, y2 = to_px(*p_to)
    tot = math.hypot(x2 - x1, y2 - y1)
    if tot < 1e-9:
        return img
    if dashed:
        seg, g = 26, 16; n = max(1, int(tot // (seg + g)))
        for k in range(n):
            start = k * (seg + g)
            a, b = start / tot, min(1.0, (start + seg) / tot)
            d.line([(lerp(x1,x2,a),lerp(y1,y2,a)),(lerp(x1,x2,b),lerp(y1,y2,b))], fill=col, width=w)
    else:
        d.line([(x1,y1),(x2,y2)], fill=col, width=w)
    ang = math.atan2(y2-y1, x2-x1); hl = 28
    for s in (2.6, -2.6):
        d.line([(x2,y2),(x2-hl*math.cos(ang+s), y2-hl*math.sin(ang+s))], fill=col, width=w)
    return img

def render_pitch_frame(spec, tt):
    """spec: 段的 'pitch' 规格;tt: 段内秒。返回全屏 RGBA 帧。
    画序:底帧 -> 场 -> 越位线 -> 箭头 -> 球员 -> 球 -> 场景标签。"""
    f = new_frame()
    draw_pitch(f)
    ol = spec.get("offside_line")
    oz = spec.get("offside_zone")
    if oz:
        draw_offside_zone(f, interp(oz["keys"], tt)[0], oz.get("label", "越位区"))
    bz = spec.get("battle_zone")
    if bz:
        k = interp(bz["keys"], tt)
        draw_battle_zone(f, k[0], k[1], bz.get("label", "对抗博弈区"))
    if ol:
        draw_offside_line(f, interp(ol["keys"], tt)[0])
    for ar in spec.get("arrows", []):
        if ar.get("t", 0) <= tt <= ar.get("t", 0) + ar.get("dur", 9):
            draw_arrow(f, ar["from"], ar["to"],
                       col=(tuple(C(ar.get("color","gold")))+(255,)),
                       dashed=ar.get("style","dashed")=="dashed")
    for pl in spec.get("players", []):
        nx, ny = interp(pl["keys"], tt)
        draw_player(f, nx, ny, pl.get("team","red"), pl.get("label",""))
    b = spec.get("ball")
    if b:
        bx, by = interp(b["keys"], tt); draw_ball(f, bx, by)
    lab = spec.get("scene_label")
    if lab:
        ImageDraw.Draw(f).text((W//2, Y0-70), lab, font=font("b", 56),
                               fill=tuple(C("gold"))+(255,), anchor="mm")
    return f
