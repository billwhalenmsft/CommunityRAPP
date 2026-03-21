# Deployment Guide: SMA4 Persona Workbench → Copilot Studio

## Overview

This guide deploys the **SMA4 Persona Workbench** as a single unified generative agent in Copilot Studio. The agent is **self-contained** — all knowledge is embedded in the agent instructions, no backend HTTP calls or Power Automate flows required.

**Target environment:** `org6feab6b5.crm.dynamics.com`
**Channels:** M365 Copilot, Teams, Custom UI

---

## Architecture

```
┌─────────────────────────────────────────┐
│          Copilot Studio Agent           │
│     "SMA4 Persona Workbench"            │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   Agent Instructions            │    │
│  │   (instructions.md content)     │    │
│  │   - All pipeline data           │    │
│  │   - All tasks, exceptions       │    │
│  │   - Approval matrix             │    │
│  │   - Handoff coordination        │    │
│  │   - Persona filtering rules     │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Topics (generative orchestration):     │
│  ├── Greeting (persona selection)       │
│  ├── Cockpit View                       │
│  ├── Pipeline                           │
│  ├── Tasks                              │
│  ├── Exceptions                         │
│  ├── Approvals                          │
│  ├── Handoffs                           │
│  └── Help                               │
└─────────────────────────────────────────┘
         ↕ Generative AI (GPT-4)
```

No Power Automate flows. No connectors. No external APIs.

---

## Step 1: Create Agent in Copilot Studio

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Ensure you're in the correct environment: **org6feab6b5.crm.dynamics.com**
   - Check the environment selector in the top-right corner
3. Click **Create** → **New agent**
4. Name: **SMA4 Persona Workbench**
5. Description: *Unified sales operations assistant with persona-specific cockpit views*
6. Click **Create**

## Step 2: Configure Agent Instructions

1. In the agent editor, click **Instructions** from the top menu
2. **Replace** the default instructions with the FULL content of `instructions.md` from this package
3. This is the most critical step — the entire agent's knowledge is in these instructions

> **Tip:** The instructions contain ~10KB of structured data (pipeline, tasks, exceptions, approvals, handoffs). Copilot Studio supports large instruction sets for generative agents.

## Step 3: Enable Generative AI

1. In the agent editor, go to **Settings** → **Generative AI**
2. Ensure **Generative answers** is set to **Generative (preview)** or **Classic + Generative**
3. Set the model to **GPT-4o** if available
4. Enable **Allow the AI to use its own general knowledge** → ON

## Step 4: Create Topics

For each topic file in the `topics/` directory, create a corresponding topic in Copilot Studio:

### 4a. Greeting Topic
1. Go to **Topics** → **+ New topic** → **From blank**
2. Name: **Greeting**
3. Add trigger phrases: "hello", "hi", "start", "get started"
4. Add a **Message** node with the greeting text from `topic_greeting.yaml`
5. Add a **Question** node asking which persona they are
6. Add a final **Message** node with usage examples

### 4b. Cockpit View Topic
1. **+ New topic** → **From blank**
2. Name: **Cockpit View**
3. Add trigger phrases from `topic_cockpit_view.yaml`: "show me my cockpit view", "cockpit", "dashboard", "morning briefing"
4. Add a **Generative answers** node
5. In the content moderation, select **Medium** to allow rich data responses

### 4c. Pipeline, Tasks, Exceptions, Approvals, Handoffs Topics
Repeat the pattern for each — create topic, add trigger phrases from the YAML, add a **Generative answers** node.

### 4d. Help Topic
1. **+ New topic** → **From blank**
2. Name: **Help**
3. Add trigger phrases: "help", "what can you do", "capabilities"
4. Add a **Message** node with the help content from `topic_help.yaml`

## Step 5: Test in Canvas

1. Click **Test your agent** (bottom-left panel)
2. Try these test conversations:

**Test 1 — Persona Selection:**
> "Hi, I'm Sarah Chen"
> Expected: Agent recognizes Sales Rep persona

**Test 2 — Cockpit View:**
> "Show me my cockpit view"
> Expected: Pipeline (4 deals), tasks (4 items), exceptions (2), approval (1 pending), handoffs (3)

**Test 3 — Pipeline Detail:**
> "Tell me about the Fabrikam deal"
> Expected: $185K, CRM Rollout, Develop stage, 18% discount, pending approval, missing decision_maker

**Test 4 — Manager View:**
> "I'm James Harrison. Show me all exceptions."
> Expected: All 5 exceptions, critical items first (credit hold, discount breach)

**Test 5 — Cross-domain:**
> "What's blocking the Adventure Works deal?"
> Expected: Stalled (22 days in Propose), credit hold ($410K > $400K), close date slip, handoff blocked

## Step 6: Publish

1. Click **Publish** from the top menu
2. Click **Publish** again to confirm
3. Wait for publication to complete

## Step 7: Enable Channels

### Teams
1. Go to **Channels** → **Microsoft Teams**
2. Click **Turn on Teams**
3. Click **Open in Teams** to test

### M365 Copilot
1. Go to **Channels** → **Microsoft 365 Copilot**
2. Enable the channel
3. Submit for admin approval if required by your org

### Custom UI
1. Go to **Channels** → **Custom website**
2. Copy the embed code or Direct Line token
3. Integrate into your custom UI

---

## Alternative: VS Code Extension Push (Advanced)

If you prefer using the VS Code Copilot Studio Extension:

1. **Clone** the agent you created in Step 1:
   - Open VS Code → Copilot Studio Extension panel
   - Connect to `org6feab6b5.crm.dynamics.com`
   - Find "SMA4 Persona Workbench" → Clone locally

2. **Replace** the cloned topic files with the ones from this `topics/` directory

3. **Push** changes back:
   - In VS Code, right-click the agent → Push to Copilot Studio

4. **Publish** in Copilot Studio UI

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent gives generic answers | Verify instructions.md content was fully pasted into Agent Instructions |
| Topics not triggering | Check trigger phrases match user input; ensure generative orchestration is ON |
| Persona filtering not working | Ensure instruction text includes all persona filtering rules |
| Responses truncated | Enable "Allow long messages" in agent settings |
| No data in responses | Check that all tables from instructions.md are present in agent instructions |

---

## Files in This Package

| File | Purpose |
|------|---------|
| `agent_manifest.json` | Agent metadata and configuration |
| `instructions.md` | **Complete agent instructions** — paste into Copilot Studio |
| `topics/topic_greeting.yaml` | Greeting + persona selection topic |
| `topics/topic_cockpit_view.yaml` | Unified dashboard topic |
| `topics/topic_pipeline.yaml` | Pipeline / opportunity topic |
| `topics/topic_tasks.yaml` | Task queue topic |
| `topics/topic_exceptions.yaml` | Exception monitor topic |
| `topics/topic_approvals.yaml` | Approval routing topic |
| `topics/topic_handoffs.yaml` | Handoff coordination topic |
| `topics/topic_help.yaml` | Help / capabilities topic |
| `DEPLOYMENT_GUIDE.md` | This file |
