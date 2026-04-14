"""
Agent: MfgCoE PM Agent
Purpose: Project Manager for the Discrete Manufacturing CoE.
         Manages backlog, tracks work in progress, generates weekly digests,
         detects conflicts between agent proposals, and assigns work to personas.

Actions:
  plan_sprint          — Identify top N ready backlog items and assign to personas
  get_status           — Current CoE status: open items, in-progress, completed this week
  prioritize_backlog   — Re-order/score open GitHub issues by business value + urgency
  assign_work          — Assign a GitHub issue to a persona (adds label + comment)
  generate_weekly_digest — Summarize last 7 days activity as a new GitHub Issue
  detect_conflicts     — Scan open issues for overlapping/contradictory proposals
  advance_pipeline_stage — Move an idea through stages: raw-idea → use-case → tech-solution → done
"""

import json
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.context_card_loader import load_all_context_cards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO = "kody-w/CommunityRAPP"
COE_LABEL = "mfg-coe"

PIPELINE_STAGES = ["raw-idea", "use-case", "tech-solution", "agent-task", "done"]

PERSONA_LABELS = {
    "pm": "persona:pm",
    "sme": "persona:sme",
    "developer": "persona:developer",
    "architect": "persona:architect",
}


def _gh(args: List[str]) -> Any:
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


class MfgCoEPMAgent(BasicAgent):
    """Project Manager persona for the Mfg CoE."""

    def __init__(self):
        self.name = "MfgCoEPM"
        self.metadata = {
            "name": self.name,
            "description": (
                "Project Manager agent for the Discrete Manufacturing CoE. "
                "Plans sprints, tracks status, generates weekly digests, detects conflicts "
                "between agent proposals, and advances ideas through the pipeline stages. "
                "Ask this agent for CoE status, sprint planning, or to kick off the weekly digest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "plan_sprint",
                            "get_status",
                            "prioritize_backlog",
                            "assign_work",
                            "generate_weekly_digest",
                            "detect_conflicts",
                            "advance_pipeline_stage"
                        ],
                        "description": "PM action to perform"
                    },
                    "sprint_size": {
                        "type": "integer",
                        "description": "Number of items to include in sprint (default: 5)"
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "GitHub Issue number to act on"
                    },
                    "persona": {
                        "type": "string",
                        "enum": ["pm", "sme", "developer", "architect"],
                        "description": "Persona to assign work to"
                    },
                    "target_stage": {
                        "type": "string",
                        "enum": ["raw-idea", "use-case", "tech-solution", "agent-task"],
                        "description": "Pipeline stage to advance to"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for the action"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")
        handlers = {
            "plan_sprint":             self._plan_sprint,
            "get_status":              self._get_status,
            "prioritize_backlog":      self._prioritize_backlog,
            "assign_work":             self._assign_work,
            "generate_weekly_digest":  self._generate_weekly_digest,
            "detect_conflicts":        self._detect_conflicts,
            "advance_pipeline_stage":  self._advance_pipeline_stage,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoEPMAgent error in {action}: {e}")
            return json.dumps({"error": str(e)})

    def _get_all_coe_issues(self, state="open") -> List[Dict]:
        result = _gh([
            "issue", "list", "--repo", REPO,
            "--label", COE_LABEL,
            "--state", state,
            "--limit", "100",
            "--json", "number,title,labels,createdAt,updatedAt,url,body"
        ])
        return result if isinstance(result, list) else []

    def _get_status(self, **kwargs) -> str:
        open_issues = self._get_all_coe_issues("open")
        closed_issues = self._get_all_coe_issues("closed")

        needs_bill = [i for i in open_issues if any(l["name"] == "needs-bill" for l in i.get("labels", []))]
        in_progress = [i for i in open_issues if any(l["name"] in PERSONA_LABELS.values() for l in i.get("labels", []))]

        # Closed in last 7 days
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        completed_recently = [
            i for i in closed_issues
            if i.get("updatedAt", "") >= cutoff
        ]

        by_persona = {}
        for persona, label in PERSONA_LABELS.items():
            count = sum(1 for i in open_issues if any(l["name"] == label for l in i.get("labels", [])))
            if count:
                by_persona[persona] = count

        return json.dumps({
            "as_of": datetime.utcnow().isoformat(),
            "open_items": len(open_issues),
            "needs_bill": len(needs_bill),
            "in_progress": len(in_progress),
            "completed_last_7_days": len(completed_recently),
            "by_persona": by_persona,
            "pending_decisions": [{"number": i["number"], "title": i["title"], "url": i["url"]} for i in needs_bill]
        }, indent=2)

    def _plan_sprint(self, **kwargs) -> str:
        sprint_size = kwargs.get("sprint_size", 5)
        issues = self._get_all_coe_issues("open")

        # Filter out needs-bill (blocked) items
        actionable = [
            i for i in issues
            if not any(l["name"] == "needs-bill" for l in i.get("labels", []))
        ]

        # Priority scoring: p1=3pts, p2=2pts, p3=1pt, raw-idea=0.5pts
        def score(issue):
            label_names = [l["name"] for l in issue.get("labels", [])]
            s = 0
            if "p1-critical" in label_names: s += 3
            elif "p2-high" in label_names: s += 2
            elif "p3-medium" in label_names: s += 1
            if "raw-idea" in label_names: s -= 1
            if "use-case" in label_names: s += 0.5
            if "tech-solution" in label_names: s += 1
            return s

        ranked = sorted(actionable, key=score, reverse=True)[:sprint_size]

        sprint_items = []
        for issue in ranked:
            label_names = [l["name"] for l in issue.get("labels", [])]
            # Auto-suggest persona based on labels
            suggested_persona = "developer"
            if "sop" in label_names or "process" in label_names:
                suggested_persona = "sme"
            elif "tech-solution" in label_names:
                suggested_persona = "architect"
            elif "use-case" in label_names:
                suggested_persona = "sme"

            sprint_items.append({
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "labels": label_names,
                "suggested_persona": suggested_persona,
                "score": score(issue)
            })

        return json.dumps({
            "sprint_size": len(sprint_items),
            "items": sprint_items,
            "recommendation": "Assign these items to their suggested personas and advance each to the appropriate pipeline stage."
        }, indent=2)

    def _prioritize_backlog(self, **kwargs) -> str:
        issues = self._get_all_coe_issues("open")

        def priority_key(issue):
            labels = [l["name"] for l in issue.get("labels", [])]
            score = 0
            if "p1-critical" in labels: score += 100
            elif "p2-high" in labels: score += 50
            elif "p3-medium" in labels: score += 20
            if "needs-bill" in labels: score -= 50  # blocked
            if "tech-solution" in labels: score += 10
            if "use-case" in labels: score += 5
            return score

        ranked = sorted(issues, key=priority_key, reverse=True)
        return json.dumps({
            "total": len(ranked),
            "prioritized": [
                {"number": i["number"], "title": i["title"], "url": i["url"],
                 "labels": [l["name"] for l in i.get("labels", [])]}
                for i in ranked
            ]
        }, indent=2)

    def _assign_work(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        persona = kwargs.get("persona", "developer")
        context = kwargs.get("context", "")

        if not issue_number:
            return json.dumps({"error": "issue_number required"})

        label = PERSONA_LABELS.get(persona, f"persona:{persona}")
        _gh(["issue", "edit", str(issue_number), "--repo", REPO, "--add-label", label])

        comment = f"**📋 Assigned to {persona.upper()} Agent**\n\n{context}\n\n---\n*Assigned by PM Agent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
        _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", comment])

        return json.dumps({"status": "assigned", "issue_number": issue_number, "persona": persona})

    def _generate_weekly_digest(self, **kwargs) -> str:
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        open_issues = self._get_all_coe_issues("open")
        closed_issues = self._get_all_coe_issues("closed")

        needs_bill = [i for i in open_issues if any(l["name"] == "needs-bill" for l in i.get("labels", []))]
        newly_closed = [i for i in closed_issues if i.get("updatedAt", "") >= cutoff]

        # Newly opened this week
        newly_opened = [i for i in open_issues if i.get("createdAt", "") >= cutoff]

        # Build digest body
        lines = [
            f"# 📊 Mfg CoE Weekly Digest — {datetime.utcnow().strftime('%Y-%m-%d')}",
            "",
            f"## ✅ Completed This Week ({len(newly_closed)})",
        ]
        for i in newly_closed:
            lines.append(f"- #{i['number']} {i['title']}")

        lines += [
            "",
            f"## 🆕 New Items This Week ({len(newly_opened)})",
        ]
        for i in newly_opened:
            lines.append(f"- #{i['number']} {i['title']}")

        lines += [
            "",
            f"## 🚨 Pending Bill's Input ({len(needs_bill)})",
        ]
        for i in needs_bill:
            lines.append(f"- #{i['number']} {i['title']} — {i['url']}")
        if not needs_bill:
            lines.append("- None 🎉")

        lines += [
            "",
            f"## 📋 Total Open Backlog: {len(open_issues)}",
            "",
            "---",
            "*Generated by PM Agent*"
        ]

        digest_body = "\n".join(lines)

        result = _gh([
            "issue", "create", "--repo", REPO,
            "--title", f"📊 Weekly CoE Digest — {datetime.utcnow().strftime('%Y-%m-%d')}",
            "--body", digest_body,
            "--label", f"{COE_LABEL},weekly-digest,persona:pm"
        ])

        return json.dumps({
            "status": "digest_created",
            "completed": len(newly_closed),
            "new_items": len(newly_opened),
            "pending_decisions": len(needs_bill),
            "open_backlog": len(open_issues),
            "github_url": result.get("output", "")
        }, indent=2)

    def _detect_conflicts(self, **kwargs) -> str:
        issues = self._get_all_coe_issues("open")
        # Group by keywords in titles to find potential overlaps
        from collections import defaultdict
        keyword_groups = defaultdict(list)
        stopwords = {"the","a","an","for","in","of","to","and","with","or","is","are","on","at"}
        for issue in issues:
            words = [w.lower().strip("[]()") for w in issue["title"].split() if w.lower() not in stopwords and len(w) > 3]
            for word in words:
                keyword_groups[word].append(issue)

        conflicts = []
        for keyword, related in keyword_groups.items():
            if len(related) >= 2:
                unique = {i["number"]: i for i in related}
                if len(unique) >= 2:
                    issues_list = list(unique.values())[:4]
                    conflicts.append({
                        "keyword": keyword,
                        "overlapping_issues": [{"number": i["number"], "title": i["title"]} for i in issues_list]
                    })

        if conflicts:
            # Flag top conflicts
            conflict_body = "## ⚠️ Potential Conflicts Detected\n\nThe PM agent has identified overlapping work items that may conflict:\n\n"
            for c in conflicts[:5]:
                conflict_body += f"**Keyword: `{c['keyword']}`**\n"
                for issue in c["overlapping_issues"]:
                    conflict_body += f"  - #{issue['number']} {issue['title']}\n"
                conflict_body += "\n"
            conflict_body += "\n**Please review and confirm these are not duplicates or contradictory approaches.**"

            result = _gh([
                "issue", "create", "--repo", REPO,
                "--title", f"⚠️ [PM] Potential conflicts detected — review needed",
                "--body", conflict_body,
                "--label", f"{COE_LABEL},needs-bill,conflict,persona:pm,p2-high"
            ])

        return json.dumps({
            "conflicts_found": len(conflicts),
            "details": conflicts[:5],
            "action": "GitHub issue created for Bill's review" if conflicts else "No conflicts detected"
        }, indent=2)

    def _advance_pipeline_stage(self, **kwargs) -> str:
        issue_number = kwargs.get("issue_number")
        target_stage = kwargs.get("target_stage", "use-case")

        if not issue_number:
            return json.dumps({"error": "issue_number required"})

        # Remove previous stage labels and add new one
        previous_stages = [s for s in PIPELINE_STAGES if s != target_stage and s != "done"]
        for stage in previous_stages:
            _gh(["issue", "edit", str(issue_number), "--repo", REPO, "--remove-label", stage])

        _gh(["issue", "edit", str(issue_number), "--repo", REPO, "--add-label", target_stage])

        comment = f"**🔄 Pipeline Stage Advanced**\n\nThis item has been moved to: **`{target_stage}`**\n\n---\n*Advanced by PM Agent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
        _gh(["issue", "comment", str(issue_number), "--repo", REPO, "--body", comment])

        return json.dumps({"status": "advanced", "issue_number": issue_number, "new_stage": target_stage})
