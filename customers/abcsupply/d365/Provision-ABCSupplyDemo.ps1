<#
.SYNOPSIS
    ABC Supply Savage Branch — Base Demo Provisioning Script
    Provisions: Accounts, Contacts, Base Cases

.DESCRIPTION
    Idempotent. Safe to re-run. Creates or updates records based on name/title match.

.PARAMETER Action
    Accounts | Contacts | Cases | All

.EXAMPLE
    .\Provision-ABCSupplyDemo.ps1 -Action Accounts
    .\Provision-ABCSupplyDemo.ps1 -Action All
#>

[CmdletBinding()]
param(
    [ValidateSet("Accounts","Contacts","Cases","All")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"

# ─────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────
$OrgUrl    = "https://orgecbce8ef.crm.dynamics.com"
$ApiBase   = "$OrgUrl/api/data/v9.2"
$DataDir   = "$PSScriptRoot\..\..\data"

if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Force -Path $DataDir | Out-Null }

# Get token via Azure CLI
$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null)
if (-not $token) {
    Write-Error "Could not get Azure token. Run 'az login' first."
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "OData-MaxVersion" = "4.0"
    "OData-Version" = "4.0"
    "Content-Type" = "application/json"
    "Prefer" = "return=representation"
}

function Invoke-D365 {
    param([string]$Method, [string]$Url, [hashtable]$Body = $null)
    $params = @{ Method = $Method; Uri = $Url; Headers = $headers; TimeoutSec = 30 }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    return Invoke-RestMethod @params
}

function Find-Record {
    param([string]$Entity, [string]$FilterField, [string]$FilterValue, [string]$SelectFields = "")
    $url = "$ApiBase/$Entity`?`$filter=$FilterField eq '$([System.Web.HttpUtility]::UrlEncode($FilterValue))'"
    if ($SelectFields) { $url += "&`$select=$SelectFields" }
    $resp = Invoke-D365 -Method GET -Url $url
    return $resp.value | Select-Object -First 1
}

function Upsert-Account {
    param([hashtable]$Data)
    $existing = Find-Record -Entity "accounts" -FilterField "name" -FilterValue $Data.name -SelectFields "accountid,name"
    if ($existing) {
        Write-Host "  [SKIP] Account exists: $($Data.name)" -ForegroundColor DarkGray
        return $existing.accountid
    }
    $body = @{
        name              = $Data.name
        accountnumber     = $Data.accountnumber
        telephone1        = $Data.telephone1
        emailaddress1     = $Data.emailaddress1
        address1_city     = $Data.city
        address1_stateorprovince = "MN"
        industrycode      = 7
        description       = $Data.notes
    }
    $resp = Invoke-D365 -Method POST -Url "$ApiBase/accounts" -Body $body
    Write-Host "  [CREATE] Account: $($Data.name) → $($resp.accountid)" -ForegroundColor Green
    return $resp.accountid
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Cyan
Write-Host "  ABC SUPPLY — Base Demo Provisioning" -ForegroundColor Cyan
Write-Host "  Action: $Action" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Cyan

$accountIds = @{}

# ─────────────────────────────────────────────────────────────────
# ACCOUNTS
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Accounts") {
    Write-Host "`n  ── Accounts ──" -ForegroundColor Yellow

    $accounts = @(
        @{ name="Andersen Exteriors Savage"; accountnumber="AES-001"; telephone1="952-441-8823"; emailaddress1="service@andersen-exteriors-savage.com"; city="Savage"; notes="Hero Account — Tier 1 Premier Contractor. Highest WO volume. Hero caller: Mike Bergstrom." },
        @{ name="Pella Pro Contractors MN";  accountnumber="PPC-002"; telephone1="952-890-4410"; emailaddress1="dispatch@pellprocontractors.com";       city="Burnsville"; notes="Tier 2 contractor. Pella product focus." },
        @{ name="Prairie Windows & Doors";   accountnumber="PWD-003"; telephone1="952-226-5551"; emailaddress1="info@prairiewindows.com";               city="Shakopee"; notes="Tier 3 standard contractor." },
        @{ name="Bergstrom Home Services";   accountnumber="BHS-004"; telephone1="952-555-0192"; emailaddress1="mike@bergstromhomeservices.com";        city="Eden Prairie"; notes="Tier 4 — small handyman/contractor." }
    )

    foreach ($acct in $accounts) {
        $id = Upsert-Account -Data $acct
        $accountIds[$acct.name] = $id
    }

    $accountIds | ConvertTo-Json | Set-Content "$DataDir\account_ids.json"
    Write-Host "  Account IDs saved → $DataDir\account_ids.json" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────
# CONTACTS
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Contacts") {
    Write-Host "`n  ── Contacts ──" -ForegroundColor Yellow

    if (-not $accountIds.Count) {
        $loaded = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
        if ($loaded) { $loaded.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }
    }

    $contacts = @(
        @{ first="Mike";   last="Bergstrom"; account="Andersen Exteriors Savage"; phone="952-441-8823"; mobile="952-441-8823"; email="mike.bergstrom@andersen-exteriors-savage.com"; title="Service Manager";       notes="Hero caller — use for voice screen pop demo" },
        @{ first="Tyler";  last="Schroeder"; account="Pella Pro Contractors MN";  phone="952-890-4410"; mobile="";            email="tyler.schroeder@pellaprocontractors.com";       title="Field Operations Lead";  notes="" },
        @{ first="Debra";  last="Haugen";    account="Prairie Windows & Doors";   phone="952-226-5551"; mobile="";            email="debra.haugen@prairiewindows.com";                title="Owner";                  notes="" },
        @{ first="Sarah";  last="Kowalski";  account="Andersen Exteriors Savage"; phone="";             mobile="612-555-0234"; email="sarah.kowalski@gmail.com";                     title="Homeowner";              notes="End customer — receives SMS updates for WO-2026-001" }
    )

    $contactIds = @{}
    foreach ($c in $contacts) {
        $existing = Find-Record -Entity "contacts" -FilterField "emailaddress1" -FilterValue $c.email -SelectFields "contactid,fullname"
        if ($existing) {
            Write-Host "  [SKIP] Contact exists: $($c.first) $($c.last)" -ForegroundColor DarkGray
            $contactIds["$($c.first) $($c.last)"] = $existing.contactid
            continue
        }
        $body = @{
            firstname     = $c.first
            lastname      = $c.last
            telephone1    = $c.phone
            mobilephone   = $c.mobile
            emailaddress1 = $c.email
            jobtitle      = $c.title
            description   = $c.notes
        }
        $acctId = $accountIds[$c.account]
        if ($acctId) { $body["parentcustomerid_account@odata.bind"] = "/accounts($acctId)" }
        $resp = Invoke-D365 -Method POST -Url "$ApiBase/contacts" -Body $body
        Write-Host "  [CREATE] Contact: $($c.first) $($c.last) → $($resp.contactid)" -ForegroundColor Green
        $contactIds["$($c.first) $($c.last)"] = $resp.contactid
    }

    $contactIds | ConvertTo-Json | Set-Content "$DataDir\contact_ids.json"
    Write-Host "  Contact IDs saved → $DataDir\contact_ids.json" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────
# BASE CASES
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Cases") {
    Write-Host "`n  ── Base Cases ──" -ForegroundColor Yellow

    if (-not $accountIds.Count) {
        $loaded = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
        if ($loaded) { $loaded.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }
    }
    $contactIds = @{}
    $loadedC = Get-Content "$DataDir\contact_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedC) { $loadedC.PSObject.Properties | ForEach-Object { $contactIds[$_.Name] = $_.Value } }

    $cases = @(
        @{
            title      = "Andersen 400 Casement — Seal Failure / Water Intrusion"
            account    = "Andersen Exteriors Savage"
            contact    = "Mike Bergstrom"
            origin     = 1
            priority   = 1
            status     = 1
            description = "Homeowner (Sarah Kowalski, Prior Lake) reporting water coming in around casement window frame. Andersen Exteriors installed 14 months ago. Seal failure confirmed — manufacturer warranty claim filed. Replacement seal kit ordered from Andersen. ETA 12-14 business days."
        },
        @{
            title      = "Pella Impervia Slider — Operator Mechanism Failure"
            account    = "Pella Pro Contractors MN"
            contact    = "Tyler Schroeder"
            origin     = 2
            priority   = 2
            status     = 1
            description = "Pella sliding window operator mechanism stripped. Window unable to lock. Part in stock at warehouse. Tech dispatched Thursday 10am."
        },
        @{
            title      = "Screen Replacement — 12-Unit Prairie Windows Project"
            account    = "Prairie Windows & Doors"
            contact    = "Debra Haugen"
            origin     = 3
            priority   = 3
            status     = 5
            description = "12 window screen replacements completed. Frames measured, screens installed. Pre/post photos captured. Awaiting customer sign-off."
        },
        @{
            title      = "Casement Window — Balance Spring Broken / Won't Stay Open"
            account    = "Andersen Exteriors Savage"
            contact    = "Mike Bergstrom"
            origin     = 1
            priority   = 2
            status     = 1
            description = "Balance spring broken on casement window — master bedroom. Part PART-BAL-KIT in stock. Quick repair — same-day dispatch possible."
        }
    )

    $caseIds = @{}
    foreach ($c in $cases) {
        $existing = Find-Record -Entity "incidents" -FilterField "title" -FilterValue $c.title -SelectFields "incidentid,title"
        if ($existing) {
            Write-Host "  [SKIP] Case exists: $($c.title.Substring(0,[Math]::Min(50,$c.title.Length)))..." -ForegroundColor DarkGray
            $caseIds[$c.title] = $existing.incidentid
            continue
        }
        $body = @{
            title           = $c.title
            description     = $c.description
            caseorigincode  = $c.origin
            prioritycode    = $c.priority
            statecode       = 0
            statuscode      = $c.status
        }
        $acctId = $accountIds[$c.account]
        $ctcId  = $contactIds[$c.contact]
        if ($acctId) { $body["customerid_account@odata.bind"] = "/accounts($acctId)" }
        if ($ctcId)  { $body["primarycontactid@odata.bind"]   = "/contacts($ctcId)" }

        $resp = Invoke-D365 -Method POST -Url "$ApiBase/incidents" -Body $body
        Write-Host "  [CREATE] Case: $($c.title.Substring(0,[Math]::Min(50,$c.title.Length)))... → $($resp.incidentid)" -ForegroundColor Green
        $caseIds[$c.title] = $resp.incidentid
    }

    $caseIds | ConvertTo-Json | Set-Content "$DataDir\case_ids.json"
    Write-Host "  Case IDs saved → $DataDir\case_ids.json" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  ABC Supply Base Provisioning Complete" -ForegroundColor Green
Write-Host ("═" * 60) -ForegroundColor Green
