"""
Agent: MfgCoE Power Platform Dev Agent
Purpose: Power Platform specialist for the Mfg CoE.
         Generates Copilot Studio YAML topics (Skills-kind), Power Automate flow
         definitions, Power Apps canvas app structure docs, and custom connector stubs.
         Reads D365 Dev artifacts for entity/field context when building flows and topics.

Actions:
  execute_issue                — Full build: parse issue → generate PP artifacts → write to disk
  generate_copilot_studio_topic — Copilot Studio YAML topic (AdaptiveDialog)
  generate_power_automate_flow  — Power Automate flow JSON (Skills kind, modern designer)
  generate_canvas_app_structure — Power Apps screen/formula stub documentation
  generate_custom_connector     — Custom connector definition stub
  get_copilot_studio_patterns   — Return CAT team best practices for CS topic authoring
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, List

from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.context_card_loader import load_context_card

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KB_DIR = os.path.join(REPO_ROOT, "customers", "mfg_coe", "knowledge_base")
CS_DIR = os.path.join(REPO_ROOT, "customers", "mfg_coe", "copilot-studio")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def _extract_topic_name(title: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9 ]", " ", title)
    words = [w.title() for w in clean.split() if len(w) > 2][:4]
    return " ".join(words) or "Mfg CoE Topic"


class MfgCoEPPDevAgent(BasicAgent):
    """Power Platform specialist — Copilot Studio topics, Power Automate flows, Power Apps."""

    def __init__(self):
        self.name = "MfgCoEPPDev"
        self.metadata = {
            "name": self.name,
            "description": (
                "Power Platform developer for the Mfg CoE. "
                "Generates Copilot Studio YAML topics (AdaptiveDialog, generative orchestration), "
                "Power Automate flow definitions (Skills kind for CS integration), "
                "Power Apps canvas app structure docs, and custom connector stubs. "
                "Follows CAT team best practices for CS topic authoring."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "execute_issue",
                            "generate_copilot_studio_topic",
                            "generate_power_automate_flow",
                            "generate_canvas_app_structure",
                            "generate_custom_connector",
                            "get_copilot_studio_patterns",
                        ],
                        "description": "Power Platform Dev action to perform",
                    },
                    "issue_title": {"type": "string"},
                    "issue_body": {"type": "string"},
                    "topic_name": {"type": "string", "description": "Copilot Studio topic display name"},
                    "flow_inputs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Flow input parameter names",
                    },
                    "flow_outputs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Flow output parameter names",
                    },
                    "prior_artifacts": {
                        "type": "object",
                        "description": "Artifacts from prior specialists (e.g., d365_dev entity schema)",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "execute_issue")
        handlers = {
            "execute_issue": self._execute_issue,
            "generate_copilot_studio_topic": self._generate_cs_topic,
            "generate_power_automate_flow": self._generate_pa_flow,
            "generate_canvas_app_structure": self._generate_canvas_app,
            "generate_custom_connector": self._generate_custom_connector,
            "get_copilot_studio_patterns": self._get_cs_patterns,
        }
        fn = handlers.get(action)
        if not fn:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return fn(**kwargs)
        except Exception as e:
            logger.error("PPDev %s failed: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    def _execute_issue(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        prior = kwargs.get("prior_artifacts", {})

        combined = (title + " " + body).lower()
        slug = _slug(title)
        os.makedirs(KB_DIR, exist_ok=True)

        parts = [
            f"# Power Platform Artifact — {title}",
            f"_Generated by MfgCoE PP Dev Agent | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_",
        ]

        # Always generate a CS topic
        topic_result = json.loads(self._generate_cs_topic(
            issue_title=title, issue_body=body, prior_artifacts=prior))
        parts.append("\n## Copilot Studio Topic\n")
        parts.append(topic_result.get("content", ""))

        # Generate PA flow if integration keywords present
        if any(kw in combined for kw in ["flow", "automate", "integrate", "call", "data", "lookup", "fetch"]):
            flow_result = json.loads(self._generate_pa_flow(
                issue_title=title, issue_body=body, prior_artifacts=prior))
            parts.append("\n## Power Automate Flow\n")
            parts.append(flow_result.get("content", ""))

        fname = f"pp_artifact_{slug}.md"
        fpath = os.path.join(KB_DIR, fname)
        artifact = "\n".join(parts)

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(artifact)

        rel_path = os.path.relpath(fpath, REPO_ROOT).replace("\\", "/")
        logger.info("PP artifact written to %s", rel_path)

        return json.dumps({
            "status": "artifact_written",
            "output_path": rel_path,
            "abs_path": fpath,
            "agent": "pp_dev",
            "content_preview": artifact[:500],
        }, indent=2)

    def _generate_cs_topic(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        prior = kwargs.get("prior_artifacts", {})
        topic_name = kwargs.get("topic_name") or _extract_topic_name(title)

        # Infer trigger queries from title words
        words = [w.lower() for w in re.sub(r"[^a-zA-Z0-9 ]", " ", title).split() if len(w) > 3]
        triggers = [
            title,
            f"help with {words[0] if words else 'request'}",
            f"I need {words[0] if words else 'help'}",
            f"show me {words[0] if words else 'information'}",
            f"what is {' '.join(words[:2]) if len(words) >= 2 else 'this'}",
        ]

        # Detect if we need a PA flow call
        combined = (title + " " + body).lower()
        needs_flow = any(kw in combined for kw in ["data", "lookup", "fetch", "search", "find", "get"])

        flow_action = ""
        if needs_flow:
            input_name = (words[0] if words else "query").replace(" ", "_")
            flow_action = f"""
    - kind: InvokeFlowAction
      id: callFlow
      input:
        binding:
          {input_name}: =Topic.UserInput
      output:
        binding:
          result: Topic.FlowResult
      # ⚠️  Set flowId to the Dataverse botcomponent GUID after connecting in CS UI
      flowId: REPLACE_WITH_BOTCOMPONENT_GUID
    - kind: SendActivity
      id: sendResult
      activity: |-
        Here's what I found: {{Topic.FlowResult}}"""

        yaml = f"""```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: {topic_name}
    triggerQueries:
{chr(10).join(f'      - {t}' for t in triggers)}

  actions:
    - kind: SendActivity
      id: welcome
      activity: |-
        I can help you with **{topic_name}**. Let me gather a few details.

    - kind: Question
      id: askInput
      interruptionPolicy:
        allowInterruption: true
      variable: Topic.UserInput
      prompt:
        text: What specifically would you like to know?
      entity:
        kind: TextPrebuiltEntity
{flow_action}
    - kind: SendActivity
      id: closing
      activity: |-
        Is there anything else I can help you with regarding {topic_name.lower()}?
```

> **Authoring notes (CAT team patterns):**
> - `allowInterruption: true` on every Question — required for generative orchestration
> - Set `flowId` to the Dataverse `botcomponentid` (NOT the Power Automate flow GUID)
> - Use agent-level instructions for disambiguation in multi-agent setups
> - After connecting a flow in CS UI, delete + re-add the Action node to refresh binding cache"""

        return json.dumps({"status": "ok", "topic_name": topic_name, "content": yaml})

    def _generate_pa_flow(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        prior = kwargs.get("prior_artifacts", {})
        flow_inputs = kwargs.get("flow_inputs", ["user_query"])
        flow_outputs = kwargs.get("flow_outputs", ["response_text", "record_id"])

        # Extract D365 entity from prior artifacts if available
        entity = "account"
        if prior.get("d365_dev"):
            d365_content = str(prior["d365_dev"])
            m = re.search(r"entity.*?`([a-z_]+)`", d365_content)
            if m:
                entity = m.group(1)

        # Build schema properties for inputs
        input_props = {}
        for inp in flow_inputs:
            input_props[inp] = {"type": "string", "title": inp.replace("_", " ").title()}
        required_inputs = flow_inputs

        # Build response schema properties for outputs
        output_props = {}
        for out in flow_outputs:
            output_props[out] = {
                "type": "string",
                "title": out.replace("_", " ").title(),
                "x-ms-dynamically-added": True,
            }

        flow_content = f"""### Power Automate Flow Definition — {title}

**Kind:** `LogicAppFlow` (Copilot Studio Skills trigger)
**Response action:** `Respond to the agent` (kind: Skills) — **must be set in Modern Designer UI**

> ⚠️  **Critical:** After creating this flow, open it in the **Modern Designer**
> (make.powerautomate.com, toggle "New designer" ON) and:
> 1. Delete and re-add the `Respond to the agent` action
> 2. Add each output via "Add an output" button as **Text** type
> 3. Save + Publish
> 4. In CS topic: delete + re-add the Action node to refresh binding cache

#### Trigger Schema
```json
{{
  "type": "object",
  "properties": {json.dumps(input_props, indent=4)},
  "required": {json.dumps(required_inputs)}
}}
```

#### Flow Steps
1. **Trigger** — When Copilot Studio calls this flow
   - Inputs: `{', '.join(f'`{i}`' for i in flow_inputs)}`

2. **Initialize** — Set up variables
   ```
   Set Variable: resultText = ""
   Set Variable: recordId = ""
   ```

3. **Query Dataverse** — List `{entity}s`
   ```
   GET {entity}s?$filter=contains(ascend_name, @{{triggerBody()?['user_query']}})&$select=ascend_name,{entity}id&$top=5
   ```

4. **Build Response** — Compose output
   ```
   response_text: @{{concat('Found: ', string(length(outputs('List_{entity.title()}s')?['body/value'])), ' records')}}
   record_id: @{{coalesce(first(outputs('List_{entity.title()}s')?['body/value'])?['{entity}id'], '')}}
   ```
   > Use `string()` to cast numbers — numeric types cause "Any" type binding errors in CS

5. **Respond to the agent** (Skills kind — set in Modern Designer)
   - Outputs: `{', '.join(f'`{o}`' for o in flow_outputs)}`

#### Response Schema (for RespondToCopilotStudio)
```json
{{
  "type": "object",
  "properties": {json.dumps(output_props, indent=4)}
}}
```
"""
        return json.dumps({"status": "ok", "content": flow_content})

    def _generate_canvas_app(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        content = f"""## Power Apps Canvas App — {title}

### Screen Structure
| Screen | Purpose | Key Controls |
|---|---|---|
| `scrHome` | Landing / navigation | `btnSearch`, `lblWelcome`, `galRecentItems` |
| `scrSearch` | Search + filter records | `txtSearch`, `galResults`, `btnFilter` |
| `scrDetail` | Record detail view | `frmRecord`, `btnEdit`, `btnBack` |
| `scrEdit` | Create / edit form | `frmEdit`, `btnSave`, `btnCancel` |

### Key Formulas
```powerfx
// Navigate to search
OnSelect of btnSearch:
Navigate(scrSearch, ScreenTransition.Fade)

// Load records from Dataverse
OnVisible of scrSearch:
ClearCollect(colResults, Filter('{title}s', Status = "Active"))

// Save record
OnSelect of btnSave:
If(IsBlank(frmEdit.Item),
    Patch('{title}s', Defaults('{title}s'), frmEdit.Updates),
    Patch('{title}s', frmEdit.Item, frmEdit.Updates)
);
Navigate(scrSearch, ScreenTransition.Back)
```

### Connection Requirements
- **Dataverse connector** — primary data source
- **Office 365 Users** — for current user context (`Office365Users.MyProfileV2()`)

### Accessibility & Responsive Design
- Use `App.Width` / `App.Height` for responsive layouts
- Target: Tablet (1366×768) and Mobile (375×812)
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_custom_connector(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        slug = _slug(title)
        content = f"""## Custom Connector — {title}

### Connector Definition (swagger.json stub)
```json
{{
  "swagger": "2.0",
  "info": {{
    "title": "{title} Connector",
    "description": "Custom connector for {title}",
    "version": "1.0"
  }},
  "host": "REPLACE_WITH_HOST",
  "basePath": "/api",
  "schemes": ["https"],
  "consumes": ["application/json"],
  "produces": ["application/json"],
  "paths": {{
    "/{slug}": {{
      "post": {{
        "operationId": "Execute{_slug(title).title().replace('_','')}",
        "summary": "Execute {title}",
        "parameters": [
          {{
            "name": "body",
            "in": "body",
            "required": true,
            "schema": {{"$ref": "#/definitions/Request"}}
          }}
        ],
        "responses": {{
          "200": {{
            "description": "Success",
            "schema": {{"$ref": "#/definitions/Response"}}
          }}
        }}
      }}
    }}
  }},
  "definitions": {{
    "Request": {{
      "type": "object",
      "properties": {{
        "query": {{"type": "string"}}
      }}
    }},
    "Response": {{
      "type": "object",
      "properties": {{
        "result": {{"type": "string"}},
        "status": {{"type": "string"}}
      }}
    }}
  }}
}}
```
"""
        return json.dumps({"status": "ok", "content": content})

    def _get_cs_patterns(self, **kwargs) -> str:
        content = """## Copilot Studio CAT Team Best Practices

### Topic Authoring
- `allowInterruption: true` on every Question node — required for generative orchestration to switch topics
- Use `triggerQueries` as semantic anchors even with generative orchestration
- Multi-line markdown in SendActivity: use YAML block scalar `|-`
- Power Fx interpolation: `{Topic.VarName}` inline in activity text

### Flow Binding (Biggest Pitfalls)
- `flowId` in topics = Dataverse `botcomponentid` (NOT Power Automate flow GUID)
- After changing flow schema: delete + re-add Action node (refresh doesn't clear binding cache)
- All flow outputs must be declared as **Text** in Modern Designer to avoid "Any" type errors
- Use `string(length(...))` not `length(...)` — numeric return types break CS variable binding
- `RespondToCopilotStudio` must have `kind: Skills` for outputs to appear in CS picker
- Both `body` AND `schema` parameters required on `RespondToCopilotStudio`

### Multi-Agent Disambiguation
- Use agent-level instructions instead of trigger phrase engineering for similar topics
- Agent instructions scale better than trigger keyword overlap

### Expressions
- `char(10)` is INVALID in PA — use `decodeUriComponent('%0A')` for newlines
- Use `coalesce(field?['value'], '')` to guard all optional Dataverse fields
- String-cast numbers: `string(length(collection))` not `length(collection)`
"""
        return json.dumps({"status": "ok", "content": content})
