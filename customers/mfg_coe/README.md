# Agentic CoE — Discrete Manufacturing

A multi-persona AI agent team that operates autonomously and in partnership with Bill Whalen to accelerate output across Discrete Manufacturing work: SOPs, business process documentation, CRM/agentic use cases, and Microsoft tech stack solutions.

## 🌐 Command Center Web UI

The team's live dashboard is the **Bots in Blazers Command Center** — a single-page web app that provides a real-time view of agent activity, GitHub Issues, outcomes, and a chat interface.

**Live:** [bots-in-blazers.fun](https://bots-in-blazers.fun)  
**Source:** `customers/mfg_coe/web_ui/index.html`

### Features

| Panel | Description |
|-------|-------------|
| 🏠 Dashboard | KPIs, agent status feed, `needs-bill` alerts, recent activity |
| 🤖 Agent Team | All agent cards with status, role, and quick-chat |
| 🎯 Outcomes | Outcome tracking with progress bars and linked issues |
| 📋 Backlog | GitHub Issues filtered by `mfg-coe` label |
| 🗂️ Kanban | Issues by pipeline stage (raw-idea → outcome-validated) |
| 💬 Chat | Direct conversation with any agent via Azure Functions |
| 🌐 Forum | Linked GitHub Discussions |
| 🗺️ Environments | D365 demo environment cards |
| ⚙️ Settings | GitHub PAT, agent endpoint, and **theme picker** |

### Themes

Pick from 7 built-in themes — via the dropdown in the topbar or the **Appearance** card in Settings:

| Theme | Vibe |
|-------|------|
| 🌙 Dark | GitHub-style dark (default) |
| ☀️ Light | Clean white |
| ⚡ Neon | Cyan glow with boot sequence |
| 🌿 Forest | Deep greens |
| 🌌 Midnight | Deep purple/indigo |
| 🌅 Sunset | Warm orange/ember |
| 🌊 Ocean | Dark teal/deep blue |

---

## 🚀 Deploying the Web UI

### Option A — GitHub Pages (Free, Public)

Best for: open/public repos, zero infrastructure, simplest setup.

1. **Enable Pages** in repo Settings → Pages → Source: `GitHub Actions`
2. The workflow at `.github/workflows/mfg_coe_deploy_web.yml` deploys on every push to `main`
3. URL: `https://billwhalenmsft.github.io/CommunityRAPP-BillWhalen/`

To deploy manually:
```bash
# Trigger the workflow
gh workflow run "mfg-coe-deploy-web" --repo billwhalenmsft/CommunityRAPP-BillWhalen
```

---

### Option B — Azure Static Web Apps (Free Tier) ⭐ Recommended

Best for: custom domain, auth, private repos, SLA-backed.  
**This is what powers [bots-in-blazers.fun](https://bots-in-blazers.fun).**

**Create the Static Web App:**
```bash
az staticwebapp create \
  --name bots-in-blazers \
  --resource-group your-rg \
  --location "eastus2" \
  --sku Free \
  --source https://github.com/billwhalenmsft/CommunityRAPP-BillWhalen \
  --branch main \
  --app-location "customers/mfg_coe/web_ui" \
  --output-location "." \
  --login-with-github
```

**Add the deployment token as a secret:**
```bash
# Copy the token from the Azure portal → Static Web App → Manage deployment token
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN \
  --repo billwhalenmsft/CommunityRAPP-BillWhalen \
  --body "YOUR_TOKEN_HERE"
```

**Custom domain:**
```bash
az staticwebapp hostname set \
  --name bots-in-blazers \
  --resource-group your-rg \
  --hostname bots-in-blazers.fun
```

---

### Option C — Azure Blob Storage Static Website (~$0.01/month)

Best for: ultra-low cost, no CI/CD needed, manual updates OK.

```bash
# Enable static website hosting
az storage blob service-properties update \
  --account-name YOUR_STORAGE_ACCOUNT \
  --static-website \
  --index-document index.html \
  --404-document index.html

# Upload the file
az storage blob upload \
  --account-name YOUR_STORAGE_ACCOUNT \
  --container-name '$web' \
  --name index.html \
  --file customers/mfg_coe/web_ui/index.html \
  --overwrite

# Get the URL
az storage account show \
  --name YOUR_STORAGE_ACCOUNT \
  --query "primaryEndpoints.web" -o tsv
```

---

### Comparison

| | GitHub Pages | Azure SWA (Free) | Azure Blob |
|--|--|--|--|
| Cost | Free | Free | ~$0.01/mo |
| Custom domain | ✅ | ✅ | ✅ |
| HTTPS | ✅ | ✅ | ✅ |
| Auth (AAD/GitHub) | ❌ | ✅ | ❌ |
| CI/CD auto-deploy | ✅ | ✅ | Manual |
| Private repo support | ❌ | ✅ | N/A |
| SLA | ❌ | 99.95% | 99.9% |

---

### First-Time Setup (Browser)

Once deployed, open the web app and:

1. Go to **Settings** ⚙️
2. Enter your **GitHub PAT** (`ghp_...`) with `repo` + `read:discussion` scopes
3. Click **Save PAT** — the dashboard will load live data
4. Pick your preferred **theme** in the Appearance section

The PAT is stored only in your browser's `localStorage` — it never leaves your machine except to call `api.github.com`.

---

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
  web_ui/             — Command Center web app (index.html)
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
