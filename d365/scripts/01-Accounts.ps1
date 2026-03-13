<#
.SYNOPSIS
    Step 01 - Create Accounts for Zurn Elkay Demo
.DESCRIPTION
    Creates Zurn and Elkay as two equal, peer-level accounts (no parent/child).
    Creates distributor customer accounts across all 4 tiers.
    Creates a small set of consumer/end-user accounts for less-common scenarios.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "01" "Create Accounts"
Connect-Dataverse

# ============================================================
# Load config
# ============================================================
$config = Get-Content "$scriptDir\..\config\environment.json" | ConvertFrom-Json

# ============================================================
# 1. Manufacturer Accounts - Zurn and Elkay (equals)
# ============================================================
Write-Host "`nCreating manufacturer accounts..." -ForegroundColor Yellow

$manufacturers = @(
    @{
        name               = "Zurn Industries"
        description        = "Zurn Industries, LLC - Commercial plumbing products, flush valves, faucets, drainage, backflow prevention (Wilkins brand)."
        telephone1         = "(855) 663-9876"
        websiteurl         = "https://www.zurn.com"
        address1_city      = "Milwaukee"
        address1_stateorprovince = "WI"
        address1_postalcode = "53202"
        address1_line1     = "511 W Freshwater Way"
        address1_country   = "US"
        accountcategorycode = 2  # Standard
        customertypecode   = 10  # Supplier
        industrycode       = 12  # Durable Manufacturing
    },
    @{
        name               = "Elkay Manufacturing"
        description        = "Elkay Manufacturing Company - Stainless steel sinks, drinking fountains & bottle fillers, water coolers, cabinetry."
        telephone1         = "(630) 572-3192"
        websiteurl         = "https://www.elkay.com"
        address1_city      = "Downers Grove"
        address1_stateorprovince = "IL"
        address1_postalcode = "60515"
        address1_line1     = "2222 Camden Court"
        address1_country   = "US"
        accountcategorycode = 2  # Standard
        customertypecode   = 10  # Supplier
        industrycode       = 12  # Durable Manufacturing
    }
)

$mfgIds = @{}
foreach ($mfg in $manufacturers) {
    $id = Find-OrCreate-Record `
        -EntitySet "accounts" `
        -Filter "name eq '$($mfg.name)'" `
        -IdField "accountid" `
        -Body $mfg `
        -DisplayName $mfg.name
    $mfgIds[$mfg.name] = $id
}

# ============================================================
# 2. Distributor Accounts (primary customer type) - 4 tiers
# ============================================================
Write-Host "`nCreating distributor accounts..." -ForegroundColor Yellow

$distributors = @(
    # --- Tier 1 - Strategic Distributors ---
    @{ name = "Ferguson Enterprises"; tier = 1; city = "Newport News"; state = "VA"; zip = "23602"; phone = "(757) 874-7795"; web = "https://www.ferguson.com"; desc = "Largest US plumbing distributor. Major Zurn and Elkay channel partner." },
    @{ name = "Hajoca Corporation"; tier = 1; city = "Ardmore"; state = "PA"; zip = "19003"; phone = "(610) 649-3600"; web = "https://www.hajoca.com"; desc = "Privately held wholesale distributor - plumbing, heating, industrial." },
    @{ name = "Winsupply Inc."; tier = 1; city = "Dayton"; state = "OH"; zip = "45402"; phone = "(937) 222-3071"; web = "https://www.winsupply.com"; desc = "Network of local distributors - plumbing, HVAC, waterworks." },

    # --- Tier 2 - Key Distributors ---
    @{ name = "HD Supply"; tier = 2; city = "Atlanta"; state = "GA"; zip = "30339"; phone = "(770) 852-9000"; web = "https://www.hdsupply.com"; desc = "National MRO and waterworks distributor." },
    @{ name = "Wolseley Industrial Group"; tier = 2; city = "Burlington"; state = "ON"; zip = "L7L 5Z9"; phone = "(905) 335-2410"; web = "https://www.wolseleyinc.ca"; desc = "Industrial PVF and plumbing distributor (Canada and US)." },
    @{ name = "Consolidated Supply Co."; tier = 2; city = "Portland"; state = "OR"; zip = "97232"; phone = "(503) 234-4181"; web = "https://www.consolidatedsupply.com"; desc = "Pacific Northwest plumbing and waterworks distributor." },

    # --- Tier 3 - Standard Distributors ---
    @{ name = "Pacific Plumbing Supply"; tier = 3; city = "Seattle"; state = "WA"; zip = "98108"; phone = "(206) 762-6050"; web = "https://www.pacificps.com"; desc = "Regional plumbing supply house - Pacific Northwest." },
    @{ name = "Midwest Pipe & Supply"; tier = 3; city = "Kansas City"; state = "MO"; zip = "64108"; phone = "(816) 471-4200"; web = ""; desc = "Regional distributor servicing Midwest plumbing contractors." },
    @{ name = "Southern Pipe & Supply"; tier = 3; city = "Meridian"; state = "MS"; zip = "39301"; phone = "(601) 693-4491"; web = "https://www.southernpipe.com"; desc = "Full-line plumbing, HVAC, and waterworks distributor - Southeastern US." },
    @{ name = "Gateway Supply Company"; tier = 3; city = "Columbia"; state = "SC"; zip = "29201"; phone = "(803) 779-3200"; web = "https://www.gatewaysupply.com"; desc = "Plumbing, HVAC, and appliance distributor - Southeast." },

    # --- Tier 4 - Basic / Small Distributors ---
    @{ name = "ABC Plumbing Wholesale"; tier = 4; city = "Denver"; state = "CO"; zip = "80202"; phone = "(303) 555-0101"; web = ""; desc = "Small local plumbing wholesaler. Occasional Zurn orders." },
    @{ name = "Metro Building Supply"; tier = 4; city = "Phoenix"; state = "AZ"; zip = "85003"; phone = "(602) 555-0202"; web = ""; desc = "General building supply. Minor plumbing fixture volume." },
    @{ name = "Lakeside Plumbing Parts"; tier = 4; city = "Cleveland"; state = "OH"; zip = "44114"; phone = "(216) 555-0303"; web = ""; desc = "Small regional parts distributor." }
)

$distIds = @{}
foreach ($dist in $distributors) {
    $body = @{
        name                     = $dist.name
        description              = "[Tier $($dist.tier)] $($dist.desc)"
        telephone1               = $dist.phone
        websiteurl               = $dist.web
        address1_city            = $dist.city
        address1_stateorprovince = $dist.state
        address1_postalcode      = $dist.zip
        address1_country         = "US"
        accountcategorycode      = 1  # Customer
        customertypecode         = 3  # Customer
        industrycode             = 10 # Distributors, Dispatchers and Processors
        accountnumber            = "TIER-$($dist.tier)"
    }

    $id = Find-OrCreate-Record `
        -EntitySet "accounts" `
        -Filter "name eq '$($dist.name)'" `
        -IdField "accountid" `
        -Body $body `
        -DisplayName "$($dist.name) [Tier $($dist.tier)]"
    $distIds[$dist.name] = $id
}

# ============================================================
# 3. End-User / Consumer Accounts (less common, but does happen)
# ============================================================
Write-Host "`nCreating end-user accounts..." -ForegroundColor Yellow

$endUsers = @(
    @{ name = "Greenfield School District";    type = "School District"; city = "Greenfield"; state = "WI"; phone = "(414) 555-0401" },
    @{ name = "City of Mesa Water Dept";       type = "Municipality";    city = "Mesa";       state = "AZ"; phone = "(480) 555-0501" },
    @{ name = "Marriott Downtown Milwaukee";   type = "Commercial";      city = "Milwaukee";  state = "WI"; phone = "(414) 555-0601" },
    @{ name = "Johnson Residence";             type = "Homeowner";       city = "Madison";    state = "WI"; phone = "(608) 555-0701" }
)

$euIds = @{}
foreach ($eu in $endUsers) {
    $body = @{
        name                     = $eu.name
        description              = "$($eu.type) - end-user requesting technical support or product information."
        telephone1               = $eu.phone
        address1_city            = $eu.city
        address1_stateorprovince = $eu.state
        address1_country         = "US"
        accountcategorycode      = 1  # Preferred Customer
        customertypecode         = 3  # Customer
    }

    $id = Find-OrCreate-Record `
        -EntitySet "accounts" `
        -Filter "name eq '$($eu.name)'" `
        -IdField "accountid" `
        -Body $body `
        -DisplayName "$($eu.name) [$($eu.type)]"
    $euIds[$eu.name] = $id
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Accounts Created Successfully" -ForegroundColor Green
Write-Host " Manufacturers : $($mfgIds.Count)" -ForegroundColor White
Write-Host " Distributors  : $($distIds.Count)" -ForegroundColor White
Write-Host " End-Users     : $($euIds.Count)" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

# Export IDs for downstream scripts
$allAccountIds = @{
    Manufacturers = $mfgIds
    Distributors  = $distIds
    EndUsers      = $euIds
}
$allAccountIds | ConvertTo-Json -Depth 3 | Out-File "$scriptDir\..\data\account-ids.json" -Encoding utf8
Write-Host "Account IDs saved to data\account-ids.json" -ForegroundColor DarkGray
