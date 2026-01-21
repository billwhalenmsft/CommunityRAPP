"""
Salesforce Connection Test Script
Run this after configuring your Salesforce credentials in local.settings.json

Usage:
    cd CommunityRAPP-main
    .venv\Scripts\activate
    python scripts/test_salesforce_connection.py
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment from local.settings.json
def load_local_settings():
    """Load settings from local.settings.json into environment."""
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'local.settings.json'
    )
    
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if value:  # Only set non-empty values
                    os.environ[key] = value
        print(f"✅ Loaded settings from {settings_path}")
    else:
        print(f"⚠️ No local.settings.json found at {settings_path}")

def test_connection():
    """Test Salesforce connection and run sample queries."""
    from utils.salesforce_client import (
        SalesforceConfig, 
        SalesforceClient,
        test_salesforce_connection
    )
    
    print("\n" + "="*60)
    print("SALESFORCE CONNECTION TEST")
    print("="*60)
    
    # Check configuration
    config = SalesforceConfig()
    
    print("\n📋 Configuration Status:")
    print(f"   Instance URL: {config.instance_url}")
    print(f"   API Version:  {config.api_version}")
    print(f"   Username:     {config.username or '(not set)'}")
    print(f"   Client ID:    {'✅ Set' if config.client_id else '❌ Not set'}")
    print(f"   Client Secret:{'✅ Set' if config.client_secret else '❌ Not set'}")
    print(f"   Password:     {'✅ Set' if config.password else '❌ Not set'}")
    print(f"   Security Token: {'✅ Set' if config.security_token else '❌ Not set'}")
    
    if not config.is_configured:
        print("\n❌ Salesforce credentials not fully configured.")
        print("   Please update local.settings.json with your credentials.")
        print("   See docs/SALESFORCE_SETUP_GUIDE.md for instructions.")
        return False
    
    # Test connection
    print("\n🔐 Testing Authentication...")
    result = test_salesforce_connection()
    
    if result['status'] == 'connected':
        print(f"✅ Connected to Salesforce!")
        print(f"   Instance: {result['instance_url']}")
        print(f"   API Version: {result['api_version']}")
        print(f"   Test Query: {result['test_query']}")
    else:
        print(f"❌ Connection failed: {result.get('message', 'Unknown error')}")
        return False
    
    # Run sample queries
    print("\n📊 Running Sample Queries...")
    client = SalesforceClient()
    client.authenticate()
    
    # Count cases
    case_count = client.query("SELECT COUNT() FROM Case")
    print(f"   Total Cases in Org: {case_count.get('totalSize', 'Error')}")
    
    # Get recent cases
    recent_cases = client.query("""
        SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate 
        FROM Case 
        ORDER BY CreatedDate DESC 
        LIMIT 5
    """)
    
    if recent_cases.get('records'):
        print(f"\n📋 Recent Cases ({len(recent_cases['records'])} found):")
        for case in recent_cases['records']:
            print(f"   [{case.get('CaseNumber')}] {case.get('Subject', 'No subject')[:50]}")
            print(f"       Status: {case.get('Status')} | Priority: {case.get('Priority')}")
    else:
        print("   No cases found in this org.")
    
    # Check for custom fields
    print("\n🔍 Checking Custom Fields on Case Object...")
    describe = client.describe_object('Case')
    custom_fields = [f['name'] for f in describe.get('fields', []) if f['name'].endswith('__c')]
    
    expected_fields = [
        'Triage_Status__c', 'Triage_Priority__c', 'Triage_Summary__c',
        'Recommended_Action__c', 'AI_Triaged_Date__c', 'Product_Model__c',
        'Serial_Number__c'
    ]
    
    found_fields = [f for f in expected_fields if f in custom_fields]
    missing_fields = [f for f in expected_fields if f not in custom_fields]
    
    if found_fields:
        print(f"   ✅ Found: {', '.join(found_fields)}")
    if missing_fields:
        print(f"   ⚠️ Missing: {', '.join(missing_fields)}")
        print("      (Create these fields for full triage functionality)")
    
    print("\n" + "="*60)
    print("✅ Salesforce connection test complete!")
    print("="*60)
    return True

def test_agents():
    """Test the Carrier agents with Salesforce."""
    print("\n" + "="*60)
    print("TESTING CARRIER AGENTS")
    print("="*60)
    
    from agents.carrier_sf_case_monitor_agent import CarrierSFCaseMonitorAgent
    from agents.carrier_sf_writer_agent import CarrierSFWriterAgent
    
    # Test Case Monitor
    print("\n🔍 Testing CarrierSFCaseMonitorAgent...")
    monitor = CarrierSFCaseMonitorAgent()
    print(f"   Mock mode: {monitor.config['use_mock_data']}")
    
    result = json.loads(monitor.perform(action="get_queue_summary"))
    print(f"   Status: {result.get('status')}")
    print(f"   Source: {result.get('source')}")
    
    if result.get('summary'):
        summary = result['summary']
        print(f"   New Cases: {summary.get('total_new', 0)}")
        print(f"   Aging Cases: {summary.get('total_aging', 0)}")
    
    # Test Case Writer (mock only for safety)
    print("\n✏️ Testing CarrierSFWriterAgent (mock mode)...")
    writer = CarrierSFWriterAgent()
    writer.config['use_mock_data'] = True  # Force mock for safety
    
    result = json.loads(writer.perform(
        action="update_case_triage",
        case_id="500xx000000TEST",
        triage_summary="Test triage summary",
        priority="Medium"
    ))
    print(f"   Status: {result.get('status')}")
    print(f"   Message: {result.get('message', 'N/A')}")
    
    print("\n✅ Agent tests complete!")

if __name__ == "__main__":
    # Load environment
    load_local_settings()
    
    # Run tests
    if test_connection():
        test_agents()
    else:
        print("\n⚠️ Fix Salesforce connection before testing agents.")
        print("   Agents will use mock data until connection is configured.")
