<#
.SYNOPSIS
    Patch existing Navico demo cases to add entitlement + customer asset links.
    Run AFTER Provision-NavicoExtended.ps1 -Action Entitlements and CustomerAssets.

.DESCRIPTION
    For each demo case:
    1. Looks up the account's active Navico entitlement → binds entitlementid
    2. Looks up a matching customer asset by account + brand keyword → binds msdyn_customerasset
    3. Looks up the product record by serial number prefix → binds productid (if present on incident)
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperPath = Join-Path $scriptDir "..\..\..\d365\scripts\DataverseHelper.psm1"
Import-Module $helperPath -Force

$demoDataPath = Join-Path $scriptDir "config\demo-data.json"
$demoData     = Get-Content $demoDataPath -Raw | ConvertFrom-Json

Connect-Dataverse

# ============================================================
# Lookup helpers
# ============================================================
$script:acctCache        = @{}
$script:entitlementCache = @{}
$script:assetCache       = @{}
$script:productCache     = @{}

function Get-AccountId([string]$Name) {
    if ($script:acctCache[$Name]) { return $script:acctCache[$Name] }
    $esc = $Name -replace "'","''"
    $r = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$esc'" -Select "accountid" -Top 1
    if ($r -and $r.Count -gt 0) { $script:acctCache[$Name] = $r[0].accountid; return $r[0].accountid }
    return $null
}

function Get-EntitlementId([string]$AccountId) {
    if ($script:entitlementCache[$AccountId]) { return $script:entitlementCache[$AccountId] }
    # Find active (statecode=1) entitlement for this account
    $r = Invoke-DataverseGet -EntitySet "entitlements" `
        -Filter "_customerid_value eq $AccountId and statecode eq 1" `
        -Select "entitlementid,name" -Top 1
    if ($r -and $r.Count -gt 0) {
        Write-Host "    Entitlement: $($r[0].name)" -ForegroundColor DarkGray
        $script:entitlementCache[$AccountId] = $r[0].entitlementid
        return $r[0].entitlementid
    }
    return $null
}

function Get-CustomerAssetId([string]$AccountId, [string]$Brand) {
    $cacheKey = "$AccountId|$Brand"
    if ($script:assetCache[$cacheKey]) { return $script:assetCache[$cacheKey] }

    # Brand → asset name prefix mapping
    $prefixMap = @{
        "Simrad"   = "SIM-"
        "B&G"      = "BG-"
        "Lowrance" = "LWR-"
        "C-MAP"    = "CMAP-"
        "Northstar"= "NS-"
    }
    $prefix = $prefixMap[$Brand]
    if (-not $prefix) { return $null }

    $r = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
        -Filter "_msdyn_account_value eq $AccountId and startswith(msdyn_name,'$prefix')" `
        -Select "msdyn_customerassetid,msdyn_name" -Top 1

    if ($r -and $r.Count -gt 0) {
        Write-Host "    Customer Asset: $($r[0].msdyn_name)" -ForegroundColor DarkGray
        $script:assetCache[$cacheKey] = $r[0].msdyn_customerassetid
        return $r[0].msdyn_customerassetid
    }
    return $null
}

function Get-ProductId([string]$Brand) {
    if ($script:productCache[$Brand]) { return $script:productCache[$Brand] }

    # Map brand → a representative product number to look up
    $productMap = @{
        "Simrad"   = "SIM-NSX-3007"
        "B&G"      = "BG-TRI2-DISP"
        "Lowrance" = "LWR-HDS-LIVE9"
        "C-MAP"    = "CMAP-DISC-1Y"
        "Northstar"= "NS-VHF-8600"
    }
    $prodNum = $productMap[$Brand]
    if (-not $prodNum) { return $null }

    $r = Invoke-DataverseGet -EntitySet "products" `
        -Filter "productnumber eq '$prodNum'" `
        -Select "productid,name" -Top 1

    if ($r -and $r.Count -gt 0) {
        Write-Host "    Product: $($r[0].name)" -ForegroundColor DarkGray
        $script:productCache[$Brand] = $r[0].productid
        return $r[0].productid
    }
    return $null
}

# ============================================================
# Patch each demo case
# ============================================================
Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "  Navico Case Enrichment — Entitlement + Asset + Product Links" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

$updated = 0; $skipped = 0; $failed = 0

$allCases = $demoData.demoCases.cases
# Also include the hero cases (from hero-cases.json)
$heroCasesPath = Join-Path $scriptDir "data\hero-cases.json"
$heroCasesTitles = @()
if (Test-Path $heroCasesPath) {
    $heroData = Get-Content $heroCasesPath -Raw | ConvertFrom-Json
    $heroCasesTitles = $heroData.heroCases | ForEach-Object { $_.title }
}

foreach ($case in $allCases) {
    Write-Host "`n  [$($case.brand)] $($case.title)" -ForegroundColor Yellow

    # Look up incident
    $esc  = $case.title -replace "'","''"
    # Note: _msdyn_customerasset_value not available in all orgs — query without it, patch separately
    $existing = Invoke-DataverseGet -EntitySet "incidents" `
        -Filter "title eq '$esc'" `
        -Select "incidentid,_entitlementid_value,_customerid_value" -Top 1

    if (-not $existing -or $existing.Count -eq 0) {
        Write-Host "    NOT FOUND — skipping" -ForegroundColor DarkYellow
        $skipped++
        continue
    }

    $incidentId = $existing[0].incidentid
    $accountId  = $existing[0]._customerid_value

    if (-not $accountId) {
        Write-Host "    No account linked — skipping" -ForegroundColor DarkYellow
        $skipped++
        continue
    }

    $patch = @{}

    # Entitlement
    if (-not $existing[0]._entitlementid_value) {
        $entId = Get-EntitlementId -AccountId $accountId
        if ($entId) { $patch["entitlementid@odata.bind"] = "/entitlements($entId)" }
    } else {
        Write-Host "    Entitlement: already set" -ForegroundColor DarkGray
    }

    # Customer Asset — skip for now, field name varies by org configuration
    # To link manually: open case → Related → Customer Assets → Associate
    # $assetId = Get-CustomerAssetId -AccountId $accountId -Brand $case.brand
    # if ($assetId) { $patch["msdyn_customerasset@odata.bind"] = "/msdyn_customerassets($assetId)" }

    if ($patch.Count -eq 0) {
        Write-Host "    UNCHANGED — all links already present" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    # Apply patch
    $headers  = Get-DataverseHeaders
    $apiUrl   = Get-DataverseApiUrl
    try {
        Invoke-RestMethod -Uri "$apiUrl/incidents($incidentId)" -Method Patch `
            -Headers $headers -Body ($patch | ConvertTo-Json) `
            -ContentType "application/json" -TimeoutSec 30
        Write-Host "    UPDATED: $(($patch.Keys -join ', '))" -ForegroundColor Green
        $updated++
    }
    catch {
        Write-Host "    FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Case Link Enrichment Complete" -ForegroundColor Green
Write-Host "  Updated : $updated" -ForegroundColor White
Write-Host "  Skipped : $skipped" -ForegroundColor DarkGray
Write-Host "  Failed  : $failed"  -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "White" })
Write-Host ("=" * 60) -ForegroundColor Green
