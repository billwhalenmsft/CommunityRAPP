"""
Create demo cases in Salesforce for Carrier MVP demonstration.
These cases have realistic HVAC scenarios with varying complexity and urgency.
"""

from simple_salesforce import Salesforce
import json
import sys
sys.path.insert(0, '..')

# Load settings
with open('local.settings.json') as f:
    settings = json.load(f)['Values']

sf = Salesforce(
    username=settings['SALESFORCE_USERNAME'],
    password=settings['SALESFORCE_PASSWORD'],
    security_token=settings['SALESFORCE_SECURITY_TOKEN'],
    domain='login'
)

# Demo cases with realistic HVAC scenarios
demo_cases = [
    {
        'Subject': 'Commercial HVAC Unit Not Cooling - Error Code E47',
        'Description': '''Customer: ABC Manufacturing Plant
Location: Chicago, IL
Equipment: Carrier 50XC WeatherMaster Rooftop Unit
Model: 50XC-A12A2A1A0A0A0
Serial: 2419F45892

Issue: Unit displaying E47 fault code. Outdoor unit running but no cooling output.
Compressor cycling on/off every 3-5 minutes. High pressure switch tripping.

Customer reports ambient temp 92F outside, building temp rising to 85F.
Production floor needs to stay below 75F for equipment.

This is affecting their manufacturing line - URGENT.

Previous service: Refrigerant charge checked 6 months ago, was within spec.''',
        'Status': 'New',
        'Priority': 'High',
        'Origin': 'Email',
        'Product__c': 'WeatherMaster Rooftop Unit',
        'Product_Model__c': '50XC-A12A2A1A0A0A0',
        'Serial_Number__c': '2419F45892',
    },
    {
        'Subject': 'Chiller Plant Efficiency Degradation - Multiple Units',
        'Description': '''Customer: Regional Medical Center
Contact: Tom Reeves, Facilities Director
Phone: 555-234-5678

Equipment affected:
- Carrier 19XR Centrifugal Chiller (3 units)
- Model: 19XR-XR-777-EHF-52
- Serial Numbers: CH2020-4521, CH2020-4522, CH2020-4523

Problem: All three chillers showing 15-20% efficiency loss over past 2 weeks.
COP dropped from 6.2 to approximately 5.1 across all units.

Monitoring system shows:
- Condenser approach temps elevated by 4-5 degrees
- Evaporator approach normal
- No fault codes displayed

Building: 450,000 sq ft hospital, critical cooling for OR suites and data center.
Currently compensating with lead/lag adjustments but concerned about summer load.

Maintenance up to date - tubes cleaned 4 months ago.''',
        'Status': 'New', 
        'Priority': 'High',
        'Origin': 'Phone',
        'Product__c': 'Centrifugal Chiller',
        'Product_Model__c': '19XR-XR-777-EHF-52',
        'Serial_Number__c': 'CH2020-4521',
    },
    {
        'Subject': 'VRF System Communication Fault - Building Wide',
        'Description': '''Customer: Parkview Office Tower
Building Manager: Sarah Chen
Email: schen@parkviewtower.com

System: Carrier VRF (Variable Refrigerant Flow)
Model: 38VMR outdoor units (12 total)
Indoor Units: 156 ducted and cassette units across 20 floors

Issue: Intermittent communication faults between outdoor units and BMS.
Error codes: U4, U0 appearing randomly across different zones.
Sometimes units stop responding to thermostat commands.

Timeline:
- Started 3 days ago after thunderstorm
- Getting worse - now affecting 30% of zones at any given time
- Tenants complaining about comfort issues

Power surge protectors in place, no visible damage to wiring.
Previous comm issues 8 months ago resolved by replacing comm board on one ODU.''',
        'Status': 'New',
        'Priority': 'Medium',
        'Origin': 'Web',
        'Product__c': 'VRF System',
        'Product_Model__c': '38VMR',
        'Serial_Number__c': 'VRF2022-8834',
    },
    {
        'Subject': 'Residential Heat Pump Frozen - No Heat',
        'Description': '''Homeowner: Margaret Wilson
Address: 847 Oak Street, Minneapolis, MN
Phone: 555-876-5432

Equipment: Carrier Infinity Heat Pump with Greenspeed Intelligence
Model: 25VNA836A003
Serial: 4521G78234
Install Date: March 2022

Complaint: Heat pump outdoor unit completely frozen over, no heat to house.
Indoor temp dropped to 58F overnight. Using space heaters currently.

Observations from customer:
- Defrost cycle not running
- Fan on outdoor unit not spinning
- Saw ice buildup starting 2 days ago

Homeowner is elderly, outdoor temp currently 15F.
This is a warranty unit - needs priority service.

System has Cor thermostat - customer unable to access diagnostics.''',
        'Status': 'New',
        'Priority': 'High',
        'Origin': 'Phone',
        'Product__c': 'Infinity Heat Pump',
        'Product_Model__c': '25VNA836A003',
        'Serial_Number__c': '4521G78234',
        'Install_Date__c': '2022-03-15',
    },
    {
        'Subject': 'AHU Vibration and Noise - New Installation',
        'Description': '''Customer: Lincoln Elementary School
Facility Manager: Dave Martinez
Phone: 555-345-6789

Equipment: Carrier AquaSnap 30RBP Air Handler
Model: 30RBP-080
Serial: AH2025-1123
Installed: 2 weeks ago (new construction)

Issue: Excessive vibration and rumbling noise from unit.
Can hear it in adjacent classrooms during quiet periods.
Vibration noticeable on floor near mechanical room.

Noise level measured at 68 dB at 10 feet (spec says 58 dB).

Startup/commissioning was completed by Johnson Controls.
Unit running at design conditions - 8000 CFM, 2.5 in WG.

Principal concerned about noise affecting learning environment.
School opens to students in 3 weeks - need resolution before then.

Suspect: Motor alignment? Fan balance? Duct resonance?''',
        'Status': 'New',
        'Priority': 'Medium',
        'Origin': 'Email',
        'Product__c': 'AquaSnap Air Handler',
        'Product_Model__c': '30RBP-080',
        'Serial_Number__c': 'AH2025-1123',
        'Install_Date__c': '2026-01-07',
    },
    {
        'Subject': 'Data Center Precision Cooling Alarm - High Humidity',
        'Description': '''URGENT - DATA CENTER ENVIRONMENT ALERT

Customer: TechFlow Data Services
Data Center Manager: James Park
Phone: 555-999-8888 (24/7 contact)

Equipment: Carrier DataMate Precision Cooling
Model: 50BYF024
Units affected: DC-COOL-07, DC-COOL-08 (redundant pair)
Serial: DCM2023-7701, DCM2023-7702

Alert: High humidity alarm - reading 72% RH (setpoint 45% +/- 5%)
Both units showing same condition simultaneously.

Current conditions in hot aisle:
- Temp: 78F (acceptable)
- Humidity: 72% (CRITICAL - causing condensation risk)

Customer has already:
- Checked humidifier is OFF
- Verified drain lines clear
- Restarted units - no change

Server uptime SLA at risk. Customer considering emergency portable dehumidification.
This is a Tier 3 facility with $2M+ in servers at risk.

Need immediate remote diagnostics or emergency dispatch.''',
        'Status': 'New',
        'Priority': 'High',
        'Origin': 'Phone',
        'Product__c': 'DataMate Precision Cooling',
        'Product_Model__c': '50BYF024',
        'Serial_Number__c': 'DCM2023-7701',
    },
]

print('Creating demo cases in Salesforce...')
print('=' * 60)

created = []
for i, case_data in enumerate(demo_cases):
    result = sf.Case.create(case_data)
    case_id = result['id']
    print(f"\n{i+1}. Created: {case_data['Subject'][:55]}...")
    print(f"   Case ID: {case_id}")
    print(f"   Priority: {case_data['Priority']}, Origin: {case_data['Origin']}")
    created.append(case_id)

print('\n' + '=' * 60)
print(f'Successfully created {len(created)} demo cases!')
print('\nCase IDs for reference:')
for case_id in created:
    print(f"  - {case_id}")

# Show cases in Salesforce
print(f"\nView in Salesforce:")
print(f"  {settings['SALESFORCE_INSTANCE_URL']}/lightning/o/Case/list")
