# Zurn Elkay Competitive Intelligence System
## Executive Summary

---

### The Opportunity

Zurn Elkay operates across **5 business units** competing in distinct but related markets. Today, each BU conducts competitive intelligence independently, creating three challenges:

| Challenge | Impact |
|-----------|--------|
| **Time** | CI analysts spend 2-3 weeks manually gathering quarterly data |
| **Consistency** | Each BU uses different methods, making roll-ups difficult |
| **Coordination Blindspots** | Misses when competitors like Watts or Morris Group make coordinated moves across their portfolios |

---

### The Solution

We've built an **AI-powered Competitive Intelligence System** purpose-built for Zurn Elkay's structure:

```
                    ┌──────────────────┐
                    │   CI ORCHESTRATOR │  ← Quality Assurance
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  CROSS-BU        │  ← Enterprise View
                    │  SYNTHESIZER     │
                    └────────┬─────────┘
           ┌─────┬─────┬─────┼─────┬─────┐
           ▼     ▼     ▼     ▼     ▼     ▼
        Drains Wilkins Drinking Sinks Commercial
                       Water         Brass
```

**7 specialized AI agents** work together:
- **5 BU Agents** - Each knows its category's competitors, signals, and trade sources
- **1 Synthesizer** - Aggregates BU reports and finds cross-portfolio patterns
- **1 Orchestrator** - Ensures quality and manages quarterly workflows

---

### Key Capabilities

#### 1. Parent Company Tracking
We monitor 5 major parent companies across their entire portfolios:

| Parent Company | BUs Affected | Example Insight |
|----------------|--------------|-----------------|
| **Watts Water Technologies** | Drains, Wilkins, Drinking Water, Commercial Brass | Coordinated digital platform investment |
| **Morris Group** | Sinks, Commercial Brass | Just Mfg + T&S bundled healthcare solutions |
| **Lixil** | Commercial Brass, Sinks | American Standard positioning |
| **Geberit** | Commercial Brass, Drains | European premium strategy |
| **Aalberts** | Wilkins | Caleffi acquisition integration |

#### 2. Confidence Calibration
Every piece of intelligence is tagged:
- **High** - Verified against official databases (NSF, FDA) or multiple sources
- **Medium** - Single reliable trade publication or press release
- **Low** - Inference or unverified company announcement

#### 3. Source Attribution
All intelligence traced to origin:
- Third-party sources prioritized over company PR
- Verification URLs provided where available
- Executive reports include full source listings

---

### Business Value

| Before | After |
|--------|-------|
| 2-3 weeks per quarterly report | Hours with automated gathering |
| 5 different BU methodologies | Unified framework across all BUs |
| Missed cross-portfolio moves | Automatic parent company alerts |
| Manual executive roll-ups | CEO-ready briefings on demand |
| Inconsistent source quality | Every item attributed with confidence |

---

### What Makes This Different

1. **Purpose-Built for Zurn Elkay** - Not a generic CI tool. Knows your category structure, competitors, and parent companies.

2. **Cross-BU Intelligence** - Sees what individual BUs can't: coordinated competitive moves across portfolios.

3. **Transparent & Auditable** - Every insight has a source. Your executives can trust the data.

4. **Quality Assured** - Orchestrator validates all reports before delivery. Confidence calibration built-in.

---

### Deployment Options

| Tier | Components | Use Case |
|------|------------|----------|
| **Core** | 5 BU Agents | BU-level competitive intelligence |
| **Plus** | + Synthesizer | Enterprise view with cross-BU patterns |
| **Enterprise** | + Orchestrator | Full automation with QA and scheduling |

---

### Next Steps

1. **Demo** - 30-45 minute live demonstration with your team
2. **Pilot** - Deploy 1-2 BU agents with real data sources
3. **Scale** - Expand to full 7-agent system
4. **Integrate** - Connect to Power BI, data warehouse, existing workflows

---

*Contact: [Your Name] | [Date]*

---

# APPENDIX: Technical Details

## A. System Components

### Agent Inventory

| Agent | Level | Primary Function | Key Actions |
|-------|-------|------------------|-------------|
| CI Orchestrator | 0 | Workflow management, QA | `health_check`, `run_quarterly_workflow`, `validate_report` |
| Cross-BU Synthesizer | 2 | Enterprise aggregation | `synthesize_quarterly_report`, `detect_cross_bu_patterns`, `generate_executive_briefing` |
| Drains CI | 1 | Core Spec, Siteworks, FOG | `run_quarterly_analysis`, `analyze_competitor`, `check_parent_company_coordination` |
| Wilkins CI | 1 | Backflow, PRVs, TMVs | Same + `get_digital_innovation`, `get_certification_changes` |
| Drinking Water CI | 1 | Bottle Fillers, Filtration | Same + `check_nsf_certifications`, `get_public_sector_wins` |
| Sinks CI | 1 | Healthcare, ADA, Food Service | Same + `get_healthcare_innovations`, `get_ada_compliance_updates` |
| Commercial Brass CI | 1 | Flush Valves, Faucets | Same + `get_platform_launches`, `get_touchless_technology` |

### Competitors Tracked per BU

**Drains:** JR Smith, Watts, MiFab, Schier, Josam, Wade, Blucher

**Wilkins:** Watts, Caleffi, Honeywell, Apollo, Febco, Ames, Conbraco

**Drinking Water:** Elkay, Oasis, Halsey Taylor, 3M/Cuno, Haws, Sunroc

**Sinks:** Just Manufacturing, T&S Brass, Kohler, Bradley, Advance Tabco, Eagle Group

**Commercial Brass:** Sloan, Kohler, Bradley, TOTO, American Standard, Chicago Faucets

---

## B. Sample Output Structures

### BU Quarterly Analysis
```json
{
  "report_type": "Quarterly Competitive Intelligence",
  "business_unit": "Drains",
  "quarter": "Q4",
  "year": 2025,
  "highlights_by_product_family": {
    "Core Spec Drains": [...],
    "Siteworks": [...],
    "FOG Separation": [...]
  },
  "top_3_significant_changes": [
    {
      "rank": 1,
      "competitor": "Watts",
      "signal_type": "product_launch",
      "description": "...",
      "confidence": "high",
      "source": "..."
    }
  ],
  "implications": {
    "near_term": "...",
    "mid_term": "..."
  },
  "generated_at": "2025-01-23T12:00:00Z"
}
```

### Executive Briefing
```json
{
  "executive_summary": "3-4 sentence overview for CEO/COO",
  "critical_findings": [
    {
      "finding": "...",
      "business_units_affected": ["Drains", "Wilkins"],
      "recommended_action": "..."
    }
  ],
  "strategic_recommendations": [...],
  "generated_at": "2025-01-23T12:00:00Z"
}
```

---

## C. Integration Points

| System | Integration Method | Status |
|--------|-------------------|--------|
| Power BI | JSON API / REST | Ready |
| Data Warehouse | Structured JSON export | Ready |
| SharePoint | Document generation | Configurable |
| Email Alerts | SMTP integration | Configurable |
| Salesforce | API connector | Future |

---

## D. Data Sources (Expandable)

| Source Type | Examples | Integration |
|-------------|----------|-------------|
| Official Databases | NSF, FDA, UL | API verification |
| Trade Publications | PM Engineer, Supply House Times | RSS/API |
| Company Sources | Press releases, SEC filings | Web scrape |
| Industry Events | Trade shows, conferences | Manual input |
| Internal Data | Your own market research | Custom connector |

---

## E. Quality Assurance Framework

The Orchestrator validates every report against:

1. **Completeness** - All required fields present
2. **Confidence Distribution** - Reasonable mix of high/medium/low
3. **Source Attribution** - Every claim has a source
4. **Recency** - Data within acceptable timeframe
5. **Consistency** - Cross-BU data doesn't conflict

Failed validation triggers:
- Automatic retry with different parameters
- Human review flag if retry fails
- Audit log entry for tracking

---

*Technical Documentation v1.0 | January 2026*
