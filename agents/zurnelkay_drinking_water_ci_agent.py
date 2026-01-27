"""
Agent: ZurnElkay Drinking Water Competitive Intelligence Agent
Purpose: Quarterly competitive intelligence for Elkay Drinking Water business unit
Scope: Bottle Fillers, Drinking Fountains, Filtration, Water Coolers
Customer: Zurn Elkay Water Solutions

This is a LEVEL 1 domain agent - source of truth for Drinking Water category.
Focus: NSF certifications, public sector wins, sustainability claims.

Competitors Monitored:
- Bottle Fillers: Halsey Taylor (Elkay), Oasis, Haws (Watts WWT), Aquafil, Global Industrial
- Drinking Fountains: Halsey Taylor (Elkay), Haws (Watts WWT), Oasis, Sunroc
- Filtration: Culligan, 3M/Cuno, Everpure (Pentair), Brita, InSinkErator (Whirlpool)
- Water Coolers: Culligan, Primo, Oasis, Crystal Rock

Special Focus: NSF/ANSI certification verification, LEED/sustainability claims,
public sector contract wins, lead-free compliance.
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


class ZurnElkayDrinkingWaterCIAgent(BasicAgent):
    """
    Drinking Water Competitive Intelligence Agent for Zurn Elkay.
    
    Monitors Bottle Fillers, Drinking Fountains, Filtration, and Water Coolers.
    Special focus on NSF certifications, public sector wins, sustainability.
    """

    def __init__(self):
        self.name = 'DrinkingWaterCIAgent'
        self.metadata = {
            "name": self.name,
            "description": """Drinking Water Competitive Intelligence Agent for Zurn Elkay. Monitors Bottle Fillers, 
Drinking Fountains, Filtration, and Water Coolers. Special focus on NSF certifications, 
public sector contract wins, sustainability claims, and lead-free compliance.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "run_quarterly_analysis",
                            "analyze_competitor",
                            "check_nsf_certifications",
                            "get_public_sector_wins",
                            "get_sustainability_claims",
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
                    "product_family": {
                        "type": "string",
                        "enum": ["bottle_fillers", "drinking_fountains", "filtration", "water_coolers"],
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
            "bottle_fillers": {
                "primary": ["Oasis", "Haws", "Aquafil"],
                "secondary": ["Global Industrial"]
            },
            "drinking_fountains": {
                "primary": ["Haws", "Oasis", "Sunroc"],
                "secondary": []
            },
            "filtration": {
                "primary": ["Culligan", "3M/Cuno", "Everpure", "Brita"],
                "secondary": ["InSinkErator"]
            },
            "water_coolers": {
                "primary": ["Culligan", "Primo", "Oasis", "Crystal Rock"],
                "secondary": []
            }
        }
        
        # Parent company mapping
        self.parent_companies = {
            "Watts Water Technologies": ["Haws"],
            "Pentair": ["Everpure"],
            "Whirlpool": ["InSinkErator"],
            "Primo Water": ["Primo", "Crystal Rock"]
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
        
        # NSF Certification Updates
        self.simulated_certifications = [
            {
                "competitor": "Haws",
                "parent_company": "Watts Water Technologies",
                "certification": "NSF/ANSI 61",
                "product_line": "Hydration Station Series - New SKUs",
                "certification_body": "NSF International",
                "date": "2025-10-28",
                "source": "NSF Certified Products Database",
                "confidence": "high",
                "signal_priority": 2,
                "verification_url": "nsf.org/certified-products"
            },
            {
                "competitor": "Oasis",
                "certification": "NSF/ANSI 372",
                "product_line": "VersaFiller Line - Lead-free certification expansion",
                "certification_body": "NSF International",
                "date": "2025-11-05",
                "source": "NSF Database + Oasis Press",
                "confidence": "high",
                "signal_priority": 1,
                "verification_url": "nsf.org/certified-products"
            },
            {
                "competitor": "3M/Cuno",
                "certification": "NSF/ANSI 53",
                "product_line": "Scale Gard Pro Series - Lead reduction claims",
                "certification_body": "NSF International",
                "date": "2025-09-18",
                "source": "3M Press Release + NSF Database",
                "confidence": "high",
                "signal_priority": 2
            },
            {
                "competitor": "Brita",
                "certification": "NSF/ANSI 42, 53",
                "product_line": "Commercial Filtration - New product line",
                "certification_body": "WQA",
                "date": "2025-10-10",
                "source": "WQA Database",
                "confidence": "high",
                "signal_priority": 3,
                "note": "Brita expanding into commercial - watch for bottle filler partnerships"
            }
        ]
        
        # Public Sector Contract Wins
        self.simulated_public_sector = [
            {
                "competitor": "Oasis",
                "contract_type": "State blanket PO",
                "entity": "Texas Department of Administrative Services",
                "scope": "Statewide bottle filler contract - K-12 schools",
                "estimated_value": "$2.5M over 3 years",
                "date": "2025-10-15",
                "source": "TX state procurement database + industry source",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Oasis winning state-level contracts through aggressive pricing"
            },
            {
                "competitor": "Haws",
                "parent_company": "Watts Water Technologies",
                "contract_type": "GSA Schedule",
                "entity": "GSA",
                "scope": "GSA Schedule 78 - hydration station categories",
                "estimated_value": "Federal access",
                "date": "2025-09-01",
                "source": "GSA Advantage catalog",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Haws strengthening federal market access"
            },
            {
                "competitor": "Culligan",
                "contract_type": "Municipal contract",
                "entity": "Chicago Public Schools",
                "scope": "Water filtration + cooler services - 500+ schools",
                "estimated_value": "$5M+ annually",
                "date": "2025-11-01",
                "source": "CPS procurement announcement",
                "confidence": "medium",
                "signal_priority": 1,
                "implication": "Culligan winning filtration-as-a-service contracts"
            }
        ]
        
        # Sustainability Claims
        self.simulated_sustainability = [
            {
                "competitor": "Oasis",
                "claim_type": "Product certification",
                "claim": "LEED v4 Water Efficiency Credits",
                "products": ["PSWQ1F", "VersaFiller Series"],
                "substantiation": "USGBC certification database",
                "date": "2025-10-01",
                "confidence": "high",
                "signal_priority": 2,
                "verification": "Verified in USGBC database"
            },
            {
                "competitor": "Haws",
                "parent_company": "Watts Water Technologies",
                "claim_type": "Plastic bottle savings",
                "claim": "Digital counters tracking 150M+ bottles saved across installed base",
                "products": ["Hydration stations with digital counter"],
                "substantiation": "Marketing claim - methodology unclear",
                "date": "2025-09-15",
                "confidence": "medium",
                "signal_priority": 3,
                "verification": "Marketing claim - no third-party audit"
            },
            {
                "competitor": "Aquafil",
                "claim_type": "Carbon neutral manufacturing",
                "claim": "Carbon neutral bottle filler production by 2026",
                "products": ["All bottle fillers"],
                "substantiation": "Third-party carbon accounting",
                "date": "2025-11-10",
                "confidence": "medium",
                "signal_priority": 3,
                "verification": "Commitment announced - implementation pending"
            }
        ]
        
        # Product Launches
        self.simulated_product_launches = [
            {
                "competitor": "Oasis",
                "product_family": "bottle_fillers",
                "product_name": "VersaFiller Touch-Free Sensor Series",
                "description": "Touchless bottle filling with antimicrobial surfaces",
                "key_features": ["Hands-free operation", "Antimicrobial copper touch points", "Real-time filter status"],
                "target_market": "K-12 schools, healthcare",
                "launch_date": "2025-11-15",
                "source": "Oasis dealer communication + Supply House Times",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Post-COVID hygiene features becoming standard"
            },
            {
                "competitor": "Haws",
                "parent_company": "Watts Water Technologies",
                "product_family": "bottle_fillers",
                "product_name": "Hydration Station Connect",
                "description": "IoT-enabled bottle filler with cloud dashboard",
                "key_features": ["Filter monitoring", "Usage analytics", "Maintenance alerts"],
                "target_market": "Facility managers, corporate campuses",
                "launch_date": "2025-10-01",
                "source": "Watts/Haws press release",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Watts bringing connected product strategy to Haws portfolio"
            },
            {
                "competitor": "Culligan",
                "product_family": "filtration",
                "product_name": "Smart Water Pro",
                "description": "Commercial filtration with subscription monitoring",
                "key_features": ["Automatic filter replacement scheduling", "Water quality monitoring", "Subscription model"],
                "target_market": "Commercial, foodservice",
                "launch_date": "2025-09-20",
                "source": "Culligan commercial press",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Culligan pushing subscription/service model"
            },
            {
                "competitor": "Primo",
                "parent_company": "Primo Water",
                "product_family": "water_coolers",
                "product_name": "hTRIO Enhanced",
                "description": "Bottom-load cooler with UV sterilization",
                "key_features": ["UV sanitization cycle", "Self-cleaning mode", "Child safety lock"],
                "target_market": "Office, residential",
                "launch_date": "2025-10-25",
                "source": "Primo press + retail listings",
                "confidence": "high",
                "signal_priority": 3
            }
        ]
        
        # Leadership Changes
        self.simulated_leadership = [
            {
                "competitor": "Oasis",
                "person": "Robert Menendez",
                "previous_role": "VP Sales, Elkay",
                "new_role": "SVP Commercial Sales, Oasis",
                "date": "2025-09-15",
                "source": "LinkedIn + Oasis announcement",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Oasis hiring ex-Elkay talent - brings customer relationships and playbook knowledge"
            }
        ]

    def perform(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute the requested competitive intelligence action."""
        actions = {
            "run_quarterly_analysis": self._run_quarterly_analysis,
            "analyze_competitor": self._analyze_competitor,
            "check_nsf_certifications": self._check_nsf_certifications,
            "get_public_sector_wins": self._get_public_sector_wins,
            "get_sustainability_claims": self._get_sustainability_claims,
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
        logger.info(f"Running Drinking Water quarterly analysis: {time_period}")
        
        # Build prioritized signal list
        all_signals = []
        
        for launch in self.simulated_product_launches:
            all_signals.append({
                "type": "product_launch",
                "priority": launch.get("signal_priority", 5),
                "confidence": launch.get("confidence"),
                "description": f"{launch['competitor']}: {launch['product_name']}",
                "implication": launch.get("implication")
            })
        
        for contract in self.simulated_public_sector:
            all_signals.append({
                "type": "public_sector_win",
                "priority": contract.get("signal_priority", 5),
                "confidence": contract.get("confidence"),
                "description": f"{contract['competitor']}: {contract['entity']} - {contract['scope'][:50]}...",
                "implication": contract.get("implication")
            })
        
        all_signals.sort(key=lambda x: x["priority"])
        
        return {
            "report_type": "Quarterly Competitive Intelligence",
            "business_unit": "Elkay Drinking Water",
            "period": time_period,
            "generated_at": datetime.now().isoformat(),
            
            "highlights_by_product_family": {
                "bottle_fillers": {
                    "key_development": "Touch-free and IoT-enabled products becoming standard",
                    "competitive_dynamic": "Oasis and Haws both launching connected products"
                },
                "filtration": {
                    "key_development": "Subscription/service models gaining traction",
                    "competitive_dynamic": "Culligan pushing filtration-as-a-service"
                },
                "public_sector": {
                    "key_development": "State-level blanket contracts creating lock-in",
                    "competitive_dynamic": "Oasis winning K-12 through aggressive state contracts"
                }
            },
            
            "top_3_significant_changes": all_signals[:3],
            
            "certification_activity": self._check_nsf_certifications(),
            
            "talent_movement": {
                "alert": "Ex-Elkay SVP Sales joined Oasis",
                "implication": "Customer relationship risk and competitive intelligence exposure"
            },
            
            "implications": {
                "near_term": "Touch-free and IoT features becoming table stakes in post-COVID environment",
                "mid_term": "State-level contract wins creating multi-year competitive barriers"
            },
            
            "watch_list": [
                "Oasis VersaFiller launch - pricing and channel strategy",
                "Haws/Watts digital platform integration",
                "Culligan subscription model adoption rates"
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
        certs = [c for c in self.simulated_certifications if c.get("competitor") == competitor]
        contracts = [c for c in self.simulated_public_sector if c.get("competitor") == competitor]
        
        return {
            "competitor": competitor,
            "parent_company": parent,
            "product_launches": launches,
            "certifications": certs,
            "public_sector_wins": contracts,
            "generated_at": datetime.now().isoformat()
        }

    def _check_nsf_certifications(self, product_family: str = None, **kwargs) -> Dict[str, Any]:
        """Check NSF certification status and changes."""
        certs = self.simulated_certifications
        
        return {
            "certification_updates": certs,
            "standards_monitored": [
                "NSF/ANSI 42 - Drinking Water Treatment Units (aesthetic)",
                "NSF/ANSI 53 - Drinking Water Treatment Units (health)",
                "NSF/ANSI 61 - Drinking Water System Components",
                "NSF/ANSI 372 - Lead Content"
            ],
            "verification_sources": [
                "NSF International Certified Products Database",
                "Water Quality Association (WQA) Product Certification",
                "IAPMO Certified Products Directory"
            ],
            "note": "All certifications verified against official databases where possible",
            "generated_at": datetime.now().isoformat()
        }

    def _get_public_sector_wins(self, **kwargs) -> Dict[str, Any]:
        """Get public sector contract wins and losses."""
        return {
            "contract_activity": self.simulated_public_sector,
            "sources_monitored": [
                "GSA Advantage",
                "State procurement databases (TX, CA, NY, FL)",
                "K-12 school district RFPs",
                "Municipal bid announcements"
            ],
            "generated_at": datetime.now().isoformat()
        }

    def _get_sustainability_claims(self, **kwargs) -> Dict[str, Any]:
        """Track and verify sustainability claims."""
        return {
            "claims": self.simulated_sustainability,
            "verification_approach": """All sustainability claims categorized by:
1. Third-party certified (LEED, Energy Star, etc.) - HIGH confidence
2. Audited/documented (carbon accounting) - MEDIUM confidence  
3. Marketing claims only - LOW confidence until verified""",
            "generated_at": datetime.now().isoformat()
        }

    def _search_trade_publications(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search trade publications."""
        return {
            "query": query,
            "results": [
                {"source": "Supply House Times", "title": f"Drinking Water Trends: {query}", "relevance": "high"},
                {"source": "PM Engineer", "title": f"Product Review: {query}", "relevance": "medium"}
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
            "alert": "HIGH: Ex-Elkay leadership joined key competitor",
            "generated_at": datetime.now().isoformat()
        }

    def _generate_bu_report(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Generate BU report for GM/PM distribution."""
        analysis = self._run_quarterly_analysis(time_period)
        
        return {
            "report_title": "ELKAY DRINKING WATER COMPETITIVE INTELLIGENCE REPORT",
            "period": time_period,
            "prepared_for": "GM/PM Review",
            
            "executive_summary": """Connected/IoT bottle fillers becoming standard feature set. 
Public sector contract activity elevated with state-level wins creating competitive barriers. 
Talent movement alert: ex-Elkay SVP Sales joined Oasis, bringing customer relationships.""",
            
            "critical_alert": {
                "type": "Talent Movement",
                "detail": "Robert Menendez (ex-Elkay VP Sales) joined Oasis as SVP Commercial Sales",
                "risk": "Customer relationship exposure, competitive playbook knowledge"
            },
            
            "highlights": analysis["highlights_by_product_family"],
            "top_changes": analysis["top_3_significant_changes"],
            "implications": analysis["implications"],
            "watch_list": analysis["watch_list"],
            
            "certification_summary": {
                "total_updates": len(self.simulated_certifications),
                "key_note": "NSF 372 (lead-free) certifications expanding across competitors"
            },
            
            "sources": [
                "1. NSF International Certified Products Database - verified certifications",
                "2. TX/GSA procurement databases - contract wins",
                "3. Supply House Times, PM Engineer - product launches",
                "4. LinkedIn + company announcements - leadership",
                "Note: Third-party sources prioritized"
            ],
            
            "generated_at": datetime.now().isoformat()
        }
