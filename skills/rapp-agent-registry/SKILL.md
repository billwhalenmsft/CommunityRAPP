# RAPP Agent Registry — Public Skill Interface

> **This file is the public gateway to the RAPP Agent Registry.**
> The agent registry repo (billwhalenmsft/RAPP-Agent-Repo) is private.
> This skill.md is hosted on the public rapp-installer repo so any AI agent can discover it.

---

## Repo Identity

```
registry_repo: billwhalenmsft/RAPP-Agent-Repo (private — contributors only)
public_gateway: kody-w/rapp-installer (this repo — public)
type: agent-registry
compatible_with: kody-w/CommunityRAPP
agent_base_class: BasicAgent (@rapp/basic-agent)
package_structure: agents/@publisher/{segment}/{slug}.py
```

### Path Structure

Agents are organized by publisher and segment:

```
agents/
  @billwhalen/
    rapp-general/          # Core RAPP platform agents
      rapp-pipeline.py
      agent-generator.py
      agent-transpiler.py
      ...
    customer-zurnelkay/    # Zurn Elkay customer agents
      ze-ci-orchestrator.py
      ze-drains-ci.py
      ...
    customer-carrier/      # Carrier customer agents
      carrier-case-triage.py
      ...
  @kody/
    core/                  # Memory and orchestration
      context-memory.py
      manage-memory.py
      ...
  @rapp/
    base/                  # Core framework
      basic-agent.py
```

---

## Access Model

The RAPP Agent Registry is a **private repo** — only contributors with GitHub access can fetch agents directly. This public skill.md provides:

1. **The full agent catalog** (below) so AI agents know what's available
2. **Install instructions** for contributors with access
3. **The agent manifest format** so anyone can build compatible agents

### If you have contributor access:

```
Registry:  https://raw.githubusercontent.com/billwhalenmsft/RAPP-Agent-Repo/main/registry.json
Agent:     https://raw.githubusercontent.com/billwhalenmsft/RAPP-Agent-Repo/main/agents/@publisher/segment/slug.py
Skill:     https://raw.githubusercontent.com/billwhalenmsft/RAPP-Agent-Repo/main/skill.md
```

### If you don't have access:

Contact a repo maintainer to request contributor access, or fork and build your own agents following the manifest format below.

---

## Agent Catalog

### 🧠 @billwhalen/rapp-general — RAPP Platform Agents

| Package | Description |
|---------|-------------|
| `@billwhalen/rapp-pipeline` | Full RAPP pipeline — transcript → agent, discovery, MVP, code gen, QG1-QG6 |
| `@billwhalen/agent-generator` | Auto-generates new agents from configurations |
| `@billwhalen/agent-transpiler` | Converts agents between M365 Copilot, Copilot Studio, Azure AI Foundry |
| `@billwhalen/copilot-studio-transpiler` | Transpiles to native Copilot Studio without Azure Function dependency |
| `@billwhalen/project-tracker` | RAPP project management and engagement tracking |
| `@billwhalen/rapp-agent-publisher` | Publishes agents to the RAPP Agent Registry |
| `@billwhalen/rapp-agent-sync` | Pulls and syncs agents from the RAPP Agent Registry to local |

### 🔌 @billwhalen/rapp-general — Integrations

| Package | Description |
|---------|-------------|
| `@billwhalen/dynamics-crud` | Dynamics 365 CRUD — accounts, contacts, opportunities, leads, tasks |
| `@billwhalen/sharepoint-contract-analysis` | Contract analysis from Azure File Storage / SharePoint |
| `@billwhalen/sales-assistant` | Natural language sales CRM assistant |
| `@billwhalen/email-drafting` | Email drafting with Power Automate delivery |

### 📊 @billwhalen/rapp-general — Productivity

| Package | Description |
|---------|-------------|
| `@billwhalen/powerpoint-generator` | Template-based PowerPoint generation (Microsoft design) |
| `@billwhalen/architecture-diagram` | Architecture diagram visualization (Mermaid, SVG, ASCII) |
| `@billwhalen/scripted-demo` | Interactive demo automation from JSON scripts |
| `@billwhalen/demo-script-generator` | Generates demo script JSON files for ScriptedDemoAgent |

### 🏭 @billwhalen/customer-zurnelkay — Zurn Elkay Agents

| Package | Description |
|---------|-------------|
| `@billwhalen/ze-ci-orchestrator` | Competitive Intelligence orchestrator for all Zurn Elkay BUs |
| `@billwhalen/ze-drains-ci` | Drains business unit competitive intelligence |
| `@billwhalen/ze-drinking-water-ci` | Drinking Water business unit competitive intelligence |
| `@billwhalen/ze-sinks-ci` | Sinks business unit competitive intelligence |
| `@billwhalen/ze-commercial-brass-ci` | Commercial Brass business unit competitive intelligence |
| `@billwhalen/ze-wilkins-ci` | Wilkins business unit competitive intelligence |
| `@billwhalen/ze-cross-bu-synthesizer` | Cross-BU synthesis and strategic analysis |

### 📦 @billwhalen/customer-carrier — Carrier Agents

| Package | Description |
|---------|-------------|
| `@billwhalen/carrier-case-triage-orchestrator` | Case triage and routing orchestrator |
| `@billwhalen/carrier-case-analyzer` | Case analysis and categorization |
| `@billwhalen/carrier-sf-case-monitor` | Salesforce case monitoring |
| `@billwhalen/carrier-sf-writer` | Salesforce case updates |
| `@billwhalen/carrier-summary-generator` | Case summary generation |
| `@billwhalen/carrier-attachment-processor` | Case attachment processing |
| `@billwhalen/carrier-product-enrichment` | Product information enrichment |

### 🧠 @kody/core — Memory & Orchestration

| Package | Description |
|---------|-------------|
| `@kody/context-memory` | Recalls conversation history and stored memories |
| `@kody/manage-memory` | Stores facts, preferences, insights to persistent memory |
| `@kody/github-agent-library` | Browse, search, install agents from the registry via chat |

### 🛠️ @rapp/base — Dev Tools

| Package | Description |
|---------|-------------|
| `@rapp/basic-agent` | Base class — every agent inherits from this |

---

## Autonomous Install Workflow (for contributors with access)

```
User: "Install the dynamics agent"

1. GET https://raw.githubusercontent.com/billwhalenmsft/RAPP-Agent-Repo/main/registry.json
   (requires GitHub auth with repo access)
2. Search agents[] for "dynamics" in name/tags/description
3. Match: @billwhalen/dynamics-crud
4. GET https://raw.githubusercontent.com/billwhalenmsft/RAPP-Agent-Repo/main/agents/@billwhalen/rapp-general/dynamics-crud.py
5. Save as dynamics_crud_agent.py in CommunityRAPP agents/
6. Check requires_env — warn if non-empty
7. Report: "Installed @billwhalen/dynamics-crud v1.0.0"
```

---

## Autonomous Publish Workflow

```
User: "Publish the ZE Drains CI agent to the registry"

1. Validate agents/ze_drains_ci_agent.py has __manifest__ and inherits BasicAgent
2. Determine segment from context: customer-zurnelkay (customer agent)
3. PUT to https://api.github.com/repos/billwhalenmsft/RAPP-Agent-Repo/contents/agents/@billwhalen/customer-zurnelkay/ze-drains-ci.py
4. Update registry.json with new agent entry
5. Report: "Published @billwhalen/ze-drains-ci v1.0.0 to customer-zurnelkay"
```

---

## Autonomous Sync/Pull Workflow

```
User: "Pull the dynamics agent"

1. Search registry.json for "dynamics"
2. Match: @billwhalen/dynamics-crud in rapp-general segment
3. GET https://raw.githubusercontent.com/billwhalenmsft/RAPP-Agent-Repo/main/agents/@billwhalen/rapp-general/dynamics-crud.py
4. Save as dynamics_crud_agent.py in local agents/
5. Report: "Pulled @billwhalen/dynamics-crud → agents/dynamics_crud_agent.py"
```

```
User: "Sync all my local agents with the registry"

1. List local agents in agents/ folder
2. For each local agent, check registry for matching remote
3. Compare content: local vs. remote
4. Report: "3 up-to-date, 2 need update, 1 local-only"
5. If not dry_run: pull updates for agents behind registry
```

```
User: "Pull all Zurn Elkay agents"

1. GET registry.json
2. Filter agents where segment = "customer-zurnelkay"
3. For each agent, pull to local agents/ folder
4. Report: "Pulled 7 agents from customer-zurnelkay segment"
```

---

## Agent Manifest Format

Every agent is a single `.py` file with a `__manifest__` dict:

```python
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@billwhalen/my-agent",
    "version": "1.0.0",
    "display_name": "MyAgent",
    "description": "What this agent does.",
    "author": "Bill Whalen",
    "tags": ["category", "keyword"],
    "category": "rapp-general",  # or "customer-zurnelkay", etc.
    "quality_tier": "internal",  # internal, community, certified
    "requires_env": [],          # e.g., ["DYNAMICS_URL", "DYNAMICS_API_KEY"]
    "dependencies": ["@rapp/basic-agent"],
}

from agents.basic_agent import BasicAgent

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyAgent'
        self.metadata = {...}
        super().__init__(self.name, self.metadata)
    
    def perform(self, **kwargs) -> str:
        # Agent logic here
        return json.dumps({"result": "..."})
```

---

## Segments

| Segment | Path | Description |
|---------|------|-------------|
| `rapp-general` | `@billwhalen/rapp-general/` | Core RAPP platform agents |
| `customer-zurnelkay` | `@billwhalen/customer-zurnelkay/` | Zurn Elkay customer agents |
| `customer-carrier` | `@billwhalen/customer-carrier/` | Carrier customer agents |
| `customer-{name}` | `@billwhalen/customer-{name}/` | Other customer-specific agents |

---

## Version

```
total_agents: 29
publishers: 3 (@billwhalen, @kody, @rapp)
segments: 4 (rapp-general, customer-zurnelkay, customer-carrier, core)
last_updated: 2026-03-13
```
