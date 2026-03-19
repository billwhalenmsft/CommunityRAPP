# Demo Action Flows

Power Automate flow definitions for triggering D365 actions from the Demo Execution Guide.

## Flow Definitions

| File | Action | Trigger | What It Does |
|------|--------|---------|-------------|
| `send_notification_flow.json` | Send Toast Notification | HTTP Request | Creates a D365 in-app notification via `appnotification` entity |
| `create_case_flow.json` | Create Case | HTTP Request | Creates a new case in D365 Customer Service with account linking |
| `trigger_sla_breach_flow.json` | SLA Breach | HTTP Request | Updates a case priority and sends breach/warning notification |
| `enrich_callpop_context_flow.json` | Enrich Call Pop | Row Created (Conversation) | Populates Account, Contact, Tier, Open Cases on incoming voice calls |

## Call Pop Enrichment Flow

**`enrich_callpop_context_flow.json`** works with the `bw_incoming_call_callpop` notification template
(created by `d365/scripts/29-CallPopNotification.ps1`) to show rich customer context on incoming calls.

### How It Works

```
Inbound Call → ANI Match → Conversation Created → Flow Triggers
                                                       │
                  ┌────────────────────────────────────┘
                  ▼
         Read Contact (_msdyn_customer_value)
                  │
                  ▼
         Read Parent Account (parentcustomerid)
           → account name
           → cra1f_servicelevel (Gold/Silver/Bronze)
                  │
                  ▼
         Count Open Cases (statecode = 0)
                  │
                  ▼
         PATCH msdyn_contextvariables on conversation
           → msdyn_account_name
           → msdyn_contact_name
           → msdyn_tier
           → msdyn_open_cases
                  │
                  ▼
         Notification template reads slugs → Agent sees full context
```

### Setup in Power Automate

1. Go to [Power Automate](https://make.powerautomate.com)
2. Create a new **Automated Cloud Flow**
3. Trigger: **When a row is added** (Dataverse) → Table: **Conversation** (`msdyn_ocliveworkitem`)
4. Add row filter: `msdyn_channel eq 192440000` (Voice calls only)
5. Build each action from the JSON definition (Get Contact → Get Account → Count Cases → Update Context)
6. **Save** and enable

> **Timing Note**: The flow must complete before the agent accepts the call (120s timeout).
> Typical execution is 2-5 seconds. If row-created trigger is too slow, use the
> `msdyn_OnConversationCreate` bound action trigger instead (see `_metadata.alternative_trigger` in the JSON).

### Tier Field Mapping

| Value | Label |
|-------|-------|
| 276120000 | Gold |
| 276120001 | Silver |
| 276120002 | Bronze |

Field: `account.cra1f_servicelevel`

## Setup Instructions

### For Each Flow

1. Go to [Power Automate](https://make.powerautomate.com)
2. Create a new **Instant Cloud Flow**
3. Add trigger: **When an HTTP request is received**
4. Copy the schema from the flow JSON file's `trigger.inputs.schema`
5. Add the Dataverse actions described in `_metadata.setup_steps`
6. **Save** the flow — Power Automate generates an HTTP POST URL
7. Copy that URL into the Demo Action Panel's config section

### Connections Required

- **Dataverse** (Microsoft Dataverse connector) — for CRUD operations on cases, accounts, appnotifications
- **Office 365 Outlook** (only for email simulation flow) — to send simulated customer emails

### Environment

- **Org URL**: `https://orgecbce8ef.crm.dynamics.com`
- **Admin**: `admin@D365DemoTSCE30330346.onmicrosoft.com`

## How Buttons Work

The Demo Action Panel supports **three modes** for executing actions:

### Mode 1: Power Automate (recommended for demos)
- Buttons call the HTTP-triggered Power Automate flows directly
- Flows run in D365's security context — no extra auth needed
- Best for: D365-native actions (notifications, case creation, SLA)

### Mode 2: Azure Function App (deployed RAPP)
- Buttons call `https://rapp-ov4bzgynnlvii.azurewebsites.net/api/trigger/copilot-studio`
- Uses the existing RAPP trigger system to invoke agents
- Best for: AI-powered orchestrations (triage, analysis)

### Mode 3: Local Dev (func start)
- Same as Azure mode but calls `http://localhost:7071`
- Requires `func start` running locally
- Best for: Building and debugging new actions

## RAPP Trigger Configs

Corresponding YAML trigger configs live in `/triggers/`:

| File | Trigger Name | Endpoint |
|------|-------------|----------|
| `demo_send_notification.yaml` | `demo_send_notification` | `POST /api/trigger/manual/demo_send_notification` |
| `demo_create_case.yaml` | `demo_create_case` | `POST /api/trigger/manual/demo_create_case` |
| `demo_sla_breach.yaml` | `demo_sla_breach` | `POST /api/trigger/manual/demo_sla_breach` |
