# Copilot Studio Skills Integration Guide

> **End-to-end workflow: RAPP Pipeline → Skills for Copilot Studio → Production Agent**

This guide shows how to combine the RAPP pipeline's agent generation capabilities with Microsoft's
[Skills for Copilot Studio](https://github.com/microsoft/skills-for-copilot-studio) plugin to build,
test, and deploy production-grade Copilot Studio agents from the terminal.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        RAPP Pipeline                                  │
│                                                                       │
│  Discovery Transcript ──→ RAPP Agent ──→ Transpiler ──→ YAML Output  │
│                                                                       │
│  • transcript_to_agent    • Python agent    • agent_manifest.json     │
│  • auto_process           • System prompt   • topics/*.yml            │
│  • manual steps           • Metadata        • flows/*.json            │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  Skills for Copilot Studio Plugin                      │
│                                                                       │
│  YAML Refinement ──→ Push via VS Code ──→ Test ──→ Troubleshoot      │
│                                                                       │
│  • /copilot-studio:author    • VS Code Extension    • :test           │
│  • CAT team best practices   • Push creates draft   • :troubleshoot   │
│  • Schema validation         • Publish makes live   • Batch suites    │
└──────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Production Copilot Studio Agent                     │
│                                                                       │
│  • Microsoft Teams          • M365 Copilot        • Power Apps        │
│  • Custom websites          • Omnichannel          • DirectLine       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Step 1: Install the Plugin

In GitHub Copilot CLI or Claude Code:

```
/plugin marketplace add microsoft/skills-for-copilot-studio
/plugin install copilot-studio@microsoft/skills-for-copilot-studio
```

Verify: type `/` and look for `copilot-studio:author`, `copilot-studio:test`, `copilot-studio:troubleshoot`.

### Step 2: Install the VS Code Extension

Install the [Copilot Studio VS Code Extension](https://github.com/microsoft/vscode-copilotstudio) from the VS Code marketplace. This is required for cloning agents locally and pushing changes back.

### Step 3: Create or Clone a Copilot Studio Agent

**Option A: New agent from RAPP transcript**
```
# Generate agent + demo + tester from a transcript
RAPP action="transcript_to_agent" project_id="contoso-support" customer_name="Contoso"

# Then create an empty agent in Copilot Studio UI
# Clone it locally via VS Code extension
# Apply the RAPP-generated instructions and topics
```

**Option B: Existing agent refinement**
```
# Clone existing agent via VS Code extension
# Navigate to the cloned directory
cd ~/CopilotStudio/MyAgent

# Start authoring
/copilot-studio:author What topics does this agent have? Give me an overview.
```

**Option C: Transpile an existing RAPP agent**
```
# Transpile a Python RAPP agent to Copilot Studio format
CopilotStudioTranspiler action="transpile" agent_name="my_custom_agent"

# Output in transpiled/my_custom_agent/
# Clone empty agent, apply generated YAML
```

### Step 4: Author with Best Practices

```
# Create topics from requirements
/copilot-studio:author I need topics for: product inquiry, order status, returns, 
  and escalation to live agent. Use generative answers for product questions.

# Add knowledge sources
/copilot-studio:author Add a knowledge source pointing to our SharePoint site at 
  https://contoso.sharepoint.com/sites/KnowledgeBase

# Add adaptive cards
/copilot-studio:author Add an adaptive card for order status that shows order number, 
  status, estimated delivery, and tracking link

# Validate
/copilot-studio:troubleshoot Validate all topics in my agent
```

### Step 5: Push + Publish

1. **Push** via VS Code: `Ctrl+Shift+P` → "Copilot Studio: Push"
2. **Publish** in Copilot Studio UI at [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com)

> ⚠️ Push creates a **draft**. You must also **Publish** to make changes live.

### Step 6: Test

```
# Quick point-test
/copilot-studio:test Send "How do I return a product?" to the published agent

# Run batch test suite (requires Power CAT Copilot Studio Kit)
/copilot-studio:test Run my test suite

# Analyze evaluation results
/copilot-studio:test Analyze my evaluation results from ~/Downloads/eval_results.csv
```

### Step 7: Troubleshoot

```
# Wrong topic triggered
/copilot-studio:troubleshoot The agent triggers "Order Status" when I ask about returns

# Disambiguation issues
/copilot-studio:troubleshoot The agent keeps asking "did you mean X or Y" for every question

# Hallucination
/copilot-studio:troubleshoot The agent is making up product details instead of using knowledge
```

---

## Existing RAPP Assets for Copilot Studio

### Pre-Transpiled Agents

These agents have already been transpiled from RAPP Python agents to Copilot Studio format and are ready for the plugin workflow:

| Suite | Agents | Status | Location |
|-------|--------|--------|----------|
| Zurn Elkay CI | 7 (orchestrator + 5 BU + synthesizer) | ✅ Deployed | `transpiled/zurnelkay_*` |
| Plumbing Code Intel | 3 (monitor + extractor + synthesizer) | ✅ Transpiled | `transpiled/plumbing_code_*` |
| Carrier Case Mgmt | 1 (case analyzer) | ✅ Transpiled | `transpiled/carrier_*` |

### Deployment Tools

| Tool | Purpose |
|------|---------|
| `utils/copilot_studio_api.py` | Python client for Dataverse API — create agents, topics, knowledge sources programmatically |
| `scripts/deploy_agents.py` | Batch deployment of agents with system prompts |
| `scripts/fix_agent_generative_ai.py` | Fix `useModelKnowledge` flag on deployed agents |
| `copilot_studio_deployment_config.json` | Environment credentials for deployment |

### Testing Resources

| Resource | Location |
|----------|----------|
| 100+ test prompts by agent | `docs/copilot_studio_testing_guide.md` |
| API deployment guide | `docs/copilot_studio_api_guide.md` |
| Power Platform integration | `docs/POWER_PLATFORM_INTEGRATION.md` |

---

## Advanced: Multi-Agent Orchestrator Pattern

For complex scenarios like the Zurn Elkay 7-agent suite, use this pattern:

```
# 1. Create orchestrator agent in Copilot Studio
# 2. Clone locally
# 3. Configure orchestration via plugin:

/copilot-studio:author This is an orchestrator agent that routes to 5 sub-agents 
  based on business unit. Use agent instructions to describe when to route to each:
  - Drains CI Agent: drainage products, Watts, JR Smith, MiFab
  - Drinking Water CI Agent: fountains, bottle fillers, Elkay, Oasis
  - Sinks CI Agent: stainless steel sinks, Just Manufacturing
  - Commercial Brass CI Agent: valves, fittings, Watts, Nibco
  - Wilkins CI Agent: backflow prevention, Febco, Ames

# 4. Add connected agents
/copilot-studio:author Add the 5 BU agents as connected agents

# 5. The plugin uses agent-level instructions for smart disambiguation
#    (this is the CAT team pattern from the blog post)
```

> **Key insight from the CAT team:** For multi-agent disambiguation, use **agent instructions** rather than complex trigger phrase engineering. The orchestrator model uses the instructions to decide routing, which scales much better than trigger-based approaches.

---

## Comparison: RAPP API vs Plugin Authoring

| Capability | RAPP API (`copilot_studio_api.py`) | Plugin (`/copilot-studio:author`) |
|---|---|---|
| Agent creation | ✅ Programmatic via Dataverse | ❌ Create in UI first, then clone |
| Topic authoring | ✅ JSON via API | ✅ YAML with schema validation |
| Knowledge sources | ✅ Programmatic | ✅ Via skill with best practices |
| AI instructions | ✅ Custom GPT component (type 15) | ✅ Via `edit-agent` skill |
| Batch deployment | ✅ Script-based | ❌ One agent at a time |
| Testing | ❌ Manual | ✅ Point-test, batch, DirectLine |
| Troubleshooting | ❌ Manual | ✅ Schema-aware debugging |
| Best practices | ❌ Developer knowledge | ✅ CAT team patterns built-in |

**Recommendation:** Use the RAPP API for **initial bulk deployment** (creating agents + setting AI config), then use the plugin for **refinement, testing, and troubleshooting**.

---

## Troubleshooting the Plugin

| Issue | Solution |
|-------|---------|
| Plugin not found after install | Run `/plugin list` to verify. Try reinstalling. |
| Schema lookup "not found" | Definition names are case-sensitive. Use `lookup-schema` with search. |
| YAML parse error on push | Run `/copilot-studio:validate` before pushing. |
| Test returns "not published" | Push AND Publish in Copilot Studio UI. |
| DirectLine auth failure | Verify DirectLine secret or token endpoint URL. |
| App Registration error | Ensure `CopilotStudio.Copilots.Invoke` permission is granted by admin. |

---

## References

- [Skills for Copilot Studio — GitHub](https://github.com/microsoft/skills-for-copilot-studio)
- [Skills for Copilot Studio — Blog Post](https://microsoft.github.io/mcscatblog/posts/skills-for-copilot-studio/)
- [Copilot Studio VS Code Extension](https://github.com/microsoft/vscode-copilotstudio)
- [Power CAT Copilot Studio Kit](https://github.com/microsoft/Power-CAT-Copilot-Studio-Kit)
- [Copilot Studio Documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
