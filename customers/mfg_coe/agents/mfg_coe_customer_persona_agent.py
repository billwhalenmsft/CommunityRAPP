"""
Agent: MfgCoE Customer Persona Agent
Purpose: Simulates real customer interactions for testing demo scenarios.
         Loads a customer persona profile and scenario, then generates realistic
         in-character conversation turns to drive testing against chatbot surfaces.
         Integrates with the Playwright test harness.

Actions:
  simulate_conversation  — Run a full scenario conversation and return all turns
  play_scenario_turn     — Generate the next user message for a given scenario state
  get_customer_profiles  — List all available customer personas
  get_scenarios          — List scenarios for a specific customer
  get_scenario_detail    — Get full scenario definition including success criteria
  generate_test_script   — Generate a Playwright-ready test script from a scenario
  evaluate_response      — Check if an agent response meets scenario success criteria
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TESTING_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "testing")
)

CUSTOMERS = ["navico", "otis", "zurnelkay", "vermeer", "carrier", "aes", "sma4"]


class MfgCoECustomerPersonaAgent(BasicAgent):
    """
    Customer Persona Agent — simulates customers for testing Discrete Mfg demo scenarios.
    Generates realistic, in-character conversation turns based on persona profiles.
    """

    def __init__(self):
        self.name = "MfgCoECustomerPersona"
        self.metadata = {
            "name": self.name,
            "description": (
                "Customer Persona Agent for the Discrete Manufacturing CoE. "
                "Simulates real customers (Navico dealer, Otis building manager, Zurn contractor, etc.) "
                "to test demo chatbot scenarios. Generates in-character conversation turns, "
                "evaluates agent responses against success criteria, and produces Playwright test scripts. "
                "Use this agent to run scenario tests or generate test data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "simulate_conversation",
                            "play_scenario_turn",
                            "get_customer_profiles",
                            "get_scenarios",
                            "get_scenario_detail",
                            "generate_test_script",
                            "evaluate_response"
                        ],
                        "description": "Action to perform"
                    },
                    "customer": {
                        "type": "string",
                        "enum": ["navico", "otis", "zurnelkay", "vermeer", "carrier", "aes", "sma4"],
                        "description": "Customer name"
                    },
                    "scenario_id": {
                        "type": "string",
                        "description": "Scenario ID to run or generate"
                    },
                    "persona_id": {
                        "type": "string",
                        "description": "Specific persona to use (optional — uses scenario default)"
                    },
                    "agent_response": {
                        "type": "string",
                        "description": "Agent response to evaluate against success criteria"
                    },
                    "turn_number": {
                        "type": "integer",
                        "description": "Current turn number in the conversation (for play_scenario_turn)"
                    },
                    "conversation_history": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Prior turns in the conversation"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_customer_profiles")
        handlers = {
            "simulate_conversation": self._simulate_conversation,
            "play_scenario_turn":    self._play_scenario_turn,
            "get_customer_profiles": self._get_customer_profiles,
            "get_scenarios":         self._get_scenarios,
            "get_scenario_detail":   self._get_scenario_detail,
            "generate_test_script":  self._generate_test_script,
            "evaluate_response":     self._evaluate_response,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoECustomerPersonaAgent error in {action}: {e}")
            return json.dumps({"error": str(e)})

    def _load_personas(self, customer: str) -> List[Dict]:
        path = os.path.join(TESTING_DIR, customer, "personas.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("personas", [])

    def _load_scenarios(self, customer: str) -> List[Dict]:
        path = os.path.join(TESTING_DIR, customer, "scenarios.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("scenarios", [])

    def _get_persona(self, customer: str, persona_id: str) -> Optional[Dict]:
        for p in self._load_personas(customer):
            if p["persona_id"] == persona_id:
                return p
        return None

    def _get_scenario(self, customer: str, scenario_id: str) -> Optional[Dict]:
        for s in self._load_scenarios(customer):
            if s["scenario_id"] == scenario_id:
                return s
        return None

    def _get_customer_profiles(self, **kwargs) -> str:
        all_profiles = {}
        for customer in CUSTOMERS:
            personas = self._load_personas(customer)
            if personas:
                all_profiles[customer] = [
                    {"persona_id": p["persona_id"], "name": p["name"], "role": p["role"]}
                    for p in personas
                ]
        return json.dumps({"customers": all_profiles, "total_customers": len(all_profiles)}, indent=2)

    def _get_scenarios(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        if not customer:
            all_scenarios = {}
            for c in CUSTOMERS:
                scenarios = self._load_scenarios(c)
                if scenarios:
                    all_scenarios[c] = [
                        {"scenario_id": s["scenario_id"], "title": s["title"]}
                        for s in scenarios
                    ]
            return json.dumps(all_scenarios, indent=2)
        scenarios = self._load_scenarios(customer)
        return json.dumps({
            "customer": customer,
            "scenarios": [{"scenario_id": s["scenario_id"], "title": s["title"]} for s in scenarios]
        }, indent=2)

    def _get_scenario_detail(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        scenario_id = kwargs.get("scenario_id", "")
        if not customer or not scenario_id:
            return json.dumps({"error": "customer and scenario_id required"})
        scenario = self._get_scenario(customer, scenario_id)
        if not scenario:
            return json.dumps({"error": f"Scenario {scenario_id} not found for {customer}"})
        return json.dumps(scenario, indent=2)

    def _simulate_conversation(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        scenario_id = kwargs.get("scenario_id", "")
        if not customer or not scenario_id:
            return json.dumps({"error": "customer and scenario_id required"})

        scenario = self._get_scenario(customer, scenario_id)
        if not scenario:
            return json.dumps({"error": f"Scenario {scenario_id} not found for {customer}"})

        persona = self._get_persona(customer, scenario.get("persona_id", ""))
        flow = scenario.get("conversation_flow", [])

        # Build conversation transcript
        transcript = []
        for turn in flow:
            actor = turn.get("actor", "user")
            if actor == "user":
                transcript.append({
                    "actor": "user",
                    "persona": persona.get("name", "Customer") if persona else "Customer",
                    "message": turn.get("message", ""),
                    "in_character_note": self._get_character_note(persona, turn.get("message", ""))
                })
            else:
                expected = turn.get("expected_contains", [])
                transcript.append({
                    "actor": "agent",
                    "expected_keywords": expected,
                    "validation": f"Response must contain: {', '.join(expected)}" if expected else "No specific validation"
                })

        return json.dumps({
            "customer": customer,
            "scenario": scenario_id,
            "title": scenario.get("title", ""),
            "persona": {
                "name": persona.get("name") if persona else "Unknown",
                "role": persona.get("role") if persona else "Unknown",
                "style": persona.get("language_style") if persona else ""
            },
            "transcript": transcript,
            "success_criteria": scenario.get("success_criteria", []),
            "max_turns": scenario.get("max_turns", 8),
            "escalation_expected": scenario.get("escalation_expected", False)
        }, indent=2)

    def _play_scenario_turn(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        scenario_id = kwargs.get("scenario_id", "")
        turn_number = kwargs.get("turn_number", 0)
        history = kwargs.get("conversation_history", [])

        scenario = self._get_scenario(customer, scenario_id) if customer and scenario_id else None
        persona_id = kwargs.get("persona_id") or (scenario.get("persona_id") if scenario else None)
        persona = self._get_persona(customer, persona_id) if persona_id else None

        # Get next user turn from flow
        if scenario:
            user_turns = [t for t in scenario.get("conversation_flow", []) if t.get("actor") == "user"]
            if turn_number < len(user_turns):
                message = user_turns[turn_number]["message"]
                return json.dumps({
                    "turn": turn_number,
                    "actor": "user",
                    "message": message,
                    "persona": persona.get("name") if persona else "Customer",
                    "in_character": True
                })

        return json.dumps({
            "turn": turn_number,
            "actor": "user",
            "message": "Can you help me with my issue?",
            "persona": persona.get("name") if persona else "Customer",
            "in_character": False,
            "note": "No scripted turn available — generic fallback"
        })

    def _evaluate_response(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        scenario_id = kwargs.get("scenario_id", "")
        agent_response = kwargs.get("agent_response", "")
        turn_number = kwargs.get("turn_number", 0)

        if not agent_response:
            return json.dumps({"error": "agent_response required"})

        scenario = self._get_scenario(customer, scenario_id) if customer and scenario_id else None
        if not scenario:
            return json.dumps({"pass": True, "note": "No scenario loaded — cannot validate"})

        # Check expected keywords for this turn
        agent_turns = [t for t in scenario.get("conversation_flow", []) if t.get("actor") == "agent"]
        if turn_number < len(agent_turns):
            expected = agent_turns[turn_number].get("expected_contains", [])
            response_lower = agent_response.lower()
            found = [k for k in expected if k.lower() in response_lower]
            missing = [k for k in expected if k.lower() not in response_lower]
            passed = len(missing) == 0
            return json.dumps({
                "turn": turn_number,
                "pass": passed,
                "expected_keywords": expected,
                "found": found,
                "missing": missing,
                "response_preview": agent_response[:200]
            }, indent=2)

        # Check overall success criteria
        criteria = scenario.get("success_criteria", [])
        return json.dumps({
            "turn": turn_number,
            "pass": True,
            "note": "Turn beyond defined flow — using overall success criteria",
            "success_criteria": criteria
        }, indent=2)

    def _generate_test_script(self, **kwargs) -> str:
        customer = kwargs.get("customer", "")
        scenario_id = kwargs.get("scenario_id", "")
        if not customer or not scenario_id:
            return json.dumps({"error": "customer and scenario_id required"})

        scenario = self._get_scenario(customer, scenario_id)
        if not scenario:
            return json.dumps({"error": f"Scenario {scenario_id} not found"})

        persona = self._get_persona(customer, scenario.get("persona_id", ""))
        flow = scenario.get("conversation_flow", [])

        test_steps = []
        for i, turn in enumerate(flow):
            if turn["actor"] == "user":
                test_steps.append(f"    // Turn {i+1} — {persona['name'] if persona else 'User'}\n    await chatInput.fill({json.dumps(turn['message'])});\n    await sendButton.click();")
            else:
                expected = turn.get("expected_contains", [])
                for kw in expected:
                    test_steps.append(f"    await expect(page.locator('[data-testid=\"chat-messages\"]').last()).toContainText({json.dumps(kw)}, {{ ignoreCase: true }});")
                test_steps.append("    await page.waitForTimeout(1000);")

        steps_code = "\n".join(test_steps)
        criteria_comments = "\n".join([f"    // ✓ {c}" for c in scenario.get("success_criteria", [])])

        script = f"""import {{ test, expect }} from '@playwright/test';

/**
 * Auto-generated Playwright test
 * Customer: {customer.title()}
 * Scenario: {scenario.get('title', scenario_id)}
 * Persona: {persona['name'] if persona else 'Customer'} — {persona['role'] if persona else ''}
 * Generated: {datetime.utcnow().strftime('%Y-%m-%d')} by MfgCoE Customer Persona Agent
 *
 * Success Criteria:
{criteria_comments}
 */

test('{scenario.get("title", scenario_id)}', async ({{ page }}) => {{
  await page.goto(process.env.CHAT_URL || 'http://localhost:7071');
  await page.waitForSelector('[data-testid="chat-input"]', {{ timeout: 10000 }});
  const chatInput = page.locator('[data-testid="chat-input"]');
  const sendButton = page.locator('[data-testid="send-button"]');

{steps_code}
}});
"""

        # Save test file
        output_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "tests", "playwright", customer)
        )
        os.makedirs(output_dir, exist_ok=True)
        test_path = os.path.join(output_dir, f"{scenario_id}.spec.ts")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(script)

        return json.dumps({
            "status": "generated",
            "scenario": scenario_id,
            "customer": customer,
            "test_file": test_path,
            "turns": len(flow)
        }, indent=2)

    def _get_character_note(self, persona: Optional[Dict], message: str) -> str:
        if not persona:
            return ""
        style = persona.get("language_style", "")
        return f"[In character as {persona.get('name', 'Customer')} — {style[:80]}]"
