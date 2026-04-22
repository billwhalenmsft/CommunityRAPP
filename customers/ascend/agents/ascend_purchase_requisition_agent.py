"""
Ascend – Purchase Requisition Creator Agent
Phase 6: Upstream Procurement Agent

Handles the full PR creation lifecycle via natural language:
  Intent → Vendor Validation → Item Classification → Line Structure
  → Agreement Check → GL Derivation → DoA/Approver → Preview → SAP Write

SAP ECC 6.0 table reads:  LFA1, LFB1, LFM1, MARA, MAKT, T023, T023T,
                           EINA, EINE, EORD, EKKO, EKPO, T030, SKA1,
                           SKB1, CSKS, AUFK, PRPS, PROJ, T16FS, T161F,
                           T161G, T161H, T161S
SAP ECC 6.0 table writes: EBAN (PR lines), EBKN (account assignment)
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from agents.basic_agent import BasicAgent
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from utils.storage_factory import get_storage_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error severity constants
# ---------------------------------------------------------------------------
WARN = "warning"
BLOCK = "blocking"
ESCALATE = "escalation"

# ---------------------------------------------------------------------------
# Demo / mock data — replace with live SAP connector calls in production
# ---------------------------------------------------------------------------
MOCK_VENDORS = {
    "microsoft": [
        {"id": "V100001", "name": "Microsoft Corporation",      "company_code": "1000", "purch_org": "1000", "blocked": False},
        {"id": "V100002", "name": "Microsoft Licensing LLC",    "company_code": "1000", "purch_org": "1000", "blocked": False},
        {"id": "V100003", "name": "Microsoft Ireland Operations","company_code": "1000", "purch_org": "1000", "blocked": False},
    ],
    "dell": [
        {"id": "V200001", "name": "Dell Technologies Inc",      "company_code": "1000", "purch_org": "1000", "blocked": False},
    ],
    "amazon": [
        {"id": "V300001", "name": "Amazon Web Services Inc",    "company_code": "1000", "purch_org": "1000", "blocked": False},
        {"id": "V300002", "name": "Amazon Business Services",   "company_code": "1000", "purch_org": "1000", "blocked": False},
    ],
}

MOCK_CATEGORIES = {
    "software": {"code": "ITSOFT", "gl": "612345", "description": "IT Software & Licenses"},
    "hardware": {"code": "ITHW",   "gl": "612100", "description": "IT Hardware"},
    "services": {"code": "ITSVC",  "gl": "620000", "description": "IT Services"},
    "subscription": {"code": "ITSOFT", "gl": "612345", "description": "IT Software & Licenses"},
    "consulting": {"code": "CONSLT","gl": "625000", "description": "Consulting Services"},
    "maintenance": {"code": "MAINT","gl": "630000", "description": "Maintenance & Repair"},
}

MOCK_GL_ACCOUNTS = {
    "612345": {"valid": True, "description": "IT Software Expense"},
    "612100": {"valid": True, "description": "IT Hardware Expense"},
    "620000": {"valid": True, "description": "IT Services Expense"},
    "625000": {"valid": True, "description": "Consulting Expense"},
    "630000": {"valid": True, "description": "Maintenance Expense"},
}

MOCK_COST_CENTERS = {
    "100200": {"valid": True, "description": "IT Operations",     "active": True},
    "100300": {"valid": True, "description": "Finance",           "active": True},
    "100400": {"valid": True, "description": "HR",                "active": True},
    "999999": {"valid": False,"description": "Inactive Center",   "active": False},
}

MOCK_AGREEMENTS = {
    ("V100002", "ITSOFT"): {"contract_num": "4500012345", "valid": True,
                             "expires": "2027-12-31", "max_value": 500000},
}

MOCK_DOA = {
    (0, 5000):      {"approver_id": "U001", "approver_name": "Jane Doe",    "level": "L1"},
    (5001, 25000):  {"approver_id": "U002", "approver_name": "John Smith",  "level": "L2"},
    (25001, 100000):{"approver_id": "U003", "approver_name": "Susan Lee",   "level": "L3"},
    (100001, 9e99): {"approver_id": "U004", "approver_name": "CFO Office",  "level": "L4"},
}


def _resolve_approver(total_value: float) -> Optional[Dict]:
    for (lo, hi), approver in MOCK_DOA.items():
        if lo <= total_value <= hi:
            return approver
    return None


def _search_vendors(vendor_name: str) -> List[Dict]:
    key = vendor_name.lower().strip()
    for k, vendors in MOCK_VENDORS.items():
        if k in key or key in k:
            return [v for v in vendors if not v["blocked"]]
    return []


def _classify_item(description: str) -> Optional[Dict]:
    desc_lower = description.lower()
    for keyword, cat in MOCK_CATEGORIES.items():
        if keyword in desc_lower:
            return cat
    return None


def _check_agreement(vendor_id: str, category_code: str) -> Optional[Dict]:
    return MOCK_AGREEMENTS.get((vendor_id, category_code))


def _validate_cost_center(cc: str) -> Dict:
    return MOCK_COST_CENTERS.get(cc, {"valid": False, "description": "Unknown", "active": False})


def _validate_gl(gl: str) -> Dict:
    return MOCK_GL_ACCOUNTS.get(gl, {"valid": False, "description": "Unknown"})


class AscendPurchaseRequisitionAgent(BasicAgent):
    """
    Conversational Purchase Requisition agent for Ascend.
    Orchestrates the full 11-step PR creation flow with SAP ECC 6.0 integration.
    """

    def __init__(self):
        self.name = "AscendPurchaseRequisition"
        self.metadata = {
            "name": self.name,
            "description": (
                "Creates Purchase Requisitions in SAP ECC 6.0 via natural language conversation. "
                "Handles vendor validation (LFA1/LFB1/LFM1), item classification (MARA/T023), "
                "GL derivation (T030/CSKS), DoA approval routing (T16FS), "
                "and PR write (EBAN/EBKN). "
                "Actions: create_pr, validate_vendor, classify_item, build_pr_lines, "
                "check_agreement, derive_gl, determine_approver, preview_pr, submit_pr, "
                "get_pr_status, list_my_prs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Operation to perform.",
                        "enum": [
                            "create_pr",
                            "validate_vendor",
                            "classify_item",
                            "build_pr_lines",
                            "check_agreement",
                            "derive_gl",
                            "determine_approver",
                            "preview_pr",
                            "submit_pr",
                        ],
                    },
                    "vendor_name": {"type": "string", "description": "Vendor name to search for."},
                    "vendor_id":   {"type": "string", "description": "SAP vendor ID once selected."},
                    "item_description": {"type": "string", "description": "What the user is purchasing."},
                    "cadence": {
                        "type": "string",
                        "description": "Billing frequency.",
                        "enum": ["one-time", "monthly", "quarterly", "yearly"],
                    },
                    "amount_per_period": {"type": "number", "description": "Amount per billing period."},
                    "periods":           {"type": "integer","description": "Number of periods (months, quarters, etc.)"},
                    "cost_center":       {"type": "string", "description": "SAP cost center code."},
                    "pr_data":           {"type": "object", "description": "Full PR data dict for preview/submit."},
                    "user_guid":         {"type": "string", "description": "Requestor user GUID."},
                    "user_name":         {"type": "string", "description": "Requestor display name."},
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    # ------------------------------------------------------------------
    # Main dispatcher
    # ------------------------------------------------------------------
    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "create_pr")
        try:
            if action == "validate_vendor":
                return self._validate_vendor(kwargs)
            if action == "classify_item":
                return self._classify_item(kwargs)
            if action == "build_pr_lines":
                return self._build_pr_lines(kwargs)
            if action == "check_agreement":
                return self._check_agreement(kwargs)
            if action == "derive_gl":
                return self._derive_gl(kwargs)
            if action == "determine_approver":
                return self._determine_approver(kwargs)
            if action == "preview_pr":
                return self._preview_pr(kwargs)
            if action == "submit_pr":
                return self._submit_pr(kwargs)
            # Default: guided creation narrative
            return self._create_pr_guidance(kwargs)
        except Exception as exc:
            logger.error("AscendPurchaseRequisitionAgent error: %s", exc, exc_info=True)
            return json.dumps({
                "status": "error",
                "severity": BLOCK,
                "message": f"An unexpected error occurred: {exc}. Please try again or contact support.",
                "error_category": "technical_system",
            })

    # ------------------------------------------------------------------
    # Step 2 – Vendor validation (SAP: LFA1, LFB1, LFM1)
    # ------------------------------------------------------------------
    def _validate_vendor(self, kwargs: Dict) -> str:
        vendor_name = kwargs.get("vendor_name", "").strip()
        if not vendor_name:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "Which vendor would you like to use?",
                "error_category": "user_input",
            })

        matches = _search_vendors(vendor_name)
        if not matches:
            return json.dumps({
                "status": "not_found",
                "severity": BLOCK,
                "message": (
                    f"No active vendor found matching '{vendor_name}'. "
                    "Please refine the vendor name or check with your procurement team."
                ),
                "error_category": "master_data",
                "sap_tables": ["LFA1", "LFB1", "LFM1"],
            })
        if len(matches) == 1:
            v = matches[0]
            return json.dumps({
                "status": "found",
                "vendor": v,
                "message": f"Found vendor: {v['name']}. Is this correct?",
                "sap_tables": ["LFA1", "LFB1", "LFM1"],
            })
        # Multiple matches — require user selection
        names = [f"{i+1}. {v['name']}" for i, v in enumerate(matches)]
        return json.dumps({
            "status": "multiple_found",
            "severity": WARN,
            "vendors": matches,
            "message": (
                f"I found multiple vendors for '{vendor_name}'. Please select one:\n"
                + "\n".join(names)
            ),
            "sap_tables": ["LFA1", "LFB1", "LFM1"],
        })

    # ------------------------------------------------------------------
    # Step 3 – Item / category classification (SAP: MARA, MAKT, T023)
    # ------------------------------------------------------------------
    def _classify_item(self, kwargs: Dict) -> str:
        desc = kwargs.get("item_description", "").strip()
        if not desc:
            return json.dumps({
                "status": "needs_input",
                "severity": BLOCK,
                "message": "What are you purchasing? Please provide a description.",
                "error_category": "user_input",
            })

        category = _classify_item(desc)
        if not category:
            return json.dumps({
                "status": "category_unknown",
                "severity": WARN,
                "message": (
                    f"I wasn't able to automatically classify '{desc}'. "
                    "Can you clarify — is this software, hardware, services, consulting, or maintenance?"
                ),
                "error_category": "master_data",
                "sap_tables": ["MARA", "MAKT", "T023", "T023T"],
            })
        return json.dumps({
            "status": "classified",
            "category": category,
            "message": f"Classified as: {category['description']} (GL: {category['gl']}). Does that look right?",
            "sap_tables": ["MARA", "MAKT", "T023", "T023T", "EINA", "EINE"],
        })

    # ------------------------------------------------------------------
    # Step 4 – Line structure logic
    # ------------------------------------------------------------------
    def _build_pr_lines(self, kwargs: Dict) -> str:
        cadence  = kwargs.get("cadence", "")
        amount   = kwargs.get("amount_per_period", 0)
        periods  = kwargs.get("periods", 0)

        errors = []
        if not cadence:
            errors.append("Please specify billing cadence: one-time, monthly, quarterly, or yearly.")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
        else:
            if amount <= 0:
                errors.append("The amount must be greater than zero. Please re-enter.")
        try:
            periods = int(periods)
        except (TypeError, ValueError):
            periods = 1
        if periods < 1:
            errors.append("Duration must be at least 1 period.")

        if errors:
            return json.dumps({
                "status": "validation_error",
                "severity": BLOCK,
                "errors": errors,
                "message": " ".join(errors),
                "error_category": "user_input",
            })

        # Cadence / period consistency check
        if cadence == "one-time" and periods != 1:
            return json.dumps({
                "status": "validation_error",
                "severity": WARN,
                "message": (
                    f"You selected 'one-time' but entered {periods} period(s). "
                    "Should I treat this as a single payment or change the cadence?"
                ),
                "error_category": "user_input",
            })

        total = amount * periods
        cadence_label = {
            "one-time": "One-Time Payment",
            "monthly":  "Monthly",
            "quarterly":"Quarterly",
            "yearly":   "Annual",
        }.get(cadence, cadence)

        lines = []
        for i in range(periods):
            lines.append({
                "line_num":    i + 1,
                "description": f"Period {i+1} of {periods}",
                "quantity":    1,
                "unit_price":  amount,
                "total":       amount,
            })

        # Warn if unusually high
        warn_msg = None
        if total > 250000:
            warn_msg = f"The total value is ${total:,.2f}. Please confirm this is correct."

        result = {
            "status": "ok",
            "cadence": cadence,
            "cadence_label": cadence_label,
            "amount_per_period": amount,
            "periods": periods,
            "total_value": total,
            "lines": lines,
            "message": f"Structured as {periods} {cadence_label} payment(s) of ${amount:,.2f} — total ${total:,.2f}.",
        }
        if warn_msg:
            result["warning"] = warn_msg
            result["severity"] = WARN
        return json.dumps(result)

    # ------------------------------------------------------------------
    # Step 5 – Agreement & sourcing validation (SAP: EKKO, EKPO, EORD)
    # ------------------------------------------------------------------
    def _check_agreement(self, kwargs: Dict) -> str:
        vendor_id     = kwargs.get("vendor_id", "")
        category_code = kwargs.get("pr_data", {}).get("category_code", "")

        agreement = _check_agreement(vendor_id, category_code)
        if agreement:
            return json.dumps({
                "status": "agreement_found",
                "agreement": agreement,
                "message": (
                    f"Contract {agreement['contract_num']} found for this vendor and category "
                    f"(expires {agreement['expires']}). This PR will reference the existing agreement."
                ),
                "sap_tables": ["EKKO", "EKPO", "EORD"],
            })
        return json.dumps({
            "status": "no_agreement",
            "severity": WARN,
            "message": (
                "No existing contract or source-list entry was found for this vendor and category. "
                "This will be flagged as non-contracted spend. Do you want to proceed?"
            ),
            "sap_tables": ["EKKO", "EKPO", "EORD", "EINA", "EINE"],
        })

    # ------------------------------------------------------------------
    # Step 6 – GL and account assignment derivation (SAP: T030, CSKS)
    # ------------------------------------------------------------------
    def _derive_gl(self, kwargs: Dict) -> str:
        gl_code     = kwargs.get("pr_data", {}).get("gl_code", "")
        cost_center = kwargs.get("cost_center", "")

        errors = []
        gl_info = _validate_gl(gl_code)
        cc_info = _validate_cost_center(cost_center)

        if not gl_code or not gl_info.get("valid"):
            errors.append(f"GL account '{gl_code}' is invalid or not found (SAP: T030, SKA1).")
        if not cost_center:
            errors.append("Cost center is required. Please provide your cost center.")
        elif not cc_info.get("valid") or not cc_info.get("active"):
            errors.append(
                f"Cost center '{cost_center}' is inactive or invalid (SAP: CSKS). "
                "Please provide a valid cost center."
            )

        if errors:
            return json.dumps({
                "status": "validation_error",
                "severity": BLOCK,
                "errors": errors,
                "message": " ".join(errors),
                "error_category": "master_data",
                "sap_tables": ["T030", "SKA1", "SKB1", "CSKS"],
            })

        return json.dumps({
            "status": "ok",
            "gl_code": gl_code,
            "gl_description": gl_info["description"],
            "cost_center": cost_center,
            "cost_center_description": cc_info["description"],
            "message": f"GL {gl_code} ({gl_info['description']}) and cost center {cost_center} ({cc_info['description']}) are valid.",
            "sap_tables": ["T030", "SKA1", "CSKS"],
        })

    # ------------------------------------------------------------------
    # Step 7 – Approval determination / DoA (SAP: T16FS, T161F-S)
    # ------------------------------------------------------------------
    def _determine_approver(self, kwargs: Dict) -> str:
        total_value = float(kwargs.get("pr_data", {}).get("total_value", 0))
        approver = _resolve_approver(total_value)
        if not approver:
            return json.dumps({
                "status": "no_approver",
                "severity": BLOCK,
                "message": (
                    "No approver could be determined for this PR value. "
                    "Please contact your procurement administrator to set up delegation of authority."
                ),
                "error_category": "process_configuration",
                "sap_tables": ["T16FS", "T161F", "T161G", "T161H", "T161S"],
            })
        return json.dumps({
            "status": "ok",
            "approver": approver,
            "message": (
                f"Approver determined: {approver['approver_name']} "
                f"(Level {approver['level']} for ${total_value:,.2f})."
            ),
            "sap_tables": ["T16FS", "T161F", "T161G", "T161H", "T161S"],
        })

    # ------------------------------------------------------------------
    # Step 9 – PR preview generation
    # ------------------------------------------------------------------
    def _preview_pr(self, kwargs: Dict) -> str:
        pr = kwargs.get("pr_data", {})
        required = ["vendor_name", "item_description", "cadence", "amount_per_period",
                    "periods", "total_value", "gl_code", "cost_center", "approver_name"]
        missing = [f for f in required if not pr.get(f)]
        if missing:
            return json.dumps({
                "status": "incomplete",
                "severity": BLOCK,
                "missing_fields": missing,
                "message": (
                    f"The following required fields are missing: {', '.join(missing)}. "
                    "I cannot generate the preview until all fields are complete."
                ),
                "error_category": "user_input",
            })

        agreement_status = "Found" if pr.get("agreement_num") else "Not found — non-contracted spend"
        preview = {
            "status": "ready_for_confirmation",
            "preview": {
                "Vendor":         pr["vendor_name"],
                "Description":    pr["item_description"],
                "Frequency":      pr["cadence"].title(),
                "Amount":         f"${float(pr['amount_per_period']):,.2f}",
                "Duration":       f"{pr['periods']} period(s)",
                "Total":          f"${float(pr['total_value']):,.2f}",
                "Agreement":      agreement_status,
                "GL Code":        pr["gl_code"],
                "Cost Center":    pr["cost_center"],
                "Approver":       pr["approver_name"],
            },
            "message": (
                "Here is your purchase requisition for review:\n"
                f"  Vendor: {pr['vendor_name']}\n"
                f"  Description: {pr['item_description']}\n"
                f"  Frequency: {pr['cadence'].title()}\n"
                f"  Amount: ${float(pr['amount_per_period']):,.2f}\n"
                f"  Duration: {pr['periods']} period(s)\n"
                f"  Total: ${float(pr['total_value']):,.2f}\n"
                f"  Agreement: {agreement_status}\n"
                f"  GL Code: {pr['gl_code']}\n"
                f"  Cost Center: {pr['cost_center']}\n"
                f"  Approver: {pr['approver_name']}\n\n"
                "Do you want me to create this purchase requisition in SAP? "
                "Say 'create requisition' to confirm or let me know what to change."
            ),
        }
        return json.dumps(preview)

    # ------------------------------------------------------------------
    # Step 10 – PR submission to SAP (writes EBAN + EBKN)
    # ------------------------------------------------------------------
    def _submit_pr(self, kwargs: Dict) -> str:
        pr = kwargs.get("pr_data", {})
        user_guid = kwargs.get("user_guid", "anonymous")

        # Duplicate check (simplified — in production query EBAN)
        storage = get_storage_manager()
        existing_key = f"ascend/pr_index/{user_guid}_recent.json"
        try:
            existing_raw = storage.read_file("rapp-data", existing_key) or "[]"
            existing = json.loads(existing_raw)
        except Exception:
            existing = []

        vendor_dup = pr.get("vendor_name", "")
        dup = next(
            (e for e in existing
             if e.get("vendor_name") == vendor_dup
             and e.get("total_value") == pr.get("total_value")
             and e.get("status") == "pending"),
            None,
        )
        if dup:
            return json.dumps({
                "status": "duplicate_warning",
                "severity": WARN,
                "existing_pr": dup,
                "message": (
                    f"A similar PR for {vendor_dup} of ${float(pr.get('total_value',0)):,.2f} "
                    f"is already pending (PR {dup.get('pr_number')}). "
                    "Do you still want to create a new one?"
                ),
            })

        # Generate PR number (in production this comes back from SAP BAPI)
        pr_number = f"1{datetime.now().strftime('%Y%m%d%H%M%S')[:8]}"
        pr_record = {
            "pr_number":       pr_number,
            "vendor_id":       pr.get("vendor_id", ""),
            "vendor_name":     pr.get("vendor_name", ""),
            "item_description":pr.get("item_description", ""),
            "cadence":         pr.get("cadence", ""),
            "amount_per_period":float(pr.get("amount_per_period", 0)),
            "periods":         int(pr.get("periods", 1)),
            "total_value":     float(pr.get("total_value", 0)),
            "gl_code":         pr.get("gl_code", ""),
            "cost_center":     pr.get("cost_center", ""),
            "approver_id":     pr.get("approver_id", ""),
            "approver_name":   pr.get("approver_name", ""),
            "agreement_num":   pr.get("agreement_num", ""),
            "requestor_guid":  user_guid,
            "requestor_name":  kwargs.get("user_name", ""),
            "created_at":      datetime.utcnow().isoformat(),
            "status":          "pending_approval",
            "sap_tables_written": ["EBAN", "EBKN"],
        }

        # Persist to storage (represents SAP EBAN/EBKN write in demo mode)
        existing.append(pr_record)
        try:
            storage.write_file("rapp-data", existing_key, json.dumps(existing, indent=2))
        except Exception as exc:
            logger.warning("Storage write failed (non-fatal for demo): %s", exc)

        return json.dumps({
            "status": "created",
            "pr_number": pr_number,
            "pr_record": pr_record,
            "message": (
                f"✅ Your purchase requisition has been created successfully.\n"
                f"PR Number: {pr_number}\n"
                f"This request has been sent to {pr.get('approver_name', 'your approver')} for approval.\n"
                f"You can approve via SAP, email, or this agent."
            ),
            "sap_tables_written": ["EBAN", "EBKN"],
        })

    # ------------------------------------------------------------------
    # Default: creation guidance narrative
    # ------------------------------------------------------------------
    def _create_pr_guidance(self, kwargs: Dict) -> str:
        return json.dumps({
            "status": "guidance",
            "message": (
                "I can help you create a purchase requisition. Here's the process:\n\n"
                "1. Tell me the vendor name\n"
                "2. Describe what you are purchasing\n"
                "3. Specify billing cadence (one-time / monthly / quarterly / yearly)\n"
                "4. Provide the amount and duration\n"
                "5. I'll look up your GL code, cost center, and approver\n"
                "6. You review the summary and confirm\n"
                "7. I'll create the PR in SAP and notify the approver\n\n"
                "To start, which vendor would you like to use?"
            ),
        })
