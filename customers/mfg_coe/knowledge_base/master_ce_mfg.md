# Context Card: Master CE Mfg

> All CoE agents load this context card before generating code, SOPs, or configs targeting this environment.

## Environment Overview

- **Name:** Master CE Mfg
- **Type:** Discrete Manufacturing — Dynamics 365 Customer Engagement demo environment
- **Purpose:** Primary demo environment for Discrete Manufacturing CRM/CE scenarios

## Key Characteristics

- Discrete Manufacturing focus (not process/batch manufacturing)
- Field Service + Customer Service integration scenarios
- Copilot Studio agents deployed for customer self-service and internal agent assist
- Power Platform solutions active

## Known Entities / Data Model Notes

- Accounts: Manufacturing companies (OEMs, distributors, dealers)
- Contacts: Procurement, maintenance, field ops personas
- Cases: Warranty claims, RMAs, field service requests, order inquiries
- Products: Manufactured goods with serial numbers, warranty dates
- Work Orders: Field service dispatch scenarios

## Integration Points

- D365 Field Service
- D365 Customer Service
- Copilot Studio (self-service + agent assist)
- Power Automate flows for case routing

## Limitations / Gotchas

- _Add known limitations as they are discovered_

## Change Log

| Date | Change | By |
|---|---|---|
| 2026-04-14 | Initial context card created | CoE Intake Agent |
