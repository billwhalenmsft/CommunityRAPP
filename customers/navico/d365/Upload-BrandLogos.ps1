<#
.SYNOPSIS
    Upload Navico brand logo SVGs as Dataverse web resources.
.DESCRIPTION
    Uploads 6 brand logo SVGs (Lowrance, Simrad, B&G, C-MAP, Northstar, Navico)
    as Dataverse web resources so the Service Toolkit Custom Page can reference
    them dynamically via Switch() formula based on the asset's brand.

    Web resource names:
      cr74e_logo_lowrance
      cr74e_logo_simrad
      cr74e_logo_bng
      cr74e_logo_cmap
      cr74e_logo_northstar
      cr74e_logo_navico

    The Canvas App references them as:
      "/WebResources/cr74e_logo_lowrance"  etc.

.NOTES
    Idempotent - updates existing if found, creates if not.
    Run after initial environment setup.
#>

$ErrorActionPreference = "Stop"
$scriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot     = Resolve-Path "$scriptDir\..\..\.."
$logoDir      = "$repoRoot\customers\navico\d365\demo-assets\web-resources"

# Import shared helpers from d365/scripts
Import-Module "$repoRoot\d365\scripts\DataverseHelper.psm1" -Force

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Upload Navico Brand Logo Web Resources" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

Connect-Dataverse
$api = Get-DataverseApiUrl
$h   = Get-DataverseHeaders

# Brand logos to upload: filename stem → display name
$logos = [ordered]@{
    "cr74e_logo_lowrance"  = "Lowrance Brand Logo"
    "cr74e_logo_simrad"    = "Simrad Brand Logo"
    "cr74e_logo_bng"       = "B&G Brand Logo"
    "cr74e_logo_cmap"      = "C-MAP Brand Logo"
    "cr74e_logo_northstar" = "Northstar Brand Logo"
    "cr74e_logo_navico"    = "Navico Brand Logo"
}

# Generic fallback (shared across all customer builds) — lives in d365/web-resources/
$sharedLogos = [ordered]@{
    "cr74e_logo_generic_mfg" = "Generic Manufacturer Logo (fallback)"
}
$sharedLogoDir = Join-Path $repoRoot "d365\web-resources"

$uploaded = 0; $updated = 0; $failed = 0

foreach ($wrName in $logos.Keys) {
    $displayName = $logos[$wrName]
    $svgPath     = Join-Path $logoDir "$wrName.svg"

    if (-not (Test-Path $svgPath)) {
        Write-Host "  MISSING: $svgPath" -ForegroundColor Red
        $failed++
        continue
    }

    # Base64-encode the SVG content
    $svgContent = Get-Content $svgPath -Raw -Encoding UTF8
    $base64     = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($svgContent))

    # Check if web resource already exists
    $existing = $null
    try {
        $resp = Invoke-RestMethod -Method GET `
            -Uri "$api/webresourceset?`$filter=name eq '$wrName'&`$select=webresourceid,name" `
            -Headers $h -ErrorAction Stop
        if ($resp.value -and $resp.value.Count -gt 0) {
            $existing = $resp.value[0]
        }
    } catch { }

    if ($existing) {
        # Update existing
        $wrId = $existing.webresourceid
        $patchBody = @{ content = $base64 } | ConvertTo-Json
        $patchH = $h.Clone()
        $patchH["If-Match"] = "*"
        try {
            Invoke-RestMethod -Method PATCH `
                -Uri "$api/webresourceset($wrId)" `
                -Headers $patchH -Body $patchBody -ContentType "application/json" -ErrorAction Stop
            Write-Host "  UPDATED: $wrName" -ForegroundColor Cyan
            $updated++
        } catch {
            Write-Host "  FAILED to update $wrName : $($_.Exception.Message)" -ForegroundColor Red
            $failed++
            continue
        }
    } else {
        # Create new
        $createBody = @{
            name             = $wrName
            displayname      = $displayName
            webresourcetype  = 11   # SVG (type 11)
            content          = $base64
            description      = "Navico brand logo for Service Toolkit sidebar — auto-uploaded"
        } | ConvertTo-Json

        try {
            $result = Invoke-RestMethod -Method POST `
                -Uri "$api/webresourceset" `
                -Headers $h -Body $createBody -ContentType "application/json" -ErrorAction Stop
            $wrId = ($result.webresourceid) ??
                    ([regex]::Match($result, '[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}').Value)
            Write-Host "  CREATED: $wrName" -ForegroundColor Green
            $uploaded++
        } catch {
            $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
            Write-Host "  FAILED to create $wrName : $($err.error.message ?? $_.Exception.Message)" -ForegroundColor Red
            $failed++
            continue
        }
    }

    # Publish the web resource
    try {
        $publishBody = @{
            ParameterXml = "<importexportxml><webresources><webresource>$wrId</webresource></webresources></importexportxml>"
        } | ConvertTo-Json
        Invoke-RestMethod -Method POST -Uri "$api/PublishXml" `
            -Headers $h -Body $publishBody -ContentType "application/json" -ErrorAction Stop
        Write-Host "    Published $wrName" -ForegroundColor DarkGray
    } catch {
        Write-Host "    WARNING: publish failed for $wrName — may need manual publish" -ForegroundColor Yellow
    }
}

# ── Shared / generic logos ──────────────────────────────────
Write-Host "`n--- Shared generic logos ---" -ForegroundColor Yellow
foreach ($wrName in $sharedLogos.Keys) {
    $displayName = $sharedLogos[$wrName]
    $svgPath     = Join-Path $sharedLogoDir "$wrName.svg"

    if (-not (Test-Path $svgPath)) {
        Write-Host "  MISSING: $svgPath" -ForegroundColor Red
        $failed++
        continue
    }

    $svgContent = Get-Content $svgPath -Raw -Encoding UTF8
    $base64     = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($svgContent))

    $existing = $null
    try {
        $resp = Invoke-RestMethod -Method GET `
            -Uri "$api/webresourceset?`$filter=name eq '$wrName'&`$select=webresourceid,name" `
            -Headers $h -ErrorAction Stop
        if ($resp.value -and $resp.value.Count -gt 0) { $existing = $resp.value[0] }
    } catch { }

    if ($existing) {
        $wrId = $existing.webresourceid
        $patchBody = @{ content = $base64 } | ConvertTo-Json
        $patchH = $h.Clone(); $patchH["If-Match"] = "*"
        Invoke-RestMethod -Method PATCH -Uri "$api/webresourceset($wrId)" `
            -Headers $patchH -Body $patchBody -ContentType "application/json" -ErrorAction Stop
        Write-Host "  UPDATED: $wrName" -ForegroundColor Cyan
        $updated++
    } else {
        $createBody = @{
            name            = $wrName
            displayname     = $displayName
            webresourcetype = 11
            content         = $base64
            description     = "Generic manufacturing fallback logo — used when no brand logo is matched"
        } | ConvertTo-Json
        $result = Invoke-RestMethod -Method POST -Uri "$api/webresourceset" `
            -Headers $h -Body $createBody -ContentType "application/json" -ErrorAction Stop
        $wrId = $result.webresourceid
        Write-Host "  CREATED: $wrName" -ForegroundColor Green
        $uploaded++
    }

    $publishBody = @{
        ParameterXml = "<importexportxml><webresources><webresource>$wrId</webresource></webresources></importexportxml>"
    } | ConvertTo-Json
    Invoke-RestMethod -Method POST -Uri "$api/PublishXml" `
        -Headers $h -Body $publishBody -ContentType "application/json" -ErrorAction Stop
    Write-Host "    Published $wrName" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Brand Logo Upload Complete" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Created : $uploaded" -ForegroundColor Cyan
Write-Host "  Updated : $updated" -ForegroundColor Cyan
Write-Host "  Failed  : $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "DarkGray" })
Write-Host ""
Write-Host "  Next: Apply 00-brand-patch.md to the Custom Page in Power Apps Studio" -ForegroundColor Yellow
