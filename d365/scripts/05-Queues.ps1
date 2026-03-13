<#
.SYNOPSIS
    Step 05 - Create Queues for Zurn Elkay Customer Service
.DESCRIPTION
    Creates email and phone queues matching their Salesforce Pulse supervisor
    layout. Assigns queues for the two brands.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "05" "Create Queues"
Connect-Dataverse

# ============================================================
# Queue definitions - matching their Pulse Service Zurn layout
# ============================================================
Write-Host "Creating customer service queues..." -ForegroundColor Yellow

$queues = @(
    # --- Zurn Email Queues ---
    @{ name = "Apps-Eng-CB Email";       type = "Email"; brand = "Zurn";  desc = "Applications Engineering and Commercial/Builder email queue" },
    @{ name = "Commercial Email";        type = "Email"; brand = "Zurn";  desc = "Commercial plumbing product inquiries via email" },
    @{ name = "Consumer";                type = "Email"; brand = "Zurn";  desc = "Consumer/homeowner inquiries - general product questions" },
    @{ name = "Drainage";               type = "Email"; brand = "Zurn";  desc = "Floor drains, trench drains, roof drains inquiries" },
    @{ name = "eCommerce";              type = "Email"; brand = "Zurn";  desc = "eCommerce order support and online sales inquiries" },
    @{ name = "General Support";         type = "Email"; brand = "Zurn";  desc = "General customer support - catch-all queue" },
    @{ name = "Install Care";           type = "Email"; brand = "Zurn";  desc = "Installation guidance and post-install support" },
    @{ name = "PVF/Hydro Retail";        type = "Email"; brand = "Zurn";  desc = "PVF and Hydro retail product support" },

    # --- Zurn Phone Queues ---
    @{ name = "Zurn Phone - Tier 1";     type = "Phone"; brand = "Zurn";  desc = "Phone queue for Tier 1 strategic distributor calls" },
    @{ name = "Zurn Phone - General";    type = "Phone"; brand = "Zurn";  desc = "Phone queue for general incoming calls" },
    @{ name = "Zurn Phone - Tech Support"; type = "Phone"; brand = "Zurn"; desc = "Phone queue for technical troubleshooting calls" },
    @{ name = "Zurn Phone - Backflow/Wilkins"; type = "Phone"; brand = "Zurn"; desc = "Phone queue for Wilkins backflow product calls" },

    # --- Elkay Email Queues ---
    @{ name = "Elkay Hydration Support"; type = "Email"; brand = "Elkay"; desc = "Bottle fillers, drinking fountains, water coolers" },
    @{ name = "Elkay Sinks & Fixtures";  type = "Email"; brand = "Elkay"; desc = "Stainless steel sinks, faucets, accessories" },
    @{ name = "Elkay General Support";   type = "Email"; brand = "Elkay"; desc = "General Elkay customer support" },
    @{ name = "Elkay Orders";           type = "Email"; brand = "Elkay"; desc = "Elkay order management and status inquiries" },

    # --- Elkay Phone Queues ---
    @{ name = "Elkay Phone - General";   type = "Phone"; brand = "Elkay"; desc = "General Elkay phone support" },
    @{ name = "Elkay Phone - Tech";      type = "Phone"; brand = "Elkay"; desc = "Elkay technical support calls" }
)

$queueIds = @{}
foreach ($q in $queues) {
    # Queue incoming type: 0 = default queue for entity type
    $body = @{
        name        = $q.name
        description = "$($q.brand) | $($q.type) | $($q.desc)"
        queueviewtype = 0  # Public
    }

    # Set email on email queues (placeholder - replace with real mailbox if available)
    if ($q.type -eq "Email") {
        $emailAlias = ($q.name -replace '[^a-zA-Z0-9]', '').ToLower()
        $body["emailaddress"] = "$emailAlias@zurnelkay-demo.com"
    }

    $id = Find-OrCreate-Record `
        -EntitySet "queues" `
        -Filter "name eq '$($q.name)'" `
        -IdField "queueid" `
        -Body $body `
        -DisplayName "$($q.name) [$($q.type)]"

    $queueIds[$q.name] = $id
}

# ============================================================
# Summary
# ============================================================
$emailCount = ($queues | Where-Object { $_.type -eq "Email" }).Count
$phoneCount = ($queues | Where-Object { $_.type -eq "Phone" }).Count
$zurnCount  = ($queues | Where-Object { $_.brand -eq "Zurn" }).Count
$elkayCount = ($queues | Where-Object { $_.brand -eq "Elkay" }).Count

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Queues Created Successfully" -ForegroundColor Green
Write-Host " Total Queues  : $($queues.Count)" -ForegroundColor White
Write-Host " Email Queues  : $emailCount" -ForegroundColor White
Write-Host " Phone Queues  : $phoneCount" -ForegroundColor White
Write-Host " Zurn Queues   : $zurnCount" -ForegroundColor White
Write-Host " Elkay Queues  : $elkayCount" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

# Export
$queueIds | ConvertTo-Json -Depth 2 | Out-File "$scriptDir\..\data\queue-ids.json" -Encoding utf8
Write-Host "Queue IDs saved to data\queue-ids.json" -ForegroundColor DarkGray
