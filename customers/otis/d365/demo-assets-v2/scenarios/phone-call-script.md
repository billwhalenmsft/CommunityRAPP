# Otis — Inbound Phone Call Demo Script

> **Customer**: Otis Elevator Company
> **Channel**: Phone (D365 Voice / Azure Communication Services)
> **Agent Persona**: Agent
> **Hero Caller**: Sarah Mitchell (Facilities Manager, Empire State Building)

---

## Pre-Call Setup

### Environment Checklist
- [ ] Agent logged into Customer Service Workspace
- [ ] Omnichannel presence set to **Available** (green)
- [ ] Phone channel enabled in agent's capacity profile
- [ ] Secondary phone ready for demo call
- [ ] This script open on second monitor

### D365 Verification
- [ ] Hero account (Empire State Building) exists and shows as **Premium** tier
- [ ] Hero contact (Sarah Mitchell) has phone number: `+1-555-0147`
- [ ] At least one open case visible on account timeline

---

## Call Flow

### 1. 📞 Call Arrives — Screen Pop Hero Moment

*Your secondary phone calls the Voice Channel number. D365 shows incoming call.*

**What to Show:**
- Incoming call notification with caller ID
- **Screen Pop**: Customer recognized as Sarah Mitchell from Empire State Building
- Tier indicator: **Premium** prominently displayed
- Open cases visible immediately
- Recent interaction timeline

💬 **Talk Track:**
> "Sarah Mitchell calls in. Before I even answer, I can see everything — 
> their account, Empire State Building, is a Premium customer. I see their open cases, 
> recent interactions, and contact history. No asking for account numbers."

**Voice Line (You as Agent):**
> "Thank you for calling Otis support, this is Agent. 
> I see you're calling from Empire State Building. How can I help you today?"

**Voice Line (Caller - Sarah Mitchell):**
> "Hi Agent, we have a product issue. Can you help?"

---

### 2. 🔍 Customer Context Review

**What to Show:**
- Customer 360 pane with full account context
- SLA entitlement and timer visibility
- Recent orders/cases in timeline
- Contact details and preferences

💬 **Talk Track:**
> "Notice I didn't have to ask Sarah Mitchell for any account information. 
> The system recognized them instantly. I can see their service history, 
> their Premium SLA coverage, and any open issues."

**Key Value Points:**
- ⏱️ Saved 30-45 seconds by not asking for account number
- 📊 Complete context before saying hello
- 🎯 Tier-based priority immediately visible

---

### 3. 🤖 Copilot Assistance

**What to Show:**
- Real-time transcription running
- Copilot panel with suggested KB articles
- Sentiment analysis indicator
- Suggested next actions

💬 **Talk Track:**
> "As we talk, Copilot is listening and suggesting relevant knowledge articles. 
> I can see a sentiment indicator — it helps me gauge how the conversation is going. 
> The AI is augmenting my work, not replacing it."

**Demonstrate:**
1. Click Copilot panel to expand
2. Show suggested KB article: "This article matches what they're describing"
3. Point out real-time transcription

---

### 4. 📋 Case Creation / Update

**What to Show:**
- Create new case (or open existing)
- Case form pre-populated with caller context
- SLA timer starting automatically
- Copilot draft response

💬 **Talk Track:**
> "Let me create a case for this issue. Notice the case is already linked to 
> Empire State Building, and our Premium SLA has automatically started. 
> Copilot is drafting notes based on our conversation."

---

### 5. ✅ Resolution & Wrap-Up

**Voice Line (You as Agent):**
> "I've logged this and our team will follow up within your SLA window. 
> Is there anything else I can help with today?"

**Voice Line (Caller - Sarah Mitchell):**
> "No, that was great. Thank you!"

**What to Show:**
- Agent clicks **Resolve Case** or schedules follow-up
- Copilot auto-fills resolution notes from transcript
- Case disposition captured
- Post-call survey triggered (optional)

---

## Key Points to Emphasize


### Value Metrics:
| Metric | Before | After |
|--------|--------|-------|
| Time to identify customer | 30-60 sec | **Instant** |
| Context gathering | Manual lookup | **Pre-loaded** |
| Note-taking | Manual typing | **AI-transcribed** |
| KB search | Agent-driven | **AI-suggested** |

### Hot Words Configured:
*These words trigger priority escalation: urgent, emergency, safety*
