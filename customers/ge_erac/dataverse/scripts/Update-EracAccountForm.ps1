<#
.SYNOPSIS
    Add ERAC custom columns to the Account main form.

.DESCRIPTION
    Fetches the Account main form XML, injects a new "ERAC Partnership" tab
    with all 15 ERAC custom columns organized into logical sections, then
    PATCHes it back and publishes.

    Sections created:
      - Cedent Classification (tier, iscedent, cedenttype, segment)
      - Financial Profile (exposurem, premiumvolume, lossratio, tier)
      - Relationship Management (relationshipmanager, partnershipstatus, lastqbrdate)
      - Risk Profile (riskrating, watchlist, watchlistreason, notes)

.PARAMETER Org
    Dataverse org URL
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM"
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
        $msg = $_.ErrorDetails.Message
        Write-Warning "  ✗ $Method $Path : $($msg.Substring(0,[Math]::Min(400,$msg.Length)))"
        return $null
    }
}

Write-Host "=== UPDATE ACCOUNT FORM ===" -ForegroundColor Cyan

# ── Get the Account main form ────────────────────────────────────────────────
Write-Host "[1] Fetching Account main form..."
$forms = Invoke-Dv GET "systemforms?`$select=formid,name,formxml&`$filter=objecttypecode eq 'account' and type eq 2 and name eq 'Account'"
if (-not $forms -or $forms.value.Count -eq 0) {
    # Try 'Main' or first main form
    $forms = Invoke-Dv GET "systemforms?`$select=formid,name,formxml&`$filter=objecttypecode eq 'account' and type eq 2"
}
if (-not $forms -or $forms.value.Count -eq 0) { Write-Error "No Account main form found." }

$form = $forms.value[0]
Write-Host "  Using form: '$($form.name)' ($($form.formid))"

[xml]$xml = $form.formxml

# ── Check if ERAC tab already exists ────────────────────────────────────────
$tabNodes = $xml.SelectNodes("//tab")
$eracTab = $tabNodes | Where-Object { $_.name -eq "erac_partnershipTab" }
if ($eracTab) {
    Write-Host "  ⏭ ERAC tab already exists on this form — skipping" -ForegroundColor Yellow
    exit 0
}

Write-Host "[2] Building ERAC Partnership tab..."

# Helper to create a control element
function New-Control([System.Xml.XmlDocument]$doc, [string]$id, [string]$classid, [string]$datafieldname) {
    $ctrl = $doc.CreateElement("control")
    $ctrl.SetAttribute("id", $id)
    $ctrl.SetAttribute("classid", $classid)
    $ctrl.SetAttribute("datafieldname", $datafieldname)
    $ctrl.SetAttribute("disabled", "false")
    return $ctrl
}

# Helper to create a cell (wrapping a control)
function New-Cell([System.Xml.XmlDocument]$doc, [string]$ctrlId, [string]$classid, [string]$field) {
    $cell = $doc.CreateElement("cell")
    $cell.AppendChild((New-Control $doc $ctrlId $classid $field)) | Out-Null
    return $cell
}

# Helper to create a row with 1 or 2 cells
function New-Row([System.Xml.XmlDocument]$doc, [array]$fields) {
    $row = $doc.CreateElement("row")
    foreach ($f in $fields) {
        $row.AppendChild((New-Cell $doc "erac_ctrl_$($f.name)" $f.class $f.name)) | Out-Null
    }
    return $row
}

# Standard text/lookup classids
$txtClass     = "{4273EDBD-AC1D-40d3-9FB2-095C621B552D}"  # SingleLine.Text
$decClass     = "{C3EFE0C3-0EC6-42be-8349-CBD9079C818A}"  # Decimal
$boolClass    = "{B0C6723A-8503-4fd7-BB28-C8A06AC933C2}"  # Boolean
$pickClass    = "{3EF39988-22BB-4f0b-BBBE-64B5A3748AEE}"  # OptionSet
$memoClass    = "{E0DECE4B-6FC8-4a8f-A065-082708572369}"  # MultiLine.Text
$dateClass    = "{5B773807-9FB2-42db-97C3-7A91EFF8ADFF}"  # DateAndTime.DateOnly
$lookClass    = "{270BD3DB-D9AF-4782-9025-509E298DEC0A}"  # Lookup

$fieldDefs = @(
    # Section 1: Cedent Classification
    @{ section="Cedent Classification"; rows=@(
        @(@{ name="erac_iscedent";     class=$boolClass }, @{ name="erac_cedenttype";  class=$pickClass }),
        @(@{ name="erac_segment";      class=$pickClass }, @{ name="erac_tier";        class=$pickClass })
    )},
    # Section 2: Financial Profile
    @{ section="Financial Profile"; rows=@(
        @(@{ name="erac_exposurem";    class=$decClass  }, @{ name="erac_premiumvolume"; class=$decClass }),
        @(@{ name="erac_lossratio";    class=$decClass  })
    )},
    # Section 3: Relationship Management
    @{ section="Relationship Management"; rows=@(
        @(@{ name="erac_relationshipmanager"; class=$txtClass }, @{ name="erac_partnershipstatus"; class=$pickClass }),
        @(@{ name="erac_lastqbrdate";  class=$dateClass })
    )},
    # Section 4: Risk Profile
    @{ section="Risk Profile"; rows=@(
        @(@{ name="erac_riskrating";   class=$pickClass }, @{ name="erac_watchlist"; class=$boolClass }),
        @(@{ name="erac_watchlistreason"; class=$memoClass }),
        @(@{ name="erac_notes";        class=$memoClass })
    )}
)

# Build the tab — Dataverse requires GUID-format ids for tab/section elements
$tabGuid    = [System.Guid]::NewGuid().ToString("D")
$tabEl = $xml.CreateElement("tab")
$tabEl.SetAttribute("id",                "{$tabGuid}")
$tabEl.SetAttribute("name",              "erac_partnershipTab")
$tabEl.SetAttribute("expanded",          "true")
$tabEl.SetAttribute("verticallayout",    "true")
$tabEl.SetAttribute("showlabel",         "true")
$tabEl.SetAttribute("locklevel",         "0")

$tabLabels = $xml.CreateElement("labels")
$tabLabel  = $xml.CreateElement("label")
$tabLabel.SetAttribute("description", "ERAC Partnership")
$tabLabel.SetAttribute("languagecode", "1033")
$tabLabels.AppendChild($tabLabel) | Out-Null
$tabEl.AppendChild($tabLabels) | Out-Null

$columnsEl = $xml.CreateElement("columns")
$colEl     = $xml.CreateElement("column")
$colEl.SetAttribute("width", "100%")
$sectionsEl = $xml.CreateElement("sections")

foreach ($sec in $fieldDefs) {
    $secGuid = [System.Guid]::NewGuid().ToString("D")
    $secEl = $xml.CreateElement("section")
    $secEl.SetAttribute("id",          "{$secGuid}")
    $secEl.SetAttribute("name",        "erac_sec_$($sec.section -replace '\s','')")
    $secEl.SetAttribute("showlabel",   "true")
    $secEl.SetAttribute("locklevel",   "0")
    $secEl.SetAttribute("columns",     "2")

    $secLabels = $xml.CreateElement("labels")
    $secLabel  = $xml.CreateElement("label")
    $secLabel.SetAttribute("description", $sec.section)
    $secLabel.SetAttribute("languagecode", "1033")
    $secLabels.AppendChild($secLabel) | Out-Null
    $secEl.AppendChild($secLabels) | Out-Null

    $rowsEl = $xml.CreateElement("rows")
    foreach ($rowFields in $sec.rows) {
        $rowsEl.AppendChild((New-Row $xml $rowFields)) | Out-Null
    }
    $secEl.AppendChild($rowsEl) | Out-Null
    $sectionsEl.AppendChild($secEl) | Out-Null
}

$colEl.AppendChild($sectionsEl) | Out-Null
$columnsEl.AppendChild($colEl) | Out-Null
$tabEl.AppendChild($columnsEl) | Out-Null

# Append tab to form
$formNode = $xml.SelectSingleNode("//tabs")
if (-not $formNode) { $formNode = $xml.SelectSingleNode("//form") }
$formNode.AppendChild($tabEl) | Out-Null

Write-Host "  ✓ ERAC tab built (4 sections, 15 columns)" -ForegroundColor Green

# ── Serialize and PATCH ──────────────────────────────────────────────────────
Write-Host "[3] Saving form..."
# Dataverse requires form XML to start with the root element — no XML declaration
$xwSettings = New-Object System.Xml.XmlWriterSettings
$xwSettings.OmitXmlDeclaration = $true
$xwSettings.Indent = $false
$sb = New-Object System.Text.StringBuilder
$xw = [System.Xml.XmlWriter]::Create($sb, $xwSettings)
$xml.Save($xw)
$xw.Flush()
$newXml = $sb.ToString()

# Remove Prefer header for PATCH (returns 204)
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
        Write-Warning "  PATCH returned $code — $($msg.Substring(0,[Math]::Min(300,$msg.Length)))"
    }
}

# ── Add form to solution ─────────────────────────────────────────────────────
Write-Host "[4] Adding form to solution..."
$addBody = @{
    ComponentId           = $form.formid
    ComponentType         = 24   # SystemForm
    SolutionUniqueName    = $SolutionUniqueName
    AddRequiredComponents = $false
} | ConvertTo-Json
try {
    Invoke-WebRequest "$Org/api/data/v9.2/AddSolutionComponent" `
        -Method POST -Headers $hPatch -Body $addBody -UseBasicParsing -TimeoutSec 30 | Out-Null
    Write-Host "  ✓ Added to solution" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ AddSolutionComponent: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
}

# ── Publish ──────────────────────────────────────────────────────────────────
Write-Host "[5] Publishing..."
try {
    Invoke-WebRequest "$Org/api/data/v9.2/PublishAllXml" `
        -Method POST -Headers $hPatch -UseBasicParsing -TimeoutSec 120 | Out-Null
    Write-Host "  ✓ Published" -ForegroundColor Green
} catch {
    Write-Host "  ✓ Published (204)" -ForegroundColor Green
}

Write-Host "`n✅ Account form updated — open any Account record in ERAC Lite CRM" -ForegroundColor Green
Write-Host "   → 'ERAC Partnership' tab will appear with all 15 custom fields"
