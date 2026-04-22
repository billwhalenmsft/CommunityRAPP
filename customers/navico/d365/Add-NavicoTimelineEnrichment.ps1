#Requires -Version 7.0
<#
.SYNOPSIS
    Adds enriched timeline activities to Navico demo cases.
    Safe to re-run — uses Find-OrCreate-Record (idempotent, deduplicates on subject+caseId).

.DESCRIPTION
    Reads all case activities from demo-data.json and seeds them into the live Dataverse org.
    Only adds missing activities — will not create duplicates.

.EXAMPLE
    .\Add-NavicoTimelineEnrichment.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Paths ──────────────────────────────────────────────────────────────────────
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))
$configDir   = Join-Path $scriptDir "config"
$demoDataPath = Join-Path $configDir "demo-data.json"
$helperPath  = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"

if (-not (Test-Path $helperPath))  { throw "DataverseHelper.psm1 not found at $helperPath" }
if (-not (Test-Path $demoDataPath)) { throw "demo-data.json not found at $demoDataPath" }

Import-Module $helperPath -Force

# ── Connect ───────────────────────────────────────────────────────────────────
Write-Host "`n=== Navico Timeline Enrichment ===" -ForegroundColor Cyan
Connect-Dataverse

# ── Load data ─────────────────────────────────────────────────────────────────
$demoData = Get-Content $demoDataPath -Raw | ConvertFrom-Json
$cases    = $demoData.demoCases.cases | Where-Object { $_.PSObject.Properties['activities'] -and $_.activities.Count -gt 0 }

Write-Host "Cases with activities to seed: $($cases.Count)" -ForegroundColor Cyan
$baseTime = (Get-Date).ToUniversalTime()

foreach ($case in $cases) {
    Write-Host "`n--- $($case.title)" -ForegroundColor Yellow

    # Look up the case by title
    $esc = $case.title -replace "'", "''"
    $caseRecords = Invoke-DataverseGet -EntitySet "incidents" `
        -Filter "title eq '$esc'" -Select "incidentid,title" -Top 1

    if (-not $caseRecords -or $caseRecords.Count -eq 0) {
        Write-Warning "  Case not found in Dataverse — skipping: $($case.title)"
        continue
    }

    $caseId = $caseRecords[0].incidentid
    Write-Host "  Case ID: $caseId" -ForegroundColor DarkGray

    foreach ($activity in $case.activities) {
        $actTime    = $baseTime.AddHours($activity.createdRelativeHours)
        $actTimeStr = $actTime.ToString("yyyy-MM-ddTHH:mm:ssZ")

        switch ($activity.type) {
            "note" {
                try {
                    $noteBody = @{
                        subject   = $activity.subject
                        notetext  = $activity.description
                        "objectid_incident@odata.bind" = "/incidents($caseId)"
                    }
                    Find-OrCreate-Record -EntitySet "annotations" `
                        -Filter "subject eq '$($activity.subject -replace "'","''")' and _objectid_value eq '$caseId'" `
                        -IdField "annotationid" -Body $noteBody -DisplayName $activity.subject | Out-Null
                    Write-Host "    [Note] $($activity.subject)" -ForegroundColor DarkGray
                } catch { Write-Warning "    Note skipped: $($_.Exception.Message)" }
            }
            "email" {
                try {
                    $isInbound = $activity.direction -eq "Inbound"
                    $emailBody = @{
                        subject       = $activity.subject
                        description   = $activity.description
                        directioncode = -not $isInbound
                        actualend     = $actTimeStr
                        "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                    }
                    Find-OrCreate-Record -EntitySet "emails" `
                        -Filter "subject eq '$($activity.subject -replace "'","''")' and _regardingobjectid_value eq '$caseId'" `
                        -IdField "activityid" -Body $emailBody -DisplayName $activity.subject | Out-Null
                    $dir = if ($isInbound) { "Inbound" } else { "Outbound" }
                    Write-Host "    [Email/$dir] $($activity.subject)" -ForegroundColor DarkGray
                } catch { Write-Warning "    Email skipped: $($_.Exception.Message)" }
            }
            "phonecall" {
                try {
                    $phoneBody = @{
                        subject       = $activity.subject
                        description   = $activity.description
                        directioncode = ($activity.direction -ne "Inbound")
                        actualend     = $actTimeStr
                        "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                    }
                    Find-OrCreate-Record -EntitySet "phonecalls" `
                        -Filter "subject eq '$($activity.subject -replace "'","''")' and _regardingobjectid_value eq '$caseId'" `
                        -IdField "activityid" -Body $phoneBody -DisplayName $activity.subject | Out-Null
                    $dir = if ($activity.direction -eq "Inbound") { "Inbound" } else { "Outbound" }
                    Write-Host "    [Call/$dir] $($activity.subject)" -ForegroundColor DarkGray
                } catch { Write-Warning "    Phone call skipped: $($_.Exception.Message)" }
            }
        }
    }

    Write-Host "  Done: $($case.activities.Count) activities processed" -ForegroundColor Green
}

Write-Host "`n=== Timeline enrichment complete ===" -ForegroundColor Cyan
