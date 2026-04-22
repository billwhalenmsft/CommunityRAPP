# Carrier Developer Quickstart
## Build with VS Code + GitHub Copilot (Vibe Coding Style)

This guide helps your team recreate the same workflow used in the Trailer Prioritization work: fast iteration, high quality output, and clear business alignment.

## 1) What you need

- A GitHub account with GitHub Copilot access enabled
- Visual Studio Code (latest stable)
- Node.js LTS (for web app work)
- Python 3.11+ (for Python and automation work)
- Access to this repository in GitHub

## 2) One-time setup (15-20 minutes)

1. Install VS Code.
2. Install these VS Code extensions:
- GitHub Copilot
- GitHub Copilot Chat
- ESLint
- Prettier
- Python (Microsoft)
3. Sign in to GitHub in VS Code.
4. Verify Copilot is active:
- Open Copilot Chat in VS Code.
- Ask: "Summarize this folder and suggest next steps."

## 3) Clone and open the project

1. Clone the repo.
2. Open the repository folder in VS Code.
3. Open an integrated terminal and set up local dependencies as needed.

Recommended first commands (PowerShell):

```powershell
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

## 4) The vibe coding workflow (the exact pattern we used)

Use this 6-step loop for every change.

1. Frame the business goal
- Example: "Reduce manual trailer scheduling effort and improve OTIF-related prioritization."

2. Give Copilot a concrete task
- Include: desired outcome, files, constraints, and definition of done.

3. Ask Copilot to implement, not just explain
- Prefer direct edits + validation over long theory.

4. Validate immediately
- Run build/tests after each meaningful change.
- Fix issues while context is fresh.

5. Update docs in the same pass
- Keep implementation notes and guide content aligned with code.

6. Package the result for business users
- Produce one technical artifact and one customer-friendly artifact.

## 5) Prompt templates your team can copy/paste

### A) Feature build prompt

```text
Implement [feature] in [path/file].
Context:
- Business goal: [goal]
- Users: [personas]
- Constraints: [performance/security/style]
Do the work end-to-end:
1) Edit code
2) Run validation
3) Update related docs
4) Summarize changes with file references
```

### B) UI improvement prompt

```text
Refactor this UI to be clearer for operations users.
Keep the same functionality, improve hierarchy, spacing, labels, and responsive behavior.
Then run a production build and report any issues fixed.
```

### C) Data realism prompt

```text
Expand local mock data so demos feel realistic.
Add enough records for meaningful KPIs and status variety.
Update docs to match the seeded dataset and verify build.
```

### D) Bug fix prompt

```text
Fix this runtime issue: [paste error].
Find root cause, patch only what is needed, validate, and explain why the fix works.
```

### E) Customer collateral prompt

```text
Create a customer-friendly how-to based on what we built.
Audience: business + developer stakeholders.
Output: clear steps, glossary, rollout plan, and next actions.
```

## 6) Quality bar (definition of done)

Before marking any task complete:

- The app runs without runtime errors
- Build succeeds
- User-facing flow is easy to follow
- Docs match current behavior
- Handoff notes are clear enough for another developer to continue

## 7) Team operating model (recommended)

Use a two-person pairing model for the first 2-3 weeks:

- Driver: works in VS Code with Copilot and implements changes
- Reviewer: checks business alignment, tests behavior, and improves prompts

Daily rhythm:

- 15 min: choose one business outcome
- 60-90 min: implement one small vertical slice
- 15 min: demo + capture follow-ups

## 8) First-week starter backlog

Day 1:
- Local setup and environment validation
- Run current app
- Read the engagement guide end-to-end

Day 2:
- Make one low-risk UI improvement
- Run build and capture before/after screenshots

Day 3:
- Add one data or scoring enhancement
- Update docs to reflect new behavior

Day 4:
- Improve one operational workflow (notifications, exception handling, or scheduling UX)

Day 5:
- Dry-run a customer demo
- Finalize customer-facing notes and next sprint recommendations

## 9) Common mistakes to avoid

- Asking Copilot broad, vague questions without concrete scope
- Making large changes without running validation between steps
- Updating code but forgetting docs
- Shipping technical detail without business context

## 10) What to share with your business partners each sprint

- What changed (in plain language)
- Why it matters (OTIF, cycle time, manual effort, service level)
- Evidence (screenshots, demo steps, metrics)
- Decision requests for the next sprint

## Related project assets

- Engagement guide (HTML): customers/carrier/docs/carrier-trailer-prioritization-engagement-guide.html
- Engagement guide (Markdown): customers/carrier/docs/carrier-trailer-prioritization-engagement-guide.md
- Demo script: customers/carrier/demos/carrier_trailer_prioritization_demo.json
- Implementation README: customers/carrier/d365/trailer-prioritization/README.md

---

If useful, we can also provide a version of this guide as a branded HTML handout for direct sharing with business stakeholders.
