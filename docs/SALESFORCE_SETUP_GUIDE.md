# Salesforce Setup Guide for Carrier Case Triage Agents

## Overview
This guide walks you through connecting your Salesforce instance to the Carrier Case Triage Agent Swarm.

**Your Salesforce Instance:** `https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com`

## Step 1: Create a Connected App in Salesforce

1. **Log into Salesforce Setup**
   - Navigate to your Salesforce instance
   - Click the gear icon → Setup
   - Or go to: `https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com/lightning/setup/SetupOneHome/home`

2. **Create Connected App**
   - In Setup, search for "App Manager"
   - Click **New Connected App**
   - Fill in:
     - **Connected App Name:** `Carrier RAPP Agent`
     - **API Name:** `Carrier_RAPP_Agent`
     - **Contact Email:** Your email
   
3. **Enable OAuth Settings**
   - Check **Enable OAuth Settings**
   - **Callback URL:** `https://login.salesforce.com/services/oauth2/callback`
   - **Selected OAuth Scopes:** Add these:
     - `Access and manage your data (api)`
     - `Perform requests on your behalf at any time (refresh_token, offline_access)`
     - `Full access (full)`
   - Check **Enable Client Credentials Flow** (optional, for server-to-server)
   
4. **Save and Get Credentials**
   - Click **Save**
   - Wait 2-10 minutes for activation
   - Click **Manage Consumer Details**
   - Copy:
     - **Consumer Key** → This is your `SALESFORCE_CLIENT_ID`
     - **Consumer Secret** → This is your `SALESFORCE_CLIENT_SECRET`

## Step 2: Get Your Security Token

1. **Generate Security Token**
   - Click your profile icon → Settings
   - Search for "Reset My Security Token"
   - Click **Reset Security Token**
   - Check your email for the token

2. **Save the Token**
   - Copy the security token from the email
   - This is your `SALESFORCE_SECURITY_TOKEN`

## Step 3: Update local.settings.json

Edit `CommunityRAPP-main/local.settings.json` with your Salesforce credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage__accountName": "stkt6i6mlby5wzi",
    "AZURE_OPENAI_ENDPOINT": "https://openai-kt6i6mlby5wzi.openai.azure.com/",
    "AZURE_OPENAI_API_VERSION": "2025-01-01-preview",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-deployment",
    "AZURE_STORAGE_ACCOUNT_NAME": "stkt6i6mlby5wzi",
    "AZURE_FILES_SHARE_NAME": "azfrapp-kt6i6mlby5wzikt6i6mlby5wzi",
    "ASSISTANT_NAME": "RAPP Agent",
    "CHARACTERISTIC_DESCRIPTION": "Rapid Agent Prototyping Platform assistant",
    
    "SALESFORCE_INSTANCE_URL": "https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com",
    "SALESFORCE_LOGIN_URL": "https://login.salesforce.com",
    "SALESFORCE_CLIENT_ID": "YOUR_CONSUMER_KEY_HERE",
    "SALESFORCE_CLIENT_SECRET": "YOUR_CONSUMER_SECRET_HERE",
    "SALESFORCE_USERNAME": "your.email@example.com",
    "SALESFORCE_PASSWORD": "YourSalesforcePassword",
    "SALESFORCE_SECURITY_TOKEN": "YOUR_SECURITY_TOKEN_HERE",
    "SALESFORCE_API_VERSION": "v59.0"
  }
}
```

## Step 4: Create Custom Fields in Salesforce

The agents use custom fields on the Case object. Create these in Setup → Object Manager → Case → Fields & Relationships:

| Field Label | API Name | Type | Length |
|-------------|----------|------|--------|
| Triage Status | `Triage_Status__c` | Picklist | - |
| Triage Priority | `Triage_Priority__c` | Picklist | - |
| Triage Issue Type | `Triage_Issue_Type__c` | Picklist | - |
| Triage Summary | `Triage_Summary__c` | Long Text Area | 32000 |
| Recommended Action | `Recommended_Action__c` | Text Area | 1000 |
| Recommended Queue | `Recommended_Queue__c` | Text | 255 |
| AI Triaged Date | `AI_Triaged_Date__c` | Date/Time | - |
| Product Model | `Product_Model__c` | Text | 100 |
| Serial Number | `Serial_Number__c` | Text | 100 |
| Install Date | `Install_Date__c` | Date | - |

### Picklist Values:

**Triage_Status__c:**
- New
- In Progress
- Completed
- Failed
- Escalated

**Triage_Priority__c:**
- Critical
- High
- Medium
- Low

**Triage_Issue_Type__c:**
- Equipment Failure
- Controls Issue
- Preventive Maintenance
- Parts Request
- Warranty Claim
- Installation
- General Inquiry
- Other

## Step 5: Test the Connection

### Option A: Run locally
```powershell
cd CommunityRAPP-main
.venv\Scripts\activate
python -c "from utils.salesforce_client import test_salesforce_connection; print(test_salesforce_connection())"
```

### Option B: Test via the agent
```python
from agents.carrier_sf_case_monitor_agent import CarrierSFCaseMonitorAgent

agent = CarrierSFCaseMonitorAgent()
result = agent.perform(action="get_queue_summary")
print(result)
```

## Step 6: Switch from Mock to Live Data

Once connected, the agents will automatically detect the Salesforce configuration and use live data. You can verify by checking the response:

- **Mock data:** `"source": "mock_data"`
- **Live data:** `"source": "salesforce_live"`

To force mock data for testing, you can set in the agent:
```python
agent.config["use_mock_data"] = True
```

## Troubleshooting

### Authentication Errors

**Error: "invalid_client_id"**
- Wait 10 minutes after creating the Connected App
- Verify the Consumer Key is correct

**Error: "invalid_grant"**
- Check username/password are correct
- Verify security token is appended to password
- Ensure the user has API access

**Error: "Request blocked or restricted IP"**
- Add your IP to Salesforce trusted IP ranges
- Setup → Security → Network Access → Add your IP

### Field Not Found Errors

If you get "Field does not exist" errors:
1. Verify the custom fields were created
2. Check field-level security grants access to your user
3. Ensure API names match exactly (case-sensitive)

## Security Best Practices

1. **Never commit credentials** - Use environment variables
2. **Use a service account** - Don't use a personal login
3. **Limit permissions** - Grant only necessary object/field access
4. **Rotate secrets regularly** - Update tokens periodically
5. **Monitor API usage** - Check Salesforce API limits

## Next Steps

After successful connection:
1. Create test cases in Salesforce
2. Run the orchestrator: `CarrierCaseTriageOrchestratorAgent().perform(action="triage_all_new_cases")`
3. Verify triage results appear on Case records
4. Deploy to Azure and configure App Settings with the same credentials
