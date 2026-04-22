# D365 Customer Service Demo Setup

You are launching a new Dynamics 365 Customer Service demo build. Walk the user through an interactive setup, collecting information in small groups (2-3 questions at a time).

## Collect This Information

**Customer basics:** name, industry, brands, D365 org URL, incumbent CRM
**Support model:** channels, agent count, tier structure, SLA targets, business hours, hot words
**Demo goals:** pain points, personas (with names), products/services, capabilities to showcase
**Context:** timeline, competitive notes, first demo vs deep-dive, specific asks

## Then Execute

1. Create `customers/{name}/d365/config/environment.json` (use `customers/zurnelkay/d365/config/environment.json` as the reference schema)
2. Create folder structure: `d365/data/`, `d365/demo-assets/`, `d365/copilot-studio/`
3. Create `customers/{name}/d365/config/demo-data.json` — accounts, contacts, product serials, pre-seeded cases
4. Create `customers/{name}/d365/data/hero-cases.json` — hero case scenarios with activity timelines
5. Create `customers/{name}/d365/data/knowledge-articles.json` — KB articles for Copilot to surface
6. Create `customers/{name}/d365/Provision-{Customer}Demo.ps1` — base provisioning script
7. Create `customers/{name}/d365/Provision-{Customer}HeroCases.ps1` — hero cases, KB articles, quick responses
8. **Generate ONE unified HTML demo tool** (save to `customers/{name}/d365/demo-assets/{customer}_demo_unified.html`):
   - Single file combining execution guide + demo script into one story-based flow
   - Left slide-in navigation (hamburger toggle, PIN to dock)
   - Story-based flow top to bottom — tell the story in order
   - **Tell-Show-Tell (TST) segments** in every scenario using `.tst-wrapper` > `.tst-header` + `.tst-body`
   - Pre-flight checklist, hero records reference, all scenarios, competitive close
   - Use `customers/navico/d365/demo-assets/navico_demo_unified.html` as the canonical template
   - Copy the exact CSS/JS patterns from that file — only swap brand colors and content
9. Create `customers/{name}/d365/Provision-{Customer}Extended.ps1` — price lists, full product catalog, customer assets, entitlements, tier logic
10. Create `customers/{name}/d365/Run-{Customer}DemoSetup.ps1` — master orchestrator (copy from `d365/scripts/Run-DemoSetup.template.ps1`, swap script names)
11. Run `Run-{Customer}DemoSetup.ps1 -Phase All` to build the full environment in correct order
12. Run `Set-{Customer}CaseLinks.ps1` (post-case patch) — link entitlements and assets to cases
13. Validate the environment (entity counts, brand accounts, SLAs, data exports)
14. Report results and validation score

## Unified HTML Tool Standards

- **Single file** — no separate script + guide. One file, open it and flow top-to-bottom.
- **Left nav** (hamburger + PIN): auto-built from DOM via JavaScript, scroll-based active highlight
- **Sections**: collapsible `.exec-section` cards with numbered circles, colored by scenario type
- **Step labels**: TELL, SHOW, CLICK, SAY, TIP, CAUTION, COPILOT, TRANSITION, VOICE, CHAT, EMAIL
- **Tell-Show-Tell**: every scenario has TELL (current pain) → SHOW (demo steps) → TELL (value/ROI)
- **Talk tracks**: verbatim `.talk-track` quote blocks with opening quotation mark
- **Callouts**: `.callout.roi`, `.callout.warning`, `.callout.success`, `.callout.info`
- **Competitive table** in the close section comparing incumbent vs D365
- **Brand colors**: use customer brand colors in hero gradient and exec-number circles
- **Self-contained**: no external dependencies — works offline
- **Reference file**: `customers/navico/d365/demo-assets/navico_demo_unified.html`

## Build Phase Order — CRITICAL

**Cases must be created LAST.** All reference data must exist before cases are provisioned so entitlements, assets, and products can be linked correctly.

```
PHASE 1 — Foundation (no dependencies)
  1. Accounts
  2. Contacts           (needs accounts)
  3. Price Lists
  4. Products           (needs price lists + unit group)

PHASE 2 — Rich Data
  5. Customer Assets    (needs accounts + products)
  6. Entitlements       (needs accounts)
  7. KB Articles        (no deps — but publish manually after)
  8. Quick Responses    (no deps)

PHASE 3 — Cases (LAST — needs everything above)
  9. Demo Cases         (needs accounts, contacts, entitlements, assets)
 10. Hero Cases         (needs accounts, contacts, KB articles)

PHASE 4 — Post-Case Enrichment
 11. Case Link Enrich   (links cases → entitlements + assets)
 12. Tier Logic         (patches case priority from account tier)
 13. Primary Contacts   (verify all accounts linked)
```

The generic template lives at `d365/scripts/Run-DemoSetup.template.ps1`.
Each customer gets their own `customers/{name}/d365/Run-{Customer}DemoSetup.ps1` which calls their specific scripts in this order.

## Known API Gotchas (D365 Dataverse)

- `caseorigincode` valid values in orgecbce8ef: `1`=Phone, `2`=Email, `3`=Web, `2483`=Chat, `3986`=Portal. Value `4` is invalid.
- `knowledgearticles` POST: do NOT include `languageid`, `islatestversion`, `isprimary`, `articlepublicnumber`, or `statecode/statuscode`. Only `title`, `content`, `description` (max 155 chars).
- `msdyn_cannedmessages` POST: do NOT include `msdyn_locale`. Only `msdyn_title`, `msdyn_message`.
- `knowledgearticles` GET with filter can hang — add `-TimeoutSec 30` to `Invoke-RestMethod`. Filter by `title` not `articlepublicnumber`.
- KB articles are created as drafts — must be manually published in D365 UI for Copilot Agent Assist to surface them.

## Rules
- Idempotent: safe to re-run any step
- No hard-coded customer values in shared scripts
- Export all record IDs to `customers/{name}/d365/data/`
- Use real customer personas/products in all demo content
- Always generate the unified HTML demo tool — it is as important as the provisioning scripts
