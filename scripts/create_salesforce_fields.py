"""
Script to create custom fields on Case object in Salesforce.
Uses the Tooling API to create CustomField metadata.
"""
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_salesforce import Salesforce

def load_settings():
    """Load settings from local.settings.json"""
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'local.settings.json'
    )
    with open(settings_path) as f:
        return json.load(f)['Values']

def create_custom_fields():
    """Create custom fields on the Case object."""
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
    
    # Get Case object ID for field creation
    case_obj = sf.toolingexecute(f"query/?q=SELECT+Id+FROM+EntityDefinition+WHERE+QualifiedApiName='Case'")
    if not case_obj.get('records'):
        print("ERROR: Could not find Case object")
        return
    
    case_entity_id = case_obj['records'][0]['Id']
    print(f"Case Entity ID: {case_entity_id}")
    
    # Define custom fields to create
    fields = [
        {
            'FullName': 'Case.Triage_Status__c',
            'Metadata': {
                'label': 'Triage Status',
                'type': 'Text',
                'length': 50,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Triage_Priority__c',
            'Metadata': {
                'label': 'Triage Priority',
                'type': 'Text',
                'length': 20,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Triage_Issue_Type__c',
            'Metadata': {
                'label': 'Triage Issue Type',
                'type': 'Text',
                'length': 100,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Triage_Summary__c',
            'Metadata': {
                'label': 'Triage Summary',
                'type': 'LongTextArea',
                'length': 32000,
                'visibleLines': 5,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Recommended_Action__c',
            'Metadata': {
                'label': 'Recommended Action',
                'type': 'TextArea',
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Recommended_Queue__c',
            'Metadata': {
                'label': 'Recommended Queue',
                'type': 'Text',
                'length': 255,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.AI_Triaged_Date__c',
            'Metadata': {
                'label': 'AI Triaged Date',
                'type': 'DateTime',
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Product_Model__c',
            'Metadata': {
                'label': 'Product Model',
                'type': 'Text',
                'length': 100,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Serial_Number__c',
            'Metadata': {
                'label': 'Serial Number',
                'type': 'Text',
                'length': 100,
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        },
        {
            'FullName': 'Case.Install_Date__c',
            'Metadata': {
                'label': 'Install Date',
                'type': 'Date',
                'required': False,
                'trackFeedHistory': False,
                'trackHistory': False
            }
        }
    ]
    
    print(f"\nCreating {len(fields)} custom fields on Case object...\n")
    
    created = 0
    skipped = 0
    failed = 0
    
    for field_def in fields:
        field_name = field_def['FullName'].split('.')[1]
        label = field_def['Metadata']['label']
        
        try:
            # Check if field already exists
            check_query = f"SELECT Id FROM CustomField WHERE DeveloperName='{field_name.replace('__c', '')}' AND TableEnumOrId='Case'"
            existing = sf.toolingexecute(f"query/?q={check_query.replace(' ', '+')}")
            
            if existing.get('records') and len(existing['records']) > 0:
                print(f"  ⏭️  Already exists: {label} ({field_name})")
                skipped += 1
                continue
            
            # Create the field using Tooling API
            result = sf.restful(
                'tooling/sobjects/CustomField',
                method='POST',
                json=field_def
            )
            
            if result and result.get('success'):
                print(f"  ✅ Created: {label} ({field_name})")
                created += 1
            else:
                print(f"  ❌ Failed: {label} - {result}")
                failed += 1
                
        except Exception as e:
            error_msg = str(e)
            if 'DUPLICATE_DEVELOPER_NAME' in error_msg or 'already exists' in error_msg.lower():
                print(f"  ⏭️  Already exists: {label} ({field_name})")
                skipped += 1
            else:
                print(f"  ❌ Failed: {label} - {error_msg[:100]}")
                failed += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {created} created, {skipped} already existed, {failed} failed")
    print(f"{'='*60}")
    
    if created > 0:
        print("\n⚠️  Note: You may need to add these fields to your Case page layout")
        print("   Go to: Setup → Object Manager → Case → Page Layouts → Edit")

if __name__ == '__main__':
    create_custom_fields()
