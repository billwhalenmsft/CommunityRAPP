#!/usr/bin/env -S bash -l
# End-to-end build: generate diagrams + build slides + validate
#
# Usage:
#   bash -l skills/microsoft-presentation/scripts/build_and_validate.sh <slide-folder>
#
# Example:
#   bash -l skills/microsoft-presentation/scripts/build_and_validate.sh slide-diagram

set -euo pipefail

SLIDE_FOLDER="${1:?Usage: $0 <slide-folder>}"
MD_FILE="${SLIDE_FOLDER}/slides.md"
HTML_FILE="${SLIDE_FOLDER}/slides.html"

echo "━━━ Step 1: Generate all diagrams ━━━"
for f in diagrams/*.py; do
    echo "  → python3 $f"
    python3 "$f"
done
echo ""

echo "━━━ Step 2: Build deck (HTML + PPTX) ━━━"
npm run generate -- "$MD_FILE"
echo ""

echo "━━━ Step 3: Validate rendered slides ━━━"
node scripts/validate_slides.mjs "$HTML_FILE"
echo ""

echo "━━━ Done ━━━"
