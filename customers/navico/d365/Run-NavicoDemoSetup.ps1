<#
.SYNOPSIS
    Master orchestration script for Navico D365 CS Demo — runs all provisioning
    in the CORRECT dependency order.

.DESCRIPTION
    Correct build order (dependencies flow top → bottom):

    PHASE 1 — Foundation
        1. Accounts          (no dependencies)
        2. Contacts          (needs accounts)
        3. Price Lists       (no dependencies)
        4. Products          (needs price lists + unit group)

    PHASE 2 — Rich Data
        5. Customer Assets   (needs accounts + products)
        6. Entitlements      (needs accounts)
        7. KB Articles       (no dependencies — but publish manually after)
        8. Quick Responses   (no dependencies)

    PHASE 3 — Cases (LAST — needs everything above)
        9. Demo Cases        (needs accounts, contacts, entitlements, assets)
       10. Hero Cases        (needs accounts, contacts, KB articles)

    PHASE 4 — Post-Case
       11. Case Link Enrich  (links cases → entitlements + assets)
       12. Tier Logic        (patches case priority based on account tier)

.PARAMETER Phase
    Which phase(s) to run. Default = "All"
    Options: All, Foundation, RichData, Cases, PostCase

.EXAMPLE
    .\Run-NavicoDemoSetup.ps1                  # Full build from scratch
    .\Run-NavicoDemoSetup.ps1 -Phase Cases     # Only run case creation (phase 3)
    .\Run-NavicoDemoSetup.ps1 -Phase PostCase  # Only patch cases post-creation
#>

[CmdletBinding()]
param(
    [ValidateSet("All","Foundation","RichData","Cases","PostCase")]
    [string]$Phase = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Run-Step {
    param([string]$Label, [string]$Script, [string]$Action = "")
    Write-Host ""
    Write-Host ("─" * 60) -ForegroundColor DarkGray
    Write-Host "  ▶ $Label" -ForegroundColor Cyan
    Write-Host ("─" * 60) -ForegroundColor DarkGray

    $scriptPath = Join-Path $scriptDir $Script
    if (-not (Test-Path $scriptPath)) {
        Write-Warning "  Script not found: $scriptPath — skipping"
        return
    }

    if ($Action) {
        & $scriptPath -Action $Action
    } else {
        & $scriptPath
    }
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  NAVICO D365 CS DEMO — MASTER SETUP" -ForegroundColor Green
Write-Host "  Phase: $Phase" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green

# ── PHASE 1: FOUNDATION ──────────────────────────────────────
if ($Phase -in "All","Foundation") {
    Write-Host "`n  ═══ PHASE 1: Foundation ═══" -ForegroundColor Yellow

    Run-Step "1. Accounts" "Provision-NavicoDemo.ps1" "Accounts"
    Run-Step "2. Contacts" "Provision-NavicoDemo.ps1" "Contacts"
    Run-Step "3. Price Lists + Products (full catalog)" "Provision-NavicoExtended.ps1" "PriceList"
}

# ── PHASE 2: RICH DATA ───────────────────────────────────────
if ($Phase -in "All","RichData") {
    Write-Host "`n  ═══ PHASE 2: Rich Data ═══" -ForegroundColor Yellow

    Run-Step "4. Customer Assets (serials per account)" "Provision-NavicoExtended.ps1" "CustomerAssets"
    Run-Step "5. Entitlements (tier-based SLA)" "Provision-NavicoExtended.ps1" "Entitlements"
    Run-Step "6. KB Articles + Quick Responses" "Provision-NavicoHeroCases.ps1" "KBAndResponses"
}

# ── PHASE 3: CASES (last!) ───────────────────────────────────
if ($Phase -in "All","Cases") {
    Write-Host "`n  ═══ PHASE 3: Cases (runs AFTER all data is in place) ═══" -ForegroundColor Yellow

    Run-Step "7. Demo Cases (base)" "Provision-NavicoDemo.ps1" "Cases"
    Run-Step "8. Hero Cases (rich activity timelines)" "Provision-NavicoHeroCases.ps1" "HeroCases"
}

# ── PHASE 4: POST-CASE ──────────────────────────────────────
if ($Phase -in "All","PostCase") {
    Write-Host "`n  ═══ PHASE 4: Post-Case Enrichment ═══" -ForegroundColor Yellow

    Run-Step "9.  Enrich Cases — entitlement + asset links" "Set-NavicoCaseLinks.ps1"
    Run-Step "10. Tier Logic — case priority from account tier" "Provision-NavicoExtended.ps1" "TierLogic"
    Run-Step "11. Primary Contacts — verify all accounts linked" "Set-NavicoPrimaryContacts.ps1"
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "  MANUAL STEPS STILL REQUIRED:" -ForegroundColor Yellow
Write-Host "   1. Publish KB articles (CS Hub → Knowledge Articles)" -ForegroundColor White
Write-Host "   2. Add 'Tier Level' column to My Active Cases view" -ForegroundColor White
Write-Host "      (make.powerapps.com → Tables → Case → Views)" -ForegroundColor DarkGray
Write-Host "   3. Verify Copilot features enabled (CS Admin → Copilot)" -ForegroundColor White
Write-Host "   4. Verify screen pop config for +1 651-226-3398" -ForegroundColor White
Write-Host ""
Write-Host "  D365 Org: https://orgecbce8ef.crm.dynamics.com" -ForegroundColor DarkGray
Write-Host ("═" * 60) -ForegroundColor Green
