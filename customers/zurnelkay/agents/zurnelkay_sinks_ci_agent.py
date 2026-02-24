"""
Agent: ZurnElkay Sinks Competitive Intelligence Agent
Purpose: Quarterly competitive intelligence for Elkay & Just Sinks business unit
Scope: Commercial Sinks, Healthcare/Patient Care, ADA Compliance
Customer: Zurn Elkay Water Solutions

This is a LEVEL 1 domain agent - source of truth for Sinks category.
Focus: Healthcare/infection control innovations, ADA compliance, commercial kitchen.

Competitors Monitored:
- Commercial Sinks: Just Manufacturing, Advance Tabco, Eagle, Regency, Vollrath
- Healthcare: Sloan (Rohl), Franke,?"Morris, T&S Brass
- Kitchen/Food Service: Just, Advance Tabco, John Boos, Eagle

Special Focus: Healthcare infection control innovations, ADA compliance,
commercial kitchen sustainability, Morris/Lixil/Franke coordination signals.
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


class ZurnElkaySinksCIAgent(BasicAgent):
    """
    Sinks Competitive Intelligence Agent for Zurn Elkay.
    
    Monitors Commercial Sinks, Healthcare/Patient Care, and Food Service.
    Special focus on healthcare infection control and ADA compliance.
    """

    def __init__(self):
        self.name = 'SinksCIAgent'
        self.metadata = {
            "name": self.name,
            "description": """Sinks Competitive Intelligence Agent for Zurn Elkay. Monitors Commercial Sinks, 
Healthcare/Patient Care, and Food Service applications. Special focus on healthcare infection control 
innovations, ADA compliance, and commercial kitchen sustainability requirements.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "run_quarterly_analysis",
                            "analyze_competitor",
                            "check_parent_company_coordination",
                            "get_healthcare_innovations",
                            "get_ada_compliance_updates",
                            "get_sustainability_updates",
                            "search_trade_publications",
                            "get_product_launches",
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
                        "enum": ["Morris Group", "Lixil", "Franke", "Illinois Tool Works"],
                        "description": "Parent company to check for coordinated moves"
                    },
                    "product_family": {
                        "type": "string",
                        "enum": ["commercial_sinks", "healthcare", "food_service"],
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
            "commercial_sinks": {
                "primary": ["Just Manufacturing", "Advance Tabco", "Eagle", "Regency"],
                "secondary": ["Vollrath", "BK Resources"]
            },
            "healthcare": {
                "primary": ["Sloan", "Franke", "T&S Brass"],
                "secondary": ["Chicago Faucets"]
            },
            "food_service": {
                "primary": ["Just Manufacturing", "Advance Tabco", "John Boos", "Eagle"],
                "secondary": ["Vollrath", "Regency"]
            }
        }
        
        # Parent company mapping - critical for coordination analysis
        self.parent_companies = {
            "Morris Group": ["Just Manufacturing", "T&S Brass", "Chicago Faucets"],
            "Lixil": ["Grohe", "American Standard"],
            "Franke": ["Franke Foodservice Systems"],
            "Illinois Tool Works": ["Sloan"]
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
        
        # Healthcare Infection Control Innovations
        self.simulated_healthcare_innovations = [
            {
                "competitor": "Sloan",
                "parent_company": "Illinois Tool Works",
                "product_family": "healthcare",
                "innovation": "Antimicrobial Sink System with CuVerro",
                "description": "Copper-infused sink surfaces with EPA-registered antimicrobial properties",
                "key_features": ["CuVerro copper alloy", "Continuous bacteria kill", "NSF certified"],
                "target_market": "Hospitals, ambulatory surgery centers",
                "launch_date": "2025-10-20",
                "source": "Sloan press release + Healthcare Facilities Today",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Sloan positioning for premium infection control segment"
            },
            {
                "competitor": "Franke",
                "parent_company": "Franke",
                "product_family": "healthcare",
                "innovation": "Contactless Scrub Sink Station",
                "description": "Full touchless surgical scrub station with foot and sensor controls",
                "key_features": ["100% touchless operation", "Integrated timing display", "Water conservation mode"],
                "target_market": "Operating rooms, surgical centers",
                "launch_date": "2025-09-15",
                "source": "Franke Foodservice press + LinkedIn product manager post",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Franke investing in healthcare vertical"
            },
            {
                "competitor": "T&S Brass",
                "parent_company": "Morris Group",
                "product_family": "healthcare",
                "innovation": "ChekPoint Hygiene System",
                "description": "Faucet + sink integration with hand hygiene compliance monitoring",
                "key_features": ["Compliance tracking", "Hand wash duration monitoring", "Dashboard integration"],
                "target_market": "Hospital hand hygiene programs",
                "launch_date": "2025-11-01",
                "source": "T&S Brass trade show demo + Healthcare Design",
                "confidence": "medium",
                "signal_priority": 2,
                "implication": "Morris Group (via T&S) entering hygiene compliance monitoring"
            }
        ]
        
        # ADA Compliance Updates
        self.simulated_ada_updates = [
            {
                "type": "Code Update",
                "jurisdiction": "Federal - DOJ",
                "update": "2025 ADA Accessibility Guidelines - Sink Requirements",
                "key_changes": [
                    "Updated knee clearance requirements",
                    "New insulation requirements for exposed pipes",
                    "Enhanced reach range specifications"
                ],
                "effective_date": "2026-03-15",
                "source": "Federal Register + ADA.gov",
                "confidence": "high",
                "implication": "Product redesign may be required for compliance"
            },
            {
                "competitor": "Just Manufacturing",
                "parent_company": "Morris Group",
                "type": "Product Certification",
                "certification": "ADA/ICC A117.1-2017",
                "product_line": "Full product line recertification",
                "date": "2025-10-01",
                "source": "Just Manufacturing catalog update",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Just staying ahead of accessibility requirements"
            }
        ]
        
        # Sustainability/Green Kitchen Updates
        self.simulated_sustainability = [
            {
                "competitor": "Advance Tabco",
                "initiative": "Green Kitchen Program",
                "description": "30% recycled stainless steel content certification",
                "certification": "SCS Global Services - Recycled Content",
                "date": "2025-10-15",
                "source": "Advance Tabco press + SCS database",
                "confidence": "high",
                "signal_priority": 2,
                "target_market": "LEED projects, corporate sustainability programs"
            },
            {
                "competitor": "Eagle",
                "initiative": "Water-Saving Sink Series",
                "description": "Integrated water recycling for pot wash stations",
                "features": ["Greywater recycling", "30% water reduction claims"],
                "date": "2025-09-20",
                "source": "Eagle press + Foodservice Equipment Reports",
                "confidence": "medium",
                "signal_priority": 3
            }
        ]
        
        # Product Launches
        self.simulated_product_launches = [
            {
                "competitor": "Just Manufacturing",
                "parent_company": "Morris Group",
                "product_family": "healthcare",
                "product_name": "Intellisink Healthcare Series",
                "description": "Smart patient care sinks with integrated monitoring",
                "key_features": ["Water temp monitoring", "Usage logging", "Infection control surfaces"],
                "target_market": "Patient rooms, long-term care",
                "launch_date": "2025-11-10",
                "source": "Just Manufacturing dealer preview + Healthcare Design",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Just entering smart/connected healthcare sink segment"
            },
            {
                "competitor": "Regency",
                "product_family": "food_service",
                "product_name": "Budget Line Commercial Sinks",
                "description": "Value-oriented commercial sink line for foodservice",
                "key_features": ["Entry price point", "Basic NSF compliance", "Standard sizes"],
                "target_market": "Small restaurants, budget-conscious operators",
                "launch_date": "2025-10-05",
                "source": "WebstaurantStore new listings + Regency catalog",
                "confidence": "high",
                "signal_priority": 3,
                "implication": "Regency pressuring price floor in commercial foodservice"
            },
            {
                "competitor": "Advance Tabco",
                "product_family": "commercial_sinks",
                "product_name": "Modular Work Station System",
                "description": "Configurable sink/work surface system for ghost kitchens",
                "key_features": ["Modular design", "Quick assembly", "Small footprint options"],
                "target_market": "Ghost kitchens, cloud kitchens, food halls",
                "launch_date": "2025-09-25",
                "source": "Advance Tabco press + Nation's Restaurant News",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Advance Tabco targeting ghost kitchen trend"
            }
        ]
        
        # Parent Company Coordination Signals
        self.simulated_coordination = {
            "Morris Group": [
                {
                    "signal": "Healthcare Vertical Integration",
                    "brands_involved": ["Just Manufacturing", "T&S Brass"],
                    "description": "Joint product development - Just sinks with integrated T&S faucetry",
                    "date": "2025-10-15",
                    "source": "Trade show displays, combined spec sheets",
                    "confidence": "high",
                    "implication": "Morris creating bundled healthcare solutions across brands"
                },
                {
                    "signal": "Shared Rep Network Expansion",
                    "brands_involved": ["Just Manufacturing", "T&S Brass", "Chicago Faucets"],
                    "description": "Consolidated rep groups in SE and SW regions",
                    "date": "2025-09-01",
                    "source": "Industry contacts, rep network announcements",
                    "confidence": "medium",
                    "implication": "Morris consolidating go-to-market for efficiency"
                }
            ],
            "Lixil": [
                {
                    "signal": "Commercial Market Entry Signal",
                    "brands_involved": ["Grohe", "American Standard"],
                    "description": "LinkedIn job postings for commercial specification sales",
                    "date": "2025-11-01",
                    "source": "LinkedIn job postings",
                    "confidence": "low",
                    "implication": "Lixil may be preparing commercial push - monitor for product announcements"
                }
            ]
        }
        
        # Leadership Changes
        self.simulated_leadership = [
            {
                "competitor": "Advance Tabco",
                "person": "Michael Chen",
                "previous_role": "VP Product Development, Vollrath",
                "new_role": "Chief Product Officer, Advance Tabco",
                "date": "2025-09-01",
                "source": "Advance Tabco announcement + LinkedIn",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Advance Tabco investing in product development leadership"
            }
        ]

    def perform(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute the requested competitive intelligence action."""
        actions = {
            "run_quarterly_analysis": self._run_quarterly_analysis,
            "analyze_competitor": self._analyze_competitor,
            "check_parent_company_coordination": self._check_parent_company_coordination,
            "get_healthcare_innovations": self._get_healthcare_innovations,
            "get_ada_compliance_updates": self._get_ada_compliance_updates,
            "get_sustainability_updates": self._get_sustainability_updates,
            "search_trade_publications": self._search_trade_publications,
            "get_product_launches": self._get_product_launches,
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
        logger.info(f"Running Sinks quarterly analysis: {time_period}")
        
        # Build prioritized signals
        all_signals = []
        
        for innov in self.simulated_healthcare_innovations:
            all_signals.append({
                "type": "healthcare_innovation",
                "priority": innov.get("signal_priority", 5),
                "confidence": innov.get("confidence"),
                "description": f"{innov['competitor']}: {innov['innovation']}",
                "implication": innov.get("implication")
            })
        
        for launch in self.simulated_product_launches:
            all_signals.append({
                "type": "product_launch",
                "priority": launch.get("signal_priority", 5),
                "confidence": launch.get("confidence"),
                "description": f"{launch['competitor']}: {launch['product_name']}",
                "implication": launch.get("implication")
            })
        
        all_signals.sort(key=lambda x: x["priority"])
        
        return {
            "report_type": "Quarterly Competitive Intelligence",
            "business_unit": "Elkay & Just Sinks",
            "period": time_period,
            "generated_at": datetime.now().isoformat(),
            
            "highlights_by_segment": {
                "healthcare": {
                    "key_development": "Infection control innovation accelerating",
                    "competitive_dynamic": "Sloan, Franke, Morris Group (via T&S/Just) all investing"
                },
                "food_service": {
                    "key_development": "Ghost kitchen/modular solutions emerging",
                    "competitive_dynamic": "Advance Tabco targeting new foodservice formats"
                },
                "commercial": {
                    "key_development": "Sustainability certifications becoming spec requirements",
                    "competitive_dynamic": "Recycled content and water savings claims increasing"
                }
            },
            
            "top_3_significant_changes": all_signals[:3],
            
            "parent_company_coordination": {
                "morris_group": "Just + T&S healthcare bundling observed",
                "watch_for": "Lixil commercial market entry signals"
            },
            
            "regulatory_watch": {
                "ada_update": "2026 ADA guidelines will require product updates",
                "action_needed": "Review product line against new knee clearance requirements"
            },
            
            "implications": {
                "near_term": "Healthcare infection control features becoming standard in patient care sinks",
                "mid_term": "Morris Group coordination creating bundled solution competition"
            },
            
            "watch_list": [
                "Just Intellisink launch - feature set and pricing",
                "2026 ADA guideline implementation",
                "Morris Group healthcare bundling expansion"
            ]
        }

    def _analyze_competitor(self, competitor: str, **kwargs) -> Dict[str, Any]:
        """Deep dive analysis on specific competitor."""
        logger.info(f"Analyzing competitor: {competitor}")
        
        parent = None
        for p, brands in self.parent_companies.items():
            if competitor in brands:
                parent = p
                break
        
        launches = [l for l in self.simulated_product_launches if l.get("competitor") == competitor]
        innovations = [i for i in self.simulated_healthcare_innovations if i.get("competitor") == competitor]
        
        # Check for parent company coordination
        coordination = []
        if parent:
            coordination = self.simulated_coordination.get(parent, [])
        
        return {
            "competitor": competitor,
            "parent_company": parent,
            "product_launches": launches,
            "healthcare_innovations": innovations,
            "parent_coordination_signals": coordination,
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

    def _get_healthcare_innovations(self, **kwargs) -> Dict[str, Any]:
        """Get healthcare/infection control innovations."""
        return {
            "innovations": self.simulated_healthcare_innovations,
            "trend_summary": "Antimicrobial surfaces, touchless operation, and compliance monitoring emerging as key features",
            "generated_at": datetime.now().isoformat()
        }

    def _get_ada_compliance_updates(self, **kwargs) -> Dict[str, Any]:
        """Get ADA compliance and accessibility updates."""
        return {
            "updates": self.simulated_ada_updates,
            "standards_monitored": [
                "ADA Accessibility Guidelines (ADAAG)",
                "ICC A117.1 Accessible Design",
                "California Building Code (CBC) accessibility provisions"
            ],
            "generated_at": datetime.now().isoformat()
        }

    def _get_sustainability_updates(self, **kwargs) -> Dict[str, Any]:
        """Get sustainability and green kitchen updates."""
        return {
            "initiatives": self.simulated_sustainability,
            "certification_trends": [
                "Recycled stainless content certification",
                "Water efficiency ratings",
                "LEED credit eligibility documentation"
            ],
            "generated_at": datetime.now().isoformat()
        }

    def _search_trade_publications(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search trade publications."""
        return {
            "query": query,
            "results": [
                {"source": "Foodservice Equipment Reports", "title": f"Commercial Kitchen: {query}", "relevance": "high"},
                {"source": "Healthcare Design", "title": f"Healthcare Environments: {query}", "relevance": "medium"},
                {"source": "Nation's Restaurant News", "title": f"Restaurant Industry: {query}", "relevance": "medium"}
            ],
            "note": "Simulated results - production would use live API"
        }

    def _get_product_launches(self, product_family: str = None, **kwargs) -> Dict[str, Any]:
        """Get product launches."""
        launches = self.simulated_product_launches
        if product_family:
            launches = [l for l in launches if l.get("product_family") == product_family]
        
        return {
            "launches": launches,
            "generated_at": datetime.now().isoformat()
        }

    def _get_leadership_changes(self, **kwargs) -> Dict[str, Any]:
        """Get leadership changes."""
        return {
            "changes": self.simulated_leadership,
            "generated_at": datetime.now().isoformat()
        }

    def _generate_bu_report(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Generate BU report for GM/PM distribution."""
        analysis = self._run_quarterly_analysis(time_period)
        
        return {
            "report_title": "ELKAY & JUST SINKS COMPETITIVE INTELLIGENCE REPORT",
            "period": time_period,
            "prepared_for": "GM/PM Review",
            
            "executive_summary": """Healthcare segment seeing significant innovation investment from 
Sloan, Franke, and Morris Group (via Just/T&S). Infection control and touchless features becoming 
standard. Morris Group coordination across Just and T&S creating bundled healthcare solutions. 
2026 ADA guideline changes will require product review.""",
            
            "key_observation": """Morris Group leveraging portfolio across Just + T&S for integrated 
healthcare solutions. This is portfolio strategy, not individual brand tactics.""",
            
            "highlights": analysis["highlights_by_segment"],
            "top_changes": analysis["top_3_significant_changes"],
            
            "regulatory_alert": {
                "item": "2026 ADA Accessibility Guidelines",
                "impact": "Updated knee clearance and insulation requirements",
                "action": "Review product line compliance by Q1 2026"
            },
            
            "implications": analysis["implications"],
            "watch_list": analysis["watch_list"],
            
            "sources": [
                "1. Healthcare Facilities Today, Healthcare Design - healthcare innovations",
                "2. Federal Register, ADA.gov - regulatory updates",
                "3. Foodservice Equipment Reports - commercial launches",
                "4. SCS Global Services - sustainability certifications",
                "Note: Third-party sources prioritized"
            ],
            
            "generated_at": datetime.now().isoformat()
        }
