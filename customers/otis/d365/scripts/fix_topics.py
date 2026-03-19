"""
Fix Otis Service topics - delete malformed ones and recreate with proper YAML format.
"""
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
    'OData-Version': '4.0',
    'Prefer': 'return=representation'
}

api = f'{org_url}/api/data/v9.2'
bot_id = '87f54269-3321-f111-8341-6045bda80a72'

# Our service topics with proper YAML format
TOPICS = [
    {
        "name": "Entrapment Response",
        "schemaname": "cr328_entrapment_response",
        "trigger_phrases": ["entrapment", "stuck in elevator", "trapped", "emergency", "people stuck", "passenger stuck"],
        "response": "I understand this is an emergency. Let me help you with the entrapment response protocol. First, can you confirm the building address and elevator ID?",
        "description": "Handle elevator entrapment emergencies with priority dispatch"
    },
    {
        "name": "Door Troubleshooting",
        "schemaname": "cr328_door_troubleshooting",
        "trigger_phrases": ["door issue", "doors won't close", "door malfunction", "door stuck", "door problem", "door not working"],
        "response": "I can help troubleshoot the door issue. Can you describe what's happening with the elevator doors? Are they not opening, not closing, or making unusual sounds?",
        "description": "Troubleshoot elevator door problems"
    },
    {
        "name": "Billing Verification",
        "schemaname": "cr328_billing_verification",
        "trigger_phrases": ["billing", "invoice", "contract", "payment", "account balance", "billing question"],
        "response": "I can help with billing and contract questions. Can you provide the account number or building address so I can look up the contract details?",
        "description": "Handle billing inquiries and contract verification"
    },
    {
        "name": "Modernization Handoff",
        "schemaname": "cr328_modernization_handoff",
        "trigger_phrases": ["upgrade", "modernization", "new elevator", "replacement", "interested in upgrading"],
        "response": "Thank you for your interest in elevator modernization! Let me connect you with our sales team who can discuss upgrade options for your building.",
        "description": "Identify upgrade opportunities and handoff to sales"
    },
    {
        "name": "Maintenance Scheduling",
        "schemaname": "cr328_maintenance_scheduling",
        "trigger_phrases": ["maintenance", "PM visit", "inspection", "scheduled service", "preventive maintenance", "service visit"],
        "response": "I can help coordinate maintenance scheduling. Can you provide the building address and preferred date/time for the service visit?",
        "description": "Schedule and coordinate maintenance visits"
    }
]

def build_topic_yaml(topic):
    """Build proper YAML format for Copilot Studio topic."""
    triggers = "\n".join(f"      - {phrase}" for phrase in topic['trigger_phrases'])
    
    return f"""kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: {topic['name']}
    includeInOnSelectIntent: true
    triggerQueries:
{triggers}

  actions:
    - kind: SendActivity
      id: sendMessage_main
      activity:
        text:
          - "{topic['response']}"
"""

# Step 1: Delete old malformed topics
print("=== Deleting old malformed topics ===")
old_topics = [
    '7593c781-3321-f111-8341-6045bda80a72',  # Entrapment
    '8393c781-3321-f111-8341-6045bda80a72',  # Door Issue
    '7daf2487-3321-f111-8342-7ced8d18c8d7',  # Billing
    'aeaf2487-3321-f111-8342-7ced8d18c8d7',  # Modernization
    'd7af2487-3321-f111-8342-7ced8d18c8d7',  # Preventive
]

for topic_id in old_topics:
    r = requests.delete(f"{api}/botcomponents({topic_id})", headers=headers)
    if r.status_code == 204:
        print(f"  Deleted: {topic_id}")
    elif r.status_code == 404:
        print(f"  Not found (already deleted): {topic_id}")
    else:
        print(f"  Error deleting {topic_id}: {r.status_code}")

# Step 2: Create new topics with proper YAML format
print("\n=== Creating topics with proper YAML format ===")
created_topics = []

for topic in TOPICS:
    yaml_content = build_topic_yaml(topic)
    
    component_data = {
        "name": topic['name'],
        "schemaname": topic['schemaname'],
        "description": topic['description'],
        "componenttype": 9,  # topic_v2
        "data": yaml_content,  # YAML goes in 'data', not 'content'!
        f"parentbotid@odata.bind": f"/bots({bot_id})",
        "statecode": 0,
        "statuscode": 1
    }
    
    r = requests.post(f"{api}/botcomponents", headers=headers, json=component_data)
    
    if r.status_code in [200, 201]:
        result = r.json()
        comp_id = result.get('botcomponentid')
        print(f"  Created: {topic['name']} ({comp_id})")
        
        # Associate with bot
        assoc_data = {"@odata.id": f"{api}/botcomponents({comp_id})"}
        r2 = requests.post(f"{api}/bots({bot_id})/bot_botcomponent/$ref", headers=headers, json=assoc_data)
        if r2.status_code in [200, 204]:
            print(f"    Associated with bot")
        else:
            print(f"    Warning: Association failed: {r2.status_code}")
        
        created_topics.append(comp_id)
    else:
        print(f"  FAILED: {topic['name']} - {r.status_code}: {r.text[:200]}")

print(f"\n=== DONE ===")
print(f"Created {len(created_topics)} topics")
print("\nNow refresh the Topics page in Copilot Studio to see the new topics!")
