"""
Test Results Aggregator for the Mfg CoE.

Reads JSONL daily result files and produces:
- Pass/fail counts per customer
- Failure trend analysis
- Summary formatted for the PM Agent weekly digest
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


RESULTS_DIR = Path(__file__).parent.parent / "customers" / "mfg_coe" / "test_results"


def load_daily_results(days_back: int = 7) -> list[dict[str, Any]]:
    """Load all test results from the past N days."""
    all_results = []
    for i in range(days_back):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        results_file = RESULTS_DIR / f"results_{date_str}.jsonl"
        if results_file.exists():
            with open(results_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            all_results.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    return all_results


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce pass/fail summary grouped by customer."""
    summary: dict[str, dict[str, int]] = {}
    failures: list[dict[str, Any]] = []

    for r in results:
        customer = r.get("customer", "unknown")
        status = r.get("status", "unknown")
        if customer not in summary:
            summary[customer] = {"pass": 0, "fail": 0, "partial": 0}
        summary[customer][status] = summary[customer].get(status, 0) + 1
        if status in ("fail", "partial"):
            failures.append(r)

    total = len(results)
    passed = sum(v.get("pass", 0) for v in summary.values())
    failed = sum(v.get("fail", 0) + v.get("partial", 0) for v in summary.values())

    return {
        "total_runs": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "by_customer": summary,
        "failures": failures,
    }


def get_digest_summary(days_back: int = 7) -> str:
    """Return a markdown-formatted test summary for the PM weekly digest."""
    results = load_daily_results(days_back)
    if not results:
        return "No test results found for the past {} days.".format(days_back)

    s = summarize_results(results)

    lines = [
        "## 🎭 Customer Persona Test Results (last {} days)".format(days_back),
        "",
        f"**{s['passed']}/{s['total_runs']} scenarios passing** ({s['pass_rate']}%)",
        "",
        "| Customer | Pass | Fail | Partial |",
        "|---|---|---|---|",
    ]

    for customer, counts in sorted(s["by_customer"].items()):
        lines.append(
            f"| {customer} | {counts.get('pass', 0)} | {counts.get('fail', 0)} | {counts.get('partial', 0)} |"
        )

    if s["failures"]:
        lines += [
            "",
            "### ❌ Failures",
        ]
        for f in s["failures"]:
            lines.append(
                f"- **{f.get('customer')}** / {f.get('scenario_id')} — "
                f"{f.get('failure_reason', 'no reason recorded')} "
                f"(persona: {f.get('persona', 'unknown')})"
            )

    return "\n".join(lines)


def save_aggregated_summary() -> str:
    """Save the current aggregated summary to test_results/latest_summary.json."""
    results = load_daily_results(days_back=30)
    summary = summarize_results(results)
    summary["generated_at"] = datetime.now().isoformat()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / "aggregated_summary.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    return str(out_file)


if __name__ == "__main__":
    print(get_digest_summary())
