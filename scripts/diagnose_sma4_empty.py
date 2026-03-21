"""Diagnose why SMA4 agent appears empty in Copilot Studio."""
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

# Get ALL component details
resp = requests.get(
    f"{client.api_base_url}/botcomponents?$filter=_parentbotid_value eq {bot_id}&$select=name,componenttype,schemaname,data,content",
    headers=client.headers
)
print("=== COMPONENTS ===")
for c in resp.json().get('value', []):
    ct = c.get('componenttype')
    name = c.get('name', '')
    schema = c.get('schemaname', '')
    data = c.get('data') or ''
    content = c.get('content') or ''
    print(f"type={ct:>2}  data={len(data):>6}  content={len(content):>6}  name={name}")
    if ct == 15:
        print(f"  GPT schema: {schema}")
        if data:
            print(f"  GPT data preview ({len(data)} chars):")
            for line in data.split('\n')[:10]:
                print(f"    {line}")
        else:
            print("  *** GPT DATA IS EMPTY! ***")
    if ct == 10:
        print(f"  Instr schema: {schema}")
        if content:
            print(f"  Content preview ({len(content)} chars): {content[:200]}")
        else:
            print(f"  Content is empty. Data ({len(data)} chars): {data[:200]}")

# Check bot configuration
print("\n=== BOT CONFIGURATION ===")
bot = requests.get(
    f"{client.api_base_url}/bots({bot_id})?$select=name,configuration,schemaname",
    headers=client.headers
)
b = bot.json()
print(f"Bot name: {b.get('name')}")
print(f"Bot schema: {b.get('schemaname')}")
config_data = b.get('configuration', '')
if config_data:
    cfg = json.loads(config_data)
    gpt_settings = cfg.get('gPTSettings', {})
    ai_settings = cfg.get('aISettings', {})
    settings = cfg.get('settings', {})
    print(f"gPTSettings: {json.dumps(gpt_settings)}")
    print(f"aISettings.useModelKnowledge: {ai_settings.get('useModelKnowledge')}")
    print(f"aISettings.generativeAnswersEnabled: {ai_settings.get('generativeAnswersEnabled')}")
    print(f"settings.orchestrationType: {settings.get('orchestrationType')}")
    
    # Check if GPT defaultSchemaName matches actual GPT component
    default_schema = gpt_settings.get('defaultSchemaName', '')
    print(f"\nGPT defaultSchemaName in config: {default_schema}")
    
    # Find actual GPT component schema
    for c in resp.json().get('value', []):
        if c.get('componenttype') == 15:
            actual_schema = c.get('schemaname', '')
            print(f"Actual GPT component schema: {actual_schema}")
            if default_schema != actual_schema:
                print("*** MISMATCH! Config references different schema than actual GPT component! ***")
            else:
                print("MATCH - schemas align")
