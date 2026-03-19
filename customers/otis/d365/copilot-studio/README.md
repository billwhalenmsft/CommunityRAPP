# Copilot Studio Deployment Guide for Otis Service Copilot

This directory contains everything needed to programmatically deploy the Otis Service Copilot to Microsoft Copilot Studio.

## Two Deployment Options

### Option A: Direct API Deployment (Fastest)

Use the Python script to deploy directly via Dataverse API:

```powershell
# Prerequisites
az login  # Authenticate to Azure

# Preview what will be deployed
python scripts/Deploy-CopilotStudioAgent.py --preview

# Deploy the agent
python scripts/Deploy-CopilotStudioAgent.py
```

**What it creates:**
- Otis Service Copilot agent with instructions
- 5 demo topics (Entrapment, Door Issues, Billing, Modernization, PM)
- Configured for UK English (EMEA)

### Option B: YAML + VS Code Extension (More Control)

Use the Skills for Copilot Studio plugin with VS Code:

#### Prerequisites

1. Install [VS Code Copilot Studio Extension](https://github.com/microsoft/vscode-copilotstudio)
2. Install the Skills for Copilot Studio plugin:
   ```
   /plugin marketplace add microsoft/skills-for-copilot-studio
   /plugin install copilot-studio@skills-for-copilot-studio
   ```

#### Workflow

1. **Create empty agent in Copilot Studio UI** (required first step)
   - Go to https://copilotstudio.microsoft.com
   - Create new agent named "Otis Service Copilot"

2. **Clone the agent locally** using VS Code Extension
   - Open VS Code with Copilot Studio extension
   - Clone your new empty agent to `copilotstudioclones/otis-service-copilot/`

3. **Copy our YAML files** into the cloned directory:
   ```powershell
   Copy-Item .\agent.mcs.yml $HOME\copilotstudioclones\otis-service-copilot\
   Copy-Item .\topics\*.mcs.yml $HOME\copilotstudioclones\otis-service-copilot\topics\
   ```

4. **Use Skills plugin to refine** (optional):
   ```
   @copilot-studio:author Review and enhance the Otis Service Copilot topics
   @copilot-studio:test Test the entrapment response topic with these prompts...
   @copilot-studio:troubleshoot Why isn't the billing topic triggering?
   ```

5. **Push changes** via VS Code Extension

6. **Publish** in Copilot Studio UI

## File Structure

```
copilot-studio/
├── agent.mcs.yml              # Main agent configuration (YAML)
├── copilot-config.json        # Detailed configuration (JSON)
├── topics/
│   ├── entrapment-response.mcs.yml
│   ├── door-troubleshooting.mcs.yml
│   ├── billing-verification.mcs.yml
│   ├── modernization-handoff.mcs.yml
│   └── pm-coordination.mcs.yml
└── README.md                  # This file
```

## Agent Topics

| Topic | Purpose | Key KB Articles |
|-------|---------|-----------------|
| **Entrapment Response** | Emergency rescue situations | KB-001247, KB-002156 |
| **Door Troubleshooting** | Door operator issues | KB-002104 |
| **Billing Verification** | Contract coverage disputes | KB-001050 |
| **Modernization Handoff** | Sales opportunity identification | KB-003145 |
| **PM Coordination** | Scheduled maintenance coordination | - |

## Post-Deployment Configuration

After deploying via either method, complete these manual steps in Copilot Studio:

### 1. Add Knowledge Sources

1. Open your agent in Copilot Studio
2. Go to **Knowledge** → **Add knowledge source**
3. Select **Dataverse** → **Knowledge Articles**
4. Set filter: `statecode eq 3` (Published only)
5. Enable for agent assistance

### 2. Configure Customer Service Workspace Integration

1. Go to **Channels** → **Customer Service workspace**
2. Enable the integration
3. Test Copilot availability in CSW

### 3. Test Demo Scenarios

Test each hero case scenario:

| Case | Test Prompt |
|------|-------------|
| CAS-19121-P9C5M0 | "Someone is trapped in an elevator at a hospital" |
| CAS-19122-M4V0M1 | "The elevator door keeps reversing and won't close" |
| CAS-19123-Q8K5Z7 | "Customer wants to upgrade their freight elevators" |
| CAS-19129-N0B2P3 | "Customer was charged for a repair that should be covered" |
| CAS-19125-X8P0V5 | "Need to confirm details for scheduled maintenance visit" |

## Troubleshooting

### Agent not appearing in Copilot Studio
- Verify deployment completed successfully
- Check the `data/deployment-record.json` for bot ID
- Search by schema name: `cr328_otisservicecopilot`

### Topics not triggering correctly
- Use `@copilot-studio:troubleshoot` to debug
- Check trigger phrases match user queries
- Verify topic priority settings

### KB articles not surfacing
- Ensure articles are Published (statecode=3)
- Verify knowledge source filter is correct
- Check that KB-00xxxx articles exist in Dataverse

## Related Resources

- [Skills for Copilot Studio Blog](https://microsoft.github.io/mcscatblog/posts/skills-for-copilot-studio/)
- [GitHub: skills-for-copilot-studio](https://github.com/microsoft/skills-for-copilot-studio)
- [Copilot Studio Documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
- [RAPP Copilot Studio API](../../../utils/copilot_studio_api.py)
