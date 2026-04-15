"""
Agent: MfgCoE Developer Agent
Purpose: Developer persona for the Discrete Manufacturing CoE.
         Scaffolds agent code, generates D365 customization configs,
         creates RAPP pipeline artifacts, and performs code reviews.
         Knows the Master CE Mfg and Mfg Gold Template environment contexts.

Actions:
  scaffold_agent         — Generate a new RAPP-pattern agent skeleton for a given use case
  generate_d365_config   — Generate D365 CE customization config (views, forms, workflows)
  create_rapp_artifact   — Generate a RAPP pipeline artifact (demo JSON, agent metadata, etc.)
  code_review            — Review an existing agent file for quality and patterns
  generate_playwright_test — Scaffold a Playwright test for a customer scenario
  list_existing_agents   — List agents in the customers/ directory for a given customer
  get_agent_pattern      — Return the standard RAPP agent boilerplate pattern
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.context_card_loader import load_context_card

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CUSTOMERS_DIR = os.path.join(REPO_ROOT, "customers")
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")

# Developer skill areas — routes tasks to the right expertise
SKILL_AREAS = {
    "power_platform": {
        "display": "Power Platform Developer",
        "description": "Canvas apps, model-driven apps, Power Automate cloud flows, Dataverse tables, Power Pages portals",
        "keywords": ["canvas app", "model-driven", "power automate", "flow", "dataverse", "power pages", "portal", "app"],
        "tools": ["Power Apps Studio", "Power Automate Designer", "Dataverse", "Power Pages"],
        "languages": ["Power Fx", "YAML", "JSON"],
    },
    "copilot_studio": {
        "display": "Copilot Studio Developer",
        "description": "Conversational AI topics, entities, generative AI actions, custom connectors, adaptive cards, voice bots",
        "keywords": ["copilot studio", "bot", "topic", "conversational", "pva", "virtual agent", "chat", "voice", "adaptive card", "agent"],
        "tools": ["Copilot Studio", "Adaptive Cards Designer", "Power Automate connector", "Bot Framework"],
        "languages": ["YAML", "Adaptive Cards JSON", "Power Fx"],
    },
    "dynamics_crm": {
        "display": "Dynamics 365 / CE Developer",
        "description": "D365 CE customizations, plugins, PCF controls, solution packaging, business rules, workflows, Copilot in D365",
        "keywords": ["d365", "dynamics", "crm", "ce", "plugin", "pcf", "entity", "form", "view", "solution", "business rule", "case", "incident", "account", "contact"],
        "tools": ["Solution Explorer", "Plugin Registration Tool", "XrmToolBox", "Power Platform CLI", "D365 CE"],
        "languages": ["C#", "TypeScript", "JavaScript", "Power Fx"],
    },
    "azure_functions": {
        "display": "Azure Functions / Backend Developer",
        "description": "Python/C# Azure Functions, API Management, Service Bus, Azure Storage, Logic Apps, custom connectors",
        "keywords": ["azure function", "api", "backend", "service bus", "logic app", "storage", "queue", "python", "rest", "webhook", "endpoint"],
        "tools": ["Azure Functions Core Tools", "VS Code Azure Extension", "Azure CLI", "API Management"],
        "languages": ["Python", "C#", "JavaScript", "YAML"],
    },
    "azure_ai": {
        "display": "Azure AI / Agent Developer",
        "description": "Azure OpenAI, Copilot Studio AI actions, prompt engineering, agent design, AI Search, Azure AI Foundry, RAG pipelines",
        "keywords": ["openai", "gpt", "ai", "agent", "prompt", "embedding", "search", "foundry", "rag", "semantic kernel", "langchain"],
        "tools": ["Azure OpenAI Studio", "Azure AI Foundry", "Azure AI Search", "Semantic Kernel", "Prompt Flow"],
        "languages": ["Python", "C#", "YAML", "JSON"],
    },
    "integration": {
        "display": "Integration Developer",
        "description": "API connectors, data flows, ETL pipelines, middleware, system-to-system integration between D365, Azure, and external systems",
        "keywords": ["integration", "connector", "etl", "api", "middleware", "sync", "webhook", "dataflow", "erp", "sap", "external system"],
        "tools": ["Azure Integration Services", "Power Platform connectors", "Azure Data Factory", "Logic Apps", "Azure Service Bus"],
        "languages": ["Python", "C#", "JSON", "YAML"],
    },
}


def _detect_required_skills(use_case: str, description: str = "") -> list:
    """Detect which developer skill areas are needed for a given use case."""
    combined = (use_case + " " + description).lower()
    matched = []
    for skill_key, skill in SKILL_AREAS.items():
        if any(kw in combined for kw in skill["keywords"]):
            matched.append(skill_key)
    return matched if matched else ["dynamics_crm", "copilot_studio"]  # sensible default for mfg CoE


class MfgCoEDeveloperAgent(BasicAgent):
    """Developer persona — scaffolds agents, D365 configs, RAPP artifacts, and Playwright tests."""

    def __init__(self):
        self.name = "MfgCoEDeveloper"
        self.metadata = {
            "name": self.name,
            "description": (
                "Developer agent for the Discrete Manufacturing CoE. "
                "Scaffolds RAPP-pattern agent code, generates D365 customization configs, "
                "creates RAPP pipeline artifacts (demo JSON, metadata), reviews agent code, "
                "and generates Playwright test skeletons. "
                "Use this agent when you need code generated or reviewed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "scaffold_agent",
                            "generate_d365_config",
                            "create_rapp_artifact",
                            "code_review",
                            "generate_playwright_test",
                            "list_existing_agents",
                            "get_agent_pattern",
                            "recommend_skill",
                            "list_skills",
                        ],
                        "description": "Developer action to perform"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Name for the new agent (PascalCase, e.g. WarrantyLookup)"
                    },
                    "agent_description": {
                        "type": "string",
                        "description": "What the agent does — used in metadata and docstring"
                    },
                    "actions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of action names for the agent's enum (e.g. ['lookup_warranty','check_status'])"
                    },
                    "customer": {
                        "type": "string",
                        "description": "Customer directory name (e.g. navico, otis, zurnelkay)"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["master_ce_mfg", "mfg_gold_template", "generic"],
                        "description": "Target demo environment"
                    },
                    "entity": {
                        "type": "string",
                        "description": "D365 entity name for config generation (e.g. incident, account)"
                    },
                    "artifact_type": {
                        "type": "string",
                        "enum": ["demo_json", "agent_metadata", "test_data", "deployment_config"],
                        "description": "Type of RAPP artifact to generate"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Relative path to agent file for code review"
                    },
                    "scenario_name": {
                        "type": "string",
                        "description": "Scenario name for Playwright test generation"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context or requirements"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_agent_pattern")
        handlers = {
            "scaffold_agent":           self._scaffold_agent,
            "generate_d365_config":     self._generate_d365_config,
            "create_rapp_artifact":     self._create_rapp_artifact,
            "code_review":              self._code_review,
            "generate_playwright_test": self._generate_playwright_test,
            "list_existing_agents":     self._list_existing_agents,
            "get_agent_pattern":        self._get_agent_pattern,
            "recommend_skill":          self._recommend_skill,
            "list_skills":              self._list_skills,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoEDeveloperAgent error in {action}: {e}")
            return json.dumps({"error": str(e)})

    def _scaffold_agent(self, **kwargs) -> str:
        agent_name = kwargs.get("agent_name", "MyAgent")
        description = kwargs.get("agent_description", f"{agent_name} agent")
        actions = kwargs.get("actions", ["execute", "get_status", "health_check"])
        customer = kwargs.get("customer", "mfg_coe")
        environment = kwargs.get("environment", "master_ce_mfg")
        context = kwargs.get("context", "")

        # Load environment context card
        env_context = ""
        if environment != "generic":
            try:
                env_context = f"# Environment: {environment}\n" + load_context_card(environment)[:300]
            except Exception:
                pass

        snake_name = agent_name.lower().replace(" ", "_")
        class_name = "".join(w.title() for w in agent_name.replace("_", " ").split()) + "Agent"
        actions_enum = json.dumps(actions)
        actions_handlers = "\n".join([
            f"            \"{a}\": self._{a},"
            for a in actions
        ])
        actions_methods = "\n\n".join([
            f"    def _{a}(self, **kwargs) -> str:\n        # TODO: Implement {a}\n        return json.dumps({{\"action\": \"{a}\", \"status\": \"not_implemented\"}})"
            for a in actions
        ])

        code = f'''"""
Agent: {class_name}
Customer: {customer.title()}
Environment: {environment.replace("_", " ").title()}
Purpose: {description}
Generated: {datetime.utcnow().strftime("%Y-%m-%d")} by MfgCoE Developer Agent

{env_context}
"""

import json
import logging
from datetime import datetime
from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.context_card_loader import load_context_card

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {class_name}(BasicAgent):
    """{description}"""

    def __init__(self):
        self.name = "{agent_name}"
        self.metadata = {{
            "name": self.name,
            "description": "{description}",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "action": {{
                        "type": "string",
                        "enum": {actions_enum},
                        "description": "Action to perform"
                    }},
                    "context": {{
                        "type": "string",
                        "description": "Additional context or input data"
                    }}
                }},
                "required": ["action"]
            }}
        }}
        # Load environment context at startup
        try:
            self._env_context = load_context_card("{environment}")
        except Exception:
            self._env_context = ""
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "{actions[0]}")
        handlers = {{
{actions_handlers}
        }}
        handler = handlers.get(action)
        if not handler:
            return json.dumps({{"error": f"Unknown action: {{action}}"}})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"{class_name} error in {{action}}: {{e}}")
            return json.dumps({{"error": str(e)}})

{actions_methods}
'''

        # Write to customer agents directory
        output_dir = os.path.join(CUSTOMERS_DIR, customer, "agents")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{snake_name}_agent.py")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)

        return json.dumps({
            "status": "scaffolded",
            "agent_name": agent_name,
            "class_name": class_name,
            "file": output_path,
            "actions": actions,
            "next_steps": [
                f"Implement each action method in {output_path}",
                "Add the agent to agents/ root directory or customer agents/ directory",
                "Write a test scenario in customers/mfg_coe/testing/"
            ]
        }, indent=2)

    def _generate_d365_config(self, **kwargs) -> str:
        entity = kwargs.get("entity", "incident")
        customer = kwargs.get("customer", "generic")
        context = kwargs.get("context", "")
        environment = kwargs.get("environment", "master_ce_mfg")

        config = {
            "entity": entity,
            "environment": environment,
            "customer": customer,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "MfgCoE Developer Agent",
            "views": [
                {
                    "name": f"Active {entity.title()}s",
                    "type": "Public",
                    "columns": ["title", "statuscode", "createdon", "ownerid"],
                    "filter": "statecode eq 0"
                }
            ],
            "forms": [
                {
                    "name": f"{entity.title()} Main Form",
                    "type": "Main",
                    "sections": ["Summary", "Details", "Timeline"],
                    "fields_to_highlight": []
                }
            ],
            "business_rules": [],
            "notes": context or f"D365 config scaffold for {entity} in {environment}. Fill in views, forms, and business rules."
        }

        output_dir = os.path.join(CUSTOMERS_DIR, customer, "d365", "configs")
        os.makedirs(output_dir, exist_ok=True)
        config_path = os.path.join(output_dir, f"{entity}_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        return json.dumps({"status": "generated", "entity": entity, "path": config_path}, indent=2)

    def _create_rapp_artifact(self, **kwargs) -> str:
        artifact_type = kwargs.get("artifact_type", "demo_json")
        agent_name = kwargs.get("agent_name", "MyAgent")
        description = kwargs.get("agent_description", "")
        customer = kwargs.get("customer", "mfg_coe")

        if artifact_type == "demo_json":
            artifact = {
                "agent_id": agent_name.lower().replace(" ", "_"),
                "agent_name": agent_name,
                "description": description,
                "customer": customer,
                "demo_scenarios": [
                    {
                        "scenario_id": "scenario_01",
                        "title": f"{agent_name} — Primary Demo",
                        "steps": [
                            {"user": "Hello, I need help with [topic]", "agent": "I can help with that. Let me look that up..."},
                            {"user": "[Follow-up question]", "agent": "[Agent provides detailed response]"}
                        ]
                    }
                ],
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": "MfgCoE Developer Agent"
            }
        elif artifact_type == "agent_metadata":
            artifact = {
                "name": agent_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": [], "description": "Action to perform"},
                        "context": {"type": "string", "description": "Additional context"}
                    },
                    "required": ["action"]
                }
            }
        else:
            artifact = {"type": artifact_type, "agent": agent_name, "generated_at": datetime.utcnow().isoformat()}

        output_dir = os.path.join(REPO_ROOT, "demos")
        os.makedirs(output_dir, exist_ok=True)
        artifact_path = os.path.join(output_dir, f"{agent_name.lower().replace(' ','_')}_{artifact_type}.json")
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2)

        return json.dumps({"status": "created", "artifact_type": artifact_type, "path": artifact_path}, indent=2)

    def _code_review(self, **kwargs) -> str:
        file_path = kwargs.get("file_path", "")
        if not file_path:
            return json.dumps({"error": "file_path required"})

        full_path = os.path.join(REPO_ROOT, file_path)
        if not os.path.exists(full_path):
            return json.dumps({"error": f"File not found: {full_path}"})

        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()

        checks = {
            "has_docstring": '"""' in code[:500],
            "inherits_basic_agent": "BasicAgent" in code,
            "has_metadata": '"parameters"' in code and '"properties"' in code,
            "has_required_fields": '"required"' in code,
            "has_perform_method": "def perform(" in code,
            "has_error_handling": "try:" in code and "except" in code,
            "has_logging": "logger." in code or "logging." in code,
            "uses_json_returns": "json.dumps(" in code,
            "has_action_dispatch": "handlers = {" in code or "action ==" in code,
            "no_print_statements": "print(" not in code,
        }

        score = int((sum(checks.values()) / len(checks)) * 100)
        issues = [k for k, v in checks.items() if not v]

        return json.dumps({
            "file": file_path,
            "quality_score": f"{score}%",
            "checks": checks,
            "issues": issues,
            "line_count": len(code.splitlines()),
            "recommendation": "Looks good!" if score >= 80 else f"Address these issues: {', '.join(issues)}"
        }, indent=2)

    def _generate_playwright_test(self, **kwargs) -> str:
        scenario_name = kwargs.get("scenario_name", "basic_scenario")
        customer = kwargs.get("customer", "generic")
        context = kwargs.get("context", "")

        safe_name = scenario_name.lower().replace(" ", "_")
        test_code = f"""import {{ test, expect }} from '@playwright/test';

/**
 * Playwright Test: {scenario_name}
 * Customer: {customer.title()}
 * Generated: {datetime.utcnow().strftime("%Y-%m-%d")} by MfgCoE Developer Agent
 * {context}
 */

test.describe('{scenario_name}', () => {{

  test.beforeEach(async ({{ page }}) => {{
    // Navigate to the Copilot Studio webchat or D365 portal
    await page.goto(process.env.CHAT_URL || 'http://localhost:7071');
    // Wait for the chat interface to load
    await page.waitForSelector('[data-testid="chat-input"]', {{ timeout: 10000 }});
  }});

  test('should handle primary scenario successfully', async ({{ page }}) => {{
    // TODO: Replace with actual trigger utterance from personas.json
    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    const chatMessages = page.locator('[data-testid="chat-messages"]');

    // Step 1: Send trigger utterance
    await chatInput.fill('TODO: trigger utterance from scenario');
    await sendButton.click();

    // Step 2: Wait for agent response
    await page.waitForSelector('[data-testid="agent-message"]', {{ timeout: 15000 }});

    // Step 3: Validate expected response
    const response = await chatMessages.last().textContent();
    // TODO: Add assertions based on success_criteria in scenarios.json
    expect(response).toBeTruthy();
  }});

  test('should handle escalation gracefully', async ({{ page }}) => {{
    // TODO: Test escalation path
    expect(true).toBe(true); // Placeholder
  }});

}});
"""

        output_dir = os.path.join(REPO_ROOT, "tests", "playwright", customer)
        os.makedirs(output_dir, exist_ok=True)
        test_path = os.path.join(output_dir, f"{safe_name}.spec.ts")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        return json.dumps({
            "status": "generated",
            "scenario": scenario_name,
            "test_file": test_path,
            "next_steps": [
                "Fill in trigger utterances from the customer's scenarios.json",
                "Add assertions based on success_criteria",
                "Run with: npx playwright test " + test_path
            ]
        }, indent=2)

    def _list_existing_agents(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        results = {}
        search_dirs = [os.path.join(CUSTOMERS_DIR, customer, "agents")] if customer else [
            os.path.join(CUSTOMERS_DIR, d, "agents")
            for d in os.listdir(CUSTOMERS_DIR)
            if os.path.isdir(os.path.join(CUSTOMERS_DIR, d))
        ]
        for d in search_dirs:
            if os.path.exists(d):
                agents = [f for f in os.listdir(d) if f.endswith("_agent.py")]
                if agents:
                    key = os.path.basename(os.path.dirname(d))
                    results[key] = agents
        return json.dumps(results, indent=2)

    def _get_agent_pattern(self, **kwargs) -> str:
        return json.dumps({
            "pattern": "RAPP BasicAgent",
            "required_components": [
                "Inherit from BasicAgent",
                "Set self.name (string)",
                "Set self.metadata (OpenAI function-calling schema)",
                "metadata.parameters.properties must include 'action' with enum",
                "metadata.parameters.required must include 'action'",
                "Implement perform(**kwargs) -> str",
                "Return json.dumps() from all code paths",
                "Use action dispatch dict pattern",
                "Wrap all handlers in try/except"
            ],
            "scaffold_command": "Use action=scaffold_agent to generate a pre-filled skeleton"
        }, indent=2)

    def _recommend_skill(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", kwargs.get("agent_name", ""))
        description = kwargs.get("context", kwargs.get("agent_description", ""))
        skills = _detect_required_skills(use_case, description)

        skill_details = []
        for sk in skills:
            info = SKILL_AREAS.get(sk, {})
            skill_details.append({
                "skill_key": sk,
                "display": info.get("display"),
                "description": info.get("description"),
                "tools": info.get("tools", []),
                "languages": info.get("languages", []),
            })

        comment_lines = "\n".join(
            f"- **{s['display']}** — {s['description']} _(tools: {', '.join(s['tools'][:3])})_"
            for s in skill_details
        )

        return json.dumps({
            "status": "ok",
            "summary": f"Detected {len(skills)} required skill area(s) for: {use_case}",
            "required_skills": skills,
            "skill_details": skill_details,
            "comment": f"### 🛠️ Required Developer Skills\n\n{comment_lines}",
        }, indent=2)

    def _list_skills(self, **kwargs) -> str:
        skills_list = [
            {
                "skill_key": k,
                "display": v["display"],
                "description": v["description"],
                "tools": v["tools"],
                "languages": v["languages"],
            }
            for k, v in SKILL_AREAS.items()
        ]
        return json.dumps({
            "status": "ok",
            "count": len(skills_list),
            "summary": f"{len(skills_list)} developer skill areas defined in the CoE.",
            "skills": skills_list,
        }, indent=2)
