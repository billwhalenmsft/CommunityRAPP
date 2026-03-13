Import-Module "$PSScriptRoot\DataverseHelper.psm1" -Force
Connect-Dataverse

# Get all KB articles
$arts = Invoke-DataverseGet -EntitySet "knowledgearticles" `
    -Select "title,articlepublicnumber,statecode,statuscode,knowledgearticleid" -Top 50

Write-Host "KNOWLEDGE ARTICLES ($($arts.Count) total):" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------"
foreach ($a in $arts) {
    $stateLabel = switch ($a.statecode) { 0 { "Draft" } 1 { "Approved" } 2 { "Scheduled" } 3 { "Published" } 4 { "Expired" } 5 { "Archived" } default { "Unknown" } }
    Write-Host "  $($a.title) | State=$stateLabel | ID=$($a.knowledgearticleid)"
}

# Get category associations
Write-Host ""
Write-Host "KB ARTICLE CATEGORY ASSOCIATIONS:" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------"
$assoc = Invoke-DataverseGet -EntitySet "knowledgearticlescategories" `
    -Select "knowledgearticleid,categoryid" -Top 100
Write-Host "  Total associations: $($assoc.Count)"
foreach ($a in $assoc) {
    Write-Host "  Article=$($a.knowledgearticleid) -> Category=$($a.categoryid)"
}

# Check if categories have parent structure
Write-Host ""
Write-Host "CATEGORY DETAILS:" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------"
$cats = Invoke-DataverseGet -EntitySet "categories" `
    -Select "title,categorynumber,categoryid,_parentcategoryid_value" -Top 50
foreach ($c in $cats) {
    Write-Host "  $($c.title) | ID=$($c.categoryid) | Parent=$($c._parentcategoryid_value)"
}

# Check the KB web template content
Write-Host ""
Write-Host "KB HOME WEB TEMPLATE:" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------"
$kbTemplates = Invoke-DataverseGet -EntitySet "adx_webtemplates" `
    -Filter "adx_name eq 'Knowledge Base - Home'" `
    -Select "adx_name,adx_source,adx_webtemplateid"
if ($kbTemplates.Count -gt 0) {
    $tmpl = $kbTemplates[0]
    Write-Host "  Template ID: $($tmpl.adx_webtemplateid)"
    Write-Host "  Template Name: $($tmpl.adx_name)"
    $srcLen = 0
    if ($tmpl.adx_source) { $srcLen = $tmpl.adx_source.Length }
    Write-Host "  Source Length: $srcLen chars"
    if ($tmpl.adx_source -and $srcLen -lt 5000) {
        Write-Host ""
        Write-Host $tmpl.adx_source
    } else {
        Write-Host "  (Source too long, showing first 2000 chars)"
        Write-Host ""
        Write-Host $tmpl.adx_source.Substring(0, [Math]::Min(2000, $srcLen))
    }
}
