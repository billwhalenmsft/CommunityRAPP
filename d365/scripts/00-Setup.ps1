<#
.SYNOPSIS
    Step 00 - Master Orchestrator - Run All Setup Scripts
.DESCRIPTION
    Dynamics Demo Prep - Runs all D365 Customer Service demo setup scripts in order.
    Supports running individual steps or all steps sequentially.
    
.PARAMETER Customer
    Customer folder name under customers/ (e.g., -Customer Zurn). Defaults to Zurn.

.PARAMETER From
    Start from a specific step number (e.g., -From 3 to start at Products).
    
.PARAMETER Only
    Run only a specific step number (e.g., -Only 5 to run only Queues).

.EXAMPLE
    # Run everything for default customer
    .\00-Setup.ps1
    
    # Run for a specific customer
    .\00-Setup.ps1 -Customer Contoso

    # Run from step 3 onward
    .\00-Setup.ps1 -From 3
    
    # Run only step 5
    .\00-Setup.ps1 -Only 5
#>

[CmdletBinding()]
param(
    [string]$Customer = "Zurn",
    [int]$From = 1,
    [int]$Only = 0
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============================================================
# Banner
# ============================================================
# Load customer config if available
# Path: customers/{Customer}/d365/config/environment.json (from repo root)
$configFile = "$scriptDir\..\..\customers\$Customer\d365\config\environment.json"
$envName = "Demo Environment"
$envUrl = "(not configured)"
if (Test-Path $configFile) {
    $cfg = Get-Content $configFile | ConvertFrom-Json
    $envName = $cfg.environment.name
    $envUrl = $cfg.environment.url
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host "  Dynamics Demo Prep - Data Setup" -ForegroundColor Magenta
Write-Host "  Environment: $envName" -ForegroundColor DarkGray
Write-Host "  URL: $envUrl" -ForegroundColor DarkGray
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host ""

# ============================================================
# Verify prerequisites
# ============================================================
Write-Host "Checking prerequisites..." -ForegroundColor Cyan

# Check pac CLI
try {
    $pacCheck = & pac help 2>&1
    Write-Host "  pac CLI: Installed" -ForegroundColor DarkGray
} catch {
    throw "pac CLI not found. Install via: dotnet tool install --global Microsoft.PowerApps.CLI.Tool"
}

# Temporarily allow errors from native commands (az cli writes warnings to stderr)
$ErrorActionPreference = "SilentlyContinue"

# Check az CLI
$azVersionOutput = & az version 2>$null
$ErrorActionPreference = "Stop"
if ($azVersionOutput) {
    $azVer = ($azVersionOutput | ConvertFrom-Json -ErrorAction SilentlyContinue).'azure-cli'
    Write-Host "  az CLI: $azVer" -ForegroundColor DarkGray
} else {
    throw "Azure CLI not found. Install from https://aka.ms/installazurecliwindows"
}

# Check az login
$ErrorActionPreference = "SilentlyContinue"
$azAccount = & az account show --query "user.name" -o tsv 2>$null
$ErrorActionPreference = "Stop"
if ($azAccount) {
    Write-Host "  az login: $azAccount" -ForegroundColor DarkGray
} else {
    Write-Host "  Not logged in to Azure CLI. Running 'az login'..." -ForegroundColor Yellow
    az login
}

# Check pac auth
$ErrorActionPreference = "SilentlyContinue"
$pacAuth = pac auth list 2>$null
$ErrorActionPreference = "Stop"
Write-Host "  pac auth: Connected" -ForegroundColor DarkGray

Write-Host ""

# ============================================================
# Define steps
# ============================================================
$steps = @(
    @{ num = 1; name = "Accounts"; script = "01-Accounts.ps1" },
    @{ num = 2; name = "Contacts"; script = "02-Contacts.ps1" },
    @{ num = 3; name = "Products"; script = "03-Products.ps1" },
    @{ num = 3.5; name = "Parts Products"; script = "03a-PartsProducts.ps1"; conditional = $true },
    @{ num = 4; name = "Case Config"; script = "04-CaseConfig.ps1" },
    @{ num = 5; name = "Queues"; script = "05-Queues.ps1" },
    @{ num = 6; name = "SLAs"; script = "06-SLAs.ps1" },
    @{ num = 7; name = "Demo Cases"; script = "07-DemoCases.ps1" },
    @{ num = 8; name = "Knowledge Articles"; script = "08-KnowledgeArticles.ps1" },
    @{ num = 9; name = "Entitlements"; script = "09-Entitlements.ps1" },
    @{ num = 10; name = "Routing"; script = "10-Routing.ps1" },
    @{ num = 11; name = "Classification"; script = "11-Classification.ps1" },
    @{ num = 12; name = "Queue Visuals"; script = "12-QueueAndVisuals.ps1" },
    @{ num = 13; name = "Tier Field"; script = "13-TierField.ps1" },
    @{ num = 14; name = "Portal"; script = "14-Portal.ps1" },
    @{ num = 15; name = "Chat Widget"; script = "15-ChatWidget.ps1" },
    @{ num = 16; name = "KB Page"; script = "16-KBPage.ps1" },
    @{ num = 17; name = "Phone Scenario"; script = "17-PhoneScenario.ps1" },
    @{ num = 18; name = "Chat Scenario"; script = "18-ChatScenario.ps1" },
    @{ num = 19; name = "Portal Hero Users"; script = "19-PortalHeroUsers.ps1" },
    @{ num = 20; name = "Order Management"; script = "20-OrderMgmt.ps1" },
    @{ num = 21; name = "Shipment Tracking"; script = "21-ShipmentTracking.ps1" },
    @{ num = 22; name = "Customer Intent Agent"; script = "22-CustomerIntentAgent.ps1" },
    @{ num = 23; name = "Workforce Management"; script = "23-WFM.ps1" },
    @{ num = 29; name = "Call Pop Notification"; script = "29-CallPopNotification.ps1" }
)

# Filter steps
if ($Only -gt 0) {
    $steps = $steps | Where-Object { $_.num -eq $Only }
    if ($steps.Count -eq 0) {
        throw "Invalid step number: $Only. Valid: 1-23, 29 (use 3.5 for Parts Products)."
    }
} elseif ($From -gt 1) {
    $steps = $steps | Where-Object { $_.num -ge $From }
}

# ============================================================
# Confirmation
# ============================================================
Write-Host "Steps to execute:" -ForegroundColor Yellow
foreach ($s in $steps) {
    Write-Host "  [$($s.num)] $($s.name) - $($s.script)" -ForegroundColor White
}
Write-Host ""
$confirm = Read-Host "Press Enter to start, or Ctrl+C to cancel"

# ============================================================
# Execute
# ============================================================
$startTime = Get-Date
$results = @()

foreach ($s in $steps) {
    $stepStart = Get-Date
    $scriptPath = Join-Path $scriptDir $s.script

    if (-not (Test-Path $scriptPath)) {
        Write-Warning "Script not found: $($s.script) - Skipping."
        $results += @{ step = $s.num; name = $s.name; status = "SKIPPED"; duration = "0s" }
        continue
    }

    # Conditional step: 03a-PartsProducts only runs if a parts catalog exists for this customer
    if ($s.conditional) {
        $partsCatalog = "$scriptDir\..\..\customers\$Customer\d365\data\parts-catalog.json"
        if (-not (Test-Path $partsCatalog)) {
            Write-Host "  No parts catalog found for $Customer - skipping $($s.name)" -ForegroundColor DarkGray
            $results += @{ step = $s.num; name = $s.name; status = "SKIPPED (no catalog)"; duration = "0s" }
            continue
        }
    }

    try {
        # Pass -Customer for scripts that accept it (03a-PartsProducts)
        if ($s.script -eq "03a-PartsProducts.ps1") {
            & $scriptPath -Customer $Customer
        } else {
            & $scriptPath
        }
        $duration = [math]::Round(((Get-Date) - $stepStart).TotalSeconds, 1)
        $results += @{ step = $s.num; name = $s.name; status = "SUCCESS"; duration = "${duration}s" }
    } catch {
        $duration = [math]::Round(((Get-Date) - $stepStart).TotalSeconds, 1)
        Write-Error "Step $($s.num) ($($s.name)) failed: $($_.Exception.Message)"
        $results += @{ step = $s.num; name = $s.name; status = "FAILED"; duration = "${duration}s"; error = $_.Exception.Message }

        $continue = Read-Host "Continue to next step? (Y/N)"
        if ($continue -ne "Y") {
            break
        }
    }
}

# ============================================================
# Final Summary
# ============================================================
$totalDuration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host "  SETUP COMPLETE" -ForegroundColor Magenta
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host ""
Write-Host "  Results:" -ForegroundColor White

foreach ($r in $results) {
    $statusColor = switch ($r.status) {
        "SUCCESS" { "Green" }
        "FAILED" { "Red" }
        "SKIPPED" { "Yellow" }
    }
    Write-Host "  [$($r.step)] $($r.name.PadRight(15)) $($r.status.PadRight(8)) ($($r.duration))" -ForegroundColor $statusColor
}

Write-Host ""
Write-Host "  Total time: ${totalDuration}s" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Cyan
Write-Host "    1. Activate SLA in Customer Service admin center" -ForegroundColor White
Write-Host "    2. Configure Unified Routing workstreams" -ForegroundColor White
Write-Host "    3. Set up Genesys CTI via Channel Integration Framework" -ForegroundColor White
Write-Host "    4. Enable Copilot features (Case Summary, Draft Email)" -ForegroundColor White
Write-Host "    5. Build Power BI dashboards (replace Tableau)" -ForegroundColor White
Write-Host ""
