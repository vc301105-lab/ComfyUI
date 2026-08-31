"""Final assembly: ffmpeg concat + optional audio mux + subtitles."""

import os
import subprocess

from state import load_plan, load_state


def _run(cmd):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True)


def concat_videos(project, out_name="final.mp4", fps=24):
    """Assemble scene videos in plan order -> project/final.mp4"""
    plan = load_plan(project)
    state = load_state(project)
    videos = []
    for sc in plan["scenes"]:
        meta = state.get(f"scene_{int(sc['id']):02d}", {})
        v = meta.get("video")
        if v:
            videos.append(os.path.join(project, "scenes", v))
    if not videos:
        raise SystemExit("Koi rendered scene video nahi mila — pehle 'director.py render'")

    # concat via re-encode (safe across encoders/resolutions)
    list_file = os.path.join(project, "meta", "concat.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for v in videos:
            f.write(f"file '{os.path.abspath(v)}'\n")
    out = os.path.join(project, out_name)
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                    "-vf", f"fps={fps}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-pix_fmt", "yuv420p", "-an", out],
                   check=True)
    print(f"[assemble] -> {out}")
    return out


def mux_audio(video, audio, out=None):
    out = out or video.replace(".mp4", "_with_audio.mp4")
    _run(["ffmpeg", "-y", "-i", video, "-i", audio,
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out])
    return out


def burn_subtitles(video, srt, out=None):
    out = out or video.replace(".mp4", "_subs.mp4")
    _run(["ffmpeg", "-y", "-i", video, "-i", srt,
          "-c:v", "libx264", "-crf", "19", "-preset", "medium",
          "-c:a", "copy",
          "-vf", "subtitles=" + os.path.abspath(srt).replace(":", "\\:"), out])
    return out
