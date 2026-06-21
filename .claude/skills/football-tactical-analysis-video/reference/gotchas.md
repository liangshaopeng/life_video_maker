# 制作踩坑(都是真撞过的墙)

## 1. telestrator(定格 + 战术圈)已弃用 → 改进球慢镜头
720p 宽转播镜头球员仅~20px,**做不到像素级精确圈人**,圈偏了显廉价、用户会嫌"画得不准"。决策点的呈现**改用进球慢镜头**(speed≈0.55)。
`lib_overlays_v.py` 里的 `telestrator` layout / `draw_marks`、`verify_marks.py`(抽 freeze 帧叠标注核验圈位)、`gridframe.py`(叠坐标网格读 telestrator 坐标)都还在,**真要复活标注再用**;否则 project.json 不要写 `footage.freeze` / `layout:telestrator` / `marks`。

## 2. 本机 ffmpeg 没 drawtext/libass
所有文字(标题面板、字幕、水印)用 **Pillow 烧成透明 PNG 再 overlay**。别用 ffmpeg 的字幕/drawtext 滤镜(多半没编译进去)。

## 3. 字幕断句要顺、外国名绝不能断(硬要求)
- **现象**:碎片满屏(3-4 字小块如"到这儿/而梅西")、孤字吊行尾("…地点!这"+"就是…")、外国名被切("尼科·冈萨雷斯"断开)→ 显业余、听感卡。
- **两层一起治**:
  - **脚本层**:逗号只放自然换气处,别堆破折号"——"(edge-tts 每个标点都停顿→碎);外国名去掉"·"(写"尼科冈萨雷斯")避免 TTS 停顿;名字要带上下文别孤立成块。
  - **字幕层**:`make_narration.py` 的 `fine_cues()` 已实现——**整段文本重切**(跨 edge-tts 原始 cue 边界,消孤字)+ **贪心合并小碎块**(<4字并入邻行)+ **`no_split` 人名保护**(切点落名字内部→回退到词首)+ **承接字(就/是/的/了…)不留行首**。
  - project.json 配 `caption_maxlen:16`、`no_split:[...]`:**把片中会出现的所有外国人名都列进去**(射手、助攻、双方球队、教练),写**去"·"**的形式。漏一个就可能被切。
- **配音后必扫一遍每段 `build/subs/segN.srt`**,确认没断名、没碎片、没孤字(没有专门检测脚本,靠肉眼过一遍)。

## 4. 慢镜头素材跑量(clip 是算出来的,先渲后验)
每段时长 `clip` = 该段解说音频时长 + `pad`,由 `make_narration.py` 自动算进 `timeline.json`,**你不在 project.json 手写 clip**,所以渲染前算不准确切跑量。慢镜头段实际消耗 `clip × speed` 秒真实素材;build-up 段(speed 1.0)消耗 `clip` 秒。
**务实做法**:`start` 先按缩略图墙估,渲完抽帧看切得对不对——不够/切进换镜就调 `start`/`speed`,**只改这俩只需重跑 4→5**(便宜)。确认起点之后是连续比赛画面(别切进转播换镜/回放角度/广告)。build-up 起点要让进球落在该段后段(慢镜头当回放彩蛋)。

## 5. edge-tts 偶发失败 / BGM 必须循环成 bed
- `make_narration.py` 已内置 **6 次重试 + 坏 mp3 体积校验**(<1200 字节判失败重试)。
- BGM 偏好:冷静悬念/极简([Incompetech](https://incompetech.com) 的 *Static Motion* 等),CC 协议;音量 ~0.18 垫底,sidechain 自动闪避解说。
- `mix_bgm.sh` **不会自动循环 BGM**:短素材(如 15s 的《Static Motion》)要**先循环成 ≥成片总长的 bed**,再 mix,否则音乐中途断掉。循环命令(circle 到 180s):
  ```bash
  ffmpeg -stream_loop -1 -i bgm/Static_Motion.mp3 -t 180 -c copy bgm/static_bed.mp3
  ```
- `mix_bgm.sh` 参数:`mix_bgm.sh <输入成片> <bgm.mp3> <输出.mp4> [bgm起始秒=45] [bgm音量=0.42]`。战术片常用 `0 0.18`(从头播、垫低)。
- 成片总长用 `ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 <vertical.mp4>` 查,据此定 bed 长度。

## 6. 拼接与重渲
- `assemble_v.py` 用 `len(segments)` 动态遍历(别写死段数,会漏收尾段)。
- 重渲叠加层前清空 `build/overlays`(防旧帧残留;`render_overlays_v.py` 已自动 rmtree)。
- 改了段数后,旧 `build/` 里多出的 `audio/overlays/clips/segN` 目录无害(脚本只遍历当前 segments),混淆时可手动清。

## 7. 去台标 / 比分牌(局部虚化)
下载素材常烧死比分牌(左上)、台标、搬运号水印。给该段 `footage.blur:[[x,y,w,h],...]`(**画面带内坐标 0..1080 × 0..608**)做局部高斯模糊,顶层 `blur_sigma` 调强度(粗体台标 sigma≥16 才不可读)。注意坐标是画面带内的,不是整张 1080×1920。

## 8. 字体路径(macOS)
`lib_overlays_v.py` / `make_watermark.py` 用 `/System/Library/Fonts/Hiragino Sans GB.ttc`(index2=W6 粗,index0=常规)和 `Arial Black.ttf`(大号拉丁数字)。换机器要改这两个路径。
