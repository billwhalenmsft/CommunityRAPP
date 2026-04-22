#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# generate.sh — Build this presentation (fully self-contained)
#
# Usage:
#   bash generate.sh             # HTML + PPTX
#   bash generate.sh --pdf       # HTML + PPTX + PDF
#
# Run from THIS folder — all paths are local.
# ─────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WANT_PDF=false
for arg in "$@"; do
  case "$arg" in --pdf) WANT_PDF=true ;; esac
done

THEME="./microsoft-internal.css"

if [ ! -f "$THEME" ]; then
  echo "ERROR: Theme CSS not found at $THEME"
  echo "Copy it: cp ../theme/microsoft-internal.css ."
  exit 1
fi

echo "━━━ Building: slides.md ━━━"
npx marp slides.md -o slides.html --theme-set "$THEME" --html
echo "  ✅ slides.html"

npx marp slides.md -o slides.pptx --pptx --theme-set "$THEME" --html --allow-local-files
echo "  ✅ slides.pptx"

if $WANT_PDF; then
  npx marp slides.md -o slides.pdf --pdf --theme-set "$THEME" --html --allow-local-files
  echo "  ✅ slides.pdf"
fi

echo "━━━ Done ━━━"
