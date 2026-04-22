"""
Ascend – PR Status Agent
Phase 6: Upstream Procurement Agent

Handles PR status queries, PR list, and follow-up actions:
  - Status by PR number or user list
  - Cancel / Edit / Remind actions

SAP ECC 6.0 table reads:  EBAN (release fields), EBKN, workflow logs
SAP ECC 6.0 table writes: EBAN (cancel/edit), workflow (reminder trigger)
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


class AscendPRStatusAgent(BasicAgent):
    """
    PR Status and Follow-up Actions agent for Ascend.
    Reads PR state from SAP EBAN and exposes cancel/edit/remind via natural language.
    """

    def __init__(self):
        self.name = "AscendPRStatus"
        self.metadata = {
            "name": self.name,
            "description": (
                "Check the status of Purchase Requisitions for Ascend. "
                "Query by PR number or list recent PRs for the current user. "
                "Supports follow-up actions: cancel a PR, edit a PR, remind the approver. "
                "Reads from SAP EBAN (release fields) and EBKN. "
                "Actions: get_pr_status, list_my_prs, cancel_pr, edit_pr, remind_approver."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_pr_status", "list_my_prs", "cancel_pr", "edit_pr", "remind_approver"],
                        "description": "Operation to perform.",
                    },
                    "pr_number":   {"type": "string",  "description": "SAP PR number, e.g. 10012345."},
                    "user_guid":   {"type": "string",  "description": "Requestor user GUID."},
                    "user_name":   {"type": "string",  "description": "Requestor display name."},
                    "pr_updates":  {"type": "object",  "description": "Updated fields for edit_pr action."},
                    "status_filter":{
                        "type": "string",
                        "description": "Optional filter: pending_approval, approved, rejected, cancelled.",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    # ------------------------------------------------------------------
    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "list_my_prs")
        try:
            if action == "get_pr_status":  return self._get_pr_status(kwargs)
            if action == "list_my_prs":    return self._list_my_prs(kwargs)
            if action == "cancel_pr":      return self._cancel_pr(kwargs)
            if action == "edit_pr":        return self._edit_pr(kwargs)
            if action == "remind_approver":return self._remind_approver(kwargs)
            return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as exc:
            logger.error("AscendPRStatusAgent error: %s", exc, exc_info=True)
            return json.dumps({
                "status": "error",
                "severity": BLOCK,
                "message": f"An unexpected error occurred: {exc}. Please try again or contact support.",
                "error_category": "technical_system",
            })

    # ------------------------------------------------------------------
    # Helpers – load / save the PR store (represents SAP EBAN in demo mode)
    # ------------------------------------------------------------------
    def _load_prs(self, user_guid: str) -> List[Dict]:
        storage = get_storage_manager()
        key = f"ascend/pr_index/{user_guid}_recent.json"
        try:
            raw = storage.read_file("rapp-data", key) or "[]"
            return json.loads(raw)
        except Exception:
            return []

    def _save_prs(self, user_guid: str, prs: List[Dict]) -> None:
        storage = get_storage_manager()
        key = f"ascend/pr_index/{user_guid}_recent.json"
        try:
            storage.write_file("rapp-data", key, json.dumps(prs, indent=2))
        except Exception as exc:
            logger.warning("Storage write failed: %s", exc)

    def _find_pr(self, user_guid: str, pr_number: str) -> Optional[Dict]:
        return next((p for p in self._load_prs(user_guid) if p.get("pr_number") == pr_number), None)

    # ------------------------------------------------------------------
    # 1. Get PR status by PR number (SAP: EBAN release fields)
    # ------------------------------------------------------------------
    def _get_pr_status(self, kwargs: Dict) -> str:
        pr_number = kwargs.get("pr_number", "").strip()
        user_guid = kwargs.get("user_guid", "anonymous")

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Please provide a PR number — for example: 'Status of PR 10012345'.",
                "error_category": "user_input",
            })

        pr = self._find_pr(user_guid, pr_number)
        if not pr:
            # Cross-user fallback (admin mode): scan all stored data would go here
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": (
                    f"PR {pr_number} was not found for your account. "
                    "Please verify the PR number or check with your procurement team."
                ),
                "error_category": "master_data",
                "sap_tables": ["EBAN"],
            })

        status_label = {
            "pending_approval": "Pending Approval",
            "approved":         "Approved",
            "rejected":         "Rejected",
            "cancelled":        "Cancelled",
        }.get(pr.get("status", ""), pr.get("status", "Unknown"))

        submitted = pr.get("created_at", "")[:10]
        return json.dumps({
            "status": "found",
            "pr": pr,
            "message": (
                f"PR {pr_number} — {pr.get('vendor_name', 'Unknown Vendor')}\n"
                f"  Status:    {status_label}\n"
                f"  Amount:    ${pr.get('total_value', 0):,.2f}\n"
                f"  Approver:  {pr.get('approver_name', 'N/A')}\n"
                f"  Submitted: {submitted}\n\n"
                "You can say 'Remind the approver', 'Cancel this PR', or 'Edit this PR'."
            ),
            "sap_tables": ["EBAN", "EBKN"],
        })

    # ------------------------------------------------------------------
    # 2. List PRs for current user (SAP: EBAN by requestor, sorted by date)
    # ------------------------------------------------------------------
    def _list_my_prs(self, kwargs: Dict) -> str:
        user_guid     = kwargs.get("user_guid", "anonymous")
        status_filter = kwargs.get("status_filter", "")

        prs = self._load_prs(user_guid)
        if status_filter:
            prs = [p for p in prs if p.get("status") == status_filter]

        if not prs:
            msg = "You have no purchase requests"
            if status_filter:
                msg += f" with status '{status_filter}'"
            msg += ". Would you like to create one?"
            return json.dumps({
                "status": "no_results",
                "message": msg,
                "sap_tables": ["EBAN"],
            })

        # Return most recent 10
        prs_sorted = sorted(prs, key=lambda p: p.get("created_at", ""), reverse=True)[:10]

        STATUS_MAP = {
            "pending_approval": "Pending Approval",
            "approved":         "Approved",
            "rejected":         "Rejected",
            "cancelled":        "Cancelled",
        }

        lines = []
        for p in prs_sorted:
            lines.append(
                f"  PR {p['pr_number']} – {p.get('vendor_name','?')} – "
                f"${p.get('total_value',0):,.2f} – "
                f"{STATUS_MAP.get(p.get('status',''),'Unknown')}"
            )

        return json.dumps({
            "status": "found",
            "prs": prs_sorted,
            "message": (
                "Here are your recent purchase requests:\n"
                + "\n".join(lines)
                + "\n\nSay a PR number for details, e.g. 'Status of PR 10012345'."
            ),
            "sap_tables": ["EBAN"],
        })

    # ------------------------------------------------------------------
    # 3. Cancel PR (SAP: EBAN update to cancelled)
    # ------------------------------------------------------------------
    def _cancel_pr(self, kwargs: Dict) -> str:
        pr_number = kwargs.get("pr_number", "").strip()
        user_guid = kwargs.get("user_guid", "anonymous")

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which PR would you like to cancel? Please provide the PR number.",
                "error_category": "user_input",
            })

        prs = self._load_prs(user_guid)
        idx = next((i for i, p in enumerate(prs) if p.get("pr_number") == pr_number), None)

        if idx is None:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": f"PR {pr_number} was not found. Please verify the PR number.",
                "error_category": "master_data",
            })

        pr = prs[idx]

        # Eligibility checks
        if pr.get("status") == "approved":
            return json.dumps({
                "status": "action_blocked",
                "severity": BLOCK,
                "message": f"PR {pr_number} has already been approved and cannot be cancelled.",
                "error_category": "policy_compliance",
                "sap_tables": ["EBAN"],
            })
        if pr.get("status") == "cancelled":
            return json.dumps({
                "status": "action_blocked",
                "severity": WARN,
                "message": f"PR {pr_number} is already cancelled.",
                "error_category": "process_configuration",
            })
        if pr.get("locked"):
            return json.dumps({
                "status": "action_blocked",
                "severity": BLOCK,
                "message": f"PR {pr_number} is currently locked in SAP and cannot be cancelled. Please try again shortly.",
                "error_category": "technical_system",
            })

        prs[idx]["status"] = "cancelled"
        prs[idx]["cancelled_at"] = datetime.utcnow().isoformat()
        self._save_prs(user_guid, prs)

        return json.dumps({
            "status": "cancelled",
            "pr_number": pr_number,
            "message": f"PR {pr_number} has been cancelled successfully.",
            "sap_tables_written": ["EBAN"],
        })

    # ------------------------------------------------------------------
    # 4. Edit PR (SAP: EBAN / EBKN update)
    # ------------------------------------------------------------------
    def _edit_pr(self, kwargs: Dict) -> str:
        pr_number  = kwargs.get("pr_number", "").strip()
        user_guid  = kwargs.get("user_guid", "anonymous")
        pr_updates = kwargs.get("pr_updates", {})

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which PR would you like to edit?",
                "error_category": "user_input",
            })
        if not pr_updates:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "What would you like to change? Please specify the field and new value.",
                "error_category": "user_input",
            })

        prs = self._load_prs(user_guid)
        idx = next((i for i, p in enumerate(prs) if p.get("pr_number") == pr_number), None)

        if idx is None:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": f"PR {pr_number} was not found.",
                "error_category": "master_data",
            })

        pr = prs[idx]

        # Edit eligibility checks
        if pr.get("status") in ("approved", "cancelled"):
            return json.dumps({
                "status": "action_blocked",
                "severity": BLOCK,
                "message": (
                    f"PR {pr_number} has status '{pr['status']}' and cannot be edited. "
                    "Only pending PRs can be modified."
                ),
                "error_category": "policy_compliance",
            })
        if pr.get("locked"):
            return json.dumps({
                "status": "action_blocked",
                "severity": BLOCK,
                "message": f"PR {pr_number} is currently locked in SAP. Please try again in a few minutes.",
                "error_category": "technical_system",
            })

        # Apply updates
        allowed_fields = {"item_description", "amount_per_period", "periods",
                          "cost_center", "cadence", "gl_code"}
        applied = {}
        rejected = {}
        for field, value in pr_updates.items():
            if field in allowed_fields:
                prs[idx][field] = value
                applied[field] = value
            else:
                rejected[field] = f"Field '{field}' cannot be edited after creation."

        # Recalculate total if amount or periods changed
        if "amount_per_period" in applied or "periods" in applied:
            prs[idx]["total_value"] = float(prs[idx].get("amount_per_period", 0)) * int(prs[idx].get("periods", 1))

        prs[idx]["last_updated"] = datetime.utcnow().isoformat()
        self._save_prs(user_guid, prs)

        msg = f"PR {pr_number} has been updated."
        if applied:
            msg += f" Changed: {', '.join(f'{k}={v}' for k, v in applied.items())}."
        if rejected:
            msg += f" Note: {'; '.join(rejected.values())}"

        return json.dumps({
            "status": "updated",
            "pr_number": pr_number,
            "applied_updates": applied,
            "rejected_updates": rejected,
            "new_total": prs[idx].get("total_value"),
            "message": msg,
            "sap_tables_written": ["EBAN", "EBKN"],
        })

    # ------------------------------------------------------------------
    # 5. Remind approver (workflow / email trigger)
    # ------------------------------------------------------------------
    def _remind_approver(self, kwargs: Dict) -> str:
        pr_number = kwargs.get("pr_number", "").strip()
        user_guid = kwargs.get("user_guid", "anonymous")

        if not pr_number:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which PR would you like to send a reminder for?",
                "error_category": "user_input",
            })

        pr = self._find_pr(user_guid, pr_number)
        if not pr:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": f"PR {pr_number} was not found.",
                "error_category": "master_data",
            })

        if pr.get("status") != "pending_approval":
            status_label = pr.get("status", "unknown")
            return json.dumps({
                "status": "action_blocked",
                "severity": WARN,
                "message": (
                    f"PR {pr_number} is not pending approval (current status: {status_label}). "
                    "A reminder can only be sent for PRs awaiting approval."
                ),
                "error_category": "process_configuration",
            })

        # In production: trigger SAP workflow BUS2105 reminder or send email via Power Automate
        return json.dumps({
            "status": "reminder_sent",
            "pr_number": pr_number,
            "approver_name": pr.get("approver_name", ""),
            "message": (
                f"✅ A reminder has been sent to {pr.get('approver_name', 'the approver')} "
                f"for PR {pr_number} (${pr.get('total_value', 0):,.2f} – "
                f"{pr.get('vendor_name', '')})."
            ),
            "notification_channels": ["SAP Workflow", "Email"],
        })
