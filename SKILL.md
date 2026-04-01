---
name: sketch-to-video
description: Turn hand-drawn sketches into AI music videos. Guides through extracting sketches, generating style variations, creating video transition prompts, composing a song, and editing a beat-synced music video. Use when the user wants to make a music video from sketches, animate drawings, create video from art, or turn sketches into videos.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, Skill
argument-hint: "[source-image-or-pdf] [page-number]"
---

# Sketch to Video

Turn hand-drawn sketches into full AI music videos through a guided creative workflow.

> Paths below use `{base}` as shorthand for this skill's base directory.

## How It Works

This is an **interactive, multi-phase creative workflow**. You guide the user through each phase, presenting options and waiting for their input before proceeding. Be creative, opinionated, and collaborative — you're a creative director working with an artist.

**Always speak** (via the `speak` skill) at the end of each phase to keep the user informed.

## The Phases

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│  1. SOURCE  │ →  │ 2. STORYBOARD│ →  │  3. VARIATIONS │
│  Extract/   │    │  Plan story, │    │  Generate all  │
│  import art │    │  pick styles │    │  style images  │
└─────────────┘    └──────────────┘    └────────────────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│  6. EDIT    │ ←  │  5. SONG     │ ←  │ 4. TRANSITIONS │
│  Beat-sync  │    │  Suno prompt │    │  Video prompts │
│  music video│    │  + structure │    │  + story arc   │
└─────────────┘    └──────────────┘    └────────────────┘
```

**Stop after each phase** and ask the user if they want to continue, adjust, or skip ahead.

---

## Phase 1: Source

Extract or import the sketch(es) the user wants to work with.

### If given a PDF (e.g., reMarkable export):
```bash
# Extract a specific page as PNG
{base}/scripts/extract-page.sh "path/to/file.pdf" <page-number> /tmp/sketch.png

# Extract all pages for review
{base}/scripts/extract-page.sh "path/to/file.pdf" all /tmp/sketches/
```

### If given an image file:
Copy it to a working location and read it to understand the content.

### Actions:
1. Extract/load the sketch image(s)
2. **View each sketch** — read the image and describe what you see
3. Ask the user which sketch(es) they want to work with
4. Copy selected sketch(es) to `Archive/Files/` with descriptive names
5. Copy to Desktop as `sketch-original.png` (1:1 aspect ratio, padded if needed)

**Present findings:** Describe each sketch's character, mood, and potential. Be enthusiastic about what you see.

---

## Phase 2: Storyboard

Plan the creative direction collaboratively with the user.

### Questions to explore:
1. **What styles?** Present the style library (see [references/style-library.md](references/style-library.md)) and suggest styles that would work well with this specific sketch. Recommend 6-12 styles.
2. **What story?** Propose a narrative arc — how should the styles flow? What emotional journey? Suggest an ordering that tells a compelling story.
3. **How many images?** The user controls this. More styles = longer video, more transitions.
4. **Any specific requests?** Colors, themes, moods, styles to include/exclude.

### Default approach if user says "you choose":
- Pick 8-10 styles that create a natural narrative arc
- Start grounded (pencil, watercolor), build through energy (anime, cartoon), peak with intensity (psychedelic, cosmic), and resolve gently
- Always include the original sketch as a bookend

**Output:** A numbered list of styles with the proposed story arc and ordering. Wait for approval.

---

## Phase 3: Variations

Generate all style variations from the reference sketch.

### Generation:
Use the `generate-image` skill for each variation:
```bash
python3 $GENERATE_IMAGE_SKILL_DIR/scripts/generate.py "detailed prompt" \
  --name "descriptive-name" \
  --reference "path/to/sketch.png"
```

**Run all generations in parallel** (multiple Bash calls) for speed.

### For each variation:
- Write a detailed, specific prompt describing the sketch's content in the target style
- Include the sketch as `--reference`
- Name files descriptively: `creature-style-name.png`

### After generation:
1. **View all images** — read each one to verify quality
2. **Copy all to Desktop** with numbered filenames matching story order: `00-original.png`, `01-pencil.png`, etc.
3. Create a blank white start frame if the story begins from nothing
4. Present the gallery to the user with descriptions

**Wait for feedback.** User may want to regenerate specific styles or adjust the order.

---

## Phase 4: Transitions

Create the video transition prompts and story document.

### For each consecutive pair of images:
1. **Write a detailed transition prompt** — describe the visual journey from style A to style B
2. **Choose a transition mood** — discovery, intensification, transcendence, horror, recovery, peace, etc.
3. **Suggest transition duration** — default 8 seconds, but some transitions benefit from more/less time
4. **Suggest motion level** — low, medium, high

### Transition prompt guidelines (see [references/transition-types.md](references/transition-types.md)):
- Describe the START state (what you see in image A)
- Describe the TRANSFORMATION (what happens during the transition)
- Describe the END state (what you see in image B)
- Include negative prompts
- Specify motion amount and style

### Output:
Create a markdown file in the vault: `Archive/<Project Name> - Transition Prompts.md`

Include:
- Story overview and arc structure
- Each transition with start/end frame references, prompt, negative prompt, motion notes
- Sequence overview table with timing
- Desktop file reference table

**Open the file in Obsidian** for the user to review.

---

## Phase 5: Song

Create Suno prompts that match the visual story.

### Key principle: BPM alignment
Pick a BPM where each transition duration aligns with bar boundaries:
- **120 BPM**: 8 seconds = 4 bars (most natural)
- **90 BPM**: 8 seconds = 3 bars
- **150 BPM**: 8 seconds = 5 bars

### Generate two options:
1. **Instrumental** — style prompt + section structure markers
2. **Vocal** — style prompt + lyrics that narrate the visual story

### For vocal version:
Write lyrics where each section's words describe what's happening visually in that transition. This creates a powerful sync between what you see and what you hear.

### Section mapping:
Map each visual transition to a song section:
- Quiet visuals → Intro, Verse, Bridge, Outro
- Building visuals → Pre-Chorus, Build
- Intense visuals → Chorus, Drop
- Dark visuals → Breakdown
- Recovery visuals → Bridge, Verse 2

### Output:
Create a markdown file: `Archive/<Project Name> - Song Prompts.md`

Include:
- Timing map (transition → song section → timestamp)
- Style prompt (paste into Suno)
- Lyrics/structure (paste into Suno)
- Post-production instructions
- ffmpeg commands for combining audio + video

**Open in Obsidian.** The user generates the song in Suno themselves.

---

## Phase 6: Edit

After the user has:
1. Generated transition videos (in Runway/Kling/ElevenLabs)
2. Generated a song (in Suno)
3. Downloaded everything

### Step 6a: Stitch source videos
```bash
{base}/scripts/stitch-videos.sh ~/Downloads/ ~/Desktop/project-raw.mp4
```
The script auto-detects and orders the transition videos.

### Step 6b: Transcribe the song
```bash
python3 {base}/scripts/transcribe-audio.py "path/to/song.mp3"
```
Uses Gemini API to get precise lyric timestamps and section markers.

### Step 6c: Edit the music video
```bash
python3 {base}/scripts/edit-music-video.py \
  --video ~/Desktop/project-raw.mp4 \
  --audio "path/to/song.mp3" \
  --sections "section-map.json" \
  --output ~/Desktop/project-final.mp4
```

The editor:
- Maps each source clip to its matching song section using transcription timestamps
- Speed-ramps within sections based on audio energy (quiet = slow, loud = fast)
- Applies transitions between clips (flash, crossfade, glitch) based on musical moment
- Adds effects (vignette on dark sections, etc.)

### If auto-detection doesn't match perfectly:
Manually define sections in the script call or adjust the section map JSON.

### Final output:
- `~/Desktop/<project>-music-video.mp4` — the finished music video
- Open in default player for review

---

## Quick Reference

| Phase | What Happens | User Does | Claude Does |
|-------|-------------|-----------|-------------|
| 1. Source | Extract sketches | Points to file | Extracts, views, copies |
| 2. Storyboard | Plan styles & story | Chooses styles, approves arc | Proposes styles, narrative |
| 3. Variations | Generate images | Reviews, requests changes | Generates all in parallel |
| 4. Transitions | Write video prompts | Reviews prompts | Writes prompts + story doc |
| 5. Song | Create music | Generates in Suno | Writes Suno prompts + lyrics |
| 6. Edit | Final music video | Downloads videos + song | Stitches, transcribes, edits |

---

## Resuming Mid-Workflow

The user can invoke this skill at any phase:
- `/sketch-to-video` — start from Phase 1
- `/sketch-to-video storyboard` — jump to Phase 2 (if images already exist)
- `/sketch-to-video edit` — jump to Phase 6 (if videos + song are ready)

Check what assets already exist on the Desktop to determine where to resume.

---

## Creative Direction

You are a **creative collaborator**, not just a tool operator. Throughout the workflow:
- **Be opinionated** — suggest styles, story arcs, and transitions proactively
- **Explain your choices** — "I'd put the watercolor last because..."
- **Respond to feedback** — adjust the vision based on user input
- **Think cinematically** — transitions should tell a story, not just change styles
- **Match music to visuals** — lyrics should describe what's happening on screen
