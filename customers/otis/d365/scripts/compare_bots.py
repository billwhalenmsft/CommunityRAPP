"""Check what components a working Copilot Studio agent has."""
import requests
import subprocess
import json

org_url = 'https://orgecbce8ef.crm.dynamics.com'
result = subprocess.run(f'az account get-access-token --resource {org_url} --query accessToken -o tsv', capture_output=True, text=True, shell=True)
token = result.stdout.strip()

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

api = f'{org_url}/api/data/v9.2'

# Check Customer Portal bot (user created, works)
print("=== Customer Service Portal Assistant ===")
bot_id = 'da8f1b23-c018-f111-8342-7ced8d18c8d7'
r = requests.get(f'{api}/bots({bot_id})/bot_botcomponent', headers=headers)
comps = r.json().get('value', [])
print(f"Component count: {len(comps)}")
for c in comps[:20]:
    print(f"  Type {c.get('componenttype'):2}: {c.get('name', 'N/A')[:60]}")

# Check our Otis bot
print("\n=== Otis Service Copilot ===")
bot_id = '87f54269-3321-f111-8341-6045bda80a72'
r = requests.get(f'{api}/bots({bot_id})/bot_botcomponent', headers=headers)
comps = r.json().get('value', [])
print(f"Component count: {len(comps)}")
for c in comps[:20]:
    print(f"  Type {c.get('componenttype'):2}: {c.get('name', 'N/A')[:60]}")

# Check for system topics
print("\n=== Looking for system topics ===")
r = requests.get(f"{api}/botcomponents?$filter=contains(schemaname,'system') and componenttype eq 9&$top=10", headers=headers)
for c in r.json().get('value', [])[:5]:
    print(f"  {c.get('schemaname')}")
