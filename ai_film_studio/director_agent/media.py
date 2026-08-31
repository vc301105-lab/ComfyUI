"""FFmpeg helpers (subprocess wrappers) + engine command templating."""
import os
import shutil
import subprocess


def which(cmd):
    return shutil.which(cmd) is not None


def run(cmd, check=True):
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def probe(path, key="sample_rate"):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", f"stream={key}", "-of",
         "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    return r.stdout.strip()


def normalize_audio(src, dst, sr=48000, ac=2):
    run(["ffmpeg", "-y", "-i", src, "-ar", str(sr), "-ac", str(ac), dst])
    return dst


def make_silence(dst, seconds, sr=48000, ac=2):
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"anullsrc=r={sr}:cl=stereo", "-t", f"{seconds}",
         "-ar", str(sr), "-ac", str(ac), dst])
    return dst


def concat_audio(files, dst):
    lst = os.path.join(os.path.dirname(dst), "concat_audio.list")
    with open(lst, "w", encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", dst])
    return dst


def duck_mix(video, music, dst, music_volume=0.18):
    """Music bed ko voice ke neeche mix (volume amix)."""
    run(["ffmpeg", "-y", "-i", video, "-i", music,
         "-filter_complex",
         f"[1:a]volume={music_volume}[m];[0:a][m]amix=inputs=2:duration=first:"
         f"dropout_transition=3[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", dst])
    return dst


def loudness_normalize(video, dst, target=-14.0):
    run(["ffmpeg", "-y", "-i", video,
         "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11",
         "-c:v", "copy", "-c:a", "aac", dst])
    return dst


def template_command(cfg, key, replacements):
    """%PLACEHOLDER% replacement aur shell command chalata hai."""
    cmd_t = (cfg.get(key) or {}).get("command") or ""
    if not cmd_t:
        return None
    for k, v in replacements.items():
        cmd_t = cmd_t.replace(f"%{k}%", str(v))
    print("  engine:", cmd_t)
    subprocess.run(cmd_t, shell=True, check=True, timeout=3600)
    return True
