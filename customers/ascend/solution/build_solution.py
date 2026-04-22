#!/usr/bin/env python3
"""
build_solution.py — Ascend Procurement Agent Solution Builder
=============================================================
Packages the Ascend Power Platform solution ZIP from source files.
Validates XML structure before packaging to catch errors before import.

Usage:
    python customers/ascend/solution/build_solution.py          # build + validate
    python customers/ascend/solution/build_solution.py --validate-only

Output:
    customers/ascend/solution/AscendProcurementAgent_1_0_0_0.zip

Power Platform solution ZIP structure rules (enforced by validator):
    [Content_Types].xml  — MUST have xmlns="...openxmlformats.org/package/2006/content-types"
    solution.xml         — root must be <ImportExportXml> with version + SolutionPackageVersion
    customizations.xml   — entity definitions must be INLINE (not in Entities/ subfolders)
                           root must be <ImportExportXml>
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOLUTION_DIR = Path(__file__).resolve().parent
SOLUTION_SRC = SOLUTION_DIR / "solution_src"
TOPICS_DIR = REPO_ROOT / "transpiled" / "copilot_studio_native" / "ascend_pr_agent" / "topics"
MANIFEST_FILE = REPO_ROOT / "transpiled" / "copilot_studio_native" / "ascend_pr_agent" / "agent_manifest.json"
INSTRUCTIONS_FILE = REPO_ROOT / "transpiled" / "copilot_studio_native" / "ascend_pr_agent" / "instructions.md"
OUTPUT_ZIP = SOLUTION_DIR / "AscendProcurementAgent_1_0_0_0.zip"

BOT_SCHEMA = "ascend_ProcurementAssistant"
TOPIC_TO_SCHEMA = {
    "topic_create_purchase_requisition.yaml": "ascend_topic_CreatePurchaseRequisition",
    "topic_check_pr_status.yaml":             "ascend_topic_CheckPRStatus",
    "topic_approve_reject_pr.yaml":           "ascend_topic_ApproveRejectPR",
    "topic_pr_followup_actions.yaml":         "ascend_topic_PRFollowUpActions",
}

OPC_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


# ── Validator ──────────────────────────────────────────────────────────────────

def validate() -> list[str]:
    """
    Validate all solution source files before packaging.
    Returns list of error strings; empty list = pass.

    Rules enforced:
      1. [Content_Types].xml root element must be {OPC_NS}Types
      2. solution.xml root element must be ImportExportXml with required attributes
      3. customizations.xml root element must be ImportExportXml
      4. customizations.xml must NOT be empty (entity definitions must be inline)
      5. All referenced files must exist
    """
    errors = []

    # ── Rule 1: [Content_Types].xml namespace ──────────────────────────────
    ct_file = SOLUTION_SRC / "[Content_Types].xml"
    if not ct_file.exists():
        errors.append("[Content_Types].xml not found")
    else:
        try:
            tree = ET.parse(ct_file)
            root = tree.getroot()
            expected_tag = f"{{{OPC_NS}}}Types"
            if root.tag != expected_tag:
                if root.tag == "Types":
                    errors.append(
                        "[Content_Types].xml: <Types> is missing the required OPC namespace. "
                        f'Must be: <Types xmlns="{OPC_NS}">  '
                        "(This causes 'Required Types tag not found' on import)"
                    )
                else:
                    errors.append(f"[Content_Types].xml: unexpected root element '{root.tag}'. Expected 'Types' with OPC namespace.")
        except ET.ParseError as e:
            errors.append(f"[Content_Types].xml: XML parse error — {e}")

    # ── Rule 2: solution.xml structure ────────────────────────────────────
    sol_file = SOLUTION_SRC / "solution.xml"
    if not sol_file.exists():
        errors.append("solution.xml not found")
    else:
        try:
            tree = ET.parse(sol_file)
            root = tree.getroot()
            if root.tag != "ImportExportXml":
                errors.append(f"solution.xml: root must be <ImportExportXml>, got <{root.tag}>")
            else:
                for attr in ("version", "SolutionPackageVersion"):
                    if attr not in root.attrib:
                        errors.append(f"solution.xml: missing required attribute '{attr}' on <ImportExportXml>")
                manifest = root.find("SolutionManifest")
                if manifest is None:
                    errors.append("solution.xml: missing <SolutionManifest> child element")
                else:
                    for req in ("UniqueName", "Version", "Managed"):
                        if manifest.find(req) is None:
                            errors.append(f"solution.xml: <SolutionManifest> missing <{req}>")
        except ET.ParseError as e:
            errors.append(f"solution.xml: XML parse error — {e}")

    # ── Rule 3 & 4: customizations.xml ────────────────────────────────────
    cust_file = SOLUTION_SRC / "customizations.xml"
    if not cust_file.exists():
        errors.append("customizations.xml not found")
    else:
        try:
            tree = ET.parse(cust_file)
            root = tree.getroot()
            if root.tag != "ImportExportXml":
                errors.append(f"customizations.xml: root must be <ImportExportXml>, got <{root.tag}>")
            entities_node = root.find("Entities")
            if entities_node is None:
                errors.append("customizations.xml: missing <Entities> element — entity definitions must be inline here, not in Entities/ subfolders")
            elif len(list(entities_node)) == 0:
                errors.append("customizations.xml: <Entities> is empty — entity definitions must be inline (Power Platform ignores separate Entities/*.xml files during import)")
            else:
                # ── Rule 5: every entity must have PrimaryNameAttribute ────
                for entity_elem in entities_node.findall("Entity"):
                    entity_name_elem = entity_elem.find("Name")
                    entity_name = entity_name_elem.text if entity_name_elem is not None else "unknown"
                    entity_info = entity_elem.find("EntityInfo/entity")
                    if entity_info is None:
                        errors.append(f"customizations.xml: <Entity> '{entity_name}' missing <EntityInfo><entity> element")
                        continue
                    pna = entity_info.get("PrimaryNameAttribute")
                    if not pna:
                        errors.append(
                            f"customizations.xml: Entity '{entity_name}' missing PrimaryNameAttribute on <entity> element. "
                            f"(Causes error 0x80044355: PrimaryName attribute not found at import)"
                        )
                    else:
                        # Verify the referenced attribute actually exists in <Attributes>
                        attrs = entity_elem.find("Attributes")
                        if attrs is not None:
                            attr_names = [a.get("PhysicalName") for a in attrs.findall("Attribute")]
                            if pna not in attr_names:
                                errors.append(
                                    f"customizations.xml: Entity '{entity_name}' PrimaryNameAttribute='{pna}' "
                                    f"not found in <Attributes>. Available: {attr_names}"
                                )
                            else:
                                # Also verify the attribute itself has IsPrimaryName flag
                                for a in attrs.findall("Attribute"):
                                    if a.get("PhysicalName") == pna:
                                        if a.find("IsPrimaryName") is None:
                                            errors.append(
                                                f"customizations.xml: Entity '{entity_name}' attribute '{pna}' "
                                                f"missing <IsPrimaryName>1</IsPrimaryName> — required alongside PrimaryNameAttribute "
                                                f"(otherwise error 0x80044355 at import)"
                                            )
                                        break
        except ET.ParseError as e:
            errors.append(f"customizations.xml: XML parse error — {e}")

    # ── Rule 5: required source files present ─────────────────────────────
    for required in ["solution.xml", "customizations.xml", "[Content_Types].xml"]:
        if not (SOLUTION_SRC / required).exists():
            errors.append(f"Required file missing: solution_src/{required}")

    env_xml = SOLUTION_SRC / "EnvironmentVariables" / "environmentvariables.xml"
    if not env_xml.exists():
        errors.append(f"Missing: {env_xml.relative_to(SOLUTION_DIR)}")

    return errors


def print_validation_result(errors: list[str]) -> bool:
    if not errors:
        print("  [validate] ✅ All checks passed")
        return True
    else:
        print(f"  [validate] ❌ {len(errors)} error(s) found — fix before importing:")
        for e in errors:
            print(f"             • {e}")
        return False


# ── Builder ────────────────────────────────────────────────────────────────────

def build():
    print("=" * 62)
    print("Ascend Procurement Agent — Solution Builder")
    print("=" * 62)

    # Validate first
    print("\n[step 1/3] Validating solution source files...")
    errors = validate()
    ok = print_validation_result(errors)
    if not ok:
        print("\n[ABORT] Fix validation errors before building ZIP.")
        sys.exit(1)

    print("\n[step 2/3] Packaging ZIP...")
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_file(zf, SOLUTION_SRC / "solution.xml",           "solution.xml")
        _add_file(zf, SOLUTION_SRC / "customizations.xml",     "customizations.xml")
        _add_file(zf, SOLUTION_SRC / "[Content_Types].xml",    "[Content_Types].xml")
        _add_file(zf, env_xml := SOLUTION_SRC / "EnvironmentVariables" / "environmentvariables.xml",
                  "EnvironmentVariables/environmentvariables.xml")

        workflows_dir = SOLUTION_SRC / "Workflows"
        if workflows_dir.exists():
            for flow_file in sorted(workflows_dir.glob("*.json")):
                _add_file(zf, flow_file, f"Workflows/{flow_file.name}")

        bot_base = f"BotComponents/{BOT_SCHEMA}"
        if MANIFEST_FILE.exists():
            _add_file(zf, MANIFEST_FILE, f"{bot_base}/agent_manifest.json")
        if INSTRUCTIONS_FILE.exists():
            _add_file(zf, INSTRUCTIONS_FILE, f"{bot_base}/instructions.md")
        if TOPICS_DIR.exists():
            for topic_file in sorted(TOPICS_DIR.glob("*.yaml")):
                schema = TOPIC_TO_SCHEMA.get(topic_file.name, topic_file.stem)
                _add_file(zf, topic_file, f"{bot_base}/Topics/{schema}.yaml")

        sample_data_dir = SOLUTION_DIR / "sample_data"
        if sample_data_dir.exists():
            for csv_file in sorted(sample_data_dir.glob("*.csv")):
                _add_file(zf, csv_file, f"SampleData/{csv_file.name}")

    print(f"\n[step 3/3] Verifying output ZIP...")
    size_kb = OUTPUT_ZIP.stat().st_size / 1024
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
        names = zf.namelist()

    required_in_zip = ["solution.xml", "customizations.xml", "[Content_Types].xml"]
    zip_errors = [f for f in required_in_zip if f not in names]
    if zip_errors:
        print(f"  [verify] ❌ Missing from ZIP: {zip_errors}")
        sys.exit(1)
    else:
        print(f"  [verify] ✅ ZIP valid — {len(names)} files, {size_kb:.1f} KB")

    print(f"\n[done] {OUTPUT_ZIP}")
    print(f"       {len(names)} files · {size_kb:.1f} KB")
    print()
    print("Import:")
    print("  make.powerapps.com → Solutions → Import solution")
    print(f"  Upload: {OUTPUT_ZIP.name}")
    print()
    print("⚠️  SAP DEMO MODE: All data emulates SAP ECC 6.0 via Dataverse.")
    print("   Flip ascend_DemoMode to FALSE + configure SAP ERP connector for production.")


def _add_file(zf: zipfile.ZipFile, src: Path, arc: str):
    if src.exists():
        zf.write(src, arc)
        print(f"  [add] {arc}")
    else:
        print(f"  [skip] Missing: {src.name}")


if __name__ == "__main__":
    if "--validate-only" in sys.argv:
        print("Validating solution source files...\n")
        errors = validate()
        ok = print_validation_result(errors)
        sys.exit(0 if ok else 1)
    else:
        build()
