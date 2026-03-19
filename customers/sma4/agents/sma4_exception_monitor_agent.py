"""
Agent: SMA4 Exception Monitor Agent
Purpose: Level 1 agent — detects anomalies and exceptions in the
         Prospect-to-Quote pipeline that require human attention.

Use Case: Persona Workbench / Cockpit Agent (SMA4)
Module: D365 Sales — Prospect to Quote

Exception Types Monitored:
  1. STALLED_DEAL      — Opportunity stuck at a stage beyond SLA
  2. DISCOUNT_BREACH   — Quote discount exceeds 15% threshold
  3. MISSING_FIELDS    — Required fields empty at current BPF stage
  4. CREDIT_HOLD       — Account on credit hold in F&O
  5. APPROVAL_SLA      — Approval pending > 48 hours
  6. CLOSE_DATE_SLIP   — Estimated close date in the past

Data Sources:
  CRM:  opportunities, quotes, processsessions, accounts
  ERP:  CreditManagement (stubbed)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Thresholds ──────────────────────────────────────────────────
STAGE_SLA_DAYS = {"Qualify": 14, "Develop": 21, "Propose": 14, "Close": 7}
DISCOUNT_THRESHOLD_PCT = 15
APPROVAL_SLA_HOURS = 48
REQUIRED_FIELDS_BY_STAGE = {
    "Qualify": ["accountname", "estimatedvalue", "campaign_source"],
    "Develop": ["accountname", "estimatedvalue", "decision_maker"],
    "Propose": ["accountname", "estimatedvalue", "decision_maker", "quote_id"],
    "Close":   ["accountname", "estimatedvalue", "decision_maker", "quote_id", "contract_type"]
}

# ── Stubbed data ────────────────────────────────────────────────
DEMO_OPPORTUNITIES = [
    {
        "opportunityid": "opp-001", "name": "Contoso — ERP Modernization",
        "estimatedvalue": 320000, "estimatedclosedate": "2026-04-15",
        "salesstage": "Propose", "days_in_stage": 6,
        "ownerid": "a1b2c3d4-0001-0001-0001-000000000001",
        "owner_name": "Sarah Chen",
        "accountname": "Contoso Ltd",
        "decision_maker": "CFO — Rachel Green",
        "quote_id": "qt-001",
        "contract_type": None,
        "campaign_source": "Webinar — Cloud Migration"
    },
    {
        "opportunityid": "opp-002", "name": "Fabrikam — CRM Rollout",
        "estimatedvalue": 185000, "estimatedclosedate": "2026-05-01",
        "salesstage": "Develop", "days_in_stage": 18,
        "ownerid": "a1b2c3d4-0001-0001-0001-000000000001",
        "owner_name": "Sarah Chen",
        "accountname": "Fabrikam Inc",
        "decision_maker": None,     # ← MISSING FIELD
        "quote_id": None,
        "contract_type": None,
        "campaign_source": "LinkedIn ABM"
    },
    {
        "opportunityid": "opp-004", "name": "Adventure Works — Field Service",
        "estimatedvalue": 540000, "estimatedclosedate": "2026-03-10",  # ← IN THE PAST
        "salesstage": "Propose", "days_in_stage": 22,                  # ← STALLED
        "ownerid": "a1b2c3d4-0005-0005-0005-000000000005",
        "owner_name": "Lisa Park",
        "accountname": "Adventure Works",
        "decision_maker": "VP Ops — Tom Baker",
        "quote_id": "qt-003",
        "contract_type": None,
        "campaign_source": "Partner Referral"
    }
]

DEMO_QUOTES = [
    {"quoteid": "qt-001", "opportunityid": "opp-001", "discount_pct": 8,
     "requires_approval": False, "approval_status": "n/a", "approval_requested_at": None},
    {"quoteid": "qt-002", "opportunityid": "opp-002", "discount_pct": 18,
     "requires_approval": True, "approval_status": "pending",
     "approval_requested_at": "2026-03-17T09:00:00"},
    {"quoteid": "qt-003", "opportunityid": "opp-004", "discount_pct": 12,
     "requires_approval": False, "approval_status": "n/a", "approval_requested_at": None}
]

DEMO_CREDIT_STATUS = {
    "Contoso Ltd":     {"credit_hold": False, "credit_limit": 500000, "balance": 120000, "risk": "low"},
    "Fabrikam Inc":    {"credit_hold": False, "credit_limit": 300000, "balance": 280000, "risk": "medium"},
    "Adventure Works": {"credit_hold": True,  "credit_limit": 400000, "balance": 410000, "risk": "high"},
    "Northwind Traders": {"credit_hold": False, "credit_limit": 200000, "balance": 45000, "risk": "low"},
    "WingTip Toys":    {"credit_hold": False, "credit_limit": 100000, "balance": 22000, "risk": "low"}
}


class SMA4ExceptionMonitorAgent(BasicAgent):
    """
    Exception Monitor Agent — scans pipeline for anomalies & SLA breaches.
    """

    def __init__(self):
        self.name = "ExceptionMonitorAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Monitors the D365 Sales Prospect-to-Quote pipeline for exceptions: "
                "stalled deals, discount breaches, missing required fields, credit holds, "
                "approval SLA violations, and close-date slippage."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "scan_all_exceptions",
                            "check_stalled_deals",
                            "check_discount_breaches",
                            "check_missing_fields",
                            "check_credit_holds",
                            "check_approval_sla",
                            "check_close_date_slippage",
                            "get_exception_summary"
                        ],
                        "description": "Exception check to run"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["sales_rep", "coordinator", "marketing", "manager"],
                        "description": "Caller's persona"
                    },
                    "opportunity_id": {
                        "type": "string",
                        "description": "Check a specific deal"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ── Exception detectors ────────────────────────────────────

    def _detect_stalled(self) -> List[Dict]:
        exceptions = []
        for opp in DEMO_OPPORTUNITIES:
            sla = STAGE_SLA_DAYS.get(opp["salesstage"], 14)
            if opp["days_in_stage"] > sla:
                exceptions.append({
                    "type": "STALLED_DEAL",
                    "severity": "high",
                    "opportunity": opp["name"],
                    "opportunity_id": opp["opportunityid"],
                    "stage": opp["salesstage"],
                    "days_in_stage": opp["days_in_stage"],
                    "sla_days": sla,
                    "overdue_by": opp["days_in_stage"] - sla,
                    "owner": opp["owner_name"],
                    "recommended_action": f"Escalate or advance — {opp['days_in_stage'] - sla} days past SLA"
                })
        return exceptions

    def _detect_discount_breach(self) -> List[Dict]:
        exceptions = []
        for qt in DEMO_QUOTES:
            if qt["discount_pct"] > DISCOUNT_THRESHOLD_PCT:
                opp = next((o for o in DEMO_OPPORTUNITIES
                           if o["opportunityid"] == qt["opportunityid"]), {})
                exceptions.append({
                    "type": "DISCOUNT_BREACH",
                    "severity": "high",
                    "quote_id": qt["quoteid"],
                    "opportunity": opp.get("name", "Unknown"),
                    "discount_pct": qt["discount_pct"],
                    "threshold_pct": DISCOUNT_THRESHOLD_PCT,
                    "overage_pct": qt["discount_pct"] - DISCOUNT_THRESHOLD_PCT,
                    "requires_approval": qt["requires_approval"],
                    "approval_status": qt["approval_status"],
                    "recommended_action": "Route to VP Sales for discount approval"
                })
        return exceptions

    def _detect_missing_fields(self) -> List[Dict]:
        exceptions = []
        for opp in DEMO_OPPORTUNITIES:
            required = REQUIRED_FIELDS_BY_STAGE.get(opp["salesstage"], [])
            missing = [f for f in required
                       if not opp.get(f) or opp.get(f) is None or opp.get(f) == ""]
            if missing:
                exceptions.append({
                    "type": "MISSING_FIELDS",
                    "severity": "medium",
                    "opportunity": opp["name"],
                    "opportunity_id": opp["opportunityid"],
                    "stage": opp["salesstage"],
                    "missing_fields": missing,
                    "owner": opp["owner_name"],
                    "recommended_action": f"Complete required fields: {', '.join(missing)}"
                })
        return exceptions

    def _detect_credit_hold(self) -> List[Dict]:
        """
        STUB — In production:
        GET /data/CreditManagement?$filter=CustomerAccount eq '{acct}'
        """
        exceptions = []
        for opp in DEMO_OPPORTUNITIES:
            acct = opp["accountname"]
            credit = DEMO_CREDIT_STATUS.get(acct, {})
            if credit.get("credit_hold"):
                exceptions.append({
                    "type": "CREDIT_HOLD",
                    "severity": "critical",
                    "opportunity": opp["name"],
                    "account": acct,
                    "credit_limit": credit["credit_limit"],
                    "outstanding_balance": credit["balance"],
                    "risk_score": credit["risk"],
                    "recommended_action": "Resolve credit hold with Finance before advancing quote"
                })
        return exceptions

    def _detect_approval_sla(self) -> List[Dict]:
        exceptions = []
        now = datetime.now()
        for qt in DEMO_QUOTES:
            if qt["approval_status"] == "pending" and qt["approval_requested_at"]:
                requested = datetime.fromisoformat(qt["approval_requested_at"])
                hours_pending = (now - requested).total_seconds() / 3600
                if hours_pending > APPROVAL_SLA_HOURS:
                    opp = next((o for o in DEMO_OPPORTUNITIES
                               if o["opportunityid"] == qt["opportunityid"]), {})
                    exceptions.append({
                        "type": "APPROVAL_SLA",
                        "severity": "high",
                        "quote_id": qt["quoteid"],
                        "opportunity": opp.get("name", "Unknown"),
                        "hours_pending": round(hours_pending, 1),
                        "sla_hours": APPROVAL_SLA_HOURS,
                        "overdue_hours": round(hours_pending - APPROVAL_SLA_HOURS, 1),
                        "recommended_action": "Escalate to VP — approval past 48h SLA"
                    })
        return exceptions

    def _detect_close_date_slip(self) -> List[Dict]:
        exceptions = []
        today = datetime.now().date()
        for opp in DEMO_OPPORTUNITIES:
            close_date = datetime.strptime(opp["estimatedclosedate"], "%Y-%m-%d").date()
            if close_date < today:
                exceptions.append({
                    "type": "CLOSE_DATE_SLIP",
                    "severity": "medium",
                    "opportunity": opp["name"],
                    "opportunity_id": opp["opportunityid"],
                    "estimated_close": opp["estimatedclosedate"],
                    "days_overdue": (today - close_date).days,
                    "owner": opp["owner_name"],
                    "recommended_action": "Update close date or mark as lost"
                })
        return exceptions

    # ── Action handlers ────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "scan_all_exceptions")

        if action == "scan_all_exceptions":
            return self._handle_full_scan()
        elif action == "check_stalled_deals":
            return json.dumps({"stalled": self._detect_stalled()}, indent=2)
        elif action == "check_discount_breaches":
            return json.dumps({"discounts": self._detect_discount_breach()}, indent=2)
        elif action == "check_missing_fields":
            return json.dumps({"missing_fields": self._detect_missing_fields()}, indent=2)
        elif action == "check_credit_holds":
            return json.dumps({"credit_holds": self._detect_credit_hold()}, indent=2)
        elif action == "check_approval_sla":
            return json.dumps({"approval_sla": self._detect_approval_sla()}, indent=2)
        elif action == "check_close_date_slippage":
            return json.dumps({"close_date_slips": self._detect_close_date_slip()}, indent=2)
        elif action == "get_exception_summary":
            return self._handle_summary()
        return json.dumps({"error": f"Unknown action: {action}"})

    def _handle_full_scan(self) -> str:
        all_exceptions = (
            self._detect_stalled() +
            self._detect_discount_breach() +
            self._detect_missing_fields() +
            self._detect_credit_hold() +
            self._detect_approval_sla() +
            self._detect_close_date_slip()
        )
        by_severity = {
            "critical": [e for e in all_exceptions if e["severity"] == "critical"],
            "high":     [e for e in all_exceptions if e["severity"] == "high"],
            "medium":   [e for e in all_exceptions if e["severity"] == "medium"]
        }
        return json.dumps({
            "total_exceptions": len(all_exceptions),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "exceptions": all_exceptions,
            "scanned_at": datetime.now().isoformat()
        }, indent=2)

    def _handle_summary(self) -> str:
        return json.dumps({
            "stalled_deals": len(self._detect_stalled()),
            "discount_breaches": len(self._detect_discount_breach()),
            "missing_fields": len(self._detect_missing_fields()),
            "credit_holds": len(self._detect_credit_hold()),
            "approval_sla_violations": len(self._detect_approval_sla()),
            "close_date_slips": len(self._detect_close_date_slip()),
            "scanned_at": datetime.now().isoformat()
        }, indent=2)
