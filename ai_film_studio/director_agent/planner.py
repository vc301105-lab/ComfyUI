"""Story -> structured plan generation (planner)."""

import json
import os
import re

from prompts import read_prompt


def _normalize_scenes(scenes, seconds):
    out = []
    for i, sc in enumerate(scenes, start=1):
        sc = dict(sc or {})
        sc["id"] = int(sc.get("id") or i)
        sc.setdefault("name", f"Scene {sc['id']}")
        sc.setdefault("location", "studio")
        sc.setdefault("time", "day")
        sc.setdefault("shot", "medium shot")
        sc.setdefault("description", sc.get("name", ""))
        sc.setdefault("image_prompt", "")
        dlg = sc.get("dialogue") or []
        sc["dialogue"] = [
            {"character": str(d.get("character", "NARRATOR")),
             "line": str(d.get("line", "")),
             "emotion": str(d.get("emotion", "neutral"))}
            for d in dlg if isinstance(d, dict)
        ]
        sc["seconds"] = seconds
        out.append(sc)
    return out


def mock_plan(scene_count=3, seconds=5):
    """Demo plan for --mock runs (no LLM needed)."""
    return {
        "title": "Chai Aur Sitaare",
        "logline": "Ek chhoti si chai ki tapri ke malik ka sapna — Mumbai ki chhat pe ek raat.",
        "style": "cinematic, warm Indian tones, shallow depth of field, teal-orange grade",
        "characters": [
            {"name": "RAJU", "role": "hero", "appearance": "30-year-old Indian man, short black hair, light stubble, white shirt with rolled sleeves, brown eyes"},
            {"name": "MEERA", "role": "heroine", "appearance": "26-year-old Indian woman, long dark braid, red kurti, silver bangles, warm smile"}
        ],
        "scenes": [
            {"id": 1, "name": "Tapri ki chhat", "location": "Mumbai rooftop, golden hour",
             "time": "dawn", "shot": "wide establishing shot, slow dolly-in",
             "description": "A small rooftop chai tapri at dawn. Steam rising from a steel kettle, old radio playing, RAJU pouring chai into clay cups. Warm golden light, city skyline far behind.",
             "dialogue": [
                 {"character": "RAJU", "line": "Chai bina toh din shuru hi nahi hota, Meera.", "emotion": "happy"}
             ]},
            {"id": 2, "name": "Chhat pe baat", "location": "Rooftop railing", "time": "night",
             "shot": "over-the-shoulder medium shot",
             "description": "Night. Moonlit Mumbai skyline. RAJU and MEERA stand at the rooftop railing, clay cups in hand. City lights bokeh behind them. Cool blue night tones with warm lamp light.",
             "dialogue": [
                 {"character": "MEERA", "line": "Ek din hum sitaare ginte hue sapne poore karenge.", "emotion": "hopeful"}
             ]},
            {"id": 3, "name": "Sapna", "location": "Rooftop, stars", "time": "night",
             "shot": "low-angle wide shot, slow zoom-out",
             "description": "Both characters look up at a starry sky over the Mumbai skyline. Slow zoom-out revealing the whole rooftop. Warm string lights flicker. Cinematic, hopeful, dreamy atmosphere.",
             "dialogue": [
                 {"character": "RAJU", "line": "Sitaare dekhna hi toh sapna pura karne ka pehla step hai.", "emotion": "smiling"}
             ]}
        ][:scene_count]
    }


def build_plan(cfg, llm, idea, scene_count=8, seconds=None, mock=False):
    seconds = seconds or cfg.get("scene_seconds", 5)
    if mock:
        plan = mock_plan(scene_count=min(scene_count, 3), seconds=seconds)
        plan["_mock"] = True
        plan["_idea"] = idea
        plan["video_seconds_per_scene"] = seconds
        plan["scenes"] = _normalize_scenes(plan["scenes"], seconds)
        return plan

    system = read_prompt("01_plan.md").format(
        scene_count=scene_count,
        seconds=seconds,
        total_minutes=round(scene_count * seconds / 60, 1),
    )
    user = f"Idea: {idea}\n\nGenerate the film plan JSON now."
    plan = llm.chat_json(system, user)
    plan.setdefault("title", "Untitled Film")
    plan.setdefault("logline", idea)
    plan.setdefault("style", "cinematic")
    plan.setdefault("characters", [])
    plan.setdefault("scenes", [])
    plan["video_seconds_per_scene"] = seconds
    plan["scenes"] = _normalize_scenes(plan["scenes"], seconds)
    return plan


def save_summary_text(project, plan):
    lines = [plan.get("title", ""), plan.get("logline", ""), ""]
    for sc in plan["scenes"]:
        lines.append(f"## Scene {sc['id']}: {sc['name']} ({sc['time']}, {sc['shot']})")
        lines.append(sc["description"])
        for d in sc.get("dialogue", []):
            lines.append(f"  - {d['character']}: \"{d['line']}\" ({d['emotion']})")
        lines.append("")
    with open(os.path.join(project, "script.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
