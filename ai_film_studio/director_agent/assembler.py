"""Final assembly: concat -> voice+lip-sync -> music -> subtitles -> master.

- concat_videos(): simple scene concat -> final.mp4 (backward compat)
- finish():       poora post-production pipeline (director.py post)
"""
import os
import subprocess

import audio
import lipsync
import media
import music
import subs
from state import load_plan, load_state, save_state


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


def finish(cfg, project, tts_engine=None, lipsync_engine=None,
           music_engine=None, subtitles=False, loudness=-14.0, language=None):
    """Poora post-production: TTS -> lip-sync -> concat -> music -> subs -> loudness."""
    plan = load_plan(project)
    state = load_state(project)
    if not plan:
        raise SystemExit("plan.json nahi mila — pehle 'director.py plan'")

    if tts_engine:
        cfg.setdefault("tts", {})["engine"] = tts_engine
    if lipsync_engine:
        cfg.setdefault("lipsync", {})["engine"] = lipsync_engine
    if music_engine:
        cfg.setdefault("music", {})["engine"] = music_engine
    if language:
        cfg.setdefault("subs", {})["language"] = language

    # ---- per scene: voice track + lip-sync ----
    vids = []
    for sc in plan["scenes"]:
        sid = int(sc["id"])
        meta = state.get(f"scene_{sid:02d}", {})
        raw = meta.get("video")
        if not raw:
            raise SystemExit(f"scene {sid} rendered nahi hai — pehle 'director.py render'")
        raw_path = os.path.join(project, "scenes", raw)
        src = raw_path
        track = audio.build_scene_track(cfg, project, sc)
        if track:
            meta["audio"] = os.path.basename(track)
            save_state(project, state)
            synced = lipsync.run_scene(cfg, project, sc, raw_path, track)
            if synced != raw_path:
                meta["lipsynced"] = os.path.basename(synced)
                save_state(project, state)
            src = synced
        vids.append(src)

    # ---- concat (synced nos use karo) ----
    list_file = os.path.join(project, "meta", "concat.txt")
    os.makedirs(os.path.dirname(list_file), exist_ok=True)
    with open(list_file, "w", encoding="utf-8") as f:
        for v in vids:
            f.write(f"file '{os.path.abspath(v)}'\n")
    out = os.path.join(project, "final.mp4")
    fps = cfg.get("scene_fps", 24)
    media.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
               "-vf", f"fps={fps}", "-c:v", "libx264", "-preset", "medium",
               "-crf", "19", "-pix_fmt", "yuv420p", out])
    print(f"[concat] -> {out}")

    # ---- music bed ----
    duration = sum(int(sc.get("seconds") or cfg.get("scene_seconds", 5))
                   for sc in plan["scenes"])
    score = music.generate_score(cfg, project, plan, duration)
    if score:
        tmp = out.replace(".mp4", "_music.mp4")
        media.duck_mix(out, score, tmp,
                       music_volume=float((cfg.get("music") or {}).get("volume", 0.18)))
        out = tmp
        print(f"[music] -> {out}")

    # ---- subtitles ----
    if subtitles:
        srt = subs.auto_srt(cfg, out, os.path.join(project, "meta", "subs.srt"))
        if srt:
            tmp = out.replace(".mp4", "_subs.mp4")
            out = burn_subtitles(out, srt, tmp)
            print(f"[subs] -> {out}")

    # ---- loudness master ----
    if loudness is not None:
        tmp = out.replace(".mp4", "_master.mp4")
        media.loudness_normalize(out, tmp, target=float(loudness))
        out = tmp
        print(f"[master] -> {out}")

    print("POST-PRODUCTION DONE ->", out)
    return out
