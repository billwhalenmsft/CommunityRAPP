"""Get the content/data of system topics from a working agent."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.copilot_studio_api import CopilotStudioClient
import json
import requests

with open('copilot_studio_deployment_config.json', 'r') as f:
    config = json.load(f)

client = CopilotStudioClient(
    environment_url=config['environment_url'],
    tenant_id=config['tenant_id'],
    client_id=config['client_id'],
    use_interactive_auth=True
)
client.authenticate()

# Get ZE Drains CI components with full data
WORKING_BOT_ID = "1bf18f9b-a2fb-f011-8407-000d3a316172"
resp = requests.get(
    f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {WORKING_BOT_ID}&$select=name,componenttype,schemaname,content,data,category",
    headers=client.headers
)

if resp.status_code == 200:
    components = resp.json().get('value', [])
    # Focus on system topics (type 9) and the translations (type 10)
    for c in components:
        ctype = c.get('componenttype')
        name = c.get('name', '')
        schema = c.get('schemaname', '')
        
        # Print key system topics
        if name in ['Greeting', 'Fallback', 'Escalate', 'Conversation Start', 'On Error', 'Goodbye'] or ctype == 10:
            print(f"\n{'='*60}")
            print(f"TYPE: {ctype}  NAME: {name}  SCHEMA: {schema}")
            print(f"CATEGORY: {c.get('category')}")
            print(f"{'='*60}")
            content = c.get('content', '')
            data = c.get('data', '')
            if content:
                print(f"CONTENT ({len(content)} chars):")
                print(content[:2000])
            if data:
                print(f"DATA ({len(data)} chars):")
                print(data[:2000])
else:
    print(f"Error: {resp.status_code}")
