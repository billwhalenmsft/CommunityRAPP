<#
.SYNOPSIS
    ERAC Lite CRM — Solution builder script
    Adds ERAC components to an existing Power Platform solution and creates
    the Model Driven App with filtered views and sitemap.

.DESCRIPTION
    Targets the pre-created "GE - ERAC Lite CRM" solution in make.powerapps.com.
    Adds: ERAC custom columns, filtered views, AppModule, SiteMap.

    Auth: uses `az login` — run once before executing this script.

.PARAMETER OrgUrl
    Dataverse org URL, e.g. https://orgecbce8ef.crm.dynamics.com

.PARAMETER SolutionId
    Power Platform solution GUID (from make.powerapps.com URL)

.PARAMETER Phase
    AddColumns | CreateViews | CreateApp | All (default: All)

.EXAMPLE
    .\Build-EracSolution.ps1 `
        -OrgUrl "https://orgecbce8ef.crm.dynamics.com" `
        -SolutionId "cac04215-1339-f111-88b5-6045bda80a72"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$OrgUrl,

    [Parameter(Mandatory=$true)]
    [string]$SolutionId,

    [ValidateSet("AddColumns","CreateViews","CreateApp","All")]
    [string]$Phase = "All",

    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$ApiUrl   = "$OrgUrl/api/data/v9.2"
$ScriptDir = $PSScriptRoot

Write-Host "`nERAC Lite CRM — Solution Builder" -ForegroundColor Cyan
Write-Host "Org: $OrgUrl"
Write-Host "Solution: $SolutionId"
Write-Host "Phase: $Phase`n"

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
function Get-DataverseToken {
    $resource = $OrgUrl.TrimEnd('/')
    $tokenJson = az account get-access-token --resource $resource 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Error "Auth failed. Run: az login --scope $resource/.default" }
    return ($tokenJson | ConvertFrom-Json).accessToken
}

function Get-Headers {
    param([string]$SolutionUniqueName = "")
    $token = Get-DataverseToken
    $h = @{
        "Authorization"    = "Bearer $token"
        "Accept"           = "application/json"
        "Content-Type"     = "application/json; charset=utf-8"
        "OData-MaxVersion" = "4.0"
        "OData-Version"    = "4.0"
        "Prefer"           = "return=representation"
    }
    if ($SolutionUniqueName) { $h["MSCRM.SolutionUniqueName"] = $SolutionUniqueName }
    return $h
}

function Invoke-Dv {
    param([string]$Method, [string]$Path, [object]$Body, [string]$SolutionUniqueName = "")
    $uri = "$ApiUrl/$Path"
    if ($WhatIf -and $Method -ne "GET") { Write-Host "[WhatIf] $Method $uri"; return $null }
    $headers   = Get-Headers -SolutionUniqueName $SolutionUniqueName
    $timeoutSec = if ($Path -match "EntityDefinitions|PublishAllXml|appmodules|sitemaps") { 90 } else { 30 }
    $maxRetries = 4
    for ($attempt = 1; $attempt -le $maxRetries; $attempt++) {
        try {
            $params = @{ Method=$Method; Uri=$uri; Headers=$headers; TimeoutSec=$timeoutSec; UseBasicParsing=$true }
            if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 20) }
            $resp = Invoke-WebRequest @params
            if ($resp.Content) { return $resp.Content | ConvertFrom-Json } else { return $null }
        } catch {
            $msg    = $_.Exception.Message
            $status = $null
            try { $status = $_.Exception.Response.StatusCode.value__ } catch {}
            if ($msg -match "already exists|duplicate|0x80040220") {
                Write-Host "    ↳ Already exists, skipping" -ForegroundColor DarkGray
                return $null
            }
            if ($status -eq 429 -or $msg -match "429") {
                $retryAfter = 10
                try { $retryAfter = [int]$_.Exception.Response.Headers["Retry-After"] } catch {}
                if ($retryAfter -lt 5)  { $retryAfter = 10 }
                if ($retryAfter -gt 120){ $retryAfter = 120 }
                Write-Warning "  Rate limited, waiting ${retryAfter}s (attempt $attempt/$maxRetries)"
                Start-Sleep -Seconds $retryAfter; continue
            }
            if ($attempt -lt $maxRetries -and $msg -match "timeout|canceled") {
                Write-Warning "  Timeout, retry $attempt/$maxRetries"
                Start-Sleep -Seconds 5; continue
            }
            Write-Warning "  API error ($status): $msg"
            return $null
        }
    }
}

# ─────────────────────────────────────────────
# STEP 0 — Resolve solution unique name
# ─────────────────────────────────────────────
function Get-SolutionUniqueName {
    Write-Host "[Solution] Resolving unique name for $SolutionId..." -ForegroundColor Cyan
    $result = Invoke-Dv -Method GET -Path "solutions($SolutionId)?`$select=uniquename,friendlyname,version"
    if (-not $result) { Write-Error "Could not resolve solution. Check the GUID and that you are authenticated." }
    Write-Host "  Found: '$($result.friendlyname)' (unique: $($result.uniquename), v$($result.version))"
    return $result.uniquename
}

# ─────────────────────────────────────────────
# STEP 1 — Add ERAC columns as solution components
# ─────────────────────────────────────────────
function Add-ColumnToSolution {
    param([string]$TableLogicalName, [string]$ColumnLogicalName, [string]$SolutionUniqueName)
    Write-Host "  Adding component: $TableLogicalName.$ColumnLogicalName"
    # Get attribute MetadataId
    $attr = Invoke-Dv -Method GET `
        -Path "EntityDefinitions(LogicalName='$TableLogicalName')/Attributes(LogicalName='$ColumnLogicalName')?`$select=MetadataId,LogicalName"
    if (-not $attr) { Write-Warning "  Could not find column $TableLogicalName.$ColumnLogicalName"; return }

    $body = @{
        ComponentId             = $attr.MetadataId
        ComponentType           = 2          # Attribute
        SolutionUniqueName      = $SolutionUniqueName
        AddRequiredComponents   = $false
        DoNotIncludeSubcomponents = $true
    }
    if ($WhatIf) { Write-Host "[WhatIf] AddSolutionComponent: $($attr.MetadataId)"; return }    $token   = Get-DataverseToken
    $headers = @{
        "Authorization"    = "Bearer $token"
        "Accept"           = "application/json"
        "Content-Type"     = "application/json; charset=utf-8"
        "OData-MaxVersion" = "4.0"
        "OData-Version"    = "4.0"
    }
    try {
        Invoke-WebRequest -Method POST -Uri "$ApiUrl/AddSolutionComponent" `
            -Headers $headers -Body ($body | ConvertTo-Json -Depth 5) `
            -TimeoutSec 30 -UseBasicParsing | Out-Null
        Write-Host "    ✓ Added" -ForegroundColor Green
    } catch {
        $m = $_.Exception.Message
        if ($m -match "already|duplicate") { Write-Host "    ↳ Already in solution" -ForegroundColor DarkGray }
        else { Write-Warning "    Error: $m" }
    }
    Start-Sleep -Milliseconds 500
}

function Invoke-AddColumnsPhase {
    param([string]$SolutionUniqueName)
    Write-Host "`n=== PHASE: ADD COLUMNS TO SOLUTION ===" -ForegroundColor Cyan

    $columns = @(
        @{ Table="account";     Column="erac_iscedent" },
        @{ Table="account";     Column="erac_partnershiptype" },
        @{ Table="account";     Column="erac_portfoliopct" },
        @{ Table="account";     Column="erac_tier" },
        @{ Table="account";     Column="erac_overallrating" },
        @{ Table="account";     Column="erac_lastqbrdate" },
        @{ Table="account";     Column="erac_ratingtrend" },
        @{ Table="contact";     Column="erac_contacttier" },
        @{ Table="contact";     Column="erac_function" },
        @{ Table="contact";     Column="erac_lastcontactdate" },
        @{ Table="contact";     Column="erac_preferredchannel" },
        @{ Table="task";        Column="erac_kanbanstage" },
        @{ Table="task";        Column="erac_engagementtype" },
        @{ Table="appointment"; Column="erac_meetingtype" },
        @{ Table="appointment"; Column="erac_outcome" }
    )

    foreach ($col in $columns) {
        Add-ColumnToSolution -TableLogicalName $col.Table -ColumnLogicalName $col.Column `
            -SolutionUniqueName $SolutionUniqueName
    }
    Write-Host "`n✅ Columns phase complete" -ForegroundColor Green
}

# ─────────────────────────────────────────────
# STEP 2 — Create filtered SavedQuery views
# ─────────────────────────────────────────────
function Invoke-CreateViewsPhase {
    param([string]$SolutionUniqueName)
    Write-Host "`n=== PHASE: CREATE FILTERED VIEWS ===" -ForegroundColor Cyan

    # ── Account: ERAC Cedents — Active ──────────────────────────────────
    Write-Host "[Account] ERAC Cedents — Active"
    $fetchCedentsActive = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="account">
    <attribute name="name" />
    <attribute name="erac_partnershiptype" />
    <attribute name="erac_tier" />
    <attribute name="erac_overallrating" />
    <attribute name="erac_portfoliopct" />
    <attribute name="erac_lastqbrdate" />
    <attribute name="erac_ratingtrend" />
    <attribute name="accountid" />
    <order attribute="erac_overallrating" descending="true" />
    <filter type="and">
      <condition attribute="erac_iscedent" operator="eq" value="1" />
      <condition attribute="statecode"     operator="eq" value="0" />
    </filter>
  </entity>
</fetch>
"@
    $layoutCedentsActive = @"
<grid name="resultset" object="1" jump="name" select="1" icon="1" preview="1">
  <row name="result" id="accountid">
    <cell name="name"                  width="300" />
    <cell name="erac_partnershiptype"  width="150" />
    <cell name="erac_tier"             width="100" />
    <cell name="erac_overallrating"    width="110" />
    <cell name="erac_portfoliopct"     width="110" />
    <cell name="erac_lastqbrdate"      width="130" />
    <cell name="erac_ratingtrend"      width="120" />
  </row>
</grid>
"@
    $view1 = @{
        name             = "ERAC Cedents — Active"
        returnedtypecode = "account"
        querytype        = 0
        fetchxml         = $fetchCedentsActive
        layoutxml        = $layoutCedentsActive
    }
    $r1 = Invoke-Dv -Method POST -Path "savedqueries" -Body $view1 -SolutionUniqueName $SolutionUniqueName
    if ($r1) { Write-Host "  ✓ Created: savedqueryid=$($r1.savedqueryid)" -ForegroundColor Green }

    Start-Sleep -Seconds 2

    # ── Account: ERAC Cedents — All ─────────────────────────────────────
    Write-Host "[Account] ERAC Cedents — All"
    $fetchCedentsAll = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="account">
    <attribute name="name" />
    <attribute name="erac_partnershiptype" />
    <attribute name="erac_tier" />
    <attribute name="erac_overallrating" />
    <attribute name="statecode" />
    <attribute name="accountid" />
    <order attribute="name" descending="false" />
    <filter type="and">
      <condition attribute="erac_iscedent" operator="eq" value="1" />
    </filter>
  </entity>
</fetch>
"@
    $layoutCedentsAll = @"
<grid name="resultset" object="1" jump="name" select="1" icon="1" preview="1">
  <row name="result" id="accountid">
    <cell name="name"                 width="300" />
    <cell name="erac_partnershiptype" width="150" />
    <cell name="erac_tier"            width="100" />
    <cell name="erac_overallrating"   width="110" />
    <cell name="statecode"            width="80"  />
  </row>
</grid>
"@
    $view2 = @{
        name             = "ERAC Cedents — All"
        returnedtypecode = "account"
        querytype        = 0
        fetchxml         = $fetchCedentsAll
        layoutxml        = $layoutCedentsAll
    }
    $r2 = Invoke-Dv -Method POST -Path "savedqueries" -Body $view2 -SolutionUniqueName $SolutionUniqueName
    if ($r2) { Write-Host "  ✓ Created: savedqueryid=$($r2.savedqueryid)" -ForegroundColor Green }

    Start-Sleep -Seconds 2

    # ── Contact: ERAC Contacts — Active ─────────────────────────────────
    Write-Host "[Contact] ERAC Contacts — Active"
    $fetchContactsActive = @"
<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
  <entity name="contact">
    <attribute name="fullname" />
    <attribute name="parentcustomerid" />
    <attribute name="jobtitle" />
    <attribute name="erac_function" />
    <attribute name="erac_contacttier" />
    <attribute name="erac_preferredchannel" />
    <attribute name="contactid" />
    <order attribute="fullname" descending="false" />
    <filter type="and">
      <condition attribute="statecode" operator="eq" value="0" />
    </filter>
    <link-entity name="account" from="accountid" to="parentcustomerid"
                 link-type="inner" alias="cedent">
      <filter type="and">
        <condition attribute="erac_iscedent" operator="eq" value="1" />
      </filter>
    </link-entity>
  </entity>
</fetch>
"@
    $layoutContactsActive = @"
<grid name="resultset" object="2" jump="fullname" select="1" icon="1" preview="1">
  <row name="result" id="contactid">
    <cell name="fullname"              width="200" />
    <cell name="parentcustomerid"      width="200" />
    <cell name="jobtitle"              width="180" />
    <cell name="erac_function"         width="130" />
    <cell name="erac_contacttier"      width="100" />
    <cell name="erac_preferredchannel" width="130" />
  </row>
</grid>
"@
    $view3 = @{
        name             = "ERAC Contacts — Active"
        returnedtypecode = "contact"
        querytype        = 0
        fetchxml         = $fetchContactsActive
        layoutxml        = $layoutContactsActive
    }
    $r3 = Invoke-Dv -Method POST -Path "savedqueries" -Body $view3 -SolutionUniqueName $SolutionUniqueName
    if ($r3) { Write-Host "  ✓ Created: savedqueryid=$($r3.savedqueryid)" -ForegroundColor Green }

    # Save view IDs for AppModule binding
    $viewIds = @{ CedentsActive=$r1.savedqueryid; CedentsAll=$r2.savedqueryid; ContactsActive=$r3.savedqueryid }
    $viewIds | ConvertTo-Json | Set-Content "$ScriptDir\..\data\view-ids.json" -Encoding UTF8
    Write-Host "`n  View IDs saved → data/view-ids.json"
    Write-Host "`n✅ Views phase complete" -ForegroundColor Green
    return $viewIds
}

# ─────────────────────────────────────────────
# STEP 3 — Create AppModule + SiteMap
# ─────────────────────────────────────────────
function Invoke-CreateAppPhase {
    param([string]$SolutionUniqueName)
    Write-Host "`n=== PHASE: CREATE MDA APP MODULE ===" -ForegroundColor Cyan

    # ── SiteMap ─────────────────────────────────────────────────────────
    Write-Host "[SiteMap] Creating ERAC Lite CRM SiteMap..."
    $siteMapXml = @"
<SiteMap>
  <Area Id="erac_main" Title="ERAC CRM" ShowGroups="true">
    <Group Id="cedents_group" Title="Cedents and Contacts">
      <SubArea Id="sub_cedents"  Entity="account"      Title="Cedents"        DefaultDashboard="" />
      <SubArea Id="sub_contacts" Entity="contact"      Title="Contacts"       DefaultDashboard="" />
    </Group>
    <Group Id="engagement_group" Title="Engagement">
      <SubArea Id="sub_appointments" Entity="appointment" Title="Engagement Log"  DefaultDashboard="" />
      <SubArea Id="sub_tasks"        Entity="task"        Title="Kanban Tasks"    DefaultDashboard="" />
    </Group>
    <Group Id="legal_group" Title="Legal">
      <SubArea Id="sub_opportunities" Entity="opportunity" Title="Treaties"     DefaultDashboard="" />
    </Group>
    <Group Id="analytics_group" Title="Analytics">
      <SubArea Id="sub_dashboard" Title="Portfolio Dashboard" Client="All" />
    </Group>
  </Area>
</SiteMap>
"@
    $siteMapBody = @{
        sitemapname    = "ERAC Lite CRM"
        sitemapnameunique = "erac_LiteCRM_SiteMap"
        isappaware     = $true
        sitemapxml     = $siteMapXml
    }
    $sm = Invoke-Dv -Method POST -Path "sitemaps" -Body $siteMapBody -SolutionUniqueName $SolutionUniqueName
    if ($sm) {
        Write-Host "  ✓ SiteMap created: sitemapid=$($sm.sitemapid)" -ForegroundColor Green
    } else {
        Write-Host "  ↳ SiteMap may already exist — querying existing..." -ForegroundColor Yellow
        $existing = Invoke-Dv -Method GET -Path "sitemaps?`$filter=sitemapnameunique eq 'erac_LiteCRM_SiteMap'&`$select=sitemapid"
        if ($existing.value.Count -gt 0) { $sm = $existing.value[0] }
    }

    # ── AppModule — NOTE: must be created in make.powerapps.com ──────────
    Write-Host "[AppModule] ⚠️  AppModule creation requires make.powerapps.com (API restrictions)" -ForegroundColor Yellow
    Write-Host @"

  📋 MANUAL STEPS (2 minutes):
  1. Open your solution:
     https://make.powerapps.com/environments/a3140474-230b-ee2b-8dd8-605a8fe08913/solutions/cac04215-1339-f111-88b5-6045bda80a72

  2. Click '+ New' → 'App' → 'Model-driven app'

  3. Set:
       Name:        ERAC Lite CRM
       Description: GE Verisk ERAC Finance Transformation CRM

  4. App Designer opens:
       a. Navigation → pick 'ERAC Lite CRM' (the sitemap already created above)
       b. Pages → Add pages → Dataverse table:
          Account (uses 'ERAC Cedents — Active' view automatically)
          Contact (uses 'ERAC Contacts — Active' view automatically)
          Appointment, Task
       c. Save → Publish

"@

    if ($sm) {
        @{ sitemapid=$sm.sitemapid; note="AppModule: create manually in make.powerapps.com" } |
            ConvertTo-Json | Set-Content "$ScriptDir\..\data\app-ids.json" -Encoding UTF8
        Write-Host "  SiteMap ID ($($sm.sitemapid)) saved to data/app-ids.json"
    }
    Write-Host "`n✅ App phase complete (SiteMap done, AppModule: see manual steps above)" -ForegroundColor Green
}

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
$uniqueName = Get-SolutionUniqueName

if ($Phase -eq "AddColumns" -or $Phase -eq "All") { Invoke-AddColumnsPhase -SolutionUniqueName $uniqueName }
if ($Phase -eq "CreateViews" -or $Phase -eq "All") { Invoke-CreateViewsPhase -SolutionUniqueName $uniqueName }
if ($Phase -eq "CreateApp"   -or $Phase -eq "All") { Invoke-CreateAppPhase   -SolutionUniqueName $uniqueName }

Write-Host "`n🎉 Build-EracSolution complete!" -ForegroundColor Cyan
Write-Host "Next: Open https://make.powerapps.com/environments/a3140474-230b-ee2b-8dd8-605a8fe08913/solutions/cac04215-1339-f111-88b5-6045bda80a72 to see all components`n"
