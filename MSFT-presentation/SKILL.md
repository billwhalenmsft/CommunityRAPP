```skill
---
name: microsoft-presentation
description: "Use this skill whenever creating, editing, or validating a Microsoft-branded Marp presentation. This includes: creating new slide decks from Marp Markdown; applying Microsoft CES-FY26 visual identity (dark navy theme, colors, fonts, logos, layout classes); building HTML, PPTX, and PDF outputs; and validating rendered slides with Playwright. Trigger whenever the user mentions 'presentation', 'slides', 'deck', 'Marp', or references the Microsoft visual identity guidelines. For architecture diagrams as code (optional add-on), see diagrams.md."
license: MIT
---

# Microsoft Presentation Skill

Create professional Microsoft-branded slide decks using Marp Markdown with CES-FY26 Visual Identity Guidelines.

> **CRITICAL RULE: Every deck folder must be fully self-contained.**
> Copy `microsoft-internal.css` INTO each deck folder. **Never link to the skill's `theme/` folder.**
> The theme file has logos embedded as base64 — no other assets are needed.
> A deck folder with `slides.md`, `microsoft-internal.css`, and `.marp.json` is 100% portable.

## Quick Reference

| Task | Guide |
|------|-------|
| **Create a new slide deck** | Read [marp-slides.md](marp-slides.md) |
| **Add architecture diagrams** (optional) | Read [diagrams.md](diagrams.md) |
| **Validate with Playwright** | Read [validation.md](validation.md) |
| **Baseline sample** | See [sample/](sample/) — canonical reference |

> **Important:** The `sample/` folder is the source-of-truth.
> Every slide class, front-matter convention, and build pattern is demonstrated there.
> When generating a new deck, match the sample. If output diverges, fix the output — not the sample.

---

## Workflow

### Step 1 — Create a self-contained deck folder

Every deck lives in its own folder with all assets local. **Read [marp-slides.md](marp-slides.md) for full details.**

```bash
mkdir -p my-deck
# Copy the theme CSS into the deck folder (REQUIRED)
cp theme/microsoft-internal.css my-deck/
```

**Required `.marp.json` in the deck folder (points to LOCAL theme):**

```json
{
  "theme": "./microsoft-internal.css",
  "html": true,
  "allowLocalFiles": true
}
```

**Required front-matter in `slides.md`:**

```markdown
---
marp: true
theme: microsoft-internal
paginate: true
footer: 'Microsoft Confidential'
---
```

### Step 2 — Author slides

Create `my-deck/slides.md` using Marp Markdown. See [marp-slides.md](marp-slides.md) for slide classes, syntax, and design principles.

### Step 3 — Build outputs

```bash
# From the deck folder
npx marp slides.md -o slides.html --theme-set ./microsoft-internal.css --html
npx marp slides.md -o slides.pptx --pptx --theme-set ./microsoft-internal.css --html --allow-local-files
```

Or use a build script (see `sample/generate.sh`).

### Step 4 — Validate with Playwright screenshots (REQUIRED)

**Assume there are problems. Your job is to find them.** Your first render is almost never correct. If you found zero issues on first inspection, you weren't looking hard enough.

Read [validation.md](validation.md) for the complete validation reference.

#### Automated validation

Run the Playwright validator against the built HTML:

```bash
node scripts/validate_slides.mjs <folder>/slides.html
```

This launches headless Chromium, navigates every slide, and checks:

| Check | What it validates |
|-------|-------------------|
| **Logo rendering** | `section::before` contains a `data:image/png;base64` URI on every slide |
| **Logo variant** | Dark slides use white logo; light slides auto-switch to gray |
| **Footer** | "Microsoft Confidential" text present in bottom-left |
| **Background color** | `rgb(9, 31, 44)` for dark, `rgb(244, 243, 245)` for light, `rgb(11, 39, 54)` for divider |
| **Font family** | `Segoe UI` referenced in computed styles |
| **Headings** | At least one `h1`–`h4` on every slide |
| **Page numbers** | Pagination content present (except title slides) |

It also captures **per-slide screenshots** to `artifacts/screenshots/<type>-<timestamp>/` for visual review.

#### Screenshot-based visual inspection

After automated checks pass, **review the screenshot images**:

```bash
# Screenshots are in timestamped folders — check latest
ls artifacts/screenshots/lint-latest/
```

Open each `lint-slide-N.png` and manually verify:

- [ ] Logo visible in top-left corner (correct variant for slide type)
- [ ] Footer text visible in bottom-left
- [ ] Text legible against background
- [ ] Tables correctly styled (accent header, subtle borders)
- [ ] Diagrams render at full size, not clipped or missing
- [ ] No overlapping elements
- [ ] Consistent spacing and margins
- [ ] Dark/light slide alternation creates visual rhythm

#### Pixel-level logo verification (for high confidence)

When you need proof that logos physically rendered (not just DOM-present), analyze screenshots with PIL:

```python
from PIL import Image
im = Image.open('artifacts/screenshots/lint-latest/lint-slide-1.png').convert('RGBA')
# Logo region: top-left (50,45) to (230,105)
logo_region = im.crop((50, 45, 230, 105))
pixels = list(logo_region.getdata())
# Count Microsoft badge colors (red/green/blue/yellow squares)
badge_px = sum(1 for r,g,b,a in pixels if a > 30 and (
    (r > 180 and g < 80 and b < 80) or   # red
    (g > 150 and r < 80 and b < 80) or   # green
    (b > 150 and r < 80 and g < 80) or   # blue
    (r > 180 and g > 180 and b < 80)     # yellow
))
print(f"Badge pixels: {badge_px} — {'✅ Logo visible' if badge_px > 20 else '❌ Logo MISSING'}")
```

### Step 5 — Fix and re-verify (mandatory loop)

1. **Fix** issues found in the `.md` source or diagram scripts
2. **Rebuild** — `npx marp slides.md -o slides.html --theme-set ./microsoft-internal.css --html`
3. **Re-validate** — `node scripts/validate_slides.mjs slides.html`
4. **Re-inspect** screenshots
5. **Repeat until a full pass reports zero errors and zero visual issues**

**Do not declare success until you've completed at least one fix-and-verify cycle.** One fix often creates another problem (e.g., fixing text overflow may push content into the footer region).

---

## Design Drift Detection

When the user asks about design drift — whether the Marp output matches the original PowerPoint template or brand guidelines — use this process:

### Comparing Marp output to PowerPoint source

1. **Build the Marp deck** to HTML
2. **Take Playwright screenshots** of every slide
3. **Open the source PowerPoint** (in `guidelines/`) and compare visually:

| Property | PowerPoint source | Marp output | How to check |
|----------|------------------|-------------|-------------|
| Background color | `#091F2C` solid fill | CSS `--ms-dk1` | Pixel sample dominant color |
| Logo position | (61, 62) px from top-left | CSS `section::before` | Crop logo region, count branded pixels |
| Logo variant | White on dark, gray on light | Auto-switched by CSS class | Check `section.light::before` |
| Heading font | Segoe UI Semibold 600 | CSS `h1, h2` rules | DOM computed style |
| Body font | Segoe UI 400 | CSS `:root` | DOM computed style |
| Footer | "Microsoft Confidential" at (61, 686) | CSS `footer` | DOM text content |
| Pagination | Bottom-right, subtle | CSS `section::after` | DOM `::after` content |

### Automated drift check

```bash
# Full pipeline: build + validate + screenshot
npx marp slides.md -o slides.html --theme-set ./microsoft-internal.css --html
node scripts/validate_slides.mjs slides.html
```

The validator reports drift as **errors** (wrong colors, missing logos) or **warnings** (minor font differences). A clean pass means zero design drift.

### Diagram drift

If diagrams don't match the expected architecture:

1. Regenerate: `python3 diagrams/your-diagram.py`
2. Rebuild HTML (to re-embed the updated PNG)
3. Take screenshots and verify the diagram renders correctly on the `light` class slide
4. Check that diagram PNGs are not stale — compare file timestamps

### Optional — Add architecture diagrams

If the presentation needs Azure architecture diagrams, read [diagrams.md](diagrams.md).

```bash
pip install diagrams && sudo apt-get install -y graphviz
python3 diagrams/your-diagram.py
```

Then reference in slides:

```markdown
<!-- _class: light -->

## Architecture Overview

![w:1100 center](../diagrams/output/your-diagram.png)
```

---

## Design Guidelines Summary

### Colors (CES-FY26 "Custom 21" palette)

| Token | Hex | Usage |
|-------|-----|-------|
| `--ms-dk1` | `#091F2C` | Primary dark background |
| `--ms-dk2` | `#0B2736` | Divider/section bg |
| `--ms-lt1` | `#FFFFFF` | White text on dark |
| `--ms-lt2` | `#F4F3F5` | Light slide background |
| `--ms-accent1` | `#8DC8E8` | Sky blue — links, highlights, H3 |
| `--ms-accent2` | `#0078D4` | Azure blue — brand accent |

### Typography

| Role | Font | Size |
|------|------|------|
| H1 | Segoe UI Semibold | 2.6em (title: 2.8em) |
| H2 | Segoe UI Semibold | 1.8em |
| H3/H4 | Segoe UI Semibold | 1.3em |
| Body | Segoe UI | 18px |

### Slide Classes

| Class | Directive | Purpose |
|-------|-----------|---------|
| *(default)* | — | Dark navy bg, white text |
| `title` | `<!-- _class: title -->` | Vertically centered, large heading |
| `divider` | `<!-- _class: divider -->` | Section break, accent heading |
| `light` | `<!-- _class: light -->` | Light bg — tables, data, diagrams |
| `lead` | `<!-- _class: lead -->` | Centered content, key takeaways |
| `cols` | `<!-- _class: cols -->` | Two-column grid |

### Key Rules

- Title/closing slides: `<!-- _paginate: skip -->`
- Diagram and table slides use `light` class
- Logos embedded as base64 data URIs (no external file deps)
- Footer auto-applied from front-matter

---

## Assets & Logos

Logos are **embedded as base64 data URIs** inside `microsoft-internal.css` (66 KB). This means:

- **No external logo files needed** — the theme is 100% self-contained
- **Copy the single CSS file** into any deck folder and logos just work
- No path resolution issues in any context (CLI, VS Code, browser)

| Variant | Applied to | Mechanism |
|---------|-----------|----------|
| White logo | Dark slides (default, title, divider, lead) | CSS `section::before` |
| Gray logo | Light slides | CSS `section.light::before` |

Source PNGs for theme rebuilds only: `logos/Microsoft-logo_rgb_c-wht.png`, `logos/Microsoft-logo_rgb_c-gray.png`

> **Never reference logo files from slides. Never link to the skill's `theme/` folder from a deck.**
> The CSS file IS the theme — copy it, don't link it.

---

## Dependencies

### VS Code Extension (required for preview)

Install the **Marp for VS Code** extension:

```
marp-team.marp-vscode
```

This enables live slide preview inside VS Code when editing `.md` files. Open a slide file and press `Ctrl+Shift+V` (or `Cmd+Shift+V` on Mac) to see the themed preview with logos, colors, and layout classes applied.

> **Without this extension, you cannot preview slides in the editor.** Add it to `.devcontainer/devcontainer.json` under `customizations.vscode.extensions` for automatic installation in dev containers.

### npm

```bash
npm install                        # @marp-team/marp-cli >=4.2.3, playwright >=1.58.2
npx playwright install chromium    # First time only
```

Minimum tested versions:

| Package | Minimum Version |
|---------|----------------|
| `@marp-team/marp-cli` | `4.2.3` |
| `playwright` | `1.58.2` |
| `Node.js` | `24.14.0` |

### Optional (for diagrams)

```bash
pip install diagrams>=0.25.1
sudo apt-get install -y graphviz
```

| Package | Minimum Version |
|---------|----------------|
| `diagrams` (Python) | `0.25.1` |
| `graphviz` (system) | any recent |
| `Python` | `3.12+` |

---

## Directory Structure

```
skills/microsoft-presentation/
├── SKILL.md                     # This file — skill manifest
├── marp-slides.md               # Core: slide authoring guide
├── diagrams.md                  # Optional: diagram-as-code guide
├── validation.md                # Playwright validation guide
├── package.json                 # npm deps
├── theme/
│   └── microsoft-internal.css   # SOURCE theme (copy into each deck)
├── logos/                       # Source PNGs (for theme rebuilds only)
├── scripts/
│   ├── generate.mjs             # Build HTML + PPTX + PDF
│   └── validate_slides.mjs      # Playwright validator
└── sample/                      # Canonical reference deck
    ├── slides.md                # Slide source
    ├── microsoft-internal.css   # LOCAL copy of theme (not a link!)
    ├── .marp.json               # Points to ./microsoft-internal.css
    ├── generate.sh              # Self-contained build script
    └── diagrams/                # Optional diagram integration
```

> **Every generated deck folder looks like `sample/`**: slides.md, microsoft-internal.css, .marp.json, generate.sh — all local, all portable.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Logo not rendering | Logos are base64 in CSS — reload preview |
| Theme not applied | `.marp.json` must point to `./microsoft-internal.css` (local, not `../`) |
| PPTX export fails | Run `npx playwright install chromium` |
| Diagram images missing in PPTX | Use `--allow-local-files` |
| `dot` not found | `sudo apt-get install -y graphviz` |
| Fonts differ on Linux | Segoe UI falls back to Arial — expected |
```
