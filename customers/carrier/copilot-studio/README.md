# Carrier - Copilot Studio Agents

This folder tracks Copilot Studio agents deployed for Carrier.

## Deployed Agents

| Agent Name | Environment | Status | Last Published |
|------------|-------------|--------|----------------|
| Carrier Case Triage Orchestrator | Production | ✅ Active | - |
| Carrier Case Analyzer | Production | ✅ Active | - |
| Carrier SF Case Monitor | Production | ✅ Active | - |
| Carrier SF Writer | Production | ✅ Active | - |
| Carrier Summary Generator | Production | ✅ Active | - |
| Carrier Attachment Processor | Production | ✅ Active | - |
| Carrier Product Enrichment | Production | ✅ Active | - |

## Agent Configuration

Each agent has a corresponding configuration file in YAML format:
- `{agent-name}.yaml` - Agent definition and topic configuration
- `{agent-name}-topics/` - Individual topic files (if exported)

## Model Configuration

| Agent Type | Model | Reasoning |
|------------|-------|-----------|
| Orchestrator | GPT-5 Auto (o3) | Complex routing and reasoning |
| Sub-agents | GPT-4.1 | Fast, reliable responses |

## Salesforce Integration

All agents integrate with Carrier's Salesforce instance:
- Case monitoring and triage
- Attachment processing
- Summary generation and enrichment

## Sync with RAPP Agent Repo

Local agents in `../agents/` are automatically synced to:
- Repository: `billwhalenmsft/RAPP-Agent-Repo`
- Path: `agents/@billwhalen/customer-carrier/`

Use `ProjectTracker` with `action="close_project"` to push changes.
