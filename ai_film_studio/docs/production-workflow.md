# 🎞️ Production Workflow — 5–15 min Hinglish Short Film (2026, Local)

Ye pipeline **short film ke liye tuned** hai: 15–25 scenes, Hinglish dialogues,
48GB+ local GPU. Har stage ke output ko review karna mat bhoolna — AI film me
QC hi difference banata hai.

---

## Stage 1 — Script & Direction (Bilingual/Hinglish)
**Tool:** Ollama + Qwen3 32B / Llama 3.3 70B
- Prompt: ek-line idea → 3-act structure, Hinglish dialogues
- Output: `script.md` (scenes × dialogues × shot descriptions)
- Tip: dialogues ko `[HINGLISH]` tone me likhwao: "Arre bhai, sun na…"
- **QC:** 1 min read yourself — plot holes fix karo

## Stage 2 — Character Bible
**Tools:** Qwen-Image (text in image) / FLUX.2 klein + IP-Adapter
- Har main character ke liye: `character_<name>_ref.png` (front + 3/4 angle)
- Appearance notes (hair/clothes/age) `characters.yaml`
- **QC:** Har reference me same features — nahi toh regenerate

## Stage 3 — Storyboard (15–25 Keyframes)
**Tool:** HunyuanImage 3.0 (48GB) ya FLUX.2
- Har scene ke liye: keyframe + camera move note (dolly-in, pan, slow zoom)
- Style keep karo: same seed / same prompt prefix + `--style cinematic`
- **QC:** storyboard board me check karo (KupkaProd style storyboard review)

## Stage 4 — Scene Video Generation
**Tool:** HunyuanVideo 1.5 (text) / Wan 2.2 I2V-14B (from keyframe)
- Har scene 5–10s, 720p/1080p, 24–30fps
- Character consistency ke liye IP-Adapter + reference image feed
- Multi-GPU: LTX-2.3 aur Hunyuan alag cards pe parallel
- **QC:** continuity — same lighting, same costume, same face

## Stage 5 — Voiceover / Dialogue
**Tool:** Chatterbox (Hindi) + Qwen3-TTS (English lines) + Kokoro (narration)
- Line-by-line TTS, 33–44kHz WAV export
- Emotion tags: `[happy]` `[sad]` `[angry]` (Orpheus style) jahan possible
- **QC:** lips ke liye TTS pause/breath control

## Stage 6 — Lip-Sync
**Tool:** LatentSync (hero shots) / MuseTalk (fast scenes)
- Audio + scene video → synced output
- **QC:** side profiles check karo (LatentSync best)

## Stage 7 — Music + SFX
**Tool:** ACE-Step 1.5 (score, 4min+ tracks) + YuE (theme song option) + MMAudio (foley)
- Mood mapping: scene → tempo/instrument (tabla/sitar/violin vibe bhi try karo)
- SFX: whoosh, ambience, door, rain — MMAudio from video

## Stage 8 — Subtitles (Hinglish)
**Tool:** WhisperX (word-level)
- Output .srt — Hinglish transcription, phir English translation column
- Remotion ya FFmpeg `subtitles` filter se burn-in

## Stage 9 — Edit & Assembly
**Tools:** MoviePy + FFmpeg + Remotion
- Timeline order, transitions (crossfade 0.5s, match cut)
- Title cards, credits (Remotion)
- Color grade: FFmpeg LUTs ya OpenColorIO (teal-orange / warm Indian tone)
- Audio mix: ducking VO over music, loudness -14 LUFS

## Stage 10 — Master & Upscale
**Tool:** SUPIR / Real-ESRGAN + FFmpeg
- 1080p → 4K (optional), H.264 `-crf 18` / HEVC for master
- Export: `final_1080p.mp4` + `final_4k.mkv` + `poster.png`

---

## ⚡ Time Budget (48GB+, realistic)
| Stage | Time |
|---|---|
| Script | 30 min |
| Characters + Storyboard | 1–2 hr |
| 20 scenes × ~15 min render | 5–8 hr |
| Voice + lip-sync | 2–3 hr |
| Music/SFX | 1–2 hr |
| Edit + master | 3–4 hr |
| **Total** | **~1.5–2 din** (machine mostly render me busy) |

---

## 🔁 Resumable Pipeline (KupkaProd style)
Har stage ke baad `state.json` jaisa checkpoint rakho (project folder me
`scenes/`, `keyframes/`, `audio/`, `final.mp4`). Scene 7 ka render break ho toh
sirf scene 7 dobara — latest work lost nahi.
