<#
.SYNOPSIS
    Create test cases on Riverside Medical to demonstrate hot word banners
.DESCRIPTION
    Creates 3 test cases on the Riverside Medical Centre account:
    1. CRITICAL hot words -> RED banner (entrapment, trapped)
    2. HIGH hot words -> YELLOW banner (out of service, not working)
    3. No hot words -> No banner (control case for comparison)

    Open each case to see the different banner behaviors after wiring
    bw_OtisCaseFormScripts to the Enhanced Full Case Form.

.EXAMPLE
    .\Add-RiversideTestCases.ps1
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
Write-Host "  Riverside Medical - Hot Word Test Cases" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Connect to Dataverse
Connect-Dataverse

# ============================================================
# Known IDs
# ============================================================
$riversideAccountId = "f05e7b68-241f-f111-8342-7ced8d18cb3b"
$davidChenId        = "2fd09570-241f-f111-8341-7c1e5218592b"

# Verify account exists
Write-StepHeader "1" "Verify Riverside Medical Centre Account"

$acct = Invoke-DataverseGet -EntitySet "accounts" `
    -Filter "accountid eq $riversideAccountId" `
    -Select "accountid,name" -Top 1

if (-not $acct -or $acct.Count -eq 0) {
    throw "Riverside Medical Centre not found with ID: $riversideAccountId"
}
Write-Host "  Account: $($acct[0].name) ($riversideAccountId)" -ForegroundColor Green

$contact = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "contactid eq $davidChenId" `
    -Select "contactid,fullname" -Top 1

if ($contact -and $contact.Count -gt 0) {
    Write-Host "  Contact: $($contact[0].fullname) ($davidChenId)" -ForegroundColor Green
} else {
    Write-Warning "David Chen contact not found - cases will be created without primary contact"
    $davidChenId = $null
}

# ============================================================
# Test Case 1: CRITICAL Hot Words -> RED Banner
# ============================================================
Write-StepHeader "2" "Test Case 1: CRITICAL Keywords (RED Banner)"

$criticalBody = @{
    title                                    = "Emergency - Passenger Trapped in Service Elevator B2"
    description                              = "URGENT: Elderly patient trapped between floors in service elevator B2. Patient is using a wheelchair and reports feeling dizzy. Nurse on intercom reports the patient has an injury to their left arm from when the elevator stopped abruptly. Fire alarm was triggered on floor 3. Building security on scene."
    "customerid_account@odata.bind"          = "/accounts($riversideAccountId)"
    caseorigincode                           = 1   # Phone
    casetypecode                             = 2   # Problem
    prioritycode                             = 2   # Normal (JS should auto-set to High)
    statuscode                               = 1   # In Progress
}

if ($davidChenId) {
    $criticalBody["primarycontactid@odata.bind"] = "/contacts($davidChenId)"
}

$criticalCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Emergency - Passenger Trapped in Service Elevator B2'" `
    -IdField "incidentid" `
    -Body $criticalBody `
    -DisplayName "CRITICAL Test Case (Trapped + Injury + Fire)"

Write-Host "  Case ID: $criticalCaseId" -ForegroundColor Green
Write-Host "  Hot words: TRAPPED, INJURY, FIRE, EMERGENCY" -ForegroundColor Red
Write-Host "  Expected: RED banner - EMERGENCY ALERT" -ForegroundColor Red

# ============================================================
# Test Case 2: HIGH Hot Words -> YELLOW Banner
# ============================================================
Write-StepHeader "3" "Test Case 2: HIGH Keywords (YELLOW Banner)"

$highBody = @{
    title                                    = "Elevator 5 Out of Service - Maternity Ward Access"
    description                              = "Main patient elevator (Elevator 5) is not working as of 07:30 this morning. Maternity ward on floor 4 has no lift access for patients. Multiple complaints from staff and visitors. A safety inspection was completed last week with no issues found. Requesting priority repair."
    "customerid_account@odata.bind"          = "/accounts($riversideAccountId)"
    caseorigincode                           = 2   # Email
    casetypecode                             = 2   # Problem
    prioritycode                             = 2   # Normal (JS should auto-set to High)
    statuscode                               = 1   # In Progress
}

if ($davidChenId) {
    $highBody["primarycontactid@odata.bind"] = "/contacts($davidChenId)"
}

$highCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Elevator 5 Out of Service - Maternity Ward Access'" `
    -IdField "incidentid" `
    -Body $highBody `
    -DisplayName "HIGH Test Case (Out of Service + Not Working + Complaint)"

Write-Host "  Case ID: $highCaseId" -ForegroundColor Green
Write-Host "  Hot words: OUT OF SERVICE, NOT WORKING, COMPLAINT, SAFETY INSPECTION" -ForegroundColor Yellow
Write-Host "  Expected: YELLOW banner - PRIORITY ESCALATION" -ForegroundColor Yellow

# ============================================================
# Test Case 3: No Hot Words -> No Banner (Control)
# ============================================================
Write-StepHeader "4" "Test Case 3: No Keywords (No Banner - Control)"

$normalBody = @{
    title                                    = "Scheduled quarterly maintenance - Elevators 1-4"
    description                              = "Quarterly preventive maintenance due for elevators 1 through 4 per service contract OC-RM-2026. Please schedule a technician visit for next week. David Chen will coordinate building access. Preferred window: Tuesday or Wednesday, 06:00-08:00 before main visiting hours."
    "customerid_account@odata.bind"          = "/accounts($riversideAccountId)"
    caseorigincode                           = 2   # Email
    casetypecode                             = 3   # Request
    prioritycode                             = 2   # Normal (should stay Normal)
    statuscode                               = 1   # In Progress
}

if ($davidChenId) {
    $normalBody["primarycontactid@odata.bind"] = "/contacts($davidChenId)"
}

$normalCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Scheduled quarterly maintenance - Elevators 1-4'" `
    -IdField "incidentid" `
    -Body $normalBody `
    -DisplayName "CONTROL Test Case (No Hot Words)"

Write-Host "  Case ID: $normalCaseId" -ForegroundColor Green
Write-Host "  Hot words: NONE" -ForegroundColor Gray
Write-Host "  Expected: No banner. Priority stays Normal." -ForegroundColor Gray

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  TEST CASES CREATED" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Account: Riverside Medical Centre" -ForegroundColor White
Write-Host "  Contact: David Chen (Facilities Manager)" -ForegroundColor White
Write-Host ""
Write-Host "  Case 1 (CRITICAL / RED):" -ForegroundColor Red
Write-Host "    Title:    Emergency - Passenger Trapped in Service Elevator B2" -ForegroundColor White
Write-Host "    ID:       $criticalCaseId" -ForegroundColor White
Write-Host "    Keywords: trapped, injury, fire, emergency" -ForegroundColor Red
Write-Host ""
Write-Host "  Case 2 (HIGH / YELLOW):" -ForegroundColor Yellow
Write-Host "    Title:    Elevator 5 Out of Service - Maternity Ward Access" -ForegroundColor White
Write-Host "    ID:       $highCaseId" -ForegroundColor White
Write-Host "    Keywords: out of service, not working, complaint, safety inspection" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Case 3 (CONTROL / None):" -ForegroundColor Gray
Write-Host "    Title:    Scheduled quarterly maintenance - Elevators 1-4" -ForegroundColor White
Write-Host "    ID:       $normalCaseId" -ForegroundColor White
Write-Host "    Keywords: none" -ForegroundColor Gray
Write-Host ""
Write-Host "  TESTING: Open each case to verify banner behavior" -ForegroundColor Yellow
Write-Host "  (Requires bw_OtisCaseFormScripts wired to Enhanced Full Case Form)" -ForegroundColor Yellow
Write-Host ""

# Save output IDs
$output = @{
    account    = "Riverside Medical Centre"
    accountId  = $riversideAccountId
    contactId  = $davidChenId
    testCases  = @(
        @{ type = "CRITICAL"; id = $criticalCaseId; title = "Emergency - Passenger Trapped in Service Elevator B2"; hotWords = @("trapped","injury","fire","emergency"); banner = "RED" }
        @{ type = "HIGH";     id = $highCaseId;     title = "Elevator 5 Out of Service - Maternity Ward Access";   hotWords = @("out of service","not working","complaint","safety inspection"); banner = "YELLOW" }
        @{ type = "CONTROL";  id = $normalCaseId;   title = "Scheduled quarterly maintenance - Elevators 1-4";     hotWords = @(); banner = "NONE" }
    )
} | ConvertTo-Json -Depth 4

$outputPath = Join-Path $scriptDir "..\data\riverside-test-cases.json"
$outputDir = Split-Path -Parent $outputPath
if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir -Force | Out-Null }
$output | Out-File -FilePath $outputPath -Encoding UTF8
Write-Host "  Output saved: $outputPath" -ForegroundColor Cyan
