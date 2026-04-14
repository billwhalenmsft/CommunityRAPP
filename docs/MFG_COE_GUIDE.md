# Mfg CoE Guide — Agentic Center of Excellence for Discrete Manufacturing

## What This Is

An autonomous AI agent team built to multiply output across Discrete Manufacturing work. The agents operate independently and in partnership with Bill Whalen, focused on:

- Defining **SOPs** and standard business processes (CRM, field service, warranty, order management)
- Documenting **agentic use cases** for Discrete Manufacturing + Microsoft stack
- Iterating on **technology solutions** for the Master CE Mfg and Mfg Gold Template demo environments
- **Testing** demo scenarios using real customer personas (Navico, Otis, Zurn, Vermeer, Carrier, AES)

---

## Agent Team

| Persona | Agent File | Purpose |
|---|---|---|
| ⚙️ **Orchestrator** | `mfg_coe_orchestrator_agent.py` | L0 router — single entry point for all CoE requests |
| 📋 **Intake/Logger** | `mfg_coe_intake_agent.py` | Captures ideas, logs solutions, escalates to Bill |
| 🗂️ **PM** | `mfg_coe_pm_agent.py` | Backlog, sprint planning, conflict detection, weekly digest |
| 🏭 **SME** | `mfg_coe_sme_agent.py` | SOPs, process docs, use case definitions |
| 🧑‍💻 **Developer** | `mfg_coe_developer_agent.py` | Agent scaffolding, D365 configs, RAPP artifacts, Playwright tests |
| 🏗️ **Architect** | `mfg_coe_architect_agent.py` | Solution design, Microsoft stack recommendations |
| 🎭 **Customer Persona** | `mfg_coe_customer_persona_agent.py` | Customer simulation for testing demo scenarios |

---

## How to Work With the Agents

### Talking to the Orchestrator (single entry point)

```python
from customers.mfg_coe.agents.mfg_coe_orchestrator_agent import MfgCoEOrchestratorAgent

coe = MfgCoEOrchestratorAgent()

# Auto-route any request to the right persona
result = coe.perform(action="route_request", request="Generate an SOP for the warranty claim process")

# Get full CoE status
status = coe.perform(action="get_coe_status")

# Morning standup
standup = coe.perform(action="morning_standup")

# Run a GitHub issue through the full pipeline
pipeline = coe.perform(action="run_pipeline_item", issue_number=47)

# Health check all agents
health = coe.perform(action="health_check")
```

### Talking to Specific Persona Agents

```python
from customers.mfg_coe.agents.mfg_coe_sme_agent import MfgCoESMEAgent

sme = MfgCoESMEAgent()

# Generate an SOP
sop = sme.perform(
    action="generate_sop",
    topic="Warranty Claim Process",
    process_area="warranty",
    environment="master_ce_mfg",
    description="End-to-end warranty claim from intake through resolution"
)

# Define a use case
uc = sme.perform(
    action="define_use_case",
    topic="Warranty Status Self-Service",
    process_area="warranty",
    description="Customer can check warranty status via Copilot Studio chatbot"
)
```

---

## GitHub Human-in-the-Loop (How to Steer Agents)

### The Flow

```
Agent does work autonomously
    ↓
Agent hits a decision point or needs your direction
    ↓
Agent creates/updates a GitHub Issue with label: needs-bill
    ↓
🔔 You get a GitHub notification
    ↓
You read the issue, add a comment with your direction
    ↓
Orchestrator reads your comment via process_bill_feedback
    ↓
Agent picks up direction and continues
```

### How to Respond to Agents

When you see a `needs-bill` labeled issue:

1. **Read the agent's question** in the issue body or comments
2. **Add your response as a comment** — be direct
3. The Orchestrator's `process_bill_feedback` action parses your response and routes accordingly

**Example steering comments:**
- `"Go ahead and build this — scaffold the agent"` → routes to Developer
- `"Design this first, then we'll review before building"` → routes to Architect
- `"Write the SOP first"` → routes to SME
- `"Close this, not needed right now"` → closes the issue

### GitHub Labels Reference

| Label | Meaning |
|---|---|
| `mfg-coe` | All CoE work items |
| `needs-bill` | 🚨 Waiting for your input — check these first |
| `agent-task` | Ready for agents to pick up autonomously |
| `raw-idea` | Unprocessed idea — SME will formalize |
| `use-case` | Formalized use case — Architect will design |
| `tech-solution` | Architecture complete — Developer will build |
| `sop` | SOP document |
| `sop-review` | SOP PR needs review/merge |
| `weekly-digest` | Auto-generated weekly summary |
| `test-failure` | Playwright test failure — needs investigation |
| `persona:pm/sme/developer/architect` | Which agent owns this |
| `p1-critical / p2-high / p3-medium` | Priority |

---

## Demo Environments

### Master CE Mfg
Primary Discrete Manufacturing CE demo environment. All agents load the context card from `customers/mfg_coe/knowledge_base/master_ce_mfg.md` before generating artifacts.

### Mfg Gold Template
Baseline template for standing up new Mfg demos quickly. Context card: `customers/mfg_coe/knowledge_base/mfg_gold_template.md`.

**Update context cards** when you make changes to these environments so agents stay current.

---

## Customer Testing Library

Persona + scenario definitions for testing chatbot surfaces:

| Customer | Personas | Scenarios |
|---|---|---|
| Navico | Dealer rep, Consumer, Field tech | Warranty check, RMA request, Firmware issue |
| Otis | Building manager, Field tech | Service request, Parts lookup |
| Zurn/Elkay | Contractor, Spec engineer | Code compliance, Warranty claim |
| Vermeer | *(coming soon)* | |
| Carrier | *(coming soon)* | |
| AES | *(coming soon)* | |

### Running a Test Scenario

```python
from customers.mfg_coe.agents.mfg_coe_customer_persona_agent import MfgCoECustomerPersonaAgent

persona = MfgCoECustomerPersonaAgent()

# Get all scenarios for a customer
scenarios = persona.perform(action="get_scenarios", customer="navico")

# Simulate a full conversation
sim = persona.perform(
    action="simulate_conversation",
    customer="navico",
    scenario_id="navico_warranty_check"
)

# Generate Playwright test script
script = persona.perform(
    action="generate_test_script",
    customer="navico",
    scenario_id="navico_warranty_check"
)
```

---

## Storage Layout

### Azure File Storage — `mfg_coe/` share

```
mfg_coe/
  backlog/          ← Feature request JSON records
  solutions_log/    ← Agent solution records
  sops/             ← Generated SOP files
  decisions/        ← Bill's steering decisions (permanent log)
  knowledge_base/   ← Accumulated domain knowledge
  test_results/     ← Playwright test results
  personas/         ← Agent persona state
```

### Repo Structure

```
customers/mfg_coe/
  agents/           ← All 7 CoE agent files
  sops/             ← Generated SOP markdown files
  knowledge_base/   ← Context cards + knowledge base markdown
  decisions/        ← Decision log files
  testing/          ← Customer persona + scenario JSON files
    navico/
    otis/
    zurnelkay/
    vermeer/
    carrier/
    aes/
  templates/        ← Jinja2 templates
  README.md
```

---

## The Idea → Agent Pipeline

Every idea flows through these stages, tracked via GitHub Issue labels:

```
raw-idea → use-case → tech-solution → agent-task → done
   ↑           ↑           ↑              ↑
 Intake      SME        Architect      Developer
```

The PM Agent tracks stage progression and the Orchestrator can advance any issue through the pipeline with `run_pipeline_item`.

---

## Useful Commands

```python
# Get CoE morning standup
coe.perform(action="morning_standup")

# Check for decisions needing Bill
intake.perform(action="get_pending_decisions")

# Generate weekly digest
pm.perform(action="generate_weekly_digest")

# Detect conflicting proposals
pm.perform(action="detect_conflicts")

# Add an idea to the backlog
intake.perform(
    action="log_idea",
    title="Your idea title",
    body="Detailed description",
    persona="sme",
    labels=["use-case", "p2-high"]
)

# Search knowledge base
sme.perform(action="search_knowledge_base", search_query="warranty process")
architect.perform(action="search_knowledge_base", search_query="Copilot Studio integration")
```
