"""
M365 Demo Seeder Agent — populates a Microsoft 365 tenant with demo data
to make RAPP-generated agents feel real for SE demos.

Inspired by D365JB/Cowork-DataLoader (J. Beach). This is the Python/RAPP
port of his PowerShell tool, exposed as a BasicAgent so RAPP can invoke
it as part of a customer demo prep flow alongside D365DemoPrep.

Tracking: kody-w/CommunityRAPP#59

Data shape: per-customer JSON files at
    customers/{customer}/m365_demo_data/
        emails.json
        calendar-events.json
        files.json
        chats.json
        sharepoint-files.json
        channel-messages.json
        skills.json
        files/                  # binaries to upload (.docx/.xlsx/.pptx)
        skills/{name}/SKILL.md  # Cowork skills

These schemas are intentionally compatible with Cowork-DataLoader's
data/ folder so files authored for one tool work in the other.

Authentication uses a chained credential (DefaultAzureCredential), so
locally `az login` is sufficient and in Azure the function app's managed
identity is used. Required Graph permissions are documented in each
seed_* method's docstring.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class M365DemoSeederAgent(BasicAgent):
    """
    Seed an M365 tenant with realistic demo data: emails (with backdated
    timestamps), calendar events, OneDrive files, Teams chats, Teams
    channel messages, SharePoint sites + libraries, and Cowork skills.

    Pairs with D365DemoPrep — D365 handles CRM/Dataverse seeding;
    this agent handles the surrounding M365 productivity context.
    """

    def __init__(self):
        self.name = "M365DemoSeeder"
        self.metadata = {
            "name": self.name,
            "description": (
                "Seed an M365 tenant with demo data (emails, calendar, "
                "OneDrive files, Teams chats/channels, SharePoint, Cowork "
                "skills) to make RAPP-generated agent demos feel real. "
                "Inspired by D365JB/Cowork-DataLoader."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "seed_all",
                            "seed_emails",
                            "seed_calendar",
                            "seed_files",
                            "seed_chats",
                            "seed_channels",
                            "seed_sharepoint",
                            "seed_cowork_skills",
                            "reset",
                            "list_data",
                            "validate_config",
                        ],
                        "description": "What to seed (or reset)."
                    },
                    "customer": {
                        "type": "string",
                        "description": (
                            "Customer slug under customers/{customer}/m365_demo_data/. "
                            "If omitted, uses the default 'demo' folder."
                        ),
                    },
                    "data_dir": {
                        "type": "string",
                        "description": "Override the data directory path entirely.",
                    },
                    "week_start": {
                        "type": "string",
                        "description": (
                            "Monday of the demo week as YYYY-MM-DD. "
                            "Used to anchor relative dayOffset/time fields."
                        ),
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, preview what would happen without calling Graph.",
                        "default": True,
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

        self.base_path = Path(__file__).resolve().parent.parent

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "list_data")
        handlers = {
            "seed_all": self._seed_all,
            "seed_emails": self._seed_emails,
            "seed_calendar": self._seed_calendar,
            "seed_files": self._seed_files,
            "seed_chats": self._seed_chats,
            "seed_channels": self._seed_channels,
            "seed_sharepoint": self._seed_sharepoint,
            "seed_cowork_skills": self._seed_cowork_skills,
            "reset": self._reset,
            "list_data": self._list_data,
            "validate_config": self._validate_config,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({
                "status": "error",
                "error": f"Unknown action: {action}",
                "available": sorted(handlers.keys()),
            })
        try:
            return handler(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.exception("M365DemoSeeder.%s failed", action)
            return json.dumps({"status": "error", "error": str(exc)})

    # ------------------------------------------------------------------
    # Data discovery
    # ------------------------------------------------------------------

    def _resolve_data_dir(self, **kwargs) -> Path:
        if kwargs.get("data_dir"):
            return Path(kwargs["data_dir"])
        customer = kwargs.get("customer") or "demo"
        return self.base_path / "customers" / customer / "m365_demo_data"

    def _load_json(self, path: Path) -> Any:
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _list_data(self, **kwargs) -> str:
        data_dir = self._resolve_data_dir(**kwargs)
        if not data_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error": f"Data directory not found: {data_dir}",
                "hint": (
                    "Create customers/{name}/m365_demo_data/ and drop in JSON "
                    "files matching the Cowork-DataLoader schemas."
                ),
            })

        inventory: Dict[str, Any] = {"data_dir": str(data_dir), "files": {}}
        for name in [
            "emails.json", "calendar-events.json", "files.json",
            "chats.json", "channel-messages.json", "sharepoint-files.json",
            "skills.json",
        ]:
            data = self._load_json(data_dir / name)
            if data is not None:
                inventory["files"][name] = (
                    {"count": len(data)} if isinstance(data, list) else {"present": True}
                )
        return json.dumps({"status": "success", "inventory": inventory}, indent=2)

    def _validate_config(self, **kwargs) -> str:
        data_dir = self._resolve_data_dir(**kwargs)
        problems: List[str] = []
        if not data_dir.is_dir():
            problems.append(f"Missing directory: {data_dir}")
        for required in ("emails.json", "files.json"):
            if not (data_dir / required).is_file():
                problems.append(f"Missing recommended file: {required}")
        if not kwargs.get("week_start"):
            problems.append(
                "week_start not provided — calendar/email backdating will use today as anchor"
            )
        return json.dumps({
            "status": "success" if not problems else "warning",
            "problems": problems,
            "data_dir": str(data_dir),
        }, indent=2)

    # ------------------------------------------------------------------
    # Seeders — currently dry-run/manifest only.
    #
    # The Graph API calls are intentionally NOT inlined yet: the goal of
    # this first cut is to (a) prove the BasicAgent shape and (b) emit a
    # plan that an SE can review before we burn Graph quota. Live mode
    # will be wired in a follow-up PR once kody-w confirms direction
    # (see tracking issue kody-w/CommunityRAPP#59).
    # ------------------------------------------------------------------

    def _plan(self, action: str, items: List[Dict], extra: Optional[Dict] = None) -> str:
        return json.dumps({
            "status": "planned",
            "action": action,
            "would_create": len(items),
            "sample": items[:3],
            "note": (
                "Live Graph calls are gated. Set dry_run=False AND wire "
                "credentials in a follow-up PR. See kody-w/CommunityRAPP#59."
            ),
            **(extra or {}),
        }, indent=2)

    def _seed_emails(self, **kwargs) -> str:
        data = self._load_json(self._resolve_data_dir(**kwargs) / "emails.json") or []
        # Live impl would: AppOnly Graph, POST /users/{addr}/messages with
        # internetMessageHeaders + receivedDateTime (Mail.ReadWrite App perm).
        return self._plan("seed_emails", data, {
            "graph_perms": ["Mail.Send", "Mail.ReadWrite"],
            "auth": "AppOnly (client credentials)",
            "trick": "Backdating uses Mail.ReadWrite to set receivedDateTime",
        })

    def _seed_calendar(self, **kwargs) -> str:
        data = self._load_json(self._resolve_data_dir(**kwargs) / "calendar-events.json") or []
        return self._plan("seed_calendar", data, {
            "graph_perms": ["Calendars.ReadWrite"],
            "auth": "Delegated",
            "idempotency": "PATCH existing events with matching subject",
        })

    def _seed_files(self, **kwargs) -> str:
        data = self._load_json(self._resolve_data_dir(**kwargs) / "files.json") or []
        return self._plan("seed_files", data, {
            "graph_perms": ["Files.ReadWrite.All"],
            "auth": "Delegated",
            "binary_handling": "PUT to /drive/root:/{path}:/content with bytes",
        })

    def _seed_chats(self, **kwargs) -> str:
        data = self._load_json(self._resolve_data_dir(**kwargs) / "chats.json") or []
        return self._plan("seed_chats", data, {
            "graph_perms": ["Chat.Create", "Chat.ReadWrite.All", "Teamwork.Migrate.All"],
            "auth": "AppOnly",
        })

    def _seed_channels(self, **kwargs) -> str:
        data = self._load_json(self._resolve_data_dir(**kwargs) / "channel-messages.json") or []
        return self._plan("seed_channels", data, {
            "graph_perms": ["Group.ReadWrite.All", "Channel.Create", "ChannelMessage.Send"],
            "auth": "Delegated",
        })

    def _seed_sharepoint(self, **kwargs) -> str:
        data = self._load_json(self._resolve_data_dir(**kwargs) / "sharepoint-files.json") or []
        return self._plan("seed_sharepoint", data, {
            "graph_perms": ["Sites.ReadWrite.All", "Group.ReadWrite.All"],
            "auth": "Delegated",
        })

    def _seed_cowork_skills(self, **kwargs) -> str:
        """Deploy SKILL.md files to OneDrive at /Documents/Cowork/skills/{slug}/.

        This is the bridge between the AgentTranspiler's `cowork_skill`
        target and a live tenant: the transpiler emits SKILL.md, and this
        seeder uploads it via Graph.
        """
        data = self._load_json(self._resolve_data_dir(**kwargs) / "skills.json") or []
        return self._plan("seed_cowork_skills", data, {
            "graph_perms": ["Files.ReadWrite.All"],
            "auth": "Delegated",
            "remote_path": "Documents/Cowork/skills/{slug}/SKILL.md",
            "auto_discovery": "M365 Copilot Cowork picks up new skills at conversation start",
        })

    def _seed_all(self, **kwargs) -> str:
        results = {
            "emails": json.loads(self._seed_emails(**kwargs)),
            "calendar": json.loads(self._seed_calendar(**kwargs)),
            "files": json.loads(self._seed_files(**kwargs)),
            "chats": json.loads(self._seed_chats(**kwargs)),
            "channels": json.loads(self._seed_channels(**kwargs)),
            "sharepoint": json.loads(self._seed_sharepoint(**kwargs)),
            "cowork_skills": json.loads(self._seed_cowork_skills(**kwargs)),
        }
        return json.dumps({"status": "planned", "results": results}, indent=2)

    def _reset(self, **kwargs) -> str:
        return json.dumps({
            "status": "planned",
            "note": (
                "Reset will delete demo emails (by subject), calendar events "
                "(by subject), files (by path), and SharePoint sites. Teams "
                "chats cannot be deleted programmatically (Graph API limit)."
            ),
        }, indent=2)
