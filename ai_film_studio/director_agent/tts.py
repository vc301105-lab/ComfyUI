"""Optional TTS: engines (none | chatterbox | custom command).

chatterbox: expects `chatterbox` CLI on PATH (pip install chatterbox-tts).
custom:     command template with %TEXT% and %OUT% placeholders in config.
"""

import os
import subprocess


def generate_line(cfg, text, out_path, speaker=None):
    engine = (cfg.get("tts") or {}).get("engine", "none")
    if engine == "none":
        return None
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if engine == "chatterbox":
        cmd = ["chatterbox", "--text", text, "--output_path", out_path]
        if speaker:
            cmd += ["--model_name", speaker]
        subprocess.run(cmd, check=True, timeout=300)
        return out_path
    if engine == "custom":
        template = (cfg.get("tts") or {}).get("command", "")
        if not template:
            raise SystemExit("tts.engine=custom but tts.command empty")
        parts = template.replace("%TEXT%", text).replace("%OUT%", out_path)
        subprocess.run(parts, shell=True, check=True, timeout=600)
        return out_path
    raise SystemExit(f"Unknown tts engine: {engine}")


def generate_audio_track(cfg, project, plan):
    """Per-dialogue WAV files, then concat into scenes/<scene>_audio.wav (in order)."""
    from state import load_state
    state = load_state(project)
    wavs = []
    for sc in plan["scenes"]:
        # one wav per scene containing all its dialogue lines (simplified concat)
        lines = sc.get("dialogue") or []
        scene_wavs = []
        for i, d in enumerate(lines):
            out = os.path.join(project, "audio", f"scene_{int(sc['id']):02d}_line{i:02d}.wav")
            p = generate_line(cfg, d.get("line", ""), out, speaker=d.get("character"))
            if p:
                scene_wavs.append(p)
        if scene_wavs:
            combined = os.path.join(project, "audio", f"scene_{int(sc['id']):02d}_track.wav")
            listing = os.path.join(project, "audio", f"scene_{int(sc['id']):02d}.list")
            with open(listing, "w") as f:
                for w in scene_wavs:
                    f.write(f"file '{os.path.abspath(w)}'\n")
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                            "-i", listing, combined], check=True)
            wavs.append(combined)
    return wavs
