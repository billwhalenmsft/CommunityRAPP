<#
.SYNOPSIS
    Fix from/to on Westfield London timeline activities
.DESCRIPTION
    Phone calls and emails in Dataverse require activity party records for
    from/to fields. This script patches the existing activities on the
    Westfield London entrapment case to set proper from/to parties.

    Activity Party participationtypemask values:
      1 = From (Sender)
      2 = To (Recipient)
      3 = CC
      4 = BCC

.EXAMPLE
    .\Fix-WestfieldActivityParties.ps1
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir)))

# Import Dataverse helper
$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) {
    Import-Module $helperPath -Force
} else {
    throw "DataverseHelper.psm1 not found at: $helperPath"
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Fix Activity Parties - Westfield London Cases" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

# ============================================================
# Look up IDs
# ============================================================

# Get the current user (agent) systemuserid
$headers = Get-DataverseHeaders
$apiUrl = Get-DataverseApiUrl
$me = Invoke-RestMethod -Uri "$apiUrl/systemusers?`$filter=fullname eq 'Bill Whalen'&`$select=systemuserid,fullname&`$top=1" -Headers $headers -Method Get
if (-not $me.value -or $me.value.Count -eq 0) {
    # Fallback: get current user via WhoAmI
    $whoami = Invoke-RestMethod -Uri "$apiUrl/WhoAmI" -Headers $headers -Method Get
    $agentUserId = $whoami.UserId
    Write-Host "  Agent (current user): $agentUserId" -ForegroundColor Green
} else {
    $agentUserId = $me.value[0].systemuserid
    Write-Host "  Agent: $($me.value[0].fullname) ($agentUserId)" -ForegroundColor Green
}

# James Morrison contact
$jamesId = "8cb9067a-241f-f111-8342-7c1e520a58a1"
Write-Host "  James Morrison: $jamesId" -ForegroundColor Green

# Westfield entrapment case
$entrapmentCaseId = "ffef6969-5a21-f111-8341-6045bda80a72"
Write-Host "  Entrapment case: $entrapmentCaseId" -ForegroundColor Green

# ============================================================
# Step 1: Fix Phone Calls on Entrapment Case
# ============================================================
Write-StepHeader "1" "Fix Phone Call Activity Parties"

# Get all phone calls on the entrapment case
$phoneCalls = Invoke-DataverseGet -EntitySet "phonecalls" `
    -Filter "_regardingobjectid_value eq $entrapmentCaseId" `
    -Select "activityid,subject,directioncode"

Write-Host "  Found $($phoneCalls.Count) phone calls to fix" -ForegroundColor Cyan

foreach ($call in $phoneCalls) {
    $callId = $call.activityid
    $subject = $call.subject
    $isIncoming = $call.directioncode  # true = incoming

    if ($isIncoming) {
        # Incoming: From = James Morrison (contact), To = Agent (systemuser)
        $fromParty = @{ "partyid_contact@odata.bind" = "/contacts($jamesId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 2 }
    } else {
        # Outgoing: From = Agent (systemuser), To = James Morrison (contact)
        $fromParty = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_contact@odata.bind" = "/contacts($jamesId)"; participationtypemask = 2 }
    }

    $body = @{
        phonecall_activity_parties = @($fromParty, $toParty)
    }

    try {
        Invoke-DataversePatch -EntitySet "phonecalls" -RecordId ([guid]$callId) -Body $body
        $dir = if ($isIncoming) { "IN" } else { "OUT" }
        Write-Host "  Fixed [$dir]: $subject" -ForegroundColor Green
    } catch {
        Write-Warning "  Failed to fix phone call '$subject': $($_.Exception.Message)"
    }
}

# ============================================================
# Step 2: Fix Emails on Entrapment Case
# ============================================================
Write-StepHeader "2" "Fix Email Activity Parties"

$emails = Invoke-DataverseGet -EntitySet "emails" `
    -Filter "_regardingobjectid_value eq $entrapmentCaseId" `
    -Select "activityid,subject,directioncode"

Write-Host "  Found $($emails.Count) emails to fix" -ForegroundColor Cyan

foreach ($email in $emails) {
    $emailId = $email.activityid
    $subject = $email.subject
    $isIncoming = $email.directioncode

    if ($isIncoming) {
        $fromParty = @{ "partyid_contact@odata.bind" = "/contacts($jamesId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 2 }
    } else {
        $fromParty = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_contact@odata.bind" = "/contacts($jamesId)"; participationtypemask = 2 }
    }

    $body = @{
        email_activity_parties = @($fromParty, $toParty)
    }

    try {
        Invoke-DataversePatch -EntitySet "emails" -RecordId ([guid]$emailId) -Body $body
        $dir = if ($isIncoming) { "IN" } else { "OUT" }
        Write-Host "  Fixed [$dir]: $subject" -ForegroundColor Green
    } catch {
        Write-Warning "  Failed to fix email '$subject': $($_.Exception.Message)"
    }
}

# ============================================================
# Step 3: Fix Resolved Case Activities Too
# ============================================================
Write-StepHeader "3" "Fix Resolved Case Email Parties"

# Annual Safety Inspection resolved case email
$resolvedCase2Id = "7ab82279-5a21-f111-8342-7ced8d18c8d7"
$resolvedEmails = Invoke-DataverseGet -EntitySet "emails" `
    -Filter "_regardingobjectid_value eq $resolvedCase2Id" `
    -Select "activityid,subject"

foreach ($email in $resolvedEmails) {
    $body = @{
        email_activity_parties = @(
            @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 1 },
            @{ "partyid_contact@odata.bind" = "/contacts($jamesId)"; participationtypemask = 2 }
        )
    }
    try {
        Invoke-DataversePatch -EntitySet "emails" -RecordId ([guid]$email.activityid) -Body $body
        Write-Host "  Fixed [OUT]: $($email.subject)" -ForegroundColor Green
    } catch {
        Write-Warning "  Failed: $($_.Exception.Message)"
    }
}

# ============================================================
# Also fix the ORIGINAL Riverside Medical activities
# ============================================================
Write-StepHeader "4" "Fix Riverside Medical Case Activities (David Chen)"

$davidChenId = "2fd09570-241f-f111-8341-7c1e5218592b"
$riversideCaseId = "bfb12275-b420-f111-8342-7ced8d18c8d7"

# Phone calls
$rmPhoneCalls = Invoke-DataverseGet -EntitySet "phonecalls" `
    -Filter "_regardingobjectid_value eq $riversideCaseId" `
    -Select "activityid,subject,directioncode"

Write-Host "  Found $($rmPhoneCalls.Count) Riverside Medical phone calls" -ForegroundColor Cyan

foreach ($call in $rmPhoneCalls) {
    $callId = $call.activityid
    $isIncoming = $call.directioncode

    if ($isIncoming) {
        $fromParty = @{ "partyid_contact@odata.bind" = "/contacts($davidChenId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 2 }
    } else {
        $fromParty = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_contact@odata.bind" = "/contacts($davidChenId)"; participationtypemask = 2 }
    }

    try {
        Invoke-DataversePatch -EntitySet "phonecalls" -RecordId ([guid]$callId) -Body @{
            phonecall_activity_parties = @($fromParty, $toParty)
        }
        $dir = if ($isIncoming) { "IN" } else { "OUT" }
        Write-Host "  Fixed [$dir]: $($call.subject)" -ForegroundColor Green
    } catch {
        Write-Warning "  Failed: $($_.Exception.Message)"
    }
}

# Emails
$rmEmails = Invoke-DataverseGet -EntitySet "emails" `
    -Filter "_regardingobjectid_value eq $riversideCaseId" `
    -Select "activityid,subject,directioncode"

Write-Host "  Found $($rmEmails.Count) Riverside Medical emails" -ForegroundColor Cyan

foreach ($email in $rmEmails) {
    $isIncoming = $email.directioncode

    if ($isIncoming) {
        $fromParty = @{ "partyid_contact@odata.bind" = "/contacts($davidChenId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 2 }
    } else {
        $fromParty = @{ "partyid_systemuser@odata.bind" = "/systemusers($agentUserId)"; participationtypemask = 1 }
        $toParty   = @{ "partyid_contact@odata.bind" = "/contacts($davidChenId)"; participationtypemask = 2 }
    }

    try {
        Invoke-DataversePatch -EntitySet "emails" -RecordId ([guid]$email.activityid) -Body @{
            email_activity_parties = @($fromParty, $toParty)
        }
        $dir = if ($isIncoming) { "IN" } else { "OUT" }
        Write-Host "  Fixed [$dir]: $($email.subject)" -ForegroundColor Green
    } catch {
        Write-Warning "  Failed: $($_.Exception.Message)"
    }
}

# ============================================================
# Done
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Activity Parties Fixed!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Phone calls and emails now show proper From/To:" -ForegroundColor White
Write-Host "    Incoming calls: From = Contact, To = Agent" -ForegroundColor White
Write-Host "    Outgoing calls: From = Agent, To = Contact" -ForegroundColor White
Write-Host "    Outgoing emails: From = Agent, To = Contact" -ForegroundColor White
Write-Host ""
