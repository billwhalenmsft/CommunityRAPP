"""Quick check on components of the new SMA4 agent."""
import sys, os, json, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.copilot_studio_api import CopilotStudioClient

with open('copilot_studio_deployment_config.json') as f:
    config = json.load(f)

client = CopilotStudioClient(
    environment_url=config['environment_url'],
    tenant_id=config['tenant_id'],
    client_id=config['client_id']
)
client.authenticate()

bot_id = 'e9c8c742-8b24-f111-88b4-000d3a316172'
resp = requests.get(
    f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {bot_id}&$select=name,componenttype,schemaname,data",
    headers=client.headers
)
for c in resp.json().get('value', []):
    ct = c.get('componenttype')
    name = c.get('name')
    schema = c.get('schemaname')
    data_len = len(c.get('data') or '')
    print(f"type={ct:>2}  data={data_len:>6} chars  name={name}  schema={schema}")
