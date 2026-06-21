# -*- coding: utf-8 -*-
"""
把 whisper 的短语级 segments 合并成句子级 chunk(更自然的翻译/配音单元)。
合并规则:累积到句末标点(. ! ?)或时长>MAXDUR或字数>MAXCH 就断句。
产出 build/chunks_en.json: [{id,start,end,en}]
用法: python3 merge_segments.py
"""
import json, os
ROOT=os.path.dirname(os.path.abspath(__file__)); BUILD=os.path.join(ROOT,"build")
MAXDUR=11.0; MAXCH=160

segs=json.load(open(os.path.join(BUILD,"transcript_en.json"),encoding="utf-8"))
chunks=[]; cur=None
def flush():
    global cur
    if cur: chunks.append(cur); cur=None
for s in segs:
    t=s["text"].strip()
    if not t: continue
    if cur is None:
        cur={"start":s["start"],"end":s["end"],"en":t}
    else:
        cur["end"]=s["end"]; cur["en"]=(cur["en"]+" "+t).strip()
    ends_sent = cur["en"].rstrip()[-1:] in ".!?"
    long_enough = (cur["end"]-cur["start"]>=MAXDUR) or (len(cur["en"])>=MAXCH)
    if ends_sent or long_enough:
        flush()
flush()
for i,c in enumerate(chunks): c["id"]=i
json.dump(chunks,open(os.path.join(BUILD,"chunks_en.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
tot=chunks[-1]["end"]-chunks[0]["start"] if chunks else 0
print(f"{len(chunks)} chunks, span {tot:.1f}s")
for c in chunks[:6]: print(f"[{c['start']:6.2f}-{c['end']:6.2f}] {c['en']}")
