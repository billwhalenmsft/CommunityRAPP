# MCS (Microsoft Copilot Studio) Templates

This directory contains templates for creating Copilot Studio agents in the MCS format. The MCS format is the native file format used by the Copilot Studio CLI for importing/exporting agents.

## Template Files

### Agent Definition
- **`agent.mcs.yml.template`** - GPT component metadata (instructions, conversation starters)
- **`settings.mcs.yml.template`** - Agent configuration (auth, channels, AI settings)

### Topic Templates
- **`topics/ConversationStart.mcs.yml.template`** - Initializes conversation (ACTIVE)
- **`topics/OnError.mcs.yml.template`** - Error handling (ACTIVE)
- **`topics/Fallback.mcs.yml.template`** - Unknown intent handler (DISABLED)
- **`topics/Main.mcs.yml.template`** - Catch-all message handler for RAPP backend routing

### Bot Definition
- **`botdefinition.json.template`** - Complete bot definition with all components (used for API deployment)

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `${AGENT_NAME}` | Display name of the agent | "ZE Drains CI" |
| `${SCHEMA_NAME}` | Unique schema name | "rapp_ZE_Drains_CI_20260127" |
| `${INSTRUCTIONS}` | Agent instructions/system prompt | "You are a competitive intelligence analyst..." |
| `${STARTER_1_TITLE}` | First conversation starter title | "Get Report" |
| `${STARTER_1_TEXT}` | First conversation starter text | "Generate a quarterly CI report" |
| `${BOT_ID}` | GUID for the bot | "f75ed58f-a2fb-f011-8407-000d3a316172" |
| `${FLOW_ID}` | Power Automate flow ID for RAPP backend | "ced8f731-2fef-ef11-be20-6045bd06598d" |
| `${PUBLISHER}` | Publisher unique name | "DefaultPublisher" |

## Key Design Decisions

### Topics That Should Be ACTIVE
1. **Conversation Start** - Initializes variables when conversation begins
2. **On Error** - Handles errors gracefully

### Topics That Should Be DISABLED (Inactive)
1. **Fallback** - Causes "I'm sorry, I'm not sure how to help" messages
2. **End of Conversation** - Interrupts flow with survey prompts
3. **Multiple Topics Matched** - Causes clarification prompts
4. **Escalate** - Not needed for RAPP agents
5. **Greeting** - Can conflict with generative AI
6. **Goodbye** - Can trigger unwanted responses
7. **Thank you** - Can trigger unwanted responses
8. **Start Over** - Can reset conversation unexpectedly
9. **Sign in** - Handle auth at channel level instead
10. **Lesson 1/2/3** - Tutorial topics that should never be active

## Usage

### Generating an Agent from Template

```python
from utils.mcs_generator import MCSGenerator

generator = MCSGenerator()
agent_config = generator.generate_agent(
    name="ZE Drains CI",
    instructions="You are a competitive intelligence analyst for drainage products...",
    conversation_starters=[
        {"title": "Get Report", "text": "Generate a quarterly CI report for drains"}
    ]
)

# Deploy to Copilot Studio
generator.deploy_agent(agent_config)
```

### Using Copilot Studio CLI

```bash
# Install CLI
npm install -g @microsoft/m365agentstoolkit-cli

# Import agent
atk copilot import --path ./my-agent --environment-url https://org.crm.dynamics.com
```

## Best Practices

1. **Always disable Fallback** - It produces "I'm sorry" messages that interrupt generative AI
2. **Use OnActivity for catch-all** - The Main topic catches ALL messages, bypassing topic matching
3. **Minimize active topics** - Only keep essential topics active to prevent conflicts
4. **Pre-configure topic states** - Set `state: "Inactive"` in botdefinition.json for disabled topics
5. **Use conversation history** - Store chat context in `Global.VarConversationHistory` for context-aware responses
