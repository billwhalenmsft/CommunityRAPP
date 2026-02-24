# Zurn Elkay Competitive Intelligence System
## Customer Demo Script

**Customer:** Zurn Elkay Water Solutions  
**Use Case:** Quarterly Competitive Intelligence Automation  
**Duration:** 30-45 minutes  
**Audience:** VP Strategy, BU GMs, Product Managers, CI Team

---

## System Overview

### Agents Built
| Level | Agent | Purpose |
|-------|-------|---------|
| **Level 0** | CI Orchestrator | Coordinates all agents, validates quality, manages workflows |
| **Level 1** | Drains CI Agent | Core Spec Drains, Siteworks, FOG Separation |
| **Level 1** | Wilkins CI Agent | Backflow Prevention, PRVs, TMVs |
| **Level 1** | Drinking Water CI Agent | Bottle Fillers, Filtration, Coolers |
| **Level 1** | Sinks CI Agent | Healthcare Sinks, ADA, Food Service |
| **Level 1** | Commercial Brass CI Agent | Flush Valves, Faucets, Touchless Technology |
| **Level 2** | Cross-BU Synthesizer | Aggregates BU reports, detects cross-BU patterns |

### Parent Companies Tracked
- **Watts Water Technologies** → Drains, Wilkins, Drinking Water, Commercial Brass
- **Morris Group** → Sinks, Commercial Brass
- **Lixil** → Commercial Brass, Sinks
- **Geberit** → Commercial Brass, Drains
- **Aalberts** → Wilkins

---

## Pre-Demo Checklist

- [ ] Function app running: `func start` from CommunityRAPP-main folder
- [ ] Health check passing: `curl http://localhost:7071/api/health?deep=true`
- [ ] Python environment active with all dependencies
- [ ] Demo environment loaded with simulated Q4 2025 data
- [ ] Backup: Pre-generated JSON output files in `/demos/` folder

---

## Demo Narrative

### Opening (2 minutes)

> "Today I'm going to show you how we've built a competitive intelligence system specifically designed for Zurn Elkay's multi-BU structure. 
>
> The system addresses three challenges you mentioned:
> 1. **Time** - Your CI analysts spend weeks manually gathering data
> 2. **Consistency** - Each BU does CI differently, making roll-ups difficult  
> 3. **Coordination blindspots** - You're missing when competitors like Watts or Morris Group make coordinated moves across their portfolios
>
> Let me show you how we solve each of these."

---

### Section 1: Architecture Overview (3 minutes)

> "First, let me explain how the system is structured."

**[SHOW DIAGRAM]**

```
┌─────────────────────────────────────────────────────────────────┐
│               LEVEL 0: CI ORCHESTRATOR                          │
│   • Coordinates all agents • Validates quality • Manages QA     │
│   • Executes quarterly workflows • Handles errors & retries     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               LEVEL 2: CROSS-BU SYNTHESIZER                     │
│   • Aggregates 5 BU reports • Detects cross-BU patterns        │
│   • Generates executive briefings • Parent company analysis     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────┬─────────┼─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ DRAINS  │ │ WILKINS │ │DRINKING │ │  SINKS  │ │COMMERCIAL│
│   CI    │ │   CI    │ │ WATER   │ │   CI    │ │  BRASS   │
│  Agent  │ │  Agent  │ │   CI    │ │  Agent  │ │   CI     │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
   JR Smith   Watts       Elkay       Just Mfg    Sloan
   Watts      Caleffi     Oasis       T&S Brass   Kohler
   MiFab      Honeywell   Halsey      Kohler      Bradley
   Schier     Apollo      3M/Cuno     Bradley     TOTO
```

> "Each BU has its own dedicated agent that knows:
> - The specific competitors in that category
> - Which parent companies own those competitors
> - What signals matter most - certifications, product launches, leadership changes
> - The trade publications and data sources relevant to that space
>
> This is NOT a generic CI tool. It's purpose-built for your business."

---

### Section 2: Single BU Deep Dive - Drains (8 minutes)

> "Let me show you the Drains agent in action. I'll run a quarterly analysis."

**[EXECUTE COMMAND]**
```python
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent

drains = ZurnElkayDrainsCIAgent()
result = drains.perform("run_quarterly_analysis")
print(json.dumps(result, indent=2))
```

**Expected Output Fields:**
- `report_type`: "Quarterly Competitive Intelligence"
- `business_unit`: "Drains"
- `highlights_by_product_family`: Core Spec, Siteworks, FOG with product launches
- `top_3_significant_changes`: Prioritized competitive moves with confidence levels
- `implications`: Near-term and mid-term strategic implications
- `generated_at`: Timestamp

**[WALK THROUGH OUTPUT]**

> "Notice a few things about this output:
>
> **1. Highlights by Product Family** - Core Spec Drains, Siteworks, FOG Separation each get their own analysis. The agent knows your category structure.
>
> **2. Top 3 Significant Changes** - These are prioritized by signal importance, not just recency. A certification change might matter more than a press release.
>
> **3. Confidence Calibration** - See how each item has 'high', 'medium', or 'low' confidence? We're honest about what we know vs. what we're inferring."

**[SHOW AVAILABLE ACTIONS]**
```python
print(drains.get_actions())
# Output: ['run_quarterly_analysis', 'analyze_competitor', 'check_parent_company_coordination',
#          'get_signal_summary', 'search_trade_publications', 'get_product_launches',
#          'get_leadership_changes', 'get_certification_updates', 'generate_bu_report']
```

**[HIGHLIGHT PARENT COMPANY COORDINATION]**

> "Now let me show you something your current process probably misses. Let's check for coordinated moves by Watts Water Technologies across their drain brands."

```python
result = drains.perform("check_parent_company_coordination", 
                        parent_company="Watts Water Technologies")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `parent_company`: "Watts Water Technologies"
- `brands_monitored`: ["Watts", "Josam", "Ames", "Febco", "Powers", "Bradley", "Haws"]
- `signals`: Recent coordinated activity across Watts brands
- `signal_count`: Number of signals detected

> "See this? Josam, Wade, Blucher - they're all Watts. When you see similar product launches or shared technology across these brands, that's not coincidence. That's portfolio strategy. The system flags these patterns automatically."

---

### Section 3: Show Differentiation - Wilkins Digital Focus (5 minutes)

> "Each BU agent is specialized. Let me show you Wilkins, which has a particular focus on digital/smart valve technology."

```python
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent

wilkins = ZurnElkayWilkinsCIAgent()
result = wilkins.perform("get_digital_innovation")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `digital_category`: "Smart Water Control"
- `innovations`: List of digital features by competitor
- `feature_comparison_matrix`: Bluetooth, cloud, mobile app capabilities
- `market_assessment`: Analysis of digital adoption trends

> "The Wilkins agent tracks:
> - Which competitors have Bluetooth connectivity
> - Who has cloud dashboards
> - Mobile app capabilities
> - Building management system integration
>
> It even gives you a feature comparison matrix. This is the kind of competitive tracking that would take your team days to compile manually."

**[DEEP DIVE ON WATTS]**

```python
result = wilkins.perform("analyze_competitor", competitor="Watts")
print(json.dumps(result, indent=2))
```

> "Because Watts is a portfolio player with coordinated strategy, we don't just analyze Watts as a single competitor. We analyze their portfolio strategy - brand consolidation, digital platform investments, healthcare vertical focus. This is the context your PMs need."

---

### Section 4: Source Transparency - Drinking Water (4 minutes)

> "You mentioned that your executives want to know WHERE the intelligence comes from. Let me show you the Drinking Water agent."

```python
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent

drinking = ZurnElkayDrinkingWaterCIAgent()
result = drinking.perform("check_nsf_certifications")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `certifications`: List with competitor, certification type, date, source
- Each entry has `source`, `confidence`, `verification_url`

> "Every certification is verified against the official NSF database. Every product launch is sourced to a trade publication or press release. Every leadership change has a LinkedIn or company announcement reference.
>
> We prioritize third-party sources over company PR. When we only have company sources, confidence is marked as 'medium' or 'low'."

**[SHOW SOURCES IN BU REPORT]**

```python
result = drinking.perform("generate_bu_report")
print("Sources:", json.dumps(result.get("sources", {}), indent=2))
```

> "The executive report explicitly lists sources at the bottom. Your VPs can trust this isn't just scraped marketing content."

---

### Section 5: Healthcare Focus - Sinks (4 minutes)

> "Let me show you how the Sinks agent handles the healthcare vertical, which I know is strategic for you."

```python
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent

sinks = ZurnElkaySinksCIAgent()
result = sinks.perform("get_healthcare_innovations")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `segment`: "Healthcare Sinks"
- `innovations`: Antimicrobial features, touchless, infection control
- `competitors_active`: Just Manufacturing, Bradley, T&S Brass

> "The agent tracks:
> - Antimicrobial surface innovations
> - Touchless/infection control features
> - FDA and healthcare facility requirements
>
> And critically - it watches Morris Group coordination."

```python
result = sinks.perform("check_parent_company_coordination", 
                       parent_company="Morris Group")
print(json.dumps(result, indent=2))
```

> "Morris owns Just Manufacturing AND T&S Brass. When Just launches a healthcare sink with T&S faucetry integration, that's a coordinated bundled solution play. Your reps need to know they're competing against packages, not products."

---

### Section 6: Platform Competition - Commercial Brass (5 minutes)

> "Finally, let me show you the Commercial Brass agent, where there's a major strategic shift happening."

```python
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent

brass = ZurnElkayCommercialBrassCIAgent()
result = brass.perform("get_platform_launches")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `platform_launches`: Sloan Connect, Kohler Portfolio
- `business_model_shift`: Hardware + SaaS subscription analysis
- `strategic_implications`: Platform vs. product competition

> "Sloan and Kohler have both launched enterprise restroom management platforms. This isn't just product competition anymore - it's platform competition.
>
> The agent tracks these platform moves specifically because they represent a different kind of competitive threat."

**[DEEP DIVE ON SLOAN]**

```python
result = brass.perform("analyze_competitor", competitor="Sloan")
print(json.dumps(result, indent=2))
```

> "When you ask about Sloan, you don't get a product list. You get a platform strategy analysis:
> - What's in Sloan Connect
> - What's the business model (hardware + SaaS subscription)
> - What talent are they hiring (Honeywell building automation experts)
> - What this means for your competitive position
>
> This is the kind of strategic context that changes how you plan, not just react."

---

### Section 7: Cross-BU Synthesis (5 minutes)

> "Now let me show you the real power - the Level 2 Synthesizer that sees across ALL business units."

```python
from agents.zurnelkay_crossbu_synthesizer_agent import ZurnElkayCrossbuSynthesizerAgent

synthesizer = ZurnElkayCrossbuSynthesizerAgent()
result = synthesizer.perform("synthesize_quarterly_report")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `enterprise_summary`: High-level cross-BU overview
- `cross_bu_patterns`: Patterns invisible to individual BUs
- `top_5_enterprise_signals`: Portfolio-level prioritized signals
- `bu_reports`: Aggregated data from all 5 BUs

> "The Synthesizer:
> 1. **Aggregates** all five BU reports into a single enterprise view
> 2. **Identifies cross-BU patterns** - Is Watts making coordinated moves across Drains AND Wilkins AND Commercial Brass?
> 3. **Prioritizes portfolio-level signals** - What matters most for Zurn Elkay as a whole?"

**[EXECUTIVE BRIEFING]**

```python
result = synthesizer.perform("generate_executive_briefing")
print(json.dumps(result, indent=2))
```

**Expected Output:**
- `executive_summary`: 3-4 sentence overview for CEO/COO
- `critical_findings`: Top findings requiring executive attention
- `strategic_recommendations`: Actions to consider
- `generated_at`: Timestamp

> "This is CEO-ready. Drop it straight into your quarterly strategy review."

**[PARENT COMPANY ANALYSIS]**

```python
result = synthesizer.perform("get_parent_company_summary", parent_company="Watts Water Technologies")
print(json.dumps(result, indent=2))
```

> "Want to know what Watts is doing across your entire competitive landscape? One command gives you:
> - All BUs where Watts competes
> - Combined signals across all their brands
> - Coordination patterns suggesting enterprise strategy"

---

### Section 8: Orchestrator - System Management (3 minutes)

> "Finally, the Level 0 Orchestrator ensures the whole system runs reliably."

```python
from agents.zurnelkay_ci_orchestrator_agent import ZurnElkayCIOrchestratorAgent

orchestrator = ZurnElkayCIOrchestratorAgent()

# System health check
health = orchestrator.health_check()
print(json.dumps(health, indent=2))
```

**Expected Output:**
- `overall_status`: "healthy", "degraded", or "unhealthy"
- `bu_agents`: Status of each of 5 BU agents
- `synthesizer`: Status of synthesizer agent
- `issues`: Any problems detected

```python
# System status
status = orchestrator.get_system_status()
print(json.dumps(status, indent=2))
```

> "The Orchestrator:
> - **Validates** that every BU report meets quality standards
> - **Ensures** all required fields are present
> - **Flags** confidence calibration issues
> - **Retries** failed steps automatically
> - **Logs** everything for audit trails"

**[FULL QUARTERLY WORKFLOW - Optional if time permits]**

```python
# Run the entire quarterly workflow
quarterly = orchestrator.run_quarterly_workflow(quarter="Q4", year=2025)
print(f"Status: {quarterly['status']}")
print(f"Steps completed: {quarterly['steps_completed']}")
```

---

### Closing: Value Summary (3 minutes)

> "Let me recap what this system does for you:
>
> | Challenge | Solution |
> |-----------|----------|
> | **Time** | Weeks → Hours. Automated data gathering with human review |
> | **Consistency** | All 5 BUs use same framework, same confidence calibration |
> | **Coordination Blindspots** | Parent company tracking: Watts, Morris, Lixil, Geberit, Aalberts |
> | **Source Quality** | Third-party prioritized, every item attributed |
> | **Executive Ready** | BU reports + enterprise synthesis ready for distribution |
> | **QA Built-In** | Orchestrator validates all outputs before delivery |
>
> **Questions?**"

---

## Anticipated Questions & Answers

### Q: "How do we keep the competitor lists current?"
> "The agents have configurable competitor dictionaries. When you acquire a competitor or a new player emerges, it's a simple configuration update - no code changes needed. We'd recommend a quarterly review of the competitor lists."

### Q: "What if we want to add a data source?"
> "The agents are designed to integrate with additional APIs. We've stubbed in trade publication searches - adding PM Engineer, Supply House Times, or your own internal databases is straightforward integration work."

### Q: "How does this integrate with Power BI / our existing dashboards?"
> "Every agent returns structured JSON. That JSON can feed directly into Power BI, your data warehouse, or any BI tool. We can also generate CSV exports if that's your preferred format."

### Q: "What about real-time alerts vs. quarterly reports?"
> "The system supports both. Quarterly is the batch mode we've shown. The same agents can be triggered on-demand or connected to RSS feeds for real-time monitoring. The architecture supports both use cases."

### Q: "How confident should we be in the intelligence?"
> "That's exactly why we built confidence calibration in. High confidence = verified against official databases or multiple sources. Medium = single reliable source. Low = inference or unverified. Your team knows exactly what weight to give each item."

### Q: "Can we customize the signal priorities?"
> "Absolutely. Right now, certifications and product launches are typically Priority 1-2, leadership changes are Priority 3. But if certifications matter more to Wilkins than to Drains, we can tune that per-BU."

### Q: "What's the difference between Level 0, 1, and 2?"
> "Level 1 agents are the source of truth for each BU - they own the data. Level 2 (Synthesizer) aggregates and finds cross-BU patterns. Level 0 (Orchestrator) manages the workflow and quality control. Each level has a distinct responsibility."

---

## Demo Recovery Paths

### If live demo fails:
1. Show pre-generated JSON output files in `/demos/` folder
2. Walk through the code structure to show capability
3. Emphasize this is working system, temporary connectivity issue

### If customer asks for feature not yet built:
> "That's on our roadmap. Let me show you what we have today, and we can discuss timeline for that enhancement."

### If customer wants to see their actual competitors:
> "We've loaded simulated data that mirrors your competitive landscape. In production deployment, we'd configure the exact competitors your team identifies and connect to your preferred data sources."

---

## Post-Demo Next Steps

1. **Share demo recording** (if recorded)
2. **Provide access to test environment** for customer self-exploration
3. **Schedule follow-up** to discuss:
   - Data source integration priorities
   - Customization requirements per BU
   - Deployment timeline and phasing
4. **Send proposal** with pricing tiers:
   - **Tier 1**: 5 BU agents (core functionality)
   - **Tier 2**: + Synthesizer (cross-BU intelligence)
   - **Tier 3**: + Orchestrator (full automation with QA)

---

## Technical Notes for Demo Presenter

### Starting the Function App
```bash
cd CommunityRAPP-main
func start
```

### Quick Health Check
```bash
curl http://localhost:7071/api/health?deep=true
```

### Python Interactive Demo Setup
```python
import json  # For pretty printing

# Import all agents
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent
from agents.zurnelkay_crossbu_synthesizer_agent import ZurnElkayCrossbuSynthesizerAgent
from agents.zurnelkay_ci_orchestrator_agent import ZurnElkayCIOrchestratorAgent

# Initialize agents
drains = ZurnElkayDrainsCIAgent()
wilkins = ZurnElkayWilkinsCIAgent()
drinking = ZurnElkayDrinkingWaterCIAgent()
sinks = ZurnElkaySinksCIAgent()
brass = ZurnElkayCommercialBrassCIAgent()
synthesizer = ZurnElkayCrossbuSynthesizerAgent()
orchestrator = ZurnElkayCIOrchestratorAgent()
```

### Key Demo Commands Cheat Sheet

#### Level 1 BU Agents (All 5)
| Action | Command |
|--------|---------|
| Quarterly analysis | `agent.perform("run_quarterly_analysis")` |
| BU executive report | `agent.perform("generate_bu_report")` |
| Competitor deep dive | `agent.perform("analyze_competitor", competitor="Watts")` |
| Parent coordination | `agent.perform("check_parent_company_coordination", parent_company="Watts Water Technologies")` |
| Product launches | `agent.perform("get_product_launches")` |
| Signal summary | `agent.perform("get_signal_summary")` |

#### BU-Specific Commands
| Agent | Special Action | Command |
|-------|---------------|---------|
| Wilkins | Digital innovation | `wilkins.perform("get_digital_innovation")` |
| Wilkins | Certification changes | `wilkins.perform("get_certification_changes")` |
| Drinking Water | NSF certifications | `drinking.perform("check_nsf_certifications")` |
| Drinking Water | Public sector wins | `drinking.perform("get_public_sector_wins")` |
| Sinks | Healthcare innovations | `sinks.perform("get_healthcare_innovations")` |
| Sinks | ADA compliance | `sinks.perform("get_ada_compliance_updates")` |
| Commercial Brass | Platform launches | `brass.perform("get_platform_launches")` |
| Commercial Brass | Touchless tech | `brass.perform("get_touchless_technology")` |

#### Level 2 Synthesizer
| Action | Command |
|--------|---------|
| Quarterly synthesis | `synthesizer.perform("synthesize_quarterly_report")` |
| Cross-BU patterns | `synthesizer.perform("detect_cross_bu_patterns")` |
| Executive briefing | `synthesizer.perform("generate_executive_briefing")` |
| Parent company summary | `synthesizer.perform("get_parent_company_summary", parent_company="Watts Water Technologies")` |
| Compare BU pressure | `synthesizer.perform("compare_bu_competitive_pressure")` |

#### Level 0 Orchestrator
| Action | Command |
|--------|---------|
| Health check | `orchestrator.health_check()` |
| System status | `orchestrator.get_system_status()` |
| Run quarterly workflow | `orchestrator.run_quarterly_workflow(quarter="Q4", year=2025)` |
| Single BU report | `orchestrator.run_bu_report("drains")` |
| Parent company alert | `orchestrator.run_parent_company_alert("Watts")` |
| Execution log | `orchestrator.get_execution_log()` |

---

## Files Reference

### Agent Files
| Agent | JSON Definition | Python Implementation |
|-------|----------------|----------------------|
| Drains | `demos/zurnelkay_drains_ci_agent.json` | `agents/zurnelkay_drains_ci_agent.py` |
| Wilkins | `demos/zurnelkay_wilkins_ci_agent.json` | `agents/zurnelkay_wilkins_ci_agent.py` |
| Drinking Water | `demos/zurnelkay_drinking_water_ci_agent.json` | `agents/zurnelkay_drinking_water_ci_agent.py` |
| Sinks | `demos/zurnelkay_sinks_ci_agent.json` | `agents/zurnelkay_sinks_ci_agent.py` |
| Commercial Brass | `demos/zurnelkay_commercial_brass_ci_agent.json` | `agents/zurnelkay_commercial_brass_ci_agent.py` |
| Synthesizer | `demos/zurnelkay_crossbu_synthesizer_agent.json` | `agents/zurnelkay_crossbu_synthesizer_agent.py` |
| Orchestrator | `demos/zurnelkay_ci_orchestrator_agent.json` | `agents/zurnelkay_ci_orchestrator_agent.py` |

### Test Files
- Test suite: `tests/test_zurnelkay_ci_agents.py` (46 tests)
- Run tests: `python -m pytest tests/test_zurnelkay_ci_agents.py -v`

---

*Last Updated: January 23, 2026*  
*Demo Version: 1.0*  
*System Status: All 7 agents implemented, 44 tests passing*
