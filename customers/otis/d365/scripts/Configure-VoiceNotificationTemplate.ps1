<#
.SYNOPSIS
    Configures a rich voice call notification template for Otis EMEA demo.
.DESCRIPTION
    Creates/updates the voice channel notification template in D365 Customer Service
    to show enriched caller context:
      - Customer Name (from phone number matching)
      - Account Name
      - Service Tier
      - Open Cases count
      - Phone Number
    
    Also creates context variables on the voice workstream so these fields
    can be populated by a Copilot Studio bot or Power Automate flow.

    PREREQUISITES:
      - az login completed
      - Voice channel provisioned in D365 CS
      - DataverseHelper.psm1 in parent scripts folder

.EXAMPLE
    .\Configure-VoiceNotificationTemplate.ps1
    .\Configure-VoiceNotificationTemplate.ps1 -WorkstreamName "Voice - Otis EMEA"
#>

[CmdletBinding()]
param(
    [string]$WorkstreamName = "Voice",  # Name/partial match of your voice workstream
    [string]$TemplateName = "Otis Voice - Rich Context"
)

# ── Load helper ────────────────────────────────────────────────
$helperPath = Join-Path $PSScriptRoot "..\..\..\..\d365\scripts\DataverseHelper.psm1"
if (-not (Test-Path $helperPath)) {
    $helperPath = Join-Path $PSScriptRoot "..\..\..\d365\scripts\DataverseHelper.psm1"
}
if (-not (Test-Path $helperPath)) {
    Write-Error "Cannot find DataverseHelper.psm1. Run from customers/otis/d365/scripts/ directory."
    exit 1
}
Import-Module $helperPath -Force
Connect-Dataverse

$apiUrl = Get-DataverseApiUrl
$headers = Get-DataverseHeaders

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Otis EMEA — Rich Voice Notification Template Setup" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# ============================================================
# Step 1: Find the Voice Workstream
# ============================================================
Write-Host "Step 1: Finding Voice workstream..." -ForegroundColor Yellow

$workstreams = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
    -Filter "contains(msdyn_name,'$WorkstreamName')" `
    -Select "msdyn_liveworkstreamid,msdyn_name,msdyn_streamsource"

if (-not $workstreams -or $workstreams.Count -eq 0) {
    Write-Warning "No workstream found matching '$WorkstreamName'."
    Write-Host "  Listing all workstreams:" -ForegroundColor DarkGray
    $allWs = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
        -Select "msdyn_liveworkstreamid,msdyn_name,msdyn_streamsource"
    if ($allWs) {
        foreach ($ws in $allWs) {
            Write-Host "    - $($ws.msdyn_name) (source=$($ws.msdyn_streamsource), id=$($ws.msdyn_liveworkstreamid))" -ForegroundColor DarkGray
        }
    }
    Write-Host "`n  Re-run with: -WorkstreamName 'YourVoiceWorkstreamName'" -ForegroundColor Yellow
} else {
    $voiceWs = $workstreams[0]
    $wsId = $voiceWs.msdyn_liveworkstreamid
    Write-Host "  Found: $($voiceWs.msdyn_name) ($wsId)" -ForegroundColor Green
}

# ============================================================
# Step 2: Query existing notification templates
# ============================================================
Write-Host "`nStep 2: Querying notification templates..." -ForegroundColor Yellow

$templates = Invoke-DataverseGet -EntitySet "msdyn_consoleapplicationnotificationtemplates" `
    -Select "msdyn_consoleapplicationnotificationtemplateid,msdyn_name,msdyn_title,msdyn_timeout" `
    -Filter "contains(msdyn_name,'voice') or contains(msdyn_name,'Voice') or contains(msdyn_name,'Otis')"

if ($templates -and $templates.Count -gt 0) {
    Write-Host "  Existing voice/Otis templates:" -ForegroundColor DarkGray
    foreach ($t in $templates) {
        Write-Host "    - $($t.msdyn_name) | title=$($t.msdyn_title) | timeout=$($t.msdyn_timeout)s | id=$($t.msdyn_consoleapplicationnotificationtemplateid)" -ForegroundColor DarkGray
    }
}

# Also list ALL templates for reference
$allTemplates = Invoke-DataverseGet -EntitySet "msdyn_consoleapplicationnotificationtemplates" `
    -Select "msdyn_consoleapplicationnotificationtemplateid,msdyn_name,msdyn_title"
if ($allTemplates) {
    Write-Host "`n  All notification templates in environment:" -ForegroundColor DarkGray
    foreach ($t in $allTemplates) {
        Write-Host "    - $($t.msdyn_name) | $($t.msdyn_title) | $($t.msdyn_consoleapplicationnotificationtemplateid)" -ForegroundColor DarkGray
    }
}

# ============================================================
# Step 3: Create/Update Rich Notification Template
# ============================================================
Write-Host "`nStep 3: Creating rich notification template..." -ForegroundColor Yellow

# Check if our custom template already exists
$existing = Invoke-DataverseGet -EntitySet "msdyn_consoleapplicationnotificationtemplates" `
    -Filter "msdyn_name eq '$TemplateName'" `
    -Select "msdyn_consoleapplicationnotificationtemplateid" -Top 1

$templateBody = @{
    msdyn_name                     = $TemplateName
    msdyn_title                    = "Incoming Voice Call — {customerName}"
    msdyn_timeout                  = 120          # 2 minutes countdown
    msdyn_desktopnotificationmode  = 192350000    # Always
    msdyn_acceptbuttontext         = "Accept"
    msdyn_rejectbuttontext         = "Reject"
    msdyn_showreject               = $true
    msdyn_autoacceptvoicecall      = $false
    msdyn_uniquename               = "otis_voice_rich_context"
}

if ($existing -and $existing.Count -gt 0) {
    $templateId = $existing[0].msdyn_consoleapplicationnotificationtemplateid
    Write-Host "  Updating existing template: $templateId" -ForegroundColor DarkGray
    Invoke-DataversePatch -EntitySet "msdyn_consoleapplicationnotificationtemplates" `
        -RecordId $templateId -Body $templateBody
} else {
    Write-Host "  Creating new template: $TemplateName" -ForegroundColor Green
    $result = Invoke-DataversePost -EntitySet "msdyn_consoleapplicationnotificationtemplates" `
        -Body $templateBody
    if ($result) {
        if ($result.msdyn_consoleapplicationnotificationtemplateid) {
            $templateId = $result.msdyn_consoleapplicationnotificationtemplateid
        } else {
            try { $templateId = [string]$result } catch { }
        }
    }
    
    # Fallback: re-query
    if (-not $templateId) {
        $refetch = Invoke-DataverseGet -EntitySet "msdyn_consoleapplicationnotificationtemplates" `
            -Filter "msdyn_name eq '$TemplateName'" `
            -Select "msdyn_consoleapplicationnotificationtemplateid" -Top 1
        if ($refetch -and $refetch.Count -gt 0) {
            $templateId = $refetch[0].msdyn_consoleapplicationnotificationtemplateid
        }
    }
}

if ($templateId) {
    Write-Host "  Template ID: $templateId" -ForegroundColor Green
} else {
    Write-Error "Failed to create/find notification template. Stopping."
    exit 1
}

# ============================================================
# Step 4: Add Notification Fields
# ============================================================
Write-Host "`nStep 4: Adding notification fields..." -ForegroundColor Yellow

# Remove existing fields for this template first (clean slate)
$existingFields = Invoke-DataverseGet -EntitySet "msdyn_consoleapplicationnotificationfields" `
    -Filter "_msdyn_consoleapplicationnotificationtemplateid_value eq '$templateId'" `
    -Select "msdyn_consoleapplicationnotificationfieldid,msdyn_name"

if ($existingFields -and $existingFields.Count -gt 0) {
    Write-Host "  Removing $($existingFields.Count) existing fields..." -ForegroundColor DarkGray
    foreach ($f in $existingFields) {
        Invoke-DataverseDelete -EntitySet "msdyn_consoleapplicationnotificationfields" `
            -RecordId $f.msdyn_consoleapplicationnotificationfieldid | Out-Null
    }
}

# Define the fields we want on the notification pop-up
# Slugs: {customerName} is resolved from phone matching → Contact → Account
# Custom context vars (populated by bot/flow): {AccountName}, {TierLevel}, {OpenCases}
$notificationFields = @(
    @{ Name = "Customer";     Value = "{customerName}";  Order = 1 }
    @{ Name = "Account";      Value = "{AccountName}";   Order = 2 }
    @{ Name = "Service Tier"; Value = "{TierLevel}";     Order = 3 }
    @{ Name = "Open Cases";   Value = "{OpenCases}";     Order = 4 }
    @{ Name = "Phone";        Value = "{PhoneNumber}";   Order = 5 }
    @{ Name = "Countdown";    Value = "{countdown}";     Order = 6 }
)

foreach ($field in $notificationFields) {
    $fieldBody = @{
        msdyn_name  = $field.Name
        msdyn_value = $field.Value
        msdyn_order = $field.Order
        "msdyn_consoleapplicationnotificationtemplateid@odata.bind" = "/msdyn_consoleapplicationnotificationtemplates($templateId)"
    }
    
    $result = Invoke-DataversePost -EntitySet "msdyn_consoleapplicationnotificationfields" -Body $fieldBody
    if ($result) {
        Write-Host "  + $($field.Name) = $($field.Value)" -ForegroundColor Green
    } else {
        Write-Warning "  Failed to add field: $($field.Name)"
    }
}

# ============================================================
# Step 5: Create Context Variables on Voice Workstream 
# ============================================================
if ($wsId) {
    Write-Host "`nStep 5: Creating context variables on workstream..." -ForegroundColor Yellow
    
    $contextVars = @(
        @{ Name = "AccountName"; Type = 192350000; DisplayName = "Account Name" }       # String type
        @{ Name = "TierLevel";   Type = 192350000; DisplayName = "Service Tier Level" }  # String type
        @{ Name = "OpenCases";   Type = 192350000; DisplayName = "Open Cases Count" }    # String type
        @{ Name = "PhoneNumber"; Type = 192350000; DisplayName = "Caller Phone" }        # String type
    )
    
    foreach ($cv in $contextVars) {
        # Check if already exists
        $existingCv = Invoke-DataverseGet -EntitySet "msdyn_ocliveworkstreamcontextvariables" `
            -Filter "msdyn_name eq '$($cv.Name)' and _msdyn_liveworkstreamid_value eq '$wsId'" `
            -Select "msdyn_ocliveworkstreamcontextvariableid" -Top 1
        
        if ($existingCv -and $existingCv.Count -gt 0) {
            Write-Host "  Already exists: $($cv.Name)" -ForegroundColor DarkGray
        } else {
            $cvBody = @{
                msdyn_name        = $cv.Name
                msdyn_displayname = $cv.DisplayName
                msdyn_datatype    = $cv.Type
                msdyn_issystemdefined = $false
                "msdyn_liveworkstreamid@odata.bind" = "/msdyn_liveworkstreams($wsId)"
            }
            
            $result = Invoke-DataversePost -EntitySet "msdyn_ocliveworkstreamcontextvariables" -Body $cvBody
            if ($result) {
                Write-Host "  + Context variable: $($cv.Name)" -ForegroundColor Green
            } else {
                Write-Warning "  Failed to create context variable: $($cv.Name)"
            }
        }
    }
} else {
    Write-Host "`nStep 5: SKIPPED — No workstream found. Context variables must be created manually." -ForegroundColor Yellow
    Write-Host "  Go to: CS Admin Center > Workstreams > [Your Voice Workstream] > Advanced Settings > Context Variables" -ForegroundColor DarkGray
}

# ============================================================
# Step 6: Summary and Next Steps
# ============================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Setup Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Notification Template: $TemplateName" -ForegroundColor White
Write-Host "  Template ID:           $templateId" -ForegroundColor White
if ($wsId) {
    Write-Host "  Voice Workstream:      $($voiceWs.msdyn_name) ($wsId)" -ForegroundColor White
}
Write-Host ""
Write-Host "  Fields configured:" -ForegroundColor White
foreach ($f in $notificationFields) {
    Write-Host "    $($f.Name) = $($f.Value)" -ForegroundColor DarkGray
}

Write-Host "`n  ╔════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "  ║  MANUAL STEPS REQUIRED (CS Admin Center)              ║" -ForegroundColor Yellow
Write-Host "  ╚════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. ASSIGN TEMPLATE TO WORKSTREAM:" -ForegroundColor White
Write-Host "     CS Admin Center > Workstreams > [Voice Workstream]" -ForegroundColor DarkGray
Write-Host "     > Advanced Settings > Notification" -ForegroundColor DarkGray
Write-Host "     > Set 'Incoming authenticated' to: '$TemplateName'" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. CONFIGURE COPILOT STUDIO BOT (for dynamic context):" -ForegroundColor White
Write-Host "     To populate AccountName, TierLevel, and OpenCases dynamically," -ForegroundColor DarkGray
Write-Host "     add a Copilot Studio bot as first responder on the workstream." -ForegroundColor DarkGray
Write-Host "     The bot should:" -ForegroundColor DarkGray
Write-Host "       a. Get the caller phone number" -ForegroundColor DarkGray
Write-Host "       b. Call a Power Automate flow that:" -ForegroundColor DarkGray
Write-Host "          - Looks up Contact by phone" -ForegroundColor DarkGray
Write-Host "          - Gets parent Account name + tier" -ForegroundColor DarkGray
Write-Host "          - Counts active cases for the account" -ForegroundColor DarkGray
Write-Host "       c. Set context variables: AccountName, TierLevel, OpenCases" -ForegroundColor DarkGray
Write-Host "       d. Transfer to agent (notification fires with populated context)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. VERIFY PHONE NUMBER MATCHING:" -ForegroundColor White
Write-Host "     CS Admin Center > Workstreams > [Voice Workstream]" -ForegroundColor DarkGray
Write-Host "     > Advanced Settings > Identify the caller using phone number" -ForegroundColor DarkGray
Write-Host "     Ensure 'Identify' is set to 'Contact' entity" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  See: customers/otis/d365/demo-assets-v2/notification-setup-guide.md" -ForegroundColor DarkGray
Write-Host "       for complete step-by-step instructions." -ForegroundColor DarkGray
Write-Host ""
