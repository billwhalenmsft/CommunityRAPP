<#
.SYNOPSIS
    Step 17 - Hero Account Enrichment + Phone Call Scenario
.DESCRIPTION
    Builds out the "hero record" for the live demo phone call scenario:
      1. Enriches Ferguson Enterprises with additional contacts (a third contact
         who will call in), address fields, revenue, employee count
      2. Creates Sales Orders with line items tied to Ferguson (simulates FNO data)
      3. Creates a pre-staged "active" case with timeline notes (shows case history
         during screen pop)
      4. Creates phone call activity records (prior calls for context)
      5. Creates the NEW inbound case that the live call will create
      6. Outputs the demo call script and IDs
.NOTES
    Hero Account: Ferguson Enterprises (Tier 1)
    Hero Contact: Tom Harrison (Plumbing Category Manager)
    Second Contact: Rachel Chen (Purchasing Director)
    NEW Contact: Mike Reynolds (Field Operations Manager) - the caller
    Run with: .\17-PhoneScenario.ps1
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Connect-Dataverse

# ============================================================
# IDs from prior scripts
# ============================================================
$accountIds  = Get-Content "$scriptDir\..\data\account-ids.json" | ConvertFrom-Json
$productIds  = Get-Content "$scriptDir\..\data\product-ids.json" | ConvertFrom-Json

$fergusonId = $accountIds.Distributors."Ferguson Enterprises"
Write-Host "Hero Account: Ferguson Enterprises ($fergusonId)" -ForegroundColor Cyan

# ============================================================
# Step 1: Enrich the Ferguson account record
# ============================================================
Write-StepHeader "1" "Enrich Hero Account -- Ferguson Enterprises"

$apiUrl = Get-DataverseApiUrl
$headers = Get-DataverseHeaders

# Update account with richer fields (split into two patches for reliability)
$acctPatch1 = @{
    revenue                = 27800000000.0
    numberofemployees      = 36000
    address1_line1         = "751 Lakefront Commons"
    address1_city          = "Newport News"
    address1_stateorprovince = "VA"
    address1_postalcode    = "23602"
    address1_country       = "US"
    address1_telephone1    = "(757) 874-7795"
    websiteurl             = "https://www.ferguson.com"
    description            = "Largest US plumbing distributor. #1 Zurn/Elkay channel partner. Tier 1 Strategic account with 450+ branches nationwide. Primary products: hydration, backflow, drainage, commercial fixtures. Annual Zurn/Elkay volume: ~42M. Key contacts: Tom Harrison (Plumbing Category Mgr), Rachel Chen (Purchasing Dir), Mike Reynolds (Field Ops)."
}

try {
    Invoke-RestMethod -Uri "$apiUrl/accounts($fergusonId)" -Method Patch `
        -Headers $headers -Body ($acctPatch1 | ConvertTo-Json -Depth 5) `
        -ContentType "application/json; charset=utf-8" -ErrorAction Stop
    Write-Host "  Account enriched with revenue, employees, address, description" -ForegroundColor Green
} catch {
    Write-Warning "Account patch failed: $($_.Exception.Message)"
}

# ============================================================
# Step 2: Create hero contact -- Mike Reynolds (the caller)
# ============================================================
Write-StepHeader "2" "Create Hero Contact -- Mike Reynolds"

$mikeId = Find-OrCreate-Record `
    -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'mike.reynolds@ferguson.com'" `
    -IdField "contactid" `
    -Body @{
        firstname                              = "Mike"
        lastname                               = "Reynolds"
        jobtitle                               = "Field Operations Manager"
        emailaddress1                          = "mike.reynolds@ferguson.com"
        telephone1                             = "(713) 555-0184"
        mobilephone                            = "(713) 555-0185"
        address1_line1                         = "4200 Gulf Freeway"
        address1_city                          = "Houston"
        address1_stateorprovince               = "TX"
        address1_postalcode                    = "77023"
        description                            = "Manages field operations for Ferguson Houston DC. Primary contact for shipping issues, returns, and jobsite escalations. Calls frequently about order status and expedites."
        "parentcustomerid_account@odata.bind"  = "/accounts($fergusonId)"
    } `
    -DisplayName "Mike Reynolds (Ferguson - Houston)"

Write-Host "  Mike Reynolds ID: $mikeId" -ForegroundColor Green

# Also look up Tom and Rachel for cross-references
$tomRecords = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'tom.harrison@ferguson.com'" `
    -Select "contactid,fullname"
$tomId = if ($tomRecords -and $tomRecords.Count -gt 0) { $tomRecords[0].contactid } else { $null }
Write-Host "  Tom Harrison ID: $tomId" -ForegroundColor DarkGray

$rachelRecords = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'rachel.chen@ferguson.com'" `
    -Select "contactid,fullname"
$rachelId = if ($rachelRecords -and $rachelRecords.Count -gt 0) { $rachelRecords[0].contactid } else { $null }
Write-Host "  Rachel Chen ID: $rachelId" -ForegroundColor DarkGray

# ============================================================
# Step 3: Create Sales Orders for Ferguson
# ============================================================
Write-StepHeader "3" "Create Sales Orders for Ferguson"

# Look up price lists by name (live, not from stale JSON)
$zurnPLs = Invoke-DataverseGet -EntitySet "pricelevels" `
    -Filter "name eq 'Zurn Standard Price List'" -Select "pricelevelid"
$elkayPLs = Invoke-DataverseGet -EntitySet "pricelevels" `
    -Filter "name eq 'Elkay Standard Price List'" -Select "pricelevelid"
$zurnPriceListId = if ($zurnPLs -and $zurnPLs.Count -gt 0) { $zurnPLs[0].pricelevelid } else { $null }
$elkayPriceListId = if ($elkayPLs -and $elkayPLs.Count -gt 0) { $elkayPLs[0].pricelevelid } else { $null }
Write-Host "  Zurn PL: $zurnPriceListId  |  Elkay PL: $elkayPriceListId" -ForegroundColor DarkGray

# Get USD currency
$currencies = Invoke-DataverseGet -EntitySet "transactioncurrencies" `
    -Filter "currencyname eq 'US Dollar'" `
    -Select "transactioncurrencyid"
$usdId = if ($currencies -and $currencies.Count -gt 0) { $currencies[0].transactioncurrencyid } else { $null }

if (-not $usdId) {
    $currencies = Invoke-DataverseGet -EntitySet "transactioncurrencies" `
        -Select "transactioncurrencyid,currencyname" -Top 5
    if ($currencies -and $currencies.Count -gt 0) {
        $usdId = $currencies[0].transactioncurrencyid
        Write-Host "  Using currency: $($currencies[0].currencyname) ($usdId)" -ForegroundColor DarkGray
    }
}

# Helper: look up product by product number
function Get-ProductId {
    param([string]$ProductNumber)
    $prods = Invoke-DataverseGet -EntitySet "products" `
        -Filter "productnumber eq '$ProductNumber'" -Select "productid,name"
    if ($prods -and $prods.Count -gt 0) {
        return $prods[0].productid
    }
    return $null
}

# Build the order body helper
function New-OrderBody {
    param(
        [string]$Name,
        [string]$OrderNumber,
        [string]$Description,
        [string]$PriceListId,
        [hashtable]$ShipTo,
        [hashtable]$BillTo,
        [string]$DeliveryDate
    )
    $body = @{
        name                                    = $Name
        ordernumber                             = $OrderNumber
        description                             = $Description
        "customerid_account@odata.bind"         = "/accounts($fergusonId)"
    }
    if ($PriceListId) {
        $body["pricelevelid@odata.bind"] = "/pricelevels($PriceListId)"
    }
    if ($usdId) {
        $body["transactioncurrencyid@odata.bind"] = "/transactioncurrencies($usdId)"
    }
    if ($BillTo) {
        foreach ($k in $BillTo.Keys) { $body["billto_$k"] = $BillTo[$k] }
    }
    if ($ShipTo) {
        foreach ($k in $ShipTo.Keys) { $body["shipto_$k"] = $ShipTo[$k] }
    }
    if ($DeliveryDate) {
        $body["requestdeliveryby"] = $DeliveryDate
    }
    return $body
}

# Helper: add write-in line items (avoids price list item config issues)
function Add-WriteInLine {
    param(
        [string]$OrderId,
        [string]$ProductDesc,
        [int]$Qty,
        [double]$UnitPrice
    )
    # Check if this exact line already exists
    $existing = Invoke-DataverseGet -EntitySet "salesorderdetails" `
        -Filter "_salesorderid_value eq $OrderId and productdescription eq '$ProductDesc'" `
        -Select "salesorderdetailid" -Top 1
    if ($existing -and $existing.Count -gt 0) {
        Write-Host "    $ProductDesc - already exists" -ForegroundColor DarkGray
        return
    }

    $lineBody = @{
        "salesorderid@odata.bind" = "/salesorders($OrderId)"
        isproductoverridden       = $true
        productdescription        = $ProductDesc
        quantity                  = $Qty
        priceperunit              = $UnitPrice
        ispriceoverridden         = $true
    }
    try {
        Invoke-DataversePost -EntitySet "salesorderdetails" -Body $lineBody
        $total = $Qty * $UnitPrice
        Write-Host "    $ProductDesc x $Qty = `$$total" -ForegroundColor Green
    } catch {
        Write-Warning "    Failed: $($_.Exception.Message)"
    }
}

# --- Order 1: Large hydration order (the one Mike will call about) ---
$order1Body = New-OrderBody `
    -Name "Ferguson PO #94820 - Hydration Products Q1" `
    -OrderNumber "PO-94820" `
    -Description "Q1 2026 hydration product order for Ferguson national rollout. 5 line items. Ship to Houston DC." `
    -PriceListId $elkayPriceListId `
    -BillTo @{ name = "Ferguson Enterprises"; line1 = "751 Lakefront Commons"; city = "Newport News"; stateorprovince = "VA"; postalcode = "23602" } `
    -ShipTo @{ name = "Ferguson Houston DC"; line1 = "4200 Gulf Freeway"; city = "Houston"; stateorprovince = "TX"; postalcode = "77023" } `
    -DeliveryDate "2026-03-15T00:00:00Z"

$order1Id = Find-OrCreate-Record `
    -EntitySet "salesorders" `
    -Filter "name eq 'Ferguson PO #94820 - Hydration Products Q1'" `
    -IdField "salesorderid" `
    -Body $order1Body `
    -DisplayName "Ferguson PO #94820 (Hydration Q1)"

Write-Host "  Order 1 ID: $order1Id" -ForegroundColor Green

# Add line items as write-in products (reliable, no price list item dependency)
Write-Host "  Adding line items to PO #94820..." -ForegroundColor Yellow
Add-WriteInLine -OrderId $order1Id -ProductDesc "EK-BF-5001 Elkay EZH2O Bottle Filling Station" -Qty 120 -UnitPrice 1150.00
Add-WriteInLine -OrderId $order1Id -ProductDesc "EK-WC-5002 Elkay Wall Mount Water Cooler Bi-Level ADA" -Qty 60 -UnitPrice 780.00
Add-WriteInLine -OrderId $order1Id -ProductDesc "EK-FL-6003 Elkay WaterSentry Plus Replacement Filter" -Qty 200 -UnitPrice 29.50
Add-WriteInLine -OrderId $order1Id -ProductDesc "EK-DF-5003 Elkay Floor Mount Drinking Fountain ADA" -Qty 25 -UnitPrice 1450.00
Add-WriteInLine -OrderId $order1Id -ProductDesc "EK-SS-6001 Elkay Stainless Steel Single Bowl Sink Commercial" -Qty 40 -UnitPrice 780.00

# --- Order 2: Zurn backflow/drainage order (prior order, shows history) ---
$order2Body = New-OrderBody `
    -Name "Ferguson PO #93201 - Zurn Backflow Q4" `
    -OrderNumber "PO-93201" `
    -Description "Q4 2025 backflow and drainage order. Delivered to Newport News warehouse." `
    -PriceListId $zurnPriceListId `
    -BillTo @{ name = "Ferguson Enterprises" } `
    -ShipTo @{ name = "Ferguson Newport News Warehouse"; line1 = "751 Lakefront Commons"; city = "Newport News"; stateorprovince = "VA"; postalcode = "23602" }

$order2Id = Find-OrCreate-Record `
    -EntitySet "salesorders" `
    -Filter "name eq 'Ferguson PO #93201 - Zurn Backflow Q4'" `
    -IdField "salesorderid" `
    -Body $order2Body `
    -DisplayName "Ferguson PO #93201 (Zurn Backflow Q4)"

Write-Host "  Order 2 ID: $order2Id" -ForegroundColor Green

Write-Host "  Adding line items to PO #93201..." -ForegroundColor Yellow
Add-WriteInLine -OrderId $order2Id -ProductDesc "WK-DC-4002 Wilkins Double Check Valve Assembly 4in" -Qty 50 -UnitPrice 485.00
Add-WriteInLine -OrderId $order2Id -ProductDesc "WK-RP-4001 Wilkins RPZ Backflow Preventer" -Qty 30 -UnitPrice 1250.00
Add-WriteInLine -OrderId $order2Id -ProductDesc "ZN-FD-3001 Zurn Floor Drain Cast Iron" -Qty 100 -UnitPrice 185.00
Add-WriteInLine -OrderId $order2Id -ProductDesc "ZN-TD-3002 Zurn Trench Drain System 4ft" -Qty 40 -UnitPrice 425.00
Add-WriteInLine -OrderId $order2Id -ProductDesc "ZN-RD-3003 Zurn Roof Drain 4in" -Qty 75 -UnitPrice 145.00

# --- Order 3: Recent small flush valve order ---
$order3Body = New-OrderBody `
    -Name "Ferguson PO #95102 - Flush Valves Replenishment" `
    -OrderNumber "PO-95102" `
    -Description "Emergency replenishment for flush valves. Houston branch low on stock." `
    -PriceListId $zurnPriceListId `
    -ShipTo @{ name = "Ferguson Houston DC"; line1 = "4200 Gulf Freeway"; city = "Houston"; stateorprovince = "TX"; postalcode = "77023" }

$order3Id = Find-OrCreate-Record `
    -EntitySet "salesorders" `
    -Filter "name eq 'Ferguson PO #95102 - Flush Valves Replenishment'" `
    -IdField "salesorderid" `
    -Body $order3Body `
    -DisplayName "Ferguson PO #95102 (Flush Valves)"

Write-Host "  Adding line items to PO #95102..." -ForegroundColor Yellow
Add-WriteInLine -OrderId $order3Id -ProductDesc "ZN-AV-1001 Zurn AquaVantage AV Flush Valve" -Qty 200 -UnitPrice 245.00
Add-WriteInLine -OrderId $order3Id -ProductDesc "ZN-EZ-1002 Zurn EZ Flush Sensor Retrofit Kit" -Qty 150 -UnitPrice 189.00
Add-WriteInLine -OrderId $order3Id -ProductDesc "ZN-UR-1003 Zurn Urinal Flush Valve 0.5 GPF" -Qty 80 -UnitPrice 215.00

# ============================================================
# Step 4: Create the phone call CASE (the one set up for the live demo)
# ============================================================
Write-StepHeader "4" "Create Phone Call Demo Case"

# This is the case the agent will have OPEN when the "call comes in"
# Scenario: Mike Reynolds calls about PO #94820 -- wants to cancel 2 lines
# and expedite the remaining 3.
$phoneCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Ferguson PO #94820 - Order modification request'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "Ferguson PO #94820 - Order modification request"
        description                              = "Mike Reynolds from Ferguson Houston called regarding PO #94820 (Hydration Products Q1). Customer wants to cancel 2 of the 5 line items (EK-DF-5003 Drinking Fountains x25 and EK-SS-6001 Sinks x40) due to a project scope change at their end customer. Remaining 3 lines (EZH2O Bottle Fillers x120, Wall Mount Coolers x60, Replacement Filters x200) need to be expedited -- requested delivery moved up from March 15 to March 10. Ferguson is our #1 distributor -- Tier 1 Strategic. Handle with priority."
        "customerid_account@odata.bind"          = "/accounts($fergusonId)"
        "primarycontactid@odata.bind"            = "/contacts($mikeId)"
        caseorigincode                           = 1   # Phone
        prioritycode                             = 1   # High
        casetypecode                             = 2   # Problem
        cr377_tierlevel                          = 192350000
    } `
    -DisplayName "Ferguson PO #94820 - Order modification (Phone Case)"

Write-Host "  Phone case ID: $phoneCaseId" -ForegroundColor Green

# ============================================================
# Step 5: Add timeline activities to the phone case
# ============================================================
Write-StepHeader "5" "Add Timeline Activities (Case History)"

# Prior note -- internal note from Tom Harrison case
$noteBody = @{
    subject                              = "Prior discussion with Rachel Chen re: PO #94820"
    notetext                             = "Rachel Chen (Purchasing Director) emailed last week confirming the Q1 hydration order. She mentioned the Fort Worth school district project may reduce scope, which could affect the drinking fountain and sink lines. Tom Harrison flagged this as well. Mike Reynolds (Houston) is the day-to-day contact for this order."
    "objectid_incident@odata.bind"       = "/incidents($phoneCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $noteBody
    Write-Host "  Added internal note (prior Rachel Chen discussion)" -ForegroundColor Green
} catch {
    Write-Warning "  Note creation failed: $($_.Exception.Message)"
}

# Phone call activity -- prior call (2 days ago)
$priorCallBody = @{
    subject                                = "Mike Reynolds - PO #94820 delivery timeline check"
    description                            = "Mike called to check delivery timeline for PO #94820. Confirmed current ETA is March 15. He mentioned the end customer (Fort Worth ISD) might reduce scope on the school renovation project. Said he'd call back if they need to modify the order. No action needed yet."
    phonenumber                            = "(713) 555-0184"
    directioncode                          = $true   # Incoming
    "regardingobjectid_incident@odata.bind" = "/incidents($phoneCaseId)"
    actualstart                            = "2026-03-03T14:30:00Z"
    actualend                              = "2026-03-03T14:37:00Z"
    actualdurationminutes                  = 7
}
try {
    Invoke-DataversePost -EntitySet "phonecalls" -Body $priorCallBody
    Write-Host "  Added prior phone call (March 3 - delivery check)" -ForegroundColor Green
} catch {
    Write-Warning "  Phone call activity failed: $($_.Exception.Message)"
}

# Email activity -- Rachel's original PO confirmation
$emailBody = @{
    subject                                = "RE: PO #94820 - Q1 Hydration Products Order Confirmation"
    description                            = "Rachel confirmed the full order on Feb 20. 5 line items totaling approx 295K. She noted the Fort Worth ISD project is the primary driver for the drinking fountains and sinks. Bottle filling stations and coolers are for their national FM contract (confirmed, no risk)."
    directioncode                          = $true
    "regardingobjectid_incident@odata.bind" = "/incidents($phoneCaseId)"
    actualstart                            = "2026-02-20T10:15:00Z"
}
try {
    Invoke-DataversePost -EntitySet "emails" -Body $emailBody
    Write-Host "  Added email activity (Feb 20 - Rachel PO confirmation)" -ForegroundColor Green
} catch {
    Write-Warning "  Email activity failed: $($_.Exception.Message)"
}

# Another note -- shipping status
$note2Body = @{
    subject                              = "PO #94820 warehouse status"
    notetext                             = "Checked with Paso Robles warehouse. EZH2O units (120) and Wall Mount Coolers (60) are staged and ready to ship. Filters (200) shipping from Erie. Drinking Fountains (25) and Sinks (40) are backordered -- ETA to warehouse is March 12. If customer reduces scope on those two lines, we avoid the backorder entirely."
    "objectid_incident@odata.bind"       = "/incidents($phoneCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $note2Body
    Write-Host "  Added warehouse status note" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}

# ============================================================
# Step 6: Create a second case for screen pop variety
# ============================================================
Write-StepHeader "6" "Create Additional Ferguson Context Cases"

# A resolved case (shows history)
try {
$resolvedCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Ferguson - EZH2O filter replacement bulk discount approved'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "Ferguson - EZH2O filter replacement bulk discount approved"
        description                              = "Rachel Chen negotiated 15% volume discount on WaterSentry Plus filters (EK-FL-6003) for orders over 500 units. Discount approved by pricing team. Applied to PO #94820 and all future filter orders. Valid through 12/2026."
        "customerid_account@odata.bind"          = "/accounts($fergusonId)"
        "primarycontactid@odata.bind"            = "/contacts($rachelId)"
        caseorigincode                           = 2   # Email
        prioritycode                             = 2   # Normal
        cr377_tierlevel                          = 192350000
    } `
    -DisplayName "Ferguson - Filter discount (resolved)"
} catch {
    Write-Warning "Could not create resolved case: $($_.Exception.Message)"
    $resolvedCaseId = $null
}

# Try to resolve it (only if case was created)
if ($resolvedCaseId) {
try {
    $resolvePayload = @{
        Status  = 5   # Problem Solved
        Incidentid = @{
            incidentid      = "$resolvedCaseId"
            "@odata.type"   = "Microsoft.Dynamics.CRM.incident"
        }
        Resolution = @{
            subject                                = "Bulk discount approved - 15% on filters"
            description                            = "Pricing team approved 15% discount on EK-FL-6003 for 500+ unit orders. Applied to current and future POs."
            "incidentid@odata.bind"                = "/incidents($resolvedCaseId)"
            actualdurationminutes                  = 45
            timespent                              = 45
        }
    }
    # Use direct API call for CloseIncident action
    Invoke-RestMethod -Uri "$apiUrl/CloseIncident" -Method Post `
        -Headers $headers -Body ($resolvePayload | ConvertTo-Json -Depth 5) `
        -ContentType "application/json; charset=utf-8" -ErrorAction Stop
    Write-Host "  Resolved: Filter discount case" -ForegroundColor Green
} catch {
    Write-Host "  Could not auto-resolve (may already be resolved or schema mismatch): $($_.Exception.Message)" -ForegroundColor DarkGray
}
} # end if ($resolvedCaseId)

# ============================================================
# Step 7: Output summary and demo call script
# ============================================================
Write-StepHeader "7" "Summary and Demo Call Script"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " HERO ACCOUNT SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Hero Account: Ferguson Enterprises (Tier 1 Strategic)" -ForegroundColor White
Write-Host "   Account ID:  $fergusonId" -ForegroundColor DarkGray
Write-Host "   Revenue:     `$27.8B | Employees: 36,000" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Hero Contacts:" -ForegroundColor White
Write-Host "   Mike Reynolds  (713) 555-0184  mike.reynolds@ferguson.com" -ForegroundColor White
Write-Host "     -> Field Ops Manager, Houston DC. THE CALLER." -ForegroundColor Yellow
Write-Host "   Tom Harrison   (757) 555-2001  tom.harrison@ferguson.com" -ForegroundColor DarkGray
Write-Host "   Rachel Chen    (757) 555-2002  rachel.chen@ferguson.com" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Sales Orders:" -ForegroundColor White
Write-Host "   PO #94820 - Hydration Products Q1 (~`$295K, 5 lines) <-- DEMO ORDER" -ForegroundColor Yellow
Write-Host "   PO #93201 - Zurn Backflow Q4 (5 lines, delivered)" -ForegroundColor DarkGray
Write-Host "   PO #95102 - Flush Valves Replenishment (3 lines)" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Phone Case: Ferguson PO #94820 - Order modification request" -ForegroundColor White
Write-Host "   Case ID: $phoneCaseId" -ForegroundColor DarkGray
Write-Host "   Timeline: 2 notes, 1 prior phone call, 1 email" -ForegroundColor DarkGray

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host " DEMO CALL SCRIPT" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host " SETUP: Log into CS Workspace as the agent. Have 'My Active" -ForegroundColor White
Write-Host " Cases' view open. The Ferguson order mod case should be visible." -ForegroundColor White
Write-Host ""
Write-Host " SCENARIO: Mike Reynolds from Ferguson Houston calls about" -ForegroundColor White
Write-Host " PO #94820. He needs to cancel 2 lines (drinking fountains" -ForegroundColor White
Write-Host " and sinks) and expedite the remaining 3 lines." -ForegroundColor White
Write-Host ""
Write-Host " --- WHAT THE AGENT SEES ---" -ForegroundColor Cyan
Write-Host " 1. Inbound call arrives -> Screen pop shows:" -ForegroundColor White
Write-Host "    - Mike Reynolds, Ferguson Enterprises (Tier 1)" -ForegroundColor White
Write-Host "    - 3 open orders, case history, account 360" -ForegroundColor White
Write-Host "    - Tier 1 Strategic banner (red pill)" -ForegroundColor White
Write-Host " 2. Real-time transcript appears as conversation flows" -ForegroundColor White
Write-Host " 3. Copilot suggests KB articles about order modifications" -ForegroundColor White
Write-Host " 4. Agent opens the case, sees PO #94820 context" -ForegroundColor White
Write-Host " 5. Agent updates case notes with the modification details" -ForegroundColor White
Write-Host " 6. After call: Copilot auto-summarizes the conversation" -ForegroundColor White
Write-Host ""
Write-Host " --- WHAT YOU SAY (AS MIKE) ---" -ForegroundColor Cyan
Write-Host " 'Hi, this is Mike Reynolds from Ferguson, calling from our" -ForegroundColor White
Write-Host "  Houston distribution center. I need to make some changes" -ForegroundColor White
Write-Host "  to PO #94820 -- the hydration products order.'" -ForegroundColor White
Write-Host ""
Write-Host " 'The Fort Worth school district project just reduced scope." -ForegroundColor White
Write-Host "  We need to CANCEL the drinking fountains -- that was 25 units" -ForegroundColor White
Write-Host "  of the floor mount model -- and also cancel the 40 stainless" -ForegroundColor White
Write-Host "  steel sinks. Those two lines are no longer needed.'" -ForegroundColor White
Write-Host ""
Write-Host " 'But here is the thing -- the remaining three lines, the" -ForegroundColor White
Write-Host "  bottle filling stations, the wall mount coolers, and the" -ForegroundColor White
Write-Host "  replacement filters -- we actually need those SOONER. Can" -ForegroundColor White
Write-Host "  you move the delivery up from March 15 to March 10? Our" -ForegroundColor White
Write-Host "  FM contractor is starting the national rollout early.'" -ForegroundColor White
Write-Host ""
Write-Host " 'And Rachel Chen mentioned something about a filter discount" -ForegroundColor White
Write-Host "  that was just approved -- can you make sure that is applied" -ForegroundColor White
Write-Host "  to this order too?'" -ForegroundColor White
Write-Host ""
Write-Host " --- KEY DEMO MOMENTS ---" -ForegroundColor Yellow
Write-Host " * Screen pop with full customer context (no 'who am I" -ForegroundColor White
Write-Host "   speaking with?' needed)" -ForegroundColor White
Write-Host " * Real-time transcript captures the order modification" -ForegroundColor White
Write-Host "   details as Mike speaks" -ForegroundColor White
Write-Host " * Copilot suggests: 'Order Modification Process' KB article" -ForegroundColor White
Write-Host " * Agent sees prior call note (March 3) confirming Mike" -ForegroundColor White
Write-Host "   warned about possible scope reduction" -ForegroundColor White
Write-Host " * Agent sees warehouse note: fountains & sinks were" -ForegroundColor White
Write-Host "   backordered anyway -- cancelling avoids backorder" -ForegroundColor White
Write-Host " * Rachel's filter discount already in case history" -ForegroundColor White
Write-Host " * After wrap-up: Copilot summarizes the call and drafts" -ForegroundColor White
Write-Host "   confirmation email to Mike" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Save hero record IDs for downstream scripts
$heroData = @{
    HeroAccount = @{
        Name = "Ferguson Enterprises"
        Id = "$fergusonId"
        Tier = 1
    }
    HeroContacts = @{
        MikeReynolds = @{
            Id = "$mikeId"
            Phone = "(713) 555-0184"
            Email = "mike.reynolds@ferguson.com"
            Role = "Field Operations Manager - Houston DC"
        }
        TomHarrison = @{
            Id = "$tomId"
            Phone = "(757) 555-2001"
            Email = "tom.harrison@ferguson.com"
            Role = "Plumbing Category Manager"
        }
        RachelChen = @{
            Id = "$rachelId"
            Phone = "(757) 555-2002"
            Email = "rachel.chen@ferguson.com"
            Role = "Purchasing Director"
        }
    }
    Orders = @{
        "PO-94820" = @{
            Id = "$order1Id"
            Desc = "Hydration Products Q1 - 5 lines - DEMO ORDER"
            Lines = @(
                "EK-BF-5001 x120 Bottle Filling Stations",
                "EK-WC-5002 x60 Wall Mount Coolers",
                "EK-FL-6003 x200 Replacement Filters",
                "EK-DF-5003 x25 Drinking Fountains (CANCEL)",
                "EK-SS-6001 x40 Stainless Sinks (CANCEL)"
            )
        }
        "PO-93201" = @{
            Id = "$order2Id"
            Desc = "Zurn Backflow Q4 - 5 lines - delivered"
        }
        "PO-95102" = @{
            Id = "$order3Id"
            Desc = "Flush Valves Replenishment - 3 lines"
        }
    }
    PhoneCaseId = "$phoneCaseId"
}

$heroData | ConvertTo-Json -Depth 5 | Set-Content "$scriptDir\..\data\hero-record-ids.json" -Encoding UTF8
Write-Host "`nHero record IDs saved to data/hero-record-ids.json" -ForegroundColor Green
