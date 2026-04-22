import unittest
import importlib.util
import json
import pathlib
import yaml


REPO_ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = REPO_ROOT / "customers" / "mfg_coe" / "skills" / "copilot-studio-binding-sync" / "binding_sync.py"
if not MODULE_PATH.exists():
    raise FileNotFoundError(f"Expected binding_sync.py at {MODULE_PATH}")
SPEC = importlib.util.spec_from_file_location("binding_sync", MODULE_PATH)
binding_sync = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(binding_sync)

normalize_flow_tool_data = binding_sync.normalize_flow_tool_data
normalize_topic_yaml = binding_sync.normalize_topic_yaml
apply_ux_payload = binding_sync._apply_ux_payload
load_ux_payloads = binding_sync._load_ux_payloads
should_patch_topic = binding_sync.should_patch_topic
UX_PAYLOADS_DIR = binding_sync.UX_PAYLOADS_DIR


class TestBindingSync(unittest.TestCase):
    def test_should_patch_topic_includes_all_sap_topics(self):
        for topic_name in [
            "SAP Vendor Lookup",
            "SAP Create PR",
            "SAP Get PR Status",
            "SAP Approve Reject PR",
            "SAP Cancel Edit PR",
            "SAP Send Reminder",
            "SAP List My PRs",
            "SAP Pending Approvals",
        ]:
            self.assertTrue(should_patch_topic(topic_name))

    def test_topic_normalization_converts_question_and_bindings(self):
        raw = """
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  actions:
    - kind: Question
      id: askUser
      interruptionPolicy:
        allowInterruption: true
      variable: Topic.Requestor
      prompt: Who are you?
      entity:
        kind: TextPrebuiltEntity
    - kind: InvokeFlowAction
      id: callFlow
      input:
        binding:
          user_id: "demo-user"
      output:
        binding:
          total_value: Topic.Total
          status_label: Topic.Status
          results_count: Topic.Count
      flowId: abc123
"""
        updated, changed = normalize_topic_yaml(raw)
        self.assertTrue(changed)
        self.assertIn("alwaysPrompt: false", updated)
        self.assertIn("allowInterruption: true", updated)
        self.assertIn("variable: init:Topic.Requestor", updated)
        self.assertIn("entity: StringPrebuiltEntity", updated)
        self.assertIn('user_id: ="demo-user"', updated)
        self.assertIn("total_amount: Topic.Total", updated)
        self.assertIn("status: Topic.Status", updated)
        self.assertIn("pr_count: Topic.Count", updated)
        self.assertIn("flowId: abc123", updated)

    def test_flow_tool_cache_normalization(self):
        raw = """output: { total_value: 1, status_label: "Open", results_count: 3 }
requester: "demo-user" """
        updated, changed = normalize_flow_tool_data(raw)
        self.assertTrue(changed)
        self.assertIn("total_amount", updated)
        self.assertIn("status", updated)
        self.assertIn("pr_count", updated)
        self.assertIn('requester: ="demo-user"', updated)

    def test_apply_ux_replaces_message_and_preserves_inputs_and_flow_bindings(self):
        raw = """
kind: AdaptiveDialog
inputs:
  - kind: AutomaticTaskInput
    propertyName: PRNumber
    description: PR number
    entity: StringPrebuiltEntity
beginDialog:
  kind: OnRecognizedIntent
  id: main
  actions:
    - kind: InvokeFlowAction
      id: callFlow
      output:
        binding:
          pr_count: Topic.Count
          total_amount: Topic.Amount
    - kind: SendActivity
      id: finalMsg
      activity:
        text: old text
"""
        payload = {
            "topic": "SAP Get PR Status",
            "target_action_ids": ["finalMsg"],
            "markdown": "**Updated** message",
            "adaptive_card": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.5",
                "body": [{"type": "TextBlock", "text": "Hello"}],
            },
        }
        updated, changed = apply_ux_payload(raw, payload)
        self.assertTrue(changed)

        doc = yaml.safe_load(updated)
        self.assertEqual(doc["inputs"][0]["propertyName"], "PRNumber")
        flow_binding = doc["beginDialog"]["actions"][0]["output"]["binding"]
        self.assertEqual(flow_binding["pr_count"], "Topic.Count")
        self.assertEqual(flow_binding["total_amount"], "Topic.Amount")
        send_activity = doc["beginDialog"]["actions"][1]["activity"]
        self.assertEqual(send_activity["text"], "**Updated** message")
        self.assertEqual(send_activity["attachments"][0]["contentType"], "application/vnd.microsoft.card.adaptive")

    def test_apply_ux_is_idempotent(self):
        raw = """
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  actions:
    - kind: SendActivity
      id: finalMsg
      activity:
        text: old text
"""
        payload = {
            "topic": "SAP Send Reminder",
            "target_action_ids": ["finalMsg"],
            "markdown": "**🔔 Reminder Sent — `${Topic.PRNumber}`**",
        }
        first, first_changed = apply_ux_payload(raw, payload)
        second, second_changed = apply_ux_payload(first, payload)
        self.assertTrue(first_changed)
        self.assertFalse(second_changed)
        self.assertEqual(first, second)

    def test_adaptive_card_payloads_are_valid_json(self):
        payloads = load_ux_payloads(UX_PAYLOADS_DIR)
        self.assertEqual(len(payloads), 8)
        cards_checked = 0
        for payload in payloads.values():
            card = payload.get("adaptive_card")
            if not card:
                continue
            encoded = json.dumps(card)
            decoded = json.loads(encoded)
            self.assertEqual(decoded.get("type"), "AdaptiveCard")
            self.assertEqual(decoded.get("version"), "1.5")
            cards_checked += 1
        self.assertEqual(cards_checked, 4)


if __name__ == "__main__":
    unittest.main()
