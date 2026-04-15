# Context Card: Master CE Mfg

> All CoE agents load this context card before generating code, SOPs, or configs targeting this environment.

## Environment Overview

- **Name:** Master CE Mfg
- **Environment ID:** `a3140474-f21d-e811-a97e-000d3a1ab78c`
- **URL:** `https://orgecbce8ef.crm.dynamics.com/`
- **Type:** Discrete Manufacturing — Dynamics 365 Customer Engagement demo environment
- **Purpose:** Primary demo environment for Discrete Manufacturing CRM/CE scenarios
- **Region:** North America
- **Status:** Active (managed, production-tier)

## Key Characteristics

- Discrete Manufacturing focus (not process/batch manufacturing)
- Field Service + Customer Service integration scenarios
- Copilot Studio agents deployed for customer self-service and internal agent assist
- Power Platform solutions active
- Primary environment for live customer demos

## Known Entities / Data Model Notes

- Accounts: Manufacturing companies (OEMs, distributors, dealers)
- Contacts: Procurement, maintenance, field ops personas
- Cases: Warranty claims, RMAs, field service requests, order inquiries
- Products: Manufactured goods with serial numbers, warranty dates
- Work Orders: Field service dispatch scenarios

## Deployed Agents (Copilot Studio)

- Customer self-service agent (warranty check, RMA initiation, order status)
- Internal agent assist (case summarization, KB search)
- _Run inventory agent to get full list_

## Integration Points

- D365 Field Service
- D365 Customer Service
- Copilot Studio (self-service + agent assist)
- Power Automate flows for case routing
- Power Pages (customer portal)

## Customers Demoed Here

- Navico (marine electronics)
- Otis Elevator
- Zurn Elkay (water solutions)
- Vermeer Corporation
- Carrier Global
- AES Corporation

## Limitations / Gotchas

- Data is accumulative — may have artifacts from multiple customer builds
- Do NOT delete core accounts/cases without checking with Bill first
- Custom solutions installed — sync carefully with Gold Template

## Agent Instructions

When generating artifacts FOR this environment:
1. Use the D365 URL above when constructing API calls or Copilot Studio configs
2. Assume Field Service + Customer Service are both installed
3. Assume Copilot Studio agents are deployed — don't re-scaffold from scratch
4. Check `customers/mfg_coe/d365_environments.json` for full solution list when available

## Inventory Status

- **Last inventoried:** Not yet (stub — trigger inventory agent from Knowledge Base tab)
- **Solutions installed:** _Run inventory to populate_
- **Power Automate flows:** _Run inventory to populate_

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-13 | Added environment IDs, URL, customers, agent instructions | CoE Web UI |
| 2026-04-14 | Initial context card created | CoE Intake Agent |
