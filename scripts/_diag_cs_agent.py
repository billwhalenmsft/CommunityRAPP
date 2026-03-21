"""Diagnose Copilot Studio SMA4 agent - check bot config, GPT component, and publication status"""
import json
import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.copilot_studio_api import CopilotStudioClient

ENV_URL = "https://org6feab6b5.crm.dynamics.com"
BOT_ID = "e9c8c742-8b24-f111-88b4-000d3a316172"

client = CopilotStudioClient(ENV_URL)
client.authenticate()

api = client.api_base_url
hdrs = client.headers

print("=" * 70)
print("COPILOT STUDIO SMA4 AGENT DIAGNOSTICS")
print("=" * 70)

# 1. Check bot exists
print("\n[1] Bot entity...")
gpt_settings = {}
try:
    r = requests.get(f"{api}/bots({BOT_ID})", headers=hdrs)
    r.raise_for_status()
    bot = r.json()
    print(f"  Name: {bot.get('name')}")
    print(f"  SchemaName: {bot.get('schemaname')}")
    print(f"  State: {bot.get('statecode')} (0=active)")
    print(f"  Status: {bot.get('statuscode')}")
    
    config_str = bot.get('configuration', '{}')
    config = json.loads(config_str) if config_str else {}
    gpt_settings = config.get('gPTSettings', {})
    print(f"  gPTSettings.defaultSchemaName: {gpt_settings.get('defaultSchemaName', 'NOT SET')}")
    print(f"  gPTSettings.isGPTGenerated: {gpt_settings.get('isGPTGenerated', 'NOT SET')}")
    
    print(f"\n  Full config:")
    print(f"  {json.dumps(config, indent=2)[:3000]}")
    
except Exception as e:
    print(f"  ERROR: {e}")

# 2. Check components
print("\n[2] Bot components...")
gpt_component = None
try:
    r = requests.get(
        f"{api}/botcomponents?$filter=_parentbotid_value eq '{BOT_ID}'&$select=name,componenttype,schemaname,data",
        headers=hdrs
    )
    r.raise_for_status()
    components = r.json().get('value', [])
    print(f"  Total components: {len(components)}")
    
    type_counts = {}
    for c in components:
        ct = c.get('componenttype')
        type_counts[ct] = type_counts.get(ct, 0) + 1
        if ct == 15:
            gpt_component = c
            print(f"\n  GPT Component (type 15):")
            print(f"    Name: {c.get('name')}")
            print(f"    SchemaName: {c.get('schemaname')}")
            data = c.get('data', '')
            print(f"    Data length: {len(data)} chars")
            if data:
                print(f"    Data preview: {data[:600]}")
        if ct == 10:
            print(f"\n  Instructions Component (type 10):")
            print(f"    Name: {c.get('name')}")
            print(f"    SchemaName: {c.get('schemaname')}")
    
    print(f"\n  Component type counts: {json.dumps(type_counts)}")
    
    if not gpt_component:
        print("\n  *** NO GPT COMPONENT (type 15) FOUND! ***")
        
except Exception as e:
    print(f"  ERROR: {e}")

# 3. Schema alignment
print("\n[3] Schema alignment check...")
if gpt_component and gpt_settings:
    cfg_schema = gpt_settings.get('defaultSchemaName', '')
    gpt_schema = gpt_component.get('schemaname', '')
    if cfg_schema == gpt_schema:
        print(f"  MATCH: {cfg_schema}")
    else:
        print(f"  MISMATCH!")
        print(f"    Config says: {cfg_schema}")
        print(f"    GPT has:     {gpt_schema}")
elif not gpt_component:
    print("  Cannot check - no GPT component exists")

# 4. Check published versions
print("\n[4] Published versions...")
try:
    r = requests.get(
        f"{api}/botversions?$filter=_parentbotid_value eq '{BOT_ID}'&$select=name,publishedon,createdon,statuscode&$orderby=createdon desc&$top=5",
        headers=hdrs
    )
    r.raise_for_status()
    versions = r.json().get('value', [])
    print(f"  Total versions: {len(versions)}")
    for v in versions:
        print(f"    {v.get('name')} | Published: {v.get('publishedon')} | Status: {v.get('statuscode')}")
except Exception as e:
    print(f"  ERROR: {e}")

# 5. Check generative AI orchestration
print("\n[5] Generative AI check...")
try:
    r = requests.get(
        f"{api}/bots({BOT_ID})?$select=name,configuration,authenticationtrigger,language",
        headers=hdrs
    )
    r.raise_for_status()
    bot2 = r.json()
    print(f"  Auth trigger: {bot2.get('authenticationtrigger')} (0=Never, 2=AsNeeded)")
    print(f"  Language: {bot2.get('language')}")
    
    r2 = requests.get(
        f"{api}/botcomponents?$filter=_parentbotid_value eq '{BOT_ID}' and componenttype eq 15&$select=schemaname,data,name",
        headers=hdrs
    )
    r2.raise_for_status()
    gpt_comps = r2.json().get('value', [])
    print(f"  GPT components found: {len(gpt_comps)}")
    for gc in gpt_comps:
        print(f"    Schema: {gc.get('schemaname')}")
        data = gc.get('data', '')
        has_instructions = 'instructions:' in data
        has_capabilities = 'gptCapabilities:' in data or 'Capabilities' in data
        print(f"    Has instructions: {has_instructions}")
        print(f"    Has capabilities: {has_capabilities}")
        
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
