<#
.SYNOPSIS
    Step 33 - Backfill Product (Model) and Functional Location on Otis Customer Assets
.DESCRIPTION
    Populates the two missing fields on all 205 Otis UK customer assets:

    1. PRODUCT — Creates Otis elevator/escalator/walkway product records
       (Gen2 Comfort, Gen2 Premier, Gen2 Life, SkyRise, SkyRise DD,
       NCE, NCE Heavy Duty, Travolator), then links each asset to the
       correct product based on the serial number prefix.

    2. FUNCTIONAL LOCATION — Creates one functional location per Otis
       account (building name), then links each asset to its account's
       location.

    Safe to run multiple times — uses Find-or-Create pattern.

.PARAMETER Customer
    Customer folder name under customers/ (default: "otis")

.EXAMPLE
    .\33-BackfillProductAndLocation.ps1
    .\33-BackfillProductAndLocation.ps1 -Customer otis
#>

[CmdletBinding()]
param(
    [string]$Customer = "otis"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "33" "Backfill Product (Model) and Functional Location on Otis Assets"
Connect-Dataverse

$headers = Get-DataverseHeaders
$baseUrl = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# ============================================================
# Load demo-data.json for account/equipment mapping
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
# PART 1: Create Otis Product Records
# ============================================================
Write-Host "`n--- PART 1: Create Otis Product Records ---" -ForegroundColor Yellow

# Serial prefix -> model name mapping
# Derived from demo-data.json equipment definitions:
#   GEN2, G2C  = Gen2 Comfort
#   G2P        = Gen2 Premier
#   G2L        = Gen2 Life
#   SKY        = SkyRise
#   SKDD       = SkyRise DD
#   NCE        = NCE  (or NCE Heavy Duty for OTIS-UK-004)
#   TRV        = Travolator
$productDefs = @(
    @{ Name = "Gen2 Comfort";    Desc = "Mid-rise machine-room-less elevator for residential and commercial buildings"; Prefixes = @("G2C","GEN2") }
    @{ Name = "Gen2 Premier";    Desc = "High-performance elevator for institutional and commercial applications";      Prefixes = @("G2P") }
    @{ Name = "Gen2 Life";       Desc = "Healthcare-optimized elevator with smooth ride and antimicrobial surfaces";    Prefixes = @("G2L") }
    @{ Name = "SkyRise";         Desc = "Ultra-high-rise elevator with regenerative drives";                            Prefixes = @("SKY") }
    @{ Name = "SkyRise DD";      Desc = "Double-deck elevator for maximum throughput in skyscrapers";                   Prefixes = @("SKDD") }
    @{ Name = "NCE";             Desc = "Energy-efficient escalator for retail and transportation";                     Prefixes = @("NCE") }
    @{ Name = "Travolator";      Desc = "Moving walkway for airports and large retail";                                 Prefixes = @("TRV") }
)

# NCE Heavy Duty is used specifically at Birmingham New Street (OTIS-UK-004)
# We'll handle that by serial range below

$productIdMap = @{}  # Name -> productid

foreach ($pDef in $productDefs) {
    $pName = $pDef.Name
    Write-Host "  Checking product: $pName..." -ForegroundColor Cyan

    # Check if the product already exists
    $escapedName = $pName -replace "'", "''"
    $existing = Invoke-DataverseGet -EntitySet "products" `
        -Filter "name eq '$escapedName'" `
        -Select "productid,name,statecode" -Top 1

    if ($existing -and $existing.Count -gt 0) {
        $productIdMap[$pName] = [string]$existing[0].productid
        Write-Host "    [EXISTS] $pName -> $($existing[0].productid)" -ForegroundColor DarkGray
    } else {
        # Create product record
        # Products need a default unit and unit group
        # First, get the default unit group
        $unitGroups = Invoke-DataverseGet -EntitySet "uomschedules" -Select "uomscheduleid,name" -Top 1
        if (-not $unitGroups -or $unitGroups.Count -eq 0) {
            Write-Host "    [ERROR] No unit groups found — cannot create product" -ForegroundColor Red
            continue
        }
        $unitGroupId = $unitGroups[0].uomscheduleid

        # Get the primary unit for that group
        $units = Invoke-DataverseGet -EntitySet "uoms" `
            -Filter "_uomscheduleid_value eq $unitGroupId" `
            -Select "uomid,name" -Top 1
        if (-not $units -or $units.Count -eq 0) {
            Write-Host "    [ERROR] No units found for unit group — cannot create product" -ForegroundColor Red
            continue
        }
        $unitId = $units[0].uomid

        $productBody = @{
            "name"                          = $pName
            "description"                   = $pDef.Desc
            "productnumber"                 = "OTIS-" + ($pName -replace " ", "-").ToUpper()
            "producttypecode"               = 1  # Product (not bundle)
            "quantitydecimal"               = 0
            "defaultuomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
            "defaultuomid@odata.bind"         = "/uoms($unitId)"
        }

        $result = Invoke-DataversePost -EntitySet "products" -Body $productBody
        $newId = $null
        if ($result) {
            # Extract GUID: result may be full object or string GUID
            if ($result -is [PSCustomObject] -and $result.productid) {
                $newId = $result.productid
            } elseif ($result -is [string] -and $result -match '[0-9a-fA-F\-]{36}') {
                $newId = $result
            }
        }
        if ($newId) {
            $productIdMap[$pName] = $newId
            Write-Host "    [CREATED] $pName -> $newId" -ForegroundColor Green
        } else {
            Write-Host "    [ERROR] Failed to create $pName" -ForegroundColor Red
        }
    }
}

# Also add NCE Heavy Duty separately
$nceHDName = "NCE Heavy Duty"
Write-Host "  Checking product: $nceHDName..." -ForegroundColor Cyan
$existing = Invoke-DataverseGet -EntitySet "products" `
    -Filter "name eq '$nceHDName'" `
    -Select "productid,name" -Top 1

if ($existing -and $existing.Count -gt 0) {
    $productIdMap[$nceHDName] = [string]$existing[0].productid
    Write-Host "    [EXISTS] $nceHDName -> $($existing[0].productid)" -ForegroundColor DarkGray
} else {
    $unitGroups = Invoke-DataverseGet -EntitySet "uomschedules" -Select "uomscheduleid" -Top 1
    $unitGroupId = $unitGroups[0].uomscheduleid
    $units = Invoke-DataverseGet -EntitySet "uoms" -Filter "_uomscheduleid_value eq $unitGroupId" -Select "uomid" -Top 1
    $unitId = $units[0].uomid

    $productBody = @{
        "name"                          = $nceHDName
        "description"                   = "High-traffic escalator for transportation hubs"
        "productnumber"                 = "OTIS-NCE-HEAVY-DUTY"
        "producttypecode"               = 1
        "quantitydecimal"               = 0
        "defaultuomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
        "defaultuomid@odata.bind"         = "/uoms($unitId)"
    }
    $result = Invoke-DataversePost -EntitySet "products" -Body $productBody
    $newId = $null
    if ($result) {
        if ($result -is [PSCustomObject] -and $result.productid) {
            $newId = $result.productid
        } elseif ($result -is [string] -and $result -match '[0-9a-fA-F\-]{36}') {
            $newId = $result
        }
    }
    if ($newId) {
        $productIdMap[$nceHDName] = $newId
        Write-Host "    [CREATED] $nceHDName -> $newId" -ForegroundColor Green
    }
}

Write-Host "`n  Product map:" -ForegroundColor White
foreach ($k in $productIdMap.Keys) {
    Write-Host "    $k = $($productIdMap[$k])" -ForegroundColor Gray
}

# ============================================================
# PART 2: Create Functional Location per Otis Account
# ============================================================
Write-Host "`n--- PART 2: Create Functional Locations ---" -ForegroundColor Yellow

$accounts = $demoData.serviceAccounts.accounts | Where-Object { $_.accountNumber -match "^OTIS-UK" }
$locationIdMap = @{}  # accountNumber -> functionalLocationId

foreach ($acct in $accounts) {
    $locName = $acct.name
    Write-Host "  Checking location: $locName..." -ForegroundColor Cyan

    $escapedName = $locName -replace "'", "''"
    $existing = Invoke-DataverseGet -EntitySet "msdyn_functionallocations" `
        -Filter "msdyn_name eq '$escapedName'" `
        -Select "msdyn_functionallocationid,msdyn_name" -Top 1

    if ($existing -and $existing.Count -gt 0) {
        $locationIdMap[$acct.accountNumber] = $existing[0].msdyn_functionallocationid
        Write-Host "    [EXISTS] $locName -> $($existing[0].msdyn_functionallocationid)" -ForegroundColor DarkGray
    } else {
        $locBody = @{
            "msdyn_name" = $locName
        }

        $result = Invoke-DataversePost -EntitySet "msdyn_functionallocations" -Body $locBody
        $newId = $null
        if ($result) {
            if ($result -is [PSCustomObject] -and $result.msdyn_functionallocationid) {
                $newId = $result.msdyn_functionallocationid
            } elseif ($result -is [string] -and $result -match '[0-9a-fA-F\-]{36}') {
                $newId = $result
            }
        }
        if ($newId) {
            $locationIdMap[$acct.accountNumber] = $newId
            Write-Host "    [CREATED] $locName -> $newId" -ForegroundColor Green
        } else {
            Write-Host "    [ERROR] Failed to create location: $locName" -ForegroundColor Red
        }
    }
}

Write-Host "`n  Location map:" -ForegroundColor White
foreach ($k in $locationIdMap.Keys) {
    Write-Host "    $k = $($locationIdMap[$k])" -ForegroundColor Gray
}

# ============================================================
# PART 3: Update Assets — Set Product and Functional Location
# ============================================================
Write-Host "`n--- PART 3: Update Assets with Product and Location ---" -ForegroundColor Yellow

# Build serial prefix -> product name mapping
# Serial format: PREFIX-SITECODE-NNN (e.g., G2C-MH-001)
$serialPrefixToProduct = @{
    "G2C"  = "Gen2 Comfort"
    "GEN2" = "Gen2 Comfort"
    "G2P"  = "Gen2 Premier"
    "G2L"  = "Gen2 Life"
    "SKY"  = "SkyRise"
    "SKDD" = "SkyRise DD"
    "NCE"  = "NCE"           # Default NCE; we'll override for Birmingham
    "TRV"  = "Travolator"
}

# Birmingham New Street (OTIS-UK-004) uses NCE Heavy Duty, not regular NCE
$birminghamAccountNum = "OTIS-UK-004"

# Resolve Otis account IDs
$otisAccounts = Invoke-DataverseGet -EntitySet "accounts" `
    -Filter "startswith(accountnumber,'OTIS-UK')" `
    -Select "accountid,name,accountnumber" -Top 15

$accountIdToNum = @{}
foreach ($a in $otisAccounts) {
    $accountIdToNum[$a.accountid] = $a.accountnumber
}

$totalUpdated = 0
$totalSkipped = 0
$totalErrors  = 0

foreach ($acct in $otisAccounts) {
    $accountId  = $acct.accountid
    $accountNum = $acct.accountnumber
    $accountName = $acct.name

    Write-Host "`n  Account: $accountName ($accountNum)" -ForegroundColor Cyan

    # Get all assets for this account
    $assets = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
        -Filter "_msdyn_account_value eq $accountId" `
        -Select "msdyn_customerassetid,msdyn_name,_msdyn_product_value,_msdyn_functionallocation_value" `
        -Top 100

    if (-not $assets -or $assets.Count -eq 0) {
        Write-Host "    No assets found" -ForegroundColor DarkGray
        continue
    }

    $locationId = $locationIdMap[$accountNum]

    foreach ($asset in $assets) {
        $serial   = $asset.msdyn_name
        $assetId  = $asset.msdyn_customerassetid
        $hasProduct  = -not [string]::IsNullOrEmpty($asset._msdyn_product_value)
        $hasLocation = -not [string]::IsNullOrEmpty($asset._msdyn_functionallocation_value)

        if ($hasProduct -and $hasLocation) {
            $totalSkipped++
            continue
        }

        # Determine product from serial prefix
        $prefix = ($serial -split "-")[0]
        $productName = $serialPrefixToProduct[$prefix]

        # Birmingham NCE -> NCE Heavy Duty
        if ($prefix -eq "NCE" -and $accountNum -eq $birminghamAccountNum) {
            $productName = "NCE Heavy Duty"
        }

        if (-not $productName) {
            Write-Host "    [WARN] Unknown serial prefix '$prefix' for $serial — skipping product" -ForegroundColor Yellow
        }

        $productId = if ($productName) { $productIdMap[$productName] } else { $null }

        # Build patch body
        $patchBody = @{}

        if (-not $hasProduct -and $productId) {
            $patchBody["msdyn_product@odata.bind"] = "/products($productId)"
        }

        if (-not $hasLocation -and $locationId) {
            $patchBody["msdyn_FunctionalLocation@odata.bind"] = "/msdyn_functionallocations($locationId)"
        }

        if ($patchBody.Count -eq 0) {
            $totalSkipped++
            continue
        }

        try {
            Invoke-DataversePatch -EntitySet "msdyn_customerassets" -RecordId ([guid]$assetId) -Body $patchBody
            $fields = ($patchBody.Keys | ForEach-Object { $_ -replace "@odata.bind","" -replace "msdyn_","" }) -join ", "
            Write-Host "    [OK] $serial — updated: $fields" -ForegroundColor Green
            $totalUpdated++
        } catch {
            Write-Host "    [FAIL] $serial — $($_.Exception.Message)" -ForegroundColor Red
            $totalErrors++
        }
    }
}

# ============================================================
# SUMMARY
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Results: Updated=$totalUpdated  Skipped=$totalSkipped  Errors=$totalErrors" -ForegroundColor Cyan
Write-Host "  Products created: $($productIdMap.Count)" -ForegroundColor Cyan
Write-Host "  Locations created: $($locationIdMap.Count)" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
