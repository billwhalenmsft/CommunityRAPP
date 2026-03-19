<#
.SYNOPSIS
    Add Otis Incident Types to D365 Field Service
.DESCRIPTION
    Creates Incident Type records for Otis demo scenarios.
    Also updates Case Type option set if needed.

.EXAMPLE
    .\Add-OtisIncidentTypes.ps1
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Script is at customers/otis/d365/scripts - go up 4 levels to repo root
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir)))

# Import Dataverse helper
$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) {
    Import-Module $helperPath -Force
} else {
    throw "DataverseHelper.psm1 not found at: $helperPath"
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Otis EMEA CCaaS Demo - Add Incident Types" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Connect to Dataverse
Connect-Dataverse

# ============================================================
# Otis Incident Types to Create
# ============================================================
$incidentTypes = @(
    @{
        Name = "Entrapment"
        Description = "Passenger trapped in elevator - CRITICAL priority"
        DefaultDuration = 30  # minutes
    },
    @{
        Name = "Unit Out of Service"
        Description = "Elevator non-operational, requires technician"
        DefaultDuration = 120
    },
    @{
        Name = "Door Issue"
        Description = "Door alignment, closing, or sensor problems"
        DefaultDuration = 180
    },
    @{
        Name = "Noise/Vibration Complaint"
        Description = "Unusual sounds or vibrations during operation"
        DefaultDuration = 240
    },
    @{
        Name = "Scheduled Maintenance"
        Description = "Regular preventive maintenance visit"
        DefaultDuration = 480
    },
    @{
        Name = "Billing Inquiry"
        Description = "Questions about invoices or charges"
        DefaultDuration = 480
    },
    @{
        Name = "Contract Question"
        Description = "Service contract coverage or renewal questions"
        DefaultDuration = 480
    },
    @{
        Name = "Modernization Request"
        Description = "Request for elevator upgrade or modernization quote"
        DefaultDuration = 1440
    }
)

Write-Host "`n>>> Creating Incident Types (msdyn_incidenttype)..." -ForegroundColor Green

foreach ($type in $incidentTypes) {
    Write-Host "  Creating: $($type.Name)" -ForegroundColor Gray
    
    $typeData = @{
        msdyn_name = $type.Name
        msdyn_description = $type.Description
        msdyn_estimatedduration = $type.DefaultDuration
    }
    
    try {
        $escapedName = $type.Name -replace "'", "''"
        $typeId = Find-OrCreate-Record `
            -EntitySet "msdyn_incidenttypes" `
            -Filter "msdyn_name eq '$escapedName'" `
            -IdField "msdyn_incidenttypeid" `
            -Body $typeData `
            -DisplayName $type.Name
        
        Write-Host "    ID: $typeId" -ForegroundColor DarkGray
    }
    catch {
        Write-Warning "    Failed: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Incident Types Created!" -ForegroundColor Green
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Open Power Apps > Tables > Case > Columns" -ForegroundColor White
Write-Host "  2. Find 'Primary Incident Type' (msdyn_primaryincidenttype)" -ForegroundColor White
Write-Host "  3. It should now show your new incident types in lookups" -ForegroundColor White
Write-Host ""
Write-Host "  For the Enhanced Full Case Form:" -ForegroundColor Yellow
Write-Host "  1. Open Power Apps > Tables > Case > Forms" -ForegroundColor White
Write-Host "  2. Edit 'Enhanced full case form'" -ForegroundColor White
Write-Host "  3. Drag 'Primary Incident Type' field to the form" -ForegroundColor White
Write-Host "  4. Save and Publish" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green
