#!/usr/bin/env python3
"""THE LAST LIGHTHOUSE — procedural score (Stage 5 of the course).

A soft ambient pad, synthesized with numpy + scipy (additive synthesis):
  A minor drone  ->  Fmaj7  ->  C  ->  swell into C major AT the reveal
  (shot 07, ~41.5 s — the music and the story turn together).

Zero downloads, zero licenses. Deterministic — regenerating gives the
exact same score. build_film.sh / build_vertical.sh auto-mix it ~25 dB
under the narration.

Run:  python3 make_music.py
"""
import wave
import numpy as np
from scipy.signal import butter, lfilter
from pathlib import Path

OUT = Path(__file__).parent / "music.wav"
SR = 48000
DUR = 52.5
N = int(SR * DUR)
t = np.arange(N) / SR


def lowpass(x, cutoff, order=2):
    b, a = butter(order, cutoff / (SR / 2), btype="low")
    return lfilter(b, a, x)


def note(freq, start, end, amp, vib=False, harm=(1.0, 0.45, 0.18)):
    """One warm sustained note: fundamental + 2 harmonics, slow envelopes."""
    n = int(SR * (end - start))
    tt = np.arange(n) / SR
    fmod = freq * (1 + 0.0015 * np.sin(2 * np.pi * 0.35 * tt)) if vib else freq
    phase = np.cumsum(fmod) / SR
    y = sum(h * np.sin(2 * np.pi * (i + 1) * phase) for i, h in enumerate(harm))
    env = np.ones(n)
    atk = min(int(2.0 * SR), n // 2)
    env[:atk] = np.sin(np.pi * np.arange(atk) / (2 * atk)) ** 2
    rel = min(int(2.5 * SR), n)
    env[-rel:] *= np.cos(np.pi * np.arange(rel) / (2 * rel)) ** 2
    return y * env * amp


# (start, end, notes[(freq, amp, vibrato)])
SECTIONS = [
    (0.0, 16.0, [(110.00, 0.16, True), (164.81, 0.11, True),
                 (220.00, 0.09, True), (261.63, 0.05, False)]),     # A minor drone
    (16.0, 32.0, [(87.31, 0.15, True), (130.81, 0.10, True),
                  (164.81, 0.09, True), (220.00, 0.08, True)]),     # Fmaj7
    (32.0, 41.0, [(130.81, 0.13, True), (196.00, 0.10, True),
                  (329.63, 0.06, False)]),                          # C (waiting)
    (41.0, 47.0, [(130.81, 0.17, True), (261.63, 0.13, True),
                  (329.63, 0.12, True), (392.00, 0.10, False),
                  (523.25, 0.05, False)]),                          # C major swell — THE REVEAL
    (47.0, 52.5, [(110.00, 0.10, True), (164.81, 0.06, True)]),     # quiet resolve
]

mix = np.zeros(N)
for s, e, notes in SECTIONS:
    for f, a, v in notes:
        y = note(f, max(0.0, s - 1.2), min(e + 1.2, DUR), a, v)   # overlap = crossfade
        i0 = int(max(0.0, s - 1.2) * SR)
        i1 = min(i0 + len(y), N)
        mix[i0:i1] += y[: i1 - i0]

mix = lowpass(mix, 1300)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 10 ** (-25 / 20)                 # peak -25 dBFS: under the bed, above silence

# slow stereo breathing (decorrelated amplitude wobble)
L = mix * (1 + 0.18 * np.sin(2 * np.pi * 0.045 * t))
R = mix * (1 + 0.18 * np.sin(2 * np.pi * 0.045 * t + np.pi))

fade_in = np.clip(t / 2.5, 0, 1)
fade_out = np.clip((DUR - t) / 3.0, 0, 1)
L *= fade_in * fade_out
R *= fade_in * fade_out

pcm = (np.stack([L, R], axis=1) * 32767).astype(np.int16)
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

print(f"music.wav written: {DUR}s stereo 48kHz, peak -25 dBFS, C-major swell at 41.5s")
