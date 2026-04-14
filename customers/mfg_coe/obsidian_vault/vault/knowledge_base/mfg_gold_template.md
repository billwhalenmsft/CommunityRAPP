# Context Card: Mfg Gold Template

> All CoE agents load this context card before generating code, SOPs, or configs targeting this environment.

## Environment Overview

- **Name:** Mfg Gold Template
- **Type:** Discrete Manufacturing — Gold template / baseline D365 environment
- **Purpose:** Reusable template for standing up new Discrete Manufacturing demos quickly

## Key Characteristics

- Clean, minimal data — designed to be cloned per-customer engagement
- Represents a "best practice" baseline Discrete Mfg D365 configuration
- Used as the starting point for new customer demo builds

## Known Entities / Data Model Notes

- Minimal seed data — accounts, contacts, cases created per engagement
- Standard D365 CE schema with Mfg-specific customizations applied
- Product catalog: generic Discrete Mfg products (can be swapped per customer)

## Integration Points

- D365 Customer Service (core)
- Copilot Studio baseline agent template
- Standard Power Automate flows (case creation, escalation)

## Limitations / Gotchas

- _Add known limitations as they are discovered_
- Not intended for live customer demos without data seeding first

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-04-14 | Initial context card created | CoE Intake Agent |
