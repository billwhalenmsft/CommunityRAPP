---
name: mfg-coe-skills
description: Best practices and framework guidance for Discrete Manufacturing CoE agents building Copilot Studio, D365, Power Platform, and RAPP artifacts.
---

# Mfg CoE Skills — Best Practices Reference

> **All CoE agents load this file before generating any code, configuration, or document.**
> Following these practices ensures consistency across all artifacts and alignment with Microsoft's recommended patterns.

---

## Copilot Studio (formerly Power Virtual Agents)

### Topic Structure
```yaml
# Every topic must have:
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: <Descriptive Name>
    triggerQueries:
      - <3-5 trigger phrases>
```

### Dialog Design Rules
1. **Always acknowledge** before asking a question — never start with a question
2. **Provide choices** where possible — `kind: Question` with `choices` reduces errors
3. **Handle not-found gracefully** — always have a fallback when lookups return empty
4. **Escalation path** — every topic must eventually route to `Escalate` if unresolved
5. **Variable naming** — use `Topic.VariableName` (PascalCase) consistently

### Power Automate Connection Pattern
```yaml
# Correct pattern for calling Power Automate from Copilot Studio
- kind: InvokeFlowAction
  id: callFlow
  flowId: <flow-id>
  input:
    key: !power-fx Topic.InputVariable
  output:
    Topic.OutputVariable: result
```

### Testing Checklist
- [ ] All trigger queries tested in Copilot Studio test pane
- [ ] Error paths tested (empty lookup, timeout, invalid input)
- [ ] Escalation path tested
- [ ] Playwright test script generated

---

## D365 Customer Service / Field Service

### Dataverse Web API Rules
1. Always use `$select` to limit returned fields — never `*`
2. Always use `$filter` with indexed fields (not free-text)
3. Use `OData-MaxVersion: 4.0` and `OData-Version: 4.0` headers
4. Prefer `PATCH` over `PUT` for updates
5. Use `@odata.bind` for relationship lookups

```python
# Correct: bound lookup
data = {
    "title": "Warranty Claim - Serial 12345",
    "customerid_account@odata.bind": f"/accounts({account_id})"
}

# Wrong: raw GUID assignment
data = {
    "customerid": account_id  # This will fail
}
```

### Entity Name Reference
| Friendly Name | Logical Name | API Path |
|---|---|---|
| Cases | incident | `incidents` |
| Accounts | account | `accounts` |
| Contacts | contact | `contacts` |
| Work Orders | msdyn_workorder | `msdyn_workorders` |
| Products | product | `products` |
| Cases (Activities) | activitypointer | `activitypointers` |

### Security Note
Never hard-code tenant IDs, client IDs, or secrets. Always read from environment variables:
```python
tenant_id = os.environ.get("D365_TENANT_ID")
client_id = os.environ.get("D365_CLIENT_ID")
```

---

## RAPP Agent Pattern

### Required Structure
```python
from agents.basic_agent import BasicAgent
import json

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyAgent'
        self.metadata = {
            "name": self.name,
            "description": "Clear, one-sentence description for OpenAI function calling",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["action1", "action2"],  # Always use enum
                        "description": "The action to perform"
                    },
                    "param1": {
                        "type": "string",
                        "description": "Description of what this parameter does"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action', '')
        handlers = {
            "action1": self._action1,
            "action2": self._action2,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _action1(self, **kwargs):
        # Implementation
        return json.dumps({"status": "success", "result": "..."})
```

### Common Mistakes to Avoid
- ❌ Returning `None` from `perform()` — always return `json.dumps()`
- ❌ Using `print()` — use `logging.info()` instead
- ❌ Hard-coding paths — use `Path(__file__).parent` for relative paths
- ❌ Missing try/except — every handler must catch exceptions
- ❌ Large descriptions — keep `description` under 100 characters for OpenAI

---

## Azure Storage (RAPP Pattern)

```python
from utils.storage_factory import get_storage_manager

storage = get_storage_manager()

# Write
storage.write_file('mfg_coe', 'backlog/idea_001.json', json.dumps(data))

# Read
content = storage.read_file('mfg_coe', 'backlog/idea_001.json')

# List (check if method exists before using)
files = storage.list_files('mfg_coe', prefix='backlog/')
```

---

## GitHub Issues API (via gh CLI)

```python
import subprocess
import json
import tempfile
import os

def create_issue(title: str, body: str, labels: list[str]) -> dict:
    """Create GitHub issue using gh CLI."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    tmp.write(body)
    tmp.close()
    try:
        result = subprocess.run([
            "gh", "issue", "create",
            "--repo", "kody-w/CommunityRAPP",
            "--title", title,
            "--body-file", tmp.name,
            "--label", ",".join(labels),
        ], capture_output=True, text=True)
        return {"success": result.returncode == 0, "output": result.stdout.strip()}
    finally:
        os.unlink(tmp.name)
```

---

## Outcome Mapping

Every artifact produced by the CoE must answer:
1. **What outcome does this deliver?** (customer-facing value)
2. **Which customer scenario does it apply to?** (Navico/Otis/Zurn/etc.)
3. **How is success measured?** (KPI, metric, demo success criteria)

Include this in every SOP, use case definition, and agent description:
```markdown
## Customer Outcome
**Delivers:** [Specific measurable benefit]
**Scenario:** [Customer name + scenario]
**Success metric:** [How we measure it worked]
```

---

## Microsoft AI / Responsible AI

Always include in any AI-powered demos:
1. **Transparency** — tell the user they're talking to an AI
2. **Handoff** — always provide a path to a human agent
3. **Data privacy** — don't collect PII beyond what's needed
4. **Grounding** — when using RAG, cite sources

---

## Naming Conventions

| Artifact Type | Convention | Example |
|---|---|---|
| RAPP agent file | `{context}_{function}_agent.py` | `navico_warranty_agent.py` |
| CoE agent file | `mfg_coe_{persona}_agent.py` | `mfg_coe_sme_agent.py` |
| SOP file | `sop_{process_area}_{name}.md` | `sop_warranty_claim_intake.md` |
| Use case file | `usecase_{id}_{slug}.json` | `usecase_001_warranty_selfservice.json` |
| Copilot Studio topic | PascalCase | `WarrantyCheck`, `RMARequest` |
| D365 custom fields | `bw_` prefix | `bw_warrantyexpirydate` |
