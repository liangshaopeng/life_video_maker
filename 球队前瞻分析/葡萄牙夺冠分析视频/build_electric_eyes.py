# -*- coding: utf-8 -*-
"""
C罗特写"电眼"特效:在结尾近景(partB)最后约1.3秒,双眼充能爆发青蓝电光,
能量射线四射,峰值定格在最后一帧 —— "那个男人,眼里还有火"。
做法:直接把电光合成进 build/overlays/seg9/####.png(结尾叠加层),
随后 build_ending.py 会把这些叠加层烧进 clip9。
顺序约束:必须在 render_overlays 之后、build_ending 之前运行(否则被覆盖/不生效)。
"""
import os, json, math, random
from PIL import Image, ImageDraw, ImageFilter

ROOT  = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
FPS   = 30

TL = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))
seg = [s for s in TL["segs"] if s["id"] == "ending"][0]
SEG_I = seg["seg"]
CLIP  = seg["clip"]

# --- 与 build_ending.py 完全一致的 partB 参数 ---
B_IN, B_OUT, B_SPEED = 411.0, 413.25, 0.5
partB = (B_OUT - B_IN) / B_SPEED      # 4.5s
partA = CLIP - partB                  # 庆祝段

# --- 眼睛轨迹(源时间 s -> 屏左眼(Lx,Ly), 屏右眼(Rx,Ry)),由网格抽帧人工标定 ---
KF = [
    (411.00, (998, 338), (1278, 318)),
    (411.30, (1000, 350), (1280, 325)),
    (411.80, (1008, 405), (1285, 382)),
    (412.20, (1005, 400), (1290, 400)),
    (412.60, (1010, 420), (1298, 405)),
    (413.00, (1015, 440), (1305, 415)),
    (413.25, (1018, 448), (1308, 420)),
]

def eyes_at(s):
    if s <= KF[0][0]: return KF[0][1], KF[0][2]
    if s >= KF[-1][0]: return KF[-1][1], KF[-1][2]
    for (s0, L0, R0), (s1, L1, R1) in zip(KF, KF[1:]):
        if s0 <= s <= s1:
            t = (s - s0) / (s1 - s0)
            L = (L0[0] + (L1[0]-L0[0])*t, L0[1] + (L1[1]-L0[1])*t)
            R = (R0[0] + (R1[0]-R0[0])*t, R0[1] + (R1[1]-R0[1])*t)
            return L, R
    return KF[-1][1], KF[-1][2]

# --- 充能时间线(clip 时间)---
CHARGE_START = CLIP - 1.30
PEAK_AT      = CLIP - 0.55
CYAN = (128, 224, 255)
HOT  = (236, 250, 255)

def e_out(t): t=max(0.,min(1.,t)); return 1-(1-t)**3

def intensity(tau, fi):
    if tau < CHARGE_START: return 0.0
    if tau < PEAK_AT:
        base = e_out((tau - CHARGE_START) / (PEAK_AT - CHARGE_START))
    else:
        base = 1.0
    # 峰值后保持 + 电流闪烁
    random.seed(fi * 977 + 13)
    flick = 1.0 - 0.14 * random.random() if base > 0.55 else 1.0
    return max(0.0, min(1.0, base * flick))

def glow_layer(L, R, inten, fi):
    """整帧透明层:双眼青蓝辉光 + 白热核心 + 抖动电弧 + 边缘能量涌动。"""
    layer = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))

    # 边缘能量涌动(峰值时屏幕四周泛青光)
    if inten > 0.45:
        edge = Image.new("L", (1920//4, 1080//4), 0)
        ed = ImageDraw.Draw(edge)
        ed.rectangle([0, 0, 1920//4-1, 1080//4-1], outline=255, width=22)
        edge = edge.filter(ImageFilter.GaussianBlur(26)).resize((1920, 1080))
        ev = Image.new("RGBA", (1920, 1080), CYAN + (0,))
        ev.putalpha(edge.point(lambda v: int(v * 0.42 * inten)))
        layer.alpha_composite(ev)

    for (cx, cy) in (L, R):
        cx, cy = int(cx), int(cy)
        # 大软光晕
        halo = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.ellipse([cx-66, cy-50, cx+66, cy+50], fill=CYAN + (210,))
        halo = halo.filter(ImageFilter.GaussianBlur(30))
        halo.putalpha(halo.split()[3].point(lambda v: int(v * inten)))
        layer.alpha_composite(halo)

        # 抖动电弧(向外四散)
        bolts = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bolts)
        random.seed(fi * 131 + cx)
        nb = 5
        for b in range(nb):
            if random.random() < 0.28:  # 闪烁:部分电弧本帧不出现
                continue
            ang = (b / nb) * 2 * math.pi + random.uniform(-0.35, 0.35)
            length = random.uniform(70, 150) * (0.6 + 0.4*inten)
            x, y = cx, cy
            pts = [(x, y)]
            steps = 5
            for k in range(1, steps + 1):
                seg_len = length / steps
                ang += random.uniform(-0.5, 0.5)
                x += math.cos(ang) * seg_len
                y += math.sin(ang) * seg_len
                pts.append((x, y))
            bd.line(pts, fill=CYAN + (230,), width=6, joint="curve")
        bolts = bolts.filter(ImageFilter.GaussianBlur(3))
        bd2 = ImageDraw.Draw(bolts)
        random.seed(fi * 131 + cx)  # 同样的种子重画白色芯线
        for b in range(nb):
            if random.random() < 0.28: continue
            ang = (b / nb) * 2 * math.pi + random.uniform(-0.35, 0.35)
            length = random.uniform(70, 150) * (0.6 + 0.4*inten)
            x, y = cx, cy; pts = [(x, y)]
            for k in range(1, 6):
                ang += random.uniform(-0.5, 0.5)
                x += math.cos(ang) * (length/5); y += math.sin(ang) * (length/5)
                pts.append((x, y))
            bd2.line(pts, fill=HOT + (255,), width=2, joint="curve")
        bolts.putalpha(bolts.split()[3].point(lambda v: int(v * inten)))
        layer.alpha_composite(bolts)

        # 白热核心
        core = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        cd = ImageDraw.Draw(core)
        cd.ellipse([cx-22, cy-16, cx+22, cy+16], fill=HOT + (255,))
        core = core.filter(ImageFilter.GaussianBlur(7))
        core.putalpha(core.split()[3].point(lambda v: int(v * inten)))
        layer.alpha_composite(core)

    return layer

def main():
    od = os.path.join(BUILD, "overlays", f"seg{SEG_I}")
    n = round(CLIP * FPS)
    touched = 0
    for fi in range(n):
        tau = fi / FPS
        inten = intensity(tau, fi)
        if inten <= 0.001:
            continue
        s = B_IN + (tau - partA) * B_SPEED   # partB 源时间
        L, R = eyes_at(s)
        p = os.path.join(od, f"{fi:04d}.png")
        if not os.path.exists(p): continue
        base = Image.open(p).convert("RGBA")
        base.alpha_composite(glow_layer(L, R, inten, fi))
        base.save(p)
        touched += 1
    print(f"⚡ 电眼已合成进 seg{SEG_I} 叠加层:{touched} 帧 (充能 {CHARGE_START:.2f}s→{CLIP:.2f}s)")

if __name__ == "__main__":
    main()
