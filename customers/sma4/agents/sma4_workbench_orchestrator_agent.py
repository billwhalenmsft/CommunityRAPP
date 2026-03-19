"""
Agent: SMA4 Workbench Orchestrator Agent
Purpose: Level 0 master orchestrator for the Persona Workbench / Cockpit.
         Identifies the caller's persona (Sales Rep, Coordinator, Marketing,
         Manager) and coordinates all L1 agents to assemble a unified view.

Use Case: Persona Workbench / Cockpit Agent (SMA4)
Module: D365 Sales — Prospect to Quote
Value: Low   |   Complexity: Low

Architecture:
  L0  Workbench Orchestrator   ← YOU ARE HERE
   ├── L1  Workflow State Agent
   ├── L1  Task Queue Agent
   ├── L1  Exception Monitor Agent
   ├── L1  Approval Router Agent
   └── L1  Handoff Coordinator Agent

Design Decisions:
  - Personas: Sales Rep, Sales Coordinator, Marketing, Sales Manager
  - BPF Stages: Qualify → Develop → Propose → Close (D365 Sales OOB)
  - Exceptions: Discount >15%, stuck >14d, missing fields, credit hold, approval >48h
  - Approvals: Matrix-based routing + delegation + auto-escalation
  - Handoffs: Task-based with checklists and SLA tracking
  - ERP: Stubbed D365 F&O endpoints (pricing, credit, orders)
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from agents.basic_agent import BasicAgent

# Import all L1 agents
from customers.sma4.agents.sma4_workflow_state_agent import SMA4WorkflowStateAgent
from customers.sma4.agents.sma4_task_queue_agent import SMA4TaskQueueAgent
from customers.sma4.agents.sma4_exception_monitor_agent import SMA4ExceptionMonitorAgent
from customers.sma4.agents.sma4_approval_router_agent import SMA4ApprovalRouterAgent
from customers.sma4.agents.sma4_handoff_coordinator_agent import SMA4HandoffCoordinatorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Persona definitions ─────────────────────────────────────────
PERSONAS = {
    "sales_rep": {
        "name": "Sarah Chen",
        "title": "Senior Sales Representative",
        "team": "Enterprise West",
        "primary_view": "My deals, my tasks, my handoffs to coordinator",
        "agents": ["workflow_state", "task_queue", "exception_monitor", "handoff_coordinator"]
    },
    "coordinator": {
        "name": "Mike Torres",
        "title": "Sales Coordinator",
        "team": "Deal Desk",
        "primary_view": "Quote prep queue, order entry, handoffs from reps",
        "agents": ["workflow_state", "task_queue", "handoff_coordinator", "approval_router"]
    },
    "marketing": {
        "name": "Priya Patel",
        "title": "Marketing Manager",
        "team": "Demand Gen",
        "primary_view": "Campaign pipeline, MQL→SQL conversions, handoffs to sales",
        "agents": ["workflow_state", "task_queue", "handoff_coordinator"]
    },
    "manager": {
        "name": "James Harrison",
        "title": "VP Sales — Enterprise",
        "team": "Enterprise West",
        "primary_view": "Approval queue, exceptions dashboard, team pipeline",
        "agents": ["workflow_state", "task_queue", "exception_monitor",
                   "approval_router", "handoff_coordinator"]
    }
}


class SMA4WorkbenchOrchestratorAgent(BasicAgent):
    """
    Level 0 Orchestrator — Persona Workbench / Cockpit.
    
    Identifies the caller's role and assembles a persona-specific
    cockpit view by coordinating all 5 L1 agents.
    """

    def __init__(self):
        self.name = "WorkbenchOrchestrator"
        self.metadata = {
            "name": self.name,
            "description": (
                "Persona Workbench Orchestrator for D365 Sales Prospect-to-Quote. "
                "Identifies the caller's role (Sales Rep, Coordinator, Marketing, Manager) "
                "and assembles a unified cockpit view with pipeline state, prioritised tasks, "
                "exceptions, pending approvals, and handoff status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_cockpit_view",
                            "get_pipeline",
                            "get_tasks",
                            "get_exceptions",
                            "get_approvals",
                            "get_handoffs",
                            "get_opportunity_detail",
                            "route_approval",
                            "initiate_handoff",
                            "health_check",
                            "get_architecture"
                        ],
                        "description": "Orchestrator action to perform"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["sales_rep", "coordinator", "marketing", "manager"],
                        "description": "Caller's persona / role"
                    },
                    "opportunity_id": {
                        "type": "string",
                        "description": "Specific deal to inspect"
                    },
                    "approval_id": {
                        "type": "string",
                        "description": "Approval to act on"
                    },
                    "handoff_type": {
                        "type": "string",
                        "description": "Type of handoff to initiate"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context or notes"
                    }
                },
                "required": ["action", "persona"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Initialize L1 agents
        self.workflow_state = SMA4WorkflowStateAgent()
        self.task_queue = SMA4TaskQueueAgent()
        self.exception_monitor = SMA4ExceptionMonitorAgent()
        self.approval_router = SMA4ApprovalRouterAgent()
        self.handoff_coordinator = SMA4HandoffCoordinatorAgent()

        self.agents = {
            "workflow_state": self.workflow_state,
            "task_queue": self.task_queue,
            "exception_monitor": self.exception_monitor,
            "approval_router": self.approval_router,
            "handoff_coordinator": self.handoff_coordinator
        }

    # ── Main dispatcher ────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_cockpit_view")
        persona = kwargs.get("persona", "sales_rep")

        handlers = {
            "get_cockpit_view": self._handle_cockpit,
            "get_pipeline": self._handle_pipeline,
            "get_tasks": self._handle_tasks,
            "get_exceptions": self._handle_exceptions,
            "get_approvals": self._handle_approvals,
            "get_handoffs": self._handle_handoffs,
            "get_opportunity_detail": self._handle_opp_detail,
            "route_approval": self._handle_route_approval,
            "initiate_handoff": self._handle_initiate_handoff,
            "health_check": self._handle_health_check,
            "get_architecture": self._handle_architecture
        }

        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        return handler(persona=persona, **kwargs)

    # ── Cockpit: the main persona-specific unified view ────────

    def _handle_cockpit(self, persona: str, **kwargs) -> str:
        """
        Assembles the full cockpit view for the given persona.
        Calls all relevant L1 agents in parallel (conceptually)
        and merges the results.
        """
        persona_config = PERSONAS.get(persona, PERSONAS["sales_rep"])

        # 1. Pipeline snapshot
        pipeline_raw = self.workflow_state.perform(action="get_my_pipeline", persona=persona)
        pipeline = json.loads(pipeline_raw)

        # 2. Task queue (top 5)
        tasks_raw = self.task_queue.perform(action="get_my_tasks", persona=persona)
        tasks = json.loads(tasks_raw)
        top_tasks = tasks.get("tasks", [])[:5]

        # 3. Exceptions (manager and sales_rep see these)
        exceptions = {}
        if "exception_monitor" in persona_config["agents"]:
            exc_raw = self.exception_monitor.perform(action="get_exception_summary")
            exceptions = json.loads(exc_raw)

        # 4. Pending approvals (manager and coordinator)
        approvals = {}
        if "approval_router" in persona_config["agents"]:
            apr_raw = self.approval_router.perform(action="get_pending_approvals", persona=persona)
            approvals = json.loads(apr_raw)

        # 5. Handoffs
        handoffs_raw = self.handoff_coordinator.perform(action="get_my_handoffs", persona=persona)
        handoffs = json.loads(handoffs_raw)

        # Assemble cockpit
        cockpit = {
            "persona": {
                "name": persona_config["name"],
                "role": persona,
                "title": persona_config["title"],
                "primary_view": persona_config["primary_view"]
            },
            "pipeline": {
                "deal_count": pipeline.get("pipeline_count", 0),
                "total_value": pipeline.get("pipeline_value", 0),
                "deals": pipeline.get("opportunities", [])
            },
            "top_tasks": top_tasks,
            "exceptions": exceptions,
            "approvals": approvals,
            "handoffs": {
                "incoming": handoffs.get("incoming", []),
                "outgoing": handoffs.get("outgoing", []),
                "needs_action": handoffs.get("needs_action", 0)
            },
            "alerts": self._generate_alerts(persona, pipeline, exceptions, approvals, handoffs),
            "generated_at": datetime.now().isoformat()
        }
        return json.dumps(cockpit, indent=2)

    def _generate_alerts(self, persona: str, pipeline: Dict, exceptions: Dict,
                         approvals: Dict, handoffs: Dict) -> List[str]:
        """Generate natural-language alerts for the persona."""
        alerts = []

        # Stalled deals
        stalled = exceptions.get("stalled_deals", 0)
        if stalled > 0:
            alerts.append(f"⚠️ {stalled} deal(s) stalled past SLA — review needed")

        # Discount breaches
        discounts = exceptions.get("discount_breaches", 0)
        if discounts > 0:
            alerts.append(f"🔴 {discounts} quote(s) exceed discount threshold")

        # Credit holds
        holds = exceptions.get("credit_holds", 0)
        if holds > 0:
            alerts.append(f"🛑 {holds} account(s) on credit hold — deal blocked")

        # Approval queue (manager)
        pending_count = approvals.get("pending_count", 0)
        if pending_count > 0 and persona == "manager":
            alerts.append(f"📋 {pending_count} approval(s) waiting for your review")

        # Handoffs needing action
        needs_action = handoffs.get("needs_action", 0)
        if needs_action > 0:
            alerts.append(f"🤝 {needs_action} handoff(s) need your attention")

        # At-risk deals
        at_risk = [d for d in pipeline.get("opportunities", [])
                   if d.get("velocity") in ("at-risk", "stalled")]
        if at_risk:
            alerts.append(f"📉 {len(at_risk)} deal(s) at risk or stalled in your pipeline")

        return alerts

    # ── Passthrough handlers ───────────────────────────────────

    def _handle_pipeline(self, persona: str, **kwargs) -> str:
        stage = kwargs.get("stage_filter")
        return self.workflow_state.perform(
            action="get_my_pipeline", persona=persona, stage_filter=stage)

    def _handle_tasks(self, persona: str, **kwargs) -> str:
        return self.task_queue.perform(action="get_my_tasks", persona=persona)

    def _handle_exceptions(self, persona: str, **kwargs) -> str:
        return self.exception_monitor.perform(action="scan_all_exceptions")

    def _handle_approvals(self, persona: str, **kwargs) -> str:
        return self.approval_router.perform(action="get_pending_approvals", persona=persona)

    def _handle_handoffs(self, persona: str, **kwargs) -> str:
        return self.handoff_coordinator.perform(action="get_my_handoffs", persona=persona)

    def _handle_opp_detail(self, persona: str, **kwargs) -> str:
        opp_id = kwargs.get("opportunity_id")
        return self.workflow_state.perform(
            action="get_opportunity_detail", persona=persona, opportunity_id=opp_id)

    def _handle_route_approval(self, persona: str, **kwargs) -> str:
        approval_id = kwargs.get("approval_id")
        action_type = kwargs.get("context", "approve")  # approve/reject/escalate
        if action_type == "reject":
            return self.approval_router.perform(
                action="reject", approval_id=approval_id, notes=kwargs.get("notes", ""))
        elif action_type == "escalate":
            return self.approval_router.perform(action="escalate", approval_id=approval_id)
        return self.approval_router.perform(action="approve", approval_id=approval_id)

    def _handle_initiate_handoff(self, persona: str, **kwargs) -> str:
        return self.handoff_coordinator.perform(
            action="initiate_handoff", persona=persona,
            handoff_type=kwargs.get("handoff_type"),
            opportunity_id=kwargs.get("opportunity_id"),
            context=kwargs.get("context", ""))

    # ── System ─────────────────────────────────────────────────

    def _handle_health_check(self, **kwargs) -> str:
        health = {}
        for name, agent in self.agents.items():
            try:
                # Quick smoke test — each agent should respond without error
                test_kwargs = {"action": list(agent.metadata["parameters"]["properties"]["action"]["enum"])[0]}
                if "persona" in agent.metadata["parameters"]["properties"]:
                    test_kwargs["persona"] = "manager"
                result = agent.perform(**test_kwargs)
                health[name] = {"status": "healthy", "response_length": len(result)}
            except Exception as e:
                health[name] = {"status": "error", "error": str(e)}

        all_healthy = all(h["status"] == "healthy" for h in health.values())
        return json.dumps({
            "system_status": "healthy" if all_healthy else "degraded",
            "agents": health,
            "checked_at": datetime.now().isoformat()
        }, indent=2)

    def _handle_architecture(self, **kwargs) -> str:
        return json.dumps({
            "name": "Persona Workbench / Cockpit Agent (SMA4)",
            "module": "D365 Sales — Prospect to Quote",
            "value": "Low", "complexity": "Low",
            "architecture": {
                "L0_orchestrator": {
                    "name": "WorkbenchOrchestrator",
                    "purpose": "Persona routing, coordination, unified view"
                },
                "L1_agents": [
                    {"name": "WorkflowStateAgent",
                     "purpose": "Pipeline state, opportunity & quote data"},
                    {"name": "TaskQueueAgent",
                     "purpose": "Prioritised tasks, SLA-aware ranking"},
                    {"name": "ExceptionMonitorAgent",
                     "purpose": "Anomaly detection across 6 exception types"},
                    {"name": "ApprovalRouterAgent",
                     "purpose": "Matrix-based routing, delegation, escalation"},
                    {"name": "HandoffCoordinatorAgent",
                     "purpose": "Cross-role transitions with checklists & SLAs"}
                ]
            },
            "personas": PERSONAS,
            "bpf_stages": ["Qualify", "Develop", "Propose", "Close"],
            "data_sources": {
                "crm": [
                    "GET /api/data/v9.2/opportunities",
                    "GET /api/data/v9.2/quotes",
                    "GET /api/data/v9.2/tasks",
                    "GET /api/data/v9.2/activitypointers",
                    "GET /api/data/v9.2/systemusers",
                    "GET /api/data/v9.2/msdyn_approvals"
                ],
                "erp_stubbed": [
                    "GET /data/SalesOrderHeaders",
                    "GET /data/InventItemPricing",
                    "GET /data/CreditManagement"
                ]
            }
        }, indent=2)
