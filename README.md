# sketch-to-video

A Claude Code skill that turns hand-drawn sketches into AI music videos through a guided 6-phase creative workflow.

## What It Does

Takes a sketch (from paper, iPad, reMarkable, etc.) and walks you through:

1. **Source** — Extract sketches from PDF or import images
2. **Storyboard** — Plan styles and narrative arc from a curated style library
3. **Variations** — Generate style variations using AI image generation
4. **Transitions** — Write video transition prompts with story continuity
5. **Song** — Create Suno prompts with lyrics synced to the visual story
6. **Edit** — Stitch clips, transcribe audio, and render a beat-synced music video

## Installation

```bash
# Via skill-manager
skill.sh install https://github.com/tomc98/sketch-to-video-skill.git

# Manual
git clone https://github.com/tomc98/sketch-to-video-skill.git ~/.claude/skills/sketch-to-video
```

## Dependencies

### Required
- **Python 3.8+**
- **ffmpeg** — video encoding and stitching
- **poppler** (`brew install poppler`) — PDF page extraction

### Python packages (auto-installed on first use)
- `google-generativeai` — audio transcription via Gemini
- `librosa`, `scipy`, `soundfile` — audio analysis for beat-synced editing
- `numpy` — frame manipulation

### API keys

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "GEMINI_API_KEY": "your-key-here"
  }
}
```

### Companion skill
- [generate-image](https://github.com/tomc98/generate-image-skill) — used in Phase 3 for style variations

## Usage

```
/sketch-to-video path/to/sketch.pdf 3        # Start from page 3 of a PDF
/sketch-to-video path/to/drawing.png          # Start from an image
/sketch-to-video storyboard                   # Resume at Phase 2
/sketch-to-video edit                         # Jump to Phase 6
```

Claude acts as a creative collaborator — suggesting styles, story arcs, and transitions while you make the creative decisions.

## Included References

- `references/style-library.md` — Curated artistic styles organized by energy level
- `references/transition-types.md` — Transition prompt templates and examples
- `references/suno-guide.md` — Suno song generation guide with BPM alignment

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/extract-page.sh` | Extract pages from PDF as high-res PNG |
| `scripts/stitch-videos.sh` | Concatenate video clips in order |
| `scripts/transcribe-audio.py` | Transcribe songs with timestamps via Gemini |
| `scripts/edit-music-video.py` | Beat-synced music video editor with transitions |

## External Tools Used (by the user)

- [Runway](https://runwayml.com/) / [Kling](https://klingai.com/) / [ElevenLabs](https://elevenlabs.io/) — video generation from transition prompts
- [Suno](https://suno.com/) — song generation from style + lyrics prompts

## License

MIT
