$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force
Connect-Dataverse

$siteId = "2dd891fe-1418-f111-8342-7c1e52143136"
$pages = Invoke-DataverseGet -EntitySet "adx_webpages" `
    -Filter "_adx_websiteid_value eq $siteId" `
    -Select "adx_webpageid,adx_name,adx_partialurl,adx_isroot,_adx_parentpageid_value"

# Build lookup of ROOT pages by ID
$lk = @{}
foreach ($p in $pages) {
    if ($p.adx_isroot -eq $true) {
        $lk[$p.adx_webpageid] = $p
    }
}

Write-Host ""
Write-Host "ROOT PAGES WITH FULL URLS:" -ForegroundColor Cyan
Write-Host ("-" * 70)
foreach ($p in $pages) {
    if ($p.adx_isroot -eq $true) {
        $parentUrl = ""
        if ($p._adx_parentpageid_value -and $lk.ContainsKey($p._adx_parentpageid_value)) {
            $parent = $lk[$p._adx_parentpageid_value]
            if ($parent.adx_partialurl -ne "/") {
                $parentUrl = "/" + $parent.adx_partialurl
            }
        }
        $fullUrl = $parentUrl + "/" + $p.adx_partialurl
        Write-Host ("  {0,-45} {1}" -f $fullUrl, $p.adx_name)
    }
}

# Also check KB categories
Write-Host ""
Write-Host "KB ARTICLE CATEGORIES:" -ForegroundColor Cyan
Write-Host ("-" * 70)
$cats = Invoke-DataverseGet -EntitySet "categories" `
    -Select "categoryid,title,categorynumber,_parentcategoryid_value" `
    -Top 50
if ($cats -and $cats.Count -gt 0) {
    foreach ($c in $cats) {
        $parentTag = ""
        if ($c._parentcategoryid_value) { $parentTag = " (child)" }
        Write-Host "  $($c.title)$parentTag  [$($c.categoryid)]"
    }
    Write-Host "  Total: $($cats.Count)" -ForegroundColor DarkGray
} else {
    Write-Host "  (none found)"
}
