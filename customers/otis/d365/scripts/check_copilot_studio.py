"""
Check Copilot Studio agent deployment status.
Queries Dataverse to see what was actually created.
"""

import requests
import subprocess
import json
import sys
import os

def get_token(org_url):
    """Get Azure AD token for Dataverse."""
    # Use shell=True on Windows for path resolution
    result = subprocess.run(
        f'az account get-access-token --resource {org_url} --query accessToken -o tsv',
        capture_output=True, text=True, check=True, shell=True
    )
    return result.stdout.strip()

def main():
    org_url = 'https://orgecbce8ef.crm.dynamics.com'
    
    print("Getting access token...")
    token = get_token(org_url)
    print("✓ Got token")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0'
    }
    
    api_base = f'{org_url}/api/data/v9.2'
    
    # 1. List all bots
    print("\n=== BOTS (Most Recent) ===")
    r = requests.get(
        f"{api_base}/bots?$select=name,schemaname,botid,createdon,statecode,statuscode&$orderby=createdon desc&$top=10",
        headers=headers
    )
    if r.status_code != 200:
        print(f"ERROR: {r.status_code} - {r.text}")
        return
    
    bots = r.json().get('value', [])
    for b in bots:
        print(f"  • {b.get('name')}")
        print(f"    Schema: {b.get('schemaname')}")
        print(f"    ID: {b.get('botid')}")
        print(f"    State: {b.get('statecode')} | Status: {b.get('statuscode')}")
        print(f"    Created: {b.get('createdon')}")
        print()
    
    # 2. Check for our specific bot
    target_bot_id = "87f54269-3321-f111-8341-6045bda80a72"
    print(f"\n=== CHECKING TARGET BOT: {target_bot_id} ===")
    r = requests.get(
        f"{api_base}/bots({target_bot_id})?$select=name,schemaname,configuration,statecode,statuscode",
        headers=headers
    )
    if r.status_code == 404:
        print("❌ Bot NOT FOUND - it was not created successfully!")
    elif r.status_code == 200:
        bot = r.json()
        print(f"✓ Bot exists: {bot.get('name')}")
        print(f"  Schema: {bot.get('schemaname')}")
        print(f"  State: {bot.get('statecode')}")
        
        # Check configuration
        config = bot.get('configuration', '{}')
        try:
            config_json = json.loads(config) if config else {}
            print(f"  Configuration keys: {list(config_json.keys())}")
            ai_settings = config_json.get('aISettings', {})
            print(f"  AI Settings: {ai_settings}")
        except:
            print(f"  Raw config: {config[:200] if config else 'None'}...")
    else:
        print(f"ERROR: {r.status_code} - {r.text}")
    
    # 3. Check for GPT components (type 15)
    print(f"\n=== GPT COMPONENTS (type 15) ===")
    r = requests.get(
        f"{api_base}/botcomponents?$select=name,schemaname,botcomponentid,componenttype,data&$filter=componenttype eq 15&$orderby=createdon desc&$top=5",
        headers=headers
    )
    if r.status_code == 200:
        components = r.json().get('value', [])
        if not components:
            print("❌ No GPT components found!")
        for c in components:
            print(f"  • {c.get('name')}")
            print(f"    Schema: {c.get('schemaname')}")
            print(f"    ID: {c.get('botcomponentid')}")
            data = c.get('data', '')
            if data:
                print(f"    Data preview: {data[:200]}...")
            print()
    else:
        print(f"ERROR: {r.status_code} - {r.text}")
    
    # 4. Check component associations for our bot
    print(f"\n=== COMPONENT ASSOCIATIONS for target bot ===")
    r = requests.get(
        f"{api_base}/bots({target_bot_id})/bot_botcomponent?$select=name,schemaname,componenttype",
        headers=headers
    )
    if r.status_code == 200:
        assocs = r.json().get('value', [])
        if not assocs:
            print("❌ No components associated with this bot!")
        for a in assocs:
            print(f"  • {a.get('name')} (type {a.get('componenttype')})")
    elif r.status_code == 404:
        print("❌ Bot not found for association query")
    else:
        print(f"ERROR: {r.status_code}")

if __name__ == "__main__":
    main()
