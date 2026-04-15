# GE ERAC — Lite CRM Project

## Customer Overview
**Customer:** GE Verisk ERAC (Enterprise Risk & Advisory Consulting)  
**Teams:** Claims Operations, Actuarial, Legal, Risk  
**Initiative:** Finance Transformation – Engagement Model Development & Ops Integration (Lite CRM)

## What's Built (Phase 1)

A single-file, browser-based Lite CRM demo app covering the core ERAC requirements.

**Open the app:**
```
customers/ge_erac/crm/demo-assets/erac_lite_crm.html
```
No server required — open directly in any browser.

**Tabs included:**
| Tab | Requirements Covered |
|-----|----------------------|
| 🏢 Cedents & Contacts | C-003, C-017, §4.1.4 (360° contact view) |
| 📋 Engagement Log | C-001, C-002, C-004 (Copilot meeting summaries) |
| 📊 Partnership Dashboard | PRR-001–010, Exhibit 4.1.1 |
| ⚠️ Risk Assessment | ERAC-011–019, Exhibit 4.1.2 |
| 📌 Engagement Kanban | SP-020–027, Exhibit 4.1.3 |
| 📈 Power BI Reports | C-007, C-010, C-011 |

**Optional Copilot sidebar:** Start `func start` locally, then the right-side chat panel connects to the Azure Function endpoint.

## Folder Structure
```
customers/ge_erac/
├── README.md                         ← this file
└── crm/
    ├── demo-assets/
    │   └── erac_lite_crm.html        ← main demo app
    ├── data/
    │   └── mock_data.json            ← cedents, contacts, assessments, tasks
    └── docs/
        ├── ERAC_Requirements_DRAFT.md ← full requirements document
        └── project_tracker.json       ← GitHub Project ID + issue numbers
```

## GitHub Project
**Project:** [GE ERAC – Lite CRM](https://github.com/users/billwhalenmsft/projects/13)  
**Repo:** `billwhalenmsft/CommunityRAPP-BillWhalen`  
**Label:** `area:erac`

## Phase 2 Scope (Not Yet Built)
- [ ] Actuarial tab — reserving analytics, experience studies, assumption traceability (req A-001–A-013)
- [ ] Legal tab — treaty contract tracking, legal positions, arbitration dashboard (req L-001–L-011)
- [ ] IronClad integration — read-only treaty/contract data surfaced in CRM views
- [ ] Dataverse backend — Account, Contact, Task/Notes entities replacing mock data
- [ ] Project Sherlock legacy data migration (req CF-01–CF-18)
- [ ] Power Automate workflows for cross-team routing
- [ ] Copilot Studio agent deployment over Dataverse data
