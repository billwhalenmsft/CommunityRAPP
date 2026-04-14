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

    # If there are agent-task issues to process, run them
    open_tasks = result.get("open_agent_tasks", [])
    if open_tasks:
        log.info("Found %d open agent-task issues — processing...", len(open_tasks))
        for issue_num in open_tasks[:3]:  # cap at 3 per standup to avoid runaway
            action_process_issue(issue_num)
    else:
        log.info("No open agent-task issues found.")


def action_process_issue(issue_number: int) -> None:
    """Route and execute a single GitHub issue as a CoE task."""
    log.info("=== Processing Issue #%d ===", issue_number)
    coe = _load_orchestrator()
    result_raw = coe.perform(action="run_pipeline_item", issue_number=issue_number)
    result = json.loads(result_raw)

    status = result.get("status", "unknown")
    summary = result.get("summary", str(result))

    log.info("Issue #%d result: %s", issue_number, status)

    # Build comment body
    if status == "needs_bill":
        comment_body = (
            "## 🤔 Agent needs your input\n\n"
            f"{result.get('question', 'The agent has a question before proceeding.')}\n\n"
            "**Please comment with your direction.** I'll pick it up and continue.\n\n"
            f"_Agent: {result.get('persona', 'orchestrator')} | Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
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
            + f"_Agent: {result.get('persona', 'orchestrator')} | Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
        )
        _post_issue_comment(issue_number, comment_body)
        _set_issue_label(issue_number, ["done"], ["agent-task"])
        _close_issue(issue_number)

    else:
        comment_body = (
            "## ⚠️ Agent Update\n\n"
            f"Status: `{status}`\n\n"
            f"{summary}\n\n"
            f"_Agent: {result.get('persona', 'orchestrator')} | Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
        )
        _post_issue_comment(issue_number, comment_body)


def action_bill_feedback(issue_number: int, comment: str) -> None:
    """Process Bill's comment and resume work on an issue."""
    log.info("=== Processing Bill's Feedback on Issue #%d ===", issue_number)
    coe = _load_orchestrator()
    result_raw = coe.perform(
        action="process_bill_feedback",
        feedback=comment,
        issue_number=issue_number,
    )
    result = json.loads(result_raw)

    log.info("Feedback processed: %s", json.dumps(result, indent=2))

    # Route to the appropriate agent based on feedback
    routed_action = result.get("routed_action")
    if routed_action:
        comment_body = (
            "## 🔄 Feedback received — resuming work\n\n"
            f"Understood: _{result.get('interpretation', comment)}_\n\n"
            f"Routing to **{result.get('routed_persona', 'agent')}** to: {routed_action}\n\n"
            f"_Run ID: GHA_{os.environ.get('GITHUB_RUN_ID', 'local')}_"
        )
        _post_issue_comment(issue_number, comment_body)
        _set_issue_label(issue_number, ["agent-task"], ["needs-bill"])
        # Re-process the issue now with direction
        action_process_issue(issue_number)
    else:
        log.warning("No routed action determined from feedback")


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


def action_run_backlog(max_tasks: int = 3) -> None:
    """Scan open agent-task issues and process up to max_tasks of them."""
    log.info("=== Running Backlog (max %d tasks) ===", max_tasks)

    # List open agent-task issues
    result = subprocess.run(
        [
            "gh", "issue", "list",
            "--repo", REPO,
            "--label", "agent-task",
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
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("Could not parse issue list: %s", result.stdout)
        return

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
            _set_issue_label(issue_num, ["needs-bill"], ["agent-task"])


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Mfg CoE Agent Runner")
    parser.add_argument(
        "--action",
        required=True,
        choices=["standup", "process_issue", "bill_feedback", "health_check", "run_backlog"],
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


if __name__ == "__main__":
    main()
