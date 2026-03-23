# Carrier Corporation — Inbound Trailer Prioritization
## SE Engagement Guide (Start Here If You Know Nothing)

**Customer:** Carrier Corporation — Global HVAC/refrigeration manufacturer  
**Use case:** Aftermarket warehouse trailer scheduling automation  
**Platform:** Microsoft Power Platform (Canvas App + Dataverse + Power Automate)  
**Environment:** Mfg Gold Template (`https://org6feab6b5.crm.dynamics.com`)  
**Solution:** `CarrierTrailerPrioritization` (deployed, unmanaged)

---

## The 60-Second Brief

Carrier's aftermarket division ships HVAC parts to service technicians and dealers. Their warehouse in **Chattanooga, TN** (operated by a 3PL called Kenco) receives **~190 inbound trailers per week** — but only has **dock space for 20 trailers per day**.

That means **someone has to decide which 20 trucks get in first, every day, every week**.

Today, that "someone" is **Sonali Horan**, the RC Materials Planning Manager. Every Monday morning she:
1. Pulls an in-transit report from SAP (and Excel for 3 non-SAP factories)
2. Pulls a backlog report from Power BI
3. Manually cross-references which trucks carry the most backlogged parts
4. Builds a prioritized schedule in a spreadsheet
5. Emails the schedule to the Kenco inbound scheduler

**This takes ~6 hours and is not sustainable.** One person doing this manually, with no automation, no scoring logic, and no audit trail.

**What we built:** A Power Platform app that does all of this automatically. SAP data flows in → scoring engine ranks every trailer by OTIF + revenue impact → Canvas App lets Sonali review and override → one button sends the schedule to Kenco.

---

## Who You'll Be Talking To

| Person | Role | What They Care About |
|--------|------|---------------------|
| **Sonali Horan** | RC Materials Planning Manager | Time savings, OTIF improvement, sustainable process |
| **Kevin Gollmer** | Materials Director | Revenue clearance speed, strategic vs. tactical work |
| **Samyak Jain** | IT Lead | Maintainability, Power Platform complexity, integration with SAP |
| **Lucas Skaf** | IT Lead | Technical feasibility, future E2Open integration |
| **Sumit Katyal** | Sponsor (exec) | ROI, organizational impact |

---

## The Business Problem (In Carrier's Own Words)

> *"Challenge: time consuming. It's very tactical. Too much data mining. Not a sustainable process for one person. It takes away time from strategic work."*
> — Sonali Horan, discovery call

> *"Automation would save time, improve alignment with business opportunities, increase OTIF, accelerate revenue clearance, and enhance customer satisfaction."*
> — Kanika Ramji, Microsoft PM

---

## Key Terminology You Need to Know

**OTIF (On Time In Full)**  
Carrier's #1 supply chain metric. Did the customer's order arrive complete and on time? A trailer with 47 parts on backorder means 47 customers are waiting. Getting that trailer in first directly improves OTIF.

**Backlog**  
Customer orders that can't ship because the warehouse doesn't have the inventory. The backlog count and revenue value are the primary scoring inputs.

**Composite Score**  
Every trailer gets a score: `(OTIF weight × OTIF score) + (Revenue weight × Revenue score)`. Default: 50% OTIF, 40% revenue, 10% detention. Fully configurable.

**Dock 1 / Dock 2 / Overflow**  
The three receiving areas at Kenco's Chattanooga facility.
- Dock 1: 5 trailers/day capacity (highest-priority trailers)  
- Dock 2: 15 trailers/day capacity (bulk of the schedule)  
- Overflow: 3 trailers/day (approved suppliers with low/zero backlog)

**TSP (Transportation Service Provider)**  
The ~30 trucking companies moving Carrier's trailers. They email the Kenco inbound scheduler to reschedule when something goes wrong (mechanical issues, weather, etc.)

**Kenco IB Scheduler**  
The person at the 3PL (Kenco) who books the actual dock appointments. Sonali sends them the weekly priority schedule, and they coordinate timing with the TSPs.

**E2Open**  
An external logistics scheduling platform Carrier uses. Not integrated yet — Phase 2/3 target.

**Detention/Demurrage**  
Fees Carrier pays when a trailer sits in a yard without being unloaded on time. Adds cost pressure to bring in certain trailers faster. Phase 2 scoring input.

---

## What's Actually Built (Right Now, Live)

### Dataverse Tables (in Mfg Gold Template)
| Table | What It Stores |
|-------|---------------|
| `carr_Trailer` | One row per inbound trailer: OTIF score, revenue, dock assignment, schedule status |
| `carr_ManifestLine` | Parts on each trailer: part#, qty, backorder status |
| `carr_Dock` | Dock capacities (seeded: 5/15/3) |
| `carr_Supplier` | Factory/supplier contacts and data source format |
| `carr_FieldMapping` | Maps supplier-specific column names to standard fields |
| `carr_ScoringConfig` | Scoring weights (default: OTIF 50%, Revenue 40%, Detention 10%) |

### Canvas App (3 Screens — YAML ready to paste)
| Screen | What It Does |
|--------|-------------|
| **Trailer Dashboard** | KPI cards + ranked gallery of all 190 trailers with scores |
| **Schedule Builder** | Dock capacity view + assign/auto-schedule interface |
| **Communications** | Auto-draft email to Kenco, TSP contact list, reschedule log |

### Power Automate Flows (spec in `flows/flows.yaml`)
| Flow | When It Runs |
|------|-------------|
| Ingestion | Every Monday 6 AM — pulls SAP + SharePoint data |
| Scoring | After ingestion — calculates OTIF + revenue, ranks all trailers |
| Notification | On demand — sends confirmed schedule to Kenco |
| Reschedule Watcher | Phase 2 — AI reads TSP email, auto-updates schedule |

---

## Demo Flow (8 Minutes)

> **Full step-by-step script in:** `demos/carrier_trailer_prioritization_demo.json`

**Quick version:**

1. **"Show me this week's schedule"** → ranked table of 190 trailers with scores
2. **"Why is TMS-4821 #1?"** → scoring breakdown: 47 OTIF parts, $128K revenue
3. **Assign to Dock 2** → one click, confirmed
4. **Auto-schedule all** → 190 trailers assigned in priority order, instantly
5. **Send to Kenco** → one button drafts + sends the email
6. **Log a reschedule** → TSP can't make it, system reassigns the slot

**Time saved in demo:** What took Sonali 6 hours every Monday now takes 8 minutes.

---

## What To Say When...

**"We already have a process."**  
> "Sonali told us the current process isn't sustainable for one person and takes 6 hours every Monday. This doesn't replace her judgment — it does the data mining for her so she can focus on strategic work."

**"How does this connect to SAP?"**  
> "Power Automate has a native SAP connector. Once Samyak configures the credentials, the Monday morning ingestion runs automatically. The 3 non-SAP factories send Excel — that flows in from SharePoint."

**"What about our 800 external suppliers?"**  
> "Phase 1 handles your 40 full-truckload suppliers — the ones that matter for this use case. The Field Mapping table normalizes their different column names automatically. Phase 3 adds AI Builder for the truly unstructured formats."

**"Can we pilot this first?"**  
> "Yes — it's already live in a Mfg Gold Template environment. We have a portable solution zip that imports to any Power Platform environment. Samyak can validate the data against your real SAP for one week before going live."

**"Who maintains this?"**  
> "Very little maintenance required. The scoring weights are in a config table — no code. Adding a new supplier or dock is a row in Dataverse. Power Automate handles the scheduling. Samyak estimated he could own this with his current skills."

---

## Open Items / Follow-Ups from Discovery

From Samyak's meeting recap (March 20, 2026):

| Item | Owner | Status |
|------|-------|--------|
| E2Open API details | Sonali | Pending — she's reaching out to their contact |
| SAP/Excel column headers screenshot | Sonali | Pending — promised via email post-call |
| SharePoint in-transit Excel location | Sonali | Verify if still managed |
| Power BI backend data source for backlog | Kevin | Pending — needed for scoring flow |
| Updated VSM spreadsheet | Kevin | Share with Samyak |
| Inventory Pooling use case | Kanika | Separate track |

---

## How to Import the Solution to a Different Environment

```bash
# Install PAC CLI if not already installed
npm install -g @microsoft/powerplatform-cli

# Auth to target environment
pac auth create --url https://yourorg.crm.dynamics.com

# Import the solution
pac solution import --path d365/carrier-trailer-prioritization/solution/CarrierTrailerPrioritization.zip
```

---

## Files in This Engagement

| File | Location |
|------|----------|
| This guide | `docs/carrier-trailer-prioritization-engagement-guide.md` |
| Demo script | `demos/carrier_trailer_prioritization_demo.json` |
| Agent JSON | `demos/carrier_trailer_prioritization_agent.json` |
| Solution zip | `d365/carrier-trailer-prioritization/solution/CarrierTrailerPrioritization.zip` |
| Canvas App YAML | `d365/carrier-trailer-prioritization/canvas-app/Screens/` |
| Code App | `d365/carrier-trailer-prioritization/code-app/` |
| Flow specs | `d365/carrier-trailer-prioritization/flows/flows.yaml` |
| Dataverse schema | `d365/carrier-trailer-prioritization/dataverse/schema.yaml` |
| Full README | `d365/carrier-trailer-prioritization/README.md` |
