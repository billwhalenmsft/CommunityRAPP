<#
.SYNOPSIS
    ABC Supply — Hero Cases, KB Articles, and Quick Responses Provisioning

.PARAMETER Action
    KBAndResponses | HeroCases | All

.EXAMPLE
    .\Provision-ABCSupplyHeroCases.ps1 -Action KBAndResponses
    .\Provision-ABCSupplyHeroCases.ps1 -Action All
#>

[CmdletBinding()]
param(
    [ValidateSet("KBAndResponses","HeroCases","All")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"

$OrgUrl  = "https://orgecbce8ef.crm.dynamics.com"
$ApiBase = "$OrgUrl/api/data/v9.2"
$DataDir = "$PSScriptRoot\..\..\data"

$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null)
if (-not $token) { Write-Error "Run 'az login' first."; exit 1 }

$headers = @{
    "Authorization"   = "Bearer $token"
    "OData-MaxVersion" = "4.0"
    "OData-Version"   = "4.0"
    "Content-Type"    = "application/json"
    "Prefer"          = "return=representation"
}

function Invoke-D365 {
    param([string]$Method, [string]$Url, [hashtable]$Body = $null)
    $params = @{ Method=$Method; Uri=$Url; Headers=$headers; TimeoutSec=30 }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    return Invoke-RestMethod @params
}

function Find-KBByTitle {
    param([string]$Title)
    $enc = [System.Web.HttpUtility]::UrlEncode($Title)
    $resp = Invoke-D365 -Method GET -Url "$ApiBase/knowledgearticles?`$filter=title eq '$enc'&`$select=knowledgearticleid,title"
    return $resp.value | Select-Object -First 1
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Cyan
Write-Host "  ABC Supply — Hero Cases + KB + Quick Responses" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

# ─────────────────────────────────────────────────────────────────
# KB ARTICLES + QUICK RESPONSES
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","KBAndResponses") {
    Write-Host "`n  ── Knowledge Base Articles ──" -ForegroundColor Yellow

    $articles = @(
        @{
            title       = "Window Seal Failure — Diagnosis, Warranty Process & Replacement Guide"
            description = "Step-by-step guide for diagnosing window seal failure, submitting warranty claims, and ordering replacement parts from Andersen and Pella."
            content     = "<h2>Window Seal Failure — Diagnosis &amp; Warranty Process</h2><h3>Symptoms</h3><ul><li>Visible water intrusion around window frame or sill</li><li>Condensation between glass panes (failed IG unit)</li><li>Visible cracking, gaps, or compression failure in perimeter seal</li><li>Drafts around closed window</li></ul><h3>Diagnostic Steps</h3><ol><li>Inspect exterior perimeter seal — look for cracking, separation, or compression failure</li><li>Apply light water spray around exterior frame while second person monitors interior for intrusion</li><li>Check installation date — if under 2 years, likely covered under manufacturer warranty</li><li>Take photos of damage location and extent before disturbing</li><li>Document serial number from manufacturer sticker (usually on corner of sash or frame)</li></ol><h3>Warranty Determination</h3><ul><li><strong>Under 2 years:</strong> Submit manufacturer warranty claim — order PART-SEAL-KIT from manufacturer, no charge to customer</li><li><strong>2-10 years:</strong> Review installation warranty — assess cause before determining coverage</li><li><strong>Over 10 years:</strong> Standard wear — customer pay, quote replacement</li></ul><h3>Parts Lead Time</h3><p>Standard seal kit: 10-14 business days. Custom sizing: 3-4 weeks. Set proactive SMS check-in at Day 7 for all orders over 5 business days.</p>"
        },
        @{
            title       = "Sliding Window Operator Mechanism — Replacement Procedure"
            description = "How to diagnose and replace the operator mechanism on Pella and Andersen sliding windows. Includes parts lookup and labor time estimates."
            content     = "<h2>Sliding Window Operator Replacement</h2><h3>Symptoms</h3><ul><li>Handle spins freely without engaging window</li><li>Window will not lock closed</li><li>Audible grinding — mechanism stripped</li></ul><h3>Parts</h3><ul><li>Pella standard operator: PART-OPR-MEC — typically in stock at Savage warehouse</li><li>Andersen custom: order from manufacturer, 5-7 business days</li><li>Always check warehouse stock before scheduling tech visit</li></ul><h3>Installation</h3><ol><li>Remove interior trim piece around handle</li><li>Inspect gear — look for stripped teeth or broken crank arm</li><li>Remove old operator (4 screws), clean mount area, install new</li><li>Test engagement before securing, test full open/close/lock cycle 3x</li><li>Apply weatherstrip sealant around trim</li></ol><h3>Labor Time</h3><p>Standard replacement: 45-75 minutes onsite. Add drive time. Rail/track adjustment if needed: +30-45 minutes.</p>"
        },
        @{
            title       = "Screen Replacement — Measurement, Order, and Installation Guide"
            description = "Standard process for measuring, ordering, and installing replacement screens for windows and doors."
            content     = "<h2>Screen Replacement Process</h2><h3>Measure</h3><ol><li>Measure frame opening W x H from inside edge to inside edge of window frame stop</li><li>Subtract 1/8 inch from both dimensions</li><li>Note frame color/finish for hardware match</li><li>Photograph existing screen and frame</li></ol><h3>Stock at Savage Warehouse</h3><ul><li>SCR-WIN-STD: Standard sizes 24x36, 24x48, 28x40, 28x48, 30x48, 36x60 — in stock</li><li>Custom sizes: 5-7 business day lead time</li></ul><h3>Install</h3><ol><li>Install from outside when possible for better seal</li><li>Seat bottom first, then top, then sides</li><li>Check tension — no bowing or sag</li><li>Post-install photo required</li></ol>"
        },
        @{
            title       = "Parts Order Status — Customer Communication & Self-Service Guide"
            description = "Customer communication guide for parts orders — what to communicate at each milestone, automated notifications, and self-service options."
            content     = "<h2>Parts Order Status Communication</h2><h3>Milestone Communications</h3><ul><li><strong>Parts Ordered:</strong> SMS + Email to homeowner and contractor — confirmation with ETA</li><li><strong>Day 7 (if not received):</strong> Proactive SMS to homeowner — parts still on track</li><li><strong>Parts Received:</strong> SMS to homeowner — scheduling call coming tomorrow</li><li><strong>Appointment Set:</strong> SMS to homeowner — date, time window, tech name</li><li><strong>Day Before:</strong> SMS reminder with confirm/reschedule option</li><li><strong>Tech En Route:</strong> SMS with ETA in minutes</li><li><strong>Work Complete:</strong> Email to contractor + homeowner + sales rep — completion report with photos</li></ul><h3>Goal</h3><p>Reduce inbound status calls by 40% through proactive outreach. Never let a customer call us for a status update — we tell them first.</p>"
        },
        @{
            title       = "Field Service Completion — Photo Documentation and Report Requirements"
            description = "What field techs must document at every service visit. Pre/post photo requirements, inspection checklist, and auto-generated completion report."
            content     = "<h2>Field Service Documentation Requirements</h2><h3>Required Every Visit</h3><ul><li>Pre-work photo — before touching anything</li><li>Post-work photo — finished result, same angle</li><li>Completed inspection checklist (mobile app)</li><li>Time log: arrive, work start, work end, depart</li><li>Parts used — scan or select from mobile</li></ul><h3>Inspection Checklist</h3><ol><li>Frame condition — no cracks, warping, damage</li><li>Glass condition — no scratches, cracks, seal failure</li><li>Seal/weatherstrip — intact and properly seated</li><li>Hardware operation — locks, hinges, operators</li><li>Installation plumb and level</li><li>Interior trim/finish — no damage from installation</li><li>Customer walkthrough completed — satisfaction confirmed</li></ol><h3>Completion Report</h3><p>D365 Field Service auto-generates and emails the completion report on case close. Includes: work order details, tech name, parts used, labor time, pre/post photos, inspection checklist. Auto-emailed to contractor, homeowner, and sales rep.</p>"
        }
    )

    $kbIds = @{}
    foreach ($art in $articles) {
        $existing = Find-KBByTitle -Title $art.title
        if ($existing) {
            Write-Host "  [SKIP] KB Article exists: $($art.title.Substring(0,[Math]::Min(55,$art.title.Length)))..." -ForegroundColor DarkGray
            $kbIds[$art.title] = $existing.knowledgearticleid
            continue
        }
        $body = @{ title = $art.title; description = $art.description.Substring(0,[Math]::Min(155,$art.description.Length)); content = $art.content }
        $resp = Invoke-D365 -Method POST -Url "$ApiBase/knowledgearticles" -Body $body
        Write-Host "  [CREATE] KB: $($art.title.Substring(0,[Math]::Min(55,$art.title.Length)))... → $($resp.knowledgearticleid)" -ForegroundColor Green
        $kbIds[$art.title] = $resp.knowledgearticleid
    }
    $kbIds | ConvertTo-Json | Set-Content "$DataDir\kb_ids.json"
    Write-Host "  KB IDs saved → $DataDir\kb_ids.json" -ForegroundColor DarkGray

    Write-Host "`n  ── Quick Responses (Canned Messages) ──" -ForegroundColor Yellow

    $quickResponses = @(
        @{ title = "ABC — Parts Ordered Confirmation"; message = "Hi {CustomerFirstName}, this is ABC Supply Savage. Your parts have been ordered and we expect them to arrive in approximately {LeadTimeDays} business days. We will contact you as soon as they arrive to schedule your repair. Work Order: {CaseNumber}. Questions? Call us at 952-894-0100." },
        @{ title = "ABC — Tech En Route SMS"; message = "{TechName} from ABC Supply is on the way! ETA approximately {ETAMinutes} minutes based on current traffic. If you need to reach us, call 952-894-0100. See you soon!" },
        @{ title = "ABC — Parts Arrived / Scheduling Call"; message = "Great news, {CustomerFirstName}! Your window/door parts have arrived at our warehouse. We will call you tomorrow to schedule your installation appointment. ABC Supply — 952-894-0100." },
        @{ title = "ABC — Appointment Reminder"; message = "Reminder: ABC Supply is scheduled to visit {AppointmentDate} between {TimeWindow}. Tech: {TechName}. Questions or need to reschedule? Call 952-894-0100 or reply to this message." },
        @{ title = "ABC — Work Complete / Report Sent"; message = "Hi {CustomerFirstName}, your service is complete! We have emailed a completion report with before and after photos to {ContractorEmail}. Thank you for choosing ABC Supply. Work Order: {CaseNumber}." },
        @{ title = "ABC — Warranty Claim Submitted"; message = "Your warranty claim (Work Order {CaseNumber}) has been submitted to the manufacturer. We will follow up once we have confirmation and a parts ETA. Questions? Contact Josh or Aaron at 952-894-0100." }
    )

    $qrIds = @{}
    foreach ($qr in $quickResponses) {
        $enc = [System.Web.HttpUtility]::UrlEncode($qr.title)
        $existing = (Invoke-D365 -Method GET -Url "$ApiBase/msdyn_cannedmessages?`$filter=msdyn_title eq '$enc'&`$select=msdyn_cannedmessageid").value | Select-Object -First 1
        if ($existing) {
            Write-Host "  [SKIP] Quick response exists: $($qr.title)" -ForegroundColor DarkGray
            continue
        }
        $body = @{ msdyn_title = $qr.title; msdyn_message = $qr.message }
        $resp = Invoke-D365 -Method POST -Url "$ApiBase/msdyn_cannedmessages" -Body $body
        Write-Host "  [CREATE] Quick Response: $($qr.title)" -ForegroundColor Green
        $qrIds[$qr.title] = $resp.msdyn_cannedmessageid
    }
}

# ─────────────────────────────────────────────────────────────────
# HERO CASES (rich timeline activities)
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","HeroCases") {
    Write-Host "`n  ── Hero Cases with Activity Timelines ──" -ForegroundColor Yellow

    # Load IDs from data directory
    $accountIds = @{}
    $loadedA = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedA) { $loadedA.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }

    $contactIds = @{}
    $loadedC = Get-Content "$DataDir\contact_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedC) { $loadedC.PSObject.Properties | ForEach-Object { $contactIds[$_.Name] = $_.Value } }

    $heroCases = @(
        @{
            title       = "Andersen 400 Casement — Seal Failure / Water Intrusion"
            account     = "Andersen Exteriors Savage"
            contact     = "Mike Bergstrom"
            origin      = 1
            priority    = 1
            statuscode  = 1
            description = "HERO CASE — Homeowner Sarah Kowalski (Prior Lake) reporting water intrusion around casement window frame. Installed 14 months ago by Andersen Exteriors. Seal failure confirmed as manufacturer defect. Warranty claim filed. Custom seal kit ordered — ETA 12-14 business days. All communications documented in case timeline."
            activities  = @(
                @{ type="phonecall"; subject="Initial Service Call — Water Intrusion Report"; description="Mike Bergstrom called in. Homeowner reporting water intrusion around casement frame. Case created, intake # provided. Sales rep Larry Sullivan CC'd on confirmation email."; direction=2 },
                @{ type="task"; subject="Tech Assessment — Seal Failure Confirmed"; description="Derek Olson completed onsite assessment. Drive time: 44 min. Onsite: 1.5 hrs. Seal failure confirmed as manufacturer defect. Serial: AND-CAS-2024-SAV-0042. Pre-work photos captured. Measurement taken for custom seal kit." },
                @{ type="task"; subject="Parts Order Submitted — Andersen Seal Kit"; description="PART-SEAL-KIT ordered from Andersen manufacturer portal. PO submitted in Agility. ETA: 12-14 business days. SMS sent to Sarah Kowalski confirming parts on order." },
                @{ type="task"; subject="Proactive Check-In SMS Sent (Day 7)"; description="Automated 7-day check-in SMS sent to Sarah Kowalski: 'Hi Sarah, your window parts are on track. We will contact you when they arrive to schedule installation.'" },
                @{ type="task"; subject="Parts Received — Scheduling Call Made"; description="Seal kit received at warehouse. Parts verified. SMS sent to Sarah Kowalski. Josh called and scheduled appointment: Tuesday March 31 at 9am. Appointment confirmation SMS sent." }
            )
        },
        @{
            title       = "Pella Impervia Slider — Operator Mechanism Failure"
            account     = "Pella Pro Contractors MN"
            contact     = "Tyler Schroeder"
            origin      = 2
            priority    = 2
            statuscode  = 1
            description = "HERO CASE — Pella sliding window operator mechanism stripped. Window unable to lock. Part PART-OPR-MEC confirmed in stock at Savage warehouse. Tech dispatched Thursday April 10 at 10am. Homeowner James Paulsen confirmed via SMS."
            activities  = @(
                @{ type="email"; subject="Service Request — Pella Slider Operator Failure"; description="Email from Tyler Schroeder at Pella Pro Contractors. Pella slider operator stripped, window won't lock. Auto-routed to coordinator queue. Auto-confirmation email sent with case # WO-2026-002." },
                @{ type="task"; subject="Parts Check — Operator Mechanism In Stock"; description="Aaron Dietz confirmed PART-OPR-MEC in stock at Savage warehouse. No parts order needed. Scheduled Derek Olson for Thursday April 10 at 10am. SMS sent to homeowner James Paulsen." },
                @{ type="task"; subject="Appointment Confirmed via SMS"; description="Homeowner James Paulsen replied 'C' to confirm appointment. Auto-reply sent with confirmation." }
            )
        }
    )

    $heroCaseIds = @{}
    foreach ($hc in $heroCases) {
        $existing = (Invoke-D365 -Method GET -Url "$ApiBase/incidents?`$filter=title eq '$([System.Web.HttpUtility]::UrlEncode($hc.title))'&`$select=incidentid,title" -ErrorAction SilentlyContinue).value | Select-Object -First 1
        if ($existing) {
            Write-Host "  [SKIP] Hero Case exists: $($hc.title.Substring(0,50))..." -ForegroundColor DarkGray
            $heroCaseIds[$hc.title] = $existing.incidentid
        } else {
            $body = @{
                title          = $hc.title
                description    = $hc.description
                caseorigincode = $hc.origin
                prioritycode   = $hc.priority
                statecode      = 0
                statuscode     = $hc.statuscode
            }
            $acctId = $accountIds[$hc.account]
            $ctcId  = $contactIds[$hc.contact]
            if ($acctId) { $body["customerid_account@odata.bind"] = "/accounts($acctId)" }
            if ($ctcId)  { $body["primarycontactid@odata.bind"]   = "/contacts($ctcId)" }
            $resp = Invoke-D365 -Method POST -Url "$ApiBase/incidents" -Body $body
            Write-Host "  [CREATE] Hero Case: $($hc.title.Substring(0,50))... → $($resp.incidentid)" -ForegroundColor Green
            $heroCaseIds[$hc.title] = $resp.incidentid
        }

        # Add activities to hero case
        $caseId = $heroCaseIds[$hc.title]
        if (-not $caseId) { continue }

        foreach ($act in $hc.activities) {
            try {
                if ($act.type -eq "task") {
                    $body = @{
                        subject     = $act.subject
                        description = $act.description
                        statecode   = 1
                        statuscode  = 5
                        "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                    }
                    $resp = Invoke-D365 -Method POST -Url "$ApiBase/tasks" -Body $body
                    Write-Host "    [ACT-TASK] $($act.subject.Substring(0,[Math]::Min(45,$act.subject.Length)))..." -ForegroundColor DarkGray
                } elseif ($act.type -eq "phonecall") {
                    $body = @{
                        subject     = $act.subject
                        description = $act.description
                        directioncode = ($act.direction -eq 2)
                        statecode   = 1
                        statuscode  = 2
                        "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                    }
                    $resp = Invoke-D365 -Method POST -Url "$ApiBase/phonecalls" -Body $body
                    Write-Host "    [ACT-PHONE] $($act.subject.Substring(0,[Math]::Min(45,$act.subject.Length)))..." -ForegroundColor DarkGray
                } elseif ($act.type -eq "email") {
                    $body = @{
                        subject     = $act.subject
                        description = $act.description
                        directioncode = $false
                        statecode   = 1
                        statuscode  = 6
                        "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                    }
                    $resp = Invoke-D365 -Method POST -Url "$ApiBase/emails" -Body $body
                    Write-Host "    [ACT-EMAIL] $($act.subject.Substring(0,[Math]::Min(45,$act.subject.Length)))..." -ForegroundColor DarkGray
                }
            } catch {
                Write-Warning "    Failed to create activity '$($act.subject)': $_"
            }
        }
    }

    $heroCaseIds | ConvertTo-Json | Set-Content "$DataDir\hero_case_ids.json"
    Write-Host "  Hero Case IDs saved → $DataDir\hero_case_ids.json" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  ABC Supply Hero Cases + KB + Quick Responses Complete" -ForegroundColor Green
Write-Host "`n  IMPORTANT: Manually publish KB articles in D365 UI:" -ForegroundColor Yellow
Write-Host "  Customer Service Hub → Knowledge Articles → select each → Publish" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green
