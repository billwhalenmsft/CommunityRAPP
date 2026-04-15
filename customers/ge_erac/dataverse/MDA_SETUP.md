# ERAC Lite CRM — Model Driven App Setup Guide

## What We're Building

A **Model Driven App** in Power Apps that surfaces the same 8 tabs as the HTML Lite CRM, but:
- Backed by real Dataverse tables (no mock data)
- Native MDA chrome, navigation, and forms
- Filtered to only show ERAC cedents via `erac_iscedent = true`
- Copilot Studio agent wired to the same Dataverse data

---

## Prerequisites

1. Power Platform environment with Dataverse
2. System Administrator or System Customizer role
3. `az login` completed (for provisioning scripts)
4. Solution publisher prefix `erac` created in your environment

---

## Step 1: Provision Schema + Data

```powershell
cd customers/ge_erac/dataverse/scripts

# Full run (schema + demo data)
.\Provision-EracDataverse.ps1 -OrgUrl "https://YOUR-ORG.crm.dynamics.com"

# Schema only (if already seeded data)
.\Provision-EracDataverse.ps1 -OrgUrl "https://YOUR-ORG.crm.dynamics.com" -Phase Schema

# Data only (if schema already exists)
.\Provision-EracDataverse.ps1 -OrgUrl "https://YOUR-ORG.crm.dynamics.com" -Phase Data

# Preview without changes
.\Provision-EracDataverse.ps1 -OrgUrl "https://YOUR-ORG.crm.dynamics.com" -WhatIf
```

This creates:
- Custom columns on `account`, `contact`, `task`, `appointment`
- 5 custom tables (Partnership Rating, Risk Assessment, Treaty, Reserve Adequacy, Dispute)
- 6 demo cedent accounts tagged with `erac_iscedent = true`
- 13 demo contacts linked to cedents

---

## Step 2: Create Filtered Views

In make.powerapps.com → Tables → Account → Views:

### "ERAC Cedents — Active" view
| Setting | Value |
|---------|-------|
| Filter | `Is Reinsurance Cedent = Yes` AND `Status = Active` |
| Columns | Name, Partnership Type, Tier, PRR Rating, Portfolio %, Last QBR, Rating Trend |
| Sort | PRR Overall Rating (Descending) |
| **Set as default** | Yes |

### "ERAC Contacts" view (on Contact table)
| Setting | Value |
|---------|-------|
| Filter | Related Account → `Is Reinsurance Cedent = Yes` |
| Columns | Full Name, Account, Job Title, Function, Contact Tier, Preferred Channel |

Repeat for each custom table — no filter needed (they only contain ERAC data).

---

## Step 3: Create the Model Driven App

In make.powerapps.com → Apps → New App → Model Driven:

**App name:** `ERAC Lite CRM`  
**Solution:** `ERACLiteCRM`

### Sitemap (Navigation)
```
ERAC CRM
  ├── Cedents & Contacts
  │     ├── Cedents          → Account (view: ERAC Cedents — Active)
  │     └── Contacts         → Contact (view: ERAC Contacts)
  ├── Engagement
  │     ├── Engagement Log   → Appointment
  │     └── Kanban Tasks     → Task
  ├── Risk & Partnership
  │     ├── Risk Assessments → erac_riskassessment
  │     └── PRR Ratings      → erac_partnershiprating
  ├── Actuarial
  │     └── Reserve Adequacy → erac_reserveadequacy
  ├── Legal
  │     ├── Treaties         → erac_treaty
  │     └── Disputes         → erac_dispute
  └── Analytics
        └── Portfolio Dashboard → (Power BI Dashboard or Custom Page)
```

---

## Step 4: Custom Pages (replacing HTML tabs)

Some panels don't have a native MDA equivalent and stay as **Custom Pages**:

| HTML Tab | MDA Approach |
|----------|-------------|
| Cedents & Contacts | Native MDA view (Account) |
| Engagement Log | Native MDA (Appointment + Timeline) |
| Partnership Dashboard (PRR) | Custom Page — Chart.js or Power BI |
| Risk Assessment | Native MDA form (erac_riskassessment) |
| Kanban | Native MDA Kanban view (Task with erac_kanbanstage) |
| Actuarial | Native MDA form (erac_reserveadequacy) |
| Legal | Native MDA form (erac_treaty + erac_dispute) |
| Portfolio Analytics | Custom Page or Power BI embedded |

Custom Pages use the `d365-embedded` UX profile — see `skills/ux-profiles/d365-embedded.json`.

---

## Step 5: Wire Copilot Studio Agent

1. Create a Copilot Studio agent in the same environment
2. Connect it to Dataverse via built-in connector (no custom API needed)
3. Add topics matching the existing `getFallbackResponse()` keyword branches
4. Surface in MDA via the **Copilot pane** in app settings

This replaces the HTML panel's fallback AI with a real agent reading live Dataverse data.

---

## Filtering Reference

All OData queries from Azure Function or Power Automate must include:
```
$filter=erac_iscedent eq true
```

Example — Get all active cedents:
```
GET /api/data/v9.2/accounts?$select=accountid,name,erac_partnershiptype,erac_tier,erac_overallrating&$filter=erac_iscedent eq true and statecode eq 0&$orderby=erac_overallrating desc
```

Example — Get contacts for ERAC cedents:
```
GET /api/data/v9.2/contacts?$select=contactid,fullname,jobtitle,erac_function&$filter=parentcustomerid/erac_iscedent eq true and statecode eq 0
```

---

## File Map

```
customers/ge_erac/dataverse/
  config/
    schema.json               ← Complete table/column/view/sitemap definitions
  scripts/
    Provision-EracDataverse.ps1  ← Main provisioner (schema + data)
  data/
    demo-accounts.json        ← 6 cedents + 13 contacts seed data
    account-ids.json          ← Generated after provisioning (GUID map)
  solution/
    (reserved for solution ZIP export)
  MDA_SETUP.md               ← This file
```

---

*Owner: Bill Whalen, Microsoft SE — GE ERAC Finance Transformation*
