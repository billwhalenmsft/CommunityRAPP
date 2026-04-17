<#
.SYNOPSIS
    Deploy ERAC web resources to Dataverse and add them to the solution.
    Also outputs SiteMap XML with web resource SubAreas for copy/paste into AppModule editor.

.DESCRIPTION
    Uploads erac_prr_dashboard.html and erac_portfolio_analytics.html as web resources
    to the ERAC Dataverse org, adds them to the GEERACLiteCRM solution, and prints
    instructions for wiring them into the MDA App Designer SiteMap.

.PARAMETER Org
    Dataverse org URL (default: https://orgecbce8ef.crm.dynamics.com)

.PARAMETER SolutionUniqueName
    Power Platform solution unique name (default: GEERACLiteCRM)

.PARAMETER Phase
    Which phase to run: UploadResources | PublishResources | All (default)

.EXAMPLE
    .\Deploy-EracWebResources.ps1
    .\Deploy-EracWebResources.ps1 -Phase UploadResources
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [ValidateSet("UploadResources","PublishResources","All")]
    [string]$Phase = "All"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
function Get-Token {
    $raw = az account get-access-token --resource $Org 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Azure CLI not logged in. Run: az login"
    }
    return ($raw | ConvertFrom-Json).accessToken
}

$Token = Get-Token
$Headers = @{
    Authorization    = "Bearer $Token"
    "Content-Type"   = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
    Accept             = "application/json"
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Dv {
    param([string]$Method, [string]$Path, [object]$Body = $null,
          [switch]$ReturnResponse)
    $uri = "$Org/api/data/v9.2/$Path"
    $hdrs = $Headers.Clone()
    $hdrs["MSCRM.SolutionUniqueName"] = $SolutionUniqueName

    $params = @{ Uri=$uri; Method=$Method; Headers=$hdrs; TimeoutSec=60 }
    if ($Body) { $params["Body"] = ($Body | ConvertTo-Json -Depth 10) }

    try {
        if ($ReturnResponse) {
            return Invoke-WebRequest @params
        }
        return Invoke-RestMethod @params
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        $msg  = $_.ErrorDetails.Message
        if ($code -eq 409) {
            Write-Host "    ↳ 409 Conflict — record may already exist" -ForegroundColor Yellow
            return $null
        }
        Write-Warning "  ✗ $Method $Path → $code : $msg"
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# WEB RESOURCE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
$WebResources = @(
    @{
        name        = "erac_prr_dashboard"
        displayName = "ERAC PRR Dashboard"
        description = "Partnership Rating Report — interactive dashboard with radar chart and scorecard"
        webresourcetype = 1   # HTML
        file        = Join-Path $ScriptDir "..\web-resources\erac_prr_dashboard.html"
        uniqueName  = "erac_/html/prr_dashboard.html"
    },
    @{
        name        = "erac_portfolio_analytics"
        displayName = "ERAC Portfolio Analytics"
        description = "Portfolio Analytics — donut chart, bar chart, tier distribution, engagement log"
        webresourcetype = 1   # HTML
        file        = Join-Path $ScriptDir "..\web-resources\erac_portfolio_analytics.html"
        uniqueName  = "erac_/html/portfolio_analytics.html"
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# PHASE: UPLOAD RESOURCES
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-UploadResources {
    Write-Host "`n=== PHASE: UPLOAD WEB RESOURCES ===" -ForegroundColor Cyan
    $results = @{}

    foreach ($wr in $WebResources) {
        Write-Host "[WebResource] $($wr.displayName)..."

        # Read and base64-encode file
        $filePath = Resolve-Path $wr.file -ErrorAction SilentlyContinue
        if (-not $filePath) {
            Write-Warning "  ✗ File not found: $($wr.file)"
            continue
        }
        $bytes   = [System.IO.File]::ReadAllBytes($filePath)
        $content = [Convert]::ToBase64String($bytes)

        # Check if already exists
        $existing = Invoke-Dv -Method GET -Path "webresourceset?`$filter=name eq '$($wr.uniqueName)'&`$select=webresourceid,name"
        $existingId = $null
        if ($existing -and $existing.value.Count -gt 0) {
            $existingId = $existing.value[0].webresourceid
            Write-Host "  ↳ Already exists (id=$existingId) — updating content..." -ForegroundColor Yellow
        }

        $body = @{
            name            = $wr.uniqueName
            displayname     = $wr.displayName
            description     = $wr.description
            webresourcetype = $wr.webresourcetype
            content         = $content
        }

        if ($existingId) {
            # PATCH to update
            $hdrs = $Headers.Clone()
            $hdrs["MSCRM.SolutionUniqueName"] = $SolutionUniqueName
            $uri = "$Org/api/data/v9.2/webresourceset($existingId)"
            try {
                Invoke-RestMethod -Uri $uri -Method PATCH -Headers $hdrs `
                    -Body ($body | ConvertTo-Json -Depth 5) -TimeoutSec 60
                Write-Host "  ✓ Updated: $($wr.displayName) (id=$existingId)" -ForegroundColor Green
                $results[$wr.name] = $existingId
            } catch {
                Write-Warning "  ✗ Update failed: $($_.ErrorDetails.Message)"
            }
        } else {
            # POST to create
            if ($PSCmdlet.ShouldProcess($wr.displayName, "Create web resource")) {
                $resp = Invoke-WebRequest -Uri "$Org/api/data/v9.2/webresourceset" `
                    -Method POST -Headers ($Headers + @{"MSCRM.SolutionUniqueName"=$SolutionUniqueName}) `
                    -Body ($body | ConvertTo-Json -Depth 5) -TimeoutSec 60
                if ($resp.StatusCode -eq 204) {
                    $loc = $resp.Headers["OData-EntityId"]
                    $locStr = if ($loc -is [array]) { $loc[0] } else { "$loc" }
                    $id = "?"
                    if ($locStr -match '\(([a-f0-9\-]{36})\)') { $id = $Matches[1] }
                    Write-Host "  ✓ Created: $($wr.displayName) (id=$id)" -ForegroundColor Green
                    $results[$wr.name] = $id
                } else {
                    Write-Warning "  ✗ Unexpected status: $($resp.StatusCode)"
                }
            }
        }
    }

    # Save IDs
    $idsPath = Join-Path $ScriptDir "..\data\webresource-ids.json"
    $results | ConvertTo-Json | Set-Content $idsPath -Encoding UTF8
    Write-Host "`n  Web resource IDs saved → data/webresource-ids.json" -ForegroundColor Green
    return $results
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE: PUBLISH RESOURCES
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-PublishResources {
    param([hashtable]$Ids)
    Write-Host "`n=== PHASE: PUBLISH WEB RESOURCES ===" -ForegroundColor Cyan

    if (-not $Ids -or $Ids.Count -eq 0) {
        # Try loading from saved file
        $idsPath = Join-Path $ScriptDir "..\data\webresource-ids.json"
        if (Test-Path $idsPath) {
            $loaded = Get-Content $idsPath | ConvertFrom-Json
            $Ids = @{}
            $loaded.PSObject.Properties | ForEach-Object { $Ids[$_.Name] = $_.Value }
        }
    }

    if (-not $Ids -or $Ids.Count -eq 0) {
        Write-Warning "No web resource IDs available. Run UploadResources phase first."
        return
    }

    $paramXml = "<ParameterXml><webresources>"
    $Ids.Values | ForEach-Object { $paramXml += "<webresource>{$_}</webresource>" }
    $paramXml += "</webresources></ParameterXml>"

    $publishBody = @{ ParameterXml = $paramXml }

    Write-Host "  Publishing $($Ids.Count) web resource(s)..."
    if ($PSCmdlet.ShouldProcess("WebResources", "Publish")) {
        $result = Invoke-Dv -Method POST -Path "PublishXml" -Body $publishBody
        if ($null -ne $result) {
            Write-Host "  ✓ Published successfully" -ForegroundColor Green
        } else {
            Write-Host "  ↳ PublishXml returned null — may have timed out. Use Publish All Customizations in maker portal." -ForegroundColor Yellow
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# PRINT SITEMAP UPDATE INSTRUCTIONS
# ─────────────────────────────────────────────────────────────────────────────
function Show-SiteMapInstructions {
    Write-Host "`n=== SITEMAP UPDATE INSTRUCTIONS ===" -ForegroundColor Cyan
    Write-Host @"

  The two web resources are now in Dataverse. To add them to the ERAC MDA navigation:

  OPTION A — App Designer (recommended, 2 minutes):
  ─────────────────────────────────────────────────
  1. Open your MDA app editor:
     https://make.powerapps.com/environments/a3140474-230b-ee2b-8dd8-605a8fe08913/solutions/cac04215-1339-f111-88b5-6045bda80a72

  2. Click the 'ERAC Lite CRM' app → Edit

  3. In App Designer, go to Navigation (left panel) → Edit SiteMap

  4. In the Analytics group, add two SubAreas:
     ┌─────────────────────────────────────────────────────────────────┐
     │  SubArea 1 — PRR Dashboard                                      │
     │    Type: Web Resource                                           │
     │    URL:  /WebResources/erac_/html/prr_dashboard.html           │
     │    Title: PRR Dashboard                                         │
     │    Icon: (leave default)                                        │
     │                                                                  │
     │  SubArea 2 — Portfolio Analytics                                │
     │    Type: Web Resource                                           │
     │    URL:  /WebResources/erac_/html/portfolio_analytics.html     │
     │    Title: Portfolio Analytics                                    │
     └─────────────────────────────────────────────────────────────────┘

  5. Save → Publish

  OPTION B — XML (for advanced users):
  ─────────────────────────────────────
  Add these SubArea elements to the Analytics group in your SiteMap XML:

  <SubArea Id="sub_prr_dashboard"
           Url="/WebResources/erac_/html/prr_dashboard.html"
           Title="PRR Dashboard"
           Client="All" />
  <SubArea Id="sub_portfolio_analytics"
           Url="/WebResources/erac_/html/portfolio_analytics.html"
           Title="Portfolio Analytics"
           Client="All" />

  STANDALONE PREVIEW (no D365 needed):
  ─────────────────────────────────────
  Open in browser directly to preview:
    customers\ge_erac\dataverse\web-resources\erac_prr_dashboard.html
    customers\ge_erac\dataverse\web-resources\erac_portfolio_analytics.html

  When loaded inside D365, they will auto-connect to live Dataverse data via Xrm.WebApi.
  When opened standalone, they display the seeded demo data.

"@
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
$wrIds = @{}
if ($Phase -eq "UploadResources" -or $Phase -eq "All") {
    $wrIds = Invoke-UploadResources
}
if ($Phase -eq "PublishResources" -or $Phase -eq "All") {
    Invoke-PublishResources -Ids $wrIds
}
Show-SiteMapInstructions
Write-Host "`n✅ Deploy-EracWebResources complete" -ForegroundColor Green
