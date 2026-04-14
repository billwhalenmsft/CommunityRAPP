"""
Obsidian Vault Generator for the Mfg CoE.

Generates an Obsidian-compatible markdown vault from CoE files.
The vault can be opened with Obsidian desktop to visualize:
- Agent relationships (graph view)
- SOPs and their connections to outcomes
- Decision log timeline
- Issue backlog as notes with frontmatter

Run: python customers/mfg_coe/obsidian_vault/generate_vault.py
Output: customers/mfg_coe/obsidian_vault/vault/
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
COE_ROOT = REPO_ROOT / "customers" / "mfg_coe"
VAULT_DIR = Path(__file__).parent / "vault"

AGENTS = [
    {"id": "orchestrator", "name": "Orchestrator Agent", "icon": "⚙️", "file": "mfg_coe_orchestrator_agent.py", "connects_to": ["pm", "sme", "developer", "architect", "persona", "intake"]},
    {"id": "pm", "name": "PM Agent", "icon": "🗂️", "file": "mfg_coe_pm_agent.py", "connects_to": ["intake", "orchestrator"]},
    {"id": "sme", "name": "SME Agent", "icon": "🏭", "file": "mfg_coe_sme_agent.py", "connects_to": ["intake", "orchestrator"]},
    {"id": "developer", "name": "Developer Agent", "icon": "🧑‍💻", "file": "mfg_coe_developer_agent.py", "connects_to": ["architect", "intake", "orchestrator"]},
    {"id": "architect", "name": "Architect Agent", "icon": "🏗️", "file": "mfg_coe_architect_agent.py", "connects_to": ["intake", "orchestrator"]},
    {"id": "persona", "name": "Customer Persona Agent", "icon": "🎭", "file": "mfg_coe_customer_persona_agent.py", "connects_to": ["intake", "orchestrator"]},
    {"id": "intake", "name": "Intake/Logger Agent", "icon": "📋", "file": "mfg_coe_intake_agent.py", "connects_to": ["orchestrator"]},
]

CUSTOMERS = ["navico", "otis", "zurnelkay", "vermeer", "carrier", "aes"]

OUTCOMES = [
    {"id": "warranty-self-service", "title": "Warranty Self-Service", "priority": "P1", "customers": ["navico", "otis", "zurnelkay"]},
    {"id": "ai-case-triage", "title": "AI-Powered Case Triage", "priority": "P1", "customers": ["navico", "carrier"]},
    {"id": "rma-automation", "title": "RMA Process Automation", "priority": "P2", "customers": ["navico", "otis"]},
    {"id": "sop-library", "title": "SOP Library — Discrete Mfg", "priority": "P2", "customers": []},
]


def make_frontmatter(data: dict) -> str:
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def generate_vault() -> None:
    print("Generating Obsidian vault...")

    # Clean and create vault structure
    if VAULT_DIR.exists():
        shutil.rmtree(VAULT_DIR)

    dirs = ["agents", "outcomes", "customers", "sops", "decisions", "knowledge_base", "github_issues"]
    for d in dirs:
        (VAULT_DIR / d).mkdir(parents=True, exist_ok=True)

    # Generate .obsidian config
    obsidian_dir = VAULT_DIR / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)
    with open(obsidian_dir / "app.json", "w") as f:
        json.dump({"theme": "obsidian", "cssTheme": ""}, f, indent=2)

    # ── Agents ────────────────────────────────────────────────────────────
    for agent in AGENTS:
        links = "\n".join(f"- [[agents/{a}|{a}]]" for a in agent["connects_to"])
        source_file = COE_ROOT / "agents" / agent["file"]
        source_excerpt = ""
        if source_file.exists():
            lines = source_file.read_text(encoding="utf-8").split("\n")
            doc_lines = [l for l in lines[:40] if l.strip().startswith("#") or l.strip().startswith('"""')]
            source_excerpt = "\n".join(doc_lines[:10])

        content = make_frontmatter({
            "type": "agent",
            "persona": agent["id"],
            "icon": agent["icon"],
            "tags": ["agent", "mfg-coe"],
        })
        content += f"# {agent['icon']} {agent['name']}\n\n"
        content += f"**Role:** See [[COE_CHARTER]] for full operating charter.\n\n"
        content += f"**Source:** `customers/mfg_coe/agents/{agent['file']}`\n\n"
        content += f"## Connected Agents\n\n{links}\n\n"
        if source_excerpt:
            content += f"## Code Overview\n\n```python\n{source_excerpt}\n```\n"

        with open(VAULT_DIR / "agents" / f"{agent['id']}.md", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Agent: {agent['name']}")

    # ── Outcomes ──────────────────────────────────────────────────────────
    for outcome in OUTCOMES:
        customer_links = "\n".join(f"- [[customers/{c}]]" for c in outcome["customers"])
        content = make_frontmatter({
            "type": "outcome",
            "priority": outcome["priority"],
            "tags": ["outcome", "mfg-coe", outcome["priority"].lower()],
        })
        content += f"# 🎯 {outcome['title']}\n\n"
        content += f"**Priority:** {outcome['priority']}\n\n"
        content += f"## Customer Applicability\n\n{customer_links or '- TBD'}\n\n"
        content += "## Agents Working This\n\n- [[agents/sme]]\n- [[agents/developer]]\n\n"
        content += "## Status\n\n> Update this section as work progresses.\n\n"
        content += "## Links\n\n- [[COE_CHARTER]]\n"

        with open(VAULT_DIR / "outcomes" / f"{outcome['id']}.md", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Outcome: {outcome['title']}")

    # ── Customers ─────────────────────────────────────────────────────────
    for customer in CUSTOMERS:
        testing_dir = COE_ROOT / "testing" / customer
        scenarios = []
        personas = []
        if (testing_dir / "scenarios.json").exists():
            with open(testing_dir / "scenarios.json") as f:
                raw = json.load(f)
                scenarios = raw.get("scenarios", raw) if isinstance(raw, dict) else raw
        if (testing_dir / "personas.json").exists():
            with open(testing_dir / "personas.json") as f:
                raw = json.load(f)
                personas = raw.get("personas", raw) if isinstance(raw, dict) else raw

        scenario_list = "\n".join(f"- **{s.get('title', s.get('id', ''))}**: {s.get('description', '')}" for s in scenarios)
        persona_list = "\n".join(f"- **{p.get('name', '')}** ({p.get('role', '')})" for p in personas)
        relevant_outcomes = [o["title"] for o in OUTCOMES if customer in o["customers"]]
        outcome_links = "\n".join(f"- [[outcomes/{o['id']}]]" for o in OUTCOMES if customer in o["customers"])

        content = make_frontmatter({
            "type": "customer",
            "customer": customer,
            "tags": ["customer", "mfg-coe", customer],
            "scenarios": len(scenarios),
            "personas": len(personas),
        })
        content += f"# 🏢 {customer.title()}\n\n"
        content += f"**Status:** {'✅ Profiles built' if scenarios else '📋 In backlog'}\n\n"
        content += f"## Demo Outcomes\n\n{outcome_links or '- TBD'}\n\n"
        content += f"## Personas ({len(personas)})\n\n{persona_list or '- None yet'}\n\n"
        content += f"## Test Scenarios ({len(scenarios)})\n\n{scenario_list or '- None yet'}\n\n"
        content += f"## Agent\n\n- [[agents/persona]] handles customer simulation\n"

        with open(VAULT_DIR / "customers" / f"{customer}.md", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Customer: {customer}")

    # ── Copy SOPs ─────────────────────────────────────────────────────────
    sops_src = COE_ROOT / "sops"
    if sops_src.exists():
        for sop_file in sops_src.glob("*.md"):
            shutil.copy2(sop_file, VAULT_DIR / "sops" / sop_file.name)
            print(f"  ✓ SOP: {sop_file.name}")

    # ── Copy knowledge base ───────────────────────────────────────────────
    kb_src = COE_ROOT / "knowledge_base"
    if kb_src.exists():
        for kb_file in kb_src.glob("*.md"):
            shutil.copy2(kb_file, VAULT_DIR / "knowledge_base" / kb_file.name)
            print(f"  ✓ Knowledge: {kb_file.name}")

    # ── Charter ───────────────────────────────────────────────────────────
    charter_src = COE_ROOT / "COE_CHARTER.md"
    if charter_src.exists():
        shutil.copy2(charter_src, VAULT_DIR / "COE_CHARTER.md")
        print("  ✓ Charter copied")

    # ── Home note ─────────────────────────────────────────────────────────
    home = make_frontmatter({"type": "home", "tags": ["mfg-coe", "home"]})
    home += "# 🏭 Mfg CoE — Knowledge Graph\n\n"
    home += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    home += "## Quick Links\n\n"
    home += "- [[COE_CHARTER]] — Operating rules and context\n"
    home += "- [[agents/orchestrator]] — Entry point to agent team\n"
    home += "### Outcomes\n"
    for o in OUTCOMES:
        home += f"- [[outcomes/{o['id']}]] — {o['priority']}\n"
    home += "\n### Customers\n"
    for c in CUSTOMERS:
        home += f"- [[customers/{c}]]\n"
    home += "\n### Knowledge Base\n"
    for kb in (COE_ROOT / "knowledge_base").glob("*.md") if (COE_ROOT / "knowledge_base").exists() else []:
        home += f"- [[knowledge_base/{kb.stem}]]\n"
    home += "\n> Open the **Graph View** (Ctrl+G) to see all connections visually.\n"

    with open(VAULT_DIR / "HOME.md", "w", encoding="utf-8") as f:
        f.write(home)

    print(f"\n✅ Vault generated at: {VAULT_DIR}")
    print(f"   Open with Obsidian: File → Open folder as vault → select the 'vault' folder")
    print(f"   Use Graph View (Ctrl+G) to visualize agent/outcome/customer connections")


if __name__ == "__main__":
    generate_vault()
