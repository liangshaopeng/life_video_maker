# 素材与音乐获取(合法 + 可下)

## 实战画面(比赛/集锦)
真实比赛画面有版权(FIFA/转播方),没有"开放下载"正经渠道。两条路:
1. **用户自己下文件丢进 `footage/`**(最稳,任何来源:cobalt.tools 等下载站、B站App缓存…)。
2. **yt-dlp 嵌入式客户端法下 YouTube**(见 gotchas.md 第2条)。FIFA+ 官方频道有大量决赛/集锦,
   清晰度不登录也能拿(itag 18 360p 渐进式最稳;720/1080 走 DASH itag 298/137)。

选片:优先**进球、过人、庆祝、举杯、球星特写**;判别球队的视频要**避开对手球衣/特写**(讲阿根廷
却出现巴西球衣很违和)。先下整段,再用缩略图墙(gotchas.md 第9)定时间点填进 project.json 的 footage.start。

## 通用无版权足球空镜(没有具体球星时的垫片)
- **Mixkit**(免费、免署名):直链规律 `https://assets.mixkit.co/videos/{ID}/{ID}-1080.mp4`。
  从 mixkit.co 足球分类页找 ID。注意通用素材是泛足球(非具体球队)。
- 中性氛围镜头(球/草皮/灯光/拼抢)可用;球迷庆祝类常带各国球衣,做具体球队专题要慎用。

## 背景音乐(BGM,合法免费)
- **Incompetech / Kevin MacLeod**(CC-BY,需署名):直链
  `https://incompetech.com/music/royalty-free/mp3-royaltyfree/{Track%20Name}.mp3`。
  史诗/燃曲推荐:`Crossing the Chasm`(经典预告片式推进)、`Clash Defiant`(驱动)、`Heroic Age`。
  **发布时简介挂一句署名**(如 "Music: Crossing the Chasm by Kevin MacLeod, CC BY")。
- **Mixkit Music**(免署名):`https://assets.mixkit.co/music/preview/...mp3`。
- 选曲:层层推进、结尾能上高潮的史诗管弦,最配"夺冠/举杯"收尾。BGM 用 sidechain 压在解说下面
  (mix_bgm.sh),解说一开口音乐自动让路。

## 连通性备注(本环境实测)
- YouTube 可达(需嵌入式客户端法);Bilibili 反爬 412 基本不可下。
- assets.mixkit.co、incompetech.com 直链可下;cdn.pixabay.com、videos.pexels.com 需 key/会 403。
