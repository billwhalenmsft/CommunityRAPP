"""
Agent: MfgCoE Analytics & Reporting Developer
Purpose: Generalist analytics and reporting specialist for the Mfg CoE.
         Picks the RIGHT reporting tool for the audience and use case — not just Power BI.
         Covers Power BI, D365 built-in dashboards, Excel/Power Query templates,
         Azure Monitor workbooks, embedded analytics (Power BI Embedded, Power Apps),
         paginated reports, reporting APIs, and data export pipelines.

Actions:
  execute_issue            — Full build: parse issue → generate analytics artifacts → write to disk
  recommend_tool           — Recommend the best reporting tool for a given use case/audience
  generate_report_spec     — Report design spec (fields, filters, visuals, audience)
  generate_d365_dashboard  — D365 model-driven app dashboard XML stub
  generate_power_bi_stub   — Power BI dataset description + DAX/Power Query stubs
  generate_excel_template  — Excel/Power Query template description
  generate_azure_monitor   — Azure Monitor workbook or App Insights dashboard spec
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

# Tool selection matrix
REPORTING_TOOLS = {
    "d365_dashboard": {
        "display": "D365 Model-Driven Dashboard",
        "best_for": "Sales/service managers who live in D365 CE all day",
        "audience": "internal_d365_users",
        "signals": ["d365", "dynamics", "crm", "case", "account", "queue", "model-driven",
                    "sales manager", "service manager", "pipeline"],
        "pros": ["Zero extra license", "Native in D365", "Real-time Dataverse data"],
        "cons": ["Limited chart types", "No cross-system data"],
    },
    "power_bi": {
        "display": "Power BI Report / Dashboard",
        "best_for": "KPI dashboards shared broadly, cross-system data, executive views",
        "audience": "executives_broad_teams",
        "signals": ["power bi", "kpi", "executive", "leadership", "cross-system", "trend",
                    "scorecard", "semantic model", "dax", "report distribution"],
        "pros": ["Rich visuals", "Cross-source data", "Scheduled refresh", "Mobile app"],
        "cons": ["Requires Pro/Premium license for sharing", "Setup time"],
    },
    "excel_power_query": {
        "display": "Excel / Power Query Template",
        "best_for": "One-off analysis, ad-hoc requests, field teams without BI tools",
        "audience": "field_teams_analysts",
        "signals": ["excel", "spreadsheet", "ad-hoc", "one-off", "analyst", "field team",
                    "export", "csv", "pivot", "power query"],
        "pros": ["Everyone has Excel", "Flexible manipulation", "No extra setup"],
        "cons": ["Manual refresh", "Not real-time", "Version control issues"],
    },
    "power_apps_embedded": {
        "display": "Power Apps + Embedded Analytics",
        "best_for": "Actionable dashboards where users can take action alongside the data",
        "audience": "frontline_workers_app_users",
        "signals": ["power apps", "embedded", "canvas", "actionable", "frontline",
                    "mobile app", "take action", "in-app"],
        "pros": ["Action + data in one place", "Works on mobile", "D365/Dataverse native"],
        "cons": ["More dev effort", "Power Apps license required"],
    },
    "azure_monitor": {
        "display": "Azure Monitor / App Insights Workbook",
        "best_for": "Technical/operational dashboards: agent performance, API health, CoE pipeline metrics",
        "audience": "devops_technical_teams",
        "signals": ["azure monitor", "app insights", "application insights", "workbook",
                    "telemetry", "logs", "metrics", "performance", "health", "pipeline",
                    "function app", "api calls", "error rate", "latency"],
        "pros": ["Built into Azure", "KQL queries", "Real-time logs", "No extra license"],
        "cons": ["Technical audience only", "Requires Azure Monitor setup"],
    },
    "copilot_studio_adaptive_card": {
        "display": "Copilot Studio Adaptive Card Report",
        "best_for": "Conversational reports delivered in Teams — ask a question, get a formatted card",
        "audience": "teams_chat_users",
        "signals": ["teams", "chat", "conversational", "ask me", "adaptive card", "on demand",
                    "bot report", "quick summary"],
        "pros": ["In Teams where users already are", "On-demand not scheduled", "No BI license"],
        "cons": ["Limited to card format", "Not explorable/interactive"],
    },
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def _recommend_tool(title: str, body: str) -> List[str]:
    """Return ordered list of recommended tools based on issue signals."""
    combined = (title + " " + body).lower()
    scored = []
    for key, tool in REPORTING_TOOLS.items():
        score = sum(1 for kw in tool["signals"] if kw in combined)
        if score > 0:
            scored.append((score, key))
    scored.sort(reverse=True)
    if not scored:
        # Default for Mfg CoE: D365 dashboard first, then Power BI
        return ["d365_dashboard", "power_bi"]
    return [k for _, k in scored[:3]]


class MfgCoEAnalyticsDevAgent(BasicAgent):
    """Analytics & Reporting generalist — picks the right tool, generates specs and stubs."""

    def __init__(self):
        self.name = "MfgCoEAnalyticsDev"
        self.metadata = {
            "name": self.name,
            "description": (
                "Analytics and reporting generalist for the Mfg CoE. "
                "Recommends the right reporting tool (D365 dashboard, Power BI, Excel, "
                "Power Apps embedded, Azure Monitor, Copilot Studio Adaptive Card) based on "
                "audience and use case. Generates report specs, DAX/Power Query stubs, "
                "D365 dashboard configs, and Azure Monitor workbook definitions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "execute_issue",
                            "recommend_tool",
                            "generate_report_spec",
                            "generate_d365_dashboard",
                            "generate_power_bi_stub",
                            "generate_excel_template",
                            "generate_azure_monitor",
                        ],
                        "description": "Analytics Dev action to perform",
                    },
                    "issue_title": {"type": "string"},
                    "issue_body": {"type": "string"},
                    "audience": {
                        "type": "string",
                        "description": "Target audience (e.g. 'sales manager', 'executive', 'field tech')",
                    },
                    "prior_artifacts": {
                        "type": "object",
                        "description": "Artifacts from prior specialists",
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
            "recommend_tool": self._recommend_tool_action,
            "generate_report_spec": self._generate_report_spec,
            "generate_d365_dashboard": self._generate_d365_dashboard,
            "generate_power_bi_stub": self._generate_power_bi_stub,
            "generate_excel_template": self._generate_excel_template,
            "generate_azure_monitor": self._generate_azure_monitor,
        }
        fn = handlers.get(action)
        if not fn:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return fn(**kwargs)
        except Exception as e:
            logger.error("AnalyticsDev %s failed: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    def _execute_issue(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        prior = kwargs.get("prior_artifacts", {})

        slug = _slug(title)
        recommended_tools = _recommend_tool(title, body)
        os.makedirs(KB_DIR, exist_ok=True)

        parts = [
            f"# Analytics & Reporting Artifact — {title}",
            f"_Generated by MfgCoE Analytics Dev Agent | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_",
            f"",
        ]

        # Tool recommendation first
        rec_result = json.loads(self._recommend_tool_action(issue_title=title, issue_body=body))
        parts.append("## Tool Recommendation\n")
        parts.append(rec_result.get("content", ""))

        # Generate report spec
        spec_result = json.loads(self._generate_report_spec(
            issue_title=title, issue_body=body, recommended_tools=recommended_tools, prior_artifacts=prior))
        parts.append("\n## Report Specification\n")
        parts.append(spec_result.get("content", ""))

        # Generate artifact for primary recommended tool
        primary_tool = recommended_tools[0] if recommended_tools else "d365_dashboard"
        if primary_tool == "d365_dashboard":
            tool_result = json.loads(self._generate_d365_dashboard(issue_title=title, issue_body=body))
        elif primary_tool == "power_bi":
            tool_result = json.loads(self._generate_power_bi_stub(issue_title=title, issue_body=body))
        elif primary_tool == "excel_power_query":
            tool_result = json.loads(self._generate_excel_template(issue_title=title, issue_body=body))
        elif primary_tool == "azure_monitor":
            tool_result = json.loads(self._generate_azure_monitor(issue_title=title, issue_body=body))
        else:
            tool_result = json.loads(self._generate_report_spec(issue_title=title, issue_body=body))

        parts.append(f"\n## {REPORTING_TOOLS.get(primary_tool, {}).get('display', 'Implementation')} Artifact\n")
        parts.append(tool_result.get("content", ""))

        fname = f"analytics_artifact_{slug}.md"
        fpath = os.path.join(KB_DIR, fname)
        artifact = "\n".join(parts)

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(artifact)

        rel_path = os.path.relpath(fpath, REPO_ROOT).replace("\\", "/")
        logger.info("Analytics artifact written to %s", rel_path)

        return json.dumps({
            "status": "artifact_written",
            "output_path": rel_path,
            "abs_path": fpath,
            "agent": "analytics_dev",
            "recommended_tools": recommended_tools,
            "primary_tool": primary_tool,
            "content_preview": artifact[:500],
        }, indent=2)

    def _recommend_tool_action(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        tools = _recommend_tool(title, body)

        rows = []
        for i, key in enumerate(tools):
            t = REPORTING_TOOLS.get(key, {})
            rank = "✅ **Primary**" if i == 0 else f"#{i+1} Alternative"
            rows.append(f"| {rank} | **{t.get('display', key)}** | {t.get('best_for', '')} |")

        content = (
            "| Rank | Tool | Best For |\n"
            "|---|---|---|\n"
            + "\n".join(rows)
            + "\n\n> Tool selection is based on audience signals in the issue. "
            "Override by specifying the tool explicitly."
        )
        return json.dumps({"status": "ok", "recommended": tools, "content": content})

    def _generate_report_spec(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        body = kwargs.get("issue_body", "")
        recommended_tools = kwargs.get("recommended_tools") or _recommend_tool(title, body)
        prior = kwargs.get("prior_artifacts", {})

        # Extract entity context from D365 Dev artifacts if available
        entity_context = ""
        if prior.get("d365_dev"):
            entity_context = f"\n> **D365 Entity Context:** See D365 Dev artifact for field names and record IDs."

        primary = recommended_tools[0] if recommended_tools else "d365_dashboard"
        tool_name = REPORTING_TOOLS.get(primary, {}).get("display", "Report")

        content = f"""### Report Specification — {title}
{entity_context}

**Recommended Tool:** {tool_name}

| Property | Value |
|---|---|
| Report Name | {title} |
| Tool | {tool_name} |
| Refresh Frequency | Daily (adjust as needed) |
| Target Audience | See tool recommendation above |
| Data Source | D365 CE (Master CE Mfg — `https://orgecbce8ef.crm.dynamics.com/`) |

#### Key Metrics / KPIs
| Metric | Calculation | Visualization |
|---|---|---|
| Total Count | `COUNT(records)` | Card / Big number |
| Status Breakdown | `COUNT by Status` | Donut / Bar chart |
| Trend (30d) | `COUNT by Day (last 30 days)` | Line chart |
| Top 5 by Volume | `TOP 5 GROUP BY Name` | Horizontal bar |

#### Filters / Slicers
- **Date Range** — Created On (default: last 30 days)
- **Status** — Active / Inactive / Pending
- **Owner** — Assigned user (optional)
- **Region / Territory** — If applicable

#### Drill-Through
- Click any bar/row → opens filtered detail view
- Detail shows: Name, Status, Created Date, Owner, Last Modified

#### Data Refresh
- Source: Dataverse OData endpoint
- Credentials: Service principal (avoid user-based auth for scheduled refresh)
- Refresh: Daily at 6 AM local time
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_d365_dashboard(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")
        slug = _slug(title)

        content = f"""### D365 Model-Driven Dashboard — {title}

**Where:** Settings → Dashboards → New → Dynamics 365 Dashboard

#### Layout: 2-column, 3-row grid
| Position | Component | Configuration |
|---|---|---|
| Top Left | Chart — Status Breakdown | Entity: target entity, Chart: Donut by Status |
| Top Right | Chart — Trend (30d) | Entity: target entity, Chart: Line by Created On |
| Mid Left | List — Active Records | View: "Active Records", Columns: Name, Status, Owner, Created On |
| Mid Right | Chart — Top Owners | Entity: target entity, Chart: Bar by Owner |
| Bottom | List — Recently Modified | View: "Recently Modified (7d)", Columns: Name, Modified On, Status |

#### System Dashboard XML Stub (for solution import)
```xml
<Dashboard>
  <Name>{title} Dashboard</Name>
  <Description>KPI dashboard for {title.lower()} — auto-generated by CoE Analytics Agent</Description>
  <Columns>2</Columns>
  <Rows>3</Rows>
  <Sections>
    <!-- Add FormXML sections here after designing in D365 UI -->
    <!-- Export via Solutions > Export > customizations.xml -->
  </Sections>
</Dashboard>
```

> **Tip:** Build the dashboard in D365 UI first (faster), then export via Solution to get the XML.
> Include in solution: `AscendMfgCoE_{slug.title()}` | Publisher: `ascend_`

#### Required Views (create these first)
1. `Active {title}s` — filter: `statecode eq 0`, sort: `createdon desc`
2. `Recently Modified (7d)` — filter: `modifiedon ge [today-7]`
3. `By Owner` — group by: `ownerid`
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_power_bi_stub(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")

        content = f"""### Power BI Report Stub — {title}

#### Semantic Model (dataset)

**Data Source:** Dataverse OData
```
URL: https://orgecbce8ef.crm.dynamics.com/api/data/v9.2/
Auth: OAuth2 / Service Principal (App Registration)
Tables to import:
  - [target_entity]s  → main fact table
  - systemusers       → for owner lookups
  - teams             → for team grouping
```

#### Power Query (M) — Base Table
```powerquery
let
    Source = OData.Feed(
        "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2/",
        null,
        [ODataVersion = 4, MoreColumns = true]
    ),
    Entity = Source{{[Name="[target_entity]s"]}}[Data],
    Filtered = Table.SelectRows(Entity, each [statecode] = 0),
    Selected = Table.SelectColumns(Filtered, {{
        "ascend_name", "ascend_status", "ownerid", "createdon", "modifiedon"
    }})
in
    Selected
```

#### Key DAX Measures
```dax
Total Records = COUNTROWS('[target_entity]s')

Active Records = 
    CALCULATE(COUNTROWS('[target_entity]s'), '[target_entity]s'[statecode] = 0)

Created Last 30d = 
    CALCULATE(
        COUNTROWS('[target_entity]s'),
        '[target_entity]s'[createdon] >= TODAY() - 30
    )

% Active = DIVIDE([Active Records], [Total Records], 0)
```

#### Report Pages
1. **Overview** — Cards (Total, Active, Created 30d), Trend line, Status donut
2. **Detail** — Filterable table with all records + drill-through
3. **Owner Breakdown** — Bar chart by owner + pie by team

#### License Note
- **Power BI Pro** required for sharing outside of workspace
- **Power BI Embedded** (A-SKU) for embedding in Power Apps or custom web pages
- Workspace: Publish to a shared workspace, NOT "My Workspace"
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_excel_template(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")

        content = f"""### Excel / Power Query Template — {title}

**Use case:** Ad-hoc analysis or for users without Power BI Pro licenses.

#### Workbook Structure
| Sheet | Purpose |
|---|---|
| `Data` | Raw export from D365 (hidden, auto-refreshed) |
| `Summary` | Pivot tables + charts |
| `Filters` | Slicer controls (date range, status, owner) |
| `Instructions` | How to refresh and use the template |

#### Power Query Connection (in Excel: Data → Get Data → From OData Feed)
```
URL: https://orgecbce8ef.crm.dynamics.com/api/data/v9.2/[target_entity]s
Auth: Organizational Account (user's M365 credentials)
Query: $filter=statecode eq 0&$select=ascend_name,ascend_status,ownerid,createdon&$top=5000
```

#### Key Formulas (Summary sheet)
```excel
=COUNTIFS(Data[ascend_status], "Active")           ' Count active
=AVERAGEIFS(Data[ascend_amount], Data[statecode], 0) ' Avg amount (active)
=MAXIFS(Data[createdon], Data[ownerid], A2)         ' Latest by owner
```

#### Pivot Table Setup
- Rows: `ascend_status` or `ownerid`
- Values: `COUNT of ascend_name`, `SUM of ascend_amount`
- Filters: `createdon` (date range slicer)

#### Refresh Instructions (for end users)
1. Open the workbook
2. Click **Data → Refresh All**
3. Sign in with your Microsoft 365 account if prompted
4. Pivot tables and charts update automatically

> **Distribution:** Share via SharePoint/OneDrive (not email attachment)
> so everyone uses the same live-connected version.
"""
        return json.dumps({"status": "ok", "content": content})

    def _generate_azure_monitor(self, **kwargs) -> str:
        title = kwargs.get("issue_title", "")

        content = f"""### Azure Monitor Workbook — {title}

**Use case:** Technical/operational monitoring — CoE pipeline health, agent performance, API metrics.

#### Workbook Sections

**Section 1: Request Volume**
```kusto
// App Insights — Requests over time
requests
| where timestamp > ago(7d)
| summarize count() by bin(timestamp, 1h), name
| render timechart
```

**Section 2: Error Rate**
```kusto
// Failures + success rate
requests
| where timestamp > ago(24h)
| summarize
    Total    = count(),
    Failed   = countif(success == false),
    SuccessRate = round(100.0 * countif(success == true) / count(), 1)
| extend Label = "{title} - Last 24h"
```

**Section 3: CoE Agent Execution Logs**
```kusto
// Custom events from CoE runner
customEvents
| where timestamp > ago(7d)
| where name startswith "CoE_"
| extend IssueNumber = tostring(customDimensions["issue_number"])
| extend Status      = tostring(customDimensions["status"])
| summarize count() by Status, bin(timestamp, 1d)
| render barchart
```

**Section 4: GitHub Actions Runs**
```kusto
// If GHA run IDs are logged as custom dimensions
customEvents
| where name == "CoE_PipelineRun"
| project timestamp, IssueNumber = customDimensions["issue_number"],
          RunId = customDimensions["run_id"], Status = customDimensions["status"]
| order by timestamp desc
| take 50
```

#### Workbook Parameters
- `TimeRange` — Parameter type: Time Range, default: Last 7 days
- `IssueStatus` — Drop-down: all / needs-bill / done / blocked

#### Deploy
```bash
# Via Azure CLI (after exporting workbook JSON from portal)
az monitor app-insights workbook create \\
  --resource-group REPLACE_RG \\
  --display-name "{title} Dashboard" \\
  --category workbook \\
  --serialized-data @workbook.json
```
"""
        return json.dumps({"status": "ok", "content": content})
