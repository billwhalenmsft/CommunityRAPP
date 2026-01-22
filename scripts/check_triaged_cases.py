"""Quick check of triaged cases in Salesforce"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local.settings.json'), 'r') as f:
    for k, v in json.load(f).get('Values', {}).items():
        if v: os.environ[k] = v

from utils.salesforce_client import get_salesforce_client

sf = get_salesforce_client()
sf._ensure_authenticated()

print("\n=== TRIAGED CASES IN SALESFORCE ===\n")

result = sf.query("""
    SELECT CaseNumber, Subject, Triage_Status__c, Triage_Priority__c, 
           Triage_Issue_Type__c, AI_Triaged_Date__c 
    FROM Case 
    WHERE Triage_Status__c = 'Completed' 
    ORDER BY AI_Triaged_Date__c DESC 
    LIMIT 10
""")

records = result.get('records', [])
print(f"Total triaged cases: {len(records)}\n")

for c in records:
    subj = (c.get('Subject') or 'N/A')[:50]
    date = (c.get('AI_Triaged_Date__c') or 'N/A')[:10]
    print(f"[{c['CaseNumber']}] {subj}")
    print(f"  Priority: {c.get('Triage_Priority__c', 'N/A')}")
    print(f"  Issue Type: {c.get('Triage_Issue_Type__c', 'N/A')}")
    print(f"  Triaged: {date}")
    print()
