# -*- coding: utf-8 -*-
"""
渲染《阿根廷2026·最后一舞》6个分镜的逐帧画面 (1920x1080 @30fps)。
天蓝白现代体育风。只依赖 Pillow。帧写入 build/frames/segN/####.jpg
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

# ---------------- 基本配置 ----------------
W, H = 1920, 1080
FPS = 30
ROOT = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(ROOT, "build", "frames")

# 各段配音真实时长(afinfo 实测)+ 尾部留白
SEG_AUDIO = [8.201859, 9.194014, 7.363084, 15.132063, 14.131202, 5.079546]
PAD = 0.30
CLIP_DUR = [d + PAD for d in SEG_AUDIO]

# ---------------- 配色 ----------------
SKY_TOP    = (74, 134, 196)    # 深天蓝
SKY_BOT    = (170, 208, 238)   # 浅天蓝
NAVY_TOP   = (12, 28, 64)      # 深藏蓝
NAVY_BOT   = (5, 14, 34)
WHITE      = (255, 255, 255)
NAVY_INK   = (10, 26, 63)
GOLD       = (250, 204, 21)    # 五月太阳金
SKY_NEON   = (120, 190, 245)
RED_WARN   = (235, 96, 90)

# ---------------- 字体 ----------------
F_CN   = "/System/Library/Fonts/Hiragino Sans GB.ttc"
F_NUM  = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
_font_cache = {}
def font(kind, size):
    key = (kind, size)
    if key in _font_cache:
        return _font_cache[key]
    if kind == "cn_bold":
        f = ImageFont.truetype(F_CN, size, index=2)   # W6
    elif kind == "cn_reg":
        f = ImageFont.truetype(F_CN, size, index=0)   # W3
    else:  # num
        f = ImageFont.truetype(F_NUM, size, index=0)
    _font_cache[key] = f
    return f

# ---------------- 缓动 ----------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_in_out(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)

def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3

def lerp(a, b, t):
    return a + (b - a) * t

# 元素在 [start, start+dur] 区间内出现:返回 (进度0..1, alpha0..1)
def appear(tt, start, dur):
    if tt < start:
        return 0.0, 0.0
    p = clamp((tt - start) / dur)
    return p, p

# ---------------- 背景 ----------------
def vgrad(top, bot, w, h):
    """竖直渐变(快速:1xH 再拉伸)"""
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        t = y / (h - 1)
        px[0, y] = (
            int(lerp(top[0], bot[0], t)),
            int(lerp(top[1], bot[1], t)),
            int(lerp(top[2], bot[2], t)),
        )
    return col.resize((w, h))

def draw_sun(img, cx, cy, r, color, n=16, alpha=70):
    """简化五月太阳:中心圆 + 三角光芒"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(n):
        a0 = (i / n) * 2 * math.pi
        a1 = a0 + (2 * math.pi / n) * 0.45
        r2 = r * 2.0
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p1 = (cx + r2 * math.cos((a0 + a1) / 2), cy + r2 * math.sin((a0 + a1) / 2))
        p2 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        d.polygon([p0, p1, p2], fill=color + (alpha,))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha + 30,))
    img.alpha_composite(layer)

def diagonal_stripes(img, color, alpha, count=2):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw = 150
    for k in range(count):
        off = -400 + k * 520
        d.polygon([(off, H), (off + bw, H), (off + bw + 700, 0), (off + 700, 0)],
                  fill=color + (alpha,))
    img.alpha_composite(layer)

def make_bg(kind):
    """返回 1.2 倍超采样背景(供 Ken Burns 裁切推拉)"""
    BW, BH = int(W * 1.2), int(H * 1.2)
    if kind == "bright":
        base = vgrad(SKY_TOP, SKY_BOT, BW, BH).convert("RGBA")
        diagonal_stripes(base, WHITE, 28, count=3)
        draw_sun(base, int(BW * 0.84), int(BH * 0.20), 80, GOLD, n=18, alpha=55)
    else:  # dark
        base = vgrad(NAVY_TOP, NAVY_BOT, BW, BH).convert("RGBA")
        diagonal_stripes(base, SKY_NEON, 16, count=3)
    # 暗角
    vig = Image.new("L", (BW, BH), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-BW * 0.25, -BH * 0.25, BW * 1.25, BH * 1.25], fill=90)
    vig = vig.point(lambda v: 255 - v)
    dark = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    dark.putalpha(vig.point(lambda v: int(v * 0.45)))
    base.alpha_composite(dark)
    return base

BG_BRIGHT = make_bg("bright")
BG_DARK   = make_bg("dark")

def kenburns(bg, p):
    """p:0..1 段内进度,缓慢推近 + 轻微平移"""
    BW, BH = bg.size
    k = lerp(1.16, 1.05, ease_in_out(p))   # 裁切窗变小=推近
    cw, ch = W * k, H * k
    cx = BW / 2 + lerp(-12, 12, p)
    cy = BH / 2 + lerp(8, -8, p)
    left, top = cx - cw / 2, cy - ch / 2
    crop = bg.crop((round(left), round(top), round(left + cw), round(top + ch)))
    return crop.resize((W, H)).convert("RGBA")

# ---------------- 文本 ----------------
def text_center(draw, xy, s, fnt, fill, stroke=0, stroke_fill=(0,0,0), anchor="mm"):
    draw.text(xy, s, font=fnt, fill=fill, anchor=anchor,
              stroke_width=stroke, stroke_fill=stroke_fill)

def text_layer(s, fnt, fill, stroke=0, stroke_fill=(0,0,0)):
    """独立 RGBA 层上居中绘制一段文字,返回 (层, w, h),便于缩放弹入"""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), s, font=fnt, stroke_width=stroke)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    pad = stroke + 6
    layer = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    dl.text((pad - bb[0], pad - bb[1]), s, font=fnt, fill=fill,
            stroke_width=stroke, stroke_fill=stroke_fill)
    return layer, layer.size[0], layer.size[1]

def blit_scaled(base, layer, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.001 or scale <= 0.001:
        return
    lw, lh = layer.size
    nw, nh = max(1, int(lw * scale)), max(1, int(lh * scale))
    lr = layer.resize((nw, nh))
    if alpha < 0.999:
        a = lr.split()[3].point(lambda v: int(v * alpha))
        lr.putalpha(a)
    base.alpha_composite(lr, (int(cx - nw / 2), int(cy - nh / 2)))

# ---------------- 卡片 ----------------
def make_card(big, small, accent=SKY_TOP, w=440, h=300):
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w-1, h-1], radius=28, fill=(255, 255, 255, 240))
    d.rounded_rectangle([0, 0, w-1, h-1], radius=28, outline=accent + (255,), width=4)
    d.rounded_rectangle([24, 24, w-24, 34], radius=5, fill=accent + (255,))  # 顶部装饰条
    text_center(d, (w//2, h//2 - 18), big, font("cn_bold", 66), NAVY_INK)
    text_center(d, (w//2, h//2 + 60), small, font("cn_reg", 34), (90, 110, 140))
    return card

# 数字卡(大号 Latin 数字 + 中文标签)
def make_numcard(num, big, small, accent=SKY_TOP, w=440, h=300):
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w-1, h-1], radius=28, fill=(255, 255, 255, 240))
    d.rounded_rectangle([0, 0, w-1, h-1], radius=28, outline=accent + (255,), width=4)
    text_center(d, (w//2, h//2 - 36), num, font("num", 92), accent)
    text_center(d, (w//2, h//2 + 44), big, font("cn_bold", 40), NAVY_INK)
    text_center(d, (w//2, h//2 + 92), small, font("cn_reg", 28), (90, 110, 140))
    return card

# ---------------- 通用过场:开场黑场淡入 / 段尾淡出 + 段首高光闪 ----------------
def transitions(frame, tt, dur, seg_index):
    # 段首 0.18s 从黑淡入
    if tt < 0.18:
        a = int(255 * (1 - tt / 0.18))
        ov = Image.new("RGBA", (W, H), (4, 8, 18, a))
        frame.alpha_composite(ov)
    # 段尾 0.15s 淡出到黑
    if tt > dur - 0.15:
        a = int(255 * (tt - (dur - 0.15)) / 0.15)
        ov = Image.new("RGBA", (W, H), (4, 8, 18, clamp(a,0,255)))
        frame.alpha_composite(ov)
    # 段首 0.12s 白色高光闪(更燃),seg1 除外
    if seg_index > 0 and tt < 0.12:
        a = int(150 * (1 - tt / 0.12))
        ov = Image.new("RGBA", (W, H), (255, 255, 255, a))
        frame.alpha_composite(ov)

def flash(frame, tt, t0, strength=180, dur=0.18):
    if t0 <= tt < t0 + dur:
        a = int(strength * (1 - (tt - t0) / dur))
        frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, a)))

# ================= 各分镜 =================

# 预渲染静态层(复用,提速)
L_FLAG = None
def flag_strip():
    """底部阿根廷国旗细条:浅蓝-白-浅蓝 + 中心太阳"""
    global L_FLAG
    if L_FLAG: return L_FLAG
    h = 70
    f = Image.new("RGBA", (760, h), (0,0,0,0))
    d = ImageDraw.Draw(f)
    d.rounded_rectangle([0,0,759,h-1], radius=12, fill=(255,255,255,255))
    d.rectangle([0,0,759,h//3], fill=SKY_TOP+(255,))
    d.rectangle([0,2*h//3,759,h], fill=SKY_TOP+(255,))
    d.ellipse([760//2-15,h//2-15,760//2+15,h//2+15], fill=GOLD+(255,))
    L_FLAG = f
    return f

def seg1(tt, dur):
    f = kenburns(BG_BRIGHT, tt/dur)
    d = ImageDraw.Draw(f)
    # 小标 2026世界杯·夺冠分析
    p,a = appear(tt, 0.25, 0.5)
    if a>0:
        text_center(d, (W//2, 200), "2026 世界杯 · 夺冠概率分析",
                    font("cn_reg", 40), (255,255,255), anchor="mm")
        d.rectangle([W//2-260, 232, int(W//2-260+520*ease_out(p)), 236], fill=WHITE)
    # 主标 阿根廷
    lay,_,_ = text_layer("阿 根 廷", font("cn_bold", 200), WHITE, stroke=6, stroke_fill=NAVY_INK)
    p,a = appear(tt, 0.55, 0.5)
    sc = lerp(0.6, 1.0, ease_out_back(p))
    blit_scaled(f, lay, W//2, 470, sc, a)
    # 副标 能卫冕吗?(金色)
    lay2,_,_ = text_layer("还 能 再 次 封 王 吗 ?", font("cn_bold", 96), GOLD, stroke=5, stroke_fill=NAVY_INK)
    p2,a2 = appear(tt, 1.35, 0.5)
    sc2 = lerp(0.7, 1.0, ease_out_back(p2))
    blit_scaled(f, lay2, W//2, 660, sc2, a2)
    # 国旗条
    p3,a3 = appear(tt, 1.9, 0.5)
    blit_scaled(f, flag_strip(), W//2, 820, 1.0, a3)
    return f

def seg2(tt, dur):
    f = kenburns(BG_BRIGHT, tt/dur)
    d = ImageDraw.Draw(f)
    p,a = appear(tt, 0.15, 0.4)
    if a>0:
        text_center(d, (W//2, 165), "王 朝 的 底 气", font("cn_bold", 72), WHITE,
                    stroke=4, stroke_fill=NAVY_INK)
    cards = [
        (make_numcard("#1", "国际足联排名", "世界第一", SKY_TOP), 0.6),
        (make_card("美洲杯卫冕", "2024 连续封王", GOLD if False else SKY_TOP), 1.3),
        (make_card("钢铁体系", "斯卡洛尼治下", SKY_TOP), 2.0),
    ]
    xs = [W//2 - 520, W//2, W//2 + 520]
    for (card, t0), x in zip(cards, xs):
        p,a = appear(tt, t0, 0.5)
        sc = lerp(0.5, 1.0, ease_out_back(p))
        blit_scaled(f, card, x, 560, sc, a)
    return f

def seg3(tt, dur):
    f = kenburns(BG_BRIGHT, tt/dur)
    d = ImageDraw.Draw(f)
    p,a = appear(tt, 0.1, 0.4)
    if a>0:
        text_center(d, (W//2, 180), "新 一 代 · 扛 起 大 旗", font("cn_bold", 84), WHITE,
                    stroke=5, stroke_fill=NAVY_INK)
    names = ["劳 塔 罗", "J. 阿尔瓦雷斯", "恩 佐", "麦 卡 利 斯 特"]
    times = [0.7, 1.6, 2.5, 3.4]
    ys = [380, 480, 580, 680]
    for nm, t0, y in zip(names, times, ys):
        p,a = appear(tt, t0, 0.4)
        # 名牌:从左滑入
        lay = Image.new("RGBA", (640, 86), (0,0,0,0))
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([0,0,639,85], radius=20, fill=(255,255,255,235))
        dd.rounded_rectangle([0,0,16,85], radius=8, fill=GOLD+(255,))
        text_center(dd, (330, 43), nm, font("cn_bold", 50), NAVY_INK)
        dx = int(lerp(-120, 0, ease_out(p)))
        if a>0:
            chip = lay.copy()
            al = chip.split()[3].point(lambda v:int(v*a))
            chip.putalpha(al)
            f.alpha_composite(chip, (W//2-320+dx, y-43))
    flash(f, tt, 3.4)
    return f

def seg4(tt, dur):
    f = kenburns(BG_DARK, tt/dur)
    d = ImageDraw.Draw(f)
    p,a = appear(tt, 0.2, 0.5)
    if a>0:
        text_center(d, (W//2, 150), "但 是 — — 时 间 的 隐 忧", font("cn_bold", 66),
                    RED_WARN, anchor="mm")
    # 大数字 39 计数 (30->39),0.9s 起算 1.3s
    cu_start, cu_dur = 1.0, 1.4
    pc = clamp((tt - cu_start) / cu_dur)
    val = int(round(lerp(30, 39, ease_out(pc))))
    pa, aa = appear(tt, 0.9, 0.4)
    if aa > 0:
        lay,_,_ = text_layer(str(val), font("num", 320), WHITE, stroke=6, stroke_fill=(0,0,0))
        sc = lerp(0.6, 1.0, ease_out_back(pa))
        blit_scaled(f, lay, W//2, 430, sc, aa)
        text_center(d, (W//2, 300), "梅 西 · 2026 年", font("cn_reg", 40), SKY_NEON, anchor="mm")
    # 39 落定后高光闪 + 副标
    if pc >= 0.999:
        flash(f, tt, cu_start+cu_dur, strength=120)
    p2,a2 = appear(tt, cu_start+cu_dur+0.1, 0.5)
    if a2>0:
        text_center(d, (W//2, 620), "极可能是他的最后一届世界杯", font("cn_bold", 56), GOLD,
                    stroke=3, stroke_fill=NAVY_INK, anchor="mm")
    # 下方三个隐忧点
    pts = ["迪马利亚 已离开", "奥塔门迪 38岁", "新老交替 待解"]
    t0s = [3.4, 4.0, 4.6]
    xs = [W//2-480, W//2, W//2+480]
    for s, t0, x in zip(pts, t0s, xs):
        p3,a3 = appear(tt, t0, 0.45)
        if a3>0:
            lay = Image.new("RGBA",(420,78),(0,0,0,0))
            dd = ImageDraw.Draw(lay)
            dd.rounded_rectangle([0,0,419,77], radius=18, outline=RED_WARN+(255,), width=3,
                                 fill=(20,30,55,210))
            text_center(dd,(210,39), s, font("cn_reg",36), (235,240,250))
            sc=lerp(0.7,1.0,ease_out_back(p3))
            blit_scaled(f, lay, x, 800, sc, a3)
    return f

def seg5(tt, dur):
    f = kenburns(BG_DARK, tt/dur)
    d = ImageDraw.Draw(f)
    # 顶部三个客观变量 chips
    chips = ["48 队新赛制", "北美酷暑", "强敌环伺"]
    for i,(s,x) in enumerate(zip(chips, [W//2-430, W//2, W//2+430])):
        p,a = appear(tt, 0.2+i*0.25, 0.4)
        if a>0:
            lay=Image.new("RGBA",(360,70),(0,0,0,0))
            dd=ImageDraw.Draw(lay)
            dd.rounded_rectangle([0,0,359,69],radius=35,fill=(255,255,255,30),
                                 outline=SKY_NEON+(200,),width=2)
            text_center(dd,(180,35),s,font("cn_reg",34),(225,235,248))
            blit_scaled(f, lay, x, 150, 1.0, a)
    # 标题
    p,a=appear(tt,1.0,0.4)
    if a>0:
        text_center(d,(W//2,270),"夺 冠 概 率 综 合 判 断",font("cn_bold",56),WHITE,anchor="mm")
    # 大号概率:0->16 计数,settle 后显示 12–16%
    cu_start, cu_dur = 1.3, 1.2
    pc = clamp((tt-cu_start)/cu_dur)
    pa,aa = appear(tt, 1.2, 0.4)
    if aa>0:
        if pc < 0.999:
            v = int(round(lerp(0,16,ease_out(pc))))
            s = f"{v}%"
        else:
            s = "12–16%"
        lay,_,_ = text_layer(s, font("num", 210), GOLD, stroke=5, stroke_fill=NAVY_INK)
        sc=lerp(0.7,1.0,ease_out_back(pa))
        blit_scaled(f, lay, W//2, 430, sc, aa)
    if pc>=0.999:
        flash(f, tt, cu_start+cu_dur, strength=110)
    # 对手对比条形图(凸显:第一集团但非唯一)
    bars = [("西班牙",16),("阿根廷",15),("法国",14),("英格兰",12),("巴西",10)]
    bp, ba = appear(tt, 3.0, 0.6)
    if ba>0:
        base_x, base_y, bw, gap, maxh = W//2-430, 770, 130, 90, 230
        for i,(nm,val) in enumerate(bars):
            x = base_x + i*(bw+gap-40)
            grow = ease_out(clamp((tt-3.0-i*0.12)/0.5))
            bh = int(maxh*(val/16.0)*grow)
            hi = (nm=="阿根廷")
            col = GOLD if hi else (90,120,165)
            d.rounded_rectangle([x, base_y-bh, x+bw, base_y], radius=10, fill=col)
            if grow>0.6:
                text_center(d,(x+bw//2, base_y-bh-26), f"{val}%",
                            font("num",30), GOLD if hi else (200,212,228), anchor="mm")
                text_center(d,(x+bw//2, base_y+26), nm,
                            font("cn_bold" if hi else "cn_reg",30),
                            GOLD if hi else (205,215,230), anchor="mm")
    # 结论小字
    p2,a2=appear(tt, 4.4, 0.5)
    if a2>0:
        text_center(d,(W//2, 1010),"稳居第一集团 · 但不是唯一的王",
                    font("cn_reg",38),(225,235,248),anchor="mm")
    return f

def seg6(tt, dur):
    f = kenburns(BG_BRIGHT, tt/dur)
    d = ImageDraw.Draw(f)
    flash(f, tt, 0.0, strength=200, dur=0.3)
    lay,_,_ = text_layer("2026 · 最 后 一 舞", font("cn_bold", 150), WHITE, stroke=6, stroke_fill=NAVY_INK)
    p,a=appear(tt,0.2,0.5)
    sc=lerp(0.7,1.0,ease_out_back(p))
    blit_scaled(f, lay, W//2, 410, sc, a)
    lay2,_,_=text_layer("你 敢 赌 他 笑 到 最 后 吗 ?", font("cn_bold",78), GOLD, stroke=5, stroke_fill=NAVY_INK)
    p2,a2=appear(tt,1.0,0.6)
    blit_scaled(f, lay2, W//2, 600, lerp(0.8,1.0,ease_out(p2)), a2)
    p3,a3=appear(tt,1.8,0.6)
    blit_scaled(f, flag_strip(), W//2, 770, 1.1, a3)
    return f

SEG_FUNCS = [seg1, seg2, seg3, seg4, seg5, seg6]

# ================= 主循环 =================
def render_all():
    for si, (fn, dur) in enumerate(zip(SEG_FUNCS, CLIP_DUR), start=0):
        outdir = os.path.join(FRAMES_DIR, f"seg{si+1}")
        os.makedirs(outdir, exist_ok=True)
        nframes = round(dur * FPS)
        for fi in range(nframes):
            tt = fi / FPS
            frame = fn(tt, dur)
            transitions(frame, tt, dur, si)
            frame.convert("RGB").save(os.path.join(outdir, f"{fi:04d}.jpg"),
                                      quality=95)
        print(f"seg{si+1}: {nframes} frames -> {outdir}")

if __name__ == "__main__":
    render_all()
    print("ALL FRAMES DONE")
