"""Export pack: trailer cut, poster, credits card, platform presets.

All ffmpeg-based with fail-safe (tool missing -> None + warn).
"""
import os
import subprocess

import media
from state import load_plan, load_state


def _dur(path):
    try:
        return float(media.probe(path, "duration") or 0)
    except Exception:
        return 0.0


def _concat(project, scene_files, out, fps=24, fade=0.5):
    lst = os.path.join(project, "meta", "export_concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in scene_files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    total = sum(_dur(p) for p in scene_files)
    vf = f"fps={fps}"
    if fade > 0 and total > fade * 2:
        vf += (f",fade=t=in:st=0:d={fade},"
               f"fade=t=out:st={max(0, total - fade):.2f}:d={fade}")
    media.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
               "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
               "-pix_fmt", "yuv420p", "-an", out])
    return out


def pick_top_scenes(project, n=5, black_max=0.05):
    """QC report ke top n (score order) scene ids — report na ho toh plan order."""
    plan = load_plan(project)
    state = load_state(project)
    ids = [int(sc["id"]) for sc in plan["scenes"]]
    report = os.path.join(project, "meta", "make_report.json")
    if os.path.exists(report):
        import json
        rep = json.load(open(report, encoding="utf-8"))
        scored = {}
        for sid, s in rep.get("scenes", {}).items():
            if s.get("status") != "missing" and (s.get("black_ratio") or 0) <= black_max:
                scored[int(sid)] = s.get("score", 0)
        if scored:
            ids = [sid for sid, _ in sorted(scored.items(),
                                            key=lambda kv: -kv[1])][:n]
    return ids


def scene_files(project, scene_ids):
    state = load_state(project)
    files = []
    for sid in scene_ids:
        meta = state.get(f"scene_{int(sid):02d}", {})
        v = meta.get("lipsynced") or meta.get("video")
        if v:
            files.append(os.path.join(project, "scenes", v))
    return files


def make_trailer(project, scene_ids=None, n=5, out="trailer.mp4"):
    ids = scene_ids or pick_top_scenes(project, n)
    files = scene_files(project, ids)
    if not files:
        print("[export] trailer: koi scene video nahi mila")
        return None
    print(f"[export] trailer from scenes {ids}")
    return _concat(project, files, os.path.join(project, out))


def make_poster(project, scene_id=None, out="poster.png"):
    plan = load_plan(project)
    state = load_state(project)
    sid = scene_id or (plan["scenes"][0]["id"] if plan["scenes"] else None)
    if sid is None:
        return None
    kf = state.get(f"scene_{int(sid):02d}", {}).get("keyframe")
    if not kf:
        print("[export] poster: keyframe nahi mila")
        return None
    src = os.path.join(project, "keyframes", kf)
    dst = os.path.join(project, out)
    media.run(["ffmpeg", "-y", "-i", src,
               "-vf", "scale=1080:1440:force_original_aspect_ratio=increase,"
                      "crop=1080:1440", dst])
    return dst


def make_credits(project, out="credits.mp4", seconds=6):
    plan = load_plan(project)
    title = plan.get("title", "AI FILM")
    line = plan.get("logline", "")[:80]
    dst = os.path.join(project, out)
    # escape for drawtext
    def esc(s):
        return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    vf = (f"color=c=black:s=1920x1080:d={seconds},"
          f"drawtext=text='{esc(title)}':fontsize=80:fontcolor=white:"
          f"x=(w-text_w)/2:y=(h-text_h)/2-60,"
          f"drawtext=text='{esc(line)}':fontsize=34:fontcolor=gray:"
          f"x=(w-text_w)/2:y=(h-text_h)/2+70")
    try:
        media.run(["ffmpeg", "-y", "-f", "lavfi", "-i", vf,
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", dst])
    except Exception as e:
        print(f"[export] credits drawtext fail ({e}) — plain card bana rahe hain")
        media.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                   f"color=c=black:s=1920x1080:d={seconds}",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", dst])
    return dst


PRESETS = {
    "youtube": (1920, 1080),
    "shorts": (1080, 1920),
    "reels": (1080, 1920),
    "square": (1080, 1080),
}


def platform_preset(project, src=None, preset="youtube", out=None):
    if preset not in PRESETS:
        print(f"[export] unknown preset {preset} (options: {list(PRESETS)})")
        return None
    w, h = PRESETS[preset]
    src = src or os.path.join(project, "final.mp4")
    if not os.path.exists(src):
        print(f"[export] source nahi mila: {src}")
        return None
    dst = out or os.path.join(project, f"final_{preset}.mp4")
    media.run(["ffmpeg", "-y", "-i", src,
               "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                      f"crop={w}:{h}", "-c:v", "libx264", "-crf", "19",
               "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", dst])
    return dst
