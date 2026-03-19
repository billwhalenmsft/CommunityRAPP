# D365 Customer Service Demo Build Template

> **Purpose**: Reusable template for building D365 Customer Service demos for any customer.  
> **Derived From**: Zurn/Elkay (25-script systematic build) + Otis EMEA (telephony-focused build).  
> **Last Updated**: 2026-03-16

---

## Table of Contents

1. [Overview & Philosophy](#1-overview--philosophy)
2. [Pre-Requisites Checklist](#2-pre-requisites-checklist)
3. [Customer Configuration (environment.json)](#3-customer-configuration)
4. [Data Requirements — The 15 Layers](#4-data-requirements)
5. [Process Steps — Build Order](#5-process-steps)
6. [Channel-Specific Setup](#6-channel-specific-setup)
7. [Otis vs Zurn Comparison Matrix](#7-otis-vs-zurn-comparison)
8. [What to Automate vs What's Manual](#8-automate-vs-manual)
9. [Agent Design — Demo Builder Agent](#9-agent-design)
10. [Web Front-End Vision](#10-web-front-end-vision)

---

## 1. Overview & Philosophy

Every D365 Customer Service demo consists of the same building blocks, just configured differently per customer. The Zurn/Elkay demo proved this with 25 numbered scripts driven by a single `environment.json`. The Otis demo confirmed the same layers exist even when the approach was more ad-hoc.

**Core Principle**: Config-driven, idempotent provisioning. Every script uses `Find-OrCreate-Record` so it's safe to re-run. Every piece of customer-specific data lives in config files, not hardcoded in scripts.

**Shared Infrastructure**: Both demos run in the same D365 org (`orgecbce8ef.crm.dynamics.com`). The scripts create customer-specific data within a shared environment — they don't provision new orgs.

---

## 2. Pre-Requisites Checklist

### Tools Required
| Tool | Purpose | Install |
|------|---------|---------|
| PowerShell 5.1+ | Script execution | Built into Windows |
| Azure CLI (`az`) | Dataverse auth tokens | `winget install Microsoft.AzureCLI` |
| PAC CLI | Power Platform operations | `dotnet tool install --global Microsoft.PowerApps.CLI.Tool` |
| Python 3.11 | Copilot Studio scripts, reporting | `winget install Python.Python.3.11` |
| VS Code | Script editing, Copilot Studio extension | Standard install |

### Access Required
| System | Access Level | How to Verify |
|--------|-------------|---------------|
| D365 org | System Administrator or System Customizer | Open org URL in browser |
| Azure subscription | Contributor (for az login) | `az account show` |
| Power Platform | Environment Maker | `pac auth list` |
| Copilot Studio | Maker access | Open copilotstudio.microsoft.com |
| Power Pages | Portal admin | Open portal admin center |

### Authentication
```powershell
az login                    # Azure CLI (for Dataverse tokens)
pac auth create --url https://orgecbce8ef.crm.dynamics.com  # PAC CLI
```

---

## 3. Customer Configuration

Every demo starts with a `customers/{customer}/d365/config/environment.json`. This file drives all downstream scripts.

### Template Structure

```json
{
  "environment": {
    "name": "Display Name for Logs",
    "url": "https://orgecbce8ef.crm.dynamics.com",
    "apiVersion": "v9.2"
  },
  "customer": {
    "name": "Customer Legal Name",
    "project": "Project Code / Engagement Name",
    "industry": "Industry vertical",
    "regions": ["UK", "US"],
    "currentState": {
      "crm": "Current CRM system",
      "phone": "Current telephony",
      "painPoints": ["Pain point 1", "Pain point 2"]
    }
  },
  "demo": {
    "date": "ISO 8601 demo date",
    "focusAreas": ["Primary focus", "Secondary focus"],
    "channels": ["phone", "chat", "email", "portal"],
    "brands": ["Brand 1", "Brand 2"],
    "serviceAccountTypes": ["Type 1", "Type 2"],
    "incidentTypes": [
      {
        "name": "Incident Type Name",
        "priority": "High|Normal|Low",
        "slaMinutes": 120,
        "requiresWorkOrder": true
      }
    ],
    "customerTiers": {
      "1": { "label": "Tier 1 - Premium", "priority": 9000, "color": "#e74c3c", "description": "24/7 coverage" },
      "2": { "label": "Tier 2 - Standard", "priority": 7000, "color": "#e67e22", "description": "Business hours" },
      "3": { "label": "Tier 3 - Basic", "priority": 5000, "color": "#3498db", "description": "Next business day" },
      "4": { "label": "Tier 4 - On-Call", "priority": 2000, "color": "#95a5a6", "description": "Emergency only" }
    },
    "hotWords": ["Emergency", "Urgent", "Safety", "Recall"],
    "hotWordPriorityBoost": 10000,
    "sla": {
      "firstResponseMinutes": 60,
      "resolutionMinutes": 240,
      "businessHoursStart": "08:00",
      "businessHoursEnd": "18:00",
      "workDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "emergencyCoverage": "24/7 (optional)"
    },
    "caseOrigins": { "phone": 1, "email": 2, "web": 3, "chat": 4, "iot": 5 },
    "agentCount": 35
  },
  "personas": {
    "agents": [
      { "name": "Agent Name", "role": "Title", "region": "Region", "focus": "Specialty" }
    ],
    "customers": [
      { "name": "Contact Name", "title": "Title", "company": "Account", "phone": "Number", "tier": 1, "scenario": "Demo scenario" }
    ]
  }
}
```

### Key Differences by Customer

| Config Area | Zurn/Elkay | Otis | Template Guidance |
|-------------|-----------|------|-------------------|
| **Brands** | 2 (Zurn, Elkay) | 1 (Otis) | Array, 1+ brands |
| **Tiers** | 4 (distributor-based) | 4 (contract-based) | Always 4 tiers, labels vary |
| **Hot Words** | 6 (order/supply focused) | 8 (safety/entrapment focused) | Industry-specific keywords |
| **SLA** | 4hr/8hr response/resolve | 1hr/4hr (tighter for safety) | Varies by industry |
| **Account Types** | Manufacturers, Distributors, End Users | Service Accounts (buildings) | Industry structure |
| **Channels** | Phone, Email, Web, Chat | Phone (primary), Chat, Email | Demo focus dictates priority |
| **Incident Types** | Order/shipping/quality | Entrapment, out-of-service, maintenance | Industry incidents |
| **Field Service** | No | Yes (Work Orders) | Optional layer |

---

## 4. Data Requirements — The 15 Layers

Every D365 CS demo needs these data layers. Some are always required, some are optional depending on channels being demoed.

### Layer Map

| # | Layer | Zurn Script | Otis Equivalent | Required? | Dependencies |
|---|-------|-------------|-----------------|-----------|-------------|
| 1 | **Accounts** | 01-Accounts.ps1 | Provision-OtisDemo.ps1 (Accounts) | **Always** | None |
| 2 | **Contacts** | 02-Contacts.ps1 | Provision-OtisDemo.ps1 (Contacts) | **Always** | Layer 1 |
| 3 | **Products** | 03-Products.ps1 | Provision-OtisDemo.ps1 (Products) + manual | **Always** | None |
| 4 | **Subjects (Case Config)** | 04-CaseConfig.ps1 | Manual (Copilot-assisted) | **Always** | None |
| 5 | **Queues** | 05-Queues.ps1 | Not scripted (used defaults) | Phone/Chat | None |
| 6 | **SLAs** | 06-SLAs.ps1 | sla-definitions.json (reference) | **Always** | None |
| 7 | **Demo Cases** | 07-DemoCases.ps1 | Provision-OtisHeroCases.ps1 | **Always** | Layers 1-4 |
| 8 | **Knowledge Articles** | 08-KnowledgeArticles.ps1 | Manual (Copilot-assisted) | **Always** | Layer 4 |
| 9 | **Entitlements** | 09-Entitlements.ps1 | Not created | Optional | Layer 6 |
| 10 | **Unified Routing** | 10-Routing.ps1 | Not scripted (manual) | Phone/Chat | Layer 5 |
| 11 | **Classification (Hot Words)** | 11-Classification.ps1 | Not scripted | Phone/Chat | Layers 5,10 |
| 12 | **Web Resource (JS)** | 25-ServiceToolkitForms.ps1 | Upload-CaseFormScripts.ps1 | Case Form | None |
| 13 | **Portal Branding** | 14-Portal.ps1 | Not applicable | Web/Portal | None |
| 14 | **Chat Widget** | 15-ChatWidget.ps1 | Not applicable | Chat | Layer 13 |
| 15 | **Customer Intent Agent** | 22-CustomerIntentAgent.ps1 | Manual (Copilot Studio) | Voice/Chat | Layers 7,8 |

### Supplemental Layers (Zurn-only so far)

| # | Layer | Script | Purpose |
|---|-------|--------|---------|
| S1 | Queue Visuals | 12-QueueAndVisuals.ps1 | Custom queue dashboards |
| S2 | Custom Tier Field | 13-TierField.ps1 | cr377_tierlevel choice column |
| S3 | KB Portal Page | 16-KBPage.ps1 | Public-facing KB on portal |
| S4 | Phone Scenario Data | 17-PhoneScenario.ps1 | Sample phone call data |
| S5 | Chat Scenario Data | 18-ChatScenario.ps1 | Sample chat transcripts |
| S6 | Portal Hero Users | 19-PortalHeroUsers.ps1 | Demo portal login accounts |
| S7 | Order Management | 20-OrderMgmt.ps1 | D365 orders for demo |
| S8 | Shipment Tracking | 21-ShipmentTracking.ps1 | Tracking data for demo |
| S9 | WFM Shifts | 23-WFM.ps1 | Agent schedules |
| S10 | QM Evaluation | 24-QMEvaluationCriteria.ps1 | Quality management criteria |

---

## 5. Process Steps — Build Order

### Phase 1: Foundation Data (Day 1)

| Step | Action | Script | Time | Output |
|------|--------|--------|------|--------|
| 1.1 | Create `customers/{customer}/d365/config/` folder | Manual | 5 min | Folder structure |
| 1.2 | Create `environment.json` from template | Manual/Agent | 30 min | Config file |
| 1.3 | Create `demo-data.json` with accounts/contacts/cases | Manual/Agent | 1 hr | Data file |
| 1.4 | Run Accounts provisioning | Script | 2 min | account-ids.json |
| 1.5 | Run Contacts provisioning | Script | 2 min | Contacts in D365 |
| 1.6 | Run Products provisioning + Publish | Script | 3 min | product-ids.json |
| 1.7 | Create Subject tree | Script | 2 min | Subjects in D365 |

### Phase 2: Business Logic (Day 1-2)

| Step | Action | Script | Time | Output |
|------|--------|--------|------|--------|
| 2.1 | Create Queues (if routing needed) | Script | 2 min | queue-ids.json |
| 2.2 | Create SLAs | Script | 3 min | SLA in D365 |
| 2.3 | Activate SLA | **Manual** (CS Admin Center) | 5 min | Active SLA |
| 2.4 | Create Demo Cases | Script | 5 min | Cases in D365 |
| 2.5 | Link Cases to Products/Subjects | Script | 2 min | Enriched cases |
| 2.6 | Create Entitlements (optional) | Script | 3 min | Entitlements |
| 2.7 | Set Tier field on accounts | Script | 2 min | Tier values set |

### Phase 3: Knowledge & Intelligence (Day 2)

| Step | Action | Script/Tool | Time | Output |
|------|--------|-------------|------|--------|
| 3.1 | Create Knowledge Articles (8-15 per demo) | Script/AI-assisted | 30 min | KB articles |
| 3.2 | Publish KB Articles | Script | 2 min | Published articles |
| 3.3 | Link KB Articles to Cases | Script | 2 min | KB associations |
| 3.4 | Configure Unified Routing workstream | Script/Manual | 15 min | Routing rules |
| 3.5 | Configure Classification (hot words) | Script | 5 min | ARC rules |

### Phase 4: Channels (Day 2-3)

| Step | Action | Tool | Time | Output |
|------|--------|------|------|--------|
| 4.1 | Upload Web Resource (Case form JS) | Script | 5 min | Published web resource |
| 4.2 | Configure Case Form (add web resource) | **Manual** (D365 form editor) | 15 min | Form customization |
| 4.3 | Portal Branding (if Web channel) | Script | 10 min | Branded portal |
| 4.4 | Chat Widget (if Chat channel) | Script | 5 min | Embedded chat |
| 4.5 | Configure Voice channel (if Phone) | **Manual** (CS Admin Center) | 30 min | Voice workstream |
| 4.6 | Configure Customer Intent Agent | Script + Manual (Copilot Studio) | 30 min | Intent routing |

### Phase 5: Polish & Test (Day 3)

| Step | Action | Time | Output |
|------|--------|------|--------|
| 5.1 | Create Demo Execution Guide | Agent-generated | 30 min | HTML guide |
| 5.2 | Create Quick Reference Card | Agent-generated | 15 min | HTML cheat sheet |
| 5.3 | End-to-end practice run | Manual | 1-2 hr | Verified demo |
| 5.4 | Fix data issues from practice | Manual | 30 min | Clean data |
| 5.5 | Final verification (all KB published, all links correct) | Script | 5 min | Validation report |

---

## 6. Channel-Specific Setup

### Voice / Telephony Channel
**Zurn**: Full setup with phone queues, routing rules, phone scenarios  
**Otis**: Primary focus — screen pop, embedded dialer, click-to-call

| Component | What to Configure | Where |
|-----------|------------------|-------|
| Voice Workstream | Create in CS Admin Center → Workstreams | Manual |
| Phone Queues | Brand/tier-specific queues | Script (05-Queues) |
| Routing Rules | Case origin = Phone → route by tier/brand | Script (10-Routing) |
| Screen Pop JS | Web resource on case form | Script (Upload-CaseFormScripts) |
| Phone Number | Acquire or configure in voice channel | Manual |

### Web Chat Channel (Power Pages + Copilot Studio)
**Zurn**: Full portal branding, chat widget, portal hero users  
**Otis**: Not yet configured

| Component | What to Configure | Where |
|-----------|------------------|-------|
| Power Pages Portal | Create via Guided Channel Setup | Manual |
| Portal Branding | CSS, logos, hero sections | Script (14-Portal) |
| Chat Widget | Omnichannel LCW bootstrap script | Script (15-ChatWidget) |
| Chat Workstream | Live chat or messaging workstream | CS Admin Center |
| Portal Users | Demo customer login accounts | Script (19-PortalHeroUsers) |
| KB on Portal | Public-facing knowledge base | Script (16-KBPage) |

### Email Channel
**Zurn**: Email queues configured  
**Otis**: Not yet configured

| Component | What to Configure | Where |
|-----------|------------------|-------|
| Email Queues | Per brand/category | Script (05-Queues) |
| Routing Rules | Email origin → queue by subject/brand | Script (10-Routing) |
| Email Templates | Auto-responses per incident type | Manual or Script |
| Mailbox Config | Shared mailbox for case creation | Admin Center |

### Customer Intent Agent
**Zurn**: Full setup with 10+ intents, SOPs, KB linkage  
**Otis**: Not yet configured (intents available for voice/chat)

| Component | What to Configure | Where |
|-----------|------------------|-------|
| Intent Groups | Industry-specific groups | Script (22-CustomerIntentAgent) |
| Individual Intents | 8-12 per customer | Script + Copilot Studio |
| Agent Instructions | Per-intent copilot prompts | Copilot Studio |
| KB Runbooks (SOPs) | Procedural articles per intent | Script (08/22) |

---

## 7. Otis vs Zurn Comparison

### Maturity Comparison

| Aspect | Zurn/Elkay | Otis | Gap |
|--------|-----------|------|-----|
| **Automation Level** | 25 numbered scripts, fully automated | 3 scripts + much manual work | Need orchestrator for Otis |
| **Config-Driven** | environment.json drives everything | environment.json exists but underused | Wire up remaining scripts |
| **Data Tracking** | 25 JSON tracking files | 8 JSON files | Add product-ids, queue-ids, routing-ids, classification-ids |
| **Accounts** | 19 accounts (mfg + dist + end user) | 10 accounts (service accounts) | ✅ Both adequate |
| **Contacts** | 23 contacts across account types | 7 contacts | ✅ Both adequate for demo |
| **Products** | 16 SKUs with prices/price lists | 8 products (added later) | Close gap with script |
| **Subjects** | 19 subjects (2 brand roots + children) | 7 subjects (1 root + 6 children) | ✅ Both adequate |
| **Queues** | 18 queues (brand × channel × tier) | None created (used defaults) | Need if routing demoed |
| **SLAs** | Created + documented | Defined in config, not created | Script needed |
| **Cases** | ~50 cases across all tiers | 16 cases across tiers | ✅ Both adequate |
| **KB Articles** | 15 articles (script-generated) | 11 articles (manually created) | Need to script creation |
| **KB-Case Links** | Script-generated | Script-generated (Link-OtisKBArticles.ps1) | ✅ Parity |
| **Entitlements** | 4 tier-based templates | Not created | Optional |
| **Routing** | 13 rules (hot word + case type) | Not configured | Need if routing demoed |
| **Classification** | Hot word rules consolidated | Not configured | Need if routing demoed |
| **Portal** | Branded, KB tiles, chat widget | Not applicable (phone focus) | Channel-dependent |
| **Intent Agent** | 10+ intents with SOPs | Not configured | Need for voice/chat |
| **Web Resource** | ServiceToolkitLoader.js | otis_CaseFormScripts.js | ✅ Both have |
| **Demo Guides** | 8+ assets (scripts, slides, guides) | demo-execution-guide.html + quick-ref | Close but gap |
| **Orchestrator** | 00-Setup.ps1 with -From/-Only/-Customer | None | **Critical gap** |

### What Otis Teaches Us

1. **Telephony-first demos** need fewer layers — no portal, no chat widget, fewer queues
2. **AI-assisted content creation** (using Copilot to write KB articles, case descriptions) is faster for one-off demos
3. **Web Resource customization** (screen pop JS) is critical for voice demos
4. **Products + Subjects as case enrichment** should be automated from day 1, not added later
5. **The gap between "adequate for demo" and "fully automated"** — Otis works but required significant manual effort

### What Zurn Teaches Us

1. **25-script pipeline is production-grade** — any new customer can be added by creating config files
2. **Find-OrCreate-Record pattern is essential** — idempotent, safe to re-run
3. **Data tracking files** (account-ids.json, queue-ids.json, etc.) enable downstream scripts to reference created records
4. **Hot word classification** is a powerful demo feature — easy to configure, impressive in demos
5. **Entitlement model** showcases tier-based service differentiation beautifully

---

## 8. What to Automate vs What's Manual

### Always Automate (Script)
| Task | Why | Script Pattern |
|------|-----|----------------|
| Accounts | Repeatable, data-driven | Find-OrCreate-Record by accountnumber |
| Contacts | Repeatable, linked to accounts | Find-OrCreate-Record by email |
| Products + Publish | Complex publish action | Find-OrCreate-Record + PublishProductHierarchy |
| Subjects | Hierarchical, data-driven | Find-OrCreate-Record by name + parentsubject bind |
| Demo Cases | 10-50 records, linked to everything | Find-OrCreate-Record by title |
| KB-Case Links | Tedious manual linkage | knowledgearticleincident creation |
| Product/Subject-Case Links | Tedious manual enrichment | PATCH case with productid/subjectid binds |
| Queues | Simple creation | Find-OrCreate-Record by name |
| Web Resource Upload | Prevents manual mistakes | Dataverse API to webresourceset |

### Automate When Possible (Script + Manual Verification)
| Task | Why Manual Still Needed | Script Pattern |
|------|------------------------|----------------|
| KB Article Creation | Content quality matters, but structure is repeatable | Script creates with HTML template, human reviews |
| SLAs | Can create records but activation is manual | Script creates, manual activation in Admin Center |
| Routing Rules | XML ruleset format is complex but deterministic | Script generates XML, verify in Admin Center |
| Entitlements | Can create but association per account is manual | Script creates templates, manual association |

### Always Manual
| Task | Why |
|------|-----|
| SLA Activation | D365 requires Admin Center UI interaction |
| Voice Channel Configuration | Telephony provider setup, phone number assignment |
| Copilot Studio Agent | UI-based configuration, topic/intent mapping |
| Case Form Customization | Form editor changes (add web resource, rearrange) |
| Guided Channel Setup | One-time wizard in CS Admin Center |
| Portal Creation | One-time Power Pages provisioning |
| Power BI Dashboard Setup | Visual design in PBI Desktop |
| Demo Practice Run | Human validation required |

---

## 9. Agent Design — Demo Builder Agent

### Concept

A RAPP agent (`D365DemoBuilderAgent`) that:
1. Takes customer discovery info (transcript, requirements doc, or interactive Q&A)
2. Generates all config files (environment.json, demo-data.json)
3. Generates customer-specific scripts or runs the generic pipeline with customer config
4. Creates KB articles from industry knowledge
5. Generates the demo execution guide and quick reference
6. Runs validation and reports gaps

### Agent Actions

| Action | Input | Output |
|--------|-------|--------|
| `create_customer_config` | Customer name, industry, channels, tiers | environment.json, demo-data.json |
| `generate_accounts` | environment.json | Account records + account-ids.json |
| `generate_contacts` | environment.json + account-ids | Contact records |
| `generate_products` | Industry, product list | Product records + product-ids.json |
| `generate_subjects` | Industry, incident types | Subject tree |
| `generate_kb_articles` | Industry, incident types, subjects | 8-15 KB articles |
| `generate_cases` | All above IDs + environment.json | 10-50 demo cases with full enrichment |
| `generate_queues` | Brands, channels, tiers | Queue records + queue-ids.json |
| `generate_routing` | Queues, hot words, brands | Routing workstream + rules |
| `generate_demo_guide` | All above + customer config | HTML demo execution guide |
| `validate_environment` | Customer name | Validation report (what exists, what's missing) |
| `full_build` | Customer config | End-to-end: all layers in sequence |

### Agent Architecture

```
D365DemoBuilderAgent
  ├── inherits BasicAgent
  ├── uses DataverseHelper.psm1 (via subprocess PowerShell calls)
  ├── reads customers/{customer}/d365/config/environment.json
  ├── writes customers/{customer}/d365/data/*.json (tracking files)
  ├── calls Azure OpenAI for KB article content generation
  └── generates HTML demo guides from templates
```

### Metadata Schema (for OpenAI function calling)

```json
{
  "name": "D365DemoBuilder",
  "description": "Builds D365 Customer Service demo environments. Creates accounts, contacts, products, subjects, cases, KB articles, queues, routing, and generates demo guides.",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["create_customer_config", "generate_accounts", "generate_contacts", "generate_products", "generate_subjects", "generate_kb_articles", "generate_cases", "generate_queues", "generate_routing", "generate_demo_guide", "validate_environment", "full_build"],
        "description": "The provisioning action to perform"
      },
      "customer": {
        "type": "string",
        "description": "Customer folder name (e.g., 'otis', 'zurnelkay')"
      },
      "industry": {
        "type": "string",
        "description": "Industry vertical for context-aware generation"
      },
      "channels": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Channels to configure: phone, chat, email, portal"
      }
    },
    "required": ["action", "customer"]
  }
}
```

---

## 10. Web Front-End Vision

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Demo Builder Web App                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Step Wizard   │  │ Live Status  │  │ Generated Assets     │  │
│  │ 1. Customer   │  │ ● Accounts ✓│  │ • Demo Guide (HTML)  │  │
│  │ 2. Industry   │  │ ● Contacts ✓│  │ • Quick Reference    │  │
│  │ 3. Channels   │  │ ○ Products  │  │ • Phone Call Script   │  │
│  │ 4. Tiers      │  │ ○ Cases     │  │ • Chat Demo Script    │  │
│  │ 5. Build!     │  │ ○ KB Articles│ │ • Validation Report   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure Function (RAPP Backend)                       │
│  D365DemoBuilderAgent → DataverseHelper → D365 Web API          │
│  OpenAI → KB Article Generation, Demo Guide Generation          │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│              D365 Environment                                    │
│  Accounts │ Contacts │ Products │ Cases │ KB │ Queues │ Routing │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

1. **Step Wizard**: Guide user through customer config (name, industry, channels, tiers, hot words, SLA)
2. **Live Build Status**: Real-time progress as each layer is provisioned
3. **Asset Downloads**: Generated demo guides, scripts, quick reference cards
4. **Validation Dashboard**: Show what's in D365, what's missing, what needs manual action
5. **Multi-Customer**: Switch between customers, compare builds
6. **Re-Run Safety**: Idempotent — can re-run any step without duplicating data

### Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Frontend | React or static HTML + vanilla JS | Simple, deployable anywhere |
| Backend | Azure Function (existing RAPP) | Already exists, has OpenAI integration |
| API | REST (existing `businessinsightbot_function`) | D365DemoBuilderAgent as a new agent |
| D365 Access | DataverseHelper.psm1 via PowerShell subprocess | Proven, production-tested |
| AI | Azure OpenAI GPT-4o | KB content generation, demo guide writing |
| Storage | Azure File Storage | Config files, tracking JSONs, generated guides |

### MVP Scope (Phase 1)

1. Customer config form → generates environment.json
2. "Build Foundation" button → runs Layers 1-7 (accounts through cases)
3. Live progress display
4. Download demo execution guide
5. Validation report

### Phase 2

6. KB article generation with AI
7. Routing/classification setup
8. Channel-specific configuration wizards
9. Demo guide customization (drag/drop scenarios)

### Phase 3

10. Multi-org support (not just orgecbce8ef)
11. Template library (pre-built industry configs)
12. Copilot Studio integration (auto-configure intents)
13. Diff/compare between customer builds

---

## Appendix A: Folder Structure Template

```
customers/{customer}/
  d365/
    config/
      environment.json          # Master configuration
      demo-data.json            # Accounts, contacts, products, cases data
      sla-definitions.json      # SLA timing and business hours
      productivity-toolkit.json # Productivity pane config (optional)
    data/
      account-ids.json          # Created account GUIDs
      contact-ids.json          # Created contact GUIDs  
      product-ids.json          # Created product GUIDs
      queue-ids.json            # Created queue GUIDs
      routing-ids.json          # Created routing rule GUIDs
      classification-ids.json   # Created ARC rule GUIDs
      hero-record-ids.json      # Key demo records (hero account, contact, case)
      knowledge-articles.json   # Created KB article GUIDs
      intent-agent-ids.json     # Created intent GUIDs
      deployment-record.json    # Build history and timestamps
    demo-assets/
      demo-execution-guide.html # Primary demo guide
      quick-reference.html      # One-page cheat sheet
      phone-call-script.md      # Phone demo script
      chat-demo-script.md       # Chat demo script
      scenarios/                # Per-scenario detailed scripts
        scenario-1-entrapment/
        scenario-2-maintenance/
    scripts/
      Link-{Customer}Cases.ps1      # Product/subject enrichment
      Link-{Customer}KBArticles.ps1 # KB-case associations
      Upload-CaseFormScripts.ps1    # Web resource deployment
    webresources/
      {customer}_CaseFormScripts.js  # Case form customization
    copilot-studio/
      agent-instructions.md     # Copilot Studio agent setup notes
      topic-definitions/        # Intent/topic YAML definitions
```

## Appendix B: D365 Entity Reference

| Entity | API Name | Key Fields | Notes |
|--------|----------|-----------|-------|
| Account | `accounts` | accountid, name, accountnumber | Filter by accountnumber for Find-OrCreate |
| Contact | `contacts` | contactid, emailaddress1 | Filter by email for Find-OrCreate |
| Product | `products` | productid, productnumber, name | Must PublishProductHierarchy after creation |
| Subject | `subjects` | subjectid, title | Hierarchical via parentsubject |
| Case | `incidents` | incidentid, title, prioritycode | severitycode: only 1 valid in this org |
| KB Article | `knowledgearticles` | knowledgearticleid, title | States: 0=Draft, 3=Published |
| KB-Case Link | `knowledgearticleincidents` | knowledgearticleid, incidentid | Lookup binds required |
| Queue | `queues` | queueid, name | queueviewtype: 0=Public |
| SLA | `slas` | slaid, name | slaversion: 100000001 for Enhanced |
| SLA Item | `slaitems` | slaitemid | XML conditions |
| Entitlement | `entitlements` | entitlementid, name | allocationtypecode: 0=cases |
| Workstream | `msdyn_liveworkstreams` | msdyn_liveworkstreamid | streamsource: 192350000=Record |
| Routing Rule | `msdyn_decisionrulesets` | msdyn_decisionrulesetid | XML hit-policy rules |
| Web Resource | `webresourceset` | webresourceid, name | Must Publish after upload |
| Price List | `pricelevels` | pricelevelid, name | Linked to products via price list items |
| Price List Item | `productpricelevels` | productpricelevelid | pricingmethodcode: 1=Currency Amount |
| Unit Group | `uomschedules` | uomscheduleid | Default: 293a6142-a9f8-478f-9bd9-67d1b9031548 |

## Appendix C: Key Gotchas & Lessons Learned

1. **Product Publishing**: `SetState` and PATCH `statecode` don't work. Must use unbound action `PublishProductHierarchy`.
2. **PowerShell `$PID`**: Reserved variable — never use as variable name. Use `$parentId` instead.
3. **PS 5.1 Limitations**: No `-ResponseHeadersVariable` on `Invoke-RestMethod`. Use `Invoke-WebRequest` for header access.
4. **KB Article Duplicates**: Each KB article has 2 records — Published root (state=3) + Draft content version (state=0). This is normal.
5. **severitycode**: Only value 1 is valid in this org (orgecbce8ef). Don't try 2, 3, or 4.
6. **Case Type Codes**: 1=Question, 2=Problem, 3=Request. Priority: 1=High, 2=Normal, 3=Low.
7. **Tier Field**: Custom choice column `cr377_tierlevel`. Values: 192350000=Tier 1 through 192350003=Tier 4.
8. **SLA Activation**: Must be done manually in CS Admin Center — no API for this.
9. **Token Expiry**: Azure CLI tokens expire after ~1 hour. Long-running scripts may need `Connect-Dataverse` refresh.
10. **OData Bind Syntax**: Lookups require `"fieldname@odata.bind": "/entityset(guid)"` format.
11. **Org-Specific GUIDs**: Subject GUIDs, workstream GUIDs vary per org. Scripts should query, not hardcode.
12. **Find-OrCreate Is Essential**: Without it, re-running scripts creates duplicates. Always use this pattern.
