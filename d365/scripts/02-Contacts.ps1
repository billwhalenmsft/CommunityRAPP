<#
.SYNOPSIS
    Step 02 - Create Contacts for Zurn Elkay Demo
.DESCRIPTION
    Creates contacts for manufacturer accounts (Zurn Elkay stakeholders),
    distributor contacts, and end-user contacts. Links each to their account.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "02" "Create Contacts"
Connect-Dataverse

# ============================================================
# Load account IDs from step 01
# ============================================================
$accountIdsFile = "$scriptDir\..\data\account-ids.json"
if (-not (Test-Path $accountIdsFile)) {
    throw "Account IDs file not found. Run 01-Accounts.ps1 first."
}
$accountIds = Get-Content $accountIdsFile | ConvertFrom-Json

# Helper to resolve account GUID
function Get-AccountId([string]$name) {
    $props = @("Manufacturers", "Distributors", "EndUsers")
    foreach ($p in $props) {
        $group = $accountIds.$p
        if ($group.PSObject.Properties.Name -contains $name) {
            return $group.$name
        }
    }
    # Fallback: look up from Dataverse
    $acct = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$name'" -Select "accountid" -Top 1
    if ($acct) { return $acct[0].accountid }
    return $null
}

# ============================================================
# 1. Zurn Elkay Internal Stakeholders (demo contacts)
# ============================================================
Write-Host "`nCreating Zurn Elkay stakeholder contacts..." -ForegroundColor Yellow

$zurnId = Get-AccountId "Zurn Industries"

$stakeholders = @(
    @{ first = "Lisa";  last = "Kume";      title = "Customer Care Manager";          email = "lisa.kume@zurn.com";      phone = "(414) 555-1001"; desc = "21 years at Zurn. Manages ~110 Zurn care agents." },
    @{ first = "Chad";  last = "Didriksen";  title = "IT Manager";                    email = "chad.didriksen@zurn.com"; phone = "(414) 555-1002"; desc = "Oversees Salesforce. Works with KPI Management in Tableau." },
    @{ first = "Darin"; last = "Volpe";      title = "Salesforce Admin";              email = "darin.volpe@zurn.com";    phone = "(414) 555-1003"; desc = "8 years at Zurn/Wilkins. Local Salesforce contact." },
    @{ first = "Mike";  last = "Schmidt";    title = "Director of CRM and BI";        email = "mike.schmidt@zurn.com";   phone = "(414) 555-1004"; desc = "6 months in role. Overseeing CRM transformation." },
    @{ first = "Steve"; last = "Krupp";      title = "Infrastructure & Voice Manager"; email = "steve.krupp@zurn.com";   phone = "(414) 555-1005"; desc = "Manages infrastructure and voice/telephony (Genesys CTI)." }
)

foreach ($c in $stakeholders) {
    $body = @{
        firstname             = $c.first
        lastname              = $c.last
        jobtitle              = $c.title
        emailaddress1         = $c.email
        telephone1            = $c.phone
        description           = $c.desc
        "parentcustomerid_account@odata.bind" = "/accounts($zurnId)"
    }
    Find-OrCreate-Record `
        -EntitySet "contacts" `
        -Filter "emailaddress1 eq '$($c.email)'" `
        -IdField "contactid" `
        -Body $body `
        -DisplayName "$($c.first) $($c.last)"
}

# ============================================================
# 2. Distributor Contacts - key buyer/purchasing contacts
# ============================================================
Write-Host "`nCreating distributor contacts..." -ForegroundColor Yellow

$distributorContacts = @(
    # Ferguson
    @{ acct = "Ferguson Enterprises"; first = "Tom";     last = "Harrison";   title = "Plumbing Category Manager"; email = "tom.harrison@ferguson.com";     phone = "(757) 555-2001" },
    @{ acct = "Ferguson Enterprises"; first = "Rachel";  last = "Chen";       title = "Purchasing Director";       email = "rachel.chen@ferguson.com";      phone = "(757) 555-2002" },
    # Hajoca
    @{ acct = "Hajoca Corporation";   first = "Mark";    last = "Sullivan";   title = "Branch Manager";            email = "mark.sullivan@hajoca.com";      phone = "(610) 555-2101" },
    # Winsupply
    @{ acct = "Winsupply Inc.";       first = "Karen";   last = "Ostrowski"; title = "Product Specialist";         email = "karen.ostrowski@winsupply.com"; phone = "(937) 555-2201" },
    # HD Supply
    @{ acct = "HD Supply";            first = "James";   last = "Morales";    title = "Commercial Accounts Manager"; email = "james.morales@hdsupply.com";  phone = "(770) 555-2301" },
    # Wolseley
    @{ acct = "Wolseley Industrial Group"; first = "Sarah"; last = "Tremblay"; title = "Procurement Lead";         email = "sarah.tremblay@wolseley.com";  phone = "(905) 555-2401" },
    # Consolidated Supply
    @{ acct = "Consolidated Supply Co."; first = "David";  last = "Park";     title = "Inside Sales";               email = "david.park@consupply.com";     phone = "(503) 555-2501" },
    # Pacific Plumbing
    @{ acct = "Pacific Plumbing Supply"; first = "Linda";  last = "Nguyen";   title = "Operations Manager";         email = "linda.nguyen@pacificps.com";   phone = "(206) 555-2601" },
    # Midwest Pipe
    @{ acct = "Midwest Pipe & Supply";   first = "Brian";  last = "Kowalski"; title = "Branch Buyer";               email = "brian.kowalski@midwestpipe.com"; phone = "(816) 555-2701" },
    # Southern Pipe
    @{ acct = "Southern Pipe & Supply";  first = "Angela"; last = "Foster";   title = "Customer Service Lead";      email = "angela.foster@southernpipe.com"; phone = "(601) 555-2801" },
    # Gateway
    @{ acct = "Gateway Supply Company";  first = "Eric";   last = "Hammond";  title = "Purchasing Agent";           email = "eric.hammond@gatewaysupply.com"; phone = "(803) 555-2901" },
    # ABC Plumbing
    @{ acct = "ABC Plumbing Wholesale";  first = "Tony";   last = "Reeves";   title = "Owner";                      email = "tony.reeves@abcplumbing.com";  phone = "(303) 555-3001" },
    # Metro Building
    @{ acct = "Metro Building Supply";   first = "Carmen"; last = "Diaz";     title = "Counter Sales";              email = "carmen.diaz@metrobldg.com";    phone = "(602) 555-3101" },
    # Lakeside
    @{ acct = "Lakeside Plumbing Parts"; first = "Ryan";   last = "Brooks";   title = "Owner / Buyer";              email = "ryan.brooks@lakesideparts.com"; phone = "(216) 555-3201" }
)

foreach ($c in $distributorContacts) {
    $acctId = Get-AccountId $c.acct
    $body = @{
        firstname     = $c.first
        lastname      = $c.last
        jobtitle      = $c.title
        emailaddress1 = $c.email
        telephone1    = $c.phone
    }
    if ($acctId) {
        $body["parentcustomerid_account@odata.bind"] = "/accounts($acctId)"
    }
    Find-OrCreate-Record `
        -EntitySet "contacts" `
        -Filter "emailaddress1 eq '$($c.email)'" `
        -IdField "contactid" `
        -Body $body `
        -DisplayName "$($c.first) $($c.last) ($($c.acct))"
}

# ============================================================
# 3. End-User Contacts
# ============================================================
Write-Host "`nCreating end-user contacts..." -ForegroundColor Yellow

$endUserContacts = @(
    @{ acct = "Greenfield School District";  first = "Pat";    last = "Kelley";   title = "Facilities Director";    email = "pkelley@greenfieldsd.edu";     phone = "(414) 555-4001" },
    @{ acct = "City of Mesa Water Dept";     first = "Maria";  last = "Gutierrez"; title = "Utilities Supervisor";  email = "mgutierrez@mesaaz.gov";        phone = "(480) 555-5001" },
    @{ acct = "Marriott Downtown Milwaukee"; first = "Kevin";  last = "Strand";    title = "Chief Engineer";        email = "kevin.strand@marriott.com";    phone = "(414) 555-6001" },
    @{ acct = "Johnson Residence";           first = "Robert"; last = "Johnson";   title = "";                      email = "rjohnson247@gmail.com";        phone = "(608) 555-7001" }
)

foreach ($c in $endUserContacts) {
    $acctId = Get-AccountId $c.acct
    $body = @{
        firstname     = $c.first
        lastname      = $c.last
        emailaddress1 = $c.email
        telephone1    = $c.phone
    }
    if ($c.title) { $body["jobtitle"] = $c.title }
    if ($acctId) {
        $body["parentcustomerid_account@odata.bind"] = "/accounts($acctId)"
    }
    Find-OrCreate-Record `
        -EntitySet "contacts" `
        -Filter "emailaddress1 eq '$($c.email)'" `
        -IdField "contactid" `
        -Body $body `
        -DisplayName "$($c.first) $($c.last) ($($c.acct))"
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Contacts Created Successfully" -ForegroundColor Green
Write-Host " Stakeholders         : $($stakeholders.Count)" -ForegroundColor White
Write-Host " Distributor Contacts : $($distributorContacts.Count)" -ForegroundColor White
Write-Host " End-User Contacts    : $($endUserContacts.Count)" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green
