# Productivity Toolkit Deployment Guide - Otis EMEA

## Overview

This guide walks through deploying Agent Scripts, Macros, and Quick Responses for the Otis elevator service demo in D365 Customer Service.

## Prerequisites

- Admin access to Customer Service admin center
- Customer Service workspace app profile configured
- Productivity pane enabled

---

## 1. Agent Scripts Setup

### Path: Customer Service admin center → Agent experience → Productivity → Agent scripts

### Script 1: Entrapment Protocol

| Field | Value |
|-------|-------|
| **Name** | Entrapment Response Protocol |
| **Unique Name** | otis_entrapment_protocol |
| **Description** | Guided workflow for handling passenger entrapments |
| **Language** | English |

**Steps:**

| Order | Step Name | Type | Content |
|-------|-----------|------|---------|
| 1 | Verify Entrapment | Text | Confirm with caller: "I understand there's a passenger trapped. Can you confirm the exact elevator number and current floor display?" |
| 2 | Check Passenger Status | Script | [Text instruction] Ask: "Is the passenger responsive? Any medical conditions or mobility concerns we should alert the technician about?" |
| 3 | Confirm Contact Info | Text | "I'll have a technician there within {SLA time}. What's the best number to reach you directly for updates?" |
| 4 | Dispatch Notification | Macro | *Link to "Create Emergency Work Order" macro* |
| 5 | Follow-Up Commitment | Text | "I'll call you back in 5 minutes with an ETA. Please keep the intercom line open with the passenger." |

### Script 2: Service Request Intake

| Field | Value |
|-------|-------|
| **Name** | Service Request Intake |
| **Unique Name** | otis_service_intake |
| **Description** | Standard intake flow for non-emergency service requests |

**Steps:**

| Order | Step Name | Type | Content |
|-------|-----------|------|---------|
| 1 | Verify Account | Text | "Let me pull up your account... I see you're with {Account Name}. Is this regarding your {Location} facility?" |
| 2 | Issue Description | Script | Ask: "Can you describe what's happening? When did you first notice this?" |
| 3 | Equipment Identification | Text | "Which elevator/escalator unit is affected? The unit number is usually posted inside the cab or at the landing." |
| 4 | Urgency Assessment | Macro | *Link to "Check Service Priority" macro* |

### Script 3: Contract Renewal Conversation

| Field | Value |
|-------|-------|
| **Name** | Contract Renewal Discussion |
| **Unique Name** | otis_contract_renewal |
| **Description** | Guide for handling contract renewal conversations |

**Steps:**

| Order | Step Name | Type | Content |
|-------|-----------|------|---------|
| 1 | Review History | Text | "Before we discuss renewal, let me highlight your service history over the past year..." |
| 2 | Value Summary | Text | "Based on our records, our technicians completed {X} preventive visits and resolved {Y} callbacks. Your equipment uptime was {Z}%." |
| 3 | Upgrade Options | Macro | *Link to "Show Contract Options" macro* |
| 4 | Next Steps | Text | "Would you like me to have your Account Manager reach out to discuss these options in detail?" |

---

## 2. Macros Setup

### Path: Customer Service admin center → Agent experience → Productivity → Macros

### Macro 1: Create Emergency Work Order

| Field | Value |
|-------|-------|
| **Name** | Create Emergency Work Order |
| **Unique Name** | otis_emergency_wo |
| **Description** | One-click emergency work order creation |

**Actions:**

1. **Open new form** - Entity: Work Order, Form: Quick Create
2. **Autofill** - Work Order Type: Emergency
3. **Autofill** - Priority: Urgent
4. **Autofill** - Customer: {Current case customer}
5. **Autofill** - Related Case: {Current case ID}

### Macro 2: Send SLA Alert Email

| Field | Value |
|-------|-------|
| **Name** | Send SLA Warning Email |
| **Unique Name** | otis_sla_alert |
| **Description** | Auto-compose SLA approaching email to supervisor |

**Actions:**

1. **Open new email**
2. **Set To**: Field Service Supervisor
3. **Set Subject**: "SLA Alert: Case {Case Number} - {Account Name}"
4. **Set Body**: "Case approaching SLA deadline.\n\nCase: {Title}\nAccount: {Account}\nSLA Deadline: {SLA Time}\nTime Remaining: {Remaining}\n\nPlease review for potential escalation."

### Macro 3: Open Account 360 View

| Field | Value |
|-------|-------|
| **Name** | View Account 360 |
| **Unique Name** | otis_account_360 |
| **Description** | Open customer's full account view in new tab |

**Actions:**

1. **Open record** - Entity: Account, ID: {Current case customer ID}
2. **Open tab** - Tab: Service Summary

### Macro 4: Schedule Follow-Up

| Field | Value |
|-------|-------|
| **Name** | Schedule Follow-Up Call |
| **Unique Name** | otis_schedule_followup |
| **Description** | Create follow-up phone call activity |

**Actions:**

1. **Create activity** - Type: Phone Call
2. **Set Regarding**: {Current case}
3. **Set Due Date**: {Current time + 5 minutes}
4. **Set Subject**: "Follow-up: {Case Title}"
5. **Show notification**: "Follow-up scheduled for 5 minutes"

### Macro 5: Link Knowledge Article

| Field | Value |
|-------|-------|
| **Name** | Link KB Article to Case |
| **Unique Name** | otis_link_kb |
| **Description** | Associate current KB article with case |

**Actions:**

1. **Associate record** - From: Knowledge Article (current), To: Case (current context)
2. **Show notification**: "Article linked to case"

### Macro 6: Escalate to Supervisor

| Field | Value |
|-------|-------|
| **Name** | Escalate Case Now |
| **Unique Name** | otis_escalate |
| **Description** | One-click escalation with notification |

**Actions:**

1. **Update case** - Set: escalated = true
2. **Create note** - Text: "Case escalated by {Agent Name} at {Timestamp}"
3. **Open new email** to Supervisor
4. **Show notification**: "Case escalated"

---

## 3. Quick Responses Setup

### Path: Customer Service admin center → Agent experience → Productivity → Quick responses

### Create the following quick responses:

| Name | Message | Tags |
|------|---------|------|
| **Greeting - Standard** | Hello {Customer Name}, thank you for contacting Otis Service. I'm {Agent Name} and I'll be happy to assist you today. How can I help? | greeting, opening |
| **Technician ETA** | Good news - I've dispatched a technician to your location. Their estimated arrival time is {ETA}. They'll have full access credentials and will check in with your facilities team upon arrival. | dispatch, eta |
| **Entrapment Reassurance** | I understand this is stressful. Our technician is specially trained in passenger extraction and will have the situation resolved safely. We'll maintain communication every 5 minutes until they arrive. | entrapment, safety |
| **Hold Request** | I need to check on a few details for you. Would you mind holding for approximately 2 minutes while I pull up that information? | hold, courtesy |
| **Callback Promise** | I'll call you back within {timeframe} with an update. Is {phone number} still the best number to reach you? | callback, followup |
| **Service Scheduled** | Your service visit has been scheduled for {Date} at {Time}. Our technician {Tech Name} will arrive between {Window}. Please ensure someone is available to provide building access. | scheduling, confirmation |
| **Case Resolution** | I'm pleased to confirm that your service issue has been resolved. Our technician completed {Work Description} and all equipment is now operational. Is there anything else I can help you with today? | resolution, closing |
| **Transfer Warm** | I'm going to connect you with our {Department} team who can better assist with this request. I'll stay on the line to introduce you and share the details we've discussed. | transfer, handoff |

---

## 4. Associate with App Profile

After creating all productivity tools:

1. Go to: **Customer Service admin center → Agent experience → Workspaces**
2. Open your app profile (e.g., "Customer Service workspace")
3. Go to **Productivity pane** tab
4. Enable agent scripts, macros, and quick responses
5. In **Agent scripts** section, add all three Otis scripts
6. Save and publish

---

## 5. Validation Checklist

- [ ] All 3 agent scripts created and active
- [ ] All 6 macros created and tested
- [ ] All 8 quick responses created
- [ ] Productivity tools associated with app profile
- [ ] Agent scripts appear in productivity pane
- [ ] Macros show in command bar
- [ ] Quick responses available in chat/email compose

---

## Demo Tips

1. **Show Agent Script during entrapment case** - Walk through the guided workflow step by step
2. **Use macro for quick work order** - Demonstrate one-click automation
3. **Insert quick response in chat** - Show how templates speed up responses
4. **Highlight the consistency** - All agents follow same proven protocols
