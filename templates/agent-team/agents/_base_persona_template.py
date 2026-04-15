"""
Agent: {{TEAM_SLUG}}_{{PERSONA_ID}}_agent
Purpose: {{PERSONA_ROLE}}

Replace all {{PLACEHOLDER}} values with your implementation.

Actions:
  {{ACTION_1}}  — describe what it does
  {{ACTION_2}}  — describe what it does
  get_status    — always include: reports agent readiness
"""

import json
import logging

from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)

# ── Domain constants — customize these ────────────────────────────────────────
DOMAIN_CONTEXT = {
    "focus_area": "{{DOMAIN_FOCUS}}",
    "key_concepts": ["concept_1", "concept_2", "concept_3"],
}


class {{CLASS_NAME}}(BasicAgent):
    """{{PERSONA_ROLE}}"""

    def __init__(self):
        self.name = "{{CLASS_NAME}}"
        self.metadata = {
            "name": self.name,
            "description": (
                "{{PERSONA_DESCRIPTION}} "
                "Use this agent when {{WHEN_TO_USE}}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "{{ACTION_1}}",
                            "{{ACTION_2}}",
                            "get_status",
                        ],
                        "description": "Action to perform",
                    },
                    "use_case": {
                        "type": "string",
                        "description": "The use case or topic to work on",
                    },
                    "description": {
                        "type": "string",
                        "description": "Additional context or details",
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "GitHub issue number (if applicable)",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")
        handlers = {
            "{{ACTION_1}}": self._{{action_1_method}},
            "{{ACTION_2}}": self._{{action_2_method}},
            "get_status":   self._get_status,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}", "available": list(handlers.keys())})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("{{CLASS_NAME}} error in %s: %s", action, e)
            return json.dumps({"error": str(e), "action": action})

    # ── Action handlers ────────────────────────────────────────────────────────

    def _{{action_1_method}}(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", "")
        description = kwargs.get("description", "")

        # TODO: Replace with your domain logic
        result = {
            "status": "success",
            "action": "{{ACTION_1}}",
            "use_case": use_case,
            "output": f"{{ACTION_1}} completed for: {use_case}",
            # Add your actual output fields here
        }
        return json.dumps(result)

    def _{{action_2_method}}(self, **kwargs) -> str:
        use_case = kwargs.get("use_case", "")

        # TODO: Replace with your domain logic
        result = {
            "status": "success",
            "action": "{{ACTION_2}}",
            "output": f"{{ACTION_2}} completed for: {use_case}",
        }
        return json.dumps(result)

    def _get_status(self, **kwargs) -> str:
        return json.dumps({
            "agent": self.name,
            "status": "ready",
            "domain": DOMAIN_CONTEXT["focus_area"],
            "capabilities": ["{{ACTION_1}}", "{{ACTION_2}}"],
        })
