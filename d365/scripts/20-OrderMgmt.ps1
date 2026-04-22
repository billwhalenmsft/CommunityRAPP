<#
.SYNOPSIS
    Step 20 - Seed Sales Orders for Order Management Demo
.DESCRIPTION
    Customer-driven: reads salesOrders section from customers/{Customer}/d365/config/demo-data.json.
    Creates Sales Orders with realistic line items linked to demo accounts.
    Falls back to legacy Zurn/Elkay hardcoded orders if no salesOrders section found.
    Also exports order IDs to data/order-ids.json for downstream use.

.PARAMETER Customer
    Customer folder name (e.g., "navico", "zurnelkay", "otis"). Defaults to "zurnelkay".
#>

param(
    [string]$Customer = "zurnelkay"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent (Split-Path -Parent $scriptDir)
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "20" "Seed Sales Orders for Order Management Demo"
Connect-Dataverse

$api = Get-DataverseApiUrl
$h   = Get-DataverseHeaders

# ============================================================
# Helper: Extract record ID from Invoke-DataversePost result
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
        [string]$DeliveryDate = "2026-04-30T00:00:00Z"
    )

    $lineKey = "$Sku $Description"
    $existing = Invoke-DataverseGet -EntitySet "salesorderdetails" `
        -Filter "_salesorderid_value eq '$OrderId' and productdescription eq '$lineKey'" `
        -Select "salesorderdetailid" -Top 1

    if ($existing -and $existing.Count -gt 0) {
        Write-Host "    Line $LineNumber exists: $Sku" -ForegroundColor DarkGray
        return $existing[0].salesorderdetailid
    }

    $body = @{
        "salesorderid@odata.bind" = "/salesorders($OrderId)"
        isproductoverridden        = $true
        productdescription         = $lineKey
        quantity                   = $Quantity
        priceperunit               = $UnitPrice
        ispriceoverridden          = $true
        lineitemnumber             = $LineNumber
        requestdeliveryby          = $DeliveryDate
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
# Helper: Look up account ID by name (cached)
# ============================================================
$accountCache = @{}
function Get-AccountId([string]$AccountName) {
    if ($accountCache.ContainsKey($AccountName)) { return $accountCache[$AccountName] }
    $enc = [Uri]::EscapeDataString($AccountName)
    $r = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$AccountName'" -Select "accountid" -Top 1
    if ($r -and $r.Count -gt 0) {
        $accountCache[$AccountName] = $r[0].accountid
        return $r[0].accountid
    }
    return $null
}

# ============================================================
# Helper: Look up price list ID by name (cached)
# ============================================================
$priceListCache = @{}
function Get-PriceListId([string]$PriceListName) {
    if ($priceListCache.ContainsKey($PriceListName)) { return $priceListCache[$PriceListName] }
    $r = Invoke-DataverseGet -EntitySet "pricelevels" -Filter "name eq '$PriceListName' and statecode eq 0" -Select "pricelevelid" -Top 1
    if ($r -and $r.Count -gt 0) {
        $priceListCache[$PriceListName] = $r[0].pricelevelid
        return $r[0].pricelevelid
    }
    return $null
}

# ============================================================
# Load customer demo-data.json
# ============================================================
$demoDataFile = Join-Path $repoRoot "customers\$Customer\d365\config\demo-data.json"
$useLegacy    = $false

if (-not (Test-Path $demoDataFile)) {
    Write-Warning "demo-data.json not found for $Customer — using legacy Zurn orders."
    $useLegacy = $true
} else {
    $demoData = Get-Content $demoDataFile -Raw | ConvertFrom-Json
    if (-not $demoData.salesOrders -or -not $demoData.salesOrders.orders) {
        Write-Warning "No 'salesOrders' section in demo-data.json for $Customer — using legacy Zurn orders."
        $useLegacy = $true
    }
}

$orderExport = @{}

if (-not $useLegacy) {
    # ==============================================================
    # CUSTOMER-DRIVEN PATH — reads from demo-data.json salesOrders
    # ==============================================================
    $ordersConfig  = $demoData.salesOrders
    $priceListName = $ordersConfig.priceListName
    $orders        = $ordersConfig.orders

    Write-Host "`nCustomer: $Customer | Price List: $priceListName | Orders: $($orders.Count)" -ForegroundColor Cyan

    $priceListId = Get-PriceListId -PriceListName $priceListName
    if (-not $priceListId) {
        Write-Warning "Price list '$priceListName' not found — orders will be created without price list binding."
    } else {
        Write-Host "Price list ID: $priceListId" -ForegroundColor DarkGray
    }

    foreach ($order in $orders) {
        Write-Host "`n--- $($order.orderNumber) ($($order.account)) ---" -ForegroundColor Yellow

        $existing = Invoke-DataverseGet -EntitySet "salesorders" `
            -Filter "ordernumber eq '$($order.orderNumber)'" `
            -Select "salesorderid,ordernumber" -Top 1

        if ($existing -and $existing.Count -gt 0) {
            Write-Host "  Already exists: $($existing[0].salesorderid)" -ForegroundColor DarkGray
            $orderExport[$order.orderNumber] = @{ id = $existing[0].salesorderid; name = $order.name; customer = $order.account }
            continue
        }

        $accountId = Get-AccountId -AccountName $order.account
        if (-not $accountId) {
            Write-Warning "  Account '$($order.account)' not found — skipping order $($order.orderNumber)"
            continue
        }

        # Contact (optional)
        $contactId = $null
        if ($order.contact) {
            $cResult = Invoke-DataverseGet -EntitySet "contacts" `
                -Filter "contains(fullname,'$($order.contact)')" `
                -Select "contactid" -Top 1
            if ($cResult -and $cResult.Count -gt 0) { $contactId = $cResult[0].contactid }
        }

        # Delivery date
        $deliveryDate = if ($order.requestDeliveryBy) { "$($order.requestDeliveryBy)T00:00:00Z" } else { "2026-04-30T00:00:00Z" }

        # Build order body
        $orderBody = @{
            name                            = $order.name
            ordernumber                     = $order.orderNumber
            description                     = $order.description
            "customerid_account@odata.bind" = "/accounts($accountId)"
            requestdeliveryby               = $deliveryDate
        }
        if ($priceListId) { $orderBody["pricelevelid@odata.bind"] = "/pricelevels($priceListId)" }
        # Note: salesorders contact binding not supported via odata.bind in this org — skip
        if ($order.shipTo) {
            $s = $order.shipTo
            if ($s.name)       { $orderBody["shipto_name"]            = $s.name }
            if ($s.line1)      { $orderBody["shipto_line1"]           = $s.line1 }
            if ($s.city)       { $orderBody["shipto_city"]            = $s.city }
            if ($s.state)      { $orderBody["shipto_stateorprovince"] = $s.state }
            if ($s.postalCode) { $orderBody["shipto_postalcode"]      = $s.postalCode }
            if ($s.country)    { $orderBody["shipto_country"]         = $s.country }
            if ($s.contact)    { $orderBody["shipto_contactname"]     = $s.contact }
            if ($s.phone)      { $orderBody["shipto_telephone"]       = $s.phone }
        }

        # Fulfilled date for completed orders
        if ($order.status -eq "Fulfilled" -or $order.status -eq "Delivered") {
            $orderBody["datefulfilled"] = $deliveryDate
        }

        $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
        $orderId = Extract-RecordId -Result $result -IdProperty "salesorderid"
        if (-not $orderId) { Write-Warning "  Failed to create $($order.orderNumber)"; continue }
        Write-Host "  Created: $orderId" -ForegroundColor Green

        # Create line items
        $lineNum = 1
        foreach ($line in $order.lineItems) {
            $lineDelivery = $deliveryDate
            Add-OrderLine -OrderId $orderId -LineNumber $lineNum `
                -Sku $line.sku -Description $line.description `
                -Quantity $line.quantity -UnitPrice $line.unitPrice `
                -DeliveryDate $lineDelivery
            $lineNum++
        }

        $orderExport[$order.orderNumber] = @{
            id       = $orderId
            name     = $order.name
            customer = $order.account
            tracking = if ($order.tracking) { $order.tracking } else { $null }
        }
    }

} else {
    # ==============================================================
    # LEGACY PATH — Zurn/Elkay hardcoded orders (backward compat)
    # ==============================================================
    $accountIds = @{}
    $accountIdsFile = "$scriptDir\..\data\account-ids.json"
    if (Test-Path $accountIdsFile) {
        $accountIds = Get-Content $accountIdsFile | ConvertFrom-Json
    }

    $productIds = @{}
    $productIdsFile = "$scriptDir\..\data\product-ids.json"
    if (Test-Path $productIdsFile) {
        $productIds = Get-Content $productIdsFile | ConvertFrom-Json
    }

    $fergusonId = $accountIds.Distributors.'Ferguson Enterprises'
    $hdSupplyId = $accountIds.Distributors.'HD Supply'
    $hajocaId   = $accountIds.Distributors.'Hajoca Corporation'
    $elkayPLId  = "6cfa0c6e-8d12-f111-8407-7c1e520a58a1"
    $zurnPLId   = "69fa0c6e-8d12-f111-8407-7c1e520a58a1"

    # ---- PO #94820 (Ferguson - HERO) ----
    Write-Host "`n--- PO #94820 (Ferguson - DEMO ORDER) ---" -ForegroundColor Yellow
    $po94820 = Invoke-DataverseGet -EntitySet "salesorders" -Filter "ordernumber eq 'PO-94820'" -Select "salesorderid,ordernumber,name,totalamount,statuscode" -Top 1
    if ($po94820 -and $po94820.Count -gt 0) {
        $orderId = $po94820[0].salesorderid
        Write-Host "  PO #94820 exists: $orderId" -ForegroundColor Green
        # Ensure line items have line numbers + delivery dates
        $lines = Invoke-DataverseGet -EntitySet "salesorderdetails" -Filter "_salesorderid_value eq '$orderId'" -Select "salesorderdetailid,lineitemnumber,productdescription,requestdeliveryby" -Top 10
        foreach ($line in $lines) {
            if (-not $line.lineitemnumber -or -not $line.requestdeliveryby) {
                $num = switch -Regex ($line.productdescription) {
                    'EK-BF-5001' { 1 } 'EK-WC-5002' { 2 } 'EK-FL-6003' { 3 } 'EK-DF-5003' { 4 } 'EK-SS-6001' { 5 } default { 0 }
                }
                if ($num -gt 0) {
                    Invoke-DataversePatch -EntitySet "salesorderdetails" -Id $line.salesorderdetailid -Body @{ lineitemnumber = $num; requestdeliveryby = "2026-03-15T00:00:00Z" }
                    Write-Host "    Fixed line $num : $($line.productdescription)" -ForegroundColor Cyan
                }
            } else { Write-Host "    Line $($line.lineitemnumber) OK: $($line.productdescription)" -ForegroundColor DarkGray }
        }
        $orderExport["PO-94820"] = @{ id = $orderId; name = $po94820[0].name; customer = "Ferguson" }
    } else {
        $orderBody = @{
            name = "Ferguson PO #94820 - Hydration Products Q1"; ordernumber = "PO-94820"
            description = "Q1 2026 hydration product order for Ferguson national rollout."
            "customerid_account@odata.bind" = "/accounts($fergusonId)"
            "pricelevelid@odata.bind" = "/pricelevels($elkayPLId)"
            requestdeliveryby = "2026-03-15T00:00:00Z"
            shipto_name = "Ferguson Houston DC"; shipto_line1 = "8100 Washington Ave"
            shipto_city = "Houston"; shipto_stateorprovince = "TX"; shipto_postalcode = "77007"; shipto_country = "US"
            shipto_contactname = "Mike Reynolds"; shipto_telephone = "(713) 555-4200"
            billto_name = "Ferguson Enterprises"; billto_line1 = "12500 Jefferson Ave"
            billto_city = "Newport News"; billto_stateorprovince = "VA"; billto_country = "US"
        }
        $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
        $orderId = Extract-RecordId -Result $result -IdProperty "salesorderid"
        Write-Host "  Created PO #94820: $orderId" -ForegroundColor Green
        Add-OrderLine -OrderId $orderId -LineNumber 1 -Sku "EK-BF-5001" -Description "Elkay EZH2O Bottle Filling Station" -Quantity 120 -UnitPrice 1150.00
        Add-OrderLine -OrderId $orderId -LineNumber 2 -Sku "EK-WC-5002" -Description "Elkay Wall Mount Water Cooler Bi-Level ADA" -Quantity 60 -UnitPrice 780.00
        Add-OrderLine -OrderId $orderId -LineNumber 3 -Sku "EK-FL-6003" -Description "Elkay WaterSentry Plus Replacement Filter" -Quantity 200 -UnitPrice 29.50
        Add-OrderLine -OrderId $orderId -LineNumber 4 -Sku "EK-DF-5003" -Description "Elkay Floor Mount Drinking Fountain ADA" -Quantity 25 -UnitPrice 1450.00
        Add-OrderLine -OrderId $orderId -LineNumber 5 -Sku "EK-SS-6001" -Description "Elkay Stainless Steel Single Bowl Sink Commercial" -Quantity 40 -UnitPrice 780.00
        $orderExport["PO-94820"] = @{ id = $orderId; name = "Ferguson PO #94820"; customer = "Ferguson" }
    }

    # ---- PO #93201 (Ferguson - Delivered) ----
    Write-Host "`n--- PO #93201 (Ferguson - Delivered Context) ---" -ForegroundColor Yellow
    $po93201check = Invoke-DataverseGet -EntitySet "salesorders" -Filter "ordernumber eq 'PO-93201'" -Select "salesorderid" -Top 1
    if ($po93201check -and $po93201check.Count -gt 0) {
        Write-Host "  PO #93201 already exists" -ForegroundColor DarkGray
        $orderExport["PO-93201"] = @{ id = $po93201check[0].salesorderid; name = "Ferguson PO #93201"; customer = "Ferguson" }
    } else {
        $orderBody = @{
            name = "Ferguson PO #93201 - Zurn Backflow Q4 2025"; ordernumber = "PO-93201"
            description = "Q4 2025 backflow prevention devices order. Delivered."
            "customerid_account@odata.bind" = "/accounts($fergusonId)"
            "pricelevelid@odata.bind" = "/pricelevels($zurnPLId)"
            datefulfilled = "2025-12-18T00:00:00Z"; shipto_name = "Ferguson Atlanta DC"
            shipto_city = "Atlanta"; shipto_stateorprovince = "GA"; shipto_country = "US"
            billto_name = "Ferguson Enterprises"; billto_city = "Newport News"; billto_country = "US"
        }
        $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
        $id = Extract-RecordId -Result $result -IdProperty "salesorderid"; Write-Host "  Created PO #93201: $id" -ForegroundColor Green
        Add-OrderLine -OrderId $id -LineNumber 1 -Sku "WK-RP-4001" -Description "Wilkins 975XL RPZ Assembly 2-inch" -Quantity 30 -UnitPrice 1250.00 -DeliveryDate "2025-12-15T00:00:00Z"
        Add-OrderLine -OrderId $id -LineNumber 2 -Sku "WK-DC-4002" -Description "Wilkins 350XL Double Check Valve 1-inch" -Quantity 50 -UnitPrice 485.00 -DeliveryDate "2025-12-15T00:00:00Z"
        Add-OrderLine -OrderId $id -LineNumber 3 -Sku "ZN-AV-1001" -Description "Zurn AquaVantage AV Flush Valve" -Quantity 100 -UnitPrice 245.00 -DeliveryDate "2025-12-15T00:00:00Z"
        $orderExport["PO-93201"] = @{ id = $id; name = "Ferguson PO #93201"; customer = "Ferguson" }
    }

    # ---- PO #95102 (Ferguson - Active) ----
    Write-Host "`n--- PO #95102 (Ferguson - Active Context) ---" -ForegroundColor Yellow
    $po95102check = Invoke-DataverseGet -EntitySet "salesorders" -Filter "ordernumber eq 'PO-95102'" -Select "salesorderid" -Top 1
    if ($po95102check -and $po95102check.Count -gt 0) {
        Write-Host "  PO #95102 already exists" -ForegroundColor DarkGray
        $orderExport["PO-95102"] = @{ id = $po95102check[0].salesorderid; name = "Ferguson PO #95102"; customer = "Ferguson" }
    } else {
        $orderBody = @{
            name = "Ferguson PO #95102 - Flush Valves Replenishment"; ordernumber = "PO-95102"
            description = "Q1 2026 flush valve replenishment for Ferguson Southeast."
            "customerid_account@odata.bind" = "/accounts($fergusonId)"
            "pricelevelid@odata.bind" = "/pricelevels($zurnPLId)"
            requestdeliveryby = "2026-04-01T00:00:00Z"
            shipto_city = "Jacksonville"; shipto_stateorprovince = "FL"; shipto_country = "US"
            billto_name = "Ferguson Enterprises"; billto_city = "Newport News"; billto_country = "US"
        }
        $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
        $id = Extract-RecordId -Result $result -IdProperty "salesorderid"; Write-Host "  Created PO #95102: $id" -ForegroundColor Green
        Add-OrderLine -OrderId $id -LineNumber 1 -Sku "ZN-AV-1001" -Description "Zurn AquaVantage AV Flush Valve" -Quantity 200 -UnitPrice 245.00
        Add-OrderLine -OrderId $id -LineNumber 2 -Sku "ZN-UR-1003" -Description "Zurn ZER6000AV Urinal Flush Valve" -Quantity 80 -UnitPrice 215.00
        $orderExport["PO-95102"] = @{ id = $id; name = "Ferguson PO #95102"; customer = "Ferguson" }
    }

    # ---- PO #HD-7845 (HD Supply) ----
    Write-Host "`n--- PO #HD-7845 (HD Supply - Active) ---" -ForegroundColor Yellow
    $hdOrderCheck = Invoke-DataverseGet -EntitySet "salesorders" -Filter "ordernumber eq 'PO-HD-7845'" -Select "salesorderid" -Top 1
    if ($hdOrderCheck -and $hdOrderCheck.Count -gt 0) {
        Write-Host "  PO #HD-7845 already exists" -ForegroundColor DarkGray
        $orderExport["PO-HD-7845"] = @{ id = $hdOrderCheck[0].salesorderid; name = "HD Supply PO #HD-7845"; customer = "HD Supply" }
    } else {
        $orderBody = @{
            name = "HD Supply PO #HD-7845 - Sensor Products Q1"; ordernumber = "PO-HD-7845"
            description = "Q1 2026 sensor flush valve and faucet order for HD Supply hotel contracts."
            "customerid_account@odata.bind" = "/accounts($hdSupplyId)"
            "pricelevelid@odata.bind" = "/pricelevels($zurnPLId)"
            requestdeliveryby = "2026-03-20T00:00:00Z"
            shipto_name = "HD Supply Atlanta DC"; shipto_line1 = "3400 Peachtree Rd NE"
            shipto_city = "Atlanta"; shipto_stateorprovince = "GA"; shipto_postalcode = "30326"; shipto_country = "US"
            shipto_contactname = "Derek Lawson"; shipto_telephone = "(770) 555-2305"
            billto_name = "HD Supply"; billto_city = "Atlanta"; billto_country = "US"
        }
        $result = Invoke-DataversePost -EntitySet "salesorders" -Body $orderBody
        $id = Extract-RecordId -Result $result -IdProperty "salesorderid"; Write-Host "  Created PO #HD-7845: $id" -ForegroundColor Green
        Add-OrderLine -OrderId $id -LineNumber 1 -Sku "ZN-AV-1001" -Description "Zurn AquaVantage AV Flush Valve" -Quantity 50 -UnitPrice 245.00
        Add-OrderLine -OrderId $id -LineNumber 2 -Sku "ZN-SF-2001" -Description "Zurn AquaSense Sensor Faucet" -Quantity 30 -UnitPrice 320.00
        Add-OrderLine -OrderId $id -LineNumber 3 -Sku "EK-BF-5001" -Description "Elkay EZH2O Bottle Filling Station" -Quantity 20 -UnitPrice 1150.00
        $orderExport["PO-HD-7845"] = @{ id = $id; name = "HD Supply PO #HD-7845"; customer = "HD Supply" }
    }
}

# ============================================================
# Summary & Export
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Sales Orders Seeded — $Customer" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

foreach ($key in $orderExport.Keys) {
    $o = $orderExport[$key]
    Write-Host "  $key | $($o.customer) | $($o.name)" -ForegroundColor Cyan
}

# Write to data dir
$dataDir = "$scriptDir\..\data"
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir -Force | Out-Null }
$orderExport | ConvertTo-Json -Depth 4 | Out-File "$dataDir\order-ids.json" -Encoding utf8
Write-Host "`nOrder IDs saved to data\order-ids.json" -ForegroundColor DarkGray
