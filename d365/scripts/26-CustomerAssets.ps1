<#
.SYNOPSIS
    Step 26 - Provision Customer Assets (Equipment / Installed Base)
.DESCRIPTION
    Creates msdyn_customerasset records from a customer's demo-data.json.
    Works with any customer that defines an "equipment" array on their
    service-account objects.

    Each equipment line generates individual asset records with:
      - msdyn_name   (serial number, e.g. "GEN2-WL-003")
      - msdyn_assettag (model name, e.g. "Gen2 Comfort")
      - Account lookup (matched by accountNumber)
      - Warranty dates (generated: start = 1-3 yrs ago, end = 1-3 yrs out)
      - Asset Status   (jdk_assetstatus picklist)
      - Contract Type  (cra1f_contracttype multi-select picklist)

    Designed to be called from the shared 00-Setup.ps1 orchestrator or
    run standalone for any customer.

.PARAMETER Customer
    Customer folder name under customers/ (e.g. "otis", "zurnelkay")

.PARAMETER Cleanup
    If set, removes all assets created by this script (matched by serial prefix)

.EXAMPLE
    .\26-CustomerAssets.ps1 -Customer otis
    .\26-CustomerAssets.ps1 -Customer otis -Cleanup
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Customer,

    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "26" "Customer Assets (Equipment / Installed Base)"
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

$demoData = Get-Content $demoDataPath -Raw | ConvertFrom-Json
Write-Host "Loaded demo data for: $($demoData._metadata.customer)" -ForegroundColor Cyan

# ============================================================
# Contract Type mapping → cra1f_contracttype multi-select values
# Map common contract labels to option-set integer values.
# Add new entries here as customers introduce new contract types.
# ============================================================
$contractTypeMap = @{
    "HASSLE FREE ALL IN"                  = 276120000
    "HASSLE FREE ALL IN NO PADS CM/CD INCL" = 276120000
    "AMR Silver"                          = 276120001
    "AMR Gold"                            = 276120002
    "RedTote All In"                      = 276120003
    "Distributor"                         = 276120004
    "Direct"                              = 276120005
    # Generic labels → sensible defaults
    "Premium Service - 24/7"              = 276120002   # Gold
    "Full Maintenance"                    = 276120001   # Silver
    "Basic Maintenance"                   = 276120004   # Distributor
    "Exam Only"                           = 276120005   # Direct
    # Otis Signature Service plans
    "Signature Service Premium"           = 276120000   # top-tier → HASSLE FREE equiv
    "Signature Service Plus"              = 276120001   # mid-tier → Silver equiv
    "Signature Service"                   = 276120002   # standard → Gold equiv
    "On-Call Only"                        = 276120005   # minimal  → Direct equiv
}

# Asset Status values  (jdk_assetstatus)
$assetStatusPurchased = 752870000
$assetStatusLoaner    = 752870001
$assetStatusDemo      = 752870002

# ============================================================
# Resolve accounts → GUID cache
# ============================================================
$accountCache = @{}

function Get-AccountId {
    param([string]$AccountNumber)

    if ($accountCache.ContainsKey($AccountNumber)) {
        return $accountCache[$AccountNumber]
    }

    $escapedNum = $AccountNumber -replace "'", "''"
    $found = Invoke-DataverseGet -EntitySet "accounts" `
        -Filter "accountnumber eq '$escapedNum'" `
        -Select "accountid" -Top 1

    if ($found -and $found.Count -gt 0) {
        $id = [guid]$found[0].accountid
        $accountCache[$AccountNumber] = $id
        return $id
    }
    return $null
}

# ============================================================
# Expand serial ranges → individual records
#   "GEN2-WL-001-018" with count=18 → GEN2-WL-001 .. GEN2-WL-018
# ============================================================
function Expand-SerialRange {
    param(
        [string]$SerialPattern,   # e.g. "GEN2-WL-001-018"
        [int]$Count
    )

    # Pattern: PREFIX-SITE-START-END  or  PREFIX-SITE-START
    # We split on '-', take last two as numeric range, prefix is everything before.
    $parts = $SerialPattern -split '-'

    if ($parts.Count -ge 4) {
        # e.g. ["GEN2","WL","001","018"]
        $prefix = ($parts[0..($parts.Count - 3)]) -join '-'   # GEN2-WL
        $startNum = [int]$parts[-2]                            # 1
    }
    elseif ($parts.Count -ge 2) {
        $prefix = ($parts[0..($parts.Count - 2)]) -join '-'
        $startNum = 1
    }
    else {
        $prefix = $SerialPattern
        $startNum = 1
    }

    $serials = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $num = $startNum + $i
        $serials += "$prefix-$($num.ToString('000'))"
    }
    return $serials
}

# ============================================================
# CLEANUP
# ============================================================
if ($Cleanup) {
    Write-Host "Removing Customer Assets for $Customer..." -ForegroundColor Red
    $confirm = Read-Host "Type 'DELETE' to confirm"
    if ($confirm -ne "DELETE") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        return
    }

    $accounts = $demoData.serviceAccounts.accounts
    foreach ($acct in $accounts) {
        $acctId = Get-AccountId -AccountNumber $acct.accountNumber
        if (-not $acctId) { continue }

        Write-Host "  Deleting assets for: $($acct.name)" -ForegroundColor Gray
        $assets = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
            -Filter "_msdyn_account_value eq $acctId" `
            -Select "msdyn_customerassetid,msdyn_name"

        if ($assets) {
            foreach ($a in $assets) {
                Invoke-DataverseDelete -EntitySet "msdyn_customerassets" -Id ([guid]$a.msdyn_customerassetid)
                Write-Host "    Deleted: $($a.msdyn_name)" -ForegroundColor DarkRed
            }
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
    return
}

# ============================================================
# PROVISION
# ============================================================
$totalCreated = 0
$totalSkipped = 0

$accounts = $demoData.serviceAccounts.accounts
Write-Host "Processing $($accounts.Count) accounts..." -ForegroundColor Yellow

foreach ($acct in $accounts) {
    $accountId = Get-AccountId -AccountNumber $acct.accountNumber
    if (-not $accountId) {
        Write-Host "  SKIP: Account '$($acct.name)' ($($acct.accountNumber)) not found in Dataverse" -ForegroundColor DarkYellow
        continue
    }

    Write-Host "`n  Account: $($acct.name) ($($acct.accountNumber))" -ForegroundColor Cyan

    # Determine contract type value from the account's contract label
    $contractVal = $null
    if ($acct.contract -and $contractTypeMap.ContainsKey($acct.contract)) {
        $contractVal = $contractTypeMap[$acct.contract]
    }

    if (-not $acct.equipment) {
        Write-Host "    No equipment array — skipping" -ForegroundColor DarkGray
        continue
    }

    foreach ($equip in $acct.equipment) {
        $serials = Expand-SerialRange -SerialPattern $equip.serial -Count $equip.count

        foreach ($serial in $serials) {
            # Generate realistic warranty dates
            # Start: 1-3 years ago, End: 1-3 years from now
            $yearsBack = Get-Random -Minimum 1 -Maximum 4
            $warrantyYears = Get-Random -Minimum 3 -Maximum 6
            $wStart = (Get-Date).AddYears(-$yearsBack).Date
            $wEnd   = $wStart.AddYears($warrantyYears).Date

            $body = @{
                msdyn_name              = $serial
                msdyn_assettag          = "$($equip.model) — $($equip.type)"
                "msdyn_account@odata.bind" = "/accounts($accountId)"
                jdk_assetstatus         = $assetStatusPurchased
                jdk_warrantystartdate   = $wStart.ToString("yyyy-MM-ddT00:00:00Z")
                jdk_warrantyenddate     = $wEnd.ToString("yyyy-MM-ddT00:00:00Z")
            }

            # Set last serviced date from account data (with slight variation per asset)
            if ($acct.lastServiceDate) {
                $baseSvcDate = [datetime]::Parse($acct.lastServiceDate)
                $dayOffset = ($serials.IndexOf($serial) % 15) - 7
                $svcDate = $baseSvcDate.AddDays($dayOffset)
                if ($svcDate -gt (Get-Date)) { $svcDate = $baseSvcDate }
                $body["bw_lastservicedon"] = $svcDate.ToString("yyyy-MM-ddT00:00:00Z")
            }

            # Multi-select picklist: pass as comma-separated string of int values
            if ($contractVal) {
                $body["cra1f_contracttype"] = "$contractVal"
            }

            $escapedSerial = $serial -replace "'", "''"
            $existing = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
                -Filter "msdyn_name eq '$escapedSerial'" `
                -Select "msdyn_customerassetid" -Top 1

            if ($existing -and $existing.Count -gt 0) {
                Write-Host "    EXISTS: $serial" -ForegroundColor DarkGray
                $totalSkipped++
            }
            else {
                $result = Invoke-DataversePost -EntitySet "msdyn_customerassets" -Body $body
                if ($result) {
                    Write-Host "    CREATED: $serial  ($($equip.model))" -ForegroundColor Green
                    $totalCreated++
                }
                else {
                    Write-Host "    FAILED: $serial" -ForegroundColor Red
                }
            }
        }
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Customer Assets Provisioning Complete" -ForegroundColor Green
Write-Host "  Customer: $($demoData._metadata.customer)" -ForegroundColor Gray
Write-Host "  Created:  $totalCreated" -ForegroundColor Gray
Write-Host "  Skipped:  $totalSkipped (already existed)" -ForegroundColor Gray
Write-Host ("=" * 60) -ForegroundColor Green
