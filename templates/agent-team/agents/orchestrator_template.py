"""
Agent: {{TEAM_SLUG}} Orchestrator
Purpose: L0 Orchestrator — routes requests to all persona agents,
         manages the GitHub feedback loop, and coordinates autonomous
         {{TEAM_NAME}} operations.

Pipeline (outcome-first):
  raw-idea → outcome-defined → use-case → tech-solution → agent-task → outcome-validated → done
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List

from agents.basic_agent import BasicAgent

# ── Import your persona agents here ───────────────────────────────────────────
# from {{TEAM_MODULE}}.agents.{{TEAM_SLUG}}_pm_agent import {{TeamSlug}}PMAgent
# from {{TEAM_MODULE}}.agents.{{TEAM_SLUG}}_sme_agent import {{TeamSlug}}SMEAgent
# ... add/remove based on your team_config.json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO = os.environ.get("COE_REPO", "{{REPO}}")
TEAM_LABEL = "{{TEAM_SLUG}}"

# ── Routing: map keywords to persona agents ────────────────────────────────────
# Add entries matching your team's personas and domain vocabulary
ROUTING_MAP = {
    "sme": {
        "keywords": ["process", "sop", "use case", "workflow", "business process", "document"],
        "agent_key": "sme",
        "description": "SME Agent (domain expertise, process docs)",
    },
    "developer": {
        "keywords": ["code", "build", "implement", "scaffold", "function", "script"],
        "agent_key": "developer",
        "description": "Developer Agent (code, configs)",
    },
    "architect": {
        "keywords": ["design", "architecture", "solution", "integration", "pattern", "stack"],
        "agent_key": "architect",
        "description": "Architect Agent (solution design)",
    },
    "pm": {
        "keywords": ["sprint", "backlog", "prioritize", "status", "plan", "digest"],
        "agent_key": "pm",
        "description": "PM Agent (backlog, sprint, status)",
    },
    "intake": {
        "keywords": ["idea", "log", "capture", "flag", "decision", "escalate"],
        "agent_key": "intake",
        "description": "Intake Agent (ideas, escalations)",
    },
    # Add more routing entries for your additional personas
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


class {{TeamSlug}}OrchestratorAgent(BasicAgent):
    """
    L0 Orchestrator for {{TEAM_NAME}}.

    Agent Team:
    {{AGENT_ROSTER_COMMENT}}
    """

    def __init__(self):
        self.name = "{{TeamSlug}}Orchestrator"
        self.metadata = {
            "name": self.name,
            "description": (
                "L0 Orchestrator for {{TEAM_NAME}}. "
                "Routes requests to persona agents, manages the GitHub feedback loop, "
                "and coordinates autonomous operations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "route_request",
                            "run_pipeline_item",
                            "get_status",
                            "morning_standup",
                            "process_bill_feedback",
                            "health_check",
                        ],
                        "description": "Orchestrator action to perform",
                    },
                    "use_case": {"type": "string"},
                    "description": {"type": "string"},
                    "issue_number": {"type": "integer"},
                    "target_agent": {"type": "string"},
                    "feedback_text": {"type": "string"},
                },
                "required": ["action"],
            },
        }

        # ── Instantiate your persona agents ────────────────────────────────────
        # self.pm = {{TeamSlug}}PMAgent()
        # self.sme = {{TeamSlug}}SMEAgent()
        # self.developer = {{TeamSlug}}DeveloperAgent()
        # self.architect = {{TeamSlug}}ArchitectAgent()
        # self.intake = {{TeamSlug}}IntakeAgent()
        # self.outcome_framer = {{TeamSlug}}OutcomeFramerAgent()
        # self.outcome_validator = {{TeamSlug}}OutcomeValidatorAgent()

        self.agents = {
            # "pm": self.pm,
            # "sme": self.sme,
            # "developer": self.developer,
            # "architect": self.architect,
            # "intake": self.intake,
            # "outcome_framer": self.outcome_framer,
            # "outcome_validator": self.outcome_validator,
        }

        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")
        handlers = {
            "route_request":         self._route_request,
            "run_pipeline_item":     self._run_pipeline_item,
            "get_status":            self._get_status,
            "morning_standup":       self._morning_standup,
            "process_bill_feedback": self._process_bill_feedback,
            "health_check":          self._health_check,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("Orchestrator error in %s: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    # ── Route request ──────────────────────────────────────────────────────────

    def _route_request(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", "")
        description = kwargs.get("description", "")
        combined = (use_case + " " + description).lower()

        matched_agent = None
        for key, cfg in ROUTING_MAP.items():
            if any(kw in combined for kw in cfg["keywords"]):
                matched_agent = key
                break

        if not matched_agent or matched_agent not in self.agents:
            return json.dumps({
                "status": "no_route",
                "message": "No agent matched. Add keywords to ROUTING_MAP or expand agent roster.",
                "use_case": use_case,
            })

        agent = self.agents[matched_agent]
        result_raw = agent.perform(action="get_status", use_case=use_case, description=description)
        result = json.loads(result_raw)
        return json.dumps({
            "status": "routed",
            "routed_to": matched_agent,
            "agent_response": result,
        })

    # ── Pipeline (outcome-first) ───────────────────────────────────────────────

    def _run_pipeline_item(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        use_case = kwargs.get("use_case", "")
        description = kwargs.get("description", "")

        steps_run = []

        # Step 0: Outcome Framer (gate — must define outcome before any build)
        if "outcome_framer" in self.agents:
            framer_raw = self.agents["outcome_framer"].perform(
                action="frame_outcome",
                use_case=use_case,
                description=description,
                issue_number=issue_number,
            )
            framer_result = json.loads(framer_raw)
            steps_run.append({"step": "outcome_framing", "result": framer_result})
            if framer_result.get("pipeline_blocked"):
                return json.dumps({
                    "status": "blocked_needs_outcome",
                    "blocked_reason": framer_result.get("blocked_reason", ""),
                    "questions": framer_result.get("questions", []),
                    "steps_run": steps_run,
                })

        # Step 1: SME (use case definition)
        if "sme" in self.agents:
            sme_raw = self.agents["sme"].perform(
                action="define_use_case",
                use_case=use_case,
                description=description,
                issue_number=issue_number,
            )
            steps_run.append({"step": "sme", "result": json.loads(sme_raw)})

        # Step 2: Architect (solution design)
        if "architect" in self.agents:
            arch_raw = self.agents["architect"].perform(
                action="design_solution",
                use_case=use_case,
                description=description,
                issue_number=issue_number,
            )
            steps_run.append({"step": "architect", "result": json.loads(arch_raw)})

        # Step 3: Developer (implementation)
        if "developer" in self.agents:
            dev_raw = self.agents["developer"].perform(
                action="generate_code",
                use_case=use_case,
                description=description,
                issue_number=issue_number,
            )
            steps_run.append({"step": "developer", "result": json.loads(dev_raw)})

        # Step 4: Outcome Validator (gate — verify before closing)
        if "outcome_validator" in self.agents:
            val_raw = self.agents["outcome_validator"].perform(
                action="validate_outcome",
                use_case=use_case,
                description=description,
                issue_number=issue_number,
            )
            steps_run.append({"step": "outcome_validation", "result": json.loads(val_raw)})

        return json.dumps({
            "status": "pipeline_advanced",
            "steps_run": steps_run,
            "summary": f"Pipeline completed {len(steps_run)} steps for: {use_case}",
        })

    # ── Supporting actions ─────────────────────────────────────────────────────

    def _get_status(self, **kwargs) -> str:
        agent_statuses = {}
        for key, agent in self.agents.items():
            try:
                status_raw = agent.perform(action="get_status")
                agent_statuses[key] = json.loads(status_raw).get("status", "unknown")
            except Exception as e:
                agent_statuses[key] = f"error: {e}"
        return json.dumps({
            "orchestrator": "ready",
            "repo": REPO,
            "agents": agent_statuses,
            "team": "{{TEAM_NAME}}",
        })

    def _morning_standup(self, **kwargs) -> str:
        issues = _gh(["issue", "list", "--repo", REPO, "--label", TEAM_LABEL,
                      "--state", "open", "--json", "number,title,labels"])
        return json.dumps({
            "status": "standup_complete",
            "open_items": len(issues) if isinstance(issues, list) else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "team": "{{TEAM_NAME}}",
        })

    def _process_bill_feedback(self, **kwargs) -> str:
        feedback = kwargs.get("feedback_text", kwargs.get("feedback", ""))
        issue_number = kwargs.get("issue_number")
        if not feedback or not issue_number:
            return json.dumps({"error": "feedback_text and issue_number required"})
        # Re-run the pipeline with the feedback as additional context
        return self._run_pipeline_item(
            issue_number=issue_number,
            use_case=f"Bill's feedback: {feedback}",
            description=feedback,
        )

    def _health_check(self, **kwargs) -> str:
        health = {"orchestrator": "healthy", "agents": {}}
        for key, agent in self.agents.items():
            try:
                agent.perform(action="get_status")
                health["agents"][key] = "healthy"
            except Exception as e:
                health["agents"][key] = f"unhealthy: {e}"
        all_healthy = all(v == "healthy" for v in health["agents"].values())
        health["overall"] = "healthy" if all_healthy else "degraded"
        return json.dumps(health)
