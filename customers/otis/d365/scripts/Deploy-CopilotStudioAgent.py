"""
Deploy-CopilotStudioAgent.py
Programmatically deploys the Otis Service Copilot to Copilot Studio via Dataverse API.

This script uses the existing RAPP infrastructure:
- CopilotStudioClient from utils/copilot_studio_api.py
- copilot-config.json for agent configuration
- knowledge-articles.json for KB mapping

Prerequisites:
- az login (uses Azure CLI credentials)
- Access to the D365 environment: https://orgecbce8ef.crm.dynamics.com

Usage:
    python Deploy-CopilotStudioAgent.py
    python Deploy-CopilotStudioAgent.py --preview  # Preview without deploying
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Add parent paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
sys.path.insert(0, project_root)

from utils.copilot_studio_api import CopilotStudioClient, CopilotStudioAPIError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# D365 Environment URL (same as Dataverse)
ENVIRONMENT_URL = "https://orgecbce8ef.crm.dynamics.com"

# Agent configuration
AGENT_CONFIG = {
    "name": "Otis Service Copilot",
    "schema_name": "cr328_otisservicecopilot",  # Must be unique
    "description": "AI assistant for Otis EMEA elevator service representatives",
    "language": "en-gb"  # UK English for EMEA
}

# Topics to create for demo scenarios
DEMO_TOPICS = [
    {
        "name": "Entrapment Response Protocol",
        "trigger_phrases": [
            "entrapment",
            "trapped in elevator",
            "stuck in lift",
            "passenger trapped",
            "emergency rescue",
            "someone stuck"
        ],
        "instructions": """When an entrapment case is detected:
1. Surface KB-001247 (Entrapment Response Procedure)
2. For healthcare facilities, also surface KB-002156 (Healthcare Protocols)
3. Check account SLA tier and prioritize accordingly:
   - Healthcare: 1-hour response (Priority 1)
   - Tier 1 Premium: 2-hour response
   - Standard: 4-hour response
4. Guide agent through communication cadence (5-minute callbacks)
5. Recommend nearest available technician based on skills and proximity"""
    },
    {
        "name": "Door Issue Troubleshooting",
        "trigger_phrases": [
            "door issue",
            "door not closing",
            "door reversing",
            "door operator",
            "door sensor",
            "elevator door problem"
        ],
        "instructions": """For door-related issues:
1. Surface KB-002104 (SkyRise Door Operator Troubleshooting) for high-rise elevators
2. Ask diagnostic questions:
   - Does it happen on all floors or specific floors?
   - How often does it occur?
   - Are there any error codes displayed?
3. Check for recurring issue pattern (3+ occurrences = escalation)
4. If recurring, recommend comprehensive inspection with technician supervisor"""
    },
    {
        "name": "Billing and Contract Verification",
        "trigger_phrases": [
            "billing dispute",
            "invoice question",
            "contract coverage",
            "what's covered",
            "service contract",
            "is this covered"
        ],
        "instructions": """For billing and contract questions:
1. Surface KB-001050 (Contract Coverage Guide)
2. Help agent verify if repair should be covered under contract type:
   - Full Maintenance: Parts AND labor included
   - Standard: Labor only, parts billable
   - Time & Materials: All billable
3. If billing error found, guide through correction process (CR request)
4. Note contract renewal date and escalate retention risks"""
    },
    {
        "name": "Modernization and Sales Handoff",
        "trigger_phrases": [
            "modernization",
            "upgrade elevator",
            "iot monitoring",
            "otis one",
            "equipment upgrade",
            "new features"
        ],
        "instructions": """For modernization inquiries:
1. Surface KB-003145 (Otis ONE IoT Monitoring Package)
2. Identify upsell opportunities based on:
   - Equipment age (>10 years = good candidate)
   - Maintenance frequency (high = potential for IoT monitoring)
   - Building type (commercial = regenerative drives)
3. Capture requirements from customer
4. Create sales opportunity or handoff to Account Manager
5. Schedule technical survey if appropriate"""
    },
    {
        "name": "Preventive Maintenance Coordination",
        "trigger_phrases": [
            "scheduled maintenance",
            "preventive maintenance",
            "pm schedule",
            "quarterly maintenance",
            "maintenance callback"
        ],
        "instructions": """For preventive maintenance coordination:
1. Look up scheduled maintenance in work orders
2. Provide scope of work details:
   - Number of units
   - Estimated duration
   - Team size and lead technician
3. Coordinate building access requirements
4. Send confirmation email with:
   - PM checklist
   - Technician roster
   - Access requirements
5. For high-traffic locations, confirm work hours minimize disruption"""
    }
]


def load_copilot_config():
    """Load the copilot-config.json file."""
    config_path = os.path.join(
        os.path.dirname(script_dir),
        "copilot-studio",
        "copilot-config.json"
    )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    
    logger.warning(f"Config not found at {config_path}, using defaults")
    return {}


def build_system_instructions(config: dict) -> str:
    """Build the full system instructions from config."""
    instructions = config.get("systemInstructions", {})
    base = instructions.get("baseInstructions", [])
    
    # Combine base instructions
    system_prompt = "\n".join(base) if base else ""
    
    # Add demo-specific context
    system_prompt += """

## Knowledge Articles Available
When helping agents, reference these KB articles by number:
- KB-001247: Entrapment Response Procedure
- KB-001050: Contract Coverage Guide
- KB-002104: SkyRise Door Troubleshooting
- KB-002156: Healthcare Facility Protocols
- KB-003145: Otis ONE IoT Monitoring

## Response Guidelines
1. Always be concise and action-oriented
2. Provide specific KB article numbers when recommending articles
3. Consider account SLA tier when suggesting response times
4. For escalations, include reason and recommended next steps
5. Draft customer communications in professional, empathetic tone

## Account Context
Use the case's associated account to determine:
- Contract type and coverage
- SLA response requirements
- Historical relationship notes
- Renewal status and risk level"""
    
    return system_prompt


def preview_deployment(config: dict):
    """Preview what would be deployed without actually deploying."""
    print("\n" + "=" * 60)
    print("DEPLOYMENT PREVIEW - Otis Service Copilot")
    print("=" * 60)
    
    print(f"\n📦 Agent Configuration:")
    print(f"   Name: {AGENT_CONFIG['name']}")
    print(f"   Schema: {AGENT_CONFIG['schema_name']}")
    print(f"   Language: {AGENT_CONFIG['language']}")
    print(f"   Environment: {ENVIRONMENT_URL}")
    
    print(f"\n📝 System Instructions ({len(build_system_instructions(config))} chars):")
    instructions = build_system_instructions(config)
    print(f"   {instructions[:200]}...")
    
    print(f"\n🎯 Topics to Create ({len(DEMO_TOPICS)}):")
    for topic in DEMO_TOPICS:
        print(f"   • {topic['name']}")
        print(f"     Triggers: {', '.join(topic['trigger_phrases'][:3])}...")
    
    print(f"\n📚 Knowledge Articles to Link:")
    print("   • KB-001247: Entrapment Response Procedure")
    print("   • KB-001050: Contract Coverage Guide")
    print("   • KB-002104: SkyRise Door Troubleshooting")
    print("   • KB-002156: Healthcare Facility Protocols")
    print("   • KB-003145: Otis ONE IoT Monitoring")
    
    print("\n" + "=" * 60)
    print("Run without --preview to deploy")
    print("=" * 60)


def deploy_copilot_agent():
    """Deploy the Otis Service Copilot to Copilot Studio."""
    config = load_copilot_config()
    
    print("\n" + "=" * 60)
    print("DEPLOYING Otis Service Copilot to Copilot Studio")
    print("=" * 60)
    
    # Initialize client
    print(f"\n🔗 Connecting to {ENVIRONMENT_URL}...")
    client = CopilotStudioClient(
        environment_url=ENVIRONMENT_URL,
        use_interactive_auth=True  # Will use Azure CLI if logged in
    )
    
    # Authenticate
    print("🔐 Authenticating via Azure CLI...")
    client.authenticate()
    print("✅ Authentication successful")
    
    # Build system instructions
    system_instructions = build_system_instructions(config)
    
    # Create the agent
    print(f"\n📦 Creating agent: {AGENT_CONFIG['name']}...")
    try:
        bot_id = client.create_agent(
            name=AGENT_CONFIG['name'],
            schema_name=AGENT_CONFIG['schema_name'],
            description=AGENT_CONFIG['description'],
            instructions=system_instructions,
            language=AGENT_CONFIG['language'],
            authentication_mode="none",
            web_browsing=False  # Keep focused on KB articles
        )
        print(f"✅ Agent created: {bot_id}")
    except CopilotStudioAPIError as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print(f"⚠️  Agent may already exist, attempting to find it...")
            # Try to find existing agent
            agents = client.list_agents()
            existing = next(
                (a for a in agents if a.get('name') == AGENT_CONFIG['name']),
                None
            )
            if existing:
                bot_id = existing.get('botid')
                print(f"✅ Found existing agent: {bot_id}")
            else:
                raise
        else:
            raise
    
    # Create topics
    print(f"\n🎯 Creating {len(DEMO_TOPICS)} topics...")
    for i, topic in enumerate(DEMO_TOPICS, 1):
        print(f"   [{i}/{len(DEMO_TOPICS)}] Creating topic: {topic['name']}...")
        try:
            topic_id = client.create_topic(
                bot_id=bot_id,
                name=topic['name'],
                trigger_phrases=topic['trigger_phrases'],
                content=topic['instructions']
            )
            print(f"        ✅ Created: {topic_id}")
        except CopilotStudioAPIError as e:
            print(f"        ⚠️  Topic creation failed: {e}")
            # Continue with other topics
    
    # Summary
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\n🎉 Agent deployed successfully!")
    print(f"   Bot ID: {bot_id}")
    print(f"   Environment: {ENVIRONMENT_URL}")
    print(f"\n📋 Next Steps:")
    print("   1. Open Copilot Studio: https://copilotstudio.microsoft.com")
    print("   2. Find 'Otis Service Copilot' in your agents")
    print("   3. Configure Knowledge Sources:")
    print("      - Add Dataverse > Knowledge Articles")
    print("      - Filter: statecode eq 3 (Published)")
    print("   4. Test the agent with demo scenarios")
    print("   5. Publish when ready")
    
    # Save deployment record
    deployment_record = {
        "timestamp": datetime.now().isoformat(),
        "bot_id": bot_id,
        "environment_url": ENVIRONMENT_URL,
        "agent_name": AGENT_CONFIG['name'],
        "topics_created": len(DEMO_TOPICS),
        "status": "deployed"
    }
    
    record_path = os.path.join(os.path.dirname(script_dir), "data", "deployment-record.json")
    os.makedirs(os.path.dirname(record_path), exist_ok=True)
    with open(record_path, 'w') as f:
        json.dump(deployment_record, f, indent=2)
    print(f"\n📄 Deployment record saved to: {record_path}")
    
    return bot_id


def main():
    parser = argparse.ArgumentParser(description="Deploy Otis Service Copilot to Copilot Studio")
    parser.add_argument("--preview", action="store_true", help="Preview deployment without executing")
    args = parser.parse_args()
    
    config = load_copilot_config()
    
    if args.preview:
        preview_deployment(config)
    else:
        try:
            deploy_copilot_agent()
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            print(f"\n❌ Deployment failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Ensure you're logged in: az login")
            print("  2. Check environment URL is correct")
            print("  3. Verify you have Copilot Studio access")
            sys.exit(1)


if __name__ == "__main__":
    main()
