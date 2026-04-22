from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.azure.compute import VM
from diagrams.azure.network import Firewall, NetworkInterfaces, NetworkSecurityGroupsClassic, PublicIpAddresses, Subnets, VirtualNetworks


OUTPUT_DIR = Path(__file__).parent / "output"


def build_diagram(outformat: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"azure-vm-nsg-firewall.{outformat}"

    with Diagram(
        name="Azure VM + NSG + Firewall",
        filename=str(filename.with_suffix("")),
        show=False,
        direction="LR",
        outformat=outformat,
    ):
        users = PublicIpAddresses("Internet")

        with Cluster("Hub VNet"):
            hub = VirtualNetworks("Hub VNet")
            azfw = Firewall("Azure Firewall")

            hub - azfw

        with Cluster("Spoke VNet"):
            spoke = VirtualNetworks("Spoke VNet")
            subnet = Subnets("App Subnet")
            nsg = NetworkSecurityGroupsClassic("NSG")
            nic = NetworkInterfaces("VM NIC")
            vm = VM("App VM")

            spoke - subnet - nsg - nic - vm

        users >> Edge(label="HTTPS 443") >> azfw >> Edge(label="Allow rule") >> nsg >> vm


if __name__ == "__main__":
    for fmt in ("png", "svg"):
        build_diagram(fmt)
    print(f"Generated files in: {OUTPUT_DIR}")