"""Music/SFX score generation (ACE-Step / YuE / custom engine hooks).

config.music.command:
  acestep: python cli.py --model ... --prompt "%PROMPT%" --duration %DURATION% --output "%OUT%"
  custom:  koi bhi command %PROMPT%/%DURATION%/%OUT% ke saath
"""
import os

import media


def generate_score(cfg, project, plan, duration):
    m = cfg.get("music") or {}
    engine = m.get("engine", "none")
    if engine == "none":
        return None
    cmd = m.get("command")
    if not cmd:
        raise SystemExit(f"music.engine={engine} hai lekin music.command khali hai")

    out_dir = os.path.join(project, "music")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "score.wav")
    if os.path.exists(out):
        return out
    media.template_command(cfg, "music", {
        "PROMPT": m.get("prompt", "cinematic emotional score"),
        "DURATION": int(duration),
        "OUT": out,
    })
    return out if os.path.exists(out) else None
