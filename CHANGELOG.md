# Changelog

All notable changes to CommunityRAPP are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Dates are UTC.

---

## [Unreleased]

## [2.1.0] — 2026-03-10

### 🏗️ Repository Cleanup

#### Archived
- `rappbook/` directory (posts, index, data) → `.rapp/ARCHIVED/RappbookSystem/`
- 10 GitHub Actions workflows (rappbook-auto-merge, content-generation, content-crawler, dimension-sync, rappzoo-auto-merge, rebuild-index, autonomous-ticker, data-warehouse, federated-warehouse, git-scrape)
- GitHub scripts (generate-post.js, update-index.js) and rappbook copilot instructions

#### Reorganized
- **Copilot Studio consolidation**: Moved `templates/mcs/`, `transpiled/`, `triggers/`, `copilot_studio_deployment_config.json`, and 3 Copilot Studio docs into `utils/copilot_studio/` — one location for all Copilot Studio infrastructure
- **Demo organization**: Moved HTML tools, Python scripts, and bookmarklets from `demos/` root into `demos/tools/` — `demos/` root now contains only JSON demo data

#### Removed
- `.github/agents/my-agent.agent.md` (empty scaffold)
- `docs/ZURNELKAY_CI_SYSTEM.md` (customer-specific)
- `docs/contract_analysis_e2e_test_script.md` (customer-specific)
- `docs/deploy.html` (redundant with azuredeploy.json)
- `functions.json` (unnecessary with Python v2 decorator model)

#### Fixed
- `tests/test_rapp_pipeline.py` — rewrote to import from actual `agents.rapp_agent.RAPPAgent` instead of nonexistent separate agent modules (12 tests, all passing)
- Updated code paths in `utils/mcs_generator.py`, `agents/copilot_studio_transpiler_agent.py`, `agents/agent_generator_agent.py`, `utils/triggers/trigger_registry.py` for new `utils/copilot_studio/` locations

#### Updated
- `README.md` — added architecture diagram, "Build Your Own Agent" quick start, expanded RAPP Pipeline section
- `CONSTITUTION.md` — updated directory structure and scope table
- `README.md` directories table reflects new structure

---

## [2.0.0] — 2026-02-27

### 🏗️ Repository Restructure

**The Great Cleanup** — Focused this repo solely on the CommunityRAPP Azure Functions backend and RAPP pipeline. Archived all RAPPverse/RAPPbook ecosystem code to `.rapp/`.

#### Added
- `CONSTITUTION.md` — Governing document defining repo scope, agent standards, and contribution guidelines
- `CHANGELOG.md` — This file
- `.rapp/` directory — RAPP ecosystem dotdir housing archived code

#### Added — Agents (from Bill Whalen fork)
- `agent_generator_agent.py`, `agent_transpiler_agent.py`, `architecture_diagram_agent.py`
- `copilot_studio_transpiler_agent.py`, `demo_script_generator_agent.py`
- `powerpoint_generator_agent.py`, `powerpoint_generator_agent_v2.py`
- `project_tracker_agent.py`, `rapp_agent.py`, `scripted_demo_agent.py`, `sharepoint_agent.py`

#### Added — Utilities (from Bill Whalen fork)
- `utils/copilot_studio_api.py`, `utils/mcs_generator.py`, `utils/salesforce_client.py`
- `utils/triggers/` — Event-driven trigger system (models, registry, router)

#### Changed — Core
- **`function_app.py`**: Singleton OpenAI client with TTL refresh, agent caching, request timeout handling, Copilot Studio trigger endpoint, vision/image support
- **`host.json`**: Added `functionTimeout` (5 min), structured logging config, HTTP scaling
- **`utils/azure_file_storage.py`**: Identity-based (Managed Identity) + key-based auth with `USE_IDENTITY_BASED_STORAGE` feature flag
- **`utils/rapp_report_generator.py`**: Minor formatting fix

---

## [1.0.0] — Pre-cleanup

The original CommunityRAPP repository. This version is preserved in the `.rapp/` archive directory.

---

*Maintained by the CommunityRAPP community. See CONSTITUTION.md for contribution guidelines.*
