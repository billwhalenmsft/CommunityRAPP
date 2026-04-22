<#
.SYNOPSIS
    Upload product images to Dataverse Product Entity Image field.

.DESCRIPTION
    Reads images from customers/navico/d365/demo-assets/product-images/ and uploads
    them to the matching Product record's entityimage field in Dataverse.

    Image file naming convention:
      {product-number}.jpg   e.g. SIM-NSX-3007.jpg
      {product-number}.png   e.g. LWR-HDS9-LIVE.png

    The script matches the filename (without extension) to product.productnumber.
    Images are uploaded as base64 to the Product entity's entityimage column via PATCH.

    Supported formats: .jpg, .jpeg, .png
    Max recommended size: 144x144 px (Dataverse Entity Image standard)

.PARAMETER DryRun
    Show what would be uploaded without making changes.

.EXAMPLE
    .\Upload-ProductImages.ps1
    .\Upload-ProductImages.ps1 -DryRun
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) { Import-Module $helperPath -Force } else { throw "DataverseHelper.psm1 not found" }

$imagesDir = Join-Path $scriptDir "demo-assets\product-images"

if (-not (Test-Path $imagesDir)) {
    Write-Host "No product-images directory found at: $imagesDir" -ForegroundColor Red
    Write-Host "Create the directory and add product images named by product number." -ForegroundColor Yellow
    Write-Host "Example: SIM-NSX-3007.jpg, LWR-HDS9-LIVE.png" -ForegroundColor Yellow
    exit 1
}

$imageFiles = Get-ChildItem -Path $imagesDir -Include "*.jpg","*.jpeg","*.png" -File
if ($imageFiles.Count -eq 0) {
    Write-Host "No image files found in: $imagesDir" -ForegroundColor Yellow
    Write-Host "Add .jpg or .png files named by product number." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Upload Product Images to Dataverse" -ForegroundColor Cyan
Write-Host "  Source   : $imagesDir" -ForegroundColor DarkGray
Write-Host "  Images   : $($imageFiles.Count)" -ForegroundColor DarkGray
Write-Host "  Mode     : $(if ($DryRun) {'DRY RUN'} else {'LIVE'})" -ForegroundColor $(if ($DryRun) {'Yellow'} else {'Green'})
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

# Load all products for matching
$allProducts = Invoke-DataverseGet -EntitySet "products" `
    -Select "productid,name,productnumber" -Top 200

Write-Host "  Products in system: $($allProducts.Count)" -ForegroundColor DarkGray

$uploaded = 0; $notFound = 0; $failed = 0

foreach ($file in $imageFiles) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $sizeKB   = [math]::Round($file.Length / 1024)

    # Try matching by productnumber (exact, case-insensitive)
    $match = $allProducts | Where-Object {
        $_.productnumber -ieq $baseName -or
        $_.productnumber -ieq ($baseName -replace "-","") -or
        $_.name -ieq $baseName
    } | Select-Object -First 1

    # If no exact match, try partial match on product name
    if (-not $match) {
        $match = $allProducts | Where-Object {
            $_.name -like "*$baseName*" -or
            $_.productnumber -like "*$baseName*"
        } | Select-Object -First 1
    }

    if (-not $match) {
        Write-Host "  NO MATCH: $($file.Name) — no product with number or name '$baseName'" -ForegroundColor Yellow
        $notFound++
        continue
    }

    Write-Host "  MATCH: $($file.Name) → $($match.name) [$($match.productnumber)] (${sizeKB}KB)" -ForegroundColor Gray

    if ($DryRun) {
        Write-Host "    (dry run — would upload)" -ForegroundColor Yellow
        $uploaded++
        continue
    }

    # Read image and convert to base64
    $imageBytes = [System.IO.File]::ReadAllBytes($file.FullName)
    $base64     = [System.Convert]::ToBase64String($imageBytes)

    # Upload via PATCH to entityimage
    try {
        Invoke-DataversePatch -EntitySet "products" -RecordId ([guid]$match.productid) -Body @{
            entityimage = $base64
        }
        Write-Host "    ✓ Uploaded" -ForegroundColor Green
        $uploaded++
    } catch {
        Write-Host "    ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "    Uploaded  : $uploaded" -ForegroundColor $(if ($uploaded -gt 0) {'Green'} else {'Gray'})
Write-Host "    No match  : $notFound" -ForegroundColor $(if ($notFound -gt 0) {'Yellow'} else {'Gray'})
Write-Host "    Failed    : $failed" -ForegroundColor $(if ($failed -gt 0) {'Red'} else {'Gray'})
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Naming guide — save images as:" -ForegroundColor DarkGray
Write-Host "  SIM-NSX-3007.jpg     → Simrad NSX 3007 Chartplotter" -ForegroundColor DarkGray
Write-Host "  LWR-HDS9-LIVE.jpg    → Lowrance HDS-9 Live" -ForegroundColor DarkGray
Write-Host "  LWR-ELT-FS9.jpg     → Lowrance Elite FS 9" -ForegroundColor DarkGray
Write-Host "  SIM-HALO-20.jpg     → Simrad Halo 20 Pulse Radar" -ForegroundColor DarkGray
Write-Host "  SIM-AP44.jpg        → Simrad AP44 Autopilot Controller" -ForegroundColor DarkGray
Write-Host "  LWR-HOOK-REV7.jpg   → Lowrance Hook Reveal 7" -ForegroundColor DarkGray
