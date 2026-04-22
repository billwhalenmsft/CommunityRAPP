#!/usr/bin/env python3
"""
Template for creating new Azure architecture diagrams.

Usage:
    1. Copy this file to diagrams/<your-architecture>.py
    2. Edit the diagram definition below
    3. Run: python3 diagrams/<your-architecture>.py
    4. Outputs land in diagrams/output/ as PNG and SVG

Available Azure modules (use `dir()` to discover node classes):
    diagrams.azure.compute    — VM, VMSS, VMLinux, VMWindows, ...
    diagrams.azure.network    — Firewall, FrontDoors, LoadBalancers, VirtualNetworks, ...
    diagrams.azure.database   — CosmosDb, SQLDatabases, ...
    diagrams.azure.security   — KeyVaults, Sentinel, ...
    diagrams.azure.integration — APIManagement, ServiceBus, ...
    diagrams.azure.web        — AppServices, ...
    diagrams.azure.storage    — StorageAccounts, BlobStorage, ...
    diagrams.azure.identity   — ActiveDirectory, ManagedIdentities, ...
"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.azure.compute import VM
from diagrams.azure.network import (
    Firewall,
    PublicIpAddresses,
    VirtualNetworks,
)

# ── Configuration ──────────────────────────────────────────
DIAGRAM_NAME = "My Azure Architecture"
DIAGRAM_SLUG = "my-azure-architecture"  # used for output filenames
OUTPUT_DIR = Path(__file__).parent / "output"


def build_diagram(outformat: str) -> None:
    """Build a single diagram in the specified format."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"{DIAGRAM_SLUG}.{outformat}"

    with Diagram(
        name=DIAGRAM_NAME,
        filename=str(filename.with_suffix("")),
        show=False,
        direction="LR",
        outformat=outformat,
    ):
        # ── Define your architecture here ──
        internet = PublicIpAddresses("Internet")

        with Cluster("VNet"):
            firewall = Firewall("Azure Firewall")
            vm = VM("App VM")

        internet >> Edge(label="HTTPS") >> firewall >> vm


if __name__ == "__main__":
    for fmt in ("png", "svg"):
        build_diagram(fmt)
    print(f"Generated files in: {OUTPUT_DIR}")
