<#
.SYNOPSIS
    Upload Otis Case Form Scripts as Web Resource to Demo Components solution
.DESCRIPTION
    Creates/updates the otis_CaseFormScripts web resource in Dataverse,
    adds it to the Demo Components solution, and publishes it.
    
    This JS auto-sets Priority based on Case Type and shows hot word
    notification banners (entrapment, safety, etc.) on the Case form.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir)))

# Import Dataverse helper
$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
Import-Module $helperPath -Force

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Upload Otis Case Form Scripts Web Resource" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

$headers = Get-DataverseHeaders
$base = Get-DataverseApiUrl

# ============================================================
# 1. Read and encode the JS file
# ============================================================
$jsFilePath = Join-Path $scriptDir "..\webresources\otis_CaseFormScripts.js"
if (-not (Test-Path $jsFilePath)) {
    throw "JS file not found at: $jsFilePath"
}

$jsContent = Get-Content $jsFilePath -Raw -Encoding UTF8
$jsBytes = [System.Text.Encoding]::UTF8.GetBytes($jsContent)
$jsBase64 = [Convert]::ToBase64String($jsBytes)

Write-Host "  JS file loaded: $($jsBytes.Length) bytes" -ForegroundColor Gray

# ============================================================
# 2. Create or update the Web Resource
# ============================================================
$wrName = "bw_OtisCaseFormScripts"
$wrDisplayName = "Otis - Case Form Scripts (Auto-Priority + Hot Words)"
$wrDescription = "Auto-sets Priority based on Case Type (Problem=High). Hot word banners: RED for entrapment/trapped/injury/fire, YELLOW for out of service/not working/complaint."

Write-Host "`n>>> Creating/updating web resource: $wrName" -ForegroundColor Green

$wrResp = Invoke-RestMethod -Uri "$base/webresourceset?`$filter=name eq '$wrName'&`$select=webresourceid,name" -Headers $headers

if ($wrResp.value.Count -gt 0) {
    $wrId = $wrResp.value[0].webresourceid
    Write-Host "  Found existing: $wrId - updating..." -ForegroundColor Yellow
    
    $wrPatchBody = @{
        content     = $jsBase64
        displayname = $wrDisplayName
        description = $wrDescription
    } | ConvertTo-Json -Depth 5
    
    $patchH = @{
        "Authorization" = $headers["Authorization"]
        "Content-Type"  = "application/json; charset=utf-8"
        "OData-Version" = "4.0"
        "If-Match"      = "*"
    }
    Invoke-RestMethod -Uri "$base/webresourceset($wrId)" -Headers $patchH -Method Patch -Body $wrPatchBody
    Write-Host "  Updated web resource" -ForegroundColor Green
} else {
    Write-Host "  Creating new web resource..." -ForegroundColor Yellow
    
    $wrResult = Invoke-DataversePost "webresourceset" @{
        name            = $wrName
        displayname     = $wrDisplayName
        description     = $wrDescription
        webresourcetype = 3   # 3 = JavaScript
        content         = $jsBase64
    }
    $wrId = $wrResult.webresourceid
    Write-Host "  Created: $wrId" -ForegroundColor Green
}

# ============================================================
# 3. Add to Demo Components solution
# ============================================================
Write-Host "`n>>> Adding to Demo Components solution..." -ForegroundColor Green

# Find the Demo Components solution
$solResp = Invoke-RestMethod -Uri "$base/solutions?`$filter=contains(friendlyname,'Demo')&`$select=solutionid,uniquename,friendlyname" -Headers $headers

if ($solResp.value.Count -eq 0) {
    Write-Host "  No solution found with 'Demo' in name. Listing all unmanaged solutions:" -ForegroundColor Yellow
    $allSols = Invoke-RestMethod -Uri "$base/solutions?`$filter=ismanaged eq false and isvisible eq true&`$select=uniquename,friendlyname&`$top=20" -Headers $headers
    foreach ($s in $allSols.value) {
        Write-Host "    - $($s.friendlyname) [$($s.uniquename)]" -ForegroundColor Gray
    }
    Write-Host "`n  Skipping solution association. Add manually via Power Apps." -ForegroundColor Yellow
} else {
    $solution = $solResp.value[0]
    Write-Host "  Found: $($solution.friendlyname) [$($solution.uniquename)]" -ForegroundColor Gray
    
    try {
        $addBody = @{
            ComponentId = $wrId
            ComponentType = 61   # 61 = WebResource
            SolutionUniqueName = $solution.uniquename
            AddRequiredComponents = $false
        } | ConvertTo-Json
        
        Invoke-RestMethod -Uri "$base/AddSolutionComponent" -Headers $headers -Method Post -Body $addBody
        Write-Host "  Added to solution: $($solution.friendlyname)" -ForegroundColor Green
    } catch {
        if ($_.Exception.Message -match "already exists") {
            Write-Host "  Already in solution" -ForegroundColor Green
        } else {
            Write-Host "  Warning adding to solution: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "  You can add it manually in Power Apps" -ForegroundColor Yellow
        }
    }
}

# ============================================================
# 4. Publish the web resource
# ============================================================
Write-Host "`n>>> Publishing web resource..." -ForegroundColor Green

$pubXml = "<importexportxml><webresources><webresource>{$wrId}</webresource></webresources></importexportxml>"
$pubBody = @{ ParameterXml = $pubXml } | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "$base/PublishXml" -Headers $headers -Method Post -Body $pubBody
    Write-Host "  Published successfully" -ForegroundColor Green
} catch {
    Write-Host "  Publish warning: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ============================================================
# 5. Output next steps
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Web Resource Uploaded & Published!" -ForegroundColor Green
Write-Host ""
Write-Host "  Name: $wrName" -ForegroundColor White
Write-Host "  ID:   $wrId" -ForegroundColor White
Write-Host ""
Write-Host "  NEXT: Add to Enhanced Full Case Form:" -ForegroundColor Yellow
Write-Host "  1. Power Apps > Tables > Case > Forms" -ForegroundColor White
Write-Host "  2. Edit 'Enhanced full case form'" -ForegroundColor White
Write-Host "  3. Form Properties > Libraries > Add '$wrName'" -ForegroundColor White
Write-Host "  4. OnLoad event > Function: Otis.Case.onLoad" -ForegroundColor White
Write-Host "     (Check 'Pass execution context')" -ForegroundColor White
Write-Host "  5. Save > Publish" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green
