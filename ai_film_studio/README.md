# 🎬 AI Film Studio — Setup Kit (100% Local / Free)

> Target machine: **48GB+ VRAM (multi-GPU) • Linux + NVIDIA CUDA**
> Goal: **5–15 min Hinglish short film, fully local, full cinematic quality**

Ye folder aapke ComfyUI repo ke andar ready-to-run setup kit hai. Har script
`chmod +x` karke usi order me chalayein.

---

## 📋 Quick Start (aapki 48GB+ machine pe)

```bash
cd /path/to/ComfyUI

# Step 0 — Hardware check (30 sec, kuch install nahi hota)
bash ai_film_studio/setup/00_hardware_check.sh

# Step 1 — Python venv + ComfyUI dependencies
bash ai_film_studio/setup/01_setup_venv.sh

# Step 2 — Custom nodes (video engine + character consistency + upscale)
bash ai_film_studio/setup/02_install_custom_nodes.sh

# Step 3 — Verify setup (imports + custom nodes load)
bash ai_film_studio/setup/03_verify_setup.sh

# Step 4 — Models download (exact commands, docs me)
cat ai_film_studio/docs/model-downloads.md

# Step 5 — ComfyUI start
.venv/bin/python main.py --listen 0.0.0.0
# Browser: http://localhost:8188
```

---

## 🗂️ Folder Structure

```
ai_film_studio/
├── README.md                     # Ye file — master plan
├── setup/
│   ├── 00_hardware_check.sh      # GPU/disk/python/ffmpeg check
│   ├── 01_setup_venv.sh          # Python venv + torch/CUDA + deps
│   ├── 02_install_custom_nodes.sh# Saare custom nodes (core + optional)
│   └── 03_verify_setup.sh        # Import check + node load check
└── docs/
    ├── local-stack.md            # Poore stack ka breakdown + licenses
    ├── model-downloads.md        # Exact huggingface-cli commands
    └── production-workflow.md    # 5-15 min Hinglish film ka pipeline
```

---

## 🎯 Chosen Stack (48GB+ / Multi-GPU)

| Department | Engine | License |
|---|---|---|
| Script/Direction | Ollama + Qwen3 32B / Llama 3.3 70B | Apache-2.0 |
| Video (main) | HunyuanVideo 1.5 + Wan 2.2 14B + LTX-2.3 | Open |
| Video (long shots) | SkyReels V2 | Open |
| Keyframes | HunyuanImage 3.0 + FLUX.2 + Qwen-Image + SDXL | Mix (FLUX dev = non-commercial) |
| Character consistency | IP-Adapter + InstantID + PuLID | Apache |
| Voices | Chatterbox + Qwen3-TTS + CosyVoice 3 + Kokoro | MIT / Apache |
| Music | ACE-Step 1.5 + YuE + MMAudio | MIT / Apache |
| Lip-sync | LatentSync + MuseTalk | Apache/MIT |
| Edit/Post | ComfyUI + MoviePy + FFmpeg + Remotion + WhisperX + SUPIR | Open |

Full detail: [`docs/local-stack.md`](docs/local-stack.md)

---

## 🧭 Production Pipeline (5–15 min Hinglish film, ek nazar me)

1. **Script** — Ollama se Hinglish story + dialogues (3-act structure)
2. **Character Bible** — Har character ke reference images (FLUX/Qwen-Image)
3. **Storyboard** — 15–25 keyframes (HunyuanImage 3.0)
4. **Scene video** — HunyuanVideo 1.5 / Wan 2.2 I2V (scene-by-scene, consistency ke liye IP-Adapter)
5. **Voice** — Chatterbox/Qwen3-TTS se Hindi + English dialogue lines
6. **Lip-sync** — LatentSync se mouths match
7. **Music + SFX** — ACE-Step se score, MMAudio se foley
8. **Subtitles** — WhisperX se Hinglish word-level captions
9. **Edit** — MoviePy/FFmpeg se assembly, Remotion se titles
10. **Final** — SUPIR upscale + color grade → `final.mp4`

Step-by-step: [`docs/production-workflow.md`](docs/production-workflow.md)

---

## ⚠️ Important Notes

- **Disk:** Models total ~400GB–1TB. 2TB NVMe recommended.
- **License:** Movie *sell* karni hai toh sirf Apache-2.0/MIT models use karein.
  FLUX.1/2 **dev** = non-commercial; schnell/klein commercial-safe.
- **VRAM sharing:** Multi-GPU pe ComfyUI ko `--gpu-only` ya per-model offload ke
  saath chalayein; LTX aur Hunyuan alag-alag cards pe parallel bhi chal sakte hain.
- **Ye sandbox GPU-less hai** — isliye yahan sirf kit verify kiya ja sakta hai,
  actual rendering aapki machine pe hogi.
