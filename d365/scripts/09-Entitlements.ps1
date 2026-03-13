<#
.SYNOPSIS
    Step 09 - Create Entitlements for Zurn Elkay Demo
.DESCRIPTION
    Creates tier-based entitlements for each distributor account.
    Entitlements define the support terms each customer receives based
    on their tier (1-4), driving SLA behavior, KB access levels,
    and channel allocation.

    Tier 1 (Strategic): 500 cases/year, Premium KB, all channels, no restriction
    Tier 2 (Key):       250 cases/year, Premium KB, all channels, no restriction
    Tier 3 (Standard):  100 cases/year, Standard KB, all channels, restrict at limit
    Tier 4 (Basic):      50 cases/year, Standard KB, email + web only, restrict at limit

    Also creates four Entitlement Templates (one per tier) visible in
    the Admin Center for demo purposes.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "09" "Create Entitlements (Tier 1-4)"
Connect-Dataverse

# ============================================================
# Load config
# ============================================================
$config = Get-Content "$scriptDir\..\config\environment.json" | ConvertFrom-Json

# ============================================================
# Option set values (Dataverse standard)
# ============================================================
$ALLOCATION_CASES = 0
$KB_STANDARD = 0
$KB_PREMIUM = 1
$ENTITY_TYPE_CASE = 0
$DECREASE_ON_CREATE = 1   # Decrease remaining on case creation
$CHANNEL_PHONE = 1
$CHANNEL_EMAIL = 2
$CHANNEL_WEB = 3

# ============================================================
# Tier definitions
# ============================================================
$tierDefs = @{
    "1" = @{
        label           = "Strategic Support"
        totalCases      = 500
        kbAccess        = $KB_PREMIUM
        restrictAtLimit = $false
        description     = "Tier 1 Strategic - 500 cases/year, Premium KB access, all channels. Highest SLA priority."
        channels        = @(
            @{ type = $CHANNEL_PHONE; cases = 200; name = "Phone" }
            @{ type = $CHANNEL_EMAIL; cases = 200; name = "Email" }
            @{ type = $CHANNEL_WEB; cases = 100; name = "Web" }
        )
    }
    "2" = @{
        label           = "Key Account Support"
        totalCases      = 250
        kbAccess        = $KB_PREMIUM
        restrictAtLimit = $false
        description     = "Tier 2 Key Account - 250 cases/year, Premium KB access, all channels."
        channels        = @(
            @{ type = $CHANNEL_PHONE; cases = 100; name = "Phone" }
            @{ type = $CHANNEL_EMAIL; cases = 100; name = "Email" }
            @{ type = $CHANNEL_WEB; cases = 50; name = "Web" }
        )
    }
    "3" = @{
        label           = "Standard Support"
        totalCases      = 100
        kbAccess        = $KB_STANDARD
        restrictAtLimit = $true
        description     = "Tier 3 Standard - 100 cases/year, Standard KB access. Case creation restricted at limit."
        channels        = @(
            @{ type = $CHANNEL_PHONE; cases = 30; name = "Phone" }
            @{ type = $CHANNEL_EMAIL; cases = 50; name = "Email" }
            @{ type = $CHANNEL_WEB; cases = 20; name = "Web" }
        )
    }
    "4" = @{
        label           = "Basic Support"
        totalCases      = 50
        kbAccess        = $KB_STANDARD
        restrictAtLimit = $true
        description     = "Tier 4 Basic - 50 cases/year, Standard KB access, email and web only. Restricted at limit."
        channels        = @(
            @{ type = $CHANNEL_EMAIL; cases = 40; name = "Email" }
            @{ type = $CHANNEL_WEB; cases = 10; name = "Web" }
        )
    }
}

# ============================================================
# Date range for entitlements (fiscal year)
# ============================================================
$startDate = "2025-07-01T00:00:00Z"
$endDate = "2026-06-30T23:59:59Z"

# ============================================================
# 1. Look up the Zurn Elkay SLA
# ============================================================
Write-Host "Looking up SLA..." -ForegroundColor Yellow
$slaRecords = Invoke-DataverseGet -EntitySet "slas" `
    -Filter "name eq 'Zurn Elkay Standard SLA'" `
    -Select "slaid,name" -Top 1

$slaId = $null
if ($slaRecords -and $slaRecords.Count -gt 0) {
    $slaId = $slaRecords[0].slaid
    Write-Host "  SLA: $($slaRecords[0].name) ($slaId)" -ForegroundColor DarkGray
} else {
    Write-Warning "SLA 'Zurn Elkay Standard SLA' not found. Entitlements will be created without SLA binding."
}

# ============================================================
# 2. Look up transaction currency (required for entitlement channels)
# ============================================================
Write-Host "Looking up transaction currency..." -ForegroundColor Yellow
$currencies = Invoke-DataverseGet -EntitySet "transactioncurrencies" `
    -Filter "isocurrencycode eq 'USD'" `
    -Select "transactioncurrencyid" -Top 1

$currencyId = $null
if ($currencies -and $currencies.Count -gt 0) {
    $currencyId = $currencies[0].transactioncurrencyid
    Write-Host "  Currency (USD): $currencyId" -ForegroundColor DarkGray
}

# ============================================================
# 3. Get distributor accounts with their tier
# ============================================================
Write-Host "`nQuerying distributor accounts..." -ForegroundColor Yellow

$allDistributors = Invoke-DataverseGet -EntitySet "accounts" `
    -Filter "startswith(accountnumber,'TIER-')" `
    -Select "accountid,name,accountnumber"

# De-duplicate by name (keep first occurrence)
$distributorMap = @{}
foreach ($acct in $allDistributors) {
    $tier = $acct.accountnumber -replace 'TIER-', ''
    if (-not $distributorMap.ContainsKey($acct.name)) {
        $distributorMap[$acct.name] = @{
            id   = $acct.accountid
            name = $acct.name
            tier = $tier
        }
    }
}

Write-Host "  Found $($distributorMap.Count) unique distributors across $(($allDistributors | Measure-Object).Count) records" -ForegroundColor DarkGray
$distributorMap.GetEnumerator() | Sort-Object { $_.Value.tier }, { $_.Key } | ForEach-Object {
    Write-Host "    Tier $($_.Value.tier): $($_.Key)" -ForegroundColor DarkGray
}

# ============================================================
# 4. Create Entitlement Templates (one per tier, for Admin demo)
# ============================================================
Write-Host "`nCreating entitlement templates..." -ForegroundColor Yellow

$templateIds = @{}
foreach ($tier in "1", "2", "3", "4") {
    $def = $tierDefs[$tier]
    $templateName = "Zurn Elkay $($def.label) Template"

    $templateBody = @{
        name                 = $templateName
        description          = $def.description
        totalterms           = [decimal]$def.totalCases
        allocationtypecode   = $ALLOCATION_CASES
        kbaccesslevel        = $def.kbAccess
        entitytype           = $ENTITY_TYPE_CASE
        decreaseremainingon  = $DECREASE_ON_CREATE
        restrictcasecreation = $def.restrictAtLimit
        startdate            = $startDate
        enddate              = $endDate
    }

    if ($slaId) {
        $templateBody["slaid@odata.bind"] = "/slas($slaId)"
    }

    $tplId = Find-OrCreate-Record `
        -EntitySet "entitlementtemplates" `
        -Filter "name eq '$templateName'" `
        -IdField "entitlementtemplateid" `
        -Body $templateBody `
        -DisplayName $templateName

    if ($tplId) {
        $templateIds[$tier] = $tplId
    }
}

Write-Host "  Templates created: $($templateIds.Count)" -ForegroundColor Green

# ============================================================
# 5. Create Entitlements per Distributor Account
# ============================================================
Write-Host "`nCreating entitlements for distributor accounts..." -ForegroundColor Yellow

$entitlementIds = @{}
$channelResults = @{ created = 0; skipped = 0; failed = 0 }

foreach ($entry in ($distributorMap.GetEnumerator() | Sort-Object { $_.Value.tier }, { $_.Key })) {
    $acctName = $entry.Key
    $acctId = $entry.Value.id
    $tier = $entry.Value.tier
    $def = $tierDefs[$tier]

    $entName = "$acctName - $($def.label)"

    Write-Host "  [$entName]" -ForegroundColor Cyan

    # Escape single quotes in account names for filter
    $escapedEntName = $entName.Replace("'", "''")

    $entBody = @{
        name                            = $entName
        description                     = "$($def.description) Account: $acctName."
        "customerid_account@odata.bind" = "/accounts($acctId)"
        totalterms                      = [decimal]$def.totalCases
        remainingterms                  = [decimal]$def.totalCases
        allocationtypecode              = $ALLOCATION_CASES
        kbaccesslevel                   = $def.kbAccess
        entitytype                      = $ENTITY_TYPE_CASE
        decreaseremainingon             = $DECREASE_ON_CREATE
        restrictcasecreation            = $def.restrictAtLimit
        startdate                       = $startDate
        enddate                         = $endDate
    }

    if ($slaId) {
        $entBody["slaid@odata.bind"] = "/slas($slaId)"
    }
    if ($templateIds.ContainsKey($tier)) {
        $entBody["entitlementtemplateid@odata.bind"] = "/entitlementtemplates($($templateIds[$tier]))"
    }

    $entId = Find-OrCreate-Record `
        -EntitySet "entitlements" `
        -Filter "name eq '$escapedEntName'" `
        -IdField "entitlementid" `
        -Body $entBody `
        -DisplayName $entName

    if ($entId) {
        $entitlementIds[$acctName] = @{
            entitlementId = $entId.ToString()
            tier          = $tier
            label         = $def.label
        }

        # --------------------------------------------------
        # 5a. Create entitlement channels
        # --------------------------------------------------
        foreach ($ch in $def.channels) {
            $chFilter = "_entitlementid_value eq '$entId' and channel eq $($ch.type)"
            $existingCh = Invoke-DataverseGet -EntitySet "entitlementchannels" `
                -Filter $chFilter -Select "entitlementchannelid" -Top 1

            if ($existingCh -and $existingCh.Count -gt 0) {
                Write-Host "    Channel $($ch.name): exists" -ForegroundColor DarkGray
                $channelResults.skipped++
            } else {
                $chBody = @{
                    "entitlementid@odata.bind" = "/entitlements($entId)"
                    channel                    = $ch.type
                    totalterms                 = [decimal]$ch.cases
                    remainingterms             = [decimal]$ch.cases
                }
                if ($currencyId) {
                    $chBody["transactioncurrencyid@odata.bind"] = "/transactioncurrencies($currencyId)"
                }

                $chResult = Invoke-DataversePost -EntitySet "entitlementchannels" -Body $chBody
                if ($chResult) {
                    Write-Host "    Channel $($ch.name): $($ch.cases) cases" -ForegroundColor Green
                    $channelResults.created++
                } else {
                    Write-Host "    Channel $($ch.name): FAILED" -ForegroundColor Red
                    $channelResults.failed++
                }
            }
        }
    } else {
        Write-Warning "Failed to create entitlement for $acctName"
    }
}

# ============================================================
# 6. Activate Entitlements
# ============================================================
Write-Host "`nActivating entitlements..." -ForegroundColor Yellow

$activated = 0
$alreadyActive = 0
$activationFailed = 0

foreach ($entry in $entitlementIds.GetEnumerator()) {
    $entId = $entry.Value.entitlementId

    # Check current state
    $current = Invoke-DataverseGet -EntitySet "entitlements" `
        -Filter "entitlementid eq '$entId'" `
        -Select "entitlementid,statecode" -Top 1

    if ($current -and $current.Count -gt 0 -and $current[0].statecode -eq 1) {
        $alreadyActive++
        continue
    }

    # Activate (set state to Active)
    $patchResult = Invoke-DataversePatch -EntitySet "entitlements" `
        -RecordId ([guid]$entId) `
        -Body @{ statecode = 1; statuscode = 1 }

    if ($patchResult) {
        $activated++
        Write-Host "  Activated: $($entry.Key)" -ForegroundColor Green
    } else {
        $activationFailed++
        Write-Host "  Activation failed: $($entry.Key)" -ForegroundColor Yellow
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Entitlements Created Successfully" -ForegroundColor Green
Write-Host " Templates      : $($templateIds.Count)" -ForegroundColor White
Write-Host " Entitlements    : $($entitlementIds.Count)" -ForegroundColor White
Write-Host " Channels        : $($channelResults.created) created, $($channelResults.skipped) existing, $($channelResults.failed) failed" -ForegroundColor White
Write-Host " Activated       : $activated new, $alreadyActive already active, $activationFailed failed" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

# Tier breakdown
Write-Host "`n  Breakdown by tier:" -ForegroundColor Cyan
foreach ($tier in "1", "2", "3", "4") {
    $count = ($entitlementIds.Values | Where-Object { $_.tier -eq $tier }).Count
    $def = $tierDefs[$tier]
    Write-Host "    Tier $tier ($($def.label)): $count accounts - $($def.totalCases) cases/year" -ForegroundColor White
}

# ============================================================
# Export entitlement IDs
# ============================================================
$exportData = @{
    Templates    = @{}
    Entitlements = $entitlementIds
    SlaId        = if ($slaId) { $slaId } else { "N/A" }
    DateRange    = @{ start = $startDate; end = $endDate }
}
foreach ($t in $templateIds.GetEnumerator()) {
    $exportData.Templates["Tier$($t.Key)"] = $t.Value.ToString()
}

$exportData | ConvertTo-Json -Depth 4 | Out-File "$scriptDir\..\data\entitlement-ids.json" -Encoding utf8
Write-Host "`nEntitlement IDs saved to data\entitlement-ids.json" -ForegroundColor DarkGray

# ============================================================
# Manual steps reminder
# ============================================================
Write-Host "`n--- VERIFY IN D365 ---" -ForegroundColor Magenta
Write-Host @"

  1. Open Customer Service admin center
  2. Navigate to Service Terms > Entitlements
  3. Verify 4 templates (one per tier) exist
  4. Verify each distributor has an active entitlement
  5. Open a customer account - confirm entitlement shows
     in the Related > Entitlements sub-grid
  6. Create a test case - confirm the entitlement
     is auto-selected and terms decrease

"@ -ForegroundColor Yellow
