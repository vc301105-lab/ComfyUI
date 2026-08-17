# 🖥️ GO LOCAL — Free, Open-Source AI Filmmaking with ComfyUI

*(Stage 3.5 of the masterclass — the $0 route: unlimited generations, your own GPU, your own machine.)*

---

## What "going local" means

| | Cloud (Veo / Runway / Kling) | Local (ComfyUI + Wan) |
|---|---|---|
| Cost | ~$0.10–0.40 / second | **$0 per generation** (you pay for electricity) |
| Limits | Credits | **Unlimited** takes & retries |
| Privacy | Your footage goes to their servers | Everything stays on your machine |
| Control | Prompt + some settings | **Every knob**: seeds, CFG, schedulers, LoRAs, controlnets |
| Cost of entry | None | A decent NVIDIA GPU + an afternoon of setup |

**When to go local:** you're generating daily, you want 20 takes per shot without crying, you care about privacy, or you just love tinkering.

---

## 🟢 What's set up in this workspace (ComfyUI @ /home/user/ComfyUI)

```
ComfyUI/
├── main.py                         ← server (port 8188)
├── custom_nodes/ComfyUI-Manager    ← node/model package manager
├── custom_nodes/ComfyUI_IPAdapter_plus ← IPAdapter (character consistency)
├── models/workflows/               ← validated workflows for THIS film:
│   ├── wan-i2v-the-last-lighthouse.json        (Wan 2.6 image→video)
│   ├── wan-firstlast-the-last-lighthouse.json  (Wan 2.6 start+END frame→video)
│   ├── wan22-i2v-the-last-lighthouse.json      (Wan 2.2 image→video, raw graph)
│   ├── wan22-official-i2v-the-last-lighthouse.json (Wan 2.2 official template, pre-loaded)
│   └── character-ipadapter.json                (SD1.5 + IPAdapter FaceID)
├── models/unet|text_encoders|clip_vision|vae/  ← model files go here
└── input/                          ← staged frames (shot-01/07/08, character-sheet)
```

All workflows are **generated from the live server's schemas and validated** — run `python3 ai-film-course/tools/build_comfy_workflow.py` anytime to rebuild + re-validate them.

> ⚠️ This sandbox is CPU-only and blocks HuggingFace, so model weights can't be
> downloaded *here* — but everything else (server, packs, workflows, validation)
> is real and running. `ai-film-course/tools/bootstrap.sh` restores the whole
> environment in one command on your own machine (or after a sandbox reset).

---

## 🖥️ Your machine: hardware reality check

Wan 2.6 I2V is a **14-billion-parameter** video model. Honest table:

| GPU | What you can run | Expected speed (480p, 81 frames ≈ 5 s) |
|---|---|---|
| 8 GB (RTX 3070/4060) | Wan 2.6 480p **GGUF Q4** (~8 GB) via ComfyUI-GGUF | ~8–15 min/clip (slow but free) |
| 12 GB (RTX 4070/3080) | Wan 2.6 480p **fp8** (ComfyUI `--lowvram`) | ~5–10 min/clip |
| 16 GB (RTX 4080) | Wan 2.6 480p fp8 comfortably | ~3–6 min/clip |
| 24 GB (RTX 4090/3090) | Wan 2.6 **720p** fp8, longer clips | ~2–5 min/clip |
| Apple Silicon | Not practical for 14B video models — stick to the cloud or small image models | — |

*(Approximate, model-dependent — treat as ballpark.)*

---

## 📦 The model files (download once, generate forever)

All from the **Comfy-Org repackaged** repos on HuggingFace (`split_files/` folders), or one-click via **ComfyUI-Manager → Model Manager → search "wan"**.

### Wan 2.6 (the workflows reference the fp8 480p set)

| File | Size | Goes to |
|---|---|---|
| `wan2.6_i2v_480p_14B_fp8_e4m3fn.safetensors` | ~14 GB | `models/unet/` |
| `wan2.6_i2v_480p_14B_bf16.safetensors` | ~28 GB | `models/unet/` (24 GB cards) |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | ~6 GB | `models/text_encoders/` |
| `clip_vision_h.safetensors` | ~0.4 GB | `models/clip_vision/` |
| `wan_2.1_vae.safetensors` | ~0.25 GB | `models/vae/` |

### Wan 2.2 (newer, 1280×704 native)

| File | Size | Goes to |
|---|---|---|
| `wan2.2_i2v_a14b_720p_fp8_e4m3fn.safetensors` *(raw-graph variant)* | ~14 GB | `models/unet/` |
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` + `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` *(official dual-model path)* | ~28 GB | `models/unet/` |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | ~6 GB | `models/text_encoders/` |
| `wan_2.2_vae.safetensors` | ~0.25 GB | `models/vae/` |

💡 **Wan 2.2, two honest paths:**
- **Official:** ComfyUI's bundled template (Workflow → Browse Templates → search "Wan2.2 i2v") uses *two* unets (high-noise + low-noise) chained in one component node — best quality, more VRAM, more setup.
- **Our raw-node graph** (`wan22-i2v-the-last-lighthouse.json`, validated) runs the conventional UNETLoader→KSampler chain — works with a single repackaged fp8 file. Use whichever your VRAM prefers.

💡 **Low-VRAM path (8 GB):** install the `ComfyUI-GGUF` pack, download a Q4/Q5 quant of the 14B I2V model, and swap `UNETLoader` for its `UnetLoaderGGUF` node (same input pin, drop-in).

---

## 🧰 Install on your own machine (15 minutes)

### Windows (easiest)
1. Download the **ComfyUI portable** from the GitHub releases page.
2. Extract, run `run_nvidia_gpu.bat`. Done — it bundles Python + CUDA.
3. Add ComfyUI-Manager + ComfyUI_IPAdapter_plus into `custom_nodes/` (below), or run `ai-film-course/tools/bootstrap.sh` in Git Bash.

### Linux / WSL2 (NVIDIA)
```bash
# 1. clone + venv
git clone https://github.com/comfyanonymous/ComfyUI && cd ComfyUI
python3 -m venv .venv && source .venv/bin/activate

# 2. PyTorch with CUDA (match your driver; cu130 or cu126)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130

# 3. the rest + packs
pip install -r requirements.txt
git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
git clone --depth 1 https://github.com/cubiq/ComfyUI_IPAdapter_plus.git custom_nodes/ComfyUI_IPAdapter_plus

# 4. go
python main.py --listen 0.0.0.0
# → open http://localhost:8188
```

**One-command restore / fresh-machine setup:** `bash ai-film-course/tools/bootstrap.sh` (reinstalls deps, packs, regenerates + validates the workflows, rebuilds the film).

---

## 🎬 Running THE LAST LIGHTHOUSE locally, shot by shot

1. Open ComfyUI → **Workflow → Open** → `models/workflows/wan-i2v-the-last-lighthouse.json`.
2. Confirm the model dropdowns resolved (they will once the files are in place).
3. **Shot 01:** queue it. Output lands in `output/` (`the_last_lighthouse_00001.mp4`).
4. **Shots 02–08:** drop each `demo-film/frames/shot-XX.png` into `input/`, select it in `LoadImage`, and paste that shot's **motion prompt** from `demo-film/storyboard.md` (the "Stage-4 motion prompt" column) into the positive `CLIPTextEncode`.
5. **The trick shots:**
   - *Shot 07 → 08 (the reveal):* use `wan-firstlast-the-last-lighthouse.json` — both frames locked, the model only invents the journey (see CHARACTER-CONSISTENCY.md, Layer 4).
   - *Character shots:* keep the subject slow and central; low CFG; same locked frame per scene.
6. **Iterate:** new seed per take, keep 3–5 takes per shot, cut the best in CapCut/DaVinci.
7. **Assemble** with the course's `build_film.sh` (Stage 6) — swap your generated clips in place of the Ken Burns clips.

### Settings that matter (Wan 2.6)

| Setting | Value | Why |
|---|---|---|
| `length` (frames) | 81 (480p) / 121 (720p) | ~5 s of video @16 fps |
| `steps` | 20–30 | More = smoother, slower |
| `cfg` | 6.0 | Higher = prompt-obedient but flickery; lower = dreamy |
| `sampler/scheduler` | `euler` / `simple` | Solid default for Wan |
| `seed` | lock per shot | Reproducibility; change it for new takes |
| `fps` in CreateVideo | 16 | Native training fps — upscale to 24 with RIFE later |

---

## 🧩 The local toolkit (install via ComfyUI-Manager, one click each)

| Pack | What it's for |
|---|---|
| **ComfyUI-GGUF** | Quantized models → run 14B video on 8 GB cards |
| **ComfyUI Frame Interpolation** | RIFE → smooth 16 fps to 24/30 fps |
| **ComfyUI-VideoHelperSuite** | Load/process/split video files in the graph |
| **ComfyUI-Upscalers / UltimateSDUpscale** | 480p → 1080p/4K upscaling |
| **ComfyUI_IPAdapter_plus** | FaceID — character consistency in stills |

**Character consistency:** the full local playbook is `CHARACTER-CONSISTENCY.md` — tokens → character sheet → IPAdapter → start-frame anchoring, with the sheet generated in `demo-film/frames/character-sheet/`.

**More local video models to explore** (all native in this ComfyUI build): Wan 2.6/2.2, LTX-Video 2 (fast, small), HunyuanVideo (strong text-to-video). Mix and match per shot.

---

## 🐛 Troubleshooting (real ones)

| Symptom | Fix |
|---|---|
| `CUDA out of memory` | `--lowvram` (or `--novram`), smaller resolution, GGUF quant |
| Black or gray frames | CFG too high, or VAE mismatch — check filenames |
| Weird flicker | Lower `cfg`, more `steps`, lock the seed |
| Slower than expected | fp8 model; quantize where supported |
| Server can't see new models | Refresh the browser (dropdowns rebuild) |
| Manager can't reach GitHub | This sandbox blocks it; on your machine it's just internet access |
| Environment got reset (sandbox) | `bash ai-film-course/tools/bootstrap.sh` — the course itself is committed in git, so it survives |

---

## ✅ What's verified vs. what needs your GPU

**Verified live in this workspace:** ComfyUI 0.33 boots, UI serves, ComfyUI-Manager + IPAdapter pack load, **all workflows validate cleanly** against the server's type system, the start frames are staged in `input/`.

**Needs your GPU machine:** the actual model weights and rendering — everything above is pre-wired for it.

**Next step after your first local render:** bring your clip back and mix it into the film with `build_film.sh` — you've now run the full pipeline *free*.
