#!/usr/bin/env python3
"""
Build & validate the ComfyUI workflows for THE LAST LIGHTHOUSE.

Generates workflow files in ComfyUI/models/workflows/ (UI format — drag into
the canvas) from the LIVE server's /object_info schema, and validates the
equivalent API graph by POSTing it to /prompt (structure must be clean).

Workflows:
  1. wan-i2v-the-last-lighthouse.json       Wan 2.6 image->video (shot 01)
  2. wan-firstlast-the-last-lighthouse.json Wan 2.6 FIRST+LAST frame->video
                                             (bridges shot 07 -> shot 08)
  3. wan22-i2v-the-last-lighthouse.json     Wan 2.2 image->video (raw node
                                             graph, experimental variant)
  4. character-ipadapter.json               SD1.5 + IPAdapter FaceID
                                             (if the IPAdapter pack is loaded)

Usage:
  1. Start ComfyUI:  python3 main.py
  2. Run:            python3 ai-film-course/tools/build_comfy_workflow.py
"""
import json
import shutil
import sys
import urllib.request
from pathlib import Path

COMFY = Path(__file__).resolve().parents[2]
OUTDIR = COMFY / "models" / "workflows"
FRAMES = COMFY / "ai-film-course" / "demo-film" / "frames"
API_URL = "http://127.0.0.1:8188"

# ------------------------------------------------------------------
# Prompts & models
# ------------------------------------------------------------------
POSITIVE_I2V = (
    "The camera slowly pushes toward a vast flooded dystopian city at dusk. "
    "Crumbling skyscrapers stand half-submerged in black floodwater beneath "
    "colossal storm clouds. Far away on a rocky island, a lone lighthouse "
    "sends its warm beam cutting through heavy rain. Distant lightning "
    "flickers, rain falls steadily, dark waves ripple, storm clouds drift. "
    "Moody atmospheric science fiction, teal and amber color grade, "
    "volumetric light, film grain, 35mm anamorphic lens, epic scale, "
    "slow cinematic movement."
)
POSITIVE_FIRSTLAST = (
    "The ship on the misty horizon slowly grows closer as dawn breaks: its "
    "navigation lights blinking softly, the golden sunrise parting the storm "
    "clouds, calm waves rolling, mist drifting. The camera gently pushes in. "
    "Moody atmospheric science fiction, teal and amber color grade, film "
    "grain, slow cinematic movement."
)
POSITIVE_CHARACTER = (
    "a weathered woman in her late 40s, silver-streaked dark hair tied back, "
    "deep-set tired eyes, wearing a faded mustard-yellow raincoat over a dark "
    "wool sweater, standing at the lighthouse window in soft dawn light, "
    "gentle hopeful expression, cinematic teal-and-amber grade, film grain, "
    "85mm lens, ultra-detailed natural skin texture."
)
NEGATIVE = (
    "low quality, blurry, distorted, warped, flickering, jittery, text, "
    "watermark, oversaturated, cartoon, extra limbs, bad anatomy"
)

M26 = {  # Wan 2.6 (Comfy-Org/Wan_2.6_ComfyUI_Repackaged)
    "unet": "wan2.6_i2v_480p_14B_fp8_e4m3fn.safetensors",
    "clip": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "clip_vision": "clip_vision_h.safetensors",
    "vae": "wan_2.1_vae.safetensors",
}
M22 = {  # Wan 2.2 (Comfy-Org/Wan_2.2_ComfyUI_Repackaged)
    "unet": "wan2.2_i2v_a14b_720p_fp8_e4m3fn.safetensors",
    "clip": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "vae": "wan_2.2_vae.safetensors",
}

# ------------------------------------------------------------------
# Workflow specs:  (id, type, pos, widgets, inputs {name: (from, slot)})
# ------------------------------------------------------------------
def nodes_wan26():
    return [
        (1,  "LoadImage",        (-1400, -560), ["shot-01.png"]),
        (2,  "UNETLoader",       (-1400, -140), [M26["unet"], "default"]),
        (3,  "CLIPLoader",       (-1400,  220), [M26["clip"], "wan"]),
        (4,  "CLIPVisionLoader", (-1400,  580), [M26["clip_vision"]]),
        (5,  "VAELoader",        (-1400,  940), [M26["vae"]]),
        (6,  "CLIPTextEncode",   (-720,    40), [POSITIVE_I2V]),
        (7,  "CLIPTextEncode",   (-720,   420), [NEGATIVE]),
        (8,  "CLIPVisionEncode", (-720,   800), ["center"]),
        (9,  "WanImageToVideo",  ( -40,   160), [832, 480, 81, 1]),
        (10, "KSampler",         ( 720,   160), [42, 25, 6.0, "euler", "simple", 1.0]),
        (11, "VAEDecode",        (1480,   160), []),
        (12, "CreateVideo",      (1480,   560), [16.0]),
        (13, "SaveVideo",        (2240,   300), ["the_last_lighthouse", "mp4", "auto"]),
    ], [
        (1, 0, 8, "image", "IMAGE"),
        (1, 0, 9, "start_image", "IMAGE"),
        (2, 0, 10, "model", "MODEL"),
        (3, 0, 6, "clip", "CLIP"),
        (3, 0, 7, "clip", "CLIP"),
        (4, 0, 8, "clip_vision", "CLIP_VISION"),
        (5, 0, 9, "vae", "VAE"),
        (5, 0, 11, "vae", "VAE"),
        (6, 0, 9, "positive", "CONDITIONING"),
        (7, 0, 9, "negative", "CONDITIONING"),
        (8, 0, 9, "clip_vision_output", "CLIP_VISION_OUTPUT"),
        (9, 0, 10, "positive", "CONDITIONING"),
        (9, 1, 10, "negative", "CONDITIONING"),
        (9, 2, 10, "latent_image", "LATENT"),
        (10, 0, 11, "samples", "LATENT"),
        (11, 0, 12, "images", "IMAGE"),
        (12, 0, 13, "video", "VIDEO"),
    ]


def nodes_firstlast():
    return [
        (1,  "LoadImage",               (-1600, -700), ["shot-07.png"]),
        (2,  "LoadImage",               (-1600,  -50), ["shot-08.png"]),
        (3,  "UNETLoader",              (-1600,  560), [M26["unet"], "default"]),
        (4,  "CLIPLoader",              (-1600,  920), [M26["clip"], "wan"]),
        (5,  "CLIPVisionLoader",        (-1600, 1280), [M26["clip_vision"]]),
        (6,  "VAELoader",               (-1600, 1640), [M26["vae"]]),
        (7,  "CLIPTextEncode",          (-880,   160), [POSITIVE_FIRSTLAST]),
        (8,  "CLIPTextEncode",          (-880,   560), [NEGATIVE]),
        (9,  "CLIPVisionEncode",        (-880,   960), ["center"]),
        (10, "CLIPVisionEncode",        (-880,  1320), ["center"]),
        (11, "WanFirstLastFrameToVideo",( -160,  160), [832, 480, 81, 1]),
        (12, "KSampler",                ( 720,   160), [42, 25, 6.0, "euler", "simple", 1.0]),
        (13, "VAEDecode",               (1480,   160), []),
        (14, "CreateVideo",             (1480,   560), [16.0]),
        (15, "SaveVideo",               (2240,   300), ["the_last_lighthouse_firstlast", "mp4", "auto"]),
    ], [
        (1, 0, 9,  "image", "IMAGE"),
        (2, 0, 10, "image", "IMAGE"),
        (1, 0, 11, "start_image", "IMAGE"),
        (2, 0, 11, "end_image", "IMAGE"),
        (3, 0, 12, "model", "MODEL"),
        (4, 0, 7,  "clip", "CLIP"),
        (4, 0, 8,  "clip", "CLIP"),
        (5, 0, 9,  "clip_vision", "CLIP_VISION"),
        (5, 0, 10, "clip_vision", "CLIP_VISION"),
        (6, 0, 11, "vae", "VAE"),
        (6, 0, 13, "vae", "VAE"),
        (7, 0, 11, "positive", "CONDITIONING"),
        (8, 0, 11, "negative", "CONDITIONING"),
        (9, 0, 11, "clip_vision_start_image", "CLIP_VISION_OUTPUT"),
        (10, 0, 11, "clip_vision_end_image", "CLIP_VISION_OUTPUT"),
        (11, 0, 12, "positive", "CONDITIONING"),
        (11, 1, 12, "negative", "CONDITIONING"),
        (11, 2, 12, "latent_image", "LATENT"),
        (12, 0, 13, "samples", "LATENT"),
        (13, 0, 14, "images", "IMAGE"),
        (14, 0, 15, "video", "VIDEO"),
    ]


def nodes_wan22():
    return [
        (1,  "LoadImage",             (-1400, -560), ["shot-01.png"]),
        (2,  "UNETLoader",            (-1400, -140), [M22["unet"], "default"]),
        (3,  "CLIPLoader",            (-1400,  220), [M22["clip"], "wan"]),
        (4,  "VAELoader",             (-1400,  580), [M22["vae"]]),
        (5,  "CLIPTextEncode",        (-720,    40), [POSITIVE_I2V]),
        (6,  "CLIPTextEncode",        (-720,   420), [NEGATIVE]),
        (7,  "Wan22ImageToVideoLatent", ( -40,  160), [1280, 704, 49, 1]),
        (8,  "KSampler",              ( 720,   160), [42, 25, 6.0, "euler", "simple", 1.0]),
        (9,  "VAEDecode",             (1480,   160), []),
        (10, "CreateVideo",           (1480,   560), [16.0]),
        (11, "SaveVideo",             (2240,   300), ["the_last_lighthouse_wan22", "mp4", "auto"]),
    ], [
        (1, 0, 7, "start_image", "IMAGE"),
        (2, 0, 8, "model", "MODEL"),
        (3, 0, 5, "clip", "CLIP"),
        (3, 0, 6, "clip", "CLIP"),
        (4, 0, 7, "vae", "VAE"),
        (4, 0, 9, "vae", "VAE"),
        (5, 0, 8, "positive", "CONDITIONING"),
        (6, 0, 8, "negative", "CONDITIONING"),
        (7, 0, 8, "latent_image", "LATENT"),
        (8, 0, 9, "samples", "LATENT"),
        (9, 0, 10, "images", "IMAGE"),
        (10, 0, 11, "video", "VIDEO"),
    ]


def nodes_faceid():
    return [
        (1, "CheckpointLoaderSimple",        (-1700, -560), ["v1-5-pruned-emaonly.safetensors"]),
        (2, "IPAdapterUnifiedLoaderFaceID",  (-1700,    0), ["FACEID PLUS V2", 1.0, "CPU"]),
        (3, "LoadImage",                     (-1700,  400), ["character-sheet/front.png"]),
        (4, "CLIPTextEncode",                (-1000, -200), [POSITIVE_CHARACTER]),
        (5, "CLIPTextEncode",                (-1000,  160), [NEGATIVE]),
        (6, "IPAdapterFaceID",               (-300,   -60), [0.8, 0.8, "linear", "concat", 0.2, 1.0, "V only"]),
        (7, "EmptyLatentImage",              (-300,   500), [512, 512, 1]),
        (8, "KSampler",                      ( 420,   -60), [42, 25, 5.0, "euler", "normal", 1.0]),
        (9, "VAEDecode",                     (1160,   -60), []),
        (10, "SaveImage",                    (1160,   400), ["character_pose"]),
    ], [
        (1, 0, 2, "model", "MODEL"),
        (1, 1, 4, "clip", "CLIP"),
        (1, 1, 5, "clip", "CLIP"),
        (1, 2, 9, "vae", "VAE"),
        (2, 0, 6, "model", "MODEL"),
        (2, 1, 6, "ipadapter", "IPADAPTER"),
        (3, 0, 6, "image", "IMAGE"),
        (4, 0, 8, "positive", "CONDITIONING"),
        (5, 0, 8, "negative", "CONDITIONING"),
        (6, 0, 8, "model", "MODEL"),
        (7, 0, 8, "latent_image", "LATENT"),
        (8, 0, 9, "samples", "LATENT"),
        (9, 0, 10, "images", "IMAGE"),
    ]


WORKFLOWS = {
    "wan-i2v-the-last-lighthouse.json":       nodes_wan26(),
    "wan-firstlast-the-last-lighthouse.json": nodes_firstlast(),
    "wan22-i2v-the-last-lighthouse.json":     nodes_wan22(),
    "character-ipadapter.json":               nodes_faceid(),
}

SIZES = {
    "LoadImage": [460, 500], "UNETLoader": [420, 300], "CLIPLoader": [420, 300],
    "CLIPVisionLoader": [420, 300], "VAELoader": [420, 300], "CLIPTextEncode": [420, 260],
    "CLIPVisionEncode": [420, 300], "WanImageToVideo": [560, 560], "KSampler": [420, 480],
    "VAEDecode": [300, 200], "CreateVideo": [400, 300], "SaveVideo": [540, 500],
    "WanFirstLastFrameToVideo": [620, 620], "Wan22ImageToVideoLatent": [560, 480],
    "CheckpointLoaderSimple": [420, 300], "IPAdapterUnifiedLoaderFaceID": [500, 300],
    "IPAdapterFaceID": [620, 400], "EmptyLatentImage": [320, 220], "SaveImage": [400, 500],
}

# model placeholders created just for validation, removed afterwards
PLACEHOLDERS = {
    "unet": [M26["unet"], M22["unet"]],
    "text_encoders": [M26["clip"], M22["clip"]],
    "clip_vision": [M26["clip_vision"]],
    "vae": [M26["vae"], M22["vae"]],
    "checkpoints": ["v1-5-pruned-emaonly.safetensors"],
    "ipadapter": ["ip-adapter-faceid-plusv2_sd15.bin"],
}


def get_schema():
    with urllib.request.urlopen(f"{API_URL}/object_info", timeout=60) as r:
        return json.load(r)


def input_order(schema, cls):
    out = []
    for k, v in schema[cls]["input"].get("required", {}).items():
        out.append((k, v[0] if isinstance(v, list) else v, False))
    for k, v in schema[cls]["input"].get("optional", {}).items():
        out.append((k, v[0] if isinstance(v, list) else v, True))
    return out


def output_order(schema, cls):
    return [(v[0], v[1]) for v in schema[cls]["output"]]


def build_ui_workflow(schema, spec):
    nodes_spec, links_spec = spec
    nodes, links = [], []
    by_id = {n[0]: n for n in nodes_spec}
    linkable = {}
    for nid, cls, pos, wv in nodes_spec:
        linkable[nid] = {}
        for iname, itype, iopt in input_order(schema, cls):
            if not (itype == "STRING" or itype in ("FLOAT", "INT", "BOOLEAN")
                    or isinstance(itype, list)):
                linkable[nid][iname] = itype
    link_by_target = {}
    for lid, (frm, fslot, to, iname, ltype) in enumerate(links_spec, start=1):
        link_by_target[(to, iname)] = (lid, frm, fslot, ltype)
    for nid, cls, pos, wv in nodes_spec:
        inputs = []
        for iname, itype, iopt in input_order(schema, cls):
            if iname in linkable[nid]:
                hit = link_by_target.get((nid, iname))
                inputs.append({"name": iname, "type": itype,
                               "link": hit[0] if hit else None})
        out_links = {n: [] for n, _ in output_order(schema, cls)}
        for lid, (frm, fslot, to, iname, ltype) in enumerate(links_spec, start=1):
            if frm == nid:
                oname = output_order(schema, cls)[fslot][0]
                out_links[oname].append(lid)
        outputs = [{"name": oname, "type": otype, "links": out_links[oname] or None}
                   for oname, otype in output_order(schema, cls)]
        nodes.append({
            "id": nid, "type": cls, "pos": list(pos), "size": SIZES.get(cls, [420, 300]),
            "flags": {}, "order": nid - 1, "mode": 0, "inputs": inputs,
            "outputs": outputs, "properties": {"cnr_id": "comfy-core",
                                               "Node name for S&R": cls},
            "widgets_values": wv,
        })
    for lid, (frm, fslot, to, iname, ltype) in enumerate(links_spec, start=1):
        idx = [n for n, t, o in input_order(schema, by_id[to][1])].index(iname)
        links.append([lid, frm, fslot, to, idx, ltype])
    return {"id": Path(list(WORKFLOWS.keys())[0]).stem, "revision": 0,
            "last_node_id": len(nodes_spec), "last_link_id": len(links_spec),
            "nodes": nodes, "links": links, "groups": [], "config": {},
            "extra": {}, "version": 0.4}


def build_api_prompt(schema, spec):
    nodes_spec, links_spec = spec
    prompt = {}
    for nid, cls, pos, wv in nodes_spec:
        inputs, wi = {}, 0
        for iname, itype, iopt in input_order(schema, cls):
            hit = [l for l in links_spec if l[2] == nid and l[3] == iname]
            if hit:
                inputs[iname] = [str(hit[0][0]), hit[0][1]]
            elif iopt:
                continue
            else:
                inputs[iname] = wv[wi]
                wi += 1
        prompt[str(nid)] = {"class_type": cls, "inputs": inputs}
    return prompt


def create_placeholders():
    made = []
    for folder, names in PLACEHOLDERS.items():
        for name in names:
            p = COMFY / "models" / folder / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
            made.append(p)
    return made


def cleanup(ps):
    for p in ps:
        if p.exists() and p.stat().st_size == 0:
            p.unlink(missing_ok=True)


def copy_inputs():
    for fname in ("shot-01.png", "shot-07.png", "shot-08.png"):
        src = FRAMES / fname
        dst = COMFY / "input" / fname
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    src = FRAMES / "character-sheet" / "front.png"
    dst = COMFY / "input" / "character-sheet" / "front.png"
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def main():
    schema = get_schema()
    copy_inputs()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    placeholders = create_placeholders()

    for fname, spec in WORKFLOWS.items():
        missing = [cls for nid, cls, _, _ in spec[0] if cls not in schema]
        if missing:
            print(f"SKIP  {fname}: node classes not loaded: {missing}")
            continue
        wf = build_ui_workflow(schema, spec)
        (OUTDIR / fname).write_text(json.dumps(wf, indent=1))
        body = json.dumps({"prompt": build_api_prompt(schema, spec),
                           "client_id": "wfcheck"}).encode()
        req = urllib.request.Request(f"{API_URL}/prompt", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            resp = json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            resp = json.load(e)
        errs = resp.get("node_errors") or {}
        if errs:
            print(f"FAIL  {fname}: {json.dumps(errs)[:400]}")
        else:
            status = "validated OK" if "prompt_id" in resp else "OK (no node_errors)"
            print(f"OK    {fname}: {status}")

    cleanup(placeholders)
    print("\nWorkflows written to", OUTDIR.relative_to(COMFY))
    print("In the UI: Workflow -> Open -> models/workflows/<file>.json")


if __name__ == "__main__":
    main()
