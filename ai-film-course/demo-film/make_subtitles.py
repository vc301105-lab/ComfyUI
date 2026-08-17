#!/usr/bin/env python3
"""Generate subtitles.srt for THE LAST LIGHTHOUSE.

Reads the real narration duration and distributes the six VO lines
proportionally (by character count) across it, with a 0.35s gap
between cues. Rough-but-uploadable captions for YouTube/Reels.

Run:  python3 make_subtitles.py   ->  ../subtitles.srt
"""
import re
import subprocess
from pathlib import Path

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FF = "ffmpeg"

LINES = [
    "I remember the day the oceans took the cities.",
    "I was sent to the last lighthouse on Earth — to keep the lamp burning, no matter what.",
    "The storms came harder every year. The radio fell silent long ago.",
    "But every night, I climbed the stairs and lit the lamp, and I told myself: if I keep the light alive... someone, somewhere, might find their way home.",
    "Then, one morning, a signal blinked on the horizon. A ship that should not exist.",
    "And for the first time in ten years... the lighthouse had someone to guide.",
]
LEAD = 2.5      # VO starts at 2.5s in the film
GAP = 0.35      # breathing room between cues

narr = Path(__file__).parent / "audio" / "narration.mp3"
out = subprocess.run([FF, "-hide_banner", "-i", str(narr), "-f", "null", "-"],
                     capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out.stderr)
if not m:
    raise SystemExit("could not read narration duration")
dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def ts(x):
    ms = int(round(x * 1000))
    h, rem = divmod(ms, 3600000)
    mn, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{mn:02d}:{s:02d},{ms:03d}"


chars = [len(l) for l in LINES]
total = sum(chars)
t = LEAD
blocks = []
for i, line in enumerate(LINES):
    d = dur * chars[i] / total
    end = t + max(d - GAP, 0.3)
    blocks.append(f"{i + 1}\n{ts(t)} --> {ts(end)}\n{line}\n")
    t += d

Path(__file__).parent.joinpath("subtitles.srt").write_text("\n".join(blocks))
print(f"subtitles.srt written: narration {dur:.1f}s, {len(blocks)} cues, "
      f"last cue ends {ts(t)}")
