<#
.SYNOPSIS
    Links Otis KB articles to their related cases via knowledgearticleincident.
#>

Import-Module "$PSScriptRoot\DataverseHelper.psm1" -Force
Connect-Dataverse

$headers = Get-DataverseHeaders
$base = Get-DataverseApiUrl
$postH = @{
    "Authorization" = $headers["Authorization"]
    "Content-Type"  = "application/json; charset=utf-8"
    "OData-Version" = "4.0"
}

function Link-KB {
    param(
        [string]$CaseId,
        [string]$KBId,
        [string]$Label
    )
    $body = @{
        "knowledgearticleid@odata.bind" = "/knowledgearticles($KBId)"
        "incidentid@odata.bind"         = "/incidents($CaseId)"
    } | ConvertTo-Json
    try {
        Invoke-WebRequest -Uri "$base/knowledgearticleincidents" -Headers $postH -Method Post -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -UseBasicParsing | Out-Null
        Write-Host "  OK  $Label" -ForegroundColor Green
    } catch {
        $err = $_.Exception.Message
        if ($err -match "duplicate") {
            Write-Host "  SKIP $Label (already linked)" -ForegroundColor DarkYellow
        } else {
            Write-Host "  FAIL $Label -> $err" -ForegroundColor Red
        }
    }
}

# ── KB Article IDs (using Draft/content version, state=0) ──
$kbEntrapment   = "5728358a-b520-f111-8342-7c1e52143136"  # Emergency Entrapment Response Protocol (KB-001247)
$kbHealthcare   = "2faf5097-b520-f111-8342-7ced8d18c8d7"  # Healthcare Facility Elevator Compliance (KB-002156)
$kbOtisONE      = "3177e791-b420-f111-8341-7ced8dceb26a"  # Otis ONE IoT Monitoring Package (KB-003145)
$kbSafety       = "e17f2ca0-6e21-f111-8341-7ced8dceb26a"  # Emergency Safety Incident Response (KA-01240)
$kbUnitOOS      = "cac6c79e-6e21-f111-8342-7ced8dceb433"  # Unit Out of Service Troubleshooting (KA-01239)
$kbDoor         = "5dcf14bf-6e21-f111-8341-7ced8dceb26a"  # Door Issue Diagnostic Guide (KA-01244)
$kbEscalator    = "2e1adec8-6e21-f111-8341-6045bda80a72"  # Escalator Issue Guide (KA-01245)
$kbNoise        = "544aede0-6e21-f111-8342-7c1e52143136"  # Noise and Vibration Diagnostic (KA-01248)
$kbMaintenance  = "af2f6ae8-6e21-f111-8342-7ced8d18c8d7"  # Scheduled Maintenance SLA Reference (KA-01249)
$kbModernization= "d1928dff-6e21-f111-8342-7c1e520a58a1"  # Elevator Modernization Assessment (KA-01252)
$kbBilling      = "5e284407-6f21-f111-8342-7c1e52143136"  # Billing Inquiries and Contract FAQ (KA-01253)

# ── Case IDs ──
# Entrapment cases
$cEntrapRiverside     = "b1965788-241f-f111-8342-7ced8d18c8d7"
$cEntrapRiversideCtr  = "bfb12275-b420-f111-8342-7ced8d18c8d7"
$cEntrapWestfield     = "ffef6969-5a21-f111-8341-6045bda80a72"
$cEmergencyB2         = "77ae064d-5d21-f111-8342-7c1e520a58a1"
# OOS cases
$cElev5OOS            = "7bd09d51-5d21-f111-8341-7ced8dceb26a"
$cElevOOSCanary       = "3bb32e8f-241f-f111-8341-7ced8dd8e369"
# Door cases
$cDoorLift2           = "4f1623d9-241f-f111-8342-7c1e52143136"
$cDoorCanary12        = "2f9eec80-b420-f111-8341-6045bda80a72"
# Escalator cases
$cEscBelt             = "b3673a74-5a21-f111-8342-7c1e52143136"
$cEscRough            = "c888aa8f-241f-f111-8341-7c1e5218592b"
# Modernization
$cModernShard         = "3b45bf87-b420-f111-8342-7c1e52143136"
# Maintenance
$cMaintQ1             = "d928d891-241f-f111-8341-7ced8d18ce4d"
$cMaintQuarterly      = "98d9e64e-5d21-f111-8342-7c1e52143136"
# Billing
$cBillingMarriott     = "156cdb1d-b520-f111-8342-7c1e520a58a1"
$cBillingMetro        = "e377bcdb-241f-f111-8342-6045bdedc552"

Write-Host "`n=== Linking KB Articles to Otis Cases ===" -ForegroundColor Cyan

# ── Entrapment cases get: Entrapment Protocol + Healthcare Compliance ──
Write-Host "`n-- Entrapment Cases --" -ForegroundColor Yellow
Link-KB $cEntrapRiverside    $kbEntrapment "Entrapment-Riverside -> Entrapment Protocol"
Link-KB $cEntrapRiverside    $kbHealthcare "Entrapment-Riverside -> Healthcare Compliance"
Link-KB $cEntrapRiversideCtr $kbEntrapment "Entrapment-RiversideCtr -> Entrapment Protocol"
Link-KB $cEntrapRiversideCtr $kbHealthcare "Entrapment-RiversideCtr -> Healthcare Compliance"
Link-KB $cEntrapWestfield    $kbEntrapment "Entrapment-Westfield -> Entrapment Protocol"

# ── Emergency gets: Entrapment Protocol + Safety Guide ──
Write-Host "`n-- Emergency Cases --" -ForegroundColor Yellow
Link-KB $cEmergencyB2        $kbEntrapment "Emergency-B2 -> Entrapment Protocol"
Link-KB $cEmergencyB2        $kbSafety     "Emergency-B2 -> Safety Guide"

# ── OOS cases get: Unit OOS Troubleshooting + Otis ONE IoT ──
Write-Host "`n-- Unit OOS Cases --" -ForegroundColor Yellow
Link-KB $cElev5OOS           $kbUnitOOS    "Elev5-OOS -> Unit OOS Guide"
Link-KB $cElev5OOS           $kbOtisONE    "Elev5-OOS -> Otis ONE IoT"
Link-KB $cElev5OOS           $kbHealthcare "Elev5-OOS -> Healthcare Compliance"
Link-KB $cElevOOSCanary      $kbUnitOOS    "ElevOOS-Canary -> Unit OOS Guide"
Link-KB $cElevOOSCanary      $kbOtisONE    "ElevOOS-Canary -> Otis ONE IoT"

# ── Door cases get: Door Diagnostic Guide ──
Write-Host "`n-- Door Cases --" -ForegroundColor Yellow
Link-KB $cDoorLift2          $kbDoor       "Door-Lift2 -> Door Diagnostic"
Link-KB $cDoorCanary12       $kbDoor       "DoorCanary12 -> Door Diagnostic"

# ── Escalator cases get: Escalator Guide ──
Write-Host "`n-- Escalator Cases --" -ForegroundColor Yellow
Link-KB $cEscBelt            $kbEscalator  "EscBelt-Westfield -> Escalator Guide"
Link-KB $cEscRough           $kbEscalator  "EscRough -> Escalator Guide"

# ── Modernization get: Modernization Guide + Otis ONE ──
Write-Host "`n-- Modernization --" -ForegroundColor Yellow
Link-KB $cModernShard        $kbModernization "Modern-Shard -> Modernization Guide"
Link-KB $cModernShard        $kbOtisONE       "Modern-Shard -> Otis ONE IoT"

# ── Maintenance get: Maintenance SLA Guide ──
Write-Host "`n-- Maintenance Cases --" -ForegroundColor Yellow
Link-KB $cMaintQ1            $kbMaintenance "MaintQ1 -> Maintenance SLA Guide"
Link-KB $cMaintQuarterly     $kbMaintenance "MaintQuarterly -> Maintenance SLA Guide"

# ── Billing get: Billing FAQ ──
Write-Host "`n-- Billing Cases --" -ForegroundColor Yellow
Link-KB $cBillingMarriott    $kbBilling    "BillingMarriott -> Billing FAQ"
Link-KB $cBillingMetro       $kbBilling    "BillingMetro -> Billing FAQ"

# ── Safety inspection ──
Write-Host "`n-- Safety Inspection --" -ForegroundColor Yellow
$safety = Invoke-RestMethod -Uri "$base/incidents?`$filter=contains(title,'Annual Safety')&`$select=incidentid,title" -Headers $headers
if ($safety.value.Count -gt 0) {
    Link-KB $safety.value[0].incidentid $kbMaintenance "SafetyInspection -> Maintenance SLA Guide"
    Link-KB $safety.value[0].incidentid $kbSafety      "SafetyInspection -> Safety Guide"
}

Write-Host "`n=== KB Linking Complete ===" -ForegroundColor Green
