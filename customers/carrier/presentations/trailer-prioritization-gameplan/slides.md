---
marp: true
theme: microsoft-internal
paginate: true
footer: 'Carrier Trailer Prioritization Phase 1 — Microsoft Confidential'
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Carrier Inbound Trailer Prioritization
## Phase 1 — Call Gameplan

Microsoft Dynamics 365 + Power Automate Solution

<style scoped>
section { background: linear-gradient(135deg, #0B2736 0%, #0F3F5E 100%); }
</style>

---

## Call Objective

**We packaged Phase 1 and need four key data/integration confirmations from Carrier before pilot.**

- Confirm current solution status and deliverables
- Review architecture and pilot readiness
- Walk through decision checklist
- Lock in data owners and timeline

> **Target outcome:** leave with dated checklist and confirmed owners.

---

## Executive Summary

- **Phase 1 artifacts built and packaged** — solution zip ready to import
- **Dataverse model complete** — Trailer, Dock, ScoringConfig, FieldMapping tables
- **Canvas app demo-ready** — 3-screen planner dashboard with override control
- **Scoring engine functional** — OTIF + revenue + readiness algorithm
- **Main dependency: data confirmations** — not build readiness

---

<!-- _class: divider -->

## The Problem We're Solving

---

## Current State: Manual Process

**Every Monday, 6 AM — 12 PM at Carrier**

- Warehouse receives 80–120 trailers from suppliers
- Inbound planners manually rank by OTIF score + revenue impact  
- Assign to Dock 1, Dock 2, or Overflow queue
- Email rough schedule to TSPs (3rd party schedulers) and Kenco receiving

**Risks:**
- ⚠️ Manual ranking errors → SLA breaches
- ⚠️ Capacity overload → $50–80K detention costs
- ⚠️ No standardization across sites
- ⚠️ 6-hour planning window is tight

---

## Proposed Solution

**Automated scoring engine + planner dashboard**

- Ingest SAP in-transit data + supplier OTIF history every Monday 6 AM
- Calculate priority rank (OTIF % + revenue + supplier readiness)
- Auto-assign to dock slots respecting capacity
- Canvas app planner dashboard for review + manual override
- Email TSPs with finalized schedule

**Expected Impact:**
- ✅ Save 6 hours of manual effort per week
- ✅ Reduce SLA breaches by 15–20%
- ✅ Prevent $50K+ detention costs
- ✅ Single source of truth across all sites

---

<!-- _class: divider -->

## What's Built Now — Phase 1

---

<!-- _class: light -->

## Architecture Overview

![w:1000 center](architecture.svg)

**Key components:**
- **Data sources** → SAP In-Transit, 3 SharePoint sites (Excel)
- **Ingestion** → Power Automate workflow (Monday 6 AM trigger)
- **Core model** → Dataverse Trailer, Dock, ScoringConfig, FieldMapping
- **Scoring engine** → Rank all trailers (OTIF + revenue + readiness)
- **Planner UI** → Canvas app (3 screens: Dashboard, Schedule Builder, Comms)
- **Output** → Dock assignments + email to TSP and Kenco

---

## Deliverables — Phase 1 Complete

| Component | Status | Ready to |
|-----------|--------|----------|
| **Dataverse model** | ✅ Complete | Deploy to test org |
| **Canvas app (3 screens)** | ✅ Complete | Demo live |
| **Power Automate flow** | ✅ Complete | Trigger Monday 6 AM |
| **Scoring config** | ✅ Complete | Parametrize |
| **Email templates** | ✅ Complete | Customize branding |
| **Portable solution** | ✅ Complete | Import & test |

---

## Pilot Scope (Proposed)

- **First week:** Dry run (all scoring offline, no live dock assignment)
- **Week 2–4:** Live pilot on Dock 1 only (highest-value trailers)
- **Post-pilot gate:** Confirm SLA improvement, tune scoring weights
- **Rollout:** All docks + all suppliers

---

<!-- _class: divider -->

## Critical Data Dependencies — Your Action Items

---

## Decision 1: Data Ownership & Refresh Cadence

**Question:** Who owns SAP in-transit export?

- Currently proposed: **[Carrier owner name]** pulls Monday 6 AM
- Alternative: E2Open API direct integration (TBD timing)
- Fallback: Manual export (not scalable)

**What we need:** Confirm data owner + confirm weekly export process works

---

## Decision 2: SharePoint Supplier Data — Schema Lock

**Question:** Which 3 SharePoint sites, and are column headers fixed?

- Site 1: [Supplier list site] — columns: Supplier, OTIF%, ReadinessScore
- Site 2: [In-transit site] — columns: TrailerID, ETADate, Origin, Destination
- Site 3: [Historical performance] — columns: SupplierID, OTIFTarget, SLA30Day

**What we need:** Exact URLs + column header screenshots to finalize FieldMapping config

---

## Decision 3: Power BI Backlog Integration (Phase 2)

**Question:** Who owns the Power BI performance backlog?

- Phase 1: Dataverse stores all scoring history (audit trail)
- Phase 2: Optional Power BI dashboard for trending + KPI burndown
- Blocker?: Do we need Power BI live before pilot, or after proof of concept?

**What we need:** Confirm Power BI dependency is *post-pilot*, not pre-pilot

---

## Decision 4: TSP Scheduling Confirmation

**Question:** Which TSP systems do we integrate email schedules into?

- Currently: Email-based (no API)
- Optional Phase 2: API handshake to auto-parse dock assignments
- Confirmation needed: Is current email + manual TSP parse sufficient for pilot?

**What we need:** Confirm email schedule is OK for weeks 1–4, or if API is mandatory pilot blocker

---

<!-- _class: light -->

## Call Timeline (30 Minutes)

| Time | Segment | Owners |
|------|---------|--------|
| **0–5 min** | Context + value brief | Microsoft |
| **5–15 min** | Architecture walk + demo | Microsoft |
| **15–24 min** | Decisions 1–4 | Carrier |
| **24–30 min** | Close + next steps | Both |

---

<!-- _class: divider -->

## Next Steps & Close

---

## Immediate Follow-up (This Week)

1. **Confirm data owners** for all 4 decisions
2. **Share screenshots** (SharePoint column headers, E2Open API docs if applicable)
3. **Sign off on pilot scope** (Dock 1 dry-run week, then live)
4. **Confirm TSP contact** for email & schedule handoff

Once locked, we move to **pilot kickoff checklist** (target: next week)

---

## Pilot Kickoff Checklist (Week 2)

- [ ] Deploy solution to Carrier test org
- [ ] Configure FieldMapping (once column headers confirmed)
- [ ] Load 80 sample trailers into Dataverse
- [ ] Run Monday 6 AM ingestion (dry-run mode, no dock assignment)
- [ ] Walk through Dashboard + Builder UI with planners
- [ ] Tune scoring weights (OTIF % vs revenue %)
- [ ] Confirm email output format with TSPs

---

## Success Metrics (Post-Pilot)

- ✅ All 80+ trailers ranked consistently
- ✅ Manual planner override workflow is smooth (Canvas app)
- ✅ Email schedule delivered to TSPs on-time
- ✅ No data loss or integrity issues in Dataverse
- ✅ SLA projection shows 15%+ improvement

---

<!-- _class: light -->

## Portable Assets in Your Repo

📦 **CarrierTrailerPrioritization.zip**
- Dataverse solution + all flows, canvas app, tables
- Import to any Carrier org, customize as needed

📋 **Engagement Guide**
- Full requirements, design decisions, phase roadmap

🎯 **Demo Script**
- Walk-through sequence for stakeholder demo

---

## Contact & Escalation

| Role | Contact | Async channel |
|------|---------|---------------|
| **Solution Architect** | Microsoft contact | Teams chat |
| **Data Governance** | [Carrier owner] | Email weekly sync |
| **TSP Liaison** | [Carrier TSP lead] | Email + Teams |

---

<!-- _class: title -->

# Questions?

**Let's confirm owners and lock in pilot scope.**

<style scoped>
section { background: linear-gradient(135deg, #0B2736 0%, #0F3F5E 100%); }
</style>

---

## Appendix: Scoring Formula

```
Score = (OTIF% × 0.4) + (Revenue Impact × 0.3) + (Readiness × 0.2) + (Dock Fit × 0.1)

Where:
  OTIF% = Supplier historical on-time delivery percentage
  Revenue Impact = Trailer shipment value in $K
  Readiness = Supplier prep status (0–100%)
  Dock Fit = Dock availability at assigned time window
```

---

## Appendix: Pilot Budget (Estimate)

| Line | Cost | Notes |
|------|------|-------|
| **Dynamics 365 licenses (test org)** | Included | Use trial |
| **Solution deployment + config** | 40 hrs | Data mapping, scoring tuning |
| **Planner training** | 8 hrs | Dashboard + Builder walkthrough |
| **TSP integration testing** | 16 hrs | Email + schedule validation |
| **Total Phase 1 Pilot** | **~$12K** | 4-week engagement |

---

## Appendix: Phase 2 Roadmap (Optional)

- **Power BI dashboard** for trending + KPI burndown
- **E2Open API integration** (if available) to replace SharePoint
- **AI-driven anomaly detection** (trailers flagged for manual review)
- **Kenco receiving dock console** (real-time status + mobile)
- **Multi-site rollout** (replicate model across all Carrier inbound hubs)

- Dataverse schema for trailers, manifests, docks, suppliers, field mapping, scoring config
- Canvas app structure for dashboard, schedule builder, and communications workflow
- Flow specifications for ingestion, scoring, and notification pathways
- Business scoring model for OTIF and revenue-based prioritization
- Importable solution artifact for environment portability

---

<!-- _class: light -->

## Process Flow (Current State To Future State)

Current manual flow:

`SAP + Excel extracts` -> `Backlog report mining` -> `Spreadsheet ranking` -> `Manual dock schedule` -> `Email to Kenco`

Target automated flow:

`SAP/SharePoint ingestion` -> `Dataverse normalization` -> `OTIF + revenue scoring` -> `Auto schedule + override` -> `One-click Kenco notification`

Outcome:

- Faster cycle time
- Consistent prioritization logic
- Auditability and repeatability

---

## Demo Storyline (8 Minutes)

1. Show weekly ranked trailer schedule and KPI framing
2. Explain why top trailer is ranked first (OTIF + revenue drivers)
3. Use Schedule Builder for assignment and auto-schedule sequence
4. Generate/send Kenco communication from app flow
5. Show reschedule handling path and future AI extension
6. Close with phased roadmap (Phase 1 complete, Phase 2/3 extensions)

---

<!-- _class: light -->

## Open Items To Close With Carrier

| Open Item | Owner (Current) | Why It Matters |
|---|---|---|
| E2Open API details | Sonali | Defines integration scope for next phase |
| SAP/Excel header screenshots | Sonali | Needed to finalize ingestion mapping validation |
| SharePoint in-transit file location | Sonali | Needed for productionized ingestion trigger |
| Backlog backend source confirmation | Kevin | Needed for scoring data reliability |
| Updated VSM spreadsheet | Kevin to Samyak | Needed for process baseline and pilot KPIs |

---

## Call Agenda (Recommended)

- 5 min: Reframe problem and business value
- 10 min: Review what is already built and portable
- 10 min: Walk through demo storyline and pilot path
- 10 min: Confirm open items, owners, and dates
- 5 min: Agree immediate next milestone and checkpoint

---

## Specific Asks For This Afternoon

- Confirm pilot environment and target date for solution import
- Confirm data source owners for SAP, SharePoint, and backlog feeds
- Confirm whether E2Open remains Phase 2 versus immediate dependency
- Confirm who signs off on scoring weight defaults for pilot

---

<!-- _class: light -->

## Deliverables You Can Share During The Call

| Deliverable | Location |
|---|---|
| Engagement guide (HTML) | `customers/carrier/docs/carrier-trailer-prioritization-engagement-guide.html` |
| Engagement guide (Markdown) | `customers/carrier/docs/carrier-trailer-prioritization-engagement-guide.md` |
| Demo script | `customers/carrier/demos/carrier_trailer_prioritization_demo.json` |
| D365 project README | `customers/carrier/d365/trailer-prioritization/README.md` |
| Portable solution package | `customers/carrier/d365/trailer-prioritization/solution/CarrierTrailerPrioritization.zip` |

---

<!-- _class: lead -->

## Recommended Close Statement

Phase 1 is packaged and pilot-ready.
The path to execution now depends on closing
five data/integration confirmations with owners and dates.

---

<!-- _class: title -->
<!-- _paginate: skip -->

# Thank You

Carrier Trailer Prioritization | Call Prep Deck
