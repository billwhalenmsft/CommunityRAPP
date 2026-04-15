# GE ERAC Lite CRM — Dataverse Integration Guide

This document maps the ERAC Lite CRM data model to Dataverse OOTB tables from the **Common Data Model (CDM)** and describes the path from the current demo (inline mock data) to a live Dataverse backend.

---

## Filtering Strategy — Shared Org Isolation

**Problem:** The demo Dataverse org contains accounts for multiple customers/scenarios. ERAC views must only show reinsurance cedents, not every account in the system.

**Solution:** Single custom boolean column `erac_iscedent` on the `account` table.

| | |
|--|--|
| **Column** | `erac_iscedent` (Boolean) |
| **Default** | `false` (all existing accounts unaffected) |
| **ERAC accounts** | Set to `true` during provisioning |
| **OData filter** | `$filter=erac_iscedent eq true` |
| **MDA views** | All ERAC views built with this filter baked in |

This is non-destructive — no existing data changes. When the org is reused for other demos, accounts not tagged with `erac_iscedent=true` are invisible to ERAC views. For production, actual cedent onboarding sets this field.

```
Provisioning:  .\dataverse\scripts\Provision-EracDataverse.ps1 -OrgUrl "https://orgXXX.crm.dynamics.com"
Schema:        .\dataverse\config\schema.json
Demo data:     .\dataverse\data\demo-accounts.json
```

---

```
ERAC Lite CRM (HTML/JS)
        │
        ▼
Azure Function  ──►  Dataverse (Power Platform)
        │                    │
        │            OOTB CDM Tables
        │            + ERAC Custom Tables
        ▼
Azure OpenAI (Copilot)
```

---

## CDM Table Mapping

### 1. Cedents → `account`

| ERAC Field       | Dataverse Column          | Notes                                  |
|------------------|---------------------------|----------------------------------------|
| `id`             | `accountid` (GUID)        | Auto-generated                         |
| `name`           | `name`                    |                                        |
| `type`           | `customertypecode` + `erac_partnershiptype` | Use custom option set: Strategic / Advisory / Tactical / Transactional |
| `owner`          | `ownerid` (lookup → systemuser) |                               |
| `status`         | `statuscode`              | Active / Inactive                      |
| `portfolioPct`   | `erac_portfoliopct` (Decimal) | Custom column                      |

**Relationship Managers:** Use `account_team` or relate to `systemuser` via `ownerid`.

---

### 2. Contacts → `contact`

| ERAC Field       | Dataverse Column          | Notes                                  |
|------------------|---------------------------|----------------------------------------|
| `id`             | `contactid` (GUID)        |                                        |
| `cedentId`       | `parentcustomerid` (lookup → account) |                           |
| `name`           | `fullname` / `firstname` + `lastname` |                          |
| `title`          | `jobtitle`                |                                        |
| `function`       | `department`              |                                        |
| `tier`           | `erac_contacttier` (Option Set) | Custom: Tier 1 / Tier 2 / Tier 3  |
| `email`          | `emailaddress1`           |                                        |
| `phone`          | `telephone1`              |                                        |
| `lastContact`    | `erac_lastcontactdate` (Date) | Custom                             |
| `riskFlags`      | `erac_riskflags` (Multi-select or related table) | Custom        |

---

### 3. Meetings / Engagements → `activitypointer` + `appointment`

| ERAC Field       | Dataverse Column          | Notes                                  |
|------------------|---------------------------|----------------------------------------|
| `cedentId`       | `regardingobjectid` (lookup → account) |                          |
| `type`           | `activitytypecode` / `erac_meetingtype` (custom) |               |
| `date`           | `scheduledstart` / `actualstart` |                               |
| `notes`          | `description`             |                                        |
| `participants`   | `activityparty`           | Standard activity party relationship   |
| `outcome`        | `erac_outcome` (custom text/option) | Custom column               |
| `nextSteps`      | `erac_nextsteps` (custom) |                                        |

---

### 4. Partnership Rating Reviews (PRR) → Custom Table: `erac_partnershiprating`

This is a custom CDM extension table (not OOTB). Use the Power Platform solution to create it.

| Field            | Column                    | Type                                   |
|------------------|---------------------------|----------------------------------------|
| PRR ID           | `erac_partnershipratingid` | Primary key (GUID)                    |
| Cedent           | `erac_accountid`          | Lookup → account                       |
| Period           | `erac_period`             | Text (e.g., "Q1 2026")                |
| Relationship     | `erac_relationship`       | Decimal (0–5)                          |
| Technical        | `erac_technical`          | Decimal (0–5)                          |
| Strategic        | `erac_strategic`          | Decimal (0–5)                          |
| Operational      | `erac_operational`        | Decimal (0–5)                          |
| Overall Rating   | `erac_overallrating`      | Decimal (0–5, calculated or manual)    |
| Status           | `erac_status`             | Option Set: Draft / Submitted / Approved |
| Last QBR Date    | `erac_lastqbrdate`        | Date                                   |
| Notes            | `erac_notes`              | Multi-line text                        |

---

### 5. Risk Assessments → Custom Table: `erac_riskassessment`

| Field            | Column                    | Type                                   |
|------------------|---------------------------|----------------------------------------|
| Assessment ID    | `erac_riskassessmentid`   | Primary key                            |
| Cedent           | `erac_accountid`          | Lookup → account                       |
| Period           | `erac_period`             | Text                                   |
| Financial Risk   | `erac_financialrisk`      | Option Set: Low / Medium / High / Critical |
| Technology Risk  | `erac_technologyrisk`     | Option Set                             |
| Compliance Risk  | `erac_compliancerisk`     | Option Set                             |
| Counterparty Risk| `erac_counterpartyrisk`   | Option Set                             |
| Aggregate Risk   | `erac_aggregaterisk`      | Option Set                             |
| Analyst          | `erac_analyst`            | Lookup → systemuser                    |
| Review Date      | `erac_reviewdate`         | Date                                   |
| Notes            | `erac_notes`              | Multi-line text                        |

---

### 6. Actuarial Data

#### Reserve Adequacy → Custom Table: `erac_reserveadequacy`

| Field            | Column                    | Type         |
|------------------|---------------------------|--------------|
| Cedent           | `erac_accountid`          | Lookup       |
| Line of Business | `erac_lob`                | Text         |
| Current Reserve  | `erac_currentreserve`     | Decimal (M)  |
| Recommended Reserve | `erac_recreserve`      | Decimal (M)  |
| Adequacy %       | `erac_adequacypct`        | Decimal      |
| Status           | `erac_status`             | Option Set   |

#### Experience Studies → Custom Table: `erac_experiencestudy`
#### LDF Triangles → Custom Table: `erac_ldftriangle` + `erac_ldffactor`
#### Actuarial Assumptions → Custom Table: `erac_actuarialassumption`

---

### 7. Legal Data

#### Treaties → Custom Table: `erac_treaty`

| Field            | Column                    | Type         |
|------------------|---------------------------|--------------|
| Cedent           | `erac_accountid`          | Lookup       |
| Treaty Name      | `erac_name`               | Text         |
| Type             | `erac_treatytype`         | Option Set   |
| Effective Date   | `erac_effectivedate`      | Date         |
| Expiry Date      | `erac_expirydate`         | Date         |
| Exposure (M)     | `erac_exposurem`          | Decimal      |
| Governing Law    | `erac_governinglaw`       | Text         |
| Status           | `erac_status`             | Option Set   |

#### Disputes → Custom Table: `erac_dispute`
#### Amendments → Custom Table: `erac_amendment` (linked to `erac_treaty`)

---

## Kanban Tasks → `task` (standard)

| ERAC Field       | Dataverse Column          | Notes                                  |
|------------------|---------------------------|----------------------------------------|
| `cedentId`       | `regardingobjectid`       | Lookup → account                       |
| `title`          | `subject`                 |                                        |
| `stage`          | `erac_kanbanstage`        | Custom Option Set: Backlog / Planning / Executing / Done |
| `owner`          | `ownerid`                 |                                        |
| `priority`       | `prioritycode`            | Standard: Low / Normal / High          |
| `dueDate`        | `scheduledend`            |                                        |
| `notes`          | `description`             |                                        |

---

## Azure Function Integration Pattern

```python
# utils/dataverse_client.py (to be created)
from azure.identity import DefaultAzureCredential
from msal import ConfidentialClientApplication

class DataverseClient:
    def __init__(self, org_url: str):
        self.org_url = org_url  # e.g., https://orgXXX.crm.dynamics.com
        self.api_url = f"{org_url}/api/data/v9.2"
        self.token = self._get_token()

    def get_cedents(self):
        return self._get("accounts?$select=accountid,name,erac_portfoliopct,statuscode&$filter=erac_iscedenteq true")

    def get_contacts(self, account_id=None):
        url = "contacts?$select=contactid,fullname,jobtitle,department,emailaddress1"
        if account_id:
            url += f"&$filter=_parentcustomerid_value eq {account_id}"
        return self._get(url)

    def _get(self, path):
        import requests
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "OData-MaxVersion": "4.0", "OData-Version": "4.0"}
        r = requests.get(f"{self.api_url}/{path}", headers=headers)
        r.raise_for_status()
        return r.json().get("value", [])

    def _get_token(self):
        # Use managed identity in Azure, or client credentials locally
        cred = DefaultAzureCredential()
        token = cred.get_token(f"{self.org_url}/.default")
        return token.token
```

---

## Migration Path: Demo → Production

| Phase | Action |
|-------|--------|
| **Demo** | Inline `MOCK_DATA` + `PHASE2_DATA` in HTML, no backend |
| **Phase 3** | Azure Function reads from Dataverse via OData API |
| **Phase 4** | Copilot Studio agent + Power Automate flows trigger on Dataverse changes |
| **Phase 5** | Real-time sync: Dataverse plugins → Event Grid → Azure Function |

---

## Environment Details (GE ERAC)

| Setting | Value |
|---------|-------|
| Dataverse Org | *(TBD — request from ERAC IT)* |
| Solution Name | `ERACLiteCRM` |
| Publisher Prefix | `erac` |
| Power Platform Environment | *(TBD)* |
| Service Account | *(TBD — managed identity preferred)* |

---

*Document version: 2.0 — Phase 2*  
*Owner: Bill Whalen, Microsoft SE*
