# Suno Song Generation Guide

## Quick Start

1. Go to [suno.com](https://suno.com) → Create → Custom Mode
2. Toggle **Custom** ON
3. Paste **Style Prompt** into Style field
4. Paste **Lyrics** into Lyrics field (or toggle Instrumental)
5. Select **V5.5** model
6. Generate 3-5 variations, pick the best one

---

## BPM Alignment (Critical for Video Sync)

Pick a BPM where transition duration aligns with bar boundaries:

| BPM | 8 sec = | 6 sec = | 10 sec = |
|-----|---------|---------|----------|
| **120** | **4 bars** ✓ | 3 bars | 5 bars |
| **90** | 3 bars | 2.25 bars | 3.75 bars |
| **150** | 5 bars | 3.75 bars | 6.25 bars |
| **100** | 3.33 bars | 2.5 bars | 4.17 bars |

**120 BPM is the sweet spot** for 8-second transitions.

---

## Style Prompt Format

V5.5 supports up to 1000 characters. Structure:

```
[primary genre], [tempo] bpm, [instrumentation], [vocal style OR "instrumental only, no vocals"], 
[mood/atmosphere], [production quality], [specific textures/effects]
```

**Order matters** — Suno weights the beginning most heavily.

### Example Style Prompts by Mood:

**Dreamy/Ethereal:**
```
cinematic dream pop, 120 bpm, lush reverbed synth pads, gentle piano, 
soft ethereal female vocals, atmospheric and spacious, modern clean mix, 
building from minimal to layered, shimmering textures
```

**Dark/Intense:**
```
dark cinematic electronic, 120 bpm, heavy sub bass, distorted synths, 
industrial percussion, aggressive and brooding, tense atmosphere, 
no vocals, glitchy textures, building dread
```

**Psychedelic:**
```
psychedelic progressive electronic, 120 bpm, swirling synth arpeggios, 
deep modular textures, tribal percussion, hypnotic and transcendent, 
wide stereo field, evolving soundscapes, no vocals
```

---

## Section Tags (Lyrics Field)

Place on their own line before lyrics:

| Tag | Effect | Energy |
|-----|--------|--------|
| `[Intro]` | Sparse, establishing | Low |
| `[Instrumental Intro]` | No vocals, ambient | Low |
| `[Verse 1]`, `[Verse 2]` | Melodic, narrative | Medium |
| `[Pre-Chorus]` | Building tension | Medium-High |
| `[Chorus]` | Peak melody, hook | High |
| `[Post-Chorus]` | Sustained energy | High |
| `[Bridge]` | Contrasting section | Medium |
| `[Breakdown]` | Stripped back, tension | Low-Medium |
| `[Build]` | Rising energy | Medium→High |
| `[Drop]` | Maximum energy | Peak |
| `[Instrumental Break]` | No vocals, musical | Varies |
| `[Guitar Solo]` | Instrumental feature | High |
| `[Outro]` | Winding down | Low |
| `[Fade Out]` | Gradual volume reduction | → Silent |
| `[End]` | Hard stop | — |

### Production hints in parentheses:
```
[Intro]
(soft piano, ambient texture)

[Verse 1]
Lyrics here...
```

Parenthetical notes are **not sung** — they guide the AI's instrumentation.

---

## Mapping Visuals to Song Sections

| Visual Mood | Song Section | Why |
|-------------|-------------|-----|
| Genesis/Creation | `[Intro]` | Establishing, sparse |
| Refinement | `[Verse 1]` | Building, narrative |
| Coming alive | `[Verse 1 cont.]` | Growing energy |
| Discovery | `[Pre-Chorus]` | Anticipation builds |
| Color explosion | `[Chorus]` | Peak energy, hook |
| Transcendence | `[Post-Chorus]` or `[Build]` | Sustained peak |
| Horror/Darkness | `[Breakdown]` | Dark, stripped |
| Glitch/Reboot | `[Drop]` | Dramatic shift |
| Recovery | `[Bridge]` | New perspective |
| Peace/Ending | `[Outro]` + `[Fade Out]` | Resolution |

---

## Writing Lyrics That Match Visuals

The most powerful technique: **write lyrics that describe what's happening on screen**.

When the viewer sees anime eyes opening, they hear *"Eyes open wide, nothing feels the same"*.  
When mushrooms appear, they hear *"Follow the mycelium down"*.  
When horror strikes, they hear *"Something cracked behind the light"*.

This creates an almost subliminal sync between sound and image.

### Lyric writing tips:
- Short lines (5-8 words) — fits musical phrasing
- Sensory language — colors, textures, movement
- Active verbs — "bleeds", "melts", "cracks", "drifts"
- Each section's lyrics describe that section's visual transition

---

## Post-Production

### Trim to exact length:
```bash
ffmpeg -i song.mp3 -t 80 -c copy song-trimmed.mp3
```

### Combine with video:
```bash
ffmpeg -i video.mp4 -i song.mp3 \
  -c:v copy -c:a aac -b:a 192k -shortest \
  output.mp4
```

### Adjust audio offset:
```bash
ffmpeg -i video.mp4 -itsoffset 0.5 -i song.mp3 \
  -c:v copy -c:a aac -b:a 192k -shortest \
  output.mp4
```

### Extract stems (if needed):
Use Suno's built-in stem separator (Pro/Premier) or:
```bash
# Using demucs (open source)
pip install demucs
demucs song.mp3
```
