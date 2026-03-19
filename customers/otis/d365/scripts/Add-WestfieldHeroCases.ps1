<#
.SYNOPSIS
    Provision Westfield London Shopping Centre as the hero account for Otis demo
.DESCRIPTION
    Creates:
    1. Entrapment hero case on Westfield London (James Morrison) with full timeline
    2. Two resolved historical cases for account depth
    3. Timeline activities: phone calls, notes, emails
    
    Matches the v2 demo execution guide which centers on Westfield London.

.EXAMPLE
    .\Add-WestfieldHeroCases.ps1
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
Write-Host "  Otis Demo - Westfield London Hero Cases" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Connect to Dataverse
Connect-Dataverse

# ============================================================
# Step 1: Look up Westfield London account and James Morrison
# ============================================================
Write-StepHeader "1" "Look Up Westfield London Account & James Morrison"

$westfieldAcct = Invoke-DataverseGet -EntitySet "accounts" `
    -Filter "name eq 'Westfield London Shopping Centre'" `
    -Select "accountid,name" -Top 1
if (-not $westfieldAcct -or $westfieldAcct.Count -eq 0) {
    throw "Westfield London Shopping Centre account not found. Run base provisioning first."
}
$westfieldId = $westfieldAcct[0].accountid
Write-Host "  Found account: Westfield London Shopping Centre ($westfieldId)" -ForegroundColor Green

$jamesMorrison = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'james.morrison@westfield.com'" `
    -Select "contactid,fullname" -Top 1
if (-not $jamesMorrison -or $jamesMorrison.Count -eq 0) {
    throw "James Morrison contact not found. Run base provisioning first."
}
$jamesId = $jamesMorrison[0].contactid
Write-Host "  Found contact: James Morrison ($jamesId)" -ForegroundColor Green

# ============================================================
# Step 2: Create Entrapment Hero Case
# ============================================================
Write-StepHeader "2" "Create Entrapment Hero Case (Westfield London)"

$entrapmentCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Entrapment - Westfield London Elevator 7 (Passenger Trapped)'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "Entrapment - Westfield London Elevator 7 (Passenger Trapped)"
        description                              = "URGENT: Passenger trapped in Elevator 7 between floors 2 and 3 in the East Wing parking structure. Building security on scene maintaining intercom contact. Passenger is calm but claustrophobic. This is a high-traffic shopping centre - elevator serves the multi-storey car park. Saturday afternoon, heavy footfall."
        "customerid_account@odata.bind"          = "/accounts($westfieldId)"
        "primarycontactid@odata.bind"            = "/contacts($jamesId)"
        caseorigincode                           = 1   # Phone
        prioritycode                             = 1   # High (Critical)
        casetypecode                             = 2   # Problem
        statuscode                               = 2   # In Progress
    } `
    -DisplayName "Entrapment - Westfield London Elevator 7"

Write-Host "  Entrapment case ID: $entrapmentCaseId" -ForegroundColor Green

# ============================================================
# Step 3: Add Timeline Activities to Entrapment Case
# ============================================================
Write-StepHeader "3" "Add Timeline Activities (Entrapment Case)"

# Activity 1: Initial phone call from James Morrison
$call1 = @{
    subject                                  = "Initial entrapment report - Elevator 7 East Wing"
    description                              = "James Morrison (Centre Manager) called to report a passenger trapped in Elevator 7, East Wing car park. Passenger between floors 2 and 3. Building security on scene, maintaining intercom contact. Passenger is responsive but claustrophobic. Saturday afternoon - heavy foot traffic in the car park. James requests fastest possible response."
    phonenumber                              = "+1 310-277-3901"
    directioncode                            = $true   # Incoming
    "regardingobjectid_incident@odata.bind"  = "/incidents($entrapmentCaseId)"
    actualstart                              = "2026-03-15T14:03:00Z"
    actualend                                = "2026-03-15T14:06:00Z"
    actualdurationminutes                    = 3
}
try {
    Invoke-DataversePost -EntitySet "phonecalls" -Body $call1
    Write-Host "  Added phone call: Initial entrapment report" -ForegroundColor Green
} catch {
    Write-Warning "  Phone call failed: $($_.Exception.Message)"
}

# Activity 2: Internal note - Technician dispatch
$note1 = @{
    subject                                  = "Technician Dispatch - EMERGENCY"
    notetext                                 = "Premium contract - 2 hour SLA. Contacted London West dispatch. Sarah Palmer (Tech ID: OT-UK-3192) is currently at Shepherd's Bush depot, 12 minutes away. Rerouting immediately. Gen2 Comfort elevator - standard manual release procedure applies."
    "objectid_incident@odata.bind"           = "/incidents($entrapmentCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $note1
    Write-Host "  Added note: Technician dispatch" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}

# Activity 3: Outbound email to James Morrison
$email1 = @{
    subject                                  = "Technician ETA - Elevator 7 Entrapment - PRIORITY RESPONSE"
    description                              = "Mr. Morrison, Technician Sarah Palmer is en route to Westfield London. ETA 12 minutes. She will proceed directly to East Wing Elevator 7. Please ensure security maintains intercom contact with the trapped passenger and keeps the area clear. We will call you back in 5 minutes with a status update. Given this is peak shopping hours, we are treating this as highest priority."
    directioncode                            = $false  # Outgoing
    "regardingobjectid_incident@odata.bind"  = "/incidents($entrapmentCaseId)"
    actualstart                              = "2026-03-15T14:08:00Z"
}
try {
    Invoke-DataversePost -EntitySet "emails" -Body $email1
    Write-Host "  Added email: Technician ETA notification" -ForegroundColor Green
} catch {
    Write-Warning "  Email failed: $($_.Exception.Message)"
}

# Activity 4: 5-minute callback
$call2 = @{
    subject                                  = "5-minute update call - tech en route"
    description                              = "Called James to confirm technician Sarah Palmer is 7 minutes away. Passenger still calm. Security has offered water through the door gap. James confirmed East Wing loading dock is open for service vehicle access. Car park management has redirected traffic away from the elevator bank."
    phonenumber                              = "+1 310-277-3901"
    directioncode                            = $false  # Outgoing
    "regardingobjectid_incident@odata.bind"  = "/incidents($entrapmentCaseId)"
    actualstart                              = "2026-03-15T14:13:00Z"
    actualend                                = "2026-03-15T14:15:00Z"
    actualdurationminutes                    = 2
}
try {
    Invoke-DataversePost -EntitySet "phonecalls" -Body $call2
    Write-Host "  Added phone call: 5-minute callback" -ForegroundColor Green
} catch {
    Write-Warning "  Phone call failed: $($_.Exception.Message)"
}

# Activity 5: Note - Equipment history
$note2 = @{
    subject                                  = "Equipment History - Elevator 7 (GEN2-WL-007)"
    notetext                                 = "Checked maintenance records for Elevator 7 (Gen2 Comfort, serial GEN2-WL-007). Last serviced March 8. No prior entrapment incidents. Unit installed 2019. Door sensors replaced in Jan 2026 PM cycle. Possible cause: power fluctuation or door interlock fault. Sarah Palmer has Gen2 Comfort expertise and emergency release training."
    "objectid_incident@odata.bind"           = "/incidents($entrapmentCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $note2
    Write-Host "  Added note: Equipment history" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}


# ============================================================
# Step 4: Create Historical Resolved Case #1
# ============================================================
Write-StepHeader "4" "Create Historical Resolved Cases (Account Depth)"

# Resolved case 1: Escalator belt replacement from 2 weeks ago
$resolvedCase1Id = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Escalator Belt Adjustment - Westfield London Main Atrium'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "Escalator Belt Adjustment - Westfield London Main Atrium"
        description                              = "James Morrison reported escalator NCE-WL-003 in the main atrium was making a clicking noise during morning startup. Technician found belt tension slightly loose. Adjusted and tested. No parts required. Completed same day."
        "customerid_account@odata.bind"          = "/accounts($westfieldId)"
        "primarycontactid@odata.bind"            = "/contacts($jamesId)"
        caseorigincode                           = 1   # Phone
        prioritycode                             = 2   # Normal
        casetypecode                             = 2   # Problem
    } `
    -DisplayName "Escalator Belt Adjustment (resolved)"

Write-Host "  Resolved case 1 ID: $resolvedCase1Id" -ForegroundColor Green

# Resolve it
try {
    Invoke-DataversePatch -EntitySet "incidents" -RecordId ([guid]$resolvedCase1Id) -Body @{
        statuscode   = 5   # Problem Solved
        statecode    = 1   # Resolved
    }
    Write-Host "  Resolved case 1 (Problem Solved)" -ForegroundColor Green
} catch {
    Write-Warning "  Could not resolve case 1: $($_.Exception.Message)"
}

# Add a note to the resolved case
$resolvedNote1 = @{
    subject                                  = "Technician report - belt adjustment complete"
    notetext                                 = "Technician Marcus Webb (OT-UK-2156) attended site March 3 at 7:00 AM (before centre opening). Escalator NCE-WL-003 belt tension was 0.8mm below spec. Adjusted to specification, tested 50 cycles. No abnormal noise. Customer confirmed satisfied. Total time on site: 45 minutes."
    "objectid_incident@odata.bind"           = "/incidents($resolvedCase1Id)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $resolvedNote1
    Write-Host "  Added technician report note to resolved case 1" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}


# Resolved case 2: Annual safety inspection from last month
$resolvedCase2Id = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Annual Safety Inspection Coordination - Westfield London (All Units)'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "Annual Safety Inspection Coordination - Westfield London (All Units)"
        description                              = "Coordination for annual safety inspection of all 46 units (18 elevators, 24 escalators, 4 travolators). James Morrison requested a detailed schedule to minimize disruption during February half-term school holidays. Inspection completed over 3 days with zero findings requiring immediate action."
        "customerid_account@odata.bind"          = "/accounts($westfieldId)"
        "primarycontactid@odata.bind"            = "/contacts($jamesId)"
        caseorigincode                           = 2   # Email
        prioritycode                             = 2   # Normal
        casetypecode                             = 1   # Question
    } `
    -DisplayName "Annual Safety Inspection (resolved)"

Write-Host "  Resolved case 2 ID: $resolvedCase2Id" -ForegroundColor Green

# Resolve it
try {
    Invoke-DataversePatch -EntitySet "incidents" -RecordId ([guid]$resolvedCase2Id) -Body @{
        statuscode   = 5   # Problem Solved
        statecode    = 1   # Resolved
    }
    Write-Host "  Resolved case 2 (Problem Solved)" -ForegroundColor Green
} catch {
    Write-Warning "  Could not resolve case 2: $($_.Exception.Message)"
}

# Add activities to resolved case 2
$resolvedEmail1 = @{
    subject                                  = "Westfield London - Annual Inspection Schedule (Feb 17-19)"
    description                              = "James, attached is the inspection schedule for all 46 units across 3 days. Day 1 (Feb 17): All 18 elevators. Day 2 (Feb 18): Escalators 1-12. Day 3 (Feb 19): Escalators 13-24 + 4 travolators. We'll start at 6 AM each day. Lead inspector: Angela Price. Please confirm this works with your operations team."
    directioncode                            = $false  # Outgoing
    "regardingobjectid_incident@odata.bind"  = "/incidents($resolvedCase2Id)"
    actualstart                              = "2026-02-10T09:00:00Z"
}
try {
    Invoke-DataversePost -EntitySet "emails" -Body $resolvedEmail1
    Write-Host "  Added email: Inspection schedule" -ForegroundColor Green
} catch {
    Write-Warning "  Email failed: $($_.Exception.Message)"
}

$resolvedNote2 = @{
    subject                                  = "Inspection complete - all 46 units passed"
    notetext                                 = "Annual safety inspection completed across Feb 17-19. All 46 units passed. Minor recommendations: 1) Replace handrail brushes on escalators 8 and 14 (scheduled for March PM). 2) Update emergency lighting on elevator 12 car top. 3) Recalibrate load sensors on travolator 2. None are safety-critical. Full report sent to James Morrison and Westfield compliance team."
    "objectid_incident@odata.bind"           = "/incidents($resolvedCase2Id)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $resolvedNote2
    Write-Host "  Added note: Inspection results" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}


# ============================================================
# Step 5: Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Westfield London Hero Cases - Complete!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Created:" -ForegroundColor White
Write-Host "    ACTIVE  | Entrapment - Westfield London Elevator 7       ($entrapmentCaseId)" -ForegroundColor Yellow
Write-Host "    ACTIVE  | Escalator running rough (existing)              (already in D365)" -ForegroundColor DarkGray
Write-Host "    RESOLVED| Escalator Belt Adjustment                       ($resolvedCase1Id)" -ForegroundColor DarkGray
Write-Host "    RESOLVED| Annual Safety Inspection                        ($resolvedCase2Id)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Timeline activities added:" -ForegroundColor White
Write-Host "    Entrapment case: 2 phone calls, 1 email, 2 notes" -ForegroundColor White
Write-Host "    Resolved case 1: 1 note" -ForegroundColor White
Write-Host "    Resolved case 2: 1 email, 1 note" -ForegroundColor White
Write-Host ""
Write-Host "  Westfield London now has 4 cases (2 active, 2 resolved)" -ForegroundColor Cyan
Write-Host "  with rich timeline data for the demo." -ForegroundColor Cyan
Write-Host ""

# Save output for reference
$output = @{
    westfieldAccountId = $westfieldId
    jamesMorrisonId = $jamesId
    entrapmentCaseId = "$entrapmentCaseId"
    resolvedCase1Id = "$resolvedCase1Id"
    resolvedCase2Id = "$resolvedCase2Id"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
}
$outputPath = Join-Path (Split-Path -Parent $scriptDir) "data\westfield-hero-cases.json"
$output | ConvertTo-Json -Depth 3 | Out-File $outputPath -Encoding utf8
Write-Host "  Output saved to: $outputPath" -ForegroundColor Cyan
