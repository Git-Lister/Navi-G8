#!/bin/bash
OUTPUT="context-bundle.txt"
echo "# Navi-G8 Context Bundle – $(date)" > "$OUTPUT"
echo "" >> "$OUTPUT"

FILES=("CONTEXT.md" "DESIGN.md" "DECISIONS.md" "ROADMAP.md")

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "" >> "$OUTPUT"
        echo "# $file" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        cat "$file" >> "$OUTPUT"
    else
        echo "Warning: $file not found"
    fi
done

echo "Bundle created: $OUTPUT"