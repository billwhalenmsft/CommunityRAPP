"""
Agent: SMA4 Approval Router Agent
Purpose: Level 1 agent — manages approval workflows for discount exceptions,
         quote sign-offs, and escalations to management.

Use Case: Persona Workbench / Cockpit Agent (SMA4)
Module: D365 Sales — Prospect to Quote

Approval Matrix:
  Discount ≤ 15%  → Auto-approved
  Discount 16-25% → VP Sales approval required
  Discount > 25%  → CFO approval required
  Deal > $500K    → VP Sales approval regardless of discount
  Non-standard T&C → Legal review required

Data Sources:
  CRM:  quotes, msdyn_approvals, systemusers (delegation)
  ERP:  InventItemPricing (price validation, stubbed)

Delegation Rules:
  If approver is OOO, routes to their delegate.
  Escalation after 48h with no action.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Approval matrix ─────────────────────────────────────────────
APPROVAL_RULES = {
    "discount_auto":  {"max_pct": 15, "approver": "auto"},
    "discount_vp":    {"max_pct": 25, "approver": "vp_sales"},
    "discount_cfo":   {"max_pct": 100, "approver": "cfo"},
    "high_value_deal": {"threshold": 500000, "approver": "vp_sales"},
    "non_standard_tc": {"approver": "legal"}
}

APPROVERS = {
    "vp_sales": {
        "user_id": "a1b2c3d4-0004-0004-0004-000000000004",
        "name": "James Harrison", "title": "VP Sales — Enterprise",
        "email": "j.harrison@contoso.com",
        "delegate_id": "a1b2c3d4-0006-0006-0006-000000000006",
        "delegate_name": "Karen Wu",
        "ooo": False
    },
    "cfo": {
        "user_id": "a1b2c3d4-0007-0007-0007-000000000007",
        "name": "David Kim", "title": "CFO",
        "email": "d.kim@contoso.com",
        "delegate_id": "a1b2c3d4-0008-0008-0008-000000000008",
        "delegate_name": "Amy Chen",
        "ooo": False
    },
    "legal": {
        "user_id": "a1b2c3d4-0009-0009-0009-000000000009",
        "name": "Patricia Cross", "title": "General Counsel",
        "email": "p.cross@contoso.com",
        "delegate_id": None,
        "delegate_name": None,
        "ooo": False
    }
}

# ── Stubbed pending approvals ───────────────────────────────────
DEMO_APPROVALS = [
    {
        "approval_id": "apr-001",
        "type": "discount",
        "quote_id": "qt-002",
        "opportunity": "Fabrikam — CRM Rollout",
        "deal_value": 185000,
        "discount_pct": 18,
        "requested_by": "Sarah Chen",
        "requested_at": "2026-03-17T09:00:00",
        "approver_role": "vp_sales",
        "status": "pending",
        "resolved_at": None,
        "notes": "Competitive pressure — Fabrikam has a competing offer at 20% off"
    },
    {
        "approval_id": "apr-002",
        "type": "high_value_deal",
        "quote_id": "qt-003",
        "opportunity": "Adventure Works — Field Service",
        "deal_value": 540000,
        "discount_pct": 12,
        "requested_by": "Lisa Park",
        "requested_at": "2026-03-15T14:30:00",
        "approver_role": "vp_sales",
        "status": "pending",
        "resolved_at": None,
        "notes": "Deal exceeds $500K threshold — requires VP sign-off"
    }
]

# ── Stubbed ERP pricing ─────────────────────────────────────────
DEMO_PRICING = {
    "ERP-MOD-001": {"item": "ERP Modernization Suite", "list_price": 80000,
                    "min_price": 64000, "unit": "per user/year"},
    "CRM-ENT-001": {"item": "CRM Enterprise License", "list_price": 45000,
                    "min_price": 36000, "unit": "per user/year"},
    "FS-PRO-001":  {"item": "Field Service Pro", "list_price": 120000,
                    "min_price": 96000, "unit": "per instance/year"}
}


class SMA4ApprovalRouterAgent(BasicAgent):
    """
    Approval Router Agent — routes approvals based on rules matrix,
    handles delegation and escalation.
    """

    def __init__(self):
        self.name = "ApprovalRouterAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Manages approval workflows for the Prospect-to-Quote pipeline. "
                "Routes discount exceptions, high-value deal sign-offs, and non-standard "
                "T&C reviews based on an approval matrix. Supports delegation and "
                "auto-escalation after 48h SLA."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "determine_approval_path",
                            "get_pending_approvals",
                            "approve",
                            "reject",
                            "escalate",
                            "get_approval_matrix",
                            "validate_pricing"
                        ],
                        "description": "Approval action to perform"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["sales_rep", "coordinator", "marketing", "manager"],
                        "description": "Caller's persona"
                    },
                    "quote_id": {
                        "type": "string",
                        "description": "Quote ID to route or act on"
                    },
                    "approval_id": {
                        "type": "string",
                        "description": "Approval ID for approve/reject/escalate"
                    },
                    "discount_pct": {
                        "type": "number",
                        "description": "Proposed discount percentage"
                    },
                    "deal_value": {
                        "type": "number",
                        "description": "Total deal value"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Justification or notes"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ── Routing logic ──────────────────────────────────────────

    def _determine_route(self, discount_pct: float = 0, deal_value: float = 0,
                         non_standard_tc: bool = False) -> Dict:
        """Determine who needs to approve based on the matrix."""
        approvals_needed = []

        # Discount routing
        if discount_pct <= 15:
            approvals_needed.append({
                "reason": "discount_within_threshold",
                "approver": "auto",
                "status": "auto_approved"
            })
        elif discount_pct <= 25:
            approver = APPROVERS["vp_sales"]
            if approver["ooo"]:
                approvals_needed.append({
                    "reason": f"discount_{discount_pct}%_exceeds_15%",
                    "approver": approver["delegate_name"],
                    "approver_role": "vp_sales (delegate)",
                    "note": f"{approver['name']} is OOO — routed to delegate"
                })
            else:
                approvals_needed.append({
                    "reason": f"discount_{discount_pct}%_exceeds_15%",
                    "approver": approver["name"],
                    "approver_role": "vp_sales"
                })
        else:
            approver = APPROVERS["cfo"]
            approvals_needed.append({
                "reason": f"discount_{discount_pct}%_exceeds_25%",
                "approver": approver["name"],
                "approver_role": "cfo"
            })

        # High-value routing
        if deal_value > 500000:
            vp = APPROVERS["vp_sales"]
            approvals_needed.append({
                "reason": f"deal_value_${deal_value:,.0f}_exceeds_$500K",
                "approver": vp["delegate_name"] if vp["ooo"] else vp["name"],
                "approver_role": "vp_sales"
            })

        # Legal routing
        if non_standard_tc:
            approvals_needed.append({
                "reason": "non_standard_terms_and_conditions",
                "approver": APPROVERS["legal"]["name"],
                "approver_role": "legal"
            })

        return {
            "approvals_needed": approvals_needed,
            "total_approvals": len(approvals_needed),
            "estimated_turnaround": f"{len(approvals_needed) * 24}h"
        }

    # ── Handlers ───────────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_pending_approvals")

        if action == "determine_approval_path":
            return self._handle_determine_path(**kwargs)
        elif action == "get_pending_approvals":
            return self._handle_pending(**kwargs)
        elif action == "approve":
            return self._handle_approve(**kwargs)
        elif action == "reject":
            return self._handle_reject(**kwargs)
        elif action == "escalate":
            return self._handle_escalate(**kwargs)
        elif action == "get_approval_matrix":
            return self._handle_matrix()
        elif action == "validate_pricing":
            return self._handle_validate_pricing(**kwargs)
        return json.dumps({"error": f"Unknown action: {action}"})

    def _handle_determine_path(self, **kwargs) -> str:
        discount = kwargs.get("discount_pct", 0)
        deal_val = kwargs.get("deal_value", 0)
        route = self._determine_route(discount_pct=discount, deal_value=deal_val)
        return json.dumps(route, indent=2)

    def _handle_pending(self, **kwargs) -> str:
        persona = kwargs.get("persona", "manager")
        if persona == "manager":
            pending = [a for a in DEMO_APPROVALS if a["status"] == "pending"]
        else:
            user_name = {
                "sales_rep": "Sarah Chen", "coordinator": "Mike Torres",
                "marketing": "Priya Patel"
            }.get(persona, "")
            pending = [a for a in DEMO_APPROVALS
                       if a["status"] == "pending" and a["requested_by"] == user_name]
        now = datetime.now()
        for a in pending:
            requested = datetime.fromisoformat(a["requested_at"])
            a["hours_waiting"] = round((now - requested).total_seconds() / 3600, 1)
            a["sla_status"] = "breached" if a["hours_waiting"] > 48 else "ok"
        return json.dumps({
            "pending_count": len(pending),
            "approvals": pending
        }, indent=2)

    def _handle_approve(self, **kwargs) -> str:
        approval_id = kwargs.get("approval_id")
        if not approval_id:
            return json.dumps({"error": "approval_id required"})
        match = next((a for a in DEMO_APPROVALS if a["approval_id"] == approval_id), None)
        if not match:
            return json.dumps({"error": f"Approval {approval_id} not found"})
        match["status"] = "approved"
        match["resolved_at"] = datetime.now().isoformat()
        return json.dumps({
            "result": "approved",
            "approval": match,
            "next_step": "Quote can now be sent to customer"
        }, indent=2)

    def _handle_reject(self, **kwargs) -> str:
        approval_id = kwargs.get("approval_id")
        notes = kwargs.get("notes", "")
        if not approval_id:
            return json.dumps({"error": "approval_id required"})
        match = next((a for a in DEMO_APPROVALS if a["approval_id"] == approval_id), None)
        if not match:
            return json.dumps({"error": f"Approval {approval_id} not found"})
        match["status"] = "rejected"
        match["resolved_at"] = datetime.now().isoformat()
        match["rejection_notes"] = notes
        return json.dumps({
            "result": "rejected",
            "approval": match,
            "next_step": "Sales rep must revise quote and resubmit"
        }, indent=2)

    def _handle_escalate(self, **kwargs) -> str:
        approval_id = kwargs.get("approval_id")
        if not approval_id:
            return json.dumps({"error": "approval_id required"})
        match = next((a for a in DEMO_APPROVALS if a["approval_id"] == approval_id), None)
        if not match:
            return json.dumps({"error": f"Approval {approval_id} not found"})
        current_role = match.get("approver_role", "vp_sales")
        next_role = "cfo" if current_role == "vp_sales" else "ceo"
        return json.dumps({
            "result": "escalated",
            "from_role": current_role,
            "to_role": next_role,
            "to_approver": APPROVERS.get(next_role, {}).get("name", "Executive Team"),
            "approval": match
        }, indent=2)

    def _handle_matrix(self) -> str:
        return json.dumps({
            "approval_matrix": {
                "discount_auto": "≤ 15% → Auto-approved",
                "discount_vp": "16-25% → VP Sales (James Harrison)",
                "discount_cfo": "> 25% → CFO (David Kim)",
                "high_value": "> $500K → VP Sales regardless of discount",
                "non_standard_tc": "Any non-standard terms → Legal (Patricia Cross)",
                "sla": "48 hours — auto-escalate if unresolved",
                "delegation": "If approver OOO, routes to their configured delegate"
            }
        }, indent=2)

    def _handle_validate_pricing(self, **kwargs) -> str:
        """
        STUB — In production:
        GET /data/InventItemPricing?$filter=ItemId eq '{productId}'
        """
        return json.dumps({
            "pricing_catalog": DEMO_PRICING,
            "source": "D365 F&O (stubbed)",
            "note": "Validate proposed line items against min-price floor"
        }, indent=2)
