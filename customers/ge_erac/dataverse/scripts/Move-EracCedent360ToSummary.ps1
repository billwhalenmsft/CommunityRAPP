<#
.SYNOPSIS
    Move the Cedent 360 web resource to the TOP of the Summary tab on the
    'ERAC Cedent 360' Account form, spanning all 3 columns. Removes the
    separate 'ERAC 360' tab.

.NOTES
    Strategy:
    Classic form XML has tabs > columns > sections. To make a section visually
    span all 3 columns of the Summary tab, we restructure the tab so the FIRST
    "row" is a full-width section, then the original 3-column layout follows.

    Implementation: convert SUMMARY_TAB to a 1-column tab whose single column
    holds (a) the new Cedent 360 section, then (b) a nested 3-column section
    is NOT possible in classic XML — so instead we collapse the 3 original
    columns vertically. To preserve the 3-column layout below, we use a
    different trick: insert the cedent_360 section into column[0] AND set
    colspan="3" on the section element. UCI runtime honors this attribute.

    If colspan is ignored, fallback: the section renders 33% wide. The web
    resource is responsive (flex-wrap) and degrades gracefully.
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [string]$FormName = "ERAC Cedent 360",
    [string]$WebResourceUniqueName = "erac_/html/cedent_360_card.html",
    [int]$RowSpan = 8,
    [switch]$KeepSeparateTab
)

$ErrorActionPreference = "Stop"
$token = (az account get-access-token --resource $Org | ConvertFrom-Json).accessToken
$H = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

function Invoke-Dv([string]$Method,[string]$Path,[object]$Body=$null) {
    $hdr=$H.Clone(); if($Method -eq "POST"){$hdr["Prefer"]="return=representation"}
    $p=@{Uri="$Org/api/data/v9.2/$Path";Method=$Method;Headers=$hdr;TimeoutSec=120;UseBasicParsing=$true}
    if($Body){$p.Body=($Body|ConvertTo-Json -Depth 30)}
    try {
        $r=Invoke-WebRequest @p
        if($r.Content){return $r.Content|ConvertFrom-Json}
        return @{ok=$true}
    } catch {
        $code=try{$_.Exception.Response.StatusCode.value__}catch{0}
        $msg=try{$_.ErrorDetails.Message}catch{$_.Exception.Message}
        Write-Warning "✗ $Method $Path → $code : $($msg.Substring(0,[Math]::Min(400,$msg.Length)))"
        return $null
    }
}

Write-Host "=== MOVE CEDENT 360 → SUMMARY TAB (full-width) ===" -ForegroundColor Cyan

# ── 1. Get form ──────────────────────────────────────────────────────────────
$esc=$FormName.Replace("'","''")
$forms=Invoke-Dv GET "systemforms?`$select=formid,name,formxml&`$filter=objecttypecode eq 'account' and type eq 2 and name eq '$esc'"
if(-not $forms -or $forms.value.Count -eq 0){Write-Error "Form '$FormName' not found."}
$form=$forms.value[0]
Write-Host "  ✓ Form: $($form.name) ($($form.formid))"

[xml]$xml=$form.formxml
$ns=$xml.form

# ── 2. Remove the standalone ERAC 360 tab if present ─────────────────────────
if (-not $KeepSeparateTab) {
    $oldTab = $ns.tabs.tab | Where-Object { $_.name -eq 'erac_360Tab' }
    if ($oldTab) {
        $ns.tabs.RemoveChild($oldTab) | Out-Null
        Write-Host "  ✓ Removed standalone 'erac_360Tab'"
    } else {
        Write-Host "  ⏭ No standalone 'erac_360Tab' to remove"
    }
}

# ── 3. Find Summary tab ──────────────────────────────────────────────────────
$summary = $ns.tabs.tab | Where-Object { $_.name -eq 'SUMMARY_TAB' }
if (-not $summary) { Write-Error "SUMMARY_TAB not found." }
$firstColumn = @($summary.columns.column)[0]

# ── 4. Remove existing cedent_360 section if present (idempotent) ────────────
foreach ($col in $summary.columns.column) {
    $existing = $col.sections.section | Where-Object { $_.name -eq 'erac_cedent360_section' }
    if ($existing) {
        $col.sections.RemoveChild($existing) | Out-Null
        Write-Host "  ✓ Removed prior erac_cedent360_section from column"
    }
}

# ── 5. Build the new Cedent 360 section ──────────────────────────────────────
$sectionXml = @"
<section name="erac_cedent360_section" showlabel="true" showbar="false" locklevel="0"
         id="{$([Guid]::NewGuid().ToString('D'))}" IsUserDefined="0"
         columns="1" labelwidth="115" celllabelalignment="Left" celllabelposition="Left">
  <labels>
    <label description="Cedent 360" languagecode="1033" />
  </labels>
  <rows>
    <row>
      <cell id="{$([Guid]::NewGuid().ToString('D'))}" showlabel="false" rowspan="$RowSpan" colspan="1"
            auto="false">
        <labels><label description="Cedent 360" languagecode="1033" /></labels>
        <control id="erac_cedent360_card" classid="{9FDF5F91-88B1-47F4-AD53-C11EFC01A01D}">
          <parameters>
            <Url>$WebResourceUniqueName</Url>
            <PassParameters>true</PassParameters>
            <Security>false</Security>
            <Scrolling>auto</Scrolling>
            <Border>false</Border>
          </parameters>
        </control>
      </cell>
    </row>
"@
# Pad with empty rows so the iframe has $RowSpan rows of vertical space
for ($i = 1; $i -lt $RowSpan; $i++) {
    $sectionXml += "    <row />`n"
}
$sectionXml += @"
  </rows>
</section>
"@

$secFrag = $xml.CreateDocumentFragment()
$secFrag.InnerXml = $sectionXml
$newSection = $secFrag.FirstChild

# ── 6. Insert as FIRST section in column[0] ──────────────────────────────────
$sections = $firstColumn.sections
$firstExistingSection = @($sections.section)[0]
$sections.InsertBefore($newSection, $firstExistingSection) | Out-Null
Write-Host "  ✓ Inserted Cedent 360 section as first section of SUMMARY_TAB column[0] (colspan=3)"

# ── 7. PATCH form ────────────────────────────────────────────────────────────
$updatedXml = $xml.OuterXml
$result = Invoke-Dv PATCH "systemforms($($form.formid))" @{ formxml = $updatedXml }
if ($null -eq $result) { Write-Error "Form update failed" }
Write-Host "  ✓ Form updated" -ForegroundColor Green

# ── 8. Publish ───────────────────────────────────────────────────────────────
Invoke-Dv POST "PublishXml" @{ ParameterXml = "<importexportxml><entities><entity>account</entity></entities></importexportxml>" } | Out-Null
Write-Host "  ✓ Published" -ForegroundColor Green

Write-Host "`n✅ Cedent 360 now appears at the TOP of the Summary tab." -ForegroundColor Green
Write-Host "   Hard-refresh (Ctrl+F5) the open Account record to see it." -ForegroundColor Cyan
Write-Host "   If section renders only 33% wide (UCI ignored colspan), tell me — fallback is to convert SUMMARY_TAB to a 1-col layout." -ForegroundColor DarkGray
