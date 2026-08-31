"""Scene rendering orchestration: cast -> keyframes -> videos via ComfyUI.

Supports:
- keyframe engines: sdxl | ipadapter (character ref) | qwen_image
- multi-GPU parallel rendering (--parallel N, comfy_urls list)
- resumable state (per-scene, thread-safe)
"""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# ------------------------------------------------------------------ keyframes
def render_keyframe(cfg, client, project, scene, prompt, seed,
                    ref_image=None, engine=None):
    """Generate one keyframe PNG. engine: sdxl | ipadapter | qwen_image."""
    engine = engine or cfg.get("keyframe_engine", "sdxl")
    prefix = f"ai_film_studio/{os.path.basename(project)}/kf_{scene['id']:02d}"

    if engine == "ipadapter":
        if not ref_image or not os.path.exists(ref_image):
            raise comfy.ComfyError(
                "keyframe_engine=ipadapter ke liye character reference image chahiye. "
                "Pehle: director.py cast")
        up = client.upload_image(ref_image)
        wf = templates.sdxl_ipadapter_txt2img_api(
            positive=prompt, negative=cfg["negative_prompt"],
            checkpoint=cfg["image_checkpoint"], ref_image=up["name"],
            width=cfg.get("keyframe_width", 1024),
            height=cfg.get("keyframe_height", 1024), seed=seed,
            filename_prefix=prefix,
            preset=cfg.get("ipadapter_preset", "PLUS FACE (portraits)"),
            weight=cfg.get("ipadapter_weight", 0.8),
            clip_vision=cfg.get("ipadapter_clip",
                                "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"))
    elif engine == "qwen_image":
        wf = templates.qwen_image_txt2img_api(
            positive=prompt, negative=cfg["negative_prompt"],
            unet=cfg["qwen_unet"], clip=cfg["qwen_clip"], vae=cfg["qwen_vae"],
            width=cfg.get("keyframe_width", 1024),
            height=cfg.get("keyframe_height", 1024), seed=seed,
            filename_prefix=prefix)
    else:  # sdxl
        wf = templates.sdxl_txt2img_api(
            positive=prompt, negative=cfg["negative_prompt"],
            checkpoint=cfg["image_checkpoint"],
            width=cfg.get("keyframe_width", 1024),
            height=cfg.get("keyframe_height", 1024), seed=seed,
            filename_prefix=prefix)

    pid = client.submit(wf)
    print(f"[keyframe] scene {scene['id']} ({engine}) submitted ({pid})")
    entry = client.wait(pid)
    saved = client.download_outputs(entry, os.path.join(project, "keyframes"))
    if not saved:
        raise comfy.ComfyError(f"Keyframe scene {scene['id']}: no output file")
    return max(saved, key=os.path.getmtime)


def cast_characters(cfg, client, project, plan, dry_run=False):
    """Generate one reference image per character (sdxl, no IP-Adapter)."""
    chars = plan.get("characters", [])
    out_dir = os.path.join(project, "characters")
    os.makedirs(out_dir, exist_ok=True)
    state = load_state(project)
    state.setdefault("characters", {})
    for ch in chars:
        name = ch.get("name", "CHAR").strip().replace(" ", "_")
        existing = state["characters"].get(name)
        if existing and os.path.exists(os.path.join(project, "characters", existing)):
            print(f"[cast] {name}: already exists ({existing})")
            continue
        prompt = (ch.get("appearance", "") + ", " +
                  plan.get("style", "cinematic") +
                  ", portrait, upper body, studio lighting, photorealistic, "
                  "highly detailed, film still")
        if dry_run:
            print(f"[cast][dry] {name}: {prompt[:90]}...")
            continue
        pid_path = render_keyframe(  # engine forced sdxl
            cfg, client, project,
            {"id": 0, "name": name}, prompt, seed=1000 + hash(name) % 10000,
            engine="sdxl")
        # move from keyframes to characters with the character name
        final = os.path.join(out_dir, f"{name}.png")
        os.replace(pid_path, final)
        state["characters"][name] = f"{name}.png"
        print(f"[cast] {name} -> {final}")
    save_state(project, state)
    return state["characters"]


def _pick_ref(cfg, project, plan, state, scene):
    """First character in scene dialogue -> reference image path (if any)."""
    if not cfg.get("keyframe_identity"):
        return None
    chars = state.get("characters", {})
    for d in scene.get("dialogue", []):
        name = d.get("character", "").strip().replace(" ", "_")
        f = chars.get(name)
        if f:
            p = os.path.join(project, "characters", f)
            if os.path.exists(p):
                return p
    return None


# ------------------------------------------------------------------- scenes
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
                   make_keyframes=True, parallel=1, comfy_urls=None,
                   keyframe_identity=None):
    """Render keyframes + videos for all (or selected) scenes.

    parallel > 1: scenes alag-alag ComfyUI instances (multi-GPU) pe submit
    hote hain — comfy_urls list se URLs milega.
    """
    plan = load_plan(project)
    if not plan:
        raise SystemExit("plan.json nahi mila — pehle: director.py plan ...")
    state = load_state(project)
    wf_name = wf_name or cfg.get("video_workflow")
    manifest = load_manifest().get(wf_name)
    if not manifest:
        raise SystemExit(f"Workflow '{wf_name}' manifest.json me nahi hai")
    if keyframe_identity is not None:
        cfg["keyframe_identity"] = keyframe_identity

    want = {int(s) for s in (scenes or [])}
    todo = [s for s in plan["scenes"] if (not want) or int(s["id"]) in want]

    if dry_run:
        print(f"DRY-RUN: {len(todo)} scenes (workflow={wf_name}, "
              f"parallel={parallel}, identity={cfg.get('keyframe_identity')})")
        for s in todo:
            print(f"  scene {s['id']}: {s['name']} | prompt: "
                  f"{(s.get('image_prompt') or s['description'])[:80]}...")
        return

    # multi-GPU clients
    urls = comfy_urls or cfg.get("comfy_urls") or [cfg["comfy_url"]]
    n_workers = max(1, min(int(parallel), len(urls)))
    clients = [comfy.ComfyClient(urls[i % len(urls)]) for i in range(n_workers)]
    if n_workers > 1:
        print(f"[parallel] {n_workers} workers -> {urls}")

    lock = threading.Lock()

    def run_scene(scene):
        sid = int(scene["id"])
        key = f"scene_{sid:02d}"
        with lock:
            if state.get(key, {}).get("video"):
                print(f"[skip] scene {sid} already rendered")
                return scene, None, None
        # pick client for this scene
        client = clients[sid % len(clients)]

        # 1) keyframe (i2v workflows)
        kf_path = None
        if manifest.get("image"):
            if make_keyframes:
                existing = [f for f in os.listdir(os.path.join(project, "keyframes"))
                            if f.startswith(f"kf_{sid:02d}")]
                if existing:
                    kf_path = os.path.join(project, "keyframes", existing[-1])
                else:
                    prompt = scene.get("image_prompt") or scene.get("description", "")
                    prompt = f"{prompt}, {plan.get('style', 'cinematic')}"
                    ref = _pick_ref(cfg, project, plan, state, scene)
                    if ref:
                        print(f"[scene {sid}] identity ref: {os.path.basename(ref)}")
                    kf_path = render_keyframe(cfg, client, project, scene, prompt,
                                              seed=scene.get("seed", 42 + sid),
                                              ref_image=ref)
                    print(f"[keyframe] scene {sid} -> {kf_path}")
                with lock:
                    state.setdefault(key, {})["keyframe"] = os.path.basename(kf_path)
                    save_state(project, state)
            elif scene.get("keyframe_path"):
                kf_path = scene["keyframe_path"]

        # 2) scene video
        video = render_scene(cfg, client, project, scene, plan, wf_name,
                             scene_file=kf_path, seed=scene.get("seed", 42 + sid))
        meta = {"video": os.path.basename(video), "workflow": wf_name}
        if kf_path:
            meta["keyframe"] = os.path.basename(kf_path)
        with lock:
            state[key] = meta
            save_state(project, state)
        print(f"[scene {sid}] -> {video}")
        return scene, video, kf_path

    if n_workers == 1:
        for scene in todo:
            run_scene(scene)
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futures = {pool.submit(run_scene, s): s for s in todo}
            for fut in as_completed(futures):
                fut.result()  # propagate errors

    print("Render complete. Next: director.py assemble")
