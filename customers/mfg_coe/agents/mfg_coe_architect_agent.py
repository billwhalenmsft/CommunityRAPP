"""
Agent: MfgCoE Solutions Architect Agent
Purpose: Solutions Architect persona for the Discrete Manufacturing CoE.
         Designs Microsoft stack integrations, evaluates architectural patterns,
         proposes reference architectures, and accumulates solution knowledge.
         Deeply familiar with D365, Copilot Studio, Power Platform, and Azure.

Actions:
  design_solution        — Design an end-to-end solution for a use case
  evaluate_pattern       — Evaluate whether a proposed pattern fits the MS stack
  create_architecture_doc — Generate an architecture document for a solution
  recommend_stack        — Recommend the right Microsoft tech stack components for a scenario
  add_to_knowledge_base  — Save architectural pattern or integration insight
  search_knowledge_base  — Search accumulated architectural knowledge
  get_integration_catalog — List known integration patterns for Discrete Mfg + MS stack
  assess_complexity      — Assess implementation complexity + effort for a use case
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

KNOWLEDGE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
)

# Microsoft stack component catalog for Discrete Manufacturing
MS_STACK = {
    "crm_core": "D365 Customer Engagement (Sales, Customer Service)",
    "field_service": "D365 Field Service",
    "finance_ops": "D365 Finance & Operations / Business Central",
    "copilot_studio": "Microsoft Copilot Studio (bot authoring, topic management)",
    "power_automate": "Power Automate (workflow automation, API integration)",
    "power_apps": "Power Apps (custom canvas/model-driven apps)",
    "azure_functions": "Azure Functions (serverless API, agent hosting)",
    "azure_openai": "Azure OpenAI Service (GPT-4o, embeddings)",
    "azure_storage": "Azure File/Blob Storage (agent memory, file persistence)",
    "sharepoint": "SharePoint Online (document management, knowledge base)",
    "teams": "Microsoft Teams (internal collaboration surface)",
    "m365_copilot": "Microsoft 365 Copilot (enterprise AI assistant surface)",
    "dataverse": "Microsoft Dataverse (low-code data platform)",
    "azure_ai_search": "Azure AI Search (RAG, knowledge retrieval)",
    "azure_service_bus": "Azure Service Bus (async messaging, event-driven)",
}

INTEGRATION_PATTERNS = {
    "copilot_to_d365": {
        "description": "Copilot Studio → Power Automate → D365 CE API",
        "use_cases": ["case lookup", "account search", "order status", "warranty check"],
        "complexity": "Low-Medium"
    },
    "agent_to_d365": {
        "description": "Azure Function Agent → D365 Web API (OData)",
        "use_cases": ["CRUD operations", "bulk data updates", "complex queries"],
        "complexity": "Medium"
    },
    "rag_knowledge": {
        "description": "Azure AI Search + Azure OpenAI → Agent grounded responses",
        "use_cases": ["knowledge articles", "parts catalogs", "technical manuals"],
        "complexity": "Medium-High"
    },
    "event_driven": {
        "description": "D365 Plugin/Webhook → Azure Service Bus → Azure Function",
        "use_cases": ["case escalation triggers", "SLA breach alerts", "order status changes"],
        "complexity": "Medium"
    },
    "human_in_loop": {
        "description": "Agent flags → Power Automate approval → Teams adaptive card → Resume",
        "use_cases": ["discount approval", "returns authorization", "complex case routing"],
        "complexity": "Medium"
    },
    "multi_agent_orchestration": {
        "description": "L0 Orchestrator → L1 Specialist Agents (RAPP pattern)",
        "use_cases": ["complex case triage", "multi-step process automation", "cockpit/workbench"],
        "complexity": "High"
    }
}


class MfgCoEArchitectAgent(BasicAgent):
    """Solutions Architect persona — designs Microsoft stack solutions for Discrete Mfg CoE."""

    def __init__(self):
        self.name = "MfgCoEArchitect"
        self.metadata = {
            "name": self.name,
            "description": (
                "Solutions Architect agent for the Discrete Manufacturing CoE. "
                "Designs Microsoft stack integrations (D365, Copilot Studio, Power Platform, Azure), "
                "evaluates architectural patterns, generates architecture docs, recommends tech stack "
                "components, and builds up the CoE's architectural knowledge base. "
                "Use this agent when designing solutions or evaluating technical approaches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "design_solution",
                            "evaluate_pattern",
                            "create_architecture_doc",
                            "recommend_stack",
                            "add_to_knowledge_base",
                            "search_knowledge_base",
                            "get_integration_catalog",
                            "assess_complexity"
                        ],
                        "description": "Architect action to perform"
                    },
                    "use_case": {
                        "type": "string",
                        "description": "Use case or business scenario to design for"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the requirement"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["master_ce_mfg", "mfg_gold_template", "generic"],
                        "description": "Target demo environment"
                    },
                    "proposed_pattern": {
                        "type": "string",
                        "description": "Pattern name or description to evaluate"
                    },
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of functional or non-functional requirements"
                    },
                    "knowledge_content": {
                        "type": "string",
                        "description": "Architectural knowledge or pattern to save"
                    },
                    "knowledge_topic": {
                        "type": "string",
                        "description": "Topic name for knowledge entry"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Query to search knowledge base"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_integration_catalog")
        handlers = {
            "design_solution":         self._design_solution,
            "evaluate_pattern":        self._evaluate_pattern,
            "create_architecture_doc": self._create_architecture_doc,
            "recommend_stack":         self._recommend_stack,
            "add_to_knowledge_base":   self._add_to_knowledge_base,
            "search_knowledge_base":   self._search_knowledge_base,
            "get_integration_catalog": self._get_integration_catalog,
            "assess_complexity":       self._assess_complexity,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoEArchitectAgent error in {action}: {e}")
            return json.dumps({"error": str(e)})

    def _design_solution(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", "")
        description = kwargs.get("description", "")
        environment = kwargs.get("environment", "master_ce_mfg")
        requirements = kwargs.get("requirements", [])

        env_context = ""
        if environment != "generic":
            try:
                env_context = load_context_card(environment)
            except Exception:
                pass

        # Auto-select recommended pattern based on use case keywords
        uc_lower = (use_case + " " + description).lower()
        recommended_patterns = []
        if any(k in uc_lower for k in ["lookup", "search", "check", "status", "query"]):
            recommended_patterns.append("copilot_to_d365")
        if any(k in uc_lower for k in ["knowledge", "manual", "article", "documentation"]):
            recommended_patterns.append("rag_knowledge")
        if any(k in uc_lower for k in ["trigger", "alert", "escalat", "event", "notify"]):
            recommended_patterns.append("event_driven")
        if any(k in uc_lower for k in ["approval", "human", "review", "authorize"]):
            recommended_patterns.append("human_in_loop")
        if any(k in uc_lower for k in ["orchestrat", "multi", "complex", "workbench", "cockpit"]):
            recommended_patterns.append("multi_agent_orchestration")
        if not recommended_patterns:
            recommended_patterns = ["copilot_to_d365", "agent_to_d365"]

        solution = {
            "use_case": use_case,
            "description": description,
            "environment": environment,
            "recommended_patterns": [
                {**INTEGRATION_PATTERNS[p], "pattern_id": p}
                for p in recommended_patterns if p in INTEGRATION_PATTERNS
            ],
            "suggested_components": self._suggest_components(uc_lower),
            "agent_architecture": self._suggest_agent_architecture(uc_lower),
            "data_flow": f"{use_case} → [Intake Layer] → [Processing Agent] → [D365 CE API] → [Response]",
            "requirements_coverage": {r: "TBD" for r in requirements},
            "environment_context_loaded": bool(env_context),
            "designed_at": datetime.utcnow().isoformat(),
            "designed_by": "MfgCoE Architect Agent",
            "next_steps": [
                "Have SME Agent generate use case definition",
                "Have Developer Agent scaffold agent code",
                "Create GitHub Issue to track implementation"
            ]
        }

        return json.dumps(solution, indent=2)

    def _suggest_components(self, uc_lower: str) -> List[str]:
        components = ["D365 Customer Engagement", "Azure Functions"]
        if "copilot" in uc_lower or "chat" in uc_lower or "bot" in uc_lower:
            components.append("Microsoft Copilot Studio")
        if "knowledge" in uc_lower or "article" in uc_lower:
            components.extend(["Azure AI Search", "Azure OpenAI Service"])
        if "automat" in uc_lower or "flow" in uc_lower or "trigger" in uc_lower:
            components.append("Power Automate")
        if "approval" in uc_lower or "teams" in uc_lower:
            components.append("Microsoft Teams")
        if "field" in uc_lower or "work order" in uc_lower:
            components.append("D365 Field Service")
        return list(set(components))

    def _suggest_agent_architecture(self, uc_lower: str) -> Dict:
        if any(k in uc_lower for k in ["orchestrat", "multi", "workbench"]):
            return {
                "pattern": "L0/L1 Multi-Agent (RAPP)",
                "l0_orchestrator": "Routes requests to specialist agents",
                "l1_agents": ["Specialist Agent 1", "Specialist Agent 2"],
                "reference": "See sma4_workbench_orchestrator_agent.py for pattern"
            }
        return {
            "pattern": "Single Agent (RAPP BasicAgent)",
            "agent_type": "Azure Function-hosted Python agent",
            "reference": "See agents/basic_agent.py and MfgCoEDeveloperAgent.get_agent_pattern()"
        }

    def _evaluate_pattern(self, **kwargs) -> str:
        pattern = kwargs.get("proposed_pattern", "")
        use_case = kwargs.get("use_case", "")

        # Match to known patterns
        matched = None
        for pid, pdata in INTEGRATION_PATTERNS.items():
            if pid.lower() in pattern.lower() or any(k in pattern.lower() for k in pdata["use_cases"]):
                matched = {"pattern_id": pid, **pdata}
                break

        if matched:
            return json.dumps({
                "proposed_pattern": pattern,
                "matched_pattern": matched,
                "fit_assessment": "Good match for known Microsoft stack pattern",
                "considerations": [
                    "Ensure D365 environment has required API access",
                    "Check Power Automate connector licensing",
                    "Validate Azure Function app settings and CORS"
                ]
            }, indent=2)
        else:
            return json.dumps({
                "proposed_pattern": pattern,
                "assessment": "No exact match in catalog — may be novel or composite pattern",
                "recommendation": "Consider decomposing into known patterns or flagging for architectural review",
                "known_patterns": list(INTEGRATION_PATTERNS.keys())
            }, indent=2)

    def _create_architecture_doc(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", "Solution")
        description = kwargs.get("description", "")
        environment = kwargs.get("environment", "master_ce_mfg")

        safe_name = use_case.lower().replace(" ", "_")[:40]
        doc_path = os.path.join(KNOWLEDGE_DIR, f"arch_{safe_name}.md")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

        doc = f"""# Architecture: {use_case}

**Environment:** {environment.replace("_", " ").title()}  
**Created:** {datetime.utcnow().strftime("%Y-%m-%d")}  
**Author:** MfgCoE Architect Agent  
**Status:** Draft

---

## Overview

{description or f"Architecture for {use_case} in the Discrete Manufacturing CoE."}

## Components

| Component | Role |
|---|---|
| D365 CE | [Define role] |
| Copilot Studio | [Define role] |
| Azure Functions | [Define role] |
| Power Automate | [Define role] |

## Data Flow

```
[User/Trigger]
    ↓
[Copilot Studio / API Gateway]
    ↓
[Azure Function — Agent Layer]
    ↓
[D365 CE Web API]
    ↓
[Response to User]
```

## Agent Architecture

- **Pattern:** [Single / L0-L1 Multi-Agent]
- **Orchestrator:** [Agent name]
- **Specialist Agents:** [List]

## Integration Points

| Source | Target | Method | Notes |
|---|---|---|---|
| [Source] | [Target] | [REST/Event/Flow] | [Notes] |

## Security & Auth

- [ ] Azure AD / Managed Identity
- [ ] D365 connection scoped to service account
- [ ] API keys stored in Azure Key Vault

## Open Questions

- [ ] [Question 1]
- [ ] [Question 2]

## Change Log

| Date | Change | Author |
|---|---|---|
| {datetime.utcnow().strftime("%Y-%m-%d")} | Initial draft | Architect Agent |
"""

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc)

        return json.dumps({"status": "created", "use_case": use_case, "path": doc_path}, indent=2)

    def _recommend_stack(self, **kwargs) -> str:
        description = kwargs.get("description", "")
        requirements = kwargs.get("requirements", [])
        desc_lower = description.lower()

        recommendations = []
        if any(k in desc_lower for k in ["chat", "bot", "self-service", "copilot"]):
            recommendations.append({"component": "Microsoft Copilot Studio", "reason": "Best for no-code/low-code bot authoring with D365 integration"})
        if any(k in desc_lower for k in ["crm", "case", "account", "contact", "opportunity"]):
            recommendations.append({"component": "D365 Customer Engagement", "reason": "Core CRM system for Discrete Mfg customer data"})
        if any(k in desc_lower for k in ["field", "work order", "technician", "dispatch"]):
            recommendations.append({"component": "D365 Field Service", "reason": "Purpose-built for field service / work order management"})
        if any(k in desc_lower for k in ["automate", "workflow", "trigger", "notification"]):
            recommendations.append({"component": "Power Automate", "reason": "Low-code workflow automation with 1000+ connectors"})
        if any(k in desc_lower for k in ["ai", "agent", "gpt", "intelligence", "predict"]):
            recommendations.append({"component": "Azure OpenAI + Azure Functions", "reason": "Serverless agent hosting with GPT-4o integration"})
        if any(k in desc_lower for k in ["knowledge", "search", "retrieval", "rag"]):
            recommendations.append({"component": "Azure AI Search", "reason": "Vector + semantic search for RAG patterns"})
        if not recommendations:
            recommendations = [
                {"component": "D365 Customer Engagement", "reason": "Core Discrete Mfg CRM platform"},
                {"component": "Azure Functions + Azure OpenAI", "reason": "Agent hosting backbone"}
            ]

        return json.dumps({
            "scenario": description[:100],
            "recommendations": recommendations,
            "full_stack_catalog": MS_STACK
        }, indent=2)

    def _add_to_knowledge_base(self, **kwargs) -> str:
        content = kwargs.get("knowledge_content", "")
        topic = kwargs.get("knowledge_topic", "architecture")
        if not content:
            return json.dumps({"error": "knowledge_content required"})

        safe_topic = topic.lower().replace(" ", "_")[:40]
        kb_file = os.path.join(KNOWLEDGE_DIR, f"arch_{safe_topic}.md")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

        existing = ""
        if os.path.exists(kb_file):
            with open(kb_file, "r", encoding="utf-8") as f:
                existing = f.read()

        entry = f"\n\n## Entry — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n{content}\n"
        if not existing:
            entry = f"# Architecture Knowledge: {topic}\n\n*Accumulated by MfgCoE Architect Agent*\n{entry}"

        with open(kb_file, "w", encoding="utf-8") as f:
            f.write(existing + entry)

        return json.dumps({"status": "saved", "topic": topic, "path": kb_file})

    def _search_knowledge_base(self, **kwargs) -> str:
        query = kwargs.get("search_query", "").lower()
        if not query:
            return json.dumps({"error": "search_query required"})

        results = []
        if os.path.exists(KNOWLEDGE_DIR):
            for fname in os.listdir(KNOWLEDGE_DIR):
                fpath = os.path.join(KNOWLEDGE_DIR, fname)
                if os.path.isfile(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    if query in content.lower():
                        matching_lines = [l.strip() for l in content.splitlines() if query in l.lower()][:3]
                        results.append({"file": fname, "matches": matching_lines})

        return json.dumps({"query": query, "results": results}, indent=2)

    def _get_integration_catalog(self, **kwargs) -> str:
        return json.dumps({
            "ms_stack_components": MS_STACK,
            "integration_patterns": INTEGRATION_PATTERNS,
            "total_patterns": len(INTEGRATION_PATTERNS)
        }, indent=2)

    def _assess_complexity(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", "")
        description = kwargs.get("description", "")
        requirements = kwargs.get("requirements", [])

        uc_lower = (use_case + " " + description).lower()
        complexity_score = 1

        high_complexity_signals = ["orchestrat", "multi-agent", "real-time", "erp integration", "finance", "bi-directional", "ml model"]
        medium_signals = ["approval", "rag", "knowledge base", "field service", "multi-step", "event-driven"]
        low_signals = ["lookup", "search", "status check", "simple query", "single agent"]

        for s in high_complexity_signals:
            if s in uc_lower: complexity_score += 2
        for s in medium_signals:
            if s in uc_lower: complexity_score += 1
        for s in low_signals:
            if s in uc_lower: complexity_score = max(1, complexity_score - 1)

        complexity_score += len(requirements) // 3

        if complexity_score <= 2:
            level, effort = "Low", "1-2 days"
        elif complexity_score <= 5:
            level, effort = "Medium", "3-5 days"
        elif complexity_score <= 8:
            level, effort = "High", "1-2 weeks"
        else:
            level, effort = "Very High", "2+ weeks"

        return json.dumps({
            "use_case": use_case,
            "complexity": level,
            "estimated_effort": effort,
            "complexity_score": complexity_score,
            "signals_detected": {
                "high": [s for s in high_complexity_signals if s in uc_lower],
                "medium": [s for s in medium_signals if s in uc_lower],
                "low": [s for s in low_signals if s in uc_lower]
            },
            "recommendation": f"This is a {level.lower()}-complexity use case. Estimated effort: {effort}."
        }, indent=2)
