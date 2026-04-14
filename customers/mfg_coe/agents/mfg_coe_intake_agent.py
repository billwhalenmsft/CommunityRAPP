"""
Agent: MfgCoE Intake Agent
Purpose: Captures ideas, feature requests, and solutions for the Discrete Manufacturing CoE.
         Logs everything to GitHub Issues + Azure File Storage.
         Flags items needing Bill's input with 'needs-bill' label.
         Serves as the memory/log backbone for the entire CoE.

Actions:
  log_idea          — Create a new GitHub Issue for an idea or feature request
  log_solution      — Log a completed solution as a comment on an existing issue (or new issue)
  flag_for_bill     — Add 'needs-bill' label + comment to an issue requesting Bill's direction
  get_backlog       — List open mfg-coe GitHub Issues (with optional persona/label filter)
  get_pending_decisions — List issues with 'needs-bill' label awaiting input
  log_decision      — Record Bill's steering decision to Azure storage + close needs-bill flag
  search_backlog    — Search issues by keyword
  get_solutions_log — Retrieve solution log entries from Azure storage
  load_context_card — Load a demo environment context card by name
"""

import json
import logging
import os
import subprocess
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from agents.basic_agent import BasicAgent
from utils.storage_factory import get_storage_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO = "kody-w/CommunityRAPP"
COE_LABEL = "mfg-coe"
NEEDS_BILL_LABEL = "needs-bill"
COE_STORAGE_DIR = "mfg_coe"
KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(__file__), "knowledge_base"
)


def _gh(args: List[str]) -> Dict[str, Any]:
    """Call gh CLI and return parsed JSON or raw text."""
    cmd = ["gh"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}


class MfgCoEIntakeAgent(BasicAgent):
    """
    Intake and Logger Agent for the Discrete Manufacturing CoE.
    All agent activity — ideas, solutions, decisions, escalations — flows through here.
    """

    def __init__(self):
        self.name = "MfgCoEIntake"
        self.metadata = {
            "name": self.name,
            "description": (
                "Intake and logging agent for the Discrete Manufacturing Center of Excellence. "
                "Captures ideas, logs solutions, flags items needing Bill's input via GitHub Issues, "
                "records steering decisions, and loads demo environment context cards. "
                "All CoE agent activity should be logged through this agent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "log_idea",
                            "log_solution",
                            "flag_for_bill",
                            "get_backlog",
                            "get_pending_decisions",
                            "log_decision",
                            "search_backlog",
                            "get_solutions_log",
                            "load_context_card"
                        ],
                        "description": "Action to perform"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for a new idea/issue"
                    },
                    "body": {
                        "type": "string",
                        "description": "Full description, solution details, or decision content"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional GitHub labels (e.g. ['sop','persona:sme','p2-high'])"
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "GitHub Issue number to act on"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["pm", "sme", "developer", "architect", "customer_persona"],
                        "description": "Which CoE persona is logging this item"
                    },
                    "question_for_bill": {
                        "type": "string",
                        "description": "Specific question or decision needed from Bill"
                    },
                    "decision": {
                        "type": "string",
                        "description": "Bill's decision or direction to record"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Keyword to search in backlog issues"
                    },
                    "context_card": {
                        "type": "string",
                        "enum": ["master_ce_mfg", "mfg_gold_template"],
                        "description": "Demo environment context card to load"
                    },
                    "filter_label": {
                        "type": "string",
                        "description": "Filter backlog by additional label"
                    }
                },
                "required": ["action"]
            }
        }
        self.storage = get_storage_manager()
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_backlog")
        handlers = {
            "log_idea":              self._log_idea,
            "log_solution":          self._log_solution,
            "flag_for_bill":         self._flag_for_bill,
            "get_backlog":           self._get_backlog,
            "get_pending_decisions": self._get_pending_decisions,
            "log_decision":          self._log_decision,
            "search_backlog":        self._search_backlog,
            "get_solutions_log":     self._get_solutions_log,
            "load_context_card":     self._load_context_card,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoEIntakeAgent error in {action}: {e}")
            return json.dumps({"error": str(e)})

    # ── Log Idea ──────────────────────────────────────────────────

    def _log_idea(self, **kwargs) -> str:
        title = kwargs.get("title", "Untitled Idea")
        body = kwargs.get("body", "")
        persona = kwargs.get("persona", "")
        extra_labels = kwargs.get("labels", [])

        labels = [COE_LABEL, "raw-idea", "agent-task"]
        if persona:
            labels.append(f"persona:{persona}")
        labels.extend(extra_labels)

        label_args = []
        for l in labels:
            label_args += ["--label", l]

        result = _gh(
            ["issue", "create",
             "--repo", REPO,
             "--title", title,
             "--body", self._enrich_body(body, persona, "idea"),
             ] + label_args
        )

        if "error" in result:
            return json.dumps({"status": "error", "detail": result["error"]})

        url = result.get("output", result.get("url", ""))
        issue_number = self._extract_issue_number(url)

        self._write_to_storage("backlog", {
            "id": str(uuid.uuid4()),
            "type": "idea",
            "title": title,
            "body": body,
            "persona": persona,
            "github_issue": issue_number,
            "github_url": url,
            "created_at": datetime.now().isoformat()
        })

        return json.dumps({
            "status": "logged",
            "type": "idea",
            "github_url": url,
            "issue_number": issue_number,
            "labels": labels
        })

    # ── Log Solution ───────────────────────────────────────────────

    def _log_solution(self, **kwargs) -> str:
        body = kwargs.get("body", "")
        persona = kwargs.get("persona", "")
        issue_number = kwargs.get("issue_number")
        title = kwargs.get("title", "Solution Log")

        solution_record = {
            "id": str(uuid.uuid4()),
            "type": "solution",
            "title": title,
            "body": body,
            "persona": persona,
            "created_at": datetime.now().isoformat()
        }

        if issue_number:
            comment_body = f"## ✅ Solution Logged\n\n**By:** {persona or 'CoE Agent'}\n\n{body}\n\n---\n*Logged at {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*"
            result = _gh([
                "issue", "comment", str(issue_number),
                "--repo", REPO,
                "--body", comment_body
            ])
            if "error" not in result:
                _gh(["issue", "close", str(issue_number), "--repo", REPO,
                     "--comment", "Closing — solution has been logged above."])
            solution_record["github_issue"] = issue_number
        else:
            # Create a new closed issue as a solution record
            labels = [COE_LABEL, "tech-solution"]
            if persona:
                labels.append(f"persona:{persona}")
            label_args = []
            for l in labels:
                label_args += ["--label", l]
            result = _gh([
                "issue", "create", "--repo", REPO,
                "--title", f"[Solution] {title}",
                "--body", self._enrich_body(body, persona, "solution"),
            ] + label_args)
            url = result.get("output", "")
            solution_record["github_url"] = url

        self._write_to_storage("solutions_log", solution_record)

        return json.dumps({
            "status": "logged",
            "type": "solution",
            "record": solution_record
        })

    # ── Flag for Bill ──────────────────────────────────────────────

    def _flag_for_bill(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        question = kwargs.get("question_for_bill", "")
        body = kwargs.get("body", "")
        persona = kwargs.get("persona", "")

        if not issue_number:
            # Create a new issue
            title = kwargs.get("title", "Decision needed")
            labels = [COE_LABEL, NEEDS_BILL_LABEL, "decision-needed"]
            if persona:
                labels.append(f"persona:{persona}")
            label_args = []
            for l in labels:
                label_args += ["--label", l]

            comment = f"## 🚨 Bill's Input Needed\n\n{body}\n\n**Question:** {question}\n\n---\n*Flagged by {persona or 'CoE Agent'} at {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*"
            result = _gh([
                "issue", "create", "--repo", REPO,
                "--title", title,
                "--body", comment,
            ] + label_args)
            url = result.get("output", "")
            issue_number = self._extract_issue_number(url)
            return json.dumps({"status": "flagged", "github_url": url, "issue_number": issue_number})
        else:
            # Add comment + label to existing issue
            comment = f"## 🚨 Bill's Input Needed\n\n{question or body}\n\n---\n*Flagged by {persona or 'CoE Agent'} at {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*"
            _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", comment])
            _gh(["issue", "edit", str(issue_number), "--repo", REPO,
                 "--add-label", NEEDS_BILL_LABEL, "--add-label", "decision-needed"])
            return json.dumps({"status": "flagged", "issue_number": issue_number})

    # ── Get Backlog ────────────────────────────────────────────────

    def _get_backlog(self, **kwargs) -> str:
        filter_label = kwargs.get("filter_label", "")
        labels = COE_LABEL
        if filter_label:
            labels = f"{COE_LABEL},{filter_label}"

        result = _gh([
            "issue", "list", "--repo", REPO,
            "--label", labels,
            "--state", "open",
            "--limit", "50",
            "--json", "number,title,labels,createdAt,url,body"
        ])

        if "error" in result:
            return json.dumps({"error": result["error"]})

        issues = result if isinstance(result, list) else []
        summary = []
        for issue in issues:
            label_names = [l["name"] for l in issue.get("labels", [])]
            summary.append({
                "number": issue["number"],
                "title": issue["title"],
                "labels": label_names,
                "url": issue["url"],
                "created_at": issue.get("createdAt", "")
            })

        return json.dumps({
            "open_issues": len(summary),
            "items": summary
        }, indent=2)

    # ── Get Pending Decisions ──────────────────────────────────────

    def _get_pending_decisions(self, **kwargs) -> str:
        result = _gh([
            "issue", "list", "--repo", REPO,
            "--label", f"{COE_LABEL},{NEEDS_BILL_LABEL}",
            "--state", "open",
            "--limit", "20",
            "--json", "number,title,labels,createdAt,url,body"
        ])

        if "error" in result:
            return json.dumps({"error": result["error"]})

        issues = result if isinstance(result, list) else []
        items = []
        for issue in issues:
            items.append({
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "created_at": issue.get("createdAt", ""),
                "preview": (issue.get("body") or "")[:200]
            })

        return json.dumps({
            "pending_decisions": len(items),
            "message": "These issues need Bill's input before agents can proceed.",
            "items": items
        }, indent=2)

    # ── Log Decision ───────────────────────────────────────────────

    def _log_decision(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        decision = kwargs.get("decision", "")
        body = kwargs.get("body", "")

        if not decision and not body:
            return json.dumps({"error": "decision or body content required"})

        decision_text = decision or body
        decision_record = {
            "id": str(uuid.uuid4()),
            "type": "decision",
            "decision": decision_text,
            "github_issue": issue_number,
            "recorded_at": datetime.now().isoformat()
        }

        if issue_number:
            comment = f"## ✅ Decision Logged\n\n{decision_text}\n\n---\n*Decision recorded at {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC. Removing needs-bill flag — agents may proceed.*"
            _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", comment])
            _gh(["issue", "edit", str(issue_number), "--repo", REPO,
                 "--remove-label", NEEDS_BILL_LABEL, "--remove-label", "decision-needed"])

        self._write_to_storage("decisions", decision_record)

        return json.dumps({
            "status": "decision_logged",
            "record": decision_record
        })

    # ── Search Backlog ─────────────────────────────────────────────

    def _search_backlog(self, **kwargs) -> str:
        query = kwargs.get("search_query", "")
        if not query:
            return json.dumps({"error": "search_query required"})

        result = _gh([
            "issue", "list", "--repo", REPO,
            "--label", COE_LABEL,
            "--state", "open",
            "--limit", "100",
            "--json", "number,title,labels,url,body"
        ])

        issues = result if isinstance(result, list) else []
        q = query.lower()
        matches = [
            {
                "number": i["number"],
                "title": i["title"],
                "url": i["url"],
                "labels": [l["name"] for l in i.get("labels", [])]
            }
            for i in issues
            if q in i.get("title", "").lower() or q in (i.get("body") or "").lower()
        ]

        return json.dumps({"query": query, "matches": len(matches), "items": matches}, indent=2)

    # ── Get Solutions Log ──────────────────────────────────────────

    def _get_solutions_log(self, **kwargs) -> str:
        try:
            entries = self._read_from_storage("solutions_log")
            return json.dumps({"solutions": len(entries), "items": entries}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ── Load Context Card ──────────────────────────────────────────

    def _load_context_card(self, **kwargs) -> str:
        card_name = kwargs.get("context_card", "master_ce_mfg")
        card_file = os.path.join(
            os.path.dirname(__file__), "..", "customers", "mfg_coe",
            "knowledge_base", f"{card_name}.md"
        )
        card_file = os.path.normpath(card_file)
        if not os.path.exists(card_file):
            return json.dumps({"error": f"Context card not found: {card_name}"})
        with open(card_file, "r", encoding="utf-8") as f:
            content = f.read()
        return json.dumps({"context_card": card_name, "content": content})

    # ── Helpers ────────────────────────────────────────────────────

    def _enrich_body(self, body: str, persona: str, item_type: str) -> str:
        header = f"**Type:** {item_type.title()}  \n**CoE Persona:** {persona or 'CoE Agent'}  \n**Logged:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n\n---\n\n"
        return header + body

    def _extract_issue_number(self, url: str) -> Optional[int]:
        try:
            return int(url.rstrip("/").split("/")[-1])
        except Exception:
            return None

    def _write_to_storage(self, subdir: str, record: Dict) -> None:
        try:
            filename = f"{subdir}/{record.get('id', str(uuid.uuid4()))}.json"
            self.storage.write_file(COE_STORAGE_DIR, filename, json.dumps(record, indent=2))
        except Exception as e:
            logger.warning(f"Storage write failed for {subdir}: {e}")

    def _read_from_storage(self, subdir: str) -> List[Dict]:
        try:
            files = self.storage.list_files(COE_STORAGE_DIR, prefix=subdir)
            results = []
            for f in files or []:
                content = self.storage.read_file(COE_STORAGE_DIR, f)
                if content:
                    results.append(json.loads(content))
            return results
        except Exception as e:
            logger.warning(f"Storage read failed for {subdir}: {e}")
            return []
