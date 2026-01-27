"""
List all ZE agents in the environment.
"""
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.copilot_studio_api import CopilotStudioClient

api = CopilotStudioClient(
    environment_url='https://org6feab6b5.crm.dynamics.com',
    tenant_id='daa9e2eb-aaf1-46a8-a37e-3fd2e5821cb6',
    client_id='8562b2aa-8b34-4c3a-87d9-5ac05092858e',
    use_interactive_auth=True
)
api.authenticate()
print('Authenticated!')

# Find all ZE agents
response = requests.get(
    api.api_base_url + '/bots',
    headers=api.headers,
    params={
        '$filter': "startswith(name, 'ZE')",
        '$select': 'botid,name,schemaname',
        '$orderby': 'name'
    }
)
if response.status_code == 200:
    agents = response.json().get('value', [])
    print(f'Found {len(agents)} ZE agents:')
    for a in agents:
        print(f"  {a['name']}: {a['botid']} (schema: {a['schemaname']})")
        
        # Check if agent has a Custom GPT component
        comp_response = requests.get(
            api.api_base_url + '/botcomponents',
            headers=api.headers,
            params={
                '$filter': f"_parentbotid_value eq '{a['botid']}' and componenttype eq 15",
                '$select': 'botcomponentid,name,schemaname,data'
            }
        )
        if comp_response.status_code == 200:
            comps = comp_response.json().get('value', [])
            if comps:
                for c in comps:
                    data = c.get('data', '')
                    has_instructions = 'instructions:' in data and len(data) > 100
                    print(f"    Custom GPT: {c['schemaname'][:50]}...")
                    print(f"    Has instructions: {has_instructions}")
                    if data:
                        # Show first 200 chars of data
                        print(f"    Data preview: {data[:200]}...")
            else:
                print(f"    NO Custom GPT component found!")
else:
    print(f'Error: {response.status_code}')
    print(response.text)
