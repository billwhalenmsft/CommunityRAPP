"""
D365 Demo Prep Agent
====================
RAPP agent for Dynamics 365 Customer Service demo preparation.

Actions:
  - list_customers: Show customers with D365 configs
  - get_config: Return customer D365 environment config
  - validate_environment: Check D365 org has expected demo data
  - provision_data: Generate accounts, contacts, and other demo records
  - run_powershell: Execute a numbered provisioning step (01-25)
  - generate_config_from_inputs: Create environment.json + demo-data.json from input schema
  - generate_demo_data: Use GPT-4o to generate realistic demo data from inputs
  - orchestrate_full_setup: End-to-end demo setup from inputs to provisioned D365

Requires: Azure CLI `az login` completed for Dataverse token acquisition.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from agents.basic_agent import BasicAgent

# Resolve d365 package relative to RAPP root
RAPP_ROOT = Path(__file__).resolve().parent.parent
D365_DIR = RAPP_ROOT / "d365"
SCRIPTS_DIR = D365_DIR / "scripts"
CUSTOMERS_DIR = RAPP_ROOT / "customers"


class D365DemoPrepAgent(BasicAgent):
    """
    Dynamics 365 demo environment preparation agent.

    Provisions demo data, validates environments, and manages D365 config
    across multiple customers in the RAPP platform.
    """

    def __init__(self):
        self.name = "D365DemoPrep"
        self.metadata = {
            "name": self.name,
            "description": (
                "Dynamics 365 Customer Service demo preparation agent. "
                "Provisions demo data (accounts, contacts, cases, queues, SLAs, KB articles), "
                "validates that a D365 org is demo-ready, lists customer configurations, "
                "runs PowerShell provisioning steps, and can generate complete demo configs from inputs. "
                "NEW: Use 'generate_config_from_inputs' or 'orchestrate_full_setup' for turnkey demo prep."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": (
                            "Action to perform: "
                            "'list_customers' shows customers with D365 configs, "
                            "'get_config' returns a customer's environment.json, "
                            "'validate_environment' checks the D365 org for expected data, "
                            "'provision_data' generates core demo records via API, "
                            "'run_powershell' executes a numbered provisioning script (01-25), "
                            "'generate_config_from_inputs' creates environment.json + demo-data.json from input schema, "
                            "'generate_demo_data' uses GPT-4o to generate realistic demo data, "
                            "'generate_demo_assets' creates HTML demo execution guide and supporting assets, "
                            "'orchestrate_full_setup' runs end-to-end setup from inputs to D365 with demo assets"
                        ),
                        "enum": [
                            "list_customers",
                            "get_config",
                            "validate_environment",
                            "provision_data",
                            "run_powershell",
                            "generate_config_from_inputs",
                            "generate_demo_data",
                            "generate_demo_assets",
                            "orchestrate_full_setup",
                            "run_customer_provisioner",
                            "enrich_timelines",
                            "backfill_brand_logos",
                            "demo_readiness_report",
                            "list_actions",
                        ],
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer folder name (e.g. 'zurnelkay', 'otis'). Required for most actions.",
                    },
                    "step_number": {
                        "type": "integer",
                        "description": "PowerShell step number (1-25) for run_powershell action.",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, show plan without making changes. Default: false.",
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Input data following d365_input_schema.json for generate_config_from_inputs or orchestrate_full_setup.",
                    },
                    "d365_org_url": {
                        "type": "string",
                        "description": "D365 organization URL (e.g., 'https://orgecbce8ef.crm.dynamics.com')",
                    },
                    "steps_to_run": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of step numbers to run for orchestrate_full_setup (default: [1,2,3,4,5,6,7,8])",
                    },
                    "ps_script": {
                        "type": "string",
                        "description": "Name of customer-specific PowerShell script (e.g. 'Provision-NavicoDemo.ps1', 'Provision-NavicoExtended.ps1', 'Provision-NavicoHeroCases.ps1', 'Add-NavicoTimelineEnrichment.ps1'). Used with run_customer_provisioner.",
                    },
                    "ps_action": {
                        "type": "string",
                        "description": "Action parameter to pass to the PS script (e.g. 'All', 'BrandLogo', 'HeroCases', 'Cleanup'). Passed as -Action flag.",
                    },
                    "ps_from_step": {
                        "type": "integer",
                        "description": "For 00-Setup.ps1: start from this step number (-From flag).",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        """Route to the appropriate handler based on action."""
        action = kwargs.get("action", "list_customers")

        try:
            if action == "list_customers":
                return self._list_customers()
            elif action == "get_config":
                return self._get_config(kwargs.get("customer_name"))
            elif action == "validate_environment":
                return self._validate_environment(kwargs.get("customer_name"))
            elif action == "provision_data":
                return self._provision_data(
                    kwargs.get("customer_name"),
                    kwargs.get("dry_run", False),
                )
            elif action == "run_powershell":
                return self._run_powershell(
                    kwargs.get("customer_name"),
                    kwargs.get("step_number"),
                )
            elif action == "generate_config_from_inputs":
                return self._generate_config_from_inputs(
                    kwargs.get("customer_name"),
                    kwargs.get("inputs"),
                    kwargs.get("d365_org_url"),
                    kwargs.get("dry_run", False),
                )
            elif action == "generate_demo_data":
                return self._generate_demo_data(
                    kwargs.get("customer_name"),
                    kwargs.get("inputs"),
                    kwargs.get("dry_run", False),
                )
            elif action == "generate_demo_assets":
                return self._generate_demo_assets(
                    kwargs.get("customer_name"),
                    kwargs.get("inputs"),
                    kwargs.get("dry_run", False),
                )
            elif action == "orchestrate_full_setup":
                return self._orchestrate_full_setup(
                    kwargs.get("customer_name"),
                    kwargs.get("inputs"),
                    kwargs.get("d365_org_url"),
                    kwargs.get("steps_to_run"),
                    kwargs.get("dry_run", False),
                )
            elif action == "run_customer_provisioner":
                return self._run_customer_provisioner(
                    kwargs.get("customer_name"),
                    kwargs.get("ps_script"),
                    kwargs.get("ps_action"),
                    kwargs.get("dry_run", False),
                )
            elif action == "enrich_timelines":
                return self._run_customer_provisioner(
                    kwargs.get("customer_name"),
                    "Add-NavicoTimelineEnrichment.ps1",
                    None,
                    kwargs.get("dry_run", False),
                )
            elif action == "backfill_brand_logos":
                return self._run_customer_provisioner(
                    kwargs.get("customer_name"),
                    "Provision-NavicoExtended.ps1",
                    "BrandLogo",
                    kwargs.get("dry_run", False),
                )
            elif action == "demo_readiness_report":
                return self._demo_readiness_report(kwargs.get("customer_name"))
            elif action == "list_actions":
                return self._list_actions()
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logging.error(f"D365DemoPrep error: {e}")
            return f"Error: {e}"

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _list_customers(self) -> str:
        """List customers that have D365 configurations."""
        customers = []
        if CUSTOMERS_DIR.exists():
            for entry in sorted(CUSTOMERS_DIR.iterdir()):
                config_file = entry / "d365" / "config" / "environment.json"
                if entry.is_dir() and config_file.exists():
                    with open(config_file, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    org_url = cfg.get("environment", {}).get("url", "unknown")
                    brands = cfg.get("demo", {}).get("brands", [])
                    customers.append({
                        "name": entry.name,
                        "org_url": org_url,
                        "brands": brands,
                    })

        if not customers:
            return "No customers with D365 configs found."

        lines = ["**D365 Customers:**"]
        for c in customers:
            lines.append(
                f"- **{c['name']}**: {', '.join(c['brands'])} → {c['org_url']}"
            )
        return "\n".join(lines)

    def _get_config(self, customer_name: str) -> str:
        """Return the full D365 environment config for a customer."""
        if not customer_name:
            return "Error: customer_name is required."

        config_path = CUSTOMERS_DIR / customer_name / "d365" / "config" / "environment.json"
        if not config_path.exists():
            return f"No D365 config found for '{customer_name}'."

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return json.dumps(config, indent=2)

    def _validate_environment(self, customer_name: str) -> str:
        """Validate that the D365 org has expected demo data."""
        if not customer_name:
            return "Error: customer_name is required."

        config_path = CUSTOMERS_DIR / customer_name / "d365" / "config" / "environment.json"
        if not config_path.exists():
            return f"No D365 config found for '{customer_name}'."

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        org_url = config.get("environment", {}).get("url")
        if not org_url:
            return "Error: No org URL in config."

        # Import auth lazily to avoid import errors if az isn't available
        try:
            from d365.utils.dataverse_auth import get_dataverse_session
            session = get_dataverse_session(org_url)
        except Exception as e:
            return f"Authentication failed: {e}. Ensure `az login` has been run."

        data_dir = CUSTOMERS_DIR / customer_name / "d365" / "data"
        brands = config.get("demo", {}).get("brands", [])

        checks = []

        # Entity count checks
        entity_checks = [
            ("accounts", "Accounts", 3, None),
            ("contacts", "Contacts", 2, None),
            ("incidents", "Active Cases", 3, "statecode eq 0"),
            ("products", "Products", 1, None),
            ("queues", "Queues", 2, None),
            ("knowledgearticles", "KB Articles (published)", 1, "statecode eq 3"),
            ("slas", "SLAs", 1, None),
            ("entitlements", "Entitlements", 1, None),
        ]

        for entity_set, label, min_count, filter_expr in entity_checks:
            url = f"{entity_set}?$top=0&$count=true"
            if filter_expr:
                url = f"{entity_set}?$filter={filter_expr}&$top=0&$count=true"
            try:
                resp = session.get(url, headers={"Prefer": "odata.include-annotations=*"})
                resp.raise_for_status()
                data = resp.json()
                count = data.get("@odata.count", len(data.get("value", [])))
                passed = count >= min_count
                icon = "✓" if passed else "✗"
                checks.append(f"{icon} {label}: {count} (need ≥{min_count})")
            except Exception as e:
                checks.append(f"✗ {label}: Error — {e}")

        # Brand account checks
        for brand in brands:
            try:
                resp = session.get(f"accounts?$filter=contains(name, '{brand}')&$top=1")
                resp.raise_for_status()
                found = len(resp.json().get("value", [])) > 0
                icon = "✓" if found else "✗"
                checks.append(f"{icon} Brand account: {brand}")
            except Exception as e:
                checks.append(f"✗ Brand account '{brand}': Error — {e}")

        # Data export checks
        expected_files = [
            "account-ids.json", "product-ids.json",
            "queue-ids.json", "hero-record-ids.json",
        ]
        for filename in expected_files:
            exists = (data_dir / filename).exists()
            icon = "✓" if exists else "✗"
            checks.append(f"{icon} Data export: {filename}")

        passed_count = sum(1 for c in checks if c.startswith("✓"))
        total = len(checks)

        header = f"**D365 Validation — {customer_name}** ({org_url})\n"
        body = "\n".join(checks)
        footer = f"\n\n**Score: {passed_count}/{total}**"
        if passed_count == total:
            footer += " — Environment is demo-ready!"
        else:
            footer += f" — {total - passed_count} check(s) need attention."

        return header + body + footer

    def _provision_data(self, customer_name: str, dry_run: bool = False) -> str:
        """Generate core demo records in the D365 org."""
        if not customer_name:
            return "Error: customer_name is required."

        config_path = CUSTOMERS_DIR / customer_name / "d365" / "config" / "environment.json"
        if not config_path.exists():
            return f"No D365 config found for '{customer_name}'."

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        org_url = config.get("environment", {}).get("url")
        brands = config.get("demo", {}).get("brands", [])
        tiers = list(config.get("demo", {}).get("customerTiers", {}).keys())

        if dry_run:
            return (
                f"**Dry Run — {customer_name}**\n"
                f"Org: {org_url}\n"
                f"Brands: {', '.join(brands)}\n"
                f"Tiers: {', '.join(tiers)}\n"
                f"Would create: accounts, contacts, products (no changes made)"
            )

        try:
            from d365.utils.dataverse_auth import get_dataverse_session
            session = get_dataverse_session(org_url)
        except Exception as e:
            return f"Authentication failed: {e}. Ensure `az login` has been run."

        data_dir = CUSTOMERS_DIR / customer_name / "d365" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        results = []

        # Create manufacturer account
        mfg_name = " / ".join(brands)
        mfg_id = self._find_or_create(
            session, "accounts",
            f"name eq '{mfg_name}'",
            {"name": mfg_name, "accountcategorycode": 1},
        )
        account_ids = {"manufacturer": {"id": mfg_id, "name": mfg_name}}
        results.append(f"✓ Manufacturer: {mfg_name}")

        # Create distributor accounts
        account_ids["distributors"] = []
        distributors = [f"{brands[0]} National Supply", f"{brands[0]} Regional Distributors"]
        if len(brands) > 1:
            distributors.append(f"{brands[1]} Wholesale Partners")

        for dist_name in distributors:
            dist_id = self._find_or_create(
                session, "accounts",
                f"name eq '{dist_name}'",
                {"name": dist_name, "accountcategorycode": 2},
            )
            account_ids["distributors"].append({"id": dist_id, "name": dist_name})
            results.append(f"✓ Distributor: {dist_name}")

        # Save account IDs
        with open(data_dir / "account-ids.json", "w", encoding="utf-8") as f:
            json.dump(account_ids, f, indent=2)
        results.append("✓ Exported account-ids.json")

        return f"**Provisioned for {customer_name}:**\n" + "\n".join(results)

    def _run_powershell(self, customer_name: str, step_number: int) -> str:
        """Run a numbered PowerShell provisioning step."""
        if not customer_name:
            return "Error: customer_name is required."
        if not step_number or not (1 <= step_number <= 25):
            return "Error: step_number must be 1-25."

        setup_script = SCRIPTS_DIR / "00-Setup.ps1"
        if not setup_script.exists():
            return f"Error: {setup_script} not found."

        cmd = [
            "powershell", "-ExecutionPolicy", "Bypass", "-File",
            str(setup_script), "-Only", str(step_number),
            "-Customer", customer_name,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=str(D365_DIR)
            )
            output = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
            if result.returncode != 0:
                error = result.stderr[-500:] if result.stderr else "Unknown error"
                return f"Step {step_number:02d} failed (exit {result.returncode}):\n{error}\n\nOutput:\n{output}"
            return f"Step {step_number:02d} completed:\n{output}"
        except subprocess.TimeoutExpired:
            return f"Step {step_number:02d} timed out after 300s."
        except Exception as e:
            return f"Error running step {step_number:02d}: {e}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_or_create(session, entity_set: str, filter_expr: str, body: dict) -> str:
        """Idempotent record creation — find existing or create new."""
        resp = session.get(f"{entity_set}?$filter={filter_expr}&$top=1")
        resp.raise_for_status()
        records = resp.json().get("value", [])
        if records:
            return next(iter(records[0].values()))

        resp = session.post(entity_set, body, headers={"Prefer": "return=representation"})
        resp.raise_for_status()
        return next(iter(resp.json().values()))

    # ------------------------------------------------------------------
    # NEW: Input-driven config and data generation
    # ------------------------------------------------------------------

    def _generate_config_from_inputs(
        self,
        customer_name: str,
        inputs: Optional[Dict[str, Any]],
        d365_org_url: Optional[str],
        dry_run: bool = False
    ) -> str:
        """Generate environment.json and demo-data.json from input schema."""
        if not customer_name:
            return "Error: customer_name is required."
        if not inputs:
            return "Error: inputs object is required (follow d365_input_schema.json format)."

        # Extract from inputs
        customer_info = inputs.get("customer", {})
        discovery = inputs.get("discovery", {})
        demo_reqs = inputs.get("demo_requirements", {})
        data_sources = inputs.get("data_sources", {})
        metadata = inputs.get("metadata", {})

        # Validate required fields
        if not customer_info.get("name"):
            return "Error: inputs.customer.name is required."
        if not demo_reqs.get("tiers"):
            return "Error: inputs.demo_requirements.tiers is required."

        customer_dir = CUSTOMERS_DIR / customer_name / "d365"
        config_dir = customer_dir / "config"

        # Build environment.json
        tiers_dict = {}
        for tier in demo_reqs.get("tiers", []):
            tier_name = tier.get("name", "Standard")
            tiers_dict[tier_name] = {
                "priority": tier.get("priority", 3),
                "sla": {
                    "firstResponseMinutes": tier.get("sla_first_response_minutes", 240),
                    "resolutionMinutes": tier.get("sla_resolution_minutes", 1440)
                }
            }

        environment_config = {
            "environment": {
                "name": f"{customer_info.get('name')} Demo",
                "type": "demo",
                "url": d365_org_url or "https://YOUR_ORG.crm.dynamics.com",
                "region": customer_info.get("region", "NA")
            },
            "demo": {
                "brands": customer_info.get("brands", [customer_info.get("name")]),
                "industry": customer_info.get("industry", "other"),
                "customerTiers": tiers_dict,
                "agentCount": discovery.get("agent_count", 10),
                "hotWords": demo_reqs.get("hot_words", ["urgent", "emergency", "safety"]),
                "channels": discovery.get("channels", ["phone"]),
                "currentSystem": discovery.get("current_system", ""),
                "useCase": discovery.get("use_case", "case_management")
            },
            "dataSources": {
                "website": data_sources.get("website", ""),
                "productsPage": data_sources.get("products_page", ""),
                "supportPage": data_sources.get("support_page", "")
            },
            "metadata": {
                "createdBy": metadata.get("created_by", "D365DemoPrep"),
                "createdDate": metadata.get("created_date", datetime.now().strftime("%Y-%m-%d")),
                "demoDate": metadata.get("demo_date", ""),
                "projectId": metadata.get("project_id", ""),
                "notes": metadata.get("notes", "")
            }
        }

        if dry_run:
            return f"**Dry Run — Would create for {customer_name}:**\n```json\n{json.dumps(environment_config, indent=2)}\n```"

        # Create directories
        config_dir.mkdir(parents=True, exist_ok=True)
        (customer_dir / "data").mkdir(parents=True, exist_ok=True)
        (customer_dir / "demo-assets").mkdir(parents=True, exist_ok=True)

        # Write environment.json
        env_path = config_dir / "environment.json"
        with open(env_path, "w", encoding="utf-8") as f:
            json.dump(environment_config, f, indent=2)

        # Create stub demo-data.json (will be populated by generate_demo_data)
        demo_data_stub = {
            "serviceAccounts": {"accounts": []},
            "contacts": {"contacts": []},
            "products": {"products": []},
            "demoCases": {"cases": []},
            "kbArticles": {"articles": []},
            "_generated": False,
            "_note": "Run generate_demo_data to populate with GPT-4o generated content"
        }
        demo_data_path = config_dir / "demo-data.json"
        with open(demo_data_path, "w", encoding="utf-8") as f:
            json.dump(demo_data_stub, f, indent=2)

        # Save original inputs for reference
        inputs_path = config_dir / "inputs.json"
        with open(inputs_path, "w", encoding="utf-8") as f:
            json.dump(inputs, f, indent=2)

        return (
            f"**Config generated for {customer_name}:**\n"
            f"✓ Created: {env_path}\n"
            f"✓ Created: {demo_data_path} (stub — run generate_demo_data to populate)\n"
            f"✓ Saved inputs to: {inputs_path}\n\n"
            f"Next step: Run `generate_demo_data` action to populate demo-data.json with GPT-4o generated content."
        )

    def _generate_demo_data(
        self,
        customer_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> str:
        """Use GPT-4o to generate realistic demo data based on inputs."""
        if not customer_name:
            return "Error: customer_name is required."

        # Load inputs from file if not provided
        config_dir = CUSTOMERS_DIR / customer_name / "d365" / "config"
        if not inputs:
            inputs_path = config_dir / "inputs.json"
            if inputs_path.exists():
                with open(inputs_path, "r", encoding="utf-8") as f:
                    inputs = json.load(f)
            else:
                return f"Error: No inputs provided and no inputs.json found at {inputs_path}"

        # Import the data generator
        try:
            from d365.utils.d365_data_generator import D365DataGenerator
            generator = D365DataGenerator()
        except ImportError as e:
            return f"Error: Could not import D365DataGenerator. Ensure d365/utils/d365_data_generator.py exists. {e}"

        customer_info = inputs.get("customer", {})
        demo_reqs = inputs.get("demo_requirements", {})
        discovery = inputs.get("discovery", {})

        if dry_run:
            return (
                f"**Dry Run — Would generate for {customer_name}:**\n"
                f"- Industry: {customer_info.get('industry')}\n"
                f"- Brands: {customer_info.get('brands')}\n"
                f"- Tiers: {[t.get('name') for t in demo_reqs.get('tiers', [])]}\n"
                f"- Case types: {demo_reqs.get('case_types')}\n"
                f"- Account count: {demo_reqs.get('account_count', {})}\n"
                f"- Case count: {demo_reqs.get('case_count', 20)}\n"
                f"- KB article count: {demo_reqs.get('kb_article_count', 10)}"
            )

        # Generate data using GPT-4o
        try:
            demo_data = generator.generate_full_demo_data(
                customer_name=customer_info.get("name", customer_name),
                industry=customer_info.get("industry", "other"),
                brands=customer_info.get("brands", [customer_name]),
                region=customer_info.get("region", "NA"),
                tiers=[t.get("name") for t in demo_reqs.get("tiers", [{"name": "Standard"}])],
                case_types=demo_reqs.get("case_types", ["support", "inquiry", "complaint"]),
                hero_scenario=demo_reqs.get("hero_scenario"),
                hot_words=demo_reqs.get("hot_words", ["urgent", "emergency"]),
                account_count=demo_reqs.get("account_count", {"manufacturers": 1, "distributors": 5, "end_users": 10}),
                case_count=demo_reqs.get("case_count", 20),
                kb_article_count=demo_reqs.get("kb_article_count", 10),
                channels=discovery.get("channels", ["phone"]),
                pain_points=discovery.get("pain_points", [])
            )
        except Exception as e:
            logging.error(f"Data generation failed: {e}")
            return f"Error generating demo data: {e}"

        # Write demo-data.json
        config_dir.mkdir(parents=True, exist_ok=True)
        demo_data_path = config_dir / "demo-data.json"
        with open(demo_data_path, "w", encoding="utf-8") as f:
            json.dump(demo_data, f, indent=2)

        # Summary
        accounts = demo_data.get("serviceAccounts", {}).get("accounts", [])
        contacts = demo_data.get("contacts", {}).get("contacts", [])
        cases = demo_data.get("demoCases", {}).get("cases", [])
        kb_articles = demo_data.get("kbArticles", {}).get("articles", [])

        return (
            f"**Demo data generated for {customer_name}:**\n"
            f"✓ Accounts: {len(accounts)}\n"
            f"✓ Contacts: {len(contacts)}\n"
            f"✓ Cases: {len(cases)}\n"
            f"✓ KB Articles: {len(kb_articles)}\n"
            f"✓ Saved to: {demo_data_path}\n\n"
            f"Next step: Run PowerShell provisioning steps or use `orchestrate_full_setup`."
        )

    def _orchestrate_full_setup(
        self,
        customer_name: str,
        inputs: Optional[Dict[str, Any]],
        d365_org_url: Optional[str],
        steps_to_run: Optional[list] = None,
        dry_run: bool = False
    ) -> str:
        """End-to-end demo setup: config generation, data generation, and provisioning."""
        if not customer_name:
            return "Error: customer_name is required."
        if not inputs:
            return "Error: inputs object is required."
        if not d365_org_url:
            return "Error: d365_org_url is required for provisioning."

        results = []
        results.append(f"## D365 Demo Orchestration — {customer_name}\n")

        # Step 1: Generate config
        results.append("### Step 1: Generate Configuration")
        if dry_run:
            results.append("Would generate environment.json and demo-data.json stub")
        else:
            config_result = self._generate_config_from_inputs(customer_name, inputs, d365_org_url, False)
            results.append(config_result)

        # Step 2: Generate demo data with GPT-4o
        results.append("\n### Step 2: Generate Demo Data (GPT-4o)")
        if dry_run:
            results.append("Would generate realistic demo data using GPT-4o")
        else:
            data_result = self._generate_demo_data(customer_name, inputs, False)
            results.append(data_result)

        # Step 3: Run provisioning steps
        default_steps = steps_to_run or [1, 2, 7]  # Accounts, Contacts, Cases by default
        results.append(f"\n### Step 3: Provision D365 (Steps: {default_steps})")

        if dry_run:
            results.append(f"Would run PowerShell steps: {default_steps}")
        else:
            for step in default_steps:
                results.append(f"\n**Running step {step}...**")
                step_result = self._run_powershell(customer_name, step)
                results.append(step_result[:500])  # Truncate long outputs

        # Step 4: Generate demo assets (HTML execution guide, etc.)
        results.append("\n### Step 4: Generate Demo Assets")
        if dry_run:
            results.append("Would generate HTML demo execution guide and supporting assets")
        else:
            assets_result = self._generate_demo_assets(customer_name, inputs, False)
            results.append(assets_result)

        # Step 5: Validate
        results.append("\n### Step 5: Validate Environment")
        if dry_run:
            results.append("Would validate D365 org has expected demo data")
        else:
            validation = self._validate_environment(customer_name)
            results.append(validation)

        return "\n".join(results)

    def _generate_demo_assets(
        self,
        customer_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> str:
        """Generate HTML demo execution guide and supporting assets."""
        if not customer_name:
            return "Error: customer_name is required."

        config_dir = CUSTOMERS_DIR / customer_name / "d365" / "config"
        demo_assets_dir = CUSTOMERS_DIR / customer_name / "d365" / "demo-assets"

        # Load inputs from file if not provided
        if not inputs:
            inputs_path = config_dir / "inputs.json"
            if inputs_path.exists():
                with open(inputs_path, "r", encoding="utf-8") as f:
                    inputs = json.load(f)
            else:
                return f"Error: No inputs provided and no inputs.json found at {inputs_path}"

        # Load environment config
        env_path = config_dir / "environment.json"
        if not env_path.exists():
            return f"Error: No environment.json found at {env_path}. Run generate_config_from_inputs first."

        with open(env_path, "r", encoding="utf-8") as f:
            environment_config = json.load(f)

        # Load demo data
        demo_data_path = config_dir / "demo-data.json"
        if not demo_data_path.exists():
            return f"Error: No demo-data.json found at {demo_data_path}. Run generate_demo_data first."

        with open(demo_data_path, "r", encoding="utf-8") as f:
            demo_data = json.load(f)

        # Check if demo data is populated
        if not demo_data.get("_generated", False) and not demo_data.get("serviceAccounts", {}).get("accounts"):
            return "Error: demo-data.json appears empty. Run generate_demo_data first to populate it."

        if dry_run:
            return (
                f"**Dry Run — Would generate for {customer_name}:**\n"
                f"- Demo Execution Guide (HTML)\n"
                f"- Data Validation Report (HTML)\n"
                f"- Quick Reference Card (HTML)\n"
                f"- Output directory: {demo_assets_dir}"
            )

        # Import the asset generator
        try:
            from d365.utils.demo_asset_generator import DemoAssetGenerator
            generator = DemoAssetGenerator()
        except ImportError as e:
            return f"Error: Could not import DemoAssetGenerator. Ensure d365/utils/demo_asset_generator.py exists. {e}"

        # Generate all assets
        try:
            customer_info = inputs.get("customer", {})
            created_files = generator.generate_all_assets(
                customer_name=customer_info.get("name", customer_name),
                inputs=inputs,
                demo_data=demo_data,
                environment_config=environment_config,
                output_dir=demo_assets_dir
            )
        except Exception as e:
            logging.error(f"Demo asset generation failed: {e}")
            return f"Error generating demo assets: {e}"

        # Build result summary
        results = [f"**Demo assets generated for {customer_name}:**"]
        for asset_type, path in created_files.items():
            results.append(f"✓ {asset_type}: {path}")

        results.append(f"\n**Open the demo execution guide:**")
        results.append(f"File: {demo_assets_dir / 'demo-execution-guide.html'}")

        return "\n".join(results)

    # ------------------------------------------------------------------
    # NEW: Customer-specific provisioner + readiness report
    # ------------------------------------------------------------------

    def _run_customer_provisioner(
        self,
        customer_name: str,
        ps_script: str,
        ps_action: str = None,
        dry_run: bool = False,
    ) -> str:
        """Run a customer-specific PowerShell provisioner script directly."""
        if not customer_name:
            return "Error: customer_name is required."
        if not ps_script:
            return "Error: ps_script is required (e.g. 'Provision-NavicoDemo.ps1')."

        customer_d365_dir = CUSTOMERS_DIR / customer_name / "d365"
        script_path = customer_d365_dir / ps_script

        if not script_path.exists():
            script_path = customer_d365_dir / "scripts" / ps_script
            if not script_path.exists():
                available = [p.name for p in customer_d365_dir.glob("*.ps1")]
                return (
                    f"Script '{ps_script}' not found.\n"
                    f"Available in {customer_d365_dir}:\n" +
                    "\n".join(f"  - {n}" for n in sorted(available))
                )

        cmd = ["pwsh", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
        if ps_action:
            cmd += ["-Action", ps_action]

        if dry_run:
            cmd_str = " ".join(cmd)
            return f"**Dry Run** — Would execute:\n```\n{cmd_str}\n```"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(customer_d365_dir),
            )
            output = result.stdout
            if len(output) > 3000:
                output = "...(truncated)...\n" + output[-3000:]
            if result.returncode != 0:
                err = result.stderr[-1000:] if result.stderr else "No stderr"
                return f"Script failed (exit {result.returncode}):\n{err}\n\nOutput:\n{output}"
            return f"**{ps_script}** completed successfully:\n\n{output}"
        except subprocess.TimeoutExpired:
            return f"Script timed out after 600s: {ps_script}"
        except Exception as e:
            return f"Error running {ps_script}: {e}"

    def _demo_readiness_report(self, customer_name: str) -> str:
        """Generate a full demo readiness checklist based on known Navico/CS demo requirements."""
        if not customer_name:
            return "Error: customer_name is required."

        customer_d365_dir = CUSTOMERS_DIR / customer_name / "d365"
        config_dir = customer_d365_dir / "config"
        demo_assets_dir = customer_d365_dir / "demo-assets"

        checks = []

        # File-based checks
        file_checks = [
            (config_dir / "environment.json",  "environment.json config"),
            (config_dir / "demo-data.json",    "demo-data.json data"),
            (demo_assets_dir / f"{customer_name}_demo_unified.html", "Unified demo guide HTML"),
        ]
        for path, label in file_checks:
            exists = path.exists()
            checks.append(("FILE", label, exists, str(path) if not exists else ""))

        # Script checks
        script_checks = [
            f"Provision-{customer_name.capitalize()}Demo.ps1",
            f"Provision-{customer_name.capitalize()}HeroCases.ps1",
            f"Provision-{customer_name.capitalize()}Extended.ps1",
            f"Add-{customer_name.capitalize()}TimelineEnrichment.ps1",
        ]
        for script in script_checks:
            exists = (customer_d365_dir / script).exists()
            checks.append(("SCRIPT", script, exists, ""))

        # Build report
        lines = [f"## Demo Readiness Report — {customer_name}\n"]
        passed = sum(1 for _, _, ok, _ in checks if ok)
        total = len(checks)

        for kind, label, ok, note in checks:
            icon = "✅" if ok else "❌"
            line = f"{icon} [{kind}] {label}"
            if not ok and note:
                line += f"\n     → Missing: {note}"
            lines.append(line)

        lines.append(f"\n**{passed}/{total} checks passed**")
        if passed == total:
            lines.append("Environment is ready to demo!")
        else:
            lines.append(f"{total - passed} items need attention before the demo.")

        lines.append("\n### Quick Commands to Fix Missing Items")
        lines.append("```")
        lines.append(f"# Run full provisioning:")
        lines.append(f"D365DemoPrep action=run_customer_provisioner, customer_name={customer_name}, ps_script=Provision-{customer_name.capitalize()}Demo.ps1, ps_action=All")
        lines.append(f"# Enrich timelines:")
        lines.append(f"D365DemoPrep action=enrich_timelines, customer_name={customer_name}")
        lines.append(f"# Backfill brand logos:")
        lines.append(f"D365DemoPrep action=backfill_brand_logos, customer_name={customer_name}")
        lines.append("```")

        return "\n".join(lines)

    def _list_actions(self) -> str:
        """Return a formatted list of all available actions with descriptions."""
        actions = [
            ("list_customers",            "List all customers with D365 configs in this RAPP instance"),
            ("get_config",                "Return the full environment.json config for a customer"),
            ("validate_environment",      "Check the live D365 org has expected accounts/cases/KB articles"),
            ("provision_data",            "Create core demo records (accounts, contacts) via Dataverse API"),
            ("run_powershell",            "Run a numbered provisioning step (01-25) from d365/scripts/"),
            ("run_customer_provisioner",  "Run a customer-specific PS script (e.g. Provision-NavicoDemo.ps1)"),
            ("enrich_timelines",          "Seed rich email/note/call timeline history on hero cases"),
            ("backfill_brand_logos",      "Re-stamp brand logo URLs on all customer asset records"),
            ("generate_config_from_inputs","Create environment.json + demo-data.json stub from input schema"),
            ("generate_demo_data",        "Use GPT-4o to generate realistic demo data JSON"),
            ("generate_demo_assets",      "Generate HTML demo execution guide + supporting assets"),
            ("orchestrate_full_setup",    "End-to-end: config → data → provision → assets → validate"),
            ("demo_readiness_report",     "Checklist of file/script presence and D365 data readiness"),
            ("list_actions",              "Show this help list"),
        ]
        lines = ["## D365DemoPrep — Available Actions\n"]
        for name, desc in actions:
            lines.append(f"**{name}**\n  {desc}\n")
        lines.append("---\n")
        lines.append("**Example — set up Navico from scratch:**")
        lines.append("```")
        lines.append("D365DemoPrep action=run_customer_provisioner, customer_name=navico, ps_script=Provision-NavicoDemo.ps1, ps_action=All")
        lines.append("D365DemoPrep action=run_customer_provisioner, customer_name=navico, ps_script=Provision-NavicoHeroCases.ps1, ps_action=All")
        lines.append("D365DemoPrep action=run_customer_provisioner, customer_name=navico, ps_script=Provision-NavicoExtended.ps1, ps_action=All")
        lines.append("D365DemoPrep action=enrich_timelines, customer_name=navico")
        lines.append("D365DemoPrep action=backfill_brand_logos, customer_name=navico")
        lines.append("D365DemoPrep action=demo_readiness_report, customer_name=navico")
        lines.append("```")
        return "\n".join(lines)
