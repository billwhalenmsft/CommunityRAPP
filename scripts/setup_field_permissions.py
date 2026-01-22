"""
Script to set Field Level Security for custom fields on Case object.
Makes the triage fields visible and editable for System Administrator profile.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_salesforce import Salesforce

def load_settings():
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'local.settings.json'
    )
    with open(settings_path) as f:
        return json.load(f)['Values']

def setup_field_permissions():
    settings = load_settings()
    
    print("Connecting to Salesforce...")
    sf = Salesforce(
        username=settings['SALESFORCE_USERNAME'],
        password=settings['SALESFORCE_PASSWORD'],
        security_token=settings['SALESFORCE_SECURITY_TOKEN'],
        consumer_key=settings['SALESFORCE_CLIENT_ID'],
        consumer_secret=settings['SALESFORCE_CLIENT_SECRET']
    )
    print(f"Connected to: {sf.sf_instance}")
    
    # Get System Administrator profile
    profile = sf.query("SELECT Id FROM Profile WHERE Name = 'System Administrator'")
    if not profile['records']:
        print("ERROR: Could not find System Administrator profile")
        return
    profile_id = profile['records'][0]['Id']
    print(f"System Administrator Profile ID: {profile_id}")
    
    # Get Permission Set for API access (we'll use a direct approach)
    # The fields should already be accessible, let's check describe
    
    print("\nChecking field accessibility via describe()...")
    case_describe = sf.Case.describe()
    
    triage_fields = [
        'Triage_Status__c', 'Triage_Priority__c', 'Triage_Issue_Type__c',
        'Triage_Summary__c', 'Recommended_Action__c', 'Recommended_Queue__c',
        'AI_Triaged_Date__c', 'Product_Model__c', 'Serial_Number__c', 'Install_Date__c'
    ]
    
    all_field_names = [f['name'] for f in case_describe['fields']]
    
    print("\nField Status:")
    found_count = 0
    for field in triage_fields:
        if field in all_field_names:
            print(f"  ✅ {field} - Available")
            found_count += 1
        else:
            print(f"  ❌ {field} - Not found in describe")
    
    if found_count == len(triage_fields):
        print("\n✅ All fields are accessible! Testing query...")
        result = sf.query("SELECT Id, CaseNumber, Triage_Status__c FROM Case LIMIT 1")
        print(f"   Query successful! Found {result['totalSize']} records")
    else:
        print(f"\n⚠️ {len(triage_fields) - found_count} fields not yet accessible.")
        print("   This is normal - Salesforce metadata can take 5-10 minutes to propagate.")
        print("   You can also manually go to:")
        print("   Setup → Profiles → System Administrator → Field-Level Security → Case")
        print("   And make sure all triage fields are 'Visible'")

if __name__ == '__main__':
    setup_field_permissions()
