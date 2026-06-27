---
name: football-tactical-analysis-video
description: Use when making a 足球战术解析/战术拆解 video that explains HOW each goal or play happened (mechanism, decision point, off-ball run) from real match footage — native vertical 9:16, 詹俊-style passionate Chinese commentary, per-goal build-up→slow-motion structure, fluent synced subtitles, BGM, for 抖音/视频号/B站. Distinct from highlight/夺冠盘点/数据榜 edits (those use sports-highlight-video).
---

# 足球战术解析视频制作

## 这是什么
一套**配置驱动**的足球**战术解析**(讲清楚"球是怎么进的")竖屏管线:原生 1080×1920,真实画面嵌成中间画面带(上下模糊填满无黑边)+ 詹俊激情解说 + 顶/底文字面板 + 流畅同步字幕 + 自动闪避 BGM + 水印。
一条视频 = 一个 `project.json`(每段定义解说词、画面、叠加层),脚本读它即产出。

与 **sports-highlight-video**(集锦/点评/夺冠盘点 + 数据图形,16:9 为主)是**姊妹管线**。本管线专做**战术拆解**:原生竖屏、每球两段(实时铺垫→进球慢镜头)、解说聚焦"为什么进"。

**核心原则:先 de-roll 英文原解说核实事实再解读;每球两段(铺垫→慢镜头);解说与字幕都要流畅(激情靠语速+重音不靠标点硬断,绝不断外国名);每步抽帧验证。**

**案例复盘**:做“突尼斯1-3荷兰”这类带阵容+战术的成片前,先读 `reference/tunisia-netherlands-case.md`。它沉淀了本次反复返工出来的开场、阵容、BGM、中文球员名和验证规则。

## 何时用 / 不用
- ✅ "某球员帽子戏法怎么踢的""某队怎么破密集防守""某进球战术拆解"这类**讲机制/讲门道**的竖屏短视频
- ✅ 要詹俊式激情解说、烧入流畅字幕
- ❌ 纯集锦堆叠 / 数据榜单 / 夺冠概率条形图 → 用 **sports-highlight-video**

## 两个支柱
1. **战术解读**(先想清楚再写):**先下英文原解说、de-roll 成干净解说稿核实每粒进球的射手与过程**,别只看缩略图墙猜(720p 里球员仅~20px,猜了首作把进球点全错位)。`scripts/deroll_vtt.py` 把滚动自动字幕变成一行一句带时间戳的事实地图。方法、结构、机制词汇、踩点铁律 → 读 `reference/tactical-interpretation.md`。
2. **视频制作**(配置 + 脚本):下面五步。

## 0. 准备:素材 + 依赖 + 时间点
- **依赖**:`pip3 install edge-tts pillow` + `yt-dlp` + `ffmpeg/ffprobe`。脚本用 macOS 字体路径(`lib_overlays_v.py`/`make_watermark.py` 里的 Hiragino/Arial Black),换机器要改。
- **素材**:把整场/集锦 mp4 放 `footage/`,project.json 顶层 `footage_default` 指它。下载整场用嵌入式客户端法绕 PO-token(同 `reference/tactical-interpretation.md` 的 yt-dlp 参数,但**不带** `--skip-download`)。
- **找进球秒数**(顺序很重要):
  1. **先 de-roll 英文解说**当事实地图——`python3 scripts/deroll_vtt.py xxx.en.vtt > build/commentary_clean.txt`,词级时间戳=素材秒数,解说喊出射手/助攻/扑救。**这是定位的主依据**(详见 `reference/tactical-interpretation.md`)。
  2. 再抽缩略图墙微调镜头边界(确认没切进换镜/回放):
     ```bash
     ffmpeg -ss <粗略秒> -i footage/x.mp4 -vf "fps=1/2,scale=320:-1,tile=4x3" -frames:v 1 wall.png
     ```
  英文解说说"第17分钟"≠素材第17分钟(素材未必从开球起),**以 de-roll 解说时间戳 + 抽帧确认的素材秒数为准,别靠墙猜球队/射手**。

## 五步流程(脚本是竖屏专版 `*_v`)
1. **写 `project.json`**:逐段填 `text`(解说)、`footage{start,speed}`、`overlay{layout,...}`。模板用 `example/ned-swe.project.json`(荷兰5-1瑞典成片配置:开场 2 段快过首发、含威胁进攻段、解说全部对齐 de-roll 解说稿、流畅断句)——这是体现最新踩点+流畅经验的范本;`example/tactics.project.json`(梅西帽子戏法)是另一参考。顶层 `pad/grade/theme/watermark` 照模板即可,要调再改。
2. **配音+字幕**:`python3 scripts/make_narration.py project.json` → 解说音频 + **整段重切的流畅字幕**(`fine_cues`:跨 cue 合并、人名保护、消碎片)+ `timeline.json`(各段真实时长)。
3. **叠加层**:`python3 scripts/render_overlays_v.py project.json` → 渲染竖屏透明叠加层帧(文字面板+字幕+水印都烧进去)。
4. **合成**:`python3 scripts/assemble_v.py project.json` → 逐段(画面缩成 1080 宽带嵌 y=384、上下模糊、调色、叠加、解说)合成拼接出 `<name>_vertical.mp4`。
5. **BGM**:`bash scripts/mix_bgm.sh <vertical成片> <bgm.mp3> <最终输出.mp4> <bgm起始秒> <音量>`,例 `… static_bed.mp3 final.mp4 0 0.18`(解说一开口自动闪避)。

**产出落点**:第4步出 `<output_dir>/<name>_vertical.mp4`(纯解说无BGM),第5步 `<最终输出>` 由你命名;中间件在 `build/`(`audio/ subs/segN.srt overlays/ clips/ timeline.json`)。

> 改解说词 → 必须重跑 **2→3→4→5**(时长变,字幕/切片都要重做)。只改叠加层文字 → 重跑 **3→4→5**。**只改 footage start/speed → 只跑 4→5**(`clip` 时长由解说决定不变)。BGM 短素材要先循环成 ≥总长的 bed(见踩坑#5,带命令)。

## 结构 + 叠加层
**结构 = 主题脊梁 + 每球两段**(N 个进球 → N 把钥匙,套同一模式,改 intro/ending 文案即可):
- `intro`/`lineup`:**开头画面必须第一秒有吸引力**。有转播阵容图时,直接切阵容图,不要先放普通比赛镜头;没有阵容图时,用本场 MVP/核心球员高光,别用一般进攻镜头。两队阵容介绍通常各 10~12 秒,只讲阵型特点和战术矛盾,不要念完整首发。
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
- **詹俊激情腔**:`voice` 用 `zh-CN-YunjianNeural`,`rate` `+12%`(紧凑)到 `+24%`(最激情,荷兰5-1瑞典用此档)、`pitch +0~+3Hz`、`volume +8~+12%`。
- **阵容段要更利落**:有两队阵容展示时可把 `rate` 提到 `+30%` 左右;目标是“看阵容特点”,不是拖成赛前发布会。
- **文案要流畅,激情靠语速+重音、不靠标点硬断**(用户反复强调,首作就栽在这):
  - **一句话一口气说完**——主语紧贴动作别拆,写 `布罗比推射破门,一比零!`,**不要**写成 `布罗比!推射破门!`(每个"!"都让 edge-tts 顿一下,听感一卡一卡、字幕还被切成"布罗比"+"推射破门"两块碎片)。
  - 标点只放**真正换气处**:一粒进球的播报当成一条连贯的浪,只在小句之间用逗号、句末用一个"!"。**别在短语中间堆"!"和破折号"——"**。
  - 激情用**更快的语速 + 关键词重音**(进球瞬间喊射手名、比分)来给,而不是靠把句子剁碎。`example/ned-swe.project.json` 的进球段(g1b/g2b…)就是流畅范例。
- **字幕必须流畅、绝不断外国名**:project.json 配 `caption_maxlen:16` 和 `no_split:[外国人名]`;`make_narration.py` 的 `fine_cues` 已做整段重切+人名保护+消碎片;脚本端逗号只放换气处、去破折号、外国名去"·"。**配音后必扫一遍每段 srt**。详见 `reference/gotchas.md` #3。

## 进球切法铁律:解说讲哪个动作,画面就必须拍到那个动作(用户反复返工的痛点)
**进球段画面必须看得见"进球过程":盘带/传中→射门→球进网。不是庆祝、不是远景回放、不是中场倒脚。**
解说说"一脚贴地斩洞穿奥乔亚",画面里就得看见那脚低射钻过门将;看不见=这粒球白讲了(战术片的命就是"讲清楚球怎么进的")。
- **优先切近景慢镜回放**:FOX/转播合集每粒球的结构通常是『实时铺垫 → 实时进球(常是**远景**看不清) → 庆祝 → **近景慢镜回放**』。**最能看清"怎么进的"的,往往是随后那段近景慢镜回放——优先切它**,`speed` 0.5~0.6。
- **用 de-roll 原解说区分"实时进球 / 回放 / 庆祝"三种句子**(`build/commentary_clean.txt`):解说**第一次喊射手名**多半是"进球/庆祝"瞬间;**晚几秒**那句描述动作细节的(如 "past Ochoa, one shot one goal")才是压在**慢镜回放**上的——`start` 锚后者,别锚前者(锚错就切到庆祝/远景=上一版墨西哥那球的坑)。
- 庆祝最多留个尾巴(进球后 1~2 秒),别让庆祝/远景占满整段。
- 慢镜头要 `clip × speed` 秒真实素材,确认起点之后是**连续同一镜头**(别切进转播换镜/下一粒球/广告)。
- 只改 `footage.start`/`speed` → 只重跑 **4→5**(便宜),所以"切错了不好改"不成立。

## 必读:踩坑(`reference/gotchas.md`)
动手前先看,尤其:**①telestrator 定格圈已弃用→改进球慢镜头**;②本机 ffmpeg 无 drawtext→全用 Pillow 烧字;③字幕断句两层治、绝不断外国名;④edge-tts 重试 / BGM 循环成 bed;⑤开场别用普通镜头;⑥BGM 要足球剪辑语境,不是泛史诗;⑦去台标用 `footage.blur`。

## 验证门禁(出片前必过,别拿"跑通了"当验证)
**合成后,声称做完之前,必须逐球过墙——全部进球,不是抽样:**
```bash
python3 scripts/verify_goals.py project.json   # 出 build/gverify/WALL_goals.png:每个进球段沿整段均匀抽6帧拼一行
```
看 `WALL_goals.png`,**逐行问一句:这行看得见『射门→球进网』的过程吗?** 只有庆祝/远景/中场倒脚=切错 → 调该段 `footage.start`/`speed`,重跑 4→5,**再过一次墙**,直到每一行都拍到进球过程。
- 同时:字幕完整成行不断外国名(扫 `build/subs/segN.srt`)、无定格圈残留;`ffprobe` 查各 clip 时长(漏段=总时长偏短)。
- ❌ **不准用这些代替全数过墙**:"assemble 退出码 0"、"抽了 3 个看着对"、"de-roll 时间戳算出来的应该没错"。上一版就是这么栽的:墨西哥那球 start 锚在远景回放上 → 整段没进球画面,用户一眼看出来。**抽样=漏检**。

## 持续优化
v1 从"梅西帽子戏法"沉淀;v2 经"荷兰5-1瑞典"打磨;v3 经"梅西18球"再加一条铁律。三条铁律:**①先 de-roll 英文解说核实事实再切**(`deroll_vtt.py`);**②解说文案要流畅,激情靠语速+重音不靠标点硬断**;**③进球段画面必须拍到"进球过程"(射门→球进网)不是庆祝,优先切近景慢镜回放,出片前用 `verify_goals.py` 全数过墙**(用户最易返工的点:"解说和进球画面要对上"——梅西18球一连返工三轮才达标)。后续可加:转场、词级字幕对齐、多镜头混剪、更多机制 overlay 模板。新增 layout 就在 `lib_overlays_v.py` 加 `layout_xxx` 并在上表补一行。
