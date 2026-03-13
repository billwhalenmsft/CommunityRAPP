$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0"; "Content-Type"="application/json; charset=utf-8"; "Prefer"="return=representation" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# Find our SLA
$slaFilter = [System.Uri]::EscapeDataString("name eq 'Zurn Elkay Standard SLA'")
$slaR = (Invoke-WebRequest -Uri "$b/slas?`$filter=$slaFilter&`$select=slaid" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
if ($slaR.value.Count -eq 0) { Write-Host "SLA not found!"; exit 1 }
$slaId = $slaR.value[0].slaid
Write-Host "SLA ID: $slaId"

# Check existing SLA Items
$itemFilter = [System.Uri]::EscapeDataString("_slaid_value eq '$slaId'")
$existingItems = ((Invoke-WebRequest -Uri "$b/slaitems?`$filter=$itemFilter&`$select=name,slaitemid" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
Write-Host "Existing SLA Items: $($existingItems.Count)"
$existingItems | ForEach-Object { Write-Host "  $($_.name)" }

# Create First Response KPI if missing
$hasFR = $existingItems | Where-Object { $_.name -match 'First Response' }
if (-not $hasFR) {
    Write-Host "Creating First Response - 4 Hours KPI..."
    $frBody = @{
        name                 = 'First Response - 4 Hours'
        'slaid@odata.bind'   = "/slas($slaId)"
        applicablewhenxml    = "<fetch><entity name='incident'><filter><condition attribute='statecode' operator='eq' value='0' /></filter></entity></fetch>"
        successconditionsxml = "<fetch><entity name='incident'><filter><condition attribute='firstresponsesent' operator='eq' value='1' /></filter></entity></fetch>"
        failureafter         = 240
        warnafter            = 180
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-WebRequest -Uri "$b/slaitems" -Method Post -Headers $h -Body $frBody -UseBasicParsing -ErrorAction Stop
        Write-Host "  Created! Status: $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host "  Details: $($_.ErrorDetails.Message)" }
    }
} else {
    Write-Host "First Response KPI already exists"
}

# Create Resolution KPI if missing
$hasRes = $existingItems | Where-Object { $_.name -match 'Resolution' }
if (-not $hasRes) {
    Write-Host "Creating Resolution - 8 Hours KPI..."
    $resBody = @{
        name                 = 'Resolution - 8 Hours'
        'slaid@odata.bind'   = "/slas($slaId)"
        applicablewhenxml    = "<fetch><entity name='incident'><filter><condition attribute='statecode' operator='eq' value='0' /></filter></entity></fetch>"
        successconditionsxml = "<fetch><entity name='incident'><filter><condition attribute='statecode' operator='eq' value='1' /></filter></entity></fetch>"
        failureafter         = 480
        warnafter            = 360
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-WebRequest -Uri "$b/slaitems" -Method Post -Headers $h -Body $resBody -UseBasicParsing -ErrorAction Stop
        Write-Host "  Created! Status: $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host "  Details: $($_.ErrorDetails.Message)" }
    }
} else {
    Write-Host "Resolution KPI already exists"
}

# Enable pause/resume now that KPIs exist
Write-Host "`nEnabling pause/resume on SLA..."
$patchBody = @{ allowpauseresume = $true } | ConvertTo-Json
try {
    Invoke-WebRequest -Uri "$b/slas($slaId)" -Method Patch -Headers $h -Body $patchBody -UseBasicParsing -ErrorAction Stop | Out-Null
    Write-Host "  Pause/resume enabled" -ForegroundColor Green
} catch {
    Write-Host "  Could not enable pause/resume: $($_.Exception.Message)" -ForegroundColor Yellow
    if ($_.ErrorDetails.Message) { Write-Host "  $($_.ErrorDetails.Message)" }
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
Write-Host "SLA: Zurn Elkay Standard SLA ($slaId)"
Write-Host "NOTE: SLA must be activated manually in CS admin center"
