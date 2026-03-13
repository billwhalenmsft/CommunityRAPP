# Copilot Studio Bot Setup Guide -- Zurn Elkay Customer Care

## Overview

Configure a Copilot Studio agent (bot) that handles initial customer chat on the Zurn Elkay portal. The bot triages inquiries, surfaces KB articles, and escalates to a live Customer Care Associate when needed.

**Environment**: https://orgecbce8ef.crm.dynamics.com
**Portal**: https://zurnelkaycustomercare.powerappsportals.com
**Chat Workstream**: 9bc69cb2-6cd0-b8b5-8fab-da65ba399e94
**Bot ID**: da8f1b23-c018-f111-8342-7ced8d18c8d7
**Schema**: cra1f_customerServicePortalAssistant
**Agent Source**: agents/Customer Service Portal Assistant/

---

## Agent Source Files (VS Code)

The bot is cloned locally and customizations are made in YAML, then pushed back via the Copilot Studio extension.

| File | Purpose |
|------|---------|
| agent.mcs.yml | Agent instructions + capabilities (Zurn-branded) |
| settings.mcs.yml | Channels, AI settings, authentication |
| topics/ConversationStart.mcs.yml | Opening greeting (Zurn-branded) |
| topics/Greeting.mcs.yml | Greeting response (Zurn-branded) |
| topics/Escalate.mcs.yml | Transfer to live agent (Zurn triggers + message) |
| topics/Search.mcs.yml | Generative KB search / conversational boosting |
| topics/Fallback.mcs.yml | Fallback after 3 failed attempts -> escalate |

### Key Customizations Applied

1. **ConversationStart** -- Branded welcome: "Welcome to Zurn Elkay Customer Care!"
2. **Greeting** -- Lists capabilities (troubleshooting, warranty, orders)
3. **Agent Instructions** -- Full Zurn/Elkay product context, tier awareness, tone examples
4. **Escalate** -- Cleaned up message + added Zurn-specific triggers (warranty, RMA, recall, safety, urgent)
5. **Escalation Handoff** -- TransferToAgent with AutomaticTransferContext (Omnichannel)

---

## Step 1: Push Changes to Copilot Studio

After editing YAML files locally, push to the environment:

1. Open the `agents/Customer Service Portal Assistant` folder in VS Code
2. Use the Copilot Studio extension to sync changes
3. Alternatively, copy updated YAML content directly into Copilot Studio web editor

---

## Step 2: Configure Knowledge Sources (Browser Required)

Knowledge source connections are NOT stored in YAML -- must be configured in the browser.

1. Go to https://copilotstudio.microsoft.com
2. Select the **Customer Service Portal Assistant** agent
3. Go to **Knowledge** (left nav)
4. Click **Add knowledge**
5. Select **Dataverse** -> **Knowledge articles** (knowledgearticles entity)
6. Enable: "Use knowledge to answer questions"

### Key KB Articles the Bot Should Surface

| Scenario | Expected KB Article |
|----------|-------------------|
| Flush valve / sensor issues | "Troubleshooting Zurn AquaVantage and E-Z Flush Valve Issues" |
| Warranty / RMA questions | "Zurn Warranty Policy and RMA Process" |
| Order status / placement | "How to Place a Zurn Product Order Through Your Distribution Partner" |
| Pricing / discounts | "Pricing, Quotes and Distributor Discount Tiers" |
| Backflow preventer issues | "Wilkins Backflow Preventer Maintenance and Testing Guide" |
| Drain issues | "Zurn Floor, Roof and Trench Drain Troubleshooting" |
| SLA questions | "SLA Targets and Response Time Standards" |
| Quality / recall | "Quality and Recall Notification Procedures" |

---

## Step 3: Verify Omnichannel Connection (Browser Required)

The bot is already connected to Omnichannel (configured in settings.mcs.yml). Verify in D365:

1. Go to Customer Service admin center
2. Navigate to **Workstreams** -> find the Chat workstream (9bc69cb2-6cd0-b8b5-8fab-da65ba399e94)
3. Click on it -> **Bot** section
4. Add/verify the **Customer Service Portal Assistant** is connected
5. Set bot behavior:
   - **Add bot** -> select your Copilot Studio bot
   - Position: Before live agent (bot handles first, then escalates)

---

## Step 4: Optional Custom Topics

The following custom topics can be created in Copilot Studio browser for richer demo flow. These are optional -- the generative Search topic + KB articles handle most queries.

### Topic: Product Troubleshooting

**Trigger phrases**: troubleshooting, not working, broken, issue with, problem with, flush valve, sensor, drain, faucet

**Flow**:
1. Ask: "Which product are you having trouble with?"
   - Flush valves / urinals
   - Bottle filling stations
   - Drains (floor, roof, trench)
   - Faucets / sensors
   - Backflow preventers
   - Other
2. Based on selection, search KB for matching articles
3. Present article summary and link
4. Ask: "Did this help resolve your issue?"
   - Yes -> "Glad I could help! Is there anything else?"
   - No -> "Let me connect you with a Customer Care Associate." -> Escalate

### Topic: Warranty / RMA

**Trigger phrases**: warranty, RMA, return, defective, claim, faulty, replace

**Flow**:
1. Bot says: "I can help with warranty information. For processing an actual warranty claim or RMA, I'll need to connect you with a Customer Care Associate."
2. Ask: "Would you like to review our warranty policy first, or connect directly with an agent?"
   - Review policy -> Surface "Zurn Warranty Policy and RMA Process" KB article
   - Connect to agent -> Escalate

---

## Step 5: Test the Flow

### Test in Copilot Studio (browser):
1. Click **Test your agent** (bottom-left)
2. Type: "I'm having trouble with a flush valve that keeps flushing by itself"
3. Verify: Bot surfaces the AquaVantage troubleshooting KB article
4. Type: "I already tried all that. Can I talk to someone?"
5. Verify: Bot escalates

### Test End-to-End (portal):
1. Open portal: https://zurnelkaycustomercare.powerappsportals.com
2. Click chat widget
3. Verify bot greeting appears
4. Walk through Scenario A (flush valve) or Scenario B (warranty claim)
5. Verify escalation routes to CS Workspace
6. Verify agent sees full bot transcript + customer context

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot doesn't appear on portal chat | Verify Channel connection in Copilot Studio + bot assignment in Omnichannel workstream settings |
| KB articles not surfacing | Check Knowledge source is connected + articles are in Published state |
| Escalation fails | Verify Omnichannel chat workstream is active + bot is connected to the correct channel |
| Agent doesn't see bot transcript | Ensure context variables are mapped in Omnichannel admin |
| Bot greets but then hangs | Check that topics don't have infinite loops; verify Fallback topic has an escalation path |

---

## Architecture Summary

```
Customer (Portal)
    |
    v
Chat Widget (Omnichannel)
    |
    v
Copilot Studio Bot
    |-- Answers from KB articles (self-serve)
    |-- Recognizes escalation triggers
    |
    v (escalate)
Omnichannel Routing
    |-- Tier-based queue assignment
    |-- Skills matching
    |-- Capacity check
    |
    v
Customer Care Associate (CS Workspace)
    |-- Full bot transcript visible
    |-- Customer 360 (account, tier, contacts, orders)
    |-- Copilot assist (KB suggestions, summarize, draft)
    |-- Case auto-created with chat context
```

---

## Time Estimate

| Task | Estimated Time |
|------|---------------|
| Push YAML changes (already done) | 5 min |
| Connect KB knowledge source | 5 min |
| Verify Omnichannel bot assignment | 10 min |
| Optional custom topics | 15 min |
| End-to-end testing | 15 min |
| **Total** | **~50 min** |
