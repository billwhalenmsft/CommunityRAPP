#!/usr/bin/env python3
"""
Copilot Studio Binding Sync (Python implementation)

Fixes topic↔flow binding drift for the Ascend SAP Procurement Agent.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Tuple

import requests
import yaml


ASCEND_BROKEN_TOPICS = {
    "SAP Create PR",
    "SAP Get PR Status",
    "SAP Approve Reject PR",
    "SAP Cancel Edit PR",
    "SAP Send Reminder",
    "SAP List My PRs",
    "SAP Pending Approvals",
}
BASELINE_TOPIC_NAME = "SAP Vendor Lookup"
FLOW_TOOL_NAME_PREFIX = "Ascend: SAP "
OUTPUT_RENAMES = {
    "total_value": "total_amount",
    "status_label": "status",
    "results_count": "pr_count",
}


def get_access_token(org_url: str) -> str:
    az_cmd = "az.cmd" if os.name == "nt" else "az"
    result = subprocess.run(
        [az_cmd, "account", "get-access-token", "--resource", org_url, "--query", "accessToken", "-o", "tsv"],
        capture_output=True,
        text=True,
        check=False,
        shell=(os.name == "nt"),
    )
    token = result.stdout.strip()
    if result.returncode != 0 or not token:
        raise RuntimeError(
            f"Unable to acquire token with az cli (exit code {result.returncode}): {result.stderr.strip()}"
        )
    return token


def build_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "If-Match": "*",
    }


def list_botcomponents(org_url: str, headers: Dict[str, str], filter_expr: str) -> List[Dict[str, Any]]:
    base = f"{org_url.rstrip('/')}/api/data/v9.2/botcomponents"
    params = {"$filter": filter_expr, "$select": "botcomponentid,name,componenttype,data"}
    all_rows: List[Dict[str, Any]] = []
    next_url = base

    while next_url:
        if next_url == base:
            resp = requests.get(next_url, headers=headers, params=params, timeout=60)
        else:
            resp = requests.get(next_url, headers=headers, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        all_rows.extend(payload.get("value", []))
        next_url = payload.get("@odata.nextLink")
    return all_rows


def patch_component_data(org_url: str, headers: Dict[str, str], component_id: str, new_data: str) -> None:
    url = f"{org_url.rstrip('/')}/api/data/v9.2/botcomponents({component_id})"
    resp = requests.patch(url, headers=headers, json={"data": new_data}, timeout=60)
    resp.raise_for_status()


def _rename_keys(obj: Any, rename_map: Dict[str, str]) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for key, value in obj.items():
            new_key = rename_map.get(key, key)
            out[new_key] = _rename_keys(value, rename_map)
        return out
    if isinstance(obj, list):
        return [_rename_keys(item, rename_map) for item in obj]
    return obj


def _convert_question_to_v1(question: Dict[str, Any]) -> None:
    interruption_policy = question.pop("interruptionPolicy", None)
    if isinstance(interruption_policy, dict) and "allowInterruption" in interruption_policy:
        question["allowInterruption"] = interruption_policy["allowInterruption"]
    if "allowInterruption" not in question:
        question["allowInterruption"] = True
    question["alwaysPrompt"] = False

    var = question.get("variable")
    if isinstance(var, str) and var.startswith("Topic."):
        question["variable"] = f"init:{var}"

    entity = question.get("entity")
    if isinstance(entity, dict) and entity.get("kind") == "TextPrebuiltEntity":
        question["entity"] = "StringPrebuiltEntity"


def _normalize_flow_action(flow_action: Dict[str, Any]) -> None:
    output = flow_action.get("output")
    if isinstance(output, dict) and isinstance(output.get("binding"), dict):
        output["binding"] = _rename_keys(output["binding"], OUTPUT_RENAMES)

    input_obj = flow_action.get("input")
    if isinstance(input_obj, dict) and isinstance(input_obj.get("binding"), dict):
        for k, v in list(input_obj["binding"].items()):
            if isinstance(v, str) and not v.startswith("="):
                stripped = v.strip()
                if is_power_fx_expression(stripped):
                    input_obj["binding"][k] = f"={stripped}"
                elif (stripped.startswith('"') and stripped.endswith('"')) or (
                    stripped.startswith("'") and stripped.endswith("'")
                ):
                    input_obj["binding"][k] = f"={stripped}"
                else:
                    input_obj["binding"][k] = f'="{stripped}"'


def is_power_fx_expression(value: str) -> bool:
    if value.startswith(("Topic.", "System.", "Global.", "Conversation.", "User.", "init:")):
        return True
    # Matches Power Fx function calls, e.g. Concatenate(...)
    return bool(re.match(r"^[A-Za-z_][\w.]*\(", value))


def _walk_and_normalize(obj: Any) -> None:
    if isinstance(obj, dict):
        kind = obj.get("kind")
        if kind == "Question":
            _convert_question_to_v1(obj)
        elif kind == "InvokeFlowAction":
            _normalize_flow_action(obj)
        for value in obj.values():
            _walk_and_normalize(value)
    elif isinstance(obj, list):
        for item in obj:
            _walk_and_normalize(item)


def _find_first_question(obj: Any) -> Dict[str, Any] | None:
    if isinstance(obj, dict):
        if obj.get("kind") == "Question":
            return obj
        for v in obj.values():
            found = _find_first_question(v)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_first_question(item)
            if found is not None:
                return found
    return None


def _ensure_topic_inputs(doc: Dict[str, Any]) -> bool:
    """Add a top-level `inputs:` block so the orchestrator can pre-fill the
    first Question's variable (slot-filling). Returns True if changed."""
    if not isinstance(doc, dict) or doc.get("kind") != "AdaptiveDialog":
        return False
    if isinstance(doc.get("inputs"), list) and len(doc["inputs"]) > 0:
        return False  # already has inputs

    question = _find_first_question(doc)
    if not question:
        return False

    var = question.get("variable", "")
    if not isinstance(var, str):
        return False
    # Accept "init:Topic.Name" or "Topic.Name"
    m = re.match(r"^(?:init:)?Topic\.([A-Za-z0-9_]+)$", var)
    if not m:
        return False
    prop_name = m.group(1)

    entity = question.get("entity")
    if isinstance(entity, dict):
        entity_val = entity.get("name") or entity.get("kind") or "StringPrebuiltEntity"
    elif isinstance(entity, str):
        entity_val = entity
    else:
        entity_val = "StringPrebuiltEntity"

    description = question.get("prompt") or f"User-supplied {prop_name}"
    if isinstance(description, str):
        description = description.strip().splitlines()[0][:240]

    new_input = {
        "kind": "AutomaticTaskInput",
        "propertyName": prop_name,
        "description": description,
        "entity": entity_val,
    }

    # Insert `inputs:` right after `kind:` for readability
    new_doc: Dict[str, Any] = {}
    inserted = False
    for k, v in doc.items():
        new_doc[k] = v
        if k == "kind" and not inserted:
            new_doc["inputs"] = [new_input]
            inserted = True
    if not inserted:
        new_doc["inputs"] = [new_input]
    doc.clear()
    doc.update(new_doc)
    return True


def normalize_topic_yaml(raw_yaml: str) -> Tuple[str, bool]:
    doc = yaml.safe_load(raw_yaml)
    if doc is None:
        return raw_yaml, False

    before = json.dumps(doc, sort_keys=True, default=str)
    doc = _rename_keys(doc, OUTPUT_RENAMES)
    _walk_and_normalize(doc)
    _ensure_topic_inputs(doc)
    after = json.dumps(doc, sort_keys=True, default=str)
    changed = before != after
    if not changed:
        return raw_yaml, False
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200), True


def normalize_flow_tool_data(raw_data: str) -> Tuple[str, bool]:
    updated = raw_data
    for old_name, new_name in OUTPUT_RENAMES.items():
        updated = re.sub(rf"\b{re.escape(old_name)}\b", new_name, updated)
    updated = re.sub(r'(:\s*)"demo-user"', r'\1="demo-user"', updated)
    return updated, updated != raw_data


def should_patch_topic(topic_name: str) -> bool:
    return topic_name == BASELINE_TOPIC_NAME or topic_name in ASCEND_BROKEN_TOPICS


def run(org_url: str, bot_id: str, dry_run: bool) -> None:
    token = get_access_token(org_url)
    headers = build_headers(token)

    topics = list_botcomponents(
        org_url,
        headers,
        f"_parentbotid_value eq {bot_id} and componenttype eq 9",
    )

    flow_tools = list_botcomponents(
        org_url,
        headers,
        f"_parentbotid_value eq {bot_id} and contains(name,'{FLOW_TOOL_NAME_PREFIX}')",
    )

    topics_inspected = 0
    topics_changed = 0
    tools_changed = 0

    for topic in topics:
        name = topic.get("name", "")
        if not should_patch_topic(name):
            continue
        topics_inspected += 1
        current_data = topic.get("data") or ""
        try:
            new_data, changed = normalize_topic_yaml(current_data)
        except Exception as ex:
            print(f"[WARN] Failed to normalize topic '{name}': {ex}")
            continue

        if not changed:
            continue
        topics_changed += 1
        print(f"[PATCH] Topic: {name}")
        if not dry_run:
            patch_component_data(org_url, headers, topic["botcomponentid"], new_data)

    for tool in flow_tools:
        current_data = tool.get("data") or ""
        new_data, changed = normalize_flow_tool_data(current_data)
        if not changed:
            continue
        tools_changed += 1
        print(f"[PATCH] Flow tool cache: {tool.get('name')}")
        if not dry_run:
            patch_component_data(org_url, headers, tool["botcomponentid"], new_data)

    mode = "DRY RUN" if dry_run else "APPLY"
    print("\n=== Binding Sync Summary ===")
    print(f"mode: {mode}")
    print(f"topics_inspected: {topics_inspected}")
    print(f"topic_patches: {topics_changed}")
    print(f"flow_tool_patches: {tools_changed}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix Copilot Studio topic↔flow binding drift for Ascend SAP bot.")
    parser.add_argument("--org-url", default=os.getenv("COPILOT_STUDIO_ORG_URL"))
    parser.add_argument("--bot-id", default=os.getenv("COPILOT_STUDIO_BOT_ID"))
    parser.add_argument("--apply", action="store_true", help="Apply PATCH calls. Default is dry-run.")
    args = parser.parse_args(argv)
    if not args.org_url or not args.bot_id:
        parser.error(
            "--org-url and --bot-id are required (or set COPILOT_STUDIO_ORG_URL/COPILOT_STUDIO_BOT_ID)."
        )
    return args


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    run(org_url=args.org_url, bot_id=args.bot_id, dry_run=not args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
