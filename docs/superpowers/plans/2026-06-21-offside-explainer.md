# 越位科普视频 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 产出一支竖屏 9:16 / 约 90 秒的"有观点的越位解读"短视频(`越位_final.mp4`),实现设计文档 `docs/superpowers/specs/2026-06-21-offside-explainer-design.md`。

**Architecture:** 复用 `football-tactical-analysis-video` skill 的整条配置驱动竖屏管线(edge-tts 配音 + 流畅字幕 + 逐帧 overlay + 竖屏合成 + sidechain BGM + 水印)。**唯一新增**是一个 PIL 战术板动画引擎(`lib_pitch.py` + `render_pitch.py`):逐帧画竖向足球场 + 红蓝球员(关键帧插值移动)+ 可推拉越位线 + 球/箭头,输出全屏 1080×1920 背景帧。再扩展 `assemble_v.py` 让"动画段"用这些背景帧(替代真实 footage 画面带),"真实切片段"(梅西破越位)仍走原 footage 逻辑。

**Tech Stack:** Python3 · Pillow(PIL) · edge-tts · ffmpeg/ffprobe · bash。所有脚本沿用 macOS 字体路径。

---

## 视觉风格(执行前请用户拍板,Task 3 出首帧后确认)

**暗色极简战术板**,与现有 overlay 文字面板配色统一:
- 背景:`navy (8,16,34)` 纯色;足球场用**半透明白线**勾勒(边界/中线/中圈/上下禁区/球门),不画绿草皮。
- 球员:实心圆点 + 白描边。红队 `warn (244,86,80)`、蓝(防守)队 `sky (96,178,240)`,半径约 26px,可带白色号码/小标签。
- 越位线:`gold (252,209,50)` **虚线横线**,横跨球场,醒目。
- 球:白色小圆(半径 ~12px)。
- 箭头:复用 gold/good 色,虚线或实线(传球/跑动)。

## 坐标系约定(贯穿动画规格与绘制)

- 球场绘制区:`X0=90, Y0=320, FW=900, FH=1280`(即场地占 x∈[90,990]、y∈[320,1600],上方留顶部文字面板,下方留字幕区)。
- 动画规格里所有位置用**归一化坐标** `nx,ny ∈ [0,1]`:`px = X0 + nx*FW`,`py = Y0 + ny*FH`。`ny=0` 在上(对方球门一侧),`ny=1` 在下(本方)。
- 越位线是水平线,只需一个 `ny`:从左画到右,像素 y = `Y0 + ny*FH`。

## 配音声线

设计要求"笃定·有网感的观点旁白"。edge-tts 候选:`zh-CN-YunxiNeural`(云希,叙事感强、年轻、有网感 — **默认**)、备选 `zh-CN-YunyangNeural`(云扬,权威笃定)。`rate` 用 `+6%`(比詹俊激情的 +12% 慢,讲道理不喊球),`pitch +0Hz`,`volume +6%`。Task 10 试听后定。

---

## File Structure

新建项目目录 `规则科普视频/越位/`(与现有 `战术解析视频/…` 等同级)。每个视频项目是 skill 的一次实例:把 skill 脚本复制进来再扩展(沿用现有项目惯例)。

```
规则科普视频/越位/
├── project.json              # 配置:旁白文案 + 5段(pitch动画规格 / footage) + overlay文字
├── lib_overlays_v.py         # [复制] 文字面板/字幕/水印 (不改)
├── make_narration.py         # [复制] 配音+流畅字幕+timeline (不改)
├── render_overlays_v.py      # [复制] 逐帧透明叠加层 (不改)
├── assemble_v.py             # [复制+改] 增加 pitch 段分支
├── mix_bgm.sh                # [复制] BGM 闪避 (不改)
├── make_watermark.py         # [复制] 水印PNG (不改)
├── add_watermark.sh          # [复制] 叠水印 (不改)
├── lib_pitch.py              # [新增] 战术板绘图:场/球员/线/球 + 关键帧插值
├── render_pitch.py           # [新增] 逐帧渲染动画段背景帧 -> build/pitch/segN/####.png
├── test_pitch.py             # [新增] interp() 纯函数单元测试
├── footage/
│   └── messi_offside.mp4     # 梅西破越位真实切片(Task 12 接入)
├── bgm/
│   └── bed.mp3               # BGM(循环成 ≥总长)
└── build/                    # 中间件(脚本自动生成)
    ├── audio/segN.mp3  subs/segN.srt  timeline.json
    ├── overlays/segN/####.png   # 透明文字层
    ├── pitch/segN/####.png      # 战术板背景帧(新增)
    └── clips/clipN.mp4  concat.txt
```

**段落 → 类型映射**(对应分镜脚本 5 段):

| seg | id | 时间 | 背景类型 | 说明 |
|---|---|---|---|---|
| 1 | hook | 0–3s | pitch(静态/闪) | 钩子,标题叠加 |
| 2 | no_offside | 3–22s | pitch 动画 | 演示蹲门口、中场掏空 |
| 3 | the_line | 22–45s | pitch 动画 → 切 footage | 越位线 + 梅西切片 |
| 4 | core | 45–70s | pitch 动画 | 两队压一条线对抗 vs 空旷对比 |
| 5 | meaning | 70–90s | pitch(快闪) | 升华 |

> 注:seg3 较长且混合"动画+真实切片",实现时可拆成 3a(动画讲越位线)与 3b(梅西切片)两个 segment,使每段背景类型单一。Task 9 定稿时按此拆。

---

## Task 1: 建项目目录并复制 skill 脚本

**Files:**
- Create dir: `规则科普视频/越位/`、`规则科普视频/越位/footage/`、`规则科普视频/越位/bgm/`
- Copy: skill `scripts/*` → 项目目录

- [ ] **Step 1: 建目录并复制脚本**

```bash
cd "/Users/liangshaopeng_backup/code/life/life_video_maker"
mkdir -p "规则科普视频/越位/footage" "规则科普视频/越位/bgm"
SK=".claude/skills/football-tactical-analysis-video/scripts"
cp "$SK/lib_overlays_v.py" "$SK/make_narration.py" "$SK/render_overlays_v.py" \
   "$SK/assemble_v.py" "$SK/mix_bgm.sh" "$SK/make_watermark.py" "$SK/add_watermark.sh" \
   "规则科普视频/越位/"
```

- [ ] **Step 2: 验证脚本齐全**

Run: `ls "规则科普视频/越位/"`
Expected: 列出 7 个脚本(lib_overlays_v.py / make_narration.py / render_overlays_v.py / assemble_v.py / mix_bgm.sh / make_watermark.py / add_watermark.sh)。

- [ ] **Step 3: 验证依赖可用**

Run: `python3 -c "import edge_tts, PIL; print('ok')" && which ffmpeg ffprobe`
Expected: 打印 `ok` 且 ffmpeg/ffprobe 有路径。缺 edge-tts/pillow 则 `pip3 install edge-tts pillow`。

- [ ] **Step 4: Commit**

```bash
git add "规则科普视频/越位/"
git commit -m "feat(越位): 初始化项目目录并复制管线脚本"
```

---

## Task 2: lib_pitch.py — 坐标映射 + 关键帧插值(TDD)

**Files:**
- Create: `规则科普视频/越位/lib_pitch.py`
- Test: `规则科普视频/越位/test_pitch.py`

- [ ] **Step 1: 写失败测试**

`规则科普视频/越位/test_pitch.py`:
```python
# -*- coding: utf-8 -*-
import lib_pitch as P

def test_interp_before_first_key_returns_first():
    keys = [[1.0, 0.2, 0.3], [3.0, 0.8, 0.9]]
    assert P.interp(keys, 0.0) == [0.2, 0.3]

def test_interp_after_last_key_returns_last():
    keys = [[1.0, 0.2, 0.3], [3.0, 0.8, 0.9]]
    assert P.interp(keys, 9.0) == [0.8, 0.9]

def test_interp_midpoint_is_linear():
    keys = [[0.0, 0.0, 0.0], [2.0, 1.0, 0.5]]
    assert P.interp(keys, 1.0) == [0.5, 0.25]

def test_interp_scalar_value():
    keys = [[0.0, 0.2], [4.0, 0.6]]
    assert P.interp(keys, 2.0) == [0.4]

def test_to_px_maps_normalized_to_pitch_rect():
    assert P.to_px(0.0, 0.0) == (P.X0, P.Y0)
    assert P.to_px(1.0, 1.0) == (P.X0 + P.FW, P.Y0 + P.FH)
```

- [ ] **Step 2: 运行,确认失败**

Run: `cd "规则科普视频/越位" && python3 -m pytest test_pitch.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'lib_pitch'` 或 AttributeError)。

- [ ] **Step 3: 写最小实现**

`规则科普视频/越位/lib_pitch.py`:
```python
# -*- coding: utf-8 -*-
"""战术板俯视图动画库:竖向足球场 + 球员(关键帧插值)+ 越位线 + 球。
复用 lib_overlays_v 的画布常量/配色/字体/缓动。输出全屏 1080x1920 背景帧。"""
import math
from PIL import Image, ImageDraw
from lib_overlays_v import W, H, FPS, THEME, C, font, lerp, clamp, e_io

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
```

- [ ] **Step 4: 运行,确认通过**

Run: `cd "规则科普视频/越位" && python3 -m pytest test_pitch.py -v`
Expected: 5 passed。

- [ ] **Step 5: Commit**

```bash
git add "规则科普视频/越位/lib_pitch.py" "规则科普视频/越位/test_pitch.py"
git commit -m "feat(越位): 战术板坐标映射与关键帧插值(TDD)"
```

---

## Task 3: lib_pitch.py — 画竖向足球场

**Files:** Modify `规则科普视频/越位/lib_pitch.py`

- [ ] **Step 1: 追加足球场绘制函数**

在 `lib_pitch.py` 末尾追加:
```python
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
        d.rectangle([cx - paw//2, yy, cx + paw//2, yy + sgn*pah], outline=white, width=4)
        gy = yy - sgn*gh if sgn < 0 else yy
        d.rectangle([cx - gw//2, min(yy, yy+sgn*gh), cx + gw//2, max(yy, yy+sgn*gh)],
                    outline=(255,255,255,200), width=5)
    return img

def new_frame():
    """全屏 navy 底帧(RGBA)。"""
    return Image.new("RGBA", (W, H), tuple(C("navy")) + (255,))
```

- [ ] **Step 2: 渲染一帧抽看**

Run:
```bash
cd "规则科普视频/越位" && python3 -c "import lib_pitch as P; f=P.new_frame(); P.draw_pitch(f); f.convert('RGB').save('/tmp/pitch_test.png')"
```
Expected: 生成 `/tmp/pitch_test.png`。用 Read 工具查看该 PNG:应是深蓝底 + 白线竖向球场(边界/中线/中圈/上下禁区/球门),无报错。

- [ ] **Step 3: (检查点)请用户确认球场视觉风格**,不满意则调 `draw_pitch` 的线色/线宽/禁区尺寸后重渲。

- [ ] **Step 4: Commit**

```bash
git add "规则科普视频/越位/lib_pitch.py"
git commit -m "feat(越位): 竖向极简足球场绘制"
```

---

## Task 4: lib_pitch.py — 画球员

**Files:** Modify `规则科普视频/越位/lib_pitch.py`

- [ ] **Step 1: 追加球员绘制**

在 `lib_pitch.py` 末尾追加:
```python
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
```

- [ ] **Step 2: 渲染抽看**

Run:
```bash
cd "规则科普视频/越位" && python3 -c "
import lib_pitch as P
f=P.new_frame(); P.draw_pitch(f)
P.draw_player(f,0.5,0.12,'red','9')      # 红方蹲对方门口
P.draw_player(f,0.5,0.85,'blue','2')     # 蓝方后卫
f.convert('RGB').save('/tmp/pitch_players.png')"
```
Expected: Read 查看 `/tmp/pitch_players.png`:门口有红点(标9)、下方有蓝点(标2),圆点清晰带白边。

- [ ] **Step 3: Commit**

```bash
git add "规则科普视频/越位/lib_pitch.py"
git commit -m "feat(越位): 球员圆点绘制"
```

---

## Task 5: lib_pitch.py — 画越位线与球

**Files:** Modify `规则科普视频/越位/lib_pitch.py`

- [ ] **Step 1: 追加越位线与球**

在 `lib_pitch.py` 末尾追加:
```python
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

def draw_ball(img, nx, ny):
    d = ImageDraw.Draw(img)
    px, py = to_px(nx, ny)
    r = 12
    d.ellipse([px-r, py-r, px+r, py+r], fill=(255,255,255,255), outline=(20,20,20,255), width=2)
    return img
```

- [ ] **Step 2: 渲染抽看**

Run:
```bash
cd "规则科普视频/越位" && python3 -c "
import lib_pitch as P
f=P.new_frame(); P.draw_pitch(f)
P.draw_offside_line(f,0.30)
P.draw_player(f,0.5,0.12,'red','9'); P.draw_ball(f,0.52,0.6)
f.convert('RGB').save('/tmp/pitch_line.png')"
```
Expected: Read 查看 `/tmp/pitch_line.png`:上部有金色虚线横线、红点在线上方(越位)、白色小球在中下。

- [ ] **Step 3: Commit**

```bash
git add "规则科普视频/越位/lib_pitch.py"
git commit -m "feat(越位): 越位线与球绘制"
```

---

## Task 6: lib_pitch.py — 组合渲染单帧(按 spec + 时间)

**Files:** Modify `规则科普视频/越位/lib_pitch.py`

- [ ] **Step 1: 追加箭头(复用 lib_overlays)与主渲染函数**

在 `lib_pitch.py` 末尾追加:
```python
def draw_arrow(img, p_from, p_to, col=None, w=8, dashed=True):
    """归一化两点间画箭头(直线+箭头头)。"""
    d = ImageDraw.Draw(img)
    col = col or (tuple(C("gold")) + (255,))
    x1, y1 = to_px(*p_from); x2, y2 = to_px(*p_to)
    if dashed:
        seg, g = 26, 16; tot = math.hypot(x2-x1, y2-y1); n = max(1, int(tot//(seg+g)))
        for k in range(n):
            a = k*(seg+g)/tot; b = min(1.0, (k*(seg+g)+seg)/tot)
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
```

- [ ] **Step 2: 渲染三个时间点抽看(验证插值动起来)**

Run:
```bash
cd "规则科普视频/越位" && python3 -c "
import lib_pitch as P
spec={'scene_label':'假如没有越位',
 'players':[{'team':'red','label':'9','keys':[[0,0.5,0.6],[2,0.5,0.12]]},
            {'team':'blue','label':'2','keys':[[0,0.5,0.85],[2,0.5,0.85]]}],
 'ball':{'keys':[[0,0.5,0.62],[2,0.5,0.16]]}}
for tt in (0.0,1.0,2.0):
    f=P.render_pitch_frame(spec,tt); f.convert('RGB').save(f'/tmp/anim_{tt}.png')"
```
Expected: Read 查看 `/tmp/anim_0.0.png` / `_1.0.png` / `_2.0.png`:红点+球从中场逐步移动到对方门口,蓝点不动,顶部有"假如没有越位"金字。

- [ ] **Step 3: Commit**

```bash
git add "规则科普视频/越位/lib_pitch.py"
git commit -m "feat(越位): 箭头+按时间组合渲染战术板单帧"
```

---

## Task 7: render_pitch.py — 逐帧渲染动画段背景

**Files:** Create `规则科普视频/越位/render_pitch.py`

- [ ] **Step 1: 写渲染脚本**

`规则科普视频/越位/render_pitch.py`:
```python
# -*- coding: utf-8 -*-
"""读 project.json + build/timeline.json,对每个含 'pitch' 的段逐帧渲染全屏背景帧
   -> build/pitch/segN/####.png (1080x1920, 30fps)。用法: python3 render_pitch.py [project.json]"""
import os, json, sys
import lib_pitch as P

PROJ = sys.argv[1] if len(sys.argv) > 1 else "project.json"
cfg = json.load(open(PROJ, encoding="utf-8"))
ROOT = os.path.dirname(os.path.abspath(PROJ))
BUILD = os.path.join(ROOT, cfg.get("build_dir", "build"))
TL = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))

for seg, tl in zip(cfg["segments"], TL["segs"]):
    spec = seg.get("pitch")
    if not spec:
        continue
    i = tl["seg"]; clip = tl["clip"]; n = max(1, round(clip * P.FPS))
    outdir = os.path.join(BUILD, "pitch", f"seg{i}")
    os.makedirs(outdir, exist_ok=True)
    for fi in range(n):
        tt = fi / P.FPS
        fr = P.render_pitch_frame(spec, tt)
        fr.convert("RGB").save(os.path.join(outdir, f"{fi:04d}.png"))
    print(f"→ pitch seg{i}({tl['id']}) {n} 帧 ({clip:.1f}s)")
print("✅ 战术板背景帧渲染完成")
```

- [ ] **Step 2: 用临时 timeline 冒烟测试**

Run:
```bash
cd "规则科普视频/越位" && mkdir -p build && python3 -c "
import json,os; os.makedirs('build',exist_ok=True)
json.dump({'total':2.0,'segs':[{'seg':1,'id':'t','audio':1.65,'clip':2.0,'start':0,'end':2.0}]},open('build/timeline.json','w'))
json.dump({'segments':[{'id':'t','pitch':{'players':[{'team':'red','keys':[[0,0.5,0.6],[2,0.5,0.12]]}]}}]},open('_tmp_proj.json','w'))
" && python3 render_pitch.py _tmp_proj.json
```
Expected: 打印 `pitch seg1(t) 60 帧`。

- [ ] **Step 3: 验证帧数与分辨率**

Run: `ls build/pitch/seg1 | wc -l && python3 -c "from PIL import Image; print(Image.open('build/pitch/seg1/0000.png').size)"`
Expected: `60` 且 `(1080, 1920)`。

- [ ] **Step 4: 清理临时文件并 Commit**

```bash
rm -f _tmp_proj.json && rm -rf build
git add "规则科普视频/越位/render_pitch.py"
git commit -m "feat(越位): 逐帧渲染战术板动画段背景"
```

---

## Task 8: 扩展 assemble_v.py — 支持 pitch 段

**Files:** Modify `规则科普视频/越位/assemble_v.py:52`(`build_clip` 函数开头)

- [ ] **Step 1: 在 build_clip 内、freeze 判断之前插入 pitch 分支**

在 `build_clip` 中,把现有 `freeze=fp.get("freeze")`(`:59`)之后、`if freeze is not None:`(`:61`)之前,插入:
```python
    # —— 动画段:背景用战术板帧序列(全屏1080x1920),不走画面带逻辑 ——
    if seg.get("pitch") is not None:
        pdir = os.path.join(BUILD, "pitch", f"seg{i}", "%04d.png")
        vf = (f"[0:v]fps=30,trim=duration={clip:.3f},setpts=PTS-STARTPTS,"
              f"fade=t=in:st=0:d=0.2,fade=t=out:st={clip-0.2:.3f}:d=0.2[bgp];"
              f"[bgp][1:v]overlay=0:0:shortest=0[v]")
        af = f"[2:a]apad,atrim=duration={clip:.3f},afade=t=out:st={clip-0.15:.3f}:d=0.15[a]"
        cmd = ["ffmpeg","-y","-hide_banner","-loglevel","error",
               "-framerate","30","-i",pdir,            # 0 = 战术板背景帧
               "-framerate","30","-i",ov,              # 1 = 透明叠加层
               "-i",aud,                                # 2 = 配音
               "-filter_complex",vf+";"+af,
               "-map","[v]","-map","[a]","-r","30","-c:v","libx264","-profile:v","high",
               "-pix_fmt","yuv420p","-preset","medium","-c:a","aac","-b:a","192k","-t",f"{clip:.3f}",out]
        print(f"→ clip{i}({tl['id']}) PITCH {clip:.1f}s")
        subprocess.run(cmd,check=True)
        return out
```

- [ ] **Step 2: 验证语法**

Run: `cd "规则科普视频/越位" && python3 -c "import ast; ast.parse(open('assemble_v.py').read()); print('ok')"`
Expected: `ok`(本任务的端到端验证在 Task 11)。

- [ ] **Step 3: Commit**

```bash
git add "规则科普视频/越位/assemble_v.py"
git commit -m "feat(越位): assemble 支持战术板动画段背景"
```

---

## Task 9: 写 project.json(旁白文案 + 动画规格 + overlay)

**Files:** Create `规则科普视频/越位/project.json`

- [ ] **Step 1: 写配置**。以分镜脚本(spec)为准,逐段填 `text`(旁白)、`pitch` 或 `footage`、`overlay`。按 File Structure 表把 seg3 拆为 3a(动画)+3b(梅西切片)。顶层照搬下列骨架,`players/ball/offside_line/arrows` 的关键帧坐标参照"坐标系约定"手填,执行时按 Task 6 方式抽帧微调。

`规则科普视频/越位/project.json` 骨架(文案为定稿,动画坐标为初值待调):
```json
{
  "name": "越位",
  "output_dir": ".",
  "build_dir": "build",
  "voice": { "name": "zh-CN-YunxiNeural", "rate": "+6%", "pitch": "+0Hz", "volume": "+6%" },
  "pad": 0.3,
  "caption_maxlen": 16,
  "no_split": ["梅西"],
  "watermark": "思考的我",
  "theme": { "navy": [8,16,34], "gold": [252,209,50], "sky": [96,178,240], "warn": [244,86,80] },
  "segments": [
    {
      "id": "hook",
      "text": "足球里最招人骂的规则,越位。但你敢删了它试试?",
      "pitch": { "players": [], "scene_label": "" },
      "overlay": { "layout": "title", "title": "越 位", "subtitle": "最招人骂\\n又最不能删的规则", "sup": "规则科普 · 越位" }
    },
    {
      "id": "no_offside",
      "text": "没有越位,最聪明的踢法就是派个人,一直杵在对方门口,等一脚长传喂饼。两边都这么干,中场就空了,足球变成隔着大半个场子互相开大脚。",
      "pitch": {
        "scene_label": "假如没有越位",
        "players": [
          {"team":"red","label":"9","keys":[[0,0.5,0.55],[3,0.5,0.10],[19,0.5,0.10]]},
          {"team":"blue","label":"2","keys":[[0,0.5,0.85],[19,0.5,0.82]]},
          {"team":"blue","label":"9","keys":[[6,0.5,0.90],[19,0.5,0.92]]}
        ],
        "ball": {"keys":[[0,0.5,0.6],[2.5,0.5,0.14]]},
        "arrows":[{"from":[0.5,0.6],"to":[0.5,0.14],"t":0.5,"dur":2.0,"color":"gold","style":"dashed"}]
      },
      "overlay": { "layout": "beat", "title": "蹲门口等喂饼", "kicker": "中场没人了", "accent": "warn" }
    },
    {
      "id": "the_line",
      "text": "越位这条线就是来治它的:不许你提前站到最后一个后卫身后等球。想得分,就得跟防线斗,在出球那一刻、压着线冲过去。",
      "pitch": {
        "scene_label": "越位线 = 倒数第二个防守人",
        "offside_line": {"keys":[[0,0.35],[8,0.35]]},
        "players": [
          {"team":"red","label":"9","keys":[[0,0.5,0.5],[4,0.5,0.30]]},
          {"team":"blue","label":"2","keys":[[0,0.5,0.35],[8,0.5,0.35]]}
        ]
      },
      "overlay": { "layout": "beat", "title": "不许站后卫身后等球", "kicker": "看'出球那一刻'", "accent": "sky" }
    },
    {
      "id": "messi",
      "text": "早半步,吹掉。看梅西,就是踩着这条线,在出球那一刻反插进去。",
      "footage": { "src": "footage/messi_offside.mp4", "start": 0, "speed": 0.7 },
      "overlay": { "layout": "beat", "title": "压着线反插", "kicker": "梅西破越位", "accent": "gold" }
    },
    {
      "id": "core",
      "text": "看明白没?越位不是为了少进球。它是把两队摁在同一条线上,面对面真刀真枪地拼,而不是各蹲一头,等天上掉馅饼。",
      "pitch": {
        "scene_label": "摁在一条线上 面对面拼",
        "offside_line": {"keys":[[0,0.45],[25,0.45]]},
        "players": [
          {"team":"red","label":"","keys":[[0,0.30,0.50],[25,0.40,0.42]]},
          {"team":"red","label":"","keys":[[0,0.55,0.52],[25,0.60,0.44]]},
          {"team":"blue","label":"","keys":[[0,0.35,0.45],[25,0.45,0.45]]},
          {"team":"blue","label":"","keys":[[0,0.62,0.45],[25,0.58,0.45]]}
        ]
      },
      "overlay": { "layout": "beat", "title": "把两队摁在一条线上", "kicker": "面对面拼,而不是等馅饼", "accent": "good" }
    },
    {
      "id": "meaning",
      "text": "规则是人定的,不是天定的。可一旦删了越位,足球就垮成大脚冲吊。好规则从来不是为了限制谁,是为了不让比赛沦为投机。这,就是越位存在的意义。",
      "pitch": { "players": [], "scene_label": "" },
      "overlay": { "layout": "end", "title": "好规则不是限制\\n是反投机", "subtitle": "这就是越位存在的意义" }
    }
  ]
}
```

- [ ] **Step 2: 校验 JSON 合法**

Run: `cd "规则科普视频/越位" && python3 -c "import json; json.load(open('project.json')); print('ok')"`
Expected: `ok`。

- [ ] **Step 3: Commit**

```bash
git add "规则科普视频/越位/project.json"
git commit -m "feat(越位): project.json 旁白文案与动画规格初稿"
```

---

## Task 10: 配音 + 字幕 + 时间轴,核时长

**Files:** 生成 `build/audio/segN.mp3`、`build/subs/segN.srt`、`build/timeline.json`

- [ ] **Step 1: 跑配音**

Run: `cd "规则科普视频/越位" && python3 make_narration.py project.json`
Expected: 逐段打印生成 mp3/srt,末尾写出 `build/timeline.json`,无 edge-tts 失败。

- [ ] **Step 2: 核总时长**

Run: `python3 -c "import json; t=json.load(open('build/timeline.json')); print('total=%.1fs'%t['total'])"`
Expected: `total` 在 60–95s。若 >95s:精简 project.json 文案重跑;若 <60s:适当加句或放慢 `rate`。

- [ ] **Step 3: 扫字幕(绝不断"梅西"、无碎行)**

Run: `cat build/subs/seg*.srt`
Expected: 每行通顺、不在"梅西"中间断行;不通顺则调 `caption_maxlen`/文案标点后重跑本任务。

- [ ] **Step 4: Commit timeline(音频/字幕为 build 产物,按 .gitignore 仅提交 timeline)**

```bash
git add -f "规则科普视频/越位/build/timeline.json"
git commit -m "chore(越位): 配音时间轴(timeline)"
```

---

## Task 11: 渲染叠加层 + 战术板背景 + 合成

**Files:** 生成 `build/overlays/`、`build/pitch/`、`越位_vertical.mp4`

- [ ] **Step 1: 渲染透明叠加层**

Run: `cd "规则科普视频/越位" && python3 render_overlays_v.py project.json`
Expected: 逐段生成 `build/overlays/segN/####.png`,无报错。

- [ ] **Step 2: 渲染战术板背景帧**

Run: `python3 render_pitch.py project.json`
Expected: 对含 pitch 的段打印帧数;`build/pitch/segN/` 有帧。

- [ ] **Step 3: 合成竖屏成片**

Run: `python3 assemble_v.py project.json`
Expected: 逐段打印(PITCH 段标 `PITCH`、梅西段标 footage),末尾 `✅ 竖屏成片: …越位_vertical.mp4`。

- [ ] **Step 4: 验证分辨率/时长 + 抽帧**

Run:
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 越位_vertical.mp4
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 越位_vertical.mp4
ffmpeg -y -hide_banner -loglevel error -i 越位_vertical.mp4 -vf "fps=1,scale=270:-1,tile=5x4" -frames:v 1 /tmp/wall.png
```
Expected: `1080,1920`;时长≈timeline.total;Read 查看 `/tmp/wall.png`:各段战术板/切片+文字+字幕正常,动画有移动。

- [ ] **Step 5: (检查点)请用户看 `越位_vertical.mp4`**,按反馈调 project.json 关键帧/文案,重跑相关步骤(改文案→10→11;只改动画坐标→render_pitch→assemble)。

- [ ] **Step 6: Commit(成片为 .mp4,被 .gitignore 忽略,仅记录里程碑)**

```bash
git commit --allow-empty -m "chore(越位): 竖屏纯解说成片通过(本地产物)"
```

---

## Task 12: 接入梅西破越位真实切片

**Files:** `规则科普视频/越位/footage/messi_offside.mp4`

- [ ] **Step 1: 放置素材**。把梅西破越位竖切/横切片段放到 `footage/messi_offside.mp4`(来源由用户提供或后续确定;横屏素材会按现有 compose 逻辑嵌成画面带+模糊背景)。确认存在:

Run: `ls -la "规则科普视频/越位/footage/messi_offside.mp4"`
Expected: 文件存在且体积正常。

- [ ] **Step 2: 用缩略图墙定位反插瞬间,填 `messi` 段 footage.start**

Run: `cd "规则科普视频/越位" && ffmpeg -y -hide_banner -loglevel error -i footage/messi_offside.mp4 -vf "fps=1,scale=320:-1,tile=4x4" -frames:v 1 /tmp/messi_wall.png`
Expected: Read 查看,定位反插瞬间秒数,写回 project.json `messi` 段 `footage.start`、`speed`(慢镜 0.6–0.7)。

- [ ] **Step 3: 重合成并抽帧验证梅西段**

Run: `python3 assemble_v.py project.json && ffmpeg -y -hide_banner -loglevel error -ss 0 -i 越位_vertical.mp4 -vf "fps=2,scale=270:-1,tile=4x3" -frames:v 1 /tmp/messi_check.png`
Expected: Read 查看,梅西段真实画面清晰嵌中间带、文字/字幕正常。

- [ ] **Step 4: Commit**

```bash
git add "规则科普视频/越位/project.json"
git commit -m "feat(越位): 接入梅西破越位切片并定位"
```

---

## Task 13: BGM + 水印,出成片

**Files:** `规则科普视频/越位/bgm/bed.mp3`、`越位_final.mp4`

- [ ] **Step 1: 备 BGM 并循环成 bed**。选一段思辨/上扬情绪的纯音乐放 `bgm/`,循环到 ≥总时长:

Run:
```bash
cd "规则科普视频/越位" && ffmpeg -y -hide_banner -loglevel error -stream_loop -1 -i bgm/<源.mp3> -t 100 -c copy bgm/bed.mp3
```
Expected: 生成 `bgm/bed.mp3`(>总时长)。

- [ ] **Step 2: 混 BGM(解说自动闪避)**

Run: `bash mix_bgm.sh 越位_vertical.mp4 bgm/bed.mp3 越位_bgm.mp4 0 0.20`
Expected: 生成 `越位_bgm.mp4`;解说一开口 BGM 自动压低。

- [ ] **Step 3: 生成并叠水印**

Run:
```bash
python3 make_watermark.py "思考的我" build/watermark.png 50
bash add_watermark.sh 越位_bgm.mp4 build/watermark.png 越位_final.mp4 br "40:30"
```
Expected: 生成 `越位_final.mp4`,右下角有水印。

- [ ] **Step 4: Commit**

```bash
git add "规则科普视频/越位/project.json"
git commit --allow-empty -m "chore(越位): 成片(BGM+水印)完成(本地产物)"
```

---

## Task 14: 全片验收

- [ ] **Step 1: 终检**

Run:
```bash
cd "规则科普视频/越位"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 越位_final.mp4
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 越位_final.mp4
ffmpeg -y -hide_banner -loglevel error -i 越位_final.mp4 -vf "fps=1,scale=270:-1,tile=5x4" -frames:v 1 /tmp/final_wall.png
```
Expected: `1080,1920,30/1`;时长 60–95s;Read 查看 `/tmp/final_wall.png` 通片连贯。

- [ ] **Step 2: 对照验收清单**(逐条确认):
  - [ ] 0–3s 钩子标题成立、抓人;
  - [ ] no_offside 段能看出"蹲门口+中场空"的蠢;
  - [ ] the_line + 梅西段把"越位线/出球瞬间"讲清;
  - [ ] core 段题眼"摁在一条线上面对面拼"画面与字幕到位;
  - [ ] meaning 段升华;
  - [ ] 全程字幕通顺、不断"梅西"、与配音同步;
  - [ ] BGM 不盖解说、水印在位。

- [ ] **Step 3: 通知用户验收成片 `越位_final.mp4`**;按反馈回到对应任务迭代。

---

## Self-Review(写完计划后自查)

**Spec 覆盖:** 设计文档各项均有任务承接——定位/受众(贯穿文案与 overlay)、Show-don't-tell(Task 6/9 的 no_offside 动画)、竖屏90秒(Task 1/10/14 规格与核时长)、方案B结构(Task 9 六段)、分镜脚本(Task 9 文案逐段落地)、笃定旁白(Task 10 声线)、图示为主切片点缀(Task 2–8 动画引擎 + Task 12 梅西)、最大风险"战术板动画"(Task 2–8 专门拆解)。✅

**占位符扫描:** 无 TBD/TODO;动画坐标标注为"初值待抽帧微调"(有 Task 6 的验证手段),旁白文案为定稿,非占位。✅

**类型/命名一致性:** `interp(keys,t)`→list、`to_px(nx,ny)`→(px,py)、`render_pitch_frame(spec,tt)`、`new_frame()`、`draw_pitch/draw_player/draw_offside_line/draw_ball/draw_arrow` 在 Task 2–8 定义并在 Task 6/7 一致调用;`build/pitch/segN/####.png` 在 Task 7 产出、Task 8 consume;`pitch` 段字段(players/ball/offside_line/arrows/scene_label)在 Task 6 渲染与 Task 9 配置一致。✅

**已知风险:** 动画视觉需抽帧迭代(已在 Task 3/6/11 设检查点);梅西素材来源未定(Task 12 依赖用户提供);90s 时间预算紧(Task 10 设核时长闸)。
