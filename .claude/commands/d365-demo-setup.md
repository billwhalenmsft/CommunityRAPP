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
3. Run `d365/scripts/00-Setup.ps1 -Customer {name}` step by step
4. Validate the environment (entity counts, brand accounts, SLAs, data exports)
5. Generate demo script, execution guide, phone/chat/email scenarios
6. Report results and validation score

## Rules
- Idempotent: safe to re-run any step
- No hard-coded customer values in shared scripts
- Export all record IDs to `customers/{name}/d365/data/`
- Use real customer personas/products in all demo content
