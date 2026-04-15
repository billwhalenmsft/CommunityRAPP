# Context Card: Mfg Gold Template

> All CoE agents load this context card before generating code, SOPs, or configs targeting this environment.

## Environment Overview

- **Name:** Mfg Gold Template
- **Environment ID:** `2404ccaf-1c20-ed11-a7c7-000d3a5c48fd`
- **URL:** `https://org6feab6b5.crm.dynamics.com/`
- **Type:** Discrete Manufacturing — Gold template / baseline D365 environment
- **Purpose:** Reusable template for standing up new Discrete Manufacturing demos quickly
- **Region:** North America
- **Status:** Active (managed)

## Key Characteristics

- Clean, minimal data — designed to be cloned per-customer engagement
- Represents a "best practice" baseline Discrete Mfg D365 configuration
- Used as the starting point for new customer demo builds
- Changes here become the "standard" that flows to all customer demos

## Known Entities / Data Model Notes

- Minimal seed data — accounts, contacts, cases created per engagement
- Standard D365 CE schema with Mfg-specific customizations applied
- Product catalog: generic Discrete Mfg products (can be swapped per customer)
- Security roles and teams configured per Mfg best practice

## Integration Points

- D365 Customer Service (core)
- Copilot Studio baseline agent template
- Standard Power Automate flows (case creation, escalation)
- Power Pages template (customer portal)

## Gold Template Rules (IMPORTANT)

1. **Do not add customer-specific data** — keep data generic and industry-representative only
2. **Any new customization gets tested here first**, then applied to Master CE Mfg
3. **Track all installed solutions** — before adding, verify no conflicts with existing
4. **Before cloning** for a new customer: take a snapshot, document the date

## Agent Instructions

When generating artifacts FOR this environment:
1. Use the D365 URL above when constructing API calls
2. Assume Customer Service is installed; Field Service optional (check before using)
3. Treat this as the "canonical" Mfg pattern — outputs from here become SOPs
4. If a new pattern is validated here, document it in `knowledge_base/` and create a SOP issue

## Inventory Status

- **Last inventoried:** Not yet (stub — trigger inventory agent from Knowledge Base tab)
- **Solutions installed:** _Run inventory to populate_
- **Power Automate flows:** _Run inventory to populate_

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-13 | Added environment IDs, URL, Gold Template rules, agent instructions | CoE Web UI |
| 2026-04-14 | Initial context card created | CoE Intake Agent |
