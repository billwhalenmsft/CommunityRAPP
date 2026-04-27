"""
Minimal MCP Apps server scaffold for RAPP-generated agents.

This is the reference baseline that the RAPP transpiler will eventually
emit automatically as a 4th output of `transcript_to_agent`. See:
- README.md in this folder
- Tracking issue: kody-w/CommunityRAPP#58
- MCP Apps spec: https://modelcontextprotocol.io/extensions/apps/overview

Run locally:
    pip install -r requirements.txt
    python server.py

Then register the URL in M365 Agents Toolkit (VS Code):
    Add an Action -> Start with an MCP Server -> http://localhost:8000/mcp
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

WIDGETS_DIR = Path(__file__).parent / "widgets"

mcp = FastMCP(
    name="rapp-mcp-app-scaffold",
    instructions=(
        "Reference MCP Apps server generated from the RAPP scaffold. "
        "Replace these example tools with calls into your BasicAgent "
        "subclasses from agents/."
    ),
)


def _widget(template: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build the MCP-Apps `meta` payload that points at a widget HTML.

    MCP-Apps-aware clients (Copilot chat) render the widget inline using
    `widgetData`; legacy clients ignore `meta` and just show the text.
    """
    return {
        "openai/outputTemplate": f"ui://widget/{template}",
        "openai/widgetData": data,
    }


# ---- Resource: serve widget HTML files ------------------------------------

@mcp.resource("ui://widget/{name}")
def widget(name: str) -> str:
    path = WIDGETS_DIR / name
    if not path.is_file() or path.suffix != ".html":
        raise FileNotFoundError(f"Unknown widget: {name}")
    return path.read_text(encoding="utf-8")


# ---- Example tool: table widget -------------------------------------------

@mcp.tool()
async def list_items(query: str = "") -> dict[str, Any]:
    """List items as an inline table in Copilot chat.

    Replace the stub data with a call into your existing RAPP agent, e.g.:
        from agents.my_agent import MyAgent
        rows = MyAgent().perform(query=query)
    """
    rows = [
        {"id": "WO-1001", "plant": "Plano", "status": "Open", "priority": "High"},
        {"id": "WO-1002", "plant": "Plano", "status": "In Progress", "priority": "Med"},
        {"id": "WO-1003", "plant": "Austin", "status": "Closed", "priority": "Low"},
    ]
    summary = f"Found {len(rows)} items matching '{query or 'all'}'."
    return {
        "content": [TextContent(type="text", text=summary).model_dump()],
        "_meta": _widget("table.html", {"title": "Work Orders", "rows": rows}),
        "structuredContent": {"rows": rows},
    }


# ---- Example tool: KPI widget ---------------------------------------------

@mcp.tool()
async def get_kpis() -> dict[str, Any]:
    """Return summary KPIs as an inline tile widget."""
    kpis = [
        {"label": "Open WOs", "value": 42},
        {"label": "OEE", "value": "78%"},
        {"label": "First Pass Yield", "value": "94%"},
    ]
    return {
        "content": [TextContent(
            type="text",
            text=json.dumps({k["label"]: k["value"] for k in kpis}),
        ).model_dump()],
        "_meta": _widget("kpi.html", {"kpis": kpis}),
        "structuredContent": {"kpis": kpis},
    }


if __name__ == "__main__":
    # Streamable HTTP transport — required for MCP Apps clients
    mcp.run(transport="streamable-http")
