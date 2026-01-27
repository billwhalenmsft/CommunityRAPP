"""
Cleanup duplicate agents in Copilot Studio.
Deletes older versions keeping only the most recent ZE agents.
"""
import json
import requests
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.copilot_studio_api import CopilotStudioClient

# Load config
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'copilot_studio_deployment_config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

client = CopilotStudioClient(
    environment_url=config['environment_url'],
    tenant_id=config['tenant_id'],
    client_id=config['client_id'],
    use_interactive_auth=True
)
client.authenticate()

def delete_agent_with_components(client, bot_id, name):
    """Delete an agent and all its dependent components"""
    # First, get all bot components for this agent
    url = f'{client.api_base_url}/botcomponents'
    params = {'$filter': f'_parentbotid_value eq {bot_id}'}
    response = requests.get(url, headers=client.headers, params=params)
    
    if response.status_code == 200:
        components = response.json().get('value', [])
        print(f'  Found {len(components)} components to delete for {name}')
        
        # Delete each component
        for comp in components:
            comp_id = comp.get('botcomponentid')
            try:
                del_url = f'{client.api_base_url}/botcomponents({comp_id})'
                del_resp = requests.delete(del_url, headers=client.headers)
                if del_resp.status_code not in [200, 204]:
                    pass  # Some components may be auto-deleted or have dependencies
            except Exception as e:
                pass
        
        # Now delete the bot
        try:
            client.delete_agent(bot_id)
            print(f'  SUCCESS: Deleted {name}')
            return True
        except Exception as e:
            print(f'  FAILED: {str(e)[:100]}')
            return False
    else:
        print(f'  Could not get components: {response.status_code}')
        return False

# IDs of older duplicates to delete (from the first failed deployment batch)
old_agents_to_delete = [
    ('ZE Ci Orch (old)',             '309ffd97-97fb-f011-8407-000d3a316172'),
    ('ZE Drains Ci (old)',           'd81faab0-97fb-f011-8407-000d3a316172'),
    ('ZE Drinking Water Ci (old)',   '8616c7c9-97fb-f011-8407-000d3a316172'),
    ('ZE Sinks Ci (old)',            'b6d67be3-97fb-f011-8407-000d3a316172'),
    ('ZE Commercial Brass Ci (old)', '2c6bbffb-97fb-f011-8407-000d3a316172'),
    ('ZE Wilkins Ci (old)',          '5524de1a-98fb-f011-8407-000d3a316172'),
    ('ZE Crossbu Synth (old)',       '1850d92e-98fb-f011-8407-000d3a316172'),
]

print('Deleting older duplicate agents with their components...')
print()

deleted = 0
for name, bot_id in old_agents_to_delete:
    print(f'Processing {name}...')
    if delete_agent_with_components(client, bot_id, name):
        deleted += 1
    print()

print(f'Deleted {deleted} of {len(old_agents_to_delete)} duplicate agents')

# Verify remaining agents
print()
print('='*60)
print('Remaining ZE agents:')
print('='*60)
agents = client.list_agents()
ze_agents = [a for a in agents if a.get('name', '').startswith('ZE')]
for a in sorted(ze_agents, key=lambda x: x.get('name', '')):
    name = a.get('name', 'Unknown')[:42]
    botid = a.get('botid')
    created = a.get('createdon', 'N/A')[:19]
    print(f'{name:<42} | {botid} | {created}')
print(f'\nTotal: {len(ze_agents)} agents')
