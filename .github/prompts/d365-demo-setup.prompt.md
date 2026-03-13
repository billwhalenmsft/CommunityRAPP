---
description: 'Start a new D365 Customer Service demo build — interactive setup for provisioning, scripts, and validation'
mode: 'agent'
---

# D365 Customer Service Demo Setup

You are launching a new Dynamics 365 Customer Service demo build. Walk me through an interactive setup process, collecting the information below step by step (don't dump the whole questionnaire at once — ask 2-3 questions at a time, grouping related items).

## Information to Collect

**Customer basics:**
- Customer name (folder-friendly, e.g. "contoso")
- Industry (Manufacturing, Financial Services, Retail, Healthcare, etc.)
- Brand names / business units (comma-separated)
- D365 Org URL (e.g. https://orgXXXXX.crm.dynamics.com)
- Incumbent CRM being replaced (Salesforce, Zendesk, ServiceNow, or greenfield)

**Support model:**
- Channels in scope (email, phone, chat, web portal)
- Agent headcount / contact center size
- Number of customer tiers and their labels (e.g. 4 tiers: Strategic, Key, Standard, Basic)
- SLA targets: first response (minutes) and resolution (minutes)
- Business hours and work days
- Priority hot words (e.g. Urgent, Emergency, Recall, Safety)

**Demo goals:**
- Top 3-5 pain points or demo objectives
- Key personas (e.g. Frontline Agent, Supervisor, IT Admin) with names if available
- Products/services to feature in cases, orders, and warranties
- Which capabilities to showcase (pick from: unified routing, SLA enforcement, AI classification, Copilot assist, Customer 360, knowledge articles, omnichannel, self-service portal, order management, warranty lookup, quality management, workforce management)

**Additional context:**
- Timeline or demo date
- Competitive positioning notes
- First demo vs. deep-dive
- Any specific screens or workflows they've asked to see

## After Collecting Information

Once I have the answers, execute these steps in order:

1. **Create the customer folder and config:**
   - Create `customers/{name}/d365/config/environment.json` using the collected data
   - Create `customers/{name}/d365/data/`, `demo-assets/`, `copilot-studio/` directories

2. **Generate the environment.json** following this schema (reference `customers/zurnelkay/d365/config/environment.json` for the exact format):
   - `environment.name`, `environment.url`, `environment.apiVersion`
   - `demo.brands`, `demo.customerTiers`, `demo.hotWords`, `demo.sla`, `demo.caseOrigins`, `demo.agentCount`

3. **Run PowerShell provisioning** from `d365/scripts/`:
   ```powershell
   cd d365/scripts
   .\00-Setup.ps1 -Customer {name}
   ```
   Run step by step, troubleshooting any failures before continuing.

4. **Validate the environment:**
   - Use the D365DemoPrep agent's `validate_environment` action, or run the validation checks manually against the org.

5. **Generate demo assets:**
   - Demo script (main narrative with talking points)
   - Execution guide (presenter cheat sheet with exact record IDs and nav paths)
   - Phone call script (inbound call scenario)
   - Chat demo script (bot + escalation scenario)
   - Sample emails (email-to-case threads)

6. **Report the results** — show what was created, any failures, and the validation score.

## Key Rules
- Use `Find-OrCreate-Record` / idempotent patterns — every script must be safe to re-run
- Never hard-code customer-specific values in shared scripts
- Export all provisioned record IDs to `customers/{name}/d365/data/*.json`
- Demo scripts must use customer-specific personas, products, and terminology — never generic placeholders
