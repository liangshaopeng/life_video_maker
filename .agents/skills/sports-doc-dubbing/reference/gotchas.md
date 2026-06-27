# 译制管线踩坑(都是真撞过的墙)

## 1. edge-tts 会写"坏 mp3",缓存必须校验有效性 ★最坑
edge-tts 偶发返回 403 / 空音频 / 半截数据,会在目标路径写一个**非 0 字节但 ffprobe 解析不了**的 mp3。
- 若缓存判断是 `if not os.path.exists(mp3)` 或只查 `getsize>0`,坏文件会被当成"已生成"**永远跳过**,后续 `ffprobe` 取时长每次都崩在同一句 → 重跑 N 次都卡死、且 `tts` 根本没被重新调用。
- 正解:`valid_mp3(p)` = 能被 ffprobe 解析出 >0 时长才算有效;缺失**或损坏**都重生成(`make_dub.py` 已实现)。
- `tts()` 还要:生成后校验,无效就删了重试;**重试+退避**(403 多为瞬时);成功后 `sleep(0.1)` 轻微限速(连发几百次易触发限流)。
- 现象关键词:`Failed to find two consecutive MPEG audio frames` / `Invalid data found` / 重跑卡同一句。

## 2. 声纹 diarization 必须保原片时间轴
Resemblyzer/任何 diarization 都**不能先裁静音**(`preprocess_wav` 会裁)。一裁,声纹的时间和原片就错位,后面按时间窗映射说话人全乱。
直接 `librosa.load(sr=16000)` 整段喂、只做振幅归一。`embed_utterance(return_partials=True)` 的 `wav_splits` 才能正确换算成原片秒。

## 3. 纯声纹在"快问快答区"会系统性漏切 → 用原文交叉校正
淘汰赛/连续问答段:格式常是"报对阵(主持)→ 紧跟一句很短的选择(嘉宾)"。短选择句 2~3 秒、声纹窗少,**会被并进主持簇**(漏掉换人)。
- 别只信声纹 + "扫一眼"。`relabel_spk.py` 用 **verbatim 英文逐 chunk 人工标说话人**,英文为准、声纹兜底。
- 为什么有效:每个英文 chunk 有**独立时间戳**,投影到中文段的时间窗时,相邻 chunk 能把声纹并掉的边界**自动切回来**。
- 嫌标注重:至少重点核对 `speaker_review.txt` 里淘汰赛/快问答区 + 所有 ⚠。

## 4. 说话人簇 → 角色 的对应
`diarize_spk.py` 用开场 `[0,8s]` 那簇定为 H(访谈开场基本是主持/旁白)。若自检打印里 H/C 整体颠倒,把 `spk_of_cluster` 的 H/C 对调即可(极少见)。

## 5. edge-tts 不能克隆真人嗓
用户要"某某解说的声音"只能用**风格接近的现成音色当替身**(本片 H=云希 young / C=云健 mature)。真要本人音色得上声音克隆(GPT-SoVITS/CosyVoice)另起管线。两个音色要**明显可区分**(年龄/性别/音色差开)。

## 6. 本机 ffmpeg 多半无 libass/drawtext
字幕用 Pillow 画成透明帧再 overlay(`render_subs.py`),别用 ffmpeg 的 subtitles/drawtext 滤镜。中文字体:`/System/Library/Fonts/Hiragino Sans GB.ttc`。

## 7. 联网步骤要让用户跑
edge-tts(配音)、faster-whisper 首次下模型、`pip install resemblyzer`(连带 torch,体积大)都要联网。若你的命令行无网(沙箱),让用户在输入框用 `!命令` 跑,输出你能看到。resemblyzer 自带预训练权重,装好后跑分段**不**需联网。

## 8. YouTube 下载绕 PO-token
`yt-dlp` 加 `--extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb"`,**整段下、不要 `--download-sections`**。抽音轨:`ffmpeg -i original.mp4 -ac 1 -ar 16000 source/audio16k.wav`。

## 9. 配音对齐:段作单位 + 借静音 + 限幅压缩
`make_dub.py`:每段锚到原片 start;放不下先借前面静音提前开口(LOOKBACK=3s),再 atempo 压缩(≤1.5,>1.5 发"赶"),漂移靠后续静音自动追回。**按绝对锚点摆放,误差不累积**。中文通常比英文短,多数段反而要留尾静音——别硬拉慢。

## 10. 段内多说话人 = 多轮次
`segments_spk.json` 每段 `turns:[{spk,text}]`。段仍是对齐单位,段内各轮次按各自音色 TTS、顺序拼接;字幕按各轮次配音时长比例切。同一人内部的 `——` 是停顿、作字幕断点,不换嗓。
