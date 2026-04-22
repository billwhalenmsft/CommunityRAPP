<#
.SYNOPSIS
    Navico Marine Electronics — D365 Customer Service Competitive Demo Provisioning
.DESCRIPTION
    Creates Navico-specific demo data for D365 CS competitive bake-off vs. Salesforce Service Cloud.
    Focus: Omnichannel (Email, Chat, Voice), Intelligent Routing, Copilot Assist, RMA/Warranty Workflows.

    Provisions:
    - Brand & distributor accounts (B2B tiers + B2C consumer contacts)
    - Contacts (Jake Harrington, Christine Delacroix, Mike Torres + supporting cast)
    - Products (Simrad NSX, B&G Triton2, Lowrance HDS Live, C-MAP, Northstar)
    - Demo cases (seeded across all channels and brands)

.PARAMETER Action
    What to provision: All, Accounts, Contacts, Products, Cases, Cleanup

.EXAMPLE
    .\Provision-NavicoDemo.ps1 -Action All
    .\Provision-NavicoDemo.ps1 -Action Accounts
    .\Provision-NavicoDemo.ps1 -Action Cleanup
#>

[CmdletBinding()]
param(
    [ValidateSet("All", "Accounts", "Contacts", "Products", "Cases", "Cleanup")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Script is at customers/navico/d365/ - go up 3 levels to repo root
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

# Import Dataverse helper
$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) {
    Import-Module $helperPath -Force
} else {
    throw "DataverseHelper.psm1 not found at: $helperPath"
}

# Load configuration files
$demoDataPath  = Join-Path $scriptDir "config\demo-data.json"
$envConfigPath = Join-Path $scriptDir "config\environment.json"

if (-not (Test-Path $demoDataPath))  { throw "Demo data not found: $demoDataPath" }
if (-not (Test-Path $envConfigPath)) { throw "Environment config not found: $envConfigPath" }

$demoData  = Get-Content $demoDataPath  | ConvertFrom-Json
$envConfig = Get-Content $envConfigPath | ConvertFrom-Json

Write-Host ""
Write-Host ("=" * 65) -ForegroundColor Cyan
Write-Host "  Navico Marine Electronics — D365 CS Demo Provisioning" -ForegroundColor Cyan
Write-Host "  Environment : $($envConfig.environment.name)" -ForegroundColor DarkGray
Write-Host "  URL         : $($envConfig.environment.url)" -ForegroundColor DarkGray
Write-Host "  Action      : $Action" -ForegroundColor Yellow
Write-Host "  Brands      : Lowrance, Simrad, B&G, C-MAP, Northstar" -ForegroundColor DarkGray
Write-Host ("=" * 65) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

# Track created records for export
$createdRecords = @{
    accounts = @()
    contacts = @()
    products = @()
    cases    = @()
}

# ============================================================
# ACCOUNTS
# ============================================================
function Provision-Accounts {
    Write-Host "`n>>> Provisioning Accounts..." -ForegroundColor Green

    foreach ($account in $demoData.serviceAccounts.accounts) {
        Write-Host "  Creating: $($account.name) [$($account.tier)]" -ForegroundColor Gray

        $body = @{
            name              = $account.name
            accountnumber     = $account.accountNumber
            description       = "Tier: $($account.tier)`nType: $($account.type)`nRegion: $($account.region)`n`n$($account.description)"
            telephone1        = $account.phone
            address1_line1    = $account.address.line1
            address1_city     = $account.address.city
            address1_postalcode = $account.address.postalCode
            address1_country  = $account.address.country
            accountcategorycode = 1   # Customer
            customertypecode  = 3     # Customer
            industrycode      = 29    # Transportation, Communication, Electric, Gas and Sanitary Services (closest for marine)
        }

        if ($account.address.stateOrProvince) {
            $body.address1_stateorprovince = $account.address.stateOrProvince
        }

        $id = Find-OrCreate-Record `
            -EntitySet "accounts" `
            -Filter "accountnumber eq '$($account.accountNumber)'" `
            -IdField "accountid" `
            -Body $body `
            -DisplayName "$($account.name) [$($account.tier)]"

        $script:createdRecords.accounts += @{
            id            = $id
            name          = $account.name
            accountNumber = $account.accountNumber
            tier          = $account.tier
        }
    }

    Write-Host "  Accounts complete: $($demoData.serviceAccounts.accounts.Count) processed" -ForegroundColor Green
}

# ============================================================
# CONTACTS
# ============================================================
function Provision-Contacts {
    Write-Host "`n>>> Provisioning Contacts..." -ForegroundColor Green

    foreach ($contact in $demoData.contacts.contacts) {
        Write-Host "  Creating: $($contact.firstName) $($contact.lastName) @ $($contact.account)" -ForegroundColor Gray

        # Find parent account
        $parentAccountId = $null
        $parentAccount = $script:createdRecords.accounts | Where-Object { $_.name -eq $contact.account }
        if ($parentAccount) {
            $parentAccountId = $parentAccount.id
        } else {
            $escapedName = $contact.account -replace "'", "''"
            $existing = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$escapedName'" -Select "accountid" -Top 1
            if ($existing -and $existing.Count -gt 0) {
                $parentAccountId = $existing[0].accountid
            }
        }

        $body = @{
            firstname      = $contact.firstName
            lastname       = $contact.lastName
            jobtitle       = $contact.title
            telephone1     = $contact.phone
            mobilephone    = $contact.mobile
            emailaddress1  = $contact.email
            description    = $contact.demoRole
        }

        if ($parentAccountId) {
            $body["parentcustomerid_account@odata.bind"] = "/accounts($parentAccountId)"
        }

        $id = Find-OrCreate-Record `
            -EntitySet "contacts" `
            -Filter "emailaddress1 eq '$($contact.email)'" `
            -IdField "contactid" `
            -Body $body `
            -DisplayName "$($contact.firstName) $($contact.lastName)"

        $script:createdRecords.contacts += @{
            id      = $id
            name    = "$($contact.firstName) $($contact.lastName)"
            email   = $contact.email
            account = $contact.account
            phone   = $contact.phone
        }
    }

    Write-Host "  Contacts complete: $($demoData.contacts.contacts.Count) processed" -ForegroundColor Green
}

# ============================================================
# PRODUCTS — Marine Electronics
# ============================================================
function Provision-Products {
    Write-Host "`n>>> Provisioning Products (Marine Electronics)..." -ForegroundColor Green

    # Unit Group
    $ugId = Find-OrCreate-Record `
        -EntitySet "uomschedules" `
        -Filter "name eq 'Marine Electronics Units'" `
        -IdField "uomscheduleid" `
        -Body @{ name = "Marine Electronics Units"; baseuomname = "Each"; description = "Unit group for Navico marine electronics products" } `
        -DisplayName "Marine Electronics Units"

    $primaryUnit = Invoke-DataverseGet -EntitySet "uoms" -Filter "_uomscheduleid_value eq '$ugId' and isschedulebaseuom eq true" -Select "uomid,name" -Top 1
    $eachUnitId = if ($primaryUnit -and $primaryUnit.Count -gt 0) { $primaryUnit[0].uomid } else {
        Find-OrCreate-Record -EntitySet "uoms" -Filter "name eq 'Each' and _uomscheduleid_value eq '$ugId'" -IdField "uomid" `
            -Body @{ name = "Each"; "uomscheduleid@odata.bind" = "/uomschedules($ugId)"; quantity = 1 } -DisplayName "Each"
    }

    # Price List
    $priceListId = Find-OrCreate-Record `
        -EntitySet "pricelevels" `
        -Filter "name eq 'Navico Marine Electronics Price List'" `
        -IdField "pricelevelid" `
        -Body @{ name = "Navico Marine Electronics Price List"; description = "Standard dealer pricing for Navico brand products"; begindate = "2025-01-01"; enddate = "2028-12-31" } `
        -DisplayName "Navico Marine Electronics Price List"

    $products = @(
        # --- Simrad ---
        @{ name = "Simrad NSX 3007 Chartplotter"; code = "SIM-NSX-3007"; brand = "Simrad"; price = 1299.00; desc = "7-inch Simrad NSX chartplotter with Broadband Radar compatibility and SolarMAX HD display." },
        @{ name = "Simrad NSX 3009 Chartplotter"; code = "SIM-NSX-3009"; brand = "Simrad"; price = 1599.00; desc = "9-inch Simrad NSX chartplotter. Professional-grade for commercial and sport fishing vessels." },
        @{ name = "Simrad GO9 XSE Chartplotter/Fishfinder"; code = "SIM-GO9-XSE"; brand = "Simrad"; price = 699.00; desc = "9-inch combo chartplotter/fishfinder. Entry-level professional with StructureScan." },
        # --- B&G ---
        @{ name = "B&G Triton2 Instrument Display"; code = "BG-TRITON2"; brand = "B&G"; price = 349.00; desc = "B&G Triton2 sailing instrument display. Dedicated wind, speed, depth, and performance data." },
        @{ name = "B&G Zeus3S Chartplotter"; code = "BG-ZEUS3S"; brand = "B&G"; price = 1499.00; desc = "B&G Zeus3S sailing chartplotter with SailSteer, Wind Plot, and Race Timer." },
        # --- Lowrance ---
        @{ name = "Lowrance HDS-9 Live Fishfinder/Chartplotter"; code = "LWR-HDS9-LIVE"; brand = "Lowrance"; price = 999.00; desc = "Lowrance HDS-9 Live fish finder and chartplotter with Active Imaging sonar and C-MAP charting." },
        @{ name = "Lowrance HDS-12 Live Fishfinder/Chartplotter"; code = "LWR-HDS12-LIVE"; brand = "Lowrance"; price = 1299.00; desc = "Lowrance HDS-12 Live 12-inch combo unit. Premium recreational fishing and navigation." },
        @{ name = "Lowrance Elite FS 9 Fishfinder"; code = "LWR-ELT-FS9"; brand = "Lowrance"; price = 499.00; desc = "Lowrance Elite FS 9 entry-level fish finder with Active Imaging 3-in-1 transducer." },
        # --- C-MAP ---
        @{ name = "C-MAP DISCOVER Chart Card"; code = "CMAP-DISC"; brand = "C-MAP"; price = 149.00; desc = "C-MAP DISCOVER inland and coastal chart card. Compatible with Lowrance, Simrad, B&G." },
        @{ name = "C-MAP MAX-N+ Regional Chart Card"; code = "CMAP-MAXN"; brand = "C-MAP"; price = 249.00; desc = "C-MAP MAX-N+ premium offshore charting with 3D views and port plans." },
        # --- Northstar ---
        @{ name = "Northstar NS5500 GPS Navigator"; code = "NS-5500"; brand = "Northstar"; price = 799.00; desc = "Northstar NS5500 marine GPS navigator. Fixed mount with dedicated waypoint and route management." }
    )

    foreach ($prod in $products) {
        Write-Host "  Creating product: $($prod.name)" -ForegroundColor Gray

        $prodId = Find-OrCreate-Record `
            -EntitySet "products" `
            -Filter "productnumber eq '$($prod.code)'" `
            -IdField "productid" `
            -Body @{
                name              = $prod.name
                productnumber     = $prod.code
                description       = "[$($prod.brand)] $($prod.desc)"
                price             = $prod.price
                standardcost      = [math]::Round($prod.price * 0.6, 2)
                currentcost       = [math]::Round($prod.price * 0.6, 2)
                quantitydecimal   = 0
                producttypecode   = 1   # Sales Inventory
                "defaultuomscheduleid@odata.bind" = "/uomschedules($ugId)"
                "defaultuomid@odata.bind"         = "/uoms($eachUnitId)"
                "pricelevelid@odata.bind"          = "/pricelevels($priceListId)"
            } `
            -DisplayName $prod.name

        $script:createdRecords.products += @{ id = $prodId; name = $prod.name; code = $prod.code; brand = $prod.brand }
    }

    Write-Host "  Products complete: $($products.Count) processed" -ForegroundColor Green
}

# ============================================================
# CASES — Pre-seeded demo cases
# ============================================================
function Provision-Cases {
    Write-Host "`n>>> Provisioning Demo Cases..." -ForegroundColor Green

    $priorityMap = @{ "Critical" = 1; "High" = 2; "Normal" = 3; "Low" = 4 }
    $originMap   = @{ "Phone" = 1; "Email" = 2; "Web" = 3; "Chat" = 2483; "Portal" = 3986 }

    foreach ($case in $demoData.demoCases.cases) {
        Write-Host "  Creating case: $($case.title)" -ForegroundColor Gray

        # Find account
        $accountId = $null
        if ($case.account) {
            $acct = $script:createdRecords.accounts | Where-Object { $_.name -eq $case.account }
            if ($acct) {
                $accountId = $acct.id
            } else {
                $escapedName = $case.account -replace "'", "''"
                $found = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$escapedName'" -Select "accountid" -Top 1
                if ($found -and $found.Count -gt 0) { $accountId = $found[0].accountid }
            }
        }

        # Find contact
        $contactId = $null
        if ($case.contact) {
            $ctct = $script:createdRecords.contacts | Where-Object { $_.name -like "*$($case.contact)*" }
            if ($ctct) { $contactId = $ctct.id }
        }

        $originCode = if ($originMap.ContainsKey($case.channel)) { $originMap[$case.channel] } else { 3 }

        $body = @{
            title              = $case.title
            description        = "$($case.description)`n`nBrand: $($case.brand)`nSerial: $($case.serialNumber)`nDemo Use: $($case.demoUse)"
            prioritycode       = $priorityMap[$case.priority]
            caseorigincode     = $originCode
        }

        # Set serial number field so JS loader can pass it to Service Toolkit
        if ($case.serialNumber) { $body["productserialnumber"] = $case.serialNumber }

        # Link product record if SKU is provided
        if ($case.productSku) {
            $escapedSku = $case.productSku -replace "'", "''"
            $prod = Invoke-DataverseGet -EntitySet "products" `
                -Filter "productnumber eq '$escapedSku'" `
                -Select "productid" -Top 1
            if ($prod -and $prod.Count -gt 0) {
                $body["productid@odata.bind"] = "/products($($prod[0].productid))"
            }
        }

        if ($accountId) { $body["customerid_account@odata.bind"] = "/accounts($accountId)" }
        if ($contactId) { $body["primarycontactid@odata.bind"]   = "/contacts($contactId)" }

        $escapedTitle = $case.title -replace "'", "''"
        $id = Find-OrCreate-Record `
            -EntitySet "incidents" `
            -Filter "title eq '$escapedTitle'" `
            -IdField "incidentid" `
            -Body $body `
            -DisplayName $case.title

        $script:createdRecords.cases += @{ id = $id; title = $case.title; account = $case.account; priority = $case.priority }

        # Create timeline activities for this case
        if ($case.activities -and $case.activities.Count -gt 0) {
            $baseTime = (Get-Date).ToUniversalTime()
            foreach ($activity in $case.activities) {
                $actTime    = $baseTime.AddHours($activity.createdRelativeHours)
                $actTimeStr = $actTime.ToString("yyyy-MM-ddTHH:mm:ssZ")

                switch ($activity.type) {
                    "note" {
                        try {
                            $noteBody = @{
                                subject   = $activity.subject
                                notetext  = $activity.description
                                "objectid_incident@odata.bind" = "/incidents($id)"
                            }
                            Find-OrCreate-Record -EntitySet "annotations" `
                                -Filter "subject eq '$($activity.subject -replace "'","''")' and _objectid_value eq '$id'" `
                                -IdField "annotationid" -Body $noteBody -DisplayName $activity.subject | Out-Null
                            Write-Host "    Note: $($activity.subject)" -ForegroundColor DarkGray
                        } catch { Write-Warning "    Note skipped: $($_.Exception.Message)" }
                    }
                    "email" {
                        try {
                            $isInbound = $activity.direction -eq "Inbound"
                            $emailBody = @{
                                subject       = $activity.subject
                                description   = $activity.description
                                directioncode = -not $isInbound
                                actualend     = $actTimeStr
                                "regardingobjectid_incident@odata.bind" = "/incidents($id)"
                            }
                            Find-OrCreate-Record -EntitySet "emails" `
                                -Filter "subject eq '$($activity.subject -replace "'","''")' and _regardingobjectid_value eq '$id'" `
                                -IdField "activityid" -Body $emailBody -DisplayName $activity.subject | Out-Null
                            Write-Host "    Email: $($activity.subject)" -ForegroundColor DarkGray
                        } catch { Write-Warning "    Email skipped: $($_.Exception.Message)" }
                    }
                    "phonecall" {
                        try {
                            $phoneBody = @{
                                subject       = $activity.subject
                                description   = $activity.description
                                directioncode = ($activity.direction -ne "Inbound")
                                actualend     = $actTimeStr
                                "regardingobjectid_incident@odata.bind" = "/incidents($id)"
                            }
                            Find-OrCreate-Record -EntitySet "phonecalls" `
                                -Filter "subject eq '$($activity.subject -replace "'","''")' and _regardingobjectid_value eq '$id'" `
                                -IdField "activityid" -Body $phoneBody -DisplayName $activity.subject | Out-Null
                            Write-Host "    Phone call: $($activity.subject)" -ForegroundColor DarkGray
                        } catch { Write-Warning "    Phone call skipped: $($_.Exception.Message)" }
                    }
                }
            }
        }
    }

    Write-Host "  Cases complete: $($demoData.demoCases.cases.Count) processed" -ForegroundColor Green
}

# ============================================================
# CLEANUP
# ============================================================
function Invoke-Cleanup {
    Write-Host "`n>>> WARNING: This will delete all Navico demo data!" -ForegroundColor Red
    $confirm = Read-Host "Type 'DELETE' to confirm"
    if ($confirm -ne "DELETE") { Write-Host "Cleanup cancelled." -ForegroundColor Yellow; return }

    foreach ($case in $demoData.demoCases.cases) {
        $esc = $case.title -replace "'", "''"
        $r = Invoke-DataverseGet -EntitySet "incidents" -Filter "title eq '$esc'" -Select "incidentid" -Top 1
        if ($r -and $r.Count -gt 0) {
            Invoke-DataverseDelete -EntitySet "incidents" -Id $r[0].incidentid
            Write-Host "  Deleted case: $($case.title)" -ForegroundColor DarkRed
        }
    }
    foreach ($contact in $demoData.contacts.contacts) {
        $r = Invoke-DataverseGet -EntitySet "contacts" -Filter "emailaddress1 eq '$($contact.email)'" -Select "contactid" -Top 1
        if ($r -and $r.Count -gt 0) {
            Invoke-DataverseDelete -EntitySet "contacts" -Id $r[0].contactid
            Write-Host "  Deleted contact: $($contact.firstName) $($contact.lastName)" -ForegroundColor DarkRed
        }
    }
    foreach ($account in $demoData.serviceAccounts.accounts) {
        $r = Invoke-DataverseGet -EntitySet "accounts" -Filter "accountnumber eq '$($account.accountNumber)'" -Select "accountid" -Top 1
        if ($r -and $r.Count -gt 0) {
            Invoke-DataverseDelete -EntitySet "accounts" -Id $r[0].accountid
            Write-Host "  Deleted account: $($account.name)" -ForegroundColor DarkRed
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
}

# ============================================================
# MAIN
# ============================================================
switch ($Action) {
    "All"      { Provision-Accounts; Provision-Contacts; Provision-Products; Provision-Cases }
    "Accounts" { Provision-Accounts }
    "Contacts" { Provision-Contacts }
    "Products" { Provision-Products }
    "Cases"    { Provision-Cases }
    "Cleanup"  { Invoke-Cleanup }
}

# Export record IDs
$exportPath = Join-Path $scriptDir "data\navico-demo-ids.json"
New-Item -ItemType Directory -Path (Split-Path $exportPath -Parent) -Force | Out-Null
$createdRecords | ConvertTo-Json -Depth 5 | Set-Content $exportPath -Force

Write-Host ""
Write-Host ("=" * 65) -ForegroundColor Green
Write-Host "  Navico Demo Provisioning Complete!" -ForegroundColor Green
Write-Host "  Accounts : $($createdRecords.accounts.Count)" -ForegroundColor Gray
Write-Host "  Contacts : $($createdRecords.contacts.Count)" -ForegroundColor Gray
Write-Host "  Products : $($createdRecords.products.Count)" -ForegroundColor Gray
Write-Host "  Cases    : $($createdRecords.cases.Count)" -ForegroundColor Gray
Write-Host "  IDs saved: $exportPath" -ForegroundColor DarkGray
Write-Host ("=" * 65) -ForegroundColor Green
Write-Host ""
Write-Host "  Next: Run .\Provision-NavicoHeroCases.ps1 -Action All" -ForegroundColor Cyan
Write-Host ""
