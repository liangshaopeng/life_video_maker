# -*- coding: utf-8 -*-
"""第2章动画样片:假如没有越位 -> 两队蹲两端 -> 中场掏空 -> 长传冲吊。
渲染 8s -> /tmp/ch2.mp4,并抽 4 个阶段帧拼成 /tmp/ch2_seq.png"""
import os, subprocess
from PIL import Image
import lib_pitch3d as P

# fx:0左门..1右门(红队攻右门), fy:0远..1近(主看台)
spec = {
  "players": [
    # 红队(攻右门):3 外场 + 门将   ——   蓝队(守):3 外场 + 门将   (对称)
    {"team":"red","num":"9","keys":[[0,0.42,0.55],[8,0.42,0.55]]},                                  # 红9 持球,留中场
    {"team":"red","num":"11","keys":[[0,0.55,0.42],[1,0.55,0.42],[4.5,0.90,0.46],[8,0.90,0.46]]},   # 红11 冲右门蹲点
    {"team":"red","num":"6","keys":[[0,0.40,0.45],[1,0.40,0.45],[4.5,0.16,0.52],[8,0.16,0.52]]},    # 红6 回防左门
    {"team":"blue","num":"5","keys":[[0,0.48,0.50],[8,0.48,0.50]]},                                 # 蓝5 留中场盯红9
    {"team":"blue","num":"10","keys":[[0,0.45,0.62],[1,0.45,0.62],[4.5,0.10,0.56],[8,0.10,0.56]]},  # 蓝10 冲左门蹲点
    {"team":"blue","num":"4","keys":[[0,0.60,0.38],[1,0.60,0.38],[4.5,0.85,0.44],[8,0.85,0.44]]},   # 蓝4 回防右门防红11
    {"team":"red_gk","num":"1","keys":[[0,0.025,0.50],[8,0.025,0.50]]},                             # 左门=红队门将(亮红)
    {"team":"blue_gk","num":"1","keys":[[0,0.975,0.50],[8,0.975,0.50]]},                            # 右门=蓝队门将(亮蓝)
  ],
  "ball": {"keys":[[0,0.45,0.56],[5,0.45,0.56],[7,0.88,0.47],[8,0.88,0.47]]},                       # 红9 长传冲吊给红11
}

OUT="/tmp/ch2_frames"; os.makedirs(OUT, exist_ok=True)
DUR, FPS = 8.0, 30; N=int(DUR*FPS)
for i in range(N):
    P.render_frame(spec, i/FPS).convert("RGB").save(f"{OUT}/{i:04d}.png")
print(f"frames: {N}")
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-framerate","30",
  "-i",f"{OUT}/%04d.png","-c:v","libx264","-pix_fmt","yuv420p","/tmp/ch2.mp4"], check=True)
for t in (0, 3, 5, 7.5):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(t),
      "-i","/tmp/ch2.mp4","-frames:v","1",f"/tmp/ch2_{t}.png"], check=True)
ims=[Image.open(f"/tmp/ch2_{t}.png").resize((780,439)) for t in (0,3,5,7.5)]
seq=Image.new("RGB",(780*2+24,439*2+24),(18,18,18))
for idx,im in enumerate(ims):
    seq.paste(im,((idx%2)*(780+24)+8,(idx//2)*(439+24)+8))
seq.save("/tmp/ch2_seq.png")
print("mp4 + seq done")
