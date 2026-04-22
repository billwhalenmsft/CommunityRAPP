# ============================================================
#  RAPP Hatchery — Install the hatchery agent into your brainstem
#  Usage: irm https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/hatch.ps1 | iex
# ============================================================

$AgentUrl  = "https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/hatchery/rapp_hatchery_agent.py"
$AgentFile = "rapp_hatchery_agent.py"

Write-Host "=== RAPP Hatchery ===" -ForegroundColor Cyan
Write-Host ""

# ── Detect brainstem agents/ directory ──────────────────────

$AgentsDir = $null

# 1. Environment variable
if ($env:RAPP_BRAINSTEM_DIR -and (Test-Path "$env:RAPP_BRAINSTEM_DIR\agents")) {
    $AgentsDir = "$env:RAPP_BRAINSTEM_DIR\agents"
}
# 2. Current directory has soul.md
elseif ((Test-Path "soul.md") -and (Test-Path "agents")) {
    $AgentsDir = Join-Path (Get-Location) "agents"
}
# 3. Parent rapp_brainstem directory
elseif ((Test-Path "rapp_brainstem\soul.md") -and (Test-Path "rapp_brainstem\agents")) {
    $AgentsDir = Join-Path (Get-Location) "rapp_brainstem\agents"
}
# 4. Default install location
elseif (Test-Path "$HOME\rapp-installer\rapp_brainstem\agents") {
    $AgentsDir = "$HOME\rapp-installer\rapp_brainstem\agents"
}

if (-not $AgentsDir) {
    Write-Host "Could not find your brainstem's agents/ directory." -ForegroundColor Red
    Write-Host ""
    Write-Host "Try one of:"
    Write-Host "  1. Run this from inside your brainstem directory"
    Write-Host '  2. Set $env:RAPP_BRAINSTEM_DIR = "C:\path\to\rapp_brainstem"'
    Write-Host "  3. Install the brainstem first: https://github.com/kody-w/rapp-installer"
    exit 1
}

Write-Host "Brainstem agents directory: $AgentsDir"

# ── Download the hatchery agent ────────────────────────────

Write-Host "Downloading hatchery agent..."
$dest = Join-Path $AgentsDir $AgentFile
Invoke-WebRequest -Uri $AgentUrl -OutFile $dest -UseBasicParsing

Write-Host ""
Write-Host "Hatchery agent installed to $dest" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart your brainstem (or wait for the agent cache to refresh)"
Write-Host "  2. Tell your brainstem: 'Hatch a project called my-project'"
Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
