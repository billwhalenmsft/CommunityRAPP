# Demo Execution Guide — Zurn / Elkay Customer Service

> **Demo Date**: March 12, 2026 (2 hours)  
> **Environment**: https://orgecbce8ef.crm.dynamics.com  
> **Portal**: https://zurnelkaycustomercare.powerappsportals.com  
> **Email Queue**: `customerservice@D365DemoTSCE30330346.onmicrosoft.com`  
> **Your character**: **Bill** — Customer Service Representative  
> **Supervisor character**: **Sarah Kim** — Care Leader / QA Supervisor

---

## 📑 Table of Contents

1. [The Story](#the-story)
2. [Pre-Demo Checklist](#pre-demo-checklist)
3. [Quick Reference — Hero Records](#quick-reference--hero-records)
4. [Portal Login Credentials](#portal-login-credentials)
5. **Demo Flow**
   - [Section 1: Connect & Orient](#section-1-connect--orient-10-min) (~10 min)
   - [Section 2: Their World Today](#section-2-their-world-today-5-min) (~5 min)
   - [Section 3a: CS Workspace & Dashboards](#section-3a-cs-workspace--dashboards-5-min) (~5 min)
   - [Section 3b: Email Case & Copilot](#section-3b-email-case--copilot-10-min) (~10 min) 📧
   - [Section 3c: Timeline & Customer 360](#section-3c-timeline--customer-360-5-min) (~5 min)
   - [Section 3d: Knowledge](#section-3d-knowledge-in-the-flow-of-work-5-min) (~5 min)
   - [Section 3e: Teams Embedded](#section-3e-teams-embedded-chat-3-min) (~3 min)
   - [Section 3f: PHONE CALL — THE MAIN EVENT](#section-3f-phone-call--the-main-event-10-15-min) (~10-15 min) 📞
   - [Section 3g: Chat / Digital Messaging](#section-3g-chat--digital-messaging-10-15-min) (~10-15 min) 💬
   - [Section 3h: Tiered Routing](#section-3h-tiered-routing--skills-5-min) (~5 min)
   - [Section 3i: Guided Process Flows](#section-3i-guided-process-flows-5-min) (~5 min)
   - [Section 3j: Proactive Notifications](#section-3j-proactive-notifications-3-min) (~3 min)
   - [Section 4a: Real-Time Dashboards](#section-4a-real-time-dashboards) (Care Leader)
   - [Section 4b: Agent Performance](#section-4b-agent-performance-metrics) (Care Leader)
   - [Section 4c: Workforce Management](#section-4c-workforce-management) (Care Leader)
   - [Section 4d: Quality Management](#section-4d-quality-management) (Care Leader)
   - [Section 5: AI Agents](#section-5-ai-agents-10-min) (~10 min)
   - [Section 6: Platform & Close](#section-6-platform-extensibility--close) (~5 min)
6. [Data Appendix](#data-appendix)

---

## The Story

This demo tells **one connected story** across channels, roles, and scenarios — all centered on **Ferguson Enterprises**, the largest US plumbing distributor and Zurn/Elkay's #1 channel partner.

**The characters:**
- **Bill** (you) — the CSR handling Ferguson's account. You know Mike, Rachel, and Tom. You're their go-to person.
- **Mike Reynolds** — Ferguson's Houston DC Field Ops Manager. He's calling about PO #94820 — a $258K hydration products order that needs modification after a school district project scope change.
- **Rachel Chen** — Ferguson's Purchasing Director. She chats in about a defective filter batch (WS-2026-0217). She also negotiated the 15% bulk filter discount Mike will ask about.
- **Derek Lawson** — HD Supply's Facilities Maintenance Supervisor with sensor flush valve issues at a Hilton hotel.
- **Sarah Kim** — your supervisor (Care Leader). She reviews dashboards, agent performance, WFM schedules, and QM evaluations.

**The arc:**
1. **Email arrives** (Section 3b) — Ferguson shipment issue creates a case automatically
2. **Mike calls** (Section 3f) — Same account, different contact, different issue. Bill handles PO modifications live with Copilot and the Intent Agent surfacing procedures in real-time
3. **Derek chats** (Section 3g-A) — Different customer, different channel. Bot triages, then escalates to Bill with full context
4. **Rachel chats** (Section 3g-B) — Back to Ferguson. Different contact, quality issue. Cross-references Mike's order
5. **Sarah reviews** (Section 4) — Supervisor sees the whole operation: dashboards, agent metrics, WFM schedules, QM scoring
6. **AI reveal** (Section 5) — Connect the dots: Intent Agent, Case Management Agent, Knowledge Agent

> **Everything connects.** The email, phone call, and chats all show up in Ferguson's timeline. Sarah sees Bill's performance across all channels. The AI agents surface the right procedures at the right moments. This is the unified platform story.

---

## Pre-Demo Checklist

*30 minutes before showtime*

- [ ] Log into CS Workspace: https://orgecbce8ef.crm.dynamics.com
- [ ] Verify "My Active Cases" view — Ferguson case visible
- [ ] Verify voice channel status is green (connected)
- [ ] Verify Copilot panel is enabled (right side)
- [ ] Open portal in separate browser tab: https://zurnelkaycustomercare.powerappsportals.com
- [ ] Pre-stage portal logins: `derek.lawson` / `ZeDemo!2026` (Scenario A) or `rachel.chen` / `ZeDemo!2026` (Scenario B)
- [ ] Confirm portal contact name appears in header/profile menu
- [ ] Have second phone ready for Mike Reynolds call
- [ ] Have this guide open on second monitor
- [ ] Quick test: open Ferguson account → confirm revenue, tier, orders visible
- [ ] Quick test: open phone case → confirm timeline has notes, call, email
- [ ] Pre-draft the Ferguson email in Outlook (Tab 4) — ready to send

---

## Quick Reference — Hero Records

### 🏢 Hero Account — Ferguson Enterprises

| Field | Value |
|-------|-------|
| Account Name | **Ferguson Enterprises** |
| Account ID | `ee8604af-8912-f111-8342-000d3a316172` |
| Customer Tier | **Tier 1 Strategic** (red badge) |
| Revenue | $27.8 billion |
| Employees | 36,000 |
| HQ | 751 Lakefront Commons, Newport News, VA 23602 |

### 👤 Hero Contacts

| Name | Role | Phone | Email |
|------|------|-------|-------|
| **Mike Reynolds** 📞 | Field Ops Mgr — Houston DC | (713) 555-0184 | mike.reynolds@ferguson.com |
| **Rachel Chen** 💬 | Purchasing Director | (757) 555-2002 | rachel.chen@ferguson.com |
| Tom Harrison | Plumbing Category Mgr | (757) 555-2001 | tom.harrison@ferguson.com |

> Mike is the caller. Rachel is the chatter (Scenario B). Tom appears in the timeline.

### 📦 PO #94820 — The Demo Order ($258,150)

| SKU | Product | Qty | Unit$ | Extended | Action |
|-----|---------|-----|-------|----------|--------|
| EK-BF-5001 | EZH2O Bottle Filling Station | 120 | $1,150 | $138,000 | ✅ **KEEP — expedite** |
| EK-WC-5002 | Wall Mount Cooler Bi-Level ADA | 60 | $780 | $46,800 | ✅ **KEEP — expedite** |
| EK-FL-6003 | WaterSentry Plus Filter | 200 | $29.50 | $5,900 | ✅ **KEEP — expedite + discount?** |
| EK-DF-5003 | Floor Mount Drinking Fountain ADA | 25 | $1,450 | $36,250 | ❌ **CANCEL** |
| EK-SS-6001 | Stainless Steel Sink Commercial | 40 | $780 | $31,200 | ❌ **CANCEL** |

> **Cancel total**: ~$67K. **Remaining**: ~$191K. **Delivery move**: March 15 → March 10.  
> **Filter discount**: 15% on 500+ units (Rachel negotiated). Mike's order has 200 — may not qualify unless qty increases.

### 📞 Hero Case — Phone Scenario

| Field | Value |
|-------|-------|
| Case Title | Ferguson PO #94820 - Order modification request |
| Case ID | `41739b76-a718-f111-8342-7c1e520a58a1` |
| Origin | Phone |
| Priority | High |
| Tier Level | Tier 1 (red) |
| Primary Contact | Mike Reynolds |
| Serial Number | `234567ABC` (AquaVantage Flush Valve, warranty active through 2028-01-10) |

### Other Ferguson Orders

| PO # | Description | ID |
|------|------------|-----|
| #93201 | Zurn Backflow Q4 (delivered, context) | `82017270-a718-f111-8342-7ced8d18c8d7` |
| #95102 | Flush Valves Replenishment (active, context) | `5667fe76-a718-f111-8342-7ced8d18c8d7` |

---

## Portal Login Credentials

> 📋 **COPY/PASTE READY** — All passwords are `ZeDemo!2026`

| Persona | Username | Password | Account | Use |
|---------|----------|----------|---------|-----|
| Derek Lawson | `derek.lawson` | `ZeDemo!2026` | HD Supply | Chat Scenario A |
| James Morales | `james.morales` | `ZeDemo!2026` | HD Supply | Alternate |
| Rachel Chen | `rachel.chen` | `ZeDemo!2026` | Ferguson | Chat Scenario B |
| Tom Harrison | `tom.harrison` | `ZeDemo!2026` | Ferguson | Alternate |
| Mike Reynolds | `mike.reynolds` | `ZeDemo!2026` | Ferguson | Alternate |

---

## Demo Flow — Section by Section

---

### Section 1: Connect & Orient (~10 min)

**No special data needed.** General workspace orientation.

**Navigate**: CS Workspace home → point out left nav, session tabs, Copilot panel, multisession concept.

**Say**: "I'm Bill, and I work the Ferguson account — they're our biggest distributor. Let me show you what my day looks like in D365."

---

### Section 2: Their World Today (~5 min)

**No special data needed.** Validate their pain points — keep under 5 minutes.

> ⚠️ **DO NOT** bash Salesforce by name. Frame as "where you are today" vs "what's possible."

**Say**: "Before I show you what this can do, let me play back what I've heard about where you are today — Salesforce here, Genesys here, spreadsheets in between. Let me know if this matches."

**Transition bridge**: "Let's jump in and see how this works when everything is on one platform."

---

### Section 3a: CS Workspace & Dashboards (~5 min)

**Navigate**: Home → My Active Cases view

**What to show**:
- Tier Level column with colored pills (Tier 1 red, Tier 2 orange, Tier 3 blue, Tier 4 gray)
- SLA timers on cases (countdown)
- Case origin icons (email, phone)
- Priority column

> Ferguson cases will appear near the top due to Tier 1 + High priority.

**Say**: "These are my active cases. Notice how Ferguson shows up first — Tier 1 Strategic, red badge. The system knows they're our most important customer and treats them accordingly."

> 💰 **ROI — Agent Desktop Consolidation**: Agents work in one screen instead of 3–4 systems — CRM, phone, knowledge base, order management. Eliminating alt-tab reduces average handle time 15–30% and cuts new-hire ramp time 30–50% (one system to learn, not three). For a 200-agent center, that's the equivalent of 30–60 FTE-days of training recovered per hiring class.

---

### Section 3b: Email Case & Copilot (~10 min) 📧

> 📋 **YOU MUST SEND THIS EMAIL before this section. It creates the case.**

#### Step 1: Send the email

Open Outlook (Tab 4). Send the pre-drafted email to the queue:

---

> 📋 **COPY — Email Address (To field)**
>
> ```
> customerservice@D365DemoTSCE30330346.onmicrosoft.com
> ```

---

> 📋 **COPY — Email Subject**
>
> ```
> PO #91447 — Wrong flush valve models shipped
> ```

---

> 📋 **COPY — Email Body**
>
> ```
> Hi Zurn Team,
>
> We received shipment for PO #91447 today at our Houston distribution center and the contents don't match our order. We ordered 48 units of the Zurn AquaVantage AV flush valve (P/N Z6000-AV) but received 48 units of the Z6000-WS1 instead.
>
> We have a contractor job starting Monday that depends on these valves. Can you please expedite the correct product and provide a return label for the wrong shipment?
>
> Order details:
> - PO #91447
> - Ship-to: Ferguson Houston DC, 4200 Gulf Freeway, Houston TX 77023
> - Original order date: 02/24/2026
> - Qty: 48 ea Z6000-AV AquaVantage flush valves
>
> Please advise on next steps ASAP.
>
> Thanks,
> Mike Reynolds
> Ferguson Enterprises — Commercial Division
> Phone: (713) 555-0184
> ```

---

#### Step 2: Narrate while waiting

Switch back to D365 (Tab 1).

**Say**: "I just sent an email from Mike at Ferguson about a shipment issue. In the current world, someone would manually create a case, copy-paste details, search for the customer record, and try to figure out context from the email chain. Let's see what happens here."

> ⚠️ **Server-side sync takes 1-2 minutes.** Keep talking about the pain. If it doesn't appear within 2 min, open a pre-existing email case: "Here's one that came in earlier through the same process."

#### Step 3: Open the new case

Once the case appears in your queue / active cases:

1. Click the **case title** in the grid → opens as a new session tab
2. Point to: Customer field (auto-matched to Ferguson), Case Origin (Email), Priority, Tier Level
3. Scroll to **Timeline** — the email appears as the first entry

#### Step 4: Copilot

**Click** Copilot pane → "Summarize this case"

**Say**: "Copilot reads the entire email thread and gives me a summary — customer received wrong product, needs correct shipment expedited, wants a return label. As Bill, I don't have to read through a long email thread to understand what Mike needs."

**Click** → "Draft a response"

**Say**: "And it drafts a response for me that I can review and send. No blank screen, no starting from scratch."

> **Differentiator**: "In Service Cloud, Copilot is a paid add-on. Here it's included, and it works across email, chat, and phone — same AI, same context, every channel."

> 💰 **ROI — AI-Assisted Handle Time**: Copilot summarization, smart-draft, and suggested actions reduce AHT 10–25%. For a 200-agent contact center at $75K loaded cost, even a 10% AHT improvement reclaims ~20 FTE-equivalent capacity — roughly $1.5M/yr in absorbed volume growth without adding headcount. And unlike Einstein for Service, Copilot is included in the D365 license.

---

### Section 3c: Timeline & Customer 360 (~5 min)

**Use**: The Ferguson PO #94820 case (navigate: Cases → search "Ferguson PO")

**Timeline should show** (from provisioning):
- Internal note: "Prior discussion with Rachel Chen re: PO #94820" (scope reduction warning)
- Phone call: "Mike Reynolds - PO #94820 delivery timeline check" (March 3, 7 min)
- Email: "RE: PO #94820 - Q1 Hydration Products Order Confirmation" (Rachel's Feb 20 confirmation)
- **Warehouse note**: "PO #94820 warehouse status" — EZH2O staged, **fountains/sinks backordered**

> 🎯 **DEMO GOLD**: The warehouse note says fountains and sinks were backordered with ETA March 12. When Mike asks to cancel those lines, the agent sees they were backordered anyway — **cancelling them actually helps fulfillment**. This is the "aha" moment.

**Then click into the Ferguson account**:
- Revenue $27.8B, 36K employees, Tier 1
- 3 open sales orders visible in related records
- Multiple contacts (Tom, Rachel, Mike)
- Case history: previous resolved/active cases

**Say**: "As Bill, I see everything about Ferguson in one place. Sales and Service share the same data. No integration to build. When Mike calls me next, I already know his order history, who else at Ferguson has been in touch, and what's happening in the warehouse."

> 💰 **ROI — First Contact Resolution**: When agents see the full picture — sales orders, contacts, prior cases, warehouse notes — in one view, FCR improves 15–25%. Each repeat contact costs $5–12 to handle. For organizations handling 500K+ cases/yr, a 10% FCR improvement eliminates ~50K repeat contacts — $250K–600K/yr in avoided cost, plus measurable CSAT improvement.

---

### Section 3d: Knowledge in the Flow of Work (~5 min)

**Navigate**: From any case → Copilot pane or KB search tab

**KB articles likely to surface**:
- "Order Modification Process"
- "Backflow Preventer Installation Guide"
- "EZH2O Bottle Filling Station Troubleshooting"
- "Warranty Claim Procedures"

**Say**: "While I'm working a case, Copilot can search our knowledge base. We have 30 articles — product guides, troubleshooting, SOPs. But the real magic happens during the phone call, when the system surfaces articles automatically based on what the customer is saying. Let me show you."

> ⚠️ **DO NOT** read article titles to the audience or demo the KB admin. Save that for a deep dive.

---

### Section 3e: Teams Embedded Chat (~3 min)

**Navigate**: From any case form → Teams panel (right side or tab)

**Say**: "If I need to pull in an engineer or a warehouse lead, I don't leave D365. Teams is embedded right here — I can start a chat, and the case context auto-populates. Anything important gets captured back to the case timeline."

> **Differentiator**: "No third-party plugin. No copy-pasting case numbers into Slack or Teams. It's built in."

---

### Section 3f: PHONE CALL — THE MAIN EVENT (~10-15 min) 📞

> ⚠️ **THIS IS THE HERO DEMO. Telephony is non-negotiable. Go all-in.**

#### Setup

1. Have the Ferguson PO #94820 case visible in your session
2. Second phone ready with the voice channel number
3. Copilot pane visible on right side

---

#### Phase 1: Ring & Screen Pop (0:00 – 0:30)

**Action**: Dial the voice channel number from your second phone.

**On screen**: Incoming call banner → Accept → Screen pop shows:
- Ferguson Enterprises, Mike Reynolds, **Tier 1 Strategic (red)**
- $27.8B revenue, 36K employees
- Recent cases and open orders visible

**Say**: "Notice the system immediately identifies Mike and shows the full customer context — Ferguson, Tier 1, our biggest customer. No 'Can I get your account number?' needed. As Bill, I already know who's calling and why."

---

#### Phase 2: Greeting (0:30 – 1:00)

> 📋 **SPEAK AS MIKE (second phone):**
>
> *"Hi, this is Mike Reynolds from Ferguson, calling from our Houston distribution center. I'm calling about PO number 94820 — the hydration products order we placed for Q1."*

**On screen**: Real-time transcript appearing, Copilot processing.

**Say to audience**: "The real-time transcript captures everything. Copilot is already analyzing context. As Bill, I can see the transcript updating live and the system connecting Mike's words to his account."

---

#### Phase 3: Cancellation Request (1:00 – 2:00)

> 📋 **SPEAK AS MIKE:**
>
> *"The Fort Worth school district project just reduced their scope. We need to cancel two of the five line items — the floor mount drinking fountains, that was 25 units of the EK-DF model — and also cancel the 40 stainless steel sinks. Those two lines are no longer needed."*

**On screen**: Transcript updating, Copilot may suggest "Order Modification Process" KB article.

> 🎯 **INTENT AGENT MOMENT #1**: Watch for the **SOP: Processing Order Quantity Changes** article to surface in the Copilot pane. Don't announce it immediately — let it appear, then pause and say:
>
> "See what just happened? Mike said 'cancel two line items' and the system surfaced a step-by-step procedure. Bill didn't search for anything — the system understood the intent and delivered the playbook."

**Say**: "And look at the timeline. There's a note from March 3 where Mike warned this might happen. And the warehouse note shows those two items were on backorder anyway — **cancelling them actually helps our fulfillment**. As Bill, I have all the context without asking."

> 🎯 **KEY MOMENT**: Warehouse note says fountains and sinks were backordered with ETA March 12. Cancelling avoids the backorder entirely. This is the "unified timeline" win.

---

#### Phase 4: Expedite Request (2:00 – 3:00)

> 📋 **SPEAK AS MIKE:**
>
> *"But here's the thing — the remaining three lines, the bottle filling stations, the wall mount coolers, and the replacement filters — we actually need those sooner. Can you move the delivery up from March 15 to March 10? Our FM contractor is starting the national rollout early."*

> 🎯 **INTENT AGENT MOMENT #2**: Watch for the **SOP: Expediting Urgent Orders** article to surface. Say:
>
> "Notice it switched — different request, different procedure. It's not matching on one keyword. It's tracking the conversation as it evolves and adapting what it recommends."

**Say**: "Bill can see from the warehouse note that EZH2O units (120) and coolers (60) are already staged and ready to ship. Filters ship from Erie. The expedite is feasible."

---

#### Phase 5: Discount Question (3:00 – 3:30)

> 📋 **SPEAK AS MIKE:**
>
> *"One more thing — Rachel Chen mentioned something about a filter discount that was just approved. 15 percent on bulk orders? Can you make sure that's applied to this PO as well?"*

**Say**: "Bill doesn't have to go hunting for this. The discount approval is right there in the customer's history. Rachel negotiated 15% on filter orders over 500 units. This order has 200 filters — so Bill knows to check whether Mike wants to increase the quantity to qualify."

> 💡 **Smart demo tip**: This creates a natural follow-up point. Bill adds value by proactively flagging that 200 units is below the 500-unit threshold.

---

#### Phase 6: Wrap-Up (3:30 – 4:30)

> 📋 **SPEAK AS MIKE:**
>
> *"That's everything. Can you send me a confirmation email once the changes are processed? My email is mike.reynolds@ferguson.com."*

> 💰 **ROI — Telephony Consolidation**: The native voice channel replaces Genesys entirely — license, integration, and admin overhead. A typical enterprise Genesys contract runs $500K–2M/yr depending on agent count. That's license cost eliminated + integration maintenance retired + one fewer vendor to manage, contract to negotiate, and upgrade cycle to plan for.

**Bill's actions**:
- Update case notes with modification details
- End the call

**After hangup** (💰 the money shot):
- Copilot auto-summarizes the call
- Summary includes: lines to cancel, expedite request, discount inquiry
- Copilot drafts a confirmation email to Mike

**Say**: "After the call ends, Copilot generates a summary from the transcript and drafts the confirmation email. Bill just reviews and sends. No manual note-taking — what used to take 5-10 minutes takes seconds."

> 💰 **ROI — After-Call Work Elimination**: Auto-summarization eliminates 60–90 seconds of manual wrap-up per interaction. At 200 agents × 30 calls/day × 75 seconds saved = **6,250 hours/year** of agent capacity returned to customer-facing work — roughly 3 FTE worth of productive time recovered.

---

#### Fallbacks

**If voice channel is not working**: Open the case directly, walk through the screen layout, show the timeline, explain the screen pop, show Copilot pane with KB suggestions. Still effective, just less dramatic.

**If Copilot is slow**: Continue naturally, show transcript manually, point where suggestions would appear. "In a live environment, Copilot responds in real time."

---

### Section 3g: Chat / Digital Messaging (~8-10 min) 💬

> Full chat script: See [chat-demo-script.md](chat-demo-script.md)  
> Bot setup: See [copilot-studio-setup.md](copilot-studio-setup.md)

---

#### Chat Scenario — Ferguson (Tier 1 Strategic — same hero account as phone)

| Field | Value |
|-------|-------|
| Account | Ferguson Enterprises |
| Account ID | `9b1e5a20-8d12-f111-8406-7ced8dceb26a` |
| Tier | 1 (red) |
| Chatter | Rachel Chen — Purchasing Director |
| Case ID | `b078bc55-bd18-f111-8342-7c1e52143136` |
| Issue | 50 WaterSentry Plus filters from batch WS-2026-0217 failing at ~1200 gal (rated 3000) |
| Root Cause | Carbon media loading variance at Erie plant |
| Resolution | RMA approved, replacements from verified batch WS-2026-0303 |
| Cross-ref | PO #94820 from phone scenario (200 filters — batch verified good) |

**Setup**: Fresh InPrivate / Incognito window → portal login

> 📋 **PORTAL LOGIN**
>
> URL: `https://zurnelkaycustomercare.powerappsportals.com`  
> Username: `rachel.chen`  
> Password: `ZeDemo!2026`

**Say**: "Now we move to the digital channel. Rachel Chen is Purchasing Director at Ferguson — the same Tier 1 Strategic account we saw in the phone scenario, but a different contact and a different issue. She's on the self-service portal."

**Steps**:
1. Log into portal as Rachel Chen
2. Click chat widget (bottom-right bubble)
3. Bot greets customer — Ferguson is identified from authenticated session

> 📋 **TYPE AS RACHEL:**
>
> *"I need to initiate a warranty claim for defective WaterSentry Plus filters. Batch number WS-2026-0217. 50 units."*

4. Bot surfaces "Zurn Warranty Policy and RMA Process" KB article

> 📋 **TYPE AS RACHEL:**
>
> *"Yes, please connect me. I also need to know if this batch was shipped to any of our other locations. These filters are failing at around 1200 gallons — less than half their rated capacity."*

5. Bot escalates to live agent
6. **Switch to CS Workspace** — accept incoming chat as Bill
7. Show: Ferguson Enterprises account, **Tier 1 red badge**, Rachel Chen contact, **full bot transcript**
8. Open case → show timeline (Rachel's defect report email, quality team batch investigation, warranty verification note)
9. Agent sees: defect confirmed by quality team, 200 units shipped to 3 distributors (Ferguson 50, Hajoca 80, Pacific Plumbing 70), Tier 1 = 48-hour priority RMA

**Say**: "Look at the treatment difference. Ferguson is Tier 1 Strategic — red badge, priority routing. I get the complete bot conversation history, Rachel's account, her contact details. No 'can you repeat what you told the bot?' The quality team has already confirmed the batch defect — it's right here on the timeline."

10. Agent resolves: RMA pre-approved, replacements from batch WS-2026-0303, proactive recall to Hajoca + Pacific Plumbing

> 📋 **TYPE AS RACHEL (cross-channel moment):**
>
> *"I also want to flag — we have a pending order, PO #94820, for 200 WaterSentry Plus filters arriving soon. Can you verify those are from a good batch?"*

11. **Cross-channel continuity**: Agent sees PO #94820 from Mike Reynolds' phone call on the same account → confirms batch WS-2026-0303 (verified good)
12. Wrap up: Copilot summarizes chat (including bot portion), drafts RMA confirmation email with batch verification

**Say**: "Here's the power of unified data. Mike Reynolds called about PO #94820 on the phone — different person, different channel, same account. Rachel is asking about it via chat. Because everything lives on one platform, I see the complete picture. And Copilot auto-summarizes the entire interaction — including the bot triage — and drafts the follow-up email."

> 💰 **ROI — Unified Omnichannel**: Same routing engine, same workspace, same AI across every channel. No separate bot platform license, no integration between chat vendor and CRM. Self-service bot deflection alone typically handles 20–40% of inquiries without agent involvement — at $0 marginal cost per deflected interaction. And cross-channel context (phone ↔ chat ↔ email) eliminates the "can you repeat what you told the bot?" tax that adds 2–3 minutes to every escalated conversation.

---

#### Fallback: If Bot Is Not Ready

Open portal chat directly (without bot — goes to agent queue). Walk through the agent experience receiving the chat. Reference the bot architecture from [copilot-studio-setup.md](copilot-studio-setup.md).

---

### Section 3h: Tiered Routing & Skills (~5 min)

**Navigate**: From any case → hover over Tier Level pill → show routing outcome

**Key data**:
- 4 tiers: Tier 1 (red/Strategic), Tier 2 (orange/Premium), Tier 3 (blue/Standard), Tier 4 (gray/Basic)
- Hot words: **Urgent, Emergency, Recall, Safety, Legal, Next Day Air** → boost priority to 10,000
- 18 queues (brand × channel × tier)
- Skills-based routing active

> ⚠️ **DO NOT open Admin Center.** Show the outcomes on cases only. Save config for tech deep dive.

**Say**: "Notice the color coding — Tier 1 gets the red badge and routes to our senior team. If Mike's email had said 'EMERGENCY,' the system would have boosted priority to 10,000 and routed it to the escalation queue. Six hot words trigger this — Urgent, Emergency, Recall, Safety, Legal, Next Day Air."

---

### Section 3i: Guided Process Flows (~5 min)

> **Status**: ✅ Built and registered. Order Modification Wizard is live in the D365 productivity pane.

**Architecture**: Power Apps Custom Page embedded in the D365 productivity pane as a side-panel tool — the D365 equivalent of Salesforce's Lightning Flow for Service.

**4-Screen Wizard**:
1. **Order Lookup** — Gallery of customer's active orders (auto-filters to account)
2. **Line Management** — Cancel checkboxes + delivery date pickers per line
3. **Review & Confirm** — Change summary with red strikethrough on cancellations, credit total
4. **Confirmation** — Success + "Add to Case Timeline" + "Draft Confirmation Email"

**Demo flow** (during or referencing the phone call with Mike):
- Bill opens the Order Modification tool in the productivity pane
- Selects PO #94820 → sees 5 line items
- Checks "cancel" on Line 4 (drinking fountains, $36,250) and Line 5 (sinks, $31,200)
- Changes delivery to March 10 for remaining 3 lines
- Reviews: "Cancelling 2 lines = -$67,450" → Submits
- Adds note to case timeline, drafts confirmation email

**Say**: "This is exactly what your team does today in Salesforce Screen Flows — same guided wizard, same side panel position, but built natively on Power Platform with direct Dataverse access. No Apex code, no deployment pipelines."

---

### Section 3j: Proactive Notifications (~3 min)

**Navigate**: Show in-app notification (if active), SLA warning toast, supervisor dashboard.

No special data needed — general platform capability.

**Say**: "The system doesn't wait for problems. SLA warnings, backorder alerts, batch defect notifications — all push to the right people automatically."

**Transition**: "You've seen Bill's world — the associate experience. Now let's switch to Sarah Kim's view. Sarah is the care leader. Let's see what she lives in every day."

---

### Section 4a: Real-Time Dashboards

**Navigate**: CS Workspace → left nav → **Omnichannel real-time analytics** (under Service)

**Say**: "Sarah, here's your world. Today you're pulling reports from Salesforce for cases, a separate report from Genesys for telephony data, and spreadsheets for SLA tracking. Three systems to answer one question: how is my team doing right now? Here it's one screen, real-time, no assembly required."

**Show** (point to each):
1. **Active conversations by channel** — email, phone, chat breakdown
2. **Agent availability grid** — who's available, busy, away, offline
3. **Queue wait times** — per queue
4. **SLA compliance rate**
5. **Conversation status breakdown** — active, waiting, wrap-up

**Say**: "In Service Cloud, you'd need a custom dashboard, Genesys data via integration, and hope timestamps align. Here the telephony, case, and routing data are all one system — numbers are always right."

> 💡 If dashboard looks sparse: "In production with your full team, this lights up. Right now we're seeing demo data, but the structure is exactly what you'd see at scale."

---

### Section 4b: Agent Performance Metrics

**Navigate**: From real-time dashboard → **Agent** tab or **Omnichannel historical analytics** → **Agent**

**Say**: "Benton, you asked about performance metrics — handle time, wait time, call duration. All captured natively because phone, email, and chat all run through one platform. No reconciling Genesys talk time with Salesforce case metrics in Excel."

**Show**:
- Average handle time by agent/channel
- Average wait time
- Conversations handled per agent
- Active vs. idle time
- Transfer rate

**Say** (supervisor workflow): "Sarah does her morning routine: pulls up this view, sees who handled the most cases yesterday, who had the longest handle times, who transferred the most. That's her coaching conversation for the day — data-driven, not anecdotal."

**Say** (convergence): "The key is convergence. Every interaction — phone, email, chat — flows through the same system. The numbers are real-time and trustworthy."

> 💰 **ROI — Supervisor Efficiency**: One real-time dashboard replaces 3 separate reporting tools (Genesys Supervisor, Salesforce dashboards, WFM reports). Supervisors save 30–60 minutes/day that was spent switching between systems, exporting data, and reconciling numbers. For 20 supervisors, that recovers 10–20K hours/year of management capacity — time spent coaching agents instead of chasing reports.

---

### Section 4c: Workforce Management

**Navigate**: CS Admin Center → Workforce Management → Schedule Management

**Say**: "Sarah also manages scheduling. WFM is built into the platform — not a third-party bolt-on."

> **All WFM features enabled**: Forecast, Capacity planning, Schedule management, Shift-based routing, Calendar, Bidding, Swapping.

**Show navigation** → walk through the shift plans:

| Shift Plan | Hours (CT) | Days | Staff |
|---|---|---|---|
| Morning | 6:00 AM – 2:00 PM | Mon-Fri | 4 |
| Day | 8:00 AM – 5:00 PM | Mon-Fri | 6 |
| Afternoon | 2:00 PM – 10:00 PM | Mon-Fri | 3 |
| Staggered | 7:00 AM – 3:00 PM | Mon-Fri | 2 |
| Weekend | 8:00 AM – 2:00 PM | Sat-Sun | 2 |

> 14 agents across 5 shift plans. Tyler Stein and Riley Ramirez cover both Staggered (weekdays) and Weekend shifts.

**Activity types**: Case Work, Break (15 min), Lunch (60 min), Training (60 min), Team Meeting (30 min), Coaching (30 min)

**Time off requests** (show these):

| Agent | Type | When |
|---|---|---|
| Renee Lo | Vacation | 5 days out (4-day PTO) |
| Markus Long | Training | 3 days out (1-day) |
| Alan Steiner | Personal | 7 days out (1-day) |
| Enrico Cattaneo | Sick Leave | Yesterday – today |
| David So | Vacation | 12 days out (5-day) |

**Key talking points**:
- "The schedule IS the routing configuration. If Renee is on PTO, she doesn't get cases. Period."
- "Agents can bid on open shifts and request swaps directly in the platform."
- "Non-assignable activities (training, meetings, coaching) automatically remove agents from routing."
- vs. Salesforce: "With Service Cloud, WFM requires Workforce Engagement or third-party. Here it's native."

> 💰 **ROI — WFM Consolidation**: Built-in WFM replaces Verint, NICE, or Calabrio contracts typically running $50–150K/yr. Beyond license savings, eliminating the data sync between a third-party WFM tool and CRM removes a constant source of forecast inaccuracy — overstaffing costs money, understaffing costs customers.

---

### Section 4d: Quality Management

> ✅ Fully configured and LIVE. 6 criteria sections, 21 AI-scored questions, 2 evaluation plans.

**Say**: "The last piece of Sarah's toolkit is Quality Management. This is where she scores agent interactions against evaluation criteria — the QA process, built into the platform."

**Navigate**: CS Admin Center → Quality Management → Evaluation criteria → click **Manufacturing Service Quality Standard**

**Walk through sections** (scroll, don't read every question):

| Section | Weight | Questions | Key Point |
|---------|--------|-----------|-----------|
| Customer Identification & Account Handling | 15% | 3 | "Did Bill verify identity and recognize the tier?" |
| Technical Accuracy & Product Knowledge | 25% | 4 | "Heaviest weight — correct specs, right parts" |
| Process Compliance & Escalation Handling | 20% | 4 | "Hot word detection — did Bill escalate properly?" |
| Resolution Effectiveness | 20% | 4 | "Resolved on first contact? Documentation thorough?" |
| Communication & Professionalism | 10% | 3 | "Tone, clarity, expectations" |
| Tool Adoption & Efficiency | 10% | 3 | "Did Bill use Copilot, KB, and AI tools?" |

**Say**: "Every question has AI-response enabled. The Quality Management Agent reads Bill's conversation transcript and case notes, then scores each question automatically. Sarah only reviews the flagged ones."

**Navigate**: Quality Management → Evaluation plans:

| Plan | Type | Scope |
|------|------|-------|
| Daily Case Quality Review | Recurring (daily) | Cases — evaluates all resolved cases each day |
| Conversation Quality Review | Trigger (on close) | Conversations — evaluates every closed chat/voice interaction |

**Say**: "Two approaches: manual evaluation — Sarah picks a conversation and scores it. Or the Quality Management Agent — AI that automatically scores every interaction and flags the ones that need review. Instead of randomly sampling 5% of calls, the system tells Sarah which conversations deserve attention."

**Say** (connect to their world): "Lisa, think about your QA process today. How many calls does your team review per week? How do you decide which ones? With the QM Agent, every interaction gets evaluated, and Sarah's time goes to the conversations that actually need coaching."

> **Differentiator**: "With Salesforce, quality management requires Einstein Conversation Insights + a third-party QA tool. Here it's native."

> 💰 **ROI — QM Coverage Expansion**: Traditional QM samples 3–5% of interactions — problems are found after a pattern emerges, often after customer damage is done. Built-in AI-powered QM evaluates 100% of interactions and flags the ones that need human review. That's the difference between reactive QA that catches trends quarterly and real-time quality assurance that catches issues the same day. Reduces customer churn from undetected service failures and turns QA from a cost center into a coaching accelerator.

---

### Section 5: AI Agents (~10 min)

**Three agents to reference** (show outcomes, not config):
1. **Intent Agent** — already demonstrated during the phone call and chat
2. **Case Management Agent** — auto-follow-up on stale cases
3. **Knowledge Management Agent** — identifies KB gaps, drafts articles

**Narrative approach — refer back to the story**:

**Say**: "Remember when Mike said he needed to modify the order and the procedure appeared? That's the Intent Agent. It recognized the service intent — not just a keyword match, but what Mike actually needed — and delivered the right runbook to Bill."

**Say**: "We've configured it for your top 10 service scenarios — the calls and chats your team handles every day: order changes, expedites, defect reports, quality holds, invoice disputes."

**Say**: "A new hire on day one gets the same procedural guidance that your 20-year veteran carries in their head. The system levels the playing field."

**For Case Management Agent**: "This one watches Bill's queue. If a case sits for 48 hours waiting on a customer reply, it sends a follow-up. If a new case matches a pattern seen 50 times before, it suggests the resolution."

**For Knowledge Management Agent**: "This agent watches for patterns. 15 cases about the same issue and no article? It drafts one and sends it for review. This is how you build that internal KB automatically — from the cases your team is already resolving."

> 💰 **ROI — Intelligent Automation**: AI agents handle routine inquiries end-to-end — order status, tracking, warranty checks — without human involvement. Typical deflection: 30–50% of Tier 1 volume. For a center handling 100K interactions/month, deflecting 30% means 30K interactions/month routed to automation. The Intent Agent also levels the playing field: a new hire on day one receives the same procedural guidance that a 20-year veteran carries in their head, cutting time-to-competency and reducing escalation rates from inexperienced staff.

> ⚠️ **DO NOT**: List all 10 intents, show admin screens, or mention "2 groups" (that's config language, not customer value).

---

### Section 6: Platform Extensibility & Close

**Say**: "Everything you've seen today — the agent workspace, the phone channel, the bot, the dashboards, WFM, QM — all sits on the Microsoft Power Platform. That means Power Apps for custom screens like the order wizard, Power Automate for business process automation, and a full AppSource marketplace for third-party extensions. Plus code-first options when you need them."

**5 differentiators to land**:
1. **One platform** for Sales + Service (no middleware)
2. **Native telephony** with real-time transcript + AI (replaces Genesys)
3. **Unified omnichannel** (chat, email, phone) with intelligent routing
4. **Copilot everywhere** (summarize, suggest, draft, guide)
5. **WFM + QM built in**, not bolted on

> 💰 **ROI Summary — The Single-Platform Business Case**:
>
> Everything you saw today runs on one platform. Here's what that means in dollars and outcomes:
>
> | Impact Area | Metric | Annual Value Range |
> |---|---|---|
> | **Genesys replacement** | Eliminate telephony vendor license + integration | $500K–2M |
> | **WFM consolidation** | Replace Verint/NICE/Calabrio | $50–150K |
> | **QM coverage** | 100% AI-scored vs. 3–5% manual sampling | Quality-driven CSAT lift |
> | **Copilot AHT reduction** | 10–25% handle time improvement | ~$1.5M (200-agent equivalent) |
> | **After-call work** | Auto-summarization saves 60–90s per call | 6,250 hrs/yr recovered |
> | **FCR improvement** | 15–25% improvement from unified Customer 360 | $250K–600K avoided repeat contacts |
> | **Integration elimination** | Retire 3–4 middleware connections | $150–600K/yr maintenance saved |
> | **New-hire ramp** | One system vs. 3–4 → 30–50% faster onboarding | Training cost + time-to-productivity |
> | **Supervisor efficiency** | One dashboard replaces three reporting tools | 10–20K supervisor hrs/yr recovered |
> | **Bot deflection** | 20–40% self-service containment | $0 marginal cost per deflection |
>
> **The compounding effect**: These aren't independent line items. A unified platform creates a flywheel — better data drives better AI, better AI drives faster resolution, faster resolution drives higher satisfaction, higher satisfaction drives retention. None of that compounds when the data lives in 4 systems connected by middleware.

**Schedule next**: Tech deep dive, guided actions deep dive, IT/platform session.

---

## Data Appendix

### Intent Agent Reference

| Group | Intents |
|-------|---------|
| **Orders & Logistics** | Change order quantity, Expedite urgent order, Request invoice correction, Track shipment, Update delivery address |
| **Production & Quality** | Provide material spec, Report defective batch, Request process change, Request quality inspection, Schedule production run |

**SOP → Intent Mapping:**

| Intent | SOP Article Surfaced |
|--------|---------------------|
| Change order quantity | SOP: Processing Order Quantity Changes |
| Expedite urgent order | SOP: Expediting Urgent Orders |
| Request invoice correction | SOP: Handling Invoice Correction Requests |
| Track shipment | SOP: Tracking Shipments and Handling Delivery Exceptions |
| Update delivery address | SOP: Updating Delivery Address on Orders |
| Provide material spec | SOP: Providing Product Material Specifications |
| Report defective batch | SOP: Defective Batch Reporting and Quality Hold Process |
| Request process change | SOP: Processing Change Requests |
| Request quality inspection | SOP: Quality Inspection Requests and Procedures |
| Schedule production run | SOP: Scheduling and Managing Production Runs |

---

### All Accounts (19 total)

**Manufacturers (2)**:

| Account | Type |
|---------|------|
| Zurn Industries LLC | Manufacturer |
| Elkay Manufacturing Company | Manufacturer |

**Distributors (13)**:

| Account | Tier | Revenue |
|---------|------|---------|
| **Ferguson Enterprises** | 1 — Strategic | $27.8B |
| HD Supply | 2 — Premium | $8.5B |
| Hajoca Corporation | 2 — Premium | $4.3B |
| Winsupply Inc | 2 — Premium | $6.5B |
| Johnstone Supply | 3 — Standard | $3.6B |
| F.W. Webb Company | 3 — Standard | $2.8B |
| Pacific Plumbing Supply | 3 — Standard | $1.2B |
| R.E. Michel Company | 3 — Standard | $1.5B |
| Wolseley Canada | 2 — Premium | $3.2B |
| Gateway Supply Co | 4 — Basic | $450M |
| Kaman Industrial Tech | 4 — Basic | $1.8B |
| Dakota Supply Group | 3 — Standard | $890M |
| Thermal Equipment Corp | 4 — Basic | $320M |

**End Users (4)**: Fort Worth ISD, Memorial Hermann Health, Hilton Hotels Corp, Denver International Airport

---

### All Products (16)

| SKU | Product | Brand | Price |
|-----|---------|-------|-------|
| ZN-AV-1001 | AquaVantage Flush Valve | Zurn | $285 |
| ZN-UR-1003 | Urinal Flush Valve | Zurn | $195 |
| ZN-BF-2001 | Wilkins 975XL Backflow | Zurn | $1,250 |
| ZN-HY-3001 | Hydrant Repair Kit | Zurn | $165 |
| ZN-SC-4001 | Sensor Faucet Commercial | Zurn | $425 |
| ZN-DC-4002 | Deck Mount Sensor Faucet | Zurn | $385 |
| ZN-FD-4003 | Floor Drain 12" | Zurn | $95 |
| ZN-RK-9001 | Repair Kit Master | Zurn | $45 |
| EK-BF-5001 | EZH2O Bottle Filling Station | Elkay | $1,150 |
| EK-WC-5002 | Wall Mount Cooler Bi-Level ADA | Elkay | $780 |
| EK-DF-5003 | Floor Mount Drinking Fountain ADA | Elkay | $1,450 |
| EK-SS-6001 | Stainless Steel Sink Commercial | Elkay | $780 |
| EK-FL-6003 | WaterSentry Plus Filter | Elkay | $29.50 |
| EK-SW-6002 | Swirl Flo Aerator | Elkay | $45 |
| EK-CL-6004 | CoolerSentry Filter System | Elkay | $85 |
| EK-UV-6005 | UV Lamp Replacement Kit | Elkay | $120 |

---

### All Orders (10)

| Order | Customer | Total | Status | Note |
|-------|----------|-------|--------|------|
| **PO-94820** | Ferguson | $258,150 | Active | **DEMO ORDER** — cancel 2 lines, expedite 3 |
| PO-93201 | Ferguson | $108,125 | Active | Zurn Backflow Q4 (delivered) |
| PO-95102 | Ferguson | $94,550 | Active | Flush Valves replenishment |
| PO-HD-7845 | HD Supply | $53,450 | Active | Sensor products |
| 6 aftermarket parts orders | Various | $2,350–$8,750 each | Active | Context orders |

**Orders with tracking**:

| Order | Tracking # | Carrier |
|-------|-----------|---------|
| PO-94820 | 1Z999AA10123456784 | UPS |
| PO-93201 | 7891-2345-6789 | FedEx |
| PO-95102 | 1Z999AA10987654321 | UPS |
| PO-HD-7845 | 7891-9876-5432 | FedEx |

---

### All Queues (18)

Brand × Channel × Tier pattern: `Zurn Email Tier 1`, `Zurn Phone Tier 1`, `Elkay Email Tier 1`, etc. across all 4 tiers + general queues.

---

### All Entitlements (13)

| Tier | Count | Accounts |
|------|-------|----------|
| Tier 1 — Strategic | 4 | Ferguson, HD Supply, Hajoca, Winsupply |
| Tier 2 — Premium | 4 | Wolseley, Johnstone, F.W. Webb, R.E. Michel |
| Tier 3 — Standard | 3 | Pacific Plumbing, Dakota Supply, Kaman |
| Tier 4 — Basic | 2 | Gateway Supply, Thermal Equipment |

SLA ID: `f8c8c488...` (4hr first response, 8hr resolution, M-F 8am-5pm)

---

### Serial Numbers & Warranty

| Serial Number | Product | Status | Warranty End |
|---------------|---------|--------|-------------|
| `234567ABC` | AquaVantage Flush Valve | **ACTIVE** | 2028-01-10 |
| `123456ABC` | EZH2O Bottle Filling Station | **ACTIVE** | 2027-06-15 |
| `ZRN-2024-10583` | Wilkins 975XL Backflow | **ACTIVE** | 2029-03-20 |
| `ZRN-2025-20091` | Sensor Faucet Commercial | **ACTIVE** | 2030-01-05 |
| `ZRN-2025-30044` | Hydrant Repair Kit | **ACTIVE** | 2029-11-15 |
| `ELK-2021-08832` | Wall Mount Cooler | **EXPIRED** | 2024-08-15 |
| `ELK-2023-00471` | Floor Mount Drinking Fountain | **EXPIRED** | 2025-12-01 |

---

### WFM Data Summary

**5 shift plans**, **14 agents**, **1,196 total bookings**, **6 activity types**, **5 time-off requests**, **7 time-off types**

---

### QM Data Summary

**Manufacturing Service Quality Standard**: 6 sections, 21 questions, 100% total weight

**Evaluation plans**: Daily Case Quality Review (recurring) + Conversation Quality Review (trigger on close)

---

### Key Numbers

| Metric | Value |
|--------|-------|
| Total accounts | 19 (2 mfg + 13 dist + 4 end users) |
| Total cases | ~40 across tiers and channels |
| KB articles | 30 (20 product/case + 10 SOP runbooks) |
| Queues | 18 (brand × channel × tier) |
| Entitlements | 13 (4 tiers) |
| Products | ~30 (Zurn + Elkay + Wilkins) |
| Hot words | 6 (Urgent, Emergency, Recall, Safety, Legal, Next Day Air) |
| SLA: First response | 4 business hours |
| SLA: Resolution | 8 business hours |

---

### Environment URLs

| Resource | URL |
|----------|-----|
| CS Workspace | https://orgecbce8ef.crm.dynamics.com |
| Portal | https://zurnelkaycustomercare.powerappsportals.com |
| Admin Center | https://orgecbce8ef.crm.dynamics.com (Settings → Advanced) |
| Fabric Workspace | App ID: `4ea7cd33-e2fd-480d-8ae7-c72c6a94a410` |
