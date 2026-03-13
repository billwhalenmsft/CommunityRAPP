<#
.SYNOPSIS
    Fix connection references for Quality Evaluation Agent, 
    Knowledge Management Agent, and Case Management Agent.
.DESCRIPTION
    Programmatically sets connectionid on connection references 
    that are EMPTY, using existing authenticated connections 
    from the same environment.
#>

$ErrorActionPreference = "Stop"
$orgUrl = "https://orgecbce8ef.crm.dynamics.com"
$apiUrl = "$orgUrl/api/data/v9.2"

# --- Authenticate ---
Write-Host "`n=== Authenticating ===" -ForegroundColor Cyan
$token = az account get-access-token --resource $orgUrl --query accessToken -o tsv
if (-not $token) { throw "Could not get access token. Run 'az login' first." }
$headers = @{
    Authorization      = "Bearer $token"
    Accept             = "application/json"
    "Content-Type"     = "application/json; charset=utf-8"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}
Write-Host "Authenticated." -ForegroundColor Green

# --- Step 1: Get ALL connection references ---
Write-Host "`n=== Step 1: Querying all connection references ===" -ForegroundColor Cyan
$allRefs = (Invoke-RestMethod -Uri "$apiUrl/connectionreferences?`$select=connectionreferenceid,connectionreferencedisplayname,connectionid,connectorid" -Headers $headers).value

# --- Step 2: Find existing working connections by connector type ---
Write-Host "`n=== Step 2: Finding existing connections to reuse ===" -ForegroundColor Cyan

# Dataverse connections that are already set
$dvRefs = $allRefs | Where-Object { $_.connectorid -like '*commondataserviceforapps*' -and $_.connectionid }
$dvConnectionIds = $dvRefs | Select-Object -ExpandProperty connectionid -Unique
Write-Host "  Found $($dvConnectionIds.Count) existing Dataverse connection(s):"
$dvConnectionIds | ForEach-Object { Write-Host "    - $_" -ForegroundColor DarkGray }

# Copilot Studio connections that are already set
$mcsRefs = $allRefs | Where-Object { $_.connectorid -like '*copilotstudio*' -and $_.connectionid }
$mcsConnectionIds = $mcsRefs | Select-Object -ExpandProperty connectionid -Unique
Write-Host "  Found $($mcsConnectionIds.Count) existing Copilot Studio connection(s):"
$mcsConnectionIds | ForEach-Object { Write-Host "    - $_" -ForegroundColor DarkGray }

# Office 365 connections
$o365Refs = $allRefs | Where-Object { $_.connectorid -like '*office365*' -and $_.connectionid }
$o365ConnectionIds = $o365Refs | Select-Object -ExpandProperty connectionid -Unique
Write-Host "  Found $($o365ConnectionIds.Count) existing Office 365 connection(s):"
$o365ConnectionIds | ForEach-Object { Write-Host "    - $_" -ForegroundColor DarkGray }

# Pick the first available connection for each type
$dvConnId = $dvConnectionIds | Select-Object -First 1
$mcsConnId = $mcsConnectionIds | Select-Object -First 1
$o365ConnId = $o365ConnectionIds | Select-Object -First 1

if (-not $dvConnId) {
    Write-Host "`n  WARNING: No existing Dataverse connection found!" -ForegroundColor Red
    Write-Host "  You need to create one manually first:" -ForegroundColor Yellow
    Write-Host "  1. Go to https://make.powerapps.com > Connections" -ForegroundColor Yellow
    Write-Host "  2. Click + New connection > Microsoft Dataverse" -ForegroundColor Yellow
    Write-Host "  3. Sign in and create it, then re-run this script" -ForegroundColor Yellow
}
if (-not $mcsConnId) {
    Write-Host "`n  WARNING: No existing Copilot Studio connection found!" -ForegroundColor Red
    Write-Host "  You need to create one manually first:" -ForegroundColor Yellow
    Write-Host "  1. Go to https://make.powerapps.com > Connections" -ForegroundColor Yellow
    Write-Host "  2. Click + New connection > Microsoft Copilot Studio" -ForegroundColor Yellow
    Write-Host "  3. Sign in and create it, then re-run this script" -ForegroundColor Yellow
}

# --- Step 3: Define which connection references need fixing ---
# These are the specific refs for QEA, KM, and Case Management agents

$refsToFix = @(
    # Quality Evaluation Agent - Dataverse
    @{ 
        Id       = "b378a5ed-8f93-4352-9155-c94854009c9d"
        Name     = "Microsoft Dataverse Connection Reference for QEA"
        ConnType = "Dataverse"
    },
    @{
        Id       = "49cd4cc6-2ca3-42a2-a747-0fb1c034c771"
        Name     = "Microsoft Dataverse CDS Connection for QEA Conversation"
        ConnType = "Dataverse"
    },
    @{
        Id       = "c7de0812-6072-4b13-be78-91fd303894be"
        Name     = "QMA.Incident.DVPluginConnection"
        ConnType = "Dataverse"
    },
    # Quality Evaluation Agent - Copilot Studio
    @{
        Id       = "4fb28300-ddc2-494f-ab18-b1bd9ff0e7e9"
        Name     = "Microsoft Copilot Studio Connection Reference for QEA"
        ConnType = "CopilotStudio"
    },
    # Knowledge Management Agent - Dataverse
    @{
        Id       = "bf26e2fa-b105-4901-adf4-111bb3f12840"
        Name     = "Microsoft Dataverse CustomerServiceKnowledgeHarvest"
        ConnType = "Dataverse"
    },
    # Knowledge Management Agent - Copilot Studio
    @{
        Id       = "3d8e30e4-1a18-4194-bcd1-3f8eb6453c9f"
        Name     = "Microsoft Copilot Studio CustomerServiceKnowledgeHarvest"
        ConnType = "CopilotStudio"
    },
    # Case Management Agent - Dataverse
    @{
        Id       = "6aabf1db-6625-4f8a-9e2c-266416d28acd"
        Name     = "Case Management Agent CDS Connection"
        ConnType = "Dataverse"
    },
    # Case Management Agent - Copilot Studio
    @{
        Id       = "581b7d9d-871b-4bf0-a0c0-a4334d413325"
        Name     = "Case Management Agent MCS Connection"
        ConnType = "CopilotStudio"
    }
)

# --- Step 4: PATCH each connection reference ---
Write-Host "`n=== Step 3: Updating connection references ===" -ForegroundColor Cyan

$successCount = 0
$failCount = 0
$skipCount = 0

foreach ($ref in $refsToFix) {
    $targetConnId = switch ($ref.ConnType) {
        "Dataverse" { $dvConnId }
        "CopilotStudio" { $mcsConnId }
        "Office365" { $o365ConnId }
    }

    if (-not $targetConnId) {
        Write-Host "  SKIP  $($ref.Name) - no $($ref.ConnType) connection available" -ForegroundColor Yellow
        $skipCount++
        continue
    }

    # Check if already set
    $existing = $allRefs | Where-Object { $_.connectionreferenceid -eq $ref.Id }
    if ($existing.connectionid -eq $targetConnId) {
        Write-Host "  OK    $($ref.Name) - already set" -ForegroundColor Green
        continue
    }

    Write-Host "  PATCH $($ref.Name)" -ForegroundColor White -NoNewline
    Write-Host " -> $targetConnId" -ForegroundColor DarkGray

    $body = @{ connectionid = $targetConnId } | ConvertTo-Json
    $patchUrl = "$apiUrl/connectionreferences($($ref.Id))"

    try {
        Invoke-RestMethod -Uri $patchUrl -Method Patch -Headers $headers -Body $body -ErrorAction Stop
        Write-Host "         Done" -ForegroundColor Green
        $successCount++
    } catch {
        $errMsg = $_.ErrorDetails.Message
        if ($errMsg) {
            $errObj = $errMsg | ConvertFrom-Json -ErrorAction SilentlyContinue
            $detail = if ($errObj.error.message) { $errObj.error.message } else { $errMsg }
        } else {
            $detail = $_.Exception.Message
        }
        Write-Host "         FAILED: $detail" -ForegroundColor Red
        $failCount++
    }
}

# --- Summary ---
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "  Updated:  $successCount" -ForegroundColor Green
Write-Host "  Failed:   $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Skipped:  $skipCount" -ForegroundColor $(if ($skipCount -gt 0) { "Yellow" } else { "Green" })

if ($failCount -eq 0 -and $skipCount -eq 0) {
    Write-Host "`nAll connection references updated!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Turn on the flows in Power Automate:" -ForegroundColor White
    Write-Host "     - QEA On Demand Evaluation Case" -ForegroundColor DarkGray
    Write-Host "     - AI Evaluation Flow for Conversation" -ForegroundColor DarkGray
    Write-Host "     - Expire evaluations" -ForegroundColor DarkGray
    Write-Host "     - QEA Simulation" -ForegroundColor DarkGray
    Write-Host "     - Knowledge Harvest Trigger Flow V2" -ForegroundColor DarkGray
    Write-Host "  2. Publish the Copilot Studio agents:" -ForegroundColor White
    Write-Host "     - Quality Evaluation Agent" -ForegroundColor DarkGray
    Write-Host "     - CustomerServiceKnowledgeHarvest" -ForegroundColor DarkGray
} elseif ($skipCount -gt 0) {
    Write-Host "`nSome references were skipped because no connection exists." -ForegroundColor Yellow
    Write-Host "Create the missing connections at https://make.powerapps.com > Connections," -ForegroundColor Yellow
    Write-Host "then re-run this script." -ForegroundColor Yellow
}
