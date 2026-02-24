# Zurn Elkay CI Demo - Quick Reference Card

## Agent Imports
```python
from agents.zurnelkay_drains_ci_agent import ZurnElkayDrainsCIAgent
from agents.zurnelkay_wilkins_ci_agent import ZurnElkayWilkinsCIAgent
from agents.zurnelkay_drinking_water_ci_agent import ZurnElkayDrinkingWaterCIAgent
from agents.zurnelkay_sinks_ci_agent import ZurnElkaySinksCIAgent
from agents.zurnelkay_commercial_brass_ci_agent import ZurnElkayCommercialBrassCIAgent
from agents.zurnelkay_crossbu_synthesizer_agent import ZurnElkayCrossbuSynthesizerAgent
from agents.zurnelkay_ci_orchestrator_agent import ZurnElkayCIOrchestratorAgent
import json
```

## Initialize All Agents
```python
drains = ZurnElkayDrainsCIAgent()
wilkins = ZurnElkayWilkinsCIAgent()
drinking = ZurnElkayDrinkingWaterCIAgent()
sinks = ZurnElkaySinksCIAgent()
brass = ZurnElkayCommercialBrassCIAgent()
synthesizer = ZurnElkayCrossbuSynthesizerAgent()
orchestrator = ZurnElkayCIOrchestratorAgent()
```

---

## Demo Flow Commands

### 1. DRAINS - Quarterly Analysis
```python
result = drains.perform("run_quarterly_analysis")
print(json.dumps(result, indent=2))
```

### 2. DRAINS - Parent Company Coordination (Watts)
```python
result = drains.perform("check_parent_company_coordination", 
                        parent_company="Watts Water Technologies")
print(json.dumps(result, indent=2))
```

### 3. WILKINS - Digital Innovation Focus
```python
result = wilkins.perform("get_digital_innovation")
print(json.dumps(result, indent=2))
```

### 4. WILKINS - Competitor Analysis (Watts)
```python
result = wilkins.perform("analyze_competitor", competitor="Watts")
print(json.dumps(result, indent=2))
```

### 5. DRINKING WATER - NSF Certifications
```python
result = drinking.perform("check_nsf_certifications")
print(json.dumps(result, indent=2))
```

### 6. DRINKING WATER - BU Report with Sources
```python
result = drinking.perform("generate_bu_report")
print("Sources:", json.dumps(result.get("sources", {}), indent=2))
```

### 7. SINKS - Healthcare Innovations
```python
result = sinks.perform("get_healthcare_innovations")
print(json.dumps(result, indent=2))
```

### 8. SINKS - Morris Group Coordination
```python
result = sinks.perform("check_parent_company_coordination", 
                       parent_company="Morris Group")
print(json.dumps(result, indent=2))
```

### 9. COMMERCIAL BRASS - Platform Launches
```python
result = brass.perform("get_platform_launches")
print(json.dumps(result, indent=2))
```

### 10. COMMERCIAL BRASS - Sloan Analysis
```python
result = brass.perform("analyze_competitor", competitor="Sloan")
print(json.dumps(result, indent=2))
```

### 11. SYNTHESIZER - Quarterly Synthesis
```python
result = synthesizer.perform("synthesize_quarterly_report")
print(json.dumps(result, indent=2))
```

### 12. SYNTHESIZER - Executive Briefing
```python
result = synthesizer.perform("generate_executive_briefing")
print(json.dumps(result, indent=2))
```

### 13. SYNTHESIZER - Watts Across All BUs
```python
result = synthesizer.perform("get_parent_company_summary", 
                             parent_company="Watts Water Technologies")
print(json.dumps(result, indent=2))
```

### 14. ORCHESTRATOR - Health Check
```python
health = orchestrator.health_check()
print(json.dumps(health, indent=2))
```

### 15. ORCHESTRATOR - System Status
```python
status = orchestrator.get_system_status()
print(json.dumps(status, indent=2))
```

### 16. ORCHESTRATOR - Full Quarterly (5+ min)
```python
quarterly = orchestrator.run_quarterly_workflow(quarter="Q4", year=2025)
print(f"Status: {quarterly['status']}")
print(f"Steps: {quarterly['steps_completed']}")
```

---

## Parent Companies Quick Reference

| Parent | Brands | BUs |
|--------|--------|-----|
| **Watts WWT** | Watts, Josam, Ames, Febco, Bradley, Haws | Drains, Wilkins, DW, CB |
| **Morris** | JR Smith, Acorn, Just Mfg, T&S Brass | Drains, Sinks, CB |
| **Lixil** | GROHE, American Standard | CB, Sinks |
| **Geberit** | Geberit, Chicago Faucets | CB, Drains |
| **Aalberts** | Caleffi, Pegler | Wilkins |

---

## Troubleshooting

### Agent import fails
```python
import sys
sys.path.insert(0, 'c:/path/to/CommunityRAPP-main')
```

### Check available actions
```python
print(drains.get_actions())
```

### Pretty print helper
```python
def pp(result):
    print(json.dumps(result, indent=2, default=str))
```
