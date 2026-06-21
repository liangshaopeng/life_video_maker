---
name: football-tactical-analysis-video
description: Use when making a 足球战术解析/战术拆解 video that explains HOW each goal or play happened (mechanism, decision point, off-ball run) from real match footage — native vertical 9:16, 詹俊-style passionate Chinese commentary, per-goal build-up→slow-motion structure, fluent synced subtitles, BGM, for 抖音/视频号/B站. Distinct from highlight/夺冠盘点/数据榜 edits (those use sports-highlight-video).
---

# 足球战术解析视频制作

## 这是什么
一套**配置驱动**的足球**战术解析**(讲清楚"球是怎么进的")竖屏管线:原生 1080×1920,真实画面嵌成中间画面带(上下模糊填满无黑边)+ 詹俊激情解说 + 顶/底文字面板 + 流畅同步字幕 + 自动闪避 BGM + 水印。
一条视频 = 一个 `project.json`(每段定义解说词、画面、叠加层),脚本读它即产出。

与 **sports-highlight-video**(集锦/点评/夺冠盘点 + 数据图形,16:9 为主)是**姊妹管线**。本管线专做**战术拆解**:原生竖屏、每球两段(实时铺垫→进球慢镜头)、解说聚焦"为什么进"。

**核心原则:先用英文原解说核实事实再解读;每球两段(铺垫→慢镜头);字幕要顺、绝不断外国名;每步抽帧验证。**

## 何时用 / 不用
- ✅ "某球员帽子戏法怎么踢的""某队怎么破密集防守""某进球战术拆解"这类**讲机制/讲门道**的竖屏短视频
- ✅ 要詹俊式激情解说、烧入流畅字幕
- ❌ 纯集锦堆叠 / 数据榜单 / 夺冠概率条形图 → 用 **sports-highlight-video**

## 两个支柱
1. **战术解读**(先想清楚再写):**先下英文原解说核实射手与过程**,别只看画面猜(720p 里球员仅~20px,极易判错)。方法、结构、机制词汇 → 读 `reference/tactical-interpretation.md`。
2. **视频制作**(配置 + 脚本):下面五步。

## 0. 准备:素材 + 依赖 + 时间点
- **依赖**:`pip3 install edge-tts pillow` + `yt-dlp` + `ffmpeg/ffprobe`。脚本用 macOS 字体路径(`lib_overlays_v.py`/`make_watermark.py` 里的 Hiragino/Arial Black),换机器要改。
- **素材**:把整场/集锦 mp4 放 `footage/`,project.json 顶层 `footage_default` 指它。下载整场用嵌入式客户端法绕 PO-token(同 `reference/tactical-interpretation.md` 的 yt-dlp 参数,但**不带** `--skip-download`)。
- **找进球秒数**:先抽缩略图墙定位镜头(填进 `footage.start`):
  ```bash
  ffmpeg -ss <粗略秒> -i footage/x.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 wall.png
  ```
  英文解说说"第17分钟"≠素材第17分钟(素材未必从开球起),**以缩略图墙/抽帧定位的素材秒数为准**。

## 五步流程(脚本是竖屏专版 `*_v`)
1. **写 `project.json`**:逐段填 `text`(解说)、`footage{start,speed}`、`overlay{layout,...}`。拿 `example/tactics.project.json`(梅西帽子戏法成片配置)当模板;顶层 `pad/grade/theme/watermark` 照模板即可,要调再改。
2. **配音+字幕**:`python3 scripts/make_narration.py project.json` → 解说音频 + **整段重切的流畅字幕**(`fine_cues`:跨 cue 合并、人名保护、消碎片)+ `timeline.json`(各段真实时长)。
3. **叠加层**:`python3 scripts/render_overlays_v.py project.json` → 渲染竖屏透明叠加层帧(文字面板+字幕+水印都烧进去)。
4. **合成**:`python3 scripts/assemble_v.py project.json` → 逐段(画面缩成 1080 宽带嵌 y=384、上下模糊、调色、叠加、解说)合成拼接出 `<name>_vertical.mp4`。
5. **BGM**:`bash scripts/mix_bgm.sh <vertical成片> <bgm.mp3> <最终输出.mp4> <bgm起始秒> <音量>`,例 `… static_bed.mp3 final.mp4 0 0.18`(解说一开口自动闪避)。

**产出落点**:第4步出 `<output_dir>/<name>_vertical.mp4`(纯解说无BGM),第5步 `<最终输出>` 由你命名;中间件在 `build/`(`audio/ subs/segN.srt overlays/ clips/ timeline.json`)。

> 改解说词 → 必须重跑 **2→3→4→5**(时长变,字幕/切片都要重做)。只改叠加层文字 → 重跑 **3→4→5**。**只改 footage start/speed → 只跑 4→5**(`clip` 时长由解说决定不变)。BGM 短素材要先循环成 ≥总长的 bed(见踩坑#5,带命令)。

## 结构 + 叠加层
**结构 = 主题脊梁 + 每球两段**(N 个进球 → N 把钥匙,套同一模式,改 intro/ending 文案即可):
- `intro`(`title` 全屏,speed 1.0,抛出主题,如"三种方式打穿大巴";两球就是"两把钥匙")
- 每个进球**两段**:**①拆解·导火索**(`beat`,实时 build-up speed 1.0,口播把决策点讲掉)→ **②进球**(`beat`,**直接切进球慢镜头** speed≈0.55,喊出终结并给这粒球命名"第N把钥匙/机制")
- `ending`(`end` 全屏,可略放慢 speed≈0.85 配收尾画面,回扣主题)

| layout | 用途 | 关键参数 |
|---|---|---|
| `title` | 开场大标题 | title(可 `\n` 两行), subtitle, sup |
| `beat` | 每球的拆解段 / 进球段 | phase, idx, accent, title, kicker, points[] |
| `end` | 收尾 | title, subtitle |
| ~~`telestrator`~~ | **已弃用·勿写**(圈不准) | 见踩坑#1 |

字段语义(都只是**显示用文本**,非枚举,渲染不靠它分支):`phase`=胶囊标签(拆解·导火索/进球),`idx`=进球编号(G1/G2…),`accent`=该段主题色取 `theme` 的键(惯例:拆解段 `sky`、进球段 `good`、强调 `gold`),`title`/`kicker`=大标题/副行,`points[]`=底部 1~3 条短要点(每条≤~12字)。组件源码 `scripts/lib_overlays_v.py`(主题色由 project.json 的 `theme` 覆盖)。

## 解说 + 字幕(关键)
- **詹俊激情腔**:`voice` 用 `zh-CN-YunjianNeural`,`rate` 约 `+12%`(紧凑)、`pitch +0Hz`、`volume +8%`;文案短句、play-by-play 喊出来("梅西推射破门!")。
- **字幕必须流畅、绝不断外国名**:project.json 配 `caption_maxlen:16` 和 `no_split:[外国人名]`;`make_narration.py` 的 `fine_cues` 已做整段重切+人名保护+消碎片;脚本端逗号只放换气处、去破折号、外国名去"·"。**配音后必扫一遍每段 srt**。详见 `reference/gotchas.md` #3。

## 慢镜头切法
- 进球段 `footage.speed` 0.5~0.6,`start` 用**英文解说时间戳**定位的进球瞬间;build-up 段实时(speed 1.0),起点让进球落在该段后段,慢镜头当回放彩蛋。
- 慢镜头需要 `clip × speed` 秒真实素材,确认起点之后素材够长(别切进转播换镜)。

## 必读:踩坑(`reference/gotchas.md`)
动手前先看,尤其:**①telestrator 定格圈已弃用→改进球慢镜头**;②本机 ffmpeg 无 drawtext→全用 Pillow 烧字;③字幕断句两层治、绝不断外国名;④edge-tts 重试 / BGM 循环成 bed;⑤去台标用 `footage.blur`。

## 验证
每次合成后抽关键帧肉眼看:慢镜头切得对、字幕完整成行不断名、无定格圈残留;`ffprobe` 查各 clip 时长(漏段=总时长偏短)。

## 持续优化
这是从"梅西帽子戏法"片沉淀的 v1。后续可加:转场、词级字幕对齐、多镜头混剪、更多机制 overlay 模板。新增 layout 就在 `lib_overlays_v.py` 加 `layout_xxx` 并在上表补一行。
