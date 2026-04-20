<#
.SYNOPSIS
    Phase B — Create 15 saved views (3 per custom entity) and 2 charts.
    Idempotent: checks by name before creating.

.DESCRIPTION
    Views (3 per entity × 5 entities = 15):
      - Active <Entity>          — statecode eq 0
      - My <Entity>              — ownerid eq @CurrentUser
      - <Entity> by Cedent       — sorted by parent account

    Charts (2):
      - Treaty Exposure by Cedent  (column, on erac_treaty)
      - Reserve Adequacy Distribution (doughnut, on erac_reserveadequacy)

    All components are added to the GEERACLiteCRM solution and published.

.PARAMETER Org
    Dataverse org URL (default: https://orgecbce8ef.crm.dynamics.com)
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── AUTH ─────────────────────────────────────────────────────────────────────
$token = (az account get-access-token --resource $Org | ConvertFrom-Json).accessToken
$H = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

function Invoke-Dv {
    param([string]$Method,[string]$Path,[object]$Body=$null,[switch]$ReturnRaw)
    $hdr = $H.Clone()
    if ($Method -eq "POST") { $hdr["Prefer"] = "return=representation" }
    $p = @{ Uri="$Org/api/data/v9.2/$Path"; Method=$Method; Headers=$hdr; TimeoutSec=60; UseBasicParsing=$true }
    if ($Body) { $p.Body = ($Body | ConvertTo-Json -Depth 20) }
    try {
        $r = Invoke-WebRequest @p
        if ($ReturnRaw) { return $r }
        if ($r.Content) { return $r.Content | ConvertFrom-Json }
        return @{ ok=$true }
    } catch {
        $code = try { $_.Exception.Response.StatusCode.value__ } catch { 0 }
        $msg  = try { $_.ErrorDetails.Message } catch { $_.Exception.Message }
        Write-Warning "  ✗ $Method $Path → $code : $($msg.Substring(0,[Math]::Min(300,$msg.Length)))"
        return $null
    }
}

function Add-ToSolution([string]$ComponentId,[int]$ComponentType) {
    Invoke-Dv POST "AddSolutionComponent" @{
        ComponentId           = $ComponentId
        ComponentType         = $ComponentType
        SolutionUniqueName    = $SolutionUniqueName
        AddRequiredComponents = $false
    } | Out-Null
}

# ─── ENTITY DEFINITIONS ───────────────────────────────────────────────────────
# Each: logical name, set name, primary cols list (for view layout), display label
$entities = @(
    @{
        logical="erac_treaty"; set="erac_treaties"; etc=10001
        label="Treaty";  labelPl="Treaties"
        cols = @("erac_name","erac_treatytype","erac_effectivedate","erac_expirydate","erac_exposurem","erac_status")
        widths = @(200,120,110,110,110,100)
    },
    @{
        logical="erac_reserveadequacy"; set="erac_reserveadequacies"; etc=10002
        label="Reserve Adequacy Record"; labelPl="Reserve Adequacy Records"
        cols = @("erac_name","erac_lob","erac_period","erac_currentreserve","erac_recreserve","erac_adequacypct","erac_status")
        widths = @(200,120,100,120,120,90,100)
    },
    @{
        logical="erac_partnershiprating"; set="erac_partnershipratings"; etc=10003
        label="Partnership Rating"; labelPl="Partnership Ratings"
        cols = @("erac_name","erac_period","erac_overallrating","erac_ratingtrend","erac_lastqbrdate","erac_status")
        widths = @(200,100,110,100,110,100)
    },
    @{
        logical="erac_riskassessment"; set="erac_riskassessments"; etc=10004
        label="Risk Assessment"; labelPl="Risk Assessments"
        cols = @("erac_name","erac_period","erac_aggregaterisk","erac_financialrisk","erac_approvalstatus","erac_reviewdate")
        widths = @(200,100,110,110,110,110)
    },
    @{
        logical="erac_dispute"; set="erac_disputes"; etc=10005
        label="Legal Dispute"; labelPl="Legal Disputes"
        cols = @("erac_name","erac_disputetype","erac_fileddate","erac_exposure","erac_status")
        widths = @(220,120,110,110,100)
    }
)

# ─── BUILD FETCHXML + LAYOUTXML HELPERS ───────────────────────────────────────
function Build-FetchXml {
    param([string]$entity,[string[]]$cols,[string]$filter,[string]$orderBy="erac_name",[bool]$orderDesc=$false)
    $colXml = ($cols | ForEach-Object { "    <attribute name='$_' />" }) -join "`n"
    $orderDir = if ($orderDesc) { "true" } else { "false" }
    $filterXml = if ($filter) { "  <filter type='and'>`n$filter`n  </filter>" } else { "" }
    @"
<fetch version='1.0' output-format='xml-platform' mapping='logical' distinct='false'>
  <entity name='$entity'>
$colXml
    <attribute name='createdon' />
    <order attribute='$orderBy' descending='$orderDir' />
$filterXml
  </entity>
</fetch>
"@
}

function Build-LayoutXml {
    param([string]$entity,[int]$etc,[string[]]$cols,[int[]]$widths)
    $cells = ""
    for ($i=0; $i -lt $cols.Count; $i++) {
        $w = $widths[$i]
        $cells += "    <cell name='$($cols[$i])' width='$w' />`n"
    }
    @"
<grid name='resultset' object='$etc' jump='erac_name' select='1' icon='1' preview='1'>
  <row name='result' id='$($entity)id'>
$cells  </row>
</grid>
"@
}

# ─── SAVED QUERY CREATION ─────────────────────────────────────────────────────
function New-SavedQuery {
    param(
        [string]$Name,
        [string]$Description,
        [string]$Entity,
        [int]$Etc,
        [string]$FetchXml,
        [string]$LayoutXml,
        [int]$QueryType = 0   # 0 = Public View
    )
    # Idempotent check
    $esc = $Name.Replace("'","''")
    $exists = Invoke-Dv GET "savedqueries?`$filter=name eq '$esc' and returnedtypecode eq '$Entity'&`$select=savedqueryid"
    if ($exists -and $exists.value -and $exists.value.Count -gt 0) {
        Write-Host "  ↳ View '$Name' already exists ($($exists.value[0].savedqueryid))" -ForegroundColor Yellow
        return $exists.value[0].savedqueryid
    }
    $body = @{
        name             = $Name
        description      = $Description
        returnedtypecode = $Entity
        fetchxml         = $FetchXml
        layoutxml        = $LayoutXml
        querytype        = $QueryType
        isdefault        = $false
        isuserdefined    = $false
    }
    $r = Invoke-Dv POST "savedqueries" $body
    if ($r) {
        $id = $r.savedqueryid
        Write-Host "  ✓ Created view '$Name' ($id)" -ForegroundColor Green
        Add-ToSolution $id 26
        return $id
    }
    return $null
}

# ─── PHASE B.1: VIEWS ─────────────────────────────────────────────────────────
Write-Host "`n=== PHASE B.1: VIEWS ===" -ForegroundColor Cyan
$createdViews = @()

foreach ($e in $entities) {
    Write-Host "`n[$($e.logical)]" -ForegroundColor Cyan

    # 1. Active <Entity>
    $activeName = "Active $($e.labelPl)"
    $activeFetch = Build-FetchXml -entity $e.logical -cols $e.cols `
        -filter "    <condition attribute='statecode' operator='eq' value='0' />" `
        -orderBy "createdon" -orderDesc $true
    $layout = Build-LayoutXml -entity $e.logical -etc $e.etc -cols $e.cols -widths $e.widths
    $id = New-SavedQuery -Name $activeName -Description "Active $($e.labelPl) sorted by created date" `
        -Entity $e.logical -Etc $e.etc -FetchXml $activeFetch -LayoutXml $layout
    if ($id) { $createdViews += $id }

    # 2. My <Entity>
    $myName = "My $($e.labelPl)"
    $myFetch = Build-FetchXml -entity $e.logical -cols $e.cols `
        -filter "    <condition attribute='ownerid' operator='eq-userid' />" `
        -orderBy "modifiedon" -orderDesc $true
    $id = New-SavedQuery -Name $myName -Description "My $($e.labelPl)" `
        -Entity $e.logical -Etc $e.etc -FetchXml $myFetch -LayoutXml $layout
    if ($id) { $createdViews += $id }

    # 3. <Entity> by Cedent
    $byName = "$($e.labelPl) by Cedent"
    $colsWithAcct = @($e.cols) + @("erac_accountid")
    $widthsWithAcct = @($e.widths) + @(180)
    $byLayout = Build-LayoutXml -entity $e.logical -etc $e.etc -cols $colsWithAcct -widths $widthsWithAcct
    $byFetch = Build-FetchXml -entity $e.logical -cols $colsWithAcct -orderBy "erac_accountid" -orderDesc $false
    $id = New-SavedQuery -Name $byName -Description "$($e.labelPl) sorted by cedent" `
        -Entity $e.logical -Etc $e.etc -FetchXml $byFetch -LayoutXml $byLayout
    if ($id) { $createdViews += $id }
}

Write-Host "`n  Total views processed: $($createdViews.Count)" -ForegroundColor Green

# ─── PHASE B.2: CHARTS ────────────────────────────────────────────────────────
Write-Host "`n=== PHASE B.2: CHARTS ===" -ForegroundColor Cyan

function New-Chart {
    param(
        [string]$Name,
        [string]$Description,
        [string]$Entity,
        [string]$DataDescriptionXml,
        [string]$PresentationDescriptionXml
    )
    $esc = $Name.Replace("'","''")
    $exists = Invoke-Dv GET "savedqueryvisualizations?`$filter=name eq '$esc' and primaryentitytypecode eq '$Entity'&`$select=savedqueryvisualizationid"
    if ($exists -and $exists.value -and $exists.value.Count -gt 0) {
        Write-Host "  ↳ Chart '$Name' already exists ($($exists.value[0].savedqueryvisualizationid))" -ForegroundColor Yellow
        return $exists.value[0].savedqueryvisualizationid
    }
    $body = @{
        name                       = $Name
        description                = $Description
        primaryentitytypecode      = $Entity
        datadescription            = $DataDescriptionXml
        presentationdescription    = $PresentationDescriptionXml
    }
    $r = Invoke-Dv POST "savedqueryvisualizations" $body
    if ($r) {
        $id = $r.savedqueryvisualizationid
        Write-Host "  ✓ Created chart '$Name' ($id)" -ForegroundColor Green
        Add-ToSolution $id 59
        return $id
    }
    return $null
}

# Chart 1: Treaty Exposure by Cedent (column)
$treatyData = @"
<datadefinition>
  <fetchcollection>
    <fetch version='1.0' aggregate='true' mapping='logical'>
      <entity name='erac_treaty'>
        <attribute name='erac_exposurem' alias='sum_exposure' aggregate='sum' />
        <link-entity name='account' from='accountid' to='erac_accountid' alias='cedent'>
          <attribute name='name' alias='cedent_name' groupby='true' />
        </link-entity>
        <order alias='sum_exposure' descending='true' />
      </entity>
    </fetch>
  </fetchcollection>
  <categorycollection>
    <category>
      <measurecollection>
        <measure alias='sum_exposure' />
      </measurecollection>
    </category>
  </categorycollection>
</datadefinition>
"@

$treatyPresentation = @"
<Chart Palette='BrightPastel' PaletteCustomColors='59, 117, 208; 234, 137, 12; 87, 153, 87; 175, 79, 79; 105, 91, 167'>
  <Series>
    <Series ChartType='Column' IsValueShownAsLabel='True' Color='59, 117, 208' Font='Segoe UI, 9pt' LabelForeColor='59, 59, 59'>
      <SmartLabelStyle Enabled='True' />
    </Series>
  </Series>
  <ChartAreas>
    <ChartArea BorderColor='White' BorderDashStyle='Solid'>
      <AxisY LineColor='165, 172, 181'>
        <MajorGrid LineColor='219, 219, 219' />
        <LabelStyle Font='Segoe UI, 9pt' />
      </AxisY>
      <AxisX LineColor='165, 172, 181' Interval='1'>
        <MajorGrid Enabled='False' />
        <LabelStyle Font='Segoe UI, 9pt' />
      </AxisX>
    </ChartArea>
  </ChartAreas>
</Chart>
"@

New-Chart -Name "Treaty Exposure by Cedent" `
    -Description "Total treaty exposure (millions) summed per cedent" `
    -Entity "erac_treaty" `
    -DataDescriptionXml $treatyData `
    -PresentationDescriptionXml $treatyPresentation | Out-Null

# Chart 2: Reserve Adequacy Distribution (doughnut)
$reserveData = @"
<datadefinition>
  <fetchcollection>
    <fetch version='1.0' aggregate='true' mapping='logical'>
      <entity name='erac_reserveadequacy'>
        <attribute name='erac_reserveadequacyid' alias='count_id' aggregate='count' />
        <attribute name='erac_status' alias='status_g' groupby='true' />
        <order alias='count_id' descending='true' />
      </entity>
    </fetch>
  </fetchcollection>
  <categorycollection>
    <category>
      <measurecollection>
        <measure alias='count_id' />
      </measurecollection>
    </category>
  </categorycollection>
</datadefinition>
"@

$reservePresentation = @"
<Chart Palette='BrightPastel' PaletteCustomColors='87, 153, 87; 234, 184, 12; 234, 137, 12; 175, 79, 79; 130, 130, 130'>
  <Series>
    <Series ChartType='Doughnut' IsValueShownAsLabel='True' Font='Segoe UI, 9pt' LabelForeColor='59, 59, 59' CustomProperties='DoughnutRadius=60, PieLabelStyle=Outside' />
  </Series>
  <ChartAreas>
    <ChartArea BorderColor='White' BorderDashStyle='Solid' />
  </ChartAreas>
  <Legends>
    <Legend Alignment='Center' Docking='Bottom' Font='Segoe UI, 9pt' LegendStyle='Table' />
  </Legends>
</Chart>
"@

New-Chart -Name "Reserve Adequacy Distribution" `
    -Description "Count of reserve adequacy records grouped by status" `
    -Entity "erac_reserveadequacy" `
    -DataDescriptionXml $reserveData `
    -PresentationDescriptionXml $reservePresentation | Out-Null

# ─── PUBLISH ──────────────────────────────────────────────────────────────────
Write-Host "`n=== PUBLISH ===" -ForegroundColor Cyan
$entityList = ($entities | ForEach-Object { "<entity>$($_.logical)</entity>" }) -join ""
$publishXml = "<importexportxml><entities>$entityList</entities></importexportxml>"
Invoke-Dv POST "PublishXml" @{ ParameterXml = $publishXml } | Out-Null
Write-Host "  ✓ Published all 5 entities" -ForegroundColor Green

Write-Host "`n✅ Add-EracViewsAndCharts complete" -ForegroundColor Green
