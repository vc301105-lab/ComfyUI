# 🎬 AI Filmmaking Masterclass — From Zero to Your First AI Film

A complete, hands-on course that takes you from "I've never made a film" to shipping your first AI short — **and it includes a real film built step by step alongside the lessons.**

> 💾 This course lives **inside the ComfyUI git repo** (`/home/user/ComfyUI/ai-film-course/`)
> and is committed to the session branch — so sandbox resets can never eat it again.
> `tools/bootstrap.sh` restores the environment in one command.

## What's inside

| File | What it is |
|---|---|
| **GUIDE.md** | The full step-by-step masterclass — Stages 0–7 (concept → script → style lock → storyboard → key frames → animation → voice & sound → editing → grade/export/ship), a 30-day roadmap, legal/ethics, and a build log |
| **GO-LOCAL.md** | 🖥️ Stage 3.5 — the free & open-source route: ComfyUI + Wan 2.6/2.2 setup, model list, GPU guide, and validated image-to-video workflows for the demo film |
| **CHARACTER-CONSISTENCY.md** | 🎭 The local playbook for keeping the same character across shots: tokens → character sheet → IPAdapter/LoRA → start-frame anchoring (with a validated IPAdapter FaceID workflow) |
| **PROMPTS.md** | Copy-paste prompt library: style presets, shot prompts, negative prompts, motion prompts, voice-direction cheat sheet, music prompts |
| **YOUTUBE-KIT.md** | 🚀 Stage 7 ship kit: titles, description, tags, Shorts caption, upload checklist, AI-disclosure, festivals |
| **tools/** | `build_comfy_workflow.py` (generates & validates all workflows against the live server) · `bootstrap.sh` (one-command restore) |
| **demo-film/** | 🎥 **THE LAST LIGHTHOUSE** — the 60-second AI film we build together in this course |

## The demo film (`demo-film/`)

```
demo-film/
├── script.md          ← logline + narration script + shot list
├── storyboard.md      ← every shot with the EXACT prompt used
├── frames/            ← 8 AI-generated key frames (+ poster.png, character-sheet/)
├── audio/
│   ├── narration.mp3  ← AI-narrated voiceover
│   ├── ambience.wav   ← procedural storm/sound bed (synthesized, no library!)
│   ├── music.wav      ← procedural ambient score (synthesized, no library!)
│   └── make_ambience.py / make_music.py ← regenerate the beds (deterministic)
├── subtitles.srt      ← YouTube/Reels captions
├── build_film.sh      ← assembles film.mp4 (16:9, Ken Burns + crossfades)
├── build_vertical.sh  ← assembles film-vertical.mp4 (9:16 Shorts cut, pans)
├── make_thumbnail.py  ← composits thumbnail.png from the poster
├── film.mp4           ← 🎬 the finished film (VO + storm + score)
├── film-vertical.mp4  ← 📱 the 9:16 Shorts/Reels cut
└── thumbnail.png      ← YouTube/Shorts thumbnail (1280x720)
```

## How to use this course

1. Read **GUIDE.md** from top to bottom (each stage ends with a ✋ hands-on step).
2. Follow along with the demo: open `demo-film/script.md` → `storyboard.md` → then watch `film.mp4`.
3. Copy the demo's structure for **your** film: same folders, same shot list template, same style-block discipline.
4. Re-run `demo-film/build_film.sh` anytime to re-assemble the film from the frames + audio.
5. Going local? **GO-LOCAL.md** + the workflows in `models/workflows/` get you rendering video for $0.

## The one-line version of the whole course

> **AI filmmaking is directing, not prompting.** Lock the story, lock the style, lock every shot as a still image *first*, animate with motion-only prompts, cast a voice by auditioning it on your actual lines, and make the film in the edit. The AI is your crew — you're the director.

Happy filmmaking! 🎬
