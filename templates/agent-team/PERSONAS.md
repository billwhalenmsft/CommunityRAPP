# Agent Team Personas — Reference Guide

Each persona is a specialized AI agent with a defined role, keyword routing triggers, and a set of actions. Choose the combination that fits your team's mission.

---

## Core Personas (always recommended)

### 🎯 Outcome Framer
**File:** `{team_slug}_outcome_framer_agent.py`  
**Purpose:** Ensures every issue has a defined outcome before any build work begins. The CoE's "why-first" gate.

**When invoked:** Any issue without a defined success metric. Also triggered when a work item is first created.

**Key actions:** `frame_outcome`, `define_kpi`, `validate_feasibility`, `output_outcome_statement`

**Why it matters:** Without defined outcomes, agents can build the wrong thing. This persona asks: *What does success look like? Who measures it? How will we know when we're done?*

---

### 📋 Intake / Logger
**File:** `{team_slug}_intake_agent.py`  
**Purpose:** Captures raw ideas, logs agent-generated solutions, and escalates to the human owner when needed.

**When invoked:** New raw ideas, solution logging, `needs-bill` escalations.

**Key actions:** `log_idea`, `log_solution`, `flag_for_owner`, `get_backlog`

**Why it matters:** Without a logger, agent insights evaporate. This persona is the team's institutional memory.

---

### ✅ Outcome Validator
**File:** `{team_slug}_outcome_validator_agent.py`  
**Purpose:** Before closing any issue, validates that the stated outcome was actually delivered and documented.

**When invoked:** Issues labeled `outcome-validated` or near-completion pipeline items.

**Key actions:** `validate_outcome`, `check_kpi_met`, `request_sign_off`, `archive_outcome`

**Why it matters:** Enforces outcome accountability. Nothing closes without evidence of value delivered.

---

## Planning Personas

### 🗂️ Project Manager (PM)
**File:** `{team_slug}_pm_agent.py`  
**Purpose:** Sprint planning, backlog prioritization, status reporting, conflict detection.

**When invoked:** Keywords: `sprint`, `backlog`, `plan`, `status`, `prioritize`, `assign`, `roadmap`

**Key actions:** `plan_sprint`, `get_status`, `prioritize_backlog`, `assign_work`, `detect_conflicts`, `generate_digest`

**Good for:** Any team. Essential for CoE mode where autonomous agents need coordination.

---

## Domain Expertise Personas

### 🏭 Subject Matter Expert (SME)
**File:** `{team_slug}_sme_agent.py`  
**Purpose:** Defines use cases, documents processes and SOPs, captures domain knowledge.

**When invoked:** Keywords: `sop`, `process`, `use case`, `workflow`, `standard`, `document`

**Key actions:** `generate_sop`, `document_process`, `define_use_case`, `review_sop`, `update_knowledge_base`

**Good for:** CoEs, consulting teams, operations groups. Anyone who needs to codify "how we do things."

---

### 👤 Customer Persona Simulator
**File:** `{team_slug}_customer_persona_agent.py`  
**Purpose:** Simulates end-user interactions to test agent outputs from a business user's perspective.

**When invoked:** Keywords: `user story`, `persona`, `test as user`, `customer scenario`

**Key actions:** `simulate_user`, `generate_test_conversation`, `validate_user_experience`, `identify_friction_points`

**Good for:** Product teams, CoEs with end-user-facing solutions, chatbot development.

---

## Technical Personas

### 🧑‍💻 Developer
**File:** `{team_slug}_developer_agent.py`  
**Purpose:** Code generation, implementation, config generation, artifact creation.

**When invoked:** Keywords: `code`, `build`, `implement`, `develop`, `scaffold`, `generate`, `fix`

**Key actions:** `scaffold_agent`, `generate_config`, `create_artifact`, `code_review`, `write_tests`

**Specializations to configure:**
- Power Platform / Canvas Apps
- Copilot Studio (YAML topics)
- Azure Functions / Python
- Dynamics 365 configuration
- Power Automate flows

---

### 🏗️ Architect
**File:** `{team_slug}_architect_agent.py`  
**Purpose:** Solution design, stack recommendations, architecture documentation, pattern evaluation.

**When invoked:** Keywords: `design`, `architecture`, `pattern`, `stack`, `recommend`, `evaluate`, `approach`

**Key actions:** `design_solution`, `evaluate_pattern`, `create_architecture_doc`, `recommend_stack`, `assess_technical_debt`

**Good for:** Any team making platform or design decisions. Prevents ad-hoc tech choices.

---

## Quality & Compliance Personas

### 🔒 Security Reviewer
**File:** `{team_slug}_security_reviewer_agent.py`  
**Purpose:** Code security review, compliance checks, risk assessment, secrets/credential scanning.

**When invoked:** Keywords: `security`, `vulnerability`, `compliance`, `risk`, `pen test`, `secret`, `credentials`

**Key actions:** `review_security`, `check_compliance`, `assess_risk`, `validate_no_secrets`, `generate_security_report`

**Good for:** Any team with production deployments, especially those handling customer data.

---

### 🧪 QA Engineer
**File:** `{team_slug}_qa_engineer_agent.py`  
**Purpose:** Test case design, regression testing, acceptance criteria validation, test automation.

**When invoked:** Keywords: `test`, `qa`, `quality`, `bug`, `regression`, `acceptance`, `verify`

**Key actions:** `design_test_cases`, `write_regression_tests`, `validate_acceptance_criteria`, `identify_edge_cases`, `generate_test_report`

**Good for:** Software teams, anyone shipping code to production.

---

## Content & Communication Personas

### 🎨 UX Designer
**File:** `{team_slug}_ux_designer_agent.py`  
**Purpose:** User experience design, wireframes (text-based), accessibility review, user journey mapping.

**When invoked:** Keywords: `ux`, `ui`, `design`, `wireframe`, `user flow`, `interface`, `accessibility`

**Key actions:** `design_user_flow`, `create_wireframe`, `review_accessibility`, `map_user_journey`, `suggest_ux_improvements`

**Good for:** Product teams, web/app developers, anyone building user-facing surfaces.

---

### ✍️ Content Strategist
**File:** `{team_slug}_content_strategist_agent.py`  
**Purpose:** Documentation strategy, editorial standards, content architecture, writing reviews.

**When invoked:** Keywords: `content`, `docs`, `documentation`, `write`, `editorial`, `readme`, `guide`

**Key actions:** `plan_content_strategy`, `review_documentation`, `create_content_outline`, `enforce_style_guide`, `audit_content_gaps`

**Good for:** DevRel teams, CoEs producing SOPs, anyone with a documentation backlog.

---

### 📊 Data Analyst
**File:** `{team_slug}_data_analyst_agent.py`  
**Purpose:** Trend analysis, KPI tracking, data-driven recommendations, outcome measurement.

**When invoked:** Keywords: `analyze`, `data`, `trend`, `kpi`, `metric`, `report`, `insight`, `measure`

**Key actions:** `analyze_trends`, `generate_kpi_report`, `identify_patterns`, `recommend_improvements`, `create_data_summary`

**Good for:** CoEs, ops teams, anyone tracking outcomes over time. Pairs naturally with Outcome Validator.

---

## Persona Combinations by Use Case

| Scenario | Personas |
|----------|---------|
| **Autonomous CoE (full)** | All 14 |
| **Software dev team** | Outcome Framer + PM + Developer + Architect + QA + Security + Intake + Outcome Validator |
| **Content / docs team** | Outcome Framer + SME + Content Strategist + UX Designer + Intake + Outcome Validator |
| **Research / analysis** | Outcome Framer + SME + Data Analyst + Architect + Intake + Outcome Validator |
| **Lightweight project** | Outcome Framer + PM + Developer + Intake + Outcome Validator |
| **Consulting engagement** | Outcome Framer + PM + SME + Architect + Developer + Customer Persona + Outcome Validator |

> **Rule of thumb:** Always include Outcome Framer + Intake + Outcome Validator. These three enforce the pipeline's start, memory, and close gates — they're the team's connective tissue.

---

## Adding a Custom Persona

1. Copy `templates/agent-team/agents/_base_persona_template.py`
2. Replace `{{PLACEHOLDER}}` values
3. Implement `perform()` with your actions
4. Import and wire into orchestrator `__init__` and `ROUTING_MAP`
5. Add a `persona:your-persona` GitHub label

See `customers/mfg_coe/agents/mfg_coe_data_analyst_agent.py` for a complete example.
