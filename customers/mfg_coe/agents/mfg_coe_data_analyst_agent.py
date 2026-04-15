"""
Agent: MfgCoE Data Analyst Agent
Purpose: Data Analyst persona for the Discrete Manufacturing CoE.
         Aggregates outcomes, spots patterns, tracks KPI trends, generates
         insights from accumulated CoE work, and produces the data that
         powers the Outcomes Intelligence Dashboard.

         Over time becomes the source of truth for: what process areas generate
         the most work, average time-to-outcome, outcome confidence trends,
         RAPP pipeline ROI, and patterns in Discrete Manufacturing AI adoption.

Actions:
  analyze_outcomes       — Aggregate and analyze all outcome definitions on file
  generate_weekly_report — Weekly metrics: issues moved, outcomes validated, blockers
  detect_patterns        — Find recurring themes across issues and outcomes
  kpi_trend              — Track KPI baseline vs target for a specific outcome
  pipeline_metrics       — RAPP pipeline velocity: time per stage, blockage rate
  rapp_roi               — Estimate ROI signal from accumulated CoE activity
  dashboard_data         — Return structured JSON for Outcomes Intelligence Dashboard
  generate_insight       — Natural language insight from a dataset
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTCOMES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "outcomes")
)

PROCESS_AREAS = [
    "warranty", "case_management", "field_service", "returns_rma",
    "dealer_management", "crm", "order_management", "default",
]


class MfgCoEDataAnalystAgent(BasicAgent):
    """
    Data Analyst — aggregates CoE activity into patterns, metrics, and insights.
    Powers the Outcomes Intelligence Dashboard. Runs in the Daily Wrap-Up to
    generate trend reports. Feeds the Content Strategist with data for executive
    summaries.
    """

    def __init__(self):
        self.name = "MfgCoEDataAnalyst"
        self.metadata = {
            "name": self.name,
            "description": (
                "Data Analyst agent — aggregates CoE outcome data, detects patterns, "
                "tracks KPI trends, measures pipeline velocity, and produces insights for "
                "the Outcomes Intelligence Dashboard and weekly reports. "
                "Runs autonomously in Daily Wrap-Up. Powers ROI reporting for the RAPP toolset."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "analyze_outcomes",
                            "generate_weekly_report",
                            "detect_patterns",
                            "kpi_trend",
                            "pipeline_metrics",
                            "rapp_roi",
                            "dashboard_data",
                            "generate_insight",
                        ],
                        "description": "Analytics action to perform",
                    },
                    "issue_number": {"type": "integer", "description": "Specific issue to analyze"},
                    "process_area": {"type": "string", "description": "Filter by process area"},
                    "time_period": {"type": "string", "description": "Time period: 'week', 'month', 'all'"},
                    "dataset": {"type": "string", "description": "Raw data or description to generate insight from"},
                    "context": {"type": "string", "description": "Additional context"},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "dashboard_data")
        handlers = {
            "analyze_outcomes": self._analyze_outcomes,
            "generate_weekly_report": self._generate_weekly_report,
            "detect_patterns": self._detect_patterns,
            "kpi_trend": self._kpi_trend,
            "pipeline_metrics": self._pipeline_metrics,
            "rapp_roi": self._rapp_roi,
            "dashboard_data": self._dashboard_data,
            "generate_insight": self._generate_insight,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("DataAnalyst error in %s: %s", action, e)
            return json.dumps({"error": str(e)})

    def _read_outcome_files(self) -> List[Dict]:
        os.makedirs(OUTCOMES_DIR, exist_ok=True)
        outcomes = []
        for f in Path(OUTCOMES_DIR).glob("outcome_*.md"):
            try:
                lines = f.read_text(encoding="utf-8").split("\n")
                issue_num = None
                confidence = None
                process_area = "unknown"
                status = "draft"
                date_framed = None

                for line in lines:
                    if line.startswith("**Issue:**"):
                        try:
                            issue_num = int(line.split("#")[1].strip())
                        except Exception:
                            pass
                    if "Confidence Level:" in line:
                        try:
                            confidence = int(line.split("(")[1].split("/")[0])
                        except Exception:
                            pass
                    if "**Date Framed:**" in line:
                        date_framed = line.split("**Date Framed:**")[-1].strip()
                    if "Status:" in line and "Draft" in line:
                        status = "draft"
                    if "Status:" in line and "Confirmed" in line:
                        status = "confirmed"

                # Infer process area from filename
                fname = f.name.lower()
                for area in PROCESS_AREAS:
                    if area.replace("_", "") in fname or area.split("_")[0] in fname:
                        process_area = area
                        break

                outcomes.append({
                    "file": f.name,
                    "issue_number": issue_num,
                    "confidence": confidence,
                    "process_area": process_area,
                    "status": status,
                    "date_framed": date_framed,
                })
            except Exception:
                pass
        return outcomes

    def _analyze_outcomes(self, **kwargs) -> str:
        outcomes = self._read_outcome_files()
        process_area = kwargs.get("process_area")
        if process_area:
            outcomes = [o for o in outcomes if o["process_area"] == process_area]

        total = len(outcomes)
        confirmed = sum(1 for o in outcomes if o["status"] == "confirmed")
        avg_confidence = (
            sum(o["confidence"] for o in outcomes if o["confidence"]) / max(1, sum(1 for o in outcomes if o["confidence"]))
        )
        area_counts = {}
        for o in outcomes:
            area_counts[o["process_area"]] = area_counts.get(o["process_area"], 0) + 1

        top_area = max(area_counts, key=area_counts.get) if area_counts else "none"

        return json.dumps({
            "status": "ok",
            "total_outcomes": total,
            "confirmed": confirmed,
            "draft": total - confirmed,
            "avg_confidence_score": round(avg_confidence, 1),
            "process_area_distribution": area_counts,
            "top_process_area": top_area,
            "summary": (
                f"{total} outcome definition(s) on file. "
                f"{confirmed} confirmed, {total - confirmed} draft. "
                f"Avg confidence: {round(avg_confidence, 1)}/100. "
                f"Most active area: {top_area.replace('_', ' ').title()}."
            ),
            "persona": "data-analyst",
        }, indent=2)

    def _generate_weekly_report(self, **kwargs) -> str:
        outcomes = self._read_outcome_files()
        date = datetime.utcnow().strftime("%B %d, %Y")

        report = (
            f"## 📊 CoE Weekly Data Report — {date}\n\n"
            f"### Outcome Definitions\n"
            f"- **Total on file:** {len(outcomes)}\n"
            f"- **Confirmed:** {sum(1 for o in outcomes if o['status'] == 'confirmed')}\n"
            f"- **Draft (awaiting Bill):** {sum(1 for o in outcomes if o['status'] == 'draft')}\n\n"
            f"### Pipeline Activity\n"
            f"- Issues blocked for outcome: *check GitHub issues with needs-bill label*\n"
            f"- Issues advanced this week: *check GitHub activity feed*\n\n"
            f"### Insight\n"
            f"[Data Analyst: add one natural-language observation about trends this week]\n\n"
            f"### Recommended Actions\n"
            f"- [ ] Review draft outcome definitions older than 7 days\n"
            f"- [ ] Confirm or reject blocked issues\n"
            f"- [ ] Check if any validated outcomes need executive summary\n\n"
            f"---\n*Generated by CoE Data Analyst | {date}*"
        )

        return json.dumps({
            "status": "ok",
            "summary": f"Weekly report generated. {len(outcomes)} outcomes on file.",
            "report": report,
            "persona": "data-analyst",
        }, indent=2)

    def _detect_patterns(self, **kwargs) -> str:
        outcomes = self._read_outcome_files()
        area_counts = {}
        for o in outcomes:
            area_counts[o["process_area"]] = area_counts.get(o["process_area"], 0) + 1

        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        patterns = []
        if sorted_areas:
            top = sorted_areas[0]
            patterns.append(f"Most active process area: **{top[0].replace('_', ' ').title()}** ({top[1]} outcomes)")
        if len(sorted_areas) > 1:
            patterns.append(f"Second most active: **{sorted_areas[1][0].replace('_', ' ').title()}** ({sorted_areas[1][1]} outcomes)")

        low_confidence = [o for o in outcomes if o["confidence"] and o["confidence"] < 35]
        if low_confidence:
            patterns.append(f"{len(low_confidence)} outcome(s) had LOW confidence — these needed Bill's input to unblock")

        patterns_md = "\n".join(f"- {p}" for p in patterns) if patterns else "- Not enough data yet. Patterns emerge after 5+ outcomes."

        return json.dumps({
            "status": "ok",
            "patterns": patterns,
            "patterns_markdown": f"## 🔍 Detected Patterns\n\n{patterns_md}",
            "summary": f"Pattern analysis complete. {len(patterns)} pattern(s) detected from {len(outcomes)} outcomes.",
            "persona": "data-analyst",
        }, indent=2)

    def _kpi_trend(self, **kwargs) -> str:
        issue = kwargs.get("issue_number")
        return json.dumps({
            "status": "ok",
            "summary": "KPI trend tracking requires real baseline data. Once outcome is confirmed and KPI baselines are set by Bill, this agent will track actuals vs targets.",
            "template": {
                "kpi": "[KPI name]",
                "baseline": None,
                "target": None,
                "current": None,
                "trend": "insufficient_data",
                "note": "Set baselines in the outcome definition to enable tracking.",
            },
            "persona": "data-analyst",
        }, indent=2)

    def _pipeline_metrics(self, **kwargs) -> str:
        return json.dumps({
            "status": "ok",
            "summary": "Pipeline metrics require GitHub API access at runtime. Metrics tracked: time per stage, blockage rate, avg days blocked.",
            "metrics_schema": {
                "avg_days_raw_idea_to_outcome_defined": None,
                "avg_days_outcome_defined_to_use_case": None,
                "avg_days_use_case_to_tech_solution": None,
                "blockage_rate_pct": None,
                "issues_blocked_7_plus_days": None,
                "validated_this_month": None,
            },
            "note": "Run this action from coe_runner.py after GitHub issue data is loaded to populate metrics.",
            "persona": "data-analyst",
        }, indent=2)

    def _rapp_roi(self, **kwargs) -> str:
        outcomes = self._read_outcome_files()
        validated = sum(1 for o in outcomes if o["status"] == "confirmed")
        return json.dumps({
            "status": "ok",
            "summary": f"RAPP ROI signal: {validated} confirmed outcomes from {len(outcomes)} total definitions. ROI strengthens as KPI baselines and actuals are set.",
            "roi_indicators": {
                "outcomes_defined": len(outcomes),
                "outcomes_confirmed": validated,
                "outcomes_with_kpi_targets": 0,
                "kpi_targets_met": 0,
                "roi_narrative": "Not enough validated KPI data yet. As outcomes move from draft→confirmed and KPIs are tracked, this will show real ROI evidence.",
            },
            "persona": "data-analyst",
        }, indent=2)

    def _dashboard_data(self, **kwargs) -> str:
        outcomes = self._read_outcome_files()
        area_counts = {}
        for o in outcomes:
            area_counts[o["process_area"]] = area_counts.get(o["process_area"], 0) + 1

        return json.dumps({
            "status": "ok",
            "summary": f"Dashboard data ready. {len(outcomes)} outcomes, {len(area_counts)} process areas.",
            "dashboard": {
                "total_outcomes": len(outcomes),
                "confirmed": sum(1 for o in outcomes if o["status"] == "confirmed"),
                "draft": sum(1 for o in outcomes if o["status"] == "draft"),
                "avg_confidence": round(
                    sum(o["confidence"] for o in outcomes if o["confidence"]) / max(1, sum(1 for o in outcomes if o["confidence"])), 1
                ),
                "process_area_distribution": area_counts,
                "recent_outcomes": [
                    {"file": o["file"], "issue": o["issue_number"], "area": o["process_area"], "status": o["status"]}
                    for o in outcomes[-5:]
                ],
                "as_of": datetime.utcnow().isoformat(),
            },
            "persona": "data-analyst",
        }, indent=2)

    def _generate_insight(self, **kwargs) -> str:
        dataset = kwargs.get("dataset", "")
        context = kwargs.get("context", "")
        insight = (
            f"## 💡 Data Insight\n\n"
            f"**Dataset:** {dataset[:200] if dataset else '[No dataset provided]'}\n\n"
            f"**Observation:** [Data Analyst: state one clear, specific finding. "
            f"Format: 'X% of [something] show [pattern], suggesting [implication].']\n\n"
            f"**So what:** [Why this matters for the CoE or for Bill's work.]\n\n"
            f"**Recommended action:** [One specific, actionable next step.]\n\n"
            f"---\n*Data Analyst Agent | {datetime.utcnow().strftime('%Y-%m-%d')}*"
        )
        return json.dumps({
            "status": "ok",
            "summary": "Insight template generated. Populate with real data observations.",
            "insight": insight,
            "persona": "data-analyst",
        }, indent=2)
