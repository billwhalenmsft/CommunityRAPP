"""
D365 Client — Dataverse Web API access for CoE agents.

Uses service principal (App Registration) authentication.
Credentials loaded from environment variables — see d365_access/SETUP.md.

Usage:
    from customers.mfg_coe.d365_access.d365_client import D365Client

    client = D365Client()
    cases = client.get_cases(top=10)
    account = client.get_account_by_name("Navico")
"""

import json
import logging
import os
from typing import Any, Optional

import requests

log = logging.getLogger(__name__)


class D365ClientError(Exception):
    pass


class D365Client:
    """
    Thin wrapper around the Dataverse Web API.
    Handles token acquisition and common CRUD operations.
    """

    AUTHORITY_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    def __init__(
        self,
        environment_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.environment_url = (
            environment_url or os.environ.get("D365_MASTER_CE_MFG_URL", "")
        ).rstrip("/")
        self.tenant_id = tenant_id or os.environ.get("D365_TENANT_ID", "")
        self.client_id = client_id or os.environ.get("D365_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("D365_CLIENT_SECRET", "")
        self._token: Optional[str] = None

        if not all([self.environment_url, self.tenant_id, self.client_id, self.client_secret]):
            log.warning(
                "D365Client: Missing credentials. Set D365_MASTER_CE_MFG_URL, "
                "D365_TENANT_ID, D365_CLIENT_ID, D365_CLIENT_SECRET env vars."
            )

    # ── Authentication ────────────────────────────────────────────────────────

    def _get_token(self) -> str:
        """Acquire (or return cached) OAuth2 bearer token."""
        if self._token:
            return self._token

        url = self.AUTHORITY_URL.format(tenant_id=self.tenant_id)
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{self.environment_url}/.default",
        }
        resp = requests.post(url, data=payload, timeout=30)
        if resp.status_code != 200:
            raise D365ClientError(f"Token acquisition failed: {resp.status_code} {resp.text}")

        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "odata.include-annotations=OData.Community.Display.V1.FormattedValue",
        }

    # ── Generic CRUD ──────────────────────────────────────────────────────────

    def _get(self, entity: str, params: Optional[dict] = None) -> dict[str, Any]:
        url = f"{self.environment_url}/api/data/v9.2/{entity}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        if resp.status_code != 200:
            raise D365ClientError(f"GET {entity} failed: {resp.status_code} {resp.text}")
        return resp.json()

    def _post(self, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.environment_url}/api/data/v9.2/{entity}"
        resp = requests.post(url, headers=self._headers(), json=data, timeout=30)
        if resp.status_code not in (201, 204):
            raise D365ClientError(f"POST {entity} failed: {resp.status_code} {resp.text}")
        return {"id": resp.headers.get("OData-EntityId", ""), "status": "created"}

    def _patch(self, entity: str, record_id: str, data: dict[str, Any]) -> None:
        url = f"{self.environment_url}/api/data/v9.2/{entity}({record_id})"
        resp = requests.patch(url, headers=self._headers(), json=data, timeout=30)
        if resp.status_code not in (200, 204):
            raise D365ClientError(f"PATCH {entity} failed: {resp.status_code} {resp.text}")

    # ── Common entity helpers ─────────────────────────────────────────────────

    def get_accounts(self, top: int = 20, filter_expr: Optional[str] = None) -> list[dict]:
        params: dict[str, Any] = {
            "$select": "name,accountnumber,telephone1,emailaddress1,industrycode",
            "$top": top,
        }
        if filter_expr:
            params["$filter"] = filter_expr
        return self._get("accounts", params).get("value", [])

    def get_account_by_name(self, name: str) -> Optional[dict]:
        results = self.get_accounts(filter_expr=f"name eq '{name}'")
        return results[0] if results else None

    def get_cases(
        self,
        top: int = 20,
        account_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        params: dict[str, Any] = {
            "$select": "title,ticketnumber,statecode,statuscode,createdon,modifiedon",
            "$top": top,
            "$orderby": "createdon desc",
        }
        filters = []
        if account_name:
            account = self.get_account_by_name(account_name)
            if account:
                filters.append(f"_customerid_value eq {account['accountid']}")
        if status:
            status_map = {"active": 0, "resolved": 1, "cancelled": 2}
            code = status_map.get(status.lower())
            if code is not None:
                filters.append(f"statecode eq {code}")
        if filters:
            params["$filter"] = " and ".join(filters)
        return self._get("incidents", params).get("value", [])

    def create_case(
        self, title: str, account_name: str, description: str = "", priority: int = 2
    ) -> dict[str, Any]:
        account = self.get_account_by_name(account_name)
        if not account:
            raise D365ClientError(f"Account not found: {account_name}")

        data = {
            "title": title,
            "description": description,
            "prioritycode": priority,
            f"customerid_account@odata.bind": f"/accounts({account['accountid']})",
        }
        return self._post("incidents", data)

    def get_environment_info(self) -> dict[str, Any]:
        """Return basic info about the connected D365 environment."""
        try:
            orgs = self._get("organizations", {"$select": "name,uniquename,version"})
            return {
                "environment_url": self.environment_url,
                "organizations": orgs.get("value", []),
                "connected": True,
            }
        except D365ClientError as e:
            return {"connected": False, "error": str(e)}

    def is_configured(self) -> bool:
        """Return True if all required credentials are present."""
        return all([self.environment_url, self.tenant_id, self.client_id, self.client_secret])


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    client = D365Client()
    if not client.is_configured():
        print("D365Client: credentials not configured. See customers/mfg_coe/d365_access/SETUP.md")
    else:
        info = client.get_environment_info()
        print(json.dumps(info, indent=2))
