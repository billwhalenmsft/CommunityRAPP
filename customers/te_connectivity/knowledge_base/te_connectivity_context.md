# Context Card: TE Connectivity

> All CoE agents load this context card before generating code, topics, flows, or configs targeting TE Connectivity engagements.

## Company Profile

- **Name:** TE Connectivity Ltd
- **Industry:** Electronic Components Manufacturing | Global Logistics & Supply Chain
- **Scale:** ~10,000 engineers | ~130 countries | NYSE: TEL
- **HQ:** Schaffhausen, Switzerland | Operational HQ: Berwyn, PA, USA
- **Website:** https://www.te.com
- **Business Model:** B2B — Sells connectors, sensors, and electronic components to OEMs in automotive, aerospace, industrial, medical, and communications sectors

## Logistics Context

TE Connectivity ships globally to customers in ~130 countries. Their freight booking team coordinates with multiple Freight Forwarders (3PLs) via email for each shipment. The booking cycle involves:

1. Freight booking instruction sent to forwarder
2. Forwarder confirms or requests additional info
3. Booking agent responds to queries
4. Forwarder issues booking confirmation / BL
5. Shipment execution

**Key pain point:** Step 2–3 creates asynchronous email chains that get lost across shifts, causing delayed responses, missed cutoffs, and shipment delays.

## Active Agent Project: FreightBot

**Agent Name:** FreightBot (Freight Control Tower)  
**Platform:** Copilot Studio (Agent Flows)  
**Status:** Phase 1 Demo / Sandbox  
**Environment:** M365 Sandbox — `admin@[sandbox].onmicrosoft.com`

### What FreightBot Does

| Capability | Description |
|---|---|
| Email Triage | Monitors shared mailbox, classifies forwarder emails as exceptions, creates Planner tasks |
| Shift Briefing | "What's my queue?" — open tasks, aged items, high priority count |
| Task Lookup | Find tasks by booking ID or forwarder name |
| Mark Complete | Close a Planner task via chat |
| Exception Summary | Filtered views: high priority / aged >24h / by bucket |

### Exception Buckets

| Bucket | Triggers |
|---|---|
| Missing Info | Shipper/consignee details missing, packing list required, address needed |
| Documentation | Invoice corrections, BoL issues, HS code problems, certificate of origin |
| Clarification | Schedule changes, vessel substitutions, ETD/ETA changes, booking confirmations |

### Priority Logic (Phase 1 — Rule Based)

| Priority | Keywords |
|---|---|
| High | urgent, penalty, demurrage, missed cutoff, hot shipment, expedite, hold, critical, asap |
| Medium | (default — everything else) |

### SLA Thresholds

- Acknowledge: 4 hours
- Resolve: 24 hours
- Escalate: 48 hours
- Business hours: 08:00–18:00 CET, Mon–Fri

## Demo Freight Forwarders

| Forwarder | Region | Demo Email Domain |
|---|---|---|
| Kuehne+Nagel | EMEA | kuehne-nagel-demo.com |
| DHL Freight | Americas | dhl-freight-demo.com |
| Panalpina | EMEA | panalpina-demo.com |
| Geodis | APAC | geodis-demo.com |
| DB Schenker | APAC | db-schenker-demo.com |

## Personas

| Name | Role | Sample Utterances |
|---|---|---|
| Sarah Chen | Team Leader | "Give me the shift briefing", "What's aged?", "Show high priority" |
| Alex Rodriguez | Booking Agent | "Find tasks for BKG-2024-00341", "Mark TASK-003 done" |
| Marcus Webb | Night Shift Agent | "What came in overnight?", "Any urgent exceptions?" |

## Technology Stack

- **Copilot Studio** — Agent Flows, generative AI, Teams channel
- **Microsoft Planner** — Task board ("Freight Booking Exceptions" plan, 3 buckets)
- **Microsoft Outlook** — Shared mailbox trigger
- **Microsoft Teams** — Primary end-user interface
- **Azure OpenAI (via CS)** — GPT-4o for classification and conversational responses

## What NOT to Do in Phase 1

- Do NOT generate SAP/TMS integration code — out of scope
- Do NOT generate automated email reply flows — out of scope Phase 1
- Do NOT use complex intent ML models — keyword rules only
- Do NOT reference Power BI datasets — no dashboard in Phase 1
- Do NOT hardcode tenant IDs, plan IDs, or mailbox addresses
