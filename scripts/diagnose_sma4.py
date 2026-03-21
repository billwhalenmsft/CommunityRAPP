"""Diagnose the broken SMA4 agent in Copilot Studio."""
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
print("Authenticated\n")

# 1. Get our broken agent
SMA4_BOT_ID = "c6897bdf-8924-f111-88b4-000d3a316172"
print("=== SMA4 AGENT ===")
try:
    bot = client.get_agent(SMA4_BOT_ID)
    for k in ['botid', 'name', 'schemaname', 'language', 'statecode', 'statuscode']:
        print(f"  {k}: {bot.get(k)}")
    config_str = bot.get('configuration', '{}')
    print(f"  configuration: {config_str[:500]}")
except Exception as e:
    print(f"  Error getting SMA4: {e}")

# 2. Get its components
print("\n=== SMA4 COMPONENTS ===")
resp = requests.get(
    f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {SMA4_BOT_ID}&$select=name,componenttype,schemaname,data",
    headers=client.headers
)
if resp.status_code == 200:
    components = resp.json().get('value', [])
    print(f"  Total components: {len(components)}")
    for c in components:
        data_preview = (c.get('data') or '')[:200]
        print(f"  type={c.get('componenttype')} name={c.get('name')} schema={c.get('schemaname')}")
        if data_preview:
            print(f"    data: {data_preview}...")
else:
    print(f"  Error: {resp.status_code} {resp.text[:500]}")

# 3. Find a WORKING Zurn Elkay agent for comparison
print("\n=== FINDING WORKING AGENT FOR COMPARISON ===")
agents = client.list_agents()
print(f"  Total agents: {len(agents)}")
working_bot = None
for a in agents:
    name = a.get('name', '')
    print(f"  - {name} (id={a.get('botid')}, state={a.get('statecode')}, status={a.get('statuscode')})")
    if 'ZE' in name and 'Drains' in name and not working_bot:
        working_bot = a

# 4. Compare with working agent
if working_bot:
    wid = working_bot['botid']
    print(f"\n=== WORKING AGENT: {working_bot['name']} ===")
    wbot = client.get_agent(wid)
    for k in ['botid', 'name', 'schemaname', 'language', 'statecode', 'statuscode']:
        print(f"  {k}: {wbot.get(k)}")
    print(f"  configuration: {wbot.get('configuration', '{}')[:500]}")

    print(f"\n=== WORKING AGENT COMPONENTS ===")
    resp2 = requests.get(
        f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {wid}&$select=name,componenttype,schemaname",
        headers=client.headers
    )
    if resp2.status_code == 200:
        wcomps = resp2.json().get('value', [])
        print(f"  Total components: {len(wcomps)}")
        for c in wcomps:
            print(f"  type={c.get('componenttype')} name={c.get('name')} schema={c.get('schemaname')}")
