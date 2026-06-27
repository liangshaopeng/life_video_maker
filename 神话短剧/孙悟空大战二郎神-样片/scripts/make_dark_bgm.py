# -*- coding: utf-8 -*-
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "bgm" / "dark_myth_bgm.wav"
SR = 44100
DURATION = 32.0


def clamp(v: float) -> float:
    return max(-0.98, min(0.98, v))


def envelope(t: float, start: float, length: float) -> float:
    if t < start or t > start + length:
        return 0.0
    x = (t - start) / length
    return math.exp(-5.0 * x) * math.sin(math.pi * min(1.0, x * 4.0))


def sample(t: float) -> float:
    rumble = 0.18 * math.sin(2 * math.pi * 44 * t) + 0.08 * math.sin(2 * math.pi * 66 * t)
    pulse = 0.0
    for beat in [0.0, 3.9, 8.8, 14.9, 21.8, 27.8]:
        pulse += 0.55 * envelope(t, beat, 1.2) * math.sin(2 * math.pi * (68 - 20 * (t - beat)) * t)
    shimmer = 0.025 * random.uniform(-1.0, 1.0)
    fade_in = min(1.0, t / 1.2)
    fade_out = min(1.0, max(0.0, (DURATION - t) / 2.4))
    return clamp((rumble + pulse + shimmer) * fade_in * fade_out)


def main() -> int:
    random.seed(42)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = int(SR * DURATION)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        for i in range(frames):
            value = int(sample(i / SR) * 32767)
            packed = struct.pack("<hh", value, value)
            w.writeframesraw(packed)
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
