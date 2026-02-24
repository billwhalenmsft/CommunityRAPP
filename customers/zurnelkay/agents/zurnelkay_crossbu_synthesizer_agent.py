"""
Agent: ZurnElkay Cross-BU CI Synthesizer
Purpose: Level 2 agent that aggregates BU reports and identifies portfolio-level patterns
Customer: Zurn Elkay Water Solutions

This is a LEVEL 2 synthesizer agent. It:
- Collects reports from all 5 Level 1 BU agents
- Identifies cross-BU coordination by parent companies
- Generates enterprise-level executive briefings
- Re-prioritizes signals from portfolio perspective

Parent Companies Tracked Across BUs:
- Watts Water Technologies: Drains, Wilkins, Drinking Water, Commercial Brass
- Morris Group: Sinks, Commercial Brass
- Lixil: Commercial Brass, Sinks
- Geberit: Commercial Brass, Drains
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from agents.basic_agent import BasicAgent

# Import all BU agents
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZurnElkayCrossbuSynthesizerAgent(BasicAgent):
    """
    Cross-BU CI Synthesizer for Zurn Elkay.
    
    Aggregates intelligence from all 5 BU agents and identifies
    portfolio-level patterns invisible to individual BUs.
    """

    def __init__(self):
        self.name = 'CrossBUSynthesizerAgent'
        self.metadata = {
            "name": self.name,
            "description": """Cross-BU Competitive Intelligence Synthesizer for Zurn Elkay. Aggregates reports 
from all 5 BU CI agents (Drains, Wilkins, Drinking Water, Sinks, Commercial Brass) and identifies 
portfolio-level competitive patterns. Detects coordinated moves by parent companies (Watts, Morris, 
Lixil, Geberit) across multiple product categories.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "synthesize_quarterly_report",
                            "detect_cross_bu_patterns",
                            "generate_executive_briefing",
                            "prioritize_enterprise_signals",
                            "compare_bu_competitive_pressure",
                            "get_parent_company_summary",
                            "get_all_bu_reports"
                        ],
                        "description": "The synthesis action to perform"
                    },
                    "parent_company": {
                        "type": "string",
                        "enum": ["Watts Water Technologies", "Morris Group", "Lixil", "Geberit", "Aalberts"],
                        "description": "Specific parent company to analyze"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["last_quarter", "last_90_days", "last_6_months", "ytd"],
                        "description": "Time period for analysis"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include strategic recommendations in output"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Initialize all BU agents
        self.bu_agents = {
            "drains": ZurnElkayDrainsCIAgent(),
            "wilkins": ZurnElkayWilkinsCIAgent(),
            "drinking_water": ZurnElkayDrinkingWaterCIAgent(),
            "sinks": ZurnElkaySinksCIAgent(),
            "commercial_brass": ZurnElkayCommercialBrassCIAgent()
        }
        
        # Parent company to BU mapping
        self.parent_bu_mapping = {
            "Watts Water Technologies": ["drains", "wilkins", "drinking_water", "commercial_brass"],
            "Morris Group": ["sinks", "commercial_brass"],
            "Lixil": ["commercial_brass", "sinks"],
            "Geberit": ["commercial_brass", "drains"],
            "Aalberts": ["wilkins"]
        }
        
        # Strategic themes to watch
        self.strategic_themes = {
            "platform_competition": {
                "description": "Companies building integrated platforms vs. selling products",
                "key_players": ["Sloan", "Kohler", "Geberit"],
                "bus_affected": ["commercial_brass"]
            },
            "digital_features": {
                "description": "IoT, connectivity, smart features becoming table stakes",
                "key_players": ["Watts", "Caleffi", "Sloan"],
                "bus_affected": ["wilkins", "commercial_brass", "drains"]
            },
            "portfolio_bundling": {
                "description": "Parent companies bundling products across brands",
                "key_players": ["Watts", "Morris Group"],
                "bus_affected": ["sinks", "wilkins", "commercial_brass"]
            },
            "vertical_focus": {
                "description": "Healthcare, education, hospitality vertical specialization",
                "key_players": ["Watts/Powers/Bradley", "Morris/Just/T&S"],
                "bus_affected": ["sinks", "drinking_water", "commercial_brass"]
            }
        }

    def perform(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute the requested synthesis action."""
        actions = {
            "synthesize_quarterly_report": self._synthesize_quarterly_report,
            "detect_cross_bu_patterns": self._detect_cross_bu_patterns,
            "generate_executive_briefing": self._generate_executive_briefing,
            "prioritize_enterprise_signals": self._prioritize_enterprise_signals,
            "compare_bu_competitive_pressure": self._compare_bu_competitive_pressure,
            "get_parent_company_summary": self._get_parent_company_summary,
            "get_all_bu_reports": self._get_all_bu_reports
        }
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available_actions": list(actions.keys())}
        
        try:
            return actions[action](**kwargs)
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return {"error": str(e), "action": action}

    def _collect_bu_reports(self, time_period: str = "last_quarter") -> Dict[str, Any]:
        """Collect quarterly reports from all BU agents."""
        reports = {}
        for bu_name, agent in self.bu_agents.items():
            try:
                reports[bu_name] = agent.perform("run_quarterly_analysis", time_period=time_period)
            except Exception as e:
                logger.error(f"Error collecting {bu_name} report: {e}")
                reports[bu_name] = {"error": str(e)}
        return reports

    def _synthesize_quarterly_report(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Synthesize all BU reports into enterprise view."""
        logger.info(f"Synthesizing quarterly report: {time_period}")
        
        # Collect all BU reports
        bu_reports = self._collect_bu_reports(time_period)
        
        # Aggregate top signals from all BUs
        all_signals = []
        for bu_name, report in bu_reports.items():
            if "error" not in report:
                top_changes = report.get("top_3_significant_changes", [])
                for signal in top_changes:
                    signal["source_bu"] = bu_name
                    all_signals.append(signal)
        
        # Sort by priority
        all_signals.sort(key=lambda x: x.get("priority", 5))
        
        # Detect cross-BU patterns
        cross_bu_patterns = self._detect_cross_bu_patterns()
        
        return {
            "report_type": "Enterprise Quarterly CI Synthesis",
            "period": time_period,
            "generated_at": datetime.now().isoformat(),
            
            "enterprise_summary": self._generate_enterprise_summary(bu_reports),
            
            "bu_reports_collected": list(bu_reports.keys()),
            "bu_report_status": {bu: "success" if "error" not in r else "failed" 
                                 for bu, r in bu_reports.items()},
            
            "top_5_enterprise_signals": all_signals[:5],
            
            "cross_bu_patterns": cross_bu_patterns.get("patterns", []),
            
            "strategic_themes_active": self._assess_strategic_themes(bu_reports),
            
            "watch_list": self._compile_enterprise_watch_list(bu_reports)
        }

    def _generate_enterprise_summary(self, bu_reports: Dict) -> str:
        """Generate enterprise-level summary paragraph."""
        active_themes = []
        
        # Check for platform competition
        brass_report = bu_reports.get("commercial_brass", {})
        if "platform" in str(brass_report.get("strategic_theme", "")).lower():
            active_themes.append("platform competition intensifying in Commercial Brass")
        
        # Check for Watts coordination
        watts_mentions = 0
        for bu, report in bu_reports.items():
            if "watts" in str(report).lower():
                watts_mentions += 1
        if watts_mentions >= 3:
            active_themes.append("Watts Water Technologies coordinating across multiple categories")
        
        # Check for healthcare focus
        sinks_report = bu_reports.get("sinks", {})
        if "healthcare" in str(sinks_report).lower():
            active_themes.append("healthcare vertical seeing elevated competitive activity")
        
        if active_themes:
            return f"Key enterprise themes this quarter: {'; '.join(active_themes)}. " \
                   f"All 5 BUs reported. Cross-BU pattern analysis identifies coordinated " \
                   f"competitor moves requiring portfolio-level response."
        else:
            return "Quarterly synthesis complete. No critical cross-BU patterns detected. " \
                   "Individual BU competitive dynamics remain within normal parameters."

    def _detect_cross_bu_patterns(self, parent_company: str = None, **kwargs) -> Dict[str, Any]:
        """Detect coordinated moves across BUs by parent companies."""
        logger.info(f"Detecting cross-BU patterns: {parent_company or 'all'}")
        
        patterns = []
        
        # Check each parent company
        companies_to_check = [parent_company] if parent_company else list(self.parent_bu_mapping.keys())
        
        for company in companies_to_check:
            if company not in self.parent_bu_mapping:
                continue
                
            affected_bus = self.parent_bu_mapping[company]
            coordination_signals = []
            
            # Collect coordination signals from each affected BU
            for bu_name in affected_bus:
                agent = self.bu_agents.get(bu_name)
                if agent and company in agent.parent_companies:
                    result = agent.perform("check_parent_company_coordination", parent_company=company)
                    signals = result.get("coordination_signals", [])
                    for signal in signals:
                        signal["detected_in_bu"] = bu_name
                        coordination_signals.append(signal)
            
            if coordination_signals:
                # Determine confidence based on number of BUs showing signals
                bus_with_signals = set(s["detected_in_bu"] for s in coordination_signals)
                if len(bus_with_signals) >= 3:
                    confidence = "high"
                elif len(bus_with_signals) == 2:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                patterns.append({
                    "parent_company": company,
                    "bus_affected": list(bus_with_signals),
                    "signal_count": len(coordination_signals),
                    "confidence": confidence,
                    "signals": coordination_signals,
                    "interpretation": self._interpret_coordination(company, coordination_signals)
                })
        
        return {
            "patterns": patterns,
            "total_patterns_detected": len(patterns),
            "highest_concern": patterns[0] if patterns else None,
            "generated_at": datetime.now().isoformat()
        }

    def _interpret_coordination(self, company: str, signals: List[Dict]) -> str:
        """Generate interpretation of coordination pattern."""
        if company == "Watts Water Technologies":
            return "Watts executing portfolio strategy - digital platform, brand consolidation, " \
                   "and vertical market focus are coordinated enterprise initiatives, not BU tactics."
        elif company == "Morris Group":
            return "Morris leveraging Just + T&S for bundled solutions. " \
                   "Expect integrated product packages targeting healthcare and foodservice."
        elif company == "Lixil":
            return "Lixil Americas reorganization suggests commercial market push. " \
                   "Monitor for Grohe commercial products entering US market."
        elif company == "Geberit":
            return "Geberit digital ecosystem investment signals specification influence play. " \
                   "Expect enhanced BIM tools and digital specification platforms."
        else:
            return f"Coordination detected for {company}. Monitor for portfolio-level strategy."

    def _generate_executive_briefing(self, time_period: str = "last_quarter", 
                                      include_recommendations: bool = True, **kwargs) -> Dict[str, Any]:
        """Generate CEO/COO-level executive briefing."""
        logger.info("Generating executive briefing")
        
        # Get synthesized report
        synthesis = self._synthesize_quarterly_report(time_period)
        
        # Get competitive pressure comparison
        pressure = self._compare_bu_competitive_pressure()
        
        briefing = {
            "briefing_title": "ZURN ELKAY COMPETITIVE INTELLIGENCE EXECUTIVE BRIEFING",
            "period": time_period,
            "prepared_for": "CEO/COO Review",
            "generated_at": datetime.now().isoformat(),
            
            "executive_summary": synthesis["enterprise_summary"],
            
            "critical_findings": [
                {
                    "finding": "Platform competition emerging in Commercial Brass",
                    "detail": "Sloan Connect and Kohler Wellnected represent shift from product to platform competition",
                    "business_impact": "Customers adopting competitor platforms creates switching cost barriers",
                    "urgency": "HIGH"
                },
                {
                    "finding": "Watts portfolio coordination accelerating",
                    "detail": "Digital features, brand consolidation, healthcare bundling observed across 4 BUs",
                    "business_impact": "Watts competing at portfolio level while we compete at BU level",
                    "urgency": "HIGH"
                },
                {
                    "finding": "Healthcare vertical intensifying",
                    "detail": "Morris (Just+T&S), Watts (Powers+Bradley), and Sloan all targeting healthcare",
                    "business_impact": "Bundled solutions becoming expected in healthcare specifications",
                    "urgency": "MEDIUM"
                }
            ],
            
            "top_5_signals": synthesis["top_5_enterprise_signals"],
            
            "cross_bu_coordination_detected": synthesis["cross_bu_patterns"],
            
            "bu_competitive_pressure": pressure["rankings"],
            
            "strategic_themes": synthesis["strategic_themes_active"],
            
            "watch_list": synthesis["watch_list"]
        }
        
        if include_recommendations:
            briefing["strategic_recommendations"] = [
                {
                    "recommendation": "Evaluate platform/ecosystem strategy",
                    "rationale": "Sloan and Kohler establishing platform standards. Risk of being locked out.",
                    "priority": 1,
                    "owner_suggestion": "VP Strategy + Commercial Brass GM"
                },
                {
                    "recommendation": "Assess cross-BU bundling opportunities",
                    "rationale": "Competitors bundling across brands. Zurn Elkay has portfolio but operates in silos.",
                    "priority": 2,
                    "owner_suggestion": "BU GMs + VP Sales"
                },
                {
                    "recommendation": "Accelerate digital feature roadmap in Wilkins",
                    "rationale": "Caleffi and Watts making digital features table stakes in valves.",
                    "priority": 2,
                    "owner_suggestion": "Wilkins GM + VP Engineering"
                },
                {
                    "recommendation": "Develop healthcare vertical strategy",
                    "rationale": "Multiple competitors targeting healthcare with bundled solutions.",
                    "priority": 3,
                    "owner_suggestion": "VP Strategy + Sinks GM + Commercial Brass GM"
                }
            ]
        
        briefing["sources"] = [
            "Aggregated from 5 BU CI Agent reports",
            "Cross-BU pattern analysis engine",
            "Parent company coordination tracking",
            "Note: All underlying sources documented in BU reports"
        ]
        
        return briefing

    def _prioritize_enterprise_signals(self, **kwargs) -> Dict[str, Any]:
        """Re-prioritize all signals from enterprise perspective."""
        logger.info("Prioritizing enterprise signals")
        
        bu_reports = self._collect_bu_reports()
        
        all_signals = []
        for bu_name, report in bu_reports.items():
            if "error" not in report:
                # Get top changes
                for signal in report.get("top_3_significant_changes", []):
                    signal["source_bu"] = bu_name
                    signal["original_priority"] = signal.get("priority", 5)
                    
                    # Re-score for enterprise relevance
                    enterprise_boost = 0
                    
                    # Boost if involves major parent company
                    desc = str(signal.get("description", "")).lower()
                    if any(pc.lower() in desc for pc in ["watts", "sloan", "kohler"]):
                        enterprise_boost -= 1  # Lower number = higher priority
                    
                    # Boost if it's a platform/ecosystem signal
                    if any(term in desc for term in ["platform", "ecosystem", "connected"]):
                        enterprise_boost -= 1
                    
                    # Boost if cross-BU implication
                    if "portfolio" in str(signal.get("implication", "")).lower():
                        enterprise_boost -= 1
                    
                    signal["enterprise_priority"] = max(1, signal["original_priority"] + enterprise_boost)
                    all_signals.append(signal)
        
        # Sort by enterprise priority
        all_signals.sort(key=lambda x: x["enterprise_priority"])
        
        return {
            "enterprise_prioritized_signals": all_signals[:10],
            "total_signals_analyzed": len(all_signals),
            "prioritization_factors": [
                "Major parent company involvement (+boost)",
                "Platform/ecosystem implications (+boost)",
                "Cross-BU strategic impact (+boost)"
            ],
            "generated_at": datetime.now().isoformat()
        }

    def _compare_bu_competitive_pressure(self, **kwargs) -> Dict[str, Any]:
        """Compare competitive intensity across BUs."""
        logger.info("Comparing BU competitive pressure")
        
        bu_reports = self._collect_bu_reports()
        
        pressure_scores = {}
        for bu_name, report in bu_reports.items():
            if "error" not in report:
                score = 0
                
                # Count signals
                signals = report.get("top_3_significant_changes", [])
                score += len(signals) * 2
                
                # Check for high-priority signals
                high_priority = [s for s in signals if s.get("priority", 5) == 1]
                score += len(high_priority) * 3
                
                # Check for platform competition (highest pressure)
                if "platform" in str(report).lower():
                    score += 5
                
                # Check for parent company coordination
                if "coordination" in str(report).lower():
                    score += 3
                
                pressure_scores[bu_name] = {
                    "score": score,
                    "signal_count": len(signals),
                    "high_priority_count": len(high_priority)
                }
        
        # Rank by score
        rankings = sorted(pressure_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        return {
            "rankings": [
                {
                    "rank": i + 1,
                    "bu": bu,
                    "pressure_score": data["score"],
                    "signal_count": data["signal_count"],
                    "assessment": self._assess_pressure_level(data["score"])
                }
                for i, (bu, data) in enumerate(rankings)
            ],
            "methodology": "Score based on signal count, priority levels, platform competition, and coordination patterns",
            "generated_at": datetime.now().isoformat()
        }

    def _assess_pressure_level(self, score: int) -> str:
        """Assess pressure level from score."""
        if score >= 15:
            return "HIGH - Significant competitive activity requiring strategic response"
        elif score >= 10:
            return "MEDIUM - Elevated activity, monitor closely"
        else:
            return "NORMAL - Standard competitive dynamics"

    def _assess_strategic_themes(self, bu_reports: Dict) -> List[Dict]:
        """Assess which strategic themes are active."""
        active = []
        
        for theme_name, theme_data in self.strategic_themes.items():
            # Check if theme is active in any BU
            evidence = []
            for bu in theme_data["bus_affected"]:
                report = bu_reports.get(bu, {})
                report_str = str(report).lower()
                
                # Check for theme keywords
                if theme_name.replace("_", " ") in report_str or \
                   any(player.lower() in report_str for player in theme_data["key_players"]):
                    evidence.append(bu)
            
            if evidence:
                active.append({
                    "theme": theme_name,
                    "description": theme_data["description"],
                    "bus_showing_evidence": evidence,
                    "key_players": theme_data["key_players"]
                })
        
        return active

    def _compile_enterprise_watch_list(self, bu_reports: Dict) -> List[str]:
        """Compile enterprise-level watch list from all BUs."""
        watch_items = []
        
        # Collect watch lists from all BUs
        for bu_name, report in bu_reports.items():
            bu_watch = report.get("watch_list", [])
            for item in bu_watch:
                watch_items.append(f"[{bu_name.upper()}] {item}")
        
        # Add enterprise-level items
        watch_items.extend([
            "[ENTERPRISE] Watts Q4 earnings - portfolio strategy indicators",
            "[ENTERPRISE] Sloan Connect adoption rates in key accounts",
            "[ENTERPRISE] Morris Group healthcare bundling expansion"
        ])
        
        return watch_items[:10]  # Top 10

    def _get_parent_company_summary(self, parent_company: str = None, **kwargs) -> Dict[str, Any]:
        """Get summary of parent company activity across all BUs."""
        if parent_company and parent_company not in self.parent_bu_mapping:
            return {"error": f"Unknown parent company: {parent_company}"}
        
        companies = [parent_company] if parent_company else list(self.parent_bu_mapping.keys())
        
        summaries = {}
        for company in companies:
            affected_bus = self.parent_bu_mapping[company]
            
            all_signals = []
            for bu_name in affected_bus:
                agent = self.bu_agents.get(bu_name)
                if agent and company in agent.parent_companies:
                    result = agent.perform("check_parent_company_coordination", parent_company=company)
                    for signal in result.get("coordination_signals", []):
                        signal["bu"] = bu_name
                        all_signals.append(signal)
            
            summaries[company] = {
                "brands": self._get_company_brands(company),
                "bus_affected": affected_bus,
                "total_signals": len(all_signals),
                "signals": all_signals
            }
        
        return {
            "parent_company_summaries": summaries,
            "generated_at": datetime.now().isoformat()
        }

    def _get_company_brands(self, company: str) -> List[str]:
        """Get all brands for a parent company across all BU agents."""
        brands = set()
        for bu_name in self.parent_bu_mapping.get(company, []):
            agent = self.bu_agents.get(bu_name)
            if agent and company in agent.parent_companies:
                brands.update(agent.parent_companies[company])
        return list(brands)

    def _get_all_bu_reports(self, time_period: str = "last_quarter", **kwargs) -> Dict[str, Any]:
        """Get individual reports from all BU agents."""
        reports = {}
        for bu_name, agent in self.bu_agents.items():
            reports[bu_name] = agent.perform("generate_bu_report", time_period=time_period)
        
        return {
            "bu_reports": reports,
            "report_count": len(reports),
            "generated_at": datetime.now().isoformat()
        }
