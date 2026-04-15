<#
.SYNOPSIS
    ERAC Lite CRM — Dataverse provisioning script
    Creates custom columns on OOTB tables, provisions custom tables, and seeds demo data.

.DESCRIPTION
    Filtering strategy: erac_iscedent = true on Account table.
    All ERAC views and queries filter on this field so demo data stays isolated
    in shared/multi-customer org environments.

.PARAMETER OrgUrl
    Dataverse org URL, e.g. https://orgXXXXXX.crm.dynamics.com

.PARAMETER Phase
    Which phase to run: Schema | Data | Views | All (default: All)

.PARAMETER SkipSchema
    Skip schema creation (use if already run once)

.EXAMPLE
    .\Provision-EracDataverse.ps1 -OrgUrl "https://orgabc123.crm.dynamics.com"
    .\Provision-EracDataverse.ps1 -OrgUrl "https://orgabc123.crm.dynamics.com" -Phase Data
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$OrgUrl,

    [ValidateSet("Schema","Data","Views","All")]
    [string]$Phase = "All",

    [switch]$SkipSchema,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$ApiUrl = "$OrgUrl/api/data/v9.2"
$PublisherPrefix = "erac"
$OutputDir = "$PSScriptRoot\..\data"
New-Item -ItemType Directory -Force $OutputDir | Out-Null

# ─────────────────────────────────────────────
# AUTH — uses az cli token (run `az login` first)
# ─────────────────────────────────────────────
function Get-DataverseToken {
    $resource = $OrgUrl.TrimEnd('/')
    $tokenJson = az account get-access-token --resource $resource 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Auth failed. Run: az login --scope $resource/.default"
    }
    return ($tokenJson | ConvertFrom-Json).accessToken
}

function Get-Headers {
    $token = Get-DataverseToken
    return @{
        "Authorization"    = "Bearer $token"
        "Accept"           = "application/json"
        "Content-Type"     = "application/json; charset=utf-8"
        "OData-MaxVersion" = "4.0"
        "OData-Version"    = "4.0"
        "Prefer"           = "return=representation"
    }
}

function Invoke-Dv {
    param([string]$Method, [string]$Path, [object]$Body)
    $headers = Get-Headers
    $uri = "$ApiUrl/$Path"
    if ($WhatIf) { Write-Host "[WhatIf] $Method $uri"; return $null }
    try {
        if ($Body) {
            return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body ($Body | ConvertTo-Json -Depth 10) -TimeoutSec 30
        } else {
            return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -TimeoutSec 30
        }
    } catch {
        $msg = $_.Exception.Message
        if ($msg -match "already exists|duplicate") {
            Write-Host "  ↳ Already exists, skipping" -ForegroundColor DarkGray
            return $null
        }
        Write-Warning "  ↳ API error: $msg"
        return $null
    }
}

# ─────────────────────────────────────────────
# SCHEMA — Column definitions
# ─────────────────────────────────────────────
function Add-ChoiceColumn {
    param([string]$Table, [string]$Column, [string]$Display, [string[]]$Choices)
    Write-Host "  Adding choice column: $Column"
    $options = @()
    $val = 200000
    foreach ($c in $Choices) {
        $options += @{ Value = $val; Label = @{ LocalizedLabels = @(@{ Label = $c; LanguageCode = 1033 }) } }
        $val += 1
    }
    $body = @{
        "@odata.type"   = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
        SchemaName      = $Column
        DisplayName     = @{ LocalizedLabels = @(@{ Label = $Display; LanguageCode = 1033 }) }
        RequiredLevel   = @{ Value = "None" }
        OptionSet       = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.OptionSetMetadata"
            IsGlobal      = $false
            OptionSetType = "Picklist"
            Options       = $options
        }
    }
    Invoke-Dv -Method POST -Path "EntityDefinitions(LogicalName='$Table')/Attributes" -Body $body | Out-Null
}

function Add-DecimalColumn {
    param([string]$Table, [string]$Column, [string]$Display, [double]$Min=0, [double]$Max=100, [int]$Precision=2)
    Write-Host "  Adding decimal column: $Column"
    $body = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
        SchemaName    = $Column
        DisplayName   = @{ LocalizedLabels = @(@{ Label = $Display; LanguageCode = 1033 }) }
        RequiredLevel = @{ Value = "None" }
        MinValue      = $Min
        MaxValue      = $Max
        Precision     = $Precision
    }
    Invoke-Dv -Method POST -Path "EntityDefinitions(LogicalName='$Table')/Attributes" -Body $body | Out-Null
}

function Add-BooleanColumn {
    param([string]$Table, [string]$Column, [string]$Display)
    Write-Host "  Adding boolean column: $Column"
    $body = @{
        "@odata.type"  = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
        SchemaName     = $Column
        DisplayName    = @{ LocalizedLabels = @(@{ Label = $Display; LanguageCode = 1033 }) }
        RequiredLevel  = @{ Value = "None" }
        DefaultValue   = $false
        OptionSet      = @{
            TrueOption  = @{ Value = 1; Label = @{ LocalizedLabels = @(@{ Label = "Yes"; LanguageCode = 1033 }) } }
            FalseOption = @{ Value = 0; Label = @{ LocalizedLabels = @(@{ Label = "No"; LanguageCode = 1033 }) } }
        }
    }
    Invoke-Dv -Method POST -Path "EntityDefinitions(LogicalName='$Table')/Attributes" -Body $body | Out-Null
}

function Add-DateColumn {
    param([string]$Table, [string]$Column, [string]$Display)
    Write-Host "  Adding date column: $Column"
    $body = @{
        "@odata.type"  = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
        SchemaName     = $Column
        DisplayName    = @{ LocalizedLabels = @(@{ Label = $Display; LanguageCode = 1033 }) }
        RequiredLevel  = @{ Value = "None" }
        Format         = "DateOnly"
    }
    Invoke-Dv -Method POST -Path "EntityDefinitions(LogicalName='$Table')/Attributes" -Body $body | Out-Null
}

function Add-TextColumn {
    param([string]$Table, [string]$Column, [string]$Display, [int]$MaxLength=200)
    Write-Host "  Adding text column: $Column"
    $body = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        SchemaName    = $Column
        DisplayName   = @{ LocalizedLabels = @(@{ Label = $Display; LanguageCode = 1033 }) }
        RequiredLevel = @{ Value = "None" }
        MaxLength     = $MaxLength
    }
    Invoke-Dv -Method POST -Path "EntityDefinitions(LogicalName='$Table')/Attributes" -Body $body | Out-Null
}

function Publish-Changes {
    Write-Host "  Publishing customizations..." -ForegroundColor Cyan
    Invoke-Dv -Method POST -Path "PublishAllXml" -Body @{} | Out-Null
}

# ─────────────────────────────────────────────
# SCHEMA PHASE
# ─────────────────────────────────────────────
function Invoke-SchemaPhase {
    Write-Host "`n=== SCHEMA PHASE ===" -ForegroundColor Cyan

    # 1. Account — cedent tag + ERAC columns
    Write-Host "`n[Account] Adding ERAC columns..." -ForegroundColor Yellow
    Add-BooleanColumn  "account" "erac_iscedent"        "Is Reinsurance Cedent"
    Add-ChoiceColumn   "account" "erac_partnershiptype" "Partnership Type"    @("Strategic","Advisory","Tactical","Transactional")
    Add-DecimalColumn  "account" "erac_portfoliopct"    "Portfolio %"         0 100 1
    Add-ChoiceColumn   "account" "erac_tier"            "Cedent Tier"         @("Tier 1","Tier 2","Tier 3")
    Add-DecimalColumn  "account" "erac_overallrating"   "PRR Overall Rating"  0 5 2
    Add-DateColumn     "account" "erac_lastqbrdate"     "Last QBR Date"
    Add-ChoiceColumn   "account" "erac_ratingtrend"     "Rating Trend"        @("Improving","Stable","Declining")

    # 2. Contact — ERAC columns
    Write-Host "`n[Contact] Adding ERAC columns..." -ForegroundColor Yellow
    Add-ChoiceColumn  "contact" "erac_contacttier"      "Contact Tier"        @("Executive","Tier 1","Tier 2","Tier 3")
    Add-ChoiceColumn  "contact" "erac_function"         "Function"            @("Claims","Actuarial","Legal","Finance","Data","Operations","Executive")
    Add-DateColumn    "contact" "erac_lastcontactdate"  "Last Contact Date"
    Add-ChoiceColumn  "contact" "erac_preferredchannel" "Preferred Channel"   @("Email","Phone","Teams","Portal")

    # 3. Task — Kanban columns
    Write-Host "`n[Task] Adding ERAC Kanban columns..." -ForegroundColor Yellow
    Add-ChoiceColumn  "task" "erac_kanbanstage"        "Kanban Stage"         @("Backlog","Planning","Executing","Done")
    Add-ChoiceColumn  "task" "erac_engagementtype"     "Engagement Type"      @("Risk","Claims","Legal","Data Integration","Strategic","Program")

    # 4. Appointment — Engagement meeting columns
    Write-Host "`n[Appointment] Adding ERAC meeting columns..." -ForegroundColor Yellow
    Add-ChoiceColumn  "appointment" "erac_meetingtype"  "Meeting Type"        @("QBR","Claims Review","Treaty Renewal","Risk Review","Ad Hoc","Executive Summit")
    Add-ChoiceColumn  "appointment" "erac_outcome"      "Outcome"             @("Positive","Neutral","Escalation Required","Follow-up Needed")

    Publish-Changes
    Write-Host "`n✅ Schema phase complete" -ForegroundColor Green
}

# ─────────────────────────────────────────────
# DATA PHASE — Seed demo accounts (cedents)
# ─────────────────────────────────────────────
function Invoke-DataPhase {
    Write-Host "`n=== DATA PHASE ===" -ForegroundColor Cyan

    $demoData = Get-Content "$PSScriptRoot\..\data\demo-accounts.json" -Raw | ConvertFrom-Json

    $accountIds = @{}

    # Create Accounts (Cedents)
    Write-Host "`n[Accounts] Seeding $($demoData.accounts.Count) cedents..." -ForegroundColor Yellow
    foreach ($acct in $demoData.accounts) {
        Write-Host "  Creating: $($acct.name)"
        $body = @{
            name                    = $acct.name
            erac_iscedent           = $true
            erac_partnershiptype    = $acct.partnershipTypeValue
            erac_tier               = $acct.tierValue
            erac_portfoliopct       = $acct.portfolioPct
            erac_overallrating      = $acct.overallRating
            erac_ratingtrend        = $acct.ratingTrendValue
            industrycode            = 14   # Insurance
            accountcategorycode     = 1    # Preferred Customer
            description             = $acct.description
        }
        $result = Invoke-Dv -Method POST -Path "accounts" -Body $body
        if ($result) { $accountIds[$acct.id] = $result.accountid }
    }

    # Save account ID map
    $accountIds | ConvertTo-Json | Set-Content "$OutputDir\account-ids.json"
    Write-Host "  Saved account ID map → data\account-ids.json"

    # Create Contacts
    Write-Host "`n[Contacts] Seeding $($demoData.contacts.Count) contacts..." -ForegroundColor Yellow
    foreach ($contact in $demoData.contacts) {
        $accountId = $accountIds[$contact.cedentId]
        if (-not $accountId) { Write-Warning "  Skipping $($contact.fullName) — cedent not found"; continue }
        Write-Host "  Creating: $($contact.fullName)"
        $body = @{
            firstname               = $contact.firstName
            lastname                = $contact.lastName
            jobtitle                = $contact.title
            "parentcustomerid_account@odata.bind" = "/accounts($accountId)"
            emailaddress1           = $contact.email
            erac_function           = $contact.functionValue
            erac_contacttier        = $contact.tierValue
            erac_preferredchannel   = $contact.channelValue
        }
        Invoke-Dv -Method POST -Path "contacts" -Body $body | Out-Null
    }

    Write-Host "`n✅ Data phase complete" -ForegroundColor Green
}

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
Write-Host "ERAC Lite CRM — Dataverse Provisioner" -ForegroundColor Cyan
Write-Host "Org: $OrgUrl"
Write-Host "Phase: $Phase"
if ($WhatIf) { Write-Host "Mode: WhatIf (no changes will be made)" -ForegroundColor Yellow }

switch ($Phase) {
    "Schema" { Invoke-SchemaPhase }
    "Data"   { Invoke-DataPhase }
    "All"    { if (-not $SkipSchema) { Invoke-SchemaPhase }; Invoke-DataPhase }
}

Write-Host "`n🎉 Done!" -ForegroundColor Green
