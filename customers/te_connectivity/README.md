# TE Connectivity — Customer Folder

> Context loaded by CoE agents when generating code, demos, or configs for TE Connectivity engagements.

## Company Overview

**TE Connectivity Ltd** is a global industrial technology leader — a trusted electronics manufacturer with 80+ years of experience designing and manufacturing connectivity and sensing solutions.

- **Website:** https://www.te.com
- **Industry:** Electronic Components & Connectors | Global Supply Chain
- **Scale:** ~10,000 engineers | ~130 countries | NYSE: TEL
- **HQ:** Schaffhausen, Switzerland (operational HQ: Berwyn, PA, USA)
- **Segments:** Transportation Solutions | Industrial Solutions | Communications Solutions

### What They Make
Connectors, sensors, and electronic components for:
- Electric vehicles and aerospace/defense
- Digital factories and industrial automation
- Smart homes and IoT devices
- Medical devices and energy networks
- AI systems and global communications infrastructure

---

## Active Projects

| Project | Status | Phase | Folder |
|---|---|---|---|
| Freight Booking Email Control Tower | 🟡 Demo/Sandbox | Phase 1 MVP | `copilot-studio/` |

---

## Folder Structure

```
customers/te_connectivity/
  README.md                         ← This file
  knowledge_base/
    te_connectivity_context.md      ← Context card loaded by all agents
  copilot-studio/
    agent_config.json               ← FreightBot CS agent configuration
  d365/
    config/
      environment.json              ← Logistics config, forwarders, SLAs, personas
  testing/
    freight_control_tower/
      scenarios.json                ← Test scenarios for FreightBot
      personas.json                 ← User personas for testing
```

---

## Key Contacts / Personas (Demo)

| Name | Role | Focus Area |
|---|---|---|
| Sarah Chen | Team Leader | Shift oversight, SLA monitoring, shift briefings |
| Alex Rodriguez | Booking Agent | Exception resolution, forwarder communication |
| Marcus Webb | Night Shift Agent | Overnight monitoring, shift handoff documentation |

---

## Tech Stack (Phase 1)

- **Automation:** Copilot Studio Agent Flows
- **Task Management:** Microsoft Planner ("Freight Booking Exceptions" plan)
- **Email:** Shared mailbox (admin@ — demo)
- **Chat Interface:** Microsoft Teams / Copilot Studio test canvas
- **AI:** Copilot Studio generative AI (GPT-4o)

---

## Phase Roadmap

| Phase | Status | Key Capabilities |
|---|---|---|
| Phase 1 | 🟡 Demo/Sandbox | Email triage → Planner tasks, Shift briefing, Task lookup, Mark complete |
| Phase 2 | 📋 Planned | Auto-reply to forwarders, SAP booking validation, Power BI aging dashboard |
| Phase 3 | 🔮 Future | TMS integration, predictive exception detection, cross-forwarder analytics |
