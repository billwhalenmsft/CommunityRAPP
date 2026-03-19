<#
.SYNOPSIS
    Send in-app toast notifications to D365 Customer Service users.
.DESCRIPTION
    Creates appnotification records in Dataverse that appear as toast pop-ups
    inside the D365 model-driven app.  Supports:
      - New Case Created
      - SLA Nearing Breach / SLA Violated
      - Custom free-text notifications
    
    The notification shows in the bell icon area and as a transient toast.
    Requires the "In-app notifications" feature to be enabled in the target
    model-driven app (App Settings > Features > In-app notifications = On).
    
.PARAMETER Scenario
    Predefined scenario: 'NewCase', 'SLAWarning', 'SLAViolated', or 'Custom'.
.PARAMETER RecipientEmail
    Email of the user to notify.  Use '*' for all enabled users.
.PARAMETER CaseTitle
    Case title (used in NewCase / SLA scenarios).
.PARAMETER CaseNumber
    Case ticket number (used in NewCase / SLA scenarios).
.PARAMETER CaseId
    GUID of the case record (makes the notification clickable).
.PARAMETER CustomTitle
    Title for 'Custom' scenario.
.PARAMETER CustomBody
    Body text for 'Custom' scenario.
.EXAMPLE
    # New case toast to the logged-in user
    .\28-SendNotification.ps1 -Scenario NewCase -CaseTitle "Elevator stuck on floor 12" -CaseNumber "CAS-2026-00042"

    # SLA violation to a specific agent
    .\28-SendNotification.ps1 -Scenario SLAViolated -RecipientEmail "agent1@contoso.com" -CaseTitle "Backflow valve leaking" -CaseNumber "CAS-2026-00105"

    # Broadcast custom notification to all users
    .\28-SendNotification.ps1 -Scenario Custom -RecipientEmail '*' -CustomTitle "System Maintenance" -CustomBody "D365 will be unavailable 10pm-11pm tonight."
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('NewCase', 'SLAWarning', 'SLAViolated', 'Custom')]
    [string]$Scenario,

    [string]$RecipientEmail,
    [string]$CaseTitle,
    [string]$CaseNumber,
    [string]$CaseId,
    [string]$CustomTitle,
    [string]$CustomBody,
    [string]$Customer
)

# ── Bootstrap ──────────────────────────────────────────────
Import-Module (Join-Path $PSScriptRoot "DataverseHelper.psm1") -Force
Connect-Dataverse

# ── Resolve recipient(s) ──────────────────────────────────
function Get-RecipientIds {
    param([string]$Email)

    if (-not $Email -or $Email -eq '*') {
        # All enabled (licensed) users
        $users = Invoke-DataverseGet -EntitySet "systemusers" `
            -Filter "isdisabled eq false and accessmode ne 4" `
            -Select "systemuserid,fullname,internalemailaddress"
        return $users
    }

    # Single user by email
    $users = Invoke-DataverseGet -EntitySet "systemusers" `
        -Filter "internalemailaddress eq '$Email'" `
        -Select "systemuserid,fullname,internalemailaddress"
    if (-not $users -or $users.Count -eq 0) {
        throw "No systemuser found with email '$Email'"
    }
    return $users
}

# ── Build notification payload per scenario ────────────────
function Build-NotificationBody {
    param(
        [string]$Scenario,
        [string]$RecipientId,
        [hashtable]$Context
    )

    # Icon values: 100000000 = Info, 100000001 = Success, 100000002 = Failure, 100000003 = Warning, 100000004 = Mention
    # Toast type: 200000000 = Timed (auto-dismiss), 200000001 = Hidden (bell only)

    $body = @{
        "ownerid@odata.bind" = "/systemusers($RecipientId)"
        "appmoduleid"        = $null  # null = all apps the user has open
    }

    switch ($Scenario) {
        'NewCase' {
            $title = "New Case Assigned"
            $caseRef = if ($Context.CaseNumber) { " [$($Context.CaseNumber)]" } else { "" }
            $bodyText = "A new case$caseRef has been created"
            if ($Context.CaseTitle) { $bodyText += ": $($Context.CaseTitle)" }
            if ($Context.Customer)  { $bodyText += " for $($Context.Customer)" }

            $body["title"]                = $title
            $body["body"]                 = $bodyText
            $body["icontype"]             = 100000001  # Success (green check)
            $body["toasttype"]            = 200000000  # Timed toast
            $body["priority"]             = 200000000  # Normal
            $body["ttlinseconds"]         = 120
        }
        'SLAWarning' {
            $title = "SLA Warning — Nearing Breach"
            $caseRef = if ($Context.CaseNumber) { " [$($Context.CaseNumber)]" } else { "" }
            $bodyText = "Case$caseRef is approaching its SLA deadline"
            if ($Context.CaseTitle) { $bodyText += ": $($Context.CaseTitle)" }

            $body["title"]                = $title
            $body["body"]                 = $bodyText
            $body["icontype"]             = 100000003  # Warning (yellow triangle)
            $body["toasttype"]            = 200000000  # Timed toast
            $body["priority"]             = 200000001  # High
            $body["ttlinseconds"]         = 300
        }
        'SLAViolated' {
            $title = "SLA VIOLATED"
            $caseRef = if ($Context.CaseNumber) { " [$($Context.CaseNumber)]" } else { "" }
            $bodyText = "Case$caseRef has breached its SLA"
            if ($Context.CaseTitle) { $bodyText += ": $($Context.CaseTitle)" }

            $body["title"]                = $title
            $body["body"]                 = $bodyText
            $body["icontype"]             = 100000002  # Failure (red X)
            $body["toasttype"]            = 200000000  # Timed toast
            $body["priority"]             = 200000001  # High
            $body["ttlinseconds"]         = 600
        }
        'Custom' {
            $body["title"]                = if ($Context.CustomTitle) { $Context.CustomTitle } else { "Notification" }
            $body["body"]                 = if ($Context.CustomBody)  { $Context.CustomBody  } else { "" }
            $body["icontype"]             = 100000000  # Info
            $body["toasttype"]            = 200000000  # Timed toast
            $body["priority"]             = 200000000  # Normal
            $body["ttlinseconds"]         = 120
        }
    }

    # Add navigation action if we have a Case GUID
    if ($Context.CaseId) {
        $body["data"] = (@{
            type    = "mscrm.url"
            url     = "?pagetype=entityrecord&etn=incident&id=$($Context.CaseId)"
            navigationTarget = "dialog"
        } | ConvertTo-Json -Compress)
        $body["body"] += ". Click to open the case."
    }

    return $body
}

# ── Main ───────────────────────────────────────────────────
$context = @{
    CaseTitle   = $CaseTitle
    CaseNumber  = $CaseNumber
    CaseId      = $CaseId
    Customer    = $Customer
    CustomTitle = $CustomTitle
    CustomBody  = $CustomBody
}

$recipients = Get-RecipientIds -Email $RecipientEmail
$sentCount = 0
$failCount = 0

Write-Host "`n=== Sending $Scenario Notifications ===" -ForegroundColor Cyan
Write-Host "Recipients: $($recipients.Count)" -ForegroundColor White

foreach ($user in $recipients) {
    $userId   = $user.systemuserid
    $userName = $user.fullname

    $payload = Build-NotificationBody -Scenario $Scenario -RecipientId $userId -Context $context

    Write-Host "  → $userName ... " -NoNewline
    $result = Invoke-DataversePost -EntitySet "appnotifications" -Body $payload

    if ($result) {
        Write-Host "✓ Sent" -ForegroundColor Green
        $sentCount++
    } else {
        Write-Host "✗ Failed" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "  Sent:   $sentCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { 'Red' } else { 'Gray' })
Write-Host ""
