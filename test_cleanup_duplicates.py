"""
Cleanup duplicate Plumbing Code Intelligence agents from Copilot Studio.
First deletes all dependent bot components, then deletes the bots themselves.
"""
import sys, os, time, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.copilot_studio_api import CopilotStudioClient

def main():
    client = CopilotStudioClient(
        environment_url="https://org6feab6b5.crm.dynamics.com",
        tenant_id="daa9e2eb-aaf1-46a8-a37e-3fd2e5821cb6",
        client_id="8562b2aa-8b34-4c3a-87d9-5ac05092858e",
        use_interactive_auth=True
    )
    print("Authenticating...")
    client.authenticate()
    print("Authenticated!\n")

    # List all agents with "PC" in the name
    agents = client.list_agents()
    pc_agents = [a for a in agents if a.get("name", "").startswith("PC ")]

    print(f"Found {len(pc_agents)} PC agents:")
    for a in pc_agents:
        print(f"  {a['name']:40s}  bot_id={a['botid']}")

    # The FIRST deployment created duplicate "PC PC ..." agents - those are the ones to remove.
    # Keep the SECOND deployment agents (the correct ones).
    # Identify duplicates: "PC PC" prefix or the older bot IDs from first run.
    first_run_ids = {
        "6936280f-2d0c-f111-8342-000d3a316172",  # PC PC Source Monitor
        "af55c33b-2d0c-f111-8342-000d3a316172",  # PC PC Technical Extractor
        "f6eaf455-2d0c-f111-8342-000d3a316172",  # PC PC Monthly Synth
    }

    to_delete = [a for a in pc_agents if a["botid"] in first_run_ids]
    to_keep = [a for a in pc_agents if a["botid"] not in first_run_ids]

    if not to_delete:
        print("\nNo duplicate agents found to clean up!")
        print("Remaining agents:")
        for a in to_keep:
            print(f"  {a['name']}  ({a['botid']})")
        return

    print(f"\nWill DELETE {len(to_delete)} duplicate agents:")
    for a in to_delete:
        print(f"  {a['name']}  ({a['botid']})")
    print(f"\nWill KEEP {len(to_keep)} agents:")
    for a in to_keep:
        print(f"  {a['name']}  ({a['botid']})")

    # Delete each duplicate: first remove ALL components, then the bot
    api_base = client.api_base_url
    headers = client.headers

    for agent in to_delete:
        bot_id = agent["botid"]
        name = agent["name"]
        print(f"\n--- Deleting: {name} ({bot_id}) ---")

        # Get ALL components that reference this bot (via parentbotid)
        try:
            resp = requests.get(
                f"{api_base}/botcomponents?$filter=_parentbotid_value eq '{bot_id}'",
                headers=headers
            )
            if resp.status_code == 200:
                components = resp.json().get("value", [])
                print(f"  Found {len(components)} total components (parentbotid)")

                for comp in components:
                    comp_id = comp.get("botcomponentid")
                    comp_name = comp.get("name", "unnamed")
                    comp_type = comp.get("componenttype", "?")

                    del_resp = requests.delete(
                        f"{api_base}/botcomponents({comp_id})",
                        headers=headers
                    )
                    status = "OK" if del_resp.status_code in [200, 204] else f"FAIL({del_resp.status_code})"
                    print(f"    [{comp_type}] {comp_name}: {status}")
            else:
                print(f"  Could not query components: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"  Error querying components: {e}")

        # Also get components via the relationship (belt and suspenders)
        try:
            resp = requests.get(
                f"{api_base}/bots({bot_id})/bot_botcomponent",
                headers=headers
            )
            if resp.status_code == 200:
                rel_components = resp.json().get("value", [])
                if rel_components:
                    print(f"  Found {len(rel_components)} relationship components still remaining")
                    for comp in rel_components:
                        comp_id = comp.get("botcomponentid")
                        # Disassociate then delete
                        requests.delete(
                            f"{api_base}/bots({bot_id})/bot_botcomponent({comp_id})/$ref",
                            headers=headers
                        )
                        del_resp = requests.delete(
                            f"{api_base}/botcomponents({comp_id})",
                            headers=headers
                        )
                        status = "OK" if del_resp.status_code in [200, 204] else f"FAIL({del_resp.status_code})"
                        print(f"    Rel component {comp.get('name','?')}: {status}")
        except Exception as e:
            pass

        time.sleep(2)

        # Now delete the bot itself
        try:
            del_resp = requests.delete(
                f"{api_base}/bots({bot_id})",
                headers=headers
            )
            if del_resp.status_code in [200, 204]:
                print(f"  Bot DELETED successfully!")
            else:
                print(f"  Bot delete failed ({del_resp.status_code}): {del_resp.text[:300]}")
        except Exception as e:
            print(f"  Bot delete error: {e}")

        time.sleep(2)

    # Final check
    print("\n" + "=" * 60)
    print("POST-CLEANUP CHECK")
    print("=" * 60)
    remaining = client.list_agents()
    pc_remaining = [a for a in remaining if "PC " in a.get("name", "")]
    print(f"Remaining PC agents: {len(pc_remaining)}")
    for a in pc_remaining:
        print(f"  {a['name']}  ({a['botid']})")

if __name__ == "__main__":
    main()
