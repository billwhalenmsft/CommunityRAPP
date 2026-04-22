<#
.SYNOPSIS
    Send a seed email to the D365 support queue for live demo.

.DESCRIPTION
    Uses Microsoft Graph API to send an email that will be picked up by D365
    Omnichannel email routing. This creates a live case during the demo.

    Prerequisites:
    - `az login` completed (uses Azure CLI token for Graph API)
    - D365 email routing enabled with a shared mailbox or queue mailbox
    - The sender email should match a Contact record in D365 for customer recognition

.PARAMETER Scenario
    Which seed email to send:
      BG-Email   — Christine Delacroix / B&G Triton2 wind issue (default, best for demo)
      LWR-Email  — Mike Torres / Lowrance HDS-9 power issue (B2C consumer)

.PARAMETER ToAddress
    The D365 support queue email address (e.g., support@yourorg.onmicrosoft.com)

.PARAMETER FromAddress
    Send-as address. If not specified, sends from the logged-in user.

.PARAMETER DryRun
    Show the email content without sending.

.EXAMPLE
    .\Send-NavicoSeedEmail.ps1 -ToAddress "support@orgecbce8ef.onmicrosoft.com"
    .\Send-NavicoSeedEmail.ps1 -Scenario LWR-Email -ToAddress "support@yourorg.onmicrosoft.com"
    .\Send-NavicoSeedEmail.ps1 -DryRun
#>

[CmdletBinding()]
param(
    [ValidateSet("BG-Email", "LWR-Email")]
    [string]$Scenario = "BG-Email",

    [string]$ToAddress = "",

    [string]$FromAddress = "",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# ============================================================
# SEED EMAIL TEMPLATES
# ============================================================

$templates = @{
    "BG-Email" = @{
        subject = "B&G Triton2 Wind Angle Issue — 3 units affected, race season approaching"
        body    = @"
Hi Navico Support,

I'm Christine Delacroix, Service Manager at Euro Marine Distributors (Account: EMEA-001).

We have an urgent situation. Three of our B&G Triton2 Instrument Displays are showing erratic Apparent Wind Angle (AWA) readings. The wind angle values are jumping ±15-20 degrees randomly, making them unusable for competitive sailing.

Affected units:
- Serial BG-2024-TRI2-20011 (flagship demo vessel)
- Serial BG-2024-TRI2-20013 (customer fleet unit)
- Serial BG-2024-TRI2-20015 (customer fleet unit)

All three units were running firmware v2.4.1 and the issue started after last week's calibration session. We've already tried:
1. Factory reset on all three displays
2. Re-running the AWA calibration wizard
3. Checking the masthead wind sensor connections

None of these resolved the issue. Our spring racing season starts in 3 weeks and we have 4 vessels that depend on these instruments.

As a Platinum Expert partner, I'd like to escalate this to your B&G sailing instrument specialists. We may need RMA replacements if this can't be resolved via firmware.

Can someone from your B&G team get back to me urgently?

Best regards,
Christine Delacroix
Service Manager | Euro Marine Distributors
christine.delacroix@D365DemoTSCE30330346.onmicrosoft.com
+44 20 7946 0123
"@
        senderName = "Christine Delacroix"
        brand      = "B&G"
    }

    "LWR-Email" = @{
        subject = "My Lowrance HDS wont turn on"
        body    = @"
Hi,

I bought my HDS 9 Live about a year ago and this morning it just won't turn on at all. I tried pressing the power button many times and checked the fuse but nothing works. Serial is on the back of the unit - LWR-2024-HDS-88821. Please help!

I really need this fixed before my fishing trip next weekend.

Thanks,
Mike Torres
mjtorres87@gmail.com
"@
        senderName = "Mike Torres"
        brand      = "Lowrance"
    }
}

$template = $templates[$Scenario]

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Navico Demo — Seed Email" -ForegroundColor Cyan
Write-Host "  Scenario : $Scenario ($($template.senderName) / $($template.brand))" -ForegroundColor DarkGray
Write-Host "  To       : $(if ($ToAddress) {$ToAddress} else {'(not set)'})" -ForegroundColor DarkGray
Write-Host "  Mode     : $(if ($DryRun) {'DRY RUN'} else {'LIVE'})" -ForegroundColor $(if ($DryRun) {'Yellow'} else {'Green'})
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Write-Host "Subject: $($template.subject)" -ForegroundColor White
Write-Host ""
Write-Host $template.body -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "(Dry run — email not sent)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To send for real:" -ForegroundColor Cyan
    Write-Host "  .\Send-NavicoSeedEmail.ps1 -ToAddress 'YOUR_QUEUE_EMAIL' -Scenario $Scenario" -ForegroundColor White
    exit 0
}

if (-not $ToAddress) {
    Write-Host "ERROR: -ToAddress is required. Set it to your D365 queue mailbox email." -ForegroundColor Red
    Write-Host "Example: .\Send-NavicoSeedEmail.ps1 -ToAddress 'support@orgecbce8ef.onmicrosoft.com'" -ForegroundColor Yellow
    exit 1
}

# ============================================================
# SEND VIA MICROSOFT GRAPH
# ============================================================

Write-Host "Getting Microsoft Graph token via Azure CLI..." -ForegroundColor Gray
$graphToken = az account get-access-token --resource "https://graph.microsoft.com" --query accessToken -o tsv 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Could not get Graph token. Run 'az login' first." -ForegroundColor Red
    Write-Host $graphToken -ForegroundColor DarkRed
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $graphToken"
    "Content-Type"  = "application/json"
}

$emailPayload = @{
    message = @{
        subject = $template.subject
        body = @{
            contentType = "Text"
            content     = $template.body
        }
        toRecipients = @(
            @{ emailAddress = @{ address = $ToAddress } }
        )
    }
    saveToSentItems = $true
} | ConvertTo-Json -Depth 5

try {
    $sendUrl = "https://graph.microsoft.com/v1.0/me/sendMail"
    Invoke-RestMethod -Uri $sendUrl -Method Post -Headers $headers -Body $emailPayload
    Write-Host "✓ Email sent successfully!" -ForegroundColor Green
    Write-Host "  From: (your account)" -ForegroundColor DarkGray
    Write-Host "  To:   $ToAddress" -ForegroundColor DarkGray
    Write-Host "  Subj: $($template.subject)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "The email should appear in the D365 Omnichannel queue within 1-2 minutes." -ForegroundColor Cyan
    Write-Host "A case will be auto-created when the routing rule picks it up." -ForegroundColor Cyan
} catch {
    Write-Host "ERROR sending email: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor DarkRed
    }
    exit 1
}
