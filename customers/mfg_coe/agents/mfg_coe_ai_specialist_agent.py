"""
Agent: MfgCoE AI Specialist Agent
Purpose: Microsoft AI stack specialist for the Mfg CoE.
         Covers Azure AI Foundry (projects, agents, evaluations), Azure OpenAI
         (prompt engineering, fine-tuning), M365 Copilot declarative agents,
         Semantic Kernel, Azure AI Search / RAG pipelines, and AI extensibility
         patterns across the Microsoft stack.

Actions:
  execute_issue                  — Full build: parse issue → generate AI artifacts → write to disk
  generate_system_prompt         — System prompt + few-shot examples for a use case
  generate_azure_ai_foundry_config — Azure AI Foundry project + agent + eval setup
  generate_declarative_agent     — M365 Copilot declarative agent manifest + instructions
  generate_semantic_kernel_agent — Semantic Kernel agent pattern in Python
  generate_ai_search_index       — Azure AI Search index definition for RAG
  get_ai_stack_overview          — Microsoft AI stack overview and when to use each layer
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, List

from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.context_card_loader import load_context_card

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KB_DIR = os.path.join(REPO_ROOT, "customers", "mfg_coe", "knowledge_base")

# Azure AI Foundry East US 2 — primary deployment region for Mfg CoE
AI_FOUNDRY_DEFAULTS = {
    "location": "eastus2",
    "subscription_id": "REPLACE_WITH_SUBSCRIPTION_ID",
    "resource_group": "REPLACE_WITH_RESOURCE_GROUP",
    "ai_services_name": "REPLACE_WITH_AI_SERVICES_NAME",
    "model_name": "gpt-4o",
    "model_version": "2024-08-06",
    "embedding_model": "text-embedding-3-large",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def _detect_ai_focus(title: str, body: str) -> List[str]:
    """Detect which AI sub-technologies are relevant."""
    combined = (title + " " + body).lower()
    focus = []
    if any(kw in combined for kw in ["foundry", "azure ai", "evaluation", "eval", "batch"]):
        focus.append("foundry")
    if any(kw in combined for kw in ["prompt", "openai", "gpt", "completion", "chat", "fine-tun"]):
        focus.append("openai")
    if any(kw in combined for kw in ["declarative agent", "m365 copilot", "copilot extensibility", "plugin manifest"]):
        focus.append("declarative_agent")
    if any(kw in combined for kw in ["semantic kernel", "sk ", "orchestrat", "planner"]):
        focus.append("semantic_kernel")
    if any(kw in combined for kw in ["search", "rag", "retrieval", "embedding", "vector", "index", "knowledge base"]):
        focus.append("ai_search")
    return focus if focus else ["openai", "foundry"]  # default for mfg CoE


class MfgCoEAISpecialistAgent(BasicAgent):
    """AI Specialist — Azure AI Foundry, Azure OpenAI, M365 Copilot, Semantic Kernel, RAG."""

    def __init__(self):
        self.name = "MfgCoEAISpecialist"
        self.metadata = {
            "name": self.name,
            "description": (
                "Microsoft AI stack specialist for the Mfg CoE. "
                "Generates Azure AI Foundry project configs, Azure OpenAI system prompts "
                "with few-shot examples, M365 Copilot declarative agent manifests, "
                "Semantic Kernel agent patterns, and Azure AI Search RAG pipeline configs. "
                "Covers the full AI extensibility stack across Microsoft 365, Azure, and D365."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "execute_issue",
                            "generate_system_prompt",
                            "generate_azure_ai_foundry_config",
                            "generate_declarative_agent",
                            "generate_semantic_kernel_agent",
                            "generate_ai_search_index",
                            "get_ai_stack_overview",
                        ],
                        "description": "AI Specialist action to perform",
                    },
                    "issue_title": {"type": "string"},
                    "issue_body": {"type": "string"},
                    "use_case": {"type": "string", "description": "Brief description of the AI use case"},
                    "persona": {"type": "string", "description": "Agent persona/role (e.g. 'Mfg Sales Assistant')"},
                    "prior_artifacts": {
                        "type": "object",
                        "description": "Artifacts from prior specialists",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "execute_issue")
        handlers = {
            "execute_issue": self._execute_issue,
            "generate_system_prompt": self._generate_system_prompt,
            "generate_azure_ai_foundry_config": self._generate_foundry_config,
            "generate_declarative_agent": self._generate_declarative_agent,
            "generate_semantic_kernel_agent": self._generate_sk_agent,
            "generate_ai_search_index": self._generate_ai_search_index,
            "get_ai_stack_overview": self._get_ai_stack_overview,
        }
        fn = handlers.get(action)
        if not fn:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return fn(**kwargs)
        except Exception as e:
            logger.error("AISpecialist %s failed: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    def _execute_issue(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        prior = kwargs.get("prior_artifacts", {})

        slug = _slug(title)
        focus_areas = _detect_ai_focus(title, body)
        os.makedirs(KB_DIR, exist_ok=True)

        parts = [
            f"# AI Specialist Artifact — {title}",
            f"_Generated by MfgCoE AI Specialist Agent | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_",
            f"**AI Focus Areas:** {', '.join(focus_areas)}",
        ]

        if "openai" in focus_areas or "foundry" in focus_areas:
            prompt_result = json.loads(self._generate_system_prompt(issue_title=title, issue_body=body))
            parts.append("\n## System Prompt\n")
            parts.append(prompt_result.get("content", ""))

        if "foundry" in focus_areas:
            foundry_result = json.loads(self._generate_foundry_config(issue_title=title, issue_body=body))
            parts.append("\n## Azure AI Foundry Configuration\n")
            parts.append(foundry_result.get("content", ""))

        if "declarative_agent" in focus_areas:
            da_result = json.loads(self._generate_declarative_agent(issue_title=title, issue_body=body))
            parts.append("\n## M365 Copilot Declarative Agent\n")
            parts.append(da_result.get("content", ""))

        if "ai_search" in focus_areas:
            search_result = json.loads(self._generate_ai_search_index(issue_title=title, issue_body=body))
            parts.append("\n## Azure AI Search Index\n")
            parts.append(search_result.get("content", ""))

        fname = f"ai_artifact_{slug}.md"
        fpath = os.path.join(KB_DIR, fname)
        artifact = "\n".join(parts)

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(artifact)

        rel_path = os.path.relpath(fpath, REPO_ROOT).replace("\\", "/")
        logger.info("AI Specialist artifact written to %s", rel_path)

        return json.dumps({
            "status": "artifact_written",
            "output_path": rel_path,
            "abs_path": fpath,
            "agent": "ai_specialist",
            "focus_areas": focus_areas,
            "content_preview": artifact[:500],
        }, indent=2)

    def _generate_system_prompt(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        use_case = kwargs.get("use_case", title)
        persona = kwargs.get("persona", "Mfg CoE AI Assistant")

        # Load Mfg CoE context
        master_ctx = load_context_card("master_ce_mfg") or ""
        env_snippet = master_ctx[:400] if master_ctx else "Master CE Mfg environment (D365 CE, Dynamics 365)"

        content = f"""### System Prompt — {title}

```
You are {persona}, an AI assistant specializing in {use_case.lower()} for discrete manufacturing.

## Your Role
- Help manufacturing sales and service teams with {use_case.lower()}
- Provide accurate, actionable answers grounded in the provided context
- When you don't know, say so and offer to escalate or search for more information

## Environment Context
{env_snippet[:300]}

## Response Guidelines
- Be concise and structured (use bullets/tables where helpful)
- For D365 lookups, reference entity names and record GUIDs when available
- For Power Platform actions, describe the step-by-step flow
- Always confirm before taking irreversible actions (delete, update, send)

## Boundaries
- Do NOT make up record IDs or GUIDs — only use data from the provided context
- Do NOT share confidential customer information outside this session
- If asked about topics outside manufacturing/CRM/Power Platform, politely redirect
```

### Few-Shot Examples

**Example 1 — Lookup request:**
> User: "Find the distributor account for Pacific Northwest"
> Assistant: "I'll search for distributor accounts in the Pacific Northwest region. 
> Based on the Master CE Mfg environment, here are the matching accounts:
> [Account Name] | [Account ID] | [Region] | [Status]
> Would you like me to open the record or take an action?"

**Example 2 — Ambiguous request:**
> User: "Update the case"
> Assistant: "I'd be happy to help update a case. Could you provide:
> 1. The case number or title
> 2. What field(s) you'd like to update
> 3. The new value(s)?"

**Example 3 — Out of scope:**
> User: "What's the weather today?"
> Assistant: "I'm specialized in manufacturing, CRM, and Power Platform topics.
> For weather, I'd recommend checking a weather service directly.
> Is there anything I can help you with in those areas?"
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_foundry_config(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        slug = _slug(title)
        d = AI_FOUNDRY_DEFAULTS

        content = f"""### Azure AI Foundry Configuration — {title}

#### 1. Create AI Services Account
```bash
az cognitiveservices account create \\
  --name "{slug}-ai-services" \\
  --resource-group "{d['resource_group']}" \\
  --location "{d['location']}" \\
  --kind AIServices \\
  --sku S0 \\
  --custom-domain "{slug}-ai"
```

#### 2. Create Foundry Project
```python
# Using azure_foundry_mcp_server tools or SDK
project_config = {{
    "subscription_id": "{d['subscription_id']}",
    "resource_group": "{d['resource_group']}",
    "azure_ai_services_name": "{slug}-ai-services",
    "project_name": "{slug}-project",
    "location": "{d['location']}"
}}
```

#### 3. Deploy Model
```python
deployment = {{
    "deployment_name": "gpt-4o-{slug}",
    "model_name": "{d['model_name']}",
    "model_format": "OpenAI",
    "model_version": "{d['model_version']}",
    "sku_name": "Standard",
    "sku_capacity": 10
}}
```

#### 4. Create Agent
```python
agent_config = {{
    "name": "{title} Agent",
    "instructions": "You are a specialist for {title.lower()} in discrete manufacturing.",
    "model": "gpt-4o-{slug}",
    "tools": [
        {{"type": "file_search"}},
        {{"type": "code_interpreter"}}
    ]
}}
```

#### 5. Evaluation Setup
```python
# Evaluators: coherence, relevance, groundedness, task_adherence
eval_dataset = "rapp_projects/{slug}/eval_dataset.jsonl"
evaluators = ["coherence", "relevance", "groundedness"]
```

#### Azure AI Foundry Portal
- Create resources at: https://ai.azure.com
- Project type: Azure AI Foundry project (not legacy ML workspace)
- Enable `allowProjectManagement: true` on AI Services account
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_declarative_agent(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        slug = _slug(title)

        content = f"""### M365 Copilot Declarative Agent — {title}

#### Declarative Agent Manifest (`declarativeAgent.json`)
```json
{{
  "$schema": "https://aka.ms/json-schemas/copilot-extensions/vNext/declarative-copilot.schema.json",
  "version": "v1.5",
  "name": "{title}",
  "description": "{body[:100].strip().replace(chr(10), ' ')}",
  "instructions": "You are a specialized assistant for {title.lower()} in discrete manufacturing. Use the provided knowledge sources and tools to give accurate, actionable responses. Focus on D365 CE data, Power Platform configurations, and manufacturing best practices.",
  "capabilities": [
    {{
      "name": "OneDriveAndSharePoint",
      "items_by_sharepoint_ids": []
    }},
    {{
      "name": "GraphConnectors",
      "connections": []
    }}
  ],
  "actions": [
    {{
      "id": "{slug}_action",
      "file": "ai-plugin.json"
    }}
  ]
}}
```

#### API Plugin Manifest (`ai-plugin.json`)
```json
{{
  "$schema": "https://aka.ms/json-schemas/copilot-extensions/vNext/plugin.schema.json",
  "schema_version": "v2.1",
  "name_for_human": "{title}",
  "description_for_human": "Plugin for {title.lower()}",
  "description_for_model": "Use this plugin to perform {title.lower()} operations. Call the API with user intent extracted from the conversation.",
  "functions": [
    {{
      "name": "execute_{slug}",
      "description": "Execute {title.lower()} operation",
      "parameters": {{
        "type": "object",
        "properties": {{
          "query": {{"type": "string", "description": "User query or intent"}}
        }},
        "required": ["query"]
      }},
      "returns": {{
        "type": "object",
        "properties": {{
          "result": {{"type": "string"}},
          "items": {{"type": "array"}}
        }}
      }},
      "states": {{
        "reasoning": {{
          "description": "Use this to look up {title.lower()} information"
        }},
        "responding": {{
          "description": "Present results from {title.lower()} lookup clearly"
        }}
      }}
    }}
  ],
  "runtimes": [
    {{
      "type": "OpenApi",
      "auth": {{"type": "OAuthPluginVault", "reference_id": "${{OAUTH_CONNECTION_ID}}"}},
      "spec": {{"url": "openapi.json"}}
    }}
  ]
}}
```

#### App Manifest (`manifest.json` key additions)
```json
{{
  "copilotAgents": {{
    "declarativeAgents": [
      {{
        "id": "{slug}Agent",
        "file": "declarativeAgent.json"
      }}
    ]
  }}
}}
```

> **Deployment:** Use Microsoft 365 Agents Toolkit (`atk`) or upload via Teams Admin Center.
> **Test:** Use Microsoft 365 Agents Playground before submitting for admin approval.
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_sk_agent(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        slug = _slug(title).replace("_", "")

        content = f"""### Semantic Kernel Agent — {title}

```python
# Requirements: semantic-kernel>=1.0.0, azure-identity

import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function
from azure.identity import DefaultAzureCredential

# ── Kernel setup ──────────────────────────────────────────────────────────────
kernel = Kernel()
kernel.add_service(AzureChatCompletion(
    deployment_name="gpt-4o",
    endpoint="https://REPLACE_WITH_ENDPOINT.openai.azure.com/",
    ad_token_provider=DefaultAzureCredential().get_token,
))

# ── Plugin (tools the agent can call) ─────────────────────────────────────────
class {slug.title()}Plugin:

    @kernel_function(description="Look up D365 records for {title.lower()}")
    async def lookup_d365_records(self, query: str) -> str:
        \"\"\"Queries the D365 CE environment for relevant records.\"\"\"
        # TODO: Integrate with D365 OData API
        return f"D365 lookup for: {{query}} — implement with requests + az token"

    @kernel_function(description="Summarize findings for {title.lower()}")
    async def summarize(self, data: str) -> str:
        \"\"\"Summarizes raw D365 data into a human-readable format.\"\"\"
        return f"Summary: {{data[:200]}}"

# ── Agent definition ──────────────────────────────────────────────────────────
kernel.add_plugin({slug.title()}Plugin(), plugin_name="{slug}")

agent = ChatCompletionAgent(
    kernel=kernel,
    name="{slug.title()}Agent",
    instructions=(
        "You are a specialist for {title.lower()} in discrete manufacturing. "
        "Use available plugins to look up D365 data and provide accurate answers. "
        "Always confirm before taking write actions."
    ),
)

# ── Run ───────────────────────────────────────────────────────────────────────
async def main():
    response = await agent.invoke("Tell me about {title.lower()}")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_ai_search_index(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        slug = _slug(title)

        content = f"""### Azure AI Search Index — {title}

#### Index Definition
```json
{{
  "name": "{slug}-index",
  "fields": [
    {{"name": "id", "type": "Edm.String", "key": true, "filterable": true}},
    {{"name": "title", "type": "Edm.String", "searchable": true, "retrievable": true}},
    {{"name": "content", "type": "Edm.String", "searchable": true, "retrievable": true}},
    {{"name": "category", "type": "Edm.String", "filterable": true, "retrievable": true}},
    {{"name": "source", "type": "Edm.String", "retrievable": true}},
    {{"name": "embedding", "type": "Collection(Edm.Single)", "searchable": true, "retrievable": false,
      "dimensions": 3072, "vectorSearchProfile": "default-profile"}}
  ],
  "vectorSearch": {{
    "profiles": [{{"name": "default-profile", "algorithm": "default-algo"}}],
    "algorithms": [{{"name": "default-algo", "kind": "hnsw"}}]
  }},
  "semantic": {{
    "configurations": [{{
      "name": "default",
      "prioritizedFields": {{
        "titleField": {{"fieldName": "title"}},
        "contentFields": [{{"fieldName": "content"}}]
      }}
    }}]
  }}
}}
```

#### RAG Query Pattern (Python)
```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

# Embed user query
oai = AzureOpenAI(azure_endpoint="...", api_version="2024-08-01-preview")
embedding = oai.embeddings.create(input=user_query, model="text-embedding-3-large").data[0].embedding

# Hybrid search (keyword + vector)
search_client = SearchClient(endpoint="...", index_name="{slug}-index", credential=credential)
results = search_client.search(
    search_text=user_query,
    vector_queries=[VectorizedQuery(vector=embedding, k_nearest_neighbors=5, fields="embedding")],
    query_type="semantic",
    semantic_configuration_name="default",
    top=5,
)
context = "\\n\\n".join(r["content"] for r in results)

# Augment prompt
messages = [
    {{"role": "system", "content": "Answer using only the provided context."}},
    {{"role": "user", "content": f"Context:\\n{{context}}\\n\\nQuestion: {{user_query}}"}}
]
```
"""
        return json.dumps({"status": "ok", "content": content})

    def _get_ai_stack_overview(self, **kwargs) -> str:
        content = """## Microsoft AI Stack — When to Use What

| Layer | Technology | Best For |
|---|---|---|
| **Conversational** | Copilot Studio | Business user-facing bots, Teams integration, low-code |
| **Declarative Extension** | M365 Copilot Declarative Agents | Extending Copilot with domain knowledge + APIs |
| **Agentic Orchestration** | Azure AI Foundry Agents | Multi-step autonomous tasks, tool-calling, evaluation |
| **Custom AI Apps** | Azure OpenAI + Azure Functions | Full-control API-based AI, RAPP pattern agents |
| **Orchestration Framework** | Semantic Kernel | Complex multi-agent patterns, planners, plugins |
| **Knowledge / Search** | Azure AI Search + Embeddings | RAG pipelines, semantic search over docs/data |
| **Analytics AI** | Power BI Copilot | Natural language queries over BI datasets |
| **Code AI** | GitHub Copilot | Developer productivity, code review, PR automation |

### Mfg CoE Recommended Stack
1. **Copilot Studio** — front-door for most use cases (low-code, Teams-native)
2. **Azure Functions (RAPP pattern)** — backend logic, D365 integration, memory
3. **Azure AI Foundry** — where we need evaluation, batch processing, or advanced agents
4. **Azure AI Search** — when agents need to search over large doc sets (SOPs, specs, D365 records)
5. **M365 Copilot Declarative Agents** — for deep M365 Copilot integration with custom context

### Decision Tree
- User needs a Teams/M365 chat experience → **Copilot Studio** + **Declarative Agent**
- Need to call D365 APIs programmatically → **Azure Functions** (RAPP agent)
- Need to evaluate AI quality at scale → **Azure AI Foundry** (batch eval)
- Need to search a knowledge base → **Azure AI Search** (RAG pipeline)
- Need complex multi-step planning → **Semantic Kernel** agent
"""
        return json.dumps({"status": "ok", "content": content})
