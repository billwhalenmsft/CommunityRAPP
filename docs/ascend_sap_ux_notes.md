# Ascend SAP Procurement Agent UX Notes

## Scope
Issue #49 UX upgrades applied through `customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py --apply-ux`.

## Channel rendering notes

### Microsoft Teams
- Markdown tables and bullet lists render reliably in topic message output.
- Adaptive Card v1.5 buttons (`Approve` / `Reject`) render as expected with `style: positive` and `style: destructive`.
- Action routing uses `Action.Submit` payload data (`route_topic`, `pr_number`, `decision`).

### Microsoft 365 Copilot
- Markdown headings, inline `code`, and status emoji render in conversational responses.
- Adaptive Card v1.5 renders for PR detail, vendor profile, list, and pending-approval views.
- `View in SAP` links use the placeholder path `https://sap.example.com/pr/{Topic.PRNumber}` pattern.

### Custom Web Chat / Web UI
- Markdown-first response remains readable even if a card host omits interactive actions.
- Adaptive Card schema is standard v1.5 and does not rely on custom fonts or externally hosted images.

## Test prompts (seeded demo data)
- `Find vendor Dell` → expected vendor `V200001` (Dell Technologies Inc)
- `Status of PR 10012345` → expected pending PR detail ($24,000)
- `Show pending approvals for jsmith` → expected pending approval list with actions
- `List my PRs` → expected compact list presentation
- `Approve PR 10012345` → expected approval confirmation response

## Screenshot placeholders
- Teams — Vendor Lookup card: _TODO add screenshot_
- Teams — PR Status card: _TODO add screenshot_
- M365 Copilot — Pending approvals cards: _TODO add screenshot_
- Web UI — List My PRs compact list: _TODO add screenshot_
