# Chat Demo Script -- Copilot Studio Bot + Live Agent Escalation

## Overview

Single chat scenario demonstrating the full customer journey: portal visit → Copilot Studio bot triage → KB article suggestion → escalation to live Customer Care Associate → resolution with full customer context and cross-channel continuity.

**Duration**: ~8-10 minutes

---

## Portal Login Credentials (Local Contact Auth)

All hero contacts use **local contact authentication** (username + password) on the Power Pages portal. No Entra / Azure AD login required.

| Persona | Username | Password | Account | Tier |
|---------|----------|----------|---------|------|
| Rachel Chen | `rachel.chen` | `ZeDemo!2026` | Ferguson Enterprises | Tier 1 Strategic |
| Derek Lawson | `derek.lawson` | `ZeDemo!2026` | HD Supply | Tier 2 Premium |
| Tom Harrison | `tom.harrison` | `ZeDemo!2026` | Hajoca Corporation | Tier 3 Standard |
| Mike Reynolds | `mike.reynolds` | `ZeDemo!2026` | Pacific Plumbing Supply | Tier 4 Basic |
| James Morales | `james.morales` | `ZeDemo!2026` | HD Supply | Tier 2 Premium |

> **Portal URL**: https://zurnelkaycustomercare.powerappsportals.com  
> **Login page**: Click "Sign In" in the portal header, then use the **Local Account** tab (not Azure AD).  
> **Tip**: Use InPrivate / Incognito so sessions don't overlap with the phone scenario.

---

## Chat Scenario: Ferguson -- Filter Defect Warranty RMA

### Context
- **Customer**: Rachel Chen, Purchasing Director, Ferguson Enterprises
- **Account Tier**: Tier 1 Strategic (red badge)
- **Issue**: 50 WaterSentry Plus filters (EK-FL-6003) from batch WS-2026-0217 showing premature failure at ~1200 gallons (rated 3000)
- **Bot KB match**: "Zurn Warranty Policy and RMA Process"
- **Escalation trigger**: Needs actual RMA number + batch recall discussion — bot can't issue RMAs
- **Cross-reference**: PO #94820 from the phone scenario (200 WaterSentry Plus filters arriving soon)

### Pre-Demo Setup
- [ ] Portal open in a fresh InPrivate / Incognito window
- [ ] Navigate to https://zurnelkaycustomercare.powerappsportals.com
- [ ] **Sign in as Rachel Chen** (`rachel.chen` / `ZeDemo!2026`) via the Local Account tab
- [ ] CS Workspace open in another browser/tab (logged in as agent)
- [ ] Chat widget visible on portal (bottom-right bubble)
- [ ] Agent status set to "Available" for chat workstream

**Talking point**: "Rachel Chen is Purchasing Director at Ferguson Enterprises — the same Tier 1 Strategic account we saw in the phone scenario, but a different contact and a different channel. She's logged into the self-service portal with her own credentials, so the system identifies her immediately."

### The Chat Flow

#### Phase 1: Customer Opens Chat (0:00 - 0:30)

**On the portal** (signed in as Rachel Chen), click the chat bubble. The bot greets — and because Rachel is authenticated, the system already knows her account (Ferguson Enterprises, Tier 1 Strategic) and contact details.

> **Bot**: "Welcome to Zurn Elkay Customer Support! I'm here to help you with product questions, order status, warranty inquiries, and more. How can I help you today?"

**Type as Rachel**:

> "I need to initiate a warranty claim for defective WaterSentry Plus filters. Batch number WS-2026-0217. 50 units."

#### Phase 2: Bot Triage + KB Suggestion (0:30 - 1:30)

**Bot responds** (Copilot Studio recognizes this as a warranty issue and surfaces KB):

> **Bot**: "I found information about our warranty process: **Zurn Warranty Policy and RMA Process**. WaterSentry Plus filters carry a 1-year warranty on manufacturing defects. To start a warranty claim, you'll need the batch number (which you have: WS-2026-0217), proof of purchase, and a description of the defect. Would you like me to connect you with a Customer Care Associate to process the RMA?"

**Type as Rachel**:

> "Yes, please connect me. I also need to know if this batch was shipped to any of our other locations. These filters are failing at around 1200 gallons — less than half their rated capacity."

**Talking point to audience**: "The bot correctly identified this as a warranty claim and surfaced the right KB article. But for transactional actions like issuing an actual RMA number or investigating a batch defect, the bot knows to escalate to a human agent. That's intelligent triage — self-serve what you can, escalate what you can't."

#### Phase 3: Bot Escalates to Agent (1:30 - 2:00)

**Bot responds**:

> **Bot**: "I'll connect you with a Customer Care Associate who can process your RMA and look into the batch details. One moment please."

(If the bot doesn't auto-escalate, type: "I need to speak to someone" or "transfer to agent")

**What happens in CS Workspace**:
- Chat notification appears for the agent
- Agent sees: **Ferguson Enterprises** identified, **Tier 1 Strategic** (RED badge), Rachel Chen
- The full bot conversation transcript is visible — agent knows what was already discussed
- Case auto-created: "Ferguson - WaterSentry Plus filter defect batch WS-2026-0217"

**Talking point**: "Look at the difference in treatment. Ferguson is Tier 1 Strategic — red badge, priority routing, premium SLA. The agent gets the complete bot conversation history with no 'can you repeat what you told the bot?' needed. Rachel's account, tier, contact info — all pre-populated."

#### Phase 4: Agent Takes Over (2:00 - 4:00)

**Agent greets Rachel in chat**:

> "Hi Rachel, this is [agent name] with Zurn Elkay Customer Care. I can see you're reporting a defect in WaterSentry Plus filters from batch WS-2026-0217. Let me pull up the details."

**Agent actions** (show to audience):
1. Open the case — show the timeline:
   - Rachel's email with photos and test data (March 3)
   - Quality team note: batch had carbon media loading variance, 200 units shipped to 3 distributors
   - Warranty verification note: confirmed in warranty, Tier 1 gets 48-hour RMA turnaround
2. Point out: "The quality team has already reviewed this batch and confirmed the defect. The agent has all the context without a single phone call to the lab."

**Key demo moment** — show the quality note that reveals this affects other distributors:

**Agent responds**:

> "Rachel, I have good news. Our quality team has already investigated batch WS-2026-0217 and confirmed a manufacturing variance in the carbon media loading at our Erie plant. Your RMA is pre-approved. I'm issuing it now — you'll get replacement filters from batch WS-2026-0303, which has been verified. For your question about other locations: this batch shipped 50 units to your Texas branches, 80 to Hajoca in Pennsylvania, and 70 to Pacific Plumbing in Washington. We're proactively reaching out to those distributors as well."

**Talking point**: "The agent didn't have to escalate to quality, wait for lab analysis, or research the batch distribution. It's all right here on the case timeline. And because Ferguson is Tier 1 Strategic with a 48-hour RMA turnaround, the replacement ships tomorrow."

#### Phase 5: Cross-Channel Continuity (4:00 - 5:30)

**Type as Rachel**:

> "Excellent. I also want to flag — we have a pending order, PO #94820, for 200 WaterSentry Plus filters arriving soon. Can you verify those are from a good batch?"

**This connects to the phone scenario!** The agent can see PO #94820 in Ferguson's orders from Mike Reynolds' phone call.

**Agent responds**:

> "Let me check... PO #94820 has 200 WaterSentry Plus filters. I can confirm those are from batch WS-2026-0303 — the verified-good batch. You're all set on that shipment. I'll include the batch verification in your RMA follow-up email."

**Talking point**: "Here's the power of unified data. Mike Reynolds called about PO #94820 on the phone earlier — different person, different channel, same account. Rachel is asking about it via chat. Because everything lives on one platform, the agent sees the complete picture across contacts and channels."

#### Phase 6: Wrap-Up (5:30 - 7:00)

**Type as Rachel**:

> "Perfect. Send everything to rachel.chen@ferguson.com. And thank you for the fast turnaround."

**Agent actions**:
- Update case notes
- Show **Copilot summarizing the chat conversation** — auto-generated from the full transcript including the bot portion
- Show **Copilot drafting a confirmation email** — RMA number, replacement batch, estimated delivery, PO #94820 verification

**Talking point**: "Just like the phone scenario, Copilot auto-summarizes the entire interaction — including the bot triage — and drafts the follow-up email. The agent reviews and sends in seconds. This entire interaction — from Rachel's first chat message to RMA issued with cross-distributor recall initiated — took under 7 minutes. In the current process, this would involve multiple emails, phone calls to quality, manual batch lookups, and days of back-and-forth."

---

## Key Demo Highlights

| Feature | What to Show |
|---------|-------------|
| Bot triage | Copilot Studio surfaces "Zurn Warranty Policy and RMA Process" KB article |
| Escalation trigger | Transactional action (issue RMA) — bot knows to hand off |
| Tier treatment | Tier 1 Strategic (red badge) — 48-hour priority RMA turnaround |
| Internal intelligence | Quality team batch investigation + cross-distributor impact already on timeline |
| Cross-channel continuity | PO #94820 from Mike's phone call visible in Rachel's chat — unified account view |
| Copilot assist | Chat summary (including bot portion) + RMA confirmation email draft |

---

## Fallback Notes

**If portal login doesn't work:**
- Try password reset: navigate to the Sign In page, click "Forgot password?", enter the email (`rachel.chen@ferguson.com`)
- If local login tab isn't visible, check site setting `Authentication/Registration/LocalLoginEnabled` = `true`
- Fallback: use Derek Lawson (`derek.lawson` / `ZeDemo!2026`) and narrate as Rachel

**If Copilot Studio bot is not configured yet:**
- Open the portal chat as a plain live chat (no bot layer)
- Walk through the scenario as agent-only
- Explain: "In the full deployment, a Copilot Studio bot handles the initial triage and KB lookup before escalating"

**If chat routing isn't working:**
- Create the case manually and walk through the timeline
- Show the data that would appear during a live chat
- Still demonstrates customer 360, tiered treatment, and agent assist

**If the bot doesn't recognize the authenticated customer:**
- The bot should receive the contact record from the portal session. If it doesn't, mention: "In the real deployment, the bot inherits the portal session identity automatically." Continue the scenario manually.

**If asked about bot customization:**
- "The bot is built in Copilot Studio — your team can customize topics, add new product flows, connect to external systems via connectors, and define exactly when to escalate vs. self-serve"

**If asked about portal authentication model:**
- "The portal supports both local contact login and Azure AD / Entra ID SSO. For the demo we're using local accounts. In production, you'd typically enable Entra ID SSO so customer contacts authenticate with their corporate credentials."

---

## Data Reference

| Item | Value |
|------|-------|
| Account | Ferguson Enterprises (Tier 1 Strategic) |
| Chatter | Rachel Chen, Purchasing Director, (757) 555-2002 |
| Portal Login | `rachel.chen` / `ZeDemo!2026` |
| Issue | 50 WaterSentry Plus filters from batch WS-2026-0217 failing at ~1200 gal (rated 3000) |
| Root Cause | Carbon media loading variance at Erie plant |
| Resolution | RMA approved, replacements from verified batch WS-2026-0303 |
| Other affected | Hajoca (80 units), Pacific Plumbing (70 units) — proactive recall |
| KB Article | "Zurn Warranty Policy and RMA Process" |
| Cross-ref | PO #94820 from phone scenario (200 filters — batch WS-2026-0303 verified good) |
| Case ID | See data/chat-scenario-ids.json |
