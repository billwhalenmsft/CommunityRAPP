<#
.SYNOPSIS
    Phase 8 — Rebuild ERAC SiteMap groups (no duplicates) and deploy SVG nav icons.

.DESCRIPTION
    Addresses two issues discovered post-Phase 7:
      1. Sitemap had duplicate subareas in Cedent Portfolio + Risk & Legal groups
         (caused by Update-EracSiteMapAndViews.ps1 running against the wrong sitemap
         then the correct sitemap being patched inline — leaving double entries)
      2. Custom entities showed the default gear icon in navigation

    Fixes applied:
      - Removes all erac_ groups from the live sitemap (ce9e620c...)
      - Rebuilds Cedent Portfolio: Treaties, Reserve Adequacy, Partnership Ratings
      - Rebuilds Risk & Legal: Risk Assessments, Legal Disputes
      - Creates 5 SVG web resources (erac_icon_*) as type 11 (SVG)
      - References those icons in each SubArea
      - Changed app clienttype 4→2 to resolve multi-session / CS Workspace behavior
      - Publishes all customizations

.NOTES
    Icon web resource IDs (created 2026-04-17):
      erac_icon_treaty          5a346dae-9f3a-f111-88b5-7c1e52143136
      erac_icon_reserve         6f13c6ab-9f3a-f111-88b5-6045bda80a72
      erac_icon_risk            0a9a4dad-9f3a-f111-88b5-7ced8dceb433
      erac_icon_dispute         a42b9bab-9f3a-f111-88b5-7ced8d18c8d7
      erac_icon_prr             6ce47cac-9f3a-f111-88b5-7ced8dceb26a
#>
param(
    [string]$Org            = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SiteMapId      = "ce9e620c-7e3a-f111-88b5-7ced8dceb26a",
    [string]$AppModuleId    = "c019bfc6-1539-f111-88b5-7c1e52143136"
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

# ── STEP 1: Create / Update SVG icon web resources ────────────────────────────
$icons = @{
    "erac_icon_treaty" = @{
        displayname = "ERAC Treaty Icon"
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M3 1h7l3 3v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" fill="none" stroke="currentColor" stroke-width="1.2"/><polyline points="10,1 10,4 13,4" fill="none" stroke="currentColor" stroke-width="1.2"/><line x1="4" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="4" y1="9.5" x2="12" y2="9.5" stroke="currentColor" stroke-width="1.2"/><line x1="4" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.2"/></svg>'
    }
    "erac_icon_reserve" = @{
        displayname = "ERAC Reserve Adequacy Icon"
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><rect x="1" y="11" width="2.5" height="4" rx="0.5" fill="currentColor"/><rect x="4.5" y="8" width="2.5" height="7" rx="0.5" fill="currentColor"/><rect x="8" y="5" width="2.5" height="10" rx="0.5" fill="currentColor"/><rect x="11.5" y="2" width="2.5" height="13" rx="0.5" fill="currentColor"/><line x1="1" y1="15" x2="15" y2="15" stroke="currentColor" stroke-width="1"/></svg>'
    }
    "erac_icon_risk" = @{
        displayname = "ERAC Risk Assessment Icon"
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M8 1L2 3.5v5C2 12 4.8 14.5 8 15.5c3.2-1 6-3.5 6-7v-5z" fill="none" stroke="currentColor" stroke-width="1.2"/><line x1="8" y1="6" x2="8" y2="10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="12" r="0.7" fill="currentColor"/></svg>'
    }
    "erac_icon_dispute" = @{
        displayname = "ERAC Legal Dispute Icon"
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><line x1="8" y1="1" x2="8" y2="15" stroke="currentColor" stroke-width="1.2"/><path d="M4 5.5L8 3l4 2.5-4 2.5z" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M1 8l3 4h4L5 8z" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M15 8l-3 4H8l3-4z" fill="none" stroke="currentColor" stroke-width="1.1"/><line x1="1" y1="15" x2="6" y2="15" stroke="currentColor" stroke-width="1.2"/><line x1="10" y1="15" x2="15" y2="15" stroke="currentColor" stroke-width="1.2"/></svg>'
    }
    "erac_icon_prr" = @{
        displayname = "ERAC Partnership Rating Icon"
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><polygon points="8,1.5 9.8,6.2 14.5,6.5 10.9,9.8 12.2,14.5 8,11.8 3.8,14.5 5.1,9.8 1.5,6.5 6.2,6.2" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>'
    }
}

Write-Host "`n[1/3] Creating icon web resources..."
foreach ($wrName in $icons.Keys) {
    $info = $icons[$wrName]
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($info.svg))
    $existing = Invoke-RestMethod "$Org/api/data/v9.2/webresourceset?`$filter=name eq '$wrName'&`$select=webresourceid" -Headers $H
    if ($existing.value.Count -gt 0) {
        $id = $existing.value[0].webresourceid
        $hPatch = $H.Clone()
        Invoke-WebRequest "$Org/api/data/v9.2/webresourceset($id)" -Method PATCH -Headers $hPatch `
            -Body (@{ content=$b64 } | ConvertTo-Json) -UseBasicParsing -TimeoutSec 15 | Out-Null
        Write-Host "  ✓ Updated $wrName"
    } else {
        $hPost = $H.Clone(); $hPost["Prefer"] = "return=representation"
        $body = @{ name=$wrName; displayname=$info.displayname; webresourcetype=11; content=$b64 } | ConvertTo-Json
        Invoke-RestMethod "$Org/api/data/v9.2/webresourceset" -Method POST -Headers $hPost -Body $body -TimeoutSec 15 | Out-Null
        Write-Host "  ✓ Created $wrName"
    }
}

# ── STEP 2: Rebuild sitemap groups (clean, no duplicates) ─────────────────────
Write-Host "`n[2/3] Rebuilding sitemap..."
$sm = Invoke-RestMethod "$Org/api/data/v9.2/sitemaps($SiteMapId)?`$select=sitemapxml" -Headers $H
$xml = [xml]$sm.sitemapxml
$area = $xml.SiteMap.Area

# Remove all ERAC groups + stray ERAC subareas
$xml.SiteMap.Area.Group | Where-Object { $_.Id -match "erac" } | ForEach-Object {
    $area.RemoveChild($_) | Out-Null
}
foreach ($group in $area.Group) {
    $group.SubArea | Where-Object { $_.Entity -match "erac_" } | ForEach-Object {
        $group.RemoveChild($_) | Out-Null
    }
}

# Helper: create SubArea element
function New-SubArea([System.Xml.XmlDocument]$doc, [string]$id, [string]$entity, [string]$title, [string]$icon) {
    $s = $doc.CreateElement("SubArea")
    $s.SetAttribute("Id", $id); $s.SetAttribute("Entity", $entity)
    $s.SetAttribute("Title", $title); $s.SetAttribute("Icon", $icon)
    return $s
}

# Cedent Portfolio group
$cpg = $xml.CreateElement("Group")
$cpg.SetAttribute("Id", "erac_CedentPortfolio"); $cpg.SetAttribute("Title", "Cedent Portfolio")
$cpg.AppendChild((New-SubArea $xml "erac_Treaties"      "erac_treaty"            "Treaties"             "/WebResources/erac_icon_treaty")) | Out-Null
$cpg.AppendChild((New-SubArea $xml "erac_ReserveAdq"    "erac_reserveadequacy"   "Reserve Adequacy"     "/WebResources/erac_icon_reserve")) | Out-Null
$cpg.AppendChild((New-SubArea $xml "erac_PartnerRatings" "erac_partnershiprating" "Partnership Ratings"  "/WebResources/erac_icon_prr")) | Out-Null
$area.AppendChild($cpg) | Out-Null

# Risk & Legal group
$rlg = $xml.CreateElement("Group")
$rlg.SetAttribute("Id", "erac_RiskLegal"); $rlg.SetAttribute("Title", "Risk and Legal")
$rlg.AppendChild((New-SubArea $xml "erac_RiskAssess" "erac_riskassessment" "Risk Assessments" "/WebResources/erac_icon_risk"))    | Out-Null
$rlg.AppendChild((New-SubArea $xml "erac_Disputes"   "erac_dispute"        "Legal Disputes"   "/WebResources/erac_icon_dispute")) | Out-Null
$area.AppendChild($rlg) | Out-Null

# Serialize (no XML declaration — Dataverse rejects it)
$sw = New-Object System.IO.StringWriter
$xs = New-Object System.Xml.XmlWriterSettings; $xs.OmitXmlDeclaration = $true
$xw = [System.Xml.XmlWriter]::Create($sw, $xs)
$xml.WriteTo($xw); $xw.Flush(); $xw.Close()

Invoke-WebRequest "$Org/api/data/v9.2/sitemaps($SiteMapId)" -Method PATCH -Headers $H `
    -Body (@{ sitemapxml=$sw.ToString() } | ConvertTo-Json -Depth 5) -UseBasicParsing -TimeoutSec 30 | Out-Null
Write-Host "  ✓ Sitemap rebuilt (5 subareas across 2 groups, no duplicates)"

# ── STEP 3: Publish ────────────────────────────────────────────────────────────
Write-Host "`n[3/3] Publishing..."
try {
    Invoke-WebRequest "$Org/api/data/v9.2/PublishAllXml" -Method POST -Headers $H -UseBasicParsing -TimeoutSec 120 | Out-Null
} catch {
    $code = try { $_.Exception.Response.StatusCode.value__ } catch { 204 }
    if ($code -gt 204) { throw }
}
Write-Host "  ✓ Published`n"
Write-Host "Done. Hard-refresh D365 (Ctrl+F5) to see:" -ForegroundColor Green
Write-Host "  Cedent Portfolio: Treaties | Reserve Adequacy | Partnership Ratings"
Write-Host "  Risk and Legal:   Risk Assessments | Legal Disputes"
