"""
Publish all ZE (Zurn Elkay) agents in Copilot Studio.

Uses the PvaPublish action on the Dataverse Web API to publish agents programmatically.
"""

import os
import sys
import time
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.copilot_studio_api import CopilotStudioClient

# Load config
with open('copilot_studio_deployment_config.json', 'r') as f:
    config = json.load(f)


def publish_ze_agents():
    """Find and publish all ZE agents."""
    
    print("=" * 70)
    print("PUBLISHING ZURN ELKAY AGENTS IN COPILOT STUDIO")
    print("=" * 70)
    
    # Initialize API client with config
    api = CopilotStudioClient(
        environment_url=config.get("environment_url"),
        tenant_id=config.get("tenant_id"),
        client_id=config.get("client_id")
    )
    
    if not api.authenticate():
        print("❌ Failed to authenticate")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Get all bots using list_agents method
    try:
        all_bots = api.list_agents()
    except Exception as e:
        print(f"❌ Failed to retrieve bots: {e}")
        return False
    
    # Filter to ZE agents
    ze_agents = [bot for bot in all_bots if bot.get("name", "").lower().startswith("ze ")]
    
    if not ze_agents:
        print("No ZE agents found.")
        return False
    
    print(f"Found {len(ze_agents)} ZE agents:\n")
    
    for agent in ze_agents:
        print(f"  - {agent['name']} ({agent['botid']})")
    
    print("\n" + "-" * 70)
    print("PROVISIONING AGENTS (if needed)")
    print("-" * 70 + "\n")
    
    # First try to provision each agent
    for i, agent in enumerate(ze_agents, 1):
        bot_id = agent["botid"]
        name = agent["name"]
        
        print(f"[{i}/{len(ze_agents)}] Provisioning: {name}")
        
        try:
            response = api.provision_agent(bot_id)
            print(f"  ✓ Provisioned")
        except Exception as e:
            # Provisioning might fail if already provisioned - that's OK
            print(f"  ℹ Provision skipped (may already be provisioned)")
        
        time.sleep(2)  # Increased delay
    
    # Wait for provisioning to complete
    print("\n⏳ Waiting 10 seconds for provisioning to complete...\n")
    time.sleep(10)
    
    print("-" * 70)
    print("PUBLISHING AGENTS")
    print("-" * 70 + "\n")
    
    success_count = 0
    failed = []
    
    for i, agent in enumerate(ze_agents, 1):
        bot_id = agent["botid"]
        name = agent["name"]
        
        print(f"[{i}/{len(ze_agents)}] Publishing: {name}")
        print(f"  Bot ID: {bot_id}")
        
        # Try publishing with retry
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = api.publish_agent(bot_id)
                print(f"  ✓ Published successfully")
                success_count += 1
                
                # Check the response for any details
                if isinstance(response, dict):
                    if response.get("Status"):
                        print(f"    Status: {response.get('Status')}")
                    if response.get("PublishJobId"):
                        print(f"    Job ID: {response.get('PublishJobId')}")
                break  # Success, exit retry loop
                    
            except Exception as e:
                error_msg = str(e)
                if "409" in error_msg and attempt < max_retries:
                    print(f"  ⏳ Conflict, retrying in 5 seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)
                else:
                    print(f"  ❌ Failed to publish: {error_msg}")
                    failed.append((name, error_msg))
        
        # Small delay between publishes to avoid rate limiting
        if i < len(ze_agents):
            time.sleep(2)
        
        print()
    
    # Summary
    print("=" * 70)
    print("PUBLISH SUMMARY")
    print("=" * 70)
    print(f"\n✓ Successfully published: {success_count}/{len(ze_agents)}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for name, error in failed:
            print(f"   - {name}: {error}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
Publishing is an asynchronous process. Check the status in Copilot Studio:

1. Open Copilot Studio: https://copilotstudio.microsoft.com/
2. Select environment: Mfg Gold Template
3. Find your agents (search for "ZE")
4. Check the publish status in each agent's Overview page

Note: Publishing typically takes 1-2 minutes per agent.
""")
    
    return success_count == len(ze_agents)


if __name__ == "__main__":
    success = publish_ze_agents()
    sys.exit(0 if success else 1)
