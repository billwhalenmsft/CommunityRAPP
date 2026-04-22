<#
.SYNOPSIS
    Navico Extended Provisioning — Price Lists, Products, Customer Assets, Entitlements, Tier Logic
.DESCRIPTION
    Provisions all extended demo data for the Navico D365 CS demo build:

    Section 1 - PriceList / Products
        • Unit Group: "Marine Electronics Units"
        • 5 brand price lists (Lowrance, Simrad, B&G, C-MAP, Northstar)
        • 26 products mapped to the correct price list
        • Price list items (productpricelevels) per product
        • Publishes each product via PublishProductHierarchy

    Section 2 - CustomerAssets
        • Reads equipment arrays from customers\navico\d365\config\demo-data.json
        • Creates msdyn_customerasset records per serial (expanded from count)
        • Idempotent — skips existing serials

    Section 3 - Entitlements
        • Creates Entitlement Templates for each Navico support tier
        • Creates per-account Entitlements with channel allocations
        • Activates entitlements
        • Attempts SLA binding to "Navico Standard SLA"

    Section 4 - TierLogic
        • Queries Navico demo cases (accounts prefixed NAV-)
        • Updates case prioritycode based on account tier

.PARAMETER Action
    Which section(s) to run. Default = "All"

.EXAMPLE
    .\Provision-NavicoExtended.ps1
    .\Provision-NavicoExtended.ps1 -Action CustomerAssets
    .\Provision-NavicoExtended.ps1 -Action Entitlements
#>

[CmdletBinding()]
param(
    [ValidateSet("All","PriceList","Products","CustomerAssets","Entitlements","TierLogic","BrandLogo","Cleanup")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"

# ============================================================
# Bootstrap — load shared DataverseHelper
# ============================================================
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperPath = Join-Path $scriptDir "..\..\..\d365\scripts\DataverseHelper.psm1"

if (-not (Test-Path $helperPath)) {
    Write-Error "DataverseHelper.psm1 not found at: $helperPath"
    exit 1
}
Import-Module $helperPath -Force

# ============================================================
# Shared constants
# ============================================================
$DEMO_DATA_PATH = Join-Path $scriptDir "config\demo-data.json"
$OUTPUT_IDS_PATH = Join-Path $scriptDir "data\navico-extended-ids.json"

# Dataverse option-set constants
$ALLOCATION_CASES   = 0
$KB_STANDARD        = 0
$KB_PREMIUM         = 1
$ENTITY_TYPE_CASE   = 0
$DECREASE_ON_CREATE = 1
$CHANNEL_PHONE      = 1
$CHANNEL_EMAIL      = 2
$CHANNEL_WEB        = 3

# ============================================================
# Summary counters (accumulate across sections)
# ============================================================
$script:summary = @{
    ProductsCreated      = 0
    AssetsCreated        = 0
    AssetsSkipped        = 0
    EntitlementsCreated  = 0
    TierUpdatesApplied   = 0
}

# IDs to persist at end
$script:persistedIds = @{
    UnitGroupId  = $null
    PriceLists   = @{}
    Products     = @{}
    Templates    = @{}
    Entitlements = @{}
}

# ============================================================
# Helper: load demo-data.json
# ============================================================
function Get-DemoData {
    if (-not (Test-Path $DEMO_DATA_PATH)) {
        Write-Error "demo-data.json not found at: $DEMO_DATA_PATH"
        exit 1
    }
    return Get-Content $DEMO_DATA_PATH -Raw | ConvertFrom-Json
}

# ============================================================
# Helper: Expand-SerialRange
#   Copied from 26-CustomerAssets.ps1
#   "SIM-AMS-NSX-001" with count=8 → SIM-AMS-NSX-001 .. SIM-AMS-NSX-008
# ============================================================
function Expand-SerialRange {
    param(
        [string]$SerialPattern,
        [int]$Count
    )

    $parts = $SerialPattern -split '-'

    # Determine prefix and start number:
    # Strategy: find the last segment that is purely numeric — that is the start index.
    # Everything before it becomes the prefix.
    $lastPart = $parts[-1]
    $startNum = 0
    $lastIsNumeric = [int]::TryParse($lastPart, [ref]$startNum)

    if ($lastIsNumeric) {
        # e.g. SIM-AMS-NSX-001 → prefix=SIM-AMS-NSX, start=1
        # e.g. GEN2-WL-001 → prefix=GEN2-WL, start=1
        $prefix = ($parts[0..($parts.Count - 2)]) -join '-'
    }
    else {
        # Last segment not numeric — use whole string as prefix, start at 1
        $prefix   = $SerialPattern
        $startNum = 1
    }

    $serials = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $num      = $startNum + $i
        $serials += "$prefix-$($num.ToString('000'))"
    }
    return $serials
}

# ============================================================
# Helper: account-id cache
# ============================================================
$script:accountCache = @{}

function Get-AccountId {
    param([string]$AccountNumber)

    if ($script:accountCache.ContainsKey($AccountNumber)) {
        return $script:accountCache[$AccountNumber]
    }

    $escaped = $AccountNumber -replace "'", "''"
    $found = Invoke-DataverseGet -EntitySet "accounts" `
        -Filter "accountnumber eq '$escaped'" `
        -Select "accountid" -Top 1

    if ($found -and $found.Count -gt 0) {
        $id = [guid]$found[0].accountid
        $script:accountCache[$AccountNumber] = $id
        return $id
    }
    return $null
}

# ===========================================================
# ███████╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗ 1
# ██╔════╝██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║
# ███████╗█████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║
# ╚════██║██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║
# ███████║███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║
# ╚══════╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
#   Price Lists + Products
# ===========================================================
function Provision-PriceListAndProducts {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  SECTION 1 — Price Lists & Products" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan

    # ----------------------------------------------------------
    # 1a. Unit Group
    # ----------------------------------------------------------
    Write-Host "`nCreating unit group..." -ForegroundColor Yellow

    $unitGroupId = Find-OrCreate-Record `
        -EntitySet   "uomschedules" `
        -Filter      "name eq 'Marine Electronics Units'" `
        -IdField     "uomscheduleid" `
        -Body        @{
            name        = "Marine Electronics Units"
            baseuomname = "Each"
            description = "Unit group for Navico marine electronics products"
        } `
        -DisplayName "Marine Electronics Units"

    $script:persistedIds.UnitGroupId = $unitGroupId.ToString()

    # Retrieve the auto-created base unit (or create it)
    $primaryUnit = Invoke-DataverseGet -EntitySet "uoms" `
        -Filter "_uomscheduleid_value eq '$unitGroupId' and isschedulebaseuom eq true" `
        -Select "uomid,name" -Top 1

    if ($primaryUnit -and $primaryUnit.Count -gt 0) {
        $eachUnitId = $primaryUnit[0].uomid
        Write-Host "  Base unit: $($primaryUnit[0].name) ($eachUnitId)" -ForegroundColor DarkGray
    }
    else {
        $eachUnitId = Find-OrCreate-Record `
            -EntitySet "uoms" `
            -Filter    "name eq 'Each' and _uomscheduleid_value eq '$unitGroupId'" `
            -IdField   "uomid" `
            -Body      @{
                name                       = "Each"
                "uomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
                quantity                   = 1
            } `
            -DisplayName "Each"
    }

    # ----------------------------------------------------------
    # 1b. Brand Price Lists
    # ----------------------------------------------------------
    Write-Host "`nCreating brand price lists..." -ForegroundColor Yellow

    $priceLists = @(
        @{ name = "Navico Lowrance Price List";  desc = "Lowrance brand products"  }
        @{ name = "Navico Simrad Price List";    desc = "Simrad brand products"    }
        @{ name = "Navico B&G Price List";       desc = "B&G sailing products"     }
        @{ name = "Navico C-MAP Price List";     desc = "C-MAP chart subscriptions"}
        @{ name = "Navico Northstar Price List"; desc = "Northstar legacy products" }
    )

    $priceListIds = @{}
    foreach ($pl in $priceLists) {
        $plId = Find-OrCreate-Record `
            -EntitySet "pricelevels" `
            -Filter    "name eq '$($pl.name)'" `
            -IdField   "pricelevelid" `
            -Body      @{
                name        = $pl.name
                description = $pl.desc
                begindate   = "2025-01-01"
                enddate     = "2028-12-31"
            } `
            -DisplayName $pl.name
        $priceListIds[$pl.name] = $plId
        $script:persistedIds.PriceLists[$pl.name] = $plId.ToString()
    }

    # ----------------------------------------------------------
    # 1c. Products
    # ----------------------------------------------------------
    Write-Host "`nCreating products..." -ForegroundColor Yellow

    $products = @(
        # ── LOWRANCE ──────────────────────────────────────────────────
        @{ num="LWR-HDS-LIVE9";  brand="Lowrance"; priceList="Navico Lowrance Price List"; price=699.99;
           name="Lowrance HDS Live 9 Fishfinder/Chartplotter";
           desc="Premium 9-inch fishfinder/chartplotter with CHIRP sonar, GPS mapping. SolarMAX HD display." }

        @{ num="LWR-HDS-LIVE12"; brand="Lowrance"; priceList="Navico Lowrance Price List"; price=1099.99;
           name="Lowrance HDS Live 12 Fishfinder/Chartplotter";
           desc="Premium 12-inch multi-touch display fishfinder/chartplotter. C-MAP compatible." }

        @{ num="LWR-HDS-CARB12"; brand="Lowrance"; priceList="Navico Lowrance Price List"; price=1499.99;
           name="Lowrance HDS Carbon 12 MFD";
           desc="High-performance 12-inch MFD with advanced networking, StructureScan 3D capability." }

        @{ num="LWR-ELITE-FS7";  brand="Lowrance"; priceList="Navico Lowrance Price List"; price=399.99;
           name="Lowrance Elite FS 7 Fishfinder";
           desc="Mid-range 7-inch fishfinder with built-in C-MAP chart. FishReveal CHIRP." }

        @{ num="LWR-HOOK-REV7";  brand="Lowrance"; priceList="Navico Lowrance Price List"; price=199.99;
           name="Lowrance Hook Reveal 7 Fishfinder";
           desc="Entry-level 7-inch fishfinder with FishReveal CHIRP sonar. 4-level zoom." }

        @{ num="LWR-ACTGT-2";    brand="Lowrance"; priceList="Navico Lowrance Price List"; price=899.99;
           name="Lowrance ActiveTarget 2 Live Sonar";
           desc="Real-time live sonar for viewing fish in 3 directions simultaneously." }

        @{ num="LWR-GHOST-97";   brand="Lowrance"; priceList="Navico Lowrance Price List"; price=1799.99;
           name="Lowrance Ghost Trolling Motor 97lb";
           desc="GPS-enabled brushless electric trolling motor, 97lb thrust. Ultra-quiet." }

        # ── SIMRAD ────────────────────────────────────────────────────
        @{ num="SIM-NSX-3007";   brand="Simrad"; priceList="Navico Simrad Price List"; price=899.99;
           name="Simrad NSX 3007 Chartplotter";
           desc="7-inch multifunction chartplotter/fishfinder. SolarMAX display. Built-in CHIRP." }

        @{ num="SIM-NSX-3009";   brand="Simrad"; priceList="Navico Simrad Price List"; price=1099.99;
           name="Simrad NSX 3009 Chartplotter";
           desc="9-inch MFD chartplotter with advanced sonar. Wireless connectivity." }

        @{ num="SIM-NSS-EVO3S9"; brand="Simrad"; priceList="Navico Simrad Price List"; price=1299.99;
           name="Simrad NSS evo3S 9 MFD";
           desc="Advanced 9-inch multifunction display with full networking. Autopilot ready." }

        @{ num="SIM-GO9-XSE";    brand="Simrad"; priceList="Navico Simrad Price List"; price=549.99;
           name="Simrad GO9 XSE Chartplotter";
           desc="Entry-level 9-inch chartplotter/fishfinder. SonarChart Live capability." }

        @{ num="SIM-HALO-20";    brand="Simrad"; priceList="Navico Simrad Price List"; price=1999.99;
           name="Simrad Halo 20 Pulse Radar";
           desc="20-inch pulse compression radar dome. 48 RPM, Doppler target separation." }

        @{ num="SIM-AP44";       brand="Simrad"; priceList="Navico Simrad Price List"; price=799.99;
           name="Simrad AP44 Autopilot Controller";
           desc="Autopilot control unit for hydraulic/mechanical steering. Colour display." }

        @{ num="SIM-RS90S";      brand="Simrad"; priceList="Navico Simrad Price List"; price=349.99;
           name="Simrad RS90S VHF Radio";
           desc="Class D DSC marine VHF radio. AIS display, NMEA 2000 compatible." }

        # ── B&G ───────────────────────────────────────────────────────
        @{ num="BG-ZEUS-S9";     brand="B&G"; priceList="Navico B&G Price List"; price=1199.99;
           name="B&G Zeus S 9 Sailing Chartplotter";
           desc="9-inch sailing MFD with regatta timer, sail performance features. SailSteer." }

        @{ num="BG-VULCAN-9R";   brand="B&G"; priceList="Navico B&G Price List"; price=799.99;
           name="B&G Vulcan 9R Sailing Chartplotter";
           desc="9-inch touchscreen sailing chartplotter. Integrated Navionics chart data." }

        @{ num="BG-TRI2-DISP";   brand="B&G"; priceList="Navico B&G Price List"; price=299.99;
           name="B&G Triton2 Instrument Display";
           desc="4.1-inch multi-purpose sailing instrument. Speed, depth, wind, heading." }

        @{ num="BG-H5000-PC";    brand="B&G"; priceList="Navico B&G Price List"; price=1599.99;
           name="B&G H5000 Pilot Controller";
           desc="Performance sailing instrument with autopilot integration. 4.1-inch display." }

        @{ num="BG-NAVTEX-300";  brand="B&G"; priceList="Navico B&G Price List"; price=399.99;
           name="B&G Navtex 300 Safety Receiver";
           desc="Dedicated NAVTEX receiver for maritime safety broadcasts. 3-inch display." }

        # ── C-MAP ─────────────────────────────────────────────────────
        @{ num="CMAP-REVEAL-1Y"; brand="C-MAP"; priceList="Navico C-MAP Price List"; price=149.99;
           name="C-MAP REVEAL Chart Subscription 1yr";
           desc="High-resolution coastal/inland charts. Relief shading, aerial photos." }

        @{ num="CMAP-DISC-1Y";   brand="C-MAP"; priceList="Navico C-MAP Price List"; price=99.99;
           name="C-MAP DISCOVER Chart Subscription 1yr";
           desc="Detailed charts for fishing and cruising. Depth contours, POI data." }

        @{ num="CMAP-4D-1Y";     brand="C-MAP"; priceList="Navico C-MAP Price List"; price=199.99;
           name="C-MAP 4D Chart Subscription 1yr";
           desc="Dynamic tidal/current data with weather overlay integration." }

        @{ num="CMAP-GENESIS-1Y";brand="C-MAP"; priceList="Navico C-MAP Price List"; price=79.99;
           name="C-MAP Genesis Chart Subscription 1yr";
           desc="Crowd-sourced bathymetric mapping. High-resolution freshwater charts." }

        @{ num="CMAP-PILOT-APP"; brand="C-MAP"; priceList="Navico C-MAP Price List"; price=49.99;
           name="C-MAP Pilot Mobile App Subscription";
           desc="Mobile navigation app for iOS/Android. Offline chart storage." }

        # ── NORTHSTAR ─────────────────────────────────────────────────
        @{ num="NS-VHF-8600";    brand="Northstar"; priceList="Navico Northstar Price List"; price=249.99;
           name="Northstar VHF 8600 Marine Radio";
           desc="Class D DSC VHF marine radio. Legacy compatible. IPX7 waterproof." }

        @{ num="NS-6000I-GPS";   brand="Northstar"; priceList="Navico Northstar Price List"; price=449.99;
           name="Northstar 6000i GPS Chartplotter";
           desc="Legacy GPS chartplotter. Compatible with older Northstar chart cards." }
    )

    $productIds = @{}

    foreach ($p in $products) {
        $plId = $priceListIds[$p.priceList]

        $body = @{
            name                              = $p.name
            productnumber                     = $p.num
            description                       = $p.desc
            quantitydecimal                   = 0
            producttypecode                   = 1   # Sales Inventory
            "defaultuomid@odata.bind"         = "/uoms($eachUnitId)"
            "defaultuomscheduleid@odata.bind" = "/uomschedules($unitGroupId)"
            "pricelevelid@odata.bind"         = "/pricelevels($plId)"
        }

        $id = Find-OrCreate-Record `
            -EntitySet   "products" `
            -Filter      "productnumber eq '$($p.num)'" `
            -IdField     "productid" `
            -Body        $body `
            -DisplayName "$($p.name) [$($p.num)]"

        if ($id) {
            $productIds[$p.num] = @{
                id          = $id
                price       = $p.price
                brand       = $p.brand
                priceListId = $plId
            }
            $script:summary.ProductsCreated++
        }
    }

    # ----------------------------------------------------------
    # 1d. Price List Items
    # ----------------------------------------------------------
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
                pricingmethodcode         = 1   # Currency Amount
            }
            $result = Invoke-DataversePost -EntitySet "productpricelevels" -Body $pliBody
            if ($result) {
                Write-Host "  PLI: $pnum = `$$($pInfo.price)" -ForegroundColor Green
            }
        }
        else {
            Write-Host "  PLI exists: $pnum" -ForegroundColor DarkGray
        }
    }

    # ----------------------------------------------------------
    # 1e. Publish Products
    # ----------------------------------------------------------
    Write-Host "`nPublishing products..." -ForegroundColor Yellow

    $headers = Get-DataverseHeaders
    $apiUrl  = Get-DataverseApiUrl

    foreach ($pnum in $productIds.Keys) {
        $pInfo      = $productIds[$pnum]
        $publishUrl = "$apiUrl/products($($pInfo.id))/Microsoft.Dynamics.CRM.PublishProductHierarchy"
        try {
            Invoke-RestMethod -Uri $publishUrl -Method Post -Headers $headers `
                -TimeoutSec 30 -ErrorAction Stop | Out-Null
            Write-Host "  Published: $pnum" -ForegroundColor Green
        }
        catch {
            $errMsg = $_.ErrorDetails.Message
            if ($errMsg -match "published" -or $errMsg -match "active" -or $errMsg -match "Active") {
                Write-Host "  Already active: $pnum" -ForegroundColor DarkGray
            }
            else {
                Write-Warning "  Could not publish $pnum : $($_.Exception.Message)"
            }
        }
    }

    # Cache product IDs for export
    foreach ($k in $productIds.Keys) {
        $script:persistedIds.Products[$k] = $productIds[$k].id.ToString()
    }

    Write-Host ""
    Write-Host "  Products section complete. Count: $($productIds.Count)" -ForegroundColor Green
}

# ===========================================================
#   Brand Logo Helpers
# ===========================================================

# Map serial prefix → full web resource URL (absolute URL required by Canvas App Image control)
# SVGs uploaded by Upload-BrandLogos.ps1
$script:orgBaseUrl  = (Get-DataverseApiUrl) -replace '/api/data/v9\.2$', ''
$script:brandLogoMap = [ordered]@{
    "LWR-"  = "$($script:orgBaseUrl)/WebResources/cr74e_logo_lowrance"
    "SIM-"  = "$($script:orgBaseUrl)/WebResources/cr74e_logo_simrad"
    "BG-"   = "$($script:orgBaseUrl)/WebResources/cr74e_logo_bng"
    "CMAP-" = "$($script:orgBaseUrl)/WebResources/cr74e_logo_cmap"
    "NST-"  = "$($script:orgBaseUrl)/WebResources/cr74e_logo_northstar"
}
$script:defaultLogoUrl = "$($script:orgBaseUrl)/WebResources/cr74e_logo_navico"
$script:genericLogoUrl = "$($script:orgBaseUrl)/WebResources/cr74e_logo_generic_mfg"

function Get-BrandLogoUrl([string]$Serial) {
    if ([string]::IsNullOrWhiteSpace($Serial)) { return $script:genericLogoUrl }
    foreach ($prefix in $script:brandLogoMap.Keys) {
        if ($Serial -like "$prefix*") { return $script:brandLogoMap[$prefix] }
    }
    return $script:defaultLogoUrl
}

function Ensure-AssetBrandLogoColumn {
    $api = Get-DataverseApiUrl
    $h   = Get-DataverseHeaders

    $logicalName = "bw_brandlogourl"
    $exists = $false
    try {
        Invoke-RestMethod -Method GET `
            -Uri "$api/EntityDefinitions(LogicalName='msdyn_customerasset')/Attributes(LogicalName='$logicalName')?`$select=LogicalName" `
            -Headers $h -ErrorAction Stop | Out-Null
        $exists = $true
    } catch { }

    if ($exists) {
        Write-Host "  Column 'bw_brandlogourl' already exists on msdyn_customerasset" -ForegroundColor DarkGray
        return
    }

    $body = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        SchemaName    = "bw_BrandLogoUrl"
        DisplayName   = @{
            "@odata.type"   = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label         = "Brand Logo URL"
                LanguageCode  = 1033
            })
        }
        Description = @{
            "@odata.type"   = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label         = "Web resource path for the brand logo displayed in Service Toolkit sidebar"
                LanguageCode  = 1033
            })
        }
        RequiredLevel = @{ Value = "None"; CanBeChanged = $true }
        MaxLength     = 200
        FormatName    = @{ Value = "Text" }
    } | ConvertTo-Json -Depth 5

    Invoke-RestMethod -Method POST `
        -Uri "$api/EntityDefinitions(LogicalName='msdyn_customerasset')/Attributes" `
        -Headers $h -Body $body -ContentType "application/json" -ErrorAction Stop | Out-Null
    Write-Host "  Created column 'bw_BrandLogoUrl' on msdyn_customerasset" -ForegroundColor Green

    # Publish
    $publishBody = @{
        ParameterXml = "<importexportxml><entities><entity>msdyn_customerasset</entity></entities></importexportxml>"
    } | ConvertTo-Json
    Invoke-RestMethod -Method POST -Uri "$api/PublishXml" `
        -Headers $h -Body $publishBody -ContentType "application/json" -ErrorAction Stop | Out-Null
    Write-Host "  Published msdyn_customerasset" -ForegroundColor DarkGray
    # Column metadata can take a few seconds to propagate before it can be queried/patched
    Write-Host "  Waiting for metadata cache to propagate..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 15
}

function Provision-AssetBrandLogos {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  SECTION — Asset Brand Logo Backfill" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan

    # Build full org URL now (after Connect-Dataverse has run)
    $orgBase = (Get-DataverseApiUrl) -replace '/api/data/v9\.2$', ''
    $script:brandLogoMap = [ordered]@{
        "LWR-"  = "$orgBase/WebResources/cr74e_logo_lowrance"
        "SIM-"  = "$orgBase/WebResources/cr74e_logo_simrad"
        "BG-"   = "$orgBase/WebResources/cr74e_logo_bng"
        "CMAP-" = "$orgBase/WebResources/cr74e_logo_cmap"
        "NST-"  = "$orgBase/WebResources/cr74e_logo_northstar"
    }
    $script:defaultLogoUrl = "$orgBase/WebResources/cr74e_logo_navico"
    $script:genericLogoUrl = "$orgBase/WebResources/cr74e_logo_generic_mfg"

    Ensure-AssetBrandLogoColumn

    # Query all Navico customer assets (those belonging to NAV-* accounts)
    Write-Host "  Querying Navico customer assets..." -ForegroundColor Yellow
    $allAssets = @()
    foreach ($prefix in @("NAV-B2B-PE", "NAV-B2B-PL", "NAV-B2B-GD", "NAV-B2B-SL", "NAV-B2B-STD", "NAV-B2C")) {
        $accts = Invoke-DataverseGet -EntitySet "accounts" `
            -Filter "startswith(accountnumber,'$prefix')" `
            -Select "accountid,accountnumber"
        if ($accts) {
            foreach ($acct in $accts) {
                $assets = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
                    -Filter "_msdyn_account_value eq $($acct.accountid)" `
                    -Select "msdyn_customerassetid,msdyn_name,bw_brandlogourl"
                if ($assets) { $allAssets += $assets }
            }
        }
    }

    if (-not $allAssets -or $allAssets.Count -eq 0) {
        Write-Host "  No Navico assets found." -ForegroundColor DarkYellow
        return
    }

    Write-Host "  Found $($allAssets.Count) assets to evaluate." -ForegroundColor DarkGray

    $updated = 0; $skipped = 0; $failed = 0

    foreach ($asset in $allAssets) {
        $serial  = $asset.msdyn_name
        $logoUrl = Get-BrandLogoUrl -Serial $serial

        if ($asset.bw_brandlogourl -eq $logoUrl) {
            $skipped++
            continue
        }

        $result = Invoke-DataversePatch -EntitySet "msdyn_customerassets" `
            -RecordId ([guid]$asset.msdyn_customerassetid) `
            -Body @{ bw_brandlogourl = $logoUrl }

        if ($result) {
            Write-Host "  $serial → $logoUrl" -ForegroundColor Green
            $updated++
        } else {
            Write-Host "  FAILED: $serial" -ForegroundColor Red
            $failed++
        }
    }

    Write-Host ""
    Write-Host "  Brand logos set. Updated: $updated  Unchanged: $skipped  Failed: $failed" -ForegroundColor Green
}

# ===========================================================
# ███████╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗ 2
#   Customer Assets
# ===========================================================
function Provision-CustomerAssets {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  SECTION 2 — Customer Assets" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan

    $demoData = Get-DemoData
    Write-Host "Loaded: $($demoData._metadata.customer)" -ForegroundColor DarkGray

    $accounts = $demoData.serviceAccounts.accounts
    Write-Host "Processing $($accounts.Count) accounts..." -ForegroundColor Yellow

    foreach ($acct in $accounts) {
        $accountId = Get-AccountId -AccountNumber $acct.accountNumber
        if (-not $accountId) {
            Write-Host "  SKIP: '$($acct.name)' ($($acct.accountNumber)) — not found in Dataverse" -ForegroundColor DarkYellow
            continue
        }

        if (-not $acct.equipment -or $acct.equipment.Count -eq 0) {
            Write-Host "  SKIP: '$($acct.name)' — no equipment array" -ForegroundColor DarkGray
            continue
        }

        Write-Host "`n  Account: $($acct.name) ($($acct.accountNumber))" -ForegroundColor Cyan

        foreach ($equip in $acct.equipment) {
            $serials = Expand-SerialRange -SerialPattern $equip.serial -Count $equip.count

            foreach ($serial in $serials) {
                $yearsBack    = Get-Random -Minimum 1 -Maximum 4
                $warrantyYrs  = Get-Random -Minimum 3 -Maximum 6
                $wStart       = (Get-Date).AddYears(-$yearsBack).Date
                $wEnd         = $wStart.AddYears($warrantyYrs).Date

                $body = @{
                    msdyn_name                 = $serial
                    msdyn_assettag             = "$($equip.model) — $($equip.type)"
                    "msdyn_account@odata.bind" = "/accounts($accountId)"
                    jdk_assetstatus            = 752870000   # Purchased
                    jdk_warrantystartdate      = $wStart.ToString("yyyy-MM-ddT00:00:00Z")
                    jdk_warrantyenddate        = $wEnd.ToString("yyyy-MM-ddT00:00:00Z")
                    cra1f_contracttype         = "276120000"  # Standard Warranty
                }

                # Link to product record if productId is in equipment config
                if ($equip.productId) {
                    $body["msdyn_product@odata.bind"] = "/products($($equip.productId))"
                }

                # lastServiceDate with slight per-asset offset for realism
                if ($acct.lastServiceDate) {
                    $baseSvcDate = [datetime]::Parse($acct.lastServiceDate)
                    $dayOffset   = ([array]$serials).IndexOf($serial) % 15 - 7
                    $svcDate     = $baseSvcDate.AddDays($dayOffset)
                    if ($svcDate -gt (Get-Date)) { $svcDate = $baseSvcDate }
                    $body["bw_lastservicedon"] = $svcDate.ToString("yyyy-MM-ddT00:00:00Z")
                }

                $escapedSerial = $serial -replace "'", "''"
                $existing = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
                    -Filter "msdyn_name eq '$escapedSerial'" `
                    -Select "msdyn_customerassetid" -Top 1

                if ($existing -and $existing.Count -gt 0) {
                    Write-Host "    EXISTS : $serial" -ForegroundColor DarkGray
                    $script:summary.AssetsSkipped++
                }
                else {
                    $result = Invoke-DataversePost -EntitySet "msdyn_customerassets" -Body $body
                    if ($result) {
                        Write-Host "    CREATED: $serial  ($($equip.model))" -ForegroundColor Green
                        $script:summary.AssetsCreated++
                    }
                    else {
                        Write-Host "    FAILED : $serial" -ForegroundColor Red
                    }
                }
            }
        }
    }

    Write-Host ""
    Write-Host "  Assets section complete. Created: $($script:summary.AssetsCreated)  Skipped: $($script:summary.AssetsSkipped)" -ForegroundColor Green
}

# ===========================================================
# ███████╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗ 3
#   Entitlements
# ===========================================================
function Provision-Entitlements {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  SECTION 3 — Entitlements" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan

    # ----------------------------------------------------------
    # Tier definitions (Navico labels)
    # ----------------------------------------------------------
    $tierDefs = @{
        "PlatinumExpert" = @{
            label            = "Platinum Expert"
            templateName     = "Navico Platinum Expert Support Template"
            entitlementName  = "Navico Platinum Expert Support"
            totalCases       = 500
            kbAccess         = $KB_PREMIUM
            restrictAtLimit  = $false
            description      = "Navico Platinum Expert — 500 cases/yr, Premium KB, all channels, 2hr SLA priority."
            channels         = @(
                @{ type = $CHANNEL_PHONE; cases = 200; name = "Phone" }
                @{ type = $CHANNEL_EMAIL; cases = 200; name = "Email" }
                @{ type = $CHANNEL_WEB;   cases = 100; name = "Web"   }
            )
        }
        "Platinum" = @{
            label            = "Platinum"
            templateName     = "Navico Platinum Support Template"
            entitlementName  = "Navico Platinum Support"
            totalCases       = 250
            kbAccess         = $KB_PREMIUM
            restrictAtLimit  = $false
            description      = "Navico Platinum — 250 cases/yr, Premium KB, all channels, 4hr SLA priority."
            channels         = @(
                @{ type = $CHANNEL_PHONE; cases = 100; name = "Phone" }
                @{ type = $CHANNEL_EMAIL; cases = 100; name = "Email" }
                @{ type = $CHANNEL_WEB;   cases = 50;  name = "Web"   }
            )
        }
        "Gold" = @{
            label            = "Gold"
            templateName     = "Navico Gold Support Template"
            entitlementName  = "Navico Gold Support"
            totalCases       = 100
            kbAccess         = $KB_STANDARD
            restrictAtLimit  = $true
            description      = "Navico Gold — 100 cases/yr, Standard KB, all channels, 8hr SLA. Restricted at limit."
            channels         = @(
                @{ type = $CHANNEL_PHONE; cases = 30; name = "Phone" }
                @{ type = $CHANNEL_EMAIL; cases = 50; name = "Email" }
                @{ type = $CHANNEL_WEB;   cases = 20; name = "Web"   }
            )
        }
        "Silver" = @{
            label            = "Silver"
            templateName     = $null   # No template requested for Silver
            entitlementName  = "Navico Silver Support"
            totalCases       = 50
            kbAccess         = $KB_STANDARD
            restrictAtLimit  = $true
            description      = "Navico Silver — 50 cases/yr, Standard KB, email and web only, 1-day SLA."
            channels         = @(
                @{ type = $CHANNEL_EMAIL; cases = 35; name = "Email" }
                @{ type = $CHANNEL_WEB;   cases = 15; name = "Web"   }
            )
        }
        "Standard" = @{
            label            = "Standard"
            templateName     = "Navico Standard Support Template"
            entitlementName  = "Navico Standard Support"
            totalCases       = 50
            kbAccess         = $KB_STANDARD
            restrictAtLimit  = $true
            description      = "Navico Standard — 50 cases/yr, Standard KB, email and web only."
            channels         = @(
                @{ type = $CHANNEL_EMAIL; cases = 35; name = "Email" }
                @{ type = $CHANNEL_WEB;   cases = 15; name = "Web"   }
            )
        }
        "Consumer" = @{
            label            = "Consumer"
            templateName     = $null
            entitlementName  = "Navico Consumer Support"
            totalCases       = 20
            kbAccess         = $KB_STANDARD
            restrictAtLimit  = $true
            description      = "Navico Consumer — 20 cases/yr, Standard KB, web only."
            channels         = @(
                @{ type = $CHANNEL_WEB; cases = 20; name = "Web" }
            )
        }
    }

    # Account-number prefix → tier key mapping
    $tierPrefixMap = @(
        @{ prefix = "NAV-B2B-PE";  tierKey = "PlatinumExpert" }
        @{ prefix = "NAV-B2B-PL";  tierKey = "Platinum"       }
        @{ prefix = "NAV-B2B-GD";  tierKey = "Gold"           }
        @{ prefix = "NAV-B2B-SL";  tierKey = "Silver"         }
        @{ prefix = "NAV-B2B-STD"; tierKey = "Standard"       }
        @{ prefix = "NAV-B2C";     tierKey = "Consumer"       }
    )

    $startDate = "2026-01-01T00:00:00Z"
    $endDate   = "2026-12-31T23:59:59Z"

    # ----------------------------------------------------------
    # 3a. Look up SLA (non-fatal if absent)
    # ----------------------------------------------------------
    Write-Host "Looking up Navico Standard SLA..." -ForegroundColor Yellow
    $slaRecords = Invoke-DataverseGet -EntitySet "slas" `
        -Filter "name eq 'Navico Standard SLA'" `
        -Select "slaid,name" -Top 1

    $slaId = $null
    if ($slaRecords -and $slaRecords.Count -gt 0) {
        $slaId = $slaRecords[0].slaid
        Write-Host "  SLA found: $($slaRecords[0].name) ($slaId)" -ForegroundColor DarkGray
    }
    else {
        Write-Warning "SLA 'Navico Standard SLA' not found. Entitlements created without SLA binding."
    }

    # ----------------------------------------------------------
    # 3b. Transaction currency (USD)
    # ----------------------------------------------------------
    $currencies = Invoke-DataverseGet -EntitySet "transactioncurrencies" `
        -Filter "isocurrencycode eq 'USD'" `
        -Select "transactioncurrencyid" -Top 1
    $currencyId = $null
    if ($currencies -and $currencies.Count -gt 0) {
        $currencyId = $currencies[0].transactioncurrencyid
    }

    # ----------------------------------------------------------
    # 3c. Entitlement Templates
    # ----------------------------------------------------------
    Write-Host "`nCreating entitlement templates..." -ForegroundColor Yellow

    $templateIds = @{}
    foreach ($key in $tierDefs.Keys) {
        $def = $tierDefs[$key]
        if (-not $def.templateName) { continue }

        $tplBody = @{
            name                 = $def.templateName
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
        if ($slaId) { $tplBody["slaid@odata.bind"] = "/slas($slaId)" }

        $tplId = Find-OrCreate-Record `
            -EntitySet   "entitlementtemplates" `
            -Filter      "name eq '$($def.templateName)'" `
            -IdField     "entitlementtemplateid" `
            -Body        $tplBody `
            -DisplayName $def.templateName

        if ($tplId) {
            $templateIds[$key] = $tplId
            $script:persistedIds.Templates[$def.templateName] = $tplId.ToString()
        }
    }
    Write-Host "  Templates created/verified: $($templateIds.Count)" -ForegroundColor Green

    # ----------------------------------------------------------
    # 3d. Per-account entitlements
    # ----------------------------------------------------------
    Write-Host "`nCreating per-account entitlements..." -ForegroundColor Yellow

    $entitlementResults = @{ created = 0; skipped = 0; channelCreated = 0; channelSkipped = 0 }

    foreach ($mapping in $tierPrefixMap) {
        $prefix  = $mapping.prefix
        $tierKey = $mapping.tierKey
        $def     = $tierDefs[$tierKey]

        $accounts = Invoke-DataverseGet -EntitySet "accounts" `
            -Filter "startswith(accountnumber,'$prefix')" `
            -Select "accountid,name,accountnumber"

        if (-not $accounts -or $accounts.Count -eq 0) {
            Write-Host "  No accounts found for prefix: $prefix" -ForegroundColor DarkGray
            continue
        }

        foreach ($acct in $accounts) {
            $entName        = "Navico $($def.label) — $($acct.name)"
            $escapedEntName = $entName -replace "'", "''"

            Write-Host "  [$entName]" -ForegroundColor Cyan

            $entBody = @{
                name                            = $entName
                description                     = "$($def.description) Account: $($acct.name)."
                "customerid_account@odata.bind" = "/accounts($($acct.accountid))"
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
            if ($slaId) { $entBody["slaid@odata.bind"] = "/slas($slaId)" }
            if ($templateIds.ContainsKey($tierKey)) {
                $entBody["entitlementtemplateid@odata.bind"] = "/entitlementtemplates($($templateIds[$tierKey]))"
            }

            $entId = Find-OrCreate-Record `
                -EntitySet   "entitlements" `
                -Filter      "name eq '$escapedEntName'" `
                -IdField     "entitlementid" `
                -Body        $entBody `
                -DisplayName $entName

            if ($entId) {
                $script:persistedIds.Entitlements[$acct.name] = $entId.ToString()
                $entitlementResults.created++
                $script:summary.EntitlementsCreated++

                # Entitlement channels
                foreach ($ch in $def.channels) {
                    $chFilter   = "_entitlementid_value eq '$entId' and channel eq $($ch.type)"
                    $existingCh = Invoke-DataverseGet -EntitySet "entitlementchannels" `
                        -Filter $chFilter -Select "entitlementchannelid" -Top 1

                    if ($existingCh -and $existingCh.Count -gt 0) {
                        Write-Host "    Channel $($ch.name): exists" -ForegroundColor DarkGray
                        $entitlementResults.channelSkipped++
                    }
                    else {
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
                            $entitlementResults.channelCreated++
                        }
                        else {
                            Write-Host "    Channel $($ch.name): FAILED" -ForegroundColor Red
                        }
                    }
                }
            }
            else {
                Write-Warning "Failed to create entitlement for $($acct.name)"
            }
        }
    }

    # ----------------------------------------------------------
    # 3e. Activate entitlements (Draft → Active)
    # ----------------------------------------------------------
    Write-Host "`nActivating entitlements..." -ForegroundColor Yellow

    $activated = 0; $alreadyActive = 0; $activationFailed = 0

    foreach ($entry in $script:persistedIds.Entitlements.GetEnumerator()) {
        $entId   = $entry.Value
        $current = Invoke-DataverseGet -EntitySet "entitlements" `
            -Filter "entitlementid eq '$entId'" `
            -Select "entitlementid,statecode" -Top 1

        if ($current -and $current.Count -gt 0 -and $current[0].statecode -eq 1) {
            $alreadyActive++
            continue
        }

        $patchResult = Invoke-DataversePatch -EntitySet "entitlements" `
            -RecordId ([guid]$entId) `
            -Body @{ statecode = 1; statuscode = 1 }

        if ($patchResult) {
            $activated++
            Write-Host "  Activated: $($entry.Key)" -ForegroundColor Green
        }
        else {
            $activationFailed++
            Write-Host "  Activation failed: $($entry.Key)" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "  Entitlements section complete." -ForegroundColor Green
    Write-Host "  Templates: $($templateIds.Count)   Entitlements: $($entitlementResults.created)" -ForegroundColor Gray
    Write-Host "  Channels:  $($entitlementResults.channelCreated) created, $($entitlementResults.channelSkipped) existing" -ForegroundColor Gray
    Write-Host "  Activated: $activated new, $alreadyActive already active, $activationFailed failed" -ForegroundColor Gray
}

# ===========================================================
# ███████╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗ 4
#   Tier Logic — Update Case Priority by Account Tier
# ===========================================================
function Provision-TierLogic {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  SECTION 4 — Tier Logic (Case Priority Updates)" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan

    # Priority codes: 1=High, 2=Normal, 3=Low
    $tierPriorityMap = @{
        "NAV-B2B-PE"  = 1   # Platinum Expert → High
        "NAV-B2B-PL"  = 2   # Platinum        → Normal
        "NAV-B2B-GD"  = 2   # Gold            → Normal
        "NAV-B2B-SL"  = 3   # Silver          → Low
        "NAV-B2B-STD" = 3   # Standard        → Low
        "NAV-B2C"     = 3   # Consumer        → Low
    }

    # cr377_tierlevel option values
    $tierLevelMap = @{
        "NAV-B2B-PE"  = 192350000   # Tier 1 (Platinum Expert)
        "NAV-B2B-PL"  = 192350001   # Tier 2 (Platinum)
        "NAV-B2B-GD"  = 192350002   # Tier 3 (Gold)
        "NAV-B2B-SL"  = 192350003   # Tier 4 (Silver)
        "NAV-B2B-STD" = 192350003   # Tier 4 (Standard)
        "NAV-B2C"     = 192350003   # Tier 4 (Consumer)
    }

    # Query all Navico demo cases (incidents linked to NAV-* accounts)
    Write-Host "Querying Navico demo cases..." -ForegroundColor Yellow

    # Build a list of all NAV- account IDs first, then query cases by account
    $navicoCases = @()
    foreach ($prefix in @("NAV-B2B-PE", "NAV-B2B-PL", "NAV-B2B-GD", "NAV-B2B-SL", "NAV-B2B-STD", "NAV-B2C")) {
        $accts = Invoke-DataverseGet -EntitySet "accounts" `
            -Filter "startswith(accountnumber,'$prefix')" `
            -Select "accountid,accountnumber"

        if ($accts) {
            foreach ($acct in $accts) {
                $cases = Invoke-DataverseGet -EntitySet "incidents" `
                    -Filter "_customerid_value eq $($acct.accountid)" `
                    -Select "incidentid,title,prioritycode,cr377_tierlevel,_customerid_value"
                if ($cases) { $navicoCases += $cases }
            }
        }
    }

    if (-not $navicoCases -or $navicoCases.Count -eq 0) {
        Write-Host "  No Navico cases found to update." -ForegroundColor DarkYellow
        return
    }

    Write-Host "  Found $($navicoCases.Count) case(s) to evaluate." -ForegroundColor DarkGray

    $updated = 0; $skipped = 0; $failed = 0

    foreach ($case in $navicoCases) {
        # Look up the account's number to determine tier
        $acctId    = $case._customerid_value
        $acctRec   = Invoke-DataverseGet -EntitySet "accounts" `
            -Filter "accountid eq '$acctId'" `
            -Select "accountnumber" -Top 1

        if (-not $acctRec -or $acctRec.Count -eq 0) { $skipped++; continue }

        $acctNum  = $acctRec[0].accountnumber
        $priority = $null
        $matchedPrefix = $null

        foreach ($prefix in $tierPriorityMap.Keys | Sort-Object { -$_.Length }) {
            if ($acctNum -like "$prefix*") {
                $priority = $tierPriorityMap[$prefix]
                $matchedPrefix = $prefix
                break
            }
        }

        if ($null -eq $priority) { $skipped++; continue }

        $tierLevel = $tierLevelMap[$matchedPrefix]

        # Only patch if priority OR tierlevel differs
        if ($case.prioritycode -eq $priority -and $case.cr377_tierlevel -eq $tierLevel) {
            Write-Host "  UNCHANGED: [$($case.title)] → priority $priority / tier $tierLevel" -ForegroundColor DarkGray
            $skipped++
            continue
        }

        $patchResult = Invoke-DataversePatch -EntitySet "incidents" `
            -RecordId ([guid]$case.incidentid) `
            -Body @{ prioritycode = $priority; cr377_tierlevel = $tierLevel }

        if ($patchResult) {
            Write-Host "  UPDATED: [$($case.title)] → priority $priority / tier $tierLevel ($acctNum)" -ForegroundColor Green
            $updated++
            $script:summary.TierUpdatesApplied++
        }
        else {
            Write-Host "  FAILED: [$($case.title)]" -ForegroundColor Red
            $failed++
        }
    }

    Write-Host ""
    Write-Host "  Tier Logic complete. Updated: $updated  Unchanged: $skipped  Failed: $failed" -ForegroundColor Green
}

# ===========================================================
#   CLEANUP
# ===========================================================
function Invoke-Cleanup {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "  CLEANUP — Navico Extended Data" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Red

    $confirm = Read-Host "Type 'DELETE' to confirm cleanup of Navico extended data"
    if ($confirm -ne "DELETE") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        return
    }

    Write-Host "`nRemoving customer assets..." -ForegroundColor Red
    $demoData = Get-DemoData
    foreach ($acct in $demoData.serviceAccounts.accounts) {
        $acctId = Get-AccountId -AccountNumber $acct.accountNumber
        if (-not $acctId) { continue }
        $assets = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
            -Filter "_msdyn_account_value eq $acctId" `
            -Select "msdyn_customerassetid,msdyn_name"
        if ($assets) {
            foreach ($a in $assets) {
                Invoke-DataverseDelete -EntitySet "msdyn_customerassets" -Id ([guid]$a.msdyn_customerassetid)
                Write-Host "  Deleted asset: $($a.msdyn_name)" -ForegroundColor DarkRed
            }
        }
    }

    Write-Host "`nRemoving entitlements (prefix: 'Navico')..." -ForegroundColor Red
    $entitlements = Invoke-DataverseGet -EntitySet "entitlements" `
        -Filter "startswith(name,'Navico ')" `
        -Select "entitlementid,name"
    if ($entitlements) {
        foreach ($e in $entitlements) {
            try {
                Invoke-DataverseDelete -EntitySet "entitlements" -Id ([guid]$e.entitlementid)
                Write-Host "  Deleted: $($e.name)" -ForegroundColor DarkRed
            } catch { Write-Warning "  Could not delete: $($e.name)" }
        }
    }

    Write-Host "`nRemoving entitlement templates (prefix: 'Navico')..." -ForegroundColor Red
    $templates = Invoke-DataverseGet -EntitySet "entitlementtemplates" `
        -Filter "startswith(name,'Navico ')" `
        -Select "entitlementtemplateid,name"
    if ($templates) {
        foreach ($t in $templates) {
            try {
                Invoke-DataverseDelete -EntitySet "entitlementtemplates" -Id ([guid]$t.entitlementtemplateid)
                Write-Host "  Deleted template: $($t.name)" -ForegroundColor DarkRed
            } catch { Write-Warning "  Could not delete template: $($t.name)" }
        }
    }

    Write-Host "`nCleanup complete." -ForegroundColor Yellow
}

# ===========================================================
#   SUMMARY + PERSIST IDS
# ===========================================================
function Write-FinalSummary {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "  NAVICO EXTENDED PROVISIONING — COMPLETE" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "  Products created/verified : $($script:summary.ProductsCreated)" -ForegroundColor White
    Write-Host "  Assets created            : $($script:summary.AssetsCreated)" -ForegroundColor White
    Write-Host "  Assets skipped (existing) : $($script:summary.AssetsSkipped)" -ForegroundColor White
    Write-Host "  Entitlements created      : $($script:summary.EntitlementsCreated)" -ForegroundColor White
    Write-Host "  Tier updates applied      : $($script:summary.TierUpdatesApplied)" -ForegroundColor White
    Write-Host ("=" * 70) -ForegroundColor Green

    # Persist IDs
    $outputDir = Split-Path $OUTPUT_IDS_PATH
    if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }
    $script:persistedIds | ConvertTo-Json -Depth 5 | Out-File $OUTPUT_IDS_PATH -Encoding utf8
    Write-Host "`n  IDs saved to: $OUTPUT_IDS_PATH" -ForegroundColor DarkGray
}

# ===========================================================
#   ENTRY POINT
# ===========================================================
switch ($Action) {
    "All" {
        Connect-Dataverse
        Provision-PriceListAndProducts
        Provision-CustomerAssets
        Provision-Entitlements
        Provision-TierLogic
        Write-FinalSummary
    }
    { $_ -in "PriceList","Products" } {
        Connect-Dataverse
        Provision-PriceListAndProducts
        Write-FinalSummary
    }
    "CustomerAssets" {
        Connect-Dataverse
        Provision-CustomerAssets
        Write-FinalSummary
    }
    "Entitlements" {
        Connect-Dataverse
        Provision-Entitlements
        Write-FinalSummary
    }
    "TierLogic" {
        Connect-Dataverse
        Provision-TierLogic
        Write-FinalSummary
    }
    "BrandLogo" {
        Connect-Dataverse
        Provision-AssetBrandLogos
        Write-FinalSummary
    }
    "Cleanup" {
        Connect-Dataverse
        Invoke-Cleanup
    }
}
