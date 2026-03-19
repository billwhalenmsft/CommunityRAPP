# Otis — Chat / Digital Messaging Demo Script

> **Customer**: Otis Elevator Company
> **Channel**: Web Chat (Portal → Copilot Studio → Live Agent)
> **Agent Persona**: Agent
> **Chat Customer**: Rachel Chen (Metro Supply)

---

## Scenario Overview

**Story**: Customer visits the self-service portal, starts a chat with the bot, 
and escalates to a live agent when they need help with a complex request.

**Key Demo Points:**
- Seamless bot → human handoff
- Full conversation context transfers to agent
- No customer repetition
- Guided actions for complex workflows

---

## Pre-Chat Setup

### Environment Checklist
- [ ] Portal open in a browser tab (incognito for clean experience)
- [ ] Agent logged into Customer Service Workspace
- [ ] Chat channel presence set to **Available**
- [ ] Chat capacity configured for agent

---

## Act 1: Customer Visits Portal

**Action**: Open the customer self-service portal in browser.

💬 **Talk Track:**
> "Let me show you the customer's perspective. A Metro Supply employee 
> visits the Otis support portal to get help."

**What to Show:**
- Portal home page with knowledge base
- Chat widget in bottom-right corner
- "Chat with us" button or bubble

---

## Act 2: Bot Greeting & Self-Service Attempt

**Action**: Click the chat widget to start a conversation.

**Bot**: "Hello! Welcome to Otis support. I'm your virtual assistant. How can I help you today?"

**Rachel Chen**: "I need help with my recent order."

**Bot**: "I'd be happy to help with your order. Can you provide your order number?"

**Rachel Chen**: "It's ORD-78421."

**Bot**: "I found your order. Here's the status:
- Order #ORD-78421
- Status: In Transit
- Expected Delivery: Tomorrow by 5 PM

Is there something specific you need help with?"

💬 **Talk Track:**
> "The bot can handle simple queries like order status lookup. It's connected 
> to our backend systems and can retrieve real-time information. Many customers 
> get their answers here without needing a live agent."

---

## Act 3: Escalation to Live Agent

**Rachel Chen**: "Actually, I need to speak with someone about modifying this order. One of the items isn't right."

**Bot**: "I understand you need help modifying your order. Let me connect you with a support specialist who can assist with that."

*Bot transfers to live agent queue with full conversation context.*

💬 **Talk Track:**
> "The customer needs help beyond what the bot can do. Watch how the handoff works."

---

## Act 4: Agent Receives Chat

**Switch to Agent View**

**What to Show (Agent Workspace):**
- Chat notification arrives with context preview
- Bot conversation transcript visible immediately
- Customer identified and account loaded
- Order details already shown

💬 **Talk Track:**
> "As the agent, I receive the chat with full context. I can see everything the 
> customer discussed with the bot — the order number, what they're trying to do. 
> Rachel Chen doesn't have to repeat anything."

**Agent Response:**
> "Hi Rachel, I can see you need help modifying order ORD-78421. 
> I have the details right here. Let me pull up the order modification tool."

---

## Act 5: Resolution with Guided Actions

**What to Show:**
- Agent opens the Order Management custom page from side pane
- Order details displayed with editable line items
- Modification workflow with validation
- Real-time updates visible to customer

💬 **Talk Track:**
> "I have guided actions built right into my workspace. This Order Management tool 
> lets me quickly view and modify orders without leaving the conversation. 
> Everything is connected."

**Agent**: "I've updated the quantity on line 3. You should see the new order total reflected. Anything else?"

**Rachel Chen**: "That's perfect, thank you!"

---

## Key Points to Emphasize

### Bot → Human Handoff
| Before (Manual) | After (D365 Omnichannel) |
|-----------------|--------------------------|
| Customer repeats everything | Full context transfers automatically |
| Agent asks for order # again | Order already loaded in agent view |
| 2-3 minute context gathering | **Instant context** |

### What Makes This Different:
- **Conversational AI** handles routine queries (order status, hours, FAQs)
- **Seamless escalation** when complexity requires human expertise
- **Guided actions** (custom pages) embedded in agent workspace
- **Unified history** — this chat appears in customer timeline alongside calls and emails
