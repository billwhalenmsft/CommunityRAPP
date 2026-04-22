---
name: power-platform
description: Working with Power Platform — Copilot Studio agents, Dataverse API, PAC CLI, Power Pages, Power Automate. Use this skill when creating, updating, or deploying Copilot Studio agents, managing Dataverse records, working with Power Platform solutions, or packaging/importing solution ZIPs.
---

# Power Platform Skill — Copilot Studio, Dataverse & PAC CLI

## Lessons Learned (Hard-Won)

### Power Platform Solution Packaging

**Critical: Every `<entity>` in `<EntityInfo>` must declare `PrimaryNameAttribute`**
- Syntax: `<entity Name="..." OwnershipType="..." CollectionName="..." PrimaryNameAttribute="fieldname">`
- The value must match an existing `nvarchar` attribute's `Name` in the same entity's `<Attributes>` block
- **The referenced attribute also needs `<IsPrimaryName>1</IsPrimaryName>` and `<RequiredLevel>SystemRequired</RequiredLevel>` inside its own `<Attribute>` block** — just pointing to it on `<entity>` is not enough
- Missing either piece → import fails at ~45% with error `0x80044355: PrimaryName attribute not found for Entity: <name>`
- **Cascade effect:** the failure stops all subsequent entity processing — all remaining entities show "Unprocessed"
- Choose the field that best labels the record (vendor name, document short text, contract number, etc.)

**Critical: `[Content_Types].xml` namespace**
- The root `<Types>` element MUST have `xmlns="http://schemas.openxmlformats.org/package/2006/content-types"`
- Missing this namespace → "Required Types tag not found. Line 2, position 2" at import
- Correct: `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">`

**Critical: Entity definitions must be inline in `customizations.xml`**
- All `<Entity>` blocks MUST live directly inside `<Entities>` in `customizations.xml`
- Separate `Entities/EntityName/Entity.xml` files (created by `pac solution unpack`) are NOT read during import
- The importer only reads `customizations.xml` — it ignores entity subfolders

**Required `customizations.xml` structure:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.24.10827"
  SolutionPackageVersion="9.2"
  languagecode="1033"
  generatedBy="CRMExport"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <Entities>
    <Entity>
      <Name>my_entity</Name>
      <ObjectTypeCode>10200</ObjectTypeCode>
      <OriginalName>my_entity</OriginalName>
      <OwnershipTypeMask>UserOwned</OwnershipTypeMask>
      <EntityInfo>...</EntityInfo>
      <Attributes>...</Attributes>
    </Entity>
    <!-- more entities inline -->
  </Entities>

  <!-- Required empty closing tags — omitting any causes import failure -->
  <Roles/>
  <FieldSecurityProfiles/>
  <Workflows/>
  <EntityMaps/>
  <EntityRelationships/>
  <OrganizationSettings/>
  <optionsets/>
  <CustomControls/>
  <EntityDataProviders/>
  <CanvasApps/>
  <Connectors/>

</ImportExportXml>
```

**Picklist option values must use publisher prefix range**
- Publisher prefix `10000` → option values start at `100000` (100000, 100001, 100002 …)
- Do NOT use generic values like `1`, `2`, `3` or `748140000` range unless that is your actual publisher prefix
- Check publisher prefix in Power Platform Admin Center → Solutions → your publisher

**Always validate before packaging**
- Use `pac solution check` (PAC CLI) for full validation
- Or build a `build_solution.py` validator that checks:
  1. `[Content_Types].xml` has OPC namespace
  2. `customizations.xml` root is `<ImportExportXml>`
  3. `<Entities>` is not empty (entities are inline)
  4. Required empty closing tags are present
  5. XML is well-formed (run `xml.etree.ElementTree.parse()`)
- The Ascend solution includes a reference implementation: `customers/ascend/solution/build_solution.py` with `--validate-only` flag
- Validator checks:
  1. `[Content_Types].xml` has OPC namespace
  2. `customizations.xml` root is `<ImportExportXml>`
  3. `<Entities>` is not empty (entities are inline)
  4. Every `<entity>` has `PrimaryNameAttribute` pointing to an existing `<Attribute>`
  5. Required empty closing tags are present
  6. XML is well-formed (run `xml.etree.ElementTree.parse()`)

**Workflow files in solution ZIPs**
- Power Automate flows go in `Workflows/*.json` in the ZIP root
- Each flow JSON must have a unique `id` (GUID) and `name`
- For SAP integration: use `description` and compose steps to document which BAPI/table is called
- Flows are stubs until the SAP ERP connector is configured — use `DemoModeCheck` compose steps so reviewers know which action is real vs. demo

**Bot components in solution ZIPs**
- Copilot Studio topics go in `BotComponents/{botSchema}/Topics/{schemaName}.yaml`
- Bot schema naming convention: `{publisher_prefix}_{BotName}` (e.g., `ascend_ProcurementAssistant`)
- Topic schema: `{botSchema}.topic.{TopicName}` — but for ZIP packaging, use the YAML filename directly
- Topics created via solution import may not render in Copilot Studio UI on first import — see "Copilot Studio API" section below

### Copilot Studio Agent Updates via API

#### `data` vs `content` field — CRITICAL
- Copilot Studio UI reads the **`data`** field on `botcomponent`, NOT `content`.
- `content` is the legacy/internal field — patching it has no visible effect in the topic canvas.
- **Always PATCH the `data` field** with the YAML string when updating topic content via API.
- When you POST a new topic, include `data` (not just `content`) in the request body.

#### What works vs what doesn't
- **What CAN be done via API:**
  - Update GPT instructions (Type 15 component) — WORKS
  - PATCH `data` field on existing topics to update YAML content — WORKS (triggers/conditions/variables show immediately)
  - Publish via PvaProvision + PvaPublish — WORKS
  - Delete topics — WORKS
  - Add topics to a solution via `AddSolutionComponent` — WORKS
- **What CANNOT fully be done via API:**
  - Create NEW custom topics that render **completely** in the UI canvas — **prompt text and SendActivity text show as empty** even when `data` contains valid YAML. The trigger phrases, conditions, and variable names DO appear, but message text inside `prompt:` and `activity:` nodes does NOT populate.
  - **Root cause:** Copilot Studio parses the node structure from `data` but does not hydrate the text content into canvas nodes on initial creation. This is a platform limitation.
  - **Fix:** After API creation, open each topic in **Code Editor** (three-dot menu → "Open code editor") and paste the full YAML. This forces the canvas to re-parse and populate all text fields.

#### Code Editor paste — the correct workflow
1. Create topics via API (scaffold with trigger phrases — these DO work) 
2. In Copilot Studio → Topics → click topic → three-dot menu → **Open code editor**
3. Select all existing YAML, paste your full `.mcs.yml` content, click **Save**
4. Close code editor — all Question/Message/Condition blocks will now be populated
5. Repeat for each topic

#### Always run the 3-step publish pipeline after any API changes:
  1. `POST /bots({botId})/Microsoft.Dynamics.CRM.PvaProvision` — provisions the bot runtime
  2. `POST /bots({botId})/Microsoft.Dynamics.CRM.PvaPublish` — publishes to the runtime
  3. `pac copilot publish --bot {botId}` — PAC CLI publish as backup
- **Wait 30-60 seconds between provision and publish** for large changes.

### Copilot Studio Extension (VS Code)
- The Copilot Studio VS Code extension clones agents into their **own workspace** (separate VS Code window).
- Cloned agents are NOT automatically visible in the main repo workspace's AGENT CHANGES panel.
- The extension stores workspace metadata in `AppData\Roaming\Code\User\workspaceStorage\`.
- **Workaround:** Skip the extension for pushing changes. Use the Dataverse API directly (see API patterns below).
- The extension is useful for initial clone/inspect but unreliable for pushing updates programmatically.

### Dataverse API — Bot Components
- Bot components are stored in the `botcomponents` entity.
- Component types:
  - `0` = Topic (legacy)
  - `9` = Topic V2 (modern — use this)
  - `10` = Bot translations / instructions overview
  - `15` = Custom GPT (AI instructions) — **REQUIRED for agent to function**
  - `16` = Knowledge source
  - `18` = Copilot settings
- **Creating a new topic:** POST to `/botcomponents` with `componenttype: 9`, `parentbotid@odata.bind: "/bots({botId})"`, and include `data: "{yaml}"` (NOT `content`).
- **Updating an existing topic:** PATCH to `/botcomponents({componentId})` with `data: "{yaml}"` — NOT `content`. Using `content` has no visible effect in the UI.
- **Topic content format:** The `data` field accepts the full `.mcs.yml` YAML as a string. After API write, trigger phrases/conditions/variable names appear but **prompt text and message text will be empty** — fix by opening Code Editor in the UI and re-pasting the YAML.
- **After any topic create/update via API:** Open each topic in Copilot Studio → three-dot menu → **Open code editor** → paste full YAML → Save. This populates all canvas text fields.
- Schema naming convention: `{botSchema}.topic.{TopicName}` (e.g., `cra1f_agentXyz.topic.ProductTroubleshoot`)

### Dataverse API — Common Gotchas
- **Entity images (product photos):** PATCH with `entityimage` as base64 string. The API may return 400 but the image persists — verify by checking `entityimage_url` field.
- **Intent Agent records:** API-created intents (`msdyn_intents`) do NOT render in D365 Admin Center UI. Must be created manually through the UI. This is a known Dynamics platform bug.
- **KB articles:** Create via POST to `/knowledgearticles`. Publish requires 2 PATCHes: statecode=1/statuscode=5 (Approve), then statecode=3/statuscode=7 (Publish). Each article gets a Draft + Published version automatically.
- **Customer assets:** `cra1f_contracttype` uses option set values 276120000-276120005 (NOT the generic 748140000 range). Always verify option set values before patching.

### PAC CLI Reference
- `pac auth list` — show authenticated profiles
- `pac auth select --index N` — switch active profile/environment
- `pac copilot list` — list all copilots in current environment
- `pac copilot status --bot-id {guid}` — check deployment status
- `pac copilot publish --bot {guid}` — publish a copilot
- `pac copilot extract-template --bot-id {guid}` — extract agent as template

### Demo Engagement Guide — Always Keep Updated
- **Every time you build a new demo component** (script, agent, KB article, workstream, email setup), update the unified execution guide at `customers/{name}/d365/demo-assets/{name}_demo_unified.html`.
- The guide has these update points:
  - **Pre-Flight Checklist** — add any new setup steps or URLs
  - **Reference Data section** — update KB article numbers, account details, serial numbers
  - **Timing Bar** — adjust if adding new demo scenarios
  - **Scenario sections** — add new TELL/SHOW/TELL sections for each new capability
  - **Quick Reference callouts** — add new email addresses, agent URLs, setup notes
- If you're unsure where to add something, search for the nearest related section and add a callout block.

### Power Pages Portal Users — Always Create with Contacts
- **Every demo contact should have a portal user** so they can log into the portal during demos.
- Portal user setup requires 3 things on the Contact record:
  1. `adx_identity_username` — set to a unique username (e.g., `christine.delacroix`)
  2. `adx_identity_emailaddress1confirmed` = `true`
  3. `adx_identity_logonenabled` = `true`
- **Web role assignment** — associate the contact with the "Authenticated Users" web role for the target website:
  ```
  POST /adx_webroles({roleId})/adx_webrole_contact/$ref
  Body: {"@odata.id": "{base}/contacts({contactId})"}
  ```
- **Portal invitation** — create an `adx_invitations` record with `adx_inviteContact@odata.bind` to generate a redemption URL
- **Finding the right web role:** Query `adx_webroles` filtered by `adx_name eq 'Authenticated Users'` and match `_adx_websiteid_value` to your portal's website ID
- **Finding the website ID:** Query `adx_websites` and match by name (e.g., "Customer Self Service 2 - customerselfservice-bw")
- **Current portal:** `https://customerselfservice-bw.powerappsportals.com` (website ID: `8d9b8371-e791-f011-b4cb-7c1e5200aedd`)

### Exchange Online — Shared Mailboxes
- `Connect-ExchangeOnline` requires interactive browser auth — cannot run fully unattended from terminal.
- Creating a shared mailbox: `New-Mailbox -Shared -Name "Name" -PrimarySmtpAddress "email@domain.com"`
- Granting SendAs: `Add-RecipientPermission -Identity "shared@domain.com" -Trustee "admin@domain.com" -AccessRights SendAs -Confirm:$false`
- If a user account with the same email already exists, delete it (including from recycle bin) before creating the shared mailbox.
- AutoMapping takes 15-30 minutes to propagate to Outlook.

### Demo Email Flow
- The HTML execution guide uses `outlook.office.com/mail/deeplink/compose` to pre-fill emails (no MSAL auth needed).
- MSAL popup auth fails from `file://` URIs — Azure AD doesn't accept `file://` as a redirect scheme.
- Config values (Graph client ID, tenant ID, queue email) should be hardcoded inline in the HTML with config file as optional override.

## API Patterns — Copy/Paste Reference

### Create a New Topic on Existing Bot
```powershell
$body = @{
    name = "My Topic"
    schemaname = "{botSchema}.topic.MyTopic"
    componenttype = 9
    content = $yamlContent  # Full .mcs.yml as string
    "parentbotid@odata.bind" = "/bots({botId})"
    statecode = 0
    statuscode = 1
}
$resp = Invoke-RestMethod -Uri "$base/botcomponents" -Method Post -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json -Depth 5)))

# Associate with bot
$assoc = @{ "@odata.id" = "$base/botcomponents($($resp.botcomponentid))" } | ConvertTo-Json
Invoke-RestMethod -Uri "$base/bots($botId)/bot_botcomponent/`$ref" -Method Post -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($assoc))
```

### Update an Existing Topic
```powershell
$patchBody = @{ content = $yamlContent } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "$base/botcomponents($componentId)" -Method Patch -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($patchBody))
```

### Full Publish Pipeline
```powershell
# 1. Provision
Invoke-RestMethod -Uri "$base/bots($botId)/Microsoft.Dynamics.CRM.PvaProvision" -Method Post -Headers $headers -Body "{}"
Start-Sleep -Seconds 5

# 2. Publish
Invoke-RestMethod -Uri "$base/bots($botId)/Microsoft.Dynamics.CRM.PvaPublish" -Method Post -Headers $headers -Body "{}"

# 3. PAC CLI backup
pac copilot publish --bot $botId
```

### Create/Publish KB Article
```powershell
# Create
$body = @{ title = "My Article"; description = "desc"; keywords = "kw1 kw2"; content = "<h2>HTML</h2>" }
Invoke-RestMethod -Uri "$base/knowledgearticles" -Method Post -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json)))

# Find draft, approve, publish
$ab = [System.Text.Encoding]::UTF8.GetBytes('{"statecode":1,"statuscode":5}')
Invoke-RestMethod -Uri "$base/knowledgearticles($draftId)" -Method Patch -Headers $headers -Body $ab
$pb = [System.Text.Encoding]::UTF8.GetBytes('{"statecode":3,"statuscode":7}')
Invoke-RestMethod -Uri "$base/knowledgearticles($draftId)" -Method Patch -Headers $headers -Body $pb
```

## Environment Reference
- **D365 Org:** `https://orgecbce8ef.crm.dynamics.com`
- **Tenant:** `daa9e2eb-aaf1-46a8-a37e-3fd2e5821cb6`
- **PAC Auth Index 2:** Master CE Mfg environment
- **Auth pattern:** `az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com"` for Dataverse, `--resource "https://graph.microsoft.com"` for Graph API
