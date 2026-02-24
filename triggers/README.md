# RAPP Event-Driven Triggers

This folder contains trigger configurations that enable RAPP agents to respond to external events automatically.

## Trigger Types

| Type | Description | Use Case |
|------|-------------|----------|
| `webhook` | HTTP webhook from external systems | Salesforce, ServiceNow, GitHub |
| `timer` | Scheduled/cron triggers | Daily reports, periodic checks |
| `dataverse` | Copilot Studio native triggers | D365/Dataverse record changes |
| `queue` | Azure Service Bus/Storage Queue | Async processing, high-volume |

## Configuration Files

- **salesforce_case_created.yaml** - Routes new Salesforce cases to triage
- **daily_ci_report.yaml** - Generates daily CI reports on schedule
- **dataverse_account_updated.yaml** - Responds to D365 account changes

## Usage

### 1. Webhook Triggers

External systems can send webhooks to:
```
POST https://<function-app>.azurewebsites.net/api/trigger/webhook/{source}?event={event_type}
```

Example:
```bash
curl -X POST "https://your-app.azurewebsites.net/api/trigger/webhook/salesforce?event=case.created" \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{"Id": "12345", "Subject": "Issue with product", "Priority": "High"}'
```

### 2. Timer Triggers

Timer triggers use Azure Functions CRON syntax:
```yaml
schedule: "0 0 8 * * 1-5"  # 8am Mon-Fri
```

### 3. Copilot Studio Integration

#### Outbound (RAPP → Copilot Studio)
Set `copilot_studio_enabled: true` to send trigger results to a Copilot Studio agent.

#### Inbound (Copilot Studio → RAPP)
Power Automate flows can call:
```
POST https://<function-app>.azurewebsites.net/api/trigger/copilot-studio
{
  "agent": "carrier_case_triage_orchestrator",
  "action": "triage_case",
  "parameters": { "case_id": "12345" }
}
```

## Configuration Schema

```yaml
name: trigger_name
description: What this trigger does
trigger_type: webhook | timer | dataverse | queue
enabled: true | false

# For webhooks
source: salesforce | servicenow | github | custom
event_type: case.created | ticket.updated | etc

# For timers
schedule: "CRON expression"
timezone: America/Chicago

# For Dataverse
table_name: account | contact | etc
change_type: create | update | delete

# Target agent
target_agent: agent_name
target_action: action_name
parameters:
  key: value

# Payload configuration
message_template: "Instructions for the agent with {{variables}}"
body_mapping:
  agent_param: source_field

# Filters (only trigger if conditions match)
filters:
  - field: Priority
    operator: equals | in | contains | greater_than
    value: High

# Notifications
on_success:
  - type: teams
    webhook_url: https://...
on_failure:
  - type: email
    to: team@company.com

# Copilot Studio
copilot_studio_enabled: true
copilot_studio_bot_id: bot-guid
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trigger/webhook/{source}` | POST | Receive webhooks |
| `/api/trigger/manual/{name}` | POST | Test triggers manually |
| `/api/trigger/copilot-studio` | POST | Receive from Copilot Studio |
| `/api/triggers` | GET | List all triggers |
| `/api/triggers/stats` | GET | Get execution statistics |

## Adding New Triggers

1. Create a YAML file in this folder
2. Configure the trigger type and target agent
3. Add filters to control when it fires
4. Test with the manual trigger endpoint
5. Configure your external system's webhook
