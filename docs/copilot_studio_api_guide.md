# Copilot Studio Programmatic Configuration Guide

This document summarizes what can and cannot be configured programmatically via the Dataverse Web API for Copilot Studio agents.

## ✅ Fully Automatable via API

### Bot/Agent Entity Properties
| Property | Description | API Field |
|----------|-------------|-----------|
| Name | Display name of the agent | `name` |
| Schema Name | Unique identifier | `schemaname` |
| Language | Primary language (1033 = en-us) | `language` |
| Authentication Mode | None (0), Integrated (2) | `authenticationmode` |
| Authentication Trigger | As Needed (0), Always (1) | `authenticationtrigger` |
| Icon | Base64 encoded image | `iconbase64` |
| State | Active (0) | `statecode` |

### Bot Configuration (JSON in `configuration` field)

**CRITICAL:** The `aISettings.useModelKnowledge` setting MUST be `true` for agents to use generative AI capabilities. Without this, agents will respond with "Sorry, I am not able to find a related topic" for any query that doesn't exactly match a topic trigger phrase.

```json
{
  "$kind": "BotConfiguration",
  "channels": [{"$kind": "ChannelDefinition", "channelId": "MsTeams"}],
  "gPTSettings": {"defaultSchemaName": "schema.gpt.default"},
  "isLightweightBot": false,
  "aISettings": {
    "$kind": "AISettings",
    "useModelKnowledge": true,         // REQUIRED: Enable AI for unmatched queries
    "isSemanticSearchEnabled": true,    // Enable semantic search
    "isFileAnalysisEnabled": true,      // Enable document analysis
    "contentModeration": "Medium",      // Content moderation level
    "optInUseLatestModels": true,       // Use latest AI models
    "generativeAnswersEnabled": true,   // Enable generative answers
    "boostedConversationsEnabled": true // Enable boosted conversations
  },
  "settings": {
    "orchestrationType": "Generative"   // Use generative orchestration
  }
}
```

#### Key AI Settings Explained
| Setting | Required | Description |
|---------|----------|-------------|
| `useModelKnowledge` | **YES** | Enables AI to handle queries that don't match topics. If `false`, agent will fail on unmatched queries. |
| `isSemanticSearchEnabled` | Recommended | Enables semantic search across knowledge sources |
| `generativeAnswersEnabled` | Recommended | Enables generative answers for better coverage |
| `boostedConversationsEnabled` | Recommended | Improves conversational AI capabilities |
| `orchestrationType` | Recommended | Set to "Generative" for best results |

### Custom GPT Component (Type 15) - AI Instructions
```yaml
kind: GptComponentMetadata
instructions: |-
  Your AI system prompt here...
responseInstructions:
gptCapabilities:
  webBrowsing: true
  codeInterpreter: false
aISettings:
  model:
    kind: CurrentModels
displayName: Agent Name
conversationStarters:
  - title: Example
    text: "Sample starter"
```

### Topics (Type 9 - "Language")
Full topic YAML including:
- Trigger phrases
- Actions and dialogs
- Variables
- Conditions
- Message nodes

### Actions (Type 17)
```yaml
kind: ExternalTriggerConfiguration
externalTriggerSource:
  kind: WorkflowExternalTrigger
  flowId: <power-automate-flow-id>
```

### Knowledge Sources (Type 16 - "Connector")
```yaml
kind: KnowledgeSourceConfiguration
source:
  kind: PublicSiteSearchSource
  site: https://example.com/
```

### API Operations
- `PvaProvision` - Provision agent for publishing
- `PvaPublish` - Publish agent to channels

## ⚠️ Partially Automatable

### Sub-Agents/Agent Routing
**What CAN be automated:**
- Instructions that describe routing behavior
- Topic triggers that mention routing to other agents

**What CANNOT be automated:**
- The actual "Agents" tab configuration in Copilot Studio
- Associating sub-agents with an orchestrator

**Workaround:** 
Sub-agent routing currently requires manual configuration in Copilot Studio UI OR custom topic creation that invokes another agent via Power Automate.

### Connectors (OAuth-based)
**What CAN be automated:**
- Basic connector component creation

**What CANNOT be automated:**
- OAuth authentication flows
- Connection configuration requiring user consent

## ❌ Requires Manual Configuration

1. **Sub-agent associations** - Must add agents in the Agents tab manually
2. **OAuth connector authentication** - Requires interactive consent
3. **Teams/M365 app manifest** - Generated but requires admin approval
4. **Custom model configurations** - Azure OpenAI or custom model setup
5. **Environment-specific security** - DLP policies, security roles

## Implementation Recommendations

### For Turnkey Deployment

1. **Use API for:**
   - Creating all agents
   - Setting instructions (Custom GPT component)
   - Creating topics
   - Provisioning and publishing

2. **Document manual steps for:**
   - Adding sub-agents to orchestrator (5 minutes per orchestrator)
   - Setting up OAuth connectors
   - Teams app approval

3. **Create helper scripts for:**
   - Validating deployment
   - Checking component configuration
   - Generating reports

### Example Deployment Script Output
```
✓ Created 7 ZE agents
✓ Added Custom GPT components with instructions
✓ Provisioned all agents
✓ Published all agents

MANUAL STEPS REQUIRED:
1. Open ZE CI Orchestrator in Copilot Studio
2. Go to Agents tab
3. Add the following agents:
   - ZE Drains CI
   - ZE Drinking Water CI
   - ZE Sinks CI
   - ZE Commercial Brass CI
   - ZE Wilkins CI
   - ZE Cross-BU Synthesizer
4. Set descriptions for routing
```

## API Endpoints Reference

### Create Agent
```
POST /api/data/v9.2/bots
```

### Create Component
```
POST /api/data/v9.2/botcomponents
```

### Provision Agent
```
POST /api/data/v9.2/bots({botid})/Microsoft.Dynamics.CRM.PvaProvision
```

### Publish Agent
```
POST /api/data/v9.2/bots({botid})/Microsoft.Dynamics.CRM.PvaPublish
```

## Component Types Reference

| Type | Name | Description |
|------|------|-------------|
| 0 | Topic | Dialog topics |
| 1 | Skill | Virtual agent skills |
| 2 | Bot Variable | Global variables |
| 9 | Language | Language-specific content |
| 10 | Bot Translations | Translation content |
| 14 | Copilot Plugin | Plugins (files, etc.) |
| 15 | Custom GPT | AI instructions and settings |
| 16 | Copilot Connector | Knowledge sources |
| 17 | Copilot Action | Power Automate actions |
| 18 | Copilot Settings | Agent settings |
