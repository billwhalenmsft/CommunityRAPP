"""
RAPP Hatchery Agent — Bridge from Brainstem (T1) to CommunityRAPP (T2/T3).

This agent runs in the BRAINSTEM (rapp-installer), NOT in CommunityRAPP.
It is downloaded into the brainstem's agents/ folder via hatch.sh / hatch.ps1.
CommunityRAPP hosts this file for distribution only.

Both repos share the same BasicAgent base class interface:
  __init__(name, metadata) + perform(**kwargs)

Uses only Python stdlib + subprocess — no Azure SDK, no openai, no utils/.
See CONSTITUTION.md Article XIII for the governing rules.
"""

import json
import logging
import os
import platform
import re
import shutil
import subprocess
import time
import urllib.request

from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)

PROJECTS_DIR = os.path.expanduser("~/rapp-projects")
MANIFEST_PATH = os.path.join(PROJECTS_DIR, ".hatchery.json")
REPO_URL = "https://github.com/kody-w/CommunityRAPP.git"
BASE_PORT = 7072  # Brainstem uses 7071

BUSINESS_HTML_URL = "https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/business.html"

CONFIGURABLE_KEYS = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    "AZURE_OPENAI_API_VERSION",
    "ASSISTANT_NAME",
    "CHARACTERISTIC_DESCRIPTION",
    "USE_CLOUD_STORAGE",
    "USE_IDENTITY_BASED_STORAGE",
    "AzureWebJobsStorage",
]

SECRET_KEYS = {"AZURE_OPENAI_API_KEY", "AzureWebJobsStorage"}


class RAPPHatcheryAgent(BasicAgent):
    def __init__(self):
        self.name = "RAPPHatchery"
        self.metadata = {
            "name": self.name,
            "description": (
                "Hatches new CommunityRAPP cloud projects from the brainstem. "
                "Use when the user is ready to deploy to Azure or set up a cloud "
                "agent instance for a customer. "
                "Actions: hatch (create project), configure (set Azure settings), "
                "status (check projects), guide (next-step instructions)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["hatch", "configure", "status", "guide"],
                        "description": (
                            "Action to perform. 'hatch' creates a new project, "
                            "'configure' sets Azure settings, 'status' checks "
                            "existing projects, 'guide' shows the next step."
                        ),
                    },
                    "project_name": {
                        "type": "string",
                        "description": (
                            "Name for the project (lowercase, hyphens ok). "
                            "Used as the directory name under ~/rapp-projects/. "
                            "Required for hatch and configure."
                        ),
                    },
                    "setting_key": {
                        "type": "string",
                        "description": (
                            "Setting to configure (e.g. 'AZURE_OPENAI_ENDPOINT'). "
                            "Used with the configure action."
                        ),
                    },
                    "setting_value": {
                        "type": "string",
                        "description": (
                            "Value for the setting. Used with configure action."
                        ),
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get("action", "guide")
        project_name = kwargs.get("project_name", "")
        setting_key = kwargs.get("setting_key", "")
        setting_value = kwargs.get("setting_value", "")

        actions = {
            "hatch": lambda: self._hatch(project_name),
            "configure": lambda: self._configure(project_name, setting_key, setting_value),
            "status": self._status,
            "guide": lambda: self._guide(project_name),
        }

        handler = actions.get(action)
        if not handler:
            return f"Unknown action '{action}'. Use: hatch, configure, status, guide."

        try:
            return handler()
        except Exception as e:
            logger.error(f"RAPPHatchery error: {e}", exc_info=True)
            return f"Error: {e}"

    # ── Hatch ──────────────────────────────────────────────────────────

    def _hatch(self, project_name):
        if not project_name:
            return (
                "Please provide a project_name (e.g. 'contoso-bot'). "
                "This will be the directory name under ~/rapp-projects/."
            )

        # Validate name
        if not re.match(r'^[a-z0-9][a-z0-9-]*$', project_name):
            return (
                f"Invalid project name '{project_name}'. "
                "Use lowercase letters, numbers, and hyphens (e.g. 'contoso-bot')."
            )

        project_dir = os.path.join(PROJECTS_DIR, project_name)
        if os.path.exists(project_dir):
            return (
                f"Project '{project_name}' already exists at {project_dir}. "
                "Use 'status' to check it, or choose a different name."
            )

        # Check prerequisites
        if not shutil.which("git"):
            return "Git is required but not found. Install it from https://git-scm.com."

        python_cmd = self._find_python()
        if not python_cmd:
            return (
                "Python 3.11+ is required but not found. "
                "CommunityRAPP needs Python 3.11 (3.13+ breaks Azure Functions v4). "
                "Install from https://python.org."
            )

        # Clone
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        tmp_dir = os.path.join(PROJECTS_DIR, f".tmp-{project_name}-{int(time.time())}")

        try:
            logger.info(f"Cloning CommunityRAPP for project '{project_name}'")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, project_dir],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return f"Git clone failed: {result.stderr.strip()}"

        except Exception as e:
            # Clean up on failure
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir, ignore_errors=True)
            raise

        # Create venv
        venv_dir = os.path.join(project_dir, ".venv")
        result = subprocess.run(
            [python_cmd, "-m", "venv", venv_dir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return (
                f"Project cloned to {project_dir} but venv creation failed: "
                f"{result.stderr.strip()}\n"
                f"You can create it manually: {python_cmd} -m venv {venv_dir}"
            )

        # Install requirements
        pip_cmd = self._get_pip_path(venv_dir)
        req_file = os.path.join(project_dir, "requirements.txt")
        if os.path.isfile(req_file):
            result = subprocess.run(
                [pip_cmd, "install", "-r", req_file, "--quiet"],
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                logger.warning(f"pip install had issues: {result.stderr[:200]}")

        # Copy settings template
        template = os.path.join(project_dir, "local.settings.template.json")
        settings = os.path.join(project_dir, "local.settings.json")
        if os.path.isfile(template) and not os.path.isfile(settings):
            shutil.copy2(template, settings)

        # Remove the hatchery directory from the hatched project — it doesn't
        # belong inside a running CommunityRAPP instance
        hatchery_dir = os.path.join(project_dir, "hatchery")
        if os.path.isdir(hatchery_dir):
            shutil.rmtree(hatchery_dir, ignore_errors=True)

        # Assign port and generate start scripts
        port = self._assign_port(project_name)
        self._write_start_scripts(project_dir, port)

        # Deploy business mode UI on first hatch (UI mutation — T2 opt-in)
        self._ensure_business_html()

        # Update manifest
        manifest = self._read_manifest()
        manifest["projects"] = manifest.get("projects", {})
        manifest["projects"][project_name] = {
            "path": project_dir,
            "port": port,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": python_cmd,
        }
        self._write_manifest(manifest)

        biz_html = os.path.join(PROJECTS_DIR, "business.html")
        biz_hint = ""
        if os.path.isfile(biz_html):
            biz_hint = (
                f"\n\nBusiness Mode UI is now available at:\n"
                f"  {biz_html}\n"
                f"Open it in a browser to chat with the brainstem and your "
                f"projects side by side."
            )

        return (
            f"Project '{project_name}' hatched at {project_dir}\n"
            f"Port: {port} | Python: {python_cmd}\n\n"
            f"It's ready to run locally — no Azure account or API keys needed.\n"
            f"Start it with: cd {project_dir} && ./start.sh"
            f"{biz_hint}\n\n"
            f"Use action 'guide' for next steps."
        )

    # ── Configure ──────────────────────────────────────────────────────

    def _configure(self, project_name, key, value):
        if not project_name:
            return "Please provide project_name to configure."

        project_dir = os.path.join(PROJECTS_DIR, project_name)
        settings_path = os.path.join(project_dir, "local.settings.json")

        if not os.path.isdir(project_dir):
            return f"Project '{project_name}' not found. Use 'hatch' to create it first."

        if not os.path.isfile(settings_path):
            template = os.path.join(project_dir, "local.settings.template.json")
            if os.path.isfile(template):
                shutil.copy2(template, settings_path)
            else:
                return f"No settings file found at {settings_path}."

        # Read current settings
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        values = settings.get("Values", {})

        # If no key provided, show current config status
        if not key:
            lines = [f"Settings for '{project_name}':\n"]
            for k in CONFIGURABLE_KEYS:
                v = values.get(k, "")
                if k in SECRET_KEYS and v and not v.startswith("<"):
                    display = v[:4] + "****"
                elif v and v.startswith("<"):
                    display = "(not set)"
                elif v:
                    display = v
                else:
                    display = "(not set)"
                lines.append(f"  {k}: {display}")
            lines.append(
                "\nTo set a value, use action 'configure' with "
                "setting_key and setting_value."
            )
            return "\n".join(lines)

        # Validate key
        if key not in CONFIGURABLE_KEYS:
            return (
                f"'{key}' is not a configurable setting. "
                f"Valid keys: {', '.join(CONFIGURABLE_KEYS)}"
            )

        if not value:
            current = values.get(key, "(not set)")
            if key in SECRET_KEYS and current and not current.startswith("<"):
                current = current[:4] + "****"
            return f"Current value of {key}: {current}\nProvide setting_value to update it."

        # Write the setting
        values[key] = value
        settings["Values"] = values
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

        display = value[:4] + "****" if key in SECRET_KEYS else value
        return f"Set {key} = {display} for project '{project_name}'."

    # ── Status ─────────────────────────────────────────────────────────

    def _status(self):
        if not os.path.isdir(PROJECTS_DIR):
            return (
                "No projects found. Use action 'hatch' with a project_name "
                "to create your first CommunityRAPP project."
            )

        manifest = self._read_manifest()
        projects = manifest.get("projects", {})

        if not projects:
            # Check for directories without manifest entries
            dirs = [
                d for d in os.listdir(PROJECTS_DIR)
                if os.path.isdir(os.path.join(PROJECTS_DIR, d)) and not d.startswith(".")
            ]
            if not dirs:
                return "No projects found. Use 'hatch' to create one."
            return (
                f"Found {len(dirs)} project directory(ies) not in manifest: "
                f"{', '.join(dirs)}. These may have been created manually."
            )

        biz_html = os.path.join(PROJECTS_DIR, "business.html")
        biz_available = os.path.isfile(biz_html)

        lines = [f"RAPP Projects ({len(projects)}):\n"]
        for name, info in sorted(projects.items()):
            path = info.get("path", os.path.join(PROJECTS_DIR, name))
            port = info.get("port", "?")
            exists = os.path.isdir(path)
            has_venv = os.path.isdir(os.path.join(path, ".venv"))
            has_settings = os.path.isfile(os.path.join(path, "local.settings.json"))

            # Check if configured (no placeholder values)
            configured = False
            if has_settings:
                try:
                    with open(os.path.join(path, "local.settings.json"), "r") as f:
                        vals = json.load(f).get("Values", {})
                    configured = (
                        vals.get("AZURE_OPENAI_ENDPOINT", "").startswith("https://")
                        and not vals.get("AZURE_OPENAI_ENDPOINT", "").startswith("https://<")
                    )
                except Exception:
                    pass

            status_parts = []
            if not exists:
                status_parts.append("missing")
            else:
                if has_venv:
                    status_parts.append("venv ready")
                else:
                    status_parts.append("no venv")
                if configured:
                    status_parts.append("configured")
                else:
                    status_parts.append("needs config")

            status = " | ".join(status_parts)
            lines.append(f"  {name} (port {port}): {status}")

        if biz_available:
            lines.append(f"\nBusiness Mode: {biz_html}")

        return "\n".join(lines)

    # ── Guide ──────────────────────────────────────────────────────────

    def _guide(self, project_name):
        manifest = self._read_manifest()
        projects = manifest.get("projects", {})

        # No projects yet
        if not projects:
            return (
                "Ready to hatch your first cloud project?\n\n"
                "Tell me the project name (e.g. 'contoso-bot') and I'll set up "
                "a CommunityRAPP instance for it.\n\n"
                "Example: 'Hatch a project called contoso-bot'"
            )

        # If no project specified, use the most recent one
        if not project_name:
            project_name = max(
                projects.keys(),
                key=lambda k: projects[k].get("created_at", ""),
            )

        if project_name not in projects:
            return f"Project '{project_name}' not found. Use 'status' to see your projects."

        info = projects[project_name]
        path = info.get("path", os.path.join(PROJECTS_DIR, project_name))
        port = info.get("port", BASE_PORT)

        # Check what state the project is in
        if not os.path.isdir(path):
            return f"Project directory missing at {path}. Use 'hatch' to recreate it."

        if not os.path.isdir(os.path.join(path, ".venv")):
            python_cmd = info.get("python", "python3")
            return (
                f"Virtual environment missing for '{project_name}'.\n"
                f"Create it manually:\n"
                f"  {python_cmd} -m venv {path}/.venv\n"
                f"  {path}/.venv/bin/pip install -r {path}/requirements.txt"
            )

        # Check if configured
        settings_path = os.path.join(path, "local.settings.json")
        configured = False
        if os.path.isfile(settings_path):
            try:
                with open(settings_path, "r") as f:
                    vals = json.load(f).get("Values", {})
                configured = (
                    vals.get("AZURE_OPENAI_ENDPOINT", "").startswith("https://")
                    and not vals.get("AZURE_OPENAI_ENDPOINT", "").startswith("https://<")
                )
            except Exception:
                pass

        if not configured:
            is_windows = platform.system() == "Windows"
            start_script = "start.ps1" if is_windows else "start.sh"
            biz_html = os.path.join(PROJECTS_DIR, "business.html")
            biz_hint = ""
            if os.path.isfile(biz_html):
                biz_hint = (
                    f"\n\nTip: Open {biz_html} in your browser for "
                    f"Business Mode — chat with brainstem and projects side by side."
                )
            return (
                f"Project '{project_name}' is ready to run locally.\n\n"
                f"Start it:\n"
                f"  cd {path} && ./{start_script}\n\n"
                f"It runs on http://localhost:{port}/api/health with local file storage.\n"
                f"No Azure account needed — add agents, customize, test the endpoints."
                f"{biz_hint}\n\n"
                f"When you're ready to add AI responses, I'll need:\n"
                f"  1. AZURE_OPENAI_ENDPOINT — your Azure OpenAI resource URL\n"
                f"  2. AZURE_OPENAI_DEPLOYMENT_NAME — model deployment (e.g. 'gpt-4o')\n"
                f"  3. AZURE_OPENAI_API_KEY — your API key (or use 'az login' for Entra ID)\n\n"
                f"Just tell me when you're ready for that step."
            )

        # Configured — guide to local testing
        is_windows = platform.system() == "Windows"
        start_script = "start.ps1" if is_windows else "start.sh"
        start_path = os.path.join(path, start_script)

        if os.path.isfile(start_path):
            return (
                f"Project '{project_name}' is configured and ready to test locally.\n\n"
                f"Start it:\n"
                f"  cd {path} && ./{start_script}\n\n"
                f"It will run on http://localhost:{port}/api/health\n\n"
                f"Once it's working locally, tell me you're ready to deploy to Azure "
                f"and I'll walk you through it."
            )

        # Fallback: manual start instructions
        activate = (
            f"{path}\\.venv\\Scripts\\activate" if is_windows
            else f"source {path}/.venv/bin/activate"
        )
        return (
            f"Project '{project_name}' is configured. Start it locally:\n\n"
            f"  cd {path}\n"
            f"  {activate}\n"
            f"  func start --port {port}\n\n"
            f"Test: curl http://localhost:{port}/api/health\n\n"
            f"When it's working, tell me you're ready to deploy to Azure."
        )

    # ── Helpers ─────────────────────────────────────────────────────────

    def _find_python(self):
        """Find Python 3.11+ (3.13+ not recommended for Azure Functions)."""
        candidates = ["python3.11", "python3.12", "python3"]
        if platform.system() == "Windows":
            candidates = ["python3.11", "python3.12", "python3", "python"]

        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, "--version"], capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split()[-1]
                    major, minor = version.split(".")[:2]
                    if int(major) == 3 and int(minor) >= 11:
                        return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def _get_pip_path(self, venv_dir):
        """Get the pip executable path inside a venv."""
        if platform.system() == "Windows":
            return os.path.join(venv_dir, "Scripts", "pip.exe")
        return os.path.join(venv_dir, "bin", "pip")

    def _assign_port(self, project_name):
        """Assign a unique port for the project."""
        manifest = self._read_manifest()
        projects = manifest.get("projects", {})
        used_ports = {p.get("port", 0) for p in projects.values()}

        port = BASE_PORT
        while port in used_ports:
            port += 1
        return port

    def _write_start_scripts(self, project_dir, port):
        """Generate start.sh and start.ps1 for the hatched project."""
        # Bash
        bash_script = (
            "#!/usr/bin/env bash\n"
            f"# Start CommunityRAPP on port {port}\n"
            "cd \"$(dirname \"$0\")\"\n"
            "source .venv/bin/activate\n"
            f"func start --port {port}\n"
        )
        bash_path = os.path.join(project_dir, "start.sh")
        with open(bash_path, "w", encoding="utf-8") as f:
            f.write(bash_script)
        try:
            os.chmod(bash_path, 0o755)
        except OSError:
            pass

        # PowerShell
        ps_script = (
            f"# Start CommunityRAPP on port {port}\n"
            "$ErrorActionPreference = 'Stop'\n"
            "Set-Location $PSScriptRoot\n"
            ".venv\\Scripts\\Activate.ps1\n"
            f"func start --port {port}\n"
        )
        ps_path = os.path.join(project_dir, "start.ps1")
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(ps_script)

    def _ensure_business_html(self):
        """Download business.html to ~/rapp-projects/ on first hatch.

        This is the 'UI mutation' — business mode only appears once the user
        has opted into T2 by hatching a project. Before that, they only see
        the brainstem's index.html.
        """
        dest = os.path.join(PROJECTS_DIR, "business.html")
        if os.path.isfile(dest):
            return  # Already there

        # Fall back to downloading from GitHub
        try:
            urllib.request.urlretrieve(BUSINESS_HTML_URL, dest)
            logger.info(f"Downloaded business.html to {dest}")
        except Exception as e:
            logger.warning(f"Could not fetch business.html: {e}")

    def _read_manifest(self):
        if not os.path.isfile(MANIFEST_PATH):
            return {}
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write_manifest(self, data):
        os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
