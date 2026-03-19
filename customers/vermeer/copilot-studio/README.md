# Vermeer - Copilot Studio Agents

This folder tracks Copilot Studio agents deployed for Vermeer.

## Deployed Agents

| Agent Name | Environment | Status | Last Published |
|------------|-------------|--------|----------------|
| Vermeer Machine Walkaround | Development | 🔄 In Progress | - |
| Vermeer Dealer Support | Development | 🔄 In Progress | - |
| Vermeer Dealer Analytics | Development | 🔄 In Progress | - |
| Vermeer Product Registration | Development | 🔄 In Progress | - |
| Vermeer Order Tracker | Development | 🔄 In Progress | - |
| Vermeer Warranty Lookup | Development | 🔄 In Progress | - |

## Agent Configuration

Each agent has a corresponding configuration file in YAML format:
- `{agent-name}.yaml` - Agent definition and topic configuration
- `{agent-name}-topics/` - Individual topic files (if exported)

## Model Configuration

| Agent Type | Model | Reasoning |
|------------|-------|-----------|
| All Agents | GPT-4.1 | Dealer-facing, fast responses |

## Dealer Network Integration

Agents support Vermeer's dealer network:
- Machine walkaround inspections
- Dealer support and analytics
- Order tracking and warranty lookup

## Sync with RAPP Agent Repo

Local agents in `../agents/` are automatically synced to:
- Repository: `billwhalenmsft/RAPP-Agent-Repo`
- Path: `agents/@billwhalen/customer-vermeer/`

Use `ProjectTracker` with `action="close_project"` to push changes.
