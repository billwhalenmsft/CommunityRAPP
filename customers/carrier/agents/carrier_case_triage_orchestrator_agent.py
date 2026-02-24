"""
Agent: CarrierCaseTriageOrchestratorAgent
Purpose: Orchestrates the full case triage workflow
Customer: Carrier

This is the MASTER AGENT that coordinates all other agents in the swarm:
1. SF Case Monitor - Get cases needing triage
2. Attachment Processor - Extract info from images/documents
3. Case Analyzer - AI-powered text analysis
4. Product Enrichment - Add product context (STUBBED)
5. Summary Generator - Create triage summary with recommendations
6. SF Writer - Write triage results back to Salesforce

Workflow:
1. Monitor → Get new/aging cases
2. For each case:
   a. Process attachments (if any)
   b. Analyze case text + attachment data
   c. Enrich with product info
   d. Generate triage summary
   e. Write results to Salesforce
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# Import swarm agents
from agents.carrier_sf_case_monitor_agent import CarrierSFCaseMonitorAgent
from agents.carrier_sf_writer_agent import CarrierSFWriterAgent
from agents.carrier_case_analyzer_agent import CarrierCaseAnalyzerAgent
from agents.carrier_summary_generator_agent import CarrierSummaryGeneratorAgent
from agents.carrier_attachment_processor_agent import CarrierAttachmentProcessorAgent
from agents.carrier_product_enrichment_agent import CarrierProductEnrichmentAgent

# =============================================================================
# ORCHESTRATOR CONFIGURATION
# =============================================================================
ORCHESTRATOR_CONFIG = {
    "use_mock_data": True,  # Set to False for production
    "max_cases_per_batch": 10,
    "enable_parallel_processing": False,  # Sequential for better logging
    "write_results_to_sf": True,
    "log_level": "INFO"
}

# =============================================================================
# WORKFLOW TEMPLATES
# =============================================================================
TRIAGE_WORKFLOW = [
    {"step": 1, "agent": "sf_case_monitor", "action": "get_case_details", "required": True},
    {"step": 2, "agent": "attachment_processor", "action": "process_attachments", "required": False},
    {"step": 3, "agent": "case_analyzer", "action": "full_analysis", "required": True},
    {"step": 4, "agent": "product_enrichment", "action": "full_enrichment", "required": False},
    {"step": 5, "agent": "summary_generator", "action": "generate_full_triage", "required": True},
    {"step": 6, "agent": "sf_writer", "action": "update_case_triage", "required": True}
]


class CarrierCaseTriageOrchestratorAgent(BasicAgent):
    """
    Master orchestrator for the Carrier Case Triage Agent Swarm.

    Coordinates 6 specialized agents to:
    - Monitor Salesforce for cases needing triage
    - Process case attachments (images, PDFs)
    - Analyze case text using AI
    - Enrich with product information
    - Generate structured triage summary
    - Write results back to Salesforce

    Capabilities:
    - triage_single_case: Full triage workflow for one case
    - triage_all_new_cases: Process all new untriaged cases
    - triage_aging_cases: Priority processing of aging cases
    - run_triage_batch: Custom batch of case IDs
    - get_triage_status: Check triage status summary
    """

    def __init__(self):
        self.name = 'CarrierCaseTriageOrchestrator'
        self.metadata = {
            "name": self.name,
            "description": "Master orchestrator for Carrier Case Triage. Coordinates 6 specialized agents to fully automate case triage: monitor cases, process attachments, analyze with AI, enrich with product data, generate summary, and write back to Salesforce.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Orchestration action to perform",
                        "enum": [
                            "triage_single_case",
                            "triage_all_new_cases",
                            "triage_aging_cases",
                            "run_triage_batch",
                            "get_triage_status",
                            "demo_full_workflow"
                        ]
                    },
                    "case_id": {
                        "type": "string",
                        "description": "Salesforce Case ID (for single case triage)"
                    },
                    "case_ids": {
                        "type": "array",
                        "description": "List of Case IDs (for batch triage)",
                        "items": {"type": "string"}
                    },
                    "max_cases": {
                        "type": "integer",
                        "description": "Maximum cases to process in batch",
                        "default": 10
                    },
                    "write_to_sf": {
                        "type": "boolean",
                        "description": "Whether to write results to Salesforce",
                        "default": True
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = ORCHESTRATOR_CONFIG

        # Initialize swarm agents
        self._initialize_swarm()

    def _initialize_swarm(self):
        """Initialize all agents in the swarm."""
        self.monitor_agent = CarrierSFCaseMonitorAgent()
        self.writer_agent = CarrierSFWriterAgent()
        self.analyzer_agent = CarrierCaseAnalyzerAgent()
        self.summary_agent = CarrierSummaryGeneratorAgent()
        self.attachment_agent = CarrierAttachmentProcessorAgent()
        self.product_agent = CarrierProductEnrichmentAgent()

        logging.info("Carrier Case Triage Swarm initialized with 6 agents")

    def perform(self, **kwargs) -> str:
        """Execute orchestration."""
        action = kwargs.get('action', 'get_triage_status')

        try:
            if action == "triage_single_case":
                result = self._triage_single_case(
                    case_id=kwargs.get('case_id'),
                    write_to_sf=kwargs.get('write_to_sf', True)
                )
            
            elif action == "triage_all_new_cases":
                result = self._triage_new_cases(
                    max_cases=kwargs.get('max_cases', 10),
                    write_to_sf=kwargs.get('write_to_sf', True)
                )
            
            elif action == "triage_aging_cases":
                result = self._triage_aging_cases(
                    max_cases=kwargs.get('max_cases', 10),
                    write_to_sf=kwargs.get('write_to_sf', True)
                )
            
            elif action == "run_triage_batch":
                result = self._run_batch(
                    case_ids=kwargs.get('case_ids', []),
                    write_to_sf=kwargs.get('write_to_sf', True)
                )
            
            elif action == "get_triage_status":
                result = self._get_triage_status()
            
            elif action == "demo_full_workflow":
                result = self._demo_full_workflow()
            
            else:
                result = {
                    "action": action,
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"Orchestrator error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "status": "failed"
            }, indent=2)

    def _triage_single_case(self, case_id: str, write_to_sf: bool = True) -> Dict:
        """Execute full triage workflow for a single case."""
        workflow_log = []
        start_time = datetime.now()

        logging.info(f"Starting triage for case: {case_id}")

        # Step 1: Get case details from Salesforce
        workflow_log.append({"step": 1, "agent": "sf_case_monitor", "action": "get_case_details"})
        case_result = json.loads(self.monitor_agent.perform(
            action="get_case_details",
            case_id=case_id
        ))
        
        if case_result.get('status') != 'success':
            return {
                "action": "triage_single_case",
                "status": "error",
                "case_id": case_id,
                "message": "Failed to retrieve case details",
                "details": case_result
            }

        case_data = case_result.get('case', {})
        workflow_log[-1]["result"] = "success"

        # Step 2: Process attachments if present
        attachments_data = {}
        if case_data.get('attachments'):
            workflow_log.append({"step": 2, "agent": "attachment_processor", "action": "process_attachments"})
            attachments_result = json.loads(self.attachment_agent.perform(
                action="process_attachments",
                case_id=case_id,
                attachments=case_data.get('attachments', [])
            ))
            attachments_data = attachments_result.get('summary', {})
            workflow_log[-1]["result"] = "success"
        else:
            workflow_log.append({"step": 2, "agent": "attachment_processor", "action": "skipped", "reason": "No attachments"})

        # Step 3: Analyze case text with AI
        workflow_log.append({"step": 3, "agent": "case_analyzer", "action": "full_analysis"})
        
        # Combine case text with attachment findings
        full_text = case_data.get('subject', '') + "\n\n" + case_data.get('description', '')
        if attachments_data.get('key_findings'):
            full_text += "\n\nAttachment Findings:\n" + "\n".join(attachments_data.get('key_findings', []))

        analysis_result = json.loads(self.analyzer_agent.perform(
            action="full_analysis",
            case_text=full_text,
            case_id=case_id
        ))
        analysis_data = analysis_result.get('analysis', {})
        workflow_log[-1]["result"] = "success"

        # Step 4: Enrich with product information
        workflow_log.append({"step": 4, "agent": "product_enrichment", "action": "full_enrichment"})
        
        # Extract model/serial from analysis
        product_refs = analysis_data.get('product_references', [])
        model = product_refs[0] if product_refs else ""
        
        enrichment_result = json.loads(self.product_agent.perform(
            action="full_enrichment",
            model=model,
            serial=case_data.get('serial_number', ''),
            account_id=case_data.get('account', {}).get('id', '')
        ))
        enrichment_data = enrichment_result
        workflow_log[-1]["result"] = "success"

        # Step 5: Generate triage summary
        workflow_log.append({"step": 5, "agent": "summary_generator", "action": "generate_full_triage"})
        
        summary_result = json.loads(self.summary_agent.perform(
            action="generate_full_triage",
            case_data=case_data,
            analysis=analysis_data,
            enrichment=enrichment_data,
            attachments=attachments_data
        ))
        triage_summary = summary_result.get('triage', {})
        workflow_log[-1]["result"] = "success"

        # Step 6: Write results to Salesforce
        sf_update_result = {}
        if write_to_sf:
            workflow_log.append({"step": 6, "agent": "sf_writer", "action": "update_case_triage"})
            
            sf_update_result = json.loads(self.writer_agent.perform(
                action="update_case_triage",
                case_id=case_id,
                triage_data={
                    "priority": triage_summary.get('priority', 'Medium'),
                    "issue_type": analysis_data.get('issue_type', 'General'),
                    "triage_summary": triage_summary.get('summary', ''),
                    "recommended_action": triage_summary.get('recommended_action', ''),
                    "recommended_queue": triage_summary.get('routing', {}).get('queue', 'General Support'),
                    "triage_status": "Completed"
                }
            ))
            workflow_log[-1]["result"] = "success" if sf_update_result.get('status') == 'success' else "failed"
        else:
            workflow_log.append({"step": 6, "agent": "sf_writer", "action": "skipped", "reason": "write_to_sf=False"})

        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "action": "triage_single_case",
            "status": "success",
            "case_id": case_id,
            "execution_time_seconds": duration,
            "workflow_log": workflow_log,
            "triage_result": {
                "case": {
                    "id": case_id,
                    "subject": case_data.get('subject'),
                    "account": case_data.get('account', {}).get('name')
                },
                "analysis": {
                    "issue_type": analysis_data.get('issue_type'),
                    "urgency": analysis_data.get('urgency'),
                    "sentiment": analysis_data.get('customer_sentiment'),
                    "products": analysis_data.get('product_references')
                },
                "enrichment": {
                    "product": enrichment_data.get('product', {}).get('full_name'),
                    "warranty": enrichment_data.get('warranty', {}).get('status'),
                    "known_issues": enrichment_data.get('known_issues', {}).get('bulletins_count', 0)
                },
                "triage": {
                    "priority": triage_summary.get('priority'),
                    "queue": triage_summary.get('routing', {}).get('queue'),
                    "recommended_action": triage_summary.get('recommended_action'),
                    "resolution_estimate": triage_summary.get('resolution_estimate')
                }
            },
            "sf_update": sf_update_result
        }

    def _triage_new_cases(self, max_cases: int = 10, write_to_sf: bool = True) -> Dict:
        """Process all new untriaged cases."""
        # Get new cases
        new_cases_result = json.loads(self.monitor_agent.perform(action="get_new_cases"))
        new_cases = new_cases_result.get('cases', [])[:max_cases]

        results = []
        for case in new_cases:
            case_result = self._triage_single_case(
                case_id=case.get('id'),
                write_to_sf=write_to_sf
            )
            results.append({
                "case_id": case.get('id'),
                "subject": case.get('subject'),
                "status": case_result.get('status'),
                "priority": case_result.get('triage_result', {}).get('triage', {}).get('priority')
            })

        return {
            "action": "triage_all_new_cases",
            "status": "success",
            "cases_found": len(new_cases_result.get('cases', [])),
            "cases_processed": len(results),
            "results": results
        }

    def _triage_aging_cases(self, max_cases: int = 10, write_to_sf: bool = True) -> Dict:
        """Priority processing of aging cases."""
        # Get aging cases
        aging_cases_result = json.loads(self.monitor_agent.perform(action="get_aging_cases"))
        aging_cases = aging_cases_result.get('cases', [])[:max_cases]

        results = []
        for case in aging_cases:
            case_result = self._triage_single_case(
                case_id=case.get('id'),
                write_to_sf=write_to_sf
            )
            results.append({
                "case_id": case.get('id'),
                "subject": case.get('subject'),
                "age_hours": case.get('age_hours'),
                "status": case_result.get('status'),
                "priority": case_result.get('triage_result', {}).get('triage', {}).get('priority')
            })

        return {
            "action": "triage_aging_cases",
            "status": "success",
            "aging_cases_found": len(aging_cases_result.get('cases', [])),
            "cases_processed": len(results),
            "results": results
        }

    def _run_batch(self, case_ids: List[str], write_to_sf: bool = True) -> Dict:
        """Process a custom batch of case IDs."""
        results = []
        for case_id in case_ids:
            case_result = self._triage_single_case(
                case_id=case_id,
                write_to_sf=write_to_sf
            )
            results.append({
                "case_id": case_id,
                "status": case_result.get('status'),
                "priority": case_result.get('triage_result', {}).get('triage', {}).get('priority')
            })

        return {
            "action": "run_triage_batch",
            "status": "success",
            "cases_requested": len(case_ids),
            "cases_processed": len(results),
            "results": results
        }

    def _get_triage_status(self) -> Dict:
        """Get overall triage status and queue summary."""
        # Get queue summary from monitor
        queue_result = json.loads(self.monitor_agent.perform(action="get_queue_summary"))
        queue_summary = queue_result.get('summary', {})

        return {
            "action": "get_triage_status",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "swarm_status": {
                "agents_active": 6,
                "agents": [
                    {"name": "SF Case Monitor", "status": "ready"},
                    {"name": "SF Writer", "status": "ready"},
                    {"name": "Case Analyzer", "status": "ready"},
                    {"name": "Summary Generator", "status": "ready"},
                    {"name": "Attachment Processor", "status": "ready"},
                    {"name": "Product Enrichment", "status": "ready (STUBBED)"}
                ]
            },
            "queue_summary": queue_summary,
            "recommendations": self._generate_recommendations(queue_summary)
        }

    def _generate_recommendations(self, queue_summary: Dict) -> List[str]:
        """Generate recommendations based on queue status."""
        recommendations = []
        
        aging = queue_summary.get('aging_cases', 0)
        new = queue_summary.get('new_cases', 0)
        untriaged = queue_summary.get('untriaged', 0)

        if aging > 0:
            recommendations.append(f"⚠️ {aging} aging case(s) detected - prioritize with 'triage_aging_cases'")
        
        if new > 5:
            recommendations.append(f"📥 {new} new cases awaiting triage - run 'triage_all_new_cases'")
        
        if untriaged > 10:
            recommendations.append(f"⏰ High volume: {untriaged} untriaged cases - consider batch processing")
        
        if not recommendations:
            recommendations.append("✅ Queue is healthy - no immediate action required")

        return recommendations

    def _demo_full_workflow(self) -> Dict:
        """Run a demonstration of the full triage workflow."""
        logging.info("Running full workflow demonstration...")

        # Use a sample case
        demo_case_id = "500xx000000JKL1AAA"

        # Run full triage
        result = self._triage_single_case(
            case_id=demo_case_id,
            write_to_sf=False  # Don't write during demo
        )

        return {
            "action": "demo_full_workflow",
            "status": "success",
            "message": "Demonstration completed successfully",
            "demo_mode": True,
            "note": "All data shown is MOCK DATA for demonstration purposes",
            "workflow_steps": [
                "1️⃣ SF Case Monitor → Retrieved case details",
                "2️⃣ Attachment Processor → Analyzed case attachments",
                "3️⃣ Case Analyzer → AI-powered text analysis",
                "4️⃣ Product Enrichment → Added product context (STUBBED)",
                "5️⃣ Summary Generator → Created triage summary",
                "6️⃣ SF Writer → Would update Salesforce (skipped for demo)"
            ],
            "result": result
        }
