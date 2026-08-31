"""Lip-sync per scene (LatentSync / Wav2Lip / MuseTalk / custom engine hooks).

Engine CLI Har user ke setup ke hisaab se configure hota hai config.lipsync.command:
  latentsync: python scripts/inference.py --video_path "%VIDEO%" --audio_path "%AUDIO%" --output_path "%OUT%"
  wav2lip:    python inference.py --checkpoint_path ckpt.pth --face "%VIDEO%" --audio "%AUDIO%" --outfile "%OUT%"
  custom:     koi bhi command %VIDEO%/%AUDIO%/%OUT% ke saath
"""
import os
import subprocess

import media


def _command(cfg):
    e = (cfg.get("lipsync") or {}).get("engine", "none")
    if e == "none":
        return None
    c = (cfg.get("lipsync") or {}).get("command")
    if c:
        return c
    if e == "latentsync":
        return ('python scripts/inference.py --video_path "%VIDEO%" '
                '--audio_path "%AUDIO%" --output_path "%OUT%"')
    if e == "wav2lip":
        return ('python inference.py --checkpoint_path checkpoint.pth '
                '--face "%VIDEO%" --audio "%AUDIO%" --outfile "%OUT%"')
    return None


def run_scene(cfg, project, scene, video, audio):
    """video + audio -> lip-synced video. Fail hone par original video return."""
    ls = cfg.get("lipsync") or {}
    cmd = _command(cfg)
    if not cmd:
        print(f"[lipsync] S{scene['id']}: engine={ls.get('engine')} -> skip")
        return video
    if not audio or not os.path.exists(audio):
        print(f"[lipsync] S{scene['id']}: audio nahi mila -> skip")
        return video

    out = os.path.join(project, "scenes", f"scene_{int(scene['id']):02d}_synced.mp4")
    if os.path.exists(out):
        return out
    cmd_t = (cmd.replace("%VIDEO%", os.path.abspath(video))
                .replace("%AUDIO%", os.path.abspath(audio))
                .replace("%OUT%", os.path.abspath(out)))
    print(f"[lipsync] S{scene['id']}: {cmd_t[:140]}")
    try:
        subprocess.run(cmd_t, shell=True, check=True, timeout=7200)
    except Exception as e:
        print(f"[lipsync] S{scene['id']} FAILED ({e}) — original video use hoga")
        return video
    return out if os.path.exists(out) else video
