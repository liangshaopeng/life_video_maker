# -*- coding: utf-8 -*-
"""生成右下角作者方形水印徽标 PNG(透明背景)。本机 ffmpeg 无 drawtext,用 Pillow 烧。
方形徽标:半透明深底 + 细金边 + 白字(4字自动排 2x2)。
用法: python3 make_watermark.py "思考的我" build/watermark.png [字号=50]
"""
import sys, math
from PIL import Image, ImageDraw, ImageFont

txt = sys.argv[1] if len(sys.argv) > 1 else "思考的我"
out = sys.argv[2] if len(sys.argv) > 2 else "build/watermark.png"
fs  = int(sys.argv[3]) if len(sys.argv) > 3 else 50
F = "/System/Library/Fonts/Hiragino Sans GB.ttc"   # index2 = W6 粗
fnt = ImageFont.truetype(F, fs, index=2)

chars = list(txt)
n = len(chars)
cols = 2 if n == 4 else math.ceil(math.sqrt(n))
rows = math.ceil(n / cols)

tmp = Image.new("RGBA", (8, 8)); d = ImageDraw.Draw(tmp)
cw = ch = 0
for c in chars:
    bb = d.textbbox((0, 0), c, font=fnt); cw = max(cw, bb[2] - bb[0]); ch = max(ch, bb[3] - bb[1])

gap, padin = 8, 18
grid_w = cols * cw + (cols - 1) * gap
grid_h = rows * ch + (rows - 1) * gap
side = max(grid_w, grid_h) + 2 * padin                # 强制正方形

im = Image.new("RGBA", (side, side), (0, 0, 0, 0))
dd = ImageDraw.Draw(im)
r = max(12, side // 9)
dd.rounded_rectangle([1, 1, side - 2, side - 2], radius=r,
                     fill=(9, 16, 44, 140), outline=(252, 209, 50, 175), width=2)
ox = (side - grid_w) // 2
oy = (side - grid_h) // 2
for i, c in enumerate(chars):
    rr, cc = divmod(i, cols)
    cx = ox + cc * (cw + gap) + cw // 2
    cy = oy + rr * (ch + gap) + ch // 2
    dd.text((cx, cy), c, font=fnt, fill=(255, 255, 255, 240),
            anchor="mm", stroke_width=2, stroke_fill=(0, 0, 18, 150))
im.save(out)
print("square watermark", out, im.size)
