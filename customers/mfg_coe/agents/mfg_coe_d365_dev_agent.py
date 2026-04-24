"""
Agent: MfgCoE D365 Dev Agent
Purpose: Dynamics 365 / Dataverse specialist for the Mfg CoE.
         Generates Dataverse entity schemas, PowerShell provisioning scripts,
         OData query examples, D365 solution overviews, and Copilot-in-D365 configs.
         Always reads the Master CE Mfg and Mfg Gold Template context cards before
         generating any D365-targeted artifacts.

Actions:
  execute_issue           — Full build: parse issue → generate D365 artifacts → write to disk
  generate_entity_schema  — Dataverse entity + field definitions (JSON)
  generate_provisioning   — PowerShell provisioning script (numbered, DataverseHelper-compatible)
  generate_odata_queries  — OData filter/expand examples for a given entity
  generate_solution_overview — D365 solution component overview markdown
  get_environment_context — Return the current Master CE Mfg / Gold Template env details
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
D365_SCRIPTS_DIR = os.path.join(REPO_ROOT, "d365", "scripts")

# Common Dataverse field types
FIELD_TYPES = {
    "string": {"xsd": "xs:string", "pa": "Text", "odata": "Edm.String"},
    "int": {"xsd": "xs:int", "pa": "Whole Number", "odata": "Edm.Int32"},
    "decimal": {"xsd": "xs:decimal", "pa": "Decimal", "odata": "Edm.Decimal"},
    "datetime": {"xsd": "xs:dateTime", "pa": "Date and Time", "odata": "Edm.DateTimeOffset"},
    "bool": {"xsd": "xs:boolean", "pa": "Two Options", "odata": "Edm.Boolean"},
    "lookup": {"xsd": "xs:string", "pa": "Lookup", "odata": "Edm.Guid"},
    "choice": {"xsd": "xs:int", "pa": "Choice", "odata": "Edm.Int32"},
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def _detect_entity(title: str, body: str) -> str:
    """Guess the primary D365 entity from issue text."""
    combined = (title + " " + body).lower()
    entity_map = {
        "incident": ["case", "incident", "ticket", "support request"],
        "account": ["account", "customer", "company", "distributor"],
        "contact": ["contact", "person", "user", "rep"],
        "product": ["product", "item", "sku", "part"],
        "queue": ["queue", "routing", "assignment", "work item"],
        "opportunity": ["opportunity", "deal", "pipeline", "forecast"],
        "order": ["order", "sales order", "purchase order"],
        "msdyn_workorder": ["work order", "field service", "technician"],
    }
    for entity, keywords in entity_map.items():
        if any(kw in combined for kw in keywords):
            return entity
    return "account"  # sensible mfg default


class MfgCoED365DevAgent(BasicAgent):
    """D365 / Dataverse specialist — generates entity schemas, provisioning scripts, and OData queries."""

    def __init__(self):
        self.name = "MfgCoED365Dev"
        self.metadata = {
            "name": self.name,
            "description": (
                "Dynamics 365 / Dataverse developer for the Mfg CoE. "
                "Generates Dataverse entity schemas, PowerShell provisioning scripts "
                "(DataverseHelper-compatible), OData query examples, and solution component "
                "overviews. Always uses Master CE Mfg and Mfg Gold Template environment context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "execute_issue",
                            "generate_entity_schema",
                            "generate_provisioning",
                            "generate_odata_queries",
                            "generate_solution_overview",
                            "get_environment_context",
                        ],
                        "description": "D365 Dev action to perform",
                    },
                    "issue_title": {"type": "string"},
                    "issue_body": {"type": "string"},
                    "entity_name": {"type": "string", "description": "Dataverse logical entity name"},
                    "fields": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Field definitions [{name, type, description}]",
                    },
                    "prior_artifacts": {
                        "type": "object",
                        "description": "Artifacts from prior specialists, keyed by discipline",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)
        self._master_ctx = None
        self._gold_ctx = None

    def _load_env_context(self):
        if not self._master_ctx:
            self._master_ctx = load_context_card("master_ce_mfg") or ""
        if not self._gold_ctx:
            self._gold_ctx = load_context_card("mfg_gold_template") or ""

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "execute_issue")
        handlers = {
            "execute_issue": self._execute_issue,
            "generate_entity_schema": self._generate_entity_schema,
            "generate_provisioning": self._generate_provisioning,
            "generate_odata_queries": self._generate_odata_queries,
            "generate_solution_overview": self._generate_solution_overview,
            "get_environment_context": self._get_environment_context,
        }
        fn = handlers.get(action)
        if not fn:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return fn(**kwargs)
        except Exception as e:
            logger.error("D365Dev %s failed: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    def _execute_issue(self, **kwargs) -> str:
        """Full build: parse issue, generate D365 artifacts, write to disk."""
        self._load_env_context()
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")

        entity = _detect_entity(title, body)
        slug = _slug(title)
        out_dir = os.path.join(KB_DIR)
        os.makedirs(out_dir, exist_ok=True)

        # Generate entity schema
        schema_result = json.loads(self._generate_entity_schema(
            entity_name=entity, issue_title=title, issue_body=body))
        schema_content = schema_result.get("content", "")

        # Generate provisioning script
        prov_result = json.loads(self._generate_provisioning(
            entity_name=entity, issue_title=title, issue_body=body))
        prov_content = prov_result.get("content", "")

        # Write combined artifact
        fname = f"d365_artifact_{slug}.md"
        fpath = os.path.join(out_dir, fname)
        artifact = "\n\n---\n\n".join([
            f"# D365 Artifact — {title}",
            f"_Generated by MfgCoE D365 Dev Agent | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_",
            f"**Primary Entity:** `{entity}`",
            "",
            "## Entity Schema",
            schema_content,
            "",
            "## Provisioning Script",
            prov_content,
        ])

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(artifact)

        rel_path = os.path.relpath(fpath, REPO_ROOT).replace("\\", "/")
        logger.info("D365 artifact written to %s", rel_path)

        return json.dumps({
            "status": "artifact_written",
            "output_path": rel_path,
            "abs_path": fpath,
            "agent": "d365_dev",
            "entity": entity,
            "content_preview": artifact[:500],
        }, indent=2)

    def _generate_entity_schema(self, **kwargs) -> str:
        entity = kwargs.get("entity_name", "account")
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        combined = (title + " " + body).lower()

        # Infer relevant fields from issue text
        base_fields = [
            {"name": f"ascend_name", "type": "string", "required": True, "description": "Primary name"},
            {"name": f"ascend_status", "type": "choice", "required": False, "description": "Status (Active/Inactive/Pending)"},
            {"name": f"ascend_description", "type": "string", "required": False, "description": "Description or notes"},
            {"name": f"ascend_created_date", "type": "datetime", "required": False, "description": "Record creation date"},
        ]
        # Add contextual fields based on keywords
        if any(kw in combined for kw in ["cost", "price", "amount", "revenue", "budget"]):
            base_fields.append({"name": "ascend_amount", "type": "decimal", "required": False, "description": "Financial amount"})
        if any(kw in combined for kw in ["priority", "severity", "urgency"]):
            base_fields.append({"name": "ascend_priority", "type": "choice", "required": False, "description": "Priority (High/Medium/Low)"})
        if any(kw in combined for kw in ["assign", "owner", "rep", "manager"]):
            base_fields.append({"name": "ascend_owner_id", "type": "lookup", "required": False, "description": "Lookup to SystemUser"})
        if any(kw in combined for kw in ["product", "sku", "part", "item"]):
            base_fields.append({"name": "ascend_product_id", "type": "lookup", "required": False, "description": "Lookup to Product"})

        schema_lines = [
            f"### Entity: `{entity}` (prefix: `ascend_`)",
            f"",
            f"| Field (Logical Name) | Type | Required | Description |",
            f"|---|---|---|---|",
        ]
        for fld in base_fields:
            req = "✅" if fld["required"] else ""
            schema_lines.append(f"| `{fld['name']}` | {FIELD_TYPES[fld['type']]['pa']} | {req} | {fld['description']} |")

        schema_lines += [
            f"",
            f"#### OData Logical Name",
            f"`{entity}s` (plural) — e.g. `GET {entity}s?$select=ascend_name,ascend_status`",
            f"",
            f"#### Relationships",
            f"- `{entity}_systemuser` — Owner lookup (SystemUser)",
            f"- Standard audit fields: `createdon`, `modifiedon`, `createdby`, `modifiedby`",
        ]

        content = "\n".join(schema_lines)
        return json.dumps({"status": "ok", "entity": entity, "fields": base_fields, "content": content})

    def _generate_provisioning(self, **kwargs) -> str:
        entity = kwargs.get("entity_name", "account")
        title = kwargs.get("issue_title", "D365 Setup")

        script = f"""# PowerShell Provisioning Script — {title}
# Compatible with DataverseHelper.psm1 pattern (d365/scripts/)
# Target: Master CE Mfg | Org ID: a3140474-230b-ee2b-8dd8-605a8fe08913
# URL: https://orgecbce8ef.crm.dynamics.com/

[CmdletBinding()]
param(
    [string]$Customer = "mfg_coe",
    [string]$OrgUrl   = "https://orgecbce8ef.crm.dynamics.com"
)

Import-Module "$PSScriptRoot/DataverseHelper.psm1" -Force

Write-Host "[{title}] Starting D365 provisioning..." -ForegroundColor Cyan

# ── Authenticate ──────────────────────────────────────────────────────────────
$Token = az account get-access-token --resource $OrgUrl --query accessToken -o tsv
$Headers = @{{ Authorization = "Bearer $Token"; "Content-Type" = "application/json" }}
$BaseUrl = "$OrgUrl/api/data/v9.2"

# ── Helper: Find or Create Record ─────────────────────────────────────────────
function Ensure-Record {{
    param([string]$EntitySet, [hashtable]$SearchFilter, [hashtable]$Body)
    $filter = ($SearchFilter.GetEnumerator() | ForEach-Object {{ "$($_.Key) eq '$($_.Value)'" }}) -join " and "
    $existing = Invoke-RestMethod "$BaseUrl/${{EntitySet}}?`$filter=$filter&`$select=$(($Body.Keys) -join ',')" -Headers $Headers
    if ($existing.value.Count -gt 0) {{
        Write-Host "  EXISTS: $EntitySet / $($existing.value[0].$(($SearchFilter.Keys)[0]))" -ForegroundColor Yellow
        return $existing.value[0]
    }}
    $created = Invoke-RestMethod "$BaseUrl/$EntitySet" -Method Post -Headers $Headers -Body (ConvertTo-Json $Body -Depth 5)
    Write-Host "  CREATED: $EntitySet" -ForegroundColor Green
    return $created
}}

# ── Step 1: Create/Verify Primary Records ────────────────────────────────────
Write-Host "`n[Step 1] Setting up {entity} records..." -ForegroundColor White

$sampleRecord = Ensure-Record `
    -EntitySet "{entity}s" `
    -SearchFilter @{{ ascend_name = "{title} Sample" }} `
    -Body @{{
        ascend_name        = "{title} Sample"
        ascend_status      = 100000000  # Active
        ascend_description = "Sample record created by CoE provisioning script"
    }}

Write-Host "`n[{title}] Provisioning complete." -ForegroundColor Green
Write-Host "Record ID: $($sampleRecord.{entity}id)"
"""
        return json.dumps({"status": "ok", "entity": entity, "content": script})

    def _generate_odata_queries(self, **kwargs) -> str:
        entity = kwargs.get("entity_name", "account")
        base_url = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"
        content = f"""## OData Query Examples — `{entity}`

**Base URL:** `{base_url}`

### List records (active only)
```
GET {base_url}/{entity}s?$filter=statecode eq 0&$select=ascend_name,ascend_status&$top=50
```

### Filter by status
```
GET {base_url}/{entity}s?$filter=ascend_status eq 100000000&$select=ascend_name,ascend_description
```

### Lookup with expand
```
GET {base_url}/{entity}s?$expand=ownerid($select=fullname)&$select=ascend_name
```

### Single record by GUID
```
GET {base_url}/{entity}s({{RECORD_GUID}})?$select=ascend_name,ascend_status,createdon
```

### Create (POST)
```json
POST {base_url}/{entity}s
{{
  "ascend_name": "Test Record",
  "ascend_status": 100000000
}}
```

### Update (PATCH)
```json
PATCH {base_url}/{entity}s({{RECORD_GUID}})
{{
  "ascend_status": 100000001
}}
```
"""
        return json.dumps({"status": "ok", "entity": entity, "content": content})

    def _generate_solution_overview(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "D365 Solution")
        entity = kwargs.get("entity_name", "account")
        content = f"""## D365 Solution Overview — {title}

| Component Type | Name | Description |
|---|---|---|
| Entity | `{entity}` | Primary data entity |
| Form | `{entity} Main Form` | Main data entry form |
| View | `Active {entity.title()}s` | Default active records view |
| Business Rule | `{entity.title()} Status Validation` | Enforce required fields by status |
| Workflow | `Notify on {entity.title()} Change` | Email alert on record update |
| Dashboard | `{title} Dashboard` | KPI tiles + embedded view |

### Solution Naming Convention
- **Publisher prefix:** `ascend_`
- **Solution name:** `AscendMfgCoE_{entity.title()}`
- **Version:** `1.0.0.0`

### Deployment Notes
- Deploy to **Mfg Gold Template** first for validation
- Use `pac solution export/import` for ALM
- Run provisioning script after import to seed data
"""
        return json.dumps({"status": "ok", "content": content})

    def _get_environment_context(self, **kwargs) -> str:
        self._load_env_context()
        return json.dumps({
            "status": "ok",
            "master_ce_mfg": {
                "env_id": "a3140474-230b-ee2b-8dd8-605a8fe08913",
                "url": "https://orgecbce8ef.crm.dynamics.com/",
                "type": "Production",
                "summary": self._master_ctx[:300] if self._master_ctx else "Not loaded",
            },
            "mfg_gold_template": {
                "env_id": "2404ccaf-d7e5-e1ff-863a-3ecbe2f0f013",
                "url": "https://org6feab6b5.crm.dynamics.com/",
                "type": "Trial (sandbox)",
                "summary": self._gold_ctx[:300] if self._gold_ctx else "Not loaded",
            },
        }, indent=2)
