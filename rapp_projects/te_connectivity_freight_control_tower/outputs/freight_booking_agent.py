"""
Agent: Freight Booking Control Tower Agent
Customer: TE Connectivity
Use Case: Freight Booking Email Control Tower with Task-Based Exception Management

Purpose:
  Manages freight forwarder exception tasks in Microsoft Planner.
  Provides shift briefings, task lookups, completions, and exception summaries
  for the TE Connectivity Transportation Operations team.

Architecture:
  - Conversational layer: Copilot Studio Agent Flows + Topics
  - Task backend: Microsoft Planner (via Graph API — stubbed for demo)
  - Email trigger: Office 365 Outlook connector (Agent Flow)
  - Storage: AzureFileStorageManager for audit logs and config

Exception Buckets:
  1. Missing Info       — shipper details, addresses, contacts
  2. Documentation      — BoL, invoices, certificates, packing lists
  3. Clarification      — schedule changes, carrier subs, booking confirmations

Priority Classification:
  HIGH (2):   urgent, delay, penalty, demurrage, missed cutoff, hot shipment, expedite
  MEDIUM (5): default when no high-priority keywords detected

Author: RAPP Pipeline (transcript_to_agent) — CommunityRAPP
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Priority keyword lists ─────────────────────────────────────────────────────
HIGH_PRIORITY_KEYWORDS = [
    "urgent", "urgently", "urgency",
    "delay", "delayed",
    "penalty", "demurrage", "storage charges",
    "missed cutoff", "cutoff", "vessel cutoff",
    "hot shipment", "expedite", "expedited",
    "hold", "on hold", "critical", "asap",
    "immediately", "missed departure",
]

# Exception type bucket detection
MISSING_INFO_KEYWORDS = [
    "missing", "need", "provide", "required", "require", "please send",
    "shipper address", "consignee", "contact details", "pickup address",
    "notify party",
]

DOCUMENTATION_KEYWORDS = [
    "document", "invoice", "commercial invoice", "packing list",
    "bill of lading", "bol", "b/l", "certificate of origin", "certificate",
    "customs", "hs code", "declaration", "customs entry",
]

CLARIFICATION_KEYWORDS = [
    "clarify", "clarification", "confirm", "confirmation",
    "schedule change", "carrier change", "vessel substitution", "substituted",
    "etd", "eta", "departure", "booking transfer", "new departure",
    "booking number",
]

# ── Demo data: simulated Planner tasks ─────────────────────────────────────────
# In production these are read live from Microsoft Graph API
# GET /planner/plans/{planId}/tasks
DEMO_PLANNER_TASKS = [
    {
        "id": "TASK-001",
        "title": "URGENT — Missing shipper address for BKG-2024-00341 — Kuehne+Nagel",
        "bucket": "Missing Info",
        "priority": "High",
        "priority_value": 2,
        "status": "open",
        "booking_id": "BKG-2024-00341",
        "shipment_id": "TE-SHP-112233",
        "forwarder": "Kuehne+Nagel",
        "created_at": (datetime.now() - timedelta(hours=26)).isoformat(),
        "due_at": (datetime.now() - timedelta(hours=2)).isoformat(),  # overdue
        "description": "Missing shipper address and contact. Missed vessel cutoff risk. Demurrage penalty if not resolved.",
        "email_from": "dispatch@kuehne-nagel-demo.com",
        "age_hours": 26,
        "overdue": True,
    },
    {
        "id": "TASK-002",
        "title": "Commercial Invoice correction needed — BKG-2024-00298 — DHL Freight",
        "bucket": "Documentation",
        "priority": "Medium",
        "priority_value": 5,
        "status": "open",
        "booking_id": "BKG-2024-00298",
        "shipment_id": "TE-SHP-109876",
        "forwarder": "DHL Freight",
        "created_at": (datetime.now() - timedelta(hours=18)).isoformat(),
        "due_at": (datetime.now() + timedelta(hours=6)).isoformat(),
        "description": "Incorrect HS code on commercial invoice. Customs broker flagged. Cannot clear until corrected.",
        "email_from": "ops@dhl-freight-demo.com",
        "age_hours": 18,
        "overdue": False,
    },
    {
        "id": "TASK-003",
        "title": "Schedule change — please confirm BKG-2024-00355 — Panalpina",
        "bucket": "Clarification",
        "priority": "Medium",
        "priority_value": 5,
        "status": "open",
        "booking_id": "BKG-2024-00355",
        "shipment_id": "TE-SHP-113344",
        "forwarder": "Panalpina",
        "created_at": (datetime.now() - timedelta(hours=8)).isoformat(),
        "due_at": (datetime.now() + timedelta(hours=16)).isoformat(),
        "description": "MSC AMBRA substituted with MSC ELISA. ETD changed from 11-Nov to 14-Nov. Customer confirmation needed.",
        "email_from": "bookings@panalpina-demo.com",
        "age_hours": 8,
        "overdue": False,
    },
    {
        "id": "TASK-004",
        "title": "Packing list required for BKG-2024-00317 — Geodis",
        "bucket": "Missing Info",
        "priority": "Medium",
        "priority_value": 5,
        "status": "open",
        "booking_id": "BKG-2024-00317",
        "shipment_id": "TE-SHP-110045",
        "forwarder": "Geodis",
        "created_at": (datetime.now() - timedelta(hours=52)).isoformat(),
        "due_at": (datetime.now() - timedelta(hours=28)).isoformat(),  # overdue
        "description": "Packing list needed before customs declaration can be completed.",
        "email_from": "freight@geodis-demo.com",
        "age_hours": 52,
        "overdue": True,
    },
    {
        "id": "TASK-005",
        "title": "URGENT — Certificate of Origin missing — BKG-2024-00322 — DB Schenker",
        "bucket": "Documentation",
        "priority": "High",
        "priority_value": 2,
        "status": "open",
        "booking_id": "BKG-2024-00322",
        "shipment_id": "TE-SHP-110567",
        "forwarder": "DB Schenker",
        "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        "due_at": (datetime.now() + timedelta(hours=19)).isoformat(),
        "description": "Shipment ON HOLD at Shanghai port. Certificate of Origin missing. Daily penalty fees accruing. Critical customer shipment.",
        "email_from": "escalations@db-schenker-demo.com",
        "age_hours": 5,
        "overdue": False,
    },
]


def _classify_email(subject: str, body: str) -> Dict[str, Any]:
    """
    Classify an email as a freight exception and determine priority + bucket.
    Uses keyword rules for MVP — Phase 2 will use GPT via CS Generative AI.
    """
    text = (subject + " " + body).lower()

    # Priority detection
    priority = "Medium"
    priority_value = 5
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in text:
            priority = "High"
            priority_value = 2
            break

    # Bucket detection — order matters (documentation before missing info)
    bucket = "Clarification"
    for kw in DOCUMENTATION_KEYWORDS:
        if kw in text:
            bucket = "Documentation"
            break
    for kw in MISSING_INFO_KEYWORDS:
        if kw in text:
            bucket = "Missing Info"
            break

    # Parse booking ID (BKG-YYYY-NNNNN pattern)
    import re
    booking_match = re.search(r'BKG-\d{4}-\d{5}', subject + " " + body)
    booking_id = booking_match.group(0) if booking_match else None

    # Parse shipment ID (TE-SHP-NNNNNN pattern)
    shipment_match = re.search(r'TE-SHP-\d{6}', subject + " " + body)
    shipment_id = shipment_match.group(0) if shipment_match else None

    return {
        "priority": priority,
        "priority_value": priority_value,
        "bucket": bucket,
        "booking_id": booking_id,
        "shipment_id": shipment_id,
    }


class FreightBookingControlTowerAgent(BasicAgent):
    """
    Freight Booking Control Tower Agent for TE Connectivity.

    Manages freight forwarder exception tasks via Microsoft Planner.
    Provides shift briefings, task queries, and exception management
    for the Transportation Operations team.
    """

    def __init__(self):
        self.name = "FreightBookingControlTower"
        self.metadata = {
            "name": self.name,
            "description": (
                "Manages TE Connectivity freight booking exceptions: "
                "shift briefings, task lookups by booking ID or forwarder, "
                "mark tasks complete, and exception summary views."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_shift_briefing",
                            "lookup_tasks",
                            "mark_task_complete",
                            "get_exception_summary",
                            "classify_email",
                            "get_open_tasks",
                            "get_high_priority_tasks",
                            "get_aged_tasks",
                        ],
                        "description": "The operation to perform on the freight exception task board"
                    },
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID to search for (e.g. BKG-2024-00341)"
                    },
                    "forwarder_name": {
                        "type": "string",
                        "description": "Freight forwarder name to search for (e.g. Kuehne+Nagel)"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Planner task ID to mark complete (e.g. TASK-001)"
                    },
                    "email_subject": {
                        "type": "string",
                        "description": "Email subject line for classification"
                    },
                    "email_body": {
                        "type": "string",
                        "description": "Email body text for classification and task creation"
                    },
                    "email_from": {
                        "type": "string",
                        "description": "Sender email address for the forwarder name extraction"
                    },
                    "filter_type": {
                        "type": "string",
                        "enum": ["high_priority", "aged_24h", "aged_48h", "by_bucket", "all"],
                        "description": "Filter type for exception summary view"
                    },
                    "bucket_name": {
                        "type": "string",
                        "enum": ["Missing Info", "Documentation", "Clarification"],
                        "description": "Planner bucket name to filter by"
                    },
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "")
        handlers = {
            "get_shift_briefing":    self._handle_shift_briefing,
            "lookup_tasks":          self._handle_lookup_tasks,
            "mark_task_complete":    self._handle_mark_complete,
            "get_exception_summary": self._handle_exception_summary,
            "classify_email":        self._handle_classify_email,
            "get_open_tasks":        self._handle_get_open,
            "get_high_priority_tasks": self._handle_high_priority,
            "get_aged_tasks":        self._handle_aged_tasks,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("FreightBookingAgent error in action %s: %s", action, str(e))
            return json.dumps({"error": str(e), "action": action})

    # ── Action handlers ────────────────────────────────────────────────────────

    def _handle_shift_briefing(self, **kwargs) -> str:
        """Returns shift start briefing: totals, aged counts, top 5 priority tasks."""
        open_tasks = [t for t in DEMO_PLANNER_TASKS if t["status"] == "open"]
        now = datetime.now()

        high_priority = [t for t in open_tasks if t["priority"] == "High"]
        aged_24h = [t for t in open_tasks if t["age_hours"] >= 24]
        aged_48h = [t for t in open_tasks if t["age_hours"] >= 48]

        # Top 5 by: overdue first, then high priority, then age descending
        top5 = sorted(
            open_tasks,
            key=lambda t: (
                not t["overdue"],
                0 if t["priority"] == "High" else 1,
                -t["age_hours"]
            )
        )[:5]

        return json.dumps({
            "shift_briefing": {
                "as_of": now.isoformat(),
                "total_open": len(open_tasks),
                "high_priority_count": len(high_priority),
                "aged_over_24h": len(aged_24h),
                "aged_over_48h": len(aged_48h),
                "overdue_count": len([t for t in open_tasks if t["overdue"]]),
                "buckets": {
                    "Missing Info": len([t for t in open_tasks if t["bucket"] == "Missing Info"]),
                    "Documentation": len([t for t in open_tasks if t["bucket"] == "Documentation"]),
                    "Clarification": len([t for t in open_tasks if t["bucket"] == "Clarification"]),
                },
                "top_5_tasks": [
                    {
                        "id": t["id"],
                        "title": t["title"],
                        "priority": t["priority"],
                        "bucket": t["bucket"],
                        "age_hours": t["age_hours"],
                        "overdue": t["overdue"],
                        "booking_id": t["booking_id"],
                        "forwarder": t["forwarder"],
                    }
                    for t in top5
                ]
            }
        }, indent=2)

    def _handle_lookup_tasks(self, **kwargs) -> str:
        """Search tasks by booking_id or forwarder_name."""
        booking_id = kwargs.get("booking_id", "").upper()
        forwarder_name = kwargs.get("forwarder_name", "").lower()

        results = []
        for task in DEMO_PLANNER_TASKS:
            if booking_id and booking_id in (task.get("booking_id") or "").upper():
                results.append(task)
            elif booking_id and booking_id in (task.get("shipment_id") or "").upper():
                results.append(task)
            elif forwarder_name and forwarder_name in task.get("forwarder", "").lower():
                results.append(task)

        return json.dumps({
            "query": {"booking_id": booking_id, "forwarder_name": forwarder_name},
            "count": len(results),
            "tasks": results
        }, indent=2)

    def _handle_mark_complete(self, **kwargs) -> str:
        """Mark a task as complete by task_id (demo: updates in-memory list)."""
        task_id = kwargs.get("task_id", "").upper()
        if not task_id:
            return json.dumps({"error": "task_id is required"})

        task = next((t for t in DEMO_PLANNER_TASKS if t["id"].upper() == task_id), None)
        if not task:
            return json.dumps({"error": f"Task {task_id} not found", "available_ids": [t["id"] for t in DEMO_PLANNER_TASKS]})

        # In production: PATCH /planner/tasks/{taskId} with {"percentComplete": 100}
        task["status"] = "complete"
        task["completed_at"] = datetime.now().isoformat()

        logger.info("Marked task %s as complete", task_id)
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "task_title": task["title"],
            "completed_at": task["completed_at"],
            "message": f"Task {task_id} marked as complete in Planner."
        }, indent=2)

    def _handle_exception_summary(self, **kwargs) -> str:
        """Returns filtered exception view based on filter_type."""
        filter_type = kwargs.get("filter_type", "all")
        bucket_name = kwargs.get("bucket_name", "")

        open_tasks = [t for t in DEMO_PLANNER_TASKS if t["status"] == "open"]

        if filter_type == "high_priority":
            tasks = [t for t in open_tasks if t["priority"] == "High"]
            label = "High Priority Exceptions"
        elif filter_type == "aged_24h":
            tasks = [t for t in open_tasks if t["age_hours"] >= 24]
            label = "Exceptions Aged >24 Hours"
        elif filter_type == "aged_48h":
            tasks = [t for t in open_tasks if t["age_hours"] >= 48]
            label = "Exceptions Aged >48 Hours"
        elif filter_type == "by_bucket" and bucket_name:
            tasks = [t for t in open_tasks if t["bucket"] == bucket_name]
            label = f"{bucket_name} Exceptions"
        else:
            tasks = open_tasks
            label = "All Open Exceptions"

        # Sort by priority then age
        tasks = sorted(tasks, key=lambda t: (t["priority_value"], -t["age_hours"]))

        return json.dumps({
            "filter": label,
            "total": len(tasks),
            "tasks": [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "priority": t["priority"],
                    "bucket": t["bucket"],
                    "age_hours": t["age_hours"],
                    "overdue": t["overdue"],
                    "booking_id": t["booking_id"],
                    "forwarder": t["forwarder"],
                    "description": t["description"][:200] + "..." if len(t["description"]) > 200 else t["description"],
                }
                for t in tasks
            ]
        }, indent=2)

    def _handle_classify_email(self, **kwargs) -> str:
        """Classify an incoming email and return suggested Planner task fields."""
        subject = kwargs.get("email_subject", "")
        body = kwargs.get("email_body", "")
        email_from = kwargs.get("email_from", "")

        if not subject and not body:
            return json.dumps({"error": "email_subject and/or email_body required"})

        classification = _classify_email(subject, body)

        # Extract forwarder name from email domain (demo heuristic)
        forwarder = email_from.split("@")[1].split("-demo.")[0].replace("-", " ").title() if email_from else "Unknown Forwarder"

        due_at = datetime.now() + timedelta(hours=24)
        task_title = f"{subject} — {forwarder}" if subject else f"Exception from {forwarder}"

        return json.dumps({
            "classification": classification,
            "suggested_task": {
                "title": task_title[:150],  # Planner title max 255 chars
                "description": f"{body[:500]}...\n\nBooking: {classification.get('booking_id', 'N/A')} | Shipment: {classification.get('shipment_id', 'N/A')}",
                "bucket": classification["bucket"],
                "priority": classification["priority"],
                "priority_value": classification["priority_value"],
                "due_at": due_at.isoformat(),
                "forwarder": forwarder,
                "booking_id": classification.get("booking_id"),
                "shipment_id": classification.get("shipment_id"),
            }
        }, indent=2)

    def _handle_get_open(self, **kwargs) -> str:
        """Return all open tasks."""
        tasks = [t for t in DEMO_PLANNER_TASKS if t["status"] == "open"]
        return json.dumps({"open_count": len(tasks), "tasks": tasks}, indent=2)

    def _handle_high_priority(self, **kwargs) -> str:
        """Return high priority open tasks."""
        tasks = [t for t in DEMO_PLANNER_TASKS if t["status"] == "open" and t["priority"] == "High"]
        return json.dumps({"high_priority_count": len(tasks), "tasks": tasks}, indent=2)

    def _handle_aged_tasks(self, **kwargs) -> str:
        """Return tasks aged >24h or >48h."""
        threshold = kwargs.get("hours_threshold", 24)
        tasks = [t for t in DEMO_PLANNER_TASKS if t["status"] == "open" and t["age_hours"] >= threshold]
        return json.dumps({
            "threshold_hours": threshold,
            "aged_count": len(tasks),
            "tasks": tasks
        }, indent=2)
