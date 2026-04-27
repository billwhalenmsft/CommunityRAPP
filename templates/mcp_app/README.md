# MCP App scaffold for RAPP-generated agents

> Reference scaffold for the **MCP Apps in Copilot Chat** target surface
> (announced Apr 2026 — see [the M365 dev blog post][post] and the
> [MCP Apps spec][spec]).
>
> This template is the manual baseline that the RAPP transpiler will
> eventually generate automatically as a 4th output of `transcript_to_agent`.
> See tracking issue: kody-w/CommunityRAPP#58.

[post]: https://devblogs.microsoft.com/microsoft365dev/mcp-apps-now-available-in-copilot-chat/
[spec]: https://modelcontextprotocol.io/extensions/apps/overview

## What you get

```
mcp_app/
├── server.py          # MCP server (FastMCP / official Python SDK)
├── widgets/
│   ├── table.html     # Reusable inline-table widget
│   ├── form.html      # Reusable input-form widget
│   └── kpi.html       # Reusable KPI tile widget
├── m365agents.yml     # Microsoft 365 Agents Toolkit manifest
├── requirements.txt
└── README.md          # this file
```

## Why this matters

This is the first surface that lets RAPP-generated agents **skip the
Power Automate flow + Copilot Studio binding-cache pain entirely** while
still landing in M365 Copilot chat. Same Entra ID auth as our existing
Azure Functions deployment — the MCP server is just another endpoint
behind the same identity story.

| Today (Copilot Studio path) | With MCP Apps |
|---|---|
| Python agent → Copilot Studio YAML → Power Automate flow → Azure Function | Python agent → MCP server → Copilot chat |
| Stale flow-binding cache requires manual UI refresh | No flow layer at all |
| Text/markdown responses only in chat | Rich HTML widgets inline (sandboxed iframe) |
| Needs `kind: Skills` on Response action and other gotchas | Standard MCP tool result + `meta` property |

## How widgets work (the short version)

An MCP tool returns a normal text result **plus** a `meta` property
pointing at an HTML widget. MCP-Apps-aware clients (Copilot chat) render
the widget inline; legacy MCP clients ignore `meta` and just show the
text. **Fully backward compatible.**

```python
@mcp.tool()
async def list_work_orders(plant: str) -> ToolResult:
    rows = await fetch_work_orders(plant)
    return ToolResult(
        content=[TextContent(text=f"Found {len(rows)} work orders for {plant}")],
        meta={
            "openai/outputTemplate": "ui://widget/table.html",
            "openai/widgetData": {"rows": rows, "title": f"Work Orders — {plant}"},
        },
    )
```

## Two ways to deploy

1. **M365 Agents Toolkit (VS Code)** — open this folder, "Add an Action"
   → "Start with an MCP Server" → point at your local/deployed URL.
2. **`microsoft/work-iq` GitHub Copilot CLI skill** — claims
   zero-to-deployed in one conversation. Likely the path RAPP will use
   for transpiler automation.

## Wiring an existing RAPP agent into this scaffold

If you already have an `agents/{name}_agent.py` (BasicAgent subclass):

1. Copy `templates/mcp_app/` to `mcp_apps/{name}/`
2. In `server.py`, import your existing agent class
3. For each `BasicAgent.perform()` action, add an `@mcp.tool()` that calls it
4. Pick (or add) a widget HTML for each action that returns structured data
5. Test locally with `python server.py` then register in M365 Agents Toolkit

The Python agent code stays unchanged — MCP just becomes a second
transport alongside the existing Azure Functions HTTP endpoint.

## Status

🚧 **Hand-authored baseline.** Transpiler integration tracked in
kody-w/CommunityRAPP#58. Pilot target: one Mfg CoE agent
(work-order viewer or quality dashboard) before bulk-templating.
