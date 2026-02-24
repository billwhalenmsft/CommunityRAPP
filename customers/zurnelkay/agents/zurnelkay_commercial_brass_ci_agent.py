"""
Agent: ZurnElkay Commercial Brass Competitive Intelligence Agent
Purpose: Quarterly competitive intelligence for Commercial Brass business unit
Scope: Commercial Faucets, Flush Valves, Electronic Fixtures
Customer: Zurn Elkay Water Solutions

This is a LEVEL 1 domain agent - source of truth for Commercial Brass category.
Focus: Platform/system launches, touchless technology, water management systems.

Competitors Monitored:
- Commercial Faucets: Sloan, Kohler, Moen Commercial, T&S Brass (Morris), Chicago Faucets (Morris), Delta Commercial
- Flush Valves: Sloan, Kohler, American Standard (Lixil), Gerber (Globe Union)
- Electronic/Touchless: Sloan, Kohler, Toto, Dyson (dryers), Bobrick

Special Focus: Platform/system launches, touchless technology proliferation,
water management and IoT systems, Geberit/Lixil coordination signals.
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


class ZurnElkayCommercialBrassCIAgent(BasicAgent):
    """
    Commercial Brass Competitive Intelligence Agent for Zurn Elkay.
    
    Monitors Commercial Faucets, Flush Valves, and Electronic/Touchless fixtures.
    Special focus on platform launches, IoT, and water management systems.
    """

    def __init__(self):
        self.name = 'CommercialBrassCIAgent'
        self.metadata = {
            "name": self.name,
            "description": """Commercial Brass Competitive Intelligence Agent for Zurn Elkay. Monitors Commercial 
Faucets, Flush Valves, and Electronic/Touchless fixtures. Special focus on platform/system launches, 
touchless technology proliferation, water management IoT systems, and Geberit/Lixil coordination.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "run_quarterly_analysis",
                            "analyze_competitor",
                            "check_parent_company_coordination",
                            "get_platform_launches",
                            "get_touchless_technology",
                            "get_water_management_systems",
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
                        "enum": ["Illinois Tool Works", "Lixil", "Kohler", "Morris Group", "Geberit", "Toto"],
                        "description": "Parent company to check for coordinated moves"
                    },
                    "product_family": {
                        "type": "string",
                        "enum": ["commercial_faucets", "flush_valves", "electronic_touchless"],
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
            "commercial_faucets": {
                "primary": ["Sloan", "Kohler", "Moen Commercial", "T&S Brass", "Chicago Faucets"],
                "secondary": ["Delta Commercial"]
            },
            "flush_valves": {
                "primary": ["Sloan", "Kohler", "American Standard", "Gerber"],
                "secondary": ["Toto"]
            },
            "electronic_touchless": {
                "primary": ["Sloan", "Kohler", "Toto", "Dyson", "Bobrick"],
                "secondary": ["ASI", "Bradley"]
            }
        }
        
        # Parent company mapping - critical for coordination analysis
        self.parent_companies = {
            "Illinois Tool Works": ["Sloan"],
            "Kohler": ["Kohler", "Sterling", "Kallista"],
            "Lixil": ["American Standard", "Grohe"],
            "Morris Group": ["T&S Brass", "Chicago Faucets", "Just Manufacturing"],
            "Geberit": ["Geberit"],
            "Toto": ["Toto"]
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
        
        # Platform/System Launches
        self.simulated_platform_launches = [
            {
                "competitor": "Sloan",
                "parent_company": "Illinois Tool Works",
                "platform_name": "Sloan Connect",
                "description": "Enterprise water management platform with fixture connectivity",
                "components": [
                    "Cloud-based dashboard",
                    "Connected flush valves and faucets",
                    "Usage analytics and reporting",
                    "Predictive maintenance alerts",
                    "Water consumption optimization"
                ],
                "target_market": "Airports, stadiums, universities, large commercial",
                "launch_date": "2025-10-15",
                "source": "Sloan press release + Greenbuild demo + PM Engineer",
                "confidence": "high",
                "signal_priority": 1,
                "pricing_model": "Hardware + SaaS subscription",
                "implication": "Sloan moving from product company to platform company - major strategic shift"
            },
            {
                "competitor": "Kohler",
                "parent_company": "Kohler",
                "platform_name": "Kohler Wellnected",
                "description": "Commercial restroom management system",
                "components": [
                    "Occupancy monitoring",
                    "Cleaning schedule optimization",
                    "Fixture monitoring",
                    "Sustainability reporting"
                ],
                "target_market": "Corporate offices, hospitality",
                "launch_date": "2025-09-20",
                "source": "Kohler commercial website + KBIS preview",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Kohler matching Sloan's platform approach"
            },
            {
                "competitor": "Geberit",
                "parent_company": "Geberit",
                "platform_name": "Geberit SetApp Pro",
                "description": "Commercial specification and commissioning platform",
                "components": [
                    "Electronic product configuration",
                    "Installation verification",
                    "Service scheduling",
                    "Spare parts ordering"
                ],
                "target_market": "Specifiers, installers, facility managers",
                "launch_date": "2025-11-01",
                "source": "Geberit press + ISH preview",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Geberit building digital ecosystem for specification influence"
            }
        ]
        
        # Touchless Technology Updates
        self.simulated_touchless = [
            {
                "competitor": "Sloan",
                "product_family": "flush_valves",
                "product": "SOLIS Next-Gen Solar Flushometer",
                "innovation": "Enhanced solar power + improved range/reliability",
                "key_features": [
                    "Faster solar charging",
                    "Extended low-light operation",
                    "Dual detection sensors",
                    "Connectivity-ready"
                ],
                "date": "2025-10-01",
                "source": "Sloan catalog + Facility Executive review",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Sloan continuing solar leadership while adding connectivity"
            },
            {
                "competitor": "Toto",
                "parent_company": "Toto",
                "product_family": "flush_valves",
                "product": "ECOPOWER Gen 5",
                "innovation": "Hydro-powered self-generating flush valve",
                "key_features": [
                    "No batteries or external power needed",
                    "Self-cleaning sensor",
                    "Ultra-low water consumption",
                    "20-year valve life claim"
                ],
                "date": "2025-09-15",
                "source": "Toto USA press + Facility Executive",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Toto differentiating on sustainability and lifecycle cost"
            },
            {
                "competitor": "Dyson",
                "product_family": "electronic_touchless",
                "product": "Airblade V2 Commercial",
                "innovation": "Integrated hand dryer + sensor faucet concept",
                "key_features": [
                    "Combined faucet/dryer unit",
                    "HEPA filtration",
                    "Touchless operation",
                    "Usage data collection"
                ],
                "date": "2025-11-15",
                "source": "Dyson commercial preview + trade show",
                "confidence": "medium",
                "signal_priority": 2,
                "implication": "Dyson expanding into integrated restroom solutions - category disruption potential"
            }
        ]
        
        # Water Management/IoT Systems
        self.simulated_water_management = [
            {
                "competitor": "Sloan",
                "system": "Water Usage Analytics Module",
                "description": "Real-time water consumption monitoring with anomaly detection",
                "capabilities": [
                    "Fixture-level consumption tracking",
                    "Leak detection alerts",
                    "Usage pattern analysis",
                    "Benchmarking reports"
                ],
                "integration": "Sloan Connect platform",
                "target_market": "Sustainability-focused facilities",
                "date": "2025-10-20",
                "source": "Sloan platform documentation + customer reference",
                "confidence": "high",
                "signal_priority": 1
            },
            {
                "competitor": "Kohler",
                "system": "Water Stewardship Dashboard",
                "description": "ESG reporting integration for water consumption",
                "capabilities": [
                    "LEED and WELL credit documentation",
                    "ESG reporting exports",
                    "Goal tracking and alerts",
                    "Peer benchmarking"
                ],
                "integration": "Kohler Wellnected platform",
                "target_market": "Corporate ESG programs",
                "date": "2025-09-25",
                "source": "Kohler sustainability webpage + Green Building Advisor",
                "confidence": "high",
                "signal_priority": 2
            }
        ]
        
        # Product Launches (non-platform)
        self.simulated_product_launches = [
            {
                "competitor": "Sloan",
                "parent_company": "Illinois Tool Works",
                "product_family": "commercial_faucets",
                "product_name": "Optima Hardwired Series",
                "description": "Commercial sensor faucets with building power connection",
                "key_features": ["Hardwired power option", "BACnet integration", "Programmable settings"],
                "target_market": "New construction, major renovation",
                "launch_date": "2025-10-08",
                "source": "Sloan press + Engineering specification",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Sloan enabling building system integration"
            },
            {
                "competitor": "Chicago Faucets",
                "parent_company": "Morris Group",
                "product_family": "commercial_faucets",
                "product_name": "E-Tronic Refresh",
                "description": "Updated electronic faucet line with modernized styling",
                "key_features": ["Contemporary design", "Improved sensor technology", "Easy maintenance"],
                "target_market": "Mid-market commercial",
                "launch_date": "2025-09-15",
                "source": "Chicago Faucets catalog update",
                "confidence": "high",
                "signal_priority": 3
            },
            {
                "competitor": "American Standard",
                "parent_company": "Lixil",
                "product_family": "flush_valves",
                "product_name": "Ultima Sensing System",
                "description": "Dual-flush retrofit kit with sensing technology",
                "key_features": ["Retrofit design", "Dual-flush capability", "Easy installation"],
                "target_market": "Renovation, retrofit market",
                "launch_date": "2025-11-05",
                "source": "American Standard commercial catalog + distributor preview",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Lixil targeting retrofit segment"
            }
        ]
        
        # Parent Company Coordination Signals
        self.simulated_coordination = {
            "Illinois Tool Works": [
                {
                    "signal": "Platform-First Strategy",
                    "description": "ITW segment review indicates Sloan positioned as platform business, not just product",
                    "evidence": "Q3 investor presentation, increased software/digital headcount",
                    "date": "2025-10-01",
                    "source": "ITW Q3 Earnings + LinkedIn job postings",
                    "confidence": "high",
                    "implication": "Sloan Connect is corporate strategy, expect continued investment"
                }
            ],
            "Lixil": [
                {
                    "signal": "Americas Commercial Focus",
                    "brands_involved": ["American Standard", "Grohe"],
                    "description": "Lixil reorganizing Americas to emphasize commercial growth",
                    "evidence": "Leadership changes, combined commercial teams",
                    "date": "2025-09-15",
                    "source": "Lixil press + industry contacts",
                    "confidence": "medium",
                    "implication": "Lixil may bring Grohe commercial products to US - watch for announcements"
                }
            ],
            "Geberit": [
                {
                    "signal": "Digital Ecosystem Investment",
                    "description": "Geberit announcing €50M digital platform investment",
                    "evidence": "Investor presentation, SetApp Pro launch",
                    "date": "2025-10-15",
                    "source": "Geberit Investor Day",
                    "confidence": "high",
                    "implication": "Geberit serious about digital - potential BIM and spec tool competition"
                }
            ],
            "Morris Group": [
                {
                    "signal": "Continued Independence",
                    "brands_involved": ["T&S Brass", "Chicago Faucets"],
                    "description": "Morris brands operating independently in commercial brass",
                    "evidence": "Separate catalogs, distinct market positioning",
                    "date": "2025-11-01",
                    "source": "Catalog analysis, rep feedback",
                    "confidence": "high",
                    "implication": "Less coordination threat than Sloan or Lixil"
                }
            ]
        }
        
        # Leadership Changes
        self.simulated_leadership = [
            {
                "competitor": "Sloan",
                "parent_company": "Illinois Tool Works",
                "person": "Sarah Morrison",
                "previous_role": "Director of Product, Honeywell Building Technologies",
                "new_role": "VP Digital Products, Sloan",
                "date": "2025-09-01",
                "source": "Sloan announcement + LinkedIn",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Sloan bringing building automation expertise - platform strategy is serious"
            },
            {
                "competitor": "American Standard",
                "parent_company": "Lixil",
                "person": "David Kim",
                "previous_role": "VP Commercial, Kohler",
                "new_role": "President, Lixil Americas Commercial",
                "date": "2025-10-01",
                "source": "Lixil press release",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Lixil hiring Kohler commercial talent - signals commercial market focus"
            }
        ]

    def perform(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute the requested competitive intelligence action."""
        actions = {
            "run_quarterly_analysis": self._run_quarterly_analysis,
            "analyze_competitor": self._analyze_competitor,
            "check_parent_company_coordination": self._check_parent_company_coordination,
            "get_platform_launches": self._get_platform_launches,
            "get_touchless_technology": self._get_touchless_technology,
            "get_water_management_systems": self._get_water_management_systems,
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
        logger.info(f"Running Commercial Brass quarterly analysis: {time_period}")
        
        # Build prioritized signals
        all_signals = []
        
        for platform in self.simulated_platform_launches:
            all_signals.append({
                "type": "platform_launch",
                "priority": platform.get("signal_priority", 5),
                "confidence": platform.get("confidence"),
                "description": f"{platform['competitor']}: {platform['platform_name']}",
                "implication": platform.get("implication")
            })
        
        for touchless in self.simulated_touchless:
            all_signals.append({
                "type": "touchless_technology",
                "priority": touchless.get("signal_priority", 5),
                "confidence": touchless.get("confidence"),
                "description": f"{touchless['competitor']}: {touchless['product']}",
                "implication": touchless.get("implication")
            })
        
        for leader in self.simulated_leadership:
            all_signals.append({
                "type": "leadership_change",
                "priority": leader.get("signal_priority", 5),
                "confidence": leader.get("confidence"),
                "description": f"{leader['competitor']}: {leader['person']} - {leader['new_role']}",
                "implication": leader.get("implication")
            })
        
        all_signals.sort(key=lambda x: x["priority"])
        
        return {
            "report_type": "Quarterly Competitive Intelligence",
            "business_unit": "Commercial Brass",
            "period": time_period,
            "generated_at": datetime.now().isoformat(),
            
            "strategic_theme": """Platform Battleground: Sloan and Kohler both launched enterprise restroom 
management platforms this quarter. This represents a fundamental market shift from product to platform 
competition. Geberit also investing heavily in digital ecosystem.""",
            
            "highlights_by_segment": {
                "platform_systems": {
                    "key_development": "Sloan Connect and Kohler Wellnected both launched",
                    "competitive_dynamic": "Race to establish platform standard in commercial restrooms"
                },
                "flush_valves": {
                    "key_development": "Connectivity-readiness becoming standard feature",
                    "competitive_dynamic": "Solar/hydro power + IoT integration"
                },
                "touchless": {
                    "key_development": "Dyson entering integrated restroom solutions",
                    "competitive_dynamic": "Category boundaries blurring - disruption potential"
                }
            },
            
            "top_3_significant_changes": all_signals[:3],
            
            "talent_signals": {
                "pattern": "Building automation and commercial plumbing talent moving to fixture companies",
                "examples": [
                    "Sloan hired Honeywell digital leader",
                    "Lixil hired Kohler commercial president"
                ],
                "implication": "Industry preparing for platform/IoT competition"
            },
            
            "parent_company_watch": {
                "illinois_tool_works": "Sloan Connect is corporate strategy - expect continued investment",
                "lixil": "Americas commercial reorganization - potential Grohe commercial entry",
                "geberit": "€50M digital platform investment announced"
            },
            
            "implications": {
                "near_term": "Platform/ecosystem differentiation becoming critical",
                "mid_term": "Customers will expect water management data and ESG reporting integration"
            },
            
            "watch_list": [
                "Sloan Connect adoption rates and pricing",
                "Kohler Wellnected feature expansion",
                "Lixil commercial strategy clarification",
                "Dyson integrated product commercialization"
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
        
        platforms = [p for p in self.simulated_platform_launches if p.get("competitor") == competitor]
        touchless = [t for t in self.simulated_touchless if t.get("competitor") == competitor]
        launches = [l for l in self.simulated_product_launches if l.get("competitor") == competitor]
        water_mgmt = [w for w in self.simulated_water_management if w.get("competitor") == competitor]
        
        # Special handling for Sloan as platform leader
        if competitor == "Sloan":
            return self._analyze_sloan_platform_strategy()
        
        return {
            "competitor": competitor,
            "parent_company": parent,
            "platform_launches": platforms,
            "touchless_products": touchless,
            "product_launches": launches,
            "water_management": water_mgmt,
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_sloan_platform_strategy(self) -> Dict[str, Any]:
        """Special analysis for Sloan's platform strategy."""
        return {
            "competitor": "Sloan",
            "parent_company": "Illinois Tool Works",
            "analysis_type": "Platform Strategy Deep Dive",
            
            "strategic_assessment": """Sloan is executing a platform-first strategy transformation. 
This is not incremental product improvement - it's a fundamental business model evolution from 
fixture manufacturer to restroom management platform company.""",
            
            "platform_details": {
                "name": "Sloan Connect",
                "components": [
                    "Connected fixtures (faucets, flush valves)",
                    "Cloud dashboard",
                    "Water analytics",
                    "Predictive maintenance",
                    "ESG reporting integration"
                ],
                "business_model": "Hardware + SaaS subscription",
                "target_customers": "Large commercial: airports, stadiums, universities"
            },
            
            "supporting_evidence": [
                "VP Digital Products hired from Honeywell Building Technologies",
                "ITW segment review positions Sloan as platform business",
                "Increased digital/software job postings",
                "Greenbuild demo focused on platform, not products"
            ],
            
            "competitive_implications": [
                "Sloan may establish platform standard before competitors",
                "Once customers adopt platform, switching costs are high",
                "Product-only competitors will be at disadvantage in large projects",
                "Water management data becomes Sloan competitive asset"
            ],
            
            "recommendations": [
                "Accelerate connected product roadmap",
                "Evaluate platform partnership vs. build options",
                "Ensure products are 'platform-ready' even without own platform",
                "Track Sloan Connect adoption in key accounts"
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

    def _get_platform_launches(self, **kwargs) -> Dict[str, Any]:
        """Get platform/system launches."""
        return {
            "platforms": self.simulated_platform_launches,
            "trend_summary": "Platform competition emerging as key battleground",
            "generated_at": datetime.now().isoformat()
        }

    def _get_touchless_technology(self, **kwargs) -> Dict[str, Any]:
        """Get touchless technology updates."""
        return {
            "touchless_products": self.simulated_touchless,
            "trend_summary": "Connectivity-readiness becoming standard; power technology evolving",
            "generated_at": datetime.now().isoformat()
        }

    def _get_water_management_systems(self, **kwargs) -> Dict[str, Any]:
        """Get water management/IoT system updates."""
        return {
            "systems": self.simulated_water_management,
            "trend_summary": "Water analytics and ESG integration becoming differentiators",
            "generated_at": datetime.now().isoformat()
        }

    def _search_trade_publications(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search trade publications."""
        return {
            "query": query,
            "results": [
                {"source": "PM Engineer", "title": f"Commercial Plumbing: {query}", "relevance": "high"},
                {"source": "Facility Executive", "title": f"Facilities: {query}", "relevance": "high"},
                {"source": "Buildings Magazine", "title": f"Building Technology: {query}", "relevance": "medium"}
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
            "pattern_analysis": "Building automation and commercial talent moving to fixture companies",
            "generated_at": datetime.now().isoformat()
        }

    def _generate_bu_report(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Generate BU report for GM/PM distribution."""
        analysis = self._run_quarterly_analysis(time_period)
        
        return {
            "report_title": "COMMERCIAL BRASS COMPETITIVE INTELLIGENCE REPORT",
            "period": time_period,
            "prepared_for": "GM/PM Review",
            
            "executive_summary": """Platform competition has emerged as the defining theme. Sloan Connect 
and Kohler Wellnected both launched enterprise restroom management platforms. This represents market 
shift from product to platform competition. Geberit also investing €50M in digital ecosystem. 
Talent movement (Honeywell → Sloan, Kohler → Lixil) signals industry preparing for IoT competition.""",
            
            "critical_strategic_shift": {
                "observation": "Sloan transforming from product company to platform company",
                "evidence": "Sloan Connect launch, digital leadership hire, ITW positioning",
                "risk": "Platform adoption creates customer lock-in",
                "urgency": "HIGH"
            },
            
            "highlights": analysis["highlights_by_segment"],
            "top_changes": analysis["top_3_significant_changes"],
            
            "talent_alert": analysis["talent_signals"],
            
            "parent_company_watch": analysis["parent_company_watch"],
            
            "implications": analysis["implications"],
            "watch_list": analysis["watch_list"],
            
            "strategic_questions": [
                "What is our platform/ecosystem strategy?",
                "Should we partner or build for connected product capabilities?",
                "Are our products 'platform-ready' for customer deployments?",
                "How do we compete if Sloan establishes platform standard?"
            ],
            
            "sources": [
                "1. Sloan press, ITW investor materials - platform strategy",
                "2. PM Engineer, Facility Executive - product coverage",
                "3. LinkedIn, company announcements - leadership changes",
                "4. Trade shows (Greenbuild, KBIS) - product previews",
                "Note: Third-party sources prioritized"
            ],
            
            "generated_at": datetime.now().isoformat()
        }
