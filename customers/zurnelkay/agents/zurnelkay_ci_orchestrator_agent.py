"""
Zurn Elkay CI Orchestrator Agent
Level 0 - Master orchestrator for the entire CI system

This agent coordinates all Level 1 BU agents and the Level 2 Synthesizer,
manages workflow execution, validates quality, and produces final deliverables.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.basic_agent import BasicAgent

# Import all managed agents
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent
from agents.zurnelkay_crossbu_synthesizer_agent import ZurnElkayCrossbuSynthesizerAgent


class ZurnElkayCIOrchestratorAgent(BasicAgent):
    """
    Level 0 Orchestrator for Zurn Elkay Competitive Intelligence System.
    
    Responsibilities:
    - Coordinate execution of all 5 BU agents
    - Manage the Synthesizer agent
    - Perform quality assurance validation
    - Handle errors and retries gracefully
    - Produce audit logs and system status
    - Execute quarterly and on-demand workflows
    """
    
    def __init__(self, azure_openai_client=None, model_name: str = "gpt-4"):
        super().__init__(azure_openai_client, model_name)
        self.logger = logging.getLogger(__name__)
        
        # Initialize all managed agents
        self.bu_agents = {
            "drains": ZurnElkayDrainsCIAgent(azure_openai_client, model_name),
            "wilkins": ZurnElkayWilkinsCIAgent(azure_openai_client, model_name),
            "drinking_water": ZurnElkayDrinkingWaterCIAgent(azure_openai_client, model_name),
            "sinks": ZurnElkaySinksCIAgent(azure_openai_client, model_name),
            "commercial_brass": ZurnElkayCommercialBrassCIAgent(azure_openai_client, model_name)
        }
        
        self.synthesizer = ZurnElkayCrossbuSynthesizerAgent(azure_openai_client, model_name)
        
        # Quality check requirements
        self.required_bu_fields = [
            "report_title", "business_unit", "executive_summary",
            "top_3_significant_changes", "sources", "generated_at"
        ]
        
        self.required_synthesis_fields = [
            "enterprise_summary", "cross_bu_patterns", 
            "top_5_enterprise_signals", "generated_at"
        ]
        
        self.required_briefing_fields = [
            "executive_summary", "critical_findings",
            "strategic_recommendations", "generated_at"
        ]
        
        self.valid_confidence_values = ["high", "medium", "low"]
        
        # Workflow execution log
        self.execution_log = []
        
        # System status tracking
        self.last_quarterly_run = None
        self.last_health_check = None
        self.agent_health = {}
        
    def get_actions(self) -> List[str]:
        """Return list of available orchestrator actions."""
        return [
            "run_quarterly_workflow",
            "run_bu_report",
            "health_check",
            "validate_report",
            "get_system_status",
            "get_execution_log",
            "run_parent_company_alert",
            "retry_failed_step"
        ]
    
    def _log_execution(self, step: str, status: str, details: Dict = None):
        """Log workflow execution step."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details or {}
        }
        self.execution_log.append(entry)
        self.logger.info(f"Orchestrator: {step} - {status}")
        
    # =========================================================================
    # HEALTH CHECK ACTIONS
    # =========================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all managed agents.
        Returns status of each agent and overall system health.
        """
        self._log_execution("health_check", "started")
        
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "bu_agents": {},
            "synthesizer": {},
            "overall_status": "healthy",
            "issues": []
        }
        
        # Check each BU agent
        for bu_name, agent in self.bu_agents.items():
            try:
                # Verify agent has required methods
                required_methods = ["get_competitive_landscape", "get_quarterly_report"]
                missing_methods = [m for m in required_methods if not hasattr(agent, m)]
                
                if missing_methods:
                    health_results["bu_agents"][bu_name] = {
                        "status": "unhealthy",
                        "error": f"Missing methods: {missing_methods}"
                    }
                    health_results["issues"].append(f"BU agent {bu_name} missing methods")
                else:
                    health_results["bu_agents"][bu_name] = {
                        "status": "healthy",
                        "available_actions": agent.get_actions() if hasattr(agent, 'get_actions') else []
                    }
            except Exception as e:
                health_results["bu_agents"][bu_name] = {
                    "status": "error",
                    "error": str(e)
                }
                health_results["issues"].append(f"BU agent {bu_name} error: {str(e)}")
        
        # Check synthesizer
        try:
            required_methods = ["synthesize_quarterly_report", "generate_executive_briefing"]
            missing_methods = [m for m in required_methods if not hasattr(self.synthesizer, m)]
            
            if missing_methods:
                health_results["synthesizer"] = {
                    "status": "unhealthy",
                    "error": f"Missing methods: {missing_methods}"
                }
                health_results["issues"].append(f"Synthesizer missing methods")
            else:
                health_results["synthesizer"] = {
                    "status": "healthy",
                    "available_actions": self.synthesizer.get_actions()
                }
        except Exception as e:
            health_results["synthesizer"] = {
                "status": "error",
                "error": str(e)
            }
            health_results["issues"].append(f"Synthesizer error: {str(e)}")
        
        # Determine overall status
        if health_results["issues"]:
            health_results["overall_status"] = "degraded" if len(health_results["issues"]) < 3 else "unhealthy"
        
        self.agent_health = health_results
        self.last_health_check = datetime.now()
        self._log_execution("health_check", "completed", {"status": health_results["overall_status"]})
        
        return health_results
    
    # =========================================================================
    # QUALITY VALIDATION ACTIONS
    # =========================================================================
    
    def validate_report(self, report: Dict, report_type: str) -> Dict[str, Any]:
        """
        Validate a report against quality requirements.
        
        Args:
            report: The report to validate
            report_type: One of 'bu_report', 'synthesis', 'executive_briefing'
            
        Returns:
            Validation result with issues if any
        """
        validation_result = {
            "is_valid": True,
            "report_type": report_type,
            "issues": [],
            "warnings": [],
            "validated_at": datetime.now().isoformat()
        }
        
        # Determine required fields based on report type
        if report_type == "bu_report":
            required_fields = self.required_bu_fields
        elif report_type == "synthesis":
            required_fields = self.required_synthesis_fields
        elif report_type == "executive_briefing":
            required_fields = self.required_briefing_fields
        else:
            validation_result["issues"].append(f"Unknown report type: {report_type}")
            validation_result["is_valid"] = False
            return validation_result
        
        # Check required fields
        for field in required_fields:
            if field not in report or report[field] is None:
                validation_result["issues"].append(f"Missing required field: {field}")
                validation_result["is_valid"] = False
            elif isinstance(report[field], str) and not report[field].strip():
                validation_result["issues"].append(f"Empty required field: {field}")
                validation_result["is_valid"] = False
        
        # Validate confidence values
        if "top_3_significant_changes" in report:
            for i, change in enumerate(report.get("top_3_significant_changes", [])):
                confidence = change.get("confidence_level", "").lower()
                if confidence and confidence not in self.valid_confidence_values:
                    validation_result["issues"].append(
                        f"Invalid confidence in change {i+1}: {confidence}"
                    )
                    validation_result["is_valid"] = False
        
        # Check for source attribution
        if report_type == "bu_report":
            sources = report.get("sources", {})
            total_sources = sum(len(v) if isinstance(v, list) else 1 for v in sources.values())
            if total_sources == 0:
                validation_result["warnings"].append("No sources cited in report")
        
        # Check confidence distribution (warn if all low)
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        for change in report.get("top_3_significant_changes", []):
            conf = change.get("confidence_level", "").lower()
            if conf in confidence_counts:
                confidence_counts[conf] += 1
        
        if confidence_counts["low"] > 0 and confidence_counts["high"] == 0 and confidence_counts["medium"] == 0:
            validation_result["warnings"].append("All changes have low confidence - consider additional verification")
        
        return validation_result
    
    def _validate_all_bu_reports(self, bu_reports: Dict[str, Dict]) -> Dict[str, Any]:
        """Validate all BU reports and aggregate results."""
        validation_summary = {
            "all_valid": True,
            "validated_count": 0,
            "failed_count": 0,
            "results": {}
        }
        
        for bu_name, report in bu_reports.items():
            result = self.validate_report(report, "bu_report")
            validation_summary["results"][bu_name] = result
            validation_summary["validated_count"] += 1
            
            if not result["is_valid"]:
                validation_summary["all_valid"] = False
                validation_summary["failed_count"] += 1
        
        return validation_summary
    
    # =========================================================================
    # WORKFLOW EXECUTION ACTIONS
    # =========================================================================
    
    def run_quarterly_workflow(self, quarter: str = None, year: int = None) -> Dict[str, Any]:
        """
        Execute the full quarterly CI workflow.
        
        Steps:
        1. Health check all agents
        2. Collect reports from all 5 BU agents
        3. Validate BU reports
        4. Run Cross-BU Synthesizer
        5. Validate synthesis
        6. Generate executive briefing
        7. Return final deliverable
        
        Args:
            quarter: Q1, Q2, Q3, or Q4 (defaults to current)
            year: Year (defaults to current)
        """
        # Determine quarter and year
        now = datetime.now()
        if not year:
            year = now.year
        if not quarter:
            month = now.month
            quarter = f"Q{(month - 1) // 3 + 1}"
        
        workflow_result = {
            "workflow": "quarterly_ci_report",
            "quarter": quarter,
            "year": year,
            "started_at": now.isoformat(),
            "status": "running",
            "steps_completed": [],
            "steps_failed": [],
            "bu_reports": {},
            "synthesis": None,
            "executive_briefing": None,
            "validation_results": {}
        }
        
        self._log_execution("run_quarterly_workflow", "started", {"quarter": quarter, "year": year})
        
        try:
            # Step 1: Health check
            self._log_execution("step_1_health_check", "started")
            health = self.health_check()
            
            if health["overall_status"] == "unhealthy":
                workflow_result["status"] = "failed"
                workflow_result["error"] = "System health check failed"
                workflow_result["steps_failed"].append("health_check")
                return workflow_result
            
            workflow_result["steps_completed"].append("health_check")
            
            # Step 2: Collect BU reports
            self._log_execution("step_2_collect_bu_reports", "started")
            for bu_name, agent in self.bu_agents.items():
                try:
                    report = agent.get_quarterly_report(quarter=quarter, year=year)
                    workflow_result["bu_reports"][bu_name] = report
                    self._log_execution(f"bu_report_{bu_name}", "completed")
                except Exception as e:
                    self._log_execution(f"bu_report_{bu_name}", "failed", {"error": str(e)})
                    workflow_result["steps_failed"].append(f"bu_report_{bu_name}")
            
            workflow_result["steps_completed"].append("collect_bu_reports")
            
            # Step 3: Validate BU reports
            self._log_execution("step_3_validate_bu_reports", "started")
            bu_validation = self._validate_all_bu_reports(workflow_result["bu_reports"])
            workflow_result["validation_results"]["bu_reports"] = bu_validation
            
            if not bu_validation["all_valid"]:
                self._log_execution("step_3_validate_bu_reports", "warning", 
                                   {"failed_count": bu_validation["failed_count"]})
            
            workflow_result["steps_completed"].append("validate_bu_reports")
            
            # Step 4: Run synthesizer
            self._log_execution("step_4_synthesize", "started")
            synthesis = self.synthesizer.synthesize_quarterly_report(quarter=quarter, year=year)
            workflow_result["synthesis"] = synthesis
            workflow_result["steps_completed"].append("synthesize")
            
            # Step 5: Validate synthesis
            self._log_execution("step_5_validate_synthesis", "started")
            synthesis_validation = self.validate_report(synthesis, "synthesis")
            workflow_result["validation_results"]["synthesis"] = synthesis_validation
            workflow_result["steps_completed"].append("validate_synthesis")
            
            # Step 6: Generate executive briefing
            self._log_execution("step_6_executive_briefing", "started")
            briefing = self.synthesizer.generate_executive_briefing(quarter=quarter, year=year)
            workflow_result["executive_briefing"] = briefing
            
            # Validate briefing
            briefing_validation = self.validate_report(briefing, "executive_briefing")
            workflow_result["validation_results"]["executive_briefing"] = briefing_validation
            workflow_result["steps_completed"].append("generate_executive_briefing")
            
            # Complete
            workflow_result["status"] = "completed"
            workflow_result["completed_at"] = datetime.now().isoformat()
            self.last_quarterly_run = datetime.now()
            
            self._log_execution("run_quarterly_workflow", "completed", {
                "steps_completed": len(workflow_result["steps_completed"]),
                "steps_failed": len(workflow_result["steps_failed"])
            })
            
        except Exception as e:
            workflow_result["status"] = "failed"
            workflow_result["error"] = str(e)
            self._log_execution("run_quarterly_workflow", "failed", {"error": str(e)})
        
        return workflow_result
    
    def run_bu_report(self, bu_name: str, quarter: str = None, year: int = None) -> Dict[str, Any]:
        """
        Execute a single BU agent on demand and validate output.
        
        Args:
            bu_name: One of drains, wilkins, drinking_water, sinks, commercial_brass
            quarter: Optional quarter specification
            year: Optional year specification
        """
        bu_name_lower = bu_name.lower().replace(" ", "_").replace("-", "_")
        
        if bu_name_lower not in self.bu_agents:
            return {
                "status": "error",
                "error": f"Unknown BU: {bu_name}. Valid options: {list(self.bu_agents.keys())}"
            }
        
        result = {
            "bu_name": bu_name_lower,
            "status": "running",
            "started_at": datetime.now().isoformat()
        }
        
        self._log_execution(f"run_bu_report_{bu_name_lower}", "started")
        
        try:
            agent = self.bu_agents[bu_name_lower]
            report = agent.get_quarterly_report(quarter=quarter, year=year)
            result["report"] = report
            
            # Validate
            validation = self.validate_report(report, "bu_report")
            result["validation"] = validation
            
            result["status"] = "completed" if validation["is_valid"] else "completed_with_warnings"
            result["completed_at"] = datetime.now().isoformat()
            
            self._log_execution(f"run_bu_report_{bu_name_lower}", "completed")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log_execution(f"run_bu_report_{bu_name_lower}", "failed", {"error": str(e)})
        
        return result
    
    def run_parent_company_alert(self, parent_company: str) -> Dict[str, Any]:
        """
        Check a specific parent company across all relevant BUs.
        Useful for tracking enterprise-level competitive moves.
        
        Args:
            parent_company: Name of parent company (e.g., "Watts", "Morris Group")
        """
        self._log_execution("run_parent_company_alert", "started", {"parent": parent_company})
        
        # Get the synthesizer's parent company summary
        summary = self.synthesizer.get_parent_company_summary(parent_company)
        
        # Add orchestrator metadata
        result = {
            "alert_type": "parent_company_check",
            "parent_company": parent_company,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "recommendation": self._generate_parent_company_recommendation(summary)
        }
        
        self._log_execution("run_parent_company_alert", "completed")
        return result
    
    def _generate_parent_company_recommendation(self, summary: Dict) -> str:
        """Generate actionable recommendation based on parent company activity."""
        if summary.get("status") == "not_found":
            return "No data available for this parent company. Consider expanding data collection."
        
        signals_count = len(summary.get("combined_signals", []))
        bus_affected = len(summary.get("bus_affected", []))
        
        if signals_count == 0:
            return "No recent signals detected. Continue routine monitoring."
        elif signals_count >= 3 and bus_affected >= 2:
            return "HIGH ACTIVITY: Multiple signals across multiple BUs. Recommend immediate cross-functional review to assess coordinated competitive strategy."
        elif signals_count >= 2:
            return "ELEVATED ACTIVITY: Multiple competitive signals detected. Schedule review within 2 weeks."
        else:
            return "ROUTINE: Single signal detected. Include in next quarterly review."
    
    # =========================================================================
    # SYSTEM STATUS AND LOGGING
    # =========================================================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status and metrics."""
        return {
            "system": "Zurn Elkay CI System",
            "orchestrator_version": "1.0.0",
            "status_as_of": datetime.now().isoformat(),
            "last_quarterly_run": self.last_quarterly_run.isoformat() if self.last_quarterly_run else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "agent_health_summary": self.agent_health.get("overall_status", "unknown"),
            "managed_agents": {
                "bu_agents": list(self.bu_agents.keys()),
                "synthesizer": "ZurnElkayCrossbuSynthesizerAgent"
            },
            "execution_log_entries": len(self.execution_log),
            "available_workflows": [
                "quarterly_ci_report",
                "on_demand_bu_report", 
                "parent_company_alert"
            ]
        }
    
    def get_execution_log(self, last_n: int = 20) -> List[Dict]:
        """Get recent execution log entries."""
        return self.execution_log[-last_n:]
    
    def retry_failed_step(self, step_name: str, **kwargs) -> Dict[str, Any]:
        """
        Retry a previously failed step.
        
        Args:
            step_name: Name of the step to retry
            **kwargs: Additional arguments for the step
        """
        self._log_execution("retry_failed_step", "started", {"step": step_name})
        
        # Map step names to actions
        step_mapping = {
            "health_check": self.health_check,
            "bu_report_drains": lambda: self.run_bu_report("drains", **kwargs),
            "bu_report_wilkins": lambda: self.run_bu_report("wilkins", **kwargs),
            "bu_report_drinking_water": lambda: self.run_bu_report("drinking_water", **kwargs),
            "bu_report_sinks": lambda: self.run_bu_report("sinks", **kwargs),
            "bu_report_commercial_brass": lambda: self.run_bu_report("commercial_brass", **kwargs),
        }
        
        if step_name not in step_mapping:
            return {
                "status": "error",
                "error": f"Unknown step: {step_name}. Valid steps: {list(step_mapping.keys())}"
            }
        
        try:
            result = step_mapping[step_name]()
            self._log_execution("retry_failed_step", "completed", {"step": step_name})
            return {
                "status": "success",
                "step": step_name,
                "result": result
            }
        except Exception as e:
            self._log_execution("retry_failed_step", "failed", {"step": step_name, "error": str(e)})
            return {
                "status": "failed",
                "step": step_name,
                "error": str(e)
            }
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    def get_quick_status(self) -> str:
        """Get a quick one-line status for the system."""
        health = self.agent_health.get("overall_status", "unknown")
        last_run = self.last_quarterly_run.strftime("%Y-%m-%d") if self.last_quarterly_run else "never"
        return f"System: {health} | Last quarterly: {last_run} | Agents: {len(self.bu_agents)} BU + 1 Synthesizer"
    
    def get_next_quarterly_date(self) -> str:
        """Calculate the next quarterly report date."""
        now = datetime.now()
        quarterly_dates = [
            (1, 15), (4, 15), (7, 15), (10, 15)
        ]
        
        for month, day in quarterly_dates:
            next_date = datetime(now.year, month, day)
            if next_date > now:
                return next_date.strftime("%B %d, %Y")
        
        # Next year Q1
        return datetime(now.year + 1, 1, 15).strftime("%B %d, %Y")


# Standalone execution for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    orchestrator = ZurnElkayCIOrchestratorAgent()
    
    print("=" * 60)
    print("ZURN ELKAY CI ORCHESTRATOR - SYSTEM TEST")
    print("=" * 60)
    
    # Quick status
    print(f"\n{orchestrator.get_quick_status()}")
    print(f"Next quarterly report: {orchestrator.get_next_quarterly_date()}")
    
    # Health check
    print("\n--- Health Check ---")
    health = orchestrator.health_check()
    print(f"Overall Status: {health['overall_status']}")
    for bu, status in health["bu_agents"].items():
        print(f"  {bu}: {status['status']}")
    print(f"  synthesizer: {health['synthesizer']['status']}")
    
    # Run single BU report
    print("\n--- Single BU Report (Drains) ---")
    drains_result = orchestrator.run_bu_report("drains")
    print(f"Status: {drains_result['status']}")
    if drains_result.get("validation"):
        print(f"Valid: {drains_result['validation']['is_valid']}")
    
    # Parent company alert
    print("\n--- Parent Company Alert (Watts) ---")
    watts_alert = orchestrator.run_parent_company_alert("Watts")
    print(f"BUs Affected: {watts_alert['summary'].get('bus_affected', [])}")
    print(f"Recommendation: {watts_alert['recommendation']}")
    
    # Full quarterly (commented out for quick testing)
    # print("\n--- Full Quarterly Workflow ---")
    # quarterly = orchestrator.run_quarterly_workflow()
    # print(f"Status: {quarterly['status']}")
    # print(f"Steps Completed: {quarterly['steps_completed']}")
    
    print("\n--- System Status ---")
    status = orchestrator.get_system_status()
    print(f"Managed Agents: {status['managed_agents']}")
    print(f"Available Workflows: {status['available_workflows']}")
