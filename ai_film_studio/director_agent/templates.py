"""Built-in ComfyUI API workflows (hand-written, stable node names)."""


def sdxl_txt2img_api(positive, negative, checkpoint, width=1024, height=1024,
                     seed=42, steps=25, cfg=7.0, sampler="dpmpp_2m",
                     scheduler="karras", filename_prefix="ai_film_studio/kf"):
    """Standard SDXL txt2img workflow in ComfyUI API format."""
    wf = _sdxl_base(positive, negative, checkpoint, width, height, seed,
                    steps, cfg, sampler, scheduler, filename_prefix)
    # plain KSampler directly on checkpoint
    wf["5"]["inputs"]["model"] = ["1", 0]
    return wf


def sdxl_ipadapter_txt2img_api(positive, negative, checkpoint, ref_image,
                               width=1024, height=1024, seed=42, steps=25,
                               cfg=7.0, sampler="dpmpp_2m", scheduler="karras",
                               filename_prefix="ai_film_studio/kf",
                               preset="PLUS FACE (portraits)", weight=0.8,
                               clip_vision="CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"):
    """SDXL + IPAdapter (character reference) txt2img — ComfyUI API format.

    Nodes: CheckpointLoader -> IPAdapterUnifiedLoader -> IPAdapter
           (reference image se identity inject) -> KSampler.
    """
    wf = _sdxl_base(positive, negative, checkpoint, width, height, seed,
                    steps, cfg, sampler, scheduler, filename_prefix)
    wf["5"]["inputs"]["model"] = ["9", 0]              # KSampler <- IPAdapter model
    wf["8"] = {
        "class_type": "CLIPVisionLoader",
        "inputs": {"clip_name": clip_vision},
    }
    wf["9"] = {
        "class_type": "IPAdapterUnifiedLoader",
        "inputs": {"model": ["1", 0], "preset": preset, "lora_strength": 1.0,
                   "provider": "AUTO", "cache_model": False,
                   "clip_vision": ["8", 0]},
    }
    wf["10"] = {
        "class_type": "IPAdapter",
        "inputs": {"model": ["9", 1], "ipadapter": ["9", 0],
                   "image": ["11", 0], "weight": weight, "weight_face": weight,
                   "weight_type": "linear", "combine_embeds": "concat",
                   "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"},
    }
    wf["11"] = {
        "class_type": "LoadImage",
        "inputs": {"image": ref_image},
    }
    return wf


def qwen_image_txt2img_api(positive, negative, unet, clip, vae,
                           width=1024, height=1024, seed=42, steps=20,
                           cfg=3.5, sampler="euler", scheduler="simple",
                           filename_prefix="ai_film_studio/kf"):
    """Qwen-Image (Apache 2.0, in-image text) txt2img — ComfyUI API format.

    Native ComfyUI nodes: UNETLoader + CLIPLoader(type=qwen_image) +
    VAELoader + EmptySD3LatentImage.
    """
    return {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": unet, "weight_dtype": "fp8_e4m3fn"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": clip, "type": "qwen_image",
                         "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["2", 0], "text": positive}},
        "5": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["2", 0], "text": negative}},
        "6": {"class_type": "EmptySD3LatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "positive": ["4", 0],
                         "negative": ["5", 0], "latent_image": ["6", 0],
                         "seed": seed, "steps": steps, "cfg": cfg,
                         "sampler_name": sampler, "scheduler": scheduler,
                         "denoise": 1.0}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"images": ["8", 0], "filename_prefix": filename_prefix}},
    }


def _sdxl_base(positive, negative, checkpoint, width, height, seed, steps, cfg,
               sampler, scheduler, filename_prefix):
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": checkpoint}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["1", 1], "text": positive}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["1", 1], "text": negative}},
        "4": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "5": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "positive": ["2", 0],
                         "negative": ["3", 0], "latent_image": ["4", 0],
                         "seed": seed, "steps": steps, "cfg": cfg,
                         "sampler_name": sampler, "scheduler": scheduler,
                         "denoise": 1.0}},
        "6": {"class_type": "VAEDecode",
              "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage",
              "inputs": {"images": ["6", 0], "filename_prefix": filename_prefix}},
    }
