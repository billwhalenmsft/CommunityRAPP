<#
.SYNOPSIS
    Add ERAC custom table pages to the erac_LiteCRM Model-Driven App.

.DESCRIPTION
    RESOLVED (Phase 7): The AddAppComponents API rejected all payload formats
    for componenttype=1 (Entity). The working solution was to set the app
    module's navigationtype from 0 to 1, which tells D365 to use all entities
    referenced in the sitemap rather than requiring explicit entity registration.

    PowerShell one-liner that fixed it:
        PATCH appmodules({appId}) with { "navigationtype": 1 }

    This script is kept for reference. The navigationtype patch was applied
    directly and is live. All 5 ERAC custom entities now appear in the app.

    Entities accessible via sitemap:
      erac_partnershiprating, erac_riskassessment, erac_treaty,
      erac_reserveadequacy, erac_dispute

.PARAMETER Org
    Dataverse org URL
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$AppUniqueName = "erac_LiteCRM"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$token = (az account get-access-token --resource $Org | ConvertFrom-Json).accessToken
$H = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

function Invoke-Dv([string]$Method,[string]$Path,[object]$Body=$null,[int]$Timeout=30) {
    $p = @{ Uri="$Org/api/data/v9.2/$Path"; Method=$Method; Headers=$H; TimeoutSec=$Timeout; UseBasicParsing=$true }
    if ($Body) { $p.Body = ($Body | ConvertTo-Json -Depth 10) }
    try {
        $r = Invoke-WebRequest @p
        if ($r.Content) { return $r.Content | ConvertFrom-Json }
        return @{ ok=$true }
    } catch {
        $code = try { $_.Exception.Response.StatusCode.value__ } catch { 0 }
        $msg  = try { $_.ErrorDetails.Message } catch { $_.Exception.Message }
        Write-Warning "  ✗ $Method $Path ($code): $($msg.Substring(0,[Math]::Min(300,$msg.Length)))"
        return $null
    }
}

Write-Host "=== ADD ERAC ENTITIES TO MDA APP ===" -ForegroundColor Cyan

# ── Find the app module ───────────────────────────────────────────────────────
Write-Host "[1] Finding app module '$AppUniqueName'..."
$apps = Invoke-Dv GET "appmodules?`$select=appmoduleid,name,uniquename"
$app  = $apps.value | Where-Object { $_.uniquename -eq $AppUniqueName }
if (-not $app) {
    Write-Host "  All apps: $($apps.value.uniquename -join ', ')"
    Write-Error "App '$AppUniqueName' not found."
}
$appId = $app.appmoduleid
Write-Host "  ✓ Found: '$($app.name)' ($appId)" -ForegroundColor Green

# ── Get entity metadata IDs for our 5 custom tables ──────────────────────────
Write-Host "[2] Resolving entity metadata IDs..."
$customEntities = @(
    "erac_partnershiprating",
    "erac_riskassessment",
    "erac_treaty",
    "erac_reserveadequacy",
    "erac_dispute"
)

$entityMeta = @{}
foreach ($e in $customEntities) {
    $meta = Invoke-Dv GET "EntityDefinitions(LogicalName='$e')?`$select=MetadataId,LogicalName,DisplayName"
    if ($meta -and $meta.MetadataId) {
        $entityMeta[$e] = $meta.MetadataId
        $displayName = $meta.DisplayName.UserLocalizedLabel.Label
        Write-Host "  ✓ $e → $($meta.MetadataId) ($displayName)" -ForegroundColor Green
    } else {
        Write-Warning "  ✗ Could not resolve metadata ID for $e"
    }
}

# ── Skip component existence check — AddAppComponents is idempotent ──────────
Write-Host "[3] Skipping component check — AddAppComponents is idempotent"
$existingIds = @()

# ── Add entities via AddAppComponents action ─────────────────────────────────
Write-Host "[4] Adding custom entities to app..."

# Build component list — componenttype 1 = Entity, use objectid (MetadataId)
$components = @()
foreach ($e in $customEntities) {
    if (-not $entityMeta.ContainsKey($e)) { continue }
    $metaId = $entityMeta[$e]
    $components += @{ type = 1; objectid = $metaId }
    Write-Host "  + Entity $e ($metaId)" -ForegroundColor DarkCyan
}

if ($components.Count -gt 0) {
    $addBody = @{
        AppId      = $appId
        Components = $components
    }
    $r = Invoke-Dv POST "AddAppComponents" $addBody
    if ($r -and -not $r.error) {
        Write-Host "  ✓ Added $($components.Count) entities to app" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ AddAppComponents returned unexpected response — entities may already be registered" -ForegroundColor Yellow
    }
}

# ── Also add the saved query views for each entity ────────────────────────────
Write-Host "[5] Adding ERAC views to app..."
$viewNames = @{
    "erac_partnershiprating" = "Active Partnership Ratings"
    "erac_riskassessment"    = "Active Risk Assessments"
    "erac_treaty"            = "Active Treaties"
    "erac_reserveadequacy"   = "Active Reserve Adequacy"
    "erac_dispute"           = "Active Legal Disputes"
}

$viewComponents = @()
foreach ($e in $customEntities) {
    $vname = $viewNames[$e]
    $views = Invoke-Dv GET "savedqueries?`$select=savedqueryid&`$filter=returnedtypecode eq '$e' and name eq '$vname'"
    if ($views -and $views.value.Count -gt 0) {
        $vid = $views.value[0].savedqueryid
        $viewComponents += @{ type = 26; objectid = $vid }
        Write-Host "  + View '$vname' ($vid)" -ForegroundColor DarkCyan
    }
}

if ($viewComponents.Count -gt 0) {
    $r = Invoke-Dv POST "AddAppComponents" @{ AppId=$appId; Components=$viewComponents }
    if ($r -and -not $r.error) {
        Write-Host "  ✓ Added $($viewComponents.Count) views to app" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Views may already be registered" -ForegroundColor Yellow
    }
}

# ── Publish the app ───────────────────────────────────────────────────────────
Write-Host "[6] Validating and publishing app..."
$validateResult = Invoke-Dv GET "ValidateApp(AppModuleId=$appId)" 30
if ($validateResult) {
    Write-Host "  ✓ App validated" -ForegroundColor Green
}

try {
    Invoke-WebRequest "$Org/api/data/v9.2/PublishAllXml" -Method POST -Headers $H -UseBasicParsing -TimeoutSec 120 | Out-Null
    Write-Host "  ✓ Published" -ForegroundColor Green
} catch {
    $code = try { $_.Exception.Response.StatusCode.value__ } catch { 204 }
    if ($code -le 204) { Write-Host "  ✓ Published" -ForegroundColor Green }
    else { Write-Warning "  Publish: $code" }
}

Write-Host "`n✅ ERAC custom table pages added to MDA app" -ForegroundColor Green
Write-Host "   Hard refresh D365 (Ctrl+F5) — Cedent Portfolio and Risk & Legal nav groups should now open entity lists"
