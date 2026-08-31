"""Scene rendering orchestration: keyframes + videos via ComfyUI."""

import json
import os

import comfy
import templates
from state import load_plan, load_state, save_state


def load_manifest():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "manifest.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def workflow_path(cfg, name):
    wf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(wf_dir, "workflows", name)


def _apply_manifest(wf_ui, m, positive=None, image=None, prefix=None):
    """Set values in the UI-format JSON per manifest (before conversion)."""
    nodes = {str(n.get("id")): n for n in wf_ui.get("nodes", [])}

    def set_widget(spec, value):
        if not spec or value is None:
            return
        node = nodes.get(str(spec["node"]))
        if node is None:
            raise comfy.ComfyError(f"Manifest node {spec['node']} workflow me nahi mila")
        wv = node.setdefault("widgets_values", [])
        field = spec.get("field")
        if isinstance(wv, dict):
            # VHS_VideoCombine jaise nodes: widgets_values pura dict hota hai
            if field:
                wv[field] = value
            else:
                raise comfy.ComfyError(
                    f"Node {spec['node']} ke widgets_values dict hain, field chahiye "
                    f"(manifest me 'field' set karein)")
            return
        idx = int(spec.get("widget", 0))
        while len(wv) <= idx:
            wv.append(None)
        if field:
            if not isinstance(wv[idx], dict):
                wv[idx] = {}
            wv[idx][field] = value
        else:
            wv[idx] = value

    if positive is not None:
        set_widget(m.get("positive"), positive)
    if image is not None:
        set_widget(m.get("image"), image)
    if prefix is not None:
        set_widget(m.get("output"), prefix)
    return nodes


def render_keyframe(cfg, client, project, scene, prompt, seed):
    """Generate one keyframe PNG via built-in SDXL txt2img workflow."""
    wf = templates.sdxl_txt2img_api(
        positive=prompt,
        negative=cfg["negative_prompt"],
        checkpoint=cfg["image_checkpoint"],
        width=cfg.get("keyframe_width", 1024),
        height=cfg.get("keyframe_height", 1024),
        seed=seed,
        filename_prefix=f"ai_film_studio/{os.path.basename(project)}/kf_{scene['id']:02d}",
    )
    pid = client.submit(wf)
    print(f"[keyframe] scene {scene['id']} submitted ({pid})")
    entry = client.wait(pid)
    saved = client.download_outputs(entry, os.path.join(project, "keyframes"))
    if not saved:
        raise comfy.ComfyError(f"Keyframe scene {scene['id']}: no output file")
    # SaveImage naming: filename prefix with subfolder -> pick newest image
    return max(saved, key=os.path.getmtime)


def render_scene(cfg, client, project, scene, plan, wf_name, scene_file=None,
                 keyframe=None, seed=None):
    """Render one scene video. scene_file: keyframe path (i2v) or None (t2v)."""
    wf_path = workflow_path(cfg, wf_name)
    with open(wf_path, "r", encoding="utf-8") as f:
        wf_ui = json.load(f)
    manifest = load_manifest()[wf_name]

    positive = scene.get("image_prompt") or scene.get("description", "")
    world = plan.get("style", "cinematic")
    positive = f"{positive}, {world}" if world and world not in positive else positive

    if manifest.get("requires_gemma_api"):
        raise comfy.ComfyError(
            f"{wf_name} me Gemma API key chahiye (LTX-2.3 advanced). "
            "ComfyUI me key set karke phir try karein, ya Wan/Hunyuan workflow use karein.")

    image_name = None
    if manifest.get("image") and scene_file:
        img = client.upload_image(scene_file)
        image_name = img["name"]

    prefix = f"{os.path.basename(project)}/scene_{scene['id']:02d}"
    _apply_manifest(wf_ui, manifest, positive=positive, image=image_name, prefix=prefix)
    api_wf = client.ui_to_api(wf_ui)

    if seed is not None:
        # best-effort seed override: find sampler nodes
        for nid, node in api_wf.items():
            if "Sampler" in node.get("class_type", "") and "seed" in node["inputs"]:
                node["inputs"]["seed"] = seed

    pid = client.submit(api_wf)
    print(f"[scene {scene['id']}] submitted ({wf_name}) {pid}")
    entry = client.wait(pid)
    saved = client.download_outputs(entry, os.path.join(project, "scenes"),
                                    suffix=f"_s{scene['id']:02d}")
    # prefer videos
    vids = [s for s in saved if s.lower().endswith((".mp4", ".webm", ".mov", ".gif"))]
    return (vids or saved)[0]


def render_project(cfg, project, wf_name=None, scenes=None, dry_run=False,
                   make_keyframes=True):
    """Render keyframes + videos for all (or selected) scenes."""
    plan = load_plan(project)
    if not plan:
        raise SystemExit("plan.json nahi mila — pehle: director.py plan ...")
    state = load_state(project)
    wf_name = wf_name or cfg.get("video_workflow")
    manifest = load_manifest().get(wf_name)
    if not manifest:
        raise SystemExit(f"Workflow '{wf_name}' manifest.json me nahi hai")

    want = {int(s) for s in (scenes or [])}
    todo = [s for s in plan["scenes"] if (not want) or int(s["id"]) in want]

    if dry_run:
        print(f"DRY-RUN: {len(todo)} scenes render honge (workflow={wf_name})")
        for s in todo:
            print(f"  scene {s['id']}: {s['name']} | prompt: "
                  f"{(s.get('image_prompt') or s['description'])[:80]}...")
        return

    client = comfy.ComfyClient(cfg["comfy_url"])
    for scene in todo:
        sid = int(scene["id"])
        key = f"scene_{sid:02d}"
        if state.get(key, {}).get("video"):
            print(f"[skip] scene {sid} already rendered")
            continue
        scene_meta = state.setdefault(key, {})

        # 1) keyframe (i2v workflows only)
        kf_path = None
        if manifest.get("image"):
            if make_keyframes:
                existing = [f for f in os.listdir(os.path.join(project, "keyframes"))
                            if f.startswith(f"kf_{sid:02d}")]
                if existing:
                    kf_path = os.path.join(project, "keyframes", existing[-1])
                else:
                    prompt = scene.get("image_prompt") or scene.get("description", "")
                    prompt = f"{prompt}, {plan.get('style','cinematic')}"
                    kf_path = render_keyframe(cfg, client, project, scene, prompt,
                                              seed=scene.get("seed", 42 + sid))
                    print(f"[keyframe] scene {sid} -> {kf_path}")
                scene_meta["keyframe"] = os.path.basename(kf_path)
            elif scene.get("keyframe_path"):
                kf_path = scene["keyframe_path"]

        # 2) scene video
        video = render_scene(cfg, client, project, scene, plan, wf_name,
                             scene_file=kf_path, seed=scene.get("seed", 42 + sid))
        scene_meta["video"] = os.path.basename(video)
        scene_meta["workflow"] = wf_name
        print(f"[scene {sid}] -> {video}")
        save_state(project, state)

    print("Render complete. Next: director.py assemble")
