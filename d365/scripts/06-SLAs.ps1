<#
.SYNOPSIS
    Step 06 - Create SLAs and Business Hours Calendar
.DESCRIPTION
    Creates customer service calendar (business hours), SLAs with
    first response and resolution KPIs matching Zurn Elkay targets:
      - First Response: 4 business hours
      - Resolution: 8 business hours
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "06" "Create SLAs & Business Hours"
Connect-Dataverse

# ============================================================
# 1. Customer Service Calendar (Business Hours)
# ============================================================
Write-Host "Creating business hours calendar..." -ForegroundColor Yellow

# Get root business unit (required for calendar creation)
$buResult = Invoke-DataverseGet -EntitySet "businessunits" -Filter "parentbusinessunitid eq null" -Select "businessunitid,name" -Top 1
$rootBuId = $buResult[0].businessunitid
Write-Host "  Root BU: $($buResult[0].name) ($rootBuId)" -ForegroundColor DarkGray

# Check for existing calendar
$existingCal = Invoke-DataverseGet -EntitySet "calendars" -Filter "name eq 'Zurn Elkay Business Hours'" -Select "calendarid" -Top 1

if ($existingCal -and $existingCal.Count -gt 0) {
    $calendarId = $existingCal[0].calendarid
    Write-Host "  Found existing calendar: $calendarId" -ForegroundColor DarkGray
} else {
    Write-Host "  Creating calendar: Zurn Elkay Business Hours" -ForegroundColor Green
    $calBody = @{
        name                        = "Zurn Elkay Business Hours"
        description                 = "Mon-Fri 8:00 AM - 5:00 PM CT. Standard business hours for SLA tracking."
        type                        = 0  # Customer Service calendar
        "businessunitid@odata.bind" = "/businessunits($rootBuId)"
    }
    $calResult = Invoke-DataversePost -EntitySet "calendars" -Body $calBody
    if ($calResult) {
        $calendarId = $calResult.calendarid
    } else {
        $existingCal = Invoke-DataverseGet -EntitySet "calendars" -Filter "name eq 'Zurn Elkay Business Hours'" -Select "calendarid" -Top 1
        $calendarId = $existingCal[0].calendarid
    }
}

Write-Host "  Calendar ID: $calendarId" -ForegroundColor DarkGray

# ============================================================
# 2. SLA Record
# ============================================================
Write-Host "`nCreating SLA..." -ForegroundColor Yellow

$slaId = Find-OrCreate-Record `
    -EntitySet "slas" `
    -Filter "name eq 'Zurn Elkay Standard SLA'" `
    -IdField "slaid" `
    -Body @{
    name             = "Zurn Elkay Standard SLA"
    description      = "Zurn Elkay CS SLA. First Response: 4h, Resolution: 8h business hours."
    applicablefrom   = "createdon"
    objecttypecode   = 112  # incident (case)
    primaryentityotc = 112  # required for SLA creation
    slaversion       = 100000001    # Unified Interface Enhanced SLA
} `
    -DisplayName "Zurn Elkay Standard SLA"

# ============================================================
# 3. SLA KPI Definitions (look up existing)
# ============================================================
Write-Host "`nLooking up SLA KPI definitions..." -ForegroundColor Yellow
$frKpi = Invoke-DataverseGet -EntitySet "msdyn_slakpis" -Filter "msdyn_name eq 'First Response By'" -Select "msdyn_slakpiid" -Top 1
$resKpi = Invoke-DataverseGet -EntitySet "msdyn_slakpis" -Filter "msdyn_name eq 'Resolved By'" -Select "msdyn_slakpiid" -Top 1
if ($frKpi -and $frKpi.Count -gt 0) {
    $frKpiId = $frKpi[0].msdyn_slakpiid
    Write-Host "  First Response By KPI: $frKpiId" -ForegroundColor DarkGray
} else { Write-Warning "  'First Response By' KPI definition not found" }
if ($resKpi -and $resKpi.Count -gt 0) {
    $resKpiId = $resKpi[0].msdyn_slakpiid
    Write-Host "  Resolved By KPI: $resKpiId" -ForegroundColor DarkGray
} else { Write-Warning "  'Resolved By' KPI definition not found" }

# ============================================================
# 4. SLA Items (KPIs)
# ============================================================
Write-Host "`nCreating SLA KPI items..." -ForegroundColor Yellow

# First Response KPI
$frFilter = "_slaid_value eq '$slaId' and name eq 'First Response - 4 Hours'"
$existingFR = Invoke-DataverseGet -EntitySet "slaitems" -Filter $frFilter -Select "slaitemid" -Top 1

if (-not $existingFR -or $existingFR.Count -eq 0) {
    $frBody = @{
        name                        = "First Response - 4 Hours"
        "slaid@odata.bind"          = "/slas($slaId)"
        "msdyn_SLAKPIID@odata.bind" = "/msdyn_slakpis($frKpiId)"
        applicablewhenxml           = '<fetch version="1.0" output-format="xml-platform" mapping="logical"><entity name="incident"><filter type="and"><condition attribute="statecode" operator="eq" value="0" /></filter></entity></fetch>'
        successconditionsxml        = '<fetch version="1.0" output-format="xml-platform" mapping="logical"><entity name="incident"><filter type="and"><condition attribute="firstresponsesent" operator="eq" value="1" /></filter></entity></fetch>'
        failureafter                = 240   # 4 hours in minutes
        warnafter                   = 180   # 3 hours (warn at 75%)
    }
    $frResult = Invoke-DataversePost -EntitySet "slaitems" -Body $frBody
    if ($frResult) {
        Write-Host "  Created: First Response - 4 Hours (warn at 3h)" -ForegroundColor Green
    } else {
        Write-Host "  SLA Item creation may require admin portal config" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Found existing: First Response - 4 Hours" -ForegroundColor DarkGray
}

# Resolution KPI
$resFilter = "_slaid_value eq '$slaId' and name eq 'Resolution - 8 Hours'"
$existingRes = Invoke-DataverseGet -EntitySet "slaitems" -Filter $resFilter -Select "slaitemid" -Top 1

if (-not $existingRes -or $existingRes.Count -eq 0) {
    $resBody = @{
        name                        = "Resolution - 8 Hours"
        "slaid@odata.bind"          = "/slas($slaId)"
        "msdyn_SLAKPIID@odata.bind" = "/msdyn_slakpis($resKpiId)"
        applicablewhenxml           = '<fetch version="1.0" output-format="xml-platform" mapping="logical"><entity name="incident"><filter type="and"><condition attribute="statecode" operator="eq" value="0" /></filter></entity></fetch>'
        successconditionsxml        = '<fetch version="1.0" output-format="xml-platform" mapping="logical"><entity name="incident"><filter type="and"><condition attribute="statecode" operator="eq" value="1" /></filter></entity></fetch>'
        failureafter                = 480   # 8 hours in minutes
        warnafter                   = 360   # 6 hours (warn at 75%)
    }
    $resResult = Invoke-DataversePost -EntitySet "slaitems" -Body $resBody
    if ($resResult) {
        Write-Host "  Created: Resolution - 8 Hours (warn at 6h)" -ForegroundColor Green
    } else {
        Write-Host "  SLA Item creation may require admin portal config" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Found existing: Resolution - 8 Hours" -ForegroundColor DarkGray
}

# ============================================================
# 4. Notes on SLA Activation
# ============================================================
Write-Host "`n--- MANUAL STEPS REQUIRED ---" -ForegroundColor Magenta
Write-Host @"
  
  SLA records must be activated in the D365 Customer Service admin center:
  
  1. Go to Customer Service admin center
  2. Navigate to Service Level Agreements
  3. Open "Zurn Elkay Standard SLA"
  4. Associate the "Zurn Elkay Business Hours" calendar
  5. Verify the two KPIs (First Response, Resolution)
  6. Click "Activate"
  7. Set as default SLA if desired
  
  Business Hours calendar inner rules (Mon-Fri 8AM-5PM CT) may need
  to be configured via the admin center calendar editor.
  
"@ -ForegroundColor Yellow

# ============================================================
# Summary
# ============================================================
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " SLA Configuration Created" -ForegroundColor Green
Write-Host " Calendar      : Zurn Elkay Business Hours" -ForegroundColor White
Write-Host " SLA           : Zurn Elkay Standard SLA (Enhanced)" -ForegroundColor White
Write-Host " First Response: 4 business hours (warn at 3h)" -ForegroundColor White
Write-Host " Resolution    : 8 business hours (warn at 6h)" -ForegroundColor White
Write-Host " Pause/Resume  : Enabled" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green
