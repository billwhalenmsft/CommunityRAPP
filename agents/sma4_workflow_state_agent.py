"""
Agent: SMA4 Workflow State Agent
Purpose: Level 1 agent — reads current state of opportunities, quotes, and activities
         from D365 Sales. Surfaces "where things stand" for each deal in the
         Prospect-to-Quote pipeline, persona-aware.

Use Case: Persona Workbench / Cockpit Agent (SMA4)
Module: D365 Sales — Prospect to Quote

Data Sources:
  CRM:  opportunities, quotes, activitypointers, tasks, systemusers
  ERP:  SalesOrderHeaders (stubbed — future)

Personas Served:
  - Sales Rep:        My active deals, stage progression, quote status
  - Sales Coordinator: Deals awaiting quote prep, order entry queue
  - Marketing:        MQL→SQL conversions, campaign-sourced pipeline
  - Sales Manager:    Team pipeline view, stage distribution, velocity
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
#  STUBBED CRM / ERP DATA
#  Replace with live Dataverse calls (requests + bearer token)
#  when connected to a real D365 environment.
# ───────────────────────────────────────────────────────────────

DEMO_PERSONAS = {
    "sales_rep": {
        "user_id": "a1b2c3d4-0001-0001-0001-000000000001",
        "name": "Sarah Chen",
        "title": "Senior Sales Representative",
        "team": "Enterprise West",
        "role": "sales_rep"
    },
    "coordinator": {
        "user_id": "a1b2c3d4-0002-0002-0002-000000000002",
        "name": "Mike Torres",
        "title": "Sales Coordinator",
        "team": "Deal Desk",
        "role": "coordinator"
    },
    "marketing": {
        "user_id": "a1b2c3d4-0003-0003-0003-000000000003",
        "name": "Priya Patel",
        "title": "Marketing Manager",
        "team": "Demand Gen",
        "role": "marketing"
    },
    "manager": {
        "user_id": "a1b2c3d4-0004-0004-0004-000000000004",
        "name": "James Harrison",
        "title": "VP Sales — Enterprise",
        "team": "Enterprise West",
        "role": "manager"
    }
}

DEMO_OPPORTUNITIES = [
    {
        "opportunityid": "opp-001", "name": "Contoso — ERP Modernization",
        "estimatedvalue": 320000, "estimatedclosedate": "2026-04-15",
        "stepname": "Propose", "salesstage": "Propose", "statuscode": 1,
        "ownerid": "a1b2c3d4-0001-0001-0001-000000000001",
        "owner_name": "Sarah Chen",
        "accountname": "Contoso Ltd",
        "days_in_stage": 6, "pipeline_velocity": "on-track",
        "campaign_source": "Webinar — Cloud Migration",
        "createdon": "2026-01-10"
    },
    {
        "opportunityid": "opp-002", "name": "Fabrikam — CRM Rollout",
        "estimatedvalue": 185000, "estimatedclosedate": "2026-05-01",
        "stepname": "Develop", "salesstage": "Develop", "statuscode": 1,
        "ownerid": "a1b2c3d4-0001-0001-0001-000000000001",
        "owner_name": "Sarah Chen",
        "accountname": "Fabrikam Inc",
        "days_in_stage": 18, "pipeline_velocity": "at-risk",
        "campaign_source": "LinkedIn ABM",
        "createdon": "2026-02-03"
    },
    {
        "opportunityid": "opp-003", "name": "Northwind — Data Platform",
        "estimatedvalue": 95000, "estimatedclosedate": "2026-04-30",
        "stepname": "Qualify", "salesstage": "Qualify", "statuscode": 1,
        "ownerid": "a1b2c3d4-0001-0001-0001-000000000001",
        "owner_name": "Sarah Chen",
        "accountname": "Northwind Traders",
        "days_in_stage": 4, "pipeline_velocity": "on-track",
        "campaign_source": "Inbound — Website",
        "createdon": "2026-03-12"
    },
    {
        "opportunityid": "opp-004", "name": "Adventure Works — Field Service",
        "estimatedvalue": 540000, "estimatedclosedate": "2026-06-30",
        "stepname": "Propose", "salesstage": "Propose", "statuscode": 1,
        "ownerid": "a1b2c3d4-0005-0005-0005-000000000005",
        "owner_name": "Lisa Park",
        "accountname": "Adventure Works",
        "days_in_stage": 22, "pipeline_velocity": "stalled",
        "campaign_source": "Partner Referral",
        "createdon": "2025-12-01"
    },
    {
        "opportunityid": "opp-005", "name": "WingTip Toys — Commerce",
        "estimatedvalue": 72000, "estimatedclosedate": "2026-04-10",
        "stepname": "Close", "salesstage": "Close", "statuscode": 1,
        "ownerid": "a1b2c3d4-0005-0005-0005-000000000005",
        "owner_name": "Lisa Park",
        "accountname": "WingTip Toys",
        "days_in_stage": 3, "pipeline_velocity": "on-track",
        "campaign_source": "Webinar — Cloud Migration",
        "createdon": "2026-02-20"
    }
]

DEMO_QUOTES = [
    {
        "quoteid": "qt-001", "name": "Contoso ERP — Proposal v2",
        "totalamount": 320000, "statuscode": 1, "statecode": 0,
        "quotenumber": "QT-2026-0042",
        "opportunityid": "opp-001",
        "createdon": "2026-03-12",
        "discount_pct": 8, "requires_approval": False
    },
    {
        "quoteid": "qt-002", "name": "Fabrikam CRM — Budget Estimate",
        "totalamount": 185000, "statuscode": 1, "statecode": 0,
        "quotenumber": "QT-2026-0039",
        "opportunityid": "opp-002",
        "createdon": "2026-03-01",
        "discount_pct": 18, "requires_approval": True
    },
    {
        "quoteid": "qt-003", "name": "Adventure Works FS — Final",
        "totalamount": 540000, "statuscode": 3, "statecode": 0,
        "quotenumber": "QT-2026-0035",
        "opportunityid": "opp-004",
        "createdon": "2026-02-25",
        "discount_pct": 12, "requires_approval": False
    }
]

# ── BPF stage definitions ──
BPF_STAGES = ["Qualify", "Develop", "Propose", "Close"]
STAGE_SLA_DAYS = {"Qualify": 14, "Develop": 21, "Propose": 14, "Close": 7}


class SMA4WorkflowStateAgent(BasicAgent):
    """
    Workflow State Agent — reads opportunity pipeline and quote state.
    Persona-aware: filters and formats data based on the caller's role.
    """

    def __init__(self):
        self.name = "WorkflowStateAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Reads the current state of opportunities, quotes, and pipeline "
                "progression from D365 Sales. Provides persona-specific views for "
                "Sales Reps, Coordinators, Marketing, and Managers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_my_pipeline",
                            "get_opportunity_detail",
                            "get_quote_status",
                            "get_stage_distribution",
                            "get_pipeline_velocity",
                            "get_campaign_pipeline"
                        ],
                        "description": "The pipeline action to perform"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["sales_rep", "coordinator", "marketing", "manager"],
                        "description": "Caller's persona/role"
                    },
                    "opportunity_id": {
                        "type": "string",
                        "description": "Specific opportunity ID to inspect"
                    },
                    "stage_filter": {
                        "type": "string",
                        "enum": ["Qualify", "Develop", "Propose", "Close"],
                        "description": "Filter to a specific pipeline stage"
                    }
                },
                "required": ["action", "persona"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ── CRM Data Stubs ─────────────────────────────────────────
    def _get_opportunities(self, owner_id: str = None, stage: str = None) -> List[Dict]:
        """
        STUB — In production, calls:
        GET /api/data/v9.2/opportunities
            ?$filter=ownerid eq {userId} and statecode eq 0
            &$select=name,estimatedvalue,estimatedclosedate,stepname,salesstage,statuscode
        """
        result = DEMO_OPPORTUNITIES
        if owner_id:
            result = [o for o in result if o["ownerid"] == owner_id]
        if stage:
            result = [o for o in result if o["salesstage"] == stage]
        return result

    def _get_quotes(self, opportunity_id: str = None) -> List[Dict]:
        """
        STUB — In production, calls:
        GET /api/data/v9.2/quotes
            ?$filter=_opportunityid_value eq {oppId}
            &$select=name,totalamount,statuscode,quotenumber
        """
        if opportunity_id:
            return [q for q in DEMO_QUOTES if q["opportunityid"] == opportunity_id]
        return DEMO_QUOTES

    def _get_erp_order_status(self, quote_number: str) -> Dict:
        """
        STUB — In production, calls D365 F&O:
        GET /data/SalesOrderHeaders?$filter=SalesOrderNumber eq '{quoteRef}'
        """
        return {
            "order_number": f"SO-{quote_number}",
            "status": "Confirmed",
            "requested_ship_date": "2026-05-15",
            "source": "D365 F&O (stubbed)"
        }

    # ── Action handlers ────────────────────────────────────────
    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_my_pipeline")
        persona = kwargs.get("persona", "sales_rep")
        opp_id = kwargs.get("opportunity_id")
        stage_filter = kwargs.get("stage_filter")

        handlers = {
            "get_my_pipeline": self._handle_my_pipeline,
            "get_opportunity_detail": self._handle_opp_detail,
            "get_quote_status": self._handle_quote_status,
            "get_stage_distribution": self._handle_stage_distribution,
            "get_pipeline_velocity": self._handle_velocity,
            "get_campaign_pipeline": self._handle_campaign_pipeline
        }

        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})

        return handler(persona=persona, opportunity_id=opp_id, stage_filter=stage_filter)

    def _handle_my_pipeline(self, persona: str, **kwargs) -> str:
        user = DEMO_PERSONAS.get(persona, DEMO_PERSONAS["sales_rep"])
        stage_filter = kwargs.get("stage_filter")

        if persona == "manager":
            opps = self._get_opportunities(stage=stage_filter)
        elif persona == "coordinator":
            opps = [o for o in self._get_opportunities(stage=stage_filter)
                    if o["salesstage"] in ("Propose", "Close")]
        elif persona == "marketing":
            opps = self._get_opportunities(stage=stage_filter)
        else:
            opps = self._get_opportunities(owner_id=user["user_id"], stage=stage_filter)

        total_value = sum(o["estimatedvalue"] for o in opps)
        summary = {
            "persona": user["name"],
            "role": user["role"],
            "pipeline_count": len(opps),
            "pipeline_value": total_value,
            "opportunities": [
                {
                    "id": o["opportunityid"],
                    "name": o["name"],
                    "account": o["accountname"],
                    "value": o["estimatedvalue"],
                    "stage": o["salesstage"],
                    "close_date": o["estimatedclosedate"],
                    "days_in_stage": o["days_in_stage"],
                    "velocity": o["pipeline_velocity"]
                } for o in opps
            ],
            "generated_at": datetime.now().isoformat()
        }
        return json.dumps(summary, indent=2)

    def _handle_opp_detail(self, persona: str, opportunity_id: str = None, **kwargs) -> str:
        if not opportunity_id:
            return json.dumps({"error": "opportunity_id is required"})
        matches = [o for o in DEMO_OPPORTUNITIES if o["opportunityid"] == opportunity_id]
        if not matches:
            return json.dumps({"error": f"Opportunity {opportunity_id} not found"})
        opp = matches[0]
        quotes = self._get_quotes(opportunity_id)
        sla_days = STAGE_SLA_DAYS.get(opp["salesstage"], 14)
        detail = {
            "opportunity": opp,
            "quotes": quotes,
            "stage_sla_days": sla_days,
            "sla_status": "breached" if opp["days_in_stage"] > sla_days else "ok",
            "erp_status": self._get_erp_order_status(quotes[0]["quotenumber"]) if quotes else None
        }
        return json.dumps(detail, indent=2)

    def _handle_quote_status(self, persona: str, opportunity_id: str = None, **kwargs) -> str:
        quotes = self._get_quotes(opportunity_id)
        return json.dumps({
            "quote_count": len(quotes),
            "quotes": quotes,
            "pending_approval": [q for q in quotes if q.get("requires_approval")]
        }, indent=2)

    def _handle_stage_distribution(self, persona: str, **kwargs) -> str:
        if persona == "manager":
            opps = DEMO_OPPORTUNITIES
        else:
            user = DEMO_PERSONAS.get(persona, DEMO_PERSONAS["sales_rep"])
            opps = [o for o in DEMO_OPPORTUNITIES if o["ownerid"] == user["user_id"]]
        distribution = {}
        for stage in BPF_STAGES:
            stage_opps = [o for o in opps if o["salesstage"] == stage]
            distribution[stage] = {
                "count": len(stage_opps),
                "value": sum(o["estimatedvalue"] for o in stage_opps)
            }
        return json.dumps({"stage_distribution": distribution}, indent=2)

    def _handle_velocity(self, persona: str, **kwargs) -> str:
        opps = DEMO_OPPORTUNITIES if persona == "manager" else \
            [o for o in DEMO_OPPORTUNITIES
             if o["ownerid"] == DEMO_PERSONAS.get(persona, DEMO_PERSONAS["sales_rep"])["user_id"]]
        velocity = {
            "on_track": [o["name"] for o in opps if o["pipeline_velocity"] == "on-track"],
            "at_risk": [o["name"] for o in opps if o["pipeline_velocity"] == "at-risk"],
            "stalled": [o["name"] for o in opps if o["pipeline_velocity"] == "stalled"]
        }
        return json.dumps(velocity, indent=2)

    def _handle_campaign_pipeline(self, persona: str, **kwargs) -> str:
        """Marketing persona: pipeline grouped by campaign source."""
        campaigns = {}
        for opp in DEMO_OPPORTUNITIES:
            src = opp.get("campaign_source", "Unknown")
            if src not in campaigns:
                campaigns[src] = {"count": 0, "value": 0, "deals": []}
            campaigns[src]["count"] += 1
            campaigns[src]["value"] += opp["estimatedvalue"]
            campaigns[src]["deals"].append(opp["name"])
        return json.dumps({"campaign_pipeline": campaigns}, indent=2)
