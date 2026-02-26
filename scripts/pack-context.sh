#!/bin/bash
# pack-context.sh – Generate a context bundle for LLMs

OUTPUT="context-bundle.txt"
echo "# Navi-G8 Context Bundle – $(date)" > "$OUTPUT"
echo "" >> "$OUTPUT"

FILES=(
    "CONTEXT.md"
    "DESIGN.md"
    "DECISIONS.md"
    "ROADMAP.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "
# $file
" >> "$OUTPUT"
        cat "$file" >> "$OUTPUT"
    else
        echo "Warning: $file not found"
    fi
done

# Optionally add key source files (uncomment and adjust paths)
# echo -e "
# backend/app/main.py
" >> "$OUTPUT"
# cat backend/app/main.py >> "$OUTPUT"

echo "Bundle created: $OUTPUT"
