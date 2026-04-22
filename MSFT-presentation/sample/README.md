# Sample Presentation — Baseline Reference

This folder is the **canonical baseline** for the `microsoft-presentation` skill.
Agents should use it as the source-of-truth when creating new decks. If a generated
deck diverges from the patterns here, it's a bug in the generation — not a new convention.

## What this sample validates

| File | Demonstrates |
|------|-------------|
| `slides.md` | Every slide class (`title`, `divider`, `light`, `lead`, `cols`, default), front-matter, image embedding, tables, blockquotes, code blocks, speaker notes |
| `.marp.json` | Required Marp config with theme path and `allowLocalFiles` |
| `generate.sh` | Per-folder build script with `--pdf` and `--all` flags |

## How logos work

Logos are **NOT** referenced in slide Markdown. They are embedded as base64 data URIs
directly inside `themes/microsoft-internal.css` and injected via CSS `::before` pseudo-elements:

- **Dark slides** (default, title, divider, lead) → white logo with color badge
- **Light slides** → gray logo with color badge

The Playwright validator checks every slide for a rendered logo (`data:image/png;base64,...`).
If logos are missing, the theme CSS is broken — not the slides.

### Source logo chain

```
microsoft-logo/Microsoft-logo_rgb_c-wht.png  ─┐
microsoft-logo/Microsoft-logo_rgb_c-gray.png ─┤
                                              ├─► npm run theme:build
                                              │
                                              ▼
                              themes/microsoft-internal.css
                              (logos embedded as base64 data URIs)
                                              │
                                              ▼
                              Rendered on every slide via CSS ::before
```

To update logos: replace the PNGs in `microsoft-logo/`, then run `npm run theme:build`.

## Using as a reference

When creating a new presentation, copy these patterns exactly:

1. **Front-matter** — must include `marp: true`, `theme: microsoft-internal`, `paginate: true`, `footer: 'Microsoft Confidential'`
2. **Title slides** — use `<!-- _class: title -->` + `<!-- _paginate: skip -->`
3. **Section dividers** — use `<!-- _class: divider -->`
4. **Diagram slides** — use `<!-- _class: light -->` with `![w:1100 center](...)`
5. **Data/table slides** — use `<!-- _class: light -->` for readability
6. **Two-column layouts** — use `<!-- _class: cols -->`
7. **Build script** — every folder gets a `generate.sh`

## Building the sample

```bash
# From repo root
bash skills/microsoft-presentation/sample/generate.sh --all
```

## Validating against baseline

If you modify the theme or build pipeline, rebuild this sample and confirm 0 errors:

```bash
bash skills/microsoft-presentation/sample/generate.sh --all
# Should report: 🎉 ALL CHECKS PASSED
```
