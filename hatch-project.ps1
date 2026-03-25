# ============================================================
#  RAPP Hatch Project — Create a CommunityRAPP instance for a customer
#
#  Usage:
#    irm https://raw.githubusercontent.com/kody-w/m365-agents-for-python/main/CommunityRAPP/hatch-project.ps1 | iex
#
#  Or with a name:
#    .\hatch-project.ps1 my-project
# ============================================================

param(
    [string]$ProjectName = ""
)

$ErrorActionPreference = "Stop"
$ProjectsDir = if ($env:RAPP_PROJECTS_DIR) { $env:RAPP_PROJECTS_DIR } else { "$HOME\rapp-projects" }
$RepoUrl     = "https://github.com/kody-w/m365-agents-for-python.git"
$BasePort    = 7072

# ── Helpers ─────────────────────────────────────────────────

function Find-Python {
    foreach ($cmd in @("python3.11", "python3.12", "python3", "python")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -eq 3 -and $minor -ge 11) {
                    return $cmd
                }
            }
        } catch {}
    }
    return $null
}

function Get-NextPort {
    $port = $BasePort
    $manifest = Join-Path $ProjectsDir ".hatchery.json"
    if (Test-Path $manifest) {
        try {
            $data = Get-Content $manifest -Raw | ConvertFrom-Json
            foreach ($proj in $data.projects.PSObject.Properties) {
                if ($proj.Value.port -ge $port) {
                    $port = $proj.Value.port + 1
                }
            }
        } catch {}
    }
    return $port
}

# ── Prompt for name if not provided ─────────────────────────

if (-not $ProjectName) {
    Write-Host ""
    Write-Host "=== RAPP Hatch Project ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Create a CommunityRAPP instance for a customer."
    Write-Host ""
    $ProjectName = Read-Host "Project name (e.g. contoso-bot)"
    if (-not $ProjectName) {
        Write-Host "ERROR: Project name is required." -ForegroundColor Red
        exit 1
    }
}

# ── Validate ────────────────────────────────────────────────

if ($ProjectName -notmatch '^[a-z0-9][a-z0-9-]*$') {
    Write-Host "ERROR: Invalid name '$ProjectName'. Use lowercase letters, numbers, and hyphens." -ForegroundColor Red
    exit 1
}

$ProjectDir = Join-Path $ProjectsDir $ProjectName
if (Test-Path $ProjectDir) {
    Write-Host "ERROR: Project '$ProjectName' already exists at $ProjectDir" -ForegroundColor Red
    exit 1
}

# ── Prerequisites ───────────────────────────────────────────

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is required. Install from https://git-scm.com" -ForegroundColor Red
    exit 1
}

$PythonCmd = Find-Python
if (-not $PythonCmd) {
    Write-Host "ERROR: Python 3.11+ required (3.13+ not recommended). Install from https://python.org" -ForegroundColor Red
    exit 1
}

$pyVer = & $PythonCmd --version 2>&1
Write-Host "==> Using $PythonCmd ($pyVer)"

# ── Clone ───────────────────────────────────────────────────

Write-Host ""
Write-Host "=== Hatching '$ProjectName' ===" -ForegroundColor Cyan
Write-Host ""

New-Item -ItemType Directory -Path $ProjectsDir -Force | Out-Null
$tmpDir = Join-Path $ProjectsDir ".tmp-$ProjectName-$PID"

Write-Host "==> Cloning CommunityRAPP..."
git clone --depth 1 --quiet $RepoUrl $tmpDir
Move-Item (Join-Path $tmpDir "CommunityRAPP") $ProjectDir
Remove-Item $tmpDir -Recurse -Force

# ── Venv + deps ─────────────────────────────────────────────

Write-Host "==> Creating virtual environment..."
& $PythonCmd -m venv (Join-Path $ProjectDir ".venv")

Write-Host "==> Installing dependencies..."
$pip = Join-Path $ProjectDir ".venv\Scripts\pip.exe"
& $pip install -r (Join-Path $ProjectDir "requirements.txt") --quiet 2>$null

# ── Settings ────────────────────────────────────────────────

$template = Join-Path $ProjectDir "local.settings.template.json"
$settings = Join-Path $ProjectDir "local.settings.json"
if ((Test-Path $template) -and -not (Test-Path $settings)) {
    Copy-Item $template $settings
    Write-Host "==> Copied settings template -> local.settings.json"
}

# ── Port + start scripts ───────────────────────────────────

$Port = Get-NextPort

@"
#!/usr/bin/env bash
# Start CommunityRAPP on port $Port
cd "`$(dirname "`$0")"
source .venv/bin/activate
func start --port $Port
"@ | Set-Content (Join-Path $ProjectDir "start.sh") -Encoding UTF8

@"
# Start CommunityRAPP on port $Port
`$ErrorActionPreference = 'Stop'
Set-Location `$PSScriptRoot
.venv\Scripts\Activate.ps1
func start --port $Port
"@ | Set-Content (Join-Path $ProjectDir "start.ps1") -Encoding UTF8

# ── Business Mode UI (first hatch deploys it) ────────────────

$BizHtml = Join-Path $ProjectsDir "business.html"
if (-not (Test-Path $BizHtml)) {
    Write-Host "==> Deploying Business Mode UI..."
    try {
        $BizUrl = "https://raw.githubusercontent.com/kody-w/m365-agents-for-python/main/CommunityRAPP/business.html"
        Invoke-WebRequest -Uri $BizUrl -OutFile $BizHtml -UseBasicParsing -ErrorAction SilentlyContinue
    } catch {}
}

# ── Update manifest ─────────────────────────────────────────

$manifest = Join-Path $ProjectsDir ".hatchery.json"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

if (Test-Path $manifest) {
    $data = Get-Content $manifest -Raw | ConvertFrom-Json
} else {
    $data = @{ projects = @{} } | ConvertTo-Json | ConvertFrom-Json
}

$data.projects | Add-Member -NotePropertyName $ProjectName -NotePropertyValue @{
    path       = $ProjectDir
    port       = $Port
    created_at = $timestamp
    python     = $PythonCmd
} -Force

$data | ConvertTo-Json -Depth 5 | Set-Content $manifest -Encoding UTF8

# ── Done ────────────────────────────────────────────────────

Write-Host ""
Write-Host "=== Project '$ProjectName' hatched ===" -ForegroundColor Green
Write-Host ""
Write-Host "  Location:  $ProjectDir"
Write-Host "  Port:      $Port"
Write-Host "  Python:    $PythonCmd"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Start locally:"
Write-Host "     cd $ProjectDir; .\start.ps1"
Write-Host ""
Write-Host "  2. Verify:"
Write-Host "     curl http://localhost:${Port}/api/health"
Write-Host ""
Write-Host "  Everything runs on your machine with local file storage."
Write-Host "  No Azure account or API keys needed to get started."
Write-Host ""
if (Test-Path $BizHtml) {
    Write-Host "  3. Business Mode (chat with brainstem + projects side by side):"
    Write-Host "     start $BizHtml"
    Write-Host ""
}
Write-Host "  When you're ready to add AI responses:"
Write-Host "     Edit $ProjectDir\local.settings.json"
Write-Host "     Add your Azure OpenAI endpoint, deployment name, and API key"
Write-Host ""
Write-Host "  When you're ready to deploy to the cloud:"
Write-Host "     See the deployment guide in $ProjectDir\docs\"
Write-Host ""
