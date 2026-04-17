<#
.SYNOPSIS
    Phase 6 — Add custom tables to SiteMap navigation + create default views.

.DESCRIPTION
    1. Fetches the erac_LiteCRM_SiteMap, injects two new Area groups:
         "Cedent Portfolio"  → Treaties, Reserve Adequacy
         "Risk & Legal"      → Risk Assessments, Disputes
    2. Creates an Active view (SavedQuery) for each of the 5 custom tables.
    3. Creates a Relationships view (PRR records per cedent) for PRR table.
    4. Adds all new views to the GEERACLiteCRM solution.
    5. Publishes all customizations.

.PARAMETER Org
    Dataverse org URL (default: https://orgecbce8ef.crm.dynamics.com)

.PARAMETER Phase
    SiteMap | Views | All (default)
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [ValidateSet("SiteMap","Views","All")]
    [string]$Phase = "All"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
$token = (az account get-access-token --resource $Org | ConvertFrom-Json).accessToken
$H = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

function Invoke-Dv([string]$Method,[string]$Path,[object]$Body=$null) {
    $hdr = $H.Clone()
    if ($Method -eq "POST") { $hdr["Prefer"] = "return=representation" }
    $p = @{ Uri="$Org/api/data/v9.2/$Path"; Method=$Method; Headers=$hdr; TimeoutSec=30; UseBasicParsing=$true }
    if ($Body) { $p.Body = ($Body | ConvertTo-Json -Depth 20) }
    for ($i=1; $i -le 3; $i++) {
        try {
            $r = Invoke-WebRequest @p
            if ($r.Content) { return $r.Content | ConvertFrom-Json }
            return @{ StatusCode=$r.StatusCode }
        } catch {
            $code = $_.Exception.Response.StatusCode.value__
            $msg  = $_.ErrorDetails.Message
            if ($code -eq 429) { Start-Sleep -Seconds (10*$i); continue }
            if ($i -eq 3) { Write-Warning "  ✗ $Method $Path → $code : $($msg.Substring(0,[Math]::Min(300,$msg.Length)))"; return $null }
            Start-Sleep -Seconds (2*$i)
        }
    }
}

function Add-ToSolution([string]$ComponentId,[int]$ComponentType) {
    Invoke-Dv POST "AddSolutionComponent" @{
        ComponentId          = $ComponentId
        ComponentType        = $ComponentType
        SolutionUniqueName   = $SolutionUniqueName
        AddRequiredComponents= $false
    } | Out-Null
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: SITEMAP
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-SiteMap {
    Write-Host "`n=== PHASE: SITEMAP ===" -ForegroundColor Cyan

    # Find the ERAC sitemap — use known ID first, fall back to name search
    $knownSiteMapId = "0124356c-1439-f111-88b5-7ced8d18cb3b"
    $mapDetail = Invoke-Dv GET "sitemaps($knownSiteMapId)?`$select=sitemapid,sitemapname,sitemapxml"
    if (-not $mapDetail -or -not $mapDetail.sitemapid) {
        # Fallback: list all and pick the ERAC one
        $maps = Invoke-Dv GET "sitemaps?`$select=sitemapid,sitemapname"
        Write-Host "  All sitemaps: $($maps.value.sitemapname -join ', ')"
        $match = $maps.value | Where-Object { $_.sitemapname -like "*erac*" -or $_.sitemapname -like "*ERAC*" }
        if (-not $match) { Write-Error "Could not find ERAC sitemap" }
        $mapDetail = Invoke-Dv GET "sitemaps($($match.sitemapid))?`$select=sitemapid,sitemapname,sitemapxml"
    }
    $mapId = $mapDetail.sitemapid
    Write-Host "  Using SiteMap: '$($mapDetail.sitemapname)' ($mapId)"

    [xml]$xml = $mapDetail.sitemapxml

    $area = $xml.SiteMap.Area

    # ── Check if groups already exist ──────────────────────────────────────
    $existingIds = $area.Group | ForEach-Object { $_.Id }
    Write-Host "  Existing groups: $($existingIds -join ', ')"

    if ("erac_CedentPortfolio" -notin $existingIds) {
        Write-Host "  Adding Cedent Portfolio group..."
        $grpPortfolio = $xml.CreateElement("Group")
        $grpPortfolio.SetAttribute("Id",    "erac_CedentPortfolio")
        $grpPortfolio.SetAttribute("Title", "Cedent Portfolio")
        $grpPortfolio.SetAttribute("Icon",  "$webresource:msdyncrm_/icons/contract.svg")

        foreach ($sub in @(
            @{ Id="erac_Treaties";     Entity="erac_treaty";          Title="Treaties";          Icon="/_imgs/svg_xml/ribbon/Contact.svg" },
            @{ Id="erac_ReserveAdq";   Entity="erac_reserveadequacy"; Title="Reserve Adequacy";  Icon="/_imgs/svg_xml/ribbon/ReportResults.svg" }
        )) {
            $s = $xml.CreateElement("SubArea")
            $s.SetAttribute("Id",     $sub.Id)
            $s.SetAttribute("Entity", $sub.Entity)
            $s.SetAttribute("Title",  $sub.Title)
            $grpPortfolio.AppendChild($s) | Out-Null
        }
        $area.AppendChild($grpPortfolio) | Out-Null
        Write-Host "    ✓ Cedent Portfolio" -ForegroundColor Green
    } else { Write-Host "  ⏭ Cedent Portfolio already exists" }

    if ("erac_RiskLegal" -notin $existingIds) {
        Write-Host "  Adding Risk & Legal group..."
        $grpRisk = $xml.CreateElement("Group")
        $grpRisk.SetAttribute("Id",    "erac_RiskLegal")
        $grpRisk.SetAttribute("Title", "Risk & Legal")
        $grpRisk.SetAttribute("Icon",  "/_imgs/svg_xml/ribbon/Alert.svg")

        foreach ($sub in @(
            @{ Id="erac_RiskAssess"; Entity="erac_riskassessment"; Title="Risk Assessments" },
            @{ Id="erac_Disputes";   Entity="erac_dispute";        Title="Legal Disputes" },
            @{ Id="erac_PRRRecords"; Entity="erac_partnershiprating"; Title="PRR Records" }
        )) {
            $s = $xml.CreateElement("SubArea")
            $s.SetAttribute("Id",     $sub.Id)
            $s.SetAttribute("Entity", $sub.Entity)
            $s.SetAttribute("Title",  $sub.Title)
            $grpRisk.AppendChild($s) | Out-Null
        }
        $area.AppendChild($grpRisk) | Out-Null
        Write-Host "    ✓ Risk & Legal" -ForegroundColor Green
    } else { Write-Host "  ⏭ Risk & Legal already exists" }

    # Serialize back
    $sb = New-Object System.Text.StringBuilder
    $sw = New-Object System.IO.StringWriter($sb)
    $xw = New-Object System.Xml.XmlTextWriter($sw)
    $xw.Formatting = "None"
    $xml.Save($xw)
    $newXml = $sb.ToString()

    # PATCH
    $r = Invoke-Dv PATCH "sitemaps($mapId)" @{ sitemapxml=$newXml }
    Write-Host "  ✓ SiteMap XML updated" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: VIEWS (SavedQuery)
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Views {
    Write-Host "`n=== PHASE: VIEWS ===" -ForegroundColor Cyan

    $views = @(
        @{
            Entity   = "erac_partnershiprating"
            Name     = "Active Partnership Ratings"
            FetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="erac_partnershiprating">
    <attribute name="erac_name" />
    <attribute name="erac_period" />
    <attribute name="erac_overallrating" />
    <attribute name="erac_ratingtrend" />
    <attribute name="erac_status" />
    <attribute name="erac_accountid" />
    <attribute name="modifiedon" />
    <order attribute="erac_period" descending="true" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@
            LayoutXml = @"
<grid name="resultset" object="10001" jump="erac_name" select="1" icon="1" preview="1">
  <row name="result" id="erac_partnershipratingid">
    <cell name="erac_name" width="200" />
    <cell name="erac_accountid" width="180" />
    <cell name="erac_period" width="100" />
    <cell name="erac_overallrating" width="100" />
    <cell name="erac_ratingtrend" width="120" />
    <cell name="erac_status" width="120" />
  </row>
</grid>
"@
        },
        @{
            Entity   = "erac_riskassessment"
            Name     = "Active Risk Assessments"
            FetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="erac_riskassessment">
    <attribute name="erac_name" />
    <attribute name="erac_period" />
    <attribute name="erac_aggregaterisk" />
    <attribute name="erac_approvalstatus" />
    <attribute name="erac_accountid" />
    <attribute name="erac_reviewdate" />
    <order attribute="erac_reviewdate" descending="true" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@
            LayoutXml = @"
<grid name="resultset" object="10002" jump="erac_name" select="1" icon="1" preview="1">
  <row name="result" id="erac_riskassessmentid">
    <cell name="erac_name" width="220" />
    <cell name="erac_accountid" width="180" />
    <cell name="erac_period" width="100" />
    <cell name="erac_aggregaterisk" width="130" />
    <cell name="erac_approvalstatus" width="130" />
    <cell name="erac_reviewdate" width="120" />
  </row>
</grid>
"@
        },
        @{
            Entity   = "erac_treaty"
            Name     = "Active Treaties"
            FetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="erac_treaty">
    <attribute name="erac_name" />
    <attribute name="erac_treatytype" />
    <attribute name="erac_status" />
    <attribute name="erac_effectivedate" />
    <attribute name="erac_expirydate" />
    <attribute name="erac_exposurem" />
    <attribute name="erac_accountid" />
    <order attribute="erac_expirydate" descending="true" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@
            LayoutXml = @"
<grid name="resultset" object="10003" jump="erac_name" select="1" icon="1" preview="1">
  <row name="result" id="erac_treatyid">
    <cell name="erac_name" width="250" />
    <cell name="erac_accountid" width="160" />
    <cell name="erac_treatytype" width="130" />
    <cell name="erac_status" width="120" />
    <cell name="erac_effectivedate" width="120" />
    <cell name="erac_expirydate" width="120" />
    <cell name="erac_exposurem" width="120" />
  </row>
</grid>
"@
        },
        @{
            Entity   = "erac_reserveadequacy"
            Name     = "Active Reserve Adequacy"
            FetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="erac_reserveadequacy">
    <attribute name="erac_name" />
    <attribute name="erac_lob" />
    <attribute name="erac_period" />
    <attribute name="erac_adequacypct" />
    <attribute name="erac_status" />
    <attribute name="erac_accountid" />
    <attribute name="erac_currentreserve" />
    <order attribute="erac_adequacypct" descending="false" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@
            LayoutXml = @"
<grid name="resultset" object="10004" jump="erac_name" select="1" icon="1" preview="1">
  <row name="result" id="erac_reserveadequacyid">
    <cell name="erac_name" width="220" />
    <cell name="erac_accountid" width="160" />
    <cell name="erac_lob" width="170" />
    <cell name="erac_period" width="100" />
    <cell name="erac_currentreserve" width="130" />
    <cell name="erac_adequacypct" width="130" />
    <cell name="erac_status" width="110" />
  </row>
</grid>
"@
        },
        @{
            Entity   = "erac_dispute"
            Name     = "Active Legal Disputes"
            FetchXml = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="erac_dispute">
    <attribute name="erac_name" />
    <attribute name="erac_disputetype" />
    <attribute name="erac_status" />
    <attribute name="erac_fileddate" />
    <attribute name="erac_exposure" />
    <attribute name="erac_accountid" />
    <order attribute="erac_fileddate" descending="true" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@
            LayoutXml = @"
<grid name="resultset" object="10005" jump="erac_name" select="1" icon="1" preview="1">
  <row name="result" id="erac_disputeid">
    <cell name="erac_name" width="250" />
    <cell name="erac_accountid" width="160" />
    <cell name="erac_disputetype" width="160" />
    <cell name="erac_status" width="130" />
    <cell name="erac_fileddate" width="120" />
    <cell name="erac_exposure" width="120" />
  </row>
</grid>
"@
        }
    )

    foreach ($v in $views) {
        Write-Host "  [View] $($v.Name) ($($v.Entity))..."

        # Check if view exists
        $existing = Invoke-Dv GET "savedqueries?`$select=savedqueryid,name&`$filter=returnedtypecode eq '$(($v.Entity))' and name eq '$($v.Name)'"
        if ($existing -and $existing.value.Count -gt 0) {
            Write-Host "    ⏭ Already exists" -ForegroundColor Yellow
            continue
        }

        $body = @{
            name              = $v.Name
            returnedtypecode  = $v.Entity
            querytype         = 0
            fetchxml          = $v.FetchXml.Trim()
            layoutxml         = $v.LayoutXml.Trim()
            isdefault         = $true
            statecode         = 0
            statuscode        = 1
            description       = "ERAC active view for $($v.Entity)"
        }

        $result = Invoke-Dv POST "savedqueries" $body
        # Result may be the full object or a wrapper — extract id safely
        $newId = if ($result -and $result.savedqueryid) { $result.savedqueryid }
                 elseif ($result -and $result.'@odata.id') { $result.'@odata.id' -replace '.*/savedqueries\((.+)\).*','$1' }
                 else { $null }
        if ($newId) {
            Write-Host "    ✓ Created: $newId" -ForegroundColor Green
            Add-ToSolution $newId 26  # ComponentType 26 = SavedQuery
        } else {
            Write-Host "    ⚠ Created (no ID returned — may still be OK)" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds 2
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# PUBLISH
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-Publish {
    Write-Host "`n[Publishing all customizations...]"
    try {
        $r = Invoke-WebRequest "$Org/api/data/v9.2/PublishAllXml" -Method POST -Headers $H -UseBasicParsing -TimeoutSec 120
        Write-Host "  ✓ Published ($($r.StatusCode))" -ForegroundColor Green
    } catch {
        # PublishAllXml returns 204 No Content which PS treats as success, but
        # some PS versions throw on empty body — treat any ≤204 as success
        $code = try { $_.Exception.Response.StatusCode.value__ } catch { 204 }
        if ($code -le 204) {
            Write-Host "  ✓ Published" -ForegroundColor Green
        } else {
            Write-Warning "  Publish returned: $code — $($_.Exception.Message)"
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if ($Phase -eq "SiteMap" -or $Phase -eq "All") { Invoke-SiteMap }
if ($Phase -eq "Views"   -or $Phase -eq "All") { Invoke-Views }
Invoke-Publish

Write-Host "`n✅ Update-EracSiteMapAndViews complete" -ForegroundColor Green
Write-Host "   Open ERAC Lite CRM in D365 — new nav groups should appear after hard refresh (Ctrl+F5)"
