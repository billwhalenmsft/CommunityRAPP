"""
Agent: CarrierSFCaseMonitorAgent
Purpose: Monitors Salesforce for new and aging cases that need triage
Customer: Carrier
Data Sources: Salesforce Service Cloud (Cases, Attachments)
Demo Mode: Uses stubbed data - set use_mock_data=False for live Salesforce

Salesforce Instance: https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com/

Integration Points:
- Salesforce REST API v59.0: Case, CaseComment, Attachment, ContentDocument objects
- SOQL queries for case retrieval
- OAuth 2.0 Username-Password flow for authentication

Configuration (via environment variables):
- SALESFORCE_INSTANCE_URL
- SALESFORCE_CLIENT_ID
- SALESFORCE_CLIENT_SECRET
- SALESFORCE_USERNAME
- SALESFORCE_PASSWORD
- SALESFORCE_SECURITY_TOKEN
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# Import Salesforce client
try:
    from utils.salesforce_client import get_salesforce_client, is_salesforce_configured
except ImportError:
    def get_salesforce_client():
        return None
    def is_salesforce_configured():
        return False

# =============================================================================
# CONFIGURATION
# =============================================================================
SALESFORCE_CONFIG = {
    "instance_url": os.environ.get('SALESFORCE_INSTANCE_URL', 
        "https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com"),
    "api_version": os.environ.get('SALESFORCE_API_VERSION', "v59.0"),
    "use_mock_data": not is_salesforce_configured()  # Auto-detect based on config
}

# =============================================================================
# STUBBED DATA - Mirrors Salesforce Case Object Structure
# Production: Replace with actual SOQL queries to Salesforce
#
# Salesforce Case Object Fields:
#   Id, CaseNumber, Subject, Description, Status, Priority, CreatedDate,
#   ContactId, AccountId, Origin, Type, Reason, etc.
# =============================================================================
STUBBED_CASES = {
    "new_cases": [
        {
            "Id": "500xx000000ABC001",
            "CaseNumber": "00012345",
            "Subject": "HVAC unit not cooling - urgent production floor issue",
            "Description": """Our Carrier 50XC rooftop unit (serial: 2419G12345) installed in 2019 
stopped cooling yesterday. The unit is running but blowing warm air. We've checked 
the thermostat settings and filters. The production floor temperature is now 85°F 
and rising. We need this fixed ASAP as it's affecting worker safety and product quality.

Error code E47 is showing on the control panel. Please advise on next steps.""",
            "Status": "New",
            "Priority": "High",
            "Type": "Mechanical",
            "Origin": "Web",
            "CreatedDate": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
            "Account": {
                "Id": "001xx000000ACC001",
                "Name": "Acme Manufacturing Inc.",
                "AccountNumber": "ACME-001",
                "Type": "Customer - Enterprise"
            },
            "Contact": {
                "Id": "003xx000000CON001",
                "Name": "John Smith",
                "Email": "jsmith@acmemfg.com",
                "Phone": "555-123-4567"
            },
            "Product_Model__c": "50XC",
            "Serial_Number__c": "2419G12345",
            "Install_Date__c": "2019-06-15",
            "Attachments": [
                {
                    "Id": "068xx000000ATT001",
                    "Name": "error_code_e47.jpg",
                    "ContentType": "image/jpeg",
                    "BodyLength": 245678
                },
                {
                    "Id": "068xx000000ATT002",
                    "Name": "unit_photo.jpg",
                    "ContentType": "image/jpeg",
                    "BodyLength": 389012
                }
            ],
            "Triage_Status__c": None,
            "SLA_Deadline__c": (datetime.utcnow() + timedelta(hours=4)).isoformat() + "Z"
        },
        {
            "Id": "500xx000000ABC002",
            "CaseNumber": "00012346",
            "Subject": "Request for preventive maintenance quote",
            "Description": """We have 12 Carrier units across our facility and would like to set up 
a preventive maintenance contract. Please provide a quote for quarterly inspections 
and filter replacements.

Units:
- 4x 38AUD (Split systems, installed 2020)
- 6x 50XC (Rooftop, installed 2018-2021)
- 2x 30RB (Chillers, installed 2017)

Looking for response within the week.""",
            "Status": "New",
            "Priority": "Medium",
            "Type": "Request",
            "Origin": "Email",
            "CreatedDate": (datetime.utcnow() - timedelta(hours=5)).isoformat() + "Z",
            "Account": {
                "Id": "001xx000000ACC002",
                "Name": "Riverside Office Park",
                "AccountNumber": "ROP-2024",
                "Type": "Customer - Commercial"
            },
            "Contact": {
                "Id": "003xx000000CON002",
                "Name": "Sarah Johnson",
                "Email": "sjohnson@riversideop.com",
                "Phone": "555-987-6543"
            },
            "Product_Model__c": None,
            "Serial_Number__c": None,
            "Install_Date__c": None,
            "Attachments": [],
            "Triage_Status__c": None,
            "SLA_Deadline__c": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        },
        {
            "Id": "500xx000000ABC003",
            "CaseNumber": "00012347",
            "Subject": "Chiller making unusual noise - vibration concern",
            "Description": """Our 30RB chiller has started making a loud grinding/vibration noise 
during startup. It seems to run fine once it's going but the startup is concerning.

Model: 30RB 100
Serial: 0918E54321
Location: Building B mechanical room

Attached is a video of the startup sequence showing the noise.

This unit is still under warranty (purchased March 2022).""",
            "Status": "New",
            "Priority": "High",
            "Type": "Mechanical",
            "Origin": "Phone",
            "CreatedDate": (datetime.utcnow() - timedelta(minutes=45)).isoformat() + "Z",
            "Account": {
                "Id": "001xx000000ACC003",
                "Name": "Memorial Hospital",
                "AccountNumber": "MH-2019",
                "Type": "Customer - Healthcare"
            },
            "Contact": {
                "Id": "003xx000000CON003",
                "Name": "Mike Chen",
                "Email": "mchen@memhosp.org",
                "Phone": "555-456-7890"
            },
            "Product_Model__c": "30RB 100",
            "Serial_Number__c": "0918E54321",
            "Install_Date__c": "2022-03-15",
            "Attachments": [
                {
                    "Id": "068xx000000ATT003",
                    "Name": "chiller_startup_noise.mp4",
                    "ContentType": "video/mp4",
                    "BodyLength": 15234567
                }
            ],
            "Triage_Status__c": None,
            "SLA_Deadline__c": (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
        }
    ],
    "aging_cases": [
        {
            "Id": "500xx000000ABC010",
            "CaseNumber": "00012298",
            "Subject": "Controls integration issue with BMS",
            "Description": """Having trouble integrating the Carrier i-Vu control system with our 
existing Johnson Controls BMS. Need technical support for BACnet configuration.

Getting communication timeouts when trying to poll the i-Vu controller.""",
            "Status": "Open",
            "Priority": "Medium",
            "Type": "Controls",
            "Origin": "Web",
            "CreatedDate": (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z",
            "Account": {
                "Id": "001xx000000ACC004",
                "Name": "Downtown Convention Center",
                "AccountNumber": "DCC-2021",
                "Type": "Customer - Commercial"
            },
            "Contact": {
                "Id": "003xx000000CON004",
                "Name": "Lisa Park",
                "Email": "lpark@downtowncc.com",
                "Phone": "555-321-0987"
            },
            "Product_Model__c": "i-Vu",
            "Serial_Number__c": "IVU-2023-001",
            "Install_Date__c": "2023-08-01",
            "Attachments": [
                {
                    "Id": "068xx000000ATT010",
                    "Name": "bacnet_config.pdf",
                    "ContentType": "application/pdf",
                    "BodyLength": 523456
                }
            ],
            "Triage_Status__c": None,
            "SLA_Deadline__c": (datetime.utcnow() - timedelta(hours=12)).isoformat() + "Z",
            "Hours_Without_Triage": 72
        }
    ],
    "queue_summary": {
        "total_new": 3,
        "total_aging": 1,
        "sla_at_risk": 2,
        "by_priority": {
            "Critical": 0,
            "High": 2,
            "Medium": 2,
            "Low": 0
        },
        "by_type": {
            "Mechanical": 2,
            "Controls": 1,
            "Request": 1
        }
    }
}


class CarrierSFCaseMonitorAgent(BasicAgent):
    """
    Monitors Salesforce for new and aging cases that need triage.

    Integration Points:
    - Salesforce REST API v59.0
    - Case, CaseComment, Attachment, ContentDocument objects

    Demo Mode: Returns stubbed data matching Salesforce Case object structure
    Production: Connect to live Salesforce instance

    Salesforce Query Examples (for production):
        -- New cases needing triage
        SELECT Id, CaseNumber, Subject, Description, Status, Priority, Type, Origin,
               CreatedDate, Account.Name, Contact.Name, Contact.Email,
               Product_Model__c, Serial_Number__c, Install_Date__c,
               (SELECT Id, Name, ContentType, BodyLength FROM Attachments)
        FROM Case
        WHERE CreatedDate > :lastCheckTime
          AND Triage_Status__c = null
        ORDER BY Priority DESC, CreatedDate ASC

        -- Aging cases approaching SLA
        SELECT Id, CaseNumber, Subject, Status, Priority, SLA_Deadline__c,
               CreatedDate, HOUR_SINCE_CREATED
        FROM Case
        WHERE Status NOT IN ('Closed', 'Resolved')
          AND SLA_Deadline__c < :slaWarningThreshold
          AND Triage_Status__c = null
    """

    def __init__(self):
        self.name = 'CarrierSFCaseMonitor'
        self.metadata = {
            "name": self.name,
            "description": "Monitors Salesforce for new and aging customer service cases. Retrieves case details including attachments for triage processing. Part of the Carrier Case Triage Agent Swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": [
                            "get_new_cases",
                            "get_aging_cases",
                            "get_untriaged_cases",
                            "get_case_details",
                            "get_case_history",
                            "get_queue_summary"
                        ]
                    },
                    "case_id": {
                        "type": "string",
                        "description": "Salesforce Case ID (18-char) for specific case lookup"
                    },
                    "case_number": {
                        "type": "string",
                        "description": "Case number (e.g., 00012345) for case lookup"
                    },
                    "hours_lookback": {
                        "type": "integer",
                        "description": "Number of hours to look back for new cases (default: 24)",
                        "default": 24
                    },
                    "priority_filter": {
                        "type": "string",
                        "description": "Filter by priority level",
                        "enum": ["Critical", "High", "Medium", "Low"]
                    },
                    "include_attachments": {
                        "type": "boolean",
                        "description": "Include attachment metadata in response",
                        "default": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of cases to return",
                        "default": 50
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = SALESFORCE_CONFIG

    def perform(self, **kwargs) -> str:
        """Execute case monitoring logic."""
        action = kwargs.get('action', 'get_queue_summary')
        case_id = kwargs.get('case_id')
        case_number = kwargs.get('case_number')
        hours_lookback = kwargs.get('hours_lookback', 24)
        priority_filter = kwargs.get('priority_filter')
        include_attachments = kwargs.get('include_attachments', True)
        max_results = kwargs.get('max_results', 50)

        try:
            if self.config["use_mock_data"]:
                result = self._handle_mock_request(
                    action, case_id, case_number, hours_lookback,
                    priority_filter, include_attachments, max_results
                )
            else:
                result = self._handle_live_request(
                    action, case_id, case_number, hours_lookback,
                    priority_filter, include_attachments, max_results
                )

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"CarrierSFCaseMonitor error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "status": "failed"
            }, indent=2)

    def _handle_mock_request(
        self, action: str, case_id: str, case_number: str,
        hours_lookback: int, priority_filter: str,
        include_attachments: bool, max_results: int
    ) -> Dict:
        """Handle request using stubbed data."""
        
        if action == "get_new_cases":
            cases = STUBBED_CASES["new_cases"]
            if priority_filter:
                cases = [c for c in cases if c["Priority"] == priority_filter]
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "count": len(cases),
                "cases": cases[:max_results],
                "query_params": {
                    "hours_lookback": hours_lookback,
                    "priority_filter": priority_filter
                }
            }

        elif action == "get_aging_cases":
            cases = STUBBED_CASES["aging_cases"]
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "count": len(cases),
                "cases": cases[:max_results],
                "warning": "These cases are approaching or past SLA deadline"
            }

        elif action == "get_untriaged_cases":
            all_cases = STUBBED_CASES["new_cases"] + STUBBED_CASES["aging_cases"]
            untriaged = [c for c in all_cases if c.get("Triage_Status__c") is None]
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "count": len(untriaged),
                "cases": untriaged[:max_results]
            }

        elif action == "get_case_details":
            # Find case by ID or number
            all_cases = STUBBED_CASES["new_cases"] + STUBBED_CASES["aging_cases"]
            case = None
            for c in all_cases:
                if case_id and c["Id"] == case_id:
                    case = c
                    break
                if case_number and c["CaseNumber"] == case_number:
                    case = c
                    break
            
            if case:
                if not include_attachments:
                    case = {k: v for k, v in case.items() if k != "Attachments"}
                return {
                    "action": action,
                    "status": "success",
                    "source": "mock_data",
                    "case": case
                }
            else:
                return {
                    "action": action,
                    "status": "not_found",
                    "message": f"Case not found: {case_id or case_number}"
                }

        elif action == "get_case_history":
            # Mock case history/comments
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "case_id": case_id or case_number,
                "history": [
                    {
                        "field": "Status",
                        "old_value": None,
                        "new_value": "New",
                        "changed_by": "System",
                        "changed_date": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
                    }
                ],
                "comments": []
            }

        elif action == "get_queue_summary":
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "summary": STUBBED_CASES["queue_summary"],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "salesforce_instance": self.config["instance_url"]
            }

        else:
            return {
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _handle_live_request(
        self, action: str, case_id: str, case_number: str,
        hours_lookback: int, priority_filter: str,
        include_attachments: bool, max_results: int
    ) -> Dict:
        """
        Handle request using live Salesforce API.
        Uses the SalesforceClient from utils/salesforce_client.py
        """
        client = get_salesforce_client()
        
        if not client or not client.authenticate():
            return {
                "action": action,
                "status": "auth_failed",
                "message": "Salesforce authentication failed. Check credentials in environment variables.",
                "required_vars": [
                    "SALESFORCE_INSTANCE_URL",
                    "SALESFORCE_CLIENT_ID",
                    "SALESFORCE_CLIENT_SECRET",
                    "SALESFORCE_USERNAME",
                    "SALESFORCE_PASSWORD",
                    "SALESFORCE_SECURITY_TOKEN"
                ]
            }
        
        try:
            if action == "get_new_cases":
                cases = client.get_new_cases(limit=max_results)
                # Filter by priority if specified
                if priority_filter:
                    cases = [c for c in cases if c.get('Priority') == priority_filter]
                
                # Get attachments if requested
                if include_attachments:
                    for case in cases:
                        case['Attachments'] = client.get_case_attachments(case['Id'])
                
                return {
                    "action": action,
                    "status": "success",
                    "source": "salesforce_live",
                    "instance": client.instance_url,
                    "count": len(cases),
                    "cases": cases,
                    "query_params": {
                        "hours_lookback": hours_lookback,
                        "priority_filter": priority_filter
                    }
                }

            elif action == "get_aging_cases":
                cases = client.get_aging_cases(threshold_hours=4, limit=max_results)
                
                if include_attachments:
                    for case in cases:
                        case['Attachments'] = client.get_case_attachments(case['Id'])
                
                return {
                    "action": action,
                    "status": "success",
                    "source": "salesforce_live",
                    "instance": client.instance_url,
                    "count": len(cases),
                    "cases": cases,
                    "warning": "These cases are approaching or past SLA deadline"
                }

            elif action == "get_untriaged_cases":
                # Get both new and aging untriaged cases
                new_cases = client.get_new_cases(limit=max_results)
                aging_cases = client.get_aging_cases(limit=max_results)
                all_cases = new_cases + aging_cases
                # Deduplicate
                seen_ids = set()
                unique_cases = []
                for c in all_cases:
                    if c['Id'] not in seen_ids:
                        seen_ids.add(c['Id'])
                        unique_cases.append(c)
                
                return {
                    "action": action,
                    "status": "success",
                    "source": "salesforce_live",
                    "instance": client.instance_url,
                    "count": len(unique_cases),
                    "cases": unique_cases[:max_results]
                }

            elif action == "get_case_details":
                case = None
                if case_id:
                    case = client.get_case_details(case_id)
                elif case_number:
                    # Query by case number
                    result = client.query(f"SELECT Id FROM Case WHERE CaseNumber = '{case_number}'")
                    if result.get('records'):
                        case = client.get_case_details(result['records'][0]['Id'])
                
                if case:
                    if include_attachments:
                        case['Attachments'] = client.get_case_attachments(case['Id'])
                    return {
                        "action": action,
                        "status": "success",
                        "source": "salesforce_live",
                        "case": case
                    }
                else:
                    return {
                        "action": action,
                        "status": "not_found",
                        "message": f"Case not found: {case_id or case_number}"
                    }

            elif action == "get_case_history":
                comments = client.get_case_comments(case_id) if case_id else []
                return {
                    "action": action,
                    "status": "success",
                    "source": "salesforce_live",
                    "case_id": case_id or case_number,
                    "comments": comments
                }

            elif action == "get_queue_summary":
                # Build summary from live queries
                new_cases = client.get_new_cases(limit=100)
                aging_cases = client.get_aging_cases(limit=100)
                
                # Calculate summary stats
                all_cases = new_cases + aging_cases
                by_priority = {}
                by_type = {}
                for c in all_cases:
                    p = c.get('Priority', 'Medium')
                    t = c.get('Type', 'Other')
                    by_priority[p] = by_priority.get(p, 0) + 1
                    by_type[t] = by_type.get(t, 0) + 1
                
                return {
                    "action": action,
                    "status": "success",
                    "source": "salesforce_live",
                    "instance": client.instance_url,
                    "summary": {
                        "total_new": len(new_cases),
                        "total_aging": len(aging_cases),
                        "sla_at_risk": len([c for c in aging_cases if c.get('Priority') in ['Critical', 'High']]),
                        "by_priority": by_priority,
                        "by_type": by_type
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            else:
                return {
                    "action": action,
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logging.error(f"Salesforce API error: {str(e)}")
            return {
                "action": action,
                "status": "error",
                "message": f"Salesforce API error: {str(e)}"
            }

    def _build_soql_query(self, action: str, **kwargs) -> str:
        """Build SOQL query for the given action."""
        # This would be used in production to generate dynamic queries
        base_fields = """
            Id, CaseNumber, Subject, Description, Status, Priority,
            Type, Origin, CreatedDate, LastModifiedDate,
            Account.Id, Account.Name, Account.AccountNumber,
            Contact.Id, Contact.Name, Contact.Email, Contact.Phone,
            Product_Model__c, Serial_Number__c, Install_Date__c,
            Triage_Status__c, Triage_Summary__c, SLA_Deadline__c
        """
        
        attachment_subquery = """
            (SELECT Id, Name, ContentType, BodyLength FROM Attachments)
        """
        
        if action == "get_new_cases":
            hours = kwargs.get("hours_lookback", 24)
            lookback = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
            return f"""
                SELECT {base_fields}, {attachment_subquery}
                FROM Case
                WHERE CreatedDate > {lookback}
                  AND Triage_Status__c = null
                ORDER BY Priority DESC, CreatedDate ASC
            """
        
        # Add more query builders as needed
        return ""
