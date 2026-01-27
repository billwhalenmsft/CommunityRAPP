# Copilot Studio Native Transpiler Output

This folder contains RAPP Python agents transpiled to native Microsoft Copilot Studio format.

## Overview

The **CopilotStudioTranspilerAgent** converts RAPP Python agents into standalone Copilot Studio solutions that run **without a Function App backend**. This enables:

- **Zero-code deployment** - Import directly into Copilot Studio
- **Native connectors** - Uses Power Platform connectors instead of custom code
- **Built-in AI** - Leverages Copilot Studio's native Generative AI capabilities
- **Power Automate flows** - Complex operations run as cloud flows

## Generated Structure

Each transpiled agent folder contains:

```
{agent_name}/
├── agent_manifest.json     # Copilot Studio agent definition
├── instructions.md         # System prompt and behavior guidelines
├── DEPLOYMENT_GUIDE.md     # Step-by-step deployment instructions
├── topics/                 # Topic definitions (user intents)
│   ├── topic_greeting.yaml
│   ├── topic_{action}.yaml
│   └── ...
└── flows/                  # Power Automate cloud flows
    ├── flow_{action}.json
    └── ...
```

## Transpiled Agents

### Zurn Elkay Competitive Intelligence System

| Agent | Topics | Flows | Description |
|-------|--------|-------|-------------|
| zurnelkay_ci_orchestrator_agent | 1 | 0 | Level 0 coordinator for all BU agents |
| zurnelkay_drains_ci_agent | 10 | 5 | Drains competitive intelligence |
| zurnelkay_drinking_water_ci_agent | 10 | 5 | Drinking water & fountains CI |
| zurnelkay_sinks_ci_agent | 11 | 5 | Sinks & wash stations CI |
| zurnelkay_commercial_brass_ci_agent | 11 | 5 | Commercial brass/faucets CI |
| zurnelkay_wilkins_ci_agent | 10 | 5 | Wilkins backflow prevention CI |
| zurnelkay_crossbu_synthesizer_agent | 8 | 5 | Cross-BU synthesis & reporting |

## Deployment Steps

### 1. Prerequisites
- Microsoft Copilot Studio license
- Power Platform environment
- Required connectors enabled (if applicable)

### 2. Import Agent
1. Open [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create new agent or import from manifest
3. Copy `instructions.md` content to agent instructions

### 3. Configure Topics
1. Import topic YAML files
2. Review trigger phrases for each topic
3. Adjust as needed for your terminology

### 4. Configure Flows (if applicable)
1. Import flow JSON files to Power Automate
2. Configure connector connections
3. Link flows to corresponding topics

### 5. Test & Publish
1. Test each topic in the canvas
2. Verify flow execution
3. Publish to channels (Teams, Web, etc.)

## Connector Mappings

| Python Integration | Copilot Studio Equivalent |
|-------------------|---------------------------|
| Azure Cosmos DB | Microsoft Dataverse |
| Salesforce API | Salesforce connector |
| SharePoint API | SharePoint connector |
| Azure OpenAI | Native Generative AI |
| Outlook/Email | Office 365 Outlook connector |

## Limitations

- **Complex Python logic**: Some advanced logic may need manual flow creation
- **Custom APIs**: Require custom connectors in Power Platform
- **Sub-agent orchestration**: May need multi-topic routing

## Regenerating

To regenerate transpiled agents:

```python
from agents.copilot_studio_transpiler_agent import CopilotStudioTranspilerAgent

agent = CopilotStudioTranspilerAgent()

# Single agent
result = agent.perform(action='transpile', agent_name='zurnelkay_drains_ci_agent')

# Batch transpile
result = agent.perform(action='batch_transpile', pattern='zurnelkay')

# Create ZIP package
result = agent.perform(action='package', agent_name='zurnelkay_drains_ci_agent')
```

## Programmatic Deployment (NEW)

The transpiler now supports **direct deployment to Copilot Studio** via the Dataverse Web API.

### Setup Deployment

1. **Configure deployment credentials:**
```python
result = agent.perform(action='configure_deployment')
# Returns setup instructions and current config
```

2. **Set your Dataverse environment:**
```python
result = agent.perform(
    action='configure_deployment',
    environment_url='https://yourorg.crm.dynamics.com',
    tenant_id='your-tenant-guid',
    client_id='your-app-client-id'
)
```

### Deploy an Agent

```python
# Deploy transpiled agent to Copilot Studio
result = agent.perform(
    action='deploy',
    agent_name='zurnelkay_drains_ci_agent'
)
```

### Check Deployment Status

```python
# Check all deployments
result = agent.perform(action='deploy_status')

# Check specific agent
result = agent.perform(action='deploy_status', agent_name='zurnelkay_drains_ci_agent')
```

### Required Azure AD App Registration

1. Create app in Azure Portal → Azure AD → App registrations
2. Add Dataverse API permission (user_impersonation)
3. Create client secret (for service principal auth)
4. Add app as application user in Power Platform Admin Center
5. Assign System Customizer or higher role

### Environment Variables (Alternative to Config)

```bash
DATAVERSE_ENVIRONMENT_URL=https://yourorg.crm.dynamics.com
AZURE_TENANT_ID=your-tenant-guid
COPILOT_STUDIO_CLIENT_ID=your-app-client-id
COPILOT_STUDIO_CLIENT_SECRET=your-secret  # Optional for interactive auth
```

