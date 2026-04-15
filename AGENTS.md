# AGENTS.md — AI Agent Instructions for CommunityRAPP

> This file is the unified instruction source for all AI coding agents (GitHub Copilot, Claude, Cursor, etc.).
> It is generated/maintained with [agentrc](https://github.com/microsoft/agentrc).
> For the full project guide see [CLAUDE.md](./CLAUDE.md).

## Project Overview

**CommunityRAPP** is the Rapid AI Agent Production Pipeline — a 14-step methodology and toolset for building production-ready AI agents on Azure Functions + OpenAI. It also hosts the **Mfg CoE Agentic Center of Excellence** for Discrete Manufacturing.

**Primary language:** Python 3.11  
**Runtime:** Azure Functions v4  
**Key entry point:** `function_app.py`

## How to Run

```bash
# Local development (Windows)
.\run.ps1

# Local development (Mac/Linux)
./run.sh

# Test the API
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

## How to Test

```bash
python tests/run_tests.py          # all unit tests (no API keys needed)
python tests/run_tests.py -v       # verbose
python tests/run_tests.py --live   # live API tests (requires env vars)
```

## Key Conventions

### Agent pattern
All agents inherit from `agents/basic_agent.py::BasicAgent`. Required fields:
- `self.name` — used as the OpenAI function name (no spaces)
- `self.metadata` — JSON schema dict for OpenAI function calling
- `def perform(self, **kwargs)` — executes the agent, returns a string

### Storage
Use `AzureFileStorageManager` from `utils/azure_file_storage.py` for all file I/O. Never use local disk directly in agent code — it won't persist on Azure.

### Environment variables
Never hardcode credentials. All secrets go in `local.settings.json` (gitignored) locally and as GitHub/Azure secrets in CI. See `.env.example` for required variables.

### Default GUID
`c0p110t0-aaaa-bbbb-cccc-123456789abc` is the intentionally invalid default user GUID. It's a security guardrail — **do not replace it with a valid UUID**.

### RAPP pipeline
The `RAPP` agent in `agents/` drives all 14 pipeline steps. Use `action="transcript_to_agent"` for the fast path: transcript → deployable agent + demo in one step.

## CoE-specific Context

The `customers/mfg_coe/` folder contains the Discrete Manufacturing Agentic CoE:
- `agents/coe_runner.py` — GitHub Actions runner for all CoE tasks
- `web_ui/index.html` — the Command Center SPA at bots-in-blazers.fun
- `COE_CHARTER.md` — loaded by all CoE agents at startup (update to change behavior)
- `knowledge_base/` — D365 environment context cards agents read before generating code

When generating code that targets a D365 environment, always check:
- `customers/mfg_coe/knowledge_base/master_ce_mfg.md` (primary demo env)
- `customers/mfg_coe/knowledge_base/mfg_gold_template.md` (baseline template)

## File Structure (key paths)

```
function_app.py          # Azure Function entry point + Assistant class
agents/                  # All agent Python files (auto-loaded at startup)
utils/                   # Shared utilities (storage, environment, etc.)
customers/mfg_coe/       # Mfg CoE — agents, web UI, knowledge base
  agents/coe_runner.py   # CoE GitHub Actions runner
  web_ui/index.html      # Command Center SPA
  COE_CHARTER.md         # Agent operating charter
  knowledge_base/        # D365 context cards
.github/workflows/       # GitHub Actions (CoE schedules, agentrc quality gate)
tests/                   # Unit + live API tests
transpiled/              # RAPP-generated Copilot Studio YAML output
```

## What NOT to do

- Do not commit `local.settings.json` — it contains secrets
- Do not use `WEBSITE_INSTANCE_ID` to detect Azure — use `USE_CLOUD_STORAGE` env var
- Do not add `\"` inside f-string expressions (Python <3.12 syntax error) — pre-compute strings first
- Do not use `submodules: true` in GitHub Actions checkouts — `.tools/azure-diagram-mcp` has no URL

## APM Package

This repo publishes agent instructions as an APM package. See `apm.yml` for the manifest.
To install shared patterns: `apm install billwhalenmsft/coe-standards`
