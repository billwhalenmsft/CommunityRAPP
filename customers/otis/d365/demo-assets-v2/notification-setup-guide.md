# Enriched Voice Call Notification — Setup Guide

**Otis EMEA CCaaS Demo**  
**Goal**: Transform the default voice notification from basic "Incoming conversation" to a rich context pop showing customer name, account, tier level, open cases, and contact info.

---

## Architecture Overview

The D365 CS voice call notification has **two layers of customer context**:

| Layer | When | What Shows | How to Configure |
|-------|------|-----------|-----------------|
| **Notification Pop-up** | Before accept (the toast) | Customer name, Account, Tier, Open Cases, Phone | Notification Template + Context Variables |
| **Customer Summary** | After accept (session opens) | Full 360: contact details, case history, interactions, timeline | Session Template + Customer Summary form |

The screenshot showing only "Comment: Incoming conversation" + "Countdown: 35 sec" is the **default notification template**. We need to replace it with a custom template.

---

## Quick Reference — What Needs to Happen

| # | Task | Method | Script |
|---|------|--------|--------|
| 1 | Create custom notification template | PowerShell script | `Configure-VoiceNotificationTemplate.ps1` |
| 2 | Add Tier Level field to Account | PowerShell script | `Add-AccountTierField.ps1` |
| 3 | Populate demo accounts with tiers | PowerShell script | `Add-AccountTierField.ps1` |
| 4 | Assign template to voice workstream | CS Admin Center (manual) | See Step 4 below |
| 5 | Add Tier Level to Account form | Power Apps maker (manual) | See Step 5 below |
| 6 | Configure Copilot Studio bot for context enrichment | Copilot Studio (manual) | See Step 6 below |
| 7 | Verify phone number matching | CS Admin Center (manual) | See Step 7 below |

---

## Step 1: Run the Notification Template Script

```powershell
cd customers/otis/d365/scripts
.\Configure-VoiceNotificationTemplate.ps1
```

This creates:
- A notification template called **"Otis Voice - Rich Context"** with fields:
  - Customer: `{customerName}` (from phone matching)
  - Account: `{AccountName}` (context variable)
  - Service Tier: `{TierLevel}` (context variable)
  - Open Cases: `{OpenCases}` (context variable)
  - Phone: `{PhoneNumber}` (context variable)
  - Countdown: `{countdown}` (built-in)
- Context variables on the voice workstream: `AccountName`, `TierLevel`, `OpenCases`, `PhoneNumber`

---

## Step 2: Run the Account Tier Field Script

```powershell
.\Add-AccountTierField.ps1
```

This:
- Creates a `cr377_tierlevel` choice field on the Account entity (same values as Case)
- Populates all 10 Otis demo accounts with their correct tier values
- Publishes the Account entity customization

---

## Step 3: Verify Data

After running both scripts, verify:
```powershell
# Check notification template exists
# (The script outputs template ID and field list)

# Check account tier values
# (The script outputs a verification table)
```

---

## Step 4: Assign Notification Template to Voice Workstream (Manual)

1. Open **Customer Service admin center**
   - URL: `https://orgecbce8ef.crm.dynamics.com/main.aspx?apptype=areapane&area-type=administration`
   - Or: Settings gear > Customer Service admin center

2. Navigate to **Workstreams**
   - Left nav: Workstreams (under Customer support)

3. Open your **Voice workstream** (e.g., "Voice" or "Voice - Otis EMEA")

4. Scroll to **Show advanced settings**

5. Under **Notification**, change:
   - **Incoming authenticated**: Select → **"Otis Voice - Rich Context"**
   - **Incoming unauthenticated**: (optionally same template or default)

6. **Save** the workstream

### Verify
- The notification template should now show 6 fields instead of 2
- Fields using context variables ({AccountName}, {TierLevel}, {OpenCases}) will show blank until Step 6 is completed

---

## Step 5: Add Tier Level to Account Form (Manual)

1. Go to **make.powerapps.com** → select your environment

2. Navigate to **Tables** → **Account** → **Forms**

3. Open the **Account** main form (Main type)

4. In the form designer:
   - Find or add the **Tier Level** column
   - Place it in the **Account Information** section (near Category / Industry)
   - Consider making it **read-only** if tier should only be set by admins

5. **Save and Publish** the form

### Why This Matters
- When an agent accepts a voice call, the **Customer Summary** panel shows the matched Account
- If Tier Level is on the Account form, it's visible in the Customer Summary
- This gives agents instant tier awareness even without the notification enrichment

---

## Step 6: Configure Copilot Studio Bot for Context Enrichment (For Dynamic Data)

This is the key step for populating the context variables dynamically. Without this, the notification shows the Customer name (from phone matching) but the custom fields (Account, Tier, Open Cases) appear blank.

### Option A: Copilot Studio Bot (Recommended)

1. **Create a Copilot Studio bot** (or use an existing one)
   - Copilot Studio: https://copilotstudio.microsoft.com

2. **Add a topic** that triggers on conversation start:
   - Trigger: "When a conversation starts"
   - Actions:
     a. Get the caller's phone number from the conversation
     b. Call a **Power Automate flow** that:
        - Queries Dataverse: Contact by phone number → get parent Account
        - Gets Account tier level (`cr377_tierlevel`)
        - Counts active cases for the account (`incidents` where `statecode eq 0`)
        - Returns: AccountName, TierLevel (text), OpenCases (number as string)
     c. Set context variables:
        - `AccountName` = flow output AccountName
        - `TierLevel` = flow output TierLevel (e.g., "Tier 1 - Premium")
        - `OpenCases` = flow output OpenCases (e.g., "3 active")
     d. Transfer to agent queue

3. **Associate the bot with the voice workstream**:
   - CS Admin Center → Workstreams → [Voice] → Bot section
   - Add your Copilot Studio bot as the first responder

### Option B: Power Automate Flow (Alternative)

If you don't want a bot intermediary:

1. Create a **cloud flow** triggered by "When a row is added" on the `msdyn_ocliveworkitem` table
2. The flow:
   - Gets the conversation's customer ID
   - Looks up Account tier and open cases
   - Updates the conversation's context variables via Dataverse API
3. This is trickier because the context variables must be set BEFORE the notification fires

### Option C: Demo Shortcut (Quick & Dirty)

For demo purposes only, you can pre-populate the context variables manually:

1. Skip the bot entirely
2. The notification will show Customer name (from phone matching) + blank custom fields
3. Accept the call → Customer Summary shows the full context
4. Talk through "In production, this data populates automatically from the IVR"

**This is actually fine for most demos** — the Customer Summary after accept shows everything, and the notification shows the customer name.

---

## Step 7: Verify Phone Number Matching

This is critical for `{customerName}` to resolve in the notification.

1. **CS Admin Center** → **Workstreams** → [Voice workstream]

2. Open the workstream → scroll to **Advanced settings**

3. Under **Identify records automatically**:
   - Method: **Pre-conversation survey** or **Use phone number**
   - Entity: **Contact**
   - Match on: **Business Phone** or **Mobile Phone**

4. Ensure your demo contacts have phone numbers set:
   - David Chen: `+1 (555) 867-5309` → Riverside Medical Centre
   - James Morrison: `+1 (555) 234-5678` → Westfield London Shopping Centre
   - Sophie Williams: (check `otis-demo-ids.json` for phone)

5. **Test**: Call the voice channel number from the phone that matches a contact
   - The notification should show the contact's name in the `{customerName}` field

---

## What the Final Notification Should Look Like

### Before (Default — What You Have Now)
```
╔══════════════════════════════════════╗
║  Voice call request from James M... ║
║                                      ║
║  Comment:   Incoming conversation    ║
║  Countdown: 35 sec                   ║
║                                      ║
║  [Accept]  [Reject]                  ║
╚══════════════════════════════════════╝
```

### After (With Rich Context Template)
```
╔══════════════════════════════════════╗
║  Incoming Voice Call — James Morrison║
║                                      ║
║  Customer:     James Morrison        ║
║  Account:      Westfield London SC   ║
║  Service Tier: Tier 1 - Premium      ║
║  Open Cases:   2 active              ║
║  Phone:        +1 (555) 234-5678     ║
║  Countdown:    35 sec                ║
║                                      ║
║  [Accept]  [Reject]                  ║
╚══════════════════════════════════════╝
```

### After Accept (Customer Summary Panel)
The session opens with the Customer Summary showing:
- **Contact card**: James Morrison, Facilities Manager, Westfield London
- **Account**: Westfield London Shopping Centre
- **Tier Level**: Tier 1 - Premium Service (red badge)
- **Open Cases**: 2 cases listed with titles, priorities, SLA status
- **Recent Activities**: Last 5 interactions (calls, emails, cases)
- **Equipment**: 46 units at location (from Customer Assets)

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Customer name shows blank | Phone number not matching to a Contact | Check contact phone field matches caller's number |
| Custom fields show blank | Context variables not populated | Enable Copilot Studio bot (Step 6) or use Demo Shortcut |
| Template not working | Not assigned to workstream | Complete Step 4 — assign in CS Admin Center |
| Field not on Account form | Form not updated | Complete Step 5 — add column to form |
| Notification looks same as before | Template not published or wrong template selected | Re-check workstream notification settings |
| "Tier Level" field not found | Field creation failed (permissions) | Create manually via make.powerapps.com (see script output) |

---

## Related Files

| File | Purpose |
|------|---------|
| `Configure-VoiceNotificationTemplate.ps1` | Creates notification template + context vars |
| `Add-AccountTierField.ps1` | Creates Account tier field + populates data |
| `otis_CaseFormScripts.js` | Existing Case form auto-population (reads account tier) |
| `otis_AgentScriptSwitcher.js` | Agent script selection based on case type |
| `demo-execution-guide.html` | Main demo guide (screen pop section references these) |
| `environment.json` | Customer tier definitions and demo config |
