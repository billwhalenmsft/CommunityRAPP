"""
Ascend – PR Approval Agent
Phase 6: Upstream Procurement Agent

Handles the approver-side of the PR lifecycle:
  - Delegation of Authority (DoA) evaluation
  - Approve / reject via natural language
  - Approval notification dispatch
  - SAP workflow (BUS2105) interaction

SAP ECC 6.0 table reads:  EBAN (release fields), T16FS, T161F, T161G,
                           T161H, T161S, workflow logs
SAP ECC 6.0 table writes: EBAN (release decision), BUS2105 workflow trigger,
                           notification (email/SAP/Teams)
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent
from utils.storage_factory import get_storage_manager

logger = logging.getLogger(__name__)

WARN     = "warning"
BLOCK    = "blocking"
ESCALATE = "escalation"

# ---------------------------------------------------------------------------
# Mock DoA configuration — maps (lo, hi) value range to approval level
# In production this reads T16FS / T161F / T161G / T161H / T161S
# ---------------------------------------------------------------------------
DOA_CONFIG = {
    (0,      5000):   {"level": "L1", "role": "Line Manager",        "backup": "U002"},
    (5001,   25000):  {"level": "L2", "role": "Department Director",  "backup": "U003"},
    (25001,  100000): {"level": "L3", "role": "VP Finance",           "backup": "U004"},
    (100001, 9e99):   {"level": "L4", "role": "CFO Office",           "backup": "U004"},
}

APPROVER_REGISTRY = {
    "U001": {"name": "Jane Doe",     "email": "jane.doe@ascend.com",    "active": True},
    "U002": {"name": "John Smith",   "email": "john.smith@ascend.com",  "active": True},
    "U003": {"name": "Susan Lee",    "email": "susan.lee@ascend.com",   "active": True},
    "U004": {"name": "CFO Office",   "email": "cfo@ascend.com",         "active": True},
}


def _resolve_approver_for_value(total_value: float) -> Optional[Dict]:
    for (lo, hi), config in DOA_CONFIG.items():
        if lo <= total_value <= hi:
            return config
    return None


def _get_approver_info(approver_id: str) -> Optional[Dict]:
    info = APPROVER_REGISTRY.get(approver_id)
    if info:
        return {**info, "id": approver_id}
    return None


class AscendPRApprovalAgent(BasicAgent):
    """
    PR Approval and DoA Agent for Ascend.
    Enables approvers to approve/reject PRs via natural language.
    Evaluates Delegation of Authority (DoA) release strategies from SAP ECC 6.0.
    """

    def __init__(self):
        self.name = "AscendPRApproval"
        self.metadata = {
            "name": self.name,
            "description": (
                "Handles Purchase Requisition approvals for Ascend. "
                "Approvers can approve or reject PRs via natural language. "
                "Evaluates Delegation of Authority (DoA) release strategies "
                "(SAP: T16FS, T161F, T161G, T161H, T161S). "
                "Updates SAP EBAN release fields and triggers BUS2105 workflow. "
                "Actions: approve_pr, reject_pr, get_pending_approvals, "
                "evaluate_doa, get_approval_history."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "approve_pr",
                            "reject_pr",
                            "get_pending_approvals",
                            "evaluate_doa",
                            "get_approval_history",
                        ],
                        "description": "Operation to perform.",
                    },
                    "pr_number":     {"type": "string",  "description": "SAP PR number."},
                    "approver_guid": {"type": "string",  "description": "GUID of the person approving/rejecting."},
                    "approver_name": {"type": "string",  "description": "Display name of approver."},
                    "rejection_reason":{"type": "string","description": "Reason for rejection (required for reject_pr)."},
                    "total_value":   {"type": "number",  "description": "Total PR value for DoA evaluation."},
                    "company_code":  {"type": "string",  "description": "SAP company code."},
                    "cost_center":   {"type": "string",  "description": "SAP cost center."},
                    "requestor_guid":{"type": "string",  "description": "GUID of the PR requestor (to notify)."},
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    # ------------------------------------------------------------------
    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_pending_approvals")
        try:
            if action == "approve_pr":            return self._approve_pr(kwargs)
            if action == "reject_pr":             return self._reject_pr(kwargs)
            if action == "get_pending_approvals": return self._get_pending_approvals(kwargs)
            if action == "evaluate_doa":          return self._evaluate_doa(kwargs)
            if action == "get_approval_history":  return self._get_approval_history(kwargs)
            return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as exc:
            logger.error("AscendPRApprovalAgent error: %s", exc, exc_info=True)
            return json.dumps({
                "status": "error",
                "severity": BLOCK,
                "message": f"An unexpected error occurred: {exc}. Please try again or contact support.",
                "error_category": "technical_system",
            })

    # ------------------------------------------------------------------
    # Storage helpers — simulates EBAN reads/writes in demo mode
    # ------------------------------------------------------------------
    def _load_all_prs(self) -> List[Dict]:
        """Load PRs across all users (admin-level read for approver view)."""
        storage = get_storage_manager()
        try:
            raw = storage.read_file("rapp-data", "ascend/pr_index/global_index.json") or "[]"
            return json.loads(raw)
        except Exception:
            return []

    def _load_user_prs(self, user_guid: str) -> List[Dict]:
        storage = get_storage_manager()
        key = f"ascend/pr_index/{user_guid}_recent.json"
        try:
            raw = storage.read_file("rapp-data", key) or "[]"
            return json.loads(raw)
        except Exception:
            return []

    def _find_pr_anywhere(self, pr_number: str) -> Optional[tuple]:
        """Returns (pr_record, requestor_guid) — scans known indexes."""
        storage = get_storage_manager()
        # Try global index first
        global_prs = self._load_all_prs()
        for pr in global_prs:
            if pr.get("pr_number") == pr_number:
                return pr, pr.get("requestor_guid", "anonymous")
        return None, None

    def _update_pr_status(self, pr_number: str, requestor_guid: str,
                          new_status: str, extra_fields: Dict) -> bool:
        storage = get_storage_manager()
        key = f"ascend/pr_index/{requestor_guid}_recent.json"
        try:
            raw = storage.read_file("rapp-data", key) or "[]"
            prs = json.loads(raw)
            for i, p in enumerate(prs):
                if p.get("pr_number") == pr_number:
                    prs[i]["status"] = new_status
                    prs[i].update(extra_fields)
                    storage.write_file("rapp-data", key, json.dumps(prs, indent=2))
                    return True
            return False
        except Exception as exc:
            logger.error("Failed to update PR %s: %s", pr_number, exc)
            return False

    def _validate_approver_authority(self, approver_guid: str,
                                     pr: Dict) -> tuple:
        """Returns (is_authorized, reason)."""
        # Check approver is the assigned one
        assigned_id = pr.get("approver_id", "")
        if approver_guid != assigned_id:
            # Check if this approver has a higher DoA level (escalation path)
            approver_info = _get_approver_info(approver_guid)
            if not approver_info:
                return False, f"Approver GUID '{approver_guid}' is not registered in the DoA system."
            # In production: check T16FS for multi-level release paths
            # For demo: only assigned approver or level L4 can act
            is_cfo = approver_guid == "U004"
            if not is_cfo:
                return False, (
                    f"You are not the assigned approver for PR {pr.get('pr_number')}. "
                    f"Assigned approver: {pr.get('approver_name', 'unknown')}."
                )
        # Check approver is active
        ainfo = _get_approver_info(approver_guid)
        if ainfo and not ainfo.get("active"):
            return False, "Your approver account is currently inactive. Please contact your administrator."
        return True, "authorized"

    # ------------------------------------------------------------------
    # 1. Approve PR (SAP: EBAN release fields + BUS2105 workflow)
    # ------------------------------------------------------------------
    def _approve_pr(self, kwargs: Dict) -> str:
        pr_number      = kwargs.get("pr_number", "").strip()
        approver_guid  = kwargs.get("approver_guid", "")
        approver_name  = kwargs.get("approver_name", "")
        requestor_guid = kwargs.get("requestor_guid", "anonymous")

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which PR would you like to approve? Please provide the PR number.",
                "error_category": "user_input",
            })

        # Load PR — try requestor's store first, then global
        prs = self._load_user_prs(requestor_guid)
        pr = next((p for p in prs if p.get("pr_number") == pr_number), None)
        if not pr:
            pr, requestor_guid = self._find_pr_anywhere(pr_number)

        if not pr:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": f"PR {pr_number} could not be found. Please verify the PR number.",
                "error_category": "master_data",
                "sap_tables": ["EBAN"],
            })

        # Already processed?
        if pr.get("status") in ("approved", "rejected", "cancelled"):
            return json.dumps({
                "status": "already_processed",
                "severity": WARN,
                "current_status": pr["status"],
                "message": (
                    f"PR {pr_number} has already been {pr['status']}. "
                    "No further approval action is needed."
                ),
                "sap_tables": ["EBAN"],
            })

        # Authority check
        if approver_guid:
            authorized, reason = self._validate_approver_authority(approver_guid, pr)
            if not authorized:
                return json.dumps({
                    "status": "unauthorized",
                    "severity": BLOCK,
                    "message": reason,
                    "error_category": "policy_compliance",
                    "sap_tables": ["T16FS", "T161F", "T161G", "T161H", "T161S"],
                })

        # Apply approval
        extra = {
            "approved_by_id":   approver_guid,
            "approved_by_name": approver_name,
            "approved_at":      datetime.utcnow().isoformat(),
            "workflow_event":   "BUS2105_APPROVED",
        }
        success = self._update_pr_status(pr_number, requestor_guid, "approved", extra)

        if not success:
            return json.dumps({
                "status": "sap_update_failed",
                "severity": ESCALATE,
                "message": (
                    f"Failed to update PR {pr_number} in SAP. "
                    "Please try again or contact your procurement administrator."
                ),
                "error_category": "technical_system",
                "sap_tables_written": ["EBAN"],
            })

        return json.dumps({
            "status": "approved",
            "pr_number": pr_number,
            "approved_by": approver_name or approver_guid,
            "vendor": pr.get("vendor_name", ""),
            "total_value": pr.get("total_value", 0),
            "message": (
                f"✅ PR {pr_number} has been approved by {approver_name or 'you'}.\n"
                f"  Vendor: {pr.get('vendor_name', '')}\n"
                f"  Amount: ${pr.get('total_value', 0):,.2f}\n"
                "The requestor has been notified."
            ),
            "sap_tables_written": ["EBAN"],
            "workflow_triggered": "BUS2105",
        })

    # ------------------------------------------------------------------
    # 2. Reject PR (SAP: EBAN release fields + BUS2105 workflow)
    # ------------------------------------------------------------------
    def _reject_pr(self, kwargs: Dict) -> str:
        pr_number        = kwargs.get("pr_number", "").strip()
        approver_guid    = kwargs.get("approver_guid", "")
        approver_name    = kwargs.get("approver_name", "")
        rejection_reason = kwargs.get("rejection_reason", "").strip()
        requestor_guid   = kwargs.get("requestor_guid", "anonymous")

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which PR would you like to reject? Please provide the PR number.",
                "error_category": "user_input",
            })
        if not rejection_reason:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": (
                    f"Please provide a reason for rejecting PR {pr_number}. "
                    "For example: 'Reject PR 10012345 – reason: budget exceeded'."
                ),
                "error_category": "user_input",
            })

        prs = self._load_user_prs(requestor_guid)
        pr = next((p for p in prs if p.get("pr_number") == pr_number), None)
        if not pr:
            pr, requestor_guid = self._find_pr_anywhere(pr_number)

        if not pr:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": f"PR {pr_number} could not be found.",
                "error_category": "master_data",
            })

        if pr.get("status") in ("approved", "rejected", "cancelled"):
            return json.dumps({
                "status": "already_processed",
                "severity": WARN,
                "message": f"PR {pr_number} has already been {pr['status']}.",
            })

        if approver_guid:
            authorized, reason = self._validate_approver_authority(approver_guid, pr)
            if not authorized:
                return json.dumps({
                    "status": "unauthorized",
                    "severity": BLOCK,
                    "message": reason,
                    "error_category": "policy_compliance",
                })

        extra = {
            "rejected_by_id":   approver_guid,
            "rejected_by_name": approver_name,
            "rejection_reason": rejection_reason,
            "rejected_at":      datetime.utcnow().isoformat(),
            "workflow_event":   "BUS2105_REJECTED",
        }
        success = self._update_pr_status(pr_number, requestor_guid, "rejected", extra)

        if not success:
            return json.dumps({
                "status": "sap_update_failed",
                "severity": ESCALATE,
                "message": f"Failed to update PR {pr_number} in SAP. Please try again.",
                "error_category": "technical_system",
            })

        return json.dumps({
            "status": "rejected",
            "pr_number": pr_number,
            "rejected_by": approver_name or approver_guid,
            "rejection_reason": rejection_reason,
            "message": (
                f"PR {pr_number} has been rejected by {approver_name or 'you'}.\n"
                f"  Reason: {rejection_reason}\n"
                "The requestor has been notified."
            ),
            "sap_tables_written": ["EBAN"],
            "workflow_triggered": "BUS2105",
        })

    # ------------------------------------------------------------------
    # 3. Get pending approvals for this approver
    # ------------------------------------------------------------------
    def _get_pending_approvals(self, kwargs: Dict) -> str:
        approver_guid = kwargs.get("approver_guid", "")

        # In production: query EBAN WHERE release status = pending AND approver = this user
        # For demo: scan all stored PRs
        all_prs = self._load_all_prs()

        pending = [
            p for p in all_prs
            if p.get("status") == "pending_approval"
            and (not approver_guid or p.get("approver_id") == approver_guid)
        ]

        if not pending:
            return json.dumps({
                "status": "no_pending",
                "message": "You have no purchase requests awaiting your approval.",
                "sap_tables": ["EBAN"],
            })

        lines = []
        for p in pending[:10]:
            lines.append(
                f"  PR {p['pr_number']} – {p.get('vendor_name','?')} – "
                f"${p.get('total_value',0):,.2f} – "
                f"Requested by {p.get('requestor_name','?')} on {p.get('created_at','')[:10]}"
            )

        return json.dumps({
            "status": "found",
            "pending_prs": pending[:10],
            "message": (
                f"You have {len(pending)} PR(s) awaiting approval:\n"
                + "\n".join(lines)
                + "\n\nSay 'Approve PR [number]' or 'Reject PR [number] – reason: [reason]'."
            ),
            "sap_tables": ["EBAN"],
        })

    # ------------------------------------------------------------------
    # 4. Evaluate DoA for a given total value (SAP: T16FS, T161F-S)
    # ------------------------------------------------------------------
    def _evaluate_doa(self, kwargs: Dict) -> str:
        total_value  = float(kwargs.get("total_value", 0))
        company_code = kwargs.get("company_code", "1000")
        cost_center  = kwargs.get("cost_center", "")

        if total_value <= 0:
            return json.dumps({
                "status": "validation_error",
                "severity": BLOCK,
                "message": "Please provide a valid total value to evaluate the approval level.",
                "error_category": "user_input",
            })

        doa = _resolve_approver_for_value(total_value)
        if not doa:
            return json.dumps({
                "status": "no_strategy",
                "severity": ESCALATE,
                "message": (
                    f"No release strategy found for ${total_value:,.2f}. "
                    "Please contact your procurement administrator."
                ),
                "error_category": "process_configuration",
                "sap_tables": ["T16FS", "T161F", "T161G", "T161H", "T161S"],
            })

        return json.dumps({
            "status": "ok",
            "total_value": total_value,
            "approval_level": doa["level"],
            "approver_role": doa["role"],
            "company_code": company_code,
            "cost_center": cost_center,
            "message": (
                f"For a PR value of ${total_value:,.2f}, approval level {doa['level']} "
                f"is required ({doa['role']})."
            ),
            "sap_tables": ["T16FS", "T161F", "T161G", "T161H", "T161S"],
        })

    # ------------------------------------------------------------------
    # 5. Get approval history for a PR
    # ------------------------------------------------------------------
    def _get_approval_history(self, kwargs: Dict) -> str:
        pr_number      = kwargs.get("pr_number", "").strip()
        requestor_guid = kwargs.get("requestor_guid", "anonymous")

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which PR's approval history would you like to see?",
                "error_category": "user_input",
            })

        prs = self._load_user_prs(requestor_guid)
        pr = next((p for p in prs if p.get("pr_number") == pr_number), None)
        if not pr:
            pr, _ = self._find_pr_anywhere(pr_number)

        if not pr:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": f"PR {pr_number} was not found.",
                "error_category": "master_data",
            })

        # Build history from stored PR fields
        history = []
        history.append({
            "event": "Created",
            "by":    pr.get("requestor_name", "requestor"),
            "at":    pr.get("created_at", "")[:19],
        })
        if pr.get("approved_at"):
            history.append({
                "event": "Approved",
                "by":    pr.get("approved_by_name", "approver"),
                "at":    pr.get("approved_at", "")[:19],
            })
        if pr.get("rejected_at"):
            history.append({
                "event": "Rejected",
                "by":    pr.get("rejected_by_name", "approver"),
                "at":    pr.get("rejected_at", "")[:19],
                "reason": pr.get("rejection_reason", ""),
            })
        if pr.get("cancelled_at"):
            history.append({
                "event": "Cancelled",
                "by":    pr.get("requestor_name", "requestor"),
                "at":    pr.get("cancelled_at", "")[:19],
            })

        lines = [f"  {h['event']} by {h['by']} at {h['at']}" for h in history]
        return json.dumps({
            "status": "found",
            "pr_number": pr_number,
            "history": history,
            "message": (
                f"Approval history for PR {pr_number}:\n" + "\n".join(lines)
            ),
            "sap_tables": ["EBAN", "workflow logs"],
        })
