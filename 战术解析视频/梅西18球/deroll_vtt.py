#!/usr/bin/env python3
"""把 YouTube 自动字幕(auto-caption)VTT 去滚动(de-roll)成干净的逐行解说稿。

为什么需要这步:YouTube 自动字幕是"滚动字幕"——每个 cue 块把上一行已经显示
过的文字再抄一遍,只在末行追加几个带词级时间戳 `<HH:MM:SS.mmm>` 的新词。直接读
原始 VTT 满屏重复、根本读不通,也对不准时间。de-roll = 每个块只取那条"带词级
时间戳的新内容行",去标签,前缀块的起始时间 → 一行一句、带 `MM:SS` 时间戳的稿子。

这份干净稿才是战术片的**事实地图**:解说会喊出射手、助攻、过程(谁传谁射、扑救、
越位),你照它把每粒进球/威胁/扑救定位到素材的第几秒,再决定 footage.start。
别只看 720p 缩略图墙猜球队/射手(球员仅~20px,极易判错)。

用法:
    # 先下英文自动字幕(只要字幕,不重复下整场画面):
    yt-dlp --write-auto-subs --sub-langs "en.*" --skip-download \
      --extractor-args "youtube:player_client=tv_embedded,web_embedded,android_vr,mweb" \
      "<比赛/集锦 URL>"
    # 再 de-roll:
    python3 deroll_vtt.py xxx.en.vtt > build/commentary_clean.txt

输出每行:  MM:SS<两空格>整句解说   (MM 可大于 59,即累计分钟,便于对齐整场)
"""
import re
import sys

TAG_TS = re.compile(r"<\d\d:\d\d:\d\d\.\d\d\d>")          # 词级时间戳 <00:00:00.560>
TAG_C = re.compile(r"</?c[^>]*>")                        # <c> </c> <c.colorXXXX>
HEADER = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d\d\d\s+-->")  # cue 起始时间行


def strip_tags(line: str) -> str:
    line = TAG_TS.sub("", line)
    line = TAG_C.sub("", line)
    return re.sub(r"\s+", " ", line).strip()


def deroll(vtt_text: str):
    """按 cue 头行切块(VTT 里 cue 之间夹着空行或纯空格行,不能用空行分割)。
    每块只取那条带词级时间戳的"新内容行",去标签,前缀块起始 MM:SS。"""
    out = []
    last = None
    cur_min = cur_sec = None  # 当前 cue 头时间
    pending = None            # 当前 cue 里待提取的带标签行
    for ln in vtt_text.splitlines():
        m = HEADER.match(ln.strip())
        if m:
            # 收掉上一个 cue
            if pending is not None and cur_min is not None:
                clean = strip_tags(pending)
                if clean and clean != last:
                    last = clean
                    out.append(f"{cur_min:02d}:{cur_sec:02d}  {clean}")
            hh, mm, ss = (int(x) for x in m.groups())
            cur_min, cur_sec = hh * 60 + mm, ss
            pending = None
        elif TAG_TS.search(ln):
            pending = ln  # 这条带词级时间戳 = 该 cue 的新内容
    # 收尾最后一个 cue
    if pending is not None and cur_min is not None:
        clean = strip_tags(pending)
        if clean and clean != last:
            out.append(f"{cur_min:02d}:{cur_sec:02d}  {clean}")
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: deroll_vtt.py <auto-caption.en.vtt>  > commentary_clean.txt")
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    print("\n".join(deroll(text)))


if __name__ == "__main__":
    main()
