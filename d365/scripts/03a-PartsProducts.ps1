<#
.SYNOPSIS
    Step 03a - Create Aftermarket Parts Products & Price List
.DESCRIPTION
    Reads a customer-specific parts-catalog.json and provisions:
    - Unit Group (for parts)
    - Price List (customer-named aftermarket parts)
    - Products (with cr74e_parts = true flag)
    - Price List Items (linking products to the parts price list)
    - Publishes products (Draft -> Active)

    This is a reusable script — it reads all data from the JSON file,
    not hardcoded. Each customer project can have its own parts catalog
    at customers/{customer}/d365/data/parts-catalog.json.

.PARAMETER CatalogFile
    Path to the parts-catalog.json file. If not specified, the script
    looks in the standard location: customers/{Customer}/d365/data/parts-catalog.json

.PARAMETER Customer
    Customer folder name (e.g., "otis", "zurnelkay"). Used to locate
    the parts-catalog.json when CatalogFile is not specified.

.EXAMPLE
    .\03a-PartsProducts.ps1 -Customer otis
    .\03a-PartsProducts.ps1 -CatalogFile "C:\path\to\parts-catalog.json"
#>

param(
    [string]$CatalogFile,
    [string]$Customer
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent (Split-Path -Parent $scriptDir)
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "03a" "Create Aftermarket Parts Products & Price List"

# ============================================================
# 0. Locate and load the parts catalog
# ============================================================
if (-not $CatalogFile) {
    if (-not $Customer) {
        Write-Error "Specify -Customer or -CatalogFile. Example: .\03a-PartsProducts.ps1 -Customer otis"
        exit 1
    }
    $CatalogFile = Join-Path $repoRoot "customers\$Customer\d365\data\parts-catalog.json"
}

if (-not (Test-Path $CatalogFile)) {
    Write-Error "Parts catalog not found: $CatalogFile"
    exit 1
}

Write-Host "Loading parts catalog: $CatalogFile" -ForegroundColor Cyan
$catalog = Get-Content $CatalogFile -Raw | ConvertFrom-Json

# Validate required fields
if (-not $catalog.priceListName) { Write-Error "parts-catalog.json missing 'priceListName'"; exit 1 }
if (-not $catalog.parts -or $catalog.parts.Count -eq 0) { Write-Error "parts-catalog.json has no parts"; exit 1 }

$customerName    = $catalog.customer
$priceListName   = $catalog.priceListName
$unitGroupName   = if ($catalog.unitGroupName) { $catalog.unitGroupName } else { "$customerName Service Parts" }
$baseUnitName    = if ($catalog.baseUnitName)  { $catalog.baseUnitName }  else { "Each" }
$validFrom       = if ($catalog.validFrom)     { $catalog.validFrom }     else { "2025-01-01" }
$validTo         = if ($catalog.validTo)       { $catalog.validTo }       else { "2027-12-31" }

Write-Host "  Customer      : $customerName" -ForegroundColor White
Write-Host "  Price List    : $priceListName" -ForegroundColor White
Write-Host "  Unit Group    : $unitGroupName" -ForegroundColor White
Write-Host "  Parts Count   : $($catalog.parts.Count)" -ForegroundColor White
Write-Host "  Valid          : $validFrom to $validTo" -ForegroundColor White

Connect-Dataverse

# ============================================================
# 1. Unit Group
# ============================================================
Write-Host "`nCreating unit group..." -ForegroundColor Yellow

$unitGroupId = Find-OrCreate-Record `
    -EntitySet "uomschedules" `
    -Filter "name eq '$unitGroupName'" `
    -IdField "uomscheduleid" `
    -Body @{ name = $unitGroupName; baseuomname = $baseUnitName; description = "Unit group for $customerName aftermarket parts" } `
    -DisplayName $unitGroupName

# Get the primary unit (auto-created with the schedule)
$primaryUnit = Invoke-DataverseGet -EntitySet "uoms" `
    -Filter "_uomscheduleid_value eq '$unitGroupId' and isschedulebaseuom eq true" `
    -Select "uomid,name" -Top 1

if ($primaryUnit) {
    $eachUnitId = $primaryUnit[0].uomid
    Write-Host "  Primary unit: $($primaryUnit[0].name) ($eachUnitId)" -ForegroundColor DarkGray
} else {
    $eachUnitId = Find-OrCreate-Record `
        -EntitySet "uoms" `
        -Filter "name eq '$baseUnitName' and _uomscheduleid_value eq '$unitGroupId'" `
        -IdField "uomid" `
        -Body @{
            name                       = $baseUnitName
            "uomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
            quantity                   = 1
        } `
        -DisplayName $baseUnitName
}

# ============================================================
# 2. Price List
# ============================================================
Write-Host "`nCreating price list..." -ForegroundColor Yellow

$priceListId = Find-OrCreate-Record `
    -EntitySet "pricelevels" `
    -Filter "name eq '$priceListName'" `
    -IdField "pricelevelid" `
    -Body @{
        name        = $priceListName
        description = "Aftermarket parts pricing for $customerName"
        begindate   = $validFrom
        enddate     = $validTo
    } `
    -DisplayName $priceListName

# ============================================================
# 3. Products
# ============================================================
Write-Host "`nCreating products ($($catalog.parts.Count) parts)..." -ForegroundColor Yellow

$productIds = @{}
$created = 0
$existing = 0

foreach ($part in $catalog.parts) {
    # Support both field name conventions: num/desc/price (legacy) and sku/description/unitPrice (new)
    $partNum   = if ($part.num)         { $part.num }         else { $part.sku }
    $partDesc  = if ($part.desc)        { $part.desc }        else { $part.description }
    $partPrice = if ($null -ne $part.price) { $part.price }   else { $part.unitPrice }

    if (-not $partNum) { Write-Host "  Skipping part with no sku/num: $($part.name)" -ForegroundColor DarkYellow; continue }

    $body = @{
        name                              = $part.name
        productnumber                     = $partNum
        description                       = $partDesc
        quantitydecimal                   = 2
        producttypecode                   = 1  # Sales Inventory
        "defaultuomid@odata.bind"         = "/uoms($eachUnitId)"
        "defaultuomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
        "pricelevelid@odata.bind"         = "/pricelevels($priceListId)"
    }

    $id = Find-OrCreate-Record `
        -EntitySet "products" `
        -Filter "productnumber eq '$partNum'" `
        -IdField "productid" `
        -Body $body `
        -DisplayName "$($part.name) [$partNum]"

    if ($id) {
        $productIds[$partNum] = @{
            id          = $id
            price       = $partPrice
            category    = $part.category
            priceListId = $priceListId
        }
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
# 5. Publish Products (Draft -> Active)
# ============================================================
Write-Host "`nPublishing products (Draft -> Active)..." -ForegroundColor Yellow

foreach ($pnum in $productIds.Keys) {
    $pInfo = $productIds[$pnum]
    try {
        $headers = Get-DataverseHeaders
        $apiUrl  = Get-DataverseApiUrl
        $publishUrl = "$apiUrl/products($($pInfo.id))/Microsoft.Dynamics.CRM.PublishProductHierarchy"
        Invoke-RestMethod -Uri $publishUrl -Method Post -Headers $headers -ErrorAction Stop
        Write-Host "  Published: $pnum" -ForegroundColor Green
    } catch {
        $errMsg = $_.ErrorDetails.Message
        if ($errMsg -match "published" -or $errMsg -match "active") {
            Write-Host "  Already active: $pnum" -ForegroundColor DarkGray
        } else {
            Write-Warning "  Could not publish $pnum : $($_.Exception.Message)"
        }
    }
}

# ============================================================
# Summary & Export
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Aftermarket Parts Created" -ForegroundColor Green
Write-Host " Customer     : $customerName" -ForegroundColor White
Write-Host " Price List   : $priceListName" -ForegroundColor White
Write-Host " Unit Group   : $unitGroupName" -ForegroundColor White
Write-Host " Products     : $($productIds.Count)" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

# Export IDs to customer data folder
$outputDir = Split-Path -Parent $CatalogFile
$outputFile = Join-Path $outputDir "parts-product-ids.json"
$productIds | ConvertTo-Json -Depth 3 | Out-File $outputFile -Encoding utf8
Write-Host "Parts product IDs saved to $outputFile" -ForegroundColor DarkGray
