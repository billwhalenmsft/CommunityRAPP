"""
Agent: SMA4 Task Queue Agent
Purpose: Level 1 agent — builds a prioritized, persona-specific task list.
         Answers "what should I do RIGHT NOW?" ranked by SLA urgency,
         deal value, and aging.

Use Case: Persona Workbench / Cockpit Agent (SMA4)
Module: D365 Sales — Prospect to Quote

Data Sources:
  CRM:  tasks, activitypointers (emails, phone calls, appointments),
        opportunities (for context enrichment)

Ranking Algorithm:
  Score = (SLA_urgency * 40) + (deal_value_norm * 30) + (aging_factor * 30)
  - SLA_urgency: days remaining ÷ SLA window (inverted — less time = higher)
  - deal_value_norm: deal value ÷ max deal value in queue
  - aging_factor: days since task created ÷ 30 (capped at 1.0)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Stubbed demo tasks (CRM: activitypointers + tasks) ─────────

DEMO_TASKS = [
    {
        "task_id": "task-001",
        "subject": "Prepare Contoso ERP proposal deck",
        "description": "Customer expects final proposal by EOW. Include ROI analysis.",
        "activity_type": "task",
        "owner_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "regarding_id": "opp-001", "regarding_name": "Contoso — ERP Modernization",
        "deal_value": 320000,
        "priority": "high",
        "scheduled_end": "2026-03-21",
        "created_on": "2026-03-14",
        "status": "open",
        "persona_roles": ["sales_rep"]
    },
    {
        "task_id": "task-002",
        "subject": "Follow up with Fabrikam on technical requirements",
        "description": "Stakeholder meeting notes pending. CTO wants architecture overview.",
        "activity_type": "phonecall",
        "owner_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "regarding_id": "opp-002", "regarding_name": "Fabrikam — CRM Rollout",
        "deal_value": 185000,
        "priority": "high",
        "scheduled_end": "2026-03-20",
        "created_on": "2026-03-10",
        "status": "open",
        "persona_roles": ["sales_rep"]
    },
    {
        "task_id": "task-003",
        "subject": "Generate quote for Contoso ERP v2",
        "description": "Pricing approved. Assemble line items and send to legal.",
        "activity_type": "task",
        "owner_id": "a1b2c3d4-0002-0002-0002-000000000002",
        "regarding_id": "opp-001", "regarding_name": "Contoso — ERP Modernization",
        "deal_value": 320000,
        "priority": "high",
        "scheduled_end": "2026-03-20",
        "created_on": "2026-03-15",
        "status": "open",
        "persona_roles": ["coordinator"]
    },
    {
        "task_id": "task-004",
        "subject": "Review Fabrikam discount exception",
        "description": "18% discount requested. Threshold is 15%. Needs VP approval.",
        "activity_type": "task",
        "owner_id": "a1b2c3d4-0004-0004-0004-000000000004",
        "regarding_id": "opp-002", "regarding_name": "Fabrikam — CRM Rollout",
        "deal_value": 185000,
        "priority": "urgent",
        "scheduled_end": "2026-03-19",
        "created_on": "2026-03-17",
        "status": "open",
        "persona_roles": ["manager"]
    },
    {
        "task_id": "task-005",
        "subject": "Update campaign attribution for Northwind lead",
        "description": "Lead came in via website but also attended webinar. Verify primary source.",
        "activity_type": "task",
        "owner_id": "a1b2c3d4-0003-0003-0003-000000000003",
        "regarding_id": "opp-003", "regarding_name": "Northwind — Data Platform",
        "deal_value": 95000,
        "priority": "normal",
        "scheduled_end": "2026-03-25",
        "created_on": "2026-03-16",
        "status": "open",
        "persona_roles": ["marketing"]
    },
    {
        "task_id": "task-006",
        "subject": "Send revised SOW to Adventure Works",
        "description": "Legal redlined scope. Re-send with updated terms.",
        "activity_type": "email",
        "owner_id": "a1b2c3d4-0002-0002-0002-000000000002",
        "regarding_id": "opp-004", "regarding_name": "Adventure Works — Field Service",
        "deal_value": 540000,
        "priority": "high",
        "scheduled_end": "2026-03-20",
        "created_on": "2026-03-12",
        "status": "open",
        "persona_roles": ["coordinator"]
    },
    {
        "task_id": "task-007",
        "subject": "Approve WingTip Toys final quote",
        "description": "Standard pricing, no exceptions. Ready for signature.",
        "activity_type": "task",
        "owner_id": "a1b2c3d4-0004-0004-0004-000000000004",
        "regarding_id": "opp-005", "regarding_name": "WingTip Toys — Commerce",
        "deal_value": 72000,
        "priority": "normal",
        "scheduled_end": "2026-03-22",
        "created_on": "2026-03-18",
        "status": "open",
        "persona_roles": ["manager"]
    },
    {
        "task_id": "task-008",
        "subject": "Qualify Northwind — schedule discovery call",
        "description": "Initial MQL scored 85. Set up call with account exec.",
        "activity_type": "phonecall",
        "owner_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "regarding_id": "opp-003", "regarding_name": "Northwind — Data Platform",
        "deal_value": 95000,
        "priority": "normal",
        "scheduled_end": "2026-03-24",
        "created_on": "2026-03-15",
        "status": "open",
        "persona_roles": ["sales_rep"]
    }
]

PERSONAS = {
    "sales_rep":   "a1b2c3d4-0001-0001-0001-000000000001",
    "coordinator": "a1b2c3d4-0002-0002-0002-000000000002",
    "marketing":   "a1b2c3d4-0003-0003-0003-000000000003",
    "manager":     "a1b2c3d4-0004-0004-0004-000000000004"
}


class SMA4TaskQueueAgent(BasicAgent):
    """
    Task Queue Agent — prioritised, persona-specific work list.
    """

    def __init__(self):
        self.name = "TaskQueueAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Builds a prioritized, persona-specific task list from D365 Sales "
                "activities. Ranks by SLA urgency, deal value, and task aging. "
                "Answers 'what should I work on right now?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_my_tasks",
                            "get_task_detail",
                            "get_overdue_tasks",
                            "get_urgent_tasks",
                            "get_team_workload"
                        ],
                        "description": "The task queue action to perform"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["sales_rep", "coordinator", "marketing", "manager"],
                        "description": "Caller's persona/role"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Specific task ID for detail view"
                    }
                },
                "required": ["action", "persona"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ── CRM Stub ───────────────────────────────────────────────
    def _get_tasks(self, owner_id: str = None, persona: str = None) -> List[Dict]:
        """
        STUB — In production:
        GET /api/data/v9.2/tasks?$filter=_ownerid_value eq {userId} and statecode eq 0
        GET /api/data/v9.2/activitypointers?$filter=_regardingobjectid_value eq {oppId}
        """
        tasks = [t for t in DEMO_TASKS if t["status"] == "open"]
        if persona == "manager":
            return tasks  # sees all
        if owner_id:
            tasks = [t for t in tasks if t["owner_id"] == owner_id]
        if persona:
            tasks = [t for t in tasks if persona in t.get("persona_roles", [])]
        return tasks

    # ── Priority scoring ───────────────────────────────────────
    def _score_task(self, task: Dict) -> float:
        """
        Score = (SLA_urgency × 40) + (deal_value_norm × 30) + (aging × 30)
        Higher = more urgent.
        """
        today = datetime.now().date()

        # SLA urgency (inverted: closer to due = higher score)
        due = datetime.strptime(task["scheduled_end"], "%Y-%m-%d").date()
        days_remaining = max((due - today).days, 0)
        sla_urgency = max(1.0 - (days_remaining / 14), 0)  # 14-day window

        # Deal value normalised against $600k ceiling
        deal_norm = min(task.get("deal_value", 0) / 600000, 1.0)

        # Aging factor
        created = datetime.strptime(task["created_on"], "%Y-%m-%d").date()
        age_days = (today - created).days
        aging = min(age_days / 30, 1.0)

        # Priority boost
        priority_boost = {"urgent": 0.3, "high": 0.15, "normal": 0, "low": -0.1}
        boost = priority_boost.get(task.get("priority", "normal"), 0)

        score = (sla_urgency * 0.40) + (deal_norm * 0.30) + (aging * 0.30) + boost
        return round(score, 3)

    def _rank_tasks(self, tasks: List[Dict]) -> List[Dict]:
        for t in tasks:
            t["_score"] = self._score_task(t)
        return sorted(tasks, key=lambda t: t["_score"], reverse=True)

    # ── Handlers ───────────────────────────────────────────────
    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_my_tasks")
        persona = kwargs.get("persona", "sales_rep")
        task_id = kwargs.get("task_id")

        if action == "get_my_tasks":
            return self._handle_my_tasks(persona)
        elif action == "get_task_detail":
            return self._handle_task_detail(task_id)
        elif action == "get_overdue_tasks":
            return self._handle_overdue(persona)
        elif action == "get_urgent_tasks":
            return self._handle_urgent(persona)
        elif action == "get_team_workload":
            return self._handle_team_workload()
        return json.dumps({"error": f"Unknown action: {action}"})

    def _handle_my_tasks(self, persona: str) -> str:
        owner_id = PERSONAS.get(persona)
        tasks = self._get_tasks(owner_id=owner_id, persona=persona)
        ranked = self._rank_tasks(tasks)
        return json.dumps({
            "persona": persona,
            "task_count": len(ranked),
            "tasks": [
                {
                    "rank": i + 1,
                    "id": t["task_id"],
                    "subject": t["subject"],
                    "deal": t["regarding_name"],
                    "deal_value": t["deal_value"],
                    "due": t["scheduled_end"],
                    "priority": t["priority"],
                    "type": t["activity_type"],
                    "score": t["_score"]
                } for i, t in enumerate(ranked)
            ],
            "generated_at": datetime.now().isoformat()
        }, indent=2)

    def _handle_task_detail(self, task_id: str = None) -> str:
        if not task_id:
            return json.dumps({"error": "task_id required"})
        matches = [t for t in DEMO_TASKS if t["task_id"] == task_id]
        if not matches:
            return json.dumps({"error": f"Task {task_id} not found"})
        t = matches[0]
        t["_score"] = self._score_task(t)
        return json.dumps(t, indent=2)

    def _handle_overdue(self, persona: str) -> str:
        owner_id = PERSONAS.get(persona)
        tasks = self._get_tasks(owner_id=owner_id, persona=persona)
        today = datetime.now().date()
        overdue = [t for t in tasks
                   if datetime.strptime(t["scheduled_end"], "%Y-%m-%d").date() < today]
        return json.dumps({
            "overdue_count": len(overdue),
            "overdue_tasks": [{"id": t["task_id"], "subject": t["subject"],
                               "due": t["scheduled_end"]} for t in overdue]
        }, indent=2)

    def _handle_urgent(self, persona: str) -> str:
        owner_id = PERSONAS.get(persona)
        tasks = self._get_tasks(owner_id=owner_id, persona=persona)
        urgent = [t for t in tasks if t["priority"] in ("urgent", "high")]
        ranked = self._rank_tasks(urgent)
        return json.dumps({
            "urgent_count": len(ranked),
            "urgent_tasks": [{"id": t["task_id"], "subject": t["subject"],
                              "deal": t["regarding_name"], "score": t["_score"]}
                             for t in ranked]
        }, indent=2)

    def _handle_team_workload(self) -> str:
        """Manager view: task count per persona."""
        workload = {}
        for persona, uid in PERSONAS.items():
            tasks = [t for t in DEMO_TASKS if t["owner_id"] == uid and t["status"] == "open"]
            workload[persona] = {
                "count": len(tasks),
                "high_priority": len([t for t in tasks if t["priority"] in ("urgent", "high")])
            }
        return json.dumps({"team_workload": workload}, indent=2)
