$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0"; "Content-Type"="application/json; charset=utf-8"; "Prefer"="return=representation" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$slaId = 'f8c8c488-9912-f111-8407-7c1e52143136'
$firstResponseKpiId = '680ca024-0c71-ef11-a671-7c1e520b7f56'
$resolvedByKpiId = '0c94637a-0c71-ef11-a671-7c1e520b7f56'

# Check existing items
$itemFilter = [System.Uri]::EscapeDataString("_slaid_value eq '$slaId'")
$existingItems = ((Invoke-WebRequest -Uri "$b/slaitems?`$filter=$itemFilter&`$select=name,slaitemid" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
Write-Host "Existing SLA Items for our SLA: $($existingItems.Count)"

# First Response KPI
$hasFR = $existingItems | Where-Object { $_.name -match 'First Response' }
if (-not $hasFR) {
    Write-Host "Creating First Response - 4 Hours..."
    $frBody = @{
        name                              = 'First Response - 4 Hours'
        'slaid@odata.bind'                = "/slas($slaId)"
        'msdyn_slakpiid@odata.bind'       = "/msdyn_slakpis($firstResponseKpiId)"
        applicablewhenxml                 = "<fetch><entity name='incident'><filter><condition attribute='statecode' operator='eq' value='0' /></filter></entity></fetch>"
        successconditionsxml              = "<fetch><entity name='incident'><filter><condition attribute='firstresponsesent' operator='eq' value='1' /></filter></entity></fetch>"
        failureafter                      = 240
        warnafter                         = 180
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-WebRequest -Uri "$b/slaitems" -Method Post -Headers $h -Body $frBody -UseBasicParsing -ErrorAction Stop
        Write-Host "  SUCCESS: $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host "  Details: $($_.ErrorDetails.Message)" }
    }
} else {
    Write-Host "First Response already exists"
}

# Resolution KPI
$hasRes = $existingItems | Where-Object { $_.name -match 'Resolution' }
if (-not $hasRes) {
    Write-Host "Creating Resolution - 8 Hours..."
    $resBody = @{
        name                              = 'Resolution - 8 Hours'
        'slaid@odata.bind'                = "/slas($slaId)"
        'msdyn_slakpiid@odata.bind'       = "/msdyn_slakpis($resolvedByKpiId)"
        applicablewhenxml                 = "<fetch><entity name='incident'><filter><condition attribute='statecode' operator='eq' value='0' /></filter></entity></fetch>"
        successconditionsxml              = "<fetch><entity name='incident'><filter><condition attribute='statecode' operator='eq' value='1' /></filter></entity></fetch>"
        failureafter                      = 480
        warnafter                         = 360
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-WebRequest -Uri "$b/slaitems" -Method Post -Headers $h -Body $resBody -UseBasicParsing -ErrorAction Stop
        Write-Host "  SUCCESS: $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host "  Details: $($_.ErrorDetails.Message)" }
    }
} else {
    Write-Host "Resolution already exists"
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
