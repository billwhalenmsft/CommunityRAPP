<#
.SYNOPSIS
    Links all Otis cases to their appropriate products, subjects, and KB articles.
#>

Import-Module "$PSScriptRoot\DataverseHelper.psm1" -Force
Connect-Dataverse

$headers = Get-DataverseHeaders
$base = Get-DataverseApiUrl
$patchH = @{
    "Authorization" = $headers["Authorization"]
    "Content-Type"  = "application/json; charset=utf-8"
    "OData-Version" = "4.0"
}

function Link-Case {
    param(
        [string]$CaseId,
        [string]$SubjectId,
        [string]$ProductId,
        [string]$Label
    )
    $body = @{}
    if ($SubjectId) { $body["subjectid@odata.bind"] = "/subjects($SubjectId)" }
    if ($ProductId) { $body["productid@odata.bind"] = "/products($ProductId)" }
    $json = $body | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$base/incidents($CaseId)" -Headers $patchH -Method Patch -Body ([System.Text.Encoding]::UTF8.GetBytes($json))
        Write-Host "  OK  $Label" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL $Label -> $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ── Subject IDs ──
$sElevMaint = "bdfad935-7021-f111-8342-7ced8dceb433"  # Elevator Maintenance
$sElevEmerg = "cf0de039-7021-f111-8342-7ced8d18c8d7"  # Elevator Emergency
$sEscalator = "befad935-7021-f111-8342-7ced8dceb433"  # Escalator Service
$sDoor      = "4c658936-7021-f111-8341-6045bda80a72"  # Door Systems
$sModern    = "4d658936-7021-f111-8341-6045bda80a72"  # Modernization
$sBilling   = "a165fc35-7021-f111-8342-7c1e520a58a1"  # Billing and Contracts

# ── Product IDs ──
$pGen2    = "cb387e58-7021-f111-8342-7ced8d18c8d7"  # Otis Gen2 Elevator
$pSkyRise = "2f6dd356-7021-f111-8342-7ced8dceb433"  # Otis SkyRise Elevator
$pSwitch  = "326dd356-7021-f111-8342-7ced8dceb433"  # Otis GeN2 SWITCH
$pLink    = "6aeff558-7021-f111-8341-7ced8dceb26a"  # Otis Link Escalator
$pONE     = "d6324a5c-7021-f111-8342-7c1e52143136"  # Otis ONE IoT Platform
$pSvcFull = "a2a8d05c-7021-f111-8342-7ced8dceb433"  # Service Contract - Full
$pSvcComp = "e366ee5c-7021-f111-8341-6045bda80a72"  # Service Contract - Comprehensive
$pSvcBasic= "74eff558-7021-f111-8341-7ced8dceb26a"  # Service Contract - Basic

Write-Host "`n=== Linking Otis Cases to Products and Subjects ===" -ForegroundColor Cyan

# ── Entrapment / Emergency Cases → Elevator Emergency ──
Write-Host "`n-- Entrapment / Emergency --" -ForegroundColor Yellow
Link-Case "b1965788-241f-f111-8342-7ced8d18c8d7" $sElevEmerg $pGen2    "Entrapment - Riverside Elevator 3"
Link-Case "bfb12275-b420-f111-8342-7ced8d18c8d7" $sElevEmerg $pGen2    "Entrapment - Riverside Centre Elevator 3"
Link-Case "ffef6969-5a21-f111-8341-6045bda80a72" $sElevEmerg $pGen2    "Entrapment - Westfield Elevator 7"
Link-Case "77ae064d-5d21-f111-8342-7c1e520a58a1" $sElevEmerg $pSkyRise "Emergency - Trapped B2"

# ── Unit Out of Service → Elevator Emergency ──
Write-Host "`n-- Unit Out of Service --" -ForegroundColor Yellow
Link-Case "7bd09d51-5d21-f111-8341-7ced8dceb26a" $sElevEmerg $pSkyRise "Elevator 5 OOS - Maternity Ward"
Link-Case "3bb32e8f-241f-f111-8341-7ced8dd8e369" $sElevEmerg $pSkyRise "Elevator OOS - Canary Tower A"

# ── Door Issues → Door Systems ──
Write-Host "`n-- Door Issues --" -ForegroundColor Yellow
Link-Case "4f1623d9-241f-f111-8342-7c1e52143136" $sDoor $pGen2 "Door not closing - Marriott Lift 2"
Link-Case "2f9eec80-b420-f111-8341-6045bda80a72" $sDoor $pGen2 "Recurring Door - Canary Elev 12"

# ── Escalator Issues → Escalator Service ──
Write-Host "`n-- Escalator Issues --" -ForegroundColor Yellow
Link-Case "b3673a74-5a21-f111-8342-7c1e52143136" $sEscalator $pLink "Escalator Belt Adjustment - Westfield"
Link-Case "c888aa8f-241f-f111-8341-7c1e5218592b" $sEscalator $pLink "Escalator running rough - Westfield"

# ── Modernization → Modernization ──
Write-Host "`n-- Modernization --" -ForegroundColor Yellow
Link-Case "3b45bf87-b420-f111-8342-7c1e52143136" $sModern $pSkyRise "Modernization - The Shard Freight"

# ── Scheduled Maintenance → Elevator Maintenance ──
Write-Host "`n-- Scheduled Maintenance --" -ForegroundColor Yellow
Link-Case "d928d891-241f-f111-8341-7ced8d18ce4d" $sElevMaint $pSvcComp "Scheduled maintenance Q1 - Birmingham"
Link-Case "98d9e64e-5d21-f111-8342-7c1e52143136" $sElevMaint $pSvcFull "Scheduled quarterly - Elevators 1-4"

# ── Billing → Billing and Contracts ──
Write-Host "`n-- Billing --" -ForegroundColor Yellow
Link-Case "156cdb1d-b520-f111-8342-7c1e520a58a1" $sBilling $pSvcFull  "Billing Dispute - Marriott"
Link-Case "e377bcdb-241f-f111-8342-6045bdedc552" $sBilling $pSvcBasic "Billing question - Metro Office"

# ── Find and link Annual Safety Inspection ──
Write-Host "`n-- Safety Inspection --" -ForegroundColor Yellow
$safety = Invoke-RestMethod -Uri "$base/incidents?`$filter=contains(title,'Annual Safety')&`$select=incidentid,title" -Headers $headers
if ($safety.value.Count -gt 0) {
    Link-Case $safety.value[0].incidentid $sElevMaint $pSvcComp "Annual Safety Inspection - Westfield"
} else {
    Write-Host "  SKIP - Annual Safety Inspection case not found" -ForegroundColor DarkYellow
}

# ── Verify all cases ──
Write-Host "`n=== Verification ===" -ForegroundColor Cyan
$otis = Invoke-RestMethod -Uri "$base/incidents?`$filter=(contains(title,'Elevator') or contains(title,'Escalator') or contains(title,'Entrapment') or contains(title,'Emergency') or contains(title,'Billing') or contains(title,'Modernization') or contains(title,'maintenance') or contains(title,'Door not') or contains(title,'Recurring Door') or contains(title,'Annual Safety'))&`$select=title,ticketnumber&`$expand=productid(`$select=name),subjectid(`$select=title)&`$orderby=title" -Headers $headers

$otisCases = $otis.value | Where-Object { $_.productid.name -like "Otis*" }
Write-Host "`nOtis cases with products linked: $($otisCases.Count)" -ForegroundColor Cyan
foreach ($c in $otisCases) {
    $prodName = if ($c.productid.name) { $c.productid.name } else { "(none)" }
    $subjName = if ($c.subjectid.title) { $c.subjectid.title } else { "(none)" }
    Write-Host "  $($c.ticketnumber) | $($c.title)" -ForegroundColor White
    Write-Host "    Product: $prodName | Subject: $subjName" -ForegroundColor Gray
}

Write-Host "`nDone!" -ForegroundColor Green
