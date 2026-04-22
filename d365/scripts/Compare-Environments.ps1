<#
.SYNOPSIS
    Compare two Dataverse / D365 environments and produce an HTML diff report.

.DESCRIPTION
    Queries both environments via the Dataverse Web API and compares solutions,
    custom tables, apps, flows, security roles, web resources, Copilot Studio
    agents, plugins, and demo data record counts.  Output is a self-contained
    Fluent 2-styled HTML file.

.PARAMETER EnvA
    Full org URL for environment A (e.g. https://org6feab6b5.crm.dynamics.com).
    Alternatively, a path to a JSON config file containing environment.url.

.PARAMETER EnvB
    Full org URL for environment B (or config file path).

.PARAMETER OutputPath
    File path for the HTML report.  Defaults to .\comparison-report.html.

.PARAMETER IncludeData
    When set, also compares record counts for key demo tables.

.EXAMPLE
    # Compare two environments by URL
    .\Compare-Environments.ps1 `
        -EnvA "https://org6feab6b5.crm.dynamics.com" `
        -EnvB "https://orgecbce8ef.crm.dynamics.com"

    # Compare using config files
    .\Compare-Environments.ps1 `
        -EnvA "..\..\customers\mfg_coe\d365\config\environment-gold.json" `
        -EnvB "..\..\customers\mfg_coe\d365\config\environment-master.json"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$EnvA,

    [Parameter(Mandatory)]
    [string]$EnvB,

    [string]$OutputPath = ".\comparison-report.html",

    [switch]$IncludeData
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============================================================
# Import helpers
# ============================================================
Import-Module "$scriptDir\DataverseHelper.psm1" -Force -DisableNameChecking

# ============================================================
# Resolve environment URLs (accept URL or JSON config path)
# ============================================================
function Resolve-EnvUrl {
    param([string]$Input_)
    if ($Input_ -match '^https?://') {
        return @{ url = $Input_.TrimEnd('/'); name = $Input_ }
    }
    # Treat as config file path
    $path = if ([System.IO.Path]::IsPathRooted($Input_)) { $Input_ } else { Join-Path $scriptDir $Input_ }
    if (-not (Test-Path $path)) { throw "Config file not found: $path" }
    $cfg = Get-Content $path -Raw | ConvertFrom-Json
    return @{
        url  = $cfg.environment.url.TrimEnd('/')
        name = $cfg.environment.name
        type = $cfg.environment.type
        release = $cfg.environment.releaseCycle
    }
}

$envAInfo = Resolve-EnvUrl $EnvA
$envBInfo = Resolve-EnvUrl $EnvB

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Magenta
Write-Host "  D365 Environment Comparison" -ForegroundColor Magenta
Write-Host "  A: $($envAInfo.name) ($($envAInfo.url))" -ForegroundColor DarkGray
Write-Host "  B: $($envBInfo.name) ($($envBInfo.url))" -ForegroundColor DarkGray
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
Write-Host ("=" * 70) -ForegroundColor Magenta
Write-Host ""

# ============================================================
# Query helper — switches target env, queries, returns results
# ============================================================
function Query-Environment {
    param(
        [string]$Url,
        [string]$EntitySet,
        [string]$Filter = "",
        [string]$Select = ""
    )
    Set-DataverseUrl -Url $Url
    Connect-Dataverse
    $params = @{ EntitySet = $EntitySet }
    if ($Filter) { $params.Filter = $Filter }
    if ($Select) { $params.Select = $Select }
    $result = Invoke-DataverseGet @params
    if ($null -eq $result) { return @() }
    return $result
}

# ============================================================
# Define comparison categories
# ============================================================
$categories = @(
    @{
        name     = "Unmanaged Solutions"
        entity   = "solutions"
        filter   = "ismanaged eq false and isvisible eq true"
        select   = "uniquename,friendlyname,version,publisherid"
        key      = "uniquename"
        display  = "friendlyname"
        extra    = @("version")
    },
    @{
        name     = "Managed Solutions (Demo Hub / ISV)"
        entity   = "solutions"
        filter   = "ismanaged eq true and isvisible eq true"
        select   = "uniquename,friendlyname,version"
        key      = "uniquename"
        display  = "friendlyname"
        extra    = @("version")
    },
    @{
        name     = "Custom Tables"
        entity   = "EntityDefinitions"
        filter   = "IsCustomEntity eq true"
        select   = "LogicalName,DisplayName"
        key      = "LogicalName"
        display  = "LogicalName"
        extra    = @()
        isMetadata = $true
    },
    @{
        name     = "Model-Driven Apps"
        entity   = "appmodules"
        filter   = ""
        select   = "uniquename,name,appmoduleversion"
        key      = "uniquename"
        display  = "name"
        extra    = @("appmoduleversion")
    },
    @{
        name     = "Canvas Apps"
        entity   = "canvasapps"
        filter   = ""
        select   = "name,displayname,status"
        key      = "name"
        display  = "displayname"
        extra    = @("status")
    },
    @{
        name     = "Cloud Flows (Power Automate)"
        entity   = "workflows"
        filter   = "category eq 5"
        select   = "name,statecode,statuscode"
        key      = "name"
        display  = "name"
        extra    = @("statecode")
    },
    @{
        name     = "Classic Workflows"
        entity   = "workflows"
        filter   = "category eq 0"
        select   = "name,statecode"
        key      = "name"
        display  = "name"
        extra    = @("statecode")
    },
    @{
        name     = "Security Roles"
        entity   = "roles"
        filter   = ""
        select   = "name,roleid,iscustomizable"
        key      = "name"
        display  = "name"
        extra    = @()
    },
    @{
        name     = "Web Resources"
        entity   = "webresourceset"
        filter   = ""
        select   = "name,displayname,webresourcetype"
        key      = "name"
        display  = "name"
        extra    = @("webresourcetype")
    },
    @{
        name     = "Copilot Studio Agents"
        entity   = "bots"
        filter   = ""
        select   = "name,schemaname,statecode"
        key      = "schemaname"
        display  = "name"
        extra    = @("statecode")
    },
    @{
        name     = "Plugin Assemblies"
        entity   = "pluginassemblies"
        filter   = ""
        select   = "name,version"
        key      = "name"
        display  = "name"
        extra    = @("version")
    }
)

# Demo data tables (optional)
$dataTables = @(
    @{ name = "Accounts";           entity = "accounts" },
    @{ name = "Contacts";           entity = "contacts" },
    @{ name = "Cases";              entity = "incidents" },
    @{ name = "Knowledge Articles"; entity = "knowledgearticles" },
    @{ name = "Products";           entity = "products" },
    @{ name = "Queues";             entity = "queues" },
    @{ name = "Entitlements";       entity = "entitlements" },
    @{ name = "SLAs";               entity = "slas" }
)

# ============================================================
# Run comparisons
# ============================================================
$results = @()
$totalCategories = $categories.Count
$catIdx = 0

foreach ($cat in $categories) {
    $catIdx++
    Write-Host "[$catIdx/$totalCategories] Comparing: $($cat.name)..." -ForegroundColor Cyan

    try {
        $dataA = @(Query-Environment -Url $envAInfo.url -EntitySet $cat.entity -Filter $cat.filter -Select $cat.select)
        $dataB = @(Query-Environment -Url $envBInfo.url -EntitySet $cat.entity -Filter $cat.filter -Select $cat.select)
    } catch {
        Write-Warning "  Skipped $($cat.name): $($_.Exception.Message)"
        $results += @{
            category = $cat.name
            error    = $_.Exception.Message
            aOnly    = @()
            bOnly    = @()
            both     = @()
            diffs    = @()
            countA   = 0
            countB   = 0
        }
        continue
    }

    $keyField = $cat.key

    # Build lookup tables
    $mapA = @{}
    foreach ($item in $dataA) {
        $k = $item.$keyField
        if ($k) { $mapA[$k] = $item }
    }
    $mapB = @{}
    foreach ($item in $dataB) {
        $k = $item.$keyField
        if ($k) { $mapB[$k] = $item }
    }

    $aOnlyItems = @()
    $bOnlyItems = @()
    $bothItems  = @()
    $diffItems  = @()

    # Items in A only
    foreach ($k in $mapA.Keys) {
        if (-not $mapB.ContainsKey($k)) {
            $displayVal = $mapA[$k].($cat.display)
            if (-not $displayVal) { $displayVal = $k }
            $aOnlyItems += @{ key = $k; display = $displayVal; item = $mapA[$k] }
        }
    }

    # Items in B only
    foreach ($k in $mapB.Keys) {
        if (-not $mapA.ContainsKey($k)) {
            $displayVal = $mapB[$k].($cat.display)
            if (-not $displayVal) { $displayVal = $k }
            $bOnlyItems += @{ key = $k; display = $displayVal; item = $mapB[$k] }
        }
    }

    # Items in both — check for version/state differences
    foreach ($k in $mapA.Keys) {
        if ($mapB.ContainsKey($k)) {
            $displayVal = $mapA[$k].($cat.display)
            if (-not $displayVal) { $displayVal = $k }
            $bothItems += @{ key = $k; display = $displayVal }

            # Check extra fields for differences
            foreach ($field in $cat.extra) {
                $valA = $mapA[$k].$field
                $valB = $mapB[$k].$field
                if ("$valA" -ne "$valB") {
                    $diffItems += @{
                        key     = $k
                        display = $displayVal
                        field   = $field
                        valueA  = "$valA"
                        valueB  = "$valB"
                    }
                }
            }
        }
    }

    $results += @{
        category = $cat.name
        error    = $null
        aOnly    = $aOnlyItems
        bOnly    = $bOnlyItems
        both     = $bothItems
        diffs    = $diffItems
        countA   = $mapA.Count
        countB   = $mapB.Count
    }

    Write-Host "  A: $($mapA.Count)  |  B: $($mapB.Count)  |  A-only: $($aOnlyItems.Count)  |  B-only: $($bOnlyItems.Count)  |  Diffs: $($diffItems.Count)" -ForegroundColor DarkGray
}

# ============================================================
# Demo data record counts (optional)
# ============================================================
$dataResults = @()
if ($IncludeData) {
    Write-Host ""
    Write-Host "Comparing demo data record counts..." -ForegroundColor Cyan
    foreach ($tbl in $dataTables) {
        Write-Host "  $($tbl.name)..." -ForegroundColor DarkGray -NoNewline
        try {
            Set-DataverseUrl -Url $envAInfo.url
            Connect-Dataverse
            $headers = Get-DataverseHeaders
            $cntA = Invoke-RestMethod -Uri "$(Get-DataverseUrl)/api/data/v9.2/$($tbl.entity)/`$count" -Headers $headers -Method Get
            if ($null -eq $cntA) { $cntA = 0 }

            Set-DataverseUrl -Url $envBInfo.url
            Connect-Dataverse
            $headers = Get-DataverseHeaders
            $cntB = Invoke-RestMethod -Uri "$(Get-DataverseUrl)/api/data/v9.2/$($tbl.entity)/`$count" -Headers $headers -Method Get
            if ($null -eq $cntB) { $cntB = 0 }

            $dataResults += @{
                name   = $tbl.name
                countA = $cntA
                countB = $cntB
                delta  = $cntA - $cntB
            }
            Write-Host " A: $cntA  B: $cntB" -ForegroundColor DarkGray
        } catch {
            Write-Warning "  Could not count $($tbl.name): $($_.Exception.Message)"
            $dataResults += @{ name = $tbl.name; countA = "?"; countB = "?"; delta = 0 }
        }
    }
}

# ============================================================
# Generate HTML report
# ============================================================
Write-Host ""
Write-Host "Generating HTML report..." -ForegroundColor Cyan

$envALabel = if ($envAInfo.name -ne $envAInfo.url) { "$($envAInfo.name)" } else { $envAInfo.url -replace 'https://','' }
$envBLabel = if ($envBInfo.name -ne $envBInfo.url) { "$($envBInfo.name)" } else { $envBInfo.url -replace 'https://','' }
$envARelease = if ($envAInfo.release) { " ($($envAInfo.release))" } else { "" }
$envBRelease = if ($envBInfo.release) { " ($($envBInfo.release))" } else { "" }

$html = @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>D365 Environment Comparison — $envALabel vs $envBLabel</title>
<style>
  :root {
    --bg: #FAFAFA; --surface: #FFFFFF; --border: #E1DFDD;
    --text: #242424; --text-secondary: #616161;
    --primary: #0078D4; --primary-hover: #106EBE;
    --success: #107C10; --warning: #C19C00; --danger: #A4262C;
    --a-color: #0078D4; --b-color: #8764B8;
    --a-bg: #EFF6FC; --b-bg: #F3F0F9; --both-bg: #F0FFF0; --diff-bg: #FFF4CE;
    --radius: 8px; --shadow: 0 2px 8px rgba(0,0,0,0.08);
    --font: 'Segoe UI', -apple-system, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.5; }

  .header {
    background: linear-gradient(135deg, #0078D4, #50E6FF);
    color: white; padding: 32px 40px; margin-bottom: 24px;
  }
  .header h1 { font-size: 1.75rem; font-weight: 600; margin-bottom: 8px; }
  .header .meta { opacity: 0.9; font-size: 0.9rem; }

  .container { max-width: 1200px; margin: 0 auto; padding: 0 24px 60px; }

  /* Summary cards */
  .summary-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 32px;
  }
  .env-card {
    background: var(--surface); border-radius: var(--radius); padding: 20px 24px;
    box-shadow: var(--shadow); border-left: 4px solid var(--primary);
  }
  .env-card.env-b { border-left-color: var(--b-color); }
  .env-card h3 { font-size: 1.1rem; margin-bottom: 4px; }
  .env-card .url { color: var(--text-secondary); font-size: 0.85rem; word-break: break-all; }
  .env-card .badge {
    display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem;
    font-weight: 600; margin-top: 8px;
  }
  .badge-early { background: #FFF4CE; color: #8A6914; }
  .badge-standard { background: #DFF6DD; color: #0E700E; }
  .badge-trial { background: #FDE7E9; color: #A4262C; }
  .badge-prod { background: #DFF6DD; color: #0E700E; }

  /* Score bar */
  .score-bar {
    display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 32px;
  }
  .score-item {
    background: var(--surface); border-radius: var(--radius); padding: 16px 20px;
    box-shadow: var(--shadow); flex: 1; min-width: 140px; text-align: center;
  }
  .score-item .num { font-size: 1.75rem; font-weight: 700; }
  .score-item .label { font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; }
  .num-a { color: var(--a-color); }
  .num-b { color: var(--b-color); }
  .num-match { color: var(--success); }
  .num-diff { color: var(--warning); }

  /* Category sections */
  .category {
    background: var(--surface); border-radius: var(--radius); margin-bottom: 16px;
    box-shadow: var(--shadow); overflow: hidden;
  }
  .cat-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 16px 20px; cursor: pointer; user-select: none;
    border-bottom: 1px solid var(--border);
  }
  .cat-header:hover { background: #F5F5F5; }
  .cat-header h3 { font-size: 1rem; }
  .cat-badges span {
    display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem;
    font-weight: 600; margin-left: 6px;
  }
  .badge-aonly { background: var(--a-bg); color: var(--a-color); }
  .badge-bonly { background: var(--b-bg); color: var(--b-color); }
  .badge-match { background: #DFF6DD; color: var(--success); }
  .badge-diffs { background: var(--diff-bg); color: #8A6914; }
  .badge-error { background: #FDE7E9; color: var(--danger); }
  .chevron { transition: transform 0.2s; font-size: 0.8rem; }
  .chevron.open { transform: rotate(90deg); }

  .cat-body { padding: 0 20px 16px; display: none; }
  .cat-body.open { display: block; }

  /* Tables inside categories */
  .diff-section { margin-top: 12px; }
  .diff-section h4 {
    font-size: 0.85rem; font-weight: 600; margin-bottom: 6px;
    padding: 4px 8px; border-radius: 4px; display: inline-block;
  }
  .diff-section h4.a-only { background: var(--a-bg); color: var(--a-color); }
  .diff-section h4.b-only { background: var(--b-bg); color: var(--b-color); }
  .diff-section h4.diffs { background: var(--diff-bg); color: #8A6914; }

  table { width: 100%; border-collapse: collapse; margin: 4px 0 12px; font-size: 0.85rem; }
  th { text-align: left; padding: 8px 10px; background: #F3F2F1; font-weight: 600; border-bottom: 2px solid var(--border); }
  td { padding: 6px 10px; border-bottom: 1px solid #EDEBE9; }
  tr:hover td { background: #F9F9F9; }
  .val-a { color: var(--a-color); font-weight: 600; }
  .val-b { color: var(--b-color); font-weight: 600; }
  .empty { color: #C8C8C8; font-style: italic; }

  /* Data comparison */
  .data-table { margin-top: 24px; }
  .data-table td.positive { color: var(--success); }
  .data-table td.negative { color: var(--danger); }
  .data-table td.zero { color: var(--text-secondary); }

  /* Expand/Collapse all */
  .toolbar { display: flex; justify-content: flex-end; margin-bottom: 12px; gap: 8px; }
  .toolbar button {
    background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    padding: 6px 14px; font-size: 0.8rem; cursor: pointer; font-family: var(--font);
  }
  .toolbar button:hover { background: #F5F5F5; }

  @media (max-width: 768px) {
    .summary-grid { grid-template-columns: 1fr; }
    .score-bar { flex-direction: column; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>D365 Environment Comparison</h1>
  <div class="meta">Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') &nbsp;|&nbsp; Bills Demo Manager</div>
</div>

<div class="container">

  <!-- Environment cards -->
  <div class="summary-grid">
    <div class="env-card">
      <h3>Environment A: $envALabel</h3>
      <div class="url">$($envAInfo.url)</div>
$(if ($envAInfo.release) { "      <span class=`"badge $(if ($envAInfo.release -match 'Early') {'badge-early'} else {'badge-standard'})`">$($envAInfo.release)</span>" })
$(if ($envAInfo.type) { "      <span class=`"badge $(if ($envAInfo.type -match 'Trial') {'badge-trial'} else {'badge-prod'})`">$($envAInfo.type)</span>" })
    </div>
    <div class="env-card env-b">
      <h3>Environment B: $envBLabel</h3>
      <div class="url">$($envBInfo.url)</div>
$(if ($envBInfo.release) { "      <span class=`"badge $(if ($envBInfo.release -match 'Early') {'badge-early'} else {'badge-standard'})`">$($envBInfo.release)</span>" })
$(if ($envBInfo.type) { "      <span class=`"badge $(if ($envBInfo.type -match 'Trial') {'badge-trial'} else {'badge-prod'})`">$($envBInfo.type)</span>" })
    </div>
  </div>

"@

# Calculate totals
$totalAOnly = ($results | ForEach-Object { $_.aOnly.Count } | Measure-Object -Sum).Sum
$totalBOnly = ($results | ForEach-Object { $_.bOnly.Count } | Measure-Object -Sum).Sum
$totalBoth  = ($results | ForEach-Object { $_.both.Count }  | Measure-Object -Sum).Sum
$totalDiffs = ($results | ForEach-Object { $_.diffs.Count } | Measure-Object -Sum).Sum

$html += @"

  <!-- Score bar -->
  <div class="score-bar">
    <div class="score-item"><div class="num num-a">$totalAOnly</div><div class="label">A-Only Items</div></div>
    <div class="score-item"><div class="num num-b">$totalBOnly</div><div class="label">B-Only Items</div></div>
    <div class="score-item"><div class="num num-match">$totalBoth</div><div class="label">Matching Items</div></div>
    <div class="score-item"><div class="num num-diff">$totalDiffs</div><div class="label">Version Differences</div></div>
  </div>

  <!-- Toolbar -->
  <div class="toolbar">
    <button onclick="toggleAll(true)">Expand All</button>
    <button onclick="toggleAll(false)">Collapse All</button>
  </div>

"@

# Render each category
foreach ($r in $results) {
    $hasAOnly = $r.aOnly.Count -gt 0
    $hasBOnly = $r.bOnly.Count -gt 0
    $hasDiffs = $r.diffs.Count -gt 0
    $hasError = $null -ne $r.error

    $html += @"
  <div class="category">
    <div class="cat-header" onclick="toggleCat(this)">
      <h3><span class="chevron">&#9654;</span> &nbsp;$($r.category)</h3>
      <div class="cat-badges">
        <span class="badge-match">$($r.both.Count) match</span>
$(if ($hasAOnly) { "        <span class=`"badge-aonly`">$($r.aOnly.Count) A-only</span>" })
$(if ($hasBOnly) { "        <span class=`"badge-bonly`">$($r.bOnly.Count) B-only</span>" })
$(if ($hasDiffs) { "        <span class=`"badge-diffs`">$($r.diffs.Count) diffs</span>" })
$(if ($hasError) { "        <span class=`"badge-error`">error</span>" })
      </div>
    </div>
    <div class="cat-body">

"@

    if ($hasError) {
        $html += "      <p style=`"color:var(--danger);padding:12px`">Error: $($r.error)</p>`n"
    }

    # A-only table
    if ($hasAOnly) {
        $html += @"
      <div class="diff-section">
        <h4 class="a-only">Only in $envALabel ($($r.aOnly.Count))</h4>
        <table><thead><tr><th>Name</th><th>Key</th></tr></thead><tbody>

"@
        foreach ($item in ($r.aOnly | Sort-Object { $_.display })) {
            $html += "          <tr><td>$($item.display)</td><td style=`"color:var(--text-secondary)`">$($item.key)</td></tr>`n"
        }
        $html += "        </tbody></table></div>`n"
    }

    # B-only table
    if ($hasBOnly) {
        $html += @"
      <div class="diff-section">
        <h4 class="b-only">Only in $envBLabel ($($r.bOnly.Count))</h4>
        <table><thead><tr><th>Name</th><th>Key</th></tr></thead><tbody>

"@
        foreach ($item in ($r.bOnly | Sort-Object { $_.display })) {
            $html += "          <tr><td>$($item.display)</td><td style=`"color:var(--text-secondary)`">$($item.key)</td></tr>`n"
        }
        $html += "        </tbody></table></div>`n"
    }

    # Diffs table
    if ($hasDiffs) {
        $html += @"
      <div class="diff-section">
        <h4 class="diffs">Version / State Differences ($($r.diffs.Count))</h4>
        <table><thead><tr><th>Name</th><th>Field</th><th>$envALabel</th><th>$envBLabel</th></tr></thead><tbody>

"@
        foreach ($d in ($r.diffs | Sort-Object { $_.display })) {
            $html += "          <tr><td>$($d.display)</td><td>$($d.field)</td><td class=`"val-a`">$($d.valueA)</td><td class=`"val-b`">$($d.valueB)</td></tr>`n"
        }
        $html += "        </tbody></table></div>`n"
    }

    # Close category
    if (-not $hasAOnly -and -not $hasBOnly -and -not $hasDiffs -and -not $hasError) {
        $html += "      <p style=`"padding:12px;color:var(--success)`">&#10003; Environments are identical for this category.</p>`n"
    }

    $html += "    </div>`n  </div>`n`n"
}

# Data comparison section
if ($IncludeData -and $dataResults.Count -gt 0) {
    $html += @"
  <div class="category" style="margin-top:32px">
    <div class="cat-header" onclick="toggleCat(this)">
      <h3><span class="chevron">&#9654;</span> &nbsp;Demo Data Record Counts</h3>
      <div class="cat-badges"><span class="badge-match">$($dataResults.Count) tables</span></div>
    </div>
    <div class="cat-body">
      <table class="data-table">
        <thead><tr><th>Table</th><th style="text-align:right">$envALabel</th><th style="text-align:right">$envBLabel</th><th style="text-align:right">Delta</th></tr></thead>
        <tbody>

"@
    foreach ($d in $dataResults) {
        $deltaClass = if ($d.delta -gt 0) { "positive" } elseif ($d.delta -lt 0) { "negative" } else { "zero" }
        $deltaStr = if ($d.delta -gt 0) { "+$($d.delta)" } else { "$($d.delta)" }
        $html += "          <tr><td>$($d.name)</td><td style=`"text-align:right`">$($d.countA)</td><td style=`"text-align:right`">$($d.countB)</td><td style=`"text-align:right`" class=`"$deltaClass`">$deltaStr</td></tr>`n"
    }
    $html += "        </tbody></table>`n    </div>`n  </div>`n"
}

# Close HTML
$html += @"

</div>

<script>
function toggleCat(header) {
  const body = header.nextElementSibling;
  const chevron = header.querySelector('.chevron');
  body.classList.toggle('open');
  chevron.classList.toggle('open');
}
function toggleAll(open) {
  document.querySelectorAll('.cat-body').forEach(b => {
    if (open) b.classList.add('open'); else b.classList.remove('open');
  });
  document.querySelectorAll('.chevron').forEach(c => {
    if (open) c.classList.add('open'); else c.classList.remove('open');
  });
}
</script>
</body>
</html>
"@

# ============================================================
# Write file
# ============================================================
$html | Out-File -FilePath $OutputPath -Encoding utf8 -Force
$fullPath = (Resolve-Path $OutputPath).Path
Write-Host ""
Write-Host "Report saved to: $fullPath" -ForegroundColor Green
Write-Host "Open in browser to view the comparison." -ForegroundColor DarkGray
Write-Host ""
