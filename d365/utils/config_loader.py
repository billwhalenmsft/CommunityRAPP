"""
D365 Config Loader for RAPP
============================
Loads customer D365 configuration from:
  customers/<name>/d365/config/environment.json

Also supports listing customers that have D365 configs.
"""

import json
import os
from pathlib import Path

# RAPP project root (parent of d365/)
RAPP_ROOT = Path(__file__).resolve().parent.parent.parent
CUSTOMERS_DIR = RAPP_ROOT / "customers"


def list_d365_customers() -> list[str]:
    """Return customer names that have a D365 config file."""
    customers = []
    if CUSTOMERS_DIR.exists():
        for entry in sorted(CUSTOMERS_DIR.iterdir()):
            config_file = entry / "d365" / "config" / "environment.json"
            if entry.is_dir() and config_file.exists():
                customers.append(entry.name)
    return customers


def load_customer_config(customer_name: str) -> dict:
    """Load environment.json for a customer's D365 configuration."""
    config_path = CUSTOMERS_DIR / customer_name / "d365" / "config" / "environment.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"No D365 config for customer '{customer_name}' at {config_path}"
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_customer_d365_dir(customer_name: str) -> Path:
    """Return the d365/ directory for a customer."""
    d365_dir = CUSTOMERS_DIR / customer_name / "d365"
    if not d365_dir.exists():
        raise FileNotFoundError(f"D365 directory not found: {d365_dir}")
    return d365_dir


def get_data_dir(customer_name: str) -> Path:
    """Return the data directory for a customer's D365 exports."""
    data_dir = CUSTOMERS_DIR / customer_name / "d365" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_demo_assets_dir(customer_name: str) -> Path:
    """Return the demo-assets directory for a customer."""
    assets_dir = CUSTOMERS_DIR / customer_name / "d365" / "demo-assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir
