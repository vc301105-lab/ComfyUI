# 🚀 THE LAST LIGHTHOUSE — Distribution Kit (Stage 7: Ship)

Everything you need to publish the film. Files: `film.mp4` (16:9 master),
`film-vertical.mp4` (9:16 Shorts cut), `thumbnail.png` (1280×720), `subtitles.srt`.

---

## 1. Titles (pick one per platform)

| # | Title |
|---|---|
| 1 | **THE LAST LIGHTHOUSE — 60-Second AI Short Film** |
| 2 | **She Kept the Light for Ten Years. Then a Ship Came. | AI Short Film** |
| 3 | **The Last Lighthouse (Sci-Fi AI Short Film — Full Film)** |

Shorts/Reels: `The last lighthouse on Earth. She kept the light for 10 years. Then a ship came. 🌊🚢 #aifilm #shorts`

---

## 2. Description (copy-paste, fill in your links)

```
When the oceans took the cities, one keeper stayed — to keep the lamp
burning in case anyone was left to find their way home. Then, one
morning, a ship that should not exist blinked on the horizon.

THE LAST LIGHTHOUSE — a 60-second AI short film.
Written, directed & generated as a complete AI filmmaking walkthrough:
script → style lock → storyboard → key frames → AI narration → sound
design → edit → grade → export.

🎬 Tools: AI image generation (locked style block + character tokens),
AI voice casting, procedural sound design (synthesized storm + score),
ffmpeg assembly — plus open-source Wan 2.6 image-to-video workflows for
ComfyUI (see the course repo for the full pipeline).

00:00 The last city
00:26 The radio fell silent
00:41 A ship that should not exist

#AIFilm #AIShortFilm #ComfyUI #WanAI #SciFiShort #AIGenerated
```

---

## 3. Tags (paste into YouTube)

```
ai short film, ai film, ai filmmaking, ai generated movie, comfyui,
wan 2.6, wan 2.2, image to video, text to video, sci fi short film,
lighthouse, post apocalyptic, ai voice, ai narration, ai sound design,
60 second film, short film 2026, ai movie, open source ai
```

---

## 4. Upload checklist

- [ ] `film.mp4` → YouTube (16:9, 1080p24)
- [ ] `film-vertical.mp4` → Shorts / Reels / TikTok
- [ ] `thumbnail.png` uploaded as custom thumbnail
- [ ] `subtitles.srt` attached (Upload captions → English → Upload file)
- [ ] **AI disclosure: YouTube Studio → video details → "Altered content" → YES** *(synthetic/generated media — required by YouTube's policy)*
- [ ] Reels/TikTok: use their built-in AI-generated content label
- [ ] Pin a comment: "How this was made — [link to course/docs]"

---

## 5. Final QC numbers (verified)

| Check | Value |
|---|---|
| Master | 1920×1080 @ 24 fps, H.264, stereo AAC |
| Duration | ~52 s |
| VO loudness | ≈ −14 LUFS (YouTube target) |
| Storm bed | RMS ≈ −33 dBFS under the VO |
| Score | peak ≈ −25 dBFS, swells only at the reveal |
| Vertical | 1080×1920 @ 24 fps, SAR 1:1 |
| Thumbnail | 1280×720 |

---

## 6. Festivals & communities

- **Runway AIFF** (Runway AI Film Festival) — annual AI film competition
- r/aivideo, r/StableDiffusion, ComfyUI Discord, Runway Discord
- Curious Refuge, AI Film Academy (curriculum + community)

---

## 7. Rights & disclosure notes

- All visuals: AI-generated from original prompts (kept in `storyboard.md`).
- Voice: AI-synthesized (cast by audition — see GUIDE Stage 5).
- Sound bed + score: **synthesized in code** (`make_ambience.py`, `make_music.py`) — zero third-party samples, zero licenses needed.
- Your edit, arrangement, and sound design are the authored work.
- Keep records of prompts + generations (festival submissions ask).

## 8. Rebuilding from scratch (any machine)

```bash
bash tools/bootstrap.sh            # env + workflows
python3 demo-film/audio/make_ambience.py   # storm bed
python3 demo-film/audio/make_music.py      # score
python3 demo-film/make_subtitles.py        # captions
python3 demo-film/make_thumbnail.py        # thumbnail
./demo-film/build_film.sh          # film.mp4
./demo-film/build_vertical.sh      # film-vertical.mp4
```
