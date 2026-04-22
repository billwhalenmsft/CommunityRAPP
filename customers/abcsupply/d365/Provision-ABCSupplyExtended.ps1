<#
.SYNOPSIS
    ABC Supply — Extended Demo Data: Price Lists, Products, Customer Assets, Entitlements

.PARAMETER Action
    PriceList | Products | CustomerAssets | Entitlements | TierLogic | All

.EXAMPLE
    .\Provision-ABCSupplyExtended.ps1 -Action All
    .\Provision-ABCSupplyExtended.ps1 -Action Products
#>

[CmdletBinding()]
param(
    [ValidateSet("PriceList","Products","CustomerAssets","Entitlements","TierLogic","All")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"

$OrgUrl  = "https://orgecbce8ef.crm.dynamics.com"
$ApiBase = "$OrgUrl/api/data/v9.2"
$DataDir = "$PSScriptRoot\..\..\data"

$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null)
if (-not $token) { Write-Error "Run 'az login' first."; exit 1 }

$headers = @{
    "Authorization"   = "Bearer $token"
    "OData-MaxVersion" = "4.0"
    "OData-Version"   = "4.0"
    "Content-Type"    = "application/json"
    "Prefer"          = "return=representation"
}

function Invoke-D365 {
    param([string]$Method, [string]$Url, [hashtable]$Body = $null)
    $params = @{ Method=$Method; Uri=$Url; Headers=$headers; TimeoutSec=30 }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    return Invoke-RestMethod @params
}

function Find-Record {
    param([string]$Entity, [string]$FilterField, [string]$FilterValue, [string]$SelectFields = "")
    $enc = [System.Web.HttpUtility]::UrlEncode($FilterValue)
    $url = "$ApiBase/$Entity`?`$filter=$FilterField eq '$enc'"
    if ($SelectFields) { $url += "&`$select=$SelectFields" }
    $resp = Invoke-D365 -Method GET -Url $url
    return $resp.value | Select-Object -First 1
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Cyan
Write-Host "  ABC Supply — Extended Demo Data" -ForegroundColor Cyan
Write-Host "  Action: $Action" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Cyan

# ─────────────────────────────────────────────────────────────────
# PRICE LIST
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","PriceList") {
    Write-Host "`n  ── Price List ──" -ForegroundColor Yellow

    $existing = Find-Record -Entity "pricelists" -FilterField "name" -FilterValue "ABC Supply — Standard Price List" -SelectFields "pricelevelid,name"
    if ($existing) {
        Write-Host "  [SKIP] Price list exists" -ForegroundColor DarkGray
        $priceListId = $existing.pricelevelid
    } else {
        $body = @{
            name              = "ABC Supply — Standard Price List"
            transactioncurrencyid = $null
            description       = "Standard pricing for ABC Supply Savage Branch — Windows, Doors, Parts, and Service"
            begindate         = "2026-01-01"
            enddate           = "2026-12-31"
        }
        # Get USD currency
        $usd = (Invoke-D365 -Method GET -Url "$ApiBase/transactioncurrencies?`$filter=isocurrencycode eq 'USD'&`$select=transactioncurrencyid").value | Select-Object -First 1
        if ($usd) { $body["transactioncurrencyid@odata.bind"] = "/transactioncurrencies($($usd.transactioncurrencyid))" }
        $resp = Invoke-D365 -Method POST -Url "$ApiBase/pricelists" -Body $body
        Write-Host "  [CREATE] Price List → $($resp.pricelevelid)" -ForegroundColor Green
        $priceListId = $resp.pricelevelid
    }
    $priceListId | Set-Content "$DataDir\pricelist_id.txt"
}

# ─────────────────────────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Products") {
    Write-Host "`n  ── Products ──" -ForegroundColor Yellow

    $products = @(
        @{ name="Window — Casement Standard";      number="WIN-CAS-STD";    price=485.00  },
        @{ name="Window — Double-Hung Standard";   number="WIN-DH-STD";     price=420.00  },
        @{ name="Window — Sliding Standard";       number="WIN-SLD-STD";    price=395.00  },
        @{ name="Patio Door — Sliding";            number="DOOR-PAT-SLD";   price=1250.00 },
        @{ name="Entry Door — Standard";           number="DOOR-ENT-STD";   price=890.00  },
        @{ name="Screen — Window Standard";        number="SCR-WIN-STD";    price=68.00   },
        @{ name="Screen — Door Standard";          number="SCR-DOOR-STD";   price=145.00  },
        @{ name="Seal / Weatherstrip Kit";         number="PART-SEAL-KIT";  price=42.00   },
        @{ name="Window Operator Mechanism";       number="PART-OPR-MEC";   price=89.00   },
        @{ name="Balance Replacement Kit";         number="PART-BAL-KIT";   price=55.00   },
        @{ name="Service Visit — Assessment";      number="SVC-ASSESS";     price=125.00  },
        @{ name="Service Visit — Window Repair";   number="SVC-WIN-RPR";    price=185.00  },
        @{ name="Service Visit — Measurement";     number="SVC-MEASURE";    price=75.00   },
        @{ name="Drive Time — Per Hour";           number="SVC-DRIVE-HR";   price=65.00   }
    )

    # Get default unit group
    $unitGroup = (Invoke-D365 -Method GET -Url "$ApiBase/uomschedules?`$select=uomscheduleid,name&`$top=1").value | Select-Object -First 1
    $unit      = if ($unitGroup) { (Invoke-D365 -Method GET -Url "$ApiBase/uoms?`$filter=_uomscheduleid_value eq '$($unitGroup.uomscheduleid)'&`$select=uomid,name&`$top=1").value | Select-Object -First 1 } else { $null }

    $priceListId = Get-Content "$DataDir\pricelist_id.txt" -ErrorAction SilentlyContinue
    $productIds = @{}

    foreach ($p in $products) {
        $existing = Find-Record -Entity "products" -FilterField "productnumber" -FilterValue $p.number -SelectFields "productid,name"
        if ($existing) {
            Write-Host "  [SKIP] Product exists: $($p.name)" -ForegroundColor DarkGray
            $productIds[$p.number] = $existing.productid
            continue
        }
        $body = @{ name=$p.name; productnumber=$p.number; price=$p.price; statecode=0 }
        if ($unit) {
            $body["defaultuomid@odata.bind"] = "/uoms($($unit.uomid))"
            $body["defaultuomscheduleid@odata.bind"] = "/uomschedules($($unitGroup.uomscheduleid))"
        }
        $resp = Invoke-D365 -Method POST -Url "$ApiBase/products" -Body $body
        Write-Host "  [CREATE] Product: $($p.name) → $($resp.productid)" -ForegroundColor Green
        $productIds[$p.number] = $resp.productid

        # Publish product
        try {
            Invoke-D365 -Method POST -Url "$ApiBase/PublishProductHierarchy" -Body @{ Target = @{ "@odata.type" = "Microsoft.Dynamics.CRM.product"; productid = $resp.productid } } | Out-Null
        } catch { Write-Warning "  Could not auto-publish $($p.name)" }
    }

    $productIds | ConvertTo-Json | Set-Content "$DataDir\product_ids.json"
    Write-Host "  Product IDs saved → $DataDir\product_ids.json" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────
# CUSTOMER ASSETS
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","CustomerAssets") {
    Write-Host "`n  ── Customer Assets (Installed Product Serials) ──" -ForegroundColor Yellow

    $accountIds = @{}
    $loadedA = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedA) { $loadedA.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }

    $productIds = @{}
    $loadedP = Get-Content "$DataDir\product_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedP) { $loadedP.PSObject.Properties | ForEach-Object { $productIds[$_.Name] = $_.Value } }

    $assets = @(
        @{ name="Andersen 400 Casement — WO-2026-001"; serial="AND-CAS-2024-SAV-0042"; account="Andersen Exteriors Savage"; product="WIN-CAS-STD"; installDate="2024-11-15" },
        @{ name="Pella Impervia Slider — WO-2026-002"; serial="PEL-SLD-2023-BRN-0117"; account="Pella Pro Contractors MN";  product="WIN-SLD-STD"; installDate="2023-09-22" },
        @{ name="Andersen Casement — Balance Issue";   serial="AND-CAS-2023-SAV-0031"; account="Andersen Exteriors Savage"; product="WIN-CAS-STD"; installDate="2023-06-10" },
        @{ name="Prairie Windows Screen Project";      serial="SCR-WIN-2025-PWD-0012"; account="Prairie Windows & Doors";   product="SCR-WIN-STD"; installDate="2025-07-14" }
    )

    $assetIds = @{}
    foreach ($a in $assets) {
        $existing = Find-Record -Entity "msdyn_customerassets" -FilterField "msdyn_serialnumber" -FilterValue $a.serial -SelectFields "msdyn_customerassetid,msdyn_name"
        if ($existing) {
            Write-Host "  [SKIP] Asset exists: $($a.serial)" -ForegroundColor DarkGray
            $assetIds[$a.serial] = $existing.msdyn_customerassetid
            continue
        }
        $body = @{ msdyn_name=$a.name; msdyn_serialnumber=$a.serial }
        $acctId = $accountIds[$a.account]
        $prodId = $productIds[$a.product]
        if ($acctId) { $body["msdyn_account@odata.bind"]  = "/accounts($acctId)" }
        if ($prodId) { $body["msdyn_product@odata.bind"]  = "/products($prodId)" }
        try {
            $resp = Invoke-D365 -Method POST -Url "$ApiBase/msdyn_customerassets" -Body $body
            Write-Host "  [CREATE] Asset: $($a.name) → $($resp.msdyn_customerassetid)" -ForegroundColor Green
            $assetIds[$a.serial] = $resp.msdyn_customerassetid
        } catch { Write-Warning "  Asset create failed for $($a.name): $_" }
    }
    $assetIds | ConvertTo-Json | Set-Content "$DataDir\asset_ids.json"
}

# ─────────────────────────────────────────────────────────────────
# ENTITLEMENTS
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Entitlements") {
    Write-Host "`n  ── Entitlements (Tier SLAs) ──" -ForegroundColor Yellow

    $accountIds = @{}
    $loadedA = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedA) { $loadedA.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }

    $entitlements = @(
        @{ name="Andersen Exteriors — Premier Contractor SLA"; account="Andersen Exteriors Savage"; totalTerms=200; allotmentType=2; startDate="2026-01-01"; endDate="2026-12-31" },
        @{ name="Pella Pro Contractors — Active SLA";          account="Pella Pro Contractors MN";  totalTerms=100; allotmentType=2; startDate="2026-01-01"; endDate="2026-12-31" },
        @{ name="Prairie Windows — Standard SLA";              account="Prairie Windows & Doors";   totalTerms=50;  allotmentType=2; startDate="2026-01-01"; endDate="2026-12-31" }
    )

    $entIds = @{}
    foreach ($e in $entitlements) {
        $existing = Find-Record -Entity "entitlements" -FilterField "name" -FilterValue $e.name -SelectFields "entitlementid,name"
        if ($existing) {
            Write-Host "  [SKIP] Entitlement exists: $($e.name)" -ForegroundColor DarkGray
            $entIds[$e.name] = $existing.entitlementid
            continue
        }
        $body = @{
            name             = $e.name
            totalterms       = $e.totalTerms
            allotmenttype    = $e.allotmentType
            startdate        = $e.startDate
            enddate          = $e.endDate
            statecode        = 0
        }
        $acctId = $accountIds[$e.account]
        if ($acctId) { $body["customerid_account@odata.bind"] = "/accounts($acctId)" }
        try {
            $resp = Invoke-D365 -Method POST -Url "$ApiBase/entitlements" -Body $body
            Write-Host "  [CREATE] Entitlement: $($e.name)" -ForegroundColor Green
            $entIds[$e.name] = $resp.entitlementid
        } catch { Write-Warning "  Entitlement create failed: $($e.name) — $_" }
    }
    $entIds | ConvertTo-Json | Set-Content "$DataDir\entitlement_ids.json"
}

# ─────────────────────────────────────────────────────────────────
# TIER LOGIC — Patch case priority from account tier
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","TierLogic") {
    Write-Host "`n  ── Tier Logic (patch case priority) ──" -ForegroundColor Yellow

    $accountIds = @{}
    $loadedA = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedA) { $loadedA.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }

    $tierPriority = @{
        "Andersen Exteriors Savage" = 1
        "Pella Pro Contractors MN"  = 2
        "Prairie Windows & Doors"   = 3
        "Bergstrom Home Services"   = 3
    }

    foreach ($accountName in $tierPriority.Keys) {
        $acctId = $accountIds[$accountName]
        if (-not $acctId) { continue }

        $cases = (Invoke-D365 -Method GET -Url "$ApiBase/incidents?`$filter=_customerid_value eq '$acctId' and statecode eq 0&`$select=incidentid,title,prioritycode").value
        foreach ($case in $cases) {
            $targetPriority = $tierPriority[$accountName]
            if ($case.prioritycode -ne $targetPriority) {
                Invoke-D365 -Method PATCH -Url "$ApiBase/incidents($($case.incidentid))" -Body @{ prioritycode = $targetPriority } | Out-Null
                Write-Host "  [PATCH] Priority for '$($case.title.Substring(0,[Math]::Min(40,$case.title.Length)))...' → $targetPriority" -ForegroundColor DarkGray
            }
        }
    }
    Write-Host "  Tier logic applied." -ForegroundColor Green
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  ABC Supply Extended Provisioning Complete" -ForegroundColor Green
Write-Host ("═" * 60) -ForegroundColor Green
