<#
.SYNOPSIS
    Fix hero case serial numbers — patches productserialnumber on existing hero cases
    so the Equipment & Warranty screen can match assets to cases.

.DESCRIPTION
    Reads hero-cases.json, finds each case in Dataverse by title, and patches
    the productserialnumber field. Also verifies that matching customer assets exist.

.EXAMPLE
    .\Fix-HeroCaseSerials.ps1
    .\Fix-HeroCaseSerials.ps1 -DryRun
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) { Import-Module $helperPath -Force } else { throw "DataverseHelper.psm1 not found: $helperPath" }

$heroCasesPath = Join-Path $scriptDir "data\hero-cases.json"
$heroCases     = Get-Content $heroCasesPath | ConvertFrom-Json

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Fix Hero Case Serials — Navico" -ForegroundColor Cyan
Write-Host "  Mode: $(if ($DryRun) {'DRY RUN'} else {'LIVE'})" -ForegroundColor $(if ($DryRun) {'Yellow'} else {'Green'})
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

$fixed = 0; $alreadyOk = 0; $notFound = 0; $assetMissing = 0

foreach ($case in $heroCases.heroCases) {
    if (-not $case.serialNumber) {
        Write-Host "  SKIP (no serial): $($case.title)" -ForegroundColor DarkGray
        continue
    }

    $serial = $case.serialNumber
    $esc    = $case.title -replace "'", "''"

    # Find the case
    $caseRec = Invoke-DataverseGet -EntitySet "incidents" `
        -Filter "title eq '$esc'" `
        -Select "incidentid,productserialnumber,title" -Top 1

    if (-not $caseRec -or $caseRec.Count -eq 0) {
        Write-Host "  NOT FOUND: $($case.title)" -ForegroundColor Red
        $notFound++
        continue
    }

    $caseId      = $caseRec[0].incidentid
    $currentSN   = $caseRec[0].productserialnumber

    # Check if already correct
    if ($currentSN -eq $serial) {
        Write-Host "  OK: $($case.title) → $serial" -ForegroundColor DarkGreen
        $alreadyOk++
    } else {
        Write-Host "  PATCH: $($case.title)" -ForegroundColor Yellow
        Write-Host "    Current : $($currentSN ?? '(blank)')" -ForegroundColor DarkGray
        Write-Host "    Target  : $serial" -ForegroundColor Green

        if (-not $DryRun) {
            Invoke-DataversePatch -EntitySet "incidents" -RecordId ([guid]$caseId) -Body @{
                productserialnumber = $serial
            }
            Write-Host "    ✓ Patched" -ForegroundColor Green
        } else {
            Write-Host "    (dry run — no change)" -ForegroundColor Yellow
        }
        $fixed++
    }

    # Verify matching customer asset exists
    $escapedSerial = $serial -replace "'", "''"
    $asset = Invoke-DataverseGet -EntitySet "msdyn_customerassets" `
        -Filter "msdyn_name eq '$escapedSerial'" `
        -Select "msdyn_customerassetid,msdyn_name,msdyn_assettag" -Top 1

    if ($asset -and $asset.Count -gt 0) {
        Write-Host "    Asset OK: $($asset[0].msdyn_name) ($($asset[0].msdyn_assettag))" -ForegroundColor DarkGreen
    } else {
        Write-Host "    ⚠ NO MATCHING ASSET for serial '$serial'" -ForegroundColor Red
        Write-Host "      The Equipment screen won't find this unit until the asset is created." -ForegroundColor DarkRed
        $assetMissing++
    }

    Write-Host ""
}

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "    Patched       : $fixed" -ForegroundColor $(if ($fixed -gt 0) {'Green'} else {'Gray'})
Write-Host "    Already OK    : $alreadyOk" -ForegroundColor Gray
Write-Host "    Case not found: $notFound" -ForegroundColor $(if ($notFound -gt 0) {'Red'} else {'Gray'})
Write-Host "    Asset missing : $assetMissing" -ForegroundColor $(if ($assetMissing -gt 0) {'Red'} else {'Gray'})
Write-Host ("=" * 70) -ForegroundColor Cyan
