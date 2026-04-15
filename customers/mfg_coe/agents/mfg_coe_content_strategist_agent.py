"""
Agent: MfgCoE Content Strategist Agent
Purpose: Content Strategist / Technical Writer persona for the Discrete Manufacturing CoE.
         Ensures every deliverable — SOPs, outcome definitions, documentation packs,
         community content, forum posts, and Use Case Intake responses — is written
         in business language that resonates with manufacturing executives and
         business users, not just engineers.

         Owns: voice/tone, SOP templates, documentation structure, SSP response
         writing, community-facing content, and editorial review of agent output.

Actions:
  write_sop              — Write a structured SOP from a process description
  write_outcome_summary  — Convert a technical outcome definition into exec-ready prose
  write_use_case_response — Compose the documentation package for Use Case Intake output
  review_content         — Editorial review: clarity, tone, business language
  generate_ssm_response  — Generate an SSP/RFP alignment document
  write_forum_post       — Draft an agent forum post (announcement, insight, update)
  get_voice_guidelines   — Return CoE voice and tone guidelines
  write_executive_summary — Compose executive summary for CoE portfolio
"""

import json
import logging
from datetime import datetime

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VOICE_GUIDELINES = {
    "tone": "Confident and direct. No hedging. No passive voice. No 'we will attempt to...'",
    "audience": "Manufacturing executives, operations leaders, IT directors — people who care about outcomes, not architecture diagrams.",
    "language": "Business outcomes first, technology second. Lead with what changes for the user.",
    "length": "Every section should be 30% shorter than your first draft. Cut the adjectives.",
    "jargon_banned": [
        "leverage", "synergy", "utilize", "paradigm shift", "best-of-breed",
        "holistic", "scalable solution", "robust", "seamless", "end-to-end solution",
        "digital transformation journey", "empower",
    ],
    "instead_say": {
        "leverage": "use",
        "utilize": "use",
        "robust": "reliable",
        "seamless": "straightforward",
        "empower": "enable" ,
        "leverage the platform": "use the platform",
    },
}

SOP_TEMPLATE = """# SOP: {title}

**Process Area:** {process_area}
**Version:** 1.0
**Owner:** {owner}
**Last Updated:** {date}
**Status:** Draft

---

## Purpose

{purpose}

## Who This Is For

**Role:** {primary_role}
**When to use this SOP:** {trigger}

## Before You Start

**You will need:**
{prerequisites}

## Steps

{steps}

## What to Do If Something Goes Wrong

{exceptions}

## Success Looks Like

{success_criteria}

---

*Reviewed by: Content Strategist Agent | {date}*
*Next review due: {next_review}*
"""


class MfgCoEContentStrategistAgent(BasicAgent):
    """
    Content Strategist — owns the voice, tone, and quality of every written
    deliverable the CoE produces. Runs after Outcome Framer and SME to polish
    content before it reaches customers or stakeholders. Also writes the
    documentation package returned by the Use Case Intake feature.
    """

    def __init__(self):
        self.name = "MfgCoEContentStrategist"
        self.metadata = {
            "name": self.name,
            "description": (
                "Content Strategist agent — writes and reviews all CoE deliverables. "
                "SOPs, outcome summaries, Use Case Intake response docs, SSP/RFP alignment, "
                "forum posts, and executive summaries. Ensures business language, not technical "
                "jargon. Runs after Outcome Framer and SME. Every customer-facing doc "
                "goes through this agent before delivery."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "write_sop",
                            "write_outcome_summary",
                            "write_use_case_response",
                            "review_content",
                            "generate_ssm_response",
                            "write_forum_post",
                            "get_voice_guidelines",
                            "write_executive_summary",
                        ],
                        "description": "Content action to perform",
                    },
                    "title": {"type": "string", "description": "Title of the SOP, document, or content piece"},
                    "process_area": {"type": "string", "description": "Business process area"},
                    "content": {"type": "string", "description": "Raw content to review or transform"},
                    "outcome_definition": {"type": "string", "description": "Outcome definition to summarize"},
                    "use_case_text": {"type": "string", "description": "Use case input from intake form"},
                    "audience": {"type": "string", "description": "Target audience (exec, IT, operations, customer)"},
                    "context": {"type": "string", "description": "Additional context"},
                    "issue_number": {"type": "integer", "description": "GitHub issue number"},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_voice_guidelines")
        handlers = {
            "write_sop": self._write_sop,
            "write_outcome_summary": self._write_outcome_summary,
            "write_use_case_response": self._write_use_case_response,
            "review_content": self._review_content,
            "generate_ssm_response": self._generate_ssm_response,
            "write_forum_post": self._write_forum_post,
            "get_voice_guidelines": self._get_voice_guidelines,
            "write_executive_summary": self._write_executive_summary,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("ContentStrategist error in %s: %s", action, e)
            return json.dumps({"error": str(e)})

    def _write_sop(self, **kwargs) -> str:
        title = kwargs.get("title", "Process")
        process_area = kwargs.get("process_area", "General")
        context = kwargs.get("context", "")
        date = datetime.utcnow().strftime("%Y-%m-%d")

        steps = (
            "1. **[Step name]** — [What the user does. One sentence. Active voice.]\n"
            "   - ✅ Expected result: [what they see]\n\n"
            "2. **[Step name]** — [What the user does.]\n"
            "   - ✅ Expected result: [what they see]\n\n"
            "3. **[Step name]** — [What the user does.]\n"
            "   - ✅ Expected result: [what they see]"
        )

        content = SOP_TEMPLATE.format(
            title=title,
            process_area=process_area,
            owner="CoE SME + Content Strategist",
            date=date,
            purpose=f"[One sentence: why this process exists and what it prevents or enables.] {context}",
            primary_role="[Role name, e.g. 'Customer Service Representative']",
            trigger="[When does someone follow this SOP? E.g. 'When a customer submits a warranty claim']",
            prerequisites=(
                "- [ ] [System access or data needed]\n"
                "- [ ] [Prerequisite 2]"
            ),
            steps=steps,
            exceptions=(
                "**If [error condition]:** [What to do. Who to contact.]\n\n"
                "**If [system is unavailable]:** [Fallback procedure.]"
            ),
            success_criteria=(
                "- The [outcome] is complete and visible in [system]\n"
                "- The customer/user has received confirmation\n"
                "- No manual follow-up is required"
            ),
            next_review=f"{datetime.utcnow().replace(year=datetime.utcnow().year + 1).strftime('%Y-%m-%d')}",
        )

        return json.dumps({
            "status": "ok",
            "summary": f"SOP template created for: {title}",
            "content": content,
            "persona": "content-strategist",
        }, indent=2)

    def _write_outcome_summary(self, **kwargs) -> str:
        title = kwargs.get("title", "Outcome")
        outcome_def = kwargs.get("outcome_definition", "")
        audience = kwargs.get("audience", "executive")

        summary = (
            f"## {title}\n\n"
            f"**What changed:** [One sentence. What can a user do now that they couldn't before?]\n\n"
            f"**Who benefits:** [Role + how many people]\n\n"
            f"**Measured by:** [The one KPI that proves it worked]\n\n"
            f"**Before:** [In plain language, what the old process looked like]\n\n"
            f"**After:** [In plain language, what the new process looks like]\n\n"
            f"---\n"
            f"*This outcome was delivered by the Discrete Manufacturing CoE "
            f"using the RAPP pipeline and Microsoft technology stack.*"
        )

        return json.dumps({
            "status": "ok",
            "summary": f"Executive outcome summary drafted for: {title}",
            "content": summary,
            "persona": "content-strategist",
        }, indent=2)

    def _write_use_case_response(self, **kwargs) -> str:
        use_case = kwargs.get("use_case_text", "")
        title = kwargs.get("title", "Use Case Response")
        process_area = kwargs.get("process_area", "General")

        doc = (
            f"# {title}\n\n"
            f"*Prepared by Bots in Blazers CoE | {datetime.utcnow().strftime('%B %d, %Y')}*\n\n"
            f"---\n\n"
            f"## What You Submitted\n\n"
            f"{use_case[:500] if use_case else '[Use case text]'}\n\n"
            f"---\n\n"
            f"## What We Heard\n\n"
            f"[Content Strategist: translate the use case into the core business problem in 2-3 sentences. "
            f"No technology mentioned yet.]\n\n"
            f"## The Outcome We'd Deliver\n\n"
            f"[Outcome Framer output — business problem, affected users, KPI, demo story]\n\n"
            f"## How We'd Build It\n\n"
            f"[Architect output — recommended stack, pattern, components]\n\n"
            f"## Relevant SOPs and Prior Work\n\n"
            f"[SME output — matched SOPs, prior use cases, knowledge base hits]\n\n"
            f"## RAPP Pipeline Alignment\n\n"
            f"[Which RAPP steps apply. Estimated time to first demo.]\n\n"
            f"## Next Steps\n\n"
            f"- [ ] Bill to review and confirm outcome definition\n"
            f"- [ ] Schedule 30-minute working session to refine KPI targets\n"
            f"- [ ] Development begins after outcome is confirmed\n\n"
            f"---\n"
            f"*Questions? Reply to this doc or visit [bots-in-blazers.fun](https://bots-in-blazers.fun)*"
        )

        return json.dumps({
            "status": "ok",
            "summary": f"Use case response document drafted for: {title}",
            "content": doc,
            "persona": "content-strategist",
        }, indent=2)

    def _review_content(self, **kwargs) -> str:
        content = kwargs.get("content", "")
        issues = []

        # Check for banned jargon
        for word in VOICE_GUIDELINES["jargon_banned"]:
            if word.lower() in content.lower():
                replacement = VOICE_GUIDELINES["instead_say"].get(word, "simpler alternative")
                issues.append(f"⚠️ **Jargon:** '{word}' → use '{replacement}'")

        # Check for passive voice markers
        passive_markers = ["will be", "was done", "has been", "are being", "were provided"]
        for marker in passive_markers:
            if marker in content.lower():
                issues.append(f"⚠️ **Passive voice:** found '{marker}' — rewrite in active voice")

        # Check length
        word_count = len(content.split())
        if word_count > 500:
            issues.append(f"⚠️ **Length:** {word_count} words — aim for < 350. Cut 30%.")

        score = max(0, 100 - (len(issues) * 15))
        status = "approved" if score >= 80 else "needs_revision"

        return json.dumps({
            "status": status,
            "score": score,
            "issues": issues,
            "issue_count": len(issues),
            "summary": f"Content review complete. Score: {score}/100. {'Approved.' if status == 'approved' else f'{len(issues)} issues found.'}",
            "persona": "content-strategist",
        }, indent=2)

    def _generate_ssm_response(self, **kwargs) -> str:
        title = kwargs.get("title", "SSP Response")
        context = kwargs.get("context", "")
        doc = (
            f"# Microsoft Stack Alignment: {title}\n\n"
            f"*{datetime.utcnow().strftime('%B %Y')}*\n\n"
            f"## Executive Summary\n\n"
            f"[2-3 sentences: how Microsoft + CoE methodology aligns to this requirement]\n\n"
            f"## Requirement Mapping\n\n"
            f"| Requirement | Microsoft Solution | Delivery Approach |\n"
            f"|------------|-------------------|-------------------|\n"
            f"| [Req 1]    | D365 CE + Copilot Studio | RAPP pipeline, 4-week sprint |\n"
            f"| [Req 2]    | Power Platform + Azure AI | Outcome-first delivery |\n\n"
            f"## Why Microsoft\n\n"
            f"[3 bullets: specific advantages for this use case. No marketing language.]\n\n"
            f"## Reference Outcomes\n\n"
            f"[Link to 2-3 validated outcomes from this CoE that match the requirement]\n\n"
            f"## Proposed Next Step\n\n"
            f"[One specific action. Date. Owner.]\n"
        )
        return json.dumps({
            "status": "ok",
            "summary": f"SSP alignment doc drafted: {title}",
            "content": doc,
            "persona": "content-strategist",
        }, indent=2)

    def _write_forum_post(self, **kwargs) -> str:
        title = kwargs.get("title", "Update")
        context = kwargs.get("context", "")
        post = (
            f"## {title}\n\n"
            f"*Posted by CoE Agent Team | {datetime.utcnow().strftime('%B %d, %Y')}*\n\n"
            f"{context if context else '[Agent: add the update content here — 2-4 sentences max. Lead with the outcome, not the activity.]'}\n\n"
            f"**What this means for you:** [One sentence on impact or action needed]\n\n"
            f"---\n💬 *Reply with questions or reactions below.*"
        )
        return json.dumps({
            "status": "ok",
            "summary": f"Forum post drafted: {title}",
            "content": post,
            "persona": "content-strategist",
        }, indent=2)

    def _get_voice_guidelines(self, **kwargs) -> str:
        banned_md = "\n".join(f"- ~~{w}~~" for w in VOICE_GUIDELINES["jargon_banned"])
        return json.dumps({
            "status": "ok",
            "guidelines": VOICE_GUIDELINES,
            "summary": "CoE voice and tone guidelines returned.",
            "markdown": (
                f"## CoE Voice & Tone Guidelines\n\n"
                f"**Tone:** {VOICE_GUIDELINES['tone']}\n\n"
                f"**Audience:** {VOICE_GUIDELINES['audience']}\n\n"
                f"**Language:** {VOICE_GUIDELINES['language']}\n\n"
                f"**Length:** {VOICE_GUIDELINES['length']}\n\n"
                f"### Banned Jargon\n{banned_md}"
            ),
            "persona": "content-strategist",
        }, indent=2)

    def _write_executive_summary(self, **kwargs) -> str:
        context = kwargs.get("context", "")
        date = datetime.utcnow().strftime("%B %Y")
        summary = (
            f"# CoE Executive Summary — {date}\n\n"
            f"## What the CoE Delivered This Period\n\n"
            f"[3-5 bullets. Each = one verified outcome. Format: 'Reduced X by Y% for Z customer.']\n\n"
            f"## Work in Progress\n\n"
            f"[Issues in active pipeline — title + current stage]\n\n"
            f"## What's Blocked\n\n"
            f"[Items needing decisions. Owner. Age.]\n\n"
            f"## Key Metrics\n\n"
            f"| Metric | This Period | Trend |\n"
            f"|--------|------------|-------|\n"
            f"| Outcomes Validated | — | — |\n"
            f"| Avg Time to Outcome | — | — |\n"
            f"| Issues Blocked >7d | — | — |\n\n"
            f"## Recommended Decisions\n\n"
            f"[1-3 specific asks for leadership. Be direct.]\n"
        )
        return json.dumps({
            "status": "ok",
            "summary": "Executive summary template generated.",
            "content": summary,
            "persona": "content-strategist",
        }, indent=2)
