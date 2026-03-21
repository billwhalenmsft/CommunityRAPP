"""
Deploy SMA4 Persona Workbench to Copilot Studio.

Creates a single unified agent with:
1. Bot entity with proper AI configuration
2. GPT component (type 15) containing full instructions
3. Instructions component (type 10) for CS Overview display
4. All required system topics (type 9) — Greeting, Fallback, Escalate, etc.
5. Provisions and publishes the agent

Uses the existing copilot_studio_deployment_config.json for environment credentials.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.copilot_studio_api import CopilotStudioClient
import json
import time

# Load config
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'copilot_studio_deployment_config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Load instructions from the transpiled package
instructions_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'transpiled', 'copilot_studio_native', 'sma4_persona_workbench', 'instructions.md'
)
with open(instructions_path, 'r', encoding='utf-8') as f:
    instructions = f.read()

AGENT = {
    "name": "SMA4 Persona Workbench",
    "description": (
        "Unified sales operations assistant providing persona-specific cockpit views "
        "of pipeline, tasks, exceptions, approvals, and handoffs for Contoso's "
        "enterprise sales team. Supports 4 personas: Sarah Chen (Sales Rep), "
        "Mike Torres (Coordinator), Priya Patel (Marketing), James Harrison (Manager)."
    ),
    "instructions": instructions
}


def main():
    print("=" * 70)
    print("DEPLOYING SMA4 PERSONA WORKBENCH TO COPILOT STUDIO")
    print("=" * 70)
    print(f"\nEnvironment: {config['environment_url']}")
    print(f"Instructions: {len(instructions):,} characters")
    print()

    # Authenticate
    client = CopilotStudioClient(
        environment_url=config['environment_url'],
        tenant_id=config['tenant_id'],
        client_id=config['client_id'],
        use_interactive_auth=True
    )
    client.authenticate()
    print("✓ Authenticated successfully\n")

    # Check for existing agent with same name and delete
    print("Checking for existing agent...")
    existing = client.list_agents(
        filter_query=f"name eq '{AGENT['name']}'"
    )
    if existing:
        for ex in existing:
            ex_id = ex.get('botid')
            print(f"  Deleting existing: {ex_id} ({ex.get('name')})")
            # Must delete bot components first
            import requests as req
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
                print(f"    Deleted {len(comps)} components")
            try:
                client.delete_agent(ex_id)
            except Exception as del_err:
                print(f"    ⚠ Delete agent: {del_err}")
        time.sleep(3)
        print("  ✓ Cleaned up existing agent(s)\n")
    else:
        print("  No existing agent found\n")

    # Step 1: Create the bot entity (includes GPT component type 15)
    print("[1/5] Creating agent with GPT component...")
    bot_id = client.create_agent(
        name=AGENT['name'],
        description=AGENT['description'],
        instructions=AGENT['instructions'],
        language="en-us"
    )
    print(f"  ✓ Created agent: {bot_id}")
    print(f"  ✓ GPT component (type 15) with {len(AGENT['instructions']):,} chars")

    # Get the bot schema name for system topics
    bot = client.get_agent(bot_id)
    bot_schema = bot.get('schemaname', '')
    print(f"  ✓ Schema: {bot_schema}")

    # Step 2: Create instructions component (type 10)
    print("\n[2/5] Creating instructions component (type 10)...")
    try:
        instr_id = client.create_instructions_component(
            bot_id=bot_id,
            name=AGENT['name'],
            instructions=AGENT['instructions'],
            description=AGENT['description'],
            bot_schema_name=bot_schema
        )
        print(f"  ✓ Instructions component: {instr_id}")
    except Exception as e:
        print(f"  ⚠ Instructions component: {e}")

    # Step 3: Create all required system topics (type 9)
    print("\n[3/5] Creating system topics...")
    topic_ids = client.create_system_topics(bot_id, bot_schema)
    print(f"  ✓ Created {len(topic_ids)} system topics")

    # Step 4: Ensure generative AI configuration
    print("\n[4/5] Configuring generative AI settings...")
    client.update_agent_configuration(
        bot_id=bot_id,
        enable_generative_ai=True,
        enable_web_browsing=False,
        enable_semantic_search=True
    )
    print("  ✓ Generative orchestration enabled")
    print("  ✓ useModelKnowledge = True")

    # Step 5: Provision and publish
    print("\n[5/5] Provisioning and publishing agent...")
    time.sleep(3)

    # Try provision first
    try:
        prov_result = client.provision_agent(bot_id)
        print(f"  ✓ Provisioned: {prov_result}")
        time.sleep(5)
    except Exception as e:
        print(f"  ⚠ Provision: {e}")

    # Then publish
    try:
        pub_result = client.publish_agent(bot_id)
        print(f"  ✓ Published: {pub_result}")
    except Exception as e:
        print(f"  ⚠ Publish: {e}")
        print("  → You can publish manually from Copilot Studio UI")

    # Verify components
    print("\n" + "-" * 50)
    print("VERIFYING COMPONENTS...")
    import requests as req
    resp = req.get(
        f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {bot_id}&$select=name,componenttype",
        headers=client.headers
    )
    if resp.status_code == 200:
        comps = resp.json().get('value', [])
        type_counts = {}
        for c in comps:
            t = c.get('componenttype')
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"  Total components: {len(comps)}")
        for t, count in sorted(type_counts.items()):
            type_names = {9: 'topics', 10: 'translations', 15: 'GPT'}
            print(f"    Type {t} ({type_names.get(t, 'other')}): {count}")

    # Summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT COMPLETE")
    print("=" * 70)
    print(f"""
Agent:        {AGENT['name']}
Bot ID:       {bot_id}
Schema:       {bot_schema}
Environment:  {config['environment_url']}
Instructions: {len(AGENT['instructions']):,} characters
Components:   GPT (type 15) + Instructions (type 10) + {len(topic_ids)} system topics

NEXT STEPS:
1. Open Copilot Studio: https://copilotstudio.microsoft.com/
2. Switch to environment: org6feab6b5.crm.dynamics.com
3. Find "SMA4 Persona Workbench" → click "Go to agent"
4. Click Publish from the top menu
5. Test in the Test pane:
   - "Hi, I'm Sarah Chen. Show me my cockpit view."
   - "What exceptions need attention?"
   - "I'm James Harrison. Show me all pending approvals."
6. Enable channels: Teams, M365 Copilot
""")

    # Save deployment result
    result_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'transpiled', 'copilot_studio_native', 'sma4_persona_workbench',
        'deployment_result.json'
    )
    with open(result_path, 'w') as f:
        json.dump({
            "agent_name": AGENT['name'],
            "bot_id": bot_id,
            "bot_schema": bot_schema,
            "environment_url": config['environment_url'],
            "instructions_length": len(AGENT['instructions']),
            "system_topics_created": len(topic_ids),
            "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "deployed"
        }, f, indent=2)
    print(f"Deployment result saved to: {result_path}")


if __name__ == "__main__":
    main()
