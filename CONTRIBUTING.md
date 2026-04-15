# Contributing to CommunityRAPP

Thanks for contributing! This repo is maintained by the Mfg CoE Agentic Team.

## Getting Started

1. **Fork** `billwhalenmsft/CommunityRAPP-BillWhalen`
2. **Clone** your fork locally
3. **Create** `local.settings.json` from `.env.example` (fill in your Azure keys)
4. **Activate** the virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate`
5. **Install** dependencies: `pip install -r requirements.txt`
6. **Run** locally: `.\run.ps1` (Windows) or `./run.sh`

## Making Changes

- Branch from `main`
- Use descriptive branch names: `feat/my-feature`, `fix/bug-description`
- Keep changes focused — one feature or fix per PR
- Run tests before opening a PR: `python tests/run_tests.py`

## Adding a New Agent

1. Create `agents/my_agent.py` inheriting from `BasicAgent`
2. Define `name`, `metadata` (OpenAI function schema), and `perform(**kwargs)`
3. Agent auto-loads on next function startup — no registration needed
4. Add a test in `tests/`

See `AGENTS.md` and `CLAUDE.md` for full conventions.

## CoE Work

Issues labeled `mfg-coe` are processed automatically by the CoE agents on schedule.
To submit work for agents: label issues `mfg-coe` + a priority (`p1-critical`, `p2-high`, `p3-medium`).

## Pull Requests

- Fill out the PR template
- Link related GitHub Issues
- All PRs to `main` require a passing `agentrc readiness` check (CI gate)

## Questions?

Open a GitHub Issue or post in the Agent Forum at [bots-in-blazers.fun](https://bots-in-blazers.fun).
