# Azure Architecture Diagrams as Code

## Overview

Use the Python `diagrams` library to generate Azure architecture diagrams programmatically. Diagrams are defined as Python scripts, version-controlled alongside the presentation, and regenerated automatically during the build.

## Prerequisites

```bash
pip install diagrams>=0.25.1
sudo apt-get install -y graphviz
```

## Quick Start

```python
from pathlib import Path
from diagrams import Cluster, Diagram, Edge
from diagrams.azure.compute import VM, VMSS
from diagrams.azure.network import (
    Firewall, FrontDoors, LoadBalancers,
    PublicIpAddresses, VirtualNetworks,
    NetworkSecurityGroupsClassic, Subnets,
    NetworkInterfaces,
)

OUTPUT_DIR = Path(__file__).parent / "output"

def build_diagram(outformat: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"my-architecture.{outformat}"

    with Diagram(
        name="My Azure Architecture",
        filename=str(filename.with_suffix("")),
        show=False,
        direction="LR",      # Left-to-right flow
        outformat=outformat,
    ):
        internet = PublicIpAddresses("Internet")
        # ... define your architecture here

if __name__ == "__main__":
    for fmt in ("png", "svg"):
        build_diagram(fmt)
    print(f"Generated files in: {OUTPUT_DIR}")
```

## Available Azure Node Libraries

The `diagrams` library provides extensive Azure icon coverage. Key modules:

| Module | Example Nodes |
|--------|---------------|
| `diagrams.azure.compute` | `VM`, `VMSS`, `VMLinux`, `VMWindows` |
| `diagrams.azure.network` | `Firewall`, `FrontDoors`, `LoadBalancers`, `VirtualNetworks`, `Subnets`, `NetworkSecurityGroupsClassic`, `PublicIpAddresses`, `ApplicationGateway`, `DNSZones`, `PrivateEndpoint` |
| `diagrams.azure.database` | `CosmosDb`, `SQLDatabases`, `DatabaseForPostgresqlServers` |
| `diagrams.azure.security` | `KeyVaults`, `Sentinel` |
| `diagrams.azure.integration` | `APIManagement`, `ServiceBus`, `EventGridDomains` |
| `diagrams.azure.web` | `AppServices` |
| `diagrams.azure.storage` | `StorageAccounts`, `BlobStorage` |
| `diagrams.azure.identity` | `ActiveDirectory`, `ManagedIdentities` |
| `diagrams.azure.devops` | `Devops`, `Repos`, `Pipelines` |
| `diagrams.azure.ml` | `MachineLearningServiceWorkspaces` |

### Discovering Available Nodes

To list all node classes in a module:

```python
import importlib
mod = importlib.import_module("diagrams.azure.network")
print([n for n in dir(mod) if n[0].isupper()])
```

## Diagram Patterns

### Hub-and-Spoke Network

```python
with Diagram(...):
    internet = PublicIpAddresses("Internet")

    with Cluster("Hub VNet"):
        firewall = Firewall("Azure Firewall")

    with Cluster("Spoke VNet"):
        with Cluster("App Subnet"):
            nsg = NetworkSecurityGroupsClassic("NSG")
            vm = VM("App VM")
            nsg - vm

    internet >> Edge(label="HTTPS") >> firewall >> nsg >> vm
```

### Scaled App Hosting

```python
with Diagram(...):
    internet = PublicIpAddresses("Internet")
    front_door = FrontDoors("Azure Front Door")

    with Cluster("Hub VNet"):
        firewall = Firewall("Azure Firewall")

    with Cluster("App VNet"):
        lb = LoadBalancers("Load Balancer")

        with Cluster("Application Tier"):
            vmss = VMSS("Web Tier (VMSS)")
            vm = VM("Stateful VM")

        lb >> Edge(label="balance") >> vmss
        lb >> Edge(label="targeted") >> vm

    internet >> Edge(label="HTTPS") >> front_door >> firewall >> lb
```

## Key Syntax

| Construct | Meaning |
|-----------|---------|
| `A >> B` | Directed edge from A to B |
| `A - B` | Undirected edge |
| `Edge(label="text")` | Labeled edge |
| `Cluster("name")` | Visual grouping box |
| `direction="LR"` | Left-to-right layout (also: `TB`, `BT`, `RL`) |
| `outformat="png"` | Output format (`png`, `svg`, `pdf`, `dot`) |
| `show=False` | Don't auto-open the generated file |

## Output

- **PNG** — Best for embedding in PPTX and HTML slides
- **SVG** — Scales perfectly; use for high-resolution or zoomable contexts

Generated files land in `diagrams/output/`.

## Integration with Slides

Reference diagrams in Marp slides using Marp's image syntax:

```markdown
<!-- _class: light -->

## Architecture Overview

![w:1100 center](../diagrams/output/my-architecture.png)
```

Use the `light` class for diagram slides — dark backgrounds reduce diagram readability.

## Existing Examples

| File | Architecture |
|------|-------------|
| `diagrams/azure_vm_nsg_firewall.py` | VM + NSG + Azure Firewall (hub-spoke) |
| `diagrams/azure_app_hosting_reference.py` | VM + VMSS + LB + Firewall + Front Door |

## Regenerating Diagrams

```bash
# Regenerate all diagrams
for f in diagrams/*.py; do python3 "$f"; done

# Or a specific one
python3 diagrams/azure_app_hosting_reference.py
```
