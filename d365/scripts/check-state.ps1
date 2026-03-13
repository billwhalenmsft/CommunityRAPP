$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
if (-not $token) { Write-Host "FAILED to get token"; exit 1 }

$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

function DoGet($url) {
    $r = Invoke-WebRequest -Uri $url -Headers $h -UseBasicParsing
    return ($r.Content | ConvertFrom-Json).value
}

Write-Host "===== ENVIRONMENT STATE CHECK =====" -ForegroundColor Cyan

# Accounts
$accts = DoGet "$b/accounts?`$select=name&`$top=50"
Write-Host "Accounts: $($accts.Count)"

# Contacts
$contacts = DoGet "$b/contacts?`$select=fullname&`$top=50"
Write-Host "Contacts: $($contacts.Count)"

# Products
$prods = DoGet "$b/products?`$select=name,statecode&`$top=50"
Write-Host "Products: $($prods.Count) (Published: $(($prods | Where-Object { $_.statecode -eq 1 }).Count))"

# Subjects
$subjs = DoGet "$b/subjects?`$select=title&`$top=50"
Write-Host "Subjects: $($subjs.Count)"

# Queues (custom only)
$queues = DoGet "$b/queues?`$filter=queueviewtype eq 0&`$select=name&`$top=50"
Write-Host "Queues: $($queues.Count)"

# SLAs
$slas = DoGet "$b/slas?`$select=name,slaid,statecode,slaversion&`$top=10"
Write-Host "`nSLAs: $($slas.Count)"
$slas | ForEach-Object { Write-Host "  $($_.name) | state=$($_.statecode) | ver=$($_.slaversion)" }

# SLA Items
$slaItems = DoGet "$b/slaitems?`$select=name,failureafter,warnafter&`$top=20"
Write-Host "SLA Items: $($slaItems.Count)"
$slaItems | ForEach-Object { Write-Host "  $($_.name) | fail=$($_.failureafter) | warn=$($_.warnafter)" }

# Calendars
$cals = DoGet "$b/calendars?`$filter=contains(name,'Zurn') or contains(name,'Business')&`$select=name,calendarid&`$top=10"
Write-Host "`nCalendars matching 'Zurn' or 'Business': $($cals.Count)"
$cals | ForEach-Object { Write-Host "  $($_.name)" }

# Cases
$cases = DoGet "$b/incidents?`$select=title,statecode,statuscode&`$top=50"
Write-Host "`nCases: $($cases.Count)"
if ($cases.Count -gt 0) {
    $active = ($cases | Where-Object { $_.statecode -eq 0 }).Count
    $resolved = ($cases | Where-Object { $_.statecode -eq 1 }).Count
    $cancelled = ($cases | Where-Object { $_.statecode -eq 2 }).Count
    Write-Host "  Active: $active | Resolved: $resolved | Cancelled: $cancelled"
}

Write-Host "`n===== DONE =====" -ForegroundColor Cyan
