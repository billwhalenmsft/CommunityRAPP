"""
Agent: CarrierSFWriterAgent
Purpose: Writes triage results back to Salesforce cases
Customer: Carrier
Data Sources: Salesforce Service Cloud (Cases)
Demo Mode: Uses stubbed responses - set use_mock_data=False for live Salesforce

Salesforce Instance: https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com/

Integration Points:
- Salesforce REST API v59.0: Case object updates
- OAuth 2.0 Username-Password flow for authentication
- Supports field updates, comments, and case routing

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
from datetime import datetime
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

# Custom fields that will be updated on Case object
TRIAGE_FIELDS = {
    "Triage_Summary__c": "Long Text Area (32000)",
    "Triage_Status__c": "Picklist: null, In Progress, Completed, Failed",
    "Triage_Date__c": "DateTime",
    "AI_Recommended_Action__c": "Text Area (1000)",
    "AI_Priority__c": "Picklist: Critical, High, Medium, Low",
    "AI_Routing_Suggestion__c": "Text (255)",
    "AI_Confidence__c": "Percent",
    "AI_Issue_Type__c": "Picklist: HVAC, Controls, Parts, Installation, Warranty, Other"
}


class CarrierSFWriterAgent(BasicAgent):
    """
    Writes triage results back to Salesforce cases.

    Integration Points:
    - Salesforce REST API v59.0 (PATCH for updates, POST for comments)
    - Case, CaseComment objects

    Demo Mode: Returns mock success responses
    Production: Connect to live Salesforce instance

    Salesforce Update Examples (for production):
        -- Update case with triage results
        PATCH /services/data/v59.0/sobjects/Case/{caseId}
        {
            "Triage_Summary__c": "...",
            "Triage_Status__c": "Completed",
            "AI_Recommended_Action__c": "...",
            "AI_Priority__c": "High"
        }

        -- Add internal comment
        POST /services/data/v59.0/sobjects/CaseComment
        {
            "ParentId": "{caseId}",
            "CommentBody": "...",
            "IsPublished": false
        }
    """

    def __init__(self):
        self.name = 'CarrierSFWriter'
        self.metadata = {
            "name": self.name,
            "description": "Writes AI triage results back to Salesforce cases. Updates custom fields, adds internal comments, and routes cases. Part of the Carrier Case Triage Agent Swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": [
                            "update_case_triage",
                            "set_case_priority",
                            "add_case_comment",
                            "update_custom_fields",
                            "route_case",
                            "bulk_update_cases"
                        ]
                    },
                    "case_id": {
                        "type": "string",
                        "description": "Salesforce Case ID (18-char)"
                    },
                    "triage_summary": {
                        "type": "string",
                        "description": "AI-generated triage summary to write to case"
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "AI-recommended next action"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Calculated priority level",
                        "enum": ["Critical", "High", "Medium", "Low"]
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Classified issue type",
                        "enum": ["HVAC", "Controls", "Parts", "Installation", "Warranty", "Other"]
                    },
                    "routing_suggestion": {
                        "type": "string",
                        "description": "Suggested queue or owner for the case"
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "AI confidence score (0.0 to 1.0)"
                    },
                    "comment_body": {
                        "type": "string",
                        "description": "Internal comment text to add"
                    },
                    "is_published": {
                        "type": "boolean",
                        "description": "Whether comment is visible to customer",
                        "default": False
                    },
                    "new_owner_id": {
                        "type": "string",
                        "description": "User or Queue ID for case assignment"
                    },
                    "cases": {
                        "type": "array",
                        "description": "Array of case updates for bulk operation",
                        "items": {
                            "type": "object"
                        }
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = SALESFORCE_CONFIG

    def perform(self, **kwargs) -> str:
        """Execute case write operations."""
        action = kwargs.pop('action', 'update_case_triage')
        case_id = kwargs.get('case_id')

        try:
            if self.config["use_mock_data"]:
                result = self._handle_mock_request(action, **kwargs)
            else:
                result = self._handle_live_request(action, **kwargs)

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"CarrierSFWriter error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "case_id": case_id,
                "status": "failed"
            }, indent=2)

    def _handle_mock_request(self, action: str, **kwargs) -> Dict:
        """Handle request with mock responses."""
        case_id = kwargs.get('case_id', '500xx000000ABC001')
        timestamp = datetime.utcnow().isoformat() + "Z"

        if action == "update_case_triage":
            triage_summary = kwargs.get('triage_summary', '')
            recommended_action = kwargs.get('recommended_action', '')
            priority = kwargs.get('priority', 'Medium')
            issue_type = kwargs.get('issue_type', 'Other')
            routing_suggestion = kwargs.get('routing_suggestion', '')
            confidence_score = kwargs.get('confidence_score', 0.85)

            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "case_id": case_id,
                "fields_updated": {
                    "Triage_Summary__c": triage_summary[:100] + "..." if len(triage_summary) > 100 else triage_summary,
                    "Triage_Status__c": "Completed",
                    "Triage_Date__c": timestamp,
                    "AI_Recommended_Action__c": recommended_action,
                    "AI_Priority__c": priority,
                    "AI_Issue_Type__c": issue_type,
                    "AI_Routing_Suggestion__c": routing_suggestion,
                    "AI_Confidence__c": confidence_score
                },
                "timestamp": timestamp,
                "message": f"Case {case_id} triage completed successfully"
            }

        elif action == "set_case_priority":
            priority = kwargs.get('priority', 'Medium')
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "case_id": case_id,
                "old_priority": "Medium",
                "new_priority": priority,
                "timestamp": timestamp,
                "message": f"Case priority updated to {priority}"
            }

        elif action == "add_case_comment":
            comment_body = kwargs.get('comment_body', '')
            is_published = kwargs.get('is_published', False)
            
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "case_id": case_id,
                "comment_id": "00axx000000CMT001",
                "is_published": is_published,
                "comment_preview": comment_body[:100] + "..." if len(comment_body) > 100 else comment_body,
                "timestamp": timestamp,
                "message": "Comment added successfully"
            }

        elif action == "update_custom_fields":
            # Generic field update
            fields_to_update = {k: v for k, v in kwargs.items() 
                               if k not in ['action', 'case_id'] and v is not None}
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "case_id": case_id,
                "fields_updated": fields_to_update,
                "timestamp": timestamp
            }

        elif action == "route_case":
            new_owner_id = kwargs.get('new_owner_id', '')
            routing_suggestion = kwargs.get('routing_suggestion', '')
            
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "case_id": case_id,
                "new_owner_id": new_owner_id or "00Gxx000000QUEUE01",
                "routing_reason": routing_suggestion,
                "timestamp": timestamp,
                "message": f"Case routed to {routing_suggestion or 'default queue'}"
            }

        elif action == "bulk_update_cases":
            cases = kwargs.get('cases', [])
            results = []
            for i, case_update in enumerate(cases):
                results.append({
                    "case_id": case_update.get('case_id', f'500xx00000ABC{i:03d}'),
                    "status": "success"
                })
            
            return {
                "action": action,
                "status": "success",
                "source": "mock_data",
                "total_cases": len(cases),
                "successful": len(cases),
                "failed": 0,
                "results": results,
                "timestamp": timestamp
            }

        else:
            return {
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _handle_live_request(self, action: str, **kwargs) -> Dict:
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
        
        case_id = kwargs.get('case_id', '')
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        try:
            if action == "update_case_triage":
                # Build triage_data - support both dict format and individual params
                if 'triage_data' in kwargs:
                    triage_data = kwargs['triage_data']
                else:
                    triage_data = {
                        'triage_summary': kwargs.get('triage_summary', ''),
                        'recommended_action': kwargs.get('recommended_action', ''),
                        'priority': kwargs.get('priority', 'Medium'),
                        'issue_type': kwargs.get('issue_type', 'Other'),
                        'recommended_queue': kwargs.get('routing_suggestion', ''),
                        'triage_status': 'Completed'
                    }
                
                # Use the client's triage update method
                result = client.update_case_triage(case_id, triage_data)
                
                if result.get('success'):
                    return {
                        "action": action,
                        "status": "success",
                        "source": "salesforce_live",
                        "instance": client.instance_url,
                        "case_id": case_id,
                        "fields_updated": triage_data,
                        "timestamp": timestamp,
                        "message": f"Case {case_id} triage completed successfully"
                    }
                else:
                    return {
                        "action": action,
                        "status": "error",
                        "case_id": case_id,
                        "error": result.get('error')
                    }

            elif action == "set_case_priority":
                priority = kwargs.get('priority', 'Medium')
                result = client.update_case(case_id, {"Priority": priority})
                
                return {
                    "action": action,
                    "status": "success" if result.get('success') else "error",
                    "source": "salesforce_live",
                    "case_id": case_id,
                    "new_priority": priority,
                    "timestamp": timestamp,
                    "error": result.get('error') if not result.get('success') else None
                }

            elif action == "add_case_comment":
                comment_body = kwargs.get('comment_body', '')
                is_published = kwargs.get('is_published', False)
                
                result = client.add_case_comment(case_id, comment_body, is_published)
                
                return {
                    "action": action,
                    "status": "success" if result.get('success') else "error",
                    "source": "salesforce_live",
                    "case_id": case_id,
                    "comment_id": result.get('id'),
                    "is_published": is_published,
                    "timestamp": timestamp,
                    "message": "Comment added successfully" if result.get('success') else result.get('error')
                }

            elif action == "update_custom_fields":
                fields_to_update = {k: v for k, v in kwargs.items() 
                                   if k not in ['action', 'case_id'] and v is not None}
                result = client.update_case(case_id, fields_to_update)
                
                return {
                    "action": action,
                    "status": "success" if result.get('success') else "error",
                    "source": "salesforce_live",
                    "case_id": case_id,
                    "fields_updated": fields_to_update,
                    "timestamp": timestamp,
                    "error": result.get('error') if not result.get('success') else None
                }

            elif action == "route_case":
                new_owner_id = kwargs.get('new_owner_id', '')
                routing_reason = kwargs.get('routing_suggestion', '')
                
                update_data = {"OwnerId": new_owner_id} if new_owner_id else {}
                if routing_reason:
                    update_data["Routing_Reason__c"] = routing_reason
                
                result = client.update_case(case_id, update_data)
                
                return {
                    "action": action,
                    "status": "success" if result.get('success') else "error",
                    "source": "salesforce_live",
                    "case_id": case_id,
                    "new_owner_id": new_owner_id,
                    "routing_reason": routing_reason,
                    "timestamp": timestamp
                }

            elif action == "bulk_update_cases":
                cases = kwargs.get('cases', [])
                results = []
                successful = 0
                failed = 0
                
                for case_update in cases:
                    cid = case_update.get('case_id')
                    triage_data = case_update.get('triage_data', {})
                    result = client.update_case_triage(cid, triage_data)
                    
                    if result.get('success'):
                        successful += 1
                        results.append({"case_id": cid, "status": "success"})
                    else:
                        failed += 1
                        results.append({"case_id": cid, "status": "error", "error": result.get('error')})
                
                return {
                    "action": action,
                    "status": "success",
                    "source": "salesforce_live",
                    "total_cases": len(cases),
                    "successful": successful,
                    "failed": failed,
                    "results": results,
                    "timestamp": timestamp
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
                "case_id": case_id,
                "message": f"Salesforce API error: {str(e)}"
            }

    def build_triage_update_payload(
        self,
        triage_summary: str,
        recommended_action: str,
        priority: str,
        issue_type: str,
        routing_suggestion: str,
        confidence_score: float
    ) -> Dict:
        """Build the Salesforce update payload for triage results."""
        return {
            "Triage_Summary__c": triage_summary,
            "Triage_Status__c": "Completed",
            "Triage_Date__c": datetime.utcnow().isoformat() + "Z",
            "AI_Recommended_Action__c": recommended_action,
            "AI_Priority__c": priority,
            "AI_Issue_Type__c": issue_type,
            "AI_Routing_Suggestion__c": routing_suggestion,
            "AI_Confidence__c": confidence_score
        }

    def build_internal_comment(self, triage_data: Dict) -> str:
        """Build internal comment text from triage data."""
        return f"""
=== AI TRIAGE RESULTS ===
Processed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Confidence: {triage_data.get('confidence_score', 0) * 100:.0f}%

ISSUE TYPE: {triage_data.get('issue_type', 'Unknown')}
PRIORITY: {triage_data.get('priority', 'Medium')}

SUMMARY:
{triage_data.get('triage_summary', 'No summary available')}

RECOMMENDED ACTION:
{triage_data.get('recommended_action', 'Review case manually')}

ROUTING SUGGESTION: {triage_data.get('routing_suggestion', 'Default Queue')}
=== END AI TRIAGE ===
        """.strip()
