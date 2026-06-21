# 踩坑与解决(本管线的硬核经验)

这些都是实战中真撞过的墙,不知道会卡很久。

## 1. 本机 ffmpeg 常缺 libass / drawtext / ass 滤镜
homebrew 某些 ffmpeg bottle 没编译这些。后果:`subtitles=`、`ass=`、`drawtext=` 全部报
`No such filter` / `Filter not found` / `No option name`。
**解决:不要用 ffmpeg 烧字幕/画字。** 用 Pillow 把字幕和所有图形画进透明叠加层(lib_overlays.py),
ffmpeg 只负责 overlay 合成。先验证:`ffmpeg -filters | grep -E 'subtitles|drawtext|ass'`。
混音用的 `sidechaincompress`/`loudnorm` 通常在,但也要先 `ffmpeg -filters` 确认。

## 2. YouTube 下载:PO-token 墙 + cookie 轮换
- 直接 yt-dlp 下载常报 `Sign in to confirm you're not a bot` / `403 Forbidden` / `Requested format is not available`。
- **可行解:嵌入式客户端 + 整段原生下载**(不要 `--download-sections`,它走 ffmpeg 直接开流会丢签名):
  ```
  yt-dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" \
         -f "298/137/best[height<=1080]" -o out.%(ext)s URL
  ```
  能拿到 itag 18(360p 渐进式,最稳)和 DASH 的 720p/1080p(137/298 等,纯视频,无需音频—我们用解说配音)。
- HLS(m3u8)能下到 1080p 但 `--download-sections` 会失败/卡 0 字节;要整段下完本地再切。
- **cookie 会被轮换失效**:从普通浏览器窗口导出的 YouTube cookie 几分钟就失效。要用就**无痕窗口登录→导出→立刻用**;但即使有 cookie,媒体数据仍可能被 PO-token 403——嵌入式客户端法更可靠。
- **Bilibili**:对 yt-dlp 基本 412 反爬,本环境下不下来;让用户自己下文件丢进 footage/。

## 3. 字体(macOS)
- 中文:`/System/Library/Fonts/Hiragino Sans GB.ttc`,**ttc 索引 0=W3(常规)、2=W6(粗体)**。
  注意没有 PingFang.ttc 在老路径;Hiragino Sans GB 一定有。
- 大号拉丁数字:`/System/Library/Fonts/Supplemental/Arial Black.ttf`(冲击力强,适合比分/年龄/概率)。

## 4. 解说要"燃":edge-tts 音色与参数
- 体育激情首选 `zh-CN-YunjianNeural`(Male / Sports / Passion)。`say` 命令是机器音,别用。
- 三个杠杆:`--rate +20%`(语速)、`--pitch +16Hz`(音高上扬=亢奋)、`--volume +15%`(饱满)。
- 文案按"解说腔"写:招牌口头禅(如"朋友们")、名字爆发("封王啦!")、短句+感叹、反问钩子。
- **不要克隆真实解说员本人的声音**(deepfake 真人声线)——只复刻"风格"。

## 5. 字幕:edge-tts 给的是整句,太长 → 按标点细分
edge-tts `--write-subtitles` 输出句级 cue(一句一条,很长)。在 make_narration 里按标点
(,。!?、)拆成 ≤12 字短句、按字数比例分配时间窗,字幕才不挤。

## 6. 段数硬编码 bug(真栽过)
assemble 的拼接循环若写死 `range(1,7)`,加到 7 段时会**漏掉最后一段**(收尾被吞,且不报错)。
**永远用 `len(segments)` 动态遍历。** 本 skill 的脚本已修。

## 7. 叠加层旧帧残留污染
段时长变短后重渲,旧的高位帧(如 0371.png)还在目录里,ffmpeg 当序列会读进去导致时长错乱。
**每次重渲前清空 overlays 目录**(render_overlays.py 已内置 shutil.rmtree)。

## 8. 慢放(决赛先生/MVP 镜头)
`speed<1`:截取 `clip*speed` 秒素材,`setpts=(1/speed)*PTS` 拉长回 clip 秒。重度慢放(0.5x)
适合突出技术细节(如"假动作骗门将")。注意 `start + clip*speed` 不能超过素材时长。
50fps 源做慢放帧够用;判别球员/球队时避开对手特写。

## 9. 选镜头:缩略图墙
20-35 分钟的素材里找"进球/庆祝/举杯/特写",用 ffmpeg 拼缩略图墙快速定位:
```
ffmpeg -ss T -i src.mp4 -frames:v 1 -vf scale=480:270 build/dm/%02d.jpg   # 多个时间点
ffmpeg -i "build/dm/%02d.jpg" -vf tile=4x3 -frames:v 1 grid.jpg
```
注意 `drawtext` 缺失,标时间戳得靠"位置=哪个时间点"自己记。

## 10. 验证:每一步抽帧看
合成后务必抽关键帧肉眼验证(叠加层/字幕/画面是否对齐、慢放是否到位):
```
ffmpeg -ss 50 -i final.mp4 -frames:v 1 check.jpg
```
还要 `volumedetect` 确认音轨非静音、`ffprobe` 确认每个 clip 时长符合预期(漏段会体现为总时长偏短)。

## 11. 素材自带台标/比分牌/水印 → 局部虚化(别全宽、别太厚)
下载的集锦/转播素材常烧死了 **比分牌(左上)、对阵标"X VS Y"(右上)、电视台标(FIFA TV)、
搬运号水印(如 luly football)**。它们会和我们的小标题(kicker)打架、显廉价。
**解决:在 assemble 里对这些矩形做局部高斯模糊(烧字幕之前)。** project.json 每段 footage 加:
```json
"footage": { "src": "...", "start": 128,
  "blur": [[0,0,880,160],[1175,0,745,185]] }   // 1920x1080 坐标 [x,y,w,h]
```
全局强度 `"blur_sigma": 18`(粗体台标要够大才糊得不可读)。`assemble.py` 已内置(无 blur 键=原行为)。
**经验(真调过几轮)**:
- **别整条全宽虚化** —— 顶部中间通常是干净看台,糊了又厚又难看。按 **左上比分牌 + 右上对阵标
  两个角块** 分开,中间留空。
- **框要盖全文字**:比分牌右侧的比分/时间、对阵标的国旗都容易露边,放大抽帧(crop 该角)逐一确认。
- **sigma 别太小**:12 糊不掉粗体台标(还能读出 FRANCE VS),18 左右才彻底不可读。
- **顺带好处**:左上角块糊成柔光,正好给 kicker 腾出干净背景,标题不再和台标重叠。
验证:`ffmpeg -ss T -i final.mp4 -frames:v 1 -vf "crop=900:240:0:0" tl.jpg` 放大看角落,文字应不可读。

## 12. 作者水印:方形徽标(PNG overlay,非 drawtext)
`scripts/make_watermark.py "网名" build/watermark.png` 生成**方形印章**(深蓝底+金边+白字,4字自动2x2),
再 `scripts/add_watermark.sh <成片> build/watermark.png <输出> br` 叠到右下角。
顺序:**assemble → mix_bgm → add_watermark → make_vertical**(水印叠在 16:9 上,竖版会跟着内容带一起带)。
别用 ffmpeg `drawtext`(本机多半没有,见 #1)。

## 13. 字幕断句要自然:别切碎人名/词,连接词别落单
字幕由 `split_fine` 按标点切片 → 按 ≤12 字合并 → 超长再硬切。三类生硬断句(真栽过,用户会挑):
- **Latin 词被腰斩**:`DeepSeek/FIFA/PSG` 每个字母都算 1 字,容易把一行撑爆,硬切时切进词中(`根据DeepSeek的谨` / `慎推算`)。
  `make_narration._ascii_safe_cut` 已护住"不切进 ASCII 词";但更稳的是**让含 Latin 词的小句 ≤~12 显示字**(如 `由DeepSeek谨慎推算`=12,一行装下)。
- **连接词落单**:`会不会` 后面带逗号 → `这支法国,会不会,`(8字)+`反而更可怕`(5)=13 超限,把后半句甩成下一条。
  **去掉连接词后的逗号**,让它和后半句并成一条(`会不会反而更可怕`)。
- **名单里位置标签拖尾**:`锋线,姆巴佩、登贝莱、特奥;中场,…` 会切成 `…特奥;中场`(看着像特奥踢中场)。
  **每个位置组用 `!` 结尾**(`…特奥!中场,…`),`!` 给视觉分隔;名字本身保持完整。
**关键认知**:edge-tts 的 cue 边界是按**朗读时值**切的,不完全跟标点走 —— 所以不能纯靠改标点精确预测断句。
**正确流程**:改完文案 → 跑 `make_narration` → **立刻 dump 每段 srt 肉眼扫一遍**(看有没有切碎的人名/词、落单的连接词),
不满意就调标点(去逗号合并 / 用 ! 分组 / 缩短含 Latin 的小句)→ 重跑 → 再扫,直到顺。
```
for i in $(seq 1 N); do echo "== seg$i =="; grep -v '^[0-9]*$' build/subs/seg$i.srt | grep -v '\-\->' | grep -v '^$'; done
```
