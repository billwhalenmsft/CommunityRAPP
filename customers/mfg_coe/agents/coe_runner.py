"""
CoE Runner — CLI entry point for GitHub Actions autonomous execution.

Usage:
    python coe_runner.py --action standup
    python coe_runner.py --action process_issue --issue 47
    python coe_runner.py --action bill_feedback --issue 47 --comment "Build the SOP first"
    python coe_runner.py --action health_check
    python coe_runner.py --action run_backlog --max 3
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Ensure repo root is on the Python path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("coe_runner")

REPO = os.environ.get("COE_REPO", "billwhalenmsft/CommunityRAPP-BillWhalen")


def _post_issue_comment(issue_number: int, body: str) -> None:
    """Post a comment on a GitHub issue via gh CLI."""
    tmp = Path("/tmp/coe_comment.md") if os.name != "nt" else Path("C:/Temp/coe_comment.md")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(body, encoding="utf-8")
    result = subprocess.run(
        ["gh", "issue", "comment", str(issue_number), "--repo", REPO, "--body-file", str(tmp)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("Failed to post issue comment: %s", result.stderr)
    else:
        log.info("Posted comment on issue #%d", issue_number)


def _set_issue_label(issue_number: int, add_labels: list[str], remove_labels: list[str]) -> None:
    """Add/remove labels on a GitHub issue."""
    for label in add_labels:
        subprocess.run(
            ["gh", "issue", "edit", str(issue_number), "--repo", REPO, "--add-label", label],
            capture_output=True,
        )
    for label in remove_labels:
        subprocess.run(
            ["gh", "issue", "edit", str(issue_number), "--repo", REPO, "--remove-label", label],
            capture_output=True,
        )


def _close_issue(issue_number: int) -> None:
    subprocess.run(
        ["gh", "issue", "close", str(issue_number), "--repo", REPO],
        capture_output=True,
    )
    log.info("Closed issue #%d", issue_number)


def _load_orchestrator():
    """Lazily import and instantiate the orchestrator (avoids import errors if deps missing)."""
    try:
        from customers.mfg_coe.agents.mfg_coe_orchestrator_agent import MfgCoEOrchestratorAgent
        return MfgCoEOrchestratorAgent()
    except ImportError as e:
        log.error("Could not import orchestrator: %s", e)
        log.error("Make sure you're running from the repo root: python customers/mfg_coe/agents/coe_runner.py")
        sys.exit(1)


# ── Actions ──────────────────────────────────────────────────────────────────

def action_standup() -> None:
    """Run morning standup — summarize open work, pick up unblocked tasks."""
    log.info("=== CoE Morning Standup ===")
    coe = _load_orchestrator()
    result_raw = coe.perform(action="morning_standup")
    result = json.loads(result_raw)

    log.info("Standup complete:\n%s", json.dumps(result, indent=2))

    # Auto-label any ready issues before processing
    action_auto_label()

    # If there are agent-task issues to process, run them
    open_tasks = result.get("open_agent_tasks", [])
    if open_tasks:
        log.info("Found %d open agent-task issues — processing...", len(open_tasks))
        for issue_num in open_tasks[:3]:  # cap at 3 per standup to avoid runaway
            action_process_issue(issue_num)
    else:
        log.info("No open agent-task issues found.")


def action_auto_label() -> None:
    """
    Scan open mfg-coe issues that have enough context to act on and add
    the 'agent-task' label so the issue handler picks them up automatically.

    Criteria for auto-labeling:
    - Has label: mfg-coe
    - Does NOT already have: agent-task, needs-bill, done, check-existing, nudge-bill
    - Body length > 100 chars (enough context to act on)
    - Was created via a structured template (contains at least one section header or list)
    - Was NOT created by the agent itself (not authored by github-actions[bot])
    """
    log.info("=== Auto-Labeling Eligible Issues ===")

    result = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--label", "mfg-coe",
         "--state", "open", "--json", "number,title,body,labels,author,createdAt",
         "--limit", "50"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error("Failed to list issues: %s", result.stderr)
        return

    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.warning("Could not parse issues for auto-labeling")
        return

    skip_labels = {"agent-task", "needs-bill", "done", "check-existing", "nudge-bill", "process-now"}
    labeled_count = 0

    for issue in issues:
        labels = {l["name"] for l in issue.get("labels", [])}
        if labels & skip_labels:
            continue  # already handled

        body = issue.get("body") or ""
        author = issue.get("author", {}).get("login", "")
        if author in ("github-actions[bot]", "billwhalenmsft-bot"):
            continue  # skip agent-generated issues

        # Require meaningful body — either structured (###/##) or long enough
        has_structure = "###" in body or "##" in body or "\n- " in body
        has_length = len(body.strip()) > 100

        if has_structure or has_length:
            log.info("Auto-labeling issue #%d: %s", issue["number"], issue["title"])
            _set_issue_label(issue["number"], ["agent-task"], [])
            labeled_count += 1

    log.info("Auto-labeled %d issue(s) as agent-task", labeled_count)


def action_assign_copilot(issue_number: int) -> None:
    """
    Assign GitHub Copilot coding agent to a tech-solution issue.
    Copilot will open a pull request with the implementation.
    Posts a comment on the issue to notify Bill.
    """
    log.info("=== Assigning Copilot to Issue #%d ===", issue_number)

    # Fetch issue details
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", REPO,
         "--json", "title,body,labels"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error("Failed to fetch issue #%d: %s", issue_number, result.stderr)
        return

    try:
        issue_data = json.loads(result.stdout)
    except Exception:
        log.error("Could not parse issue #%d", issue_number)
        return

    labels = {l["name"] for l in issue_data.get("labels", [])}
    if "tech-solution" not in labels and "code-task" not in labels:
        log.info("Issue #%d is not a tech-solution/code-task — skipping Copilot assignment", issue_number)
        return

    # Assign Copilot via gh CLI (requires Copilot coding agent enabled on the repo)
    assign_result = subprocess.run(
        ["gh", "issue", "edit", str(issue_number), "--repo", REPO,
         "--add-assignee", "@me"],  # placeholder — real Copilot assignment via API
        capture_output=True, text=True,
    )

    # Use the GitHub API to request Copilot assignment (Copilot coding agent)
    copilot_result = subprocess.run(
        ["gh", "api", "--method", "POST",
         f"/repos/{REPO}/issues/{issue_number}/assignees",
         "-f", "assignees[]=copilot"],
        capture_output=True, text=True,
    )

    if copilot_result.returncode == 0:
        comment = (
            "## 🤖 Copilot Coding Agent Assigned\n\n"
            "GitHub Copilot has been assigned to implement this task. "
            "It will analyze the issue and open a pull request.\n\n"
            "**What happens next:**\n"
            "- Copilot creates a branch and writes the code\n"
            "- A PR is opened for your review\n"
            "- Agents will review and comment on the PR\n\n"
            f"_Assigned by CoE orchestrator — Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
        )
    else:
        log.warning("Copilot assignment API call returned %d: %s",
                    copilot_result.returncode, copilot_result.stderr)
        comment = (
            "## 🔧 Code Task Ready for Copilot\n\n"
            "This issue is marked as a tech solution. To assign GitHub Copilot:\n\n"
            "1. Open the issue on GitHub\n"
            "2. In the Assignees section, click the gear and select **Copilot**\n"
            "3. Copilot will open a PR automatically\n\n"
            "_Copilot auto-assignment requires the Copilot coding agent to be enabled on this repo._\n\n"
            f"_Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
        )

    _post_issue_comment(issue_number, comment)
    _set_issue_label(issue_number, ["copilot-assigned"], ["agent-task"])


def _run_library_search_if_tech(issue_number: int) -> bool:
    """
    If the issue has the tech-solution label, run the library search agent first.
    Posts results as a comment. Returns True if a strong match was found.
    """
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", REPO,
         "--json", "title,body,labels"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False

    try:
        data = json.loads(result.stdout)
    except Exception:
        return False

    labels = [l["name"] for l in data.get("labels", [])]
    if "tech-solution" not in labels:
        return False

    log.info("Issue #%d has tech-solution label — running library search first.", issue_number)
    try:
        from customers.mfg_coe.agents.library_search_agent import run_library_search
        search_result = run_library_search(
            issue_number=issue_number,
            issue_title=data.get("title", ""),
            issue_body=data.get("body", ""),
        )
        _post_issue_comment(issue_number, search_result["comment_body"])

        if search_result.get("strong_match"):
            _set_issue_label(issue_number, ["check-existing"], [])
            log.info("Strong match found — tagged check-existing on #%d.", issue_number)
            return True
    except Exception as exc:
        log.warning("Library search failed for #%d: %s", issue_number, exc)

    return False


def _format_result_as_markdown(result: dict) -> str:
    """Convert a structured agent result dict into readable markdown."""
    lines = []
    skip_keys = {"status", "persona", "summary", "artifact"}

    # Pull out pipeline_steps specially
    pipeline_steps = result.get("pipeline_steps", [])
    if pipeline_steps:
        last_step = pipeline_steps[-1] if pipeline_steps else {}
        step_name = last_step.get("step", "")
        step_result = last_step.get("result", {})
        if step_name:
            lines.append(f"**Step completed:** `{step_name}`\n")
        if isinstance(step_result, dict):
            # Pull key readable fields
            for key in ("use_case", "description", "deliverable", "pattern", "title"):
                val = step_result.get(key)
                if val and isinstance(val, str):
                    label = key.replace("_", " ").title()
                    lines.append(f"**{label}:** {val}\n")
            use_cases = step_result.get("use_cases", [])
            if use_cases:
                lines.append("**Use Cases:**")
                for uc in use_cases[:5]:
                    lines.append(f"- {uc}")
                lines.append("")
            patterns = step_result.get("recommended_patterns", [])
            if patterns:
                lines.append("**Recommended Patterns:**")
                for p in patterns[:3]:
                    if isinstance(p, dict):
                        lines.append(f"- **{p.get('pattern_id', '')}**: {p.get('description', '')}")
                    else:
                        lines.append(f"- {p}")
                lines.append("")

    # Next steps
    next_steps = result.get("next_steps", [])
    if next_steps:
        lines.append("**Next Steps:**")
        for s in next_steps:
            lines.append(f"- {s}")
        lines.append("")

    # Stage / assigned_to
    stage = result.get("current_stage")
    assigned = result.get("assigned_to")
    if stage:
        lines.append(f"**Stage:** `{stage}`")
    if assigned:
        lines.append(f"**Assigned to:** {assigned}")

    return "\n".join(lines) if lines else "_No summary available._"


def action_process_issue(issue_number: int) -> None:
    """Route and execute a single GitHub issue as a CoE task."""
    log.info("=== Processing Issue #%d ===", issue_number)

    # Run library search before architect on tech-solution issues
    _run_library_search_if_tech(issue_number)

    coe = _load_orchestrator()
    result_raw = coe.perform(action="run_pipeline_item", issue_number=issue_number)
    result = json.loads(result_raw)

    status = result.get("status", "unknown")
    summary = result.get("summary", "")
    persona = result.get("persona", "orchestrator")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    footer = f"\n\n---\n_Agent: {persona} | Run ID: GHA_{run_id}_"

    # If no clean summary, build one from structured result fields
    if not summary:
        summary = _format_result_as_markdown(result)

    log.info("Issue #%d result: %s", issue_number, status)

    # Build comment body
    if status == "needs_bill":
        comment_body = (
            "## 🤔 Agent needs your input\n\n"
            f"{result.get('question', 'The agent has a question before proceeding.')}\n\n"
            "**Please comment with your direction.** I'll pick it up and continue."
            + footer
        )
        _post_issue_comment(issue_number, comment_body)
        _set_issue_label(issue_number, ["needs-bill"], ["agent-task"])
        log.info("Issue #%d relabeled to needs-bill", issue_number)

    elif status in ("done", "complete", "success"):
        artifact_info = result.get("artifact", "")
        comment_body = (
            "## ✅ Agent Task Complete\n\n"
            f"{summary}\n\n"
            + (f"**Artifact:** `{artifact_info}`\n\n" if artifact_info else "")
            + footer.lstrip("\n\n")
        )
        _post_issue_comment(issue_number, comment_body)
        _set_issue_label(issue_number, ["done"], ["agent-task"])
        _close_issue(issue_number)

    elif status == "pipeline_advanced":
        stage = result.get("current_stage", "unknown")
        assigned_to = result.get("assigned_to", "")
        next_steps = result.get("next_steps", [])
        steps_md = "\n".join(f"- {s}" for s in next_steps) if next_steps else ""
        comment_body = (
            f"## 🔄 Pipeline Stage Advanced\n\n"
            f"This item has been moved to: **`{stage}`**\n\n"
            + (f"**Assigned to:** {assigned_to}\n\n" if assigned_to else "")
            + (f"{summary}\n\n" if summary else "")
            + (f"**Next steps:**\n{steps_md}\n\n" if steps_md else "")
            + footer.lstrip("\n\n")
        )
        _post_issue_comment(issue_number, comment_body)

    elif status == "blocked_needs_outcome":
        blocked_reason = result.get("blocked_reason", "Outcome could not be inferred from this issue.")
        questions = result.get("questions", [])
        questions_md = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions)) if questions else ""
        comment_body = (
            f"## 🚫 Pipeline Blocked — Outcome Required\n\n"
            f"{blocked_reason}\n\n"
            + (f"**Please answer the following before work can proceed:**\n\n{questions_md}\n\n" if questions_md else "")
            + "Once you reply, the pipeline will resume automatically.\n\n"
            + footer.lstrip("\n\n")
        )
        _post_issue_comment(issue_number, comment_body)

    else:
        comment_body = (
            f"## ⚠️ Agent Update — `{status}`\n\n"
            f"{summary}"
            + footer
        )
        _post_issue_comment(issue_number, comment_body)


FORCE_COMMANDS = ("/push", "/advance", "/force")


def action_force_advance(issue_number: int, comment: str) -> None:
    """Force an issue forward regardless of agent confidence or pipeline state."""
    log.info("=== Force-Advancing Issue #%d ===", issue_number)
    run_id = os.environ.get("GITHUB_RUN_ID", "local")

    # Strip the command to get any optional direction hint after it
    direction = comment.strip()
    for cmd in FORCE_COMMANDS:
        if direction.lower().startswith(cmd):
            direction = direction[len(cmd):].strip()
            break

    # Add all bypass labels, clear blockers
    _set_issue_label(
        issue_number,
        add_labels=["outcome-defined", "in-progress"],
        remove_labels=["needs-bill", "on-deck"],
    )

    hint_line = f"\n\n**Direction:** _{direction}_" if direction else ""
    _post_issue_comment(
        issue_number,
        f"## 🚀 Force-Advanced by Bill\n\n"
        f"All pipeline checks bypassed. Proceeding to execution.{hint_line}\n\n"
        f"_Run ID: GHA_{run_id}_"
    )

    # Run the pipeline — outcome-defined label now set, so framer is skipped
    action_process_issue(issue_number)


def action_bill_feedback(issue_number: int, comment: str) -> None:
    """Process Bill's comment and resume work on an issue."""
    # Intercept force commands — bypass all agent gates
    comment_stripped = comment.strip()
    if any(comment_stripped.lower().startswith(cmd) for cmd in FORCE_COMMANDS):
        action_force_advance(issue_number, comment_stripped)
        return

    log.info("=== Processing Bill's Feedback on Issue #%d ===", issue_number)
    coe = _load_orchestrator()
    result_raw = coe.perform(
        action="process_bill_feedback",
        feedback_text=comment,  # Fix: was 'feedback', orchestrator expects 'feedback_text'
        issue_number=issue_number,
    )
    result = json.loads(result_raw)

    if "error" in result:
        log.error("Feedback processing failed: %s", result["error"])
        _post_issue_comment(issue_number,
            f"## ⚠️ Could not process feedback\n\n{result['error']}\n\n"
            f"_Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_")
        return

    log.info("Feedback processed: %s", json.dumps(result, indent=2))

    # Always acknowledge the feedback
    routed_persona = result.get("assigned_to") or result.get("routed_persona", "agent")
    next_action = result.get("next_action", "continue")
    comment_body = (
        "## 🔄 Feedback received — resuming work\n\n"
        f"Understood: _{result.get('feedback_summary', comment[:200])}_\n\n"
        f"Routing to **{routed_persona}** → `{next_action}`\n\n"
        f"_Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
    )
    _post_issue_comment(issue_number, comment_body)

    # Remove needs-bill; add outcome-defined so the pipeline skips the outcome framer
    # Do NOT add agent-task here — calling action_process_issue directly avoids double-fire
    _set_issue_label(issue_number, ["outcome-defined"], ["needs-bill"])

    # Re-process the issue with context from Bill's feedback included
    action_process_issue(issue_number)


def action_health_check() -> None:
    """Run health check on all CoE agents and report status."""
    log.info("=== CoE Health Check ===")
    coe = _load_orchestrator()
    result_raw = coe.perform(action="health_check")
    result = json.loads(result_raw)
    log.info("Health check result:\n%s", json.dumps(result, indent=2))

    # Post summary as an issue comment if issue provided via env
    issue_num = os.environ.get("COE_HEALTH_ISSUE")
    if issue_num:
        agent_status = result.get("agents", {})
        rows = "\n".join(
            f"| {name} | {'✅ OK' if ok else '❌ Error'} |"
            for name, ok in agent_status.items()
        )
        comment = f"## 🏥 CoE Health Check\n\n| Agent | Status |\n|---|---|\n{rows}"
        _post_issue_comment(int(issue_num), comment)


def action_idle_check() -> None:
    """Check for team inactivity. If no progress in 3+ days, create a needs-bill nudge issue."""
    log.info("=== CoE Idle Check ===")
    import subprocess
    from datetime import datetime, timezone, timedelta

    # Get all open mfg-coe issues with recent activity
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--label", "mfg-coe",
         "--state", "open", "--json", "number,title,updatedAt,labels", "--limit", "50"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error("Failed to list issues: %s", result.stderr)
        return

    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("Could not parse issues: %s", result.stdout)
        return

    if not issues:
        # No open issues at all — nudge Bill to add new work
        log.info("No open issues found — creating nudge for Bill.")
        _create_nudge_issue("empty_backlog")
        return

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=3)

    # Find most recently updated issue
    most_recent = max(issues, key=lambda i: i.get("updatedAt", ""))
    last_update_str = most_recent.get("updatedAt", "")
    try:
        last_update = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
    except Exception:
        log.warning("Could not parse date: %s", last_update_str)
        return

    if last_update < cutoff:
        days_idle = (now - last_update).days
        log.info("Team idle for %d days — creating nudge issue for Bill.", days_idle)
        _create_nudge_issue("idle", days_idle=days_idle)
    else:
        log.info("Team is active — last update %s. No nudge needed.", last_update_str)


def _create_nudge_issue(reason: str, days_idle: int = 0) -> None:
    """Create a GitHub issue to nudge Bill when the team needs direction."""
    if reason == "empty_backlog":
        title = "🔔 CoE Backlog Empty — Team Ready for New Assignments"
        body = (
            "## 👋 Hey Bill — the team is ready and waiting!\n\n"
            "The CoE backlog is empty. Your agents are idle and eager to work.\n\n"
            "**Suggested next steps:**\n"
            "- Add new feature requests or use cases to the backlog\n"
            "- Review completed work and set new priorities\n"
            "- Kick off a new discovery session or sprint\n\n"
            "_Automated nudge from CoE Idle Detection_"
        )
    else:
        title = f"🔔 CoE Team Idle for {days_idle} Days — Decisions Needed"
        body = (
            f"## 👋 Hey Bill — the team hasn't made progress in {days_idle} days\n\n"
            "Your agents are waiting for direction. This could mean:\n"
            "- Issues are blocked waiting for your input (check `needs-bill` label)\n"
            "- The backlog needs reprioritization\n"
            "- New work items need to be created\n\n"
            "**Quick actions:**\n"
            "- Review open issues at https://bots-in-blazers.fun\n"
            "- Comment on any `needs-bill` issues to unblock agents\n"
            "- Trigger a manual backlog run from the Actions tab\n\n"
            "_Automated nudge from CoE Idle Detection_"
        )

    # Check if a nudge issue already exists (avoid spamming)
    existing = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--label", "nudge-bill",
         "--state", "open", "--json", "number", "--limit", "1"],
        capture_output=True, text=True,
    )
    try:
        if json.loads(existing.stdout):
            log.info("Nudge issue already open — skipping duplicate creation.")
            return
    except Exception:
        pass

    subprocess.run(
        ["gh", "issue", "create", "--repo", REPO,
         "--title", title,
         "--body", body,
         "--label", "needs-bill,nudge-bill,mfg-coe"],
        capture_output=True, text=True,
    )
    log.info("Created nudge issue for Bill.")


def action_daily_wrapup() -> None:
    """Generate end-of-day wrap-up: summarize day's work, post to GitHub and Azure Storage."""
    log.info("=== CoE Daily Wrap-Up ===")
    import subprocess
    from datetime import datetime, timezone, timedelta

    # Gather issues updated today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--label", "mfg-coe",
         "--state", "all", "--json", "number,title,state,labels,updatedAt,comments",
         "--limit", "50"],
        capture_output=True, text=True,
    )

    issues_today = []
    closed_today = []
    needs_bill_open = []

    if result.returncode == 0:
        try:
            all_issues = json.loads(result.stdout)
            for issue in all_issues:
                updated = issue.get("updatedAt", "")[:10]
                if updated == today:
                    issues_today.append(issue)
                if issue.get("state") == "CLOSED" and updated == today:
                    closed_today.append(issue)
                labels = [l["name"] for l in issue.get("labels", [])]
                if "needs-bill" in labels and issue.get("state") == "OPEN":
                    needs_bill_open.append(issue)
        except Exception as e:
            log.error("Could not parse issues: %s", e)

    # Build wrap-up using OpenAI
    try:
        from utils.azure_openai_client import get_openai_client
        client, deployment = get_openai_client()

        closed_str = ', '.join(f'#{i["number"]} {i["title"]}' for i in closed_today) or 'None'
        needs_bill_str = ', '.join(f'#{i["number"]} {i["title"]}' for i in needs_bill_open) or 'None'
        activity_summary = (
            f"Issues touched today: {len(issues_today)}\n"
            f"Issues closed today: {len(closed_today)}\n"
            f"Waiting for Bill's input: {len(needs_bill_open)}\n"
            f"Closed items: {closed_str}\n"
            f"Needs Bill: {needs_bill_str}"
        )

        prompt = (
            "You are the PM Agent for a Discrete Manufacturing AI CoE, writing the daily wrap-up. "
            "Write a concise, upbeat end-of-day summary (5-8 sentences) covering what the team accomplished, "
            "what's in progress, and any items needing Bill's attention. Use emojis. Be specific but brief. "
            "End with a motivational one-liner for tomorrow.\n\n"
            f"Today's activity:\n{activity_summary}"
        )

        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        wrapup_text = response.choices[0].message.content.strip()
    except Exception as e:
        log.error("Could not generate wrap-up with AI: %s", e)
        wrapup_text = (
            f"**Daily Wrap-Up — {today}**\n\n"
            f"- Issues touched: {len(issues_today)}\n"
            f"- Issues closed: {len(closed_today)}\n"
            f"- Needs Bill: {len(needs_bill_open)}"
        )

    # Post as GitHub issue (daily digest)
    issue_body = (
        f"## 📋 CoE Daily Wrap-Up — {today}\n\n"
        f"{wrapup_text}\n\n"
        f"---\n"
        f"**Stats:** {len(issues_today)} issues touched · {len(closed_today)} closed · "
        f"{len(needs_bill_open)} waiting for Bill\n\n"
        f"_Auto-generated by CoE PM Agent at {datetime.now(timezone.utc).strftime('%H:%M UTC')}_"
    )

    subprocess.run(
        ["gh", "issue", "create", "--repo", REPO,
         "--title", f"📋 Daily Wrap-Up — {today}",
         "--body", issue_body,
         "--label", "mfg-coe,daily-digest"],
        capture_output=True, text=True,
    )
    log.info("Posted daily wrap-up issue.")

    # Also save to Azure Storage for web UI
    try:
        from utils.azure_file_storage import AzureFileStorageManager
        storage = AzureFileStorageManager()
        wrapup_record = {
            "date": today,
            "summary": wrapup_text,
            "stats": {
                "issues_touched": len(issues_today),
                "closed": len(closed_today),
                "needs_bill": len(needs_bill_open),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Load existing wrapups
        try:
            existing = json.loads(storage.read_file("coe-community", "daily_wrapups.json") or "[]")
        except Exception:
            existing = []
        existing.append(wrapup_record)
        existing = existing[-30:]  # keep 30 days
        storage.write_file("coe-community", "daily_wrapups.json", json.dumps(existing, indent=2))
        log.info("Saved wrap-up to Azure Storage.")
    except Exception as e:
        log.warning("Could not save wrap-up to storage: %s", e)


def action_community_engage(context: str = "") -> None:
    """Generate a community forum post and save it to Azure Storage."""
    log.info("=== Community Engagement ===")
    try:
        from customers.mfg_coe.agents.mfg_coe_community_agent import MfgCoECommunityAgent
        agent = MfgCoECommunityAgent()
        result_raw = agent.perform(action="generate_post", context=context)
        result = json.loads(result_raw)
        if "post" in result:
            log.info("Community post created: %s", result["post"].get("id"))
            log.info("Category: %s", result["post"].get("category"))
            log.info("Content preview: %s", result["post"].get("content", "")[:120])
        else:
            log.error("Community post failed: %s", result)
    except Exception as e:
        log.error("Community engagement failed: %s", e)


def action_run_backlog(max_tasks: int = 3) -> None:
    """Scan open agent-task issues and process up to max_tasks of them."""
    log.info("=== Running Backlog (max %d tasks) ===", max_tasks)

    # List open mfg-coe issues that aren't blocked on Bill or already done
    result = subprocess.run(
        [
            "gh", "issue", "list",
            "--repo", REPO,
            "--label", "mfg-coe",
            "--state", "open",
            "--json", "number,title,labels",
            "--limit", str(max_tasks),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        log.error("Failed to list issues: %s", result.stderr)
        return

    try:
        all_issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("Could not parse issue list: %s", result.stdout)
        return

    # Skip issues already waiting on Bill, done, or flagged for manual review
    skip_labels = {"needs-bill", "done", "community-post", "daily-digest", "nudge-bill", "coffee-break", "check-existing"}
    issues = [
        i for i in all_issues
        if not any(lbl["name"] in skip_labels for lbl in i.get("labels", []))
    ]

    if not issues:
        log.info("No open agent-task issues found.")
        return

    log.info("Found %d agent-task issues to process", len(issues))
    for issue in issues:
        issue_num = issue["number"]
        log.info("Processing issue #%d: %s", issue_num, issue["title"])
        try:
            action_process_issue(issue_num)
        except Exception as exc:
            log.error("Error processing issue #%d: %s", issue_num, exc)
            _post_issue_comment(
                issue_num,
                f"## ❌ Agent Error\n\nEncountered an error processing this issue:\n\n```\n{exc}\n```\n\nFlagging for Bill.",
            )
            _set_issue_label(issue_num, ["needs-bill"], [])


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Mfg CoE Agent Runner")
    parser.add_argument(
        "--action",
        required=True,
        choices=["standup", "process_issue", "bill_feedback", "health_check", "run_backlog",
                 "daily_wrapup", "idle_check", "community_engage", "library_search",
                 "auto_label", "assign_copilot"],
        help="Action to perform",
    )
    parser.add_argument("--issue", type=int, default=None, help="GitHub issue number")
    parser.add_argument("--comment", type=str, default=None, help="Bill's comment text (for bill_feedback)")
    parser.add_argument("--max", type=int, default=3, help="Max tasks for run_backlog")
    args = parser.parse_args()

    if args.action == "standup":
        action_standup()
    elif args.action == "process_issue":
        if not args.issue:
            parser.error("--issue required for process_issue")
        action_process_issue(args.issue)
    elif args.action == "bill_feedback":
        if not args.issue or not args.comment:
            parser.error("--issue and --comment required for bill_feedback")
        action_bill_feedback(args.issue, args.comment)
    elif args.action == "health_check":
        action_health_check()
    elif args.action == "run_backlog":
        action_run_backlog(args.max)
    elif args.action == "daily_wrapup":
        action_daily_wrapup()
    elif args.action == "idle_check":
        action_idle_check()
    elif args.action == "community_engage":
        action_community_engage(args.comment or "")
    elif args.action == "library_search":
        if not args.issue:
            parser.error("--issue required for library_search")
        from customers.mfg_coe.agents.library_search_agent import run_library_search
        import subprocess as sp
        data_r = sp.run(
            ["gh", "issue", "view", str(args.issue), "--repo", REPO, "--json", "title,body"],
            capture_output=True, text=True,
        )
        if data_r.returncode == 0:
            d = json.loads(data_r.stdout)
            result = run_library_search(args.issue, d.get("title", ""), d.get("body", ""))
            _post_issue_comment(args.issue, result["comment_body"])
            log.info("Library search complete. Strong match: %s", result["strong_match"])
    elif args.action == "auto_label":
        action_auto_label()
    elif args.action == "assign_copilot":
        if not args.issue:
            parser.error("--issue required for assign_copilot")
        action_assign_copilot(args.issue)


if __name__ == "__main__":
    main()
