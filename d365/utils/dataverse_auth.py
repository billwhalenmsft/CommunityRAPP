"""
Dataverse Authentication for RAPP
==================================
Acquires Bearer token via Azure CLI and provides an authenticated session
for Dataverse Web API calls.
"""

import json
import logging
import subprocess
import requests


class DataverseSession:
    """Authenticated requests.Session wrapper for Dataverse Web API calls."""

    def __init__(self, org_url: str, api_version: str = "v9.2"):
        self.org_url = org_url.rstrip("/")
        self.base_url = f"{self.org_url}/api/data/{api_version}"
        self._session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Acquire token via `az account get-access-token`."""
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", self.org_url],
            capture_output=True,
            text=True,
            check=True,
        )
        token_data = json.loads(result.stdout)
        token = token_data["accessToken"]

        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
            }
        )

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint}"
        return self._session.get(url, **kwargs)

    def post(self, endpoint: str, payload: dict, **kwargs) -> requests.Response:
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint}"
        return self._session.post(url, json=payload, **kwargs)

    def patch(self, endpoint: str, payload: dict, **kwargs) -> requests.Response:
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint}"
        return self._session.patch(url, json=payload, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint}"
        return self._session.delete(url, **kwargs)


def get_dataverse_session(org_url: str, api_version: str = "v9.2") -> DataverseSession:
    """Create and return an authenticated DataverseSession."""
    return DataverseSession(org_url, api_version)
