# Demo Simulation Setup Guide

Interactive customer simulation for D365 Customer Service demos.

## Quick Start

The Demo Execution Guide now includes a **right-side cheat sheet** with:
- 🎬 **Simulation Triggers** - One-click buttons for Email, Chat, Voice
- 🏢 **Hero Account/Contact/Case** - Reference data at a glance
- 🔗 **Quick Links** - D365 Workspace, Outlook
- ⚙️ **Flow Config** - Store your Power Automate URLs in localStorage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Demo Execution Guide                          │
│  ┌──────────┬─────────────────────────┬──────────────────────────┐ │
│  │  Nav     │      Demo Script        │   🎮 Cheat Sheet         │ │
│  │          │                         │                          │ │
│  │ Sections │  Click-by-click steps   │  [📧 Send Email]         │ │
│  │          │  with talk tracks       │  [💬 Start Chat]         │ │
│  │          │                         │  [📞 Incoming Call]      │ │
│  │          │                         │                          │ │
│  │          │                         │  Hero Account: Acme      │ │
│  │          │                         │  Hero Contact: John      │ │
│  │          │                         │  Hero Case: #12345       │ │
│  └──────────┴─────────────────────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ JavaScript fetch()
┌─────────────────────────────────────────────────────────────────────┐
│                     Power Automate Cloud Flows                      │
│  ┌──────────────────┬──────────────────┬──────────────────────┐   │
│  │  Email Flow      │   Chat Flow      │    Voice Flow        │   │
│  │  (HTTP trigger)  │   (HTTP trigger) │    (HTTP trigger)    │   │
│  │                  │                  │                      │   │
│  │  ▼ Outlook       │  ▼ PAD trigger   │    ▼ ACS + TTS       │   │
│  │  Send to D365    │  OR HTTP call    │    Outbound call     │   │
│  └──────────────────┴──────────────────┴──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     D365 Customer Service                           │
│  ┌──────────┬────────────────┬──────────────────────────────────┐  │
│  │  Queue   │  Voice Channel │   Portal Chat Widget             │  │
│  │  (email) │  (ACS)         │   (Power Pages/Portal)           │  │
│  └──────────┴────────────────┴──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Setup Options

### Option A: Power Automate Desktop (PAD) + StreamDeck
**Best for:** SE controls demos physically with a StreamDeck or mobile device

### Option B: Copilot Studio Customer Agent
**Best for:** SE or colleague acts as customer using natural language from a phone

### Option C: Direct Power Automate HTTP
**Best for:** Simple email/chat triggers without IVR/voice

---

## Option A: PAD + StreamDeck Setup

### Step 1: Create the PAD Flow

1. Open **Power Automate Desktop**
2. Create new flow: "Demo Chat Simulator"
3. Import the PAD flow definition from `d365/utils/demo_simulator.py`:

```python
# In Python, generate the PAD definition
from d365.utils.demo_simulator import DemoSimulator

simulator = DemoSimulator(your_config)
pad_flow = simulator.generate_chat_pad_definition()

# Save to file for import
import json
with open("chat_simulator.pad", "w") as f:
    json.dump(pad_flow, f, indent=2)
```

### Step 2: Configure StreamDeck

1. Add **Power Automate Desktop** plugin to StreamDeck
2. Create button for each simulation:
   - **Email**: Run flow "Demo Email Simulator"
   - **Chat**: Run flow "Demo Chat Simulator"  
   - **Voice**: Run flow "Demo Voice Simulator"

### Step 3: Test the Flow

1. Open your customer portal with chat widget
2. Press StreamDeck button
3. PAD launches browser, clicks chat widget, types message

---

## Option B: Copilot Studio Customer Agent

### Step 1: Create the Agent

1. Go to **Copilot Studio** (copilotstudio.microsoft.com)
2. Create new agent: "Customer Simulator [CustomerName]"
3. Import topics from generated YAML:

```python
from d365.utils.demo_simulator import generate_copilot_studio_customer_agent

agent_yaml = generate_copilot_studio_customer_agent()
# Save for import
```

### Step 2: Deploy to Teams or Mobile

1. Publish agent to Teams
2. Install on your phone
3. During demo: "Send angry email about shipping delay"

### Step 3: Configure Actions

The agent can trigger:
- Email flow via HTTP
- Chat flow via HTTP
- Voice flow via HTTP

---

## Option C: Direct HTTP Setup

### Step 1: Create Email Flow

1. Go to **Power Automate** (make.powerautomate.com)
2. Create **Instant cloud flow** with HTTP trigger
3. Add actions:
   - Parse JSON (incoming payload)
   - Send email (Office 365 Outlook)
   - Response (return status)

**Flow Definition** (from demo_simulator.py):
```json
{
  "trigger": "HTTP Request",
  "actions": [
    "Send_Email (Office 365 Outlook)",
    "Response"
  ]
}
```

### Step 2: Get HTTP URL

1. Save flow
2. Copy HTTP POST URL
3. Paste into Demo Execution Guide config panel

### Step 3: Configure in Guide

1. Open Demo Execution Guide
2. Expand "⚙️ Flow URLs" in cheat sheet
3. Paste URLs:
   - Email: `https://prod-123.azure.com/workflows/...`
   - Chat: `https://prod-456.azure.com/workflows/...`
   - Voice: `https://prod-789.azure.com/workflows/...`
4. Click **💾 Save**

---

## Voice Simulation (Advanced)

### Prerequisites

1. **Azure Communication Services** resource
2. Phone number provisioned in ACS
3. **Azure Cognitive Services (Speech)** for TTS
4. D365 Voice Channel configured to receive ACS calls

### Flow Overview

1. HTTP trigger receives call request
2. Generate TTS audio from customer script
3. Place outbound call via ACS to Voice Channel number
4. Play TTS message when answered
5. D365 routes to agent workspace

### Security Note

Voice simulation requires:
- ACS connection string (sensitive)
- Cognitive Services endpoint
- Use Key Vault references in Production

---

## Simulation Scripts

The DemoSimulator generates customer scripts from demo story characters:

| Channel | Sample Script |
|---------|--------------|
| **Email** | "Hello, I placed order #12345 last week and haven't received tracking. This is unacceptable for a Gold customer. Please advise urgently." |
| **Chat** | "Hi, I need help with my recent order. It was supposed to arrive yesterday." |
| **Voice** | "Hi, I'm calling about order twelve three four five. I haven't received it yet and I'm getting concerned." |

Scripts auto-adjust based on:
- `sentiment`: neutral, angry, happy
- `scenario`: shipping, pricing, technical, warranty
- `tier`: affects urgency language

---

## Troubleshooting

### Button shows "Configure flow URL first"
→ Expand Flow URLs section, enter your Power Automate HTTP trigger URL

### Email not appearing in D365
→ Verify support email matches D365 queue address
→ Check Outlook connector has send permissions

### Chat simulation not working
→ PAD needs browser automation permissions
→ Portal chat selector may have changed

### Voice call not ringing
→ Verify ACS phone number is correct
→ Check Voice Channel configuration in D365

---

## Security Best Practices

1. **Never commit** flow URLs to git (stored in localStorage)
2. Use **Managed Identities** for ACS/Cognitive Services
3. Restrict flows to **specific IP ranges** if possible
4. Enable **audit logging** on Power Automate
5. Use **environment variables** for sensitive endpoints

---

## Files Reference

| File | Purpose |
|------|---------|
| `d365/utils/demo_simulator.py` | Flow generators, control panel |
| `d365/utils/demo_asset_generator.py` | HTML guide with 3-column layout |
| Generated: `{customer}_execution_guide.html` | Interactive demo guide |
| Generated: `flows/email_flow.json` | Power Automate definition |
| Generated: `flows/chat_pad.json` | PAD flow definition |
| Generated: `flows/voice_flow.json` | ACS voice flow definition |
