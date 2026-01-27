"""
Fix ALL ZE agents - Enable generative AI for unmatched queries on all sub-agents.

This ensures the orchestrator AND all 6 sub-agents can use AI to handle
queries that don't exactly match topic trigger phrases.
"""

import requests
import json
import os
from azure.identity import DefaultAzureCredential

def main():
    env_url = os.environ.get('DATAVERSE_ENVIRONMENT_URL', 'https://org6feab6b5.crm.dynamics.com')
    api_base = f'{env_url}/api/data/v9.2'
    
    print("=" * 70)
    print("FIX ALL ZE AGENTS - ENABLE GENERATIVE AI")
    print("=" * 70)
    
    # Authenticate
    print("\nAuthenticating...")
    token = DefaultAzureCredential().get_token(f'{env_url}/.default').token
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Prefer': 'return=representation'
    }
    print("✓ Authenticated")
    
    # Find all ZE agents
    print("\nFinding all ZE agents...")
    response = requests.get(
        f"{api_base}/bots?$select=botid,name,configuration",
        headers=headers
    )
    
    all_bots = response.json().get('value', [])
    
    # Filter to ZE agents
    ze_terms = ['ZE CI', 'ZE Drains', 'ZE Drinking', 'ZE Sinks', 'ZE Commercial', 'ZE Wilkins', 'ZE Cross-BU']
    ze_bots = [b for b in all_bots if any(term in b.get('name', '') for term in ze_terms)]
    
    print(f"✓ Found {len(ze_bots)} ZE agents")
    
    fixed_count = 0
    already_ok_count = 0
    failed_count = 0
    
    for bot in ze_bots:
        bot_id = bot.get('botid')
        bot_name = bot.get('name')
        
        print(f"\n{'─' * 70}")
        print(f"Agent: {bot_name}")
        print(f"{'─' * 70}")
        
        # Parse current configuration
        config_str = bot.get('configuration', '{}')
        try:
            config = json.loads(config_str) if isinstance(config_str, str) else config_str
        except:
            config = {}
        
        # Check current AI settings
        ai_settings = config.get('aISettings', {})
        current_value = ai_settings.get('useModelKnowledge', False)
        
        print(f"  Current useModelKnowledge: {current_value}")
        
        if current_value == True:
            print(f"  ✓ Already configured correctly")
            already_ok_count += 1
            continue
        
        # Update AI settings
        new_ai_settings = {
            "$kind": "AISettings",
            "useModelKnowledge": True,
            "isFileAnalysisEnabled": True,
            "isSemanticSearchEnabled": True,
            "contentModeration": "Medium",
            "optInUseLatestModels": True,
            "generativeAnswersEnabled": True,
            "boostedConversationsEnabled": True
        }
        
        config['aISettings'] = new_ai_settings
        
        if 'settings' not in config:
            config['settings'] = {}
        config['settings']['orchestrationType'] = 'Generative'
        
        new_config_str = json.dumps(config)
        
        # Update the bot
        update_response = requests.patch(
            f"{api_base}/bots({bot_id})",
            headers=headers,
            json={"configuration": new_config_str}
        )
        
        if update_response.status_code in [200, 204]:
            print(f"  ✓ Updated useModelKnowledge to True")
            fixed_count += 1
            
            # Publish
            publish_response = requests.post(
                f"{api_base}/bots({bot_id})/Microsoft.Dynamics.CRM.PvaPublish",
                headers=headers,
                json={}
            )
            if publish_response.status_code in [200, 202, 204]:
                print(f"  ✓ Published")
            else:
                print(f"  ⚠ Publish may need manual trigger")
        else:
            print(f"  ✗ Failed to update: {update_response.status_code}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n  Already configured correctly: {already_ok_count}")
    print(f"  Fixed in this run: {fixed_count}")
    print(f"  Failed: {failed_count}")
    
    if failed_count == 0:
        print("\n✓ ALL ZE AGENTS NOW HAVE GENERATIVE AI ENABLED!")
        print("\nThe agents should now use AI to handle queries that don't match specific topics.")
    else:
        print(f"\n⚠ {failed_count} agents may need manual fixes in Copilot Studio")
    
    print("\n" + "=" * 70)
    print("DONE - Test the agents in Copilot Studio")
    print("=" * 70)


if __name__ == "__main__":
    main()
