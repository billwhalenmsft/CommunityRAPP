<#
.SYNOPSIS
    Step 32 - Link Demo Cases to Customer Assets (Serial Numbers)
.DESCRIPTION
    Populates productserialnumber on demo cases so that the Equipment &
    Warranty screen auto-selects the specific unit the caller is phoning from.
    
    Mapping logic:
    - Case title + account -> equipment hint in demo-data.json -> serial number
    - The Otis Service Toolkit loader JS passes this serial to the Custom Page
    - Equipment screen reads segment 4 of Param("recordId") and auto-selects

    Also updates the Westfield hero case.

.EXAMPLE
    .\32-LinkCasesToAssets.ps1
#>

$ErrorActionPreference = "Stop"
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

# Import Dataverse helper (same directory)
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  32 - Link Demo Cases to Customer Assets" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

# ============================================================
# Case-to-Serial mapping
# Each demo case in demo-data.json has an 'equipment' hint.
# We resolve that to the actual serial number pattern from
# the account's equipment list.
#
# Format: {model_prefix}-{site_code}-{unit_number}
# Example: "Gen2 Life - Elevator 3" at Riverside -> G2L-RM-003
# ============================================================

$caseSerialMap = @(
    @{
        titleMatch   = "Entrapment - Passenger stuck in Elevator 3"
        serial       = "G2L-RM-003"
        description  = "Riverside Medical Centre - Gen2 Life Elevator #3 (hospital main tower)"
    },
    @{
        titleMatch   = "Elevator out of service - Tower A"
        serial       = "SKY-CW-012"
        description  = "Canary Wharf Tower - SkyRise Elevator #12 (Tower A, floor 25)"
    },
    @{
        titleMatch   = "Escalator running rough - Main entrance"
        serial       = "NCE-WL-001"
        description  = "Westfield London - NCE Escalator #1 (main entrance)"
    },
    @{
        titleMatch   = "Door not closing properly - Lift 2"
        serial       = "G2C-MH-002"
        description  = "Marriott Hotel Manchester - Gen2 Comfort Elevator #2 (guest lift, floor 6)"
    },
    # Hero case (Westfield entrapment)
    @{
        titleMatch   = "Entrapment - Westfield London Elevator 7"
        serial       = "GEN2-WL-007"
        description  = "Westfield London - Gen2 Comfort Elevator #7 (East Wing car park)"
    }
    # Note: "Scheduled maintenance" and "Billing question" cases are facility-level, no single unit
)

Write-Host ""
Write-StepHeader "1" "Update productserialnumber on demo cases"
Write-Host ""

$updated = 0
$skipped = 0
$notFound = 0

foreach ($mapping in $caseSerialMap) {
    $title = $mapping.titleMatch
    $serial = $mapping.serial
    $desc = $mapping.description

    Write-Host "  Looking for case: '$title'" -ForegroundColor White

    # Find the case - use startswith to handle both exact and variant titles
    $cases = Invoke-DataverseGet -EntitySet "incidents" `
        -Filter "startswith(title,'$($title.Substring(0, [Math]::Min(50, $title.Length)))')" `
        -Select "incidentid,title,productserialnumber" -Top 5

    if (-not $cases -or $cases.Count -eq 0) {
        Write-Host "    [NOT FOUND] No case matching '$title'" -ForegroundColor Yellow
        $notFound++
        continue
    }

    # Find exact or closest match
    $targetCase = $null
    foreach ($c in $cases) {
        if ($c.title -eq $title -or $c.title.StartsWith($title.Substring(0, 20))) {
            $targetCase = $c
            break
        }
    }
    if (-not $targetCase) { $targetCase = $cases[0] }

    $caseId = $targetCase.incidentid
    $currentSerial = $targetCase.productserialnumber

    if ($currentSerial -eq $serial) {
        Write-Host "    [SKIP] Already set to '$serial'" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    # Verify the asset exists
    $asset = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
        -Filter "msdyn_name eq '$serial'" `
        -Select "msdyn_customerassetid,msdyn_name" -Top 1

    if (-not $asset -or $asset.Count -eq 0) {
        Write-Host "    [WARN] Asset '$serial' not found in Customer Assets - setting serial anyway" -ForegroundColor Yellow
    } else {
        Write-Host "    [OK] Asset verified: $serial ($($asset[0].msdyn_customerassetid))" -ForegroundColor Green
    }

    # Update productserialnumber on the case
    Invoke-DataversePatch -EntitySet "incidents" -RecordId ([guid]$caseId) -Body @{
        productserialnumber = $serial
    }

    Write-Host "    [OK] Set productserialnumber = '$serial' on case '$($targetCase.title)'" -ForegroundColor Green
    Write-Host "         $desc" -ForegroundColor DarkGray
    $updated++
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Results: Updated=$updated  Skipped=$skipped  NotFound=$notFound" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# ============================================================
# Step 2: Verify - list all cases with serial numbers
# ============================================================
Write-Host ""
Write-StepHeader "2" "Verify - Cases with Serial Numbers"

$allCases = Invoke-DataverseGet -EntitySet "incidents" `
    -Filter "productserialnumber ne null" `
    -Select "title,productserialnumber" -Top 20

if ($allCases -and $allCases.Count -gt 0) {
    foreach ($c in $allCases) {
        Write-Host "  $($c.productserialnumber) -> $($c.title)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "  Total cases with serial numbers: $($allCases.Count)" -ForegroundColor Green
} else {
    Write-Host "  No cases found with serial numbers set" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done! Cases are now linked to specific units via productserialnumber." -ForegroundColor Green
Write-Host "The Service Toolkit loader will pass these serials to the Equipment screen." -ForegroundColor DarkGray
Write-Host ""
