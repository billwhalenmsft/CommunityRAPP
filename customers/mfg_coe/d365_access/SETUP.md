# D365 Demo Tenant Access Setup for CoE Agents

Agents need API access to your demo tenants to autonomously configure, test, and validate changes.

---

## Required: App Registration in your Demo Tenant

You only need to do this once per demo environment.

### Step 1 — Create App Registration

1. Go to **[Azure Portal](https://portal.azure.com)** → your **demo tenant**
2. Navigate to: **Microsoft Entra ID → App registrations → New registration**
3. Settings:
   - **Name:** `RAPP-CoE-Agent`
   - **Supported account types:** Accounts in this organizational directory only
   - **Redirect URI:** Leave blank
4. Click **Register**
5. Note: **Application (client) ID** and **Directory (tenant) ID**

### Step 2 — Add a Client Secret

1. In your new App Registration: **Certificates & secrets → New client secret**
2. Description: `CoE Agent Access`
3. Expiry: **24 months** (or per your policy)
4. **Copy the secret value** — you won't see it again

### Step 3 — Grant Dataverse Permissions

1. In App Registration: **API permissions → Add a permission**
2. Select **Dynamics CRM**
3. Select **Delegated permissions → user_impersonation**
4. Click **Add permissions**
5. Click **Grant admin consent for [your tenant]**

### Step 4 — Add the App User in D365 / Power Platform

1. Go to **[Power Platform Admin Center](https://admin.powerplatform.microsoft.com)**
2. Select your **Master CE Mfg** environment
3. Go to **Settings → Users + Permissions → Application Users**
4. Click **New app user**
5. Search for `RAPP-CoE-Agent` → Add
6. Assign security role: **System Administrator** (for full demo access)

### Step 5 — Add to GitHub Secrets

In your GitHub repo `kody-w/CommunityRAPP`:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `D365_MASTER_CE_MFG_URL` | `https://yourenv.crm.dynamics.com` |
| `D365_TENANT_ID` | Directory (tenant) ID from Step 1 |
| `D365_CLIENT_ID` | Application (client) ID from Step 1 |
| `D365_CLIENT_SECRET` | Secret value from Step 2 |
| `AZURE_OPENAI_API_KEY` | Your OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Your OpenAI endpoint |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Your deployment name (e.g., gpt-4o) |
| `AZURE_OPENAI_API_VERSION` | API version |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage connection string |

---

## Optional: Power Platform CLI Access

For agents to deploy Copilot Studio solutions:

```bash
# Install PAC CLI
dotnet tool install --global Microsoft.PowerApps.CLI.Tool

# Create auth profile using service principal
pac auth create \
  --tenant $D365_TENANT_ID \
  --applicationId $D365_CLIENT_ID \
  --clientSecret $D365_CLIENT_SECRET \
  --name "CoEAgent"
```

---

## What Agents Can Do With This Access

| Capability | Method |
|---|---|
| Query D365 records (accounts, cases, contacts) | Dataverse Web API GET |
| Create/update records | Dataverse Web API POST/PATCH |
| List installed solutions | Dataverse Web API + solutions endpoint |
| Check Copilot Studio bot status | Power Platform API |
| Deploy Power Automate flows | Power Platform CLI (pac) |

---

## Security Notes

- The App Registration only has access to your **demo tenants** — never production
- Agents are constrained by `COE_CHARTER.md` — they will not delete data or modify production configs without a `needs-bill` issue
- Client secrets should be rotated every 12-24 months
- Review GitHub Actions logs to audit what agents did
