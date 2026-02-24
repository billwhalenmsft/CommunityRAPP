"""
Agent: DealerSupportAgent
Purpose: Handles support requests, creates cases, and provides troubleshooting guidance
Data Sources: Salesforce Service Cloud, Knowledge Base, Case Management System
Demo Mode: Uses stubbed data - replace with live API calls for production

Integration Points:
- Salesforce Service Cloud: Case object for ticket creation and tracking
- Knowledge Base: Article search for troubleshooting steps
- Case Management: Escalation rules and SLA tracking

Production Implementation Notes:
1. Implement case creation via Salesforce REST API
2. Integrate knowledge base search for instant answers
3. Add SLA calculation based on priority and product
4. Support file attachment for issue documentation
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from agents.basic_agent import BasicAgent

# =============================================================================
# STUBBED DATA - Mirrors Salesforce Service Cloud API Structure
# Production: Replace with Salesforce Case API calls
#
# Salesforce Case Object Fields:
#   Id, CaseNumber, Subject, Description, Status, Priority, Origin, ContactId, AccountId
#
# API Endpoint: /services/data/v58.0/sobjects/Case
# =============================================================================
STUBBED_SUPPORT_DATA = {
    "case_templates": {
        "product_issue": {
            "type": "Product Issue",
            "priority": "high",
            "sla_hours": 24,
            "auto_fields": ["product_id", "serial_number", "purchase_date"]
        },
        "order_issue": {
            "type": "Order Issue",
            "priority": "medium",
            "sla_hours": 48,
            "auto_fields": ["order_id", "tracking_number"]
        },
        "warranty_claim": {
            "type": "Warranty Claim",
            "priority": "high",
            "sla_hours": 24,
            "auto_fields": ["warranty_id", "serial_number", "issue_description"]
        },
        "general_inquiry": {
            "type": "General Inquiry",
            "priority": "low",
            "sla_hours": 72,
            "auto_fields": []
        }
    },
    "troubleshooting_guides": {
        "compressor_noise": {
            "title": "Compressor Making Unusual Noise",
            "symptoms": ["grinding noise", "rattling", "squealing", "knocking"],
            "steps": [
                {
                    "step": 1,
                    "action": "Check oil level",
                    "details": "Locate dipstick on side of unit, oil should be between MIN and MAX marks",
                    "resolves_percent": 25
                },
                {
                    "step": 2,
                    "action": "Verify air filter condition",
                    "details": "Remove filter cover, check for clogs or debris, replace if dirty",
                    "resolves_percent": 20
                },
                {
                    "step": 3,
                    "action": "Confirm unit is level",
                    "details": "Use level tool, unit should be within ±2 degrees",
                    "resolves_percent": 15
                },
                {
                    "step": 4,
                    "action": "Check belt tension",
                    "details": "Belt should deflect 1/2 inch when pressed, adjust if needed",
                    "resolves_percent": 20
                }
            ],
            "if_unresolved": "Contact support for warranty service"
        }
    },
    "resolution_options": [
        {
            "type": "warranty_replacement",
            "name": "Warranty Replacement",
            "description": "Ship defective unit back, receive replacement",
            "timeline": "2-3 business days",
            "requirements": ["Active warranty", "Original packaging preferred"]
        },
        {
            "type": "on_site_service",
            "name": "On-Site Service",
            "description": "Technician visits your location",
            "timeline": "Schedule within 5 business days",
            "requirements": ["Full coverage warranty or service contract"]
        },
        {
            "type": "depot_repair",
            "name": "Depot Repair",
            "description": "Ship unit to service center for repair",
            "timeline": "5-7 business days",
            "requirements": ["Prepaid shipping label provided"]
        },
        {
            "type": "exchange_at_dc",
            "name": "Exchange at Distribution Center",
            "description": "Swap defective unit at nearest DC",
            "timeline": "Same day",
            "requirements": ["Within 30 miles of distribution center"]
        }
    ],
    "recent_cases": [
        {
            "case_number": "SUP-2025-003421",
            "subject": "Lift System Hydraulic Leak",
            "status": "resolved",
            "created_date": "2025-11-15",
            "resolved_date": "2025-11-18",
            "resolution": "Hydraulic seal replaced under warranty"
        }
    ],
    "contact_info": {
        "support_email": "support@dealer-portal.example.com",
        "support_phone": "1-800-555-0199",
        "hours": "Mon-Fri 7AM-7PM EST, Sat 8AM-2PM EST",
        "emergency_line": "1-800-555-0911 (equipment down)"
    }
}


class DealerSupportAgent(BasicAgent):
    """
    Handles support requests, creates cases, and provides troubleshooting.

    Integration Points:
    - Salesforce Service Cloud: Case creation and management
    - Knowledge Base: Troubleshooting article search
    - Case Management: SLA tracking and escalation

    Demo Mode: Returns stubbed support data
    Production: Connect to live Salesforce Service Cloud
    """

    def __init__(self):
        self.name = 'DealerSupport'
        self.metadata = {
            "name": self.name,
            "description": "Handles dealer support requests including case creation, troubleshooting guidance, and resolution options. Can create support tickets and provide immediate troubleshooting steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'create_support_case' to open ticket, 'get_troubleshooting' for self-help, 'get_case_status' for existing case, 'get_resolution_options' for service choices",
                        "enum": ["create_support_case", "get_troubleshooting", "get_case_status", "get_resolution_options"]
                    },
                    "dealer_id": {
                        "type": "string",
                        "description": "The dealer account ID"
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Type of issue: 'product_issue', 'order_issue', 'warranty_claim', 'general_inquiry'",
                        "enum": ["product_issue", "order_issue", "warranty_claim", "general_inquiry"]
                    },
                    "product_id": {
                        "type": "string",
                        "description": "Product ID or name related to the issue"
                    },
                    "serial_number": {
                        "type": "string",
                        "description": "Serial number of affected product"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the issue"
                    },
                    "case_number": {
                        "type": "string",
                        "description": "Existing case number to look up"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute support operations with stubbed data."""
        action = kwargs.get('action', 'get_resolution_options')
        dealer_id = kwargs.get('dealer_id', 'ACC-001234')
        issue_type = kwargs.get('issue_type', 'product_issue')
        product_id = kwargs.get('product_id')
        description = kwargs.get('description', '')
        case_number = kwargs.get('case_number')

        try:
            if action == 'create_support_case':
                result = self._create_support_case(dealer_id, issue_type, product_id, description)
            elif action == 'get_troubleshooting':
                result = self._get_troubleshooting(product_id, description)
            elif action == 'get_case_status':
                result = self._get_case_status(case_number)
            elif action == 'get_resolution_options':
                result = self._get_resolution_options(issue_type)
            else:
                result = {"error": f"Unknown action: {action}"}

            return json.dumps(result, indent=2)

        except Exception as e:
            logging.error(f"DealerSupportAgent error: {e}")
            return json.dumps({"error": str(e), "demo_mode": True})

    def _create_support_case(self, dealer_id: str, issue_type: str, product_id: str, description: str) -> Dict:
        """
        Create a new support case.

        Production Implementation:
            1. Create Case record in Salesforce
            2. Link to Account and Contact
            3. Apply auto-routing rules
            4. Send confirmation email
        """
        case_number = f"SUP-2026-{datetime.now().strftime('%H%M%S')}"
        template = STUBBED_SUPPORT_DATA["case_templates"].get(issue_type, {})

        return {
            "status": "success",
            "message": "Support case created successfully",
            "case": {
                "case_number": case_number,
                "type": template.get("type", "General Inquiry"),
                "priority": template.get("priority", "medium"),
                "status": "Open - Awaiting Response",
                "created_date": datetime.now().isoformat(),
                "sla_target": f"{template.get('sla_hours', 48)} hours",
                "product": product_id or "Compressor (likely XR-500)",
                "description": description or "Unusual noise reported"
            },
            "troubleshooting": STUBBED_SUPPORT_DATA["troubleshooting_guides"].get("compressor_noise", {}),
            "resolution_options": STUBBED_SUPPORT_DATA["resolution_options"],
            "contact_info": STUBBED_SUPPORT_DATA["contact_info"],
            "source": "Salesforce Service Cloud + Knowledge Base",
            "demo_mode": True
        }

    def _get_troubleshooting(self, product_id: str, description: str) -> Dict:
        """
        Get troubleshooting steps for an issue.

        Production Implementation:
            1. Search knowledge base by product and symptoms
            2. Return top matching articles
            3. Track article views for analytics
        """
        # Demo: Return compressor troubleshooting
        guide = STUBBED_SUPPORT_DATA["troubleshooting_guides"].get("compressor_noise", {})

        return {
            "status": "success",
            "troubleshooting_guide": guide,
            "estimated_self_resolution_rate": "80%",
            "if_unresolved": "Create a support case for warranty service",
            "source": "Knowledge Base",
            "demo_mode": True
        }

    def _get_case_status(self, case_number: str) -> Dict:
        """
        Get status of existing case.

        Production Implementation:
            1. Query Salesforce Case by CaseNumber
            2. Include related activities and comments
            3. Calculate SLA status
        """
        # Demo: Return recent case
        if STUBBED_SUPPORT_DATA["recent_cases"]:
            case = STUBBED_SUPPORT_DATA["recent_cases"][0]
        else:
            case = {
                "case_number": case_number or "SUP-2026-001234",
                "status": "In Progress",
                "created_date": datetime.now().strftime('%Y-%m-%d')
            }

        return {
            "status": "success",
            "case": case,
            "contact_info": STUBBED_SUPPORT_DATA["contact_info"],
            "source": "Salesforce Service Cloud",
            "demo_mode": True
        }

    def _get_resolution_options(self, issue_type: str) -> Dict:
        """
        Get available resolution options for issue type.

        Production Implementation:
            1. Check warranty status for product
            2. Return applicable resolution paths
            3. Include estimated timelines and requirements
        """
        return {
            "status": "success",
            "issue_type": issue_type,
            "resolution_options": STUBBED_SUPPORT_DATA["resolution_options"],
            "contact_info": STUBBED_SUPPORT_DATA["contact_info"],
            "source": "Case Management System",
            "demo_mode": True
        }

    # =========================================================================
    # PRODUCTION IMPLEMENTATION STUBS
    # =========================================================================

    # def _create_salesforce_case(self, case_data: Dict) -> Dict:
    #     """
    #     Create Case in Salesforce Service Cloud.
    #
    #     API Endpoint: POST /services/data/v58.0/sobjects/Case
    #
    #     Example:
    #         import requests
    #         headers = {"Authorization": f"Bearer {access_token}"}
    #         url = f"{instance_url}/services/data/v58.0/sobjects/Case"
    #         response = requests.post(url, headers=headers, json=case_data)
    #         return response.json()
    #     """
    #     pass


# =============================================================================
# MODULE TEST
# =============================================================================
if __name__ == "__main__":
    agent = DealerSupportAgent()

    print("=== Testing DealerSupportAgent ===\n")

    print("1. Create Support Case:")
    result = agent.perform(
        action="create_support_case",
        dealer_id="ACC-001234",
        issue_type="product_issue",
        product_id="Compressor XR-500",
        description="Making strange noise"
    )
    print(result)
