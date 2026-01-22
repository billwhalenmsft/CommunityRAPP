"""
Full End-to-End Triage Flow Test
Tests the complete Carrier Case Triage workflow with live Salesforce data

Usage:
    cd CommunityRAPP-main
    .venv\\Scripts\\activate
    python scripts/test_full_triage_flow.py
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
                if value:
                    os.environ[key] = value
        print(f"✅ Loaded settings from {settings_path}")


def run_full_triage_test():
    """Run complete triage flow on a real Salesforce case."""
    from utils.salesforce_client import get_salesforce_client
    
    print("\n" + "="*70)
    print("CARRIER CASE TRIAGE - FULL END-TO-END TEST")
    print("="*70)
    
    # Step 1: Connect to Salesforce
    print("\n📡 Step 1: Connecting to Salesforce...")
    sf = get_salesforce_client()
    if not sf:
        print("❌ Failed to connect to Salesforce")
        return False
    
    # Ensure authenticated
    sf._ensure_authenticated()
    print(f"   ✅ Connected to {sf.instance_url}")
    
    # Step 2: Find an open case to triage
    print("\n🔍 Step 2: Finding open cases to triage...")
    query = """
        SELECT Id, CaseNumber, Subject, Description, Status, Priority,
               ContactId, AccountId, CreatedDate, Type,
               Triage_Status__c, Triage_Priority__c, Triage_Summary__c
        FROM Case 
        WHERE Status != 'Closed'
        AND (Triage_Status__c = null OR Triage_Status__c = '')
        ORDER BY CreatedDate DESC
        LIMIT 5
    """
    
    try:
        result = sf.query(query)
        cases = result.get('records', [])
        print(f"   Found {len(cases)} cases needing triage")
        
        if not cases:
            # Try to get any open case
            query2 = """
                SELECT Id, CaseNumber, Subject, Description, Status, Priority,
                       ContactId, AccountId, CreatedDate, Type,
                       Triage_Status__c, Triage_Priority__c, Triage_Summary__c
                FROM Case 
                WHERE Status != 'Closed'
                ORDER BY CreatedDate DESC
                LIMIT 5
            """
            result = sf.query(query2)
            cases = result.get('records', [])
            print(f"   (Expanded search found {len(cases)} open cases)")
        
        if not cases:
            print("   ⚠️ No open cases found. Creating a test case...")
            # Create a test case
            new_case = sf.Case.create({
                'Subject': 'Test Case - Generator Won\'t Start',
                'Description': 'My Carrier generator model 7500 (serial XYZ123) won\'t start after a power outage. I\'ve tried resetting the breaker but it still shows an error code E05.',
                'Status': 'New',
                'Priority': 'Medium',
                'Origin': 'Web'
            })
            test_case_id = new_case['id']
            result = sf.query(f"SELECT Id, CaseNumber, Subject, Description, Status, Priority FROM Case WHERE Id = '{test_case_id}'")
            cases = result.get('records', [])
            print(f"   ✅ Created test case: {cases[0]['CaseNumber']}")
            
    except Exception as e:
        print(f"   ❌ Error querying cases: {e}")
        return False
    
    # Step 3: Display cases available for triage
    print("\n📋 Step 3: Cases available for triage:")
    for i, case in enumerate(cases):
        subject = (case.get('Subject') or '(no subject)')[:50]
        print(f"   {i+1}. [{case['CaseNumber']}] {subject}")
        print(f"      Status: {case['Status']} | Priority: {case['Priority']}")
        if case.get('Description'):
            desc_preview = (case.get('Description') or '')[:100].replace('\n', ' ')
            print(f"      Description: {desc_preview}...")
    
    # Step 4: Triage the first case using the orchestrator
    test_case = cases[0]
    print(f"\n🤖 Step 4: Triaging case {test_case['CaseNumber']} using Orchestrator...")
    
    # Import and use the orchestrator agent
    from agents.carrier_case_triage_orchestrator_agent import CarrierCaseTriageOrchestratorAgent
    
    orchestrator = CarrierCaseTriageOrchestratorAgent()
    # Disable mock mode for live Salesforce
    orchestrator.monitor_agent.config['use_mock_data'] = False
    orchestrator.writer_agent.config['use_mock_data'] = False
    
    print(f"   Input:")
    print(f"   - Case ID: {test_case['Id']}")
    print(f"   - Case Number: {test_case['CaseNumber']}")
    print(f"   - Subject: {test_case.get('Subject', 'N/A')}")
    
    # Execute full triage workflow
    triage_result = json.loads(orchestrator.perform(
        action="triage_single_case",
        case_id=test_case['Id'],
        write_to_sf=True
    ))
    
    print(f"\n   🎯 Orchestrator Result:")
    print(f"   - Status: {triage_result.get('status')}")
    print(f"   - Execution Time: {triage_result.get('execution_time_seconds', 'N/A')}s")
    
    if triage_result.get('triage_result'):
        tr = triage_result['triage_result']
        print(f"\n   Analysis:")
        if tr.get('analysis'):
            print(f"   - Issue Type: {tr['analysis'].get('issue_type', 'N/A')}")
            print(f"   - Urgency: {tr['analysis'].get('urgency', 'N/A')}")
            print(f"   - Sentiment: {tr['analysis'].get('sentiment', 'N/A')}")
        
        print(f"\n   Triage Decision:")
        if tr.get('triage'):
            print(f"   - Priority: {tr['triage'].get('priority', 'N/A')}")
            print(f"   - Queue: {tr['triage'].get('queue', 'N/A')}")
            action = tr['triage'].get('recommended_action') or 'N/A'
            print(f"   - Action: {action[:80]}...")
    
    if triage_result.get('workflow_log'):
        print(f"\n   Workflow Steps:")
        for step in triage_result['workflow_log']:
            status = step.get('result', step.get('reason', 'N/A'))
            print(f"   - Step {step['step']}: {step['agent']} → {status}")
    
    # Step 5: Verify the Salesforce update
    print(f"\n🔄 Step 5: Verifying Salesforce update...")
    
    verify_query = f"""
        SELECT Id, CaseNumber, Subject, 
               Triage_Status__c, Triage_Priority__c, Triage_Issue_Type__c,
               Triage_Summary__c, Recommended_Action__c, AI_Triaged_Date__c
        FROM Case 
        WHERE Id = '{test_case['Id']}'
    """
    
    try:
        verify_result = sf.query(verify_query)
        if verify_result.get('records'):
            updated_case = verify_result['records'][0]
            print(f"   Case {updated_case['CaseNumber']} verified:")
            print(f"   - Triage_Status__c: {updated_case.get('Triage_Status__c', 'N/A')}")
            print(f"   - Triage_Priority__c: {updated_case.get('Triage_Priority__c', 'N/A')}")
            print(f"   - Triage_Issue_Type__c: {updated_case.get('Triage_Issue_Type__c', 'N/A')}")
            print(f"   - AI_Triaged_Date__c: {updated_case.get('AI_Triaged_Date__c', 'N/A')}")
            summary = updated_case.get('Triage_Summary__c', 'N/A')
            if summary and summary != 'N/A':
                print(f"   - Summary: {summary[:100]}...")
    except Exception as e:
        print(f"   ⚠️ Verification query failed: {e}")
    
    print("\n" + "="*70)
    print("✅ FULL TRIAGE TEST COMPLETE!")
    print("="*70)
    
    return True


if __name__ == "__main__":
    load_local_settings()
    run_full_triage_test()
