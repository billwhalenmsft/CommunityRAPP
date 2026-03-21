"""
Deploy any RAPP-transpiled agent to Copilot Studio.

Generic deployment script that takes customer name, agent name, and instructions
file path, then handles the full create → provision → publish pipeline.

Usage:
  python scripts/deploy_to_copilot_studio.py --name "Agent Name" --instructions path/to/instructions.md
  python scripts/deploy_to_copilot_studio.py --name "Agent Name" --instructions path/to/instructions.md --customer "Contoso" --description "My agent"
  python scripts/deploy_to_copilot_studio.py --name "Agent Name" --instructions path/to/instructions.md --config my_config.json
  python scripts/deploy_to_copilot_studio.py --name "Agent Name" --instructions path/to/instructions.md --solution  # Package as solution
  python scripts/deploy_to_copilot_studio.py --delete "Agent Name"  # Delete existing agent

Environment config:
  Reads copilot_studio_deployment_config.json by default:
    { "environment_url": "https://orgXXX.crm.dynamics.com",
      "tenant_id": "...", "client_id": "..." }
"""
import sys
import os
import json
import time
import argparse
import uuid
import requests as req

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.copilot_studio_api import CopilotStudioClient


def load_config(config_path: str) -> dict:
    """Load deployment configuration."""
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found: {config_path}")
        print("Create copilot_studio_deployment_config.json with:")
        print('  { "environment_url": "https://orgXXX.crm.dynamics.com",')
        print('    "tenant_id": "...", "client_id": "..." }')
        sys.exit(1)
    with open(config_path, 'r') as f:
        return json.load(f)


def authenticate(config: dict) -> CopilotStudioClient:
    """Authenticate to Copilot Studio via Dataverse."""
    client = CopilotStudioClient(
        environment_url=config['environment_url'],
        tenant_id=config['tenant_id'],
        client_id=config['client_id'],
        use_interactive_auth=True
    )
    client.authenticate()
    return client


def delete_existing_agent(client: CopilotStudioClient, name: str):
    """Find and delete an existing agent by name, including all components."""
    existing = client.list_agents(filter_query=f"name eq '{name}'")
    if not existing:
        print(f"  No existing agent named '{name}' found")
        return

    for ex in existing:
        ex_id = ex.get('botid')
        print(f"  Deleting: {ex_id} ({ex.get('name')})")

        # Delete components first (required due to dependency constraint)
        resp = req.get(
            f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {ex_id}&$select=botcomponentid,name",
            headers=client.headers
        )
        if resp.status_code == 200:
            comps = resp.json().get('value', [])
            for comp in comps:
                cid = comp.get('botcomponentid')
                try:
                    req.delete(f"{client.api_base_url}/botcomponents({cid})", headers=client.headers)
                except Exception:
                    pass
            print(f"    Removed {len(comps)} components")

        try:
            client.delete_agent(ex_id)
            print(f"    Agent deleted")
        except Exception as e:
            print(f"    Warning: {e}")

    time.sleep(2)


def deploy_agent(
    client: CopilotStudioClient,
    name: str,
    instructions: str,
    description: str = "",
    customer: str = "",
    replace: bool = True,
    solution_name: str = None
) -> dict:
    """
    Deploy an agent to Copilot Studio.

    Steps:
    1. Delete existing agent with same name (if replace=True)
    2. Create bot entity with AI configuration
    3. Create GPT component (type 15) with instructions
    4. Create instructions component (type 10)
    5. Configure generative AI settings
    6. Provision (auto-creates 15 system topics)
    7. Publish

    Returns dict with deployment details.
    """
    full_desc = description
    if customer and customer not in description:
        full_desc = f"[{customer}] {description}" if description else f"[{customer}] {name}"

    # Step 1: Clean up existing
    if replace:
        print("\n[1/6] Checking for existing agent...")
        delete_existing_agent(client, name)
    else:
        print("\n[1/6] Skipping cleanup (replace=False)")

    # Step 2: Create bot entity with GPT component
    print("\n[2/6] Creating agent...")
    bot_id = client.create_agent(
        name=name,
        description=full_desc,
        instructions=instructions,
        language="en-us"
    )
    print(f"  Agent ID: {bot_id}")

    # Get schema name
    bot = client.get_agent(bot_id)
    bot_schema = bot.get('schemaname', '')
    print(f"  Schema: {bot_schema}")

    # Step 3: Create instructions component (type 10 — shown in CS Overview)
    print("\n[3/6] Creating instructions component (type 10)...")
    try:
        instr_id = client.create_instructions_component(
            bot_id=bot_id,
            name=name,
            instructions=instructions,
            description=full_desc,
            bot_schema_name=bot_schema
        )
        print(f"  Component ID: {instr_id}")
    except Exception as e:
        print(f"  Warning: {e}")

    # Step 4: Configure generative AI
    print("\n[4/6] Configuring generative AI settings...")
    client.update_agent_configuration(
        bot_id=bot_id,
        enable_generative_ai=True,
        enable_web_browsing=False,
        enable_semantic_search=True
    )
    print("  Generative orchestration enabled")

    # Step 5: Provision (this auto-creates all 15 system topics)
    print("\n[5/6] Provisioning agent...")
    time.sleep(3)
    try:
        prov = client.provision_agent(bot_id)
        print(f"  Provisioned: {prov}")
        time.sleep(5)
    except Exception as e:
        print(f"  Warning: {e}")

    # Step 6: Publish
    print("\n[6/6] Publishing agent...")
    try:
        pub = client.publish_agent(bot_id)
        print(f"  Published: {pub}")
    except Exception as e:
        print(f"  Warning: {e}")
        print("  You can publish manually from Copilot Studio UI")

    # Verify
    print("\n" + "-" * 50)
    print("VERIFYING COMPONENTS...")
    resp = req.get(
        f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {bot_id}&$select=name,componenttype",
        headers=client.headers
    )
    type_counts = {}
    if resp.status_code == 200:
        comps = resp.json().get('value', [])
        for c in comps:
            t = c.get('componenttype')
            type_counts[t] = type_counts.get(t, 0) + 1
        type_names = {9: 'topics', 10: 'translations', 15: 'GPT'}
        print(f"  Total: {len(comps)} components")
        for t, count in sorted(type_counts.items()):
            print(f"    Type {t} ({type_names.get(t, 'other')}): {count}")

    # Check for GPT component specifically
    has_gpt = type_counts.get(15, 0) > 0
    if not has_gpt:
        print("\n  *** WARNING: GPT component (type 15) missing!")
        print("  *** Attempting to create GPT component with unique schema...")
        try:
            suffix = uuid.uuid4().hex[:8]
            gpt_yaml = f"""kind: GptComponentMetadata
instructions: |-
{chr(10).join('  ' + line for line in instructions.split(chr(10)))}
responseInstructions:
gptCapabilities:
  webBrowsing: false
  codeInterpreter: false
aISettings:
  model:
    kind: CurrentModels
displayName: {name}"""

            comp_data = {
                "name": name,
                "schemaname": f"{bot_schema}.gpt.{suffix}",
                "componenttype": 15,
                "data": gpt_yaml,
                "parentbotid@odata.bind": f"/bots({bot_id})",
                "statecode": 0,
                "statuscode": 1
            }
            gpt_resp = req.post(
                f"{client.api_base_url}/botcomponents",
                headers=client.headers,
                json=comp_data
            )
            if gpt_resp.status_code in [200, 201, 204]:
                # Extract ID and associate
                if gpt_resp.text:
                    gpt_id = gpt_resp.json().get("botcomponentid")
                else:
                    import re
                    eid = gpt_resp.headers.get("OData-EntityId", "")
                    m = re.search(r'botcomponents\(([^)]+)\)', eid)
                    gpt_id = m.group(1) if m else "unknown"

                assoc = {"@odata.id": f"{client.api_base_url}/botcomponents({gpt_id})"}
                req.post(
                    f"{client.api_base_url}/bots({bot_id})/bot_botcomponent/$ref",
                    headers=client.headers,
                    json=assoc
                )
                print(f"  *** GPT component created: {gpt_id}")
                has_gpt = True

                # Fix bot config to point to the new GPT schema
                gpt_schema_name = f"{bot_schema}.gpt.{suffix}"
                bot_data = client.get_agent(bot_id)
                bot_cfg = json.loads(bot_data.get('configuration', '{}'))
                if 'gPTSettings' not in bot_cfg:
                    bot_cfg['gPTSettings'] = {"$kind": "GPTSettings"}
                bot_cfg['gPTSettings']['defaultSchemaName'] = gpt_schema_name
                req.patch(
                    f"{client.api_base_url}/bots({bot_id})",
                    headers=client.headers,
                    json={"configuration": json.dumps(bot_cfg)}
                )
                print(f"  *** Config updated: defaultSchemaName → {gpt_schema_name}")

                # Re-provision and re-publish
                time.sleep(2)
                client.provision_agent(bot_id)
                time.sleep(3)
                client.publish_agent(bot_id)
                print("  *** Re-provisioned and re-published")
            else:
                print(f"  *** GPT creation failed: {gpt_resp.status_code} {gpt_resp.text[:200]}")
        except Exception as e:
            print(f"  *** GPT fallback failed: {e}")

    result = {
        "agent_name": name,
        "customer": customer,
        "bot_id": bot_id,
        "bot_schema": bot_schema,
        "environment_url": client.environment_url,
        "instructions_length": len(instructions),
        "components": type_counts,
        "has_gpt": has_gpt,
        "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "deployed" if has_gpt else "deployed_without_gpt"
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Deploy a RAPP agent to Copilot Studio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --name "Sales Agent" --instructions agents/instructions.md
  %(prog)s --name "Sales Agent" --instructions agents/instructions.md --customer "Contoso"
  %(prog)s --delete "Sales Agent"
        """
    )
    parser.add_argument("--name", required=True, help="Agent display name")
    parser.add_argument("--instructions", help="Path to instructions markdown file")
    parser.add_argument("--description", default="", help="Agent description")
    parser.add_argument("--customer", default="", help="Customer name (added to description)")
    parser.add_argument("--config", default="copilot_studio_deployment_config.json",
                        help="Path to deployment config JSON")
    parser.add_argument("--delete", action="store_true", help="Delete the named agent and exit")
    parser.add_argument("--no-replace", action="store_true", help="Don't delete existing agent")
    parser.add_argument("--output", help="Path to save deployment result JSON")

    args = parser.parse_args()

    # Load config and authenticate
    config = load_config(args.config)
    print("=" * 70)
    if args.delete:
        print(f"DELETING AGENT: {args.name}")
    else:
        print(f"DEPLOYING TO COPILOT STUDIO: {args.name}")
    print("=" * 70)
    print(f"Environment: {config['environment_url']}")

    client = authenticate(config)
    print("Authenticated\n")

    if args.delete:
        delete_existing_agent(client, args.name)
        print("\nDone.")
        return

    # Load instructions
    if not args.instructions:
        print("ERROR: --instructions is required for deployment")
        sys.exit(1)

    if not os.path.exists(args.instructions):
        print(f"ERROR: Instructions file not found: {args.instructions}")
        sys.exit(1)

    with open(args.instructions, 'r', encoding='utf-8') as f:
        instructions = f.read()

    print(f"Instructions: {len(instructions):,} characters from {args.instructions}\n")

    # Deploy
    result = deploy_agent(
        client=client,
        name=args.name,
        instructions=instructions,
        description=args.description,
        customer=args.customer,
        replace=not args.no_replace
    )

    # Summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT COMPLETE")
    print("=" * 70)
    print(f"""
Agent:        {result['agent_name']}
Customer:     {result.get('customer') or '(none)'}
Bot ID:       {result['bot_id']}
Schema:       {result['bot_schema']}
Environment:  {result['environment_url']}
Instructions: {result['instructions_length']:,} characters
GPT Present:  {'Yes' if result['has_gpt'] else 'NO - needs manual fix'}
Status:       {result['status']}

NEXT STEPS:
1. Open Copilot Studio: https://copilotstudio.microsoft.com/
2. Find "{result['agent_name']}" → click "Go to agent"
3. Test in the Test pane
4. Enable channels: Teams, M365 Copilot
""")

    # Save result
    output_path = args.output
    if not output_path:
        safe_name = args.name.replace(" ", "_").lower()
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "transpiled", f"{safe_name}_deployment_result.json"
        )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Result saved: {output_path}")


if __name__ == "__main__":
    main()
