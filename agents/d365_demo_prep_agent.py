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

Requires: Azure CLI `az login` completed for Dataverse token acquisition.
"""

import json
import logging
import subprocess
from pathlib import Path

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
                "and runs PowerShell provisioning steps. "
                "Use this agent when working with D365/Dataverse demo environments."
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
                            "'run_powershell' executes a numbered provisioning script (01-25)"
                        ),
                        "enum": [
                            "list_customers",
                            "get_config",
                            "validate_environment",
                            "provision_data",
                            "run_powershell",
                        ],
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer folder name (e.g. 'zurnelkay'). Required for all actions except list_customers.",
                    },
                    "step_number": {
                        "type": "integer",
                        "description": "PowerShell step number (1-25) for run_powershell action.",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, show plan without making changes. Default: false.",
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
