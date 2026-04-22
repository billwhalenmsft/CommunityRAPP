<#
.SYNOPSIS
    Navico Marine Electronics — Hero Cases, KB Articles & Agent Productivity Data
.DESCRIPTION
    Provisions rich demo data from JSON configuration:
    - Hero Cases with full activity timelines (calls, emails, notes)
    - Knowledge Articles (for Copilot Agent Assist to surface)
    - Quick Responses (pre-built replies for demo agents)

.PARAMETER Action
    What to provision: All, HeroCases, KnowledgeArticles, QuickResponses, Cleanup

.EXAMPLE
    .\Provision-NavicoHeroCases.ps1 -Action All
    .\Provision-NavicoHeroCases.ps1 -Action HeroCases
    .\Provision-NavicoHeroCases.ps1 -Action KnowledgeArticles
#>

[CmdletBinding()]
param(
    [ValidateSet("All", "HeroCases", "KnowledgeArticles", "QuickResponses", "Cleanup")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) { Import-Module $helperPath -Force } else { throw "DataverseHelper.psm1 not found: $helperPath" }

$heroCasesPath  = Join-Path $scriptDir "data\hero-cases.json"
$kbArticlesPath = Join-Path $scriptDir "data\knowledge-articles.json"
$demoIdsPath    = Join-Path $scriptDir "data\navico-demo-ids.json"
$envConfigPath  = Join-Path $scriptDir "config\environment.json"

$heroCases  = if (Test-Path $heroCasesPath)  { Get-Content $heroCasesPath  | ConvertFrom-Json } else { $null }
$kbArticles = if (Test-Path $kbArticlesPath) { Get-Content $kbArticlesPath | ConvertFrom-Json } else { $null }
$demoIds    = if (Test-Path $demoIdsPath)    { Get-Content $demoIdsPath    | ConvertFrom-Json } else { $null }
$envConfig  = if (Test-Path $envConfigPath)  { Get-Content $envConfigPath  | ConvertFrom-Json } else { $null }

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Navico — Hero Cases & Knowledge Articles" -ForegroundColor Cyan
Write-Host "  Environment : $($envConfig.environment.name)" -ForegroundColor DarkGray
Write-Host "  URL         : $($envConfig.environment.url)" -ForegroundColor DarkGray
Write-Host "  Action      : $Action" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Connect-Dataverse

$createdRecords = @{
    heroCases        = @()
    activities       = @()
    knowledgeArticles = @()
    quickResponses   = @()
}

# ============================================================
# HELPER: Find Account
# ============================================================
function Get-AccountId {
    param([string]$AccountName)
    if ($demoIds -and $demoIds.accounts) {
        $match = $demoIds.accounts | Where-Object { $_.name -eq $AccountName }
        if ($match) { return $match.id }
    }
    $esc = $AccountName -replace "'", "''"
    $r = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$esc'" -Select "accountid" -Top 1
    if ($r -and $r.Count -gt 0) { return $r[0].accountid }
    return $null
}

# ============================================================
# HELPER: Find Contact
# ============================================================
function Get-ContactId {
    param([string]$ContactName)
    if ($demoIds -and $demoIds.contacts) {
        $match = $demoIds.contacts | Where-Object { $_.name -like "*$ContactName*" }
        if ($match) { return $match.id }
    }
    $parts = $ContactName -split " "
    $fn = $parts[0]; $ln = $parts[-1]
    $r = Invoke-DataverseGet -EntitySet "contacts" -Filter "firstname eq '$fn' and lastname eq '$ln'" -Select "contactid" -Top 1
    if ($r -and $r.Count -gt 0) { return $r[0].contactid }
    return $null
}

# ============================================================
# HERO CASES
# ============================================================
function Provision-HeroCases {
    Write-Host "`n>>> Provisioning Hero Cases..." -ForegroundColor Green

    if (-not $heroCases) { Write-Warning "hero-cases.json not found — skipping."; return }

    $priorityMap = @{ "High" = 2; "Normal" = 3; "Low" = 4; "Critical" = 1 }
    $originMap   = @{ 1 = 1; 2 = 2; 4 = 4 }

    foreach ($case in $heroCases.heroCases) {
        if ($case.caseType -eq "Dashboard Demo") {
            Write-Host "  Skipping supervisor dashboard placeholder: $($case.title)" -ForegroundColor DarkGray
            continue
        }

        Write-Host "  Creating hero case: $($case.title)" -ForegroundColor Gray

        $accountId = if ($case.account) { Get-AccountId -AccountName $case.account } else { $null }
        $contactId = if ($case.contact) { Get-ContactId -ContactName $case.contact } else { $null }

        $body = @{
            title          = $case.title
            description    = $case.description
            prioritycode   = $priorityMap[$case.priority]
            caseorigincode = if ($case.origin) { $case.origin } else { 3 }
        }
        if ($accountId) { $body["customerid_account@odata.bind"] = "/accounts($accountId)" }
        if ($contactId) { $body["primarycontactid@odata.bind"]   = "/contacts($contactId)" }

        # Stamp serial number from hero-cases.json so Equipment screen can match
        if ($case.serialNumber) {
            $body["productserialnumber"] = $case.serialNumber
        }

        # Link to product record if we can find it by brand + model in title
        if ($case.brand) {
            $prodFilter = "name eq '$($case.brand)'" 
            $prodMatch = Invoke-DataverseGet -EntitySet "products" -Filter "contains(name,'$($case.brand)')" -Select "productid" -Top 1
            if ($prodMatch -and $prodMatch.Count -gt 0) {
                $body["productid@odata.bind"] = "/products($($prodMatch[0].productid))"
            }
        }

        $esc    = $case.title -replace "'", "''"
        $caseId = Find-OrCreate-Record -EntitySet "incidents" -Filter "title eq '$esc'" -IdField "incidentid" -Body $body -DisplayName $case.title

        $script:createdRecords.heroCases += @{ id = $caseId; title = $case.title; scenarioRole = $case.scenarioRole }

        # Create activities
        if ($case.activities) {
            $baseTime = (Get-Date).ToUniversalTime()
            foreach ($activity in $case.activities) {
                $actTime = $baseTime.AddHours($activity.createdRelativeHours)
                $actTimeStr = $actTime.ToString("yyyy-MM-ddTHH:mm:ssZ")

                switch ($activity.type) {
                    "note" {
                        $noteBody = @{
                            subject     = $activity.subject
                            notetext    = $activity.description
                            "objectid_incident@odata.bind" = "/incidents($caseId)"
                        }
                        try {
                            $noteId = Find-OrCreate-Record -EntitySet "annotations" `
                                -Filter "subject eq '$($activity.subject -replace "'","''")' and _objectid_value eq '$caseId'" `
                                -IdField "annotationid" -Body $noteBody -DisplayName $activity.subject
                            $script:createdRecords.activities += @{ type = "note"; id = $noteId }
                            Write-Host "    Note: $($activity.subject)" -ForegroundColor DarkGray
                        } catch { Write-Warning "    Note creation skipped: $($_.Exception.Message)" }
                    }
                    "email" {
                        try {
                            $isInbound = $activity.direction -eq "inbound"
                            $emailBody = @{
                                subject        = $activity.subject
                                description    = $activity.description
                                directioncode  = -not $isInbound
                                actualend      = $actTimeStr
                                "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                            }
                            $checkFilter = "subject eq '$($activity.subject -replace "'","''")' and _regardingobjectid_value eq '$caseId'"
                            $emailId = Find-OrCreate-Record -EntitySet "emails" -Filter $checkFilter `
                                -IdField "activityid" -Body $emailBody -DisplayName $activity.subject
                            $script:createdRecords.activities += @{ type = "email"; id = $emailId }
                            Write-Host "    Email: $($activity.subject)" -ForegroundColor DarkGray
                        } catch { Write-Warning "    Email creation skipped: $($_.Exception.Message)" }
                    }
                    "phonecall" {
                        try {
                            $phoneBody = @{
                                subject       = $activity.subject
                                description   = $activity.description
                                directioncode = if ($activity.direction -eq "inbound") { $false } else { $true }
                                actualend     = $actTimeStr
                                "regardingobjectid_incident@odata.bind" = "/incidents($caseId)"
                            }
                            $checkFilter = "subject eq '$($activity.subject -replace "'","''")' and _regardingobjectid_value eq '$caseId'"
                            $phoneId = Find-OrCreate-Record -EntitySet "phonecalls" -Filter $checkFilter `
                                -IdField "activityid" -Body $phoneBody -DisplayName $activity.subject
                            $script:createdRecords.activities += @{ type = "phonecall"; id = $phoneId }
                            Write-Host "    Phone call: $($activity.subject)" -ForegroundColor DarkGray
                        } catch { Write-Warning "    Phone call creation skipped: $($_.Exception.Message)" }
                    }
                }
            }
        }
    }

    Write-Host "  Hero cases complete: $($script:createdRecords.heroCases.Count) created" -ForegroundColor Green
}

# ============================================================
# KNOWLEDGE ARTICLES
# ============================================================
function Provision-KnowledgeArticles {
    Write-Host "`n>>> Provisioning Knowledge Articles..." -ForegroundColor Green

    if (-not $kbArticles) { Write-Warning "knowledge-articles.json not found — skipping."; return }

    foreach ($article in $kbArticles.articles) {
        Write-Host "  Creating KB article: $($article.externalNumber) — $($article.title)" -ForegroundColor Gray

        # Check if KB article already exists by title (articlepublicnumber is read-only/computed, not filterable)
        $existing = Invoke-DataverseGet -EntitySet "knowledgearticles" `
            -Filter "title eq '$($article.title)'" `
            -Select "knowledgearticleid,title" -Top 1

        if ($existing -and $existing.Count -gt 0) {
            Write-Host "    Already exists — skipping." -ForegroundColor DarkGray
            $script:createdRecords.knowledgeArticles += @{ id = $existing[0].knowledgearticleid; title = $article.title }
            continue
        }

        $desc = "Brand: $($article.brand) | $($article.product)"
        if ($desc.Length -gt 155) { $desc = $desc.Substring(0, 152) + "..." }
        $body = @{
            title       = $article.title
            content     = $article.content
            description = $desc
        }

        try {
            $r = Invoke-DataversePost -EntitySet "knowledgearticles" -Body $body
            if ($r) {
                Write-Host "    Created: $($article.externalNumber)" -ForegroundColor DarkGray
                $script:createdRecords.knowledgeArticles += @{ id = $r; title = $article.title }
            }
        } catch {
            Write-Warning "    KB article creation issue: $($_.Exception.Message). May need manual publish in D365."
        }
    }

    Write-Host "  Knowledge articles complete: $($script:createdRecords.knowledgeArticles.Count) processed" -ForegroundColor Green
}

# ============================================================
# QUICK RESPONSES (for demo agent productivity)
# ============================================================
function Provision-QuickResponses {
    Write-Host "`n>>> Provisioning Quick Responses..." -ForegroundColor Green

    $quickResponses = @(
        @{
            title   = "Navico — Platinum Expert Acknowledgment (Chat)"
            message = "Hi {CustomerFirstName}, thank you for reaching out to Navico Support. I can see you're a valued Platinum Expert partner and I'm treating this as a priority. I'm reviewing your case right now — you should have a response within 2 hours."
        },
        @{
            title   = "Navico — Warranty Confirmed, Return Instructions (Email)"
            message = "Dear {CustomerName},`n`nThank you for contacting Navico Support. I've verified your product (Serial: {SerialNumber}) is within the 3-year limited warranty (expires {WarrantyExpiry}).`n`nTo proceed with your warranty claim:`n1. A prepaid return shipping label will be emailed to you within 1 business hour.`n2. Please pack the unit securely and drop off at any UPS/FedEx location.`n3. You'll receive email tracking updates as your unit is received, diagnosed, and returned.`n`nTarget turnaround: 10 business days from receipt.`n`nDon't hesitate to reply to this case if you have any questions.`n`nBest regards,`nNavico Customer Support"
        },
        @{
            title   = "Navico — Firmware Recovery Steps (Simrad NSX)"
            message = "Hi {CustomerName},`n`nThank you for reporting this issue with your Simrad NSX chartplotter. Based on your description, this matches a known recovery procedure for firmware v3.8.x.`n`nPlease try these steps:`n1. Hold MENU button for 10 seconds (soft reset).`n2. If still unresponsive, power off completely and disconnect from power.`n3. Hold POWER + MENU simultaneously during power-on to enter Recovery Mode.`n4. Select Factory Display Calibration and allow to complete (~3 minutes).`n`nIf the issue persists after these steps, please reply to this case and we'll arrange an RMA Exchange — your unit is fully covered under warranty.`n`nBest regards,`nNavico Technical Support"
        },
        @{
            title   = "Navico — RMA Exchange Approved, Next Steps"
            message = "Hi {CustomerName},`n`nYour RMA Exchange request has been approved by our Technical Specialist team.`n`nHere's what happens next:`n- A replacement unit will ship within 2 business days from our Tulsa, OK distribution center.`n- You'll receive tracking information by email once shipped.`n- Return of the defective unit: a prepaid label will be included in your replacement shipment.`n`nRMA Reference: {CaseNumber}`n`nThank you for your patience. We appreciate your partnership.`n`nNavico Customer Support"
        },
        @{
            title   = "Navico — Escalation to Technical Specialist"
            message = "Hi {CustomerName},`n`nThank you for the additional details. I'm escalating your case to one of our brand specialists who will be able to provide the most accurate technical guidance for your {Brand} equipment.`n`nYou can expect to hear from our team within {SLATarget}. Your case reference is {CaseNumber}.`n`nBest regards,`nNavico Customer Support"
        }
    )

    foreach ($qr in $quickResponses) {
        Write-Host "  Creating quick response: $($qr.title)" -ForegroundColor Gray
        try {
            $id = Find-OrCreate-Record `
                -EntitySet "msdyn_cannedmessages" `
                -Filter "msdyn_title eq '$($qr.title -replace "'","''")'" `
                -IdField "msdyn_cannedmessageid" `
                -Body @{ msdyn_title = $qr.title; msdyn_message = $qr.message } `
                -DisplayName $qr.title
            $script:createdRecords.quickResponses += @{ id = $id; title = $qr.title }
        } catch {
            Write-Warning "    Quick response skipped (may need Omnichannel provisioned): $($_.Exception.Message)"
        }
    }

    Write-Host "  Quick responses complete: $($script:createdRecords.quickResponses.Count) processed" -ForegroundColor Green
}

# ============================================================
# CLEANUP
# ============================================================
function Invoke-Cleanup {
    Write-Host "`n>>> Cleanup: Removing Navico hero cases & KB articles..." -ForegroundColor Red
    $confirm = Read-Host "Type 'DELETE' to confirm"
    if ($confirm -ne "DELETE") { Write-Host "Cancelled."; return }

    if ($heroCases) {
        foreach ($case in $heroCases.heroCases) {
            if ($case.caseType -eq "Dashboard Demo") { continue }
            $esc = $case.title -replace "'", "''"
            $r = Invoke-DataverseGet -EntitySet "incidents" -Filter "title eq '$esc'" -Select "incidentid" -Top 1
            if ($r -and $r.Count -gt 0) {
                Invoke-DataverseDelete -EntitySet "incidents" -Id $r[0].incidentid
                Write-Host "  Deleted: $($case.title)" -ForegroundColor DarkRed
            }
        }
    }
    if ($kbArticles) {
        foreach ($article in $kbArticles.articles) {
            $r = Invoke-DataverseGet -EntitySet "knowledgearticles" -Filter "title eq '$($article.title)'" -Select "knowledgearticleid" -Top 1
            if ($r -and $r.Count -gt 0) {
                Invoke-DataverseDelete -EntitySet "knowledgearticles" -Id $r[0].knowledgearticleid
                Write-Host "  Deleted KB: $($article.title)" -ForegroundColor DarkRed
            }
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
}

# ============================================================
# MAIN
# ============================================================
switch ($Action) {
    "All"               { Provision-HeroCases; Provision-KnowledgeArticles; Provision-QuickResponses }
    "HeroCases"         { Provision-HeroCases }
    "KnowledgeArticles" { Provision-KnowledgeArticles }
    "QuickResponses"    { Provision-QuickResponses }
    "Cleanup"           { Invoke-Cleanup }
}

# Export IDs
$exportPath = Join-Path $scriptDir "data\navico-hero-ids.json"
$createdRecords | ConvertTo-Json -Depth 5 | Set-Content $exportPath -Force

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "  Navico Hero Cases & KB Provisioning Complete!" -ForegroundColor Green
Write-Host "  Hero Cases        : $($createdRecords.heroCases.Count)" -ForegroundColor Gray
Write-Host "  Knowledge Articles: $($createdRecords.knowledgeArticles.Count)" -ForegroundColor Gray
Write-Host "  Quick Responses   : $($createdRecords.quickResponses.Count)" -ForegroundColor Gray
Write-Host "  IDs saved         : $exportPath" -ForegroundColor DarkGray
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""
Write-Host "  Next: Validate in D365 — check accounts, cases, KB articles, and omnichannel config." -ForegroundColor Cyan
Write-Host ""
