# Web UI — Deployment Guide

The Agent Team Starter Kit includes a full **Command Center** web app — a single-page dashboard showing your agent team, GitHub Issues backlog, sprint board, outcomes tracker, charter, and a chat interface.

**Live example:** [bots-in-blazers.fun](https://bots-in-blazers.fun) (Mfg CoE Command Center)

---

## What's Included

| Feature | Description |
|---------|-------------|
| Agent Team view | Cards for every persona — name, role, status |
| Dashboard | KPI tiles, agent status, recent activity |
| Backlog | Live GitHub Issues via API |
| Sprint Board | Kanban: Backlog / Active / Needs Input / Done |
| Outcomes | Track delivery against defined outcomes |
| Needs Your Input | Issues labeled `needs-{owner}` surfaced for decisions |
| Activity Feed | Live ticker + recent issue feed |
| Agent Forum | GitHub Issues as discussion threads |
| SOPs & Docs | Renders Markdown files from your repo |
| Knowledge Base | Context cards your agents read |
| Charter | Your `CHARTER.md` rendered in the UI |
| Chat | Sends messages to your Azure Function agent endpoint |
| Dark / Light / Neon | Three themes |

---

## Deployment Options

### Option A — GitHub Pages (free, easiest)

**What it costs:** $0. Free on any public repo.  
**Best for:** Public CoEs, demos, open source teams.

#### Steps

1. **Enable GitHub Pages** in your repo:
   - Settings → Pages → Source: `GitHub Actions`

2. **Set a repo variable** (optional — for the Azure Function chat):
   - Settings → Variables → `AZURE_FUNCTION_ENDPOINT` = your function URL

3. **Copy the workflow:**
   ```bash
   cp workflows/deploy_web_github_pages_template.yml \
      .github/workflows/{team_slug}_deploy_web.yml
   ```
   Replace `{{TEAM_NAME}}` and `{{TEAM_SLUG}}` with your values.

4. **Push** — the workflow fires automatically and deploys `web_ui/` to Pages.

5. **Your URL:** `https://{your-org}.github.io/{your-repo}/`

#### Private repo option
GitHub Pages is **free for public repos**. For private repos, you need GitHub Teams ($4/user/month). Alternatively, use Option B or C.

---

### Option B — Azure Static Web Apps (free tier, custom domain)

**What it costs:** $0 on the Free tier (100GB bandwidth/month).  
**Best for:** Private repos, custom domain, Azure integration, auth.

#### Steps

1. **Create a Static Web App** in Azure Portal:
   - Search "Static Web Apps" → Create
   - Source: GitHub → select your repo + branch
   - App location: `web_ui`
   - Build preset: Custom
   - Output location: (leave blank)

   Or via CLI:
   ```bash
   az staticwebapp create \
     --name my-team-command-center \
     --resource-group my-rg \
     --source https://github.com/owner/repo \
     --branch main \
     --app-location web_ui \
     --login-with-github
   ```

2. **Copy the deployment token** from the Azure Portal → your Static Web App → Manage deployment token.

3. **Add the secret** to your GitHub repo:
   - Settings → Secrets → `AZURE_STATIC_WEB_APPS_API_TOKEN` = paste token

4. **Copy the workflow:**
   ```bash
   cp workflows/deploy_web_azure_swa_template.yml \
      .github/workflows/{team_slug}_deploy_web_azure.yml
   ```

5. **Push** — deploys automatically. Azure assigns a URL like `https://mango-desert-0123.azurestaticapps.net`.

6. **Custom domain:** Static Web Apps → Custom domains → Add → follow DNS steps.

#### Add Azure AD Auth (optional)
Static Web Apps has built-in auth. Add a `staticwebapp.config.json` to `web_ui/`:
```json
{
  "auth": {
    "identityProviders": {
      "azureActiveDirectory": {
        "userDetailsClaim": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/{tenant-id}/v2.0",
          "clientIdSettingName": "AAD_CLIENT_ID",
          "clientSecretSettingName": "AAD_CLIENT_SECRET"
        }
      }
    }
  },
  "routes": [
    { "route": "/*", "allowedRoles": ["authenticated"] }
  ]
}
```

---

### Option C — Azure Blob Storage Static Website (cheapest)

**What it costs:** ~$0.01–0.05/month (just storage costs, nearly free).  
**Best for:** Minimal Azure footprint, no CI/CD needed.

#### Steps

1. **Create a Storage Account** (or use your existing `AzureWebJobsStorage`):
   ```bash
   az storage account create \
     --name myteamwebui \
     --resource-group my-rg \
     --sku Standard_LRS \
     --kind StorageV2
   ```

2. **Enable static website hosting:**
   ```bash
   az storage blob service-properties update \
     --account-name myteamwebui \
     --static-website \
     --index-document index.html \
     --404-document index.html
   ```

3. **Upload the file** (after injecting your config values):
   ```bash
   az storage blob upload \
     --account-name myteamwebui \
     --container-name '$web' \
     --name index.html \
     --file web_ui/index.html \
     --content-type text/html \
     --overwrite
   ```

4. **Get your URL:**
   ```bash
   az storage account show \
     --name myteamwebui \
     --query "primaryEndpoints.web" -o tsv
   ```

#### Automate uploads (GitHub Actions)
```yaml
- name: Upload to Azure Blob
  uses: azure/CLI@v2
  with:
    inlineScript: |
      az storage blob upload \
        --account-name ${{ vars.STORAGE_ACCOUNT_NAME }} \
        --container-name '$web' \
        --name index.html \
        --file web_ui/index.html \
        --content-type text/html \
        --overwrite
```

---

## Customizing the Web UI

After running `setup_agent_team.py`, the web UI is configured automatically. If you need to customize manually:

### Key config values in `web_ui/index.html`

| Placeholder | Replace with |
|-------------|-------------|
| `{{REPO}}` | `owner/repo` (e.g. `myorg/my-team-repo`) |
| `{{TEAM_NAME}}` | Your team name |
| `{{TEAM_LABEL}}` | GitHub label filter (e.g. `my-team`) |
| `{{AZURE_FUNCTION_ENDPOINT}}` | Your Azure Function URL (for chat) |
| `{{OWNER_DISPLAY_NAME}}` | Your first name (e.g. `Alex`) |
| `{{CHARTER_PATH}}` | Path to CHARTER.md in your repo |
| `{{ENVIRONMENTS}}` | Your D365/other environment links |

### Adding/removing agents from the grid

Edit the `const AGENTS = [...]` array near the top of the `<script>` block:
```javascript
const AGENTS = [
  { id: 'orchestrator', name: 'Orchestrator', icon: '⚙️', role: 'Routes all work', status: 'idle' },
  { id: 'pm',           name: 'PM',           icon: '🗂️', role: 'Sprint planning', status: 'idle' },
  // Add or remove entries here
];
```

### Adding your logo

Place a `logo-avatar.png` (ideally 48×48px) in `web_ui/` alongside `index.html`.

---

## Comparison

| Option | Cost | Custom Domain | Auth | CI/CD | Best For |
|--------|------|--------------|------|-------|----------|
| GitHub Pages | Free | ✅ (via CNAME) | ❌ | ✅ | Public repos |
| Azure Static Web Apps | Free tier | ✅ | ✅ Azure AD | ✅ | Private, enterprise |
| Azure Blob Storage | ~$0.01/mo | Via CDN only | ❌ | Manual/scripted | Minimal setup |

**Recommendation:** Start with **GitHub Pages** (zero config). Upgrade to **Azure Static Web Apps** when you need auth or a custom domain.
