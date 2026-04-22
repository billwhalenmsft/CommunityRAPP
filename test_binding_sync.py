import unittest
import importlib.util
import pathlib


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
should_patch_topic = binding_sync.should_patch_topic


class TestBindingSync(unittest.TestCase):
    def test_should_patch_topic_skips_baseline(self):
        self.assertFalse(should_patch_topic("SAP Vendor Lookup"))
        self.assertTrue(should_patch_topic("SAP List My PRs"))

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


if __name__ == "__main__":
    unittest.main()
