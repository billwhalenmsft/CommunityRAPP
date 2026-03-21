"""
Agent: SMA4 Handoff Coordinator Agent
Purpose: Level 1 agent — tracks cross-role handoffs between Sales Reps,
         Coordinators, Marketing, and Managers. Ensures nothing drops
         when work transitions between roles.

Use Case: Persona Workbench / Cockpit Agent (SMA4)
Module: D365 Sales — Prospect to Quote

Handoff Types:
  1. MARKETING_TO_SALES   — MQL qualified, assign to sales rep
  2. SALES_TO_COORDINATOR — Deal ready for quote prep / order entry
  3. COORDINATOR_TO_SALES — Quote assembled, return for customer delivery
  4. SALES_TO_MANAGER     — Escalation or approval request
  5. MANAGER_TO_SALES     — Approval completed, return to rep

Data Sources:
  CRM:  tasks (handoff tasks), activitypointers, opportunity history
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Handoff types ───────────────────────────────────────────────
HANDOFF_TYPES = {
    "MARKETING_TO_SALES":   {"from_role": "marketing",    "to_role": "sales_rep",
                             "description": "MQL qualified — assign to rep for follow-up"},
    "SALES_TO_COORDINATOR": {"from_role": "sales_rep",    "to_role": "coordinator",
                             "description": "Deal ready for quote prep / order entry"},
    "COORDINATOR_TO_SALES": {"from_role": "coordinator",  "to_role": "sales_rep",
                             "description": "Quote assembled — return for customer delivery"},
    "SALES_TO_MANAGER":     {"from_role": "sales_rep",    "to_role": "manager",
                             "description": "Escalation or approval request"},
    "MANAGER_TO_SALES":     {"from_role": "manager",      "to_role": "sales_rep",
                             "description": "Approval complete — return to rep"}
}

HANDOFF_SLA_HOURS = {
    "MARKETING_TO_SALES": 24,
    "SALES_TO_COORDINATOR": 8,
    "COORDINATOR_TO_SALES": 24,
    "SALES_TO_MANAGER": 4,
    "MANAGER_TO_SALES": 8
}

PERSONA_NAMES = {
    "sales_rep": "Sarah Chen",
    "coordinator": "Mike Torres",
    "marketing": "Priya Patel",
    "manager": "James Harrison"
}

# ── Stubbed handoff records ─────────────────────────────────────
DEMO_HANDOFFS = [
    {
        "handoff_id": "hnd-001",
        "type": "SALES_TO_COORDINATOR",
        "opportunity": "Contoso — ERP Modernization",
        "opportunity_id": "opp-001",
        "from_person": "Sarah Chen", "from_role": "sales_rep",
        "to_person": "Mike Torres", "to_role": "coordinator",
        "initiated_at": "2026-03-15T10:00:00",
        "accepted_at": "2026-03-15T11:30:00",
        "completed_at": None,
        "status": "in_progress",
        "context": "Customer expects proposal by 3/21. Pricing approved, need quote assembly.",
        "checklist": [
            {"item": "Assemble line items from pricing approval", "done": True},
            {"item": "Add standard T&C", "done": True},
            {"item": "Run credit check", "done": False},
            {"item": "Generate PDF and return to Sarah", "done": False}
        ]
    },
    {
        "handoff_id": "hnd-002",
        "type": "MARKETING_TO_SALES",
        "opportunity": "Northwind — Data Platform",
        "opportunity_id": "opp-003",
        "from_person": "Priya Patel", "from_role": "marketing",
        "to_person": "Sarah Chen", "to_role": "sales_rep",
        "initiated_at": "2026-03-14T14:00:00",
        "accepted_at": "2026-03-14T16:00:00",
        "completed_at": "2026-03-15T09:00:00",
        "status": "completed",
        "context": "MQL score 85. Attended webinar + downloaded whitepaper. Budget: ~$100K.",
        "checklist": [
            {"item": "Review MQL scoring and lead source", "done": True},
            {"item": "Schedule discovery call", "done": True},
            {"item": "Create opportunity record", "done": True}
        ]
    },
    {
        "handoff_id": "hnd-003",
        "type": "SALES_TO_MANAGER",
        "opportunity": "Fabrikam — CRM Rollout",
        "opportunity_id": "opp-002",
        "from_person": "Sarah Chen", "from_role": "sales_rep",
        "to_person": "James Harrison", "to_role": "manager",
        "initiated_at": "2026-03-17T09:00:00",
        "accepted_at": None,
        "completed_at": None,
        "status": "pending_acceptance",
        "context": "18% discount requested. Exceeds 15% threshold. Competitive situation.",
        "checklist": [
            {"item": "Review discount justification", "done": False},
            {"item": "Check competitive intel", "done": False},
            {"item": "Approve or counter", "done": False},
            {"item": "Return decision to Sarah", "done": False}
        ]
    },
    {
        "handoff_id": "hnd-004",
        "type": "COORDINATOR_TO_SALES",
        "opportunity": "Adventure Works — Field Service",
        "opportunity_id": "opp-004",
        "from_person": "Mike Torres", "from_role": "coordinator",
        "to_person": "Lisa Park", "to_role": "sales_rep",
        "initiated_at": "2026-03-13T16:00:00",
        "accepted_at": "2026-03-13T17:00:00",
        "completed_at": None,
        "status": "blocked",
        "context": "Quote ready but account on CREDIT HOLD. Cannot send until resolved.",
        "checklist": [
            {"item": "Quote assembled", "done": True},
            {"item": "Legal T&C attached", "done": True},
            {"item": "Credit check passed", "done": False},
            {"item": "Deliver to customer", "done": False}
        ],
        "blocker": "Account on credit hold — balance $410K exceeds $400K limit"
    }
]


class SMA4HandoffCoordinatorAgent(BasicAgent):
    """
    Handoff Coordinator Agent — tracks work transitions between roles.
    Prevents dropped tasks during handoffs in the Prospect-to-Quote pipeline.
    """

    def __init__(self):
        self.name = "HandoffCoordinatorAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Tracks cross-role handoffs in the Prospect-to-Quote pipeline. "
                "Monitors Marketing→Sales, Sales→Coordinator, Coordinator→Sales, "
                "Sales→Manager transitions. Includes checklists, SLAs, and "
                "blocker detection to prevent dropped tasks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_my_handoffs",
                            "get_handoff_detail",
                            "initiate_handoff",
                            "accept_handoff",
                            "complete_handoff",
                            "get_blocked_handoffs",
                            "get_handoff_sla_status",
                            "get_handoff_types"
                        ],
                        "description": "Handoff coordination action"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["sales_rep", "coordinator", "marketing", "manager"],
                        "description": "Caller's persona"
                    },
                    "handoff_id": {
                        "type": "string",
                        "description": "Specific handoff to act on"
                    },
                    "handoff_type": {
                        "type": "string",
                        "enum": list(HANDOFF_TYPES.keys()),
                        "description": "Type of handoff to initiate"
                    },
                    "opportunity_id": {
                        "type": "string",
                        "description": "Opportunity this handoff relates to"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context notes for the recipient"
                    }
                },
                "required": ["action", "persona"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ── Helpers ─────────────────────────────────────────────────

    def _handoffs_for_persona(self, persona: str, direction: str = "both") -> List[Dict]:
        name = PERSONA_NAMES.get(persona, "")
        results = []
        for h in DEMO_HANDOFFS:
            is_from = h["from_person"] == name
            is_to = h["to_person"] == name
            if direction == "incoming" and is_to:
                results.append(h)
            elif direction == "outgoing" and is_from:
                results.append(h)
            elif direction == "both" and (is_from or is_to):
                results.append(h)
        return results

    def _calculate_sla(self, handoff: Dict) -> Dict:
        sla_hours = HANDOFF_SLA_HOURS.get(handoff["type"], 24)
        initiated = datetime.fromisoformat(handoff["initiated_at"])
        now = datetime.now()
        elapsed_hours = (now - initiated).total_seconds() / 3600

        if handoff["status"] == "completed" and handoff.get("completed_at"):
            completed = datetime.fromisoformat(handoff["completed_at"])
            elapsed_hours = (completed - initiated).total_seconds() / 3600

        return {
            "sla_hours": sla_hours,
            "elapsed_hours": round(elapsed_hours, 1),
            "status": "breached" if elapsed_hours > sla_hours and handoff["status"] != "completed" else "ok"
        }

    # ── Handlers ───────────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_my_handoffs")
        persona = kwargs.get("persona", "sales_rep")

        if action == "get_my_handoffs":
            return self._handle_my_handoffs(persona)
        elif action == "get_handoff_detail":
            return self._handle_detail(kwargs.get("handoff_id"))
        elif action == "initiate_handoff":
            return self._handle_initiate(**kwargs)
        elif action == "accept_handoff":
            return self._handle_accept(kwargs.get("handoff_id"))
        elif action == "complete_handoff":
            return self._handle_complete(kwargs.get("handoff_id"))
        elif action == "get_blocked_handoffs":
            return self._handle_blocked()
        elif action == "get_handoff_sla_status":
            return self._handle_sla_status()
        elif action == "get_handoff_types":
            return json.dumps({"handoff_types": HANDOFF_TYPES,
                               "sla_hours": HANDOFF_SLA_HOURS}, indent=2)
        return json.dumps({"error": f"Unknown action: {action}"})

    def _handle_my_handoffs(self, persona: str) -> str:
        incoming = self._handoffs_for_persona(persona, "incoming")
        outgoing = self._handoffs_for_persona(persona, "outgoing")
        pending = [h for h in incoming if h["status"] in ("pending_acceptance", "in_progress")]

        return json.dumps({
            "persona": persona,
            "incoming": [{"id": h["handoff_id"], "type": h["type"],
                          "deal": h["opportunity"], "status": h["status"],
                          "from": h["from_person"]}
                         for h in incoming if h["status"] != "completed"],
            "outgoing": [{"id": h["handoff_id"], "type": h["type"],
                          "deal": h["opportunity"], "status": h["status"],
                          "to": h["to_person"]}
                         for h in outgoing if h["status"] != "completed"],
            "needs_action": len(pending),
            "generated_at": datetime.now().isoformat()
        }, indent=2)

    def _handle_detail(self, handoff_id: str = None) -> str:
        if not handoff_id:
            return json.dumps({"error": "handoff_id required"})
        match = next((h for h in DEMO_HANDOFFS if h["handoff_id"] == handoff_id), None)
        if not match:
            return json.dumps({"error": f"Handoff {handoff_id} not found"})
        sla = self._calculate_sla(match)
        checklist_progress = sum(1 for c in match.get("checklist", []) if c["done"])
        total_items = len(match.get("checklist", []))
        return json.dumps({
            "handoff": match,
            "sla": sla,
            "checklist_progress": f"{checklist_progress}/{total_items}",
            "blocker": match.get("blocker")
        }, indent=2)

    def _handle_initiate(self, **kwargs) -> str:
        handoff_type = kwargs.get("handoff_type")
        opp_id = kwargs.get("opportunity_id", "opp-new")
        context = kwargs.get("context", "")
        persona = kwargs.get("persona", "sales_rep")

        if not handoff_type or handoff_type not in HANDOFF_TYPES:
            return json.dumps({"error": f"Invalid handoff_type: {handoff_type}"})

        ht = HANDOFF_TYPES[handoff_type]
        new_handoff = {
            "handoff_id": f"hnd-{len(DEMO_HANDOFFS) + 1:03d}",
            "type": handoff_type,
            "opportunity_id": opp_id,
            "from_person": PERSONA_NAMES.get(ht["from_role"], persona),
            "from_role": ht["from_role"],
            "to_person": PERSONA_NAMES.get(ht["to_role"], "TBD"),
            "to_role": ht["to_role"],
            "initiated_at": datetime.now().isoformat(),
            "status": "pending_acceptance",
            "context": context,
            "sla_hours": HANDOFF_SLA_HOURS.get(handoff_type, 24)
        }
        DEMO_HANDOFFS.append(new_handoff)
        return json.dumps({
            "result": "handoff_initiated",
            "handoff": new_handoff,
            "next_step": f"Waiting for {new_handoff['to_person']} to accept"
        }, indent=2)

    def _handle_accept(self, handoff_id: str = None) -> str:
        if not handoff_id:
            return json.dumps({"error": "handoff_id required"})
        match = next((h for h in DEMO_HANDOFFS if h["handoff_id"] == handoff_id), None)
        if not match:
            return json.dumps({"error": f"Handoff {handoff_id} not found"})
        match["status"] = "in_progress"
        match["accepted_at"] = datetime.now().isoformat()
        return json.dumps({"result": "accepted", "handoff": match}, indent=2)

    def _handle_complete(self, handoff_id: str = None) -> str:
        if not handoff_id:
            return json.dumps({"error": "handoff_id required"})
        match = next((h for h in DEMO_HANDOFFS if h["handoff_id"] == handoff_id), None)
        if not match:
            return json.dumps({"error": f"Handoff {handoff_id} not found"})
        match["status"] = "completed"
        match["completed_at"] = datetime.now().isoformat()
        return json.dumps({"result": "completed", "handoff": match}, indent=2)

    def _handle_blocked(self) -> str:
        blocked = [h for h in DEMO_HANDOFFS if h["status"] == "blocked"]
        return json.dumps({
            "blocked_count": len(blocked),
            "blocked_handoffs": [{
                "id": h["handoff_id"], "deal": h["opportunity"],
                "type": h["type"], "blocker": h.get("blocker", "Unknown")
            } for h in blocked]
        }, indent=2)

    def _handle_sla_status(self) -> str:
        active = [h for h in DEMO_HANDOFFS if h["status"] not in ("completed",)]
        results = []
        for h in active:
            sla = self._calculate_sla(h)
            results.append({
                "id": h["handoff_id"], "deal": h["opportunity"],
                "type": h["type"], **sla
            })
        breached = [r for r in results if r["status"] == "breached"]
        return json.dumps({
            "total_active": len(results),
            "sla_breached": len(breached),
            "handoffs": results
        }, indent=2)
