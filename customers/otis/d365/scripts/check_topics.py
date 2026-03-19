"""Check format of our service topics and fix if needed."""
import requests
import subprocess
import json

org_url = 'https://orgecbce8ef.crm.dynamics.com'
token = subprocess.run(f'az account get-access-token --resource {org_url} --query accessToken -o tsv', 
                       capture_output=True, text=True, shell=True).stdout.strip()

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

api = f'{org_url}/api/data/v9.2'

# Find our custom topics
print("=== Looking for our service topics ===")
keywords = ['Entrapment', 'Door Issue', 'Billing', 'Modernization', 'Preventive']

for kw in keywords:
    r = requests.get(
        f"{api}/botcomponents?$filter=contains(name,'{kw}')&$select=botcomponentid,name,componenttype,content,data,schemaname",
        headers=headers
    )
    for c in r.json().get('value', []):
        print(f"\nName: {c.get('name')}")
        print(f"  ID: {c.get('botcomponentid')}")
        print(f"  Schema: {c.get('schemaname')}")
        print(f"  Type: {c.get('componenttype')}")
        content = c.get('content', '')
        data = c.get('data', '')
        if content:
            print(f"  Content (first 200): {content[:200]}")
        if data:
            print(f"  Data (first 200): {data[:200]}")
        if not content and not data:
            print("  !! EMPTY - No content or data !!")

# Check what a working topic looks like
print("\n\n=== Sample working topic (Greeting) ===")
r = requests.get(
    f"{api}/botcomponents?$filter=name eq 'Greeting'&$select=botcomponentid,name,componenttype,content,data&$top=1",
    headers=headers
)
for c in r.json().get('value', []):
    print(f"Name: {c.get('name')}")
    print(f"Type: {c.get('componenttype')}")
    content = c.get('content', '')
    data = c.get('data', '')
    print(f"Content: {content[:500] if content else 'EMPTY'}")
    print(f"Data: {data[:500] if data else 'EMPTY'}")
