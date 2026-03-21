"""Fix the GPT defaultSchemaName mismatch in bot configuration."""
import sys, os, json, time, requests
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
correct_gpt_schema = 'rapp_SMA4_Persona_Workbench_20260320133321.gpt.075aca5c'

# Get current config
bot = client.get_agent(bot_id)
config_str = bot.get('configuration', '{}')
cfg = json.loads(config_str) if isinstance(config_str, str) else config_str

print(f"Current config keys: {list(cfg.keys())}")
old_gpt = cfg.get('gPTSettings', {}).get('defaultSchemaName', '(missing)')
print(f"Old defaultSchemaName: {old_gpt}")

# Ensure gPTSettings exists and fix
if 'gPTSettings' not in cfg:
    cfg['gPTSettings'] = {"$kind": "GPTSettings"}

cfg['gPTSettings']['defaultSchemaName'] = correct_gpt_schema
print(f"New defaultSchemaName: {correct_gpt_schema}")

# Update bot
resp = requests.patch(
    f"{client.api_base_url}/bots({bot_id})",
    headers=client.headers,
    json={"configuration": json.dumps(cfg)}
)
print(f"Update status: {resp.status_code}")

if resp.status_code in [200, 204]:
    print("Configuration updated!")
    
    # Re-provision
    print("Re-provisioning...")
    prov = requests.post(
        f"{client.api_base_url}/bots({bot_id})/Microsoft.Dynamics.CRM.PvaProvision",
        headers=client.headers, json={}
    )
    print(f"Provision: {prov.status_code}")
    
    time.sleep(5)
    
    # Re-publish
    print("Re-publishing...")
    pub = requests.post(
        f"{client.api_base_url}/bots({bot_id})/Microsoft.Dynamics.CRM.PvaPublish",
        headers=client.headers, json={}
    )
    print(f"Publish: {pub.status_code}")
    
    # Verify
    bot2 = client.get_agent(bot_id)
    cfg2 = json.loads(bot2.get('configuration', '{}'))
    final = cfg2.get('gPTSettings', {}).get('defaultSchemaName', '')
    print(f"\nVerified defaultSchemaName: {final}")
    if final == correct_gpt_schema:
        print("SUCCESS - schemas now match!")
    else:
        print(f"WARNING - still mismatched: expected {correct_gpt_schema}")
else:
    print(f"Error: {resp.text[:500]}")
