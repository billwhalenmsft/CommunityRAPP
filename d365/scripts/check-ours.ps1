$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization" = "Bearer $token"; "Accept" = "application/json"; "OData-Version" = "4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"
function DoGet($url) { return (Invoke-WebRequest -Uri $url -Headers $h -UseBasicParsing).Content | ConvertFrom-Json }

# Check OUR SLA specifically
Write-Host "=== Zurn Elkay SLA ===" -ForegroundColor Cyan
$filter = [System.Uri]::EscapeDataString("name eq 'Zurn Elkay Standard SLA'")
$r = DoGet "$b/slas?`$filter=$filter&`$select=name,slaid,statecode,statuscode,slaversion,description"
if ($r.value.Count -eq 0) { Write-Host "  NOT FOUND - Step 6 SLA not created yet" -ForegroundColor Red }
else { $r.value | ForEach-Object { Write-Host "  Name: $($_.name)"; Write-Host "  ID: $($_.slaid)"; Write-Host "  State: $($_.statecode) Status: $($_.statuscode)"; Write-Host "  Version: $($_.slaversion)"; Write-Host "  Desc: $($_.description)" } }

# Check our SLA Items linked to our SLA
if ($r.value.Count -gt 0) {
    $slaId = $r.value[0].slaid
    $itemFilter = [System.Uri]::EscapeDataString("_slaid_value eq '$slaId'")
    $items = DoGet "$b/slaitems?`$filter=$itemFilter&`$select=name,failureafter,warnafter"
    Write-Host "`n=== Our SLA Items ===" -ForegroundColor Cyan
    Write-Host "  Count: $($items.value.Count)"
    $items.value | ForEach-Object { Write-Host "  $($_.name) | fail=$($_.failureafter)min | warn=$($_.warnafter)min" }
}

# Check OUR cases  
Write-Host "`n=== Zurn/Elkay Cases ===" -ForegroundColor Cyan
$caseFilter = [System.Uri]::EscapeDataString("contains(title,'Zurn') or contains(title,'Elkay')")
$cases = DoGet "$b/incidents?`$filter=$caseFilter&`$select=title,statecode,statuscode&`$top=50"
Write-Host "  Cases with Zurn/Elkay in title: $($cases.value.Count)"
if ($cases.value.Count -gt 0) {
    $active = @($cases.value | Where-Object { $_.statecode -eq 0 }).Count
    $resolved = @($cases.value | Where-Object { $_.statecode -eq 1 }).Count
    $cancelled = @($cases.value | Where-Object { $_.statecode -eq 2 }).Count
    Write-Host "  Active: $active | Resolved: $resolved | Cancelled: $cancelled"
    $cases.value | Select-Object -First 5 | ForEach-Object { Write-Host "    $($_.title) [state=$($_.statecode)]" }
    if ($cases.value.Count -gt 5) { Write-Host "    ... and $($cases.value.Count - 5) more" }
}

# Check our queues
Write-Host "`n=== Zurn/Elkay Queues ===" -ForegroundColor Cyan
$qFilter = [System.Uri]::EscapeDataString("contains(name,'Zurn') or contains(name,'Elkay')")
$queues = DoGet "$b/queues?`$filter=$qFilter&`$select=name&`$top=30"
Write-Host "  Queues: $($queues.value.Count)"

# Check our products
Write-Host "`n=== Zurn/Elkay Products ===" -ForegroundColor Cyan
$pFilter = [System.Uri]::EscapeDataString("contains(name,'Zurn') or contains(name,'Elkay') or contains(name,'AquaSense') or contains(name,'EZH2O') or contains(name,'ezH2O') or contains(name,'Wilkins')")
$prods = DoGet "$b/products?`$filter=$pFilter&`$select=name,statecode&`$top=30"
Write-Host "  Products: $($prods.value.Count)"
$published = @($prods.value | Where-Object { $_.statecode -eq 1 }).Count
$draft = @($prods.value | Where-Object { $_.statecode -eq 0 }).Count
Write-Host "  Published: $published | Draft: $draft"

Write-Host "`n===== DONE =====" -ForegroundColor Cyan
