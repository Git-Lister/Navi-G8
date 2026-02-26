#!/bin/bash
# update-context.sh – Suggest updates to CONTEXT.md based on recent git commits

echo "=== Recent commits ==="
git log --oneline -5

echo ""
echo "=== Current CONTEXT.md ==="
head -20 CONTEXT.md
echo "..."

echo ""
echo "Consider updating CONTEXT.md with:"
echo "- New features or changes implemented"
echo "- Current focus (active branch)"
echo "- Next steps / open questions"
echo ""
echo "You can ask an LLM to draft updates by feeding it the git log and the current CONTEXT.md."
