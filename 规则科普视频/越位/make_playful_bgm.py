# -*- coding: utf-8 -*-
"""Generate a light, playful tactics-board music bed as a WAV file."""
import math
import sys
import wave

import numpy as np


SR = 44100
BPM = 118
BEAT = 60.0 / BPM


def pan_stereo(sig, pan):
    left = math.cos(pan * math.pi / 2)
    right = math.sin(pan * math.pi / 2)
    return np.column_stack((sig * left, sig * right))


def add_layer(mix, start, stereo):
    i = int(start * SR)
    if i >= len(mix):
        return
    n = min(len(stereo), len(mix) - i)
    mix[i:i + n] += stereo[:n]


def add_pluck(mix, start, freq, dur=0.32, gain=0.16, pan=0.5):
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    attack = 1.0 - np.exp(-t * 95)
    decay = np.exp(-t * 9.5)
    env = attack * decay
    sig = (
        0.66 * np.sin(2 * np.pi * freq * t)
        + 0.23 * np.sin(2 * np.pi * freq * 2.01 * t + 0.2)
        + 0.09 * np.sin(2 * np.pi * freq * 3.02 * t + 1.0)
    )
    sig += 0.018 * np.sin(2 * np.pi * (freq * 0.5) * t)
    add_layer(mix, start, pan_stereo(sig * env * gain, pan))


def add_bass(mix, start, freq, dur=0.44, gain=0.11, pan=0.48):
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    env = (1.0 - np.exp(-t * 70)) * np.exp(-t * 5.2)
    sig = np.sin(2 * np.pi * freq * t) + 0.22 * np.sin(2 * np.pi * freq * 2 * t)
    add_layer(mix, start, pan_stereo(sig * env * gain, pan))


def add_kick(mix, start, gain=0.16):
    n = int(0.23 * SR)
    t = np.arange(n) / SR
    phase = 2 * np.pi * (48 * t + (82 / 35.0) * (1 - np.exp(-35 * t)))
    sig = np.sin(phase) * np.exp(-t * 15)
    add_layer(mix, start, pan_stereo(sig * gain, 0.5))


def add_snare(mix, start, rng, gain=0.052):
    n = int(0.115 * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 22)
    noise = rng.standard_normal(n)
    tone = 0.4 * np.sin(2 * np.pi * 185 * t)
    sig = (0.72 * noise + tone) * env
    add_layer(mix, start, pan_stereo(sig * gain, 0.54))


def add_hat(mix, start, rng, gain=0.020):
    n = int(0.045 * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 80)
    noise = rng.standard_normal(n)
    shimmer = np.sin(2 * np.pi * 7900 * t + 0.5)
    sig = (0.74 * noise + 0.26 * shimmer) * env
    add_layer(mix, start, pan_stereo(sig * gain, 0.64))


def render(seconds=145.0):
    rng = np.random.default_rng(23)
    mix = np.zeros((int(seconds * SR), 2), dtype=np.float32)
    scale = {
        "D2": 73.42, "F2": 87.31, "G2": 98.00, "A2": 110.00, "C3": 130.81,
        "D4": 293.66, "F4": 349.23, "G4": 392.00, "A4": 440.00,
        "C5": 523.25, "D5": 587.33, "F5": 698.46, "G5": 783.99,
    }
    chord_roots = [scale["D2"], scale["F2"], scale["G2"], scale["A2"]]
    pluck_patterns = [
        [(0.00, "D5"), (0.75, "F5"), (1.50, "A4"), (2.25, "C5"), (3.25, "G4")],
        [(0.00, "F5"), (0.50, "D5"), (1.75, "A4"), (2.50, "G4"), (3.50, "C5")],
        [(0.25, "G4"), (1.00, "D5"), (1.75, "F5"), (2.75, "A4"), (3.25, "D5")],
        [(0.00, "A4"), (0.75, "C5"), (1.25, "F5"), (2.50, "D5"), (3.50, "G5")],
    ]
    total_bars = int(seconds / (BEAT * 4)) + 1
    for bar in range(total_bars):
        t0 = bar * 4 * BEAT
        if t0 >= seconds:
            break
        root = chord_roots[(bar // 2) % len(chord_roots)]
        for b in range(4):
            add_hat(mix, t0 + (b + 0.02) * BEAT, rng, 0.017)
            add_hat(mix, t0 + (b + 0.54) * BEAT, rng, 0.012)
        add_kick(mix, t0, 0.145)
        add_kick(mix, t0 + 2 * BEAT, 0.105)
        add_snare(mix, t0 + 1 * BEAT, rng, 0.047)
        add_snare(mix, t0 + 3 * BEAT, rng, 0.043)
        add_bass(mix, t0, root, 0.46, 0.100)
        add_bass(mix, t0 + 2 * BEAT, root * (1.5 if bar % 4 == 3 else 1.0), 0.36, 0.070)
        pat = pluck_patterns[bar % len(pluck_patterns)]
        lift = 1.0 + (0.04 if (bar // 8) % 2 else 0.0)
        for beat_pos, note in pat:
            pan = 0.38 + 0.24 * ((bar + int(beat_pos * 2)) % 3) / 2
            add_pluck(mix, t0 + beat_pos * BEAT, scale[note] * lift, 0.31, 0.115, pan)
        if bar % 8 == 7:
            add_pluck(mix, t0 + 3.68 * BEAT, scale["G5"], 0.28, 0.078, 0.72)
    fade = int(2.0 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)[:, None]
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix = np.tanh(mix * 1.35) / 1.35
    peak = float(np.max(np.abs(mix))) or 1.0
    return (mix / peak * 0.86).astype(np.float32)


def write_wav(path, audio):
    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767).astype("<i2")
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/playful_tactics_bed.wav"
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 145.0
    write_wav(out, render(seconds))
    print(out)
