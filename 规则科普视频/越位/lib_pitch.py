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
