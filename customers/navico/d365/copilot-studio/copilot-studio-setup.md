# Navico Self-Service Copilot Agent — Setup & Portal Embed Guide

> **Base Template:** This agent extends the reusable CS Self-Service template at `templates/copilot-studio-cs-agent/`. The base template provides universal flows (troubleshoot, warranty, registration, escalate, fallback). This Navico version adds: marine-specific diagnostics, 5-brand context, NMEA 2000 troubleshooting, safety override for marine distress, B2B Certification topic, and 14 Navico KB article references.

## Overview

This guide covers setting up the **Navico Self-Service Assistant** — a Copilot Studio agent embedded in the Power Pages portal that serves both B2B dealers/distributors and B2C consumers. The agent handles product troubleshooting, warranty checks, RMA guidance, product registration, and certification inquiries.

**What Navico Adds Over the Base Template:**
- 🚢 Marine safety override (Man Overboard, Navigation Failure, Lost at Sea, Vessel Down)
- 🏷️ 5-brand serial prefix identification (SIM-, LWR-, BG-, CMAP-, NST-)
- 📡 NMEA 2000 / Ethernet / WiFi diagnostic steps (marine networking)
- 🎓 Dealer Certification Inquiry topic (B2B — check/enroll/renew/learn)
- 🛡️ System Assembly Assurance for certified installer registrations
- 📚 14 Navico-specific KB articles linked in agent instructions

**Architecture:**
```
Customer (Power Pages Portal)
    |
    v
Chat Widget (Omnichannel)
    |
    v
Copilot Studio Agent (Navico Self-Service Assistant)
    |-- Answers from 14 Navico KB articles (self-serve)
    |-- Guided troubleshooting (power, firmware, connectivity)
    |-- Warranty lookup guidance
    |-- Product registration intake
    |-- Certification program info (B2B)
    |-- Recognizes escalation triggers
    |
    v (escalate)
Omnichannel Routing
    |-- B2B → account tier-based queue assignment
    |-- B2C → standard consumer queue
    |-- Safety keywords → immediate Tier 4
    |
    v
CSR (Customer Service Workspace)
    |-- Full bot transcript visible
    |-- Customer 360 (account, tier, assets, entitlements)
    |-- Copilot Agent Assist (KB suggestions, intent detection)
    |-- Case auto-created with chat context
```

---

## Source Files

### Base Template (inherited)
Located at `templates/copilot-studio-cs-agent/` — provides the universal CS self-service flows:

| File | Purpose |
|------|---------|
| `agent.mcs.yml` | Generic agent instructions (no branding) |
| `topics/ConversationStart.mcs.yml` | Generic welcome greeting |
| `topics/ProductTroubleshoot.mcs.yml` | Universal diagnostics: power / software / connectivity / performance |
| `topics/WarrantyCheck.mcs.yml` | Serial → warranty info → next steps |
| `topics/ProductRegistration.mcs.yml` | Serial + purchase date + installer type → escalate |
| `topics/Escalate.mcs.yml` | Live agent handoff with context |
| `topics/Fallback.mcs.yml` | Retry twice → escalate on 3rd failure |

### Navico Customizations
Located at `customers/navico/d365/copilot-studio/` — overrides and additions:

| File | What Changed vs Base |
|------|---------------------|
| `agent.mcs.yml` | Navico branding, 5-brand context, serial prefixes, marine safety override, 14 KB article references, customer tier definitions |
| `topics/ConversationStart.mcs.yml` | "Welcome to Navico Group Support!" + certification option added |
| `topics/ProductTroubleshoot.mcs.yml` | Marine-specific: NMEA 2000 backbone, firmware known-issues table, brand-specific escalation, fleet escalation |
| `topics/WarrantyCheck.mcs.yml` | Navico warranty periods, 4 RMA types (Exchange/Credit/Repair/OBS), tier-based timelines |
| `topics/ProductRegistration.mcs.yml` | System Assembly Assurance for certified installers, Navico support level qualification |
| `topics/CertificationInquiry.mcs.yml` | **NEW** — B2B dealer certification: 3 levels, portal enrollment, renewal, status check |
| `topics/Escalate.mcs.yml` | Passes BrandContext and CustomerSegment variables |
| `topics/Fallback.mcs.yml` | Adds certification to the capability menu |

---

## Step 1: Create the Agent in Copilot Studio

1. Go to **https://copilotstudio.microsoft.com**
2. Select your environment (`orgecbce8ef`)
3. Click **Create** → **New agent**
4. Name: **Navico Self-Service Assistant**
5. Description: Copy from `agent.mcs.yml`
6. Language: English (US)
7. Click **Create**

### Configure AI Settings
1. Go to **Settings** (gear icon) → **Generative AI**
2. Enable:
   - ✅ Use AI to answer questions (generative answers)
   - ✅ Boost conversations
   - ✅ Use latest AI models
3. Content moderation: **Medium**
4. Orchestration type: **Generative**

### Add Agent Instructions
1. Go to **Overview** → **Instructions**
2. Paste the full instructions from `agent.mcs.yml` (the `instructions:` block)
3. Save

---

## Step 2: Configure Knowledge Sources

> ⚠️ Knowledge sources MUST be configured in the Copilot Studio browser — they cannot be set via YAML.

1. In Copilot Studio, select the agent → **Knowledge** (left nav)
2. Click **Add knowledge**
3. Select **Dataverse** → **Knowledge articles** (`knowledgearticles` entity)
4. Filter: Published articles only (`statecode eq 3`)
5. Enable: "Use knowledge to answer questions"

### Key KB Articles the Agent Should Surface

| Scenario | KB Article |
|----------|-----------|
| Product won't turn on | KA-01268: Navico Product Fault Diagnosis |
| Firmware update failed | KA-01273: Firmware Update Recovery Steps |
| Simrad NSX touchscreen issue | KA-01262: Simrad NSX Touchscreen Recovery |
| NMEA 2000 / Ethernet issues | KA-01270: NMEA 2000 and Ethernet Troubleshooting |
| B&G wind calibration | KA-01263: B&G Triton2 Wind Calibration |
| Product compatibility | KA-01271: Product Compatibility Lookup |
| Warranty inquiry | KA-01272: Warranty Status Validation |
| Lowrance not powering on | KA-01264: Lowrance HDS Live Diagnostics |
| RMA overview | KA-01265: RMA Process Overview |
| RMA Exchange | KA-01274: RMA Exchange Processing |
| RMA Repair | KA-01280: RMA Repair Center Processing |
| RMA Credit | KA-01276: Credit and Refund Processing |
| Product registration | KA-01277: Product Registration & Warranty Activation |
| Certification program | KA-01278: Dealer Certification Program Guide |

---

## Step 3: Create Topics

For each topic YAML file, create the corresponding topic in Copilot Studio:

### Option A: Via VS Code Extension (Recommended)
1. Clone the agent in VS Code using the Copilot Studio extension
2. Copy the topic YAML files into the cloned `topics/` folder
3. Push changes back to the environment

### Option B: Via Browser
1. In Copilot Studio, go to **Topics**
2. Click **+ New topic** → **From blank**
3. Recreate each topic using the trigger phrases, questions, conditions, and messages from the YAML files

### Topics to Create

| Topic | Trigger Examples | Key Flow |
|-------|-----------------|----------|
| **ConversationStart** | (automatic) | Welcome message with 5 capability options |
| **Product Troubleshoot** | "not working", "broken", "firmware issue", "NMEA not connecting" | Serial → issue type → diagnostic steps → resolve or escalate |
| **Warranty Check** | "warranty status", "still covered", "when does warranty end" | Serial → lookup → next step (specialist / extended / RMA) |
| **Product Registration** | "register my product", "activate warranty" | Serial → purchase date → installer type → escalate to complete |
| **Certification Inquiry** | "certification status", "get certified", "renew" | Action choice → check/enroll/renew/learn → info or escalate |
| **Escalate** | "talk to a person", "live agent" | Transfer with conversation context |
| **Fallback** | (unknown intent) | Retry twice → capability menu → escalate on 3rd failure |

---

## Step 4: Connect to Omnichannel

1. Go to **D365 Customer Service Admin Center**
2. Navigate to **Workstreams** → find (or create) a **Chat** workstream for the portal
3. Under the **Bot** section:
   - Click **Add bot**
   - Select **Navico Self-Service Assistant**
   - Position: **Before live agent** (bot handles first, escalates when needed)
4. Under **Context variables**, ensure these are mapped:
   - `EscalationReason` → captures why the bot escalated
   - `SerialNumber` → passes the serial to the live agent
   - `CustomerSegment` → B2B or B2C indicator

---

## Step 5: Embed on Power Pages Portal

### Add Chat Widget to Power Pages

1. Go to **Power Pages** → select your Navico portal site
2. Go to **Set up** → **Integrated chat (preview)** or use the manual method below

### Manual Embed (if integrated chat isn't available)

1. In Copilot Studio, go to the agent → **Channels** → **Custom website**
2. Copy the embed snippet (it looks like):

```html
<script src="https://powerva.microsoft.com/api/botmanagement/v1/directline/directlinetoken?botId=YOUR_BOT_ID&tenantId=daa9e2eb-aaf1-46a8-a37e-3fd2e5821cb6"></script>
```

3. In Power Pages → **Portal Management** → **Content Snippets**
4. Find or create: `Chat Widget Code`
5. Paste the embed snippet
6. Alternatively, add to the portal's **Header** template:

```html
<!-- Navico Self-Service Copilot Agent -->
<script src="https://pva.azurewebsites.net/api/botmanagement/v1/directline/directlinetoken"
        data-bot-id="YOUR_BOT_ID"
        data-tenant-id="daa9e2eb-aaf1-46a8-a37e-3fd2e5821cb6">
</script>
```

> 📝 Replace `YOUR_BOT_ID` with the actual bot ID after creation in Step 1.

---

## Step 6: Test the Flow

### Test in Copilot Studio (browser)
1. Click **Test your agent** (bottom-left panel)
2. Scenarios to test:

| Test | What to Type | Expected Behavior |
|------|-------------|-------------------|
| Welcome | (start conversation) | Shows welcome message with 5 options |
| Troubleshoot | "My Simrad screen won't turn on" | Asks for serial → power diagnostic steps → resolve or escalate |
| Firmware | "Firmware update bricked my unit" | Asks for serial → firmware recovery steps → resolve or escalate |
| Warranty | "Is my product still under warranty?" | Asks for serial → warranty info → next step options |
| Registration | "I want to register my new Lowrance" | Asks for serial, purchase date, installer type → escalate to complete |
| Certification (B2B) | "What's my certification status?" | Offers: check/enroll/renew/learn → info or escalate |
| Escalation | "I want to talk to a person" | Transfers to live agent with context |
| Safety | "My navigation system failed while I'm at sea" | IMMEDIATE escalation with urgent priority |
| Fallback | "asdfghjkl" (3 times) | Retry message → retry → escalate |

### Test End-to-End (Portal)
1. Open your Power Pages portal
2. Click the chat widget
3. Verify bot greeting appears
4. Walk through each scenario above
5. On escalation, verify:
   - Live agent sees the bot transcript
   - Context variables (serial, escalation reason) are passed
   - Case is auto-created with chat context

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot doesn't appear on portal | Verify: Channel connected in Copilot Studio + bot assigned in Omnichannel workstream |
| KB articles not surfacing | Check: Knowledge source configured + articles in Published state |
| Escalation fails / hangs | Verify: Omnichannel chat workstream is active + bot is connected |
| Agent doesn't see bot transcript | Ensure: context variables are mapped in Omnichannel admin |
| Bot greets but then hangs | Check: topics don't have infinite loops; Fallback topic has escalation path |
| Safety words not escalating | Safety override is in the agent instructions, not a topic. Verify instructions are saved in Copilot Studio |
| B2B vs B2C not detected | Detection relies on portal login context. Verify portal authentication is configured and passing user claims |

---

## Demo Talking Points

When showing the portal agent to Navico:

1. **"60% deflection potential"** — Natalia estimated 60% of issues could be resolved without a human. The bot handles the most common: troubleshooting, warranty checks, and registration.

2. **"Replaces Rusty Tech"** — Their current ServiceTarget Q&A system is dated. This is AI-powered, conversational, and connected to live data.

3. **"No agents or self-service today"** — Their Optimizely portal has ZERO self-service capability. This is net-new value.

4. **"Context carries over"** — When the bot escalates, the live agent sees EVERYTHING: serial number, issue type, steps already attempted. No "please repeat your issue."

5. **"B2B and B2C in one agent"** — The same agent detects whether it's a dealer checking certification or a consumer asking about warranty. Different tone, same platform.

6. **"KB-powered answers"** — The bot answers from the same KB articles your CSRs use. One source of truth, two audiences.

7. **"Safety override"** — Marine electronics are safety-critical. The bot immediately escalates on distress keywords — no troubleshooting when lives could be at risk.

---

## Reuse for Another Customer

This Navico agent was built on top of the **reusable CS Self-Service template** at `templates/copilot-studio-cs-agent/`. To set up a similar agent for a different demo:

1. **Copy the base template** — `templates/copilot-studio-cs-agent/` → `customers/{name}/d365/copilot-studio/`
2. **Update agent instructions** — replace generic text with customer name, brands, products, serial patterns, tier definitions
3. **Brand the welcome** — update ConversationStart.mcs.yml with customer name
4. **Customize troubleshooting** — add product-specific diagnostic steps (the base has generic power/software/connectivity/performance)
5. **Add industry topics** — if the customer has B2B certification, field service, compliance, or other unique flows, add topic YAML files
6. **Link KB articles** — reference the customer's specific KB article numbers in the agent instructions
7. **Add safety keywords** — if the industry has safety-critical scenarios (marine distress, entrapment, hazmat, etc.)
8. **Create the setup guide** — copy this file and update the customer-specific sections

See `templates/copilot-studio-cs-agent/README.md` for the full customization checklist.
