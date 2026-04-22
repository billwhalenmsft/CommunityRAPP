---
name: msft-presentation
description: Create Microsoft-branded PowerPoint/PDF presentations from Markdown using Marp with CES-FY26 visual identity. Use when creating customer-facing decks, demo summaries, proposal slides, or any presentation output from project work. Produces HTML, PPTX, and PDF with automated brand validation.
---

# Microsoft Presentation Skill

## What This Does
Generates Microsoft CES-FY26 branded presentations (PPTX, PDF, HTML) from Markdown using the Marp framework. Includes automated Playwright validation for logos, colors, fonts, and layout.

## When To Use
- Creating customer-ready presentation decks from project/demo work
- Converting discovery notes, demo guides, or project summaries into slides
- Building proposal decks or executive summaries
- Updating an existing deck template for a new customer (e.g., Otis → Navico)

## Location
`MSFT-presentation/` in the repo root.

## Quick Start — Create a New Deck

### 1. Create deck folder and copy theme
```bash
mkdir MSFT-presentation/my-deck
cp MSFT-presentation/theme/microsoft-internal.css MSFT-presentation/my-deck/
cp MSFT-presentation/sample/.marp.json MSFT-presentation/my-deck/
cp MSFT-presentation/sample/generate.sh MSFT-presentation/my-deck/
```

### 2. Create slides.md
```markdown
---
marp: true
theme: microsoft-internal
paginate: true
footer: 'Microsoft Confidential'
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Customer Name — D365 Customer Service
## Competitive Demo Summary

---

## Content Slide
- Point one
- Point two

---

<!-- _class: light -->

## Data Table

| Feature | Current | Proposed |
|---------|---------|----------|
| Channels | Email only | Email, Chat, Voice, Portal |

---

<!-- _class: title -->
<!-- _paginate: skip -->

# Thank You
```

### 3. Build
```bash
cd MSFT-presentation/my-deck
bash generate.sh    # Produces slides.html + slides.pptx
```

### 4. Validate
```bash
cd MSFT-presentation
node scripts/validate_slides.mjs my-deck/slides.html
```

## Slide Classes

| Class | Directive | Use For |
|-------|-----------|---------|
| *(default)* | — | Regular content (dark navy background) |
| `title` | `<!-- _class: title -->` | Opening/closing slides (add `<!-- _paginate: skip -->`) |
| `divider` | `<!-- _class: divider -->` | Section breaks |
| `light` | `<!-- _class: light -->` | Tables, diagrams, data-heavy content (white background) |
| `lead` | `<!-- _class: lead -->` | Key takeaways (centered) |
| `cols` | `<!-- _class: cols -->` | Two-column layout |

## Critical Rules
1. **Every deck folder must be self-contained** — copy `microsoft-internal.css` INTO the folder (never link)
2. **Never modify the CSS theme** — it's the brand source of truth
3. **Logos are automatic** — embedded as base64 in CSS, white on dark slides, gray on light slides
4. **Always validate before sharing** — run Playwright validation for zero-error confirmation
5. **Footer must say** `Microsoft Confidential` (or appropriate classification)

## Customer Deck Pattern
For each customer engagement, create decks under `customers/{name}/presentations/`:
```
customers/navico/presentations/
├── demo-summary/
│   ├── slides.md
│   ├── microsoft-internal.css
│   ├── .marp.json
│   └── generate.sh
├── proposal/
│   └── ...
└── executive-briefing/
    └── ...
```

## Dependencies
- Node.js ≥ 18, npm
- `npm install` in `MSFT-presentation/` (installs marp-cli + playwright)
- VS Code extension `marp-team.marp-vscode` for live preview (Ctrl+Shift+V)

## Integration with RAPP Pipeline
When a RAPP project completes or a demo build finishes, generate a presentation:
1. Pull key data from the customer folder (`customers/{name}/`)
2. Create a deck folder with the template files
3. Write `slides.md` with customer-specific content
4. Build and validate
5. Output goes to `customers/{name}/presentations/{deck-name}/slides.pptx`
