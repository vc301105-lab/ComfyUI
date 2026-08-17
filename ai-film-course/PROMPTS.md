# 🧰 The AI Filmmaker's Prompt Library

Copy-paste templates. Every prompt follows the master anatomy:

```
[STYLE BLOCK] [SUBJECT + ACTION] [ENVIRONMENT] [LIGHTING] [CAMERA + LENS] [MOOD]
+ NEGATIVE PROMPT
```

---

## 1. Style blocks (lock ONE for your whole film)

**Sci-fi noir / atmospheric** *(used by the demo film)*
```
Cinematic 16:9 widescreen film still, moody atmospheric science fiction,
teal-and-amber color grade, volumetric light, heavy atmosphere, subtle film
grain, 35mm anamorphic lens, ultra-detailed, epic composition.
```

**Documentary realism**
```
Cinematic 16:9 widescreen frame, vérité documentary style, natural available
light, shallow depth of field, handheld feel, muted natural color grade,
35mm film, Kodak Portra tones, authentic, imperfect, candid.
```

**Cozy animation (Pixar-adjacent)**
```
Cinematic 16:9 frame, warm stylized 3D animation, soft global illumination,
rounded character design, saturated warm color palette, bokeh, shallow depth
of field, storybook charm, ultra-detailed render.
```

**Fantasy epic**
```
Cinematic 16:9 frame, epic high fantasy, golden-hour light, dramatic god rays,
atmospheric haze, painterly realism, rich jewel tones, 65mm IMAX framing,
majestic scale, ultra-detailed.
```

**Cyberpunk noir**
```
Cinematic 16:9 frame, rain-soaked neon cyberpunk, magenta-and-cyan palette,
wet reflective streets, holographic signage, volumetric neon fog, anamorphic
lens flare, 35mm, film grain, gritty, ultra-detailed.
```

**B&W film noir**
```
Cinematic 16:9 frame, classic 1940s film noir, high-contrast black and white,
hard venetian-blind shadows, cigarette smoke haze, 50mm lens, Tri-X 400 grain,
expressionist lighting, moody, timeless.
```

**Painterly / Ghibli-adjacent**
```
Cinematic 16:9 frame, hand-painted 2D animation, soft watercolor backgrounds,
expressive painterly clouds, gentle natural color palette, warm sunlight,
detailed linework, whimsical, serene.
```

**Retro 1980s**
```
Cinematic 16:9 frame, retro 1980s aesthetic, warm sunset haze, analog VHS
texture, halation, chromatic glow, nostalgic color grade, 35mm, sun-drenched,
dreamy.
```

**Nature documentary**
```
Cinematic 16:9 frame, blue-chip nature documentary, telephoto compression,
golden-hour rim light, mist, muted earth-tone grade, razor-sharp subject,
shallow depth of field, majestic.
```

**Elevated horror**
```
Cinematic 16:9 frame, slow-burn psychological horror, single-source practical
light, deep shadow falloff, desaturated cold palette, film grain, 35mm,
dreadful stillness, understated, realistic.
```

---

## 2. Shot-type fill-ins (plug into any style block)

```
[ESTABLISHING]  Vast [place] at [time of day], colossal [weather], a lone
                [subject] in the far distance, awe-inspiring sense of scale.

[WIDE]          [Character] stands small in the frame, surrounded by [world],
                [weather] sweeping past, context and isolation.

[MEDIUM]        [Character] from the waist up, [doing one simple action],
                [light source] shaping their face, environment softly out of focus.

[CLOSE-UP]      Close-up of [character]'s face, [emotion], lit by [light],
                shallow depth of field, intimate, [one reflective detail].

[EXTREME CU]    Extreme close-up of [hands/object/eyes], tactile detail,
                [light] rimming the edges, dust motes in the air, macro feel.

[INSERT]        A still-life insert: [object] on [surface], [one telling
                detail], [light], moody cinematic tabletop.

[FINAL SHOT]    [Character] at [time of day], [resolution action], [weather
                clearing / light breaking through], hopeful, earned.
```

---

## 3. Camera & lens vocabulary

```
Camera:  static tripod · slow dolly push · crane up · aerial drone · handheld
         drift · orbit · whip pan · rack focus · parallax tracking
Lens:    35mm anamorphic · 50mm · 85mm portrait · 24mm wide · 100mm macro ·
         telephoto compression · tilt-shift · split diopter
Depth:   shallow depth of field · deep focus · soft bokeh background
```

---

## 4. Lighting vocabulary

```
golden hour · blue hour · overcast diffused · hard noon sun · single-source
practical · candlelight · neon wash · moonlight · firelight flicker ·
volumetric god rays · rim light · silhouette · dappled shade · lightning flash
```

---

## 5. Negative-prompt bank (pick the ones that matter to you)

```
text, words, letters, watermark, logo, signature, low quality, blurry, jpeg
artifacts, extra fingers, deformed hands, deformed face, bad anatomy,
cartoon, 3D render, oversaturated, plastic skin, doll-like, duplicate
subject, cropped head, out of frame, watermark text
```

---

## 6. Motion-only prompts (Stage 4 — the video stage)

The image already has the look. Describe ONLY the movement, one sentence:

```
Slow cinematic dolly push forward, subtle wind moving the coat, rain falling.
Static camera, only the lamp beam slowly rotating, dust drifting in the light.
Gentle handheld drift, waves rolling, mist curling over the water.
Slow crane up revealing the ship on the horizon.
Rack focus from the window rain to her face.
Orbiting camera around the subject, embers rising.
Slow zoom into the hands, the lever creaking down.
Timelapse of storm clouds parting at dawn.
```

---

## 7. Voice direction cheat sheet (TTS)

```
. period       = hard beat (the drama lives here)
... ellipsis   = hesitation, trailing thought
— em-dash      = interruption or punch
line break    = longer pause
CAPS          = emphasis (use sparingly)
Keep sentences under ~15 words. Audition on YOUR lines, not demos.
```

---

## 8. Music prompts (Suno/Udio — check license tiers for commercial use)

```
"Haunting slow orchestral, solo cello, distant french horn, ocean waves,
no vocals, 65 bpm, building to a quiet hopeful resolve."

"Melancholic solo piano, felt-damped, rain ambience, sparse, 60 bpm,
no vocals, 90 seconds."

"Minimal ambient electronic, warm analog pad, soft pulse, cinematic
slow burn, no vocals, 70 bpm."
```

*(Or synthesize your own — the demo's score is ~90 lines of additive
synthesis in `demo-film/audio/make_music.py`.)*

---

## 9. LLM script prompts

**Narrator persona builder:**
```
Create a 2-line voice persona for my film's narrator: who are they, what
happened to them, why are they telling this story now? Keep it specific and
emotional. My film: [logline].
```

**Scene critiquer:**
```
You are a harsh but fair festival screener. Critique my 60-second AI film:
[script + shot list]. Where does attention drop? Which shot is redundant?
Which line is dead weight? Give 5 specific fixes.
```

---

## 10. Titles & credits (keep it simple)

- One font, bold, wide letter-spacing (e.g., 20–40% tracking).
- Title over the opening shot, fades in 1 s, holds, fades out.
- End card: `WRITTEN, DIRECTED & GENERATED BY [YOUR NAME]` — centered, small, 3 s.
