"""Verify cases and add aging context to descriptions"""

from simple_salesforce import Salesforce
import json
from datetime import datetime, timedelta

with open('local.settings.json') as f:
    settings = json.load(f)['Values']

sf = Salesforce(
    username=settings['SALESFORCE_USERNAME'],
    password=settings['SALESFORCE_PASSWORD'],
    security_token=settings['SALESFORCE_SECURITY_TOKEN'],
    domain='login'
)

# Get recent cases we just created
cases = sf.query("""
    SELECT Id, Subject, CaseNumber, CreatedDate, Priority, Description
    FROM Case 
    WHERE Status = 'New' 
    ORDER BY CreatedDate DESC 
    LIMIT 10
""")

print('Cases in Salesforce:')
print('=' * 80)
for case in cases['records']:
    subject = case['Subject'] or 'No Subject'
    print(f"Case #{case['CaseNumber']}: {subject[:55]}...")
    print(f"   Created: {case['CreatedDate']}, Priority: {case['Priority']}")
    print()

# Now let's update cases to add "Originally Reported" dates in descriptions
# This simulates aging cases for demo purposes

aging_updates = {
    'Commercial HVAC Unit Not Cooling': {
        'prefix': '*** CASE AGE: 3 DAYS - Originally reported January 18, 2026 ***\n\n',
    },
    'Chiller Plant Efficiency': {
        'prefix': '*** CASE AGE: 5 DAYS - Originally reported January 16, 2026 ***\n\n',
    },
    'VRF System Communication': {
        'prefix': '*** CASE AGE: 2 DAYS - Originally reported January 19, 2026 ***\n\n',
    },
    'Residential Heat Pump Frozen': {
        'prefix': '*** CASE AGE: 1 DAY - Originally reported January 20, 2026 (URGENT - elderly customer) ***\n\n',
    },
    'AHU Vibration and Noise': {
        'prefix': '*** CASE AGE: 7 DAYS - Originally reported January 14, 2026 ***\n\n',
    },
    'Data Center Precision Cooling': {
        'prefix': '*** CASE AGE: 4 HOURS - Just reported today January 21, 2026 (CRITICAL) ***\n\n',
    },
}

print('\nUpdating cases with aging information...')
print('=' * 80)

for case in cases['records']:
    if not case['Subject'] or not case['Description']:
        continue
    for key, update_info in aging_updates.items():
        if key in case['Subject']:
            new_desc = update_info['prefix'] + case['Description']
            sf.Case.update(case['Id'], {'Description': new_desc})
            print(f"Updated {case['CaseNumber']}: Added aging context")
            break

print('\nDone! Cases now show age information in descriptions.')
