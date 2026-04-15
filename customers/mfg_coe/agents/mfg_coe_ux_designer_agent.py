"""
Agent: MfgCoE UX Designer Agent
Purpose: UX Designer persona for the Discrete Manufacturing CoE.
         Designs user experiences BEFORE developers build anything.
         Produces wireframes (markdown/component specs), user stories,
         information architecture, interaction flows, and UX review feedback.
         Ensures every feature is designed from the user's perspective,
         not the engineer's. Covers web UI, Copilot Studio conversation UX,
         Power Apps canvas design, and mobile patterns.

Actions:
  design_feature         — Produce UX spec for a web UI or app feature
  write_user_stories     — Generate user stories from an outcome definition
  review_ux              — Review a built feature for UX issues
  create_wireframe       — ASCII/markdown wireframe for a screen or flow
  define_ia              — Define information architecture for a view or app
  design_conversation_ux — Design conversational flow UX for Copilot Studio
  design_card            — Design an achievement card or display card spec
  get_ux_principles      — Return the CoE UX design principles
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UX_PRINCIPLES = [
    "Outcome-first: every screen answers 'what does the user accomplish here?'",
    "Business language: no technical jargon visible to business users",
    "Progressive disclosure: show the summary first, depth on demand",
    "Mobile-aware: every layout works on a phone before a desktop",
    "Accessible: WCAG AA contrast, keyboard navigable, screen-reader friendly",
    "Feedback loops: every user action gets an immediate visual response",
    "Empty states are designed: no blank panels, always a helpful prompt",
    "One primary action per screen: don't make users choose between 5 buttons",
]

INTERACTION_PATTERNS = {
    "form": {
        "pattern": "Progressive form",
        "principles": ["Show one section at a time", "Inline validation", "Save progress", "Clear error states"],
        "components": ["Label + input pairs", "Helper text", "Submit + cancel", "Progress indicator"],
    },
    "dashboard": {
        "pattern": "Glanceable dashboard",
        "principles": ["KPIs first (top row)", "Trend > number alone", "Click-through to detail", "Refresh indicator"],
        "components": ["KPI cards", "Sparkline charts", "Activity feed", "Alert banners"],
    },
    "list": {
        "pattern": "Filterable list",
        "principles": ["Sort and filter always visible", "Row = one clear action", "Bulk actions for power users"],
        "components": ["Filter bar", "Sort headers", "Row with status badge", "Pagination or infinite scroll"],
    },
    "card_gallery": {
        "pattern": "Card collection",
        "principles": ["Visual hierarchy on card", "Locked/unlocked state clear", "Hover reveals detail", "Share action prominent"],
        "components": ["Card face (icon + title + earned date)", "Card back (description + criteria)", "Lock overlay", "Share button"],
    },
    "chat": {
        "pattern": "Conversational UI",
        "principles": ["User message right-aligned", "Agent message left-aligned", "Typing indicator", "Scroll to latest"],
        "components": ["Message bubbles", "Input box + send", "Agent avatar", "Timestamp on hover"],
    },
    "intake_form": {
        "pattern": "Guided intake wizard",
        "principles": ["Step indicator shows progress", "Allow back navigation", "Preview before submit", "Async result display"],
        "components": ["Step bar", "Textarea with character count", "Optional fields collapsed", "Result panel with download"],
    },
}


class MfgCoEUXDesignerAgent(BasicAgent):
    """
    UX Designer — designs user experiences before any build work begins.
    Produces wireframes, user stories, IA, conversation flows, and UX reviews.
    Works closely with the Outcome Framer (what are we solving?) and Developer
    (here's how it should look and behave before you write a line of code).
    """

    def __init__(self):
        self.name = "MfgCoEUXDesigner"
        self.metadata = {
            "name": self.name,
            "description": (
                "UX Designer agent — produces user experience specs, wireframes, user stories, "
                "information architecture, and UX reviews for CoE web UI, Power Apps, and "
                "Copilot Studio conversation flows. Runs before Developer builds. "
                "Ensures every feature solves the user's problem, not just the technical requirement."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "design_feature",
                            "write_user_stories",
                            "review_ux",
                            "create_wireframe",
                            "define_ia",
                            "design_conversation_ux",
                            "design_card",
                            "get_ux_principles",
                        ],
                        "description": "UX design action to perform",
                    },
                    "feature_name": {"type": "string", "description": "Name of the feature to design"},
                    "outcome_definition": {"type": "string", "description": "Outcome definition text to derive user stories from"},
                    "screen_type": {
                        "type": "string",
                        "enum": ["form", "dashboard", "list", "card_gallery", "chat", "intake_form"],
                        "description": "Type of screen or interaction pattern",
                    },
                    "user_type": {"type": "string", "description": "Primary user type (Bill, external guest, authenticated community user, etc.)"},
                    "context": {"type": "string", "description": "Additional context or requirements"},
                    "issue_number": {"type": "integer", "description": "GitHub issue number"},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_ux_principles")
        handlers = {
            "design_feature": self._design_feature,
            "write_user_stories": self._write_user_stories,
            "review_ux": self._review_ux,
            "create_wireframe": self._create_wireframe,
            "define_ia": self._define_ia,
            "design_conversation_ux": self._design_conversation_ux,
            "design_card": self._design_card,
            "get_ux_principles": self._get_ux_principles,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("UXDesigner error in %s: %s", action, e)
            return json.dumps({"error": str(e)})

    def _design_feature(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Unnamed Feature")
        screen_type = kwargs.get("screen_type", "form")
        user_type = kwargs.get("user_type", "Bill")
        context = kwargs.get("context", "")
        pattern = INTERACTION_PATTERNS.get(screen_type, INTERACTION_PATTERNS["form"])

        spec = (
            f"## UX Spec: {feature}\n\n"
            f"**Primary User:** {user_type}\n"
            f"**Pattern:** {pattern['pattern']}\n"
            f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            f"### Design Principles Applied\n"
            + "\n".join(f"- {p}" for p in pattern["principles"]) + "\n\n"
            f"### Required Components\n"
            + "\n".join(f"- {c}" for c in pattern["components"]) + "\n\n"
            f"### User Goal\n"
            f"*{user_type} opens this screen to: [define one primary action]*\n\n"
            f"### Success Criteria (UX)\n"
            f"- [ ] User can complete the primary task in < 3 clicks\n"
            f"- [ ] Empty state is designed and helpful\n"
            f"- [ ] Error states are clear and actionable\n"
            f"- [ ] Mobile layout tested at 375px width\n"
            f"- [ ] No technical jargon visible to business user\n\n"
            f"### Context Notes\n{context if context else '[Add specific requirements here]'}\n\n"
            f"---\n*UX Designer Agent | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
        )

        return json.dumps({
            "status": "ok",
            "summary": f"UX spec created for: {feature} ({screen_type} pattern)",
            "spec": spec,
            "pattern": screen_type,
            "components": pattern["components"],
            "persona": "ux-designer",
        }, indent=2)

    def _write_user_stories(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        outcome = kwargs.get("outcome_definition", "")
        user_type = kwargs.get("user_type", "business user")

        stories = [
            f"**As a** {user_type}, **I want to** see my current work items at a glance **so that** I can prioritize without opening multiple systems.",
            f"**As a** {user_type}, **I want to** submit a use case in plain English **so that** the agent team can respond without me knowing the technical details.",
            f"**As a** {user_type}, **I want to** see what outcomes have been delivered **so that** I can demonstrate value to stakeholders.",
            f"**As a** {user_type}, **I want to** get notified when agents need my input **so that** I don't have to check GitHub manually.",
            f"**As a** guest visitor, **I want to** browse the CoE's work **so that** I can understand the methodology without logging in.",
        ]

        stories_md = "\n".join(f"- {s}" for s in stories)
        acceptance = (
            "### Acceptance Criteria Template\n"
            "For each story:\n"
            "- [ ] Happy path works end-to-end\n"
            "- [ ] Error state is handled gracefully\n"
            "- [ ] Matches UX spec component list\n"
            "- [ ] Passes UX review before closing\n"
        )

        return json.dumps({
            "status": "ok",
            "summary": f"Generated {len(stories)} user stories for: {feature}",
            "stories": stories,
            "stories_markdown": f"## User Stories: {feature}\n\n{stories_md}\n\n{acceptance}",
            "persona": "ux-designer",
        }, indent=2)

    def _create_wireframe(self, **kwargs) -> str:
        screen_type = kwargs.get("screen_type", "dashboard")
        feature = kwargs.get("feature_name", "Screen")

        wireframes = {
            "dashboard": (
                "```\n"
                "┌─────────────────────────────────────────────────┐\n"
                "│  🤖 Bots in Blazers        [🔔 3] [👤 Bill] [☀️] │\n"
                "├─────────────┬───────────────────────────────────┤\n"
                "│  Dashboard  │  ┌──────┐ ┌──────┐ ┌──────┐      │\n"
                "│  Agents     │  │  12  │ │   4  │ │  87% │      │\n"
                "│  Outcomes   │  │Active│ │ Done │ │ Rate │      │\n"
                "│  Backlog    │  └──────┘ └──────┘ └──────┘      │\n"
                "│  Forum      │                                   │\n"
                "│  Chat       │  Agent Status     Activity Feed   │\n"
                "│  Settings   │  ┌─────────────┐  ┌───────────┐  │\n"
                "│             │  │ ✅ PM        │  │ #1 update │  │\n"
                "│             │  │ ✅ SME       │  │ #3 block  │  │\n"
                "│             │  │ ✅ Architect │  │ #2 done   │  │\n"
                "│             │  └─────────────┘  └───────────┘  │\n"
                "└─────────────┴───────────────────────────────────┘\n"
                "```"
            ),
            "intake_form": (
                "```\n"
                "┌─────────────────────────────────────────────────┐\n"
                "│  💡 Submit a Use Case                           │\n"
                "│  ─────────────────────────────────────────────  │\n"
                "│  Step 1 of 3: Describe the Problem      [●○○]  │\n"
                "│                                                 │\n"
                "│  What business problem are you solving?         │\n"
                "│  ┌───────────────────────────────────────────┐  │\n"
                "│  │ Paste your use case or SSP excerpt here.. │  │\n"
                "│  │                                           │  │\n"
                "│  │                              240/2000 chr │  │\n"
                "│  └───────────────────────────────────────────┘  │\n"
                "│                                                 │\n"
                "│  Process Area: [Warranty ▼]  Customer: [Any ▼] │\n"
                "│                                                 │\n"
                "│             [← Back]  [Next: Outcomes →]        │\n"
                "└─────────────────────────────────────────────────┘\n"
                "```"
            ),
            "card_gallery": (
                "```\n"
                "┌─────────────────────────────────────────────────┐\n"
                "│  🏆 Your Achievement Cards  (4 earned / 12)      │\n"
                "│  ─────────────────────────────────────────────  │\n"
                "│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │\n"
                "│  │    🎯    │ │    ✅    │ │  🔒          │    │\n"
                "│  │ First    │ │ Verified │ │  Agent       │    │\n"
                "│  │ Outcome  │ │ Delivery │ │  Builder     │    │\n"
                "│  │ Apr 2026 │ │ Apr 2026 │ │  Locked      │    │\n"
                "│  │ [Share↗] │ │ [Share↗] │ │              │    │\n"
                "│  └──────────┘ └──────────┘ └──────────────┘    │\n"
                "│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │\n"
                "│  │  🔒      │ │  🔒      │ │  🔒          │    │\n"
                "│  │ Streak   │ │ SOP      │ │  Community   │    │\n"
                "│  │ Locked   │ │ Locked   │ │  Locked      │    │\n"
                "│  └──────────┘ └──────────┘ └──────────────┘    │\n"
                "└─────────────────────────────────────────────────┘\n"
                "```"
            ),
        }

        wf = wireframes.get(screen_type, wireframes["dashboard"])

        return json.dumps({
            "status": "ok",
            "summary": f"Wireframe created for: {feature} ({screen_type})",
            "wireframe": wf,
            "notes": [
                "ASCII wireframe — for layout reference only",
                "Implement with actual CSS grid/flexbox",
                "Verify mobile layout at 375px",
                "Replace placeholder text with real data bindings",
            ],
            "persona": "ux-designer",
        }, indent=2)

    def _define_ia(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Application")
        ia = {
            "primary_nav": ["Dashboard", "Agent Team", "Outcomes", "Backlog", "Sprint Board", "Needs Your Input"],
            "community_nav": ["Forum", "Daily Wrap-Up", "Chat with Bill", "SOPs & Docs", "Knowledge Base", "D365 Environments"],
            "config_nav": ["CoE Charter", "Settings"],
            "new_sections": ["Achievement Cards", "Use Case Intake", "Community Mode"],
        }
        return json.dumps({
            "status": "ok",
            "summary": f"Information architecture defined for: {feature}",
            "ia": ia,
            "persona": "ux-designer",
        }, indent=2)

    def _design_conversation_ux(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Copilot Flow")
        context = kwargs.get("context", "")
        spec = (
            f"## Conversation UX: {feature}\n\n"
            "### Flow Principles\n"
            "- Open with value, not greeting: 'I can help you check warranty status.'\n"
            "- Max 2 questions before providing value\n"
            "- Always offer a way out: 'Or would you like to speak with someone?'\n"
            "- Confirm before destructive actions\n"
            "- End with a clear next step or resolution\n\n"
            "### Sample Turn Structure\n"
            "```\n"
            "User:  [Trigger phrase]\n"
            "Agent: [Value statement + one clarifying question]\n"
            "User:  [Response]\n"
            "Agent: [Result + next step options]\n"
            "User:  [Selection]\n"
            "Agent: [Confirmation + closure]\n"
            "```\n\n"
            "### Error / No-Match Handling\n"
            "- Offer 3 specific options, not 'I didn't understand'\n"
            "- After 2 no-matches, offer human escalation\n"
            "- Log the no-match utterance for SME review\n"
        )
        return json.dumps({
            "status": "ok",
            "summary": f"Conversation UX spec created for: {feature}",
            "spec": spec,
            "persona": "ux-designer",
        }, indent=2)

    def _design_card(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Achievement Card")
        context = kwargs.get("context", "")
        spec = {
            "card_face": {
                "elements": ["Large emoji icon (64px)", "Card title (bold, 16px)", "Earned date (subtle, 12px)", "Subtle glow border (unlocked) or grayscale (locked)"],
                "size": "180x240px",
                "interaction": "Hover = flip animation (300ms)",
            },
            "card_back": {
                "elements": ["Card title", "Description (2 sentences max)", "Unlock criteria (bullet list)", "Share button", "CoE watermark"],
                "size": "180x240px",
            },
            "states": {
                "locked": "Grayscale + lock icon overlay + tooltip 'Complete X to unlock'",
                "unlocked": "Full color + glow border + earned date",
                "new": "Full color + 'NEW' badge + subtle pulse animation for 24h",
            },
            "sharing": "Generates: bots-in-blazers.fun/card/{card_id} — OG image for social share",
        }
        return json.dumps({
            "status": "ok",
            "summary": f"Achievement card spec created: {feature}",
            "spec": spec,
            "persona": "ux-designer",
        }, indent=2)

    def _review_ux(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        context = kwargs.get("context", "")
        checklist = [
            ("Primary action is clear", True),
            ("Empty state is designed", None),
            ("Error states handled", None),
            ("Mobile layout verified", None),
            ("No technical jargon visible to business user", None),
            ("Loading/pending state shown", None),
            ("User can complete task in < 3 clicks", None),
            ("Consistent with existing UI patterns", None),
        ]
        items_md = "\n".join(
            f"- {'✅' if v is True else '⬜'} {label}" for label, v in checklist
        )
        return json.dumps({
            "status": "review_needed",
            "summary": f"UX review checklist generated for: {feature}. Manual review required.",
            "checklist_markdown": f"## UX Review: {feature}\n\n{items_md}\n\n*Complete this checklist before Developer closes the issue.*",
            "persona": "ux-designer",
        }, indent=2)

    def _get_ux_principles(self, **kwargs) -> str:
        principles_md = "\n".join(f"- {p}" for p in UX_PRINCIPLES)
        return json.dumps({
            "status": "ok",
            "count": len(UX_PRINCIPLES),
            "principles": UX_PRINCIPLES,
            "principles_markdown": f"## CoE UX Design Principles\n\n{principles_md}",
            "summary": f"{len(UX_PRINCIPLES)} UX principles defined for the CoE.",
            "persona": "ux-designer",
        }, indent=2)
