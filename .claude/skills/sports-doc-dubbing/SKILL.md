---
name: sports-doc-dubbing
description: Use when 把英文/外语体育访谈·纪录片·解说"译制"成中文配音视频——尤其双人对话要给每个说话人配不同音色(声纹 diarization 双音色)、配音与原片时间轴同步、烧中文字幕、原声压低垫底。触发词:译制 / 翻译视频 / 中文配音 / 双人配音 / 换音色 / 给采访配音,且素材是真人长时间讲话(非集锦剪辑)。
---

# 体育纪录片译制(双人双音色)

## 这是什么
把一段**真人讲话的外语体育视频**(访谈/纪录片/解说)译制成中文配音片:原片画面照旧 → 中文配音盖上 → 原声压低垫底 → 烧中文字幕。
亮点是**双人对话双音色**:用声纹分段(diarization)判定每句谁说,给两个说话人各配一个 edge-tts 音色,做出真正"一来一回"的对话感,而非一个嗓子自问自答。
区别于 `sports-highlight-video`(那是自己写解说的集锦剪辑);这里是**忠实译制别人说的话**。

**核心原则:谁说哪句靠声纹+原文交叉定、配音锚定原片时间轴、edge-tts 缓存必须校验有效性。**

## 何时用
- 把油管等的英文体育访谈/前瞻/纪录片**翻译配音**成中文发布
- 双人(或多人)对话,想让听感像两个人聊天 → 每人不同音色
- 需要中文字幕烧入、配音跟画面节奏对得上

## 七步流程(工作目录:`source/` `build/`)
1. **下载**:`yt-dlp` 取原片 → `source/original.mp4`;抽 16k 单声道 → `source/audio16k.wav`(下载绕 PO-token 见 gotchas)。
2. **转写**:`python3 scripts/transcribe.py large-v3`(faster-whisper)→ `build/transcript_en.json`。
3. **合句**:`python3 scripts/merge_segments.py` → `build/chunks_en.json`([{id,start,end,en}],句子级,作翻译/锚点单元)。
4. **本地化**(创作):仿 `example/localize_cn.py` 把每个 chunk **意译改写**成中文口语(不是逐字直译),用 chunk id 当时间锚点 → `build/segments_cn.json`([{start,end,cn}])。
5. **说话人判定(双音色核心,见下)** → `build/segments_spk.json`([{start,end,turns:[{spk,text}]}])。
6. **配音+字幕**:`python3 scripts/make_dub.py` → `build/dub.wav` + `build/cues.json`(逐轮次双音色 TTS,段锚定原片时间轴)。
7. **渲字幕→合成**:`python3 scripts/render_subs.py`(Pillow 烧字幕帧)→ `bash scripts/compose.sh`(画面+字幕+配音+原声垫底+loudnorm)→ 成片。

> 改本地化文案 → 重跑 5→6→7。只改说话人标注 → 重跑 6→7。先 `bash scripts/preview.sh <起><时长>` 抽段验,OK 再 compose 整片。

**数据约定**(自带转写/翻译时也得对齐这些 schema):`chunks_en.json` 的 `id` 必须**连续、从 0 开始**(`relabel_spk.py` 按 `id` 位置索引 `CHUNK_SEM` 并断言长度相等);`segments_cn.json` 每段 `cn` 里**说话人切换处插 `——`**(脚本按 `—+` 切片),同人停顿也可用 `——`。`CHUNK_SEM` 别从零标——见 `relabel_spk.py` 注释,用 `chunks_spk.json`(声纹草稿)当底改错的。`compose.sh` 的输出文件名是写死的,按你的片名改。

## 说话人判定(这步决定成败)
**别用纯文本猜谁说**(短应答"对/行/Okay"必标反)。用声纹,且和原文交叉校正:
1. `python3 scripts/diarize_spk.py`:Resemblyzer 连续声纹嵌入(**绝不裁静音、保原片时间轴**)+ kmeans2 分 2 簇,开场 [0,8s] 定为说话人 H。每段按 `——` 切片落时间窗、多数票定 H/C、合并同人片成轮次,出 `segments_spk.json` + 人读复核稿 `build/speaker_review.txt`(低置信度标 ⚠)。**不要求 HF token**(比 pyannote 轻)。
2. **快问快答区声纹会漏切**(报对阵=主持、紧跟的短选择句被并进主持)。要更准:`relabel_spk.py` 用 **verbatim 英文逐 chunk 人工标说话人**(`CHUNK_SEM`)做交叉校正——英文为准、声纹兜底;因每个英文 chunk 有独立时间戳,投影到中文段能借相邻 chunk 自动切对。
3. 复核 `speaker_review.txt`,⚠ 处人工定夺。
4. **音色映射**(`make_dub.py` 顶部 `VOICE`):本片用 `H=zh-CN-YunxiNeural`(云希,年轻)/`C=zh-CN-YunjianNeural`(云健,成熟),对比清晰。**edge-tts 不能克隆真人**,只能挑风格接近的现成音色当替身。

## 必读:踩坑
动手前看 **`reference/gotchas.md`**,尤其:
- **edge-tts 偶发写"坏 mp3"**(非空但 ffprobe 解析不了)→ 缓存判断必须用 `valid_mp3()`(能 ffprobe 出正时长),只查文件存在会**死循环卡同一句**;tts 要重试+退避+轻微限速。
- **声纹必须保时间轴**:不裁静音,否则 diarization 时间和原片对不上。
- 本机 ffmpeg 多半无 libass → 字幕用 Pillow 烧图再 overlay。
- edge-tts / faster-whisper / 装 resemblyzer 都要联网;命令行无网时让用户用 `!` 跑。

## 关键技巧
- **本地化要"老友唠嗑"腔**:连接词串碎拍、球员用中文圈外号梗、预测结论保持准确(见 example/localize_cn.py 注释)。
- **配音锚定**:段作对齐单位,放不下先借前面静音提前开口(LOOKBACK),再限幅 atempo 压缩(≤1.5),靠后续静音追回漂移——`make_dub.py` 已实现。
- **字幕断句**:别切碎外国人名/Latin 词;`make_dub.py` 的 `split_fine` 按标点+字数细分,`——` 作同人停顿断点。
- **验证**:`ffprobe` 查配音轨总时长≈原片;抽快问快答段听换人是否落对人头。
