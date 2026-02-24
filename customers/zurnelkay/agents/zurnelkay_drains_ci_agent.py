"""
Agent: ZurnElkay Drains Competitive Intelligence Agent
Purpose: Quarterly competitive intelligence for Drains business unit
Scope: Core Spec Drains, Siteworks (Div 22 & 33), FOG Separation
Customer: Zurn Elkay Water Solutions

This is a LEVEL 1 domain agent - source of truth for Drains category.
Does NOT infer enterprise-wide themes (that's the Synthesizer's job).

Competitors Monitored:
- Core Spec: JR Smith (Morris), Watts, MiFab, Josam (Watts)
- Siteworks: JR Smith, Watts, ABT, ACO, DuraTrench, NDS (ADS), Sioux Chief
- FOG: Schier, Xerxes, Canplas, Highland Tank

Parent Company Coordination Flags:
- Morris Group: JR Smith, Acorn, Murdock, Whitehall
- Watts Water Technologies: Watts, Josam, Ames, Febco, Powers, Bradley, Haws
- ADS: NDS
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from agents.basic_agent import BasicAgent
import random

# Web scraping imports (optional - will stub if not available)
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logging.warning("Web scraping disabled - requests/bs4 not available")

# Azure OpenAI for analysis
try:
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    AZURE_AI_AVAILABLE = True
except ImportError:
    AZURE_AI_AVAILABLE = False
    logging.warning("Azure OpenAI not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZurnElkayDrainsCIAgent(BasicAgent):
    """
    Drains Competitive Intelligence Agent for Zurn Elkay.
    
    Provides quarterly competitive analysis for:
    - Core Spec Drains
    - Siteworks (Division 22 & 33)
    - FOG Separation
    
    Monitors competitors and flags parent company coordination.
    """

    def __init__(self):
        self.name = 'DrainsCIAgent'
        self.metadata = {
            "name": self.name,
            "description": """Drains Competitive Intelligence Agent for Zurn Elkay. Monitors Core Spec Drains, 
Siteworks (Div 22 & 33), and FOG Separation. Tracks JR Smith (Morris), Watts, MiFab, Schier and flags 
coordinated parent company moves. Use for quarterly competitive analysis.""",
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
                            "get_product_launches",
                            "get_leadership_changes",
                            "get_certification_updates",
                            "generate_bu_report"
                        ],
                        "description": "The competitive intelligence action to perform"
                    },
                    "competitor": {
                        "type": "string",
                        "description": "Specific competitor to analyze (e.g., 'JR Smith', 'Watts', 'MiFab')"
                    },
                    "parent_company": {
                        "type": "string",
                        "enum": ["Morris", "Watts Water Technologies", "ADS", "ACO GmbH"],
                        "description": "Parent company to check for coordinated moves"
                    },
                    "product_family": {
                        "type": "string",
                        "enum": ["core_spec_drains", "siteworks", "fog_separation"],
                        "description": "Product family to focus analysis on"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["last_quarter", "last_90_days", "last_6_months", "ytd"],
                        "description": "Time period for analysis (default: last_quarter)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for trade publications"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Competitor configuration
        self.competitors = {
            "core_spec_drains": {
                "primary": ["JR Smith", "Watts", "MiFab"],
                "secondary": ["Josam"]
            },
            "siteworks": {
                "primary": ["JR Smith", "Watts", "ABT", "ACO", "DuraTrench", "NDS"],
                "secondary": ["Josam", "Sioux Chief", "MiFab"]
            },
            "fog_separation": {
                "primary": ["Schier"],
                "secondary": ["Xerxes", "Canplas", "Highland Tank"]
            }
        }
        
        # Parent company mapping
        self.parent_companies = {
            "Morris": ["JR Smith", "Acorn", "Murdock", "Whitehall"],
            "Watts Water Technologies": ["Watts", "Josam", "Ames", "Febco", "Powers", "Bradley", "Haws"],
            "ADS": ["NDS"],
            "ACO GmbH": ["ACO"]
        }
        
        # Trade publication sources
        self.trade_sources = [
            {"name": "Supply House Times", "url": "https://www.supplyht.com", "rss": None},
            {"name": "PM Engineer", "url": "https://www.pmengineer.com", "rss": None},
            {"name": "Plumbing & Mechanical", "url": "https://www.pmmag.com", "rss": None},
            {"name": "Contractor Magazine", "url": "https://www.contractormag.com", "rss": None},
        ]
        
        # Initialize OpenAI client
        self.openai_client = None
        self._init_openai_client()
        
        # Simulated competitive intelligence database
        self._init_simulated_data()

    def _init_openai_client(self):
        """Initialize Azure OpenAI client for analysis."""
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
            elif endpoint:
                credential = DefaultAzureCredential()
                token_provider = get_bearer_token_provider(
                    credential, "https://cognitiveservices.azure.com/.default"
                )
                self.openai_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    azure_ad_token_provider=token_provider,
                    api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
                )
            logger.info("DrainsCIAgent: OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def _init_simulated_data(self):
        """Initialize simulated competitive intelligence data for demo/testing."""
        # Simulated product launches
        self.simulated_product_launches = [
            {
                "competitor": "JR Smith",
                "parent_company": "Morris",
                "product_family": "core_spec_drains",
                "product_name": "FS-200 Adjustable Floor Drain Series",
                "description": "Tool-free height adjustment for spec-grade floor drains",
                "launch_date": "2025-11-15",
                "source": "PM Engineer",
                "source_url": "https://pmengineer.com/articles/jr-smith-floor-drain",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Spec pressure on floor drain adjustability features"
            },
            {
                "competitor": "Watts",
                "parent_company": "Watts Water Technologies",
                "product_family": "core_spec_drains",
                "product_name": "Expanded Stainless Steel Drainage Line",
                "description": "Healthcare-focused stainless steel floor drains and trench drains",
                "launch_date": "2025-10-22",
                "source": "Supply House Times",
                "source_url": "https://supplyht.com/articles/watts-stainless",
                "confidence": "high",
                "signal_priority": 2,
                "implication": "Watts targeting healthcare vertical with premium materials"
            },
            {
                "competitor": "Schier",
                "parent_company": None,
                "product_family": "fog_separation",
                "product_name": "GB-250 Compact FOG Interceptor",
                "description": "Compact interceptor line with NSF 46 certification",
                "launch_date": "2025-12-01",
                "source": "NSF Database + Press Release",
                "source_url": "https://info.nsf.org/certified/",
                "confidence": "high",
                "signal_priority": 1,
                "implication": "Schier strengthening FOG compliance positioning ahead of 2026 EPA guidance"
            },
            {
                "competitor": "ACO",
                "parent_company": "ACO GmbH",
                "product_family": "siteworks",
                "product_name": "ACO Sport Multidrain System",
                "description": "Integrated trench drain system for athletic facilities",
                "launch_date": "2025-09-18",
                "source": "Contractor Magazine",
                "source_url": "https://contractormag.com/products/aco-sport",
                "confidence": "medium",
                "signal_priority": 3,
                "implication": "ACO expanding into specialty vertical markets"
            },
            {
                "competitor": "NDS",
                "parent_company": "ADS",
                "product_family": "siteworks",
                "product_name": "Pro Series Catch Basin Integration",
                "description": "Integrated trench drain + catch basin system launch",
                "launch_date": "2025-11-08",
                "source": "NDS Press Release",
                "source_url": "https://ndspro.com/news",
                "confidence": "medium",
                "signal_priority": 2,
                "implication": "ADS coordinating NDS product line for complete site drainage solutions"
            }
        ]
        
        # Simulated leadership changes
        self.simulated_leadership_changes = [
            {
                "competitor": "JR Smith",
                "parent_company": "Morris",
                "person": "Michael Chen",
                "previous_role": "VP Engineering at Watts",
                "new_role": "VP of Engineering, JR Smith",
                "date": "2025-10-01",
                "source": "LinkedIn",
                "confidence": "medium",
                "signal_priority": 4,
                "implication": "Talent flow from Watts to Morris - potential strategy insight transfer"
            },
            {
                "competitor": "Schier",
                "parent_company": None,
                "person": "Sarah Martinez",
                "previous_role": "Director of Regulatory Affairs, EPA",
                "new_role": "VP of Regulatory Strategy, Schier",
                "date": "2025-09-15",
                "source": "Company Press Release",
                "confidence": "high",
                "signal_priority": 3,
                "implication": "Schier positioning for regulatory changes - likely has EPA timing insight"
            }
        ]
        
        # Simulated certifications
        self.simulated_certifications = [
            {
                "competitor": "Schier",
                "certification": "NSF/ANSI 46",
                "product_line": "GB-250 Compact Interceptor Series",
                "date": "2025-11-28",
                "source": "NSF International Database",
                "confidence": "high",
                "signal_priority": 1
            },
            {
                "competitor": "Watts",
                "certification": "ASME A112.6.3",
                "product_line": "Floor Drain Accessories",
                "date": "2025-10-15",
                "source": "ASME + Watts Press",
                "confidence": "high",
                "signal_priority": 2
            }
        ]
        
        # Simulated manufacturing/facility news
        self.simulated_facility_news = [
            {
                "competitor": "ACO",
                "parent_company": "ACO GmbH",
                "news_type": "Facility Expansion",
                "description": "$15M manufacturing facility expansion in Ohio",
                "date": "2025-08-20",
                "source": "Construction Dive",
                "source_url": "https://constructiondive.com/news/aco-ohio",
                "confidence": "medium",
                "signal_priority": 3,
                "implication": "ACO increasing North American capacity - expect product availability improvements"
            }
        ]
        
        # Parent company coordination signals
        self.simulated_coordination = {
            "Morris": [
                {
                    "signal": "Product numbering alignment",
                    "brands_involved": ["JR Smith", "Acorn"],
                    "description": "Aligned product numbering system across JR Smith and Acorn lines",
                    "date": "2025-11-01",
                    "source": "Updated catalogs observed",
                    "confidence": "high",
                    "implication": "Morris simplifying spec writing across brands"
                }
            ],
            "Watts Water Technologies": [
                {
                    "signal": "Brand consolidation",
                    "brands_involved": ["Watts", "Josam"],
                    "description": "Josam products appearing under 'Watts Commercial Drainage' branding",
                    "date": "2025-10-15",
                    "source": "Watts investor presentation Q3, Supply House Times",
                    "confidence": "high",
                    "implication": "Watts simplifying brand architecture - may reduce distributor complexity"
                }
            ],
            "ADS": [
                {
                    "signal": "Integrated site drainage system",
                    "brands_involved": ["NDS"],
                    "description": "NDS positioning as complete site drainage solution with ADS storm/sanitary products",
                    "date": "2025-09-20",
                    "source": "ADS investor materials",
                    "confidence": "medium",
                    "implication": "ADS leveraging NDS for bundled contractor packages"
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
            "get_product_launches": self._get_product_launches,
            "get_leadership_changes": self._get_leadership_changes,
            "get_certification_updates": self._get_certification_updates,
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
        logger.info(f"Running quarterly analysis for period: {time_period}")
        
        # Gather all signals
        product_launches = self._get_product_launches(time_period=time_period)
        leadership = self._get_leadership_changes(time_period=time_period)
        certifications = self._get_certification_updates(time_period=time_period)
        
        # Check parent company coordination
        coordination_signals = []
        for parent in self.parent_companies.keys():
            coord = self._check_parent_company_coordination(parent_company=parent)
            if coord.get("signals"):
                coordination_signals.extend(coord["signals"])
        
        # Identify top 3 most significant changes
        all_signals = []
        for launch in product_launches.get("launches", []):
            all_signals.append({
                "type": "product_launch",
                "priority": launch.get("signal_priority", 5),
                "confidence": launch.get("confidence", "medium"),
                "description": f"{launch['competitor']}: {launch['product_name']}",
                "implication": launch.get("implication", ""),
                "source": launch.get("source", "")
            })
        
        for change in leadership.get("changes", []):
            all_signals.append({
                "type": "leadership",
                "priority": change.get("signal_priority", 5),
                "confidence": change.get("confidence", "medium"),
                "description": f"{change['competitor']}: {change['person']} - {change['new_role']}",
                "implication": change.get("implication", ""),
                "source": change.get("source", "")
            })
        
        for coord in coordination_signals:
            all_signals.append({
                "type": "parent_coordination",
                "priority": 2,
                "confidence": coord.get("confidence", "medium"),
                "description": f"{coord.get('parent_company', 'Unknown')}: {coord.get('signal', '')}",
                "implication": coord.get("implication", ""),
                "source": coord.get("source", "")
            })
        
        # Sort by priority and take top 3
        all_signals.sort(key=lambda x: x["priority"])
        top_3 = all_signals[:3]
        
        # Build report by product family
        highlights = {}
        for family in ["core_spec_drains", "siteworks", "fog_separation"]:
            family_launches = [l for l in product_launches.get("launches", []) 
                            if l.get("product_family") == family]
            highlights[family] = {
                "product_launches": len(family_launches),
                "key_items": [l["product_name"] for l in family_launches[:3]]
            }
        
        return {
            "report_type": "Quarterly Competitive Intelligence",
            "business_unit": "Drains",
            "period": time_period,
            "generated_at": datetime.now().isoformat(),
            "highlights_by_product_family": highlights,
            "top_3_significant_changes": top_3,
            "parent_company_coordination": coordination_signals,
            "total_signals_detected": len(all_signals),
            "implications": {
                "near_term": "Spec pressure on floor drain adjustability features; FOG compliance positioning intensifying",
                "mid_term": "Parent company consolidation may reduce SKU complexity for competitors, simplifying spec writing"
            },
            "data_sources": ["Simulated CI Database", "Trade Publication Monitoring", "Certification Databases"],
            "confidence_note": "High = primary + third-party source; Medium = primary only; Low = indirect/inferred"
        }

    def _analyze_competitor(self, competitor: str, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Deep dive analysis on a specific competitor."""
        logger.info(f"Analyzing competitor: {competitor}")
        
        # Find parent company
        parent = None
        for p, brands in self.parent_companies.items():
            if competitor in brands:
                parent = p
                break
        
        # Get competitor-specific data
        launches = [l for l in self.simulated_product_launches if l["competitor"] == competitor]
        leadership = [l for l in self.simulated_leadership_changes if l["competitor"] == competitor]
        certs = [c for c in self.simulated_certifications if c["competitor"] == competitor]
        
        # Get sister brands if part of parent company
        sister_brands = []
        if parent:
            sister_brands = [b for b in self.parent_companies[parent] if b != competitor]
        
        return {
            "competitor": competitor,
            "parent_company": parent,
            "sister_brands": sister_brands,
            "analysis_period": time_period,
            "product_launches": launches,
            "leadership_changes": leadership,
            "certifications": certs,
            "strategic_assessment": self._generate_competitor_assessment(competitor, parent, launches, leadership),
            "generated_at": datetime.now().isoformat()
        }

    def _generate_competitor_assessment(self, competitor: str, parent: str, launches: List, leadership: List) -> str:
        """Generate strategic assessment text for competitor."""
        assessment_parts = []
        
        if parent:
            assessment_parts.append(f"{competitor} operates as part of {parent}, enabling resource sharing and coordinated strategy.")
        
        if launches:
            assessment_parts.append(f"Active product development with {len(launches)} launches in period, focusing on {launches[0].get('product_family', 'multiple categories')}.")
        
        if leadership:
            assessment_parts.append(f"Leadership changes signal potential strategic shifts - monitor for direction changes.")
        
        if not assessment_parts:
            assessment_parts.append(f"Limited observable activity from {competitor} in this period. Continue monitoring.")
        
        return " ".join(assessment_parts)

    def _check_parent_company_coordination(self, parent_company: str, **kwargs) -> Dict[str, Any]:
        """Identify coordinated moves across brands owned by same parent company."""
        logger.info(f"Checking coordination for: {parent_company}")
        
        if parent_company not in self.parent_companies:
            return {"error": f"Unknown parent company: {parent_company}", 
                   "valid_parents": list(self.parent_companies.keys())}
        
        brands = self.parent_companies[parent_company]
        coordination = self.simulated_coordination.get(parent_company, [])
        
        # Enrich with parent company context
        enriched_signals = []
        for signal in coordination:
            enriched = signal.copy()
            enriched["parent_company"] = parent_company
            enriched_signals.append(enriched)
        
        return {
            "parent_company": parent_company,
            "brands_monitored": brands,
            "signals": enriched_signals,
            "signal_count": len(enriched_signals),
            "strategic_interpretation": self._interpret_coordination(parent_company, enriched_signals),
            "generated_at": datetime.now().isoformat()
        }

    def _interpret_coordination(self, parent: str, signals: List) -> str:
        """Generate interpretation of parent company coordination."""
        if not signals:
            return f"No significant coordination signals detected for {parent} in this period."
        
        interpretations = {
            "Morris": "Morris executing portfolio integration strategy - making it easier for architects to spec across their brands.",
            "Watts Water Technologies": "Watts simplifying brand architecture while maintaining spec-level differentiation. Watch for accelerated consolidation.",
            "ADS": "ADS leveraging NDS for complete site drainage packages, targeting contractor relationships.",
            "ACO GmbH": "ACO expanding North American footprint with manufacturing investment."
        }
        
        return interpretations.get(parent, f"Monitor {parent} for continued cross-brand coordination.")

    def _get_signal_summary(self, product_family: str = None, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Get prioritized signal summary for executive review."""
        logger.info(f"Getting signal summary for: {product_family or 'all families'}")
        
        # Filter launches by product family if specified
        launches = self.simulated_product_launches
        if product_family:
            launches = [l for l in launches if l.get("product_family") == product_family]
        
        # Sort by signal priority
        launches.sort(key=lambda x: x.get("signal_priority", 5))
        
        # Format as summary table
        signals = []
        for launch in launches:
            signals.append({
                "priority": launch.get("signal_priority"),
                "signal": launch.get("product_name"),
                "competitor": launch.get("competitor"),
                "confidence": launch.get("confidence"),
                "source": launch.get("source")
            })
        
        return {
            "product_family": product_family or "all",
            "period": time_period,
            "signals": signals,
            "signal_count": len(signals),
            "noise_filtered": "Routine SKU churn, cosmetic updates, standard price adjustments",
            "generated_at": datetime.now().isoformat()
        }

    def _search_trade_publications(self, query: str, time_period: str = "last_90_days", **kwargs) -> Dict[str, Any]:
        """Search trade publications for competitive intelligence."""
        logger.info(f"Searching trade publications for: {query}")
        
        # In production, this would call actual APIs or web scraping
        # For now, return simulated search results
        
        simulated_results = [
            {
                "source": "PM Engineer",
                "title": f"Industry Analysis: {query}",
                "date": "2025-12-15",
                "relevance": "high",
                "url": "https://pmengineer.com/articles/example",
                "snippet": f"Comprehensive coverage of {query} in commercial plumbing market..."
            },
            {
                "source": "Supply House Times",
                "title": f"Market Update: {query}",
                "date": "2025-11-28",
                "relevance": "high",
                "url": "https://supplyht.com/articles/example",
                "snippet": f"Latest developments in {query} affecting distributors..."
            },
            {
                "source": "Contractor Magazine",
                "title": f"Product Spotlight: {query}",
                "date": "2025-10-10",
                "relevance": "medium",
                "url": "https://contractormag.com/articles/example",
                "snippet": f"Contractor perspectives on {query}..."
            }
        ]
        
        return {
            "query": query,
            "period": time_period,
            "results": simulated_results,
            "result_count": len(simulated_results),
            "sources_searched": [s["name"] for s in self.trade_sources],
            "note": "Results from simulated database - production version would use live API/scraping",
            "generated_at": datetime.now().isoformat()
        }

    def _get_product_launches(self, product_family: str = None, competitor: str = None, 
                             time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Get product launches from competitors."""
        logger.info(f"Getting product launches: family={product_family}, competitor={competitor}")
        
        launches = self.simulated_product_launches
        
        if product_family:
            launches = [l for l in launches if l.get("product_family") == product_family]
        if competitor:
            launches = [l for l in launches if l.get("competitor") == competitor]
        
        return {
            "filter": {"product_family": product_family, "competitor": competitor},
            "period": time_period,
            "launches": launches,
            "launch_count": len(launches),
            "by_competitor": self._group_by(launches, "competitor"),
            "generated_at": datetime.now().isoformat()
        }

    def _get_leadership_changes(self, competitor: str = None, 
                                time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Get leadership changes at competitors."""
        logger.info(f"Getting leadership changes: competitor={competitor}")
        
        changes = self.simulated_leadership_changes
        
        if competitor:
            changes = [c for c in changes if c.get("competitor") == competitor]
        
        return {
            "filter": {"competitor": competitor},
            "period": time_period,
            "changes": changes,
            "change_count": len(changes),
            "generated_at": datetime.now().isoformat()
        }

    def _get_certification_updates(self, competitor: str = None,
                                   time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Get certification updates from competitors."""
        logger.info(f"Getting certification updates: competitor={competitor}")
        
        certs = self.simulated_certifications
        
        if competitor:
            certs = [c for c in certs if c.get("competitor") == competitor]
        
        return {
            "filter": {"competitor": competitor},
            "period": time_period,
            "certifications": certs,
            "certification_count": len(certs),
            "standards_monitored": ["ASME", "ASSE", "NSF", "IAPMO", "UPC/IPC"],
            "generated_at": datetime.now().isoformat()
        }

    def _generate_bu_report(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Generate formatted BU report for GM/PM distribution."""
        logger.info(f"Generating BU report for period: {time_period}")
        
        # Run full analysis
        analysis = self._run_quarterly_analysis(time_period=time_period)
        
        # Format as executive report
        report = {
            "report_title": "DRAINS COMPETITIVE INTELLIGENCE REPORT",
            "period": time_period,
            "prepared_for": "GM/PM Review",
            "generated_at": datetime.now().isoformat(),
            
            "executive_summary": """Competitive activity increased in Core Spec Drains with product innovation 
focus on installer productivity. FOG segment showing regulatory-driven positioning. Parent company 
coordination observed at Morris and Watts WWT.""",
            
            "highlights_by_product_family": analysis["highlights_by_product_family"],
            
            "top_3_significant_changes": analysis["top_3_significant_changes"],
            
            "potential_implications": analysis["implications"],
            
            "watch_list_next_quarter": [
                "Schier EPA guidance positioning",
                "Watts brand consolidation progress",
                "ACO Ohio facility completion and capacity impact"
            ],
            
            "sources": [
                "1. PM Engineer - JR Smith floor drain coverage (Dec 2025)",
                "2. Supply House Times - Watts stainless expansion (Oct 2025)",
                "3. NSF International Database - Schier certification (Nov 2025)",
                "4. Watts Q3 Investor Presentation - Brand consolidation",
                "Note: Third-party sources prioritized per CI methodology"
            ],
            
            "methodology_note": "High = primary + third-party corroboration; Medium = primary only; Low = indirect/inferred",
            
            "next_update": "Q1 2026"
        }
        
        return report

    def _group_by(self, items: List[Dict], key: str) -> Dict[str, int]:
        """Group items by a key and count."""
        result = {}
        for item in items:
            k = item.get(key, "Unknown")
            result[k] = result.get(k, 0) + 1
        return result

    # Web scraping methods (for production use)
    def _scrape_trade_publication(self, url: str, query: str) -> List[Dict]:
        """Scrape trade publication for articles (production method)."""
        if not WEB_SCRAPING_AVAILABLE:
            logger.warning("Web scraping not available - using simulated data")
            return []
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; ZurnElkayCI/1.0)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Implementation would vary by publication
            # This is a placeholder for actual scraping logic
            
            return []
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

    def _fetch_nsf_certifications(self, company: str) -> List[Dict]:
        """Fetch certifications from NSF database (production method)."""
        # In production, this would query NSF's public certification database
        # NSF provides an API at https://info.nsf.org/Certified/Common/
        logger.info(f"Would fetch NSF certifications for: {company}")
        return []
