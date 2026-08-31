"""Configuration loading / defaults for the AI Film Studio Director."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # ai_film_studio/
COMPUTED = os.path.join(ROOT, "workflows")
PROJECTS_DEFAULT = os.path.join(ROOT, "projects")

DEFAULTS = {
    "comfy_url": "http://127.0.0.1:8188",
    "ollama_url": "http://127.0.0.1:11434",
    "llm_model": "qwen3:32b",
    "llm_temperature": 0.7,
    "video_workflow": "wan22_5b_i2v_example.json",     # default scene engine
    "image_workflow": "sdxl_txt2img_api.json",          # keyframe engine
    "image_checkpoint": "sd_xl_base_1.0.safetensors",
    "keyframe_engine": "sdxl",          # sdxl | ipadapter | qwen_image
    "keyframe_identity": False,         # True = character reference images + IP-Adapter
    "ipadapter_preset": "PLUS FACE (portraits)",
    "ipadapter_clip": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
    "qwen_unet": "qwen_image.safetensors",
    "qwen_clip": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
    "qwen_vae": "qwen_image_vae.safetensors",
    "comfy_urls": [],                    # multi-GPU: ["http://127.0.0.1:8188", "http://127.0.0.1:8189"]
    "project_root": PROJECTS_DEFAULT,
    "scene_width": 832,
    "scene_height": 480,
    "scene_fps": 24,
    "scene_seconds": 5,
    "negative_prompt": (
        "low quality, worst quality, blurry, distorted, watermark, text, "
        "extra fingers, mutated, deformed, bad anatomy"
    ),
    "tts": {
        "engine": "none",       # none | chatterbox | custom
        "command": "",           # custom: jiase  "chatterbox --text %TEXT% --output_path %OUT%"
        "model": "",
        "sample_rate": 48000,
        "pause": 0.4,
    },
    "lipsync": {
        "engine": "none",       # none | latentsync | wav2lip | custom
        "command": "",           # %VIDEO% %AUDIO% %OUT%
    },
    "music": {
        "engine": "none",       # none | acestep | custom
        "command": "",           # %PROMPT% %DURATION% %OUT%
        "prompt": "cinematic emotional indian score",
        "volume": 0.18,
    },
    "subs": {
        "model": "small",        # faster-whisper model
        "language": "hi",        # hi / en / "auto"
    },
    "post": {"loudness": -14.0},
    "subtitles": False,
}


def load_config(path=None):
    path = path or os.path.join(HERE, "config.json")
    cfg = dict(DEFAULTS)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    cfg["_path"] = path
    return cfg


def save_config(cfg, path=None):
    path = path or cfg.get("_path") or os.path.join(HERE, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return path
