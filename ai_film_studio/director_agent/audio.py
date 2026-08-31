"""Per-scene dialogue TTS tracks (engine hooks + ffmpeg assembly).

Engines (config.tts.engine): none | chatterbox | custom
- chatterbox: default CLI template use hota hai (agar command khali hai)
- custom: lazim config.tts.command with %TEXT%/%OUT%/%MODEL%
"""
import os
import subprocess

import media
from state import load_state, save_state


def _command(cfg):
    e = (cfg.get("tts") or {}).get("engine", "none")
    if e == "none":
        return None
    c = (cfg.get("tts") or {}).get("command")
    if c:
        return c
    if e == "chatterbox":
        return 'chatterbox --text "%TEXT%" --output_path "%OUT%"'
    return None


def build_scene_track(cfg, project, scene, force=False, out_name=None):
    """Scene ke dialogues -> ek normalized WAV track (silence gaps ke saath).

    out_name: default 'scene_XX_track' — dub me 'scene_XX_<lang>' pass hota hai.
    """
    lines = scene.get("dialogue") or []
    if not lines:
        return None
    tts = cfg.get("tts") or {}
    cmd = _command(cfg)
    if not cmd:
        print(f"[tts] scene {scene['id']}: engine={tts.get('engine')} -> skip")
        return None
    if not media.which("ffmpeg"):
        raise SystemExit("ffmpeg missing — TTS track assembly ke liye zaroori hai")

    audio_dir = os.path.join(project, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    sr = int(tts.get("sample_rate", 48000))
    pause = max(0.0, float(tts.get("pause", 0.4)))
    stem = out_name or f"scene_{int(scene['id']):02d}_track"

    track = os.path.join(audio_dir, f"{stem}.wav")
    if os.path.exists(track) and not force:
        return track
    parts = [media.make_silence(os.path.join(audio_dir, f"{stem}_lead.wav"), 0.25, sr)]

    for i, d in enumerate(lines):
        raw = os.path.join(audio_dir, f"{stem}_line{i:02d}.wav")
        norm = raw.replace(".wav", "_norm.wav")
        if not os.path.exists(raw) or force:
            cmd_t = cmd.replace("%TEXT%", str(d.get("line", ""))) \
                       .replace("%OUT%", raw) \
                       .replace("%MODEL%", str(tts.get("model", "")))
            print(f"[tts] S{scene['id']} L{i}: {cmd_t[:120]}")
            subprocess.run(cmd_t, shell=True, check=True, timeout=3600)
        if os.path.exists(raw):
            media.normalize_audio(raw, norm, sr)
            parts.append(norm)
            parts.append(media.make_silence(
                os.path.join(audio_dir, f"{stem}_gap{i}.wav"), pause, sr))
        else:
            print(f"[tts] S{scene['id']} L{i}: output nahi bana — skip")
    media.concat_audio(parts, track)
    return track


def apply_state(cfg, project, scene, track):
    state = load_state(project)
    key = f"scene_{int(scene['id']):02d}"
    state.setdefault(key, {})["audio"] = os.path.basename(track)
    save_state(project, state)
