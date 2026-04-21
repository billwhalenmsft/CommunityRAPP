<#
.SYNOPSIS
    Phase C1.3 + C1.4 — Add a Cedent Profile section to the ERAC Cedent 360
    Account form (ABOVE Account Information) and update the form header to
    show ERAC-specific fields.
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$FormName = "ERAC Cedent 360"
)
$ErrorActionPreference="Stop"
$token=(az account get-access-token --resource $Org|ConvertFrom-Json).accessToken
$H=@{Authorization="Bearer $token";"Content-Type"="application/json; charset=utf-8";Accept="application/json";"OData-MaxVersion"="4.0";"OData-Version"="4.0"}

function Invoke-Dv {
  param([string]$Method,[string]$Path,[object]$Body=$null)
  $h=$H.Clone(); if($Method -in @("POST","PUT","PATCH")){$h["Prefer"]="return=representation"}
  $p=@{Uri="$Org/api/data/v9.2/$Path";Method=$Method;Headers=$h;TimeoutSec=120;UseBasicParsing=$true}
  if($Body){$p.Body=($Body|ConvertTo-Json -Depth 30)}
  try { $r=Invoke-WebRequest @p; if($r.Content){return $r.Content|ConvertFrom-Json}; return @{ok=$true} }
  catch { $code=try{$_.Exception.Response.StatusCode.value__}catch{0}; $msg=try{$_.ErrorDetails.Message}catch{$_.Exception.Message}; if(-not $msg){$msg="(no detail)"}; Write-Warning "X $Method $Path -> $code : $($msg.Substring(0,[Math]::Min(500,$msg.Length)))"; return $null }
}

Write-Host "=== ADD CEDENT PROFILE SECTION + UPDATE HEADER ===" -ForegroundColor Cyan

$esc=$FormName.Replace("'","''")
$forms=Invoke-Dv GET "systemforms?`$select=formid,name,formxml&`$filter=objecttypecode eq 'account' and type eq 2 and name eq '$esc'"
if(-not $forms -or $forms.value.Count -eq 0){Write-Error "Form '$FormName' not found."}
$form=$forms.value[0]
[xml]$xml=$form.formxml

# ── 1. Build Cedent Profile section helper ───────────────────────────────────
function New-Cell([string]$attr, [string]$labelText) {
  $cellId = [Guid]::NewGuid().ToString('D')
  return @"
<cell id="{$cellId}" showlabel="true" rowspan="1" colspan="1" auto="false">
  <labels><label description="$labelText" languagecode="1033" /></labels>
  <control id="$attr" classid="{4273EDBD-AC1D-40d3-9FB2-095C621B552D}" datafieldname="$attr" disabled="false" />
</cell>
"@
}

# 8 fields in 2-column layout = 4 rows
$rows = @"
<row>
  $(New-Cell 'erac_cedenttier' 'Cedent Tier')
  $(New-Cell 'erac_ambestrating' 'AM Best Rating')
</row>
<row>
  $(New-Cell 'erac_grosswrittenpremium' 'Gross Written Premium')
  $(New-Cell 'erac_renewaldate' 'Renewal Date')
</row>
<row>
  $(New-Cell 'erac_yearsaspartner' 'Years as Partner')
  $(New-Cell 'erac_relationshipmanagerid' 'Relationship Manager')
</row>
<row>
  $(New-Cell 'erac_linesofbusiness' 'Lines of Business')
  $(New-Cell 'erac_financialsignatoryflag' 'Financial Signatory Flag')
</row>
"@

$secId = [Guid]::NewGuid().ToString('D')
$sectionXml = @"
<section name="erac_cedent_profile_section" showlabel="true" showbar="false" locklevel="0"
         id="{$secId}" IsUserDefined="0"
         columns="2" labelwidth="115" celllabelalignment="Left" celllabelposition="Left">
  <labels><label description="ERAC Cedent Profile" languagecode="1033" /></labels>
  <rows>$rows</rows>
</section>
"@

# ── 2. Find SUMMARY_TAB ──────────────────────────────────────────────────────
$summary = $xml.form.tabs.tab | Where-Object { $_.name -eq 'SUMMARY_TAB' }
if (-not $summary) { Write-Error "SUMMARY_TAB not found." }

# Locate "Account Information" section (in column[0])
$accountInfoCol = $null; $accountInfoSec = $null
foreach ($col in $summary.columns.column) {
  $sec = $col.sections.section | Where-Object { $_.name -eq 'ACCOUNT_INFORMATION' }
  if ($sec) { $accountInfoCol = $col; $accountInfoSec = $sec; break }
}
if (-not $accountInfoSec) { Write-Error "ACCOUNT_INFORMATION section not found." }

# Idempotent — remove if exists
$existing = $accountInfoCol.sections.section | Where-Object { $_.name -eq 'erac_cedent_profile_section' }
if ($existing) { $accountInfoCol.sections.RemoveChild($existing) | Out-Null; Write-Host "  ✓ Removed prior cedent profile section" }

$frag = $xml.CreateDocumentFragment()
$frag.InnerXml = $sectionXml
$newSection = $frag.FirstChild
$accountInfoCol.sections.InsertBefore($newSection, $accountInfoSec) | Out-Null
Write-Host "  ✓ Inserted ERAC Cedent Profile section above Account Information"

# ── 3. Update Header — replace OOTB header fields with ERAC ones ─────────────
# The form header is in <header> element, with cells referencing fields
$header = $xml.form.header
if ($header) {
  # Find existing header rows
  $headerRows = $header.rows
  if ($headerRows -and $headerRows.row) {
    # Look at all cells in header
    $cells = @()
    foreach ($r in $headerRows.row) {
      foreach ($c in $r.cell) { if ($c) { $cells += $c } }
    }
    Write-Host "  Header cells found: $($cells.Count)"

    # Map: replace by datafieldname on the inner control
    $replacements = @{
      "revenue" = @{ field="erac_cedenttier"; label="Cedent Tier" }
      "cra1f_servicelevel" = @{ field="erac_ambestrating"; label="AM Best Rating" }
      "numberofemployees" = @{ field="erac_renewaldate"; label="Renewal Date" }
    }

    $updated = 0
    foreach ($c in $cells) {
      $ctrl = $c.control
      if (-not $ctrl) { continue }
      $df = $ctrl.datafieldname
      if ($df -and $replacements.ContainsKey($df)) {
        $rep = $replacements[$df]
        $ctrl.SetAttribute("datafieldname", $rep.field)
        $ctrl.SetAttribute("id", $rep.field)
        # Update labels
        if ($c.labels -and $c.labels.label) {
          foreach ($lbl in $c.labels.label) { $lbl.SetAttribute("description", $rep.label) }
        }
        Write-Host "    ↻ $df  →  $($rep.field)" -ForegroundColor DarkCyan
        $updated++
      }
    }
    Write-Host "  ✓ Header fields swapped: $updated"
  }
} else {
  Write-Host "  ⚠ No <header> element on form — skipping header swap"
}

# ── 4. PATCH form ────────────────────────────────────────────────────────────
$result = Invoke-Dv PATCH "systemforms($($form.formid))" @{ formxml = $xml.OuterXml }
if (-not $result) { Write-Error "Form PATCH failed" }
Write-Host "  ✓ Form updated" -ForegroundColor Green

Invoke-Dv POST "PublishXml" @{ ParameterXml = "<importexportxml><entities><entity>account</entity></entities></importexportxml>" } | Out-Null
Write-Host "  ✓ Published" -ForegroundColor Green

Write-Host "`n✅ Cedent Profile section added + header refreshed." -ForegroundColor Green
Write-Host "   Hard-refresh (Ctrl+F5) the open Account record." -ForegroundColor Cyan
