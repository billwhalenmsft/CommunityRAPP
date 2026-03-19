# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Copilot Entra Agent is an enterprise AI assistant built on Azure Functions with GPT-4 integration. It features a modular agent architecture with persistent memory across sessions using Azure File Storage. The system supports multi-user conversations with user-specific and shared memory contexts.

**Deployment Options:**
- **Standalone Mode**: Direct API access via Azure Functions (REST endpoint)
- **Power Platform Integration**: Full Microsoft 365 integration via Copilot Studio, Power Automate, Teams, and M365 Copilot

## RAPP Pipeline

This repository includes the **RAPP (Rapid AI Agent Production Pipeline)** - a 14-step methodology for building production-ready AI agents with quality gates at each stage.

**FASTEST PATH - Transcript to Agent (NEW):**
```
1. Drop transcript:  rapp_projects/{project_id}/inputs/transcript.txt (or pass inline)
2. Call RAPP:        action="transcript_to_agent", project_id="your-project", customer_name="Sony Music"
3. All outputs in:   rapp_projects/{project_id}/outputs/
                     ├── {agent_id}_agent.py      # Agent code
                     ├── {agent_id}_demo.json     # Demo JSON
                     ├── agent_tester.html        # HTML tester page (test both real agent + demo)
                     └── result.json              # Metadata
4. Test locally:     Open agent_tester.html in browser
5. Also deployed:    agents/ and demos/ folders (for immediate use)
```

This generates a complete, deployable agent + demo + HTML tester from a single transcript - ready for immediate testing.

**Full Pipeline - Automated Workflow:**
```
1. Create folder: rapp_projects/{project_id}/inputs/
2. Drop files:    discovery_transcript.txt, customer_feedback.txt, etc.
3. Call agent:    RAPP with action="auto_process", project_id="your-project"
4. Get reports:   Professional PDFs in rapp_projects/{project_id}/outputs/
```

**Manual Quick Start:**
```bash
# Use the Claude Code agent
/rapp

# Or run the test script
python test_rapp_pipeline_aibast.py
```

**Pipeline Agents:**
- `RAPP` - Unified agent for ALL RAPP Pipeline operations (auto-process, discovery, MVP, code generation, quality gates QG1-QG6, PDF reports)
- `ProjectTracker` - Persist project progress and engagement data

**RAPP Agent Actions:**
- **Fast Path (NEW):** `transcript_to_agent` (transcript → deployable agent + demo in one step)
- **Automated:** `auto_process` (scans inputs, processes, generates PDF reports), `generate_report`
- Discovery: `prepare_discovery_call`, `process_transcript`, `generate_discovery_summary`
- MVP: `generate_mvp_poke`, `prioritize_features`, `define_scope`, `estimate_timeline`, `generate_full_mvp_document`
- Code: `generate_agent_code`, `generate_agent_metadata`, `generate_agent_tests`, `generate_deployment_config`, `review_code`
- Quality Gates: `execute_quality_gate` (with gate=QG1-QG6)
- Pipeline: `get_step_guidance`, `get_pipeline_status`, `recommend_next_action`, `get_step_checklist`, `validate_step_completion`

**transcript_to_agent Parameters:**
| Parameter | Description |
|-----------|-------------|
| `transcript` | Inline transcript text (OR use project_id to read from storage) |
| `project_id` | Project ID - outputs go to `rapp_projects/{project_id}/outputs/` |
| `customer_name` | Customer/company name for context |
| `agent_priority` | Which agent to prioritize (e.g., 'contract', 'chargeback', 'social_media') |
| `deploy_to_storage` | If true (default), saves to project folder + main folders |
| `deploy_to_main_folders` | If true (default), also deploys to `agents/` and `demos/` folders |

**Input File Detection (for auto_process):**
| Input Type | Matching Patterns |
|------------|-------------------|
| Discovery transcript | `transcript`, `discovery`, `call_notes`, `meeting_notes` |
| Customer feedback | `feedback`, `customer_response`, `validation`, `approval` |
| Code to review | `*.py` |
| Deployment metrics | `metrics`, `telemetry`, `usage`, `health` |

**Output Reports (Microsoft-style PDFs):**
- `discovery_report.pdf` - Structured discovery analysis
- `qg1_report.pdf` through `qg6_report.pdf` - Quality gate validations
- `mvp_report.pdf` - Customer-ready MVP proposal
- `code_report.pdf` - Agent code generation summary
- `executive_summary_report.pdf` - Overall project status

**Documentation:**
- Full guide: `docs/RAPP_PIPELINE_GUIDE.md`
- Claude agent: `.claude/agents/rapp-pipeline-guide.md`
- Slash commands: `/rapp`, `/rapp-step N`

## Development Commands

### Running Locally

**Mac/Linux:**
```bash
./run.sh
```

**Windows:**
```powershell
.\run.ps1
```

The local API endpoint will be available at: `http://localhost:7071/api/businessinsightbot_function`

### Testing the API

**curl (Mac/Linux):**
```bash
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

**PowerShell (Windows):**
```powershell
Invoke-RestMethod -Uri "http://localhost:7071/api/businessinsightbot_function" `
  -Method Post `
  -Body '{"user_input": "Hello", "conversation_history": []}' `
  -ContentType "application/json"
```

### Environment Setup

- **Python version:** 3.11 (required for Azure Functions v4 compatibility)
- **Virtual environment:** `.venv/` (created automatically by setup scripts)
  ```bash
  # Activate virtual environment
  source .venv/bin/activate  # Mac/Linux
  .venv\Scripts\activate     # Windows
  ```
- **Dependencies:** Install with `pip install -r requirements.txt`
- **Configuration:** `local.settings.json` contains all Azure service credentials and settings (auto-generated by deployment script, never commit this file)

### Storage Configuration

By default, local development uses **cloud storage** (same as production). This means:
- No syncing required between local and production
- Changes made locally are immediately reflected in production
- Requires `az login` for authentication

**Environment variable in `local.settings.json`:**
```json
"USE_CLOUD_STORAGE": "true"   // Use Azure File Storage (default)
"USE_CLOUD_STORAGE": "false"  // Use local .local_storage/ folder
```

**To use local storage instead:**
1. Set `USE_CLOUD_STORAGE` to `"false"` in `local.settings.json`
2. Sync cloud data to local: `python sync_cloud_storage.py`

**Sync script commands:**
```bash
python sync_cloud_storage.py              # Download cloud → local
python sync_cloud_storage.py --upload     # Upload local → cloud
python sync_cloud_storage.py --status     # Show sync status
python sync_cloud_storage.py --dry-run    # Preview without changes
```

### Running Tests

```bash
# Run all unit tests (mocked, no API keys needed)
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py -v

# Run live API tests (requires environment variables)
python tests/run_tests.py --live

# Run specific scenario
python tests/run_tests.py --scenario capital-markets
python tests/run_tests.py --scenario call-center

# Run only unit tests (skip live)
python tests/run_tests.py --unit-only

# Save results to JSON
python tests/run_tests.py --save-results results.json
```

### Development Tools

**Checking logs:**
```bash
# View function logs in real-time
func start --verbose

# Check Azure Function App logs
az functionapp log tail --name YOUR_FUNCTION_APP --resource-group YOUR_RESOURCE_GROUP
```

**Local debugging:**
- Set breakpoints in VS Code with Azure Functions extension
- Use `logging.info()` and `logging.error()` for debug output
- Check `/tmp/agents` and `/tmp/multi_agents` for runtime-loaded agent files

## Architecture

### Full Stack Architecture

The complete solution spans multiple layers when deployed with Power Platform integration:

**User Interface Layer:**
- Microsoft 365 Copilot (M365 chat integration)
- Microsoft Teams (standalone bot or embedded)
- Web Interface (custom HTML/React applications)

**Conversation Layer:**
- Copilot Studio: Natural language processing, conversation management, user authentication
- Handles dialog flow, intent recognition, and context maintenance

**Integration Layer:**
- Power Automate: User context from Office 365, data transformation, error handling
- Connects Copilot Studio to Azure Functions
- Manages authentication and data flow between systems

**Processing Layer:**
- Azure Functions: Agent selection & routing, memory management, Azure OpenAI integration
- Core business logic and agent orchestration
- Stateless execution with persistent storage

**Agent Layer:**
- CRM Agents (Dynamics 365, Salesforce)
- Document Agents (SharePoint, OneDrive)
- Email Agents (Outlook integration)
- Calendar Agents (meeting management)
- Custom Agents (business-specific logic)

**Data Layer:**
- Azure Storage (agent memory and file storage)
- Azure OpenAI (GPT-4o for AI processing)
- CRM Systems (business data)

### Core Components

**function_app.py (main entry point):**
- Azure Function HTTP trigger endpoint: `businessinsightbot_function`
- `Assistant` class orchestrates the AI conversation flow
- Dynamic agent loading from both local `agents/` folder and Azure File Storage (`agents/` and `multi_agents/` shares)
- GUID-based user context management with default GUID: `c0p110t0-aaaa-bbbb-cccc-123456789abc`
- Dual-response system: formatted markdown response + concise voice response (split by `|||VOICE|||` delimiter)

**Agent System:**
- All agents inherit from `BasicAgent` (agents/basic_agent.py)
- Agents define `name`, `metadata` (JSON schema for OpenAI function calling), and `perform(**kwargs)` method
- Built-in agents:
  - `ContextMemoryAgent`: Recalls conversation history (shared + user-specific memories)
  - `ManageMemoryAgent`: Stores facts, preferences, insights, and tasks to memory
  - `GithubAgentLibraryManager`: Manages agent library downloads and installations
  - `ScriptedDemoAgent`: Provides interactive demos and walkthroughs
- Custom agents can be added to `agents/` folder or uploaded to Azure File Storage

**Agent Filtering (Per-User):**
- Users can enable/disable specific agents via `agent_config/{user_guid}/enabled_agents.json`
- Format: JSON array of agent filenames (e.g., `["context_memory_agent.py", "manage_memory_agent.py"]`)
- If no config exists, all agents are loaded by default
- Useful for limiting functionality per user or testing specific agents

**Memory System:**
- Dual-layer memory: shared (all users) + user-specific (per GUID)
- Storage: Azure File Share via `AzureFileStorageManager` (utils/azure_file_storage.py)
- User context switching: Send a GUID as the first message or in `user_input` to load user-specific memory
- Memory trimming: Conversation history limited to last 20 messages to prevent memory overflow

### Request Flow

**Standalone Mode (Direct API):**
1. HTTP request → `businessinsightbot_function` endpoint
2. Load agents from local folder + Azure File Storage
3. Create `Assistant` instance with user GUID (from request or default)
4. Initialize context memory (shared + user-specific)
5. Prepare messages with system prompt containing memory contexts
6. Call Azure OpenAI with function definitions (agent metadata)
7. If function called: execute agent → add result to conversation → get final response
8. Parse response into formatted + voice parts
9. Return JSON: `{"assistant_response": "...", "voice_response": "...", "agent_logs": "...", "user_guid": "..."}`

**Power Platform Mode (Teams/M365 Copilot):**
1. User message in Teams/M365 Copilot → Copilot Studio
2. Copilot Studio processes intent → triggers Power Automate flow
3. Power Automate enriches with user context (Office 365 profile)
4. HTTP POST to Azure Function with user context
5. Azure Function processes (steps 2-8 from above)
6. Response returns to Power Automate
7. Power Automate formats response for Copilot Studio
8. Copilot Studio displays in Teams/M365 Copilot chat
9. User sees formatted response with agent actions

**Data Flow Diagram:**
```
[User] ─────→ [Copilot Studio] ─────→ [Power Automate] ─────→ [Azure Function]
   ↑                                                                    │
   │                                                                    ↓
   │                                                          [Azure OpenAI]
   │                                                                    │
   │                                                                    ↓
   │                                                             [Agent Layer]
   │                                                                    │
   │                                                                    ↓
   └──────────← [Copilot Studio] ←──────── [Power Automate] ←── [Response]
```

### Key Design Patterns

**String Safety:**
- All message content sanitized via `ensure_string_content()` to prevent None/undefined errors
- Function arguments stringified via `ensure_string_function_args()`
- Default values for all potentially None values

**CORS Handling:**
- All responses include CORS headers via `build_cors_response()`
- OPTIONS preflight requests supported

**Error Handling:**
- Retry logic (max 3 attempts) for OpenAI API calls
- Agent loading failures logged but don't crash the app
- Graceful degradation when memory initialization fails

**Intentionally Invalid Default GUID (Database Insertion Guardrail):**
- Default GUID: `c0p110t0-aaaa-bbbb-cccc-123456789abc`
- Contains non-hex characters ('p', 'l') that visually spell "copilot"
- **This is a security feature, not a bug!**
- Purpose:
  1. **Prevents accidental persistence**: Any database with UUID column validation will reject this value, preventing placeholder data from polluting production user tables
  2. **Clear marker**: Instantly recognizable in logs/debugging as "no real user context" rather than a legitimate user ID
  3. **Fails loudly**: UUID parsing libraries reject it, surfacing issues early rather than silently storing garbage data
  4. **Memory isolation**: Storage managers treat this specially, routing to shared memory without creating spurious user directories
- When you need a valid UUID for testing, generate one properly
- This default exists solely for anonymous/unauthenticated sessions

## Configuration

### Environment Variables (local.settings.json)

Required settings:
- `AZURE_OPENAI_API_KEY`: Azure OpenAI service key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL (e.g., "https://your-resource.cognitiveservices.azure.com/" for AI Services, or "https://your-resource.openai.azure.com/" for legacy OpenAI resources)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Model deployment name (e.g., "gpt-4o", "gpt-5.1-chat")
- `AZURE_OPENAI_API_VERSION`: API version (e.g., "2024-08-01-preview")
- `AzureWebJobsStorage`: Azure Storage connection string for file shares
- `ASSISTANT_NAME`: Bot display name (default: "Copilot Entra Agent")
- `CHARACTERISTIC_DESCRIPTION`: Bot personality and capabilities description

**Example local.settings.json structure:**
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=...",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_API_KEY": "your-openai-api-key",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.cognitiveservices.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",
    "ASSISTANT_NAME": "My Custom Assistant",
    "CHARACTERISTIC_DESCRIPTION": "A helpful enterprise AI assistant"
  }
}
```

**Note:** The setup scripts automatically generate this file with proper values from your Azure deployment.

### Web Interface

`index.html` provides a full-featured chat UI with:
- Multi-user support (GUID-based sessions)
- Voice synthesis for voice responses
- Markdown rendering with syntax highlighting
- Code block copy functionality
- Mobile-responsive design

## Adding Custom Agents

Create a new file in `agents/` folder:

```python
from agents.basic_agent import BasicAgent

class MyCustomAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyCustom'
        self.metadata = {
            "name": self.name,
            "description": "What this agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        input_data = kwargs.get('input', '')
        # Your logic here
        return f"Processed: {input_data}"
```

Agents are automatically loaded on function startup. To access Azure storage or other services, import `AzureFileStorageManager` from `utils.azure_file_storage`.

**Uploading Custom Agents to Azure Storage:**
```python
from utils.azure_file_storage import AzureFileStorageManager

storage = AzureFileStorageManager()

# Upload to agents/ share
with open('my_custom_agent.py', 'r') as f:
    agent_code = f.read()
    storage.write_file('agents', 'my_custom_agent.py', agent_code)

# Upload to multi_agents/ share (for coordinated agents)
storage.write_file('multi_agents', 'orchestrator_agent.py', orchestrator_code)
```

**Enabling Agents Per User:**
```python
import json

# Create agent filter for a specific user
enabled_agents = ["context_memory_agent.py", "my_custom_agent.py"]
config = json.dumps(enabled_agents)

storage.write_file('agent_config/USER_GUID', 'enabled_agents.json', config)
```

## D365 Demo Prep Engine

The `d365/` directory contains a complete Dynamics 365 Customer Service demo provisioning engine. It includes PowerShell scripts for Dataverse data creation and Python utilities for validation and config management.

### Directory Structure

```
d365/
  scripts/           — 25 numbered PowerShell provisioning scripts + utilities
    DataverseHelper.psm1  — Shared module (auth, CRUD, Find-OrCreate-Record)
    00-Setup.ps1          — Orchestrator (supports -From N, -Only N, -Customer name)
    01-Accounts.ps1 … 25-ServiceToolkitForms.ps1
    check-*.ps1, fix-*.ps1, debug-*.ps1  — Diagnostic utilities
  templates/         — Jinja2 templates for demo script generation
  utils/             — Python utilities (config_loader, dataverse_auth)
```

### Customer D365 Assets

Each customer can have D365-specific assets under `customers/<name>/d365/`:

```
customers/zurnelkay/d365/
  config/environment.json    — Brands, tiers, SLA timings, org URL
  data/                      — Exported record IDs from provisioning
  demo-assets/               — Demo scripts, guides, custom page YAML, web resources
  copilot-studio/            — Copilot Studio agent YAML topics
```

### D365DemoPrep Agent

The `D365DemoPrep` agent (in `agents/d365_demo_prep_agent.py`) provides:

| Action | Description |
|--------|-------------|
| `list_customers` | Show customers with D365 configurations |
| `get_config` | Return a customer's environment.json |
| `validate_environment` | Check D365 org for expected demo data |
| `provision_data` | Create core demo records (accounts, contacts) |
| `run_powershell` | Execute a numbered provisioning step (1-25) |

**Prerequisites:** `az login` must be completed for Dataverse token acquisition.

**Example usage via chat:**
- "Use D365DemoPrep to list customers"
- "Validate the D365 environment for zurnelkay"
- "Provision demo data for zurnelkay"
- "Run PowerShell step 7 for zurnelkay"

### Running PowerShell Scripts Directly

```powershell
cd d365/scripts

# Full setup (all steps)
.\00-Setup.ps1 -Customer zurnelkay

# Resume from step 7
.\00-Setup.ps1 -From 7 -Customer zurnelkay

# Run only step 5
.\00-Setup.ps1 -Only 5 -Customer zurnelkay
```

## Deployment

The project uses Azure Resource Manager (ARM) template deployment:
- Template: `azuredeploy.json`
- Deploy script: `deploy.sh`
- Post-deployment setup scripts auto-generated with embedded credentials

Deployment provisions:
- Azure Function App (Flex Consumption plan)
- Azure OpenAI Service
- Azure Storage Account (for file shares and function state)
- Application Insights (optional monitoring)

### Deploying to Flex Consumption (Entra ID Auth Only)

This environment uses Flex Consumption plan with Entra ID authentication (no API keys for Azure services). Follow this exact procedure:

**Step 1: Ensure storage has public network access enabled**
```bash
# REQUIRED: Flex Consumption needs ongoing storage access for deployment blobs
az storage account update --name YOUR_STORAGE_ACCOUNT --resource-group YOUR_RG --public-network-access Enabled
```

**Step 2: Deploy with REMOTE build (CRITICAL)**
```bash
# MUST use --build remote, NOT --build local
# --build local creates macOS/Windows binaries that fail on Linux
# --build remote compiles packages like 'jiter' for Linux target
func azure functionapp publish YOUR_FUNCTION_APP --build remote
```

**Step 3: Verify functions are registered**
```bash
# Should show: main - [httpTrigger]
# If empty, wait 60 seconds and check admin API:
curl "https://YOUR_FUNCTION_APP.azurewebsites.net/admin/functions?code=YOUR_MASTER_KEY"
```

**Step 4: Sync triggers if functions don't appear**
```bash
az rest --method POST --uri "https://management.azure.com/subscriptions/YOUR_SUB/resourceGroups/YOUR_RG/providers/Microsoft.Web/sites/YOUR_FUNCTION_APP/syncfunctiontriggers?api-version=2022-03-01"
```

**Step 5: Test the deployed function**
```bash
# Get function key
FUNC_KEY=$(az functionapp keys list --name YOUR_FUNCTION_APP --resource-group YOUR_RG --query "functionKeys.default" -o tsv)

# Test endpoint
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Hello","conversation_history":[]}'
```

**IMPORTANT - Storage Network Access:**
- `publicNetworkAccess` must stay **ENABLED** - Flex Consumption requires it
- Security is maintained through `allowSharedKeyAccess=false` (Entra ID auth only)
- Do NOT disable public network access after deployment - function will return 500 errors

**Common Issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 during deployment | Storage public access disabled | Enable public network access |
| Functions list empty | Wrong build type | Use `--build remote` not `--build local` |
| `ModuleNotFoundError: jiter` | macOS binaries deployed to Linux | Redeploy with `--build remote` |
| 500 Internal Server Error | Storage access blocked | Enable storage public network access |
| 404 Not Found | Functions not indexed | Sync triggers and restart function app |

**Quick Deploy Script:**
```bash
# Set variables
RG="rappdec1020205v1"
FUNC="rapp-ov4bzgynnlvii"
STORAGE="stov4bzgynnlvii"

# Ensure storage access
az storage account update --name $STORAGE --resource-group $RG --public-network-access Enabled

# Deploy with remote build
func azure functionapp publish $FUNC --build remote

# Restart to ensure clean state
az functionapp restart --name $FUNC --resource-group $RG

# Get function key and test
FUNC_KEY=$(az functionapp keys list --name $FUNC --resource-group $RG --query "functionKeys.default" -o tsv)
curl -X POST "https://$FUNC.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Hello","conversation_history":[]}'
```

## Current Production Deployment

### Resource Details

| Resource | Name | Region |
|----------|------|--------|
| Function App | `rapp-ov4bzgynnlvii` | East US 2 |
| Resource Group | `rappdec1020205v1` | East US 2 |
| Storage Account | `stov4bzgynnlvii` | East US 2 |
| Azure OpenAI | `kowil-mj09jnim-swedencentral` | Sweden Central |
| OpenAI Model | `gpt-5.1-chat` | - |

### Endpoints & Credentials

**Production API:**
```
URL: https://rapp-ov4bzgynnlvii.azurewebsites.net/api/businessinsightbot_function
```

**Get function key:**
```bash
az functionapp keys list --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1 --query "functionKeys.default" -o tsv
```

**Test the endpoint:**
```bash
FUNC_KEY=$(az functionapp keys list --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1 --query "functionKeys.default" -o tsv)
curl -X POST "https://rapp-ov4bzgynnlvii.azurewebsites.net/api/businessinsightbot_function?code=$FUNC_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Hello","conversation_history":[]}'
```

### Configuration Files

| File | Purpose |
|------|---------|
| `local.settings.json` | Local dev settings (Azure OpenAI, Storage) - **never commit** |
| `rappid.local.json` | Frontend endpoint configuration for HTML demos |
| `.funcignore` | Files excluded from deployment |
| `sync_cloud_storage.py` | Sync Azure File Storage ↔ local `.local_storage/` |

### Maintenance Commands

**Deploy updates:**
```bash
func azure functionapp publish rapp-ov4bzgynnlvii --build remote
```

**Restart function app:**
```bash
az functionapp restart --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1
```

**View app settings:**
```bash
az functionapp config appsettings list --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1 -o table
```

**Update an app setting:**
```bash
az functionapp config appsettings set --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1 \
  --settings "SETTING_NAME=value"
```

**Check function status:**
```bash
az functionapp function list --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1 -o table
```

**Get function key:**
```bash
az functionapp keys list --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1 --query "functionKeys.default" -o tsv
```

### Authentication

This deployment uses **Entra ID (token-based) authentication** for all Azure services:

- **Azure OpenAI**: Uses `ChainedTokenCredential` (ManagedIdentity in Azure, AzureCliCredential locally)
- **Azure Storage**: Uses token auth with `allowSharedKeyAccess=false` for security
- **No API keys needed**: The function app's managed identity has required RBAC roles

**Required RBAC Roles (already configured):**
- Function App → Storage Account: `Storage Blob Data Contributor`, `Storage File Data Privileged Contributor`
- Function App → Azure OpenAI: `Cognitive Services OpenAI User`

**For local development:**
```bash
# Login to Azure CLI (required for local token auth)
az login

# Verify your identity has access
az account show
```

### Troubleshooting

**Function returns 500 errors after deployment:**
```bash
# Check if storage is accessible
az storage account show --name stov4bzgynnlvii --resource-group rappdec1020205v1 --query "publicNetworkAccess"

# Enable if disabled
az storage account update --name stov4bzgynnlvii --resource-group rappdec1020205v1 --public-network-access Enabled
```

**OpenAI connection errors locally:**
1. Ensure `az login` is completed
2. Check `local.settings.json` has correct `AZURE_OPENAI_ENDPOINT`
3. Verify endpoint exists: `nslookup kowil-mj09jnim-swedencentral.openai.azure.com`

**Functions not appearing after deploy:**
```bash
# Sync triggers
az rest --method POST --uri "https://management.azure.com/subscriptions/235bca14-e532-4deb-8117-eb060662429f/resourceGroups/rappdec1020205v1/providers/Microsoft.Web/sites/rapp-ov4bzgynnlvii/syncfunctiontriggers?api-version=2022-03-01"

# Restart
az functionapp restart --name rapp-ov4bzgynnlvii --resource-group rappdec1020205v1
```

**Local function hangs/times out:**
- Usually means Azure Storage or OpenAI endpoint is unreachable
- Check `local.settings.json` for correct endpoints
- Ensure you're logged into Azure CLI: `az account show`

### Files Excluded from Deployment

The `.funcignore` file excludes these from deployment packages:
- `local.settings.json` (contains secrets)
- `.local_storage/` (local dev data)
- `__pycache__/`, `*.pyc` (Python cache)
- `docs/`, `tests/`, `experimental/` (non-production)
- `*.html`, `*.md` (static files)
- `.venv/`, `.git/`, `.claude/` (dev tooling)

## Power Platform Integration (Optional)

### Overview

Deploy your AI agents directly into Microsoft Teams and Microsoft 365 Copilot using the pre-configured Power Platform solution. This integration enables:
- Native Teams chat bot experience
- M365 Copilot declarative agent deployment
- User context from Office 365 (email, calendar, OneDrive)
- Enterprise-grade authentication and compliance
- No-code configuration through Copilot Studio

### Prerequisites

**Required Licenses:**
- Power Platform license (or trial)
- Copilot Studio license (for M365 integration)
- Microsoft 365 license (for Teams and M365 Copilot)

**Technical Requirements:**
- Azure Function must be accessible from Power Platform (public endpoint or VNet integration)
- Admin consent may be required for M365 Copilot deployment
- Function key for authentication

### Quick Setup Guide

#### 1. Download Power Platform Solution

Download the pre-configured solution package:
- File: `MSFTAIBASMultiAgentCopilot_1_0_0_2.zip`
- Location: [GitHub Releases](https://github.com/kody-w/AI-Agent-Templates/raw/main/MSFTAIBASMultiAgentCopilot_1_0_0_2.zip)

#### 2. Import Solution to Power Platform

1. Navigate to [make.powerapps.com](https://make.powerapps.com)
2. Go to **Solutions** → **Import solution**
3. Upload the downloaded ZIP file
4. Click **Next** → **Import**
5. Wait for import to complete (2-5 minutes)

#### 3. Configure Power Automate Connection

The solution includes a Power Automate flow that connects Copilot Studio to your Azure Function:

1. Open the imported solution
2. Find the flow: **"Talk to MAC (Migration Assessment Copilot)"**
3. Edit the flow and locate the HTTP action
4. Update the HTTP action configuration:
   ```
   URL: [Your Azure Function URL from deployment]
   Headers:
     - x-functions-key: [Your Function Key]
   Method: POST
   Body: Dynamic content from trigger
   ```
5. **Save** and **Turn on** the flow

**Finding Your Function URL:**
- Azure Portal → Function App → Functions → `businessinsightbot_function` → Get Function URL
- Format: `https://<your-function-app>.azurewebsites.net/api/businessinsightbot_function`

**Finding Your Function Key:**
- Azure Portal → Function App → Functions → `businessinsightbot_function` → Function Keys → Copy default key

#### 4. Configure Copilot Studio Bot

1. Navigate to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Find your imported bot: **"Agent"**
3. Open **Topics** → **MAIN** topic
4. Verify the Power Automate action is connected to your flow
5. Test the bot in the **Test** pane (right side)
   - Try: "Hello" to verify basic connectivity
   - Try: "What can you do?" to test agent routing

#### 5. Deploy to Microsoft Teams

**Teams Deployment:**
1. In Copilot Studio, go to **Channels**
2. Select **Microsoft Teams**
3. Click **Turn on Teams**
4. Click **Open bot** to test in Teams
5. Share bot with users via Teams Admin Center (if required)

**Microsoft 365 Copilot Deployment:**
1. In Copilot Studio, enable **Microsoft 365 Copilot** channel
2. Configure declarative agent settings:
   - Name: Your bot name
   - Description: What your bot does
   - Instructions: How users should interact
   - Capabilities: Select relevant actions
3. **Submit for admin approval** (if required by your organization)
4. Once approved, users can @mention your bot in M365 Copilot

### Power Automate Flow Details

**Flow Name:** Talk to MAC (Migration Assessment Copilot)

**Trigger:** When Copilot Studio calls the flow
- Receives user input and conversation context
- Passes Office 365 user information

**Actions:**
1. **Initialize Variables** - Set up conversation tracking
2. **HTTP Request** - Call Azure Function with:
   ```json
   {
     "user_input": "User's message",
     "conversation_history": [],
     "user_guid": "Office 365 user ID"
   }
   ```
3. **Parse JSON** - Process Azure Function response
4. **Return to Copilot Studio** - Send formatted response

**Error Handling:**
- Retry logic for transient failures
- Fallback messages for API errors
- Logging to Power Automate run history

### Copilot Studio Topics

**MAIN Topic:**
- Handles all user messages
- Routes to Power Automate flow
- Displays agent responses
- Manages conversation context

**Escalation Topic:**
- Transfers to human agent (if configured)
- Captures feedback
- Logs unhandled scenarios

**Fallback Topic:**
- Catches unrecognized intents
- Provides helpful suggestions
- Maintains conversation flow

### User Context Integration

When deployed via Power Platform, your agents automatically receive:

**User Information:**
- Display Name
- Email Address
- Office 365 User ID
- Department/Title (if available)

**Usage Example in Agent:**
```python
class PersonalizedAgent(BasicAgent):
    def perform(self, user_context=None, **kwargs):
        user_email = user_context.get('email', 'Unknown')
        user_name = user_context.get('name', 'User')

        return f"Hello {user_name}, I have your context from {user_email}"
```

### Monitoring and Troubleshooting

**Power Automate:**
- View run history in Power Automate portal
- Check for failed runs and error messages
- Review input/output for each action

**Copilot Studio:**
- Use Analytics dashboard for usage metrics
- Review conversation transcripts
- Monitor topic performance

**Azure Function:**
- Application Insights for detailed logs
- Function Monitor for execution history
- Log Stream for real-time debugging

**Common Issues:**

1. **401 Unauthorized Error**
   - Verify Function Key is correct
   - Check Function App authentication settings
   - Ensure CORS is configured properly

2. **Flow Fails to Execute**
   - Verify flow is turned ON
   - Check connections are authenticated
   - Review flow run history for errors

3. **Bot Doesn't Respond**
   - Test flow independently first
   - Verify Copilot Studio topic is published
   - Check Power Automate action is connected

4. **Slow Response Times**
   - Review Azure Function performance metrics
   - Check Power Automate execution time
   - Consider scaling Function App plan

### Cost Considerations

**Power Platform:**
- ~$20/user/month for Power Apps + Copilot Studio
- Included in some Microsoft 365 E3/E5 licenses
- Trial available for development

**Azure Resources:**
- Function App: ~$5-10/month (Consumption plan)
- OpenAI: ~$0.01 per 1K tokens
- Storage: <$1/month for typical usage

**Total Estimated Cost:** $25-40/user/month for full integration

### Security Best Practices

1. **Never expose Function Keys in client code**
2. **Use Managed Identity** for Azure resource authentication
3. **Enable Application Insights** for audit logging
4. **Implement rate limiting** in Azure Function
5. **Review Copilot Studio security settings** regularly
6. **Follow Microsoft 365 DLP policies**

### Advanced Scenarios

**Multi-Environment Setup:**
- Dev: Separate Function App + Copilot Studio environment
- Staging: Pre-production testing with test users
- Production: Full deployment with monitoring

**Custom Authentication:**
- Implement Azure AD authentication in Function App
- Use Power Automate premium connectors
- Configure custom claims in Copilot Studio

**Hybrid Deployment:**
- Power Platform for Teams/M365 Copilot
- Direct API for web applications
- Shared Azure Function backend

## Microsoft 365 Terminology Reference

When working with Power Platform integration, note that Microsoft 365 Agents Toolkit was formerly called Teams Toolkit:

| New Name | Former Name |
|----------|-------------|
| Microsoft 365 Agents Toolkit | Teams Toolkit |
| App Manifest | Teams app manifest |
| Microsoft 365 Agents Playground | Test Tool |
| `m365agents.yml` | `teamsapp.yml` |

Use the new names by default when writing documentation or code.

## Skills for Copilot Studio (Terminal-Based Agent Authoring)

This repo integrates with Microsoft's [Skills for Copilot Studio](https://github.com/microsoft/skills-for-copilot-studio) plugin — an open-source toolkit from the CAT team that enables authoring, testing, and troubleshooting Copilot Studio agents via YAML files directly from the terminal.

### Installation

```bash
# In GitHub Copilot CLI or Claude Code:
/plugin marketplace add microsoft/skills-for-copilot-studio
/plugin install copilot-studio@microsoft/skills-for-copilot-studio

# Or clone locally:
git clone https://github.com/microsoft/skills-for-copilot-studio.git .skills-for-copilot-studio
```

**Also required:** [Copilot Studio VS Code Extension](https://github.com/microsoft/vscode-copilotstudio) for cloning/pushing agents.

### Available Commands

| Command | Purpose |
|---------|---------|
| `/copilot-studio:author` | Create/edit YAML — topics, actions, knowledge sources, triggers, variables |
| `/copilot-studio:test` | Test published agents — point-tests, batch suites, evaluation analysis |
| `/copilot-studio:troubleshoot` | Debug — wrong topic routing, validation errors, unexpected behavior |

### RAPP → Copilot Studio Workflow

1. **Generate** agent via RAPP (`transcript_to_agent` or transpiler) → outputs in `transpiled/`
2. **Clone** target Copilot Studio agent via VS Code extension → outputs in `copilotstudioclones/`
3. **Refine** with `/copilot-studio:author` using CAT team best practices
4. **Push** via VS Code extension, then **Publish** in Copilot Studio UI
5. **Test** with `/copilot-studio:test` and **troubleshoot** with `/copilot-studio:troubleshoot`

### Key Integration Points

| RAPP Asset | Plugin Usage |
|---|---|
| `transpiled/` agents | Apply generated YAML topics + instructions to cloned agents |
| `copilotstudioclones/` | Working directory for plugin authoring |
| `utils/copilot_studio_api.py` | Programmatic bulk deployment (complements plugin's per-agent authoring) |
| `docs/copilot_studio_testing_guide.md` | 100+ test prompts to automate via `/copilot-studio:test` |

### Multi-Agent Disambiguation (CAT Team Pattern)

For complex multi-agent setups (e.g., Zurn Elkay 7-agent suite), use **agent-level instructions** instead of trigger phrase engineering:

```
/copilot-studio:author Configure agent instructions to route queries:
  - Drains CI: drainage products, Watts, JR Smith, MiFab
  - Drinking Water CI: fountains, bottle fillers, Elkay, Oasis
  - Sinks CI: stainless steel sinks, Just Manufacturing
```

The orchestrator model uses these instructions for intelligent disambiguation, which scales much better than trigger-based approaches.

**Full guide:** `docs/COPILOT_STUDIO_SKILLS_INTEGRATION.md`

## Important Notes

- **Never commit `local.settings.json`** - contains secrets
- **Python 3.11 required** - Python 3.13+ causes Azure Functions compatibility issues
- **Agent files from Azure Storage** are loaded into `/tmp/agents` and `/tmp/multi_agents` at runtime
- **Default GUID** is used when no user GUID provided to maintain backward compatibility
- **Response format** must include `|||VOICE|||` delimiter for proper voice/formatted response splitting
- **Memory context** automatically switches based on user GUID in request
- **Power Platform integration** is optional - system works standalone via REST API
- **Function keys should be rotated** regularly for security
- **Monitor API usage** to avoid unexpected costs

## Utilities

**Storage System** (`utils/`):
- `storage_factory.py`: Factory function `get_storage_manager()` that auto-detects environment and returns appropriate storage manager (Azure or Local). Uses singleton pattern with 30-minute TTL for credential refresh.
- `azure_file_storage.py`: `AzureFileStorageManager` for Azure File Storage operations with Entra ID authentication
- `local_file_storage.py`: `LocalFileStorageManager` for local development (uses `.local_storage/` folder)
- `environment.py`: Environment detection utilities (`should_use_azure_storage()`, `is_running_in_azure()`)

**Result Types** (`utils/result.py`):
- `Result`, `Success`, `Failure` types for functional error handling
- `AgentLoadError`, `APIError` for typed errors
- `partition_results()` helper for separating successes and failures

**AgentManager** (`utils/agent_manager.py`):
- Helper utilities for agent management and coordination
- Used for multi-agent orchestration scenarios

**Auto-Dependency Installation:**
- When an agent fails to load due to a missing package, the system automatically attempts to install it via pip and retry
- Common package mappings handled (e.g., `cv2` → `opencv-python`, `PIL` → `Pillow`)
- Prevents infinite loops by tracking attempted installs per session

## Common Development Patterns

**Testing a new agent locally:**
1. Create agent file in `agents/` folder (e.g., `my_test_agent.py`)
2. Restart the function: `func start`
3. Test via API call with test user GUID
4. Check logs for agent loading confirmation

**Debugging agent execution:**
```python
# Add logging in your agent's perform method
import logging

class MyAgent(BasicAgent):
    def perform(self, **kwargs):
        logging.info(f"MyAgent called with: {kwargs}")
        result = "some result"
        logging.info(f"MyAgent returning: {result}")
        return result
```

**Working with memory:**
```python
# Read current memory
storage = AzureFileStorageManager()
user_memory = storage.read_file('memory/users', f'{user_guid}_context.txt')

# Append to memory
new_content = f"\n[{datetime.now()}] User updated preferences: dark mode enabled"
updated_memory = (user_memory or "") + new_content
storage.write_file('memory/users', f'{user_guid}_context.txt', updated_memory)
```
