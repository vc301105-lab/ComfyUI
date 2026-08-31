"""Contract tests for built-in API templates (no ComfyUI needed).

Run: python3 tests/test_templates.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.dirname(HERE)
sys.path.insert(0, AGENT)

import templates  # noqa: E402


def check(name, cond):
    print(f"[{'OK' if cond else 'FAIL'}] {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


# --- SDXL txt2img ---
wf = templates.sdxl_txt2img_api("P", "N", "ckpt.safetensors")
classes = {n["class_type"] for n in wf.values()}
check("sdxl: classes", {"CheckpointLoaderSimple", "CLIPTextEncode", "KSampler",
                        "VAEDecode", "SaveImage", "EmptyLatentImage"} <= classes)
check("sdxl: graph chain", wf["5"]["inputs"]["model"] == ["1", 0]
      and wf["5"]["inputs"]["latent_image"] == ["4", 0]
      and wf["6"]["inputs"]["vae"] == ["1", 2]
      and wf["7"]["inputs"]["images"] == ["6", 0])

# --- IPAdapter (character identity) ---
wfi = templates.sdxl_ipadapter_txt2img_api("P", "N", "ckpt.safetensors", "ref.png")
ci = {n["class_type"] for n in wfi.values()}
check("ipadapter: classes", {"IPAdapterUnifiedLoader", "IPAdapter",
                             "CLIPVisionLoader", "LoadImage"} <= ci)
check("ipadapter: model chain", wfi["10"]["inputs"]["model"] == ["9", 1]
      and wfi["5"]["inputs"]["model"] == ["9", 0])
check("ipadapter: unified loader links", wfi["9"]["inputs"]["model"] == ["1", 0]
      and wfi["9"]["inputs"]["clip_vision"] == ["8", 0])
check("ipadapter: ref image node", wfi["11"]["inputs"]["image"] == "ref.png")

# --- Qwen-Image ---
wfq = templates.qwen_image_txt2img_api("P", "N", "q_unet", "q_clip", "q_vae")
cq = {n["class_type"] for n in wfq.values()}
check("qwen: classes", {"UNETLoader", "CLIPLoader", "VAELoader",
                        "EmptySD3LatentImage", "KSampler"} <= cq)
check("qwen: clip type", wfq["2"]["inputs"]["type"] == "qwen_image")
check("qwen: sampler chain", wfq["7"]["inputs"]["model"] == ["1", 0]
      and wfq["9"]["inputs"]["images"] == ["8", 0])

# --- all templates valid JSON-serializable ---
for name, obj in (("sdxl", wf), ("ipadapter", wfi), ("qwen", wfq)):
    json.dumps(obj)
    check(f"{name}: json-serializable", True)

print("\nALL TEMPLATE TESTS PASSED")
