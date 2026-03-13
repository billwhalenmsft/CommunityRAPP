<#
.SYNOPSIS
    Step 20 - Seed Sales Orders for Order Management Demo
.DESCRIPTION
    Validates PO #94820 (Ferguson) exists and is complete.
    Creates additional context orders for Ferguson and HD Supply.
    Ensures all line items have line numbers and delivery dates.
    Exports order IDs for downstream Custom Page development.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "20" "Seed Sales Orders for Order Management Demo"
Connect-Dataverse

$api = Get-DataverseApiUrl
$h   = Get-DataverseHeaders

# ============================================================
# Load reference data
# ============================================================
$accountIds = Get-Content "$scriptDir\..\data\account-ids.json" | ConvertFrom-Json
$productIds = Get-Content "$scriptDir\..\data\product-ids.json" | ConvertFrom-Json

$fergusonId   = $accountIds.Distributors.'Ferguson Enterprises'
$hdSupplyId   = $accountIds.Distributors.'HD Supply'
$hajocaId     = $accountIds.Distributors.'Hajoca Corporation'

# Price list IDs
$elkayPLId = "6cfa0c6e-8d12-f111-8407-7c1e520a58a1"
$zurnPLId  = "69fa0c6e-8d12-f111-8407-7c1e520a58a1"

# Unit (Each)
$eachUnitId = "0bcd4332-8f12-f111-8407-7ced8dceb433"

# ============================================================
# Helper: Extract record ID from Invoke-DataversePost result
# (handles PSCustomObject with return=representation or GUID string)
# ============================================================
function Extract-RecordId {
    param($Result, [string]$IdProperty)
    if ($Result -is [PSCustomObject] -and $Result.$IdProperty) {
        return $Result.$IdProperty
    } elseif ($Result -is [string] -and $Result -match '[0-9a-fA-F\-]{36}') {
        return $Matches[0]
    }
    return $null
}

# ============================================================
# Helper: Create a write-in order line (no product link needed)
# ============================================================
function Add-OrderLine {
    param(
        [string]$OrderId,
        [int]$LineNumber,
        [string]$Sku,
        [string]$Description,
        [decimal]$Quantity,
        [decimal]$UnitPrice,
        [string]$DeliveryDate = "2026-03-15T00:00:00Z"
    )

    # Check if line already exists
    $existing = Invoke-DataverseGet -EntitySet "salesorderdetails" `
        -Filter "_salesorderid_value eq '$OrderId' and productdescription eq '$Sku $Description'" `
        -Select "salesorderdetailid" -Top 1

    if ($existing -and $existing.Count -gt 0) {
        Write-Host "    Line $LineNumber exists: $Sku" -ForegroundColor DarkGray
        return $existing[0].salesorderdetailid
    }

    $body = @{
        "salesorderid@odata.bind" = "/salesorders($OrderId)"
        isproductoverridden       = $true
        productdescription        = "$Sku $Description"
        quantity                  = $Quantity
        priceperunit              = $UnitPrice
        ispriceoverridden         = $true
        lineitemnumber            = $LineNumber
        requestdeliveryby         = $DeliveryDate
    }

    $result = Invoke-DataversePost -EntitySet "salesorderdetails" -Body $body
    if ($result) {
        $lineId = Extract-RecordId -Result $result -IdProperty "salesorderdetailid"
        Write-Host "    Line $LineNumber created: $Sku x $Quantity @ `$$UnitPrice" -ForegroundColor Green
        return $lineId
    }
    return $null
}

# ============================================================
# 1. Validate / Fix PO #94820 (Ferguson - DEMO ORDER)
# ============================================================
Write-Host "`n--- PO #94820 (Ferguson - DEMO ORDER) ---" -ForegroundColor Yellow

$po94820 = Invoke-DataverseGet -EntitySet "salesorders" `
    -Filter "ordernumber eq 'PO-94820'" `
    -Select "salesorderid,ordernumber,name,totalamount,statuscode,_customerid_value" -Top 1

if ($po94820 -and $po94820.Count -gt 0) {
    $orderId = $po94820[0].salesorderid
    Write-Host "  PO #94820 exists: $orderId" -ForegroundColor Green
    Write-Host "  Name: $($po94820[0].name)" -ForegroundColor DarkGray
    Write-Host "  Total: `$$($po94820[0].totalamount)" -ForegroundColor DarkGray

    # Ensure line items have line numbers + delivery dates
    $lines = Invoke-DataverseGet -EntitySet "salesorderdetails" `
        -Filter "_salesorderid_value eq '$orderId'" `
        -Select "salesorderdetailid,lineitemnumber,productdescription,requestdeliveryby" -Top 10

    foreach ($line in $lines) {
        if (-not $line.lineitemnumber -or -not $line.requestdeliveryby) {
            # Determine line number from product description
            $num = switch -Regex ($line.productdescription) {
                'EK-BF-5001' { 1 }
                'EK-WC-5002' { 2 }
                'EK-FL-6003' { 3 }
                'EK-DF-5003' { 4 }
                'EK-SS-6001' { 5 }
                default { 0 }
            }
            if ($num -gt 0) {
                $patchBody = @{ lineitemnumber = $num; requestdeliveryby = "2026-03-15T00:00:00Z" }
                Invoke-DataversePatch -EntitySet "salesorderdetails" -Id $line.salesorderdetailid -Body $patchBody
                Write-Host "    Fixed line $num : $($line.productdescription)" -ForegroundColor Cyan
            }
        } else {
            Write-Host "    Line $($line.lineitemnumber) OK: $($line.productdescription)" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "  PO #94820 NOT FOUND - creating..." -ForegroundColor Red

    $orderBody = @{
        name                        = "Ferguson PO #94820 - Hydration Products Q1"
        ordernumber                 = "PO-94820"
        description                 = "Q1 2026 hydration product order for Ferguson national rollout. 5 line items. Ship to Houston DC."
        "customerid_account@odata.bind" = "/accounts($fergusonId)"
        "pricelevelid@odata.bind"   = "/pricelevels($elkayPLId)"
        requestdeliveryby           = "2026-03-15T00:00:00Z"
        shipto_name                 = "Ferguson Houston DC"
        shipto_line1                = "8100 Washington Ave"
        shipto_city                 = "Houston"
        shipto_stateorprovince      = "TX"
        shipto_postalcode           = "77007"
        shipto_country              = "US"
        shipto_contactname          = "Mike Reynolds"
        shipto_telephone            = "(713) 555-4200"
        billto_name                 = "Ferguson Enterprises"
        billto_line1                = "12500 Jefferson Ave"
        billto_city                 = "Newport News"
        billto_stateorprovince      = "VA"
        billto_postalcode           = "23602"
        billto_country              = "US"
    }

    $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
    $orderId = Extract-RecordId -Result $result -IdProperty "salesorderid"
    Write-Host "  Created PO #94820: $orderId" -ForegroundColor Green

    # Add 5 line items
    Add-OrderLine -OrderId $orderId -LineNumber 1 -Sku "EK-BF-5001" -Description "Elkay EZH2O Bottle Filling Station" -Quantity 120 -UnitPrice 1150.00
    Add-OrderLine -OrderId $orderId -LineNumber 2 -Sku "EK-WC-5002" -Description "Elkay Wall Mount Water Cooler Bi-Level ADA" -Quantity 60 -UnitPrice 780.00
    Add-OrderLine -OrderId $orderId -LineNumber 3 -Sku "EK-FL-6003" -Description "Elkay WaterSentry Plus Replacement Filter" -Quantity 200 -UnitPrice 29.50
    Add-OrderLine -OrderId $orderId -LineNumber 4 -Sku "EK-DF-5003" -Description "Elkay Floor Mount Drinking Fountain ADA" -Quantity 25 -UnitPrice 1450.00
    Add-OrderLine -OrderId $orderId -LineNumber 5 -Sku "EK-SS-6001" -Description "Elkay Stainless Steel Single Bowl Sink Commercial" -Quantity 40 -UnitPrice 780.00
}

# ============================================================
# 2. Context Order: Ferguson PO #93201 (Delivered - Backflow)
# ============================================================
Write-Host "`n--- PO #93201 (Ferguson - Delivered Context) ---" -ForegroundColor Yellow

$po93201check = Invoke-DataverseGet -EntitySet "salesorders" `
    -Filter "ordernumber eq 'PO-93201'" `
    -Select "salesorderid" -Top 1

if ($po93201check -and $po93201check.Count -gt 0) {
    Write-Host "  PO #93201 already exists" -ForegroundColor DarkGray
} else {
    $orderBody = @{
        name                        = "Ferguson PO #93201 - Zurn Backflow Q4 2025"
        ordernumber                 = "PO-93201"
        description                 = "Q4 2025 backflow prevention devices order. Delivered. Ferguson national replenishment."
        "customerid_account@odata.bind" = "/accounts($fergusonId)"
        "pricelevelid@odata.bind"   = "/pricelevels($zurnPLId)"
        datefulfilled               = "2025-12-18T00:00:00Z"
        shipto_name                 = "Ferguson Atlanta DC"
        shipto_city                 = "Atlanta"
        shipto_stateorprovince      = "GA"
        shipto_postalcode           = "30339"
        shipto_country              = "US"
        shipto_contactname          = "Rachel Chen"
        billto_name                 = "Ferguson Enterprises"
        billto_city                 = "Newport News"
        billto_stateorprovince      = "VA"
        billto_country              = "US"
    }

    $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
    $po93201Id = Extract-RecordId -Result $result -IdProperty "salesorderid"
    Write-Host "  Created PO #93201: $po93201Id" -ForegroundColor Green

    Add-OrderLine -OrderId $po93201Id -LineNumber 1 -Sku "WK-RP-4001" -Description "Wilkins 975XL RPZ Assembly 2-inch" -Quantity 30 -UnitPrice 1250.00 -DeliveryDate "2025-12-15T00:00:00Z"
    Add-OrderLine -OrderId $po93201Id -LineNumber 2 -Sku "WK-DC-4002" -Description "Wilkins 350XL Double Check Valve 1-inch" -Quantity 50 -UnitPrice 485.00 -DeliveryDate "2025-12-15T00:00:00Z"
    Add-OrderLine -OrderId $po93201Id -LineNumber 3 -Sku "ZN-AV-1001" -Description "Zurn AquaVantage AV Flush Valve" -Quantity 100 -UnitPrice 245.00 -DeliveryDate "2025-12-15T00:00:00Z"
    Add-OrderLine -OrderId $po93201Id -LineNumber 4 -Sku "ZN-EZ-1002" -Description "Zurn AquaSense E-Z Flush Retrofit Kit" -Quantity 75 -UnitPrice 189.00 -DeliveryDate "2025-12-15T00:00:00Z"
    Add-OrderLine -OrderId $po93201Id -LineNumber 5 -Sku "ZN-FD-3001" -Description "Zurn Z415 Floor Drain 5-inch" -Quantity 40 -UnitPrice 89.00 -DeliveryDate "2025-12-15T00:00:00Z"
}

# ============================================================
# 3. Context Order: Ferguson PO #95102 (Active - Flush Valves)
# ============================================================
Write-Host "`n--- PO #95102 (Ferguson - Active Context) ---" -ForegroundColor Yellow

$po95102check = Invoke-DataverseGet -EntitySet "salesorders" `
    -Filter "ordernumber eq 'PO-95102'" `
    -Select "salesorderid" -Top 1

if ($po95102check -and $po95102check.Count -gt 0) {
    Write-Host "  PO #95102 already exists" -ForegroundColor DarkGray
} else {
    $orderBody = @{
        name                        = "Ferguson PO #95102 - Flush Valves Replenishment"
        ordernumber                 = "PO-95102"
        description                 = "Q1 2026 flush valve replenishment for Ferguson Southeast branches."
        "customerid_account@odata.bind" = "/accounts($fergusonId)"
        "pricelevelid@odata.bind"   = "/pricelevels($zurnPLId)"
        requestdeliveryby           = "2026-04-01T00:00:00Z"
        shipto_name                 = "Ferguson Jacksonville DC"
        shipto_city                 = "Jacksonville"
        shipto_stateorprovince      = "FL"
        shipto_postalcode           = "32256"
        shipto_country              = "US"
        shipto_contactname          = "Rachel Chen"
        billto_name                 = "Ferguson Enterprises"
        billto_city                 = "Newport News"
        billto_stateorprovince      = "VA"
        billto_country              = "US"
    }

    $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
    $po95102Id = Extract-RecordId -Result $result -IdProperty "salesorderid"
    Write-Host "  Created PO #95102: $po95102Id" -ForegroundColor Green

    Add-OrderLine -OrderId $po95102Id -LineNumber 1 -Sku "ZN-AV-1001" -Description "Zurn AquaVantage AV Flush Valve" -Quantity 200 -UnitPrice 245.00 -DeliveryDate "2026-04-01T00:00:00Z"
    Add-OrderLine -OrderId $po95102Id -LineNumber 2 -Sku "ZN-UR-1003" -Description "Zurn ZER6000AV Urinal Flush Valve" -Quantity 80 -UnitPrice 215.00 -DeliveryDate "2026-04-01T00:00:00Z"
    Add-OrderLine -OrderId $po95102Id -LineNumber 3 -Sku "ZN-EZ-1002" -Description "Zurn AquaSense E-Z Flush Retrofit Kit" -Quantity 150 -UnitPrice 189.00 -DeliveryDate "2026-04-01T00:00:00Z"
}

# ============================================================
# 4. HD Supply Order: PO #HD-7845 (Active - for demo variety)
# ============================================================
Write-Host "`n--- PO #HD-7845 (HD Supply - Active) ---" -ForegroundColor Yellow

$hdOrderCheck = Invoke-DataverseGet -EntitySet "salesorders" `
    -Filter "ordernumber eq 'PO-HD-7845'" `
    -Select "salesorderid" -Top 1

if ($hdOrderCheck -and $hdOrderCheck.Count -gt 0) {
    Write-Host "  PO #HD-7845 already exists" -ForegroundColor DarkGray
} else {
    $orderBody = @{
        name                        = "HD Supply PO #HD-7845 - Sensor Products Q1"
        ordernumber                 = "PO-HD-7845"
        description                 = "Q1 2026 sensor flush valve and faucet order for HD Supply national hotel chain contracts."
        "customerid_account@odata.bind" = "/accounts($hdSupplyId)"
        "pricelevelid@odata.bind"   = "/pricelevels($zurnPLId)"
        requestdeliveryby           = "2026-03-20T00:00:00Z"
        shipto_name                 = "HD Supply Atlanta DC"
        shipto_line1                = "3400 Peachtree Rd NE"
        shipto_city                 = "Atlanta"
        shipto_stateorprovince      = "GA"
        shipto_postalcode           = "30326"
        shipto_country              = "US"
        shipto_contactname          = "Derek Lawson"
        shipto_telephone            = "(770) 555-2305"
        billto_name                 = "HD Supply"
        billto_city                 = "Atlanta"
        billto_stateorprovince      = "GA"
        billto_country              = "US"
    }

    $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
    $hdOrderId = Extract-RecordId -Result $result -IdProperty "salesorderid"
    Write-Host "  Created PO #HD-7845: $hdOrderId" -ForegroundColor Green

    Add-OrderLine -OrderId $hdOrderId -LineNumber 1 -Sku "ZN-AV-1001" -Description "Zurn AquaVantage AV Flush Valve" -Quantity 50 -UnitPrice 245.00 -DeliveryDate "2026-03-20T00:00:00Z"
    Add-OrderLine -OrderId $hdOrderId -LineNumber 2 -Sku "ZN-SF-2001" -Description "Zurn AquaSense Sensor Faucet" -Quantity 30 -UnitPrice 320.00 -DeliveryDate "2026-03-20T00:00:00Z"
    Add-OrderLine -OrderId $hdOrderId -LineNumber 3 -Sku "ZN-UR-1003" -Description "Zurn ZER6000AV Urinal Flush Valve" -Quantity 40 -UnitPrice 215.00 -DeliveryDate "2026-03-20T00:00:00Z"
    Add-OrderLine -OrderId $hdOrderId -LineNumber 4 -Sku "EK-BF-5001" -Description "Elkay EZH2O Bottle Filling Station" -Quantity 20 -UnitPrice 1150.00 -DeliveryDate "2026-03-20T00:00:00Z"
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Sales Orders Seeded for Order Management Demo" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

# Collect all order IDs for export
$orderExport = @{}

$allOrders = Invoke-DataverseGet -EntitySet "salesorders" `
    -Filter "startswith(ordernumber,'PO-')" `
    -Select "salesorderid,ordernumber,name,totalamount,_customerid_value,statuscode" -Top 20

foreach ($o in $allOrders) {
    $custName = switch ($o._customerid_value) {
        $fergusonId { "Ferguson" }
        $hdSupplyId { "HD Supply" }
        $hajocaId   { "Hajoca" }
        default     { "Unknown" }
    }
    Write-Host "  $($o.ordernumber) | $custName | `$$($o.totalamount) | status=$($o.statuscode)" -ForegroundColor Cyan
    $orderExport[$o.ordernumber] = @{
        id       = $o.salesorderid
        name     = $o.name
        customer = $custName
        total    = $o.totalamount
    }
}

$orderExport | ConvertTo-Json -Depth 3 | Out-File "$scriptDir\..\data\order-ids.json" -Encoding utf8
Write-Host "`nOrder IDs saved to data\order-ids.json" -ForegroundColor DarkGray
