"""
Agent: MfgCoE DevOps PM Agent
Purpose: Scopes incoming issues into structured project plans, identifies which
         specialist developers are needed, and returns an ordered list of deliverables
         for the orchestrator to execute.  Acts as the "team lead" layer between the
         pipeline (outcome/use-case/arch) and the specialist build agents.

Actions:
  scope_issue         — Parse an issue and return a project plan with deliverables
  create_project_plan — Write a project_plan.md artifact to disk
  get_team_roster     — Return the full specialist roster and their capabilities
  assess_complexity   — Rate effort (S/M/L/XL) and risk for an issue
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

# ── Specialist roster ─────────────────────────────────────────────────────────
SPECIALISTS = {
    "python_dev": {
        "display": "Python / Azure Functions Developer",
        "description": "Azure Function agents, CoE runner updates, GitHub Actions workflows, REST APIs, Python scripts",
        "keywords": ["azure function", "python", "api", "coe runner", "github action", "workflow",
                     "backend", "rest", "webhook", "endpoint", "script", "runner"],
        "outputs": ["*.py agent file", "GitHub Actions YAML", "requirements.txt patch"],
        "agent_class": "MfgCoEDeveloperAgent",
        "module": "customers.mfg_coe.agents.mfg_coe_developer_agent",
    },
    "d365_dev": {
        "display": "Dynamics 365 / Dataverse Developer",
        "description": "D365 CE entities, fields, forms, views, provisioning scripts, OData queries, solution packages",
        "keywords": ["d365", "dynamics", "dataverse", "entity", "field", "form", "view", "odata",
                     "crm", "ce", "solution", "account", "contact", "case", "queue", "plugin",
                     "business rule", "workflow", "provision"],
        "outputs": ["Dataverse entity schema JSON", "PowerShell provisioning script", "OData query examples"],
        "agent_class": "MfgCoED365DevAgent",
        "module": "customers.mfg_coe.agents.mfg_coe_d365_dev_agent",
    },
    "pp_dev": {
        "display": "Power Platform Developer",
        "description": "Copilot Studio YAML topics, Power Automate flows (Skills kind), Power Apps canvas apps, custom connectors",
        "keywords": ["copilot studio", "power automate", "flow", "power apps", "canvas app",
                     "model-driven", "topic", "bot", "connector", "skill", "action", "portal",
                     "power pages", "pva", "virtual agent"],
        "outputs": ["Copilot Studio YAML topic", "Power Automate flow definition JSON", "Power Apps formula stubs"],
        "agent_class": "MfgCoEPPDevAgent",
        "module": "customers.mfg_coe.agents.mfg_coe_pp_dev_agent",
    },
    "ai_specialist": {
        "display": "AI / Azure Foundry Specialist",
        "description": "Azure AI Foundry projects, Azure OpenAI prompts, declarative Copilot agents for M365, Semantic Kernel, AI Search, RAG pipelines",
        "keywords": ["ai foundry", "azure openai", "openai", "gpt", "prompt", "embedding",
                     "ai search", "semantic kernel", "rag", "declarative agent", "m365 copilot",
                     "copilot extensibility", "plugin manifest", "foundry", "langchain"],
        "outputs": ["System prompt", "Azure AI Foundry config", "Declarative agent manifest", "SK agent pattern"],
        "agent_class": "MfgCoEAISpecialistAgent",
        "module": "customers.mfg_coe.agents.mfg_coe_ai_specialist_agent",
    },
    "analytics_dev": {
        "display": "Analytics & Reporting Developer",
        "description": "Power BI reports, D365 dashboards, Excel/Power Query templates, embedded analytics, Azure Monitor workbooks, reporting APIs, and data export pipelines. Not limited to Power BI — picks the right reporting tool for the audience.",
        "keywords": ["power bi", "report", "dashboard", "kpi", "dax", "analytics", "visualization",
                     "scorecard", "excel", "power query", "azure monitor", "workbook", "embedded",
                     "paginated", "dataset", "metric", "chart", "graph", "trend", "export", "data model"],
        "outputs": ["Report design spec", "DAX/Power Query stubs", "Dashboard layout", "D365 dashboard XML"],
        "agent_class": "MfgCoEAnalyticsDevAgent",
        "module": "customers.mfg_coe.agents.mfg_coe_analytics_dev_agent",
    },
}

# Dependency ordering — if both are needed, d365_dev must run first (PP/AI need the schema)
DISCIPLINE_ORDER = ["d365_dev", "ai_specialist", "python_dev", "pp_dev", "analytics_dev"]


def _detect_disciplines(title: str, body: str) -> List[str]:
    """Return ordered list of specialist keys needed for this issue."""
    combined = (title + " " + body).lower()
    needed = []
    for key, spec in SPECIALISTS.items():
        if any(kw in combined for kw in spec["keywords"]):
            needed.append(key)
    if not needed:
        # Default for Mfg CoE: D365 + Power Platform
        needed = ["d365_dev", "pp_dev"]
    # Apply dependency ordering
    return [k for k in DISCIPLINE_ORDER if k in needed]


def _estimate_complexity(title: str, body: str, disciplines: List[str]) -> Dict[str, Any]:
    """Estimate effort size and risk."""
    combined = (title + " " + body).lower()
    n_disciplines = len(disciplines)

    xl_signals = ["full solution", "end-to-end", "complete", "phase", "entire", "all agents", "suite"]
    l_signals = ["integration", "multiple", "flows", "several", "pipeline", "provisioning", "foundry"]
    s_signals = ["quick", "simple", "single", "stub", "template", "example", "scaffold"]

    if any(s in combined for s in xl_signals) or n_disciplines >= 4:
        size = "XL"
    elif any(s in combined for s in l_signals) or n_disciplines >= 3:
        size = "L"
    elif n_disciplines == 1 and any(s in combined for s in s_signals):
        size = "S"
    elif n_disciplines <= 2:
        size = "M"
    else:
        size = "L"

    risk = "medium"
    if any(kw in combined for kw in ["production", "live", "deploy", "real data", "customer"]):
        risk = "high"
    elif size in ("S",):
        risk = "low"

    return {"size": size, "risk": risk, "discipline_count": n_disciplines}


class MfgCoEDevOpsPMAgent(BasicAgent):
    """DevOps Project Manager — scopes issues, builds project plans, assigns specialists."""

    def __init__(self):
        self.name = "MfgCoEDevOpsPM"
        self.metadata = {
            "name": self.name,
            "description": (
                "DevOps Project Manager for the Discrete Manufacturing CoE. "
                "Analyzes GitHub issues to create structured project plans, "
                "identifies which specialist developers are needed (D365, Power Platform, "
                "AI/Foundry, Python, Power BI), defines deliverables in dependency order, "
                "and writes a project_plan.md artifact for Bill's review before build begins."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["scope_issue", "create_project_plan", "get_team_roster", "assess_complexity"],
                        "description": "DevOps PM action to perform",
                    },
                    "issue_title": {"type": "string", "description": "GitHub issue title"},
                    "issue_body": {"type": "string", "description": "GitHub issue body/description"},
                    "issue_number": {"type": "integer", "description": "GitHub issue number"},
                    "project_id": {"type": "string", "description": "Optional project folder ID"},
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "scope_issue")
        handlers = {
            "scope_issue": self._scope_issue,
            "create_project_plan": self._create_project_plan,
            "get_team_roster": self._get_team_roster,
            "assess_complexity": self._assess_complexity,
        }
        fn = handlers.get(action)
        if not fn:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return fn(**kwargs)
        except Exception as e:
            logger.error("DevOpsPM %s failed: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    def _scope_issue(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        issue_number = kwargs.get("issue_number", 0)

        disciplines = _detect_disciplines(title, body)
        complexity = _estimate_complexity(title, body, disciplines)

        # Build deliverables list in dependency order
        deliverables = []
        for i, disc in enumerate(disciplines):
            spec = SPECIALISTS[disc]
            deliverables.append({
                "deliverable_id": f"DEL-{i+1:02d}",
                "discipline": disc,
                "specialist": spec["display"],
                "description": f"[{spec['display']}] Build artifact for: {title}",
                "expected_outputs": spec["outputs"],
                "depends_on": [f"DEL-{j+1:02d}" for j in range(i)],  # each depends on prior
                "agent_class": spec["agent_class"],
                "module": spec["module"],
            })

        # Write project plan to disk
        plan_artifact = self._write_project_plan(
            issue_number=issue_number,
            title=title,
            body=body,
            disciplines=disciplines,
            deliverables=deliverables,
            complexity=complexity,
        )

        return json.dumps({
            "status": "scoped",
            "issue_number": issue_number,
            "title": title,
            "disciplines": disciplines,
            "deliverables": deliverables,
            "complexity": complexity,
            "project_plan_path": plan_artifact,
            "summary": (
                f"Scoped into {len(deliverables)} deliverable(s) across "
                f"{', '.join(SPECIALISTS[d]['display'] for d in disciplines)}. "
                f"Complexity: {complexity['size']}, Risk: {complexity['risk']}."
            ),
        }, indent=2)

    def _write_project_plan(self, issue_number: int, title: str, body: str,
                             disciplines: List[str], deliverables: List[dict],
                             complexity: Dict) -> str:
        """Write project_plan.md to the CoE knowledge base and return the relative path."""
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:50]
        kb_dir = os.path.join(REPO_ROOT, "customers", "mfg_coe", "knowledge_base")
        os.makedirs(kb_dir, exist_ok=True)
        fname = f"project_plan_{slug}.md"
        fpath = os.path.join(kb_dir, fname)

        lines = [
            f"# Project Plan — {title}",
            f"",
            f"> **Issue:** #{issue_number}  |  **Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            f"> **Complexity:** {complexity['size']}  |  **Risk:** {complexity['risk']}  "
            f"|  **Disciplines:** {len(disciplines)}",
            f"",
            f"## Issue Summary",
            f"",
            f"{body[:600].strip()}",
            f"",
            f"## Deliverables",
            f"",
            f"| # | Specialist | Description | Depends On |",
            f"|---|---|---|---|",
        ]
        for d in deliverables:
            dep_str = ", ".join(d["depends_on"]) if d["depends_on"] else "—"
            lines.append(f"| {d['deliverable_id']} | {d['specialist']} | {d['description']} | {dep_str} |")

        lines += [
            f"",
            f"## Expected Outputs",
            f"",
        ]
        for d in deliverables:
            lines.append(f"### {d['deliverable_id']} — {d['specialist']}")
            for out in d["expected_outputs"]:
                lines.append(f"- {out}")
            lines.append("")

        lines += [
            f"## Review Checklist",
            f"",
            f"- [ ] Deliverables match the issue intent",
            f"- [ ] Specialist assignments are correct",
            f"- [ ] Dependencies are in the right order",
            f"- [ ] Complexity estimate is reasonable",
            f"",
            f"---",
            f"*Generated by MfgCoE DevOps PM Agent*",
        ]

        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        rel = os.path.relpath(fpath, REPO_ROOT).replace("\\", "/")
        logger.info("Project plan written to %s", rel)
        return rel

    def _create_project_plan(self, **kwargs) -> str:
        return self._scope_issue(**kwargs)

    def _get_team_roster(self, **kwargs) -> str:
        roster = []
        for key, spec in SPECIALISTS.items():
            roster.append({
                "key": key,
                "display": spec["display"],
                "description": spec["description"],
                "typical_outputs": spec["outputs"],
                "keywords": spec["keywords"][:6],
            })
        return json.dumps({
            "status": "ok",
            "team_size": len(roster),
            "specialists": roster,
            "collaboration_model": (
                "DevOps PM scopes the issue → writes project_plan.md → orchestrator calls "
                "specialists in dependency order, passing each specialist's artifacts as "
                "context to the next. D365 Dev always runs first (schema drives everything else)."
            ),
        }, indent=2)

    def _assess_complexity(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        disciplines = _detect_disciplines(title, body)
        complexity = _estimate_complexity(title, body, disciplines)
        return json.dumps({
            "status": "ok",
            "complexity": complexity,
            "disciplines_detected": disciplines,
            "recommendation": (
                "Assign to sprint" if complexity["size"] in ("S", "M")
                else "Break into sub-issues before assigning"
            ),
        }, indent=2)
