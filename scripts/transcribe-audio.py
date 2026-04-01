#!/usr/bin/env python3
"""
Transcribe a song with precise timestamps using Gemini API.
Returns lyrics, section markers, and musical analysis.

Usage: python3 transcribe-audio.py <audio-file> [--output <json-file>]
"""

import argparse
import json
import os
import sys
import re

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with timestamps via Gemini")
    parser.add_argument("audio_file", help="Path to audio file (MP3, WAV, etc.)")
    parser.add_argument("--output", help="Output JSON file path", default=None)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        print('Add to ~/.claude/settings.json: {"env": {"GEMINI_API_KEY": "your-key"}}', file=sys.stderr)
        sys.exit(1)

    try:
        import google.generativeai as genai
    except ImportError:
        print("Installing google-generativeai...", file=sys.stderr)
        os.system("pip3 install google-generativeai -q")
        import google.generativeai as genai

    genai.configure(api_key=api_key)

    audio_path = os.path.expanduser(args.audio_file)
    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Uploading {os.path.basename(audio_path)}...", file=sys.stderr)
    audio_file = genai.upload_file(audio_path, mime_type="audio/mpeg")

    print("Transcribing with Gemini...", file=sys.stderr)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        [
            audio_file,
            """Transcribe this song with precise timestamps. Return ONLY a JSON object with this exact structure:

{
  "title": "Song Title",
  "duration_seconds": 212,
  "bpm_estimate": 120,
  "sections": [
    {
      "name": "Intro",
      "type": "instrumental",
      "start_time": "0:00",
      "start_seconds": 0,
      "end_time": "0:17",
      "end_seconds": 17,
      "energy": "low",
      "description": "Soft piano and ambient texture",
      "lyrics": []
    },
    {
      "name": "Verse 1",
      "type": "vocal",
      "start_time": "0:17",
      "start_seconds": 17,
      "end_time": "0:34",
      "end_seconds": 34,
      "energy": "medium",
      "description": "Vocals enter with gentle melody",
      "lyrics": [
        {"time": "0:17", "seconds": 17, "text": "First lyric line"},
        {"time": "0:21", "seconds": 21, "text": "Second lyric line"}
      ]
    }
  ]
}

Be precise with timestamps. Include ALL sections (intro, verses, chorus, bridge, breakdown, instrumental breaks, outro). Mark energy as low/medium/high/peak. Return valid JSON only, no markdown."""
        ],
        generation_config=genai.GenerationConfig(temperature=0.1)
    )

    # Extract JSON from response
    text = response.text.strip()
    # Remove markdown code fences if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            data = json.loads(match.group())
        else:
            print("Error: Could not parse Gemini response as JSON", file=sys.stderr)
            print(text, file=sys.stderr)
            sys.exit(1)

    # Output
    output_json = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Transcription saved to {args.output}", file=sys.stderr)

    print(output_json)

    # Print summary to stderr
    print(f"\nSummary:", file=sys.stderr)
    print(f"  Title: {data.get('title', 'Unknown')}", file=sys.stderr)
    print(f"  Duration: {data.get('duration_seconds', '?')}s", file=sys.stderr)
    print(f"  Sections: {len(data.get('sections', []))}", file=sys.stderr)
    for sec in data.get('sections', []):
        n_lyrics = len(sec.get('lyrics', []))
        lyric_note = f" ({n_lyrics} lines)" if n_lyrics else ""
        print(f"    {sec['start_time']}–{sec['end_time']} [{sec['energy']:>6}] {sec['name']}{lyric_note}", file=sys.stderr)

if __name__ == "__main__":
    main()
