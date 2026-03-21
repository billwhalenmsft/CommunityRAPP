"""Add the missing GPT component (type 15) to the SMA4 agent.

The GPT component holds the AI instructions. It failed to create during deploy
due to a schema name collision with the deleted predecessor bot.
This script uses a unique schema name suffix to avoid the collision.
"""
import sys, os, json, requests, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.copilot_studio_api import CopilotStudioClient

# Load config
with open('copilot_studio_deployment_config.json') as f:
    config = json.load(f)

client = CopilotStudioClient(
    environment_url=config['environment_url'],
    tenant_id=config['tenant_id'],
    client_id=config['client_id']
)
client.authenticate()

BOT_ID = 'e9c8c742-8b24-f111-88b4-000d3a316172'
BOT_SCHEMA = 'rapp_SMA4_Persona_Workbench_20260320133321'

# Load instructions
instructions_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'transpiled', 'copilot_studio_native', 'sma4_persona_workbench', 'instructions.md'
)
with open(instructions_path, 'r', encoding='utf-8') as f:
    instructions = f.read()

print(f"Instructions loaded: {len(instructions)} chars")

# Use a unique suffix to avoid schema collision
unique_suffix = uuid.uuid4().hex[:8]
schema_name = f"{BOT_SCHEMA}.gpt.{unique_suffix}"

print(f"Using schema: {schema_name}")

# Build GPT component YAML data
gpt_data_yaml = f"""kind: GptComponentMetadata
instructions: |-
{chr(10).join('  ' + line for line in instructions.split(chr(10)))}
responseInstructions:
gptCapabilities:
  webBrowsing: false
  codeInterpreter: false
aISettings:
  model:
    kind: CurrentModels
displayName: SMA4 Persona Workbench"""

component_data = {
    "name": "SMA4 Persona Workbench",
    "schemaname": schema_name,
    "componenttype": 15,
    "data": gpt_data_yaml,
    "parentbotid@odata.bind": f"/bots({BOT_ID})",
    "statecode": 0,
    "statuscode": 1
}

print("Creating GPT component...")
resp = requests.post(
    f"{client.api_base_url}/botcomponents",
    headers=client.headers,
    json=component_data
)

if resp.status_code in [200, 201, 204]:
    # Extract component ID
    if resp.text:
        result = resp.json()
        comp_id = result.get("botcomponentid")
    else:
        import re
        entity_id = resp.headers.get("OData-EntityId", "")
        match = re.search(r'botcomponents\(([^)]+)\)', entity_id)
        comp_id = match.group(1) if match else "unknown"
    
    print(f"GPT component created: {comp_id}")
    
    # Associate with bot
    assoc_data = {"@odata.id": f"{client.api_base_url}/botcomponents({comp_id})"}
    assoc_resp = requests.post(
        f"{client.api_base_url}/bots({BOT_ID})/bot_botcomponent/$ref",
        headers=client.headers,
        json=assoc_data
    )
    print(f"Association: {assoc_resp.status_code}")
    
    # Re-provision
    print("Re-provisioning agent...")
    prov_resp = requests.post(
        f"{client.api_base_url}/bots({BOT_ID})/Microsoft.Dynamics.CRM.PvaProvision",
        headers=client.headers,
        json={}
    )
    print(f"Provision: {prov_resp.status_code} {prov_resp.text[:200] if prov_resp.text else ''}")
    
    # Re-publish
    print("Re-publishing agent...")
    pub_resp = requests.post(
        f"{client.api_base_url}/bots({BOT_ID})/Microsoft.Dynamics.CRM.PvaPublish",
        headers=client.headers,
        json={}
    )
    print(f"Publish: {pub_resp.status_code} {pub_resp.text[:200] if pub_resp.text else ''}")
    
    # Verify
    print("\nVerifying components:")
    verify = requests.get(
        f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {BOT_ID}&$select=name,componenttype,schemaname",
        headers=client.headers
    )
    components = verify.json().get('value', [])
    type_counts = {}
    for c in components:
        ct = c.get('componenttype')
        type_counts[ct] = type_counts.get(ct, 0) + 1
        if ct == 15:
            print(f"  *** GPT FOUND: {c['name']} ({c['schemaname']})")
    print(f"Total: {len(components)} components - types: {type_counts}")
    
else:
    print(f"FAILED: {resp.status_code}")
    print(resp.text[:500])
