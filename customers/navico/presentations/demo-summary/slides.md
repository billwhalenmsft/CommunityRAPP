---
marp: true
theme: microsoft-internal
paginate: true
footer: 'Microsoft Confidential'
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Navico Group — D365 Customer Service
## Competitive Demo Summary & Engagement Blueprint

---

<!-- _class: divider -->

# Discovery Summary

---

## Navico Group — Who They Are

- **World's leading marine electronics company** — 17 brands, 5 core
- **Simrad** — blue-water cruising, commercial, superyachts
- **Lowrance** — freshwater fishing, bass boats, kayak
- **B&G** — sailing, racing, performance cruising
- **C-MAP** — cartography across all segments
- **Northstar** — legacy navigation systems

**37 CSRs** | **52% Technical Support** | **48% Warranty & RMA**

---

## Current State — The Challenge

| Area | Today | Pain Point |
|------|-------|-----------|
| **CRM** | Salesforce (Sales) + D365 CS (basic case mgmt) | Two systems, no consolidation |
| **Channels** | Email, Phone (Ring Central), Portal | No ring pop, no chat, no digital channels |
| **Self-Service** | Optimizely portal (no AI, no agents) | Zero deflection capability |
| **Routing** | 1 queue, manual pick logic | No intelligent routing, no skills matching |
| **Knowledge** | ServiceTarget (Q&A format) | "Rusty tech" — no AI, no Copilot |
| **WFM** | None | No workforce management |
| **RMA** | Manual → ERP (Oracle US / AX EMEA) | No automation, TS approval bottleneck |

---

<!-- _class: divider -->

# What We Demonstrated

---

## Demo Scenarios — A Day at Navico Support

| # | Scenario | Channel | Brand | Key Features Shown |
|---|----------|---------|-------|-------------------|
| 1 | Inbound voice — screen pop + Copilot | Voice | Simrad | Call pop, customer 360, Copilot summarize |
| 2 | Email triage — intelligent routing | Email | B&G | Auto-classification, Agent Assist, KB surface |
| 3 | Live web chat — suggested replies | Chat | B&G | Portal chat, Copilot replies, escalation |
| 4 | RMA warranty case — serial lookup | Case | Lowrance | Equipment screen, warranty validation, RMA |
| 5 | Portal self-service — AI agent | Portal | All | Troubleshoot, warranty, registration, certification |
| 6 | Competitive positioning & next steps | — | — | Salesforce comparison, value summary |

---

<!-- _class: light -->

## Architecture — Omnichannel + Copilot

```
           ┌──────────────┐
           │   Customer    │
           └──────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
  Voice        Email         Portal
 (Ring Central) (D365)    (Power Pages)
    │             │             │
    └─────────────┼─────────────┘
                  │
         ┌────────▼────────┐
         │  Omnichannel     │
         │  Unified Routing │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
  Brand         Tier         Intent
  Queues       Priority     Detection
    │             │             │
    └─────────────┼─────────────┘
                  │
         ┌────────▼────────┐
         │   CSR Workspace  │
         │  + Copilot Assist│
         └─────────────────┘
```

---

## Channel Expansion — Before & After

| Capability | Current (Salesforce + Basic D365) | With D365 CS Omnichannel |
|-----------|----------------------------------|--------------------------|
| Voice | Ring Central (no screen pop) | **Integrated voice + screen pop** |
| Email | Basic case creation | **Intelligent routing + Agent Assist** |
| Chat | ❌ None | **Live chat from portal + Copilot replies** |
| SMS | ❌ None | **SMS channel available** |
| Self-Service | ❌ No AI, no agents | **Copilot Studio agent on portal** |
| Social | ❌ None | **Facebook, Twitter, WhatsApp ready** |

---

<!-- _class: divider -->

# Key Differentiators

---

## Copilot Agent Assist — AI for Every Interaction

**What the CSR sees in real-time:**

- 🧠 **Intent Detection** — automatically identifies what the customer needs
- 📚 **KB Article Suggestions** — surfaces the right SOP based on conversation context
- ✍️ **Draft Responses** — Copilot writes suggested email/chat replies
- 📝 **Case Summarization** — one-click summary of the entire interaction history
- 🔍 **Similar Cases** — finds related cases for resolution patterns

**14 Navico KB articles** configured and linked to 10 customer intents

---

## Self-Service Portal Agent — 60% Deflection

**Navico Self-Service Assistant** (Copilot Studio)

| Capability | What It Does |
|-----------|-------------|
| 🔧 Troubleshoot | Serial → issue type → guided diagnostics → resolve or escalate |
| 📋 Warranty Check | Serial → coverage details → next steps |
| 🔄 RMA Guidance | Explains Exchange/Credit/Repair/OBS → escalates to process |
| 📝 Registration | Collects serial + purchase + installer → activates warranty |
| 🎓 Certification | B2B dealer cert: check/enroll/renew/learn |
| 🚨 Safety Override | Distress keywords → immediate escalation, zero troubleshooting |

**Context carries over** — when escalated, the live agent sees the full bot transcript

---

## Brand-Aware Routing — 17 Brands, 1 Platform

**Serial number intelligence:**

| Prefix | Brand | Typical Products |
|--------|-------|-----------------|
| SIM- | Simrad | NSX MFD, HALO Radar, Autopilots |
| LWR- | Lowrance | HDS Live, Elite FS, Ghost Motor |
| BG- | B&G | Triton2, Zeus MFD, H5000 |
| CMAP- | C-MAP | Charts, Embark, DISCOVER X |
| NST- | Northstar | Legacy navigation |

**One serial number** → identifies brand, product, warranty, customer tier, and queue

---

## Customer Tier Routing

| Tier | SLA | Routing | Escalation |
|------|-----|---------|-----------|
| **Platinum Expert** | 2 hours | Direct to brand specialist | Tier 4 access |
| **Platinum** | 4 hours | Brand queue → Tier 2 | Tier 3 on request |
| **Gold** | 4 hours | Brand queue → Tier 2 | Standard path |
| **Silver** | 8 hours | General queue → Tier 1 | Standard path |
| **B2C Consumer** | 24 hours | Consumer queue | Tier 1 → Tier 2 |

**Hot words** (Safety, Man Overboard, Navigation Failure) → **immediate Tier 4 regardless of tier**

---

<!-- _class: divider -->

# Competitive Positioning

---

<!-- _class: light -->

## D365 Customer Service vs Salesforce Service Cloud

| Capability | Salesforce Service Cloud | D365 Customer Service |
|-----------|------------------------|----------------------|
| CRM Integration | Separate Sales + Service | **Unified with D365 Sales (John's demo)** |
| Omnichannel | Add-on (Digital Engagement) | **Included in license** |
| Copilot / AI | Einstein (separate SKU) | **Copilot included** |
| Knowledge | Salesforce Knowledge | **Integrated KB + Copilot search** |
| Voice | Requires partner CTI | **Native voice channel** |
| Self-Service Bot | Einstein Bots (limited) | **Copilot Studio (full gen AI)** |
| Power Platform | ❌ No equivalent | **Power Automate, Power Pages, Power BI** |
| ERP Integration | Custom connectors | **Native D365 Finance/AX integration** |
| Licensing | Per-user, per-channel add-ons | **Already owned — expand, don't buy new** |

---

## The Value Story

### 💰 Cost Avoidance
- Navico **already owns D365 licenses** — no new platform purchase
- Consolidate from Salesforce Service → D365 CS = **license savings**
- ERP integration with existing Dynamics AX (EMEA) is **native**

### 📈 Operational Impact
- **60% self-service deflection** potential (per Natalia's estimate)
- **Intelligent routing** replaces manual pick from 1 queue → brand-specific queues
- **Copilot Agent Assist** reduces average handle time

### 🔮 Future-Ready
- Customer Intent Agent for proactive routing
- Power Automate for ERP write-back (RMA → Oracle/AX)
- Asset management + product registration automation
- Certification tracking integrated into support routing

---

<!-- _class: divider -->

# Recommended Next Steps

---

## Proposed Engagement Path

| Phase | Focus | Timeline |
|-------|-------|----------|
| **Phase 1** | Omnichannel setup — Email + Voice + Chat routing | Sprint 1-2 |
| **Phase 2** | Copilot Agent Assist + KB build-out | Sprint 2-3 |
| **Phase 3** | Portal self-service agent (Copilot Studio) | Sprint 3-4 |
| **Phase 4** | RMA automation + ERP integration | Sprint 4-6 |
| **Phase 5** | Advanced — Intent Agent, WFM, Analytics | Ongoing |

### Immediate Actions
1. **Technical deep-dive** on routing configuration for 17 brands
2. **KB migration plan** from ServiceTarget → D365 Knowledge Management
3. **Portal assessment** — Power Pages vs Optimizely migration path
4. **Integration architecture** — Oracle (US) + Dynamics AX (EMEA) + D365 CS

---

<!-- _class: title -->
<!-- _paginate: skip -->

# Thank You

**Bill Whalen** — Customer Service Demo
**John Kassar** — D365 Sales Demo

Navico Group — Dynamics 365 Customer Service
