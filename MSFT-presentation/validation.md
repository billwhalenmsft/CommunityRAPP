# Slide Validation Guide

## Overview

Playwright-based visual validation ensures that every slide in a Marp deck adheres to the Microsoft CES-FY26 design guidelines. Validation catches:

- Missing or broken logo rendering
- Missing "Microsoft Confidential" footer
- Incorrect background colors for each slide class
- Wrong fonts (should be Segoe UI)
- Slides without headings
- Broken images (e.g., diagram not found)

## Running Validation

### Quick validation (main deck)

```bash
# Build the main deck and run lint + screenshot checks
npm run lint
```

This runs `scripts/lint_slides.mjs` against `slides/slides.html`.

### Generic validation (any deck)

```bash
# Build the deck first
npm run generate -- <folder>/slides.md

# Then validate
node scripts/validate_slides.mjs <folder>/slides.html
```

### Screenshot-only capture

```bash
npm run screenshots
```

## What Gets Checked

### 1. CSS Theme Integrity

| Check | Expected |
|-------|----------|
| `@theme` metadata | Present in CSS |
| Logo data URIs | At least 2 (dark + light variants) |
| CSS custom properties | `--ms-dk1`, `--ms-dk2`, etc. |
| Font family | `Segoe UI` referenced |

### 2. Markdown Source

| Check | Expected |
|-------|----------|
| Theme directive | `theme: microsoft-internal` |
| Footer directive | `footer: '...'` present |
| Paginate directive | `paginate: true` present |
| Slide count | More than 1 separator |

### 3. Marp Config

| Check | Expected |
|-------|----------|
| `.marp.json` | Exists in slide folder, points to theme |
| `html` | Enabled |

### 4. Rendered Slides (Playwright)

For each slide, the validator checks:

| Check | Expected (dark) | Expected (light) | Expected (divider) |
|-------|-----------------|-------------------|--------------------|
| Background | `rgb(9, 31, 44)` | `rgb(244, 243, 245)` | `rgb(11, 39, 54)` |
| Logo | Data URI ✓ | Data URI ✓ | Data URI ✓ |
| Footer | Contains "Confidential" | Contains "Confidential" | Contains "Confidential" |
| Font | Includes "Segoe" | Includes "Segoe" | Includes "Segoe" |
| Headings | ≥ 1 per slide | ≥ 1 per slide | ≥ 1 per slide |

### 5. Screenshot Output

Screenshots are saved to:

```
artifacts/screenshots/lint-<timestamp>/
├── lint-slide-1.png
├── lint-slide-2.png
├── ...
```

A `lint-latest` symlink always points to the most recent run.

## Custom Validation Script

For decks outside the main `slides/` folder, use `scripts/validate_slides.mjs`:

```bash
node scripts/validate_slides.mjs slide-diagram/slides.html
```

This script performs the same Playwright rendering checks as `lint_slides.mjs` but accepts any HTML path.

## Fix-and-Verify Loop

1. **Build** — `npm run generate -- <folder>/slides.md`
2. **Validate** — `node scripts/validate_slides.mjs <folder>/slides.html`
3. **Inspect** — Review screenshots in `artifacts/screenshots/`
4. **Fix** — Edit the `.md` source or diagram scripts
5. **Repeat** — Re-run steps 1–3 until all checks pass

**Do not consider the deck finished until a full validation pass reports zero errors.**

## Visual QA Checklist

When reviewing screenshots, also manually check for:

- [ ] Diagram images render at appropriate size (not clipped or overflowing)
- [ ] Text is legible against its background
- [ ] Tables have correct styling (accent header, subtle row borders)
- [ ] No overlapping elements
- [ ] Consistent spacing and margins
- [ ] Slide progression tells a coherent story

## Common Validation Failures

| Failure | Cause | Fix |
|---------|-------|-----|
| Logo NOT rendered | CSS theme not loaded | Check `.marp.json` points to correct theme path |
| Missing footer | No `footer:` in front-matter | Add `footer: 'Microsoft Confidential'` |
| Wrong background color | Missing or wrong class directive | Add `<!-- _class: light -->` etc. |
| Diagram not visible in PPTX | Local file security block | Ensure `--allow-local-files` in generate script |
| Playwright error | Chromium not installed | Run `npx playwright install chromium` |

## Prerequisites

### VS Code Extension (for preview)

Install **Marp for VS Code** (`marp-team.marp-vscode`) to get live slide preview in the editor. Without it, you cannot visually check slides while editing.

### Playwright (for automated validation)

Minimum tested versions:

| Package | Minimum Version |
|---------|----------------|
| `playwright` | `1.58.2` |
| `@marp-team/marp-cli` | `4.2.3` |
| `Node.js` | `24.14.0` |

```bash
# Install Chromium for Playwright (first time only)
npx playwright install chromium

# Or via npm script
npm run screenshots:install
```
