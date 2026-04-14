"""
Agent: MfgCoE SME Agent
Purpose: Manufacturing Business Subject Matter Expert for the Discrete Manufacturing CoE.
         Generates SOPs, documents standard business processes, defines agentic use cases
         for CRM and Discrete Manufacturing scenarios, and accumulates domain knowledge.

Actions:
  generate_sop         — Generate a structured SOP for a manufacturing process
  document_process     — Document a standard business process (CRM, order mgmt, service, etc.)
  define_use_case      — Define an agentic AI use case for a Discrete Mfg scenario
  review_sop           — Review and suggest improvements to an existing SOP
  add_to_knowledge_base — Save a learned pattern or insight to the knowledge base
  search_knowledge_base — Search accumulated domain knowledge
  list_sops            — List all generated SOPs
  get_sop_template     — Get the standard SOP template structure
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.basic_agent import BasicAgent
from customers.mfg_coe.agents.context_card_loader import load_context_card, list_context_cards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOP_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "sops")
)
KNOWLEDGE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
)


class MfgCoESMEAgent(BasicAgent):
    """
    Manufacturing Business SME — SOPs, process docs, and use case definitions
    for Discrete Manufacturing CRM and agentic scenarios.
    """

    def __init__(self):
        self.name = "MfgCoESME"
        self.metadata = {
            "name": self.name,
            "description": (
                "Manufacturing Business SME agent for the Discrete Mfg CoE. "
                "Generates SOPs, documents business processes (CRM, order management, "
                "field service, warranty), defines agentic AI use cases, and builds up "
                "the CoE knowledge base with Discrete Manufacturing domain expertise. "
                "Use this agent when you need SOPs, process documentation, or use case definitions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "generate_sop",
                            "document_process",
                            "define_use_case",
                            "review_sop",
                            "add_to_knowledge_base",
                            "search_knowledge_base",
                            "list_sops",
                            "get_sop_template"
                        ],
                        "description": "SME action to perform"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic, process name, or use case title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description or context for the request"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["master_ce_mfg", "mfg_gold_template", "generic"],
                        "description": "Target demo environment (loads context card)"
                    },
                    "process_area": {
                        "type": "string",
                        "enum": [
                            "crm", "order_management", "warranty", "field_service",
                            "case_management", "returns_rma", "parts_service",
                            "dealer_management", "customer_onboarding", "quote_to_cash"
                        ],
                        "description": "Business process area"
                    },
                    "sop_filename": {
                        "type": "string",
                        "description": "Filename of existing SOP to review (without .md)"
                    },
                    "knowledge_content": {
                        "type": "string",
                        "description": "Knowledge/pattern to save to knowledge base"
                    },
                    "knowledge_topic": {
                        "type": "string",
                        "description": "Topic name for knowledge base entry"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Query to search knowledge base"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "list_sops")
        handlers = {
            "generate_sop":           self._generate_sop,
            "document_process":       self._document_process,
            "define_use_case":        self._define_use_case,
            "review_sop":             self._review_sop,
            "add_to_knowledge_base":  self._add_to_knowledge_base,
            "search_knowledge_base":  self._search_knowledge_base,
            "list_sops":              self._list_sops,
            "get_sop_template":       self._get_sop_template,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error(f"MfgCoESMEAgent error in {action}: {e}")
            return json.dumps({"error": str(e)})

    def _generate_sop(self, **kwargs) -> str:
        topic = kwargs.get("topic", "Untitled Process")
        description = kwargs.get("description", "")
        environment = kwargs.get("environment", "generic")
        process_area = kwargs.get("process_area", "crm")

        # Load environment context if specified
        env_context = ""
        if environment != "generic":
            try:
                env_context = load_context_card(environment)
            except Exception:
                pass

        # Generate structured SOP
        now = datetime.utcnow()
        safe_name = topic.lower().replace(" ", "_").replace("/", "_")[:50]
        version = "v1.0"
        filename = f"{safe_name}_{now.strftime('%Y%m%d')}"

        sop_content = f"""# SOP: {topic}

**Version:** {version}  
**Process Area:** {process_area.replace("_", " ").title()}  
**Target Environment:** {environment.replace("_", " ").title()}  
**Created:** {now.strftime("%Y-%m-%d")}  
**Author:** MfgCoE SME Agent  
**Status:** Draft

---

## 1. Purpose

{description or f"This SOP defines the standard process for {topic} within the Discrete Manufacturing environment."}

## 2. Scope

This SOP applies to:
- **Process Area:** {process_area.replace("_", " ").title()}
- **Environment:** {environment.replace("_", " ").title()}
- **Users:** [Define applicable roles — e.g., Sales Rep, Service Agent, Field Tech]

## 3. Prerequisites

Before beginning this process, ensure:
- [ ] Access to {environment.replace("_", " ").title()} is confirmed
- [ ] Required data is available (account, product, case details as applicable)
- [ ] [Add additional prerequisites]

## 4. Process Steps

### Step 1: [First Step Title]
**Actor:** [Role]  
**System:** [D365 / Copilot Studio / Power Automate]  
**Action:** [Describe the action]  
**Expected Outcome:** [What should happen]

### Step 2: [Second Step Title]
**Actor:** [Role]  
**System:** [System]  
**Action:** [Describe the action]  
**Expected Outcome:** [What should happen]

### Step 3: [Third Step Title]
**Actor:** [Role]  
**System:** [System]  
**Action:** [Describe the action]  
**Expected Outcome:** [What should happen]

> **Note:** Add additional steps as needed following the same format.

## 5. Decision Points

| Condition | Action |
|---|---|
| [If X happens] | [Do Y] |
| [If Z happens] | [Escalate to / Do W] |

## 6. Exception Handling

| Exception | Owner | Resolution |
|---|---|---|
| [Exception type] | [Role] | [Resolution steps] |

## 7. Success Criteria

This process is complete when:
- [ ] [Success criterion 1]
- [ ] [Success criterion 2]

## 8. Related SOPs & Documents

- [Link to related SOPs]
- [Link to related use cases]

## 9. Change Log

| Version | Date | Change | Author |
|---|---|---|---|
| v1.0 | {now.strftime("%Y-%m-%d")} | Initial draft | MfgCoE SME Agent |

---
{f"## 10. Environment Notes{chr(10)}{chr(10)}{env_context[:500]}..." if env_context else ""}
"""

        # Save to sops/ directory
        os.makedirs(SOP_DIR, exist_ok=True)
        sop_path = os.path.join(SOP_DIR, f"{filename}.md")
        with open(sop_path, "w", encoding="utf-8") as f:
            f.write(sop_content)

        return json.dumps({
            "status": "generated",
            "sop_filename": f"{filename}.md",
            "sop_path": sop_path,
            "topic": topic,
            "version": version,
            "next_steps": "Review the SOP, fill in process steps, and open a GitHub PR with label 'sop-review' for versioning."
        }, indent=2)

    def _document_process(self, **kwargs) -> str:
        topic = kwargs.get("topic", "Business Process")
        description = kwargs.get("description", "")
        process_area = kwargs.get("process_area", "crm")

        process_doc = {
            "process_name": topic,
            "process_area": process_area,
            "description": description,
            "actors": [],
            "systems": ["D365 Customer Engagement", "Copilot Studio"],
            "inputs": [],
            "outputs": [],
            "kpis": [],
            "pain_points": [],
            "agentic_opportunities": [],
            "documented_at": datetime.utcnow().isoformat(),
            "documented_by": "MfgCoE SME Agent",
            "status": "draft"
        }

        # Save to knowledge_base
        safe_name = topic.lower().replace(" ", "_")[:40]
        kb_path = os.path.join(KNOWLEDGE_DIR, f"process_{safe_name}.json")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(process_doc, f, indent=2)

        return json.dumps({
            "status": "documented",
            "process": topic,
            "path": kb_path,
            "next_steps": "Fill in actors, inputs/outputs, KPIs, pain points, and agentic opportunities. Then generate an SOP from this process definition."
        }, indent=2)

    def _define_use_case(self, **kwargs) -> str:
        topic = kwargs.get("topic", "AI Use Case")
        description = kwargs.get("description", "")
        process_area = kwargs.get("process_area", "crm")
        environment = kwargs.get("environment", "master_ce_mfg")

        use_case = {
            "use_case_title": topic,
            "process_area": process_area,
            "target_environment": environment,
            "problem_statement": description,
            "agent_type": "TBD — recommend after architecture review",
            "personas_served": [],
            "trigger": "TBD",
            "inputs_required": [],
            "outputs_produced": [],
            "d365_entities_involved": [],
            "copilot_studio_topics": [],
            "value_proposition": {
                "time_saved": "TBD",
                "error_reduction": "TBD",
                "customer_impact": "TBD"
            },
            "complexity": "TBD",
            "priority": "TBD",
            "status": "raw-idea",
            "defined_at": datetime.utcnow().isoformat(),
            "defined_by": "MfgCoE SME Agent"
        }

        safe_name = topic.lower().replace(" ", "_")[:40]
        uc_path = os.path.join(KNOWLEDGE_DIR, f"usecase_{safe_name}.json")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        with open(uc_path, "w", encoding="utf-8") as f:
            json.dump(use_case, f, indent=2)

        return json.dumps({
            "status": "defined",
            "use_case": topic,
            "path": uc_path,
            "next_steps": [
                "Have the Architect agent design the technical solution",
                "Have the Developer agent scaffold the agent code",
                "Create a GitHub Issue to track this use case through the pipeline"
            ]
        }, indent=2)

    def _review_sop(self, **kwargs) -> str:
        sop_filename = kwargs.get("sop_filename", "")
        if not sop_filename:
            return json.dumps({"error": "sop_filename required"})

        sop_path = os.path.join(SOP_DIR, f"{sop_filename}.md" if not sop_filename.endswith(".md") else sop_filename)
        if not os.path.exists(sop_path):
            return json.dumps({"error": f"SOP not found: {sop_path}"})

        with open(sop_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic structural checks
        checks = {
            "has_purpose": "## 1. Purpose" in content or "Purpose" in content,
            "has_scope": "## 2. Scope" in content or "Scope" in content,
            "has_steps": "Step 1" in content or "## 4. Process Steps" in content,
            "has_exceptions": "Exception" in content,
            "has_success_criteria": "Success Criteria" in content,
            "has_change_log": "Change Log" in content,
            "steps_filled": "[First Step" not in content,
            "has_actors": "Actor" in content,
        }

        missing = [k for k, v in checks.items() if not v]
        score = int((sum(checks.values()) / len(checks)) * 100)

        return json.dumps({
            "sop": sop_filename,
            "completeness_score": f"{score}%",
            "checks": checks,
            "missing_sections": missing,
            "recommendation": "Complete missing sections before opening PR for review." if missing else "SOP looks complete — ready for PR review.",
            "character_count": len(content)
        }, indent=2)

    def _add_to_knowledge_base(self, **kwargs) -> str:
        content = kwargs.get("knowledge_content", "")
        topic = kwargs.get("knowledge_topic", "general")
        if not content:
            return json.dumps({"error": "knowledge_content required"})

        safe_topic = topic.lower().replace(" ", "_")[:40]
        kb_file = os.path.join(KNOWLEDGE_DIR, f"{safe_topic}.md")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

        # Append to existing file or create new
        existing = ""
        if os.path.exists(kb_file):
            with open(kb_file, "r", encoding="utf-8") as f:
                existing = f.read()

        entry = f"\n\n## Entry — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n{content}\n"
        if not existing:
            entry = f"# Knowledge Base: {topic}\n\n*Accumulated by MfgCoE SME + Architect Agents*\n{entry}"

        with open(kb_file, "w", encoding="utf-8") as f:
            f.write(existing + entry)

        return json.dumps({"status": "saved", "topic": topic, "path": kb_file})

    def _search_knowledge_base(self, **kwargs) -> str:
        query = kwargs.get("search_query", "").lower()
        if not query:
            return json.dumps({"error": "search_query required"})

        results = []
        if os.path.exists(KNOWLEDGE_DIR):
            for fname in os.listdir(KNOWLEDGE_DIR):
                fpath = os.path.join(KNOWLEDGE_DIR, fname)
                if os.path.isfile(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    if query in content.lower():
                        # Find matching lines
                        matching_lines = [l.strip() for l in content.splitlines() if query in l.lower()][:3]
                        results.append({
                            "file": fname,
                            "matches": matching_lines
                        })

        return json.dumps({"query": query, "files_matched": len(results), "results": results}, indent=2)

    def _list_sops(self, **kwargs) -> str:
        sops = []
        if os.path.exists(SOP_DIR):
            for fname in os.listdir(SOP_DIR):
                if fname.endswith(".md"):
                    fpath = os.path.join(SOP_DIR, fname)
                    stat = os.stat(fpath)
                    sops.append({
                        "filename": fname,
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                    })
        return json.dumps({"total_sops": len(sops), "sops": sops}, indent=2)

    def _get_sop_template(self, **kwargs) -> str:
        return json.dumps({
            "template_sections": [
                "1. Purpose",
                "2. Scope",
                "3. Prerequisites",
                "4. Process Steps (Step N: Title, Actor, System, Action, Expected Outcome)",
                "5. Decision Points (table)",
                "6. Exception Handling (table)",
                "7. Success Criteria",
                "8. Related SOPs & Documents",
                "9. Change Log"
            ],
            "required_fields": ["purpose", "scope", "at_least_3_steps", "success_criteria"],
            "tip": "Use action=generate_sop with topic and description to auto-generate a pre-filled template."
        }, indent=2)
