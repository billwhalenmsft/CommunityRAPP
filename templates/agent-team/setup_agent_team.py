#!/usr/bin/env python3
"""
Agent Team Setup Script
=======================
Sets up a new autonomous agent team from template.

Usage:
  # Interactive mode (prompts you for each value):
  python setup_agent_team.py

  # Config file mode (fill in team_config.json first):
  python setup_agent_team.py --config team_config.json

  # Dry run (see what would be created without writing files):
  python setup_agent_team.py --dry-run
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent
REPO_ROOT = TEMPLATE_DIR.parent.parent

GITHUB_LABELS = [
    # Pipeline stages
    {"name": "raw-idea",          "color": "ededed", "description": "New idea, not yet triaged"},
    {"name": "outcome-defined",   "color": "0075ca", "description": "Outcome and KPI defined"},
    {"name": "use-case",          "color": "cfd3d7", "description": "Use case being defined"},
    {"name": "tech-solution",     "color": "e4e669", "description": "Technical solution in progress"},
    {"name": "agent-task",        "color": "7057ff", "description": "Active agent task — triggers automation"},
    {"name": "outcome-validated", "color": "0e8a16", "description": "Outcome validated, ready to close"},
    {"name": "process-now",       "color": "d93f0b", "description": "Process immediately (bypass schedule)"},
    # Priority
    {"name": "p1-critical",       "color": "d93f0b", "description": "Critical priority"},
    {"name": "p2-high",           "color": "e4e669", "description": "High priority"},
    {"name": "p3-medium",         "color": "0075ca", "description": "Medium priority"},
    {"name": "p4-low",            "color": "ededed", "description": "Low priority"},
    # Human loop
    {"name": "needs-bill",        "color": "f9d0c4", "description": "Needs owner input to continue"},
    {"name": "done",              "color": "0e8a16", "description": "Complete and validated"},
]

PERSONA_LABELS = [
    {"name": "persona:orchestrator",       "color": "5319e7"},
    {"name": "persona:outcome-framer",     "color": "006b75"},
    {"name": "persona:pm",                 "color": "0075ca"},
    {"name": "persona:sme",                "color": "e4e669"},
    {"name": "persona:developer",          "color": "d93f0b"},
    {"name": "persona:architect",          "color": "7057ff"},
    {"name": "persona:ux-designer",        "color": "7057ff"},
    {"name": "persona:content-strategist", "color": "e4e669"},
    {"name": "persona:data-analyst",       "color": "0075ca"},
    {"name": "persona:security-reviewer",  "color": "d93f0b"},
    {"name": "persona:qa-engineer",        "color": "0e8a16"},
    {"name": "persona:intake",             "color": "cfd3d7"},
    {"name": "persona:outcome-validator",  "color": "0e8a16"},
]


def prompt(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer if answer else default


def prompt_bool(question: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    answer = input(f"{question}{suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower().strip()).strip("_")


def render_template(template_text: str, values: dict) -> str:
    for key, value in values.items():
        template_text = template_text.replace(f"{{{{{key}}}}}", str(value))
    return template_text


def collect_config_interactive() -> dict:
    print("\n" + "=" * 60)
    print("  Agent Team Setup — Interactive Mode")
    print("=" * 60)
    print("Answer the following questions to configure your team.")
    print("Press Enter to accept defaults.\n")

    team_name = prompt("Team name (e.g. 'Customer Success CoE', 'Platform Team')")
    if not team_name:
        print("ERROR: Team name is required.")
        sys.exit(1)

    team_slug = prompt("Team slug (short, underscored, e.g. 'cs_coe')", slugify(team_name))
    repo = prompt("GitHub repo (owner/repo, e.g. 'myorg/myrepo')")
    if not repo or "/" not in repo:
        print("ERROR: Repo must be in owner/repo format.")
        sys.exit(1)

    owner_login = prompt("Your GitHub username (for needs-bill feedback loop)")
    output_path = prompt("Where to create team files (relative to repo root, e.g. 'customers/my_team')", f"customers/{team_slug}")

    mode = "coe" if prompt_bool("CoE mode? (scheduled autonomous runs — otherwise project/manual mode only)", True) else "project"

    timezone_label = prompt("Your timezone abbreviation (e.g. CST, EST, PST)", "CST")
    standup_cron = prompt("Standup cron UTC (e.g. '0 14 * * 1-5' = 8am CST)", "0 14 * * 1-5")
    wrapup_cron = prompt("Wrap-up cron UTC (e.g. '0 23 * * 1-5' = 5pm CST)", "0 23 * * 1-5")

    print("\nWhich personas do you want? (press Enter = include, 'n' = skip)")
    available_personas = [
        ("outcome_framer",     "Outcome Framer",     "Defines outcomes before build (recommended)"),
        ("pm",                 "PM",                 "Sprint planning & backlog"),
        ("sme",                "SME",                "Domain expertise & process docs"),
        ("developer",          "Developer",          "Code generation & implementation"),
        ("architect",          "Architect",          "Solution design & stack recommendations"),
        ("ux_designer",        "UX Designer",        "Wireframes & user stories"),
        ("content_strategist", "Content Strategist", "Documentation & editorial"),
        ("data_analyst",       "Data Analyst",       "Trends, KPIs & analytics"),
        ("security_reviewer",  "Security Reviewer",  "Code security & compliance"),
        ("qa_engineer",        "QA Engineer",        "Test cases & regression"),
        ("intake",             "Intake/Logger",      "Ideas & human escalations (recommended)"),
        ("outcome_validator",  "Outcome Validator",  "Validates outcomes before closing (recommended)"),
    ]

    selected_personas = []
    for pid, pname, pdesc in available_personas:
        recommended = pid in ("outcome_framer", "pm", "sme", "developer", "architect", "intake", "outcome_validator")
        include = prompt_bool(f"  {pname} — {pdesc}", recommended)
        if include:
            selected_personas.append(pid)

    return {
        "team_name": team_name,
        "team_slug": team_slug,
        "repo": repo,
        "bill_github_login": owner_login,
        "output_path": output_path,
        "mode": mode,
        "timezone_label": timezone_label,
        "standup_cron_utc": standup_cron,
        "wrapup_cron_utc": wrapup_cron,
        "pulse_cron_utc": "0 13-22 * * 1-5",
        "pulse_afterhours_cron_utc": "0 1 * * 2-6",
        "personas": [{"id": p, "include": True} for p in selected_personas],
    }


def create_github_labels(repo: str, team_label: str, team_name: str, dry_run: bool, included_personas: list):
    print(f"\n📌 Creating GitHub labels in {repo}...")
    all_labels = [
        {"name": team_label, "color": "0075ca", "description": f"{team_name} team label"},
        *GITHUB_LABELS,
        *[l for l in PERSONA_LABELS if any(p in l["name"] for p in included_personas)],
    ]
    for label in all_labels:
        cmd = ["gh", "label", "create", label["name"],
               "--color", label["color"],
               "--description", label.get("description", ""),
               "--repo", repo,
               "--force"]
        if dry_run:
            print(f"  [DRY RUN] Would create label: {label['name']}")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            status = "✓" if result.returncode == 0 else "⚠"
            print(f"  {status} {label['name']}")


def create_team_files(cfg: dict, dry_run: bool):
    team_name = cfg["team_name"]
    team_slug = cfg["team_slug"]
    team_slug_class = "".join(w.capitalize() for w in team_slug.split("_"))
    repo = cfg["repo"]
    owner_login = cfg.get("bill_github_login", "owner")
    output_path = Path(REPO_ROOT) / cfg.get("output_path", f"customers/{team_slug}")
    included_personas = [p["id"] for p in cfg.get("personas", []) if p.get("include", True)]
    team_label = team_slug.replace("_", "-")

    template_values = {
        "TEAM_NAME": team_name,
        "TEAM_SLUG": team_slug,
        "TeamSlug": team_slug_class,
        "TEAM_LABEL": team_label,
        "TEAM_MODULE": str(output_path.relative_to(REPO_ROOT)).replace("\\", ".").replace("/", "."),
        "REPO": repo,
        "OWNER_LOGIN": owner_login,
        "TIMEZONE_LABEL": cfg.get("timezone_label", "UTC"),
        "STANDUP_CRON_UTC": cfg.get("standup_cron_utc", "0 14 * * 1-5"),
        "WRAPUP_CRON_UTC": cfg.get("wrapup_cron_utc", "0 23 * * 1-5"),
        "PULSE_CRON_UTC": cfg.get("pulse_cron_utc", "0 13-22 * * 1-5"),
        "PULSE_AFTERHOURS_CRON_UTC": cfg.get("pulse_afterhours_cron_utc", "0 1 * * 2-6"),
        "PULSE_CRON_UTC_IDENTIFIER": cfg.get("pulse_cron_utc", "").split()[1] if cfg.get("pulse_cron_utc") else "13-22",
        "RUNNER_PATH": str((output_path / "agents" / "runner.py").relative_to(REPO_ROOT)).replace("\\", "/"),
        "AGENT_ROSTER_COMMENT": "\n    ".join(f"- {p}" for p in included_personas),
    }

    # Directories to create
    dirs = [
        output_path / "agents",
        output_path / "knowledge_base",
        output_path / "outcomes",
        REPO_ROOT / ".github" / "workflows",
    ]
    for d in dirs:
        if dry_run:
            print(f"  [DRY RUN] mkdir {d}")
        else:
            d.mkdir(parents=True, exist_ok=True)

    # Render orchestrator
    orch_src = (TEMPLATE_DIR / "agents" / "orchestrator_template.py").read_text()
    orch_out = output_path / "agents" / f"{team_slug}_orchestrator_agent.py"
    if dry_run:
        print(f"  [DRY RUN] Create {orch_out}")
    else:
        orch_out.write_text(render_template(orch_src, template_values))
        print(f"  ✓ {orch_out.relative_to(REPO_ROOT)}")

    # Create stub persona agents for each selected persona
    persona_src = (TEMPLATE_DIR / "agents" / "_base_persona_template.py").read_text()
    for persona_id in included_personas:
        persona_values = {
            **template_values,
            "PERSONA_ID": persona_id,
            "CLASS_NAME": f"{team_slug_class}{persona_id.replace('_', ' ').title().replace(' ', '')}Agent",
            "PERSONA_ROLE": f"TODO: describe the {persona_id.replace('_', ' ')} role for {team_name}",
            "PERSONA_DESCRIPTION": f"TODO: describe what this agent does",
            "WHEN_TO_USE": f"TODO: describe when to invoke this agent",
            "ACTION_1": "define_use_case",
            "ACTION_2": "get_recommendations",
            "action_1_method": "_define_use_case",
            "action_2_method": "_get_recommendations",
            "DOMAIN_FOCUS": team_name,
        }
        agent_out = output_path / "agents" / f"{team_slug}_{persona_id}_agent.py"
        if dry_run:
            print(f"  [DRY RUN] Create {agent_out}")
        else:
            agent_out.write_text(render_template(persona_src, persona_values))
            print(f"  ✓ {agent_out.relative_to(REPO_ROOT)}")

    # Create __init__.py
    init_out = output_path / "agents" / "__init__.py"
    if not dry_run and not init_out.exists():
        init_out.write_text("")

    # Create runner.py stub
    runner_content = f'''#!/usr/bin/env python3
"""Runner for {team_name} agent team. See coe_runner.py in mfg_coe for a full implementation."""
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from {template_values["TEAM_MODULE"]}.agents.{team_slug}_orchestrator_agent import {team_slug_class}OrchestratorAgent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True)
    parser.add_argument("--issue", type=int)
    parser.add_argument("--comment", default="")
    parser.add_argument("--max", type=int, default=5)
    args = parser.parse_args()
    orchestrator = {team_slug_class}OrchestratorAgent()
    result = orchestrator.perform(
        action=args.action,
        issue_number=args.issue,
        feedback_text=args.comment,
    )
    print(json.dumps(json.loads(result), indent=2))

if __name__ == "__main__":
    main()
'''
    runner_out = output_path / "agents" / "runner.py"
    if dry_run:
        print(f"  [DRY RUN] Create {runner_out}")
    else:
        runner_out.write_text(runner_content)
        print(f"  ✓ {runner_out.relative_to(REPO_ROOT)}")

    # Render workflows
    workflow_map = [
        ("manual_run_template.yml",    f"{team_slug}_manual_run.yml",    True),
        ("issue_handler_template.yml", f"{team_slug}_issue_handler.yml", True),
        ("scheduled_pulse_template.yml", f"{team_slug}_scheduled_pulse.yml", cfg.get("mode") == "coe"),
    ]
    for src_name, dst_name, include in workflow_map:
        if not include:
            continue
        wf_src = (TEMPLATE_DIR / "workflows" / src_name).read_text()
        wf_out = REPO_ROOT / ".github" / "workflows" / dst_name
        if dry_run:
            print(f"  [DRY RUN] Create .github/workflows/{dst_name}")
        else:
            wf_out.write_text(render_template(wf_src, template_values))
            print(f"  ✓ .github/workflows/{dst_name}")

    # Charter
    charter_src = (TEMPLATE_DIR / "CHARTER_TEMPLATE.md").read_text() if (TEMPLATE_DIR / "CHARTER_TEMPLATE.md").exists() else "# {{TEAM_NAME}} Charter\n\nTODO: Fill in charter.\n"
    charter_out = output_path / "CHARTER.md"
    if dry_run:
        print(f"  [DRY RUN] Create {charter_out}")
    else:
        charter_out.write_text(render_template(charter_src, template_values))
        print(f"  ✓ {charter_out.relative_to(REPO_ROOT)}")

    # knowledge_base placeholder
    kb_out = output_path / "knowledge_base" / "README.md"
    if not dry_run and not kb_out.exists():
        kb_out.write_text(f"# {team_name} Knowledge Base\n\nAdd context cards here. Agents read these files before generating code or recommendations.\n")

    # outcomes placeholder
    outcomes_out = output_path / "outcomes" / ".gitkeep"
    if not dry_run and not outcomes_out.exists():
        outcomes_out.write_text("")


def print_next_steps(cfg: dict):
    team_slug = cfg["team_slug"]
    repo = cfg["repo"]
    output_path = cfg.get("output_path", f"customers/{team_slug}")
    team_label = team_slug.replace("_", "-")
    print(f"""
{'=' * 60}
  ✅ Setup Complete — Next Steps
{'=' * 60}

1. FILL IN YOUR AGENT LOGIC
   Open each generated agent file in {output_path}/agents/
   and replace the TODO sections with your domain logic.
   See customers/mfg_coe/agents/ for working examples.

2. WIRE AGENTS INTO ORCHESTRATOR
   In {output_path}/agents/{team_slug}_orchestrator_agent.py:
   - Uncomment the import lines
   - Uncomment the self.agents dict entries
   - Add routing keywords to ROUTING_MAP

3. SET GITHUB SECRETS
   In {repo} → Settings → Secrets → Actions, add:
     AZURE_OPENAI_ENDPOINT
     AZURE_OPENAI_DEPLOYMENT_NAME
     AZURE_OPENAI_API_VERSION
     AzureWebJobsStorage (or AZURE_STORAGE_CONNECTION_STRING)
     AZURE_STORAGE_ACCOUNT_NAME

4. TEST IT
   gh workflow run "{team_slug.replace('_', '-')}-manual-run" \\
     --repo {repo} -f action=health_check

5. ADD YOUR FIRST ISSUE
   Create a GitHub issue in {repo} with labels:
     {team_label}  +  raw-idea

   Then add the 'agent-task' label to trigger automation.

6. REVIEW THE CHARTER
   {output_path}/CHARTER.md — update with your team's mission,
   domain focus, and pipeline stages.

Docs: templates/agent-team/QUICK_START.md
""")


def main():
    parser = argparse.ArgumentParser(description="Set up an agent team from template")
    parser.add_argument("--config", help="Path to team_config.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    if args.config:
        print(f"Loading config from {args.config}...")
        with open(args.config) as f:
            cfg = json.load(f)
    else:
        cfg = collect_config_interactive()

    if args.dry_run:
        print("\n⚠️  DRY RUN — no files will be written or labels created\n")

    team_label = cfg["team_slug"].replace("_", "-")
    included_personas = [p["id"] for p in cfg.get("personas", []) if p.get("include", True)]

    print(f"\n🚀 Setting up: {cfg['team_name']}")
    print(f"   Repo:      {cfg['repo']}")
    print(f"   Mode:      {cfg.get('mode', 'coe')}")
    print(f"   Personas:  {', '.join(included_personas)}")
    print(f"   Output:    {cfg.get('output_path', 'customers/' + cfg['team_slug'])}")

    print("\n📁 Creating team files...")
    create_team_files(cfg, args.dry_run)

    create_github_labels(cfg["repo"], team_label, cfg["team_name"], args.dry_run, included_personas)

    if not args.dry_run:
        print_next_steps(cfg)


if __name__ == "__main__":
    main()
