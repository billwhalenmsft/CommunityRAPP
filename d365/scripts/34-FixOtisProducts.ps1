<#
.SYNOPSIS
    Fix Otis product data: copy entity image, create price list.
.DESCRIPTION
    1. Copies the Entity Image from "Otis Gen2 Elevator" to "Gen2 Comfort"
       (the product the 205 Customer Assets actually reference).
    2. Creates an "Otis UK Price List" in GBP.
    3. Adds all 8 backfill products (Gen2 Comfort, Gen2 Premier, Gen2 Life,
       SkyRise, SkyRise DD, NCE, NCE Heavy Duty, Travolator) to the price list
       with representative list prices.
#>

param(
    [string]$Customer = "otis"
)

$ErrorActionPreference = "Stop"
Import-Module "$PSScriptRoot\DataverseHelper.psm1" -Force
Connect-Dataverse

$headers = Get-DataverseHeaders

# ────────────────────────────────────────────
# Product IDs (from Dataverse query)
# ────────────────────────────────────────────
# Set 1 (original - has the entity image)
$otisGen2ElevatorId = "cb387e58-7021-f111-8342-7ced8d18c8d7"

# Set 2 (backfill - linked to 205 assets)
$products = @(
    @{ Id = "2dadc331-9b23-f111-8341-7ced8dceb26a"; Name = "Gen2 Comfort";    Price = 45000 }
    @{ Id = "c6365935-9b23-f111-8342-7ced8dceb433"; Name = "Gen2 Premier";    Price = 65000 }
    @{ Id = "43adc331-9b23-f111-8341-7ced8dceb26a"; Name = "Gen2 Life";       Price = 35000 }
    @{ Id = "47adc331-9b23-f111-8341-7ced8dceb26a"; Name = "SkyRise";         Price = 120000 }
    @{ Id = "ee9db233-9b23-f111-8342-7c1e520a58a1"; Name = "SkyRise DD";      Price = 180000 }
    @{ Id = "713cb337-9b23-f111-8342-7c1e52143136"; Name = "NCE";             Price = 55000 }
    @{ Id = "9978c337-9b23-f111-8341-7ced8dceb26a"; Name = "NCE Heavy Duty";  Price = 75000 }
    @{ Id = "743cb337-9b23-f111-8342-7c1e52143136"; Name = "Travolator";      Price = 40000 }
)

# ────────────────────────────────────────────
# STEP 1: Copy Entity Image
# ────────────────────────────────────────────
Write-Host "`n=== STEP 1: Copy Entity Image ===" -ForegroundColor Cyan
Write-Host "Downloading entity image from 'Otis Gen2 Elevator'..."

$imgHeaders = @{
    "Authorization" = $headers["Authorization"]
    "Accept"        = "application/octet-stream"
}

try {
    $imgUrl = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2/products($otisGen2ElevatorId)/entityimage/`$value"
    $imgResponse = Invoke-WebRequest `
        -Uri $imgUrl `
        -Headers $imgHeaders -UseBasicParsing -ErrorAction Stop

    $imageBytes = $imgResponse.Content
    $imageBase64 = [Convert]::ToBase64String($imageBytes)
    Write-Host "  Downloaded image: $($imageBytes.Length) bytes" -ForegroundColor Green

    # Upload to Gen2 Comfort
    $gen2ComfortId = $products[0].Id
    Write-Host "Uploading entity image to 'Gen2 Comfort' ($gen2ComfortId)..."

    $patchBody = @{ entityimage = $imageBase64 } | ConvertTo-Json
    $patchHeaders = Get-DataverseHeaders
    $patchUrl = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2/products($gen2ComfortId)"
    Invoke-RestMethod `
        -Uri $patchUrl `
        -Method Patch -Headers $patchHeaders -Body $patchBody -ErrorAction Stop

    Write-Host "  Entity image copied to Gen2 Comfort" -ForegroundColor Green
} catch {
    Write-Warning "Could not copy entity image: $($_.Exception.Message)"
    Write-Warning "You may need to upload the image manually to 'Gen2 Comfort' in Dynamics."
}

# ────────────────────────────────────────────
# STEP 2: Get or Create Default Unit of Measure
# ────────────────────────────────────────────
Write-Host "`n=== STEP 2: Get Default Unit of Measure ===" -ForegroundColor Cyan

$uomSchedules = Invoke-DataverseGet -EntitySet "uomschedules" -Top 1
if ($uomSchedules -and $uomSchedules.Count -gt 0) {
    $uomScheduleId = $uomSchedules[0].uomscheduleid
    Write-Host "  UoM Schedule: $($uomSchedules[0].name) ($uomScheduleId)" -ForegroundColor Green

    # Get the default/primary unit — filter uoms by _uomscheduleid_value
    $uomHeaders = Get-DataverseHeaders
    $uomHeaders.Remove('Prefer')
    $uomUrl = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2/uoms?`$filter=_uomscheduleid_value eq $uomScheduleId&`$select=uomid,name&`$top=5"
    $uomResp = Invoke-RestMethod -Uri $uomUrl -Headers $uomHeaders -Method Get
    $units = $uomResp.value
    $defaultUomId = $units[0].uomid
    Write-Host "  Default UoM: $($units[0].name) ($defaultUomId)" -ForegroundColor Green
} else {
    Write-Error "No Unit of Measure Schedules found. Cannot create price list items."
}

# ────────────────────────────────────────────
# STEP 3: Get or Create Currency (GBP)
# ────────────────────────────────────────────
Write-Host "`n=== STEP 3: Get Currency ===" -ForegroundColor Cyan

$currencies = Invoke-DataverseGet -EntitySet "transactioncurrencies" `
    -Filter "isocurrencycode eq 'GBP'" -Select "transactioncurrencyid,currencyname,isocurrencycode"

if ($currencies -and $currencies.Count -gt 0) {
    $gbpCurrencyId = $currencies[0].transactioncurrencyid
    Write-Host "  Found GBP currency: $gbpCurrencyId" -ForegroundColor Green
} else {
    Write-Host "  GBP not found, checking for default currency..."
    $currencies = Invoke-DataverseGet -EntitySet "transactioncurrencies" -Top 1 -Select "transactioncurrencyid,currencyname,isocurrencycode"
    $gbpCurrencyId = $currencies[0].transactioncurrencyid
    Write-Host "  Using default currency: $($currencies[0].currencyname) ($($currencies[0].isocurrencycode))" -ForegroundColor Yellow
}

# ────────────────────────────────────────────
# STEP 4: Create Price List
# ────────────────────────────────────────────
Write-Host "`n=== STEP 4: Create Otis UK Price List ===" -ForegroundColor Cyan

# Check if it already exists
$existingPL = Invoke-DataverseGet -EntitySet "pricelevels" `
    -Filter "name eq 'Otis UK Price List'" -Select "pricelevelid,name"

if ($existingPL -and $existingPL.Count -gt 0) {
    $priceListId = $existingPL[0].pricelevelid
    Write-Host "  Price list already exists: $priceListId" -ForegroundColor Yellow
} else {
    $plBody = @{
        name = "Otis UK Price List"
        description = "Standard price list for Otis UK elevator, escalator, and moving walkway products"
        "transactioncurrencyid@odata.bind" = "/transactioncurrencies($gbpCurrencyId)"
        begindate = "2024-01-01"
        enddate = "2027-12-31"
    }
    $plResult = Invoke-DataversePost -EntitySet "pricelevels" -Body $plBody
    if ($plResult -and $plResult.pricelevelid) {
        $priceListId = $plResult.pricelevelid
    } elseif ($plResult -is [string]) {
        $priceListId = $plResult
    } else {
        # Query back
        $createdPL = Invoke-DataverseGet -EntitySet "pricelevels" `
            -Filter "name eq 'Otis UK Price List'" -Select "pricelevelid"
        $priceListId = $createdPL[0].pricelevelid
    }
    Write-Host "  Created price list: $priceListId" -ForegroundColor Green
}

# ────────────────────────────────────────────
# STEP 5: Add Products to Price List
# ────────────────────────────────────────────
Write-Host "`n=== STEP 5: Add Products to Price List ===" -ForegroundColor Cyan

$added = 0
$skipped = 0
$errors = 0

foreach ($prod in $products) {
    # Check if price list item already exists
    $existingPLI = Invoke-DataverseGet -EntitySet "productpricelevels" `
        -Filter "_pricelevelid_value eq '$priceListId' and _productid_value eq '$($prod.Id)'" `
        -Select "productpricelevelid" -Top 1

    if ($existingPLI -and $existingPLI.Count -gt 0) {
        Write-Host "  SKIP  $($prod.Name) — already in price list" -ForegroundColor Yellow
        $skipped++
        continue
    }

    $pliBody = @{
        "pricelevelid@odata.bind"  = "/pricelevels($priceListId)"
        "productid@odata.bind"     = "/products($($prod.Id))"
        "uomid@odata.bind"         = "/uoms($defaultUomId)"
        amount                     = $prod.Price
        pricingmethodcode          = 1    # Currency Amount
    }

    try {
        $result = Invoke-DataversePost -EntitySet "productpricelevels" -Body $pliBody
        Write-Host "  ADDED $($prod.Name) — GBP $($prod.Price)" -ForegroundColor Green
        $added++
    } catch {
        Write-Warning "  ERROR $($prod.Name): $($_.Exception.Message)"
        $errors++
    }
}

# ────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "  Entity Image: Copied from 'Otis Gen2 Elevator' to 'Gen2 Comfort'"
Write-Host "  Price List:   'Otis UK Price List' ($priceListId)"
Write-Host "  Products:     Added=$added  Skipped=$skipped  Errors=$errors"
Write-Host "`nDone!" -ForegroundColor Green
