# Power Platform Integration Guide

Deploy RAPP agents to Microsoft Teams and Microsoft 365 Copilot using Power Platform.

## 📖 Table of Contents

- [Overview](#overview)
- [Standard Deployment Method](#standard-deployment-method)
- [Architecture](#architecture)
- [Solution Structure](#solution-structure)
- [Deploy an Existing Solution](#deploy-an-existing-solution)
- [Build a New Customer Solution](#build-a-new-customer-solution)
- [User Context Integration](#user-context-integration)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Cost Analysis](#cost-analysis)
- [Security Best Practices](#security-best-practices)

## Overview

Power Platform integration enables you to deploy your AI assistant to:
- 💬 **Microsoft Teams** - Personal and team channels
- 🤖 **Microsoft 365 Copilot** - As a declarative agent
- 📱 **Power Apps** - Embedded in custom apps
- 🔄 **Power Automate** - Workflow automation

## Standard Deployment Method

> **One approach. Always works.**

RAPP uses the **solution source + build script + PAC CLI** pattern for all Power Platform deployments. Do not use manually-crafted XML or hand-assembled ZIPs — Power Platform import is strict about schema and fails silently or with cryptic errors when XML is wrong.

### The Three-File Minimum

Every RAPP Power Platform solution must have these source files committed to `customers/<name>/solution/solution_src/`:

```
solution_src/
├── [Content_Types].xml     # OPC namespace required — xmlns="...openxmlformats.org/package/2006/content-types"
├── solution.xml            # <ImportExportXml version=... SolutionPackageVersion=...> root
├── customizations.xml      # Entity definitions INLINE here (not in separate Entities/ files)
├── EnvironmentVariables/
│   └── environmentvariables.xml
└── Workflows/
    └── *.json              # One file per Power Automate flow
```

### Prerequisites

| Requirement | Notes |
|---|---|
| Power Platform environment | Developer, Sandbox, or Production |
| Copilot Studio license | Required to import and publish bot components |
| Power Automate Premium | Required for HTTP trigger flows |
| PAC CLI | `dotnet tool install -g Microsoft.PowerApps.CLI.Tool` |

### Why Source Files, Not Generated XML

The Ascend solution builder (`customers/ascend/solution/build_solution.py`) was written from real import failures. The validator catches the exact errors PP throws:
- `0x80044355: PrimaryName attribute not found` — missing `PrimaryNameAttribute` on entity
- `Required Types tag not found` — missing OPC namespace on `[Content_Types].xml`
- Silent import failures — entity definitions in `Entities/*.xml` subfolders are ignored

Synthetically-generated XML hits these issues. Exported-then-committed source files don't.

## Architecture

### Full Stack Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
│  Microsoft Teams  │  M365 Copilot  │  Power Apps  │  Web UI     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Conversation Layer                            │
│                     Copilot Studio                               │
│  • Natural Language Processing                                   │
│  • Dialog Management                                             │
│  • Intent Recognition                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Integration Layer                             │
│                     Power Automate                               │
│  • User Context Enrichment (Office 365 profile)                 │
│  • Data Transformation                                           │
│  • Error Handling & Retry Logic                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     Processing Layer                             │
│                   Azure Function App                             │
│  • Agent Selection & Routing                                     │
│  • Memory Management                                             │
│  • Azure OpenAI Integration                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                       Agent Layer                                │
│   Memory  │  Email  │  Calendar  │  Custom  │  GitConflict     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                       Data Layer                                 │
│    Azure Storage    │    Azure OpenAI    │   Microsoft Graph   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Request Flow:**
```
1. User sends message in Teams/M365 Copilot
   ↓
2. Copilot Studio processes natural language
   ↓
3. Triggers Power Automate flow
   ↓
4. Power Automate enriches with Office 365 user data
   │ - User name
   │ - Email address
   │ - Department
   │ - Job title
   ↓
5. HTTP POST to Azure Function
   {
     "user_input": "User's message",
     "conversation_history": [...],
     "user_guid": "office365-user-id",
     "user_context": {
       "email": "user@company.com",
       "name": "John Doe",
       "department": "Engineering"
     }
   }
   ↓
6. Azure Function processes request
   │ - Loads user memory
   │ - Routes to appropriate agents
   │ - Calls Azure OpenAI
   ↓
7. Returns response to Power Automate
   ↓
8. Power Automate formats for Copilot Studio
   ↓
9. Copilot Studio displays in Teams/M365 Copilot
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
│  Microsoft Teams  │  M365 Copilot  │  Power Apps  │  Web UI     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Conversation Layer                            │
│                     Copilot Studio                               │
│  • Natural Language Processing                                   │
│  • Dialog Management  • Intent Recognition                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Integration Layer                             │
│                     Power Automate                               │
│  • User Context Enrichment (Office 365 profile)                 │
│  • HTTP connector → Azure Function  • Error Handling            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     Processing Layer                             │
│                   Azure Function App                             │
│  • Agent Selection & Routing                                     │
│  • Memory Management  • Azure OpenAI Integration                 │
└─────────────────────────────────────────────────────────────────┘
```

**Request Flow:**
```
User message → Copilot Studio → Power Automate (enriches with O365 user profile)
  → HTTP POST to Azure Function:
      { "user_input": "...", "conversation_history": [...],
        "user_guid": "<o365-user-id>",
        "user_context": { "email": "...", "name": "...", "department": "..." } }
  → Azure Function → Azure OpenAI → Agent → response
  → Power Automate → Copilot Studio → User
```

## Solution Structure

Every customer solution follows the Ascend pattern (see `customers/ascend/solution/` as the reference):

```
customers/<name>/solution/
├── build_solution.py           # Validates + packages ZIP — run this, never hand-build
├── DEPLOYMENT_GUIDE.md         # Customer-specific import and config steps
├── AscendXxx_1_0_0_0.zip       # Built artifact (committed for easy distribution)
├── configure_bot.ps1           # Post-import bot configuration
├── patch_flows.ps1             # Post-import flow URL/key patching
├── load_sample_data.ps1        # Demo data loader
└── solution_src/               # SOURCE OF TRUTH — commit these files
    ├── [Content_Types].xml
    ├── solution.xml
    ├── customizations.xml      # All entity definitions INLINE here
    ├── EnvironmentVariables/
    │   └── environmentvariables.xml
    └── Workflows/
        └── *.json              # One JSON per Power Automate flow
```

### Flow JSON Structure

Each Power Automate flow in `Workflows/*.json` follows this pattern:

```json
{
  "properties": {
    "connectionReferences": {
      "shared_office365users": { "connection": { "connectionReferenceLogicalName": "..." } }
    },
    "definition": {
      "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
      "triggers": { "manual": { "type": "Request", "kind": "PowerAppV2" } },
      "actions": {
        "Get_user_profile": { "type": "ApiConnection", "inputs": { "host": { "apiId": "/providers/Microsoft.PowerApps/apis/shared_office365users" } } },
        "Call_Azure_Function": {
          "type": "Http",
          "inputs": {
            "method": "POST",
            "uri": "@variables('functionUrl')",
            "headers": { "x-functions-key": "@variables('functionKey')" },
            "body": {
              "user_input": "@triggerBody()?['text']",
              "user_guid": "@outputs('Get_user_profile')?['body/id']",
              "user_context": { "email": "@outputs('Get_user_profile')?['body/mail']", "name": "@outputs('Get_user_profile')?['body/displayName']" }
            }
          }
        }
      }
    }
  }
}
```

## Deploy an Existing Solution

### Using the Pre-Built RAPP Solution (Recommended for New Deployments)

`MSFTAIBASMultiAgentCopilot_1_0_0_2.zip` is the validated, production-tested multi-agent solution:

```powershell
# Option A: PAC CLI (preferred — automated, repeatable)
pac auth create --environment https://YOUR-ORG.crm.dynamics.com
pac solution import --path MSFTAIBASMultiAgentCopilot_1_0_0_2.zip --activate-plugins

# Option B: Portal
# make.powerapps.com → Solutions → Import solution → Browse → Upload ZIP
```

**Post-import steps:**
1. Configure the Office 365 Users connection reference
2. Edit each flow: update `functionUrl` variable to your Function App URL
3. Edit each flow: update `functionKey` variable to your function key
4. Turn on all flows
5. Publish the bot in Copilot Studio
6. Turn on Teams / M365 Copilot channels

### Using a Customer-Specific Solution

```powershell
# 1. Build (validates XML before packaging)
python customers/<name>/solution/build_solution.py

# 2. Import
pac auth create --environment https://YOUR-ORG.crm.dynamics.com
pac solution import --path customers/<name>/solution/<Name>_1_0_0_0.zip

# 3. Configure
# Set environment variables in PP: Solutions → <Name> → Environment Variables
# Patch function URL and key:
pwsh customers/<name>/solution/patch_flows.ps1 -FunctionUrl "https://..." -FunctionKey "..."

# 4. Load sample data (demo mode only)
pwsh customers/<name>/solution/load_sample_data.ps1

# 5. Deploy to Teams
# Copilot Studio → Publish → Channels → Microsoft Teams → Turn on
```

## Build a New Customer Solution

### Step 1: Export from a Working PP Environment

Build your solution manually in PP first (flows, bot, entities). Then export it:

```powershell
pac solution export --name YourSolutionName --path exported_solution.zip --managed false
```

Unzip the export to `customers/<name>/solution/solution_src/`. This gives you real, PP-validated source files.

### Step 2: Commit Source Files

```
customers/<name>/solution/solution_src/
├── [Content_Types].xml     ← from export
├── solution.xml            ← from export
├── customizations.xml      ← from export (entities inline, not in subfolders)
├── EnvironmentVariables/environmentvariables.xml
└── Workflows/*.json        ← one per flow
```

### Step 3: Create build_solution.py

Copy from `customers/ascend/solution/build_solution.py` and update:
- `SOLUTION_DIR` path
- `OUTPUT_ZIP` name
- `BOT_SCHEMA` name
- Any customer-specific topic mappings

The validator enforces the rules that cause real PP import failures — **always run it before distributing a ZIP**.

### Step 4: Create Deployment Guide

Copy `customers/ascend/solution/DEPLOYMENT_GUIDE.md` as your template. Document:
- Environment variables and their values
- Post-import configuration steps
- Sample data loading (if applicable)
- PAC CLI import command

### Step 5: Create PowerShell Config Scripts

```powershell
# patch_flows.ps1 — update function URL/key in all flows post-import
param(
    [Parameter(Mandatory)][string]$EnvironmentUrl,
    [Parameter(Mandatory)][string]$FunctionUrl,
    [Parameter(Mandatory)][string]$FunctionKey
)
pac auth create --environment $EnvironmentUrl
# Use pac flow update or Dataverse API to patch environment variables
```

### Checklist Before Distributing a Solution ZIP

```
□ build_solution.py --validate-only passes with no errors
□ [Content_Types].xml has correct OPC namespace
□ customizations.xml has entity definitions INLINE (not in Entities/ subfolders)
□ Every entity has PrimaryNameAttribute matching an attribute with <IsPrimaryName>1</IsPrimaryName>
□ All flows use environment variables for function URL and key (not hardcoded values)
□ DEPLOYMENT_GUIDE.md documents all environment variable values
□ ZIP tested with: pac solution import --path <file>.zip in a dev environment
```

## User Context Integration

When deployed via Power Platform, agents automatically receive user context from Office 365:

```python
class PersonalizedAgent(BasicAgent):
    def perform(self, user_context=None, query="", **kwargs):
        name = (user_context or {}).get('name', 'User')
        dept = (user_context or {}).get('department', '')
        return f"Hello {name} from {dept}, how can I help?"
```

The `user_context` dict fields: `email`, `name`, `department`, `jobTitle` — populated by the Power Automate Office 365 Users connector.

## Monitoring & Troubleshooting

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Import fails: "Required Types tag not found"** | Missing OPC namespace on `[Content_Types].xml` | Run `build_solution.py --validate-only` |
| **Import fails: error 0x80044355** | Missing `PrimaryNameAttribute` or `<IsPrimaryName>` on entity | Validator catches this — fix before packaging |
| **Entity definitions not imported** | Entities in `Entities/` subfolders | Move definitions inline into `customizations.xml` |
| **"Unauthorized" (401) from flow** | Invalid function key | Update `functionKey` variable in flow; never hardcode |
| **"Timeout" (408/500) from flow** | Function execution > 230s | Check agent logic; Function App timeout is 5 min |
| **User context not passed** | Office 365 connector unauthenticated | Re-authenticate Office 365 Users connection reference |
| **Flow not turning on** | Connection references not configured | Configure all connection references before turning on flows |

**Debug Flow Runs:**  
Power Automate → My flows → select flow → 28-day run history → click failed run → expand each action

**View Function Logs:**
```bash
az functionapp log tail --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1
```

## Cost Analysis

| Service | Cost |
|---------|------|
| Azure Function App (Flex Consumption) | ~$0–20/month |
| Azure Storage | ~$5/month |
| Azure OpenAI (gpt-4o) | ~$0.01–0.03 per 1K tokens |
| Power Automate Premium | ~$15/user/month |
| Microsoft 365 Copilot (optional) | ~$30/user/month |

**Rough total: $20–25/user/month** for full Teams + M365 Copilot integration.

## Security Best Practices

- ✅ Store function key in Power Automate environment variable, not hardcoded in flow
- ✅ Rotate function keys every 90 days: `az functionapp keys renew --name ... --resource-group ...`
- ✅ Use function-level keys (not the master key)
- ✅ Enable DLP policies in Power Platform Admin Center (allow HTTP to your Function App only)
- ✅ Review flow access logs monthly in Power Platform Admin Center → Analytics
- ❌ Never share function keys via email or Teams chat

## Reference

- [customers/ascend/solution/](../customers/ascend/solution/) — Reference implementation (build script, validators, deployment guide)
- [MSFTAIBASMultiAgentCopilot_1_0_0_2.zip](../MSFTAIBASMultiAgentCopilot_1_0_0_2.zip) — Baseline multi-agent solution for new deployments
- [utils/copilot_studio_api.py](../utils/copilot_studio_api.py) — Programmatic Dataverse API client (advanced use cases)
- [Power Platform Documentation](https://learn.microsoft.com/power-platform/)
- [Copilot Studio Documentation](https://learn.microsoft.com/microsoft-copilot-studio/)

