"""
Agent: MfgCoE Orchestrator Agent
Purpose: L0 Orchestrator for the Discrete Manufacturing Center of Excellence.
         Routes requests to the correct persona agents, manages the GitHub
         human-in-the-loop feedback cycle, and coordinates autonomous CoE operations.

Architecture:
  L0  MfgCoEOrchestrator          ← YOU ARE HERE
   ├── MfgCoEOutcomeFramerAgent    — Defines business problem + KPI BEFORE any build (runs first)
   ├── MfgCoEIntakeAgent           — Idea capture, solution logging, Bill escalation
   ├── MfgCoEPMAgent               — Backlog, sprint planning, weekly digest
   ├── MfgCoESMEAgent              — SOPs, process docs, use case definitions
   ├── MfgCoEDeveloperAgent        — Agent code, D365 configs, RAPP artifacts
   ├── MfgCoEArchitectAgent        — Solution design, MS stack patterns
   ├── MfgCoECustomerPersonaAgent  — Customer simulation, Playwright test scripts
   └── MfgCoEOutcomeValidatorAgent — Validates outcome was delivered BEFORE closing (runs last)

Pipeline (outcome-first):
  raw-idea → outcome-defined → use-case → tech-solution → agent-task → outcome-validated → done

Actions:
  route_request       — Intelligently route any request to the right persona agent
  run_pipeline_item   — Run a GitHub issue through the full outcome-first pipeline
  get_coe_status      — Full CoE status: open items, pending decisions, agents ready
  morning_standup     — Generate daily standup: what's in progress, blocked, next up
  process_bill_feedback — Parse a GitHub issue comment from Bill and continue agent work
  health_check        — Verify all L1 agents are operational
  get_architecture    — Return CoE architecture overview
"""

import json
import logging
import os
import re
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
from customers.mfg_coe.agents.mfg_coe_outcome_framer_agent import MfgCoEOutcomeFramerAgent
from customers.mfg_coe.agents.mfg_coe_outcome_validator_agent import MfgCoEOutcomeValidatorAgent
from customers.mfg_coe.agents.mfg_coe_ux_designer_agent import MfgCoEUXDesignerAgent
from customers.mfg_coe.agents.mfg_coe_content_strategist_agent import MfgCoEContentStrategistAgent
from customers.mfg_coe.agents.mfg_coe_data_analyst_agent import MfgCoEDataAnalystAgent
from customers.mfg_coe.agents.mfg_coe_security_reviewer_agent import MfgCoESecurityReviewerAgent
from customers.mfg_coe.agents.mfg_coe_qa_engineer_agent import MfgCoEQAEngineerAgent
from customers.mfg_coe.agents.mfg_coe_devops_pm_agent import MfgCoEDevOpsPMAgent
from customers.mfg_coe.agents.mfg_coe_d365_dev_agent import MfgCoED365DevAgent
from customers.mfg_coe.agents.mfg_coe_pp_dev_agent import MfgCoEPPDevAgent
from customers.mfg_coe.agents.mfg_coe_ai_specialist_agent import MfgCoEAISpecialistAgent
from customers.mfg_coe.agents.mfg_coe_analytics_dev_agent import MfgCoEAnalyticsDevAgent
from customers.mfg_coe.agents.context_card_loader import load_all_context_cards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO = os.environ.get("COE_REPO", "billwhalenmsft/CommunityRAPP-BillWhalen")
COE_LABEL = "mfg-coe"

# Routing keywords to persona agents
ROUTING_MAP = {
    "sme": {
        "keywords": ["sop", "process", "use case", "business process", "workflow", "standard operating", "procedure", "crm process", "document"],
        "agent_key": "sme",
        "description": "SME Agent (SOPs, processes, use cases)"
    },
    "developer": {
        "keywords": ["code", "agent", "scaffold", "build", "implement", "python", "function", "playwright", "d365 config"],
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
        "keywords": ["customer", "persona", "simulate", "navico", "otis", "zurn", "vermeer", "carrier"],
        "agent_key": "customer_persona",
        "description": "Customer Persona Agent (testing, simulation)"
    },
    "ux_designer": {
        "keywords": ["ux", "wireframe", "user story", "user experience", "ui design", "screen", "layout", "information architecture", "conversation flow", "card design"],
        "agent_key": "ux_designer",
        "description": "UX Designer (wireframes, user stories, IA, conversation UX)"
    },
    "content_strategist": {
        "keywords": ["sop template", "write", "content", "tone", "jargon", "executive summary", "ssm", "rfp", "documentation", "forum post", "editorial"],
        "agent_key": "content_strategist",
        "description": "Content Strategist (SOPs, outcome summaries, SSP responses, editorial)"
    },
    "data_analyst": {
        "keywords": ["trend", "pattern", "metric", "kpi", "report", "dashboard", "insight", "analytics", "roi", "velocity", "coverage"],
        "agent_key": "data_analyst",
        "description": "Data Analyst (trends, patterns, KPI tracking, dashboard data)"
    },
    "security_reviewer": {
        "keywords": ["security", "secret", "credential", "auth", "permission", "vulnerability", "hardcoded", "cors", "injection", "review code"],
        "agent_key": "security_reviewer",
        "description": "Security Reviewer (code security, auth flows, secrets scanning)"
    },
    "qa_engineer": {
        "keywords": ["test", "test case", "regression", "edge case", "acceptance", "coverage", "qa", "verify", "playwright"],
        "agent_key": "qa_engineer",
        "description": "QA Engineer (test cases, test plans, regression, acceptance verification)"
    },
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
    Routes requests to 13 persona agents, manages the GitHub feedback loop,
    and coordinates autonomous CoE operations.

    Agent Team (13 agents):
      Core Pipeline:
        - OutcomeFramer    : frames + scores outcomes; hard-blocks if LOW confidence
        - OutcomeValidator : validates outcomes are delivered after work completes
        - SME              : SOPs, business processes, use case definitions
        - Developer        : code generation, D365 configs, RAPP artifacts (6 skill areas)
        - Architect        : solution design, Microsoft stack patterns
      Support:
        - PM               : sprint planning, backlog, status digest
        - Intake           : idea capture, solution logging, needs-bill alerts
        - CustomerPersona  : customer simulation for testing
      Quality & Craft:
        - UXDesigner       : wireframes, user stories, conversation UX, card design
        - ContentStrategist: SOPs, outcome summaries, SSP responses, editorial review
        - DataAnalyst      : trend detection, KPI tracking, ROI signals, dashboard data
        - SecurityReviewer : secrets scanning, auth review, pre-deploy checklists
        - QAEngineer       : test case generation, test plans, regression checklists
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
        # DevOps specialist team
        self.devops_pm = MfgCoEDevOpsPMAgent()
        self.d365_dev = MfgCoED365DevAgent()
        self.pp_dev = MfgCoEPPDevAgent()
        self.ai_specialist = MfgCoEAISpecialistAgent()
        self.analytics_dev = MfgCoEAnalyticsDevAgent()
        self.customer_persona = MfgCoECustomerPersonaAgent()
        self.outcome_framer = MfgCoEOutcomeFramerAgent()
        self.outcome_validator = MfgCoEOutcomeValidatorAgent()
        self.ux_designer = MfgCoEUXDesignerAgent()
        self.content_strategist = MfgCoEContentStrategistAgent()
        self.data_analyst = MfgCoEDataAnalystAgent()
        self.security_reviewer = MfgCoESecurityReviewerAgent()
        self.qa_engineer = MfgCoEQAEngineerAgent()

        self.agents = {
            "intake": self.intake,
            "pm": self.pm,
            "sme": self.sme,
            "developer": self.developer,
            "architect": self.architect,
            "customer_persona": self.customer_persona,
            "outcome_framer": self.outcome_framer,
            "outcome_validator": self.outcome_validator,
            "ux_designer": self.ux_designer,
            "content_strategist": self.content_strategist,
            "data_analyst": self.data_analyst,
            "security_reviewer": self.security_reviewer,
            "qa_engineer": self.qa_engineer,
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

        # Get issue details including comments for full context
        result = _gh([
            "issue", "view", str(issue_number), "--repo", REPO,
            "--json", "number,title,body,labels,comments"
        ])

        if "error" in result:
            return json.dumps({"error": result["error"]})

        title = result.get("title", "")
        body = result.get("body", "")
        labels = [l["name"] for l in result.get("labels", [])]

        # Build comment context from Bill's replies (exclude bot comments)
        bill_comments = [
            c["body"] for c in result.get("comments", [])
            if c.get("author", {}).get("login", "") not in ("github-actions", "")
        ]
        comment_context = ""
        if bill_comments:
            comment_context = "\n\n---\n**Bill's feedback (from issue comments):**\n" + \
                "\n".join(f"- {c[:500]}" for c in bill_comments)

        steps_taken = []

        # Step 0: Outcome Framer — define business problem + KPI before any build work
        # Skip if outcome already defined
        if "outcome-defined" not in labels:
            # Infer process area from title/labels
            process_area = "default"
            area_map = {
                "warranty": "warranty", "rma": "returns_rma", "return": "returns_rma",
                "case": "case_management", "triage": "case_management",
                "field service": "field_service", "distributor": "dealer_management",
                "dealer": "dealer_management", "crm": "crm", "lead": "crm",
                "order": "order_management",
            }
            title_lower = title.lower()
            for keyword, area in area_map.items():
                if keyword in title_lower:
                    process_area = area
                    break

            # Infer customer
            customer = "Discrete Manufacturing customer"
            for c in ["Navico", "Otis", "Zurn", "Vermeer", "Carrier", "AES"]:
                if c.lower() in title_lower or c.lower() in (body or "").lower():
                    customer = c
                    break

            framer_result_raw = self.outcome_framer.perform(
                action="frame_outcome",
                issue_number=issue_number,
                issue_title=title,
                issue_body=body + comment_context,  # Include Bill's comment answers
                process_area=process_area,
                customer=customer,
            )
            framer_result = json.loads(framer_result_raw)
            steps_taken.append({"step": "outcome_framing", "result": framer_result})

            # Post outcome definition (or blocking request) as issue comment
            if framer_result.get("comment_body"):
                _gh(["issue", "comment", str(issue_number), "--repo", REPO,
                     "--body", framer_result["comment_body"]])

            # HARD BLOCK: if outcome can't be determined, halt the pipeline
            if framer_result.get("pipeline_blocked"):
                _gh(["issue", "edit", str(issue_number), "--repo", REPO,
                     "--add-label", "needs-bill"])
                return json.dumps({
                    "issue_number": issue_number,
                    "title": title,
                    "pipeline_steps": steps_taken,
                    "current_stage": "raw-idea",
                    "status": "blocked_needs_outcome",
                    "summary": framer_result.get("summary", f"Pipeline blocked for #{issue_number} — outcome definition required from Bill."),
                    "next_steps": framer_result.get("next_steps", []),
                }, indent=2)

            self.pm.perform(action="advance_pipeline_stage", issue_number=issue_number,
                            target_stage="outcome-defined")

        # Step 1: SME defines use case (if not already past this stage)
        if "raw-idea" in labels or ("use-case" not in labels and "tech-solution" not in labels):
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

        # Step 2b: Developer recommends required skill areas based on solution design
        skill_result_raw = self.developer.perform(
            action="recommend_skill",
            use_case=title,
            context=body[:300],
        )
        skill_result = json.loads(skill_result_raw)
        required_skills = skill_result.get("required_skills", [])
        skill_comment = skill_result.get("comment", "")
        steps_taken.append({"step": "skills_identified", "result": skill_result})

        # Step 3: Log architecture + skill requirements to GitHub
        skills_display = ", ".join(required_skills) if required_skills else "dynamics_crm, copilot_studio"
        summary = (
            f"## 🏗️ Architecture Design Complete\n\n"
            f"**Recommended Patterns:** {', '.join([p.get('pattern_id','?') for p in arch_data.get('recommended_patterns',[])])}\n\n"
            f"**Components:** {', '.join(arch_data.get('suggested_components',[]))}\n\n"
            f"{skill_comment}\n\n"
            f"**Required Skills:** `{skills_display}`\n\n"
            f"**Next:** Developer agent to scaffold implementation.\n\n"
            f"---\n*Pipeline run by CoE Orchestrator at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
        )
        _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", summary])
        self.pm.perform(action="assign_work", issue_number=issue_number, persona="developer",
                        context="Architecture complete — ready for Developer agent to scaffold.")

        # Step 4: EXECUTE — actually build the artifact
        build_result = self._execute_build(
            issue_number=issue_number,
            title=title,
            body=body,
            labels=labels,
            required_skills=required_skills,
            arch_data=arch_data,
        )
        steps_taken.append({"step": "artifact_built", "result": build_result})

        artifact_path = build_result.get("artifact_path", "")
        artifact_preview = build_result.get("content_preview", "")[:400]
        committed = build_result.get("committed", False)
        agent_used = build_result.get("agent_used", "developer")
        build_error = build_result.get("error", "")

        if build_error:
            # Build failed — escalate to Bill with error details
            error_comment = (
                f"## ⚠️ Build Step Failed — Needs Bill\n\n"
                f"The {agent_used} agent encountered an error while building the artifact:\n\n"
                f"```\n{build_error}\n```\n\n"
                f"**Please review and provide direction.** The architecture design is complete (see above).\n\n"
                f"_Agent: {agent_used} | Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
            )
            _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", error_comment])
            _gh(["issue", "edit", str(issue_number), "--repo", REPO, "--add-label", "needs-bill"])
            return json.dumps({
                "issue_number": issue_number,
                "title": title,
                "pipeline_steps": steps_taken,
                "current_stage": "tech-solution",
                "status": "needs_bill",
                "question": f"Build step failed: {build_error}",
            }, indent=2)

        # Step 5: Post artifact for Bill's review
        commit_note = f"✅ Committed to `{artifact_path}`" if committed else f"📄 Artifact at `{artifact_path}` (commit pending)"
        review_comment = (
            f"## 🏗️ Artifact Built — Needs Your Review\n\n"
            f"The **{agent_used}** agent has produced an artifact for this issue.\n\n"
            f"**{commit_note}**\n\n"
            f"**Preview:**\n```\n{artifact_preview}\n```\n\n"
            f"**To approve and close:** Comment `/approve` or `/push`\n"
            f"**To request changes:** Comment with your feedback and the agent will iterate\n\n"
            f"---\n_Agent: {agent_used} | Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
        )
        _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", review_comment])
        _gh(["issue", "edit", str(issue_number), "--repo", REPO, "--add-label", "needs-bill"])

        return json.dumps({
            "issue_number": issue_number,
            "title": title,
            "pipeline_steps": steps_taken,
            "current_stage": "tech-solution",
            "assigned_to": agent_used,
            "artifact_path": artifact_path,
            "committed": committed,
            "status": "needs_bill_review",
            "question": f"Artifact built at `{artifact_path}`. Please review and comment `/approve` to close, or provide feedback to iterate.",
        }, indent=2)

    def _execute_build(self, issue_number: int, title: str, body: str,
                       labels: list, required_skills: list, arch_data: dict) -> dict:
        """
        Step 4: Build artifacts via the DevOps PM specialist team.
        DevOps PM scopes the issue → identifies disciplines → orchestrator calls
        each specialist in dependency order, passing prior artifacts as context.
        Knowledge tasks (SME) run first if detected, then code specialists.
        """
        # Map specialist keys → agent instances
        specialist_agents = {
            "python_dev": self.developer,
            "d365_dev": self.d365_dev,
            "pp_dev": self.pp_dev,
            "ai_specialist": self.ai_specialist,
            "analytics_dev": self.analytics_dev,
        }

        try:
            # ── DevOps PM: scope the issue ────────────────────────────────
            scope_raw = self.devops_pm.perform(
                action="scope_issue",
                issue_title=title,
                issue_body=body,
                issue_number=issue_number,
            )
            scope = json.loads(scope_raw)
            disciplines = scope.get("disciplines", [])
            deliverables = scope.get("deliverables", [])
            project_plan_path = scope.get("project_plan_path", "")
            logger.info("DevOps PM scoped #%d: %s", issue_number, disciplines)

            # Check if this is a knowledge-only task (SME handles it)
            title_lower = title.lower()
            knowledge_keywords = ["sop", "gap", "use case", "top 10", "guide", "document",
                                   "analysis", "context card", "knowledge", "survey", "research"]
            is_knowledge_only = (
                any(kw in title_lower for kw in knowledge_keywords)
                and not disciplines  # no specialist disciplines detected
            )
            if is_knowledge_only:
                disciplines = []  # fall through to SME path below

            all_artifacts = []
            prior_artifacts: dict = {}
            all_abs_paths = []

            if project_plan_path:
                # Include project plan path for commit
                abs_plan = os.path.normpath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", project_plan_path)
                )
                if os.path.exists(abs_plan):
                    all_abs_paths.append(abs_plan)
                    all_artifacts.append(project_plan_path)

            if disciplines:
                # ── Call each specialist in dependency order ───────────────
                for deliverable in deliverables:
                    disc = deliverable["discipline"]
                    agent = specialist_agents.get(disc)
                    if not agent:
                        logger.warning("No agent for discipline %s — skipping", disc)
                        continue

                    logger.info("Calling %s specialist for deliverable %s",
                                disc, deliverable["deliverable_id"])
                    result_raw = agent.perform(
                        action="execute_issue",
                        issue_title=title,
                        issue_body=body,
                        prior_artifacts=prior_artifacts,
                    )
                    result = json.loads(result_raw)

                    if "error" in result:
                        logger.warning("Specialist %s returned error: %s", disc, result["error"])
                        continue

                    abs_path = result.get("abs_path", "")
                    rel_path = result.get("output_path", "")
                    if abs_path and os.path.exists(abs_path):
                        all_abs_paths.append(abs_path)
                    if rel_path:
                        all_artifacts.append(rel_path)

                    # Pass this specialist's output to subsequent specialists
                    prior_artifacts[disc] = result.get("content_preview", "")

            else:
                # Knowledge task — SME handles it
                result_raw = self.sme.perform(
                    action="execute_issue",
                    issue_title=title,
                    issue_body=body,
                )
                result = json.loads(result_raw)
                if "error" not in result:
                    abs_path = result.get("abs_path", "")
                    rel_path = result.get("output_path", "")
                    if abs_path and os.path.exists(abs_path):
                        all_abs_paths.append(abs_path)
                    if rel_path:
                        all_artifacts.append(rel_path)
                    prior_artifacts["sme"] = result.get("content_preview", "")

            if not all_artifacts:
                return {"error": "No specialists produced artifacts", "disciplines": disciplines}

            # ── Git commit all artifacts ──────────────────────────────────
            committed = False
            repo_root = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
            try:
                subprocess.run(["git", "config", "user.email", "agents@bots-in-blazers.fun"],
                               cwd=repo_root, capture_output=True)
                subprocess.run(["git", "config", "user.name", "CoE Agent Team"],
                               cwd=repo_root, capture_output=True)
                for abs_path in all_abs_paths:
                    subprocess.run(["git", "add", abs_path], cwd=repo_root, capture_output=True)

                disc_list = ", ".join(disciplines) if disciplines else "sme"
                commit_result = subprocess.run(
                    ["git", "commit", "-m",
                     f"feat: CoE DevOps team artifacts for #{issue_number} — {title[:55]}\n\n"
                     f"Disciplines: {disc_list}\n"
                     f"Artifacts: {', '.join(all_artifacts[:3])}\n\n"
                     f"Co-authored-by: CoE Agent Team <agents@bots-in-blazers.fun>\n"
                     f"Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"],
                    cwd=repo_root, capture_output=True, text=True,
                )
                if commit_result.returncode == 0:
                    push_result = subprocess.run(["git", "push"],
                                                 cwd=repo_root, capture_output=True, text=True)
                    committed = push_result.returncode == 0
                    logger.info("Git push: %s", push_result.stdout + push_result.stderr)
                else:
                    logger.warning("Git commit failed: %s", commit_result.stderr)
            except Exception as e:
                logger.warning("Git operations failed: %s", e)

            primary_path = all_artifacts[0] if all_artifacts else ""
            preview = list(prior_artifacts.values())[0][:300] if prior_artifacts else ""

            return {
                "artifact_path": primary_path,
                "all_artifacts": all_artifacts,
                "disciplines": disciplines,
                "project_plan_path": project_plan_path,
                "content_preview": preview,
                "agent_used": "devops_team",
                "task_type": "specialist_build",
                "committed": committed,
            }

        except Exception as e:
            logger.error("_execute_build failed: %s", e)
            return {"error": str(e), "agent_used": "devops_pm"}

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
