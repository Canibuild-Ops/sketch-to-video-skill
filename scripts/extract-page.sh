#!/bin/bash
# Extract page(s) from a PDF as high-res PNG
# Usage: extract-page.sh <pdf-path> <page|all> <output-path>

set -euo pipefail

PDF_PATH="$1"
PAGE="${2:-1}"
OUTPUT="$3"

if ! command -v pdftoppm &>/dev/null; then
    echo "Installing poppler for PDF rendering..." >&2
    brew install poppler 2>/dev/null || { echo "Error: Install poppler (brew install poppler)"; exit 1; }
fi

if [ "$PAGE" = "all" ]; then
    mkdir -p "$OUTPUT"
    TOTAL=$(pdfinfo "$PDF_PATH" 2>/dev/null | grep "Pages:" | awk '{print $2}')
    echo "Extracting $TOTAL pages from: $PDF_PATH"
    for i in $(seq 1 "$TOTAL"); do
        OUT_FILE="$OUTPUT/page-${i}.png"
        pdftoppm -png -f "$i" -l "$i" -r 300 "$PDF_PATH" "$OUTPUT/page" 2>/dev/null
        # pdftoppm adds -N suffix, rename
        ACTUAL=$(ls "$OUTPUT"/page-*.png 2>/dev/null | sort -V | tail -1)
        if [ -n "$ACTUAL" ] && [ "$ACTUAL" != "$OUT_FILE" ]; then
            mv "$ACTUAL" "$OUT_FILE"
        fi
        echo "  Page $i → $OUT_FILE"
    done
else
    pdftoppm -png -f "$PAGE" -l "$PAGE" -r 300 "$PDF_PATH" "${OUTPUT%.png}"
    # Find the actual output file (pdftoppm appends -N)
    ACTUAL=$(ls "${OUTPUT%.png}"-*.png 2>/dev/null | head -1)
    if [ -n "$ACTUAL" ] && [ "$ACTUAL" != "$OUTPUT" ]; then
        mv "$ACTUAL" "$OUTPUT"
    fi
    echo "Extracted page $PAGE → $OUTPUT"
fi
