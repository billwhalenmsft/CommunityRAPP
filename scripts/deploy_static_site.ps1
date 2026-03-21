<#
.SYNOPSIS
  Deploy RAPP static web UI (index.html, demos/, agents/) to Azure Blob Storage Static Website.

.DESCRIPTION
  Enables static website hosting on your existing Azure Storage account and uploads
  all HTML/CSS/JS/JSON files needed for the RAPP chat UI and Demo Showcase.

  After running, your demos will be available at:
    https://<storage-account>.z13.web.core.windows.net/
    https://<storage-account>.z13.web.core.windows.net/demos/demos.html

.PARAMETER StorageAccount
  Azure Storage account name (default: from local.settings.json)

.PARAMETER ResourceGroup
  Azure resource group (auto-detected if not provided)

.EXAMPLE
  .\deploy_static_site.ps1
  .\deploy_static_site.ps1 -StorageAccount "stkt6i6mlby5wzi"
#>

param(
    [string]$StorageAccount,
    [string]$ResourceGroup
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n🚀 RAPP Static Website Deployment" -ForegroundColor Cyan
Write-Host "=" * 50

# --- Resolve storage account ---
if (-not $StorageAccount) {
    $settingsPath = Join-Path $repoRoot "local.settings.json"
    if (Test-Path $settingsPath) {
        $settings = Get-Content $settingsPath | ConvertFrom-Json
        $StorageAccount = $settings.Values.AZURE_STORAGE_ACCOUNT_NAME
    }
    if (-not $StorageAccount) {
        Write-Host "❌ No storage account found. Pass -StorageAccount or set AZURE_STORAGE_ACCOUNT_NAME in local.settings.json" -ForegroundColor Red
        exit 1
    }
}
Write-Host "📦 Storage account: $StorageAccount" -ForegroundColor Yellow

# --- Check Azure CLI login ---
Write-Host "`nChecking Azure CLI login..." -ForegroundColor Gray
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in. Run 'az login' first." -ForegroundColor Red
    exit 1
}

# --- Auto-detect resource group ---
if (-not $ResourceGroup) {
    Write-Host "Detecting resource group..." -ForegroundColor Gray
    $ResourceGroup = (az storage account show --name $StorageAccount --query resourceGroup -o tsv 2>$null)
    if (-not $ResourceGroup) {
        Write-Host "❌ Could not find resource group for $StorageAccount" -ForegroundColor Red
        exit 1
    }
}
Write-Host "📁 Resource group: $ResourceGroup" -ForegroundColor Yellow

# --- Enable static website hosting ---
Write-Host "`nEnabling static website hosting..." -ForegroundColor Cyan
az storage blob service-properties update `
    --account-name $StorageAccount `
    --static-website `
    --index-document "welcome.html" `
    --404-document "welcome.html" `
    --auth-mode login 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Trying with storage key instead..." -ForegroundColor Yellow
    az storage blob service-properties update `
        --account-name $StorageAccount `
        --static-website `
        --index-document "welcome.html" `
        --404-document "welcome.html"
}
Write-Host "✅ Static website enabled" -ForegroundColor Green

# --- Upload files ---
Write-Host "`nUploading files to `$web container..." -ForegroundColor Cyan

# Files to upload (relative to repo root)
$filesToUpload = @(
    @{ Source = "index.html";      Dest = "index.html";      ContentType = "text/html" }
)

# Gather all demos/*.json and demos/*.html files
$demosDir = Join-Path $repoRoot "demos"
Get-ChildItem $demosDir -Filter "*.json" | ForEach-Object {
    $filesToUpload += @{ Source = "demos/$($_.Name)"; Dest = "demos/$($_.Name)"; ContentType = "application/json" }
}
Get-ChildItem $demosDir -Filter "*.html" | ForEach-Object {
    $filesToUpload += @{ Source = "demos/$($_.Name)"; Dest = "demos/$($_.Name)"; ContentType = "text/html" }
}

# Also upload any top-level HTML files that the UI links to
$extraHtml = @("welcome.html", "agent_store.html", "RAPP-Production-Guide.html", "rapp_presentation_slide.html")
foreach ($file in $extraHtml) {
    $path = Join-Path $repoRoot $file
    if (Test-Path $path) {
        $filesToUpload += @{ Source = $file; Dest = $file; ContentType = "text/html" }
    }
}

$uploaded = 0
$failed = 0
foreach ($f in $filesToUpload) {
    $sourcePath = Join-Path $repoRoot $f.Source
    if (-not (Test-Path $sourcePath)) {
        Write-Host "  ⏭️  Skip (not found): $($f.Source)" -ForegroundColor DarkGray
        continue
    }

    try {
        az storage blob upload `
            --account-name $StorageAccount `
            --container-name "`$web" `
            --name $f.Dest `
            --file $sourcePath `
            --content-type $f.ContentType `
            --overwrite `
            --auth-mode login 2>$null

        if ($LASTEXITCODE -ne 0) {
            # Retry without auth-mode login
            az storage blob upload `
                --account-name $StorageAccount `
                --container-name "`$web" `
                --name $f.Dest `
                --file $sourcePath `
                --content-type $f.ContentType `
                --overwrite 2>$null
        }

        Write-Host "  ✅ $($f.Dest)" -ForegroundColor Green
        $uploaded++
    } catch {
        Write-Host "  ❌ $($f.Dest): $_" -ForegroundColor Red
        $failed++
    }
}

# --- Get the static website URL ---
Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
$webUrl = (az storage account show --name $StorageAccount --query "primaryEndpoints.web" -o tsv 2>$null)
if ($webUrl) {
    Write-Host "🌐 Your RAPP UI is live at:" -ForegroundColor Green
    Write-Host "   Chat:  $($webUrl)index.html" -ForegroundColor White
    Write-Host "   Demos: $($webUrl)demos/demos.html" -ForegroundColor White
} else {
    Write-Host "🌐 Static website URL: https://$StorageAccount.z13.web.core.windows.net/" -ForegroundColor Green
}

Write-Host "`n📊 Uploaded: $uploaded files | Failed: $failed files" -ForegroundColor Cyan
Write-Host "✅ Deployment complete!`n" -ForegroundColor Green
