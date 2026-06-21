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
