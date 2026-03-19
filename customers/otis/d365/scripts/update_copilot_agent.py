"""
Update an existing Copilot Studio agent with Otis content.
Use this AFTER creating a blank agent via the Copilot Studio UI.

This script:
1. Updates the GPT component with Otis instructions
2. Creates the 5 service topics
3. Associates everything properly
"""

import requests
import subprocess
import json
import sys

ORG_URL = 'https://orgecbce8ef.crm.dynamics.com'
API_BASE = f'{ORG_URL}/api/data/v9.2'

# Otis Service Copilot configuration
AGENT_INSTRUCTIONS = """You are an AI assistant helping Otis elevator service representatives.
Always prioritize safety - entrapment cases are highest priority.
Reference knowledge base articles when available.
For sales opportunities, warm transfer to the modernization team.
Track all commitments made to customers.

Key Priorities:
1. SAFETY FIRST - Any entrapment is urgent, dispatch immediately
2. Product expertise - Reference KB articles for troubleshooting  
3. Customer satisfaction - Be empathetic, acknowledge concerns
4. Sales awareness - Note upgrade/modernization opportunities

When handling cases:
- Check contract tier (Gold/Silver/Bronze) for SLA commitments
- Review maintenance history before suggesting dispatch
- Document all actions in D365 timeline
"""

TOPICS = [
    {
        "name": "Entrapment Response Protocol",
        "description": "Handle elevator entrapment emergencies",
        "trigger_phrases": ["entrapment", "stuck in elevator", "trapped", "emergency", "people stuck"]
    },
    {
        "name": "Door Issue Troubleshooting",
        "description": "Troubleshoot elevator door problems",
        "trigger_phrases": ["door issue", "doors won't close", "door malfunction", "door stuck", "door problem"]
    },
    {
        "name": "Billing and Contract Verification",
        "description": "Handle billing inquiries and contract verification",
        "trigger_phrases": ["billing", "invoice", "contract", "payment", "account balance"]
    },
    {
        "name": "Modernization and Sales Handoff",
        "description": "Identify upgrade opportunities and handoff to sales",
        "trigger_phrases": ["upgrade", "modernization", "new elevator", "replacement", "interested in"]
    },
    {
        "name": "Preventive Maintenance Coordination",
        "description": "Schedule and coordinate maintenance visits",
        "trigger_phrases": ["maintenance", "PM visit", "inspection", "scheduled service", "preventive"]
    }
]

def get_token():
    result = subprocess.run(
        f'az account get-access-token --resource {ORG_URL} --query accessToken -o tsv',
        capture_output=True, text=True, shell=True
    )
    return result.stdout.strip()

def get_headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Prefer': 'return=representation'
    }

def find_bot_by_name(headers, name):
    """Find a bot by name."""
    r = requests.get(
        f"{API_BASE}/bots?$filter=name eq '{name}'&$select=botid,schemaname,name",
        headers=headers
    )
    bots = r.json().get('value', [])
    return bots[0] if bots else None

def update_gpt_component(headers, bot_id, bot_schema, instructions):
    """Update or create GPT component with instructions."""
    gpt_schema = f"{bot_schema}.gpt.default"
    
    # Check if GPT component exists
    r = requests.get(
        f"{API_BASE}/botcomponents?$filter=schemaname eq '{gpt_schema}'&$select=botcomponentid",
        headers=headers
    )
    components = r.json().get('value', [])
    
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
displayName: Instructions
"""
    
    if components:
        # Update existing
        comp_id = components[0]['botcomponentid']
        r = requests.patch(
            f"{API_BASE}/botcomponents({comp_id})",
            headers=headers,
            json={"data": gpt_data_yaml}
        )
        if r.status_code in [200, 204]:
            print(f"✓ Updated GPT component: {comp_id}")
            return comp_id
        else:
            print(f"✗ Failed to update GPT: {r.text}")
            return None
    else:
        # Create new
        component_data = {
            "name": "Instructions",
            "schemaname": gpt_schema,
            "componenttype": 15,
            "data": gpt_data_yaml,
            f"parentbotid@odata.bind": f"/bots({bot_id})",
            "statecode": 0,
            "statuscode": 1
        }
        r = requests.post(f"{API_BASE}/botcomponents", headers=headers, json=component_data)
        if r.status_code in [200, 201]:
            comp_id = r.json().get('botcomponentid')
            # Associate
            requests.post(
                f"{API_BASE}/bots({bot_id})/bot_botcomponent/$ref",
                headers=headers,
                json={"@odata.id": f"{API_BASE}/botcomponents({comp_id})"}
            )
            print(f"✓ Created GPT component: {comp_id}")
            return comp_id
        else:
            print(f"✗ Failed to create GPT: {r.text}")
            return None

def create_topic(headers, bot_id, topic_def):
    """Create a topic for the bot."""
    schema = topic_def['name'].lower().replace(' ', '_').replace('-', '_')
    
    # Check if topic exists
    r = requests.get(
        f"{API_BASE}/botcomponents?$filter=contains(name,'{topic_def['name']}') and componenttype eq 9&$select=botcomponentid",
        headers=headers
    )
    existing = r.json().get('value', [])
    if existing:
        print(f"  Topic already exists: {topic_def['name']}")
        return existing[0]['botcomponentid']
    
    topic_content = {
        "kind": "AdaptiveDialog",
        "id": f"topic_{schema}",
        "displayName": topic_def['name'],
        "description": topic_def['description'],
        "triggers": [{
            "kind": "OnRecognizedIntent",
            "intent": schema,
            "triggerQueries": topic_def['trigger_phrases']
        }],
        "actions": [{
            "kind": "SendMessage",
            "message": f"I can help with {topic_def['name'].lower()}. Let me look into this for you."
        }]
    }
    
    component_data = {
        "name": topic_def['name'],
        "schemaname": f"topic_{schema}",
        "description": topic_def['description'],
        "componenttype": 9,
        "content": json.dumps(topic_content),
        f"parentbotid@odata.bind": f"/bots({bot_id})",
        "statecode": 0,
        "statuscode": 1
    }
    
    r = requests.post(f"{API_BASE}/botcomponents", headers=headers, json=component_data)
    if r.status_code in [200, 201]:
        comp_id = r.json().get('botcomponentid')
        # Associate
        requests.post(
            f"{API_BASE}/bots({bot_id})/bot_botcomponent/$ref",
            headers=headers,
            json={"@odata.id": f"{API_BASE}/botcomponents({comp_id})"}
        )
        print(f"✓ Created topic: {topic_def['name']}")
        return comp_id
    else:
        print(f"✗ Failed to create topic {topic_def['name']}: {r.status_code}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_copilot_agent.py <bot_name>")
        print("Example: python update_copilot_agent.py 'My New Agent'")
        print("\nThis updates an existing agent created via Copilot Studio UI.")
        return
    
    bot_name = sys.argv[1]
    
    print("Getting access token...")
    token = get_token()
    headers = get_headers(token)
    
    print(f"\nLooking for bot: {bot_name}")
    bot = find_bot_by_name(headers, bot_name)
    
    if not bot:
        print(f"✗ Bot not found: {bot_name}")
        print("\nAvailable bots:")
        r = requests.get(f"{API_BASE}/bots?$select=name&$top=10", headers=headers)
        for b in r.json().get('value', []):
            print(f"  - {b.get('name')}")
        return
    
    bot_id = bot['botid']
    bot_schema = bot['schemaname']
    print(f"✓ Found bot: {bot['name']} ({bot_id})")
    
    print("\nUpdating GPT instructions...")
    update_gpt_component(headers, bot_id, bot_schema, AGENT_INSTRUCTIONS)
    
    print("\nCreating topics...")
    for topic in TOPICS:
        create_topic(headers, bot_id, topic)
    
    print("\n" + "="*50)
    print("DONE! Now go to Copilot Studio and:")
    print("1. Open your agent and review the changes")
    print("2. Test in the Test pane")
    print("3. Publish when ready")

if __name__ == "__main__":
    main()
