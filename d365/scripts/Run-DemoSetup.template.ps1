<#
.SYNOPSIS
    TEMPLATE: Master Demo Build Orchestration Script
    Copy this to customers/{name}/d365/Run-{Customer}DemoSetup.ps1 and update script names.

.DESCRIPTION
    Runs all provisioning scripts in the correct dependency order.

    ╔══════════════════════════════════════════════════════════╗
    ║  CRITICAL: Cases must be created in Phase 3 — LAST.     ║
    ║  Entitlements, assets, and products must all exist       ║
    ║  before cases are provisioned so links can be bound.     ║
    ╚══════════════════════════════════════════════════════════╝

    PHASE 1 — Foundation (no dependencies)
        1. Accounts
        2. Contacts            needs: accounts
        3. Price Lists
        4. Products            needs: price lists + unit group

    PHASE 2 — Rich Data
        5. Customer Assets     needs: accounts + products
        6. Entitlements        needs: accounts
        7. KB Articles + Quick Responses

    PHASE 3 — Cases (LAST — needs everything above)
        8. Demo Cases          needs: accounts, contacts, entitlements, assets
        9. Hero Cases          needs: accounts, contacts, KB articles

    PHASE 4 — Post-Case Enrichment
       10. Case Link Enrich    links cases → entitlements + customer assets
       11. Tier Logic          patches case priority from account tier
       12. Contact Verify      ensures all accounts have primary contacts

.PARAMETER Phase
    All | Foundation | RichData | Cases | PostCase

.EXAMPLE
    .\Run-{Customer}DemoSetup.ps1              # Full build from scratch
    .\Run-{Customer}DemoSetup.ps1 -Phase Cases # Re-run case creation only
#>

[CmdletBinding()]
param(
    [ValidateSet("All","Foundation","RichData","Cases","PostCase")]
    [string]$Phase = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Customer name for display ──────────────────────────────
$CustomerName = "REPLACE_ME"   # e.g. "Navico", "Otis", "Zurn Elkay"

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
Write-Host "  $CustomerName D365 CS DEMO — MASTER BUILD" -ForegroundColor Green
Write-Host "  Phase: $Phase" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green

# ── PHASE 1: FOUNDATION ──────────────────────────────────────
# TODO: Replace Provision-{Customer}Demo.ps1 with your base script name
# TODO: Replace Provision-{Customer}Extended.ps1 with your extended script name
if ($Phase -in "All","Foundation") {
    Write-Host "`n  ═══ PHASE 1: Foundation ═══" -ForegroundColor Yellow
    Run-Step "1. Accounts"                      "Provision-{Customer}Demo.ps1"     "Accounts"
    Run-Step "2. Contacts"                      "Provision-{Customer}Demo.ps1"     "Contacts"
    Run-Step "3. Price Lists + Unit Group"      "Provision-{Customer}Extended.ps1" "PriceList"
    Run-Step "4. Full Product Catalog"          "Provision-{Customer}Extended.ps1" "Products"
}

# ── PHASE 2: RICH DATA ───────────────────────────────────────
if ($Phase -in "All","RichData") {
    Write-Host "`n  ═══ PHASE 2: Rich Data ═══" -ForegroundColor Yellow
    Run-Step "5. Customer Assets (serials)"     "Provision-{Customer}Extended.ps1" "CustomerAssets"
    Run-Step "6. Entitlements (tier SLAs)"      "Provision-{Customer}Extended.ps1" "Entitlements"
    Run-Step "7. KB Articles + Quick Responses" "Provision-{Customer}HeroCases.ps1" "KBAndResponses"
}

# ── PHASE 3: CASES ───────────────────────────────────────────
if ($Phase -in "All","Cases") {
    Write-Host "`n  ═══ PHASE 3: Cases (runs AFTER all data is in place) ═══" -ForegroundColor Yellow
    Run-Step "8. Demo Cases (base)"             "Provision-{Customer}Demo.ps1"      "Cases"
    Run-Step "9. Hero Cases (rich timelines)"   "Provision-{Customer}HeroCases.ps1" "HeroCases"
}

# ── PHASE 4: POST-CASE ──────────────────────────────────────
if ($Phase -in "All","PostCase") {
    Write-Host "`n  ═══ PHASE 4: Post-Case Enrichment ═══" -ForegroundColor Yellow
    Run-Step "10. Enrich Cases (entitlement + asset links)" "Set-{Customer}CaseLinks.ps1"
    Run-Step "11. Tier Logic (case priority)"               "Provision-{Customer}Extended.ps1" "TierLogic"
    Run-Step "12. Primary Contacts (verify)"                "Set-{Customer}PrimaryContacts.ps1"
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  BUILD COMPLETE — $CustomerName" -ForegroundColor Green
Write-Host ""
Write-Host "  MANUAL STEPS STILL REQUIRED:" -ForegroundColor Yellow
Write-Host "   1. Publish KB articles (CS Hub → Knowledge Articles → Publish)" -ForegroundColor White
Write-Host "   2. Add Tier Level column to My Active Cases view" -ForegroundColor White
Write-Host "      make.powerapps.com → Tables → Case → Views → My Active Cases" -ForegroundColor DarkGray
Write-Host "   3. Verify Copilot features enabled (CS Admin Center → Copilot)" -ForegroundColor White
Write-Host "   4. Configure screen pop phone number in Omnichannel Admin" -ForegroundColor White
Write-Host "   5. Verify workstreams + queues in CS Admin Center" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green
