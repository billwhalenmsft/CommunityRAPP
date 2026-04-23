# Use Case: Freight Booking Email Control Tower with Task-Based Exception Management

## Customer Outcome
**Delivers:** A conversational AI agent that transforms inbound freight forwarder exception emails into structured, prioritized Planner tasks — giving booking agents instant shift visibility and eliminating manual email triage.  
**Scenario:** TE Connectivity — Logistics/Transportation Operations team handling daily freight booking exceptions from freight forwarders globally.  
**Success metric:** Reduce mean-time-to-acknowledge freight exceptions from >4 hours (inbox buried in email) to <15 minutes (task surfaced in Planner with priority and due date). Demo shows 5 sample exceptions auto-triaged in one shift briefing.

---

## Customer Context

**Company:** TE Connectivity Ltd  
**Industry:** Electronic Components Manufacturing / Global Supply Chain  
**Primary Users:** Booking Agents and Team Leaders in the Transportation Operations Center  
**Environment:** M365 / Teams / Microsoft 365 Copilot  
**Phase:** Phase 1 — Demo/Sandbox (no live SAP/TMS integration)

---

## Problem Statement

TE Connectivity's transportation team receives dozens of freight forwarder exception emails daily to a shared `admin@` inbox. These emails contain:
- **Missing information requests** — forwarder needs additional shipping details
- **Documentation corrections** — incorrect or missing shipping documents (BoL, commercial invoice, packing list)
- **Booking clarifications** — schedule changes, carrier substitutions, port of loading conflicts

Today's process is entirely manual:
1. A team member monitors the inbox
2. Reads and manually categorizes each email
3. Creates an ad-hoc note, Teams message, or email thread to track the exception
4. Another team member picks it up (or it's forgotten overnight)

**Pain points:**
- No single source of truth for open exceptions
- Exception ownership is unclear
- No aging/SLA visibility until a forwarder escalates
- Night/weekend shift gaps cause missed handoffs
- Manual classification errors lead to wrong bucket routing

---

## Solution Architecture

### Automation Layer: Copilot Studio Agent Flow

**Trigger:** New email arrives in `admin@` demo mailbox (Office 365 Outlook connector)

**AI Classification Logic (MVP — keyword/rule engine + CS Generative AI):**
```
HIGH priority keywords:  urgent, delay, penalty, demurrage, missed cutoff, hot shipment, expedite
MEDIUM priority:         default if no high-priority keywords detected

Exception Type Buckets:
  Missing Info       →  keywords: missing, required, need, provide, confirm, please send
  Documentation      →  keywords: document, invoice, packing list, BoL, bill of lading, customs, certificate
  Clarification      →  keywords: clarify, confirm booking, schedule change, carrier, vessel, departure, ETD, ETA
```

**Planner Task Created:**
- Title: `[Subject Line] — [Forwarder Name]`
- Description: Email body snippet (first 500 chars) + parsed Booking/Shipment ID
- Priority: High (2) or Medium (5) — Planner numeric priority
- Due date: +24 hours from email received
- Bucket: `Missing Info` / `Documentation` / `Clarification` (maps to Planner bucket names)
- Plan: "Freight Booking Exceptions" (dedicated plan to be provisioned)

### Conversational Interface: 5 Copilot Studio Topics

| Topic | Trigger | Description |
|---|---|---|
| ShiftStartBriefing | "What's my exception queue?" | Returns open task counts by age and priority + top 5 list |
| TaskLookup | "Find tasks for booking [ID]" | Searches Planner by booking ID or forwarder name |
| MarkTaskComplete | "Mark task [ID] as done" | Updates Planner task status to complete |
| ExceptionSummary | "Show me all high priority exceptions" | Filtered views (high priority, aged, by bucket) |
| Help | "What can you do?" | Onboarding and capability guide |

---

## Technical Constraints (Phase 1)

- ✅ Copilot Studio Agent Flows (NOT standalone Power Automate)
- ✅ M365 connectors only: Outlook (email trigger), Microsoft Planner (CRUD)
- ✅ Standard M365 tooling — no external services or SAP/TMS
- ❌ No automated email replies (Phase 2)
- ❌ No SAP/TMS integration (Phase 2)
- ❌ No Power BI integration (Phase 2)

---

## Agent Persona

- **Name:** FreightBot / Freight Control Tower
- **Display Name:** Freight Control Tower
- **Tone:** Professional, logistics-focused, concise
- **Primary Users:** Booking Agents and Team Leaders

---

## Demo Setup Requirements

1. Email inbox: `admin@` demo mailbox (M365 sandbox tenant)
2. Planner plan: "Freight Booking Exceptions" — create with 3 buckets: Missing Info, Documentation, Clarification
3. 5 sample freight forwarder emails (see demo JSON for scenarios)
4. Agent deployed in Teams or Copilot Studio test canvas

---

## Sample Freight Forwarder Emails (for demo seeding)

### Email 1 — Missing Info (High Priority)
**From:** dispatch@kuehne-nagel-demo.com  
**Subject:** URGENT — Missing shipper address for BKG-2024-00341  
**Body:** Dear team, we are unable to proceed with booking BKG-2024-00341 for shipment TE-SHP-112233 departing Rotterdam next Tuesday. We are MISSING the complete shipper address and contact details. This will cause a missed vessel cutoff with penalty demurrage charges if not resolved by 17:00 CET today. Please provide immediately.

### Email 2 — Documentation (Medium Priority)
**From:** ops@dhl-freight-demo.com  
**Subject:** Commercial Invoice correction needed — BKG-2024-00298  
**Body:** Hi, the commercial invoice for booking BKG-2024-00298 has an incorrect HS code for the connector assemblies. The customs broker has flagged this and will not clear until corrected. Shipment ID TE-SHP-109876. Please send corrected invoice document at your earliest convenience.

### Email 3 — Clarification (Medium Priority)
**From:** bookings@panalpina-demo.com  
**Subject:** Schedule change — please confirm BKG-2024-00355  
**Body:** Please clarify the new departure date for booking BKG-2024-00355. The original vessel MSC AMBRA has been substituted with MSC ELISA with ETD now 14-Nov instead of 11-Nov. Do you wish to keep the booking or transfer to the next departure? Booking ref: TE-SHP-113344.

### Email 4 — Missing Info (Medium Priority)
**From:** freight@geodis-demo.com  
**Subject:** Packing list required for BKG-2024-00317  
**Body:** We require the packing list for shipment TE-SHP-110045, booking BKG-2024-00317. This is needed before we can complete the customs declaration. Please provide asap.

### Email 5 — Documentation (High Priority)
**From:** escalations@db-schenker-demo.com  
**Subject:** URGENT — Certificate of Origin missing — BKG-2024-00322 — HOLD  
**Body:** URGENT: Shipment TE-SHP-110567 (booking BKG-2024-00322) is currently on HOLD at the port of Shanghai because the Certificate of Origin is missing. A penalty fee will be applied for each day of delay. This is a critical shipment for a key customer. Please expedite the Certificate of Origin immediately.

---

## RAPP Pipeline Steps Applied

- [x] Step 1: Discovery — Use case defined (this document)
- [x] Step 2: MVP Poke — Scope constrained to M365 tooling, Planner, Phase 1
- [x] Step 6: Agent Code Generated (freight_booking_agent.py)
- [x] Step 8: Demo JSON (freight_booking_demo.json)
- [x] Step 9: Agent Tester HTML (agent_tester.html)
- [x] Step 10: Copilot Studio YAML Topics (transpiled/)
- [ ] Step 11: Deployment (requires M365 sandbox tenant access)
- [ ] Step 14: Customer Sign-Off
