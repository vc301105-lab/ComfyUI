"""One-shot pipeline + auto-QC-fix loop (director.py make).

run_make(): idea -> plan -> cast (optional) -> render (parallel) -> post ->
qc -> [auto re-render bad scenes] -> make_report.json + final master.
"""
import json
import os
import re
import sys

import assembler
import planner
import qcr
import renderer
import comfy
from state import load_plan, project_dir, save_plan, load_state


def slug(text, maxlen=40):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (s or "film")[:maxlen]


def _bad_scenes(rep):
    """Scenes needing re-render: missing / black / duration mismatch."""
    out = []
    for sid, s in rep["scenes"].items():
        if s.get("status") == "missing" or (s.get("black_ratio") or 0) > 0.05 \
                or s.get("duration_ok") is False:
            out.append(int(sid))
    return out


def run_make(cfg, idea, scene_count=8, mock=False, parallel=1, identity=False,
             tts=None, lipsync=None, music=None, subtitles=False, language=None,
             auto_fix=True, max_fix=2, dry_run=False, llm_model=None, verbose=True):
    name = cfg.get("project_name") or slug(idea)
    project = project_dir(cfg, name)

    # ---------- 1) plan ----------
    llm_obj = None
    if not mock:
        import llm as llm_mod
        llm_obj = llm_mod.LLM(cfg["ollama_url"], llm_model or cfg["llm_model"],
                              cfg["llm_temperature"])
    plan = planner.build_plan(cfg, llm_obj, idea, scene_count=scene_count, mock=mock)
    save_plan(project, plan)
    planner.save_summary_text(project, plan)
    print(f"[make] {plan['title']} -> {project} ({len(plan['scenes'])} scenes)")

    if dry_run:
        print(f"[make][dry] render plan: parallel={parallel} identity={identity}")
        renderer.render_project(cfg, project, dry_run=True, parallel=parallel,
                                keyframe_identity=identity)
        print("[make][dry] post engines:", tts or cfg["tts"].get("engine"),
              lipsync or cfg["lipsync"].get("engine"), music or cfg["music"].get("engine"))
        print("[make][dry] done (kuch render nahi hua)")
        return project, None

    # ---------- 2) cast (character bank) ----------
    if identity:
        client = comfy.ComfyClient(cfg["comfy_url"])
        renderer.cast_characters(cfg, client, project, plan)
        print("[make] cast done")

    # ---------- 3) render ----------
    renderer.render_project(cfg, project, parallel=parallel, keyframe_identity=identity)
    print("[make] render done")

    # ---------- 4) post ----------
    final = assembler.finish(
        cfg, project, tts_engine=tts, lipsync_engine=lipsync, music_engine=music,
        subtitles=subtitles, language=language,
        loudness=cfg.get("post", {}).get("loudness", -14.0))
    print(f"[make] post done -> {final}")

    # ---------- 5) qc + auto-fix loop ----------
    attempts = 0
    rep = qcr.review_project(project, expected_seconds=cfg.get("scene_seconds"))
    qcr.report_text(rep)
    bad = _bad_scenes(rep) if auto_fix else []
    while bad and attempts < max_fix:
        attempts += 1
        print(f"[make][fix] attempt {attempts}: re-rendering scenes {bad} "
              f"(seed +{attempts * 1000})")
        for sc in plan["scenes"]:
            if int(sc["id"]) in bad:
                sc["seed"] = (sc.get("seed") or 42) + attempts * 1000
        save_plan(project, plan)
        # stale state + purane keyframes clear karo taaki re-render ho
        from state import load_state, save_state
        st = load_state(project)
        kf_dir = os.path.join(project, "keyframes")
        for sid in bad:
            key = f"scene_{int(sid):02d}"
            st.pop(key, None)
            for f in os.listdir(kf_dir):
                if f.startswith(f"kf_{int(sid):02d}"):
                    os.remove(os.path.join(kf_dir, f))
        save_state(project, st)
        renderer.render_project(cfg, project, scenes=[str(s) for s in bad],
                                parallel=parallel, keyframe_identity=identity)
        final = assembler.finish(
            cfg, project, tts_engine=tts, lipsync_engine=lipsync,
            music_engine=music, subtitles=subtitles, language=language,
            loudness=cfg.get("post", {}).get("loudness", -14.0))
        rep = qcr.review_project(project, expected_seconds=cfg.get("scene_seconds"))
        qcr.report_text(rep)
        bad = _bad_scenes(rep)

    # ---------- 6) report ----------
    rep["fix_attempts"] = attempts
    rep["remaining_issues"] = bad
    rep["final"] = final
    rep["project"] = project
    rep["title"] = plan["title"]
    report_path = os.path.join(project, "meta", "make_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print(f"[make] report -> {report_path}")
    if bad:
        print(f"[make] WARNING: {len(bad)} scenes abhi bhi issue me hain: {bad}")
        return project, final
    print("[make] DONE ✅ (QC clean)")
    return project, final
