# Zurn Elkay Competitive Intelligence System

A multi-agent AI system for automated quarterly competitive intelligence across Zurn Elkay's five business units.

## Overview

This system automates the collection, analysis, and synthesis of competitive intelligence for Zurn Elkay Water Solutions. It monitors competitors, tracks parent company coordination, and generates executive-ready reports.

### Business Value

| Before | After |
|--------|-------|
| Weeks of manual data gathering | Hours of automated collection |
| Inconsistent BU methodologies | Standardized framework across all 5 BUs |
| Missing coordinated competitor moves | Parent company tracking across portfolios |
| Uncertain source quality | Every item attributed with confidence levels |
| Manual report formatting | Executive-ready outputs |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               LEVEL 0: CI ORCHESTRATOR                          │
│   ZurnElkayCIOrchestratorAgent                                  │
│   • Coordinates all agents • Validates quality • Manages QA     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               LEVEL 2: CROSS-BU SYNTHESIZER                     │
│   ZurnElkayCrossbuSynthesizerAgent                              │
│   • Aggregates reports • Detects cross-BU patterns             │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────┬─────────┼─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Drains  │ │ Wilkins │ │Drinking │ │  Sinks  │ │Commercial│
│   CI    │ │   CI    │ │ Water   │ │   CI    │ │  Brass   │
│  Agent  │ │  Agent  │ │   CI    │ │  Agent  │ │   CI     │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Agents

### Level 1: Business Unit Agents

| Agent | BU | Key Competitors | Parent Companies Tracked |
|-------|-----|-----------------|-------------------------|
| `ZurnElkayDrainsCIAgent` | Drains | JR Smith, Watts, MiFab, Schier | Morris, Watts WWT, ADS |
| `ZurnElkayWilkinsCIAgent` | Wilkins | Watts, Caleffi, Honeywell, Apollo | Watts WWT, Aalberts |
| `ZurnElkayDrinkingWaterCIAgent` | Drinking Water | Elkay, Oasis, Halsey Taylor, 3M | Lixil |
| `ZurnElkaySinksCIAgent` | Sinks | Just Mfg, T&S Brass, Kohler, Bradley | Morris, Lixil |
| `ZurnElkayCommercialBrassCIAgent` | Commercial Brass | Sloan, Kohler, Bradley, TOTO | Watts WWT, Lixil, Geberit |

### Level 2: Synthesizer

`ZurnElkayCrossbuSynthesizerAgent` aggregates all BU reports and identifies:
- Cross-BU patterns invisible to individual agents
- Coordinated parent company moves
- Enterprise-level strategic signals

### Level 0: Orchestrator

`ZurnElkayCIOrchestratorAgent` manages:
- Workflow execution (quarterly and on-demand)
- Quality validation of all outputs
- Error handling and retries
- Audit logging

## Quick Start

### 1. Import Agents

```python
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent
from agents.zurnelkay_crossbu_synthesizer_agent import ZurnElkayCrossbuSynthesizerAgent
from agents.zurnelkay_ci_orchestrator_agent import ZurnElkayCIOrchestratorAgent
```

### 2. Run Single BU Analysis

```python
drains = ZurnElkayDrainsCIAgent()
result = drains.perform("run_quarterly_analysis")
```

### 3. Run Full Quarterly Workflow

```python
orchestrator = ZurnElkayCIOrchestratorAgent()
quarterly = orchestrator.run_quarterly_workflow(quarter="Q4", year=2025)
```

## Available Actions

### BU Agent Actions (All 5)

| Action | Description |
|--------|-------------|
| `run_quarterly_analysis` | Full quarterly competitive analysis |
| `generate_bu_report` | Executive-ready BU report |
| `analyze_competitor` | Deep dive on specific competitor |
| `check_parent_company_coordination` | Check for coordinated parent moves |
| `get_product_launches` | Recent product launches |
| `get_leadership_changes` | Executive/leadership changes |
| `get_certification_updates` | Certification/compliance changes |
| `get_signal_summary` | Summary of all signals |
| `search_trade_publications` | Search trade pubs for intel |

### BU-Specific Actions

| Agent | Action | Description |
|-------|--------|-------------|
| Wilkins | `get_digital_innovation` | Digital/IoT feature tracking |
| Wilkins | `get_certification_changes` | Regulatory certification tracking |
| Drinking Water | `check_nsf_certifications` | NSF certification database check |
| Drinking Water | `get_public_sector_wins` | K-12, healthcare, government wins |
| Sinks | `get_healthcare_innovations` | Healthcare-specific innovations |
| Sinks | `get_ada_compliance_updates` | ADA compliance tracking |
| Commercial Brass | `get_platform_launches` | Platform/ecosystem launches |
| Commercial Brass | `get_touchless_technology` | Touchless tech innovations |

### Synthesizer Actions

| Action | Description |
|--------|-------------|
| `synthesize_quarterly_report` | Aggregate all BU reports |
| `detect_cross_bu_patterns` | Find cross-BU patterns |
| `generate_executive_briefing` | CEO/COO-ready briefing |
| `get_parent_company_summary` | Parent company activity across BUs |
| `compare_bu_competitive_pressure` | Compare competitive pressure by BU |

### Orchestrator Actions

| Action | Description |
|--------|-------------|
| `run_quarterly_workflow` | Execute full quarterly cycle |
| `run_bu_report` | Run single BU on demand |
| `health_check` | Check all agent health |
| `get_system_status` | Overall system status |
| `validate_report` | QA validate a report |
| `run_parent_company_alert` | Quick parent company check |

## Parent Companies Tracked

| Parent Company | BUs Affected |
|----------------|--------------|
| Watts Water Technologies | Drains, Wilkins, Drinking Water, Commercial Brass |
| Morris Group | Sinks, Commercial Brass |
| Lixil | Commercial Brass, Sinks |
| Geberit | Commercial Brass, Drains |
| Aalberts | Wilkins |

## Confidence Calibration

All outputs include confidence levels:

| Level | Definition |
|-------|------------|
| **High** | Verified against official databases or multiple independent sources |
| **Medium** | Single reliable primary source (company announcement, trade pub) |
| **Low** | Inference, unverified, or indirect source |

## Files

### Agent Implementations
- `agents/zurnelkay_drains_ci_agent.py`
- `agents/zurnelkay_wilkins_ci_agent.py`
- `agents/zurnelkay_drinking_water_ci_agent.py`
- `agents/zurnelkay_sinks_ci_agent.py`
- `agents/zurnelkay_commercial_brass_ci_agent.py`
- `agents/zurnelkay_crossbu_synthesizer_agent.py`
- `agents/zurnelkay_ci_orchestrator_agent.py`

### JSON Definitions
- `demos/zurnelkay_drains_ci_agent.json`
- `demos/zurnelkay_wilkins_ci_agent.json`
- `demos/zurnelkay_drinking_water_ci_agent.json`
- `demos/zurnelkay_sinks_ci_agent.json`
- `demos/zurnelkay_commercial_brass_ci_agent.json`
- `demos/zurnelkay_crossbu_synthesizer_agent.json`
- `demos/zurnelkay_ci_orchestrator_agent.json`

### Documentation
- `demos/zurnelkay_ci_demo_script.md` - Full customer demo script

### Tests
- `tests/test_zurnelkay_ci_agents.py` - 46 test cases

## Running Tests

```bash
python -m pytest tests/test_zurnelkay_ci_agents.py -v
```

Expected: 44 passed, 2 skipped

## Example Output

### Quarterly Analysis
```json
{
  "report_type": "Quarterly Competitive Intelligence",
  "business_unit": "Drains",
  "highlights_by_product_family": {
    "core_spec_drains": { "product_launches": 2, "key_items": [...] },
    "siteworks": { "product_launches": 3, "key_items": [...] },
    "fog_separation": { "product_launches": 1, "key_items": [...] }
  },
  "top_3_significant_changes": [
    {
      "change": "JR Smith launches FS-200 Adjustable Floor Drain Series",
      "competitor": "JR Smith",
      "confidence_level": "high",
      "signal_priority": 1,
      "source": "PM Engineer + Company Press"
    }
  ],
  "implications": {
    "near_term": "...",
    "mid_term": "..."
  },
  "generated_at": "2026-01-23T..."
}
```

### Executive Briefing
```json
{
  "executive_summary": "Q4 2025 showed elevated competitive activity...",
  "critical_findings": [...],
  "strategic_recommendations": [...],
  "generated_at": "2026-01-23T..."
}
```

## Integration Points

- **Power BI**: All outputs are structured JSON, directly consumable
- **Data Warehouse**: Export to CSV or load JSON to warehouse
- **Slack/Teams**: Webhook integration for alerts
- **SharePoint**: Store reports in document library

## Customization

### Adding a Competitor
Update the `competitors` dictionary in the relevant BU agent.

### Changing Signal Priorities
Modify `signal_priority` values in the simulated data or scoring logic.

### Adding Data Sources
Implement API integration in the agent's data collection methods.

---

*Built: January 2026*
*Version: 1.0*
