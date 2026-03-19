# Zurn Elkay - Copilot Studio Agents

This folder tracks Copilot Studio agents deployed for Zurn Elkay.

## Deployed Agents

| Agent Name | Environment | Status | Last Published |
|------------|-------------|--------|----------------|
| ZE Drains Contract Intelligence | Production | ✅ Active | 2026-03-13 |
| ZE Drinking Water Contract Intelligence | Production | ✅ Active | 2026-03-13 |
| ZE Sinks Contract Intelligence | Production | ✅ Active | 2026-03-13 |
| ZE Commercial Brass Contract Intelligence | Production | ✅ Active | 2026-03-13 |
| ZE Wilkins Contract Intelligence | Production | ✅ Active | 2026-03-13 |
| ZE CrossBU Synthesizer | Production | ✅ Active | 2026-03-13 |
| ZE CI Orchestrator | Production | ✅ Active | 2026-03-13 |

## Agent Configuration

Each agent has a corresponding configuration file in YAML format:
- `{agent-name}.yaml` - Agent definition and topic configuration
- `{agent-name}-topics/` - Individual topic files (if exported)

## Model Configuration

| Agent Type | Model | Reasoning |
|------------|-------|-----------|
| Orchestrator | GPT-5 Auto (o3) | Complex routing and reasoning |
| Sub-agents | GPT-4.1 | Fast, reliable responses |

## Deployment Notes

- All agents use Azure OpenAI integration
- Connected to Azure AI Search indexes for RAG
- Topics configured with proper trigger phrases
- Published via Dataverse API

## Sync with RAPP Agent Repo

Local agents in `../agents/` are automatically synced to:
- Repository: `billwhalenmsft/RAPP-Agent-Repo`
- Path: `agents/@billwhalen/customer-zurnelkay/`

Use `ProjectTracker` with `action="close_project"` to push changes.
