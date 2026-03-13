<#
.SYNOPSIS
    Step 03 - Create Products, Unit Groups, and Price Lists
.DESCRIPTION
    Creates Zurn and Elkay product families, individual products (SKUs),
    unit groups, and price lists for the Customer Service demo.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "03" "Create Products & Price Lists"
Connect-Dataverse

# ============================================================
# 1. Unit Group
# ============================================================
Write-Host "Creating unit group..." -ForegroundColor Yellow

$unitGroupId = Find-OrCreate-Record `
    -EntitySet "uomschedules" `
    -Filter "name eq 'Plumbing Units'" `
    -IdField "uomscheduleid" `
    -Body @{ name = "Plumbing Units"; baseuomname = "Each"; description = "Unit group for Zurn/Elkay products" } `
    -DisplayName "Plumbing Units"

# Get the primary unit (auto-created with the schedule)
$primaryUnit = Invoke-DataverseGet -EntitySet "uoms" -Filter "_uomscheduleid_value eq '$unitGroupId' and isschedulebaseuom eq true" -Select "uomid,name" -Top 1
if ($primaryUnit) {
    $eachUnitId = $primaryUnit[0].uomid
    Write-Host "  Primary unit: $($primaryUnit[0].name) ($eachUnitId)" -ForegroundColor DarkGray
} else {
    # Create Each unit
    $eachUnitId = Find-OrCreate-Record `
        -EntitySet "uoms" `
        -Filter "name eq 'Each' and _uomscheduleid_value eq '$unitGroupId'" `
        -IdField "uomid" `
        -Body @{
        name                       = "Each"
        "uomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
        quantity                   = 1
    } `
        -DisplayName "Each"
}

# ============================================================
# 2. Price List
# ============================================================
Write-Host "`nCreating price lists..." -ForegroundColor Yellow

$zurnPriceListId = Find-OrCreate-Record `
    -EntitySet "pricelevels" `
    -Filter "name eq 'Zurn Standard Price List'" `
    -IdField "pricelevelid" `
    -Body @{
    name        = "Zurn Standard Price List"
    description = "Standard pricing for Zurn Industries products"
    begindate   = "2025-01-01"
    enddate     = "2027-12-31"
} `
    -DisplayName "Zurn Standard Price List"

$elkayPriceListId = Find-OrCreate-Record `
    -EntitySet "pricelevels" `
    -Filter "name eq 'Elkay Standard Price List'" `
    -IdField "pricelevelid" `
    -Body @{
    name        = "Elkay Standard Price List"
    description = "Standard pricing for Elkay Manufacturing products"
    begindate   = "2025-01-01"
    enddate     = "2027-12-31"
} `
    -DisplayName "Elkay Standard Price List"

# ============================================================
# 3. Products
# ============================================================
Write-Host "`nCreating products..." -ForegroundColor Yellow

$products = @(
    # --- Zurn Flush Valves ---
    @{ name = "Zurn AquaVantage AV Flush Valve"; num = "ZN-AV-1001"; brand = "Zurn"; family = "Flush Valves"; price = 245.00; desc = "1.28 GPF sensor-operated flush valve for water closets. ADA compliant." },
    @{ name = "Zurn AquaSense E-Z Flush Valve"; num = "ZN-EZ-1002"; brand = "Zurn"; family = "Flush Valves"; price = 189.00; desc = "Retrofit sensor flush valve kit for manual flush valves." },
    @{ name = "Zurn ZER6000AV Urinal Flush Valve"; num = "ZN-UR-1003"; brand = "Zurn"; family = "Flush Valves"; price = 215.00; desc = "0.5 GPF sensor urinal flush valve. Chrome finish." },

    # --- Zurn Faucets ---
    @{ name = "Zurn AquaSense Sensor Faucet"; num = "ZN-SF-2001"; brand = "Zurn"; family = "Faucets"; price = 320.00; desc = "Battery-powered sensor faucet with below-deck mixing valve." },
    @{ name = "Zurn Z86300 AquaSpec Faucet"; num = "ZN-AS-2002"; brand = "Zurn"; family = "Faucets"; price = 165.00; desc = "Commercial AquaSpec centerset faucet. 2.2 GPM aerator." },

    # --- Zurn Drainage ---
    @{ name = "Zurn Z415 Floor Drain"; num = "ZN-FD-3001"; brand = "Zurn"; family = "Drainage"; price = 89.00; desc = 'Cast iron floor drain with 5-inch round nickel bronze strainer.' },
    @{ name = "Zurn Z886 Trench Drain"; num = "ZN-TD-3002"; brand = "Zurn"; family = "Drainage"; price = 425.00; desc = 'Linear trench drain system with slotted grate. 8-inch wide.' },
    @{ name = "Zurn Z100 Roof Drain"; num = "ZN-RD-3003"; brand = "Zurn"; family = "Drainage"; price = 195.00; desc = '15-inch cast iron roof drain with low-profile dome.' },

    # --- Zurn/Wilkins Backflow ---
    @{ name = "Wilkins 975XL RPZ Assembly"; num = "WK-RP-4001"; brand = "Zurn"; family = "Backflow Prevention"; price = 1250.00; desc = 'Reduced Pressure Zone backflow preventer. 2-inch size. Lead-free.' },
    @{ name = "Wilkins 350XL Double Check Valve"; num = "WK-DC-4002"; brand = "Zurn"; family = "Backflow Prevention"; price = 485.00; desc = 'Double check valve assembly. 1-inch size. Stainless steel.' },

    # --- Elkay Hydration ---
    @{ name = "Elkay EZH2O Bottle Filling Station"; num = "EK-BF-5001"; brand = "Elkay"; family = "Hydration"; price = 1150.00; desc = "Wall-mount bottle filler with filter. Counts bottles saved." },
    @{ name = "Elkay EZS8L Cooler"; num = "EK-WC-5002"; brand = "Elkay"; family = "Hydration"; price = 780.00; desc = "8 GPH wall-mount water cooler. ADA compliant. Light gray." },
    @{ name = "Elkay LZSTL8 Bi-Level Drinking Fountain"; num = "EK-DF-5003"; brand = "Elkay"; family = "Hydration"; price = 1450.00; desc = "Bi-level drinking fountain with bottle filler. Stainless." },

    # --- Elkay Sinks ---
    @{ name = "Elkay Lustertone DLRS3322 Sink"; num = "EK-SS-6001"; brand = "Elkay"; family = "Sinks"; price = 385.00; desc = '33 x 22 inch stainless steel double bowl drop-in sink.' },
    @{ name = "Elkay ELUH3120R Undermount Sink"; num = "EK-UM-6002"; brand = "Elkay"; family = "Sinks"; price = 520.00; desc = '31-inch undermount single bowl sink. 18-gauge stainless.' },
    @{ name = "Elkay EWF3000 Water Sentry Filter"; num = "EK-FL-6003"; brand = "Elkay"; family = "Sinks"; price = 65.00; desc = "Replacement filter for bottle fillers and coolers. 3000 gal." }
)

$productIds = @{}
foreach ($p in $products) {
    # Determine price list binding
    $priceListId = if ($p.brand -eq "Zurn") { $zurnPriceListId } else { $elkayPriceListId }

    $body = @{
        name                              = $p.name
        productnumber                     = $p.num
        description                       = $p.desc
        quantitydecimal                   = 0
        producttypecode                   = 1  # Sales Inventory
        "defaultuomid@odata.bind"         = "/uoms($eachUnitId)"
        "defaultuomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
        "pricelevelid@odata.bind"         = "/pricelevels($priceListId)"
    }

    $id = Find-OrCreate-Record `
        -EntitySet "products" `
        -Filter "productnumber eq '$($p.num)'" `
        -IdField "productid" `
        -Body $body `
        -DisplayName "$($p.name) [$($p.num)]"

    if ($id) {
        $productIds[$p.num] = @{ id = $id; price = $p.price; brand = $p.brand; priceListId = $priceListId }
    }
}

# ============================================================
# 4. Price List Items
# ============================================================
Write-Host "`nCreating price list items..." -ForegroundColor Yellow

foreach ($pnum in $productIds.Keys) {
    $pInfo = $productIds[$pnum]

    $existingPLI = Invoke-DataverseGet -EntitySet "productpricelevels" `
        -Filter "_productid_value eq '$($pInfo.id)' and _pricelevelid_value eq '$($pInfo.priceListId)'" `
        -Select "productpricelevelid" -Top 1

    if (-not $existingPLI -or $existingPLI.Count -eq 0) {
        $pliBody = @{
            "productid@odata.bind"    = "/products($($pInfo.id))"
            "pricelevelid@odata.bind" = "/pricelevels($($pInfo.priceListId))"
            "uomid@odata.bind"        = "/uoms($eachUnitId)"
            amount                    = $pInfo.price
            pricingmethodcode         = 1  # Currency Amount
        }
        $result = Invoke-DataversePost -EntitySet "productpricelevels" -Body $pliBody
        if ($result) {
            Write-Host "  Price list item: $pnum = `$$($pInfo.price)" -ForegroundColor Green
        }
    } else {
        Write-Host "  Price list item exists: $pnum" -ForegroundColor DarkGray
    }
}

# ============================================================
# 5. Publish Products (make them active)
# ============================================================
Write-Host "`nPublishing products (Draft -> Active)..." -ForegroundColor Yellow

foreach ($pnum in $productIds.Keys) {
    $pInfo = $productIds[$pnum]
    try {
        $headers = Get-DataverseHeaders
        $apiUrl = Get-DataverseApiUrl
        $publishUrl = "$apiUrl/products($($pInfo.id))/Microsoft.Dynamics.CRM.PublishProductHierarchy"
        Invoke-RestMethod -Uri $publishUrl -Method Post -Headers $headers -ErrorAction Stop
        Write-Host "  Published: $pnum" -ForegroundColor Green
    } catch {
        # May already be published
        $errMsg = $_.ErrorDetails.Message
        if ($errMsg -match "published" -or $errMsg -match "active") {
            Write-Host "  Already active: $pnum" -ForegroundColor DarkGray
        } else {
            Write-Warning "  Could not publish $pnum : $($_.Exception.Message)"
        }
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Products & Price Lists Created" -ForegroundColor Green
Write-Host " Unit Group   : Plumbing Units" -ForegroundColor White
Write-Host " Price Lists  : 2 (Zurn, Elkay)" -ForegroundColor White
Write-Host " Products     : $($productIds.Count)" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

# Export
$productIds | ConvertTo-Json -Depth 3 | Out-File "$scriptDir\..\data\product-ids.json" -Encoding utf8
Write-Host "Product IDs saved to data\product-ids.json" -ForegroundColor DarkGray
