#!/usr/bin/env python3
"""AI Film Studio — Director Agent CLI.

Usage (run from ai_film_studio/director_agent/):
  python director.py plan    --idea "Ek chai ki tapri ka sapna" [--scenes 8] [--mock]
  python director.py plan    --idea "..." --scenes 8 --llm-model qwen3:32b
  python director.py render  [--scene 1,2,3] [--workflow wan22_5b_i2v_example.json] [--dry-run]
  python director.py assemble [--with-audio] [--subtitles]
  python director.py status
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config as config_mod
import comfy  # noqa: E402
import llm  # noqa: E402
import planner  # noqa: E402
import storyboard  # noqa: E402
import assembler  # noqa: E402
import tts  # noqa: E402
import renderer  # noqa: E402
from state import load_plan, load_state, project_dir, save_plan  # noqa: E402


def cmd_plan(args, cfg):
    project = project_dir(cfg, args.project)
    print(f"[project] {project}")
    if args.mock:
        print("[llm] MOCK mode — Ollama ke bina demo Hinglish plan")
        llm_obj = None
    else:
        llm_obj = llm.LLM(cfg["ollama_url"], args.llm_model or cfg["llm_model"],
                          cfg["llm_temperature"])
    plan = planner.build_plan(cfg, llm_obj, args.idea,
                              scene_count=args.scenes, mock=args.mock)
    save_plan(project, plan)
    planner.save_summary_text(project, plan)
    kfs = storyboard.build_keyframe_prompts(plan, llm=llm_obj if not args.mock else None)
    plan["keyframes"] = [{"scene_id": k["scene_id"], "prompt": k["prompt"]} for k in kfs]
    save_plan(project, plan)
    print(f"[plan] title: {plan['title']} | scenes: {len(plan['scenes'])}")
    for k in kfs:
        print(f"  S{k['scene_id']}: {k['prompt'][:100]}...")
    if args.mock:
        print("NOTE: mock plan hai. Real LLM ke liye --mock hata ke chalein "
              "(Ollama chahiye).")
    print("Next: python director.py render --dry-run")


def cmd_render(args, cfg):
    project = project_dir(cfg, args.project)
    renderer.render_project(cfg, project, wf_name=args.workflow or cfg["video_workflow"],
                            scenes=args.scene.split(",") if args.scene else None,
                            dry_run=args.dry_run,
                            make_keyframes=not args.no_keyframes,
                            parallel=args.parallel,
                            keyframe_identity=args.identity)


def cmd_cast(args, cfg):
    project = project_dir(cfg, args.project)
    plan = load_plan(project)
    if not plan:
        raise SystemExit("plan.json nahi mila — pehle: director.py plan ...")
    if dry := args.dry_run:
        print(f"[cast][dry] {len(plan.get('characters', []))} characters")
        renderer.cast_characters(cfg, None, project, plan, dry_run=True)
        return
    client = comfy.ComfyClient(cfg["comfy_url"])
    renderer.cast_characters(cfg, client, project, plan, dry_run=False)
    print("Next: director.py render --identity")


def cmd_assemble(args, cfg):
    project = project_dir(cfg, args.project)
    video = assembler.concat_videos(project, fps=cfg["scene_fps"])
    if args.with_audio:
        print("[tts] Generating dialogue audio...")
        wavs = tts.generate_audio_track(cfg, project, load_plan(project))
        if wavs:
            video = assembler.mux_audio(video, wavs[-1])   # demo: single combined
        else:
            print("[tts] no audio generated (engine=none?)")
    if args.subtitles:
        srt = os.path.join(project, "meta", "subs.srt")
        if os.path.exists(srt):
            video = assembler.burn_subtitles(video, srt)
        else:
            print(f"[subs] {srt} nahi mila — WhisperX se banao, phir --subtitles")
    print(f"DONE -> {video}")


def cmd_post(args, cfg):
    project = project_dir(cfg, args.project)
    out = assembler.finish(
        cfg, project,
        tts_engine=args.tts, lipsync_engine=args.lipsync,
        music_engine=args.music, subtitles=args.subtitles,
        loudness=None if args.no_loudness else cfg.get("post", {}).get("loudness", -14.0),
        language=args.language)
    print(f"POPCORN TIME 🍿 -> {out}")


def cmd_qc(args, cfg):
    import qcr  # noqa: E402
    project = project_dir(cfg, args.project)
    rep = qcr.review_project(project, expected_seconds=cfg.get("scene_seconds"))
    text = qcr.report_text(rep)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2, ensure_ascii=False)
        print(f"[qc] report -> {args.json_out}")
    if args.strict and (rep["summary"]["scenes_missing"] or "black_frames" in rep["summary"]["issues"]
                        and rep["summary"]["issues"]["black_frames"]):
        raise SystemExit("QC FAILED (--strict): fix issues phir dobara")


def cmd_dub(args, cfg):
    import dub  # noqa: E402
    project = project_dir(cfg, args.project)
    llm_obj = None
    if not args.dry_run:
        llm_obj = llm.LLM(cfg["ollama_url"], args.llm_model or cfg["llm_model"],
                          cfg["llm_temperature"])
    translations = None
    if args.dry_run:
        plan = load_plan(project)
        if not plan:
            raise SystemExit("plan.json nahi mila")
        total = sum(len(sc.get("dialogue") or []) for sc in plan["scenes"])
        print(f"[dub][dry] {total} lines translate hue gi -> {args.lang}")
        return
    plan = load_plan(project)
    if not plan:
        raise SystemExit("plan.json nahi mila")
    trans = {}
    tpath = os.path.join(project, "meta", f"dub_{args.lang}.json")
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as f:
            trans = json.load(f)
        print(f"[dub] using existing translations ({len(trans)})")
    else:
        trans = dub.translate_lines(cfg, plan, args.lang, llm_obj)
        with open(tpath, "w", encoding="utf-8") as f:
            json.dump(trans, f, indent=2, ensure_ascii=False)
    out = dub.dub_project(cfg, project, target=args.lang, llm=None, translate=False)
    print(f"DUB DONE -> {out}")


def cmd_make(args, cfg):
    import pipeline  # noqa: E402
    if args.dry_run:
        cfg["project_name"] = args.project
    else:
        cfg["project_name"] = args.project if args.project != "myfilm" else None
    project, final = pipeline.run_make(
        cfg, args.idea, scene_count=args.scenes, mock=args.mock,
        parallel=args.parallel, identity=args.identity,
        tts=args.tts, lipsync=args.lipsync, music=args.music,
        subtitles=args.subtitles, language=args.language,
        auto_fix=not args.no_autofix, max_fix=args.max_fix,
        dry_run=args.dry_run, llm_model=args.llm_model)
    if final:
        print(f"READY 🍿 -> {final}")


def cmd_export(args, cfg):
    import export  # noqa: E402
    project = project_dir(cfg, args.project)
    kind = args.kind
    if kind == "trailer":
        ids = None
        if args.scene:
            ids = [int(x) for x in args.scene.split(",")]
        out = export.make_trailer(project, scene_ids=ids, n=args.n)
    elif kind == "poster":
        sid = int(args.scene) if args.scene else None
        out = export.make_poster(project, scene_id=sid)
    elif kind == "credits":
        out = export.make_credits(project, seconds=args.seconds)
    elif kind == "preset":
        out = export.platform_preset(project, preset=args.preset)
    else:
        raise SystemExit(f"unknown kind: {kind}")
    print(f"[export] {kind} -> {out}" if out else "[export] FAILED (upar dekhein)")


def cmd_status(args, cfg):
    project = project_dir(cfg, args.project)
    plan = load_plan(project)
    state = load_state(project)
    if not plan:
        print("No plan yet. Run: director.py plan --idea '...'")
        return
    done = sum(1 for s in plan["scenes"] if state.get(f"scene_{int(s['id']):02d}", {}).get("video"))
    print(f"Project: {plan['title']} | scenes rendered: {done}/{len(plan['scenes'])}")
    for s in plan["scenes"]:
        m = state.get(f"scene_{int(s['id']):02d}", {})
        print(f"  S{s['id']}: keyframe={'OK' if m.get('keyframe') else '-'} "
              f"video={'OK' if m.get('video') else '-'}")


def main():
    p = argparse.ArgumentParser(description="AI Film Studio Director Agent")
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("plan", help="Idea -> script + storyboard (needs Ollama, ya --mock)")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--idea", default="Ek chhoti chai ki tapri ke malik ka sapna")
    sp.add_argument("--scenes", type=int, default=8)
    sp.add_argument("--llm-model", default=None)
    sp.add_argument("--mock", action="store_true")

    sp = sub.add_parser("render", help="Scenes -> keyframes + videos via ComfyUI")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--workflow", default=None)
    sp.add_argument("--scene", default=None)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--no-keyframes", action="store_true")
    sp.add_argument("--parallel", type=int, default=1,
                    help="Multi-GPU: kitne ComfyUI workers pe parallel render")
    sp.add_argument("--identity", action="store_true",
                    help="Character reference + IP-Adapter consistency (pehle 'cast' chalein)")

    sp = sub.add_parser("cast", help="Plan ke characters ke reference images banao")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("assemble", help="Scene videos -> final.mp4 (ffmpeg)")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--with-audio", action="store_true")
    sp.add_argument("--subtitles", action="store_true")

    sp = sub.add_parser("post", help="Post-production: voice + lip-sync + music + subs -> master")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--tts", default=None, choices=["none", "chatterbox", "custom"])
    sp.add_argument("--lipsync", default=None,
                    choices=["none", "latentsync", "wav2lip", "custom"])
    sp.add_argument("--music", default=None, choices=["none", "acestep", "custom"])
    sp.add_argument("--subtitles", action="store_true")
    sp.add_argument("--language", default=None)
    sp.add_argument("--no-loudness", action="store_true")

    sp = sub.add_parser("make", help="ONE-SHOT: plan->cast->render->post->qc->auto-fix")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--idea", default="Ek chhoti chai ki tapri ke malik ka sapna")
    sp.add_argument("--scenes", type=int, default=8)
    sp.add_argument("--llm-model", default=None)
    sp.add_argument("--mock", action="store_true")
    sp.add_argument("--parallel", type=int, default=1)
    sp.add_argument("--identity", action="store_true")
    sp.add_argument("--tts", default=None, choices=["none", "chatterbox", "custom"])
    sp.add_argument("--lipsync", default=None,
                    choices=["none", "latentsync", "wav2lip", "custom"])
    sp.add_argument("--music", default=None, choices=["none", "acestep", "custom"])
    sp.add_argument("--subtitles", action="store_true")
    sp.add_argument("--language", default=None)
    sp.add_argument("--no-autofix", action="store_true")
    sp.add_argument("--max-fix", type=int, default=2)
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("export", help="Trailer / poster / credits / platform preset")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--kind", choices=["trailer", "poster", "credits", "preset"],
                    default="trailer")
    sp.add_argument("--scene", default=None)
    sp.add_argument("--n", type=int, default=5)
    sp.add_argument("--seconds", type=int, default=6)
    sp.add_argument("--preset", default="youtube",
                    choices=["youtube", "shorts", "reels", "square"])

    sp = sub.add_parser("qc", help="QC/review: scene checks + continuity report")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--json-out", default=None)
    sp.add_argument("--strict", action="store_true")

    sp = sub.add_parser("dub", help="Multi-language dubbing (Ollama translate + TTS + remux)")
    sp.add_argument("--project", default="myfilm")
    sp.add_argument("--lang", default="en")
    sp.add_argument("--llm-model", default=None)
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("status", help="Project render progress")
    sp.add_argument("--project", default="myfilm")

    args = p.parse_args()
    cfg = config_mod.load_config(args.config)
    {"plan": cmd_plan, "cast": cmd_cast, "render": cmd_render,
     "assemble": cmd_assemble, "post": cmd_post, "qc": cmd_qc,
     "dub": cmd_dub, "make": cmd_make, "export": cmd_export,
     "status": cmd_status}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
