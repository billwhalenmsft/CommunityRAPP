# Navico

## Engagement Summary

**Customer:** Navico Group — marine electronics (Lowrance, Simrad, B&G, C-MAP, Northstar)
**Demo Type:** Competitive Bake-Off — D365 Customer Service vs. Salesforce Service Cloud
**D365 Sales Demo:** John Kassar
**D365 Customer Service Demo:** Bill Whalen
**Environment:** [Mfg Gold Template](https://orgecbce8ef.crm.dynamics.com)

---

## Demo Focus

**Primary Theme:** *"From basic case management to a fully connected, intelligent service experience."*

Navico already uses D365 CS in a minimal way (case management only). The demo shows them what they're missing:

| Today (Current State) | With Modern D365 CS |
|---|---|
| 1 queue, no routing | Intelligent routing by brand, tier, skill |
| RingCentral — no screen pop | Screen pop with Customer 360 on every call |
| Email + phone only | Email + Chat + Voice — all unified |
| Managers manually categorize cases | Copilot auto-categorizes 89%+ |
| ServiceTarget KB (rusty tech) | Copilot Agent Assist — KB in <10 seconds |
| No analytics | Real-time supervisor insights |
| No WFM | WFM preview available |

---

## Demo Scenarios

### Scenario 1 — Voice: Inbound B2B RMA Request
- **Persona:** Jake Harrington (Purchasing Manager, Atlantic Marine Supply Co.)
- **Channel:** Phone / Voice
- **Story:** Jake calls in about a Simrad NSX 3007 chartplotter (serial SIM-2024-NSX-10042) with a touchscreen failure after a firmware update. Screen pop identifies him as a **Platinum Expert** B2B account. Agent Emma sees customer 360, serial lookup confirms warranty active. Copilot suggests KB-SIM-0042 and recommends RMA Exchange. Case routed to Marco Rossi (Simrad Tier 4 specialist) for approval.
- **Highlights:** Screen pop, Customer 360, serial/warranty lookup, Copilot KB suggestion, intelligent routing

### Scenario 2 — Chat: Platinum Expert EMEA Escalation
- **Persona:** Christine Delacroix (Service Manager, Euro Marine Distributors, London)
- **Channel:** Chat (dealer portal widget)
- **Story:** Christine chats in via the dealer portal — B&G Triton2 showing erratic wind readings with race season 3 days away. Platinum Expert tier auto-bumps queue priority. Copilot surfaces KB-BG-0117 (Triton2 calibration) in seconds. Marco uses suggested reply. Issue needs expert callback — Copilot generates case summary for handoff. Supervisor Sarah sees conversation live.
- **Highlights:** Chat widget, Platinum Expert routing, Copilot agent assist, case summarization, supervisor live view

### Scenario 3 — Email: B2C Consumer Warranty Claim
- **Persona:** Mike Torres (registered consumer, Lowrance HDS-9 Live)
- **Channel:** Email (inbound)
- **Story:** Mike emails support about his Lowrance HDS-9 Live not powering on. AI parses the email, detects warranty claim intent, extracts serial LWR-2024-HDS-88821, validates warranty (active, expires Feb 2027), auto-creates the case, and Copilot drafts the consumer response. Zero manual effort. NPS survey auto-queued on close.
- **Highlights:** AI email triage, auto case creation, serial extraction, Copilot response draft, NPS automation

### Scenario 4 — Supervisor View: Analytics & Queue Intelligence
- **Persona:** Sarah Mitchell (Customer Service Supervisor)
- **Story:** Sarah's dashboard shows 12 active conversations across email/chat/voice, agent utilization, case volume by brand, hot word alerts, and SLA compliance — all the intelligence Navico's manager doesn't have today with a single manual queue.
- **Highlights:** Omnichannel Insights, real-time queue, before/after contrast (37 cases needing manual categories → 3)

---

## Key Customer Context

- **37 CSRs** (repair dept separate), **17 brands** (5 core for demo)
- **Case split:** 52% technical support / 48% warranty & claims
- **RMA types:** Exchange, Credit, Repair, OBS (Onboard Support Request)
- **Customer tiers:** Platinum Expert → Platinum → Gold → Standard → Consumer
- **B2B:** EMEA-strong, distributor/dealer driven. **B2C:** Americas-strong, product registration + warranty focus
- **ERP:** Oracle (US) + Dynamics AX (EMEA) — RMA approval triggers ERP fulfillment line
- **Certification Program:** New in April 2026 — cert requests become D365 cases, status tracked on contact record
- **Hot word examples:** Navigation Failure, Safety, Man Overboard, Emergency

---

## Files

### Config
- `d365/config/environment.json` — Full demo config (brands, tiers, SLAs, personas, scenarios)
- `d365/config/demo-data.json` — Accounts, contacts, product serials, pre-seeded cases

### Data
- `d365/data/hero-cases.json` — 4 hero case scenarios with activity timelines and Copilot highlights
- `d365/data/knowledge-articles.json` — 6 KB articles for Copilot to surface during demo

### Demo Assets (HTML — open in browser)
- `d365/demo-assets/navico_demo_script.html` — Full presenter demo script with timing, talk tracks, objection handling, competitive notes
- `d365/demo-assets/navico_demo_execution_guide.html` — Setup checklist, environment details, scenario quick-reference, fallback options, post-demo next steps

### Scripts
- `d365/Provision-NavicoDemo.ps1` — Base provisioning (accounts, contacts, products, cases)
- `d365/Provision-NavicoHeroCases.ps1` — Hero cases, KB articles, quick responses

---

## Setup Instructions

```powershell
# Step 1: Provision base data (accounts, contacts, products, cases)
cd customers\navico\d365
.\Provision-NavicoDemo.ps1 -Action All

# Step 2: Provision hero cases, KB articles, quick responses
.\Provision-NavicoHeroCases.ps1 -Action All

# Step 3: Validate in D365
# - Check accounts: Atlantic Marine, Euro Marine, Pacific Coast, Gulf Coast, etc.
# - Check cases: 3 hero cases + queue cases
# - Check KB articles: 6 articles published
# - Confirm omnichannel routing configured (manual step in D365 admin)

# Cleanup (if needed)
.\Provision-NavicoDemo.ps1 -Action Cleanup
.\Provision-NavicoHeroCases.ps1 -Action Cleanup
```

---

## Manual D365 Config Required (post-script)

These steps require the D365 Customer Service admin center and cannot be scripted:

1. **Omnichannel workstreams** — configure email, chat, and voice channels with routing rules by brand + tier
2. **Queues** — create brand queues: Simrad Queue, B&G Queue, Lowrance Queue, C-MAP Queue, General Queue
3. **Routing rules** — B2B tier-based routing, brand skill matching, hot word priority boost
4. **Chat widget** — publish chat widget to demo portal page
5. **Voice channel** — configure Teams voice or ACS if doing live voice demo
6. **Copilot features** — enable Case Summary, Draft Email, Agent Assist in CS admin center
7. **Tier field** — verify customer tier field visible on case form (from script 13-TierField.ps1)

---

## Status
- [x] Environment config created
- [x] Demo data configured
- [x] Hero cases designed
- [x] KB articles authored
- [x] Provisioning scripts created
- [x] Demo script HTML generated (`navico_demo_script.html`)
- [x] Execution guide HTML generated (`navico_demo_execution_guide.html`)
- [ ] Scripts run against D365 environment
- [ ] Omnichannel routing configured (manual)
- [ ] Demo walkthrough validated end-to-end
