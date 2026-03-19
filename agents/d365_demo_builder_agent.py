"""
D365 Demo Builder Agent
Purpose: Build D365 Customer Service demo environments from configuration.

This agent automates the creation of demo data in Dynamics 365 Customer Service:
- Generates customer configuration files (environment.json, demo-data.json)
- Provisions accounts, contacts, products, subjects, cases, KB articles
- Links cases to products, subjects, and KB articles
- Validates existing environment data
- Generates demo execution guides

Uses the shared DataverseHelper.psm1 module for all D365 Web API operations.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from agents.basic_agent import BasicAgent
from utils.storage_factory import get_storage_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class D365DemoBuilderAgent(BasicAgent):

    CUSTOMERS_DIR = "customers"

    def __init__(self):
        self.name = 'D365DemoBuilder'
        self.metadata = {
            "name": self.name,
            "description": (
                "Builds D365 Customer Service demo environments. Creates accounts, contacts, "
                "products, subjects, cases, KB articles, queues, and routing. Generates demo "
                "execution guides. Validates existing data. All operations are idempotent "
                "(safe to re-run). Use this agent when setting up a new customer demo or "
                "checking the status of an existing demo build."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The provisioning action to perform",
                        "enum": [
                            "validate_environment",
                            "list_customers",
                            "get_config",
                            "create_customer_config",
                            "provision_foundation",
                            "provision_cases",
                            "provision_kb_articles",
                            "link_cases",
                            "generate_demo_guide",
                            "full_build",
                            "get_build_status"
                        ]
                    },
                    "customer": {
                        "type": "string",
                        "description": "Customer folder name (e.g., 'otis', 'zurnelkay')"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry vertical for AI-generated content (e.g., 'elevator-service', 'plumbing-manufacturing')"
                    },
                    "channels": {
                        "type": "string",
                        "description": "Comma-separated channels to configure: phone,chat,email,portal"
                    },
                    "config_json": {
                        "type": "string",
                        "description": "JSON string with customer configuration overrides for create_customer_config"
                    },
                    "from_step": {
                        "type": "string",
                        "description": "For full_build: step number to resume from (e.g., '3' to skip accounts/contacts)"
                    }
                },
                "required": ["action", "customer"]
            }
        }
        super().__init__(self.name, self.metadata)
        self._storage = None

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage_manager()
        return self._storage

    def perform(self, **kwargs):
        action = kwargs.get('action', '')
        customer = kwargs.get('customer', '')

        if not action:
            return "Error: 'action' parameter is required."
        if not customer and action != 'list_customers':
            return "Error: 'customer' parameter is required."

        try:
            if action == 'list_customers':
                return self._list_customers()
            elif action == 'get_config':
                return self._get_config(customer)
            elif action == 'validate_environment':
                return self._validate_environment(customer)
            elif action == 'create_customer_config':
                return self._create_customer_config(customer, kwargs)
            elif action == 'get_build_status':
                return self._get_build_status(customer)
            elif action == 'provision_foundation':
                return self._provision_foundation(customer)
            elif action == 'provision_cases':
                return self._provision_cases(customer)
            elif action == 'provision_kb_articles':
                return self._provision_kb_articles(customer)
            elif action == 'link_cases':
                return self._link_cases(customer)
            elif action == 'generate_demo_guide':
                return self._generate_demo_guide(customer, kwargs)
            elif action == 'full_build':
                return self._full_build(customer, kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"D365DemoBuilder error: {e}")
            return f"Error in {action}: {str(e)}"

    # ── List Customers ──────────────────────────────────────────

    def _list_customers(self):
        """List all customers with D365 demo configurations."""
        repo_root = self._get_repo_root()
        customers_path = os.path.join(repo_root, self.CUSTOMERS_DIR)

        if not os.path.isdir(customers_path):
            return "No customers directory found."

        customers = []
        for name in sorted(os.listdir(customers_path)):
            customer_d365 = os.path.join(customers_path, name, "d365")
            if os.path.isdir(customer_d365):
                env_file = os.path.join(customer_d365, "config", "environment.json")
                status = "configured" if os.path.isfile(env_file) else "folder-only"
                info = {"name": name, "status": status}

                if status == "configured":
                    try:
                        with open(env_file, 'r', encoding='utf-8') as f:
                            env = json.load(f)
                        info["display_name"] = env.get("customer", {}).get("name", name)
                        info["industry"] = env.get("customer", {}).get("industry", "unknown")
                        info["channels"] = env.get("demo", {}).get("channels", [])
                    except Exception:
                        pass

                customers.append(info)

        if not customers:
            return "No customers with D365 configurations found."

        lines = ["## D365 Demo Customers\n"]
        for c in customers:
            display = c.get('display_name', c['name'])
            industry = c.get('industry', '')
            channels = ', '.join(c.get('channels', []))
            lines.append(f"- **{display}** (`{c['name']}`) — {industry} — Channels: {channels} — Status: {c['status']}")

        return '\n'.join(lines)

    # ── Get Config ──────────────────────────────────────────────

    def _get_config(self, customer):
        """Return a customer's environment.json."""
        env_path = self._get_config_path(customer, "environment.json")
        if not os.path.isfile(env_path):
            return f"No environment.json found for customer '{customer}'. Expected at: {env_path}"

        with open(env_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return f"## {customer} Configuration\n\n```json\n{json.dumps(config, indent=2)}\n```"

    # ── Validate Environment ────────────────────────────────────

    def _validate_environment(self, customer):
        """Check what D365 data exists for a customer and what's missing."""
        repo_root = self._get_repo_root()
        customer_d365 = os.path.join(repo_root, self.CUSTOMERS_DIR, customer, "d365")

        report = [f"## D365 Validation Report: {customer}\n"]

        # Check config files
        report.append("### Configuration Files")
        config_files = ["environment.json", "demo-data.json", "sla-definitions.json"]
        for cf in config_files:
            path = os.path.join(customer_d365, "config", cf)
            exists = "✅" if os.path.isfile(path) else "❌"
            report.append(f"  {exists} `config/{cf}`")

        # Check data tracking files
        report.append("\n### Data Tracking Files")
        data_files = [
            "account-ids.json", "otis-demo-ids.json", "product-ids.json",
            "queue-ids.json", "routing-ids.json", "classification-ids.json",
            "hero-record-ids.json", "knowledge-articles.json",
            "intent-agent-ids.json", "deployment-record.json"
        ]
        data_dir = os.path.join(customer_d365, "data")
        for df in data_files:
            path = os.path.join(data_dir, df)
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    count = len(data) if isinstance(data, list) else len(data.keys())
                    report.append(f"  ✅ `data/{df}` ({count} items)")
                except Exception:
                    report.append(f"  ⚠️ `data/{df}` (exists but couldn't parse)")
            else:
                report.append(f"  ❌ `data/{df}`")

        # Check scripts
        report.append("\n### Customer-Specific Scripts")
        scripts_dir = os.path.join(customer_d365, "scripts")
        if os.path.isdir(scripts_dir):
            for sf in sorted(os.listdir(scripts_dir)):
                if sf.endswith(('.ps1', '.py')):
                    report.append(f"  📜 `scripts/{sf}`")
        else:
            report.append("  ❌ No scripts directory")

        # Check web resources
        report.append("\n### Web Resources")
        wr_dir = os.path.join(customer_d365, "webresources")
        if os.path.isdir(wr_dir):
            for wf in sorted(os.listdir(wr_dir)):
                report.append(f"  📜 `webresources/{wf}`")
        else:
            report.append("  ❌ No webresources directory")

        # Check demo assets
        report.append("\n### Demo Assets")
        for assets_dir_name in ["demo-assets", "demo-assets-v2"]:
            assets_dir = os.path.join(customer_d365, assets_dir_name)
            if os.path.isdir(assets_dir):
                for af in sorted(os.listdir(assets_dir)):
                    report.append(f"  📄 `{assets_dir_name}/{af}`")

        # Load environment.json for layer analysis
        env_path = os.path.join(customer_d365, "config", "environment.json")
        if os.path.isfile(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env = json.load(f)
            channels = env.get("demo", {}).get("channels", [])

            report.append("\n### Layer Coverage Analysis")
            layers = [
                ("Accounts", True, "account-ids.json OR otis-demo-ids.json"),
                ("Contacts", True, "otis-demo-ids.json"),
                ("Products", True, "product-ids.json"),
                ("Subjects", True, "Check D365 directly"),
                ("Queues", "phone" in channels or "chat" in channels, "queue-ids.json"),
                ("SLAs", True, "sla-definitions.json"),
                ("Demo Cases", True, "hero-cases.json OR otis-demo-ids.json"),
                ("KB Articles", True, "knowledge-articles.json"),
                ("Entitlements", False, "Optional"),
                ("Routing", "phone" in channels or "chat" in channels, "routing-ids.json"),
                ("Classification", "phone" in channels or "chat" in channels, "classification-ids.json"),
                ("Web Resource (JS)", True, "webresources/ folder"),
                ("Portal Branding", "portal" in channels, "N/A"),
                ("Chat Widget", "chat" in channels, "N/A"),
                ("Customer Intent Agent", "phone" in channels or "chat" in channels, "intent-agent-ids.json"),
            ]

            for layer_name, required, tracking_file in layers:
                req_label = "Required" if required is True else ("Required for channels" if required else "Optional")
                report.append(f"  {'🔵' if required else '⚪'} **{layer_name}** — {req_label} — Track: {tracking_file}")

        return '\n'.join(report)

    # ── Get Build Status ────────────────────────────────────────

    def _get_build_status(self, customer):
        """Show build history and current state."""
        repo_root = self._get_repo_root()
        deployment_path = os.path.join(
            repo_root, self.CUSTOMERS_DIR, customer, "d365", "data", "deployment-record.json"
        )

        if not os.path.isfile(deployment_path):
            return f"No deployment record found for '{customer}'. Run `validate_environment` to check current state."

        with open(deployment_path, 'r', encoding='utf-8') as f:
            record = json.load(f)

        return f"## Build Status: {customer}\n\n```json\n{json.dumps(record, indent=2)}\n```"

    # ── Create Customer Config ──────────────────────────────────

    def _create_customer_config(self, customer, kwargs):
        """Generate environment.json and demo-data.json templates for a new customer."""
        industry = kwargs.get('industry', 'general')
        channels_str = kwargs.get('channels', 'phone')
        config_json = kwargs.get('config_json', '{}')
        channels = [c.strip() for c in channels_str.split(',')]

        try:
            overrides = json.loads(config_json) if config_json else {}
        except json.JSONDecodeError:
            return "Error: config_json is not valid JSON."

        # Create folder structure
        repo_root = self._get_repo_root()
        base = os.path.join(repo_root, self.CUSTOMERS_DIR, customer, "d365")
        for subdir in ["config", "data", "scripts", "webresources", "demo-assets", "copilot-studio"]:
            os.makedirs(os.path.join(base, subdir), exist_ok=True)

        # Generate environment.json template
        env_config = {
            "environment": {
                "name": f"{customer.title()} Demo",
                "url": "https://orgecbce8ef.crm.dynamics.com",
                "apiVersion": "v9.2"
            },
            "customer": {
                "name": overrides.get("customer_name", customer.title()),
                "project": overrides.get("project", f"{customer.title()} D365 Demo"),
                "industry": industry,
                "regions": overrides.get("regions", ["US"])
            },
            "demo": {
                "date": overrides.get("demo_date", "TBD"),
                "focusAreas": overrides.get("focus_areas", ["Customer Service"]),
                "channels": channels,
                "brands": overrides.get("brands", [customer.title()]),
                "customerTiers": {
                    "1": {"label": "Tier 1 - Premium", "priority": 9000, "color": "#e74c3c"},
                    "2": {"label": "Tier 2 - Standard", "priority": 7000, "color": "#e67e22"},
                    "3": {"label": "Tier 3 - Basic", "priority": 5000, "color": "#3498db"},
                    "4": {"label": "Tier 4 - Minimal", "priority": 2000, "color": "#95a5a6"}
                },
                "hotWords": overrides.get("hot_words", ["Emergency", "Urgent", "Safety"]),
                "hotWordPriorityBoost": 10000,
                "sla": {
                    "firstResponseMinutes": overrides.get("sla_first_response", 240),
                    "resolutionMinutes": overrides.get("sla_resolution", 480),
                    "businessHoursStart": "08:00",
                    "businessHoursEnd": "17:00",
                    "workDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                },
                "caseOrigins": {"phone": 1, "email": 2, "web": 3},
                "agentCount": overrides.get("agent_count", 50)
            }
        }

        env_path = os.path.join(base, "config", "environment.json")
        with open(env_path, 'w', encoding='utf-8') as f:
            json.dump(env_config, f, indent=2)

        # Create empty data tracking file
        data_path = os.path.join(base, "data", "deployment-record.json")
        deployment_record = {
            "customer": customer,
            "created": datetime.utcnow().isoformat() + "Z",
            "steps_completed": [],
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(deployment_record, f, indent=2)

        return (
            f"## Customer '{customer}' Configuration Created\n\n"
            f"- ✅ Folder structure: `customers/{customer}/d365/`\n"
            f"- ✅ Config: `config/environment.json`\n"
            f"- ✅ Tracking: `data/deployment-record.json`\n\n"
            f"**Next steps:**\n"
            f"1. Edit `environment.json` with customer-specific details\n"
            f"2. Create `demo-data.json` with accounts, contacts, products, cases\n"
            f"3. Run `provision_foundation` to create data in D365\n"
        )

    # ── Provision Foundation ────────────────────────────────────

    def _provision_foundation(self, customer):
        """Run the foundation provisioning script (accounts, contacts, products)."""
        return self._run_powershell_provisioning(customer, "All")

    def _provision_cases(self, customer):
        """Provision demo cases."""
        return self._run_powershell_provisioning(customer, "Cases")

    def _run_powershell_provisioning(self, customer, action):
        """Execute the customer's Provision script via PowerShell."""
        repo_root = self._get_repo_root()
        provision_script = os.path.join(
            repo_root, self.CUSTOMERS_DIR, customer, "d365", f"Provision-{customer.title()}Demo.ps1"
        )

        if not os.path.isfile(provision_script):
            # Try the generic Provision script pattern
            d365_dir = os.path.join(repo_root, self.CUSTOMERS_DIR, customer, "d365")
            ps1_files = [f for f in os.listdir(d365_dir) if f.startswith("Provision-") and f.endswith(".ps1")]
            if ps1_files:
                provision_script = os.path.join(d365_dir, ps1_files[0])
            else:
                return (
                    f"No provisioning script found for '{customer}'.\n"
                    f"Expected: `Provision-{customer.title()}Demo.ps1` in `customers/{customer}/d365/`\n"
                    f"Create one or use the generic pipeline scripts in `d365/scripts/`."
                )

        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", provision_script, "-Action", action]
        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=os.path.dirname(provision_script)
            )
            output = result.stdout
            if result.returncode != 0:
                output += f"\n\n⚠️ ERRORS:\n{result.stderr}"

            self._update_deployment_record(customer, f"provision_{action.lower()}")
            return f"## Provisioning: {action}\n\n```\n{output}\n```"
        except subprocess.TimeoutExpired:
            return f"Provisioning timed out after 5 minutes. Check D365 for partial data."
        except FileNotFoundError:
            return "PowerShell not found. Ensure PowerShell is installed and on PATH."

    # ── Provision KB Articles ───────────────────────────────────

    def _provision_kb_articles(self, customer):
        """Create knowledge articles for the customer. Returns guidance if no script exists."""
        repo_root = self._get_repo_root()
        kb_script = os.path.join(
            repo_root, self.CUSTOMERS_DIR, customer, "d365", "scripts",
            f"Create-{customer.title()}KBArticles.ps1"
        )

        if os.path.isfile(kb_script):
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", kb_script]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                self._update_deployment_record(customer, "provision_kb_articles")
                output = result.stdout
                if result.returncode != 0:
                    output += f"\n\n⚠️ ERRORS:\n{result.stderr}"
                return f"## KB Articles\n\n```\n{output}\n```"
            except subprocess.TimeoutExpired:
                return "KB article creation timed out."
        else:
            # Load config for context
            env_path = self._get_config_path(customer, "environment.json")
            incident_types = []
            if os.path.isfile(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    env = json.load(f)
                incident_types = env.get("demo", {}).get("incidentTypes", [])

            suggestions = []
            for it in incident_types:
                suggestions.append(f"- KB article: **{it.get('name', 'Unknown')}** — troubleshooting guide, SOP, escalation criteria")

            return (
                f"## KB Article Generation for {customer}\n\n"
                f"No KB article script found at `scripts/Create-{customer.title()}KBArticles.ps1`.\n\n"
                f"**Suggested KB articles based on incident types:**\n"
                + '\n'.join(suggestions) +
                f"\n\n**Options:**\n"
                f"1. Create articles manually in D365 → Knowledge Articles\n"
                f"2. Use AI to generate article content and create via Dataverse API\n"
                f"3. Adapt the Zurn KB script: `d365/scripts/08-KnowledgeArticles.ps1`"
            )

    # ── Link Cases ──────────────────────────────────────────────

    def _link_cases(self, customer):
        """Run case linking scripts (products, subjects, KB articles)."""
        repo_root = self._get_repo_root()
        scripts_dir = os.path.join(repo_root, "d365", "scripts")
        customer_scripts_dir = os.path.join(repo_root, self.CUSTOMERS_DIR, customer, "d365", "scripts")

        results = []

        # Look for Link-*Cases.ps1 and Link-*KBArticles.ps1
        link_patterns = [
            (f"Link-{customer.title()}Cases.ps1", "Case → Product/Subject linking"),
            (f"Link-{customer.title()}KBArticles.ps1", "KB Article → Case linking"),
        ]

        for script_name, description in link_patterns:
            # Check customer scripts dir first, then shared scripts dir
            script_path = os.path.join(customer_scripts_dir, script_name)
            if not os.path.isfile(script_path):
                script_path = os.path.join(scripts_dir, script_name)

            if os.path.isfile(script_path):
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    output = result.stdout[:2000]
                    status = "✅" if result.returncode == 0 else "⚠️"
                    results.append(f"{status} **{description}** (`{script_name}`)\n```\n{output}\n```")
                except subprocess.TimeoutExpired:
                    results.append(f"⏱️ **{description}** — timed out")
            else:
                results.append(f"❌ **{description}** — script not found: `{script_name}`")

        self._update_deployment_record(customer, "link_cases")
        return "## Case Linking Results\n\n" + "\n\n".join(results)

    # ── Generate Demo Guide ─────────────────────────────────────

    def _generate_demo_guide(self, customer, kwargs):
        """Generate or describe what a demo guide should contain."""
        env_path = self._get_config_path(customer, "environment.json")
        if not os.path.isfile(env_path):
            return f"Cannot generate demo guide without environment.json for '{customer}'."

        with open(env_path, 'r', encoding='utf-8') as f:
            env = json.load(f)

        customer_name = env.get("customer", {}).get("name", customer)
        channels = env.get("demo", {}).get("channels", [])
        focus_areas = env.get("demo", {}).get("focusAreas", [])
        incident_types = env.get("demo", {}).get("incidentTypes", [])
        tiers = env.get("demo", {}).get("customerTiers", {})

        guide_outline = [
            f"## Demo Execution Guide Outline: {customer_name}\n",
            f"**Channels**: {', '.join(channels)}",
            f"**Focus Areas**: {', '.join(focus_areas)}",
            "",
            "### Recommended Sections",
            "",
            "1. **Pre-Flight Checklist** — verify data, logins, channels active",
            "2. **Environment Overview** — what's configured, where to find things",
            "3. **Customer/Tier Story** — walk through tier-based service differentiation",
        ]

        for i, it in enumerate(incident_types[:5], start=4):
            guide_outline.append(f"{i}. **Scenario: {it.get('name', 'TBD')}** — priority: {it.get('priority', 'N/A')}, SLA: {it.get('slaMinutes', 'N/A')} min")

        guide_outline.extend([
            f"{len(incident_types) + 4}. **Knowledge Base Demo** — search, link to case, show on form",
            f"{len(incident_types) + 5}. **Wrap-Up & Q&A** — next steps, POC proposal",
            "",
            "### Existing Demo Assets",
        ])

        # Check for existing guides
        repo_root = self._get_repo_root()
        for assets_dir_name in ["demo-assets", "demo-assets-v2"]:
            assets_dir = os.path.join(repo_root, self.CUSTOMERS_DIR, customer, "d365", assets_dir_name)
            if os.path.isdir(assets_dir):
                for f in sorted(os.listdir(assets_dir)):
                    if os.path.isfile(os.path.join(assets_dir, f)):
                        guide_outline.append(f"  - `{assets_dir_name}/{f}`")

        guide_outline.append(
            "\n**To generate the full HTML guide**, provide this outline to the AI assistant "
            "and ask it to produce a styled HTML demo execution guide."
        )

        return '\n'.join(guide_outline)

    # ── Full Build ──────────────────────────────────────────────

    def _full_build(self, customer, kwargs):
        """Execute the full build pipeline for a customer."""
        from_step = int(kwargs.get('from_step', '1'))

        steps = [
            (1, "provision_foundation", "Foundation: Accounts, Contacts, Products"),
            (2, "provision_cases", "Demo Cases"),
            (3, "provision_kb_articles", "Knowledge Articles"),
            (4, "link_cases", "Link Cases to Products/Subjects/KB"),
            (5, "generate_demo_guide", "Demo Guide Outline"),
        ]

        results = [f"## Full Build: {customer}\n"]
        results.append(f"Starting from step {from_step}...\n")

        for step_num, action, description in steps:
            if step_num < from_step:
                results.append(f"⏭️ Step {step_num}: {description} (skipped)")
                continue

            results.append(f"\n### Step {step_num}: {description}\n")
            try:
                if action == 'provision_foundation':
                    result = self._provision_foundation(customer)
                elif action == 'provision_cases':
                    result = self._provision_cases(customer)
                elif action == 'provision_kb_articles':
                    result = self._provision_kb_articles(customer)
                elif action == 'link_cases':
                    result = self._link_cases(customer)
                elif action == 'generate_demo_guide':
                    result = self._generate_demo_guide(customer, kwargs)
                else:
                    result = f"Unknown step: {action}"

                results.append(result)
            except Exception as e:
                results.append(f"❌ Step {step_num} failed: {str(e)}")
                results.append("Stopping build. Fix the error and re-run with `from_step` parameter.")
                break

        return '\n'.join(results)

    # ── Helpers ─────────────────────────────────────────────────

    def _get_repo_root(self):
        """Find the repository root (where customers/ lives)."""
        # Try relative to this file
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(agent_dir)  # agents/ -> repo root
        if os.path.isdir(os.path.join(repo_root, "customers")):
            return repo_root

        # Fallback: current working directory
        cwd = os.getcwd()
        if os.path.isdir(os.path.join(cwd, "customers")):
            return cwd

        return repo_root

    def _get_config_path(self, customer, filename):
        """Get path to a customer's config file."""
        repo_root = self._get_repo_root()
        return os.path.join(repo_root, self.CUSTOMERS_DIR, customer, "d365", "config", filename)

    def _update_deployment_record(self, customer, step_name):
        """Update the deployment record with a completed step."""
        repo_root = self._get_repo_root()
        record_path = os.path.join(
            repo_root, self.CUSTOMERS_DIR, customer, "d365", "data", "deployment-record.json"
        )

        record = {"customer": customer, "steps_completed": [], "created": datetime.utcnow().isoformat() + "Z"}
        if os.path.isfile(record_path):
            try:
                with open(record_path, 'r', encoding='utf-8') as f:
                    record = json.load(f)
            except Exception:
                pass

        record["steps_completed"].append({
            "step": step_name,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        record["last_updated"] = datetime.utcnow().isoformat() + "Z"

        os.makedirs(os.path.dirname(record_path), exist_ok=True)
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2)
