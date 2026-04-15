"""
Agent: MfgCoE QA Engineer Agent
Purpose: QA / Test Engineer persona for the Discrete Manufacturing CoE.
         Owns structured test case generation, regression test planning,
         acceptance criteria verification, and coverage reporting.
         Works from the outcome definition and acceptance criteria —
         tests prove outcomes were delivered, not just features built.

         Distinct from Customer Persona agent (which simulates users).
         QA Engineer does structured testing: test cases, coverage, regression,
         edge cases, and verification that acceptance criteria are met.

Actions:
  generate_test_cases    — Generate structured test cases from acceptance criteria
  create_test_plan       — Full test plan for a feature or issue
  verify_acceptance      — Check if acceptance criteria are met given a summary
  generate_regression    — Regression test checklist for a change
  edge_cases             — Enumerate edge cases for a use case
  coverage_report        — Report test coverage status for open issues
  write_test_script      — Write a Playwright or manual test script
  get_testing_standards  — Return CoE testing standards
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TESTING_STANDARDS = {
    "coverage": [
        "Every outcome definition must have at least 3 test cases before closing",
        "All acceptance criteria items must have a corresponding test case",
        "Happy path + at least 2 negative/edge cases required per feature",
        "Copilot Studio topics need: trigger phrase tests, fallback tests, escalation tests",
    ],
    "test_types": {
        "functional": "Does it do what the outcome definition says?",
        "acceptance": "Does it meet all acceptance criteria from the outcome definition?",
        "regression": "Did the change break anything that was working before?",
        "ux": "Can the target user complete the primary task without assistance?",
        "edge_case": "What happens with empty inputs, long text, invalid data, timeouts?",
        "security": "Coordinate with Security Reviewer for auth and data exposure checks",
    },
    "definition_of_tested": [
        "All acceptance criteria verified",
        "Happy path passes",
        "At least 2 edge/negative cases documented and pass",
        "No HIGH-severity findings from Security Reviewer",
        "UX review checklist complete",
        "Demo story can be walked through without manual workarounds",
    ],
}


class MfgCoEQAEngineerAgent(BasicAgent):
    """
    QA Engineer — generates test cases, test plans, and regression checklists
    from outcome definitions and acceptance criteria. Tests prove outcomes were
    delivered. Works with Outcome Validator to provide the evidence needed for
    a 80+ validation score.
    """

    def __init__(self):
        self.name = "MfgCoEQAEngineer"
        self.metadata = {
            "name": self.name,
            "description": (
                "QA Engineer agent — generates structured test cases, test plans, "
                "regression checklists, and edge case enumerations from outcome definitions. "
                "Tests prove outcomes were delivered, not just features built. "
                "Works with Outcome Validator to provide evidence for sign-off."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "generate_test_cases",
                            "create_test_plan",
                            "verify_acceptance",
                            "generate_regression",
                            "edge_cases",
                            "coverage_report",
                            "write_test_script",
                            "get_testing_standards",
                        ],
                        "description": "QA action to perform",
                    },
                    "issue_number": {"type": "integer", "description": "GitHub issue number"},
                    "feature_name": {"type": "string", "description": "Feature or use case name"},
                    "acceptance_criteria": {"type": "string", "description": "Acceptance criteria text from outcome definition"},
                    "artifact_summary": {"type": "string", "description": "Summary of what was built"},
                    "scenario_type": {
                        "type": "string",
                        "enum": ["copilot_studio", "power_app", "d365_workflow", "azure_function", "web_ui"],
                        "description": "Type of scenario to test",
                    },
                    "context": {"type": "string", "description": "Additional context"},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_testing_standards")
        handlers = {
            "generate_test_cases": self._generate_test_cases,
            "create_test_plan": self._create_test_plan,
            "verify_acceptance": self._verify_acceptance,
            "generate_regression": self._generate_regression,
            "edge_cases": self._edge_cases,
            "coverage_report": self._coverage_report,
            "write_test_script": self._write_test_script,
            "get_testing_standards": self._get_testing_standards,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("QAEngineer error in %s: %s", action, e)
            return json.dumps({"error": str(e)})

    def _generate_test_cases(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        acceptance = kwargs.get("acceptance_criteria", "")
        scenario_type = kwargs.get("scenario_type", "copilot_studio")

        # Parse acceptance criteria into test cases
        ac_lines = [l.strip("- [x] - [ ] ").strip() for l in acceptance.split("\n") if l.strip() and len(l.strip()) > 10]

        test_cases = []
        for i, ac in enumerate(ac_lines[:5], 1):
            test_cases.append({
                "id": f"TC-{i:02d}",
                "type": "acceptance",
                "description": ac,
                "steps": [
                    "Set up test preconditions",
                    f"Execute: {ac[:80]}",
                    "Verify expected result",
                ],
                "expected": "Acceptance criterion is visibly satisfied",
                "status": "not_run",
            })

        # Add standard test cases by scenario type
        scenario_tests = {
            "copilot_studio": [
                {"id": "TC-H1", "type": "happy_path", "description": "User sends trigger phrase and receives correct response", "status": "not_run"},
                {"id": "TC-N1", "type": "negative", "description": "User sends an unrecognized input — fallback topic fires correctly", "status": "not_run"},
                {"id": "TC-N2", "type": "negative", "description": "User asks to escalate mid-conversation — escalation flow triggers", "status": "not_run"},
            ],
            "power_app": [
                {"id": "TC-H1", "type": "happy_path", "description": "Form submits successfully with valid data", "status": "not_run"},
                {"id": "TC-N1", "type": "negative", "description": "Form submitted with empty required fields — error shown", "status": "not_run"},
                {"id": "TC-E1", "type": "edge_case", "description": "Very long text input (>500 chars) — no crash or data loss", "status": "not_run"},
            ],
            "web_ui": [
                {"id": "TC-H1", "type": "happy_path", "description": "Primary task completed in < 3 clicks", "status": "not_run"},
                {"id": "TC-N1", "type": "negative", "description": "API call fails — error state shown, not blank screen", "status": "not_run"},
                {"id": "TC-E1", "type": "edge_case", "description": "Mobile viewport (375px) — layout not broken", "status": "not_run"},
            ],
        }
        test_cases.extend(scenario_tests.get(scenario_type, scenario_tests["copilot_studio"]))

        tc_md = "\n".join(
            f"| {tc['id']} | {tc['type']} | {tc['description'][:60]} | {tc['status']} |"
            for tc in test_cases
        )

        return json.dumps({
            "status": "ok",
            "feature": feature,
            "test_case_count": len(test_cases),
            "test_cases": test_cases,
            "test_cases_markdown": (
                f"## Test Cases: {feature}\n\n"
                f"| ID | Type | Description | Status |\n"
                f"|----|----|-------------|--------|\n"
                f"{tc_md}\n\n"
                f"*{len(test_cases)} test cases. Run all before moving to outcome-validated.*"
            ),
            "summary": f"{len(test_cases)} test cases generated for: {feature}",
            "persona": "qa-engineer",
        }, indent=2)

    def _create_test_plan(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        scenario_type = kwargs.get("scenario_type", "copilot_studio")
        date = datetime.utcnow().strftime("%Y-%m-%d")

        plan = (
            f"# Test Plan: {feature}\n\n"
            f"**Date:** {date}\n"
            f"**Scenario Type:** {scenario_type}\n"
            f"**Status:** Draft\n\n"
            f"## Scope\n\n"
            f"Test the outcome defined in the issue. Focus: does it solve the business user's problem?\n\n"
            f"## Test Types Required\n\n"
            + "\n".join(f"- **{k.title()}**: {v}" for k, v in TESTING_STANDARDS["test_types"].items()) + "\n\n"
            f"## Entry Criteria\n\n"
            f"- [ ] Outcome definition confirmed by Bill\n"
            f"- [ ] Feature built and deployed to dev environment\n"
            f"- [ ] Security Reviewer has signed off\n"
            f"- [ ] UX review complete\n\n"
            f"## Exit Criteria\n\n"
            + "\n".join(f"- [ ] {c}" for c in TESTING_STANDARDS["definition_of_tested"]) + "\n\n"
            f"## Test Environment\n\n"
            f"- Master CE Mfg (`a3140474-230b-ee2b-8dd8-605a8fe08913`)\n"
            f"- Or Mfg Gold Template (`2404ccaf-d7e5-e1ff-863a-3ecbe2f0f013`)\n\n"
            f"---\n*QA Engineer Agent | {date}*"
        )

        return json.dumps({
            "status": "ok",
            "summary": f"Test plan created for: {feature}",
            "plan": plan,
            "persona": "qa-engineer",
        }, indent=2)

    def _verify_acceptance(self, **kwargs) -> str:
        acceptance = kwargs.get("acceptance_criteria", "")
        artifact = kwargs.get("artifact_summary", "")
        feature = kwargs.get("feature_name", "Feature")

        ac_lines = [l.strip("- [x] - [ ] ").strip() for l in acceptance.split("\n") if l.strip() and len(l.strip()) > 10]
        # Without live test results, generate verification checklist
        items = [{"criterion": ac, "verified": None, "note": "Manual verification required"} for ac in ac_lines]

        items_md = "\n".join(f"- ⬜ {item['criterion']}" for item in items)
        verified_count = sum(1 for i in items if i["verified"] is True)
        status = "verified" if verified_count == len(items) and items else "pending_verification"

        return json.dumps({
            "status": status,
            "total_criteria": len(items),
            "verified": verified_count,
            "pending": len(items) - verified_count,
            "items": items,
            "summary": f"Acceptance verification: {verified_count}/{len(items)} criteria verified. {len(items) - verified_count} pending manual check.",
            "checklist": f"## Acceptance Verification: {feature}\n\n{items_md}",
            "persona": "qa-engineer",
        }, indent=2)

    def _generate_regression(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Change")
        context = kwargs.get("context", "")

        regression_items = [
            "Existing Copilot Studio topics still trigger correctly",
            "Outcome Framer pipeline still blocks on low-confidence issues",
            "GitHub issue comments are still formatted as markdown (not raw dict)",
            "CoE web UI loads without JS errors",
            "Authentication (GitHub OAuth) still works on bots-in-blazers.fun",
            "Daily Standup + Hourly Pulse workflows complete without errors",
            "Azure Function App returns 200 on health check",
            "D365 environment context cards still load in agents",
        ]

        if context:
            regression_items.append(f"Verify no regression in: {context}")

        items_md = "\n".join(f"- [ ] {item}" for item in regression_items)

        return json.dumps({
            "status": "ok",
            "summary": f"Regression checklist for: {feature}. {len(regression_items)} items.",
            "checklist": f"## Regression Checklist: {feature}\n\n{items_md}",
            "items": regression_items,
            "persona": "qa-engineer",
        }, indent=2)

    def _edge_cases(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        scenario_type = kwargs.get("scenario_type", "copilot_studio")

        common_edge_cases = [
            "Empty input / no text submitted",
            "Input exceeds maximum length",
            "Special characters in input (&, <, >, quotes, emoji)",
            "Network timeout during API call",
            "User is unauthenticated / session expired",
            "Concurrent requests from same user",
            "Mobile device with slow connection",
            "Browser back button after form submission",
        ]

        scenario_edge_cases = {
            "copilot_studio": [
                "User interrupts mid-topic with an off-topic question",
                "User sends the trigger phrase twice in a row",
                "Session times out mid-conversation",
                "User provides invalid serial number / unknown product",
            ],
            "web_ui": [
                "JavaScript disabled",
                "Very long GitHub issue title (> 200 chars)",
                "GitHub API rate limit hit",
                "User scrolls past 100 issues in backlog",
            ],
            "power_app": [
                "Dataverse connection drops mid-form",
                "User submits while offline (PWA)",
                "Two users edit the same record simultaneously",
            ],
        }

        edges = common_edge_cases + scenario_edge_cases.get(scenario_type, [])
        edges_md = "\n".join(f"- ⬜ {e}" for e in edges)

        return json.dumps({
            "status": "ok",
            "summary": f"{len(edges)} edge cases for: {feature} ({scenario_type})",
            "edge_cases": edges,
            "checklist": f"## Edge Cases: {feature}\n\n{edges_md}",
            "persona": "qa-engineer",
        }, indent=2)

    def _coverage_report(self, **kwargs) -> str:
        return json.dumps({
            "status": "ok",
            "summary": "Coverage report requires live GitHub issue + test result data. Run from coe_runner.py after issue data is loaded.",
            "schema": {
                "total_open_issues": None,
                "issues_with_test_cases": None,
                "issues_with_all_ac_verified": None,
                "coverage_pct": None,
                "uncovered_issues": [],
            },
            "persona": "qa-engineer",
        }, indent=2)

    def _write_test_script(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        scenario_type = kwargs.get("scenario_type", "web_ui")

        if scenario_type == "web_ui":
            script = (
                f"```javascript\n"
                f"// Playwright test: {feature}\n"
                f"const {{ test, expect }} = require('@playwright/test');\n\n"
                f"test('{feature} — happy path', async ({{ page }}) => {{\n"
                f"  await page.goto('https://bots-in-blazers.fun');\n"
                f"  // TODO: Add authentication step\n"
                f"  await page.click('text=[Primary action]');\n"
                f"  await expect(page.locator('[Expected element]')).toBeVisible();\n"
                f"}});\n\n"
                f"test('{feature} — error state', async ({{ page }}) => {{\n"
                f"  await page.goto('https://bots-in-blazers.fun');\n"
                f"  // Simulate error condition\n"
                f"  await page.route('**/api/**', route => route.abort());\n"
                f"  await page.click('text=[Primary action]');\n"
                f"  await expect(page.locator('[Error message]')).toBeVisible();\n"
                f"}});\n"
                f"```"
            )
        else:
            script = (
                f"## Manual Test Script: {feature}\n\n"
                f"**Environment:** Master CE Mfg\n"
                f"**Tester:** [Name]\n"
                f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
                f"### Setup\n1. Log into [environment]\n2. Navigate to [starting point]\n\n"
                f"### Test Steps\n"
                f"| # | Action | Expected Result | Pass/Fail |\n"
                f"|---|--------|----------------|----------|\n"
                f"| 1 | [Action] | [Expected] | ⬜ |\n"
                f"| 2 | [Action] | [Expected] | ⬜ |\n\n"
                f"### Pass Criteria\nAll rows = ✅ AND outcome demo story walkthrough completes without workarounds."
            )

        return json.dumps({
            "status": "ok",
            "summary": f"Test script created for: {feature} ({scenario_type})",
            "script": script,
            "persona": "qa-engineer",
        }, indent=2)

    def _get_testing_standards(self, **kwargs) -> str:
        dod_md = "\n".join(f"- {s}" for s in TESTING_STANDARDS["definition_of_tested"])
        coverage_md = "\n".join(f"- {s}" for s in TESTING_STANDARDS["coverage"])
        return json.dumps({
            "status": "ok",
            "standards": TESTING_STANDARDS,
            "summary": f"Testing standards returned. {len(TESTING_STANDARDS['definition_of_tested'])} definition-of-tested criteria.",
            "markdown": (
                f"## CoE Testing Standards\n\n"
                f"### Definition of Tested\n{dod_md}\n\n"
                f"### Coverage Requirements\n{coverage_md}"
            ),
            "persona": "qa-engineer",
        }, indent=2)
