#!/bin/bash
# Stitch multiple video files together in order.
# Usage: stitch-videos.sh <input-dir-or-file-list> <output.mp4> [--pattern "glob"]
#
# Modes:
#   stitch-videos.sh ~/Downloads/ output.mp4                    # Auto-detect recent videos
#   stitch-videos.sh ~/Downloads/ output.mp4 --pattern "*.mp4"  # Custom glob
#   stitch-videos.sh file1.mp4 file2.mp4 file3.mp4 output.mp4  # Explicit files

set -euo pipefail

PATTERN=""
FILES=()
OUTPUT=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pattern) PATTERN="$2"; shift 2 ;;
        *)
            if [[ -z "$OUTPUT" ]]; then
                FILES+=("$1")
            fi
            shift
            ;;
    esac
done

# Last argument is output
OUTPUT="${FILES[-1]}"
unset 'FILES[-1]'

# If single directory given, find videos in it
if [[ ${#FILES[@]} -eq 1 ]] && [[ -d "${FILES[0]}" ]]; then
    DIR="${FILES[0]}"
    FILES=()

    if [[ -n "$PATTERN" ]]; then
        while IFS= read -r -d '' f; do
            FILES+=("$f")
        done < <(find "$DIR" -maxdepth 1 -name "$PATTERN" -print0 | sort -z)
    else
        # Auto-detect: find MP4s modified in the last 2 hours, sorted by name
        while IFS= read -r -d '' f; do
            FILES+=("$f")
        done < <(find "$DIR" -maxdepth 1 -name "*.mp4" -mmin -120 -print0 | sort -z)
    fi

    if [[ ${#FILES[@]} -eq 0 ]]; then
        echo "Error: No video files found in $DIR" >&2
        exit 1
    fi
fi

echo "Stitching ${#FILES[@]} videos → $OUTPUT"

# Create concat list
CONCAT_FILE=$(mktemp /tmp/concat_XXXXX.txt)
for f in "${FILES[@]}"; do
    echo "  + $(basename "$f")"
    echo "file '$f'" >> "$CONCAT_FILE"
done

# Check compatibility
FIRST_SPECS=$(ffprobe -v quiet -show_entries stream=codec_name,width,height,r_frame_rate \
    -select_streams v:0 -of csv=p=0 "${FILES[0]}")
echo "  Specs: $FIRST_SPECS"

# Concat
ffmpeg -y -v warning -f concat -safe 0 -i "$CONCAT_FILE" -c copy "$OUTPUT" 2>&1

rm -f "$CONCAT_FILE"

SIZE=$(du -h "$OUTPUT" | cut -f1)
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT")
echo "✓ $OUTPUT ($SIZE, ${DURATION}s)"
