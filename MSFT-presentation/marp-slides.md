# Marp Slide Authoring Guide

## Overview

Presentations are authored in Marp Markdown and rendered to HTML, PPTX, and PDF using the `microsoft-internal` theme, which implements the Microsoft CES-FY26 Visual Identity Guidelines.

> **CRITICAL RULE:** Every deck folder must be **fully self-contained**.
> Copy `microsoft-internal.css` INTO the deck folder. **Never link to `../theme/` or any path outside the deck.**
> The CSS file contains embedded base64 logos — no other assets are needed.

## Prerequisites

| Requirement | Minimum Version | Install |
|------------|----------------|----------|
| **VS Code extension** | latest | Install `marp-team.marp-vscode` from Extensions panel |
| `@marp-team/marp-cli` | `4.2.3` | `npm install` (from skill folder) |
| `playwright` | `1.58.2` | `npm install` + `npx playwright install chromium` |
| `Node.js` | `24.14.0` | Pre-installed in devcontainer |

## Creating a New Deck

### 1. Create a folder and copy the theme locally

```bash
mkdir -p my-deck
cp theme/microsoft-internal.css my-deck/
```

> This is **mandatory**. The theme CSS is the only file needed — it has logos embedded as base64.

### 2. Add a Marp config file

Create `my-deck/.marp.json` — **pointing to the LOCAL theme copy**:

```json
{
  "theme": "./microsoft-internal.css",
  "html": true,
  "allowLocalFiles": true
}
```

### 3. Create the slides

Create `my-deck/slides.md`:

```markdown
---
marp: true
theme: microsoft-internal
paginate: true
footer: 'Microsoft Confidential'
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Your Title

Subtitle or Speaker Name

---

## Agenda

- Topic one
- Topic two
- Topic three

---

<!-- _class: divider -->

## Section One

---

## Content Slide

Regular body text with **accent highlights** and [links](#).

> Blockquote for callouts

---

<!-- _class: light -->

## Data Slide

| Column A | Column B |
|----------|----------|
| Value 1  | Value 2  |

---

<!-- _class: title -->
<!-- _paginate: skip -->

# Thank You
```

### 4. Create the build script

Create `my-deck/generate.sh` so the deck is self-contained and easy to build:

```bash
#!/usr/bin/env bash
# Build this presentation (run from repo root or from this folder)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WANT_PDF=false
for arg in "$@"; do
  case "$arg" in --pdf) WANT_PDF=true ;; esac
done

THEME="./microsoft-internal.css"

echo "━━━ Building: slides.md ━━━"
npx marp slides.md -o slides.html --theme-set "$THEME" --html
npx marp slides.md -o slides.pptx --pptx --theme-set "$THEME" --html --allow-local-files

if $WANT_PDF; then
  npx marp slides.md -o slides.pdf --pdf --theme-set "$THEME" --html --allow-local-files
fi

echo "━━━ Done ━━━"
```

Make it executable: `chmod +x my-deck/generate.sh`

### 5. Build the deck

```bash
# Quick build (HTML + PPTX)
bash my-deck/generate.sh

# With PDF
bash my-deck/generate.sh --pdf

# Full pipeline: diagrams + build + validate
bash my-deck/generate.sh --all
```

Or using npm directly:

```bash
npm run generate -- my-deck/slides.md
npm run generate -- my-deck/slides.md --pdf
```

## Slide Classes

### Default (no class)

Dark navy background (`#091F2C`), white text. Standard content layout.

### `title`

Vertically centered, large heading. Use for opening and closing slides.

```markdown
<!-- _class: title -->
<!-- _paginate: skip -->

# Presentation Title

Subtitle
```

### `divider`

Slightly lighter navy (`#0B2736`), accent-blue heading. Use between major sections.

```markdown
<!-- _class: divider -->

## Section Name
```

### `light`

Off-white background (`#F4F3F5`), dark text. Logo auto-switches to gray variant.

**Use this class for:**
- Diagram slides (dark backgrounds reduce diagram readability)
- Dense content, tables, and data
- Code-heavy slides

```markdown
<!-- _class: light -->

## Content Slide
```

### `lead`

Vertically centered content, dark background. Good for key takeaways.

```markdown
<!-- _class: lead -->

## Key Takeaway
```

### `cols`

CSS grid with two equal columns. Content is split at the second heading.

```markdown
<!-- _class: cols -->

## Left Column

Content for left side.

## Right Column

Content for right side.
```

## Marp Markdown Syntax

### Images

```markdown
![w:300](image.png)           # Width 300px
![h:200](image.png)           # Height 200px
![w:1100 center](image.png)   # Centered, width 1100px (best for diagrams)
![bg](image.png)              # Background image
![bg left](image.png)         # Background left half
![bg right:40%](image.png)    # Background right 40%
```

### Speaker Notes

```markdown
## Slide Title

Content visible to audience.

<!--
Speaker notes go here.
Only visible in presenter view.
-->
```

### Directives

Per-slide properties via HTML comments:

```markdown
<!-- _class: title -->            Set slide class
<!-- _paginate: skip -->          Hide page number
<!-- _backgroundColor: #fff -->   Override background
<!-- _color: #000 -->             Override text color
```

## Design Principles

1. **Alternate dark and light slides** — use light slides for diagrams and data
2. **Use divider slides** between major sections to create visual rhythm
3. **One big idea per slide** — avoid overloading content
4. **Diagram slides should have minimal text** — let the architecture speak
5. **Benefits/comparison slides pair well with diagram slides** — explain why after showing what
6. **Tables work best on light slides** — the dark-on-light contrast improves readability
7. **Skip pagination on title/closing slides** — cleaner visual

## Logo Behavior

- **Dark slides (default, title, divider, lead):** White logo with color badge (top-left)
- **Light slides:** Gray logo with color badge (top-left)
- Logos are embedded as base64 data URIs in the CSS — no external file dependencies
- No manual logo placement needed; it's all handled by the theme CSS

## Building Outputs

Build from the deck folder using local paths:

```bash
# From inside the deck folder
npx marp slides.md -o slides.html --theme-set ./microsoft-internal.css --html
npx marp slides.md -o slides.pptx --pptx --theme-set ./microsoft-internal.css --html --allow-local-files
npx marp slides.md -o slides.pdf --pdf --theme-set ./microsoft-internal.css --html --allow-local-files
```

Or use the deck's `generate.sh`:

```bash
bash generate.sh          # HTML + PPTX
bash generate.sh --pdf    # HTML + PPTX + PDF
```

## Tips

- **Preview in VS Code:** Install the `marp-team.marp-vscode` extension, then open the `.md` file and press `Ctrl+Shift+V` for live Marp preview with the full theme applied (logos, colors, layout classes)
- **Local images in exports:** Use `--allow-local-files` for PPTX/PDF so local images (diagrams) embed correctly
- **Self-contained HTML:** The HTML output embeds all images as data URIs — safe to share as a single file
- **Adding diagrams:** If you need architecture diagrams, see [diagrams.md](diagrams.md) for the optional add-on

## QA & Validation (REQUIRED)

**Assume there are problems. Your job is to find them.** Your first render is almost never perfect. If you found zero issues on first inspection, you weren't looking hard enough.

### Automated validation with Playwright

After building HTML, run the Playwright validator:

```bash
node scripts/validate_slides.mjs slides.html
```

This checks per-slide: logo rendering (data URI), footer text, background colors, font family, heading presence. Screenshots are captured to `artifacts/screenshots/<type>-<timestamp>/`.

### Screenshot review

Open each screenshot and verify visually:

- [ ] Microsoft logo visible in top-left corner (correct variant per slide type)
- [ ] "Microsoft Confidential" footer in bottom-left
- [ ] Text legible against its background
- [ ] Tables have correct styling (accent header, subtle row borders)
- [ ] Diagrams render at full size, not clipped or missing
- [ ] No overlapping elements
- [ ] Consistent spacing and margins
- [ ] Dark/light slide alternation creates visual rhythm
- [ ] Slide progression tells a coherent story

### Fix-and-verify loop

1. **Build** — `bash generate.sh`
2. **Validate** — `node scripts/validate_slides.mjs slides.html`
3. **Inspect** screenshots
4. **Fix** issues in `.md` source
5. **Repeat** steps 1–4 until all checks pass

**Do not declare the deck finished until a full pass reports zero errors and zero visual issues.**

### Design drift detection

If the user asks whether output matches the PowerPoint template or brand guidelines:

1. Build the deck and take Playwright screenshots
2. Compare screenshot colors/layout against the source PowerPoint (in `guidelines/`)
3. Check: background color matches `#091F2C`, logo position at (61, 62), heading fonts are Segoe UI Semibold, footer is "Microsoft Confidential"
4. For diagrams: verify PNGs are not stale (check timestamps), re-generate if needed
