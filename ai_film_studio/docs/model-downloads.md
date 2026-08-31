# ⬇️ Model Downloads — Exact Commands

> Pehle: `huggingface-cli login` (free account) ya `HF_TOKEN=...` env.
> Sab download ComfyUI root se chalayein taaki paths `models/` se match ho.
> ⚠️ = HuggingFace page pe repo id ek baar verify kar lein (org naam kabhi-kabhi badalta hai).

```bash
cd /path/to/ComfyUI
HF="huggingface-cli download"
```

---

## 🎥 Video Models → `models/diffusion_models/` + `models/text_encoders/`

### HunyuanVideo 1.5 (main engine)
```bash
$HF Tencent/HunyuanVideo --local-dir models/diffusion_models/HunyuanVideo
$HF Tencent/HunyuanVideo-1.5 --local-dir models/diffusion_models/HunyuanVideo-1.5  # ⚠️ verify id
```
Text encoder (HunyuanVideoWrapper se chahiye):
```bash
$HF xtuner/llava-llama-3-8b-v1_1-transformers --local-dir models/text_encoders/llava-llama-3-8b
$HF openai/clip-vit-large-patch14 --local-dir models/clip_vision/clip-vit-large-patch14
```

### Wan 2.2 (I2V hero shots)
```bash
# Text-to-Video 5B (Chhota, fast — ComfyUI-WanVideoWrapper)
$HF Wan-AI/Wan2.2-T2V-5B --local-dir models/diffusion_models/Wan2.2-T2V-5B   # ⚠️ verify id
# Image-to-Video 14B (48GB+ pe full quality)  -- variants: Wan2.2-I2V-14B-720P
$HF Wan-AI/Wan2.2-I2V-14B-720P --local-dir models/diffusion_models/Wan2.2-I2V-14B-720P   # ⚠️ verify
```

### LTX-2.3 (4K + native audio)
```bash
$HF Lightricks/LTX-Video --local-dir models/diffusion_models/LTX-Video     # 2B (LTXV)
$HF Lightricks/LTX-2 --local-dir models/diffusion_models/LTX-2             # ⚠️ 2026 release, verify id
```

### SkyReels V2 (long shots) / CogVideoX (backup)
```bash
$HF SkyworkAI/SkyReels-V2 --local-dir models/diffusion_models/SkyReels-V2
$HF THUDM/CogVideoX-5b --local-dir models/diffusion_models/CogVideoX-5b
```

---

## 🖼️ Image Models → `models/checkpoints/` (SDXL/SD3.5) ya `models/diffusion_models/` (FLUX/Qwen)

```bash
# FLUX.2 klein = commercial-safe, chhota
$HF black-forest-labs/FLUX.1-schnell --local-dir models/diffusion_models/FLUX.1-schnell
$HF BlackForestLabs/FLUX.2-klein --local-dir models/diffusion_models/FLUX.2-klein          # ⚠️ verify id

# Qwen-Image (text-in-image, Apache)
$HF Qwen/Qwen-Image --local-dir models/diffusion_models/Qwen-Image

# HunyuanImage 3.0 (48GB+ pe full)
$HF Tencent-Hunyuan/HunyuanImage-3.0 --local-dir models/diffusion_models/HunyuanImage-3.0  # ⚠️ verify id

# SDXL / SD3.5 (LoRA ecosystem)
$HF stabilityai/stable-diffusion-xl-base-1.0 --local-dir models/checkpoints/sd-xl-base-1.0
$HF stabilityai/stable-diffusion-3.5-medium --local-dir models/checkpoints/sd-3.5-medium
```

### Consistency adapters → `models/controlnet/`, `models/loras/`
- IP-Adapter: `h94/IP-Adapter` (ip-adapter_sd15 / plus_sd15 / sdxl)
- InstantID: `InstantX/InstantID`
- PuLID: `guozinan/PuLID` (flux / sd)

---

## 🎙️ Voice Models → `models/tts/` (temporary folder; har tool apna config path leta hai)

```bash
# Chatterbox (MIT, best Hinglish quality)
$HF resemble-ai/chatterbox --local-dir models/tts/chatterbox

# Qwen3-TTS (Apache, 3s clone)
$HF Qwen/Qwen3-TTS-1.7B --local-dir models/tts/qwen3-tts

# Kokoro (CPU narration)
$HF hexgrad/Kokoro-82M --local-dir models/tts/kokoro-82m

# CosyVoice 3 (Apache multilingual)
$HF FunAudioLLM/CosyVoice2-0.5B --local-dir models/tts/cosyvoice2   # ⚠️ v3 repo verify karein
```

**GPT-SoVITS / Fish Speech / Orpheus / Zonos:** GitHub repo se `git clone` + apne download scripts se weights (sizes bade hain).

---

## 🎵 Music Models → `models/audio/`

```bash
# ACE-Step 1.5 (MIT — main score engine)
$HF ace-step/ACE-Step --local-dir models/audio/ace-step    # ⚠️ verify snapshot/repo id

# YuE (Apache — quality vocals, slow)
$HF multimodal-art-projection/YuE --local-dir models/audio/yue

# MusicGen (MIT fast loops)
$HF facebook/musicgen-large --local-dir models/audio/musicgen-large

# MMAudio (foley, video-synced)
$HF hkchengrex/MMAudio --local-dir models/audio/mmaudio
```

---

## 👄 Lip-Sync → apne repos me (GitHub clone + weights)

```bash
git clone https://github.com/bytedance/LatentSync.git external/LatentSync
git clone https://github.com/TMElyralab/MuseTalk.git   external/MuseTalk
# LatentSync weights: HF `bytedance/LatentSync-1.6` (⚠️ latest version check karein)
```

---

## 🗜️ Post-Production (GitHub only, pip install)
```bash
pip install moviepy faster-whisper opencv-python
git clone https://github.com/xlinsve/SUPIR.git external/SUPIR   # ⚠️ kijai/ComfyUI-SUPIR custom node lekin weights: XLabs-AI/SUPIR-...
```

---

## 💾 Storage Budget (approx)
| Models | Size |
|---|---|
| Wan 2.2 (5B + 14B I2V) | ~80–120GB |
| HunyuanVideo 1.5 + encoders | ~60–80GB |
| LTX-2.3 | ~60–80GB |
| HunyuanImage 3.0 | ~160GB+ |
| FLUX/Qwen/SD + adapters | ~60GB |
| TTS (5 models) | ~30GB |
| Music (ACE-Step/YuE/MMAudio) | ~40GB |
| **Total** | **~400–600GB** (2TB NVMe safe) |
