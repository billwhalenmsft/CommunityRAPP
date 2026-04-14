# Test Results

This folder stores all Playwright test run outputs for Mfg CoE customer scenarios.

## Files

| File | Description |
|---|---|
| `results_YYYY-MM-DD.jsonl` | Daily test run records (one JSON object per line) |
| `playwright_results.json` | Latest Playwright JSON reporter output |
| `aggregated_summary.json` | 30-day rolling aggregated summary |
| `latest_summary.json` | Running summary per customer |
| `aggregate_results.py` | Aggregator utility — reads JSONL files, produces digest markdown |

## Viewing Results

```bash
# Generate digest (markdown summary)
python customers/mfg_coe/test_results/aggregate_results.py

# View Playwright HTML report (after running tests)
cd tests/playwright && npx playwright show-report
```

## PM Agent Integration

The PM Agent's `generate_weekly_digest` action calls `aggregate_results.get_digest_summary()` 
to include pass/fail counts in the weekly GitHub digest issue.

## Structure of Each Result Record

```json
{
  "customer": "navico",
  "scenario_id": "navico_warranty_check",
  "scenario_title": "Warranty Status Check",
  "persona": "dealer_rep",
  "status": "pass",
  "conversation": [
    { "role": "user", "text": "check warranty", "timestamp": "..." },
    { "role": "bot", "text": "I can help...", "timestamp": "..." }
  ],
  "failure_reason": null,
  "screenshot_path": null,
  "duration_ms": 12340,
  "timestamp": "2026-04-14T12:00:00.000Z"
}
```
