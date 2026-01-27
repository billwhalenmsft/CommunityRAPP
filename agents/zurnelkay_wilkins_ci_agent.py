"""
Agent: ZurnElkay Wilkins Competitive Intelligence Agent
Purpose: Quarterly competitive intelligence for Wilkins business unit
Scope: Backflow Prevention, PRVs, TMVs
Customer: Zurn Elkay Water Solutions

This is a LEVEL 1 domain agent - source of truth for Wilkins category.
Treats Watts Water Technologies moves as portfolio-level strategy.

Competitors Monitored:
- Backflow: Watts, Ames, Febco, Powers (all Watts WWT), Apollo (Aalberts), Beeco
- PRVs: Watts, Cash Acme (Reliance), Caleffi, Apollo
- TMVs: Watts, Powers, Bradley (Watts WWT), Leonard (A.O. Smith), Lawler, Armstrong

Special Focus: Digital/smart valve technology, certifications, standards
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from agents.basic_agent import BasicAgent

# Web/API imports
try:
    import requests
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

# Azure OpenAI
try:
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    AZURE_AI_AVAILABLE = True
except ImportError:
    AZURE_AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZurnElkayWilkinsCIAgent(BasicAgent):
    """
    Wilkins Competitive Intelligence Agent for Zurn Elkay.
    
    Monitors Backflow Prevention, PRVs, and TMVs.
    Special focus on digital/smart valve technology and certification changes.
    """

    def __init__(self):
        self.name = 'WilkinsCIAgent'
        self.metadata = {
            "name": self.name,
            "description": """Wilkins Competitive Intelligence Agent for Zurn Elkay. Monitors Backflow Prevention, 
PRVs (Pressure Reducing Valves), and TMVs (Thermostatic Mixing Valves). Tracks Watts portfolio as 
primary threat. Special focus on digital/smart valve technology and certification changes.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "run_quarterly_analysis",
                            "analyze_competitor",
                            "check_parent_company_coordination",
                            "get_signal_summary",
                            "search_trade_publications",
                            "get_certification_changes",
                            "get_digital_innovation",
                            "get_leadership_changes",
                            "generate_bu_report"
                        ],
                        "description": "The competitive intelligence action to perform"
                    },
                    "competitor": {
                        "type": "string",
                        "description": "Specific competitor to analyze"
                    },
                    "parent_company": {
                        "type": "string",
                        "enum": ["Watts Water Technologies", "Aalberts", "Reliance", "A.O. Smith"],
                        "description": "Parent company to check for coordinated moves"
                    },
                    "product_family": {
                        "type": "string",
                        "enum": ["backflow", "prvs", "tmvs"],
                        "description": "Product family to focus analysis on"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["last_quarter", "last_90_days", "last_6_months", "ytd"],
                        "description": "Time period for analysis"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Competitor configuration
        self.competitors = {
            "backflow": {
                "primary": ["Watts", "Ames", "Febco", "Powers"],
                "secondary": ["Apollo", "Beeco"]
            },
            "prvs": {
                "primary": ["Watts", "Cash Acme", "Caleffi", "Apollo"],
                "secondary": []
            },
            "tmvs": {
                "primary": ["Watts", "Powers", "Bradley", "Leonard", "Lawler", "Armstrong"],
                "secondary": []
            }
        }
        
        # Parent company mapping
        self.parent_companies = {
            "Watts Water Technologies": ["Watts", "Ames", "Febco", "Powers", "Bradley", "Josam", "Haws"],
            "Aalberts": ["Apollo", "Lasco"],
            "Reliance": ["Cash Acme"],
            "A.O. Smith": ["Leonard"]
        }
        
        # Initialize simulated data
        self._init_simulated_data()
        
        # OpenAI client
        self.openai_client = None
        self._init_openai_client()

    def _init_openai_client(self):
        """Initialize Azure OpenAI client."""
        if not AZURE_AI_AVAILABLE:
            return
        try:
            endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
            api_key = os.environ.get('AZURE_OPENAI_API_KEY')
            if endpoint and api_key:
                self.openai_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
                )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")

    def _init_simulated_data(self):
        """Initialize simulated competitive intelligence data."""
        
        # Digital/Smart Valve Innovations
        self.simulated_digital_innovations = [
            {
                "competitor": "Caleffi",
                "product_family": "prvs",
                "innovation": "Digital PRV with Bluetooth Monitoring",
                "features": ["Mobile app for pressure monitoring", "Predictive maintenance alerts", "Historical data logging"],
                "target_market": "Facility managers, commercial buildings",
                "launch_date": "2025-10-15",
                "source": "Caleffi Press Release + PHCP Pros Review",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Caleffi challenging Watts on digital features - commoditizing smart PRVs"
            },
            {
                "competitor": "Watts",
                "parent_company": "Watts Water Technologies",
                "product_family": "backflow",
                "innovation": "Connected Backflow Platform",
                "features": ["Cloud-based test record management", "Automated compliance reporting", "BMS integration", "Real-time alerts"],
                "target_market": "Property managers, municipalities, healthcare",
                "launch_date": "2025-09-20",
                "source": "Watts Investor Day, PM Engineer",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Watts establishing ecosystem approach - moving beyond product to platform"
            },
            {
                "competitor": "Apollo",
                "parent_company": "Aalberts",
                "product_family": "backflow",
                "innovation": "IoT Product Development",
                "features": ["Evaluating IoT partnership"],
                "target_market": "Commercial",
                "launch_date": None,
                "source": "LinkedIn posting for IoT product manager",
                "confidence": "low",
                "signal_priority": 4,
                "implication": "Apollo may be entering digital valve space - monitor for announcements"
            }
        ]
        
        # Certification Changes
        self.simulated_certifications = [
            {
                "competitor": "Watts",
                "certification": "ASSE 1013",
                "product_line": "009M3 Series Reduced Pressure Zone Assembly",
                "date": "2025-11-08",
                "source": "ASSE Database + Watts Press",
                "confidence": "high",
                "signal_priority": 1
            },
            {
                "competitor": "Apollo",
                "certification": "ASSE 1015",
                "product_line": "4A-500 Double Check Valve",
                "date": "2025-10-22",
                "source": "ASSE Database",
                "confidence": "high",
                "signal_priority": 2
            },
            {
                "competitor": "Cash Acme",
                "parent_company": "Reliance",
                "certification": "NSF/ANSI 61",
                "product_line": "Lead-free PRV expansion",
                "date": "2025-09-15",
                "source": "NSF Database + Press",
                "confidence": "high",
                "signal_priority": 2
            }
        ]
        
        # Code/Standards Updates
        self.simulated_code_updates = [
            {
                "jurisdiction": "California",
                "update": "Stricter backflow testing requirements",
                "effective_date": "2026-01-01",
                "impact": "Increased testing frequency, documentation requirements",
                "source": "CA Plumbing Code Amendment",
                "confidence": "high",
                "implication": "Creates retrofit opportunity, may favor digital compliance tracking"
            },
            {
                "jurisdiction": "IAPMO UPC",
                "update": "Amendment A-2025: New provisions for reduced pressure zones",
                "effective_date": "2025-10-01",
                "impact": "Updated installation requirements",
                "source": "IAPMO",
                "confidence": "high",
                "implication": "May require product updates or recertification"
            }
        ]
        
        # Product Launches
        self.simulated_product_launches = [
            {
                "competitor": "Watts",
                "parent_company": "Watts Water Technologies",
                "product_family": "backflow",
                "product_name": "Bluetooth-enabled Backflow Assembly Series",
                "description": "Backflow assemblies with integrated Bluetooth diagnostics",
                "launch_date": "2025-11-01",
                "source": "Watts Press Release",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Watts continuing digital product leadership"
            },
            {
                "competitor": "Apollo",
                "parent_company": "Aalberts",
                "product_family": "backflow",
                "product_name": "Compact Double-Check Valve Retrofit Series",
                "description": "Targeting retrofit market with space-constrained installations",
                "launch_date": "2025-10-10",
                "source": "Supply House Times",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Apollo targeting retrofit niche"
            },
            {
                "competitor": "Powers",
                "parent_company": "Watts Water Technologies",
                "product_family": "tmvs",
                "product_name": "Healthcare TMV Solution",
                "description": "Coordinated launch with Bradley for hospital bathroom renovations",
                "launch_date": "2025-09-25",
                "source": "Watts Press Release",
                "confidence": "medium",
                "signal_priority": 2,
                "implication": "Watts coordinating Powers + Bradley for healthcare vertical"
            }
        ]
        
        # Leadership Changes
        self.simulated_leadership = [
            {
                "competitor": "Leonard",
                "parent_company": "A.O. Smith",
                "person": "Jennifer Walsh",
                "previous_role": "Director of Regulatory Affairs, Watts",
                "new_role": "VP Regulatory & Compliance, Leonard",
                "date": "2025-10-01",
                "source": "LinkedIn + Press",
                "confidence": "medium",
                "signal_priority": 3,
                "implication": "Leonard investing in regulatory capabilities - may signal certification push"
            }
        ]
        
        # Parent Company Coordination
        self.simulated_coordination = {
            "Watts Water Technologies": [
                {
                    "signal": "Digital Platform Integration",
                    "brands_involved": ["Watts", "Powers", "Bradley"],
                    "description": "Unified digital platform across valve products - shared app, cloud backend",
                    "date": "2025-09-01",
                    "source": "WTS Q3 earnings call",
                    "confidence": "high",
                    "implication": "Watts building ecosystem lock-in across product categories"
                },
                {
                    "signal": "Brand Consolidation - Febco",
                    "brands_involved": ["Watts", "Febco"],
                    "description": "Febco products appearing under 'Watts Backflow' branding",
                    "date": "2025-10-15",
                    "source": "Updated catalogs, distributor communications",
                    "confidence": "high",
                    "implication": "Watts simplifying brand architecture - may create rep relationship opportunities"
                },
                {
                    "signal": "Healthcare Vertical Coordination",
                    "brands_involved": ["Powers", "Bradley"],
                    "description": "Joint TMV + accessory packages for hospital renovations",
                    "date": "2025-09-20",
                    "source": "Watts marketing materials",
                    "confidence": "medium",
                    "implication": "Watts targeting healthcare with bundled solutions"
                }
            ],
            "Aalberts": [
                {
                    "signal": "Potential IoT Investment",
                    "brands_involved": ["Apollo"],
                    "description": "Job postings suggest IoT product development",
                    "date": "2025-11-01",
                    "source": "LinkedIn job postings",
                    "confidence": "low",
                    "implication": "Apollo may be entering digital space - monitor for product announcements"
                }
            ]
        }

    def perform(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute the requested competitive intelligence action."""
        actions = {
            "run_quarterly_analysis": self._run_quarterly_analysis,
            "analyze_competitor": self._analyze_competitor,
            "check_parent_company_coordination": self._check_parent_company_coordination,
            "get_signal_summary": self._get_signal_summary,
            "search_trade_publications": self._search_trade_publications,
            "get_certification_changes": self._get_certification_changes,
            "get_digital_innovation": self._get_digital_innovation,
            "get_leadership_changes": self._get_leadership_changes,
            "generate_bu_report": self._generate_bu_report
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available_actions": list(actions.keys())}
        
        try:
            return actions[action](**kwargs)
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return {"error": str(e), "action": action}

    def _run_quarterly_analysis(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Execute full quarterly competitive intelligence analysis."""
        logger.info(f"Running Wilkins quarterly analysis: {time_period}")
        
        # Gather all data
        digital = self._get_digital_innovation()
        certs = self._get_certification_changes()
        launches = self._get_product_launches()
        
        # Build top signals
        all_signals = []
        
        for d in digital.get("innovations", []):
            all_signals.append({
                "type": "digital_innovation",
                "priority": d.get("signal_priority", 5),
                "confidence": d.get("confidence"),
                "description": f"{d['competitor']}: {d['innovation']}",
                "implication": d.get("implication")
            })
        
        for c in certs.get("certifications", []):
            all_signals.append({
                "type": "certification",
                "priority": c.get("signal_priority", 5),
                "confidence": c.get("confidence"),
                "description": f"{c['competitor']}: {c['certification']} for {c['product_line']}",
                "implication": "Certification activity signals regulatory focus"
            })
        
        all_signals.sort(key=lambda x: x["priority"])
        
        return {
            "report_type": "Quarterly Competitive Intelligence",
            "business_unit": "Wilkins",
            "period": time_period,
            "generated_at": datetime.now().isoformat(),
            
            "highlights_by_product_family": {
                "backflow": {
                    "key_development": "Watts Bluetooth-enabled assemblies + connected platform",
                    "competitive_dynamic": "Digital capabilities becoming table stakes"
                },
                "prvs": {
                    "key_development": "Caleffi Bluetooth PRV challenging Watts digital leadership",
                    "competitive_dynamic": "Smart valve features commoditizing"
                },
                "tmvs": {
                    "key_development": "Watts Powers/Bradley healthcare coordination",
                    "competitive_dynamic": "Vertical-specific bundled solutions emerging"
                }
            },
            
            "top_3_significant_changes": all_signals[:3],
            
            "code_updates": self.simulated_code_updates,
            
            "implications": {
                "near_term": "Digital/smart valve features becoming spec requirements in key verticals",
                "mid_term": "Watts brand consolidation may create distributor relationship opportunities"
            },
            
            "watch_list": [
                "Watts Q4 earnings - digital revenue breakout",
                "California code implementation (Jan 2026)",
                "Apollo IoT product announcement (if any)"
            ]
        }

    def _analyze_competitor(self, competitor: str, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Deep dive analysis on specific competitor."""
        logger.info(f"Analyzing competitor: {competitor}")
        
        parent = None
        for p, brands in self.parent_companies.items():
            if competitor in brands:
                parent = p
                break
        
        # Special handling for Watts - it's a portfolio play
        if parent == "Watts Water Technologies":
            return self._analyze_watts_portfolio(time_period)
        
        launches = [l for l in self.simulated_product_launches if l.get("competitor") == competitor]
        digital = [d for d in self.simulated_digital_innovations if d.get("competitor") == competitor]
        certs = [c for c in self.simulated_certifications if c.get("competitor") == competitor]
        
        return {
            "competitor": competitor,
            "parent_company": parent,
            "product_launches": launches,
            "digital_innovations": digital,
            "certifications": certs,
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_watts_portfolio(self, time_period: str) -> Dict[str, Any]:
        """Special analysis for Watts as portfolio player."""
        return {
            "competitor": "Watts Water Technologies",
            "analysis_type": "Portfolio Analysis",
            "note": "Watts must be analyzed as a portfolio - they coordinate across brands",
            
            "brands_in_scope": self.parent_companies["Watts Water Technologies"],
            
            "portfolio_strategy_signals": self.simulated_coordination.get("Watts Water Technologies", []),
            
            "financial_context": {
                "segment": "Water Safety & Flow Control",
                "q3_trend": "Connected Products revenue +18% YoY (simulated)",
                "r_and_d": "Increased investment noted in 10-K"
            },
            
            "strategic_interpretation": """Watts executing three-pronged strategy:
1. Brand simplification (Febco → Watts Backflow)
2. Digital differentiation (Connected platform across products)
3. Vertical market focus (Healthcare with Powers + Bradley)

This is coordinated enterprise strategy, not BU-level tactical moves.""",
            
            "implications_for_wilkins": [
                "Digital feature parity becoming urgent",
                "Healthcare vertical requires bundled solution approach",
                "Brand consolidation may create rep relationship opportunities"
            ],
            
            "generated_at": datetime.now().isoformat()
        }

    def _check_parent_company_coordination(self, parent_company: str, **kwargs) -> Dict[str, Any]:
        """Check for coordinated moves across parent company brands."""
        logger.info(f"Checking coordination: {parent_company}")
        
        if parent_company not in self.parent_companies:
            return {"error": f"Unknown parent: {parent_company}"}
        
        signals = self.simulated_coordination.get(parent_company, [])
        
        return {
            "parent_company": parent_company,
            "brands_monitored": self.parent_companies[parent_company],
            "coordination_signals": signals,
            "generated_at": datetime.now().isoformat()
        }

    def _get_signal_summary(self, product_family: str = None, **kwargs) -> Dict[str, Any]:
        """Get prioritized signal summary."""
        all_items = self.simulated_product_launches + self.simulated_digital_innovations
        
        if product_family:
            all_items = [i for i in all_items if i.get("product_family") == product_family]
        
        all_items.sort(key=lambda x: x.get("signal_priority", 5))
        
        return {
            "product_family": product_family or "all",
            "signals": all_items,
            "count": len(all_items)
        }

    def _search_trade_publications(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search trade publications."""
        # Simulated results
        return {
            "query": query,
            "results": [
                {"source": "PM Engineer", "title": f"Industry Coverage: {query}", "relevance": "high"},
                {"source": "PHCP Pros", "title": f"Product Review: {query}", "relevance": "medium"}
            ],
            "note": "Simulated results - production would use live API"
        }

    def _get_certification_changes(self, product_family: str = None, **kwargs) -> Dict[str, Any]:
        """Get certification and standards changes."""
        certs = self.simulated_certifications
        if product_family:
            certs = [c for c in certs if c.get("product_family") == product_family]
        
        return {
            "certifications": certs,
            "code_updates": self.simulated_code_updates,
            "standards_monitored": ["ASSE", "IAPMO", "CSA", "NSF"],
            "generated_at": datetime.now().isoformat()
        }

    def _get_digital_innovation(self, **kwargs) -> Dict[str, Any]:
        """Track digital/IoT/smart valve developments."""
        return {
            "innovations": self.simulated_digital_innovations,
            "feature_comparison": {
                "bluetooth": {"Caleffi": True, "Watts": True, "Apollo": False},
                "cloud_dashboard": {"Caleffi": False, "Watts": True, "Apollo": False},
                "mobile_app": {"Caleffi": True, "Watts": True, "Apollo": False},
                "bms_integration": {"Caleffi": False, "Watts": True, "Apollo": False}
            },
            "trend": "Digital features transitioning from differentiator to baseline expectation",
            "generated_at": datetime.now().isoformat()
        }

    def _get_leadership_changes(self, **kwargs) -> Dict[str, Any]:
        """Get leadership changes."""
        return {
            "changes": self.simulated_leadership,
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_product_launches(self, **kwargs) -> Dict[str, Any]:
        """Get product launches."""
        return {
            "launches": self.simulated_product_launches,
            "generated_at": datetime.now().isoformat()
        }

    def _generate_bu_report(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Generate BU report for GM/PM distribution."""
        analysis = self._run_quarterly_analysis(time_period)
        
        return {
            "report_title": "WILKINS COMPETITIVE INTELLIGENCE REPORT",
            "period": time_period,
            "prepared_for": "GM/PM Review",
            
            "executive_summary": """Watts Water Technologies continues portfolio consolidation while 
accelerating digital/smart valve capabilities. Caleffi emerging as credible digital challenger. 
Standards activity elevated with California code changes creating market dynamics.""",
            
            "key_observation": """Watts treating their valve portfolio as an integrated platform play - 
brand consolidation + digital features + healthcare vertical focus. This is coordinated enterprise 
strategy, not BU-level tactical moves.""",
            
            "highlights": analysis["highlights_by_product_family"],
            "top_changes": analysis["top_3_significant_changes"],
            "implications": analysis["implications"],
            "watch_list": analysis["watch_list"],
            
            "sources": [
                "1. Watts Q3 Investor Presentation - digital strategy",
                "2. ASSE Certification Database - verified certifications",
                "3. PM Engineer - product coverage",
                "4. California Plumbing Code updates",
                "Note: Third-party sources prioritized"
            ],
            
            "generated_at": datetime.now().isoformat()
        }
