# 🧱 Local Stack — Full Breakdown (48GB+ / Multi-GPU)

> 100% local, free. Commercial movie banate waqt license column zaroor check karein.

## 1. Brain — Script / Direction (CPU + RAM)
| Tool | Install | Notes |
|---|---|---|
| Ollama | `curl -fsSL https://ollama.com/install.sh \| sh` | `ollama pull qwen3:32b` ya `llama3.3:70b` (GGUF quantized) |
| (Option) llama.cpp | GitHub `ggml-org/llama.cpp` | Manual GGUF run |

**License:** Apache-2.0 / Llama community

## 2. Video Engines (GPU)
| Model | Repo | VRAM | Use |
|---|---|---|---|
| HunyuanVideo 1.5 | github.com/Tencent/HunyuanVideo | ~14–24GB | **Main cinematic engine** |
| Wan 2.2 (5B/14B) | github.com/Wan-Video/Wan2.2 | 16–48GB | I2V + best quality/VRAM |
| LTX-2.3 | github.com/Lightricks/LTX-Video | ~24GB | **4K/50fps + native audio** |
| SkyReels V2 | github.com/SkyworkAI/SkyReels-V2 | ~14GB+ | Infinite/long continuous shots |
| CogVideoX-5B | github.com/THUDM/CogVideo | ~16GB | Quick tests |

## 3. Image / Keyframes
| Model | VRAM | License | Use |
|---|---|---|---|
| HunyuanImage 3.0 (80B) | 48GB+ | Open | Complex cinematic keyframes |
| FLUX.2 dev | ~24GB | ❌ non-commercial | Quality (personal) |
| FLUX.2 klein/schnell | ~8–16GB | ✅ Apache | Commercial-safe quality |
| Qwen-Image | 8–24GB | ✅ Apache 2.0 | In-image text (posters, titles) |
| SDXL / SD 3.5 | 6–16GB | OpenRAIL | LoRA/ControlNet ecosystem |

## 4. Character Consistency
| Tool | Purpose |
|---|---|
| ComfyUI_IPAdapter_plus | Character reference → any scene |
| ComfyUI-InstantID | Face-ID injection |
| ComfyUI-PuLID | Identity w/o clean face crops |
| ROICtrl (movie agent style) | Region-based control |

## 5. Voices (Hinglish)
| Model | License | Notes |
|---|---|---|
| Chatterbox (multilingual) | MIT | Hindi + English, 5s clone, best quality |
| Qwen3-TTS | Apache 2.0 | 3s clone, streaming |
| CosyVoice 3 | Apache 2.0 | Zero-shot, dialects |
| Kokoro-82M | Apache 2.0 | CPU, 54 voices (narration backup) |

## 6. Music / SFX
| Model | License | Notes |
|---|---|---|
| ACE-Step 1.5 | MIT | 4–10 min songs + vocals, 4GB |
| YuE | Apache 2.0 | Best quality vocals, slow (~1hr/5min song) |
| MMAudio | Research/open | Video-synced foley |
| MusicGen (AudioCraft) | MIT | 30s loops, fast |

## 7. Lip-Sync / Talking Head
| Model | License | Use |
|---|---|---|
| LatentSync | Apache 2.0 | Hero shots, best fidelity |
| MuseTalk | MIT-ish | Speed/quality balance |
| Wav2Lip | Non-commercial-ish | Quick sync |
| Hallo3 | Research | Long-form (60s+) talking head |

## 8. Post-Production
| Tool | Use |
|---|---|
| MoviePy + FFmpeg | Assembly, encoding, muxing |
| Remotion | Titles, animated captions |
| WhisperX | Hinglish word-level subtitles |
| SUPIR / Real-ESRGAN | 1080p → 4K upscale |
| OpenColorIO + FFmpeg LUTs | Cinematic color grade |
| PySceneDetect | Scene detection |
