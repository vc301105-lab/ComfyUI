#!/usr/bin/env python3
"""THE LAST LIGHTHOUSE — procedural ambience bed (Stage 5 of the course).

No music library, no downloads, no licenses: the storm is synthesized with
numpy + scipy —

  wind    = low-passed brown noise with a slow gust envelope
  sea     = band-passed white noise (swell) + wave wash
  rain    = high-passed hiss, present only during the storm scenes
  foghorn = FM-synthesized 110 Hz horn at the reveal (shot 07, ~41.5 s)

build_film.sh / build_vertical.sh auto-mix this ~18 dB under the narration.
Deterministic (fixed seeds) — regenerating gives the exact same bed.
Run:  python3 make_ambience.py
"""
import wave
import numpy as np
from scipy.signal import butter, lfilter
from pathlib import Path

OUT = Path(__file__).parent / "ambience.wav"
SR = 48000
DUR = 52.5
N = int(SR * DUR)
t = np.arange(N) / SR


def white(rng, n):
    return rng.standard_normal(n)


def brown(rng, n):
    b = np.cumsum(rng.standard_normal(n))
    b -= np.linspace(b[0], b[-1], n)          # remove slow drift
    return b / (np.sqrt(np.mean(b ** 2)) + 1e-9)


def bandpass(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)


def lowpass(x, cutoff, order=2):
    b, a = butter(order, cutoff / (SR / 2), btype="low")
    return lfilter(b, a, x)


def highpass(x, cutoff, order=2):
    b, a = butter(order, cutoff / (SR / 2), btype="high")
    return lfilter(b, a, x)


def norm(x):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-9)


rng1, rng2 = np.random.default_rng(11), np.random.default_rng(23)

# ---- components (per channel, unit rms, decorrelated L/R) ----
wind_l = norm(lowpass(brown(rng1, N), 300))
wind_r = norm(lowpass(brown(rng2, N), 300))
swell_l = norm(bandpass(white(rng1, N), 110, 420))
swell_r = norm(bandpass(white(rng2, N), 110, 420))
wash_l = norm(bandpass(white(rng1, N), 500, 3200))
wash_r = norm(bandpass(white(rng2, N), 500, 3200))
rain_l = norm(highpass(white(rng1, N), 2600))
rain_r = norm(highpass(white(rng2, N), 2600))

# ---- slow envelopes ----
env_wind = 0.65 + 0.25 * np.sin(2 * np.pi * 0.07 * t + 1.0) \
         + 0.10 * np.sin(2 * np.pi * 0.23 * t + 2.5)
env_swell = 0.45 + 0.30 * np.sin(2 * np.pi * 0.05 * t) \
          + 0.15 * np.sin(2 * np.pi * 0.017 * t + 1.2)
env_wash = 0.30 + 0.20 * np.sin(2 * np.pi * 0.11 * t + 1.0)

# rain only during the storm scenes; gone by the dawn (t ~ 38 s)
rain_env = 0.5 * np.clip((38.0 - t) / 5.0, 0.0, 1.0)

# ---- mix the bed ----
L = (wind_l * env_wind * 0.55 + swell_l * env_swell * 0.50
     + wash_l * env_wash * 0.14 + rain_l * rain_env * 0.05)
R = (wind_r * env_wind * 0.55 + swell_r * env_swell * 0.50
     + wash_r * env_wash * 0.14 + rain_r * rain_env * 0.05)

# ---- level the bed to RMS -32 dBFS ----
bed_rms = np.sqrt(np.mean(L[: int(38 * SR)] ** 2 + R[: int(38 * SR)] ** 2))
L, R = L * (10 ** (-32 / 20) / bed_rms), R * (10 ** (-32 / 20) / bed_rms)


# ---- distant foghorn at the reveal (placed AFTER leveling) ----
def foghorn(dur, f0=110.0):
    n = int(SR * dur)
    tt = np.arange(n) / SR
    wob = f0 * (1 + 0.015 * np.sin(2 * np.pi * 0.6 * tt))
    phase = np.cumsum(wob) / SR
    tone = (np.sin(2 * np.pi * phase)
            + 0.5 * np.sin(2 * np.pi * phase * 1.5)
            + 0.22 * np.sin(2 * np.pi * phase * 2.0))
    tone = lowpass(tone, 900)
    env = np.minimum(tt / 0.7, 1.0) * np.exp(-tt / 1.8)
    return tone * env


def place(sig, at, gain):
    i0 = int(at * SR)
    i1 = min(i0 + len(sig), N)
    if i1 > i0:
        seg = sig[: i1 - i0]
        L[i0:i1] += seg * gain * 0.6
        R[i0:i1] += seg * gain * 0.9


horn = foghorn(4.0)
place(horn, 41.5, 0.10 / max(np.max(np.abs(horn)), 1e-9))   # main, peak -20 dBFS
place(horn, 43.2, 0.03 / max(np.max(np.abs(horn)), 1e-9))   # faint echo

L, R = np.clip(L, -0.85, 0.85), np.clip(R, -0.85, 0.85)
pcm = (np.stack([L, R], axis=1) * 32767).astype(np.int16)

with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"ambience.wav written: {DUR}s stereo 48kHz, bed RMS -32 dBFS, foghorn at 41.5s")
