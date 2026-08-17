# 🎭 Character Consistency — The Local Playbook

*(The addendum to GO-LOCAL.md. This is the #1 unsolved-feeling problem in AI filmmaking — here is the complete, honest playbook.)*

---

## Why consistency is hard (and what actually works)

AI image/video models sample a new person from noise every generation. Nothing ties shot 2's face to shot 5's. There is no magic setting — there is a **four-layer stack**, cheapest first, and the lesson of the whole course applies: *the best consistency tool is restraint in what you ask the model to do.*

```
Layer 1  Locked description tokens      (cost: free, power: 40%)
Layer 2  Character sheet                (free, power: +30% → 70%)
Layer 3  IPAdapter for stills / LoRA    (afternoon, power: +20% → 90%)
Layer 4  Start-frame anchoring in video (+10% → ~100%, with discipline)
```

**For a 60-second film: Layers 1+2+4 are enough.** Layer 3 exists for when you need the same face in *many* new poses across a longer film.

---

## Layer 1 — Locked description tokens

Write ONE description of the character. Reuse it **verbatim** in every prompt where they appear. Never re-describe from scratch — every rephrase is a new person.

**THE LAST LIGHTHOUSE keeps (used on shots 2, 5, 8, poster, and the whole sheet):**

```
a weathered woman in her late 40s, silver-streaked dark hair tied back,
deep-set tired eyes, wearing a faded mustard-yellow raincoat over a dark
wool sweater
```

Rules:
- **One distinctive prop** (the mustard-yellow raincoat) does more identity work than any facial detail — silhouettes survive where faces drift.
- **Never change the tokens mid-film.** If shot 3's hair is wrong, fix shot 3 — don't "improve" the description.
- Keep the same **style block** (GUIDE Stage 2) — the same grade and lighting are half of "it's the same movie".

---

## Layer 2 — The character sheet

`demo-film/frames/character-sheet/` — 5 locked views of the keeper, all generated from the exact tokens above:

| File | View | Why it exists |
|---|---|---|
| `front.png` | Front, eyes to camera | Identity reference for IPAdapter / LoRA |
| `threequarter-left.png` | ¾ left | Most used camera angle in the film |
| `threequarter-right.png` | ¾ right | Reverse-angle coverage |
| `profile.png` | Side profile | Silhouette + profile shots |
| `fullbody.png` | Full body | Costume + posture anchor |

**The sheet prompt pattern** (copy for your character):

```
Cinematic character reference sheet, [VIEW] view, head and shoulders portrait:
[YOUR LOCKED TOKENS]. Neutral expression, eyes looking at the camera. Soft key
light, [your film's background] softly out of focus, subtle film grain, 85mm
lens, ultra-detailed natural skin texture, [your style block]. No text.
```

**Where the sheet plugs in:**
- **Cloud tools:** upload the sheet to Kling **Character ID**, Veo **Ingredients**, or Runway reference images — identity locks per shot.
- **Local stills:** the sheet is the reference batch for **IPAdapter** (Layer 3).
- **Local video:** start-frame anchoring (Layer 4) — the sheet is also the source for inpainting fixes.
- **Everywhere:** whenever a generation drifts, re-roll *with the sheet in context* — it's your anchor, not a suggestion.

---

## Layer 3 — IPAdapter for stills (local, one afternoon)

**When you need it:** many shots of the same face in *new* poses/lighting (stills and the key frames that seed your video).

**Install** (ComfyUI-Manager → Install Custom Nodes → search the pack):
- `ComfyUI_IPAdapter_plus` — the IPAdapter + FaceID nodes (installed in this workspace)

**Models** (Manager → Model Manager → search `ipadapter` + `insightface`):
| Model | Goes to |
|---|---|
| `ip-adapter-faceid-plusv2_sd15.bin` (or the SDXL version) | `models/ipadapter/` |
| `ViT-H` CLIP vision (`clip_vision_h` / SD1.5 or SDXL variant) | `models/clip_vision/` |
| `insightface/buffalo_l` face model bundle | `models/insightface/models/buffalo_l/` |
| Your still base model (SD1.5 or SDXL) | `models/checkpoints/` |

**The workflow:** `models/workflows/character-ipadapter.json` — `LoadImage` (your face ref) → `IPAdapterUnifiedLoaderFaceID` → `IPAdapterFaceID` → `KSampler`, with the face tokens in the prompt and the reference image weight ~0.8 (start 0.2, end 1.0). **Validated live in this workspace** against the installed pack — the model weights are the only thing that needs downloading on your machine.

**Workflow (text version, for any tool):**
1. `LoadImage` ← `sheet/front.png` (or your best likeness image)
2. `IPAdapterFaceID` with weight 0.8, start 0.2, end 1.0
3. Text prompt = **your locked tokens** + the new pose/lighting you want
4. Generate 4, keep 1. Repeat per shot — the face stays *her*.

### Layer 3.5 — LoRA training (the nuclear option, only for longer films)
- Collect **15–30 good images** of the character (sheet + best shots).
- Tag them (`kohya_ss` GUI or `ai-toolkit`), train a character LoRA on SD1.5/SDXL/Flux.
- Apply at **0.7–0.9 weight** in every generation.
- Worth it when IPAdapter isn't holding across *extreme* pose/light changes — not needed for a 60-second film.

---

## Layer 4 — Start-frame anchoring (the video discipline)

This is the course's Stage 3/4 rule, weaponized for identity:

1. **Lock every shot as a still first** — the still *is* the identity anchor.
2. **Animate with motion-only prompts** — the model changes motion, not the person.
3. **Mild motion only**: "slow push-in", "she blinks", "rain on the window". Camera moves, subject doesn't. Morphing happens when the model is forced to re-invent a face in motion.
4. **Keep the subject central and slow.** Faces drift most at frame edges and high speeds.
5. **First-frame/last-frame**: lock BOTH ends of a shot (`WanFirstLastFrameToVideo` in ComfyUI, start/end frames in Veo/Runway). The model only invents the journey between two locked identities — this is the strongest consistency trick in 2026.
6. **Per-scene reference:** same locked frame reused as the start frame of every take of that scene.

**Workflows shipped & validated in this course (drag into ComfyUI):**

| Workflow file | What it does |
|---|---|
| `models/workflows/wan-i2v-the-last-lighthouse.json` | Wan 2.6 image→video (Layer 4, standard) |
| `models/workflows/wan-firstlast-the-last-lighthouse.json` | Wan 2.6 **start + end frame** → video (Layer 4, strongest) |
| `models/workflows/wan22-i2v-the-last-lighthouse.json` | Wan **2.2** image→video (raw node graph, validated) |
| `models/workflows/wan22-official-i2v-the-last-lighthouse.json` | Wan 2.2 **official** dual-unet template, pre-loaded with shot 01 + the motion prompt |
| `models/workflows/character-ipadapter.json` | Layer 3 stills — **validated against the live server** with the IPAdapter pack installed ✅ |

> All generator-built workflows were validated against the live ComfyUI
> server in this workspace (graph types check clean). Only the model *weights*
> can't be downloaded here — on your GPU machine, drop the files in and press Queue.

---

## The fix-it loop (when a shot still drifts)

| Problem | Fix |
|---|---|
| Face off in ONE shot | Re-roll that shot with the sheet as IPAdapter reference (or re-animate with the locked frame) |
| Face off in EVERY shot | Your tokens drifted — diff your prompts against the locked tokens; restore verbatim |
| Hair/coat color flickers | Give the character one strong color prop and always name it |
| Mid-shot morphing | Lower CFG, shorten the clip, slow the motion prompt |
| Can't hold it at all | Cut around it — film grammar is your friend: hands, silhouettes, back-of-head, wide shots. The audience's imagination is the best consistency tool ever invented |

## Consistency through the edit

The last 10% of "same person" is the grade: one temperature/tint across the whole film, one grain layer, matched shadows. The demo does this in `build_film.sh` (single encode pipeline, unified fade/grade). A unified grade makes even *different* generations feel like one world — and it's free.

---

## ✅ Checklist (your film)

- [ ] One locked character description, reused verbatim (Layer 1)
- [ ] Character sheet: 5 views generated from those tokens (Layer 2)
- [ ] Every shot locked as a still BEFORE any video (Layer 4)
- [ ] Motion-only prompts, camera moves + slow subject (Layer 4)
- [ ] First/last-frame animation for the hardest shots (Layer 4)
- [ ] IPAdapter (and a LoRA only if needed) for longer films (Layer 3)
- [ ] One unified grade + grain in the edit
