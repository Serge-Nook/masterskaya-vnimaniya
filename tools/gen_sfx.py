"""Синтез звуковых эффектов и спокойной музыки (без внешних сэмплов).

python tools/gen_sfx.py  → mv/data/sfx/*.wav, calm.ogg (нужен ffmpeg)
"""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parents[1] / "mv" / "data" / "sfx"


def t(sec):
    return np.arange(int(SR * sec)) / SR


def env(x, attack=0.01, decay=4.0):
    tt = np.arange(len(x)) / SR
    a = np.clip(tt / attack, 0, 1)
    return x * a * np.exp(-tt * decay)


def tone(freq, sec, partials=((1, 1.0),), decay=4.0, attack=0.01):
    tt = t(sec)
    x = sum(a * np.sin(2 * np.pi * freq * m * tt) for m, a in partials)
    return env(x, attack, decay)


def write(name, x, peak=0.6):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    fade = min(len(x), int(SR * 0.02))
    x[-fade:] *= np.linspace(1, 0, fade)
    data = (x * 32767).astype("<i2")
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bell = tone(1318, 1.6, ((1, 1), (2.76, 0.4), (5.4, 0.15)), decay=2.5)
    write("bell", bell)
    tt = t(0.9)
    vib = np.sin(2 * np.pi * 784 * tt + 0.15 * np.sin(2 * np.pi * 5 * tt))
    pipe = vib + 0.3 * np.sin(2 * np.pi * 1568 * tt) + 0.05 * np.random.default_rng(1).normal(size=len(tt))
    write("pipe", env(pipe, attack=0.08, decay=1.2), peak=0.5)
    tt = t(0.18)
    write("pop", env(np.sin(2 * np.pi * (500 + 900 * tt / 0.18) * tt), 0.003, 18), peak=0.5)
    write("soft", tone(330, 0.5, ((1, 1), (2, 0.2)), decay=7), peak=0.35)
    write("tick", tone(1800, 0.06, decay=60, attack=0.001), peak=0.3)
    chime = np.concatenate([tone(f, 0.35, ((1, 1), (2, 0.3)), decay=5) for f in (659, 784, 1047)])
    write("chime", np.concatenate([chime, tone(1319, 0.9, ((1, 1), (2, 0.3)), decay=3)]), peak=0.45)
    noise = np.random.default_rng(2).normal(size=int(SR * 0.6))
    kernel = np.hanning(200)
    whoosh = np.convolve(noise, kernel / kernel.sum(), "same") * np.sin(np.linspace(0, np.pi, len(noise)))
    write("whoosh", whoosh, peak=0.3)
    write("step", tone(220, 0.09, decay=40, attack=0.002), peak=0.3)

    # спокойная музыка: медленные аккорды-пэды, 60 BPM, 32 секунды, бесшовная петля
    chords = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
    seg = 8.0
    total = np.zeros(int(SR * seg * len(chords)))
    tt = t(seg)
    shape = np.sin(np.linspace(0, np.pi, len(tt))) ** 1.5
    for i, ch in enumerate(chords):
        x = sum(np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * 2 * f * tt) for f in ch)
        start = int(i * seg * SR)
        total[start:start + len(tt)] += x * shape
        # мелодия: по ноте на 2 секунды
        for j, f in enumerate((ch[2] * 2, ch[1] * 2, ch[0] * 2, ch[1] * 2)):
            s = start + int(j * 2 * SR)
            n = tone(f, 2.0, ((1, 1), (3, 0.05)), decay=1.8, attack=0.05)
            total[s:s + len(n)] += 0.6 * n
    write("calm_tmp", total, peak=0.4)
    src = OUT / "calm_tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-c:a", "libvorbis", "-q:a", "3",
                    str(OUT / "calm.ogg")], check=True)
    src.unlink()


if __name__ == "__main__":
    main()
