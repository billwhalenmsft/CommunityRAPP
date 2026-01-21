"""
Agent: CarrierSummaryGeneratorAgent
Purpose: Creates structured triage summary and recommended next actions
Customer: Carrier
AI Model: Azure OpenAI GPT-4o
Demo Mode: Uses stubbed responses - replace with live AI calls for production

This agent:
- Synthesizes all extracted information into a coherent summary
- Generates recommended next actions
- Assigns final priority based on all factors
- Suggests routing to appropriate team/queue
- Estimates resolution time
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# =============================================================================
# CONFIGURATION
# =============================================================================
GENERATOR_CONFIG = {
    "use_mock_data": True,  # Set to False when Azure OpenAI is configured
    "model": "gpt-4o",
    "temperature": 0.5,
    "max_tokens": 2000
}

# Routing suggestions based on issue type and urgency
ROUTING_RULES = {
    "HVAC": {
        "Critical": "Tier 2 - Emergency HVAC Team",
        "High": "Tier 1 - HVAC Specialists",
        "Medium": "General Service Queue",
        "Low": "Self-Service / Knowledge Base"
    },
    "Controls": {
        "Critical": "Tier 2 - Controls Engineering",
        "High": "Tier 1 - Controls Support",
        "Medium": "Controls Support Queue",
        "Low": "Self-Service / Knowledge Base"
    },
    "Parts": {
        "Critical": "Parts Expedite Team",
        "High": "Parts Order Team",
        "Medium": "Parts Order Queue",
        "Low": "Self-Service Parts Portal"
    },
    "Warranty": {
        "Critical": "Warranty Claims - Urgent",
        "High": "Warranty Claims Team",
        "Medium": "Warranty Review Queue",
        "Low": "Warranty Self-Service"
    },
    "Maintenance": {
        "Critical": "Emergency Service Dispatch",
        "High": "Scheduled Service Team",
        "Medium": "Maintenance Contracts Queue",
        "Low": "Maintenance Planning"
    },
    "Installation": {
        "Critical": "Installation Emergency Team",
        "High": "Installation Support",
        "Medium": "Installation Queue",
        "Low": "Installation Planning"
    },
    "Other": {
        "Critical": "Tier 2 - General Support",
        "High": "Tier 1 - General Support",
        "Medium": "General Support Queue",
        "Low": "Self-Service Portal"
    }
}

# Resolution time estimates (in hours)
RESOLUTION_ESTIMATES = {
    "Critical": {"min": 2, "max": 8},
    "High": {"min": 4, "max": 24},
    "Medium": {"min": 24, "max": 72},
    "Low": {"min": 72, "max": 168}
}


class CarrierSummaryGeneratorAgent(BasicAgent):
    """
    Generates structured triage summary from analyzed case data.

    Capabilities:
    - Creates comprehensive case summary
    - Recommends specific next actions
    - Assigns final priority
    - Suggests team/queue routing
    - Estimates resolution timeline

    Demo Mode: Returns intelligent mock summaries
    Production: Uses Azure OpenAI GPT-4o for generation
    """

    def __init__(self):
        self.name = 'CarrierSummaryGenerator'
        self.metadata = {
            "name": self.name,
            "description": "Generates structured triage summaries with recommended actions and routing. Part of the Carrier Case Triage Agent Swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": [
                            "generate_triage_summary",
                            "recommend_next_action",
                            "assign_priority",
                            "suggest_routing",
                            "estimate_resolution_time",
                            "generate_full_triage"
                        ]
                    },
                    "case_data": {
                        "type": "object",
                        "description": "Case data including subject, description, account info"
                    },
                    "analysis_data": {
                        "type": "object",
                        "description": "Output from CarrierCaseAnalyzer agent"
                    },
                    "product_data": {
                        "type": "object",
                        "description": "Output from CarrierProductEnrichment agent"
                    },
                    "attachment_data": {
                        "type": "object",
                        "description": "Output from CarrierAttachmentProcessor agent"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = GENERATOR_CONFIG

    def perform(self, **kwargs) -> str:
        """Execute summary generation."""
        action = kwargs.get('action', 'generate_full_triage')

        try:
            if self.config["use_mock_data"]:
                result = self._handle_mock_request(action, **kwargs)
            else:
                result = self._handle_live_request(action, **kwargs)

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"CarrierSummaryGenerator error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "status": "failed"
            }, indent=2)

    def _handle_mock_request(self, action: str, **kwargs) -> Dict:
        """Handle request with mock responses."""
        case_data = kwargs.get('case_data', {})
        analysis_data = kwargs.get('analysis_data', {})
        product_data = kwargs.get('product_data', {})
        attachment_data = kwargs.get('attachment_data', {})

        if action == "generate_full_triage":
            return self._generate_full_triage(case_data, analysis_data, product_data, attachment_data)
        
        elif action == "generate_triage_summary":
            return self._generate_summary(case_data, analysis_data, product_data)
        
        elif action == "recommend_next_action":
            return self._recommend_action(analysis_data, product_data)
        
        elif action == "assign_priority":
            return self._assign_priority(analysis_data, product_data)
        
        elif action == "suggest_routing":
            return self._suggest_routing(analysis_data)
        
        elif action == "estimate_resolution_time":
            return self._estimate_resolution(analysis_data)
        
        else:
            return {
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _generate_full_triage(
        self,
        case_data: Dict,
        analysis_data: Dict,
        product_data: Dict,
        attachment_data: Dict
    ) -> Dict:
        """Generate complete triage output."""
        
        # Extract key information with defaults
        analysis = analysis_data.get('analysis', {})
        issue_type = analysis.get('issue_type', 'Other')
        urgency = analysis.get('urgency', {})
        urgency_level = urgency.get('level', 'Medium')
        urgency_factors = urgency.get('factors', [])
        products = analysis.get('products', {})
        symptoms = analysis.get('symptoms', [])
        customer_ask = analysis.get('customer_ask', 'Resolution needed')
        sentiment = analysis.get('sentiment', {})
        
        # Product enrichment data
        product_info = product_data.get('product', {})
        warranty_info = product_data.get('warranty', {})
        known_issues = product_data.get('known_issues', [])
        
        # Case info
        case_number = case_data.get('CaseNumber', 'Unknown')
        account_name = case_data.get('Account', {}).get('Name', 'Unknown Customer')
        account_type = case_data.get('Account', {}).get('Type', '')
        
        # Attachment findings
        attachment_findings = attachment_data.get('findings', [])
        
        # Determine final priority
        final_priority = self._calculate_final_priority(urgency_level, account_type, warranty_info)
        
        # Get routing suggestion
        routing = ROUTING_RULES.get(issue_type, ROUTING_RULES["Other"]).get(final_priority, "General Queue")
        
        # Get resolution estimate
        resolution_est = RESOLUTION_ESTIMATES.get(final_priority, {"min": 24, "max": 72})
        
        # Generate recommended action
        recommended_action = self._build_recommended_action(
            issue_type, symptoms, products, known_issues, warranty_info, customer_ask
        )
        
        # Build summary text
        summary_text = self._build_summary_text(
            case_number, account_name, issue_type, symptoms, products,
            urgency_factors, warranty_info, attachment_findings, customer_ask
        )
        
        return {
            "action": "generate_full_triage",
            "status": "success",
            "source": "mock_data",
            "triage_result": {
                "case_number": case_number,
                "account_name": account_name,
                "triage_summary": summary_text,
                "issue_type": issue_type,
                "final_priority": final_priority,
                "urgency_factors": urgency_factors,
                "recommended_action": recommended_action,
                "routing_suggestion": routing,
                "estimated_resolution": {
                    "min_hours": resolution_est["min"],
                    "max_hours": resolution_est["max"],
                    "display": f"{resolution_est['min']}-{resolution_est['max']} hours"
                },
                "confidence_score": analysis.get('confidence_score', 0.85),
                "warranty_status": warranty_info.get('status', 'Unknown'),
                "known_issues_found": len(known_issues) > 0,
                "attachment_insights": attachment_findings[:3] if attachment_findings else [],
                "customer_sentiment": sentiment.get('classification', 'Neutral'),
                "triage_timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "salesforce_update": {
                "Triage_Summary__c": summary_text,
                "Triage_Status__c": "Completed",
                "AI_Recommended_Action__c": recommended_action,
                "AI_Priority__c": final_priority,
                "AI_Issue_Type__c": issue_type,
                "AI_Routing_Suggestion__c": routing,
                "AI_Confidence__c": analysis.get('confidence_score', 0.85)
            }
        }

    def _generate_summary(self, case_data: Dict, analysis_data: Dict, product_data: Dict) -> Dict:
        """Generate just the summary text."""
        analysis = analysis_data.get('analysis', {})
        
        summary_text = self._build_summary_text(
            case_data.get('CaseNumber', 'Unknown'),
            case_data.get('Account', {}).get('Name', 'Unknown'),
            analysis.get('issue_type', 'Other'),
            analysis.get('symptoms', []),
            analysis.get('products', {}),
            analysis.get('urgency', {}).get('factors', []),
            product_data.get('warranty', {}),
            [],
            analysis.get('customer_ask', 'Resolution needed')
        )
        
        return {
            "action": "generate_triage_summary",
            "status": "success",
            "source": "mock_data",
            "summary": summary_text
        }

    def _recommend_action(self, analysis_data: Dict, product_data: Dict) -> Dict:
        """Generate recommended next action."""
        analysis = analysis_data.get('analysis', {})
        
        action = self._build_recommended_action(
            analysis.get('issue_type', 'Other'),
            analysis.get('symptoms', []),
            analysis.get('products', {}),
            product_data.get('known_issues', []),
            product_data.get('warranty', {}),
            analysis.get('customer_ask', '')
        )
        
        return {
            "action": "recommend_next_action",
            "status": "success",
            "source": "mock_data",
            "recommended_action": action,
            "action_type": self._get_action_type(action),
            "requires_dispatch": "dispatch" in action.lower() or "technician" in action.lower()
        }

    def _assign_priority(self, analysis_data: Dict, product_data: Dict) -> Dict:
        """Calculate and assign final priority."""
        analysis = analysis_data.get('analysis', {})
        urgency_level = analysis.get('urgency', {}).get('level', 'Medium')
        warranty = product_data.get('warranty', {})
        
        final_priority = self._calculate_final_priority(urgency_level, '', warranty)
        
        return {
            "action": "assign_priority",
            "status": "success",
            "source": "mock_data",
            "original_urgency": urgency_level,
            "final_priority": final_priority,
            "adjustment_factors": self._get_priority_factors(urgency_level, warranty)
        }

    def _suggest_routing(self, analysis_data: Dict) -> Dict:
        """Suggest case routing."""
        analysis = analysis_data.get('analysis', {})
        issue_type = analysis.get('issue_type', 'Other')
        urgency_level = analysis.get('urgency', {}).get('level', 'Medium')
        
        routing = ROUTING_RULES.get(issue_type, ROUTING_RULES["Other"]).get(urgency_level, "General Queue")
        
        return {
            "action": "suggest_routing",
            "status": "success",
            "source": "mock_data",
            "issue_type": issue_type,
            "urgency_level": urgency_level,
            "suggested_queue": routing,
            "escalation_path": self._get_escalation_path(issue_type)
        }

    def _estimate_resolution(self, analysis_data: Dict) -> Dict:
        """Estimate resolution time."""
        analysis = analysis_data.get('analysis', {})
        urgency_level = analysis.get('urgency', {}).get('level', 'Medium')
        
        estimate = RESOLUTION_ESTIMATES.get(urgency_level, {"min": 24, "max": 72})
        
        return {
            "action": "estimate_resolution_time",
            "status": "success",
            "source": "mock_data",
            "priority": urgency_level,
            "estimated_hours": {
                "min": estimate["min"],
                "max": estimate["max"]
            },
            "display": f"{estimate['min']}-{estimate['max']} hours",
            "sla_deadline_hours": estimate["max"]
        }

    def _build_summary_text(
        self,
        case_number: str,
        account_name: str,
        issue_type: str,
        symptoms: List[str],
        products: Dict,
        urgency_factors: List[str],
        warranty: Dict,
        attachment_findings: List,
        customer_ask: str
    ) -> str:
        """Build the structured summary text."""
        
        # Get product info
        models = products.get('models', products.get('models_found', []))
        serials = products.get('serial_numbers', products.get('serials', []))
        error_codes = products.get('error_codes', [])
        
        # Build warranty line
        warranty_status = warranty.get('status', 'Unknown')
        warranty_expiry = warranty.get('expiry_date', '')
        warranty_line = f"{warranty_status}"
        if warranty_expiry:
            warranty_line += f" (Expires: {warranty_expiry})"
        
        summary_lines = [
            f"=== CASE TRIAGE SUMMARY ===",
            f"",
            f"CASE: {case_number}",
            f"CUSTOMER: {account_name}",
            f"",
            f"ISSUE TYPE: {issue_type}",
            f"CUSTOMER REQUEST: {customer_ask}",
            f""
        ]
        
        if models or serials:
            summary_lines.append("PRODUCT INFORMATION:")
            if models:
                summary_lines.append(f"  Model(s): {', '.join(models)}")
            if serials:
                summary_lines.append(f"  Serial(s): {', '.join(serials)}")
            if error_codes:
                summary_lines.append(f"  Error Code(s): {', '.join(error_codes)}")
            summary_lines.append(f"  Warranty: {warranty_line}")
            summary_lines.append("")
        
        if symptoms:
            summary_lines.append("SYMPTOMS IDENTIFIED:")
            for symptom in symptoms[:5]:
                summary_lines.append(f"  • {symptom}")
            summary_lines.append("")
        
        if urgency_factors:
            summary_lines.append("URGENCY FACTORS:")
            for factor in urgency_factors[:3]:
                summary_lines.append(f"  • {factor}")
            summary_lines.append("")
        
        if attachment_findings:
            summary_lines.append("ATTACHMENT INSIGHTS:")
            for finding in attachment_findings[:3]:
                summary_lines.append(f"  • {finding}")
            summary_lines.append("")
        
        summary_lines.append("=== END TRIAGE ===")
        
        return "\n".join(summary_lines)

    def _build_recommended_action(
        self,
        issue_type: str,
        symptoms: List[str],
        products: Dict,
        known_issues: List,
        warranty: Dict,
        customer_ask: str
    ) -> str:
        """Build specific recommended action."""
        
        error_codes = products.get('error_codes', [])
        warranty_status = warranty.get('status', 'Unknown')
        
        # Check for known issues first
        if known_issues:
            issue = known_issues[0]
            return f"Known issue match: {issue.get('bulletin_id', 'N/A')} - {issue.get('recommended_action', 'Follow service bulletin procedures')}"
        
        # Build action based on issue type and context
        if issue_type == "HVAC":
            if error_codes:
                return f"Dispatch technician - Error code {error_codes[0]} detected. Run diagnostic per service manual Section 5. Check compressor and refrigerant levels."
            elif any("not cooling" in s.lower() for s in symptoms):
                return "Schedule service call - Cooling system failure. Technician to check refrigerant charge, compressor operation, and airflow."
            else:
                return "Schedule diagnostic service call to assess HVAC unit performance."
        
        elif issue_type == "Controls":
            return "Engage Controls specialist - Review BMS integration settings and communication protocols. May require on-site configuration."
        
        elif issue_type == "Parts":
            return "Route to Parts team - Verify part numbers and availability. Check warranty coverage for parts replacement."
        
        elif issue_type == "Warranty":
            if warranty_status == "Active":
                return "Process warranty claim - Unit under active warranty. Expedite service dispatch at no charge to customer."
            else:
                return "Review warranty status - May require paid service. Contact customer to discuss options."
        
        elif issue_type == "Maintenance":
            if "quote" in customer_ask.lower():
                return "Generate maintenance contract quote based on equipment list. Route to Account Manager for pricing approval."
            else:
                return "Schedule preventive maintenance visit. Review equipment list and prepare service checklist."
        
        else:
            return "Review case details and assign to appropriate specialist based on customer requirements."

    def _calculate_final_priority(
        self,
        urgency_level: str,
        account_type: str,
        warranty: Dict
    ) -> str:
        """Calculate final priority considering all factors."""
        
        priority_score = {
            "Critical": 4,
            "High": 3,
            "Medium": 2,
            "Low": 1
        }.get(urgency_level, 2)
        
        # Boost for enterprise/healthcare accounts
        if "enterprise" in account_type.lower() or "healthcare" in account_type.lower():
            priority_score = min(4, priority_score + 1)
        
        # Boost for active warranty
        if warranty.get('status') == 'Active':
            priority_score = min(4, priority_score + 0.5)
        
        # Map back to level
        if priority_score >= 3.5:
            return "Critical"
        elif priority_score >= 2.5:
            return "High"
        elif priority_score >= 1.5:
            return "Medium"
        else:
            return "Low"

    def _get_priority_factors(self, urgency_level: str, warranty: Dict) -> List[str]:
        """Get factors affecting priority."""
        factors = [f"Base urgency: {urgency_level}"]
        if warranty.get('status') == 'Active':
            factors.append("Active warranty: +priority boost")
        return factors

    def _get_action_type(self, action: str) -> str:
        """Classify the action type."""
        action_lower = action.lower()
        if "dispatch" in action_lower or "service call" in action_lower:
            return "Dispatch"
        elif "quote" in action_lower:
            return "Quote"
        elif "warranty" in action_lower:
            return "Warranty"
        elif "specialist" in action_lower:
            return "Specialist"
        else:
            return "Review"

    def _get_escalation_path(self, issue_type: str) -> List[str]:
        """Get escalation path for issue type."""
        paths = {
            "HVAC": ["Tier 1 HVAC", "Tier 2 HVAC", "Engineering"],
            "Controls": ["Controls Support", "Controls Engineering", "Product Team"],
            "Parts": ["Parts Team", "Parts Expedite", "Supply Chain"],
            "Warranty": ["Warranty Claims", "Warranty Manager", "Legal"],
            "Other": ["General Support", "Supervisor", "Manager"]
        }
        return paths.get(issue_type, paths["Other"])

    def _handle_live_request(self, action: str, **kwargs) -> Dict:
        """Handle request using live Azure OpenAI."""
        return {
            "action": action,
            "status": "not_implemented",
            "message": "Live Azure OpenAI integration not yet configured."
        }
