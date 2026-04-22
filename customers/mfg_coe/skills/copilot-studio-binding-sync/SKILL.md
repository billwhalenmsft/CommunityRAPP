---
name: copilot-studio-binding-sync
description: Diagnose and auto-fix Copilot Studio topic ↔ Power Automate flow binding drift. Use when CS shows "Topic Errors" after a flow schema change, or when a flow returns "FlowActionBadRequest" with type mismatches. INVOKE FOR phrases like "topic errors in copilot studio", "flow binding broken", "publish failing with binding errors", "topic output bindings out of sync", "fix CS topics after flow update".
---

# Copilot Studio Binding Sync Skill

## When to use
- User reports "Topic Errors" when publishing a CS agent
- A PA flow's output schema changed and topics still reference old output names
- Error: `The parameter with name 'X' on flow 'Y' evaluated to type 'StringDataType', expected type 'UnspecifiedDataType'`
- Error: `Binding X not found, refresh this flow`
- After running any RAPP transpiler that regenerates flows

## Core knowledge (hard-won, do not relearn)

### 1. Edit `botcomponent.data`, NEVER `botcomponent.content`
- `data` field = actual executable v2 schema YAML — PATCH succeeds
- `content` field = derived/cached display copy — PATCH returns `400 "parsing value: k"`

### 2. Topic schema variants — pick the one the agent already uses
Look at a known-working topic in the same agent first. Two variants exist:

**Legacy/v1 (preferred, broader compatibility):**
```yaml
- kind: Question
  id: askThing
  alwaysPrompt: false
  variable: init:Topic.Thing       # NOTE: init: prefix
  prompt: ...
  entity: StringPrebuiltEntity     # inline string
  allowInterruption: true          # at root
```

**Modern/v2 (newer agents only — rejected by some editor builds):**
```yaml
- kind: Question
  id: askThing
  interruptionPolicy:
    allowInterruption: true        # nested
  variable: Topic.Thing            # no prefix
  prompt: ...
  entity:
    kind: TextPrebuiltEntity       # object form
```

**RULE: Match the variant of the working baseline topic in the same agent.** Mixing variants in one agent causes "Topic Errors".

### 3. InvokeFlowAction binding direction is REVERSED
```yaml
input:
  binding:
    flow_param_name: =Topic.Var       # flow_param_name is KEY (left)
output:
  binding:
    flow_output_name: Topic.Var       # flow_output_name is KEY (left)
flowId: <internal-dataverse-id>       # NOT the PA flow GUID
```

### 4. Power Fx literal strings need `=` prefix
- `=""` ✅
- `="demo-user"` ✅
- `"demo-user"` ❌ (silently breaks at runtime, not at validation)

### 5. Flow output type bug — must declare `type: object` in PA flow Response
If output param shows as `UnspecifiedDataType` error, edit the PA flow in **modern designer** (not classic), set output type to `Text` or `Number` (not `Any`), and **publish from modern designer** (classic publish doesn't write the type).

### 6. Stale flow tool reference cache (the "13 Other Errors" trap)
After patching topics, if publish still fails with "Binding X not found":
- The 6 flow tool botcomponents (named `<Customer>: <FlowDisplayName>`, `componenttype = 9` but they're flow refs) cache an old schema
- PATCH each tool ref's `data` field to match the new flow output schema, OR
- In CS: open topic, click Action node → Refresh, save (this auto-updates the cache)

## Required inputs
- `org_url` — Dataverse org (e.g., `https://orgXXX.crm.dynamics.com`)
- `bot_id` — botcomponentid GUID (componenttype=15 for the bot itself)
- `flow_id` (optional) — to scope to one flow; otherwise scans all
- `dry_run` — bool (default true)

## Procedure
1. `az login` then `az account get-access-token --resource $org_url`
2. List botcomponents: `?$filter=_parentbotid_value eq {bot_id}&$select=botcomponentid,name,componenttype,data`
3. For each topic (componenttype=9), parse `data` YAML, find every `InvokeFlowAction`
4. For each invoked flow, fetch the live flow output schema from Power Automate (`/providers/Microsoft.Flow/flows/{flowId}` Logic Apps API) OR from the matching flow tool botcomponent's cached `data`
5. Diff `output.binding` keys vs flow's actual output names
6. Diff `input.binding` keys vs flow's actual input names + check for missing `=` prefix on string literals
7. If `dry_run`: print proposed PATCH per topic
8. Else: PATCH `botcomponent.data` with corrected YAML using `If-Match: *` header
9. After patching: PATCH each affected flow tool botcomponent (the cache) with the new schema
10. Report: `topics_inspected`, `mismatches_found`, `patches_applied`, `unresolved`

## PATCH headers (exact)
```
Authorization: Bearer <token>
Content-Type: application/json
OData-MaxVersion: 4.0
OData-Version: 4.0
If-Match: *
```
Body: `{"data": "<yaml string>"}`

## Verification
After running, ask the human: "Open CS → publish the agent. If it fails, paste the 'Show raw' for any topic with errors." If still failing, check the flow tool reference cache (step 9 above).

## Reference implementation
See `binding_sync.ps1` in this folder for a working PowerShell reference. Port to Python for the CoE runner.

## Python execution script (Ascend SAP)
Use `binding_sync.py` in this same folder for the executable patch flow:

```bash
# Set target explicitly (recommended)
export COPILOT_STUDIO_ORG_URL="https://org6feab6b5.crm.dynamics.com"
export COPILOT_STUDIO_BOT_ID="a1aa62dd-a23d-f111-bec6-70a8a59a411e"

# Dry run (default)
python customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py

# Apply PATCH operations
python customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py --apply
```

Expected summary fields:
- `topics_inspected`
- `topic_patches`
- `flow_tool_patches`

## Don't do
- Don't PATCH `botcomponent.content` (will fail)
- Don't change `flowId` values (each topic's flowId is the internal Dataverse ID, not the PA flow GUID)
- Don't mix v1 and v2 schema variants in the same agent
- Don't trust classic flow designer output type — always verify in modern
