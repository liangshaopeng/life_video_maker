---
name: sports-highlight-video
description: Use when creating a narrated, captioned sports analysis or highlight video (球员/球队点评、夺冠盘点、赛事分析) from real match footage — with passionate Chinese commentary, animated data overlays (big numbers, bar charts, lower-third chips), synced subtitles, background music, in 16:9 or vertical 9:16. Use when the user wants a 抖音/视频号/B站-style football/basketball edit video.
---

# 体育剪辑视频制作

## 这是什么
一套**配置驱动**的体育分析/集锦视频管线:真实比赛画面打底 + 云健激情解说 + 数据叠加层(大数字计数、条形图、标签卡)+ 逐句同步字幕 + 自动闪避的 BGM,可出 16:9 或 9:16 竖屏。
一条视频 = 一个 `project.json`(定义每段的解说词、画面、叠加层),脚本读它即可产出。

**核心原则:画面真实、解说要燃、数据醒目、每步抽帧验证。**

## 何时用
- 做"X 队夺冠概率/X 球员分析/赛事盘点"这类**解说+集锦+数据**的短视频
- 需要中文激情解说(解说员腔)、烧入字幕、数据图形、燃向 BGM
- 要发抖音/视频号(竖屏)或 B站(横屏)

## 五步流程
1. **写 `project.json`**:逐段填解说词 `text`、画面 `footage{src,start,speed,blur?}`、叠加层 `overlay{layout,...}`。先用 `example/argentina-2026.project.json` 当模板。
2. **配音+字幕**:`python3 scripts/make_narration.py project.json` → 生成解说音频、细分短句字幕、`timeline.json`(各段真实时长)。
3. **叠加层**:`python3 scripts/render_overlays.py project.json` → 按时间轴渲染透明叠加层帧(图形+字幕都烧进去)。
4. **合成(可含局部虚化)**:`python3 scripts/assemble.py project.json` → 逐段(画面+调色+叠加+解说)合成并拼接出 `<name>_16x9.mp4`。素材自带台标/比分牌 → 给该段 footage 加 `blur`(见下「去台标」)。
5. **BGM + 水印 + 竖屏**(按此序):
   - `bash scripts/mix_bgm.sh <16x9> <bgm.mp3> <out> [起始][音量]`(解说一开口自动闪避;音乐盖过解说就降音量+加大 ratio,见技巧)。
   - 作者水印(可选):`python3 scripts/make_watermark.py "网名" build/watermark.png` → `bash scripts/add_watermark.sh <带BGM> build/watermark.png <out> br`。
   - `bash scripts/make_vertical.sh <in> <out_vertical>`(水印/虚化都会跟着内容带进竖版)。

> 改了解说词 → 必须重跑 2→3→4→5(时长变了,叠加层和切片都要重做)。只改叠加层文字/画面/blur → 重跑 3→4→5。

## 叠加层组件(overlay.layout)
| layout | 用途 | 关键参数 |
|---|---|---|
| `title` | 开场大标题 | title, subtitle, sup |
| `chips` | 一行标签卡(底气/实力) | kicker, chips[] |
| `namelist` | 左侧滑入名单(新生代) | kicker, names[] |
| `stat` | 右侧大数字计数(年龄/身价) | kicker, count_to, unit, label_sup, chips[] |
| `spotlight` | 人物聚光(决赛先生/MVP) | kicker, big, name, chips[] |
| `bars` | 概率/数据条形图 | kicker, top_chips[], big, bars[[名,值]], highlight, note |
| `end` | 收尾反问钩子 | title, subtitle |
组件源码与新增方法见 `scripts/lib_overlays.py`(主题色由 project.json 的 `theme` 覆盖)。

## 去台标/比分牌(局部虚化)
下载的集锦常烧死了比分牌(左上)、对阵标"X VS Y"(右上)、电视台标、搬运号水印。会和小标题打架、显廉价。
**给该段 footage 加 `blur`,在烧字幕前对这些矩形做高斯模糊**(1920×1080 坐标 `[x,y,w,h]`):
```json
"footage": { "src": "footage/x.mp4", "start": 128,
  "blur": [[0,0,880,160],[1175,0,745,185]] }
```
全局强度顶层加 `"blur_sigma": 18`。要点:**分左上+右上两个角块、中间留空**(别全宽);框盖全文字;
sigma 够大(粗体台标≥18 才不可读)。左上角块糊掉后正好给 kicker 腾干净背景。详见 gotchas.md #11。

## 必读:踩坑
动手前先看 **`reference/gotchas.md`**(都是真撞过的墙),尤其:
- **本机 ffmpeg 多半没 libass/drawtext** → 字幕、图形、**水印**全用 Pillow 烧成图再 overlay,别用 ffmpeg 字幕/绘字滤镜。
- **YouTube 下载**靠嵌入式客户端法绕 PO-token(`player_client=tv_embedded,web_embedded,android_vr,mweb` + 整段下,不要 `--download-sections`)。Bilibili 基本下不动。
- 拼接循环用 `len(segments)` 动态遍历(写死段数会漏掉收尾段)。
- 重渲叠加层前清空目录(防旧帧残留)。
- 素材自带台标/水印 → 局部虚化(#11);别全宽别太薄,sigma 要够。
素材/音乐获取见 `reference/footage-and-music.md`。

## 关键技巧
- **选镜头**:整段素材用缩略图墙(`tile=4x3`)定位进球/庆祝/举杯/特写,把时间点填进 `footage.start`。判别球队的视频避开对手特写。
- **慢镜头**:`footage.speed` 设 0.5 突出技术细节(如"假动作骗门将")。
- **解说要燃**:`voice` 用 `zh-CN-YunjianNeural` + rate/pitch/volume 上调;文案用解说腔(口头禅+名字爆发+短句感叹+反问)。
- **字幕断句要自然**:配音后**必扫一遍每段 srt**——别切碎人名、Latin 词(DeepSeek/FIFA)、别让连接词(会不会)落单。靠改标点控制(去逗号合并 / `!` 分组 / 缩短含 Latin 小句),改完重跑再扫。详见 gotchas.md #13。
- **验证**:每次合成后抽关键帧肉眼看(叠加/字幕/慢放对不对),`ffprobe` 查各 clip 时长(漏段=总时长偏短)。

## 真·竖屏(可选升级)
当前 `make_vertical.sh` 是"画面居中+上下模糊填满"(保内容、无黑边)。要画面**满屏铺开**,需把
`lib_overlays.py` 的 `W,H` 改 1080×1920、各 layout 重排为竖向(图形移到画面上/下面板),并把素材裁成竖屏。属较大改造,按需做。

## 持续优化
这是 v1。后续可加的组件/能力:转场特效、战术箭头/连线标注、多素材混剪(一段内多镜头)、
真·竖屏布局、词级字幕对齐(forced alignment)、更多主题配色。新增 layout 就在 `lib_overlays.py` 加个
`layout_xxx` 函数并注册到 `LAYOUTS`,再在 SKILL.md 表格补一行。
