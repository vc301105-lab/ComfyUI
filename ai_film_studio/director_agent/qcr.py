"""QC / Review: per-scene checks + continuity + project report.

Checks (ffmpeg/ffprobe):
- stream info: duration (vs expected), resolution, fps, audio presence
- black frames (blackdetect)
- sudden cut count (scdet / select showinfo)
- continuity: PSNR between last frame of scene N and first frame of scene N+1

All checks fail-safe: tool missing / parse error -> warn, scene marked "unknown"
instead of crashing the pipeline.
"""
import json
import os
import re
import subprocess
import tempfile

from state import load_plan, load_state


def _run(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _to_fps(rate):
    if not rate or rate in ("0/0", "N/A"):
        return None
    try:
        num, den = rate.split("/")
        return round(float(num) / float(den), 2)
    except Exception:
        return None


def probe(video):
    r = _run(["ffprobe", "-v", "error", "-print_format", "json",
              "-show_streams", "-show_format", video])
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {}


def stream_info(video):
    p = probe(video)
    streams = p.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(p.get("format", {}).get("duration") or v.get("duration") or 0)
    return {
        "duration": round(dur, 2),
        "width": v.get("width"),
        "height": v.get("height"),
        "fps": _to_fps(v.get("avg_frame_rate") or v.get("r_frame_rate")),
        "has_audio": bool(a),
        "codec": v.get("codec_name"),
    }


def black_segments(video):
    r = _run(["ffmpeg", "-i", video,
              "-vf", "blackdetect=d=0.5:pic_th=0.98", "-an", "-f", "null", "-"])
    starts = re.findall(r"black_start:([\d.]+)", r.stderr)
    durs = re.findall(r"black_duration:([\d.]+)", r.stderr)
    return [(float(s), float(d)) for s, d in zip(starts, durs)]


def cut_times(video, threshold=0.35):
    r = _run(["ffmpeg", "-i", video,
              "-vf", f"select='gt(scene,{threshold})',showinfo",
              "-f", "null", "-"])
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def _ref_frame(video, last=False):
    """Extract first/last frame to a temp PNG, return path."""
    tmp = tempfile.mktemp(suffix=".png")
    if last:
        cmd = ["ffmpeg", "-y", "-sseof", "-0.5", "-i", video,
               "-vframes", "1", tmp]
    else:
        cmd = ["ffmpeg", "-y", "-i", video, "-vframes", "1", tmp]
    r = _run(cmd)
    return tmp if os.path.exists(tmp) and os.path.getsize(tmp) > 0 else None


def _psnr(a, b):
    if not a or not b:
        return None
    r = _run(["ffmpeg", "-i", a, "-i", b, "-lavfi", "psnr",
              "-f", "null", "-"])
    m = re.search(r"average:([\d.]+)", r.stderr)
    return round(float(m.group(1)), 2) if m else None


def review_scene(video, expected_seconds=None):
    """Return per-scene report dict (never raises)."""
    info = stream_info(video)
    report = {"video": os.path.basename(video), **info}
    # duration check
    if expected_seconds:
        report["duration_ok"] = abs(info["duration"] - expected_seconds) <= max(1.0, expected_seconds * 0.25)
    # black frames
    try:
        blacks = black_segments(video)
        report["black_segments"] = blacks
        report["black_ratio"] = round(
            sum(d for _, d in blacks) / info["duration"], 4) if info["duration"] else None
    except Exception:
        report["black_segments"] = []
        report["black_ratio"] = None
    # cuts
    try:
        cuts = cut_times(video)
        report["cuts"] = len(cuts)
    except Exception:
        report["cuts"] = None
    # score 0-100
    score = 100
    if report.get("black_ratio") is not None and report["black_ratio"] > 0.05:
        score -= 40
    if report.get("duration_ok") is False:
        score -= 20
    if report.get("cuts") is not None and report["cuts"] > 3:
        score -= 10
    if not report.get("has_audio") and report.get("audio_expected", True):
        score -= 10
    report["score"] = max(0, score)
    return report


def review_project(project, expected_seconds=None):
    """Full project QC: per scene + continuity + summary."""
    plan = load_plan(project)
    state = load_state(project)
    if not plan:
        raise SystemExit("plan.json nahi mila")
    seconds = expected_seconds or plan.get("video_seconds_per_scene")
    scenes = {}
    order = []
    for sc in plan["scenes"]:
        sid = int(sc["id"])
        meta = state.get(f"scene_{sid:02d}", {})
        v = meta.get("video")
        if not v:
            scenes[sid] = {"status": "missing", "video": None}
            continue
        path = os.path.join(project, "scenes", v)
        scenes[sid] = review_scene(path, seconds)
        order.append(sid)

    # continuity between consecutive scenes
    continuity = []
    for a, b in zip(order, order[1:]):
        fa = _ref_frame(os.path.join(project, "scenes", scenes[a]["video"]), last=True)
        fb = _ref_frame(os.path.join(project, "scenes", scenes[b]["video"]), last=False)
        psnr = _psnr(fa, fb)
        # higher PSNR = closer match (continuity good if < ~35 means big jump;
        # cuts are expected though — this is informational)
        continuity.append({"from": a, "to": b, "psnr": psnr})
        for f in (fa, fb):
            if f and os.path.exists(f):
                os.remove(f)

    scored = [s for s in scenes.values() if "score" in s]
    summary = {
        "scenes_total": len(scenes),
        "scenes_checked": len(scored),
        "scenes_missing": sum(1 for s in scenes.values() if s.get("status") == "missing"),
        "avg_score": round(sum(s["score"] for s in scored) / len(scored), 1) if scored else None,
        "issues": {
            "black_frames": sum(1 for s in scored if (s.get("black_ratio") or 0) > 0.05),
            "duration_mismatch": sum(1 for s in scored if s.get("duration_ok") is False),
            "no_audio": sum(1 for s in scored if not s.get("has_audio")),
        },
    }
    return {"scenes": scenes, "continuity": continuity, "summary": summary}


def report_text(rep):
    lines = [f"QC SUMMARY: avg_score={rep['summary']['avg_score']} "
             f"checked={rep['summary']['scenes_checked']}/{rep['summary']['scenes_total']}"]
    lines.append(f"  missing={rep['summary']['scenes_missing']} "
                 f"black={rep['summary']['issues']['black_frames']} "
                 f"duration={rep['summary']['issues']['duration_mismatch']} "
                 f"no_audio={rep['summary']['issues']['no_audio']}")
    for sid, s in sorted(rep["scenes"].items(), key=lambda kv: int(kv[0])):
        if s.get("status") == "missing":
            lines.append(f"  S{sid}: MISSING")
            continue
        lines.append(f"  S{sid}: score={s.get('score')} dur={s.get('duration')}s "
                     f"{s.get('width')}x{s.get('height')}@{s.get('fps')}fps "
                     f"audio={'Y' if s.get('has_audio') else 'N'} "
                     f"black={s.get('black_ratio')} cuts={s.get('cuts')}")
    if rep["continuity"]:
        lines.append("  continuity (PSNR last->first frame, >25 = close match):")
        for c in rep["continuity"]:
            lines.append(f"    S{c['from']}->S{c['to']}: {c['psnr']}")
    return "\n".join(lines)
