<#
.SYNOPSIS
    Step 18 - Chat Scenario Data Setup
.DESCRIPTION
    Builds sample data for two chat demo scenarios:
      Scenario A: HD Supply (Tier 2) - James Morales chats about flush valve issue
      Scenario B: Ferguson (Tier 1) - Rachel Chen chats about warranty/RMA for filters
    Creates enriched account data, cases, timeline activities, and a chat-specific
    case for each scenario. The Copilot Studio bot will handle initial triage and
    then escalate to a live Customer Care Associate.
.NOTES
    Run with: .\18-ChatScenario.ps1
    Prerequisites: Scripts 01-17 must have been run first.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Connect-Dataverse

# ============================================================
# Load reference IDs
# ============================================================
$accountIds = Get-Content "$scriptDir\..\data\account-ids.json" | ConvertFrom-Json
$adminUserId = "cc00d659-5f51-ef11-a317-0022482a41a0"
$apiUrl = Get-DataverseApiUrl
$headers = Get-DataverseHeaders

$hdSupplyId  = $accountIds.Distributors."HD Supply"
$fergusonId  = $accountIds.Distributors."Ferguson Enterprises"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Chat Scenario Data Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  HD Supply ID:  $hdSupplyId" -ForegroundColor DarkGray
Write-Host "  Ferguson ID:   $fergusonId" -ForegroundColor DarkGray

# ============================================================
# Step 1: Enrich HD Supply account
# ============================================================
Write-StepHeader "1" "Enrich HD Supply Account"

$hdPatch = @{
    revenue                  = 8500000000.0
    numberofemployees        = 11500
    websiteurl               = "https://www.hdsupply.com"
    address1_line1           = "3400 Peachtree Road NE"
    address1_city            = "Atlanta"
    address1_stateorprovince = "GA"
    address1_postalcode      = "30326"
    address1_country         = "US"
    description              = "Major MRO and specialty distribution. Tier 2 Premium account. Key verticals: hospitality, healthcare, government facilities. Zurn flush valves and drainage are primary product lines. Annual Zurn volume: approx 6M. Key contact: James Morales (Commercial Accounts)."
}

try {
    Invoke-RestMethod -Uri "$apiUrl/accounts($hdSupplyId)" -Method Patch `
        -Headers $headers -Body ($hdPatch | ConvertTo-Json -Depth 3) `
        -ContentType "application/json; charset=utf-8" -ErrorAction Stop
    Write-Host "  HD Supply enriched (revenue, address, tier, description)" -ForegroundColor Green
} catch {
    Write-Warning "  HD Supply patch failed: $($_.Exception.Message)"
}

# ============================================================
# Step 2: Look up existing contacts
# ============================================================
Write-StepHeader "2" "Look Up Contacts"

# James Morales (HD Supply)
$jamesResult = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'james.morales@hdsupply.com'" `
    -Select "contactid,fullname"
$jamesId = if ($jamesResult -and $jamesResult.Count -gt 0) { $jamesResult[0].contactid } else { $null }
Write-Host "  James Morales ID: $jamesId" -ForegroundColor Green

# Rachel Chen (Ferguson)
$rachelResult = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'rachel.chen@ferguson.com'" `
    -Select "contactid,fullname"
$rachelId = if ($rachelResult -and $rachelResult.Count -gt 0) { $rachelResult[0].contactid } else { $null }
Write-Host "  Rachel Chen ID:   $rachelId" -ForegroundColor Green

# Ensure Rachel is linked to Ferguson (may have been created under a different parent)
if ($rachelId) {
    try {
        Invoke-DataversePatch -EntitySet "contacts" -RecordId $rachelId -Body @{
            "parentcustomerid_account@odata.bind" = "/accounts($fergusonId)"
        }
        Write-Host "  Rachel Chen linked to Ferguson" -ForegroundColor Green
    } catch {
        Write-Warning "  Could not link Rachel to Ferguson: $($_.Exception.Message)"
    }
}

# Tom Harrison (Ferguson)
$tomResult = Invoke-DataverseGet -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'tom.harrison@ferguson.com'" `
    -Select "contactid,fullname"
$tomId = if ($tomResult -and $tomResult.Count -gt 0) { $tomResult[0].contactid } else { $null }
Write-Host "  Tom Harrison ID:  $tomId" -ForegroundColor Green

# ============================================================
# Step 3: Create a second HD Supply contact (site contact)
# ============================================================
Write-StepHeader "3" "Create HD Supply Site Contact -- Derek Lawson"

$derekId = Find-OrCreate-Record `
    -EntitySet "contacts" `
    -Filter "emailaddress1 eq 'derek.lawson@hdsupply.com'" `
    -IdField "contactid" `
    -Body @{
        firstname                                = "Derek"
        lastname                                 = "Lawson"
        jobtitle                                 = "Facilities Maintenance Supervisor"
        emailaddress1                            = "derek.lawson@hdsupply.com"
        telephone1                               = "(770) 555-2305"
        address1_city                            = "Atlanta"
        address1_stateorprovince                 = "GA"
        description                              = "On-site maintenance supervisor for HD Supply hospitality accounts. Handles installation issues, warranty claims, and product troubleshooting. Primary escalation contact for flush valve and sensor products."
        "parentcustomerid_account@odata.bind"    = "/accounts($hdSupplyId)"
    } `
    -DisplayName "Derek Lawson (HD Supply - Facilities)"

# Ensure Derek is linked to HD Supply (in case he was created without the parent bind)
try {
    Invoke-DataversePatch -EntitySet "contacts" -RecordId $derekId -Body @{
        "parentcustomerid_account@odata.bind" = "/accounts($hdSupplyId)"
    }
    Write-Host "  Derek Lawson linked to HD Supply" -ForegroundColor Green
} catch {
    Write-Warning "  Could not link Derek to HD Supply: $($_.Exception.Message)"
}
Write-Host "  Derek Lawson ID: $derekId" -ForegroundColor Green

# ============================================================
# Step 4: Scenario A -- HD Supply Chat Case (Flush Valve Issue)
# ============================================================
Write-StepHeader "4" "Scenario A: HD Supply Flush Valve Chat Case"

# Existing case: prior resolved issue (gives history)
$hdResolvedId = $null
try {
$hdResolvedId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'HD Supply - Marriott Buckhead flush valve replacement (complete)'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "HD Supply - Marriott Buckhead flush valve replacement (complete)"
        description                              = "Replaced 12 Zurn AquaVantage flush valves (ZN-AV-1001) across 3 floors at Marriott Buckhead. Units were original 2019 install, showing normal wear. Swap completed in 2 days. Derek Lawson coordinated on-site. No warranty claim -- outside coverage period."
        "customerid_account@odata.bind"          = "/accounts($hdSupplyId)"
        "primarycontactid@odata.bind"            = "/contacts($derekId)"
        caseorigincode                           = 1   # Phone
        prioritycode                             = 3   # Normal
        cr377_tierlevel                          = 192350001
    } `
    -DisplayName "HD Supply - Marriott flush valve (resolved history)"
} catch {
    Write-Warning "  Could not create resolved case: $($_.Exception.Message)"
}

# The active chat case -- Derek Lawson chats about sensor flush issue
$hdChatCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'HD Supply - AquaVantage sensor flush intermittent activation at Hilton Midtown'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "HD Supply - AquaVantage sensor flush intermittent activation at Hilton Midtown"
        description                              = "Derek Lawson reports intermittent phantom flushes on 8 Zurn AquaVantage sensor flush valves (ZN-AV-1001) installed at Hilton Midtown Atlanta. Units are 7 months old -- well within warranty. Flushing randomly without occupancy, approx 3-5 times per hour. Water waste is significant. Hotel management escalating. Derek tried battery replacement and sensor cleaning per standard troubleshooting -- no improvement."
        "customerid_account@odata.bind"          = "/accounts($hdSupplyId)"
        "primarycontactid@odata.bind"            = "/contacts($derekId)"
        caseorigincode                           = 3   # Web
        prioritycode                             = 2   # High
        cr377_tierlevel                          = 192350001
    } `
    -DisplayName "HD Supply - Sensor flush chat case"

Write-Host "  HD Supply chat case ID: $hdChatCaseId" -ForegroundColor Green

# Timeline: prior email from James flagging the issue
$hdEmailBody = @{
    subject                                = "FW: Hilton Midtown -- flush valve complaints escalating"
    description                            = "James forwarded the Hilton GM complaint email. 8 AquaVantage units on floors 4-6 are phantom flushing. Hotel estimates 2000+ gallons per day wasted. Derek has been troubleshooting on-site for a week. Tried new batteries, cleaned sensors, checked water pressure -- all normal. James requesting priority warranty support and possible firmware update or unit swap."
    directioncode                          = $true
    "regardingobjectid_incident@odata.bind" = "/incidents($hdChatCaseId)"
    actualstart                            = "2026-03-01T09:20:00Z"
}
try {
    Invoke-DataversePost -EntitySet "emails" -Body $hdEmailBody
    Write-Host "  Added email: James forwarded Hilton complaint" -ForegroundColor Green
} catch {
    Write-Warning "  Email failed: $($_.Exception.Message)"
}

# Timeline: internal note from service team
$hdNote1 = @{
    subject                              = "Engineering bulletin check -- AquaVantage sensors"
    notetext                             = "Checked with Paso Robles engineering team. They confirmed a known issue with AquaVantage sensor module firmware v2.3 that can cause phantom activation in high-humidity environments (hotel bathrooms are a common trigger). Firmware v2.4 patch resolves the issue. Patch can be applied on-site with the ZN-PROG-001 programming tool. If units are under warranty, we ship replacement sensor modules with updated firmware pre-loaded."
    "objectid_incident@odata.bind"       = "/incidents($hdChatCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $hdNote1
    Write-Host "  Added note: engineering bulletin on sensor firmware" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}

# Timeline: Derek's troubleshooting log
$hdNote2 = @{
    subject                              = "On-site troubleshooting log -- Derek Lawson"
    notetext                             = "March 2: Replaced batteries on all 8 units (Duracell Ultra). No change. March 3: Cleaned IR sensors with isopropyl per maintenance guide. No change. March 4: Checked water pressure -- 62 PSI, within spec (45-80). Checked for reflective surfaces near sensors -- removed one mirror that was borderline. Still phantom flushing floor 5 unit 3. Humidity measured at 78% average in affected restrooms. Derek suspects environmental factor."
    "objectid_incident@odata.bind"       = "/incidents($hdChatCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $hdNote2
    Write-Host "  Added note: Derek on-site troubleshooting log" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}

# ============================================================
# Step 5: Scenario B -- Ferguson Chat Case (Warranty/RMA for Filters)
# ============================================================
Write-StepHeader "5" "Scenario B: Ferguson Filter Warranty Chat Case"

$fergChatCaseId = Find-OrCreate-Record `
    -EntitySet "incidents" `
    -Filter "title eq 'Ferguson - WaterSentry Plus filter defect batch WS-2026-0217'" `
    -IdField "incidentid" `
    -Body @{
        title                                    = "Ferguson - WaterSentry Plus filter defect batch WS-2026-0217"
        description                              = "Rachel Chen reports that 50 WaterSentry Plus filters (EK-FL-6003) from batch WS-2026-0217 are showing premature flow rate degradation. Filters rated for 3000 gallons are failing at approximately 1200 gallons. Affecting 3 Ferguson branch locations in Texas. Rachel has retained samples for analysis. Requesting warranty RMA for the full batch of 50 units. She also wants to know if this batch was shipped to any other Ferguson locations."
        "customerid_account@odata.bind"          = "/accounts($fergusonId)"
        "primarycontactid@odata.bind"            = "/contacts($rachelId)"
        caseorigincode                           = 3   # Web
        prioritycode                             = 2   # High
        cr377_tierlevel                          = 192350000
    } `
    -DisplayName "Ferguson - Filter warranty chat case"

Write-Host "  Ferguson chat case ID: $fergChatCaseId" -ForegroundColor Green

# Timeline: email from Rachel notifying about the defect
$fergEmail = @{
    subject                                = "WaterSentry Plus batch WS-2026-0217 -- early failure report"
    description                            = "Rachel sent photos and test data from two of the failed filters. Flow rate dropped below acceptable threshold at 1200 gallons (rated 3000). She tested 5 units from the same batch and all showed similar degradation. Batch WS-2026-0217 was received Feb 17. Filters are installed in EZH2O bottle filling stations across Houston, Dallas, and San Antonio branches. Rachel retained 10 unused units from the batch for analysis."
    directioncode                          = $true
    "regardingobjectid_incident@odata.bind" = "/incidents($fergChatCaseId)"
    actualstart                            = "2026-03-03T11:45:00Z"
}
try {
    Invoke-DataversePost -EntitySet "emails" -Body $fergEmail
    Write-Host "  Added email: Rachel defect report with photos" -ForegroundColor Green
} catch {
    Write-Warning "  Email failed: $($_.Exception.Message)"
}

# Timeline: internal quality check note
$fergNote1 = @{
    subject                              = "Quality team review -- batch WS-2026-0217"
    notetext                             = "Quality team confirmed batch WS-2026-0217 (manufactured Erie plant, Feb 10-12) had a carbon media loading variance. 200 units shipped: 50 to Ferguson (TX branches), 80 to Hajoca (PA), 70 to Pacific Plumbing (WA). All units from this batch are potentially affected. Quality team recommends proactive recall of the entire batch. RMA approved for Ferguson -- ship replacement filters from batch WS-2026-0303 (verified good)."
    "objectid_incident@odata.bind"       = "/incidents($fergChatCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $fergNote1
    Write-Host "  Added note: quality team batch review" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}

# Timeline: note about warranty coverage
$fergNote2 = @{
    subject                              = "Warranty verification -- EK-FL-6003"
    notetext                             = "Confirmed: WaterSentry Plus filters carry a 1-year warranty on manufacturing defects. Batch WS-2026-0217 was shipped Feb 17, 2026 -- well within warranty. Ferguson has Strategic Support Tier 1 entitlement which includes priority RMA processing (48-hour turnaround). Standard RMA process: issue RMA number, ship replacements, customer returns defective units within 30 days. No charge for replacement or shipping on Tier 1 accounts."
    "objectid_incident@odata.bind"       = "/incidents($fergChatCaseId)"
}
try {
    Invoke-DataversePost -EntitySet "annotations" -Body $fergNote2
    Write-Host "  Added note: warranty verification" -ForegroundColor Green
} catch {
    Write-Warning "  Note failed: $($_.Exception.Message)"
}

# ============================================================
# Step 6: Save IDs and output summary
# ============================================================
Write-StepHeader "6" "Summary"

$chatIds = @{
    ScenarioA = @{
        Account     = @{ Name = "HD Supply"; Id = "$hdSupplyId"; Tier = 2 }
        Contacts    = @{
            JamesMorales = @{ Id = "$jamesId"; Role = "Commercial Accounts Manager"; Email = "james.morales@hdsupply.com"; Phone = "(770) 555-2301" }
            DerekLawson  = @{ Id = "$derekId"; Role = "Facilities Maintenance Supervisor"; Email = "derek.lawson@hdsupply.com"; Phone = "(770) 555-2305" }
        }
        ChatCaseId  = "$hdChatCaseId"
        ChatCase    = "HD Supply - AquaVantage sensor flush intermittent activation at Hilton Midtown"
        Topic       = "Phantom flush on sensor valves -- firmware issue -- warranty replacement"
    }
    ScenarioB = @{
        Account     = @{ Name = "Ferguson Enterprises"; Id = "$fergusonId"; Tier = 1 }
        Contacts    = @{
            RachelChen = @{ Id = "$rachelId"; Role = "Purchasing Director"; Email = "rachel.chen@ferguson.com"; Phone = "(757) 555-2002" }
        }
        ChatCaseId  = "$fergChatCaseId"
        ChatCase    = "Ferguson - WaterSentry Plus filter defect batch WS-2026-0217"
        Topic       = "Defective filter batch -- warranty RMA -- potential recall"
    }
}

$chatIds | ConvertTo-Json -Depth 5 | Set-Content "$scriptDir\..\data\chat-scenario-ids.json" -Encoding UTF8
Write-Host "  Chat scenario IDs saved to data/chat-scenario-ids.json" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " CHAT SCENARIO DATA SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Scenario A: HD Supply (Tier 2 Premium)" -ForegroundColor White
Write-Host "   Account: HD Supply (8.5B revenue, 11.5K employees)" -ForegroundColor DarkGray
Write-Host "   Chatter: Derek Lawson, Facilities Maintenance Supervisor" -ForegroundColor DarkGray
Write-Host "   Issue:   AquaVantage sensor phantom flushes at Hilton Midtown" -ForegroundColor DarkGray
Write-Host "   Case ID: $hdChatCaseId" -ForegroundColor DarkGray
Write-Host "   Bot KB:  'Troubleshooting Zurn AquaVantage and E-Z Flush Valve Issues'" -ForegroundColor DarkGray
Write-Host "   Escalation: Firmware issue not in KB -- needs warranty swap" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Scenario B: Ferguson Enterprises (Tier 1 Strategic)" -ForegroundColor White
Write-Host "   Account: Ferguson Enterprises (27.8B revenue, 36K employees)" -ForegroundColor DarkGray
Write-Host "   Chatter: Rachel Chen, Purchasing Director" -ForegroundColor DarkGray
Write-Host "   Issue:   Defective WaterSentry Plus filter batch WS-2026-0217" -ForegroundColor DarkGray
Write-Host "   Case ID: $fergChatCaseId" -ForegroundColor DarkGray
Write-Host "   Bot KB:  'Zurn Warranty Policy and RMA Process'" -ForegroundColor DarkGray
Write-Host "   Escalation: Needs actual RMA number + batch recall discussion" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Next: Configure Copilot Studio bot per demo-assets/copilot-studio-setup.md" -ForegroundColor Yellow
Write-Host ""
