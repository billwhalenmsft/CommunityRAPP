"""
Check and fix GPT components for the 3 PC agents.
Agents without a GPT component (componenttype=15) cannot be published.
"""
import sys, os, json, requests
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

    api_base = client.api_base_url
    headers = client.headers

    agents = {
        "PC Source Monitor": "2d300c9b-2d0c-f111-8342-000d3a316172",
        "PC Technical Extractor": "63217ab4-2d0c-f111-8342-000d3a316172",
        "PC Monthly Synthesizer": "fc31e2c6-2d0c-f111-8342-000d3a316172",
    }

    transpiled_base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "transpiled", "copilot_studio_native"
    )
    
    agent_folders = {
        "PC Source Monitor": "plumbing_code_source_monitor",
        "PC Technical Extractor": "plumbing_code_tech_extractor",
        "PC Monthly Synthesizer": "plumbing_code_monthly_synthesizer",
    }

    for name, bot_id in agents.items():
        print(f"{'='*60}")
        print(f"Checking: {name} ({bot_id})")
        print(f"{'='*60}")

        # Get all components for this bot
        resp = requests.get(
            f"{api_base}/botcomponents?$filter=_parentbotid_value eq '{bot_id}'",
            headers=headers
        )
        if resp.status_code != 200:
            print(f"  ERROR: Could not query components: {resp.status_code}")
            continue

        components = resp.json().get("value", [])
        print(f"  Total components: {len(components)}")
        
        gpt_components = [c for c in components if c.get("componenttype") == 15]
        topic_components = [c for c in components if c.get("componenttype") == 9]
        other_components = [c for c in components if c.get("componenttype") not in [9, 15]]
        
        print(f"  GPT components (type 15): {len(gpt_components)}")
        for g in gpt_components:
            print(f"    - {g.get('name', '?')} (id={g.get('botcomponentid')})")
            data = g.get('data', '')
            if data:
                # Show first 200 chars of instructions
                print(f"      Data preview: {data[:200]}...")
        
        print(f"  Topic components (type 9): {len(topic_components)}")
        for t in topic_components:
            print(f"    - {t.get('name', '?')}")
        
        print(f"  Other components: {len(other_components)}")
        for o in other_components:
            print(f"    - [{o.get('componenttype')}] {o.get('name', '?')}")

        # If no GPT component, create one
        if not gpt_components:
            print(f"\n  *** MISSING GPT COMPONENT - Creating... ***")
            
            # Load instructions from transpiled manifest
            folder = agent_folders[name]
            manifest_path = os.path.join(transpiled_base, folder, "agent_manifest.json")
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            instructions = manifest.get("instructions") or manifest.get("systemPrompt", "")
            if not instructions:
                instr_path = os.path.join(transpiled_base, folder, "instructions.md")
                if os.path.exists(instr_path):
                    with open(instr_path, 'r', encoding='utf-8') as f:
                        instructions = f.read()
            
            if not instructions:
                instructions = f"You are {name}. {manifest.get('description', '')}"
            
            try:
                comp_id = client.create_gpt_component(
                    bot_id=bot_id,
                    name=f"{name} - Instructions",
                    instructions=instructions,
                    description=manifest.get('description', '')[:500]
                )
                print(f"  GPT component created: {comp_id}")
            except Exception as e:
                print(f"  GPT creation FAILED: {e}")
        else:
            print(f"\n  GPT component present - OK")

        # Also check bot configuration
        try:
            bot = client.get_agent(bot_id)
            config_str = bot.get('configuration', '{}')
            config = json.loads(config_str) if config_str else {}
            use_model = config.get('useModelKnowledge', False)
            print(f"  useModelKnowledge: {use_model}")
            
            if not use_model:
                print(f"  *** Enabling generative AI... ***")
                client.update_agent_configuration(
                    bot_id=bot_id,
                    enable_generative_ai=True,
                    enable_web_browsing=True,
                    enable_semantic_search=True
                )
                print(f"  Generative AI enabled!")
        except Exception as e:
            print(f"  Config check/update error: {e}")

        print()

if __name__ == "__main__":
    main()
