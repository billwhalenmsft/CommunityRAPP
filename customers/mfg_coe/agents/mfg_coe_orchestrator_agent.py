"""
Agent: MfgCoE Orchestrator Agent
Purpose: L0 Orchestrator for the Discrete Manufacturing Center of Excellence.
         Routes requests to the correct persona agents, manages the GitHub
         human-in-the-loop feedback cycle, and coordinates autonomous CoE operations.

Architecture:
  L0  MfgCoEOrchestrator        ← YOU ARE HERE
   ├── MfgCoEIntakeAgent         — Idea capture, solution logging, Bill escalation
   ├── MfgCoEPMAgent             — Backlog, sprint planning, weekly digest
   ├── MfgCoESMEAgent            — SOPs, process docs, use case definitions
   ├── MfgCoEDeveloperAgent      — Agent code, D365 configs, RAPP artifacts
   ├── MfgCoEArchitectAgent      — Solution design, MS stack patterns
   └── MfgCoECustomerPersonaAgent — Customer simulation, Playwright test scripts

Actions:
  route_request       — Intelligently route any request to the right persona agent
  run_pipeline_item   — Run a GitHub issue through the full Idea→UseCase→Design→Build pipeline
  get_coe_status      — Full CoE status: open items, pending decisions, agents ready
  morning_standup     — Generate daily standup: what's in progress, blocked, next up
  process_bill_feedback — Parse a GitHub issue comment from Bill and continue agent work
  health_check        — Verify all L1 agents are operational
  get_architecture    — Return CoE architecture overview
"""

import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, List

from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.mfg_coe_intake_agent import MfgCoEIntakeAgent
from customers.mfg_coe.agents.mfg_coe_pm_agent import MfgCoEPMAgent
from customers.mfg_coe.agents.mfg_coe_sme_agent import MfgCoESMEAgent
from customers.mfg_coe.agents.mfg_coe_developer_agent import MfgCoEDeveloperAgent
from customers.mfg_coe.agents.mfg_coe_architect_agent import MfgCoEArchitectAgent
from customers.mfg_coe.agents.mfg_coe_customer_persona_agent import MfgCoECustomerPersonaAgent
from customers.mfg_coe.agents.context_card_loader import load_all_context_cards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO = "kody-w/CommunityRAPP"
COE_LABEL = "mfg-coe"

# Routing keywords to persona agents
ROUTING_MAP = {
    "sme": {
        "keywords": ["sop", "process", "use case", "business process", "workflow", "standard operating", "procedure", "crm process", "document"],
        "agent_key": "sme",
        "description": "SME Agent (SOPs, processes, use cases)"
    },
    "developer": {
        "keywords": ["code", "agent", "scaffold", "build", "implement", "python", "function", "playwright", "test", "d365 config"],
        "agent_key": "developer",
        "description": "Developer Agent (code, configs, scaffolding)"
    },
    "architect": {
        "keywords": ["design", "architecture", "solution", "integration", "stack", "pattern", "evaluate", "complexity", "components"],
        "agent_key": "architect",
        "description": "Architect Agent (solution design, stack recommendations)"
    },
    "pm": {
        "keywords": ["sprint", "backlog", "status", "digest", "prioritize", "assign", "pipeline stage", "weekly", "planning"],
        "agent_key": "pm",
        "description": "PM Agent (backlog, sprint, status)"
    },
    "intake": {
        "keywords": ["idea", "log", "capture", "flag", "decision", "bill", "needs-bill", "solution log"],
        "agent_key": "intake",
        "description": "Intake Agent (ideas, solutions, flagging)"
    },
    "customer_persona": {
        "keywords": ["customer", "persona", "test", "scenario", "simulate", "navico", "otis", "zurn", "vermeer", "carrier"],
        "agent_key": "customer_persona",
        "description": "Customer Persona Agent (testing, simulation)"
    }
}


def _gh(args: List[str]) -> Any:
    cmd = ["gh"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}


class MfgCoEOrchestratorAgent(BasicAgent):
    """
    L0 Orchestrator for the Discrete Manufacturing CoE.
    Routes requests to persona agents, manages the GitHub feedback loop,
    and coordinates autonomous CoE operations.
    """

    def __init__(self):
        self.name = "MfgCoEOrchestrator"
        self.metadata = {
            "name": self.name,
            "description": (
                "Master Orchestrator for the Discrete Manufacturing Center of Excellence. "
                "Routes requests to the correct CoE persona agent (PM, SME, Developer, Architect, "
                "Customer Persona, Intake/Logger), manages the GitHub human-in-the-loop steering loop, "
                "and coordinates autonomous agent operations. "
                "Use this as the single entry point for all CoE work."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "route_request",
                            "run_pipeline_item",
                            "get_coe_status",
                            "morning_standup",
                            "process_bill_feedback",
                            "health_check",
                            "get_architecture"
                        ],
                        "description": "Orchestrator action"
                    },
                    "request": {
                        "type": "string",
                        "description": "Free-text request to route to the right persona agent"
                    },
                    "target_persona": {
                        "type": "string",
                        "enum": ["pm", "sme", "developer", "architect", "intake", "customer_persona"],
                        "description": "Force routing to a specific persona (optional — auto-routes if not specified)"
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "GitHub Issue number for pipeline or feedback processing"
                    },
                    "persona_action": {
                        "type": "string",
                        "description": "Specific action to call on the target persona agent"
                    },
                    "persona_params": {
                        "type": "object",
                        "description": "Parameters to pass to the target persona agent's perform() method"
                    },
                    "feedback_text": {
                        "type": "string",
                        "description": "Bill's feedback text from a GitHub comment"
                    }
                },
                "required": ["action"]
            }
        }

        # Initialize all L1 agents
        self.intake = MfgCoEIntakeAgent()
        self.pm = MfgCoEPMAgent()
        self.sme = MfgCoESMEAgent()
        self.developer = MfgCoEDeveloperAgent()
        self.architect = MfgCoEArchitectAgent()
        self.customer_persona = MfgCoECustomerPersonaAgent()

        self.agents = {
            "intake": self.intake,
            "pm": self.pm,
            "sme": self.sme,
            "developer": self.developer,
            "architect": self.architect,
            "customer_persona": self.customer_persona,
        }

        # Load context cards at startup
        try:
            self._context_cards = load_all_context_cards()
        except Exception:
            self._context_cards = {}

        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_coe_status")
        handlers = {
            "route_request":          self._route_request,
            "run_pipeline_item":      self._run_pipeline_item,
            "get_coe_status":         self._get_coe_status,
            "morning_standup":        self._morning_standup,
            "process_bill_feedback":  self._process_bill_feedback,
            "health_check":           self._health_check,
            "get_architecture":       self._get_architecture,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoEOrchestrator error in {action}: {e}")
            return json.dumps({"error": str(e)})

    # ── Route Request ─────────────────────────────────────────────

    def _route_request(self, **kwargs) -> str:
        request = kwargs.get("request", "")
        target_persona = kwargs.get("target_persona")
        persona_action = kwargs.get("persona_action")
        persona_params = kwargs.get("persona_params", {})

        # Auto-detect persona if not specified
        if not target_persona:
            target_persona = self._detect_persona(request)

        agent = self.agents.get(target_persona)
        if not agent:
            return json.dumps({"error": f"Unknown persona: {target_persona}"})

        # Build params for the agent
        params = {"action": persona_action or self._suggest_action(target_persona, request)}
        params.update(persona_params)
        if "description" not in params and request:
            params["description"] = request
        if "topic" not in params and request:
            params["topic"] = request[:80]

        result = agent.perform(**params)

        return json.dumps({
            "routed_to": target_persona,
            "agent": agent.name,
            "action_called": params.get("action"),
            "result": json.loads(result) if isinstance(result, str) else result
        }, indent=2)

    def _detect_persona(self, request: str) -> str:
        req_lower = request.lower()
        scores = {}
        for persona, config in ROUTING_MAP.items():
            score = sum(1 for kw in config["keywords"] if kw in req_lower)
            if score > 0:
                scores[persona] = score
        if not scores:
            return "pm"  # Default to PM
        return max(scores, key=scores.get)

    def _suggest_action(self, persona: str, request: str) -> str:
        req_lower = request.lower()
        suggestions = {
            "sme": {
                "sop": "generate_sop",
                "process": "document_process",
                "use case": "define_use_case",
                "review": "review_sop",
            },
            "developer": {
                "scaffold": "scaffold_agent",
                "code": "scaffold_agent",
                "d365": "generate_d365_config",
                "playwright": "generate_playwright_test",
                "review": "code_review",
            },
            "architect": {
                "design": "design_solution",
                "evaluate": "evaluate_pattern",
                "stack": "recommend_stack",
                "complexity": "assess_complexity",
                "architecture": "create_architecture_doc",
            },
            "pm": {
                "sprint": "plan_sprint",
                "status": "get_status",
                "digest": "generate_weekly_digest",
                "conflict": "detect_conflicts",
                "prioritize": "prioritize_backlog",
            },
            "intake": {
                "idea": "log_idea",
                "solution": "log_solution",
                "flag": "flag_for_bill",
                "decision": "get_pending_decisions",
            },
            "customer_persona": {
                "simulate": "simulate_conversation",
                "test": "generate_test_script",
                "scenario": "get_scenarios",
                "profile": "get_customer_profiles",
            }
        }
        persona_map = suggestions.get(persona, {})
        for kw, action in persona_map.items():
            if kw in req_lower:
                return action
        # Default actions per persona
        defaults = {
            "sme": "generate_sop", "developer": "scaffold_agent",
            "architect": "design_solution", "pm": "get_status",
            "intake": "get_backlog", "customer_persona": "get_scenarios"
        }
        return defaults.get(persona, "get_status")

    # ── Run Pipeline Item ─────────────────────────────────────────

    def _run_pipeline_item(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        if not issue_number:
            return json.dumps({"error": "issue_number required"})

        # Get issue details
        result = _gh([
            "issue", "view", str(issue_number), "--repo", REPO,
            "--json", "number,title,body,labels"
        ])

        if "error" in result:
            return json.dumps({"error": result["error"]})

        title = result.get("title", "")
        body = result.get("body", "")
        labels = [l["name"] for l in result.get("labels", [])]

        steps_taken = []

        # Step 1: SME defines use case (if still raw-idea)
        if "raw-idea" in labels or "use-case" not in labels:
            uc_result = self.sme.perform(
                action="define_use_case",
                topic=title,
                description=body[:300]
            )
            steps_taken.append({"step": "use_case_defined", "result": json.loads(uc_result)})
            self.pm.perform(action="advance_pipeline_stage", issue_number=issue_number, target_stage="use-case")

        # Step 2: Architect designs solution
        arch_result = self.architect.perform(
            action="design_solution",
            use_case=title,
            description=body[:300]
        )
        arch_data = json.loads(arch_result)
        steps_taken.append({"step": "solution_designed", "result": arch_data})
        self.pm.perform(action="advance_pipeline_stage", issue_number=issue_number, target_stage="tech-solution")

        # Step 3: Log solution summary back to GitHub
        summary = f"## 🏗️ Architecture Design Complete\n\n**Recommended Patterns:** {', '.join([p.get('pattern_id','?') for p in arch_data.get('recommended_patterns',[])])}\n\n**Components:** {', '.join(arch_data.get('suggested_components',[]))}\n\n**Next:** Developer agent to scaffold implementation.\n\n---\n*Pipeline run by CoE Orchestrator at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
        _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", summary])
        self.pm.perform(action="assign_work", issue_number=issue_number, persona="developer",
                        context="Architecture complete — ready for Developer agent to scaffold.")

        return json.dumps({
            "issue_number": issue_number,
            "title": title,
            "pipeline_steps": steps_taken,
            "current_stage": "tech-solution",
            "assigned_to": "developer",
            "status": "pipeline_advanced"
        }, indent=2)

    # ── CoE Status ────────────────────────────────────────────────

    def _get_coe_status(self, **kwargs) -> str:
        pm_status = json.loads(self.pm.perform(action="get_status"))
        pending = json.loads(self.intake.perform(action="get_pending_decisions"))
        sops = json.loads(self.sme.perform(action="list_sops"))

        return json.dumps({
            "as_of": datetime.utcnow().isoformat(),
            "backlog": {
                "open_items": pm_status.get("open_items", 0),
                "needs_bill": pm_status.get("needs_bill", 0),
                "in_progress": pm_status.get("in_progress", 0),
                "completed_last_7_days": pm_status.get("completed_last_7_days", 0)
            },
            "pending_decisions": pending.get("items", []),
            "sops_generated": sops.get("total_sops", 0),
            "context_cards_loaded": list(self._context_cards.keys()),
            "agents_ready": list(self.agents.keys()),
            "agents_healthy": len(self.agents)
        }, indent=2)

    # ── Morning Standup ───────────────────────────────────────────

    def _morning_standup(self, **kwargs) -> str:
        pm_status = json.loads(self.pm.perform(action="get_status"))
        sprint = json.loads(self.pm.perform(action="plan_sprint", sprint_size=3))
        pending = json.loads(self.intake.perform(action="get_pending_decisions"))

        lines = [
            f"# 🌅 CoE Morning Standup — {datetime.utcnow().strftime('%Y-%m-%d')}",
            "",
            f"## 📊 Status",
            f"- Open items: {pm_status.get('open_items', 0)}",
            f"- In progress: {pm_status.get('in_progress', 0)}",
            f"- Completed last 7 days: {pm_status.get('completed_last_7_days', 0)}",
            "",
            f"## 🚨 Needs Bill's Input ({len(pending.get('items', []))})",
        ]
        for item in pending.get("items", []):
            lines.append(f"- #{item['number']} {item['title']} — {item['url']}")
        if not pending.get("items"):
            lines.append("- None — agents operating autonomously 🎉")

        lines += [
            "",
            "## 🎯 Up Next (Top 3 Sprint Items)",
        ]
        for item in sprint.get("items", []):
            lines.append(f"- #{item['number']} {item['title']} → {item['suggested_persona'].upper()} Agent")

        return json.dumps({
            "standup": "\n".join(lines),
            "open_items": pm_status.get("open_items", 0),
            "needs_bill": len(pending.get("items", [])),
            "next_sprint_items": sprint.get("items", [])
        }, indent=2)

    # ── Process Bill's Feedback ───────────────────────────────────

    def _process_bill_feedback(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        feedback_text = kwargs.get("feedback_text", "")

        if not issue_number or not feedback_text:
            return json.dumps({"error": "issue_number and feedback_text required"})

        # Log the decision
        self.intake.perform(
            action="log_decision",
            issue_number=issue_number,
            decision=f"Bill's direction: {feedback_text}"
        )

        # Detect intent from feedback
        feedback_lower = feedback_text.lower()
        next_action = "continue"
        assigned_to = None

        if any(k in feedback_lower for k in ["build", "code", "implement", "scaffold"]):
            assigned_to = "developer"
            next_action = "scaffold_agent"
        elif any(k in feedback_lower for k in ["design", "architecture", "plan"]):
            assigned_to = "architect"
            next_action = "design_solution"
        elif any(k in feedback_lower for k in ["sop", "process", "document"]):
            assigned_to = "sme"
            next_action = "generate_sop"
        elif any(k in feedback_lower for k in ["close", "cancel", "skip", "not needed"]):
            _gh(["issue", "close", str(issue_number), "--repo", REPO,
                 "--comment", "Closed per Bill's direction."])
            return json.dumps({"status": "closed", "issue_number": issue_number})

        if assigned_to:
            self.pm.perform(action="assign_work", issue_number=issue_number, persona=assigned_to,
                            context=f"Assigned per Bill's feedback: {feedback_text[:100]}")

        return json.dumps({
            "status": "feedback_processed",
            "issue_number": issue_number,
            "decision_logged": True,
            "assigned_to": assigned_to,
            "next_action": next_action,
            "feedback_summary": feedback_text[:200]
        }, indent=2)

    # ── Health Check ──────────────────────────────────────────────

    def _health_check(self, **kwargs) -> str:
        health = {}
        test_calls = {
            "intake":          {"action": "get_backlog"},
            "pm":              {"action": "get_status"},
            "sme":             {"action": "list_sops"},
            "developer":       {"action": "get_agent_pattern"},
            "architect":       {"action": "get_integration_catalog"},
            "customer_persona": {"action": "get_customer_profiles"},
        }
        for name, params in test_calls.items():
            try:
                result = self.agents[name].perform(**params)
                parsed = json.loads(result)
                healthy = "error" not in parsed
                health[name] = {"status": "healthy" if healthy else "degraded", "response_keys": list(parsed.keys())[:3]}
            except Exception as e:
                health[name] = {"status": "error", "error": str(e)}

        all_healthy = all(h["status"] == "healthy" for h in health.values())
        return json.dumps({
            "overall": "healthy" if all_healthy else "degraded",
            "agents": health,
            "context_cards": list(self._context_cards.keys()),
            "checked_at": datetime.utcnow().isoformat()
        }, indent=2)

    # ── Architecture ──────────────────────────────────────────────

    def _get_architecture(self, **kwargs) -> str:
        return json.dumps({
            "name": "Mfg CoE Orchestrator",
            "version": "1.0.0",
            "pattern": "L0/L1 Multi-Agent (RAPP)",
            "github_repo": REPO,
            "storage": "Azure File Storage — mfg_coe/ share",
            "human_in_loop": "GitHub Issues with needs-bill label",
            "l1_agents": {
                "intake": {"file": "mfg_coe_intake_agent.py", "purpose": "Idea logging, solution records, Bill escalation"},
                "pm": {"file": "mfg_coe_pm_agent.py", "purpose": "Backlog, sprint planning, weekly digest, conflict detection"},
                "sme": {"file": "mfg_coe_sme_agent.py", "purpose": "SOPs, process docs, use case definitions"},
                "developer": {"file": "mfg_coe_developer_agent.py", "purpose": "Agent code, D365 configs, Playwright tests"},
                "architect": {"file": "mfg_coe_architect_agent.py", "purpose": "Solution design, MS stack recommendations"},
                "customer_persona": {"file": "mfg_coe_customer_persona_agent.py", "purpose": "Customer simulation, test scenario execution"}
            },
            "demo_environments": list(self._context_cards.keys()),
            "customers_with_test_profiles": ["navico", "otis", "zurnelkay"],
            "pipeline_stages": ["raw-idea", "use-case", "tech-solution", "agent-task", "done"]
        }, indent=2)
