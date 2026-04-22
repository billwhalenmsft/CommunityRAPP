<#
.SYNOPSIS
    ERAC Lite CRM — End-to-end deploy/redeploy orchestrator.

.DESCRIPTION
    Reads ../config/env.json for target environment.
    Bootstraps publisher + solution if missing, then runs the per-area scripts
    in dependency order. Each step is wrapped — failures in one step do not stop
    the run; a final summary reports per-step status.

    Phases:
      bootstrap   — publisher + solution
      schema      — OOTB columns + Cedent Profile fields + custom tables
      data        — cedent accounts + contacts + enrich + rich seed
      ui          — views + charts + sitemap + web resources + forms + icons
      all         — all of the above (default)

    Auth: az login first. The script uses the user's az CLI token.

.PARAMETER Phase
    bootstrap | schema | data | ui | all (default: all)

.PARAMETER ConfigPath
    Path to env.json (default: ../config/env.json)

.PARAMETER ContinueOnError
    Default: $true. Set to $false to stop on the first failure.

.EXAMPLE
    .\Deploy-EracToNewEnv.ps1
    .\Deploy-EracToNewEnv.ps1 -Phase bootstrap
    .\Deploy-EracToNewEnv.ps1 -Phase ui -Verbose
#>
[CmdletBinding()]
param(
    [ValidateSet("bootstrap","schema","data","ui","all")]
    [string]$Phase = "all",
    [string]$ConfigPath = "$PSScriptRoot\..\config\env.json",
    [bool]$ContinueOnError = $true
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

# ─────────────────────────────────────────────
# Load + validate config
# ─────────────────────────────────────────────
if (-not (Test-Path $ConfigPath)) { Write-Error "Config not found: $ConfigPath" }
$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " ERAC Lite CRM — Deploy to: $($cfg.FriendlyName)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " OrgUrl   : $($cfg.OrgUrl)"
Write-Host " Solution : $($cfg.SolutionUniqueName) (prefix: $($cfg.PublisherPrefix))"
Write-Host " Phase    : $Phase"
Write-Host ""

# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────
function Get-Token {
    $j = az account get-access-token --resource $cfg.OrgUrl 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Auth failed. Run: az login --scope $($cfg.OrgUrl)/.default"
    }
    return ($j | ConvertFrom-Json).accessToken
}

function Get-Headers {
    @{
        Authorization      = "Bearer $(Get-Token)"
        "Content-Type"     = "application/json; charset=utf-8"
        Accept             = "application/json"
        "OData-MaxVersion" = "4.0"
        "OData-Version"    = "4.0"
        Prefer             = "return=representation"
    }
}

function Invoke-Dv {
    param([string]$Method, [string]$Path, [object]$Body)
    $uri = "$($cfg.OrgUrl)/api/data/v9.2/$Path"
    $params = @{ Method=$Method; Uri=$uri; Headers=(Get-Headers); TimeoutSec=60; UseBasicParsing=$true }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 20) }
    try {
        $r = Invoke-WebRequest @params
        if ($r.Content) { return $r.Content | ConvertFrom-Json }
        return $null
    } catch {
        $msg = $_.Exception.Message
        if ($msg -match "already exists|duplicate|0x80040220") {
            Write-Host "    ↳ Already exists" -ForegroundColor DarkGray
            return $null
        }
        throw
    }
}

# ─────────────────────────────────────────────
# Verify connectivity
# ─────────────────────────────────────────────
Write-Host "[Auth] Verifying connectivity..." -ForegroundColor Cyan
try {
    $who = Invoke-Dv GET "WhoAmI"
    Write-Host "  ✓ Connected as user $($who.UserId)" -ForegroundColor Green
} catch {
    Write-Error "Could not reach $($cfg.OrgUrl): $($_.Exception.Message)"
}

# ─────────────────────────────────────────────
# BOOTSTRAP — Publisher + Solution
# ─────────────────────────────────────────────
function Step-Bootstrap {
    Write-Host "`n=== BOOTSTRAP: Publisher + Solution ===" -ForegroundColor Cyan

    # Publisher
    Write-Host "[Publisher] Looking up '$($cfg.PublisherUniqueName)'..."
    $pubQ = Invoke-Dv GET "publishers?`$filter=uniquename eq '$($cfg.PublisherUniqueName)'&`$select=publisherid,uniquename,customizationprefix"
    if ($pubQ.value.Count -gt 0) {
        $pub = $pubQ.value[0]
        Write-Host "  ✓ Publisher exists: id=$($pub.publisherid) prefix=$($pub.customizationprefix)" -ForegroundColor Green
    } else {
        Write-Host "  Creating publisher..."
        $body = @{
            uniquename             = $cfg.PublisherUniqueName
            friendlyname           = $cfg.PublisherFriendlyName
            customizationprefix    = $cfg.PublisherPrefix
            customizationoptionvalueprefix = 10000
            description            = "Publisher for GE ERAC Lite CRM demo solution"
        }
        $pub = Invoke-Dv POST "publishers" $body
        Write-Host "  ✓ Publisher created: id=$($pub.publisherid)" -ForegroundColor Green
    }

    # Solution
    Write-Host "[Solution] Looking up '$($cfg.SolutionUniqueName)'..."
    $solQ = Invoke-Dv GET "solutions?`$filter=uniquename eq '$($cfg.SolutionUniqueName)'&`$select=solutionid,uniquename,friendlyname,version"
    if ($solQ.value.Count -gt 0) {
        $sol = $solQ.value[0]
        Write-Host "  ✓ Solution exists: id=$($sol.solutionid) v$($sol.version)" -ForegroundColor Green
    } else {
        Write-Host "  Creating solution..."
        $body = @{
            uniquename                       = $cfg.SolutionUniqueName
            friendlyname                     = $cfg.SolutionFriendlyName
            version                          = "1.0.0.0"
            description                      = "GE Verisk ERAC reinsurance cedent workspace — Cedents, Treaties, PRR, Risk, Reserve, Disputes"
            "publisherid@odata.bind"         = "/publishers($($pub.publisherid))"
        }
        $sol = Invoke-Dv POST "solutions" $body
        Write-Host "  ✓ Solution created: id=$($sol.solutionid)" -ForegroundColor Green
    }

    # Persist solution id back to env.json
    if ($cfg.SolutionId -ne $sol.solutionid) {
        $cfg.SolutionId = $sol.solutionid
        $cfg | ConvertTo-Json -Depth 6 | Set-Content $ConfigPath -Encoding UTF8
        Write-Host "  ✓ Saved SolutionId to env.json" -ForegroundColor Green
    }

    return @{ Publisher=$pub; Solution=$sol }
}

# ─────────────────────────────────────────────
# Step runner — wraps a child script
# ─────────────────────────────────────────────
$results = @()
function Run-Step {
    param([string]$Label, [scriptblock]$Body)
    Write-Host "`n--- [$Label] ---" -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $Body
        $sw.Stop()
        $results += [pscustomobject]@{ Step=$Label; Status="OK"; Seconds=[int]$sw.Elapsed.TotalSeconds }
        Write-Host "  ✓ $Label complete ($([int]$sw.Elapsed.TotalSeconds)s)" -ForegroundColor Green
    } catch {
        $sw.Stop()
        $results += [pscustomobject]@{ Step=$Label; Status="FAIL"; Seconds=[int]$sw.Elapsed.TotalSeconds; Error=$_.Exception.Message }
        Write-Warning "  ✗ $Label failed: $($_.Exception.Message)"
        if (-not $ContinueOnError) { throw }
    }
}

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
$bootstrap = $null
if ($Phase -in @("bootstrap","all")) {
    $bootstrap = Step-Bootstrap
}

# Reload cfg in case bootstrap saved a new SolutionId
$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$O = $cfg.OrgUrl
$S = $cfg.SolutionUniqueName

if ($Phase -in @("schema","all")) {
    Run-Step "Schema: OOTB column adds + publish" {
        & "$ScriptDir\Provision-EracDataverse.ps1" -OrgUrl $O -Phase Schema
    }
    Run-Step "Schema: 8 Cedent Profile fields" {
        & "$ScriptDir\Add-EracAccountFields.ps1" -Org $O -SolutionUniqueName $S
    }
    Run-Step "Schema: 5 ERAC custom tables" {
        & "$ScriptDir\Provision-EracCustomTables.ps1" -Org $O
    }
}

if ($Phase -in @("data","all")) {
    Run-Step "Data: cedent accounts + contacts" {
        & "$ScriptDir\Provision-EracDataverse.ps1" -OrgUrl $O -Phase Data
    }
    Run-Step "Data: enrich cedent profile fields" {
        & "$ScriptDir\Update-EracCedentData.ps1" -Org $O -SolutionUniqueName $S
    }
    Run-Step "Data: rich seed (treaties, PRR, risk, reserve, disputes)" {
        & "$ScriptDir\Seed-EracRichData.ps1" -Org $O
    }
}

if ($Phase -in @("ui","all")) {
    if (-not $cfg.SolutionId) {
        Write-Warning "  No SolutionId in config — re-run with -Phase bootstrap first"
    } else {
        Run-Step "UI: solution components + filtered views + sitemap" {
            & "$ScriptDir\Build-EracSolution.ps1" -OrgUrl $O -SolutionId $cfg.SolutionId -Phase All
        }
    }
    Run-Step "UI: views + charts (15 + 2)" {
        & "$ScriptDir\Add-EracViewsAndCharts.ps1" -Org $O
    }
    Run-Step "UI: web resources (PRR dashboard, portfolio analytics, Cedent 360 card)" {
        & "$ScriptDir\Deploy-EracWebResources.ps1" -Org $O
    }
    Run-Step "UI: ERAC Cedent 360 form" {
        & "$ScriptDir\New-EracCedent360Form.ps1" -Org $O
    }
    Run-Step "UI: Cedent 360 → Summary tab span" {
        & "$ScriptDir\Move-EracCedent360ToSummary.ps1" -Org $O
    }
    Run-Step "UI: Account form ERAC tab" {
        & "$ScriptDir\Update-EracAccountForm.ps1" -Org $O
    }
    Run-Step "UI: Cedent Profile section + header swap" {
        & "$ScriptDir\Update-EracAccountFormProfile.ps1" -Org $O
    }
    Run-Step "UI: entity icons" {
        & "$ScriptDir\Set-EracEntityIcons.ps1" -Org $O
    }
    Run-Step "UI: sitemap groups + custom-table views" {
        & "$ScriptDir\Update-EracSiteMapAndViews.ps1" -Org $O
    }
    Run-Step "UI: AppModule wiring" {
        & "$ScriptDir\Add-EracAppComponents.ps1" -Org $O
    }
    Run-Step "UI: sitemap + icons cleanup" {
        & "$ScriptDir\Fix-EracSiteMapAndIcons.ps1" -Org $O
    }
    Run-Step "UI: reserve adequacy notes patch" {
        & "$ScriptDir\Fix-EracReserveAdequacyNotes.ps1" -Org $O
    }
}

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host " DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
$results | Format-Table -AutoSize Step, Status, Seconds, Error
$ok   = ($results | Where-Object Status -EQ "OK").Count
$fail = ($results | Where-Object Status -EQ "FAIL").Count
Write-Host "Steps OK: $ok · FAILED: $fail" -ForegroundColor $(if ($fail -gt 0) { "Yellow" } else { "Green" })

Write-Host "`n📋 NEXT (manual in make.powerapps.com):"
Write-Host "  1. Open: https://make.powerapps.com/environments/$($cfg.EnvironmentId)/solutions/$($cfg.SolutionId)"
Write-Host "  2. Verify ERAC Lite CRM AppModule was created (or create new model-driven app pointing at erac_LiteCRM_SiteMap)"
Write-Host "  3. Publish all customizations"
Write-Host "  4. Update demo HTML: customers/ge_erac/dataverse/demo-assets/erac_demo_unified.html — change orgecbce8ef → $($cfg.OrgUrl -replace 'https://(org[a-z0-9]+).*','$1')"
Write-Host ""
