<#
.SYNOPSIS
    Step 31 - Fix Asset Data (Option Set Labels + Last Serviced Dates)
.DESCRIPTION
    Performs two data fixes on existing Customer Assets:

    1. OPTION SET LABELS — Renames the cra1f_contracttype multi-select
       picklist options from legacy names (AMR Gold, AMR Silver, HASSLE
       FREE ALL IN, etc.) to Otis Signature Service plan names.

    2. LAST SERVICED DATE — Backfills msdyn_lastservicedon on all assets
       belonging to each account, using the account's lastServiceDate
       from demo-data.json.

    Safe to run multiple times — label updates are idempotent and date
    backfill only updates assets where the field is currently blank.

.PARAMETER Customer
    Customer folder name under customers/ (e.g. "otis")

.PARAMETER LabelsOnly
    If set, only updates option set labels (skip date backfill)

.PARAMETER DatesOnly
    If set, only backfills last serviced dates (skip label update)

.EXAMPLE
    .\31-FixAssetData.ps1 -Customer otis
    .\31-FixAssetData.ps1 -Customer otis -LabelsOnly
    .\31-FixAssetData.ps1 -Customer otis -DatesOnly
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Customer,

    [switch]$LabelsOnly,
    [switch]$DatesOnly
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "31" "Fix Asset Data (Labels + Last Serviced Dates)"
Connect-Dataverse

# ============================================================
# Load customer demo data
# ============================================================
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$demoDataPath = Join-Path $repoRoot "customers\$Customer\d365\config\demo-data.json"

if (-not (Test-Path $demoDataPath)) {
    Write-Error "Demo data not found at: $demoDataPath"
    return
}

$demoData = Get-Content $demoDataPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "Loaded demo data for: $($demoData._metadata.customer)" -ForegroundColor Cyan

# ============================================================
# PART 1: Update Option Set Labels
# ============================================================
if (-not $DatesOnly) {
    Write-Host "`n--- PART 1: Update Contract Type Option Set Labels ---" -ForegroundColor Yellow

    # Label mapping: picklist value -> new Otis label
    $labelUpdates = @(
        @{ Value = 276120000; NewLabel = "Signature Service Premium" }
        @{ Value = 276120001; NewLabel = "Signature Service Plus" }
        @{ Value = 276120002; NewLabel = "Signature Service" }
        @{ Value = 276120003; NewLabel = "RedTote All In" }
        @{ Value = 276120004; NewLabel = "Distributor" }
        @{ Value = 276120005; NewLabel = "On-Call Only" }
    )

    $headers = Get-DataverseHeaders
    $baseUrl = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

    foreach ($update in $labelUpdates) {
        Write-Host "  Updating value $($update.Value) -> '$($update.NewLabel)'..." -ForegroundColor Cyan

        $body = @{
            "OptionSetName"        = "cra1f_contracttype"
            "Value"                = $update.Value
            "Label"                = @{
                "@odata.type"    = "Microsoft.Dynamics.CRM.Label"
                "LocalizedLabels" = @(
                    @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        "Label"       = $update.NewLabel
                        "LanguageCode" = 1033
                    }
                )
            }
            "MergeLabels" = $true
        } | ConvertTo-Json -Depth 10

        try {
            $url = "$baseUrl/UpdateOptionValue"
            Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -ErrorAction Stop
            Write-Host "    [OK] Updated to '$($update.NewLabel)'" -ForegroundColor Green
        }
        catch {
            $errMsg = $_.Exception.Message
            if ($_.ErrorDetails.Message) {
                $errDetail = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($errDetail.error.message) { $errMsg = $errDetail.error.message }
            }
            Write-Host "    [FAIL] Failed: $errMsg" -ForegroundColor Red
        }
    }

    # Publish customization so the label changes take effect
    Write-Host "`n  Publishing customization for msdyn_customerasset..." -ForegroundColor Cyan
    try {
        $publishBody = @{
            "ParameterXml" = "<importexportxml><entities><entity>msdyn_customerasset</entity></entities></importexportxml>"
        } | ConvertTo-Json -Depth 5

        $url = "$baseUrl/PublishXml"
        Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $publishBody -ErrorAction Stop
        Write-Host "    [OK] Published successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "    [WARN] Publish failed (labels may need manual publish): $($_.Exception.Message)" -ForegroundColor Yellow
    }

    Write-Host "`n  Option set label updates complete." -ForegroundColor Green
}

# ============================================================
# PART 2: Backfill Last Serviced Dates
# ============================================================
if (-not $LabelsOnly) {
    Write-Host "`n--- PART 2: Backfill Last Serviced Dates ---" -ForegroundColor Yellow

    $accounts = $demoData.serviceAccounts.accounts
    $totalUpdated = 0
    $totalSkipped = 0

    foreach ($acct in $accounts) {
        # Get last service date from demo data
        $lastSvcDate = $acct.lastServiceDate
        if (-not $lastSvcDate) {
            Write-Host "  SKIP: $($acct.name) - no lastServiceDate in demo data" -ForegroundColor DarkGray
            continue
        }

        # Resolve account ID
        $escapedNum = $acct.accountNumber -replace "'", "''"
        $found = Invoke-DataverseGet -EntitySet "accounts" `
            -Filter "accountnumber eq '$escapedNum'" `
            -Select "accountid" -Top 1

        if (-not $found -or $found.Count -eq 0) {
            Write-Host "  SKIP: $($acct.name) ($($acct.accountNumber)) - not found in Dataverse" -ForegroundColor DarkYellow
            continue
        }

        $accountId = [guid]$found[0].accountid
        Write-Host "`n  Account: $($acct.name) ($($acct.accountNumber))" -ForegroundColor Cyan
        Write-Host "  Last service date: $lastSvcDate" -ForegroundColor Gray

        # Get all assets for this account that don't have a last serviced date
        $assets = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
            -Filter "_msdyn_account_value eq $($accountId.ToString())" `
            -Select "msdyn_customerassetid,msdyn_name,bw_lastservicedon"

        if (-not $assets -or $assets.Count -eq 0) {
            Write-Host "    No assets found" -ForegroundColor DarkGray
            continue
        }

        # Parse the date - add slight variation per asset for realism
        $baseDate = [datetime]::Parse($lastSvcDate)

        $assetIndex = 0
        foreach ($asset in $assets) {
            # Only update if field is currently empty
            if ($asset.bw_lastservicedon) {
                $totalSkipped++
                continue
            }

            # Add -7 to +7 day variation based on asset index for realism
            $dayOffset = ($assetIndex % 15) - 7
            $svcDate = $baseDate.AddDays($dayOffset)

            # Don't set future dates
            if ($svcDate -gt (Get-Date)) {
                $svcDate = $baseDate.AddDays(-($assetIndex % 7))
            }

            $body = @{
                "bw_lastservicedon" = $svcDate.ToString("yyyy-MM-ddT00:00:00Z")
            }

            $result = Invoke-DataversePatch -EntitySet "msdyn_customerassets" `
                -RecordId ([guid]$asset.msdyn_customerassetid) `
                -Body $body

            if ($result) {
                Write-Host "    + $($asset.msdyn_name) -> $($svcDate.ToString('yyyy-MM-dd'))" -ForegroundColor Green
                $totalUpdated++
            }
            else {
                Write-Host "    [FAIL] $($asset.msdyn_name) - update failed" -ForegroundColor Red
            }

            $assetIndex++
        }
    }

    # ============================================================
    # Summary
    # ============================================================
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Host "  Asset Data Fix Complete" -ForegroundColor Green
    Write-Host "  Customer:             $($demoData._metadata.customer)" -ForegroundColor Gray
    Write-Host "  Last Svc Updated:     $totalUpdated" -ForegroundColor Gray
    Write-Host "  Already Had Date:     $totalSkipped (skipped)" -ForegroundColor Gray
    Write-Host ("=" * 60) -ForegroundColor Green
}
