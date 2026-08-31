"""Multi-language dubbing: translate dialogues -> alt TTS track -> remux.

Flow (director.py dub):
 1. translate_lines()   — Ollama se targeted language me saari lines (JSON)
 2. audio.build_scene_track(out_name=...) — har scene ka alt voice track
 3. concat alt tracks  — ek <lang> audio WAV
 4. mux into final_<lang>.mp4 (video copy, audio replace)
"""
import json
import os

import audio
import media
from assembler import mux_audio
from state import load_plan, load_state, save_state


def translate_lines(cfg, plan, target="en", llm=None):
    """Saari dialogues -> target lang. Return {scene_id: [lines]} + saves meta."""
    if not llm:
        raise SystemExit("dub ke liye Ollama chahiye (--mock nahi) — ya meta/dub_<lang>.json "
                         "manual bana kar dein")
    items = {}
    for sc in plan["scenes"]:
        for i, d in enumerate(sc.get("dialogue") or []):
            items[f"{int(sc['id'])}:{i}"] = d.get("line", "")
    system = (
        "Tum ek film dialogue translator ho. Hinglish dialogues ko target language me "
        "translate karo — natural, spoken style, expression bana rahe. "
        "Output SIRF JSON: {\"translations\": {\"SCENE_ID:LINE_ID\": \"translated text\"}}"
    )
    user = json.dumps(items, ensure_ascii=False)
    data = llm.chat_json(system, user)
    return data.get("translations", {})


def _patched_scene(scene, translations):
    sc = dict(scene)
    dlg = []
    for i, d in enumerate(scene.get("dialogue") or []):
        nd = dict(d)
        key = f"{int(scene['id'])}:{i}"
        if key in translations:
            nd["line"] = translations[key]
        dlg.append(nd)
    sc["dialogue"] = dlg
    return sc


def dub_project(cfg, project, target="en", llm=None, translate=True, make_tracks=True):
    plan = load_plan(project)
    if not plan:
        raise SystemExit("plan.json nahi mila")
    state = load_state(project)
    meta_dir = os.path.join(project, "meta")
    os.makedirs(meta_dir, exist_ok=True)
    trans_path = os.path.join(meta_dir, f"dub_{target}.json")
    translations = {}
    if os.path.exists(trans_path):
        with open(trans_path, encoding="utf-8") as f:
            translations = json.load(f)
    elif translate:
        translations = translate_lines(cfg, plan, target, llm)
        with open(trans_path, "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)
        print(f"[dub] translated {len(translations)} lines -> {trans_path}")
    else:
        raise SystemExit(f"meta/dub_{target}.json nahi hai — pehle translate karein")

    tracks = []
    if make_tracks:
        for sc in plan["scenes"]:
            sid = int(sc["id"])
            meta = state.get(f"scene_{sid:02d}", {})
            raw = meta.get("video")
            if not raw:
                raise SystemExit(f"scene {sid} rendered nahi hai")
            psc = _patched_scene(sc, translations)
            track = audio.build_scene_track(
                cfg, project, psc, force=False, out_name=f"scene_{sid:02d}_{target}")
            if track:
                tracks.append(track)
                print(f"[dub] S{sid} ({target}) -> {track}")
        if tracks:
            combined = os.path.join(project, "audio", f"dub_{target}.wav")
            media.concat_audio(tracks, combined)
            video = os.path.join(project, "final.mp4")
            if os.path.exists(video):
                out = os.path.join(project, f"final_{target}.mp4")
                mux_audio(video, combined, out)
                print(f"[dub] -> {out}")
                return out
    print("[dub] tracks ready (final.mp4 pe mux karne ke liye dub phir chalein)")
    return None
