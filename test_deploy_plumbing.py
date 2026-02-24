"""
Deploy the Plumbing Code Intelligence solution to Mfg Gold Template environment.
Step 1: Clean up any partially-deployed agents from previous attempts.
Step 2: Deploy all 3 agents with GPT instructions and topics.
"""
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    from utils.copilot_studio_api import CopilotStudioClient
    
    env_url = "https://org6feab6b5.crm.dynamics.com"
    tenant_id = "daa9e2eb-aaf1-46a8-a37e-3fd2e5821cb6"
    client_id = "8562b2aa-8b34-4c3a-87d9-5ac05092858e"
    
    print("=" * 60)
    print("Deploying Plumbing Code Intelligence to Mfg Gold Template")
    print("=" * 60)
    
    # Authenticate
    print("\n[1/4] Authenticating to Copilot Studio...")
    client = CopilotStudioClient(
        environment_url=env_url,
        tenant_id=tenant_id,
        client_id=client_id,
        use_interactive_auth=True
    )
    client.authenticate()
    print("  Authentication successful!")
    
    # Clean up any previous partial deployments
    print("\n[2/4] Checking for existing PC agents to clean up...")
    try:
        agents = client.list_agents("contains(name, 'PC ')")
        pc_agents = [a for a in agents if a.get("name", "").startswith("PC ")]
        if pc_agents:
            for agent in pc_agents:
                name = agent.get("name", "unknown")
                bot_id = agent.get("botid")
                print(f"  Deleting existing agent: {name} ({bot_id})")
                try:
                    client.delete_agent(bot_id)
                    print(f"    Deleted!")
                    time.sleep(2)  # Brief pause between deletes
                except Exception as e:
                    print(f"    Delete failed: {e}")
        else:
            print("  No existing PC agents found.")
    except Exception as e:
        print(f"  List/cleanup failed (continuing): {e}")
    
    # Deploy each agent manually
    print("\n[3/4] Deploying agents...")
    
    transpiled_base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "transpiled", "copilot_studio_native"
    )
    
    agents_to_deploy = [
        ("plumbing_code_source_monitor", "PC Source Monitor"),
        ("plumbing_code_tech_extractor", "PC Technical Extractor"),
        ("plumbing_code_monthly_synthesizer", "PC Monthly Synthesizer"),
    ]
    
    deployed = []
    failed = []
    
    for agent_folder, display_name in agents_to_deploy:
        agent_dir = os.path.join(transpiled_base, agent_folder)
        manifest_path = os.path.join(agent_dir, "agent_manifest.json")
        
        print(f"\n  --- {display_name} ---")
        
        if not os.path.exists(manifest_path):
            print(f"  SKIP: manifest not found at {manifest_path}")
            failed.append((display_name, "manifest not found"))
            continue
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Get instructions
        instructions = manifest.get("instructions") or manifest.get("systemPrompt", "")
        if not instructions:
            instructions_path = os.path.join(agent_dir, "instructions.md")
            if os.path.exists(instructions_path):
                with open(instructions_path, 'r', encoding='utf-8') as f:
                    instructions = f.read()
        
        description = f"Plumbing Code Intelligence pipeline. {manifest.get('description', '')}"[:500]
        
        try:
            # Create agent with GPT component
            print(f"  Creating agent...")
            bot_id = client.create_agent(
                name=display_name,
                description=description,
                instructions=instructions,
                language=manifest.get("primaryLanguage", "en-us")
            )
            print(f"  Created! bot_id={bot_id}")
            
            # Load and create topics
            topics_dir = os.path.join(agent_dir, "topics")
            topic_count = 0
            if os.path.exists(topics_dir):
                import yaml
                for topic_file in sorted(os.listdir(topics_dir)):
                    if not topic_file.endswith('.yaml'):
                        continue
                    topic_path = os.path.join(topics_dir, topic_file)
                    with open(topic_path, 'r') as f:
                        topic = yaml.safe_load(f)
                    
                    trigger_phrases = []
                    for trigger in topic.get("triggers", []):
                        trigger_phrases.extend(trigger.get("triggerQueries", []))
                    
                    try:
                        topic_id = client.create_topic(
                            bot_id=bot_id,
                            name=topic.get("displayName", topic.get("id", "Unknown")),
                            trigger_phrases=trigger_phrases,
                            description=topic.get("description", "")
                        )
                        topic_count += 1
                        print(f"    Topic: {topic.get('displayName', topic_file)} -> {topic_id}")
                    except Exception as te:
                        print(f"    Topic FAIL ({topic_file}): {te}")
            
            deployed.append({
                "name": display_name,
                "bot_id": bot_id,
                "topics": topic_count,
                "has_instructions": bool(instructions)
            })
            print(f"  SUCCESS: {display_name} ({topic_count} topics)")
            time.sleep(3)  # Brief pause between agents
            
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append((display_name, str(e)))
    
    # Summary
    print(f"\n{'=' * 60}")
    print("[4/4] DEPLOYMENT SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Deployed: {len(deployed)}")
    for d in deployed:
        print(f"    {d['name']} (bot_id={d['bot_id']}, topics={d['topics']})")
    print(f"  Failed: {len(failed)}")
    for name, err in failed:
        print(f"    {name}: {err}")
    
    copilot_url = env_url.replace('.crm.dynamics.com', '.powervirtualagents.com')
    print(f"\n  Next Steps:")
    print(f"    1. Open Copilot Studio: {copilot_url}")
    print(f"    2. Find agents by searching 'PC'")
    print(f"    3. Test each agent, then Publish")

if __name__ == "__main__":
    main()
