# Task: Fix Ascend SAP Procurement Agent Topic Errors

**Assigned to:** Bots-in-Blazers / Mfg CoE agent team
**Status:** Open — ready to pick up
**Skill to use:** `customers/mfg_coe/skills/copilot-studio-binding-sync` ← READ THIS FIRST

## Context

Copilot Studio agent **"Ascend SAP Procurement Agent"** has 8 topics calling 6 PA flows. Vendor Lookup works E2E. The other 7 topics show **13 Topic Errors + 13 Other Errors** in the publish dialog.

## Environment

| Field | Value |
|---|---|
| Org URL | `https://org6feab6b5.crm.dynamics.com` |
| Bot ID | `a1aa62dd-a23d-f111-bec6-70a8a59a411e` |
| Working baseline topic | `SAP Vendor Lookup` (`1d9231c3-b53d-f111-bec6-70a8a59a411e`) |

## Topics

| Topic | botcomponentid | Errors | Status |
|---|---|---|---|
| SAP Vendor Lookup | `1d9231c3-...` | 0 | ✅ baseline — now included in UX pass |
| SAP Create PR | `219231c3-...` | 4 | needs fix |
| SAP Get PR Status | `239231c3-...` | 1 | needs fix |
| SAP Approve Reject PR | `259231c3-...` | 2 | needs fix |
| SAP Cancel Edit PR | `279231c3-...` | 3 | needs fix |
| SAP Send Reminder | `2b9231c3-...` | 3 | needs fix |
| SAP List My PRs | (query Dataverse) | 3 | needs fix |
| SAP Pending Approvals | (query Dataverse) | 2 | needs fix |

## Diagnosed root causes (from prior session)

1. **Schema variant mismatch.** Vendor Lookup uses **v1** form (`entity: StringPrebuiltEntity` inline, `alwaysPrompt: false`, `allowInterruption: true` at root, `init:Topic.X` variable prefix). The other 7 topics use **v2** form (nested `interruptionPolicy:`, `entity: { kind: TextPrebuiltEntity }`, no `init:`). **Fix:** convert all 7 to v1.

2. **List My PRs / Pending Approvals** still bind to old flow output names (`total_value`, `status_label`, `results_count`) and have unprefixed string literals (`"demo-user"`). Flow now outputs `total_amount`, `status`, `pr_count`. **Fix:** rebind + add `=` prefix.

3. **Stale flow tool reference cache** likely causes the "13 Other Errors". After fixing topics, also PATCH the 6 flow tool botcomponents (`name like 'Ascend: SAP %'`).

## Acceptance criteria

- [ ] All 7 broken topics converted to v1 schema variant matching Vendor Lookup
- [ ] Output bindings match current PA flow output names (verify in modern designer per flow)
- [ ] All Power Fx string literals have `=` prefix
- [ ] Bot publishes with **0 Topic Errors and 0 Other Errors**
- [ ] Smoke test: Create PR → returns markdown table with PR number
- [ ] Smoke test: List My PRs → returns ≥1 row
- [ ] Update this file's status to ✅ Closed with timestamp

## Reference

- Skill: `customers/mfg_coe/skills/copilot-studio-binding-sync/SKILL.md`
- Reference impl: `customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.ps1`
- Executable script: `customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py`
- Flow definitions: `customers/ascend/solution/solution_src/Workflows/`

## Execution

```bash
export COPILOT_STUDIO_ORG_URL="https://org6feab6b5.crm.dynamics.com"
export COPILOT_STUDIO_BOT_ID="a1aa62dd-a23d-f111-bec6-70a8a59a411e"

# Dry run (default)
python customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py

# Apply PATCH operations to Dataverse
python customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py --apply

# Apply Issue #49 UX payloads (markdown + adaptive cards)
python customers/mfg_coe/skills/copilot-studio-binding-sync/binding_sync.py --apply-ux
```

## Don't

- Don't modify Vendor Lookup
- Don't PATCH `botcomponent.content` (only `data`)
- Don't change `flowId:` values in topics

## When done

Paste publish dialog screenshot (0 errors) + Test pane transcript of Create PR run.
