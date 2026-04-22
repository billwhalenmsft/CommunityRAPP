<#
.SYNOPSIS
    ABC Supply Savage Branch — Master Demo Build Orchestrator

.DESCRIPTION
    Runs all ABC Supply provisioning scripts in the correct dependency order.

    PHASE 0 — Field Service Config: Incident Types, Inspection Templates,
                                     Work Order Types, Territories, Characteristics
    PHASE 1 — Foundation:  Accounts → Contacts → Price List → Products
    PHASE 2 — Rich Data:   Customer Assets → Entitlements → KB Articles + Quick Responses
    PHASE 3 — Cases:       Base Cases → Hero Cases (LAST — needs all above)
    PHASE 4 — Post-Case:   Tier Logic → Verify Contacts

.PARAMETER Phase
    All | FSConfig | Foundation | RichData | Cases | PostCase

.EXAMPLE
    .\Run-ABCSupplyDemoSetup.ps1              # Full build
    .\Run-ABCSupplyDemoSetup.ps1 -Phase Cases # Re-run cases only
    .\Run-ABCSupplyDemoSetup.ps1 -Phase Foundation
#>

[CmdletBinding()]
param(
    [ValidateSet("All","FSConfig","Foundation","RichData","Cases","PostCase")]
    [string]$Phase = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$CustomerName = "ABC Supply Savage Branch"

function Run-Step {
    param([string]$Label, [string]$Script, [string]$Action = "")
    $scriptPath = Join-Path $scriptDir $Script
    Write-Host ""
    Write-Host ("─" * 60) -ForegroundColor DarkGray
    Write-Host "  ▶ $Label" -ForegroundColor Cyan
    Write-Host ("─" * 60) -ForegroundColor DarkGray

    if (-not (Test-Path $scriptPath)) {
        Write-Warning "  Script not found: $scriptPath — skipping"
        return
    }
    if ($Action) { & $scriptPath -Action $Action }
    else         { & $scriptPath }
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  $CustomerName D365 CS + FS DEMO — MASTER BUILD" -ForegroundColor Green
Write-Host "  Phase: $Phase" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green

# ── PHASE 0: FIELD SERVICE CONFIG ─────────────────────────────
if ($Phase -in "All","FSConfig") {
    Write-Host "`n  ═══ PHASE 0: Field Service Configuration ═══" -ForegroundColor Yellow
    Run-Step "0a. Incident Types"              "Provision-ABCSupplyFieldService.ps1" "IncidentTypes"
    Run-Step "0b. Inspection Templates"        "Provision-ABCSupplyFieldService.ps1" "InspectionTemplates"
    Run-Step "0c. Work Order Types"            "Provision-ABCSupplyFieldService.ps1" "WorkOrderTypes"
    Run-Step "0d. Service Territories"         "Provision-ABCSupplyFieldService.ps1" "Territories"
    Run-Step "0e. Tech Characteristics/Skills" "Provision-ABCSupplyFieldService.ps1" "Characteristics"
    Run-Step "0f. Service Task Types"          "Provision-ABCSupplyFieldService.ps1" "ServiceTasks"
    Run-Step "0g. Bookable Resources (Techs)"  "Provision-ABCSupplyFieldService.ps1" "Resources"
}

# ── PHASE 1: FOUNDATION ────────────────────────────────────────
if ($Phase -in "All","Foundation") {
    Write-Host "`n  ═══ PHASE 1: Foundation ═══" -ForegroundColor Yellow
    Run-Step "1. Accounts"                      "Provision-ABCSupplyDemo.ps1"     "Accounts"
    Run-Step "2. Contacts"                      "Provision-ABCSupplyDemo.ps1"     "Contacts"
    Run-Step "3. Price Lists + Unit Group"      "Provision-ABCSupplyExtended.ps1" "PriceList"
    Run-Step "4. Full Product Catalog"          "Provision-ABCSupplyExtended.ps1" "Products"
}

# ── PHASE 2: RICH DATA ─────────────────────────────────────────
if ($Phase -in "All","RichData") {
    Write-Host "`n  ═══ PHASE 2: Rich Data ═══" -ForegroundColor Yellow
    Run-Step "5. Customer Assets (serials)"     "Provision-ABCSupplyExtended.ps1"  "CustomerAssets"
    Run-Step "6. Entitlements (tier SLAs)"      "Provision-ABCSupplyExtended.ps1"  "Entitlements"
    Run-Step "7. KB Articles + Quick Responses" "Provision-ABCSupplyHeroCases.ps1" "KBAndResponses"
}

# ── PHASE 3: CASES ─────────────────────────────────────────────
if ($Phase -in "All","Cases") {
    Write-Host "`n  ═══ PHASE 3: Cases (runs AFTER all data is in place) ═══" -ForegroundColor Yellow
    Run-Step "8. Base Demo Cases"               "Provision-ABCSupplyDemo.ps1"      "Cases"
    Run-Step "9. Hero Cases (rich timelines)"   "Provision-ABCSupplyHeroCases.ps1" "HeroCases"
    Run-Step "10. FS Work Orders (Schedule Bd)" "Provision-ABCSupplyFieldService.ps1" "WorkOrders"
}

# ── PHASE 4: POST-CASE ─────────────────────────────────────────
if ($Phase -in "All","PostCase") {
    Write-Host "`n  ═══ PHASE 4: Post-Case Enrichment ═══" -ForegroundColor Yellow
    Run-Step "10. Tier Logic (case priority)"   "Provision-ABCSupplyExtended.ps1"  "TierLogic"
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  BUILD COMPLETE — $CustomerName" -ForegroundColor Green
Write-Host ""
Write-Host "  MANUAL STEPS STILL REQUIRED:" -ForegroundColor Yellow
Write-Host "   [Field Service]" -ForegroundColor Cyan
Write-Host "   1. Publish Inspection Templates:" -ForegroundColor White
Write-Host "      Field Service Settings → Inspection Templates → select each → Publish" -ForegroundColor DarkGray
Write-Host "   2. Create Bookable Resources for Derek Olson, Sam Rivera, Chris Paulson:" -ForegroundColor White
Write-Host "      Field Service → Resources → New (type: User) → assign territory + skills" -ForegroundColor DarkGray
Write-Host "   3. Set working hours for each resource (M-F 7:30am-5pm)" -ForegroundColor White
Write-Host "   4. Verify Schedule Board shows resources + WOs in unscheduled queue" -ForegroundColor White
Write-Host "   [Customer Service]" -ForegroundColor Cyan
Write-Host "   5. Publish KB articles:" -ForegroundColor White
Write-Host "      Customer Service Hub → Knowledge Articles → select each → Publish" -ForegroundColor DarkGray
Write-Host "   6. Configure telephony / CTI phone number in Omnichannel Admin Center" -ForegroundColor White
Write-Host "   7. Configure SMS channel (Azure Communication Services or carrier)" -ForegroundColor White
Write-Host "   8. Verify Copilot Agent Assist enabled:" -ForegroundColor White
Write-Host "      CS Admin Center → Copilot → Agent Assist → Enable" -ForegroundColor DarkGray
Write-Host "   [Power Automate]" -ForegroundColor Cyan
Write-Host "   9. Build SMS milestone flows (Parts Ordered, Day 7, Parts Received, En Route)" -ForegroundColor White
Write-Host "  10. Build Completion Report auto-email flow (trigger: work order complete)" -ForegroundColor White
Write-Host "   [Demo Prep]" -ForegroundColor Cyan
Write-Host "  11. Add 'My Active Cases' view with Tier column in Power Apps" -ForegroundColor White
Write-Host "  12. Open demo-assets\abcsupply_demo_unified.html → run pre-flight checklist" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green

