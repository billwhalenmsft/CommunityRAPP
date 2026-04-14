# Agentic CoE — Discrete Manufacturing

A multi-persona AI agent team that operates autonomously and in partnership with Bill Whalen to accelerate output across Discrete Manufacturing work: SOPs, business process documentation, CRM/agentic use cases, and Microsoft tech stack solutions.

## Agent Personas

| Persona | File | Role |
|---|---|---|
| 🗂️ PM | `agents/mfg_coe_pm_agent.py` | Backlog, sprint planning, weekly digest |
| 🏭 SME | `agents/mfg_coe_sme_agent.py` | SOPs, process docs, use case definitions |
| 🧑‍💻 Developer | `agents/mfg_coe_developer_agent.py` | Agent code, D365 configs, RAPP artifacts |
| 🏗️ Architect | `agents/mfg_coe_architect_agent.py` | Microsoft stack design, integration patterns |
| 📋 Intake/Logger | `agents/mfg_coe_intake_agent.py` | Idea capture, solution logging, escalation to Bill |
| 🎭 Customer Persona | `agents/mfg_coe_customer_persona_agent.py` | Simulates customers for testing scenarios |
| ⚙️ Orchestrator | `agents/mfg_coe_orchestrator_agent.py` | Routes to personas, manages GitHub feedback loop |

## How to Steer the Agents (GitHub Loop)

1. Agents log ideas + work as **GitHub Issues** labeled `mfg-coe`
2. When a decision is needed, they add label `needs-bill` and ask the question in a comment
3. **You respond via comment** — agents pick it up and continue
4. Completed work is logged as a comment and the issue is closed

## Directory Structure

```
customers/mfg_coe/
  agents/             — All CoE agent Python files
  sops/               — Generated SOP markdown documents (versioned via git)
  knowledge_base/     — Accumulated patterns and domain knowledge
  decisions/          — Logged decisions from Bill's steering input
  testing/            — Customer persona profiles and test scenarios
  templates/          — Jinja2 templates for SOPs, reports, artifacts
```

## Azure Storage Layout

```
mfg_coe/              — Azure File Share
  backlog/            — Feature requests and ideas (JSON)
  solutions_log/      — Agent-generated solution records (JSON)
  sops/               — Generated SOP files (Markdown)
  decisions/          — Decision log entries (JSON)
  knowledge_base/     — Domain knowledge files (Markdown)
  test_results/       — Playwright test results (JSON + screenshots)
  personas/           — Active persona state and assignments (JSON)
```

## Demo Environments

Agents are aware of two primary demo environments:
- **Master CE Mfg** — Primary Discrete Manufacturing CE demo environment
- **Mfg Gold Template** — Gold template for Mfg field service/CRM scenarios

Context cards for each environment live in `knowledge_base/`.

## Customer Testing Library

Persona + scenario definitions exist for:
- Navico, Otis, Zurn/Elka, Vermeer, Carrier, AES, SMA4

See `testing/` for `personas.json` and `scenarios.json` per customer.

## Full Guide

See `docs/MFG_COE_GUIDE.md` for complete onboarding, GitHub workflow, and agent interaction patterns.
