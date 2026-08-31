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

# Step 4 — Models download (license-aware, disk-check wala)
python3 ai_film_studio/setup/04_download_models.py --tier core   # video engines
python3 ai_film_studio/setup/04_download_models.py --tier optional
python3 ai_film_studio/setup/04_download_models.py --tier audio
# (manual HF commands bhi docs me: docs/model-downloads.md)

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

## 🎬 Director Agent (Script → Scenes → Render → Final MP4)

`director_agent/` me ek **pure-Python CLI** hai (sirf Python 3 stdlib — koi extra
dependency nahi). Ye aapka mini production studio automate karta hai:

```
director_agent/
├── director.py            # CLI entry point
├── config.json.example    # config template (copy -> config.json)
├── manifest.json          # Har workflow ke prompt/image/output nodes ka map
├── comfy.py               # ComfyUI API client: UI->API convert, upload, queue, download
├── planner.py             # Idea -> script (Hinglish) via Ollama (--mock demo bhi)
├── storyboard.py          # Scene -> keyframe image prompts
├── renderer.py            # Keyframes + scene videos render (resumable state)
├── assembler.py           # ffmpeg concat -> final.mp4 (+audio/subtitles)
├── tts.py                 # Optional voice (chatterbox/custom)
├── prompts/               # LLM system prompts (01_plan, 02_storyboard)
└── tests/test_converter.py# Workflow converter contract tests (pass ✓)

workflows/                  # Official example workflows (verified node maps):
├── wan21_14b_t2v_example.json      # Wan 2.1 14B T2V
├── wan22_5b_i2v_example.json       # Wan 2.2 5B TI2V (default engine)
├── hyvideo_t2v_example.json        # HunyuanVideo 1.5 T2V
├── hyvideo_i2v_example.json        # HunyuanVideo 1.5 I2V
└── ltx23_t2v_i2v_example.json      # LTX-2.3 (Gemma API chahiye, advanced)
```

### Usage

```bash
cd ai_film_studio/director_agent
cp config.json.example config.json        # apne paths/models set karein

# 1) Idea -> Hinglish script + storyboard (Ollama chahiye; --mock se bina Ollama demo)
python3 director.py plan --idea "Ek chai ki tapri ka sapna" --scenes 8 [--mock]

# 2) Cast: har character ka reference image (consistency ke liye)
python3 director.py cast [--dry-run]

# 3) Preview (koi network call nahi)
python3 director.py render --dry-run --parallel 2 --identity

# 4) Real render: --identity = IP-Adapter character consistency,
#    --parallel 2 = do ComfyUI instances pe scenes parallel (multi-GPU)
python3 director.py render [--scene 1,2,3] [--workflow wan22_5b_i2v_example.json] \
                           [--identity] [--parallel 2]

# 5) Final film (simple concat)
python3 director.py assemble

# 5b) FULL post-production: voice + lip-sync + music + subtitles + loudness
python3 director.py post --tts chatterbox --lipsync latentsync \
                         --music acestep --subtitles --language hi

# 6) QC/review (scene quality + continuity report)
python3 director.py qc --json-out qc_report.json

# 7) Multi-language dubbing (Ollama translate -> TTS -> final_en.mp4)
python3 director.py dub --lang en --dry-run    # kitni lines translate hongi
python3 director.py dub --lang en

# 8) Progress
python3 director.py status
```

**Keyframe engines** (`keyframe_engine` in config): `sdxl` (default) |
`ipadapter` (character ref + IP-Adapter, config me `keyframe_identity: true`)
| `qwen_image` (Apache, in-image text ke liye).

**Multi-GPU:** config me `comfy_urls: ["http://127.0.0.1:8188", "http://127.0.0.1:8189"]`
— phir `render --parallel 2` scenes dono GPU pe distribute karta hai.

### 🎙️ Post-production engines (config me commands set karein)

| Engine | config key | command template |
|---|---|---|
| Chatterbox TTS | `tts.command` | `chatterbox --text "%TEXT%" --output_path "%OUT%"` |
| LatentSync | `lipsync.command` | `python scripts/inference.py --video_path "%VIDEO%" --audio_path "%AUDIO%" --output_path "%OUT%"` |
| Wav2Lip | `lipsync.command` | `python inference.py --checkpoint_path ckpt.pth --face "%VIDEO%" --audio "%AUDIO%" --outfile "%OUT%"` |
| ACE-Step | `music.command` | `python cli.py --prompt "%PROMPT%" --duration %DURATION% --output "%OUT%"` |
| Subtitles | — | `pip install faster-whisper` (auto `hi`/`en` transcription) |

### 🧪 Tests (GPU ke bina — sandbox me verified)
```bash
cd ai_film_studio/director_agent
python3 tests/test_post.py          # SRT + command templates
python3 tests/test_converter.py     # 5 workflows UI->API conversion
python3 tests/test_templates.py     # SDXL/IP-Adapter/Qwen templates
python3 tests/test_qc_dub.py        # QC checks (black/cuts/PSNR) + dub translate
python3 tests/test_e2e.py           # mock ComfyUI se plan->render->assemble (multi-GPU)
```

### 📥 Model downloader (`setup/04_download_models.py`)
- Manifest: `setup/models.json` (17 models, ~311GB, licenses ke saath)
- `--tier core|optional|audio|all` • `--name "Wan"` filter • `--dry-run` plan
- Disk-space check + `[VERIFY repo id!]` wale repos pe warning

State har scene ka `meta/state.json` me save hota hai — **resumable**: koi scene
fail ho toh sirf wahi scene dobara render hota hai.

---

## ⚠️ Important Notes

- **Disk:** Models total ~400GB–1TB. 2TB NVMe recommended.
- **License:** Movie *sell* karni hai toh sirf Apache-2.0/MIT models use karein.
  FLUX.1/2 **dev** = non-commercial; schnell/klein commercial-safe.
- **VRAM sharing:** Multi-GPU pe ComfyUI ko `--gpu-only` ya per-model offload ke
  saath chalayein; LTX aur Hunyuan alag-alag cards pe parallel bhi chal sakte hain.
- **Ye sandbox GPU-less hai** — isliye yahan sirf kit verify kiya ja sakta hai,
  actual rendering aapki machine pe hogi.
