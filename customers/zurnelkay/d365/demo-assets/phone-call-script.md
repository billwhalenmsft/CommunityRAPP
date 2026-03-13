# Phone Call Demo Script -- Ferguson Order Modification

## Overview
**Scenario**: Mike Reynolds from Ferguson Enterprises (Houston DC) calls about PO #94820.
He needs to cancel 2 of 5 line items and expedite the remaining 3.

**Duration**: ~5 minutes

**Purpose**: Show inbound voice, screen pop, real-time transcript, Copilot assist, and case management.

---

## Pre-Demo Setup

### Environment Check
- [ ] Logged into CS Workspace as the agent
- [ ] "My Active Cases" view open -- Ferguson order mod case visible
- [ ] Voice channel connected (green status indicator)
- [ ] Copilot pane visible (right side)
- [ ] Browser at: https://orgecbce8ef.crm.dynamics.com

### Second Line Ready
- [ ] Use a cell phone or Teams on a second device
- [ ] Dial the voice channel number (check Omnichannel admin for the number)
- [ ] Have this script handy on the second device

---

## The Call

### 1. Call Arrives (0:00 - 0:30)

**What happens on screen:**
- Incoming call notification appears (banner or toast)
- Agent accepts the call
- **Screen pop** shows:
  - Customer: **Ferguson Enterprises** (auto-identified from phone number)
  - Contact: **Mike Reynolds** -- Field Operations Manager
  - **Tier 1 Strategic** badge (red pill)
  - Account details: $27.8B revenue, 36,000 employees, 450+ branches
  - Recent cases list (4-5 cases visible)
  - Open orders visible in related records

**Talking point**: "Notice how the system immediately identifies the caller and shows the full customer context -- no 'Can I get your account number?' needed."

### 2. Greeting (0:30 - 1:00)

**As Mike (on second phone), say:**

> "Hi, this is Mike Reynolds from Ferguson, calling from our Houston distribution center. I'm calling about PO number 94820 -- the hydration products order we placed for Q1."

**What agent sees:**
- Real-time transcript appears in the left panel
- Copilot starts processing the conversation
- The PO number "94820" triggers recognition

**Talking point**: "The real-time transcript is capturing everything Mike says. Copilot is already analyzing the context."

### 3. The Modification Request (1:00 - 2:00)

**As Mike, continue:**

> "The Fort Worth school district project just reduced their scope. We need to cancel two of the five line items -- the floor mount drinking fountains, that was 25 units of the EK-DF model -- and also cancel the 40 stainless steel sinks. Those two lines are no longer needed."

**What agent sees:**
- Transcript updating in real time
- Copilot may suggest the **"Order Modification Process"** KB article
- If Copilot assistant is enabled, it may flag the order and products mentioned

**Agent action**: Open the existing case "Ferguson PO #94820 - Order modification request"

**Talking point**: "Look at the case timeline -- there's a note from March 3 where Mike warned this might happen. And the warehouse note shows those two items were on backorder anyway -- cancelling them actually helps our fulfillment."

### 4. The Expedite Request (2:00 - 3:00)

**As Mike, continue:**

> "But here's the thing -- the remaining three lines, the bottle filling stations, the wall mount coolers, and the replacement filters -- we actually need those sooner. Can you move the delivery up from March 15 to March 10? Our FM contractor is starting the national rollout early."

**What agent sees:**
- Transcript captures the new delivery date
- Copilot may suggest checking warehouse availability
- Agent can reference the warehouse note: "EZH2O units and coolers are staged and ready to ship"

**Talking point**: "The agent can see from the internal notes that the bottle filling stations and coolers are already staged in the warehouse. The filters are shipping from Erie. The expedite is feasible."

### 5. The Discount Question (3:00 - 3:30)

**As Mike, continue:**

> "One more thing -- Rachel Chen mentioned something about a filter discount that was just approved. 15 percent on bulk orders? Can you make sure that's applied to this PO as well?"

**What agent sees:**
- The resolved case "EZH2O filter replacement bulk discount approved" is in Ferguson's case history
- Copilot may surface the discount details

**Talking point**: "The agent doesn't have to go hunting -- the discount approval case is right there in the customer's history. Rachel negotiated 15% on filter orders over 500 units. This order has 200 filters, so the agent knows to check if it qualifies or if Mike needs to increase the quantity."

### 6. Wrap-Up (3:30 - 4:30)

**As Mike:**

> "That's everything. Can you send me a confirmation email once the changes are processed? My email is mike.reynolds@ferguson.com."

**Agent actions:**
- Update the case notes with modification details
- (Optional) Show how to create a follow-up task
- End the call

**What happens after hangup:**
- **Copilot auto-summarizes** the call
- Summary includes: lines to cancel, expedite request, discount inquiry
- Copilot drafts a confirmation email to Mike

**Talking point**: "After the call ends, Copilot automatically generates a summary of the entire conversation and even drafts the confirmation email. The agent just reviews and sends -- no manual note-taking needed."

---

## Key Demo Highlights to Emphasize

| Feature | What to Show | Where |
|---------|-------------|-------|
| Screen Pop | Auto-identify caller, show full context | Call notification |
| Tier 1 Strategic | Red badge, priority routing | Case form header |
| Real-time Transcript | Live speech-to-text | Left panel |
| Copilot Assist | KB suggestions, context awareness | Right panel |
| Case Timeline | Prior calls, notes, emails | Case form |
| Warehouse Intelligence | Internal notes inform agent | Timeline notes |
| Cross-Contact Context | Rachel's discount visible from Mike's call | Case history |
| Auto-Summary | AI-generated call summary | Post-call |
| Draft Email | Copilot writes confirmation | Post-call |

---

## Fallback Notes

**If voice channel is not working:**
- Open the case directly and walk through the screen layout
- Show the timeline, notes, and Copilot pane
- Explain what the screen pop would look like
- Still effective -- just less dramatic

**If Copilot is slow:**
- Continue the conversation naturally
- Show the transcript manually
- Point out where Copilot suggestions would appear
- "In a live environment, Copilot responds in real time"

**If asked about the actual order modification in FNO:**
- "The agent creates the modification request here in Customer Service"
- "The order change flows to Dynamics 365 Finance & Operations via integration"
- "We'll show that guided process flow in the next section of the demo"

---

## Data Reference

| Item | Value |
|------|-------|
| Hero Account | Ferguson Enterprises (Tier 1) |
| Caller | Mike Reynolds, (713) 555-0184 |
| PO Number | #94820 |
| Total Lines | 5 (cancel 2, keep 3) |
| Cancel: Drinking Fountains | EK-DF-5003, 25 units, $36,250 |
| Cancel: Stainless Sinks | EK-SS-6001, 40 units, $31,200 |
| Keep: Bottle Fillers | EK-BF-5001, 120 units, $138,000 |
| Keep: Wall Coolers | EK-WC-5002, 60 units, $46,800 |
| Keep: Filters | EK-FL-6003, 200 units, $5,900 |
| Original Delivery | March 15, 2026 |
| Requested Delivery | March 10, 2026 |
| Filter Discount | 15% on 500+ units (may not apply to 200) |
| Case ID | See data/hero-record-ids.json |
