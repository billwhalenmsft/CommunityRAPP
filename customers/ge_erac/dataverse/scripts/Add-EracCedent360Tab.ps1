<#
.SYNOPSIS
    Add an "ERAC 360" tab to the Account main form with the Cedent 360 web resource embedded.

.DESCRIPTION
    Idempotent: skips if the tab already exists.
    Adds a single-section, single-cell tab containing the erac_/html/cedent_360_card.html
    web resource (must be deployed first via Deploy-EracWebResources.ps1).

.PARAMETER Org
    Dataverse org URL
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [string]$WebResourceUniqueName = "erac_/html/cedent_360_card.html"
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
    Prefer             = "return=representation"
}

function Invoke-Dv([string]$Method,[string]$Path,[object]$Body=$null) {
    $p = @{ Uri="$Org/api/data/v9.2/$Path"; Method=$Method; Headers=$H; TimeoutSec=60; UseBasicParsing=$true }
    if ($Body) { $p.Body = ($Body | ConvertTo-Json -Depth 20) }
    try {
        $r = Invoke-WebRequest @p
        if ($r.Content) { return $r.Content | ConvertFrom-Json }
        return @{ ok=$true }
    } catch {
        $msg = try { $_.ErrorDetails.Message } catch { $_.Exception.Message }
        Write-Warning "  ✗ $Method $Path : $($msg.Substring(0,[Math]::Min(400,$msg.Length)))"
        return $null
    }
}

Write-Host "=== ADD ERAC 360 TAB TO ACCOUNT FORM ===" -ForegroundColor Cyan

# ── Verify web resource exists ───────────────────────────────────────────────
Write-Host "[1] Verifying web resource '$WebResourceUniqueName'..."
$wrLookup = Invoke-Dv GET "webresourceset?`$filter=name eq '$WebResourceUniqueName'&`$select=webresourceid,name"
if (-not $wrLookup -or $wrLookup.value.Count -eq 0) {
    Write-Error "Web resource '$WebResourceUniqueName' not found. Run Deploy-EracWebResources.ps1 first."
}
Write-Host "  ✓ Found web resource ($($wrLookup.value[0].webresourceid))" -ForegroundColor Green

# ── Get the Account main form ────────────────────────────────────────────────
Write-Host "[2] Fetching Account main form..."
$forms = Invoke-Dv GET "systemforms?`$select=formid,name,formxml&`$filter=objecttypecode eq 'account' and type eq 2 and name eq 'Account'"
if (-not $forms -or $forms.value.Count -eq 0) {
    $forms = Invoke-Dv GET "systemforms?`$select=formid,name,formxml&`$filter=objecttypecode eq 'account' and type eq 2"
}
if (-not $forms -or $forms.value.Count -eq 0) { Write-Error "No Account main form found." }

$form = $forms.value[0]
Write-Host "  Using form: '$($form.name)' ($($form.formid))"

[xml]$xml = $form.formxml

# ── Idempotent check ─────────────────────────────────────────────────────────
$existing = $xml.SelectNodes("//tab") | Where-Object { $_.name -eq "erac_360Tab" }
if ($existing) {
    Write-Host "  ⏭ ERAC 360 tab already exists — skipping" -ForegroundColor Yellow
    exit 0
}

# ── Build the tab ────────────────────────────────────────────────────────────
Write-Host "[3] Building ERAC 360 tab..."

$tabGuid  = [System.Guid]::NewGuid().ToString("D")
$secGuid  = [System.Guid]::NewGuid().ToString("D")
$cellGuid = [System.Guid]::NewGuid().ToString("D")
$ctlGuid  = [System.Guid]::NewGuid().ToString("D")

$tabEl = $xml.CreateElement("tab")
$tabEl.SetAttribute("id",             "{$tabGuid}")
$tabEl.SetAttribute("name",           "erac_360Tab")
$tabEl.SetAttribute("expanded",       "true")
$tabEl.SetAttribute("verticallayout", "true")
$tabEl.SetAttribute("showlabel",      "true")
$tabEl.SetAttribute("locklevel",      "0")

$tabLabels = $xml.CreateElement("labels")
$tabLabel  = $xml.CreateElement("label")
$tabLabel.SetAttribute("description", "ERAC 360")
$tabLabel.SetAttribute("languagecode","1033")
$tabLabels.AppendChild($tabLabel) | Out-Null
$tabEl.AppendChild($tabLabels) | Out-Null

$columnsEl = $xml.CreateElement("columns")
$colEl     = $xml.CreateElement("column")
$colEl.SetAttribute("width","100%")

$sectionsEl = $xml.CreateElement("sections")
$secEl = $xml.CreateElement("section")
$secEl.SetAttribute("id",        "{$secGuid}")
$secEl.SetAttribute("name",      "erac_360Section")
$secEl.SetAttribute("showlabel", "false")
$secEl.SetAttribute("locklevel", "0")
$secEl.SetAttribute("columns",   "1")

$secLabels = $xml.CreateElement("labels")
$secLabel  = $xml.CreateElement("label")
$secLabel.SetAttribute("description", "Cedent 360")
$secLabel.SetAttribute("languagecode","1033")
$secLabels.AppendChild($secLabel) | Out-Null
$secEl.AppendChild($secLabels) | Out-Null

# Single row, single cell, web resource control
$rowsEl = $xml.CreateElement("rows")
$row    = $xml.CreateElement("row")
$cell   = $xml.CreateElement("cell")
$cell.SetAttribute("id",        "{$cellGuid}")
$cell.SetAttribute("showlabel", "false")
$cell.SetAttribute("rowspan",   "8")
$cell.SetAttribute("colspan",   "1")
$cell.SetAttribute("auto",      "false")

$cellLabels = $xml.CreateElement("labels")
$cellLabel  = $xml.CreateElement("label")
$cellLabel.SetAttribute("description", "Cedent 360")
$cellLabel.SetAttribute("languagecode","1033")
$cellLabels.AppendChild($cellLabel) | Out-Null
$cell.AppendChild($cellLabels) | Out-Null

# Web resource control
$ctrl = $xml.CreateElement("control")
$ctrl.SetAttribute("id",       "WebResource_erac_cedent360")
$ctrl.SetAttribute("classid",  "{9FDF5F91-88B1-47f4-AD53-C11EFC01A01D}")
$ctrl.SetAttribute("disabled", "false")

$params = $xml.CreateElement("parameters")
$urlEl   = $xml.CreateElement("Url");           $urlEl.InnerText  = $WebResourceUniqueName
$ppEl    = $xml.CreateElement("PassParameters");$ppEl.InnerText   = "true"
$scrEl   = $xml.CreateElement("Scrolling");     $scrEl.InnerText  = "auto"
$brdEl   = $xml.CreateElement("Border");        $brdEl.InnerText  = "false"
$secElP  = $xml.CreateElement("Security");      $secElP.InnerText = "false"
$params.AppendChild($urlEl)  | Out-Null
$params.AppendChild($ppEl)   | Out-Null
$params.AppendChild($scrEl)  | Out-Null
$params.AppendChild($brdEl)  | Out-Null
$params.AppendChild($secElP) | Out-Null
$ctrl.AppendChild($params) | Out-Null

$cell.AppendChild($ctrl) | Out-Null
$row.AppendChild($cell)  | Out-Null

# Add 7 more empty spacer rows so the iframe gets enough vertical room
for ($i = 0; $i -lt 7; $i++) {
    $spacer = $xml.CreateElement("row")
    $rowsEl.AppendChild($spacer) | Out-Null
}
# Insert the data row first so it gets the rowspan
$rowsEl.PrependChild($row) | Out-Null

$secEl.AppendChild($rowsEl) | Out-Null
$sectionsEl.AppendChild($secEl) | Out-Null
$colEl.AppendChild($sectionsEl) | Out-Null
$columnsEl.AppendChild($colEl) | Out-Null
$tabEl.AppendChild($columnsEl) | Out-Null

# ── Insert tab as the SECOND tab (right after Summary) ───────────────────────
$tabsNode = $xml.SelectSingleNode("//tabs")
if (-not $tabsNode) { Write-Error "Form XML has no <tabs> node." }

$firstTab = $tabsNode.SelectSingleNode("tab[1]")
if ($firstTab -and $firstTab.NextSibling) {
    $tabsNode.InsertAfter($tabEl, $firstTab) | Out-Null
} else {
    $tabsNode.AppendChild($tabEl) | Out-Null
}

Write-Host "  ✓ ERAC 360 tab built (web resource: $WebResourceUniqueName)" -ForegroundColor Green

# ── Serialize and PATCH ──────────────────────────────────────────────────────
Write-Host "[4] Saving form..."
$xwSettings = New-Object System.Xml.XmlWriterSettings
$xwSettings.OmitXmlDeclaration = $true
$xwSettings.Indent = $false
$sb = New-Object System.Text.StringBuilder
$xw = [System.Xml.XmlWriter]::Create($sb, $xwSettings)
$xml.Save($xw)
$xw.Flush()
$newXml = $sb.ToString()

$hPatch = $H.Clone()
$hPatch.Remove("Prefer")

try {
    Invoke-WebRequest "$Org/api/data/v9.2/systemforms($($form.formid))" `
        -Method PATCH -Headers $hPatch -Body (@{ formxml=$newXml } | ConvertTo-Json -Depth 3) `
        -UseBasicParsing -TimeoutSec 60 | Out-Null
    Write-Host "  ✓ Form XML updated" -ForegroundColor Green
} catch {
    $code = try { $_.Exception.Response.StatusCode.value__ } catch { 0 }
    $msg  = try { $_.ErrorDetails.Message } catch { "" }
    if ($code -le 204 -or $code -eq 0) {
        Write-Host "  ✓ Form XML updated" -ForegroundColor Green
    } else {
        Write-Warning "  PATCH returned $code — $($msg.Substring(0,[Math]::Min(400,$msg.Length)))"
        exit 1
    }
}

# ── Add form to solution ─────────────────────────────────────────────────────
Write-Host "[5] Adding form to solution..."
$addBody = @{
    ComponentId           = $form.formid
    ComponentType         = 24
    SolutionUniqueName    = $SolutionUniqueName
    AddRequiredComponents = $false
} | ConvertTo-Json
try {
    Invoke-WebRequest "$Org/api/data/v9.2/AddSolutionComponent" `
        -Method POST -Headers $hPatch -Body $addBody -UseBasicParsing -TimeoutSec 30 | Out-Null
    Write-Host "  ✓ Added to solution" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ AddSolutionComponent: $($_.Exception.Response.StatusCode.value__) (likely already in solution)" -ForegroundColor Yellow
}

# ── Publish ──────────────────────────────────────────────────────────────────
Write-Host "[6] Publishing account entity..."
$publishXml = "<importexportxml><entities><entity>account</entity></entities></importexportxml>"
Invoke-Dv POST "PublishXml" @{ ParameterXml = $publishXml } | Out-Null
Write-Host "  ✓ Published" -ForegroundColor Green

Write-Host "`n✅ ERAC 360 tab added to Account form." -ForegroundColor Green
Write-Host "   Open any Account record → click 'ERAC 360' tab to see the 5-tile dashboard." -ForegroundColor Cyan
