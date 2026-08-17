# 🎬 Master AI Filmmaking From Scratch — Step by Step

> The complete path from "I've never made a film" to shipping your first AI short.
> Built alongside a real worked example: **THE LAST LIGHTHOUSE** (see `demo-film/`) — a 60-second AI film produced end-to-end with the exact methods in this guide.

---

## How to use this course

- Read Stages **0 → 7** in order. Each stage ends with a ✋ *Hands-on* step you should actually do.
- `demo-film/` is this course's worked example. Open its files as you read the matching stage — seeing a real script, real prompts, and a real assembled film teaches faster than any prose.
- `PROMPTS.md` is your copy-paste library. Steal from it shamelessly.
- Going local (free generations)? `GO-LOCAL.md` (ComfyUI + Wan) and `CHARACTER-CONSISTENCY.md` (the identity playbook).
- Ready to publish? `YOUTUBE-KIT.md` (Stage 7).

---

## The pipeline (memorize this)

```
Concept → Script → Style lock → Storyboard → Key frames → Animate → Voice & Sound → Edit → Grade & Export → Ship
```

**The most important mindset shift in this entire course:**

> **AI filmmaking is directing, not prompting.** The AI is your crew — concept artist, cinematographer, voice actor, composer. You are the director. Your taste, your shot selection, your edit are what make it a *film* instead of a pile of clips. Nobody has ever watched a great film because the prompts were long.

---

# Stage 0 — Gear up: your tool stack (2026)

Four tools are enough to start. Resist the urge to collect more.

| Job | Pick ONE | Notes |
|---|---|---|
| Key frames (images) | Midjourney v7 · Nano Banana 2 (Gemini) · Flux · Ideogram | Midjourney is the community standard for cinematic stills |
| Video (animate frames) | Veo 3.1 (Google Flow) · Runway Gen-4.5 · Kling 3.0 · Luma Ray | Table below — pick one and learn it deeply |
| Voice | ElevenLabs · (or the narration pipeline used in this demo) | Audition multiple voices on YOUR lines |
| Edit | CapCut (free) or DaVinci Resolve (free, pro-grade) | DaVinci = best free color tools on earth |

### The 2026 video-model landscape

| Model | Best for | Why |
|---|---|---|
| **Veo 3.1** (Google Flow) | Best all-around cinematic output | True 4K, native audio, "Ingredients to Video" locks characters/settings from your reference images |
| **Runway Gen-4.5** | Directing & control | Motion Brush, camera control, production workstation UI |
| **Kling 3.0 / Turbo** | Value + photorealistic motion | ~$0.10–0.14/sec, Character ID keeps faces consistent; best budget pick |
| **Luma Ray** | Atmospheric, moody image-to-video | Great camera movement from a single keyframe |
| **Seedance 2.5** | Long-form image-to-video | Long takes |
| **Wan 2.6 / 2.2 / HunyuanVideo / LTX-2** | Free & open-source | Run locally in **ComfyUI** — unlimited generations, steeper setup (see GO-LOCAL.md) |

*(Sources: see "Sources & further reading" at the end of this guide.)*

### 💡 Budget reality check

A polished 60-second film needs roughly **15–25 generated clips** — you'll generate 3–5 takes per shot and keep the best. At $0.10–0.40/sec that's **$10–50 in credits per film minute** — or **$0** on open-source models (you pay in GPU time and an afternoon of setup).

**This workspace has ComfyUI checked out** at `/home/user/ComfyUI` — the open-source route is literally installed (see Stage 3.5).

✋ **Hands-on:** create your project skeleton — copy the demo structure:

```
my-film/
├── script.md
├── storyboard.md
├── frames/
├── audio/
└── film.mp4  (at the end!)
```

---

# Stage 1 — Concept & script (Day 1)

### The rules of a great first film

1. **60–90 seconds.** Short films win: costs stay sane, coherence stays possible, festivals and Shorts favor them.
2. **One character, one location, one moment of change.** That's a complete story arc at this length.
3. **Voiceover > dialogue.** Lip-sync is still the hardest problem in AI film. A narrator sidesteps it entirely. (Our demo is 100% VO.)
4. **Start from an emotion, not a tech demo.** Decide: *what do I want the viewer to feel in the last five seconds?* Write that moment first, then build the story backward to it.

### Logline formula

> `When [inciting event], [character] must [goal] or else [stakes].`

**Ours:** *When the oceans take the cities, the last lighthouse keeper on Earth keeps the lamp burning in case anyone is left to find their way home — and one morning, someone does.*

### Use an LLM as your writing room (then overrule it)

Paste this into any LLM:

```
You are a screenwriting partner. Help me write a 60-second AI short film.
Constraints: 1 character, 1 location, NO dialogue — voiceover only,
8–10 shots, 100–120 words of narration.
Output:
1) A logline.
2) The narration in 3 acts: setup → struggle → turn.
3) A shot list table: shot # | image description | motion | VO line | duration.
Style reference: [paste 2–3 films you love, e.g. "Blade Runner 2049, The Lighthouse"].
Then critique your own draft as a festival screener and give me a second draft.
```

**Then YOU edit it.** The AI drafts; you decide. Cut a line, merge two shots, change the ending. That editing pass is directing.

✋ **Hands-on:** write your logline + ~110-word narration + 8-shot list. (Ours: `demo-film/script.md`.)

---

# Stage 2 — Style lock & storyboard (Day 2)

### The style-frame ritual (non-negotiable)

Before generating any story shot, generate **4–6 style frames** — images that are pure look-and-feel (not your shots): vary lighting, weather, color. Pick ONE. Then extract its look into a reusable **style block** — a text snippet you paste verbatim onto every prompt.

**Our locked style block (used on all 8 shots of the demo):**

```
Cinematic 16:9 widescreen film still, moody atmospheric science fiction,
teal-and-amber color grade, volumetric light, heavy atmosphere,
subtle film grain, 35mm anamorphic lens, ultra-detailed, epic composition.
```

This single habit — one style block, reused verbatim — is what makes an AI film look like *one movie* instead of a random montage.

### The character sheet

Lock your character three ways, in order of cost:

1. **Text tokens** — a one-sentence description repeated verbatim in every prompt they appear in. Ours: *"a weathered woman in her late 40s, silver-streaked dark hair tied back, deep-set tired eyes, wearing a faded mustard-yellow raincoat over a dark wool sweater."*
2. **Reference images** — generate the character in 4–6 angles/expressions (front, 3/4 left, 3/4 right, profile, full-body) — see `CHARACTER-CONSISTENCY.md` and the demo's generated sheet in `demo-film/frames/character-sheet/`. Feed them to your video tool's identity feature (Kling **Character ID**, Veo **Ingredients**) or use as image prompts.
3. **Fine-tuning** — train a LoRA on 15–30 character images (Kohya / ai-toolkit) when 1 and 2 still drift. The nuclear option — most 60-second films never need it.

### Shot grammar crash course

| Shot | Feel it creates | Use it for |
|---|---|---|
| Extreme wide (EWS) | Scale, isolation | Opening and closing the film |
| Wide (WS) | Context | Placing the character in their world |
| Medium (MS) | Body language | Action beats |
| Close-up (CU) | Emotion | The turn of the story |
| Extreme close-up (ECU) | Texture, detail | Hands, objects, eyes |
| Insert | Information | The dead radio, the logbook, the photo |

**Directing rules that survive AI generation:**

- Open wide → move closer as emotion rises → resolve wide, or on your strongest close-up.
- Keep screen direction consistent — don't let the character flip left/right between shots.
- Every shot needs **one clear motion** (what moves in the frame) and **one clear job** (what it tells the audience). If a shot has two jobs, it's two shots.

**Shot list template** — one row per shot:

| # | Type | Image description | Motion (for Stage 4) | VO line | Duration |
|---|---|---|---|---|---|

Ours: `demo-film/storyboard.md` — 8 shots, ~7–9 s each, ~66 s total.

✋ **Hands-on:** generate 4 style frames, lock your style block, write your storyboard in the template above.

---

# Stage 3 — Generate key frames (the image-first workflow)

> **2026's most important rule: never text-to-video a scene directly.** Lock every shot as a still image first, then animate. Typing a full scene into a video model is rolling dice; animating a locked frame with a motion-only prompt is directing.

### Anatomy of a shot prompt

```
[STYLE BLOCK] [SUBJECT + ACTION] [ENVIRONMENT] [LIGHTING] [CAMERA + LENS] [MOOD]
+ a negative prompt
```

**Worked example** — demo shot 1 (EWS):

```
Cinematic 16:9 widescreen film still, moody atmospheric science fiction,
teal-and-amber color grade, volumetric light, heavy atmosphere, subtle film
grain, 35mm anamorphic lens, ultra-detailed, epic composition. Vast flooded
dystopian city at dusk: crumbling skyscrapers half-submerged in black
floodwater, colossal storm clouds and distant lightning. Far away on a rocky
island, a lone lighthouse stands, its warm beam cutting through heavy rain.
Desolate, awe-inspiring sense of scale, no people.

Negative: text, words, watermark, low quality, blurry, cartoon, 3D render
```

### The batch workflow

1. Generate **4 variants** of each shot.
2. Pick the strongest. Judge composition, lighting, and story clarity — not pixels.
3. If none work, change **ONE variable** (lighting? angle? distance?) — not five. You're debugging, not praying.

### Common failures & fixes

| Problem | Fix |
|---|---|
| Wrong aspect ratio | Put "16:9 widescreen" early in the prompt + set the tool's AR control |
| Character drift between shots | Repeat character tokens verbatim; add reference images |
| Garbled text/signs in frame | Negative prompt: "text, words, letters, watermark" — or compose around it |
| Plastic/oversharp look | Add "film grain, imperfect, analog, natural skin texture" |
| Random extra elements | Negative-prompt them; crop in the edit as last resort |

### Stage 3.5 — Going local: ComfyUI (installed in this workspace!)

ComfyUI is checked out at `/home/user/ComfyUI` and fully set up: **ComfyUI-Manager**, the **IPAdapter pack**, and validated Wan workflows for this film. The complete local playbook is `GO-LOCAL.md`. The open-source path: **Wan 2.6 / 2.2** (image-to-video), **HunyuanVideo**, **LTX-2** — all run image-to-video locally.

**Smart order of operations:** do Stages 1–2 in the cloud (fast style exploration), graduate to local when you're hooked and generating daily.

✋ **Hands-on:** generate all 8 key frames for your storyboard. Keep the prompts in `storyboard.md` — you'll need them again in Stage 4. (Ours: `demo-film/frames/`.)

---

# Stage 4 — Animate the shots (image-to-video)

For each locked frame:

1. **Upload the frame as the start frame.** Optionally add a second image as the *end frame* — start/end-frame animation is one of 2026's biggest features (generate "character across the room," and the model animates the journey between the two images). *The demo ships a validated first/last-frame workflow: `models/workflows/wan-firstlast-the-last-lighthouse.json`.*
2. **Motion-only prompt.** The image already contains the look; your prompt describes only movement, in one sentence:

```
Slow cinematic dolly push forward, subtle wind moving the coat, rain falling.
```

3. **Overshoot every shot.** Generate 10 s, use 6 s in the edit. The extra handles save you every time.
4. **3–5 takes per shot.** Keep everything; cut later. Pick the take with the least morphing and flicker.
5. **Camera control.** Use Motion Brush (Runway) or camera presets: dolly, pan, orbit, rack focus. *"Camera moves, subject doesn't"* reads ten times more professional than chaotic motion.

### Known failure modes (and their fixes)

| Failure | Fix |
|---|---|
| Face morphs | Reduce motion intensity; keep the subject slow and central |
| Background flicker | Simplify backgrounds; keep the style block locked |
| Physics glitches | Simplify actions — a hand on a lever, not a sword fight |
| Style drift between shots | Re-upload the locked style frame as reference if the tool allows |

✋ **Hands-on:** animate shots 1–8. Budget: 8 shots × 4 takes × 5 s ≈ 160 s of video ≈ $16–60, or free locally in ComfyUI.

---

# Stage 5 — Voice, sound & music

### Casting a voice

Audition 3–5 voices **reading your actual lines** — never judge a voice on a demo reel. (That's exactly how the demo film's narrator was cast: two candidates read the opening lines, the stronger was chosen, then the full narration was recorded.)

### Directing a TTS voice

- **Punctuation is direction.** Periods = beats. Ellipses = hesitation. Em-dashes = interruption. Line breaks = pauses. *"Then, one morning, a signal blinked on the horizon. A ship that should not exist."* — the period *is* the drama.
- Keep sentences under ~15 words; AI voices handle them best.
- **One voice = one engine = one model = one settings preset** across the whole film.

### Dialogue (only if you must)

Lip-sync costs takes and budget. Covers — the listener's reaction, a hand, a letter, a radio — let characters "speak" without visible mouths. Prefer VO for film #1. If you need sync, budget 3× takes per line.

### Sound design: the 50% of filmmaking nobody sees

Build in three layers:

1. **Ambience bed** — rain, wind, ocean, room tone — one bed under the whole film (this is what makes it feel "real").
2. **Spot SFX** — lamp clank, lever creak, radio static, ship horn — synced to actions.
3. **Music — last, and quieter than you think.**

Music sources: **Suno/Udio** can generate a 60–90 s instrumental — prompt: `haunting slow orchestral, solo cello, distant french horn, waves, no vocals, 65 bpm` — but *verify the license tier for commercial use*. Library tracks (Artlist, Epidemic Sound) are the zero-risk option.

### Procedural sound design (what the demo actually does)

The demo film's **ambience bed AND score are synthesized in code** (`demo-film/audio/make_ambience.py`, `make_music.py`):
- **Ambience:** brown noise low-passed for wind, band-passed noise for sea swell, high-passed hiss for rain (fades out when the storm ends), and an FM-synthesized 110 Hz foghorn at shot 7.
- **Score:** an additive-synthesis pad — A minor drone → Fmaj7 → C, with a soft swell into C major exactly at the reveal — gentle detune "strings," slow attack, low-passed.
- Zero downloads, zero licenses. `build_film.sh` detects `audio/ambience.wav` / `audio/music.wav` and mixes them ~18 dB / ~25 dB under the VO (stereo). A synth bed is a legit pro trick — libraries can't always give you *your* storm.

### Mixing targets

- Voiceover peaks around −6 dB; music ducked 10–15 dB under it.
- Final mix at **−14 LUFS** for YouTube.

✋ **Hands-on:** cast + record your VO (ours: `demo-film/audio/narration.mp3`), build a 3-layer sound bed.

---

# Stage 6 — Edit & assemble (where films are actually made)

Two routes for a first film — both valid:

**Route A — The Storyboard Film** *(what the demo builds — $0, teaches pacing)*
Your key frames + slow Ken Burns moves (zooms/pans) + crossfades + VO. Plays as a stylized "animated graphic novel" film. An excellent first project — and everything you learn transfers.

**Route B — The Motion Film**
Your Stage-4 clips cut together in CapCut/DaVinci.

### Editing rules that hold in both

- **Cut on motion, cut on emotion.** 4–8 s per shot at 60 s runtime. A shot that has delivered its beat is already too long.
- **J-cuts & L-cuts** — the next shot's VO starts *before* the image changes (J), or carries *over* the cut (L). This one trick is 80% of "professional."
- **Crossfades** = time passing. **Hard cuts** = same-time action.
- **Titles:** one font, wide letter-spacing, fade in/out. Restraint reads expensive.
- **One end card:** *"Written, directed & generated by [you]"* — you are the author of this film.

✋ **Hands-on:** assemble your cut. The demo does it with a fully-scripted `ffmpeg` build (`demo-film/build_film.sh`) — every step explained in the build log below. You can re-run it on your own frames.

---

# Stage 7 — Grade, export & ship

- **One grade for the whole film.** Set temperature/tint once, add a touch of contrast, vignette, and film grain. A single unified grade is what makes disparate AI shots feel like one movie. (DaVinci Resolve: free, best-in-class.)
- **Upscale:** Topaz Video AI (Astra) or local ESRGAN in ComfyUI. 1080p → 4K.
- **Export:** H.264/H.265, 4K, **24 fps**, AAC 320 kbps, −14 LUFS. Keep a 16:9 master **and** a 9:16 vertical cut for Shorts (reframe — never re-edit). The demo does both: `build_film.sh` → `film.mp4` (Ken Burns zooms) and `build_vertical.sh` → `film-vertical.mp4` (slow horizontal pans of a 9:16 window — the right reframe move, because the vertical crop discards width).
- **Publish:** `YOUTUBE-KIT.md` has titles, description, tags, captions, thumbnail, and the upload checklist. **Turn on the platform's AI/synthetic-media disclosure** (see below).
- **Share:** r/aivideo, Runway Discord, AI film festivals (e.g., Runway AIFF).

---

## Legal, ethics & disclosure — read once, keep forever

1. **Never** generate a real person's likeness or voice without written consent.
2. **Disclose** AI generation where platforms require it (YouTube's altered/synthetic media label). It's both the rule and the trust-builder.
3. **Music:** verify licenses — library tracks are the safest; Suno/Udio commercial tiers vary. (The demo's beds are code-synthesized: zero license surface.)
4. **Copyright:** your edit, arrangement, and taste are your authored work. Individual AI outputs are generally not independently copyrightable — the assembled film is where your rights live.
5. **Keep records:** prompts, generations, and edit decisions. Festivals and clients ask.

---

## The 30-day roadmap

| Week | Goal | Stages |
|---|---|---|
| **1** | Script + style frames + storyboard locked | 0–2 |
| **2** | Key frames + first animations; ship a 15 s test to friends | 3–4 |
| **3** | Full generation, VO + sound bed, first cut | 4–6 |
| **4** | Grade, export, publish — and start film #2 | 7 |

---

## Appendix — Build log: THE LAST LIGHTHOUSE (the exact build)

Everything below was actually done in this workspace. Reproduce it step by step:

1. **Script** (`demo-film/script.md`) — logline, 103-word narration in three acts, 8-shot list.
2. **Style lock** — the style block above, reused verbatim on all 8 prompts; character tokens reused on shots 2, 5, 8, 9.
3. **Character sheet** — 5 locked views (`demo-film/frames/character-sheet/`), per CHARACTER-CONSISTENCY.md.
4. **Frames** — 8 key frames + poster generated (prompts in `demo-film/storyboard.md`, outputs in `demo-film/frames/`).
5. **Voice** — narrator cast by auditioning two candidates on the opening lines; winner recorded the full narration (`demo-film/audio/narration.mp3`).
6. **Sound design** — procedurally synthesized storm bed + score (`make_ambience.py`, `make_music.py`) mixed ~18 dB / ~25 dB under the VO.
7. **Assembly** (`demo-film/build_film.sh`) — for each frame: cover-crop to 1920×1080 → Ken Burns move (alternating slow push-in/pull-out) → 24 fps. Shots are then crossfaded with a **padded overlay chain**: every shot is padded with transparent frames to the full timeline and alpha-faded in over the accumulated picture — visually identical to an xfade, and it sidesteps a filtergraph-reinit race that can kill the `xfade` filter on multi-input graphs (a real production gotcha — we hit it, diagnosed it, and worked around it). Two-stage assembly: **Stage A** builds the crossfaded 1080p timeline; **Stage B** composites the title/credits clips (pre-rendered RGBA with baked fades), places the VO after a 2.5 s lead-in, loudness-normalizes to −14 LUFS, mixes the bed + score, and fades to the end card.
8. **Reframes & extras** — `build_vertical.sh` → 9:16 Shorts cut (pan-based reframe); `make_thumbnail.py` → 1280×720 thumbnail; `subtitles.srt` for captions.
9. **Export** — `demo-film/film.mp4`, 1080p24, H.264 + stereo AAC.
10. **Upgrade path to a full motion film** — the per-shot motion prompts are already written in `storyboard.md`: upload each frame to Veo/Runway/Kling as the start frame (or run the validated local workflows in `models/workflows/`), generate 4 takes, replace the Ken Burns clips in the edit.

---

## Sources & further reading

- Best AI video generators (July 2026) — https://www.buildmvpfast.com/articles/best-llms-2026-guide/video-generation-ai
- AI video tools compared (July 2026) — https://diyai.io/ai-tools/video-generation/best-ai-video-tools/
- 2026 video model tier list & pricing — https://www.getaiperks.com/en/blogs/44-best-ai-video-generators-2026
- Character consistency for long-form AI video (Mar 2026) — https://www.aimagicx.com/blog/long-form-ai-video-character-consistency-guide-2026
- Cinematic AI short film workflow (Apr 2026) — https://www.futureflowai.in/post/how-to-make-a-cinematic-ai-short-film-in-2026-the-complete-workflow

*Tool versions move fast — this guide's method is stable; check current versions before buying credits.*
