# Ascend Procurement Agent — Deployment Guide

> **Solution:** AscendProcurementAgent_1_0_0_0.zip  
> **Version:** 1.0.0.0 (Unmanaged)  
> **SAP Integration:** Demo mode — Dataverse emulates SAP ECC 6.0 tables  
> **Production path:** Swap Dataverse actions for SAP ERP connector (see section 5)

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Power Platform environment | Developer, Sandbox, or Production |
| Copilot Studio license | Required to import and publish the bot component |
| Dataverse | Standard tables included in all Power Platform environments |
| Office 365 / Exchange | Required for approval reminder and notification emails |
| Power Automate Premium | Required to run the 6 included flows (HTTP trigger) |
| SAP ERP Connector (production only) | On-premises data gateway + SAP ERP connector license |

---

## Step 1: Import the Solution

1. Go to [make.powerapps.com](https://make.powerapps.com)
2. Select your target environment (top-right dropdown)
3. Navigate to **Solutions** → **Import solution**
4. Click **Browse** and select `AscendProcurementAgent_1_0_0_0.zip`
5. Click **Next**
6. Review component list (8 entities, 6 flows, 1 bot, 5 env vars) → click **Import**
7. Wait 3–5 minutes for import to complete

---

## Step 2: Configure Environment Variables

After import, set the environment variables:

| Variable | Demo Value | Production Value |
|---|---|---|
| `ascend_DemoMode` | `true` | `false` |
| `ascend_SAPConnectionString` | *(leave blank)* | SAP ERP gateway connection string |
| `ascend_CompanyCode` | `1000` | Your SAP BUKRS |
| `ascend_PurchasingOrg` | `1000` | Your SAP EKORG |
| `ascend_ApprovalNotificationEmail` | Your test email | Production DL or approver email |

**To set values:**  
Solutions → Ascend Procurement Agent → Environment Variables → click each → **Edit current value**

---

## Step 3: Load Sample Data (Demo Mode)

Load the 8 sample CSV files into Dataverse tables to populate SAP-emulated demo data:

| CSV File | Dataverse Table | SAP Tables Emulated |
|---|---|---|
| `ascend_sapvendor_data.csv` | `ascend_sapvendor` | LFA1, LFB1, LFM1 |
| `ascend_sapmaterialgroup_data.csv` | `ascend_sapmaterialgroup` | T023, T023T |
| `ascend_sapcostcenter_data.csv` | `ascend_sapcostcenter` | CSKS |
| `ascend_sapglaccount_data.csv` | `ascend_sapglaccount` | SKA1, SKB1 |
| `ascend_sapcontract_data.csv` | `ascend_sapcontract` | EKKO, EKPO, EORD |
| `ascend_sapreleasestrategy_data.csv` | `ascend_sapreleasestrategy` | T16FS, T161F/G/H/S |
| `ascend_sappurchaserequisition_data.csv` | `ascend_sappurchaserequisition` | EBAN |
| `ascend_sappraccountassignment_data.csv` | `ascend_sappraccountassignment` | EBKN |

**Import method:**
1. Go to [make.powerapps.com](https://make.powerapps.com) → **Dataverse** → **Tables**
2. Open each table → **Import** → **Import data from Excel / CSV**
3. Map columns and import

> ⚠️ **DEMO DISCLAIMER**: All sample data rows include `data_source = "SAP ECC 6.0 (Demo via Dataverse)"` and `demo_disclaimer` fields clearly marking them as demo data. This is intentional to prevent confusion during demos.

---

## Step 4: Connect Power Automate Flows

Each of the 6 flows needs connection references configured:

| Connection | Used By |
|---|---|
| Microsoft Dataverse | All 6 flows |
| Office 365 Outlook | `flow_sap_approve_pr`, `flow_sap_send_reminder` |

**To configure:**
1. Solutions → Ascend Procurement Agent → Cloud flows
2. Open each flow → verify connections are authorized
3. Turn ON each flow

---

## Step 5: Configure and Publish the Copilot Studio Bot

1. Go to [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com)
2. Open **Ascend Procurement Assistant**
3. Verify 4 topics are present:
   - Create Purchase Requisition
   - Check PR Status
   - Approve or Reject PR
   - PR Follow-Up Actions
4. Open each topic → verify Power Automate flow connections point to the correct flows
5. Click **Publish** (top-right)

### Deploy to Microsoft Teams (optional)
1. Channels → Microsoft Teams → **Turn on Teams**
2. Teams admin center → publish to users/channels

---

## Step 6: Run a Demo

### Sample conversation — Create PR
```
User:  I need to purchase Microsoft 365 E5 licenses
Agent: I can help with that. Which vendor would you like to use?
User:  Microsoft
Agent: I found Microsoft Corporation (V100001) and Microsoft Licensing LLC (V100002). 
       Which would you like? (Note: An active contract exists for Microsoft Licensing LLC — 
       Contract 4500012345, max value $500,000)
User:  Microsoft Licensing LLC
Agent: What are you purchasing and how often?
User:  Microsoft 365 E5, $2,000 per month for 12 months
...
Agent: PR 100250330900 created ✅
       Vendor: Microsoft Licensing LLC
       Amount: $24,000 total ($2,000/month × 12)
       Contract: 4500012345 (Enterprise Agreement)
       GL: 612345 — IT Software & Subscriptions
       Approver: John Smith (L2, $5,001–$25,000)
       ⚠️ DEMO: This PR is stored in Dataverse emulating SAP ECC 6.0 EBAN. 
          In production, BAPI_PR_CREATE would write to SAP.
```

### SAP Demo Talking Points
- Every Dataverse record has `data_source = "SAP ECC 6.0 (Demo via Dataverse)"` visible in table views
- Flow actions are labeled with SAP table names they emulate (e.g., "READ Dataverse — emulates SAP LFA1")
- Approval emails include SAP BUS2105 workflow context
- PR numbers use SAP-style BANFN format

---

## Step 7: Promote to Production (SAP Live)

When ready to connect to real SAP ECC 6.0:

1. Set `ascend_DemoMode` = `false`
2. Set `ascend_SAPConnectionString` to your SAP ERP connector connection string
3. In each Power Automate flow, swap Dataverse query actions for SAP ERP connector actions:

| Flow | Demo Action | Production SAP Action |
|---|---|---|
| Vendor lookup | Query `ascend_sapvendor` | SAP RFC_READ_TABLE → LFA1 + LFB1 + LFM1 |
| Create PR | Write to `ascend_sappurchaserequisition` | SAP BAPI_PR_CREATE → EBAN + EBKN |
| Get PR status | Read `ascend_sappurchaserequisition` | SAP BAPI_REQUISITION_GETDETAIL |
| Approve PR | Update `ascend_sappurchaserequisition` | SAP BAPI_RELEASE_PURCHASE_DOC + BUS2105 |
| Cancel/Edit PR | Update `ascend_sappurchaserequisition` | SAP BAPI_PR_CHANGE / ME52N |
| Send reminder | Office 365 email | SAP SWI_CREATE_VIA_INTERNET + email |

4. Configure the **SAP ERP connector** in Power Platform:
   - Requires on-premises data gateway
   - Requires SAP ERP connector license (Power Platform Premium + SAP ERP connector)
   - SAP system credentials: hostname, system number, client, username/password or SSO

---

## Architecture Diagram

```
Microsoft Teams / M365 Copilot
        ↓
Copilot Studio: Ascend Procurement Assistant
  ├── Topic: Create Purchase Requisition
  ├── Topic: Check PR Status
  ├── Topic: Approve / Reject PR
  └── Topic: PR Follow-Up Actions
        ↓ (Power Automate HTTP triggers)
Power Automate Flows (6 flows)
  ├── DEMO: Dataverse (ascend_sap* tables)
  └── PROD: SAP ERP Connector (on-premises gateway)
        ↓
SAP ECC 6.0 Tables (EBAN, EBKN, LFA1, T023, CSKS, T030, T16FS, EKKO)
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Solution import fails | Ensure Power Platform environment has Dataverse enabled |
| Flows not found in Copilot Studio | Republish flows, reconnect in topic action editor |
| Sample data import fails | Check column mapping — CSV headers must match Dataverse field names |
| Bot not responding | Check flow connections are authorized and flows are turned ON |
| SAP connection error (production) | Verify on-premises data gateway is running and SAP credentials are valid |

---

## Support & Contacts

- **RAPP Pipeline**: See `docs/RAPP_PIPELINE_GUIDE.md`
- **Copilot Studio YAML topics**: `transpiled/copilot_studio_native/ascend_pr_agent/topics/`
- **Backend Python agents**: `customers/ascend/agents/`
- **Sample data**: `customers/ascend/solution/sample_data/`
