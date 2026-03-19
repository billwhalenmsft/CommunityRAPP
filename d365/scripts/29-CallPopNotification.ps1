<#
.SYNOPSIS
    Step 29 - Create Custom Call Pop Notification Template for Incoming Voice Calls
.DESCRIPTION
    Creates a rich notification template that agents see BEFORE accepting an incoming
    phone call.  Displays:

      ┌──────────────────────────────────────────────┐
      │ 📞 Incoming Call from {customerName}         │
      │                                              │
      │  Customer:   Ferguson Enterprises             │
      │  Account:    Ferguson Enterprises (Tier 1)    │
      │  Contact:    Mike Reynolds                    │
      │  Tier:       Tier 1 - Strategic               │
      │  Open Cases: 3                                │
      │  Phone:      (713) 555-0142                   │
      │                                              │
      │         [ Accept ]    [ Reject ]              │
      └──────────────────────────────────────────────┘

    Two context-variable modes:

      Mode 1 — Native Voice Channel (default)
        Uses built-in D365 context variables populated by ANI/CRM lookup.

      Mode 2 — Copilot Studio IVR  (-UseCopilotStudioIVR)
        Uses va_* context variables passed from the Copilot Studio voice bot.
        The bot does the CRM lookup during the IVR flow and transfers variables
        to the agent session.

    After creating the template, the script updates voice workstreams to
    reference it instead of the default notification.

    DATAVERSE SCHEMA NOTES:
      - Notification templates: msdyn_notificationtemplates entity
      - Notification fields:    msdyn_notificationfields entity
      - Relationship:           Many-to-many via msdyn_notificationtemplate_notificationfield
      - msdyn_uniquename must use a valid publisher customization prefix (e.g., bw_)
      - msdyn_desktopnotificationmode values: 509180000=Never, 509180001=Always, 509180002=WhenBackgrounded
      - Auth is via az login token, NOT DataverseHelper headers (which may add incompatible headers)

.PARAMETER UseCopilotStudioIVR
    Switch. If set, field values use Copilot Studio va_* context variables
    instead of native OC context variables.

.PARAMETER WorkstreamName
    Name of the voice workstream to update, or "ALL" to update all voice workstreams.
    Defaults to "ALL".

.PARAMETER SkipWorkstreamUpdate
    Switch. If set, creates the template but does not update any workstream.

.PARAMETER Prefix
    Publisher customization prefix. Defaults to "bw" (Bill Whalen MSFT).

.EXAMPLE
    # Native voice channel context — update all voice workstreams
    .\29-CallPopNotification.ps1

    # Copilot Studio IVR context variables
    .\29-CallPopNotification.ps1 -UseCopilotStudioIVR

    # Create template only (don't touch workstream)
    .\29-CallPopNotification.ps1 -SkipWorkstreamUpdate

    # Target a specific workstream
    .\29-CallPopNotification.ps1 -WorkstreamName "Phone call workstream"
#>

[CmdletBinding()]
param(
    [switch]$UseCopilotStudioIVR,
    [string]$WorkstreamName = "ALL",
    [switch]$SkipWorkstreamUpdate,
    [string]$Prefix = "bw"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "29" "Create Call Pop Notification Template"
Connect-Dataverse

# Use direct token auth (DataverseHelper headers can cause 500s on some entities)
$orgUrl = (Get-DataverseApiUrl) -replace '/api/data/v9.2/', ''
$apiUrl = "$orgUrl/api/data/v9.2/"
$token  = az account get-access-token --resource $orgUrl --query accessToken -o tsv
$headers = @{
    "Authorization"    = "Bearer $token"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
    "Accept"           = "application/json"
    "Content-Type"     = "application/json; charset=utf-8"
}

# ============================================================
# 1. Define the notification template
# ============================================================
$templateUniqueName = "${Prefix}_incoming_call_callpop"
$templateName       = "Incoming Call - Customer Context"

Write-Host "`n--- Template Definition ---" -ForegroundColor Cyan
Write-Host "  Name:        $templateName" -ForegroundColor White
Write-Host "  UniqueName:  $templateUniqueName" -ForegroundColor White
Write-Host "  Prefix:      $Prefix" -ForegroundColor White
Write-Host "  Mode:        $(if ($UseCopilotStudioIVR) { 'Copilot Studio IVR (va_* vars)' } else { 'Native Voice Channel' })" -ForegroundColor White

# ============================================================
# 2. Define the fields to display on the call pop
# ============================================================
# Each field maps a display label to a context variable slug.
#
# Native voice channel variables:
#   {customerName}           - Contact name from ANI match
#   {msdyn_account_name}     - Related account name
#   {msdyn_contact_name}     - Contact full name
#   {msdyn_tier}             - Custom context key (set via routing rules or context)
#   {msdyn_open_cases}       - Custom context key
#   {customerPhone}          - Caller phone number (ANI)
#
# Copilot Studio IVR variables (va_ prefix):
#   {va_CustomerName}        - Looked up in IVR bot flow
#   {va_AccountName}         - Account name from bot CRM lookup
#   {va_ContactName}         - Contact name from bot CRM lookup
#   {va_Tier}                - Tier from bot CRM lookup
#   {va_OpenCases}           - Open case count from bot CRM lookup
#   {va_Phone}               - Caller phone from bot / ANI

if ($UseCopilotStudioIVR) {
    $fieldDefinitions = @(
        @{ Label = "Customer";   Slug = "{va_CustomerName}"; UniqueName = "${Prefix}_callpop_customer";  Order = 1 }
        @{ Label = "Account";    Slug = "{va_AccountName}";  UniqueName = "${Prefix}_callpop_account";   Order = 2 }
        @{ Label = "Contact";    Slug = "{va_ContactName}";  UniqueName = "${Prefix}_callpop_contact";   Order = 3 }
        @{ Label = "Tier";       Slug = "{va_Tier}";         UniqueName = "${Prefix}_callpop_tier";      Order = 4 }
        @{ Label = "Open Cases"; Slug = "{va_OpenCases}";    UniqueName = "${Prefix}_callpop_opencases"; Order = 5 }
        @{ Label = "Phone";      Slug = "{va_Phone}";        UniqueName = "${Prefix}_callpop_phone";     Order = 6 }
    )
    $titleSlug = "Incoming call from {va_CustomerName}"
} else {
    $fieldDefinitions = @(
        @{ Label = "Customer";   Slug = "{customerName}";        UniqueName = "${Prefix}_callpop_customer";  Order = 1 }
        @{ Label = "Account";    Slug = "{msdyn_account_name}";  UniqueName = "${Prefix}_callpop_account";   Order = 2 }
        @{ Label = "Contact";    Slug = "{msdyn_contact_name}";  UniqueName = "${Prefix}_callpop_contact";   Order = 3 }
        @{ Label = "Tier";       Slug = "{msdyn_tier}";          UniqueName = "${Prefix}_callpop_tier";      Order = 4 }
        @{ Label = "Open Cases"; Slug = "{msdyn_open_cases}";    UniqueName = "${Prefix}_callpop_opencases"; Order = 5 }
        @{ Label = "Phone";      Slug = "{customerPhone}";       UniqueName = "${Prefix}_callpop_phone";     Order = 6 }
    )
    $titleSlug = "Incoming call from {customerName}"
}

# ============================================================
# 3. Create or update notification template
# ============================================================
Write-Host "`nChecking for existing template..." -ForegroundColor Yellow

$existing = Invoke-RestMethod -Uri "${apiUrl}msdyn_notificationtemplates?`$filter=msdyn_uniquename eq '$templateUniqueName'&`$select=msdyn_notificationtemplateid" -Headers $headers
$templateId = $null

$templateBody = @{
    msdyn_name                    = $templateName
    msdyn_uniquename              = $templateUniqueName
    msdyn_title                   = $titleSlug
    msdyn_icon                    = "/webresources/msdyn_oc/_imgs/notifications/phonecallicon.svg"
    msdyn_timeout                 = 120
    msdyn_showtimeout             = $true
    msdyn_acceptbuttontext        = "Accept"
    msdyn_rejectbuttontext        = "Reject"
    msdyn_desktopnotificationmode = 509180001   # Always show
} | ConvertTo-Json -Depth 5

if ($existing.value.Count -gt 0) {
    $templateId = $existing.value[0].msdyn_notificationtemplateid
    Write-Host "  Template exists: $templateId — updating..." -ForegroundColor DarkGray
    Invoke-RestMethod -Uri "${apiUrl}msdyn_notificationtemplates($templateId)" -Method Patch `
        -Headers $headers -Body $templateBody
    Write-Host "  Template updated ✓" -ForegroundColor Green
} else {
    Write-Host "  Creating notification template..." -ForegroundColor Yellow
    $resp = Invoke-WebRequest -Uri "${apiUrl}msdyn_notificationtemplates" -Method Post `
        -Headers $headers -Body $templateBody -UseBasicParsing
    $entityUri = [string]($resp.Headers["OData-EntityId"])
    if ($entityUri -match '\(([0-9a-f-]+)\)') { $templateId = $Matches[1] }
    Write-Host "  Created: $templateName ($templateId)" -ForegroundColor Green
}

# ============================================================
# 4. Create notification fields + associate via M2M
# ============================================================
# Notification fields are separate records (msdyn_notificationfields)
# linked to templates via M2M relationship: msdyn_notificationtemplate_notificationfield
Write-Host "`nConfiguring call pop fields..." -ForegroundColor Yellow

foreach ($field in $fieldDefinitions) {
    $fieldId = $null

    # Check if this field already exists
    $ef = Invoke-RestMethod -Uri "${apiUrl}msdyn_notificationfields?`$filter=msdyn_uniquename eq '$($field.UniqueName)'&`$select=msdyn_notificationfieldid" -Headers $headers
    if ($ef.value.Count -gt 0) {
        $fieldId = $ef.value[0].msdyn_notificationfieldid
        Write-Host "  $($field.Label): exists ($fieldId) — patching" -ForegroundColor DarkGray
        $patchBody = @{ msdyn_name = $field.Label; msdyn_title = $field.Label; msdyn_value = $field.Slug; msdyn_order = $field.Order } | ConvertTo-Json
        Invoke-RestMethod -Uri "${apiUrl}msdyn_notificationfields($fieldId)" -Method Patch -Headers $headers -Body $patchBody
    } else {
        $body = @{
            msdyn_name       = $field.Label
            msdyn_title      = $field.Label
            msdyn_value      = $field.Slug
            msdyn_uniquename = $field.UniqueName
            msdyn_order      = $field.Order
        } | ConvertTo-Json
        $resp = Invoke-WebRequest -Uri "${apiUrl}msdyn_notificationfields" -Method Post `
            -Headers $headers -Body $body -UseBasicParsing
        $entityUri = [string]($resp.Headers["OData-EntityId"])
        if ($entityUri -match '\(([0-9a-f-]+)\)') { $fieldId = $Matches[1] }
        Write-Host "  $($field.Label): $($field.Slug) → $fieldId ✓" -ForegroundColor Green
    }

    # Associate to template via M2M relationship
    $assocBody = (@{ "@odata.id" = "${apiUrl}msdyn_notificationfields($fieldId)" }) | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "${apiUrl}msdyn_notificationtemplates($templateId)/msdyn_notificationtemplate_notificationfield/`$ref" `
            -Method Post -Headers $headers -Body $assocBody
        Write-Host "    → linked to template ✓" -ForegroundColor Green
    } catch {
        $errBody = if ($_.ErrorDetails) { $_.ErrorDetails.Message } else { $_.Exception.Message }
        if ($errBody -like "*duplicate*" -or $errBody -like "*Cannot insert*") {
            Write-Host "    → already linked" -ForegroundColor DarkGray
        } else {
            Write-Host "    → link warning: $($errBody.Substring(0,[Math]::Min(120,$errBody.Length)))" -ForegroundColor Yellow
        }
    }
}

# ============================================================
# 5. Update voice workstreams
# ============================================================
if (-not $SkipWorkstreamUpdate) {
    Write-Host "`nUpdating voice workstream(s)..." -ForegroundColor Yellow

    if ($WorkstreamName -eq "ALL") {
        # Find all voice-related workstreams
        $allWs = Invoke-RestMethod -Uri "${apiUrl}msdyn_liveworkstreams?`$select=msdyn_liveworkstreamid,msdyn_name,msdyn_streamsource,msdyn_notificationtemplate_incoming_auth" -Headers $headers
        $voiceWs = $allWs.value | Where-Object {
            $_.msdyn_name -like "*voice*" -or $_.msdyn_name -like "*phone*" -or
            $_.msdyn_name -like "*call*" -or $_.msdyn_streamsource -eq 192440000
        } | Where-Object { $_.msdyn_name -notlike "*voicemail*" }
    } else {
        $voiceWs = @(Invoke-RestMethod -Uri "${apiUrl}msdyn_liveworkstreams?`$filter=msdyn_name eq '$WorkstreamName'&`$select=msdyn_liveworkstreamid,msdyn_name" -Headers $headers).value
    }

    if ($voiceWs -and $voiceWs.Count -gt 0) {
        foreach ($ws in $voiceWs) {
            $wsPatch = @{
                msdyn_notificationtemplate_incoming_auth   = $templateUniqueName
                msdyn_notificationtemplate_incoming_unauth = $templateUniqueName
            } | ConvertTo-Json
            try {
                Invoke-RestMethod -Uri "${apiUrl}msdyn_liveworkstreams($($ws.msdyn_liveworkstreamid))" -Method Patch `
                    -Headers $headers -Body $wsPatch
                Write-Host "  ✓ $($ws.msdyn_name)" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ $($ws.msdyn_name): $($_.Exception.Message.Substring(0,[Math]::Min(100,$_.Exception.Message.Length)))" -ForegroundColor Red
            }
        }
    } else {
        Write-Warning "No voice workstreams found matching '$WorkstreamName'."
        Write-Host "  To assign manually:" -ForegroundColor Yellow
        Write-Host "    1. Open D365 CS Admin Center" -ForegroundColor White
        Write-Host "    2. Go to Workstreams > [Your Voice Workstream]" -ForegroundColor White
        Write-Host "    3. Under Advanced Settings > Notification, select '$templateName'" -ForegroundColor White
    }
} else {
    Write-Host "`nSkipping workstream update (-SkipWorkstreamUpdate)" -ForegroundColor DarkGray
}

# ============================================================
# 6. Output summary and context variable guide
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host " CALL POP NOTIFICATION TEMPLATE — SETUP COMPLETE" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Template:  $templateName" -ForegroundColor Green
Write-Host "  ID:        $templateId" -ForegroundColor Green
Write-Host ""
Write-Host "  Fields displayed on incoming call:" -ForegroundColor Cyan
foreach ($f in $fieldDefinitions) {
    Write-Host "    $($f.Order). $($f.Label): $($f.Slug)" -ForegroundColor White
}

if ($UseCopilotStudioIVR) {
    Write-Host ""
    Write-Host "  ── Copilot Studio IVR Setup ──" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Your Copilot Studio voice bot must set these context variables" -ForegroundColor White
    Write-Host "  BEFORE transferring the call to an agent:" -ForegroundColor White
    Write-Host ""
    Write-Host "    Topic: 'Transfer to Agent'" -ForegroundColor White
    Write-Host "    Action: 'Transfer conversation'" -ForegroundColor White
    Write-Host "    Context variables to pass:" -ForegroundColor White
    Write-Host ""
    Write-Host "    ┌─────────────────────┬────────────────────────────────────┐" -ForegroundColor DarkGray
    Write-Host "    │ Variable Name       │ Source                             │" -ForegroundColor DarkGray
    Write-Host "    ├─────────────────────┼────────────────────────────────────┤" -ForegroundColor DarkGray
    Write-Host "    │ va_CustomerName     │ CRM lookup by phone → Account     │" -ForegroundColor White
    Write-Host "    │ va_AccountName      │ CRM lookup → account.name         │" -ForegroundColor White
    Write-Host "    │ va_ContactName      │ CRM lookup → contact.fullname     │" -ForegroundColor White
    Write-Host "    │ va_Tier             │ CRM lookup → account.new_tier     │" -ForegroundColor White
    Write-Host "    │ va_OpenCases        │ CRM query  → count open incidents │" -ForegroundColor White
    Write-Host "    │ va_Phone            │ System.Activity.From or ANI       │" -ForegroundColor White
    Write-Host "    └─────────────────────┴────────────────────────────────────┘" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  In Copilot Studio:" -ForegroundColor Yellow
    Write-Host "    1. Create a topic triggered by 'On Conversation Start'" -ForegroundColor White
    Write-Host "    2. Add a 'Search Dataverse' action to look up the caller" -ForegroundColor White
    Write-Host "       by phone number (contacts → telephone1 or mobilephone)" -ForegroundColor White
    Write-Host "    3. Set the va_* variables from the lookup results" -ForegroundColor White
    Write-Host "    4. For Open Cases count: query incidents where" -ForegroundColor White
    Write-Host "       _customerid_value = contact.contactid AND statecode = 0" -ForegroundColor White
    Write-Host "    5. In the 'Transfer conversation' node, add each va_*" -ForegroundColor White
    Write-Host "       variable under 'Context variables'" -ForegroundColor White
}
else {
    Write-Host ""
    Write-Host "  ── Native Voice Channel Setup ──" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Standard context variables (customerName, customerPhone)" -ForegroundColor White
    Write-Host "  are auto-populated by ANI matching." -ForegroundColor White
    Write-Host ""
    Write-Host "  For custom context keys (msdyn_tier, msdyn_open_cases, etc.):" -ForegroundColor White
    Write-Host "    1. Go to CS Admin Center → Workstreams → $WorkstreamName" -ForegroundColor White
    Write-Host "    2. Under 'Advanced settings' → 'Context variables'" -ForegroundColor White
    Write-Host "    3. Add each custom variable:" -ForegroundColor White
    Write-Host "       • msdyn_account_name  (Text)" -ForegroundColor White
    Write-Host "       • msdyn_contact_name  (Text)" -ForegroundColor White
    Write-Host "       • msdyn_tier          (Text)" -ForegroundColor White
    Write-Host "       • msdyn_open_cases    (Text)" -ForegroundColor White
    Write-Host ""
    Write-Host "  These variables can be populated by:" -ForegroundColor White
    Write-Host "    • Pre-conversation survey" -ForegroundColor White
    Write-Host "    • Power Automate flow on conversation create" -ForegroundColor White
    Write-Host "    • Custom channel integration API" -ForegroundColor White
    Write-Host "    • Copilot Studio bot (see -UseCopilotStudioIVR flag)" -ForegroundColor White
}

Write-Host ""
Write-Host "  ── Verify in D365 ──" -ForegroundColor Cyan
Write-Host "  1. Open CS Admin Center → Workspaces → Notification templates" -ForegroundColor White
Write-Host "  2. Find '$templateName' — confirm all 6 fields appear" -ForegroundColor White
Write-Host "  3. Test: Make a phone call to the configured phone number" -ForegroundColor White
Write-Host "  4. Agent should see the call pop with Customer, Account," -ForegroundColor White
Write-Host "     Contact, Tier, Open Cases, and Phone." -ForegroundColor White
Write-Host ""

# ============================================================
# 7. Save template ID for other scripts
# ============================================================
$dataDir = Join-Path $scriptDir "..\data"
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir -Force | Out-Null }

$callPopConfig = @{
    templateId         = $templateId
    templateUniqueName = $templateUniqueName
    templateName       = $templateName
    mode               = if ($UseCopilotStudioIVR) { "CopilotStudioIVR" } else { "NativeVoiceChannel" }
    fields             = $fieldDefinitions
    createdAt          = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
}

$callPopConfig | ConvertTo-Json -Depth 5 | Set-Content "$dataDir\callpop-template.json" -Encoding UTF8
Write-Host "  Saved template config → data\callpop-template.json" -ForegroundColor DarkGray
Write-Host ""
