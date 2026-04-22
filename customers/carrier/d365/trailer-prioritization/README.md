# Carrier Corporation — Inbound Trailer Prioritization

**Customer:** Carrier Corporation (HVAC manufacturer)  
**Use Case:** Automate weekly prioritization of ~190 inbound trailers at Chattanooga warehouse  
**Platform:** Microsoft Power Platform (Canvas App + Dataverse + Power Automate)

---

## Problem Summary

Carrier's aftermarket warehouse has **limited dock space** (dock 1 = 5 slots, dock 2 = 15 slots, overflow = 3).
One materials planning manager manually matches 190 truck manifests against backlog/OTIF data every Monday in spreadsheets.
Process takes hours, is not sustainable, and prevents strategic work.

## Prioritization Business Rules

| Priority | Metric | Data Source |
|----------|--------|-------------|
| 1 | OTIF — # of part numbers on backorder in this trailer | Power BI / SAP open order report |
| 2 | Revenue impact — $ of backlog cleared if received | Power BI |
| 3 | Detention/demurrage cost (Phase 2) | Email from logistics dept |

**Dock assignment logic:**
- Highest-scored trailers → Dock 1 or Dock 2 (capacity 5 + 15 = 20/day)
- Approved suppliers with **no backlog** → Overflow (3 slots)
- Max 8 trailers/day total at Chattanooga

## Data Sources

### Internal (structured)
- **6 SAP factories**: In-transit data via SAP connector (truck#, ship date, materials, qty, carrier)
- **3 non-SAP factories** (Colleyville, Indianapolis, Charlotte): Excel via SharePoint

### External (~40 full-truckload suppliers)
- EDI, E2Open, email packing lists, WoW (international), PDF
- Field names vary by supplier → synonym mapping table required

### Reference Data
- Backlog/revenue: Power BI dataset (backend source TBD)
- Detention costs: Email from logistics (Phase 2)
- TSP contact list: To be built (< 30 contacts)
- Approved overflow suppliers: Config table

---

## Solution Architecture

```
[SAP / SharePoint / Email] 
         ↓
[Power Automate: Ingestion Flow]  (runs Monday 6 AM)
         ↓
[Dataverse: Trailers + Manifests]
         ↓
[Power Automate: Scoring Flow]
  → OTIF score + Revenue score → Composite Trailer Score
         ↓
[Dataverse: Scored Trailer Schedule]
         ↓
[Canvas App / Code App]
  → Planner view, manual overrides, dock assignment
         ↓
[Power Automate: Notification Flow]
  → Email Kenco IB Scheduler with confirmed schedule
```

---

## Deliverables in This Folder

| Folder | Contents |
|--------|----------|
| `dataverse/` | Table schemas (JSON/XML) for import |
| `canvas-app/` | Canvas App YAML source (paste into Power Apps Studio) |
| `code-app/` | React + TypeScript Code App (scaffold) |
| `flows/` | Power Automate flow definitions (JSON for import) |
| `solution/` | Power Platform solution.xml for portable deployment |

---

## Deployment

### Prerequisites
- Power Platform environment with Dataverse enabled
- Power Apps Premium license for end users
- Power Automate Premium (for SAP / custom connectors)
- SAP connector configured in environment

### Canvas App
1. Open Power Apps Studio
2. New app → From YAML
3. Paste contents of `canvas-app/Screens/*.yaml`

### Code App
```bash
cd code-app
npm install
npm run dev        # local dev
npm run deploy     # deploy to Power Apps
```

#### Demo Data Profile (Local Dev)
- The code app currently uses a seeded mock dataset of **16 trailers** in `src/App.tsx`.
- The sample intentionally mixes statuses (`Scheduled`, `Confirmed`, `Unscheduled`, `Rescheduled`, `Overflow`) so KPI, exceptions, and dock timeline views are populated.
- If you only see 1-2 trailers, restart the Vite preview/dev server to ensure the latest bundle is loaded.

### Solution Import
```bash
pac solution import --path solution/CarrierTrailerPrioritization.zip
```

---

## Phased Roadmap

| Phase | Scope |
|-------|-------|
| **1 (MVP)** | SAP + SharePoint ingestion, OTIF + Revenue scoring, Canvas App schedule view |
| **2** | Detention cost data, Code App upgrade, E2Open integration |
| **3** | AI Builder for supplier packing list normalization + TSP reschedule email parsing |
| **4** | Inventory Pooling use case |
