<#
.SYNOPSIS
    Otis EMEA CCaaS Demo - Hero Cases & Extended Data Provisioning
.DESCRIPTION
    Creates rich demo data from JSON configuration files:
    - Hero Cases with full timeline activities (calls, emails, notes)
    - Knowledge Articles for Copilot to surface
    - Agent Scripts for Service Toolkit
    - Macros for productivity automation
    - Quick Responses for common replies

.PARAMETER Action
    What to provision: All, HeroCases, KnowledgeArticles, AgentScripts, Macros, Cleanup

.EXAMPLE
    .\Provision-OtisHeroCases.ps1 -Action All
    .\Provision-OtisHeroCases.ps1 -Action HeroCases
    .\Provision-OtisHeroCases.ps1 -Action KnowledgeArticles
#>

[CmdletBinding()]
param(
    [ValidateSet("All", "HeroCases", "KnowledgeArticles", "AgentScripts", "Macros", "QuickResponses", "Cleanup")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

# Import Dataverse helper
$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) {
    Import-Module $helperPath -Force
} else {
    throw "DataverseHelper.psm1 not found at: $helperPath"
}

# Load configuration files
$heroCasesPath = Join-Path $scriptDir "data\hero-cases.json"
$kbArticlesPath = Join-Path $scriptDir "data\knowledge-articles.json"
$toolkitPath = Join-Path $scriptDir "config\productivity-toolkit.json"
$slaPath = Join-Path $scriptDir "config\sla-definitions.json"
$envConfigPath = Join-Path $scriptDir "config\environment.json"
$demoIdsPath = Join-Path $scriptDir "data\otis-demo-ids.json"

# Load files if they exist
$heroCases = if (Test-Path $heroCasesPath) { Get-Content $heroCasesPath | ConvertFrom-Json } else { $null }
$kbArticles = if (Test-Path $kbArticlesPath) { Get-Content $kbArticlesPath | ConvertFrom-Json } else { $null }
$toolkit = if (Test-Path $toolkitPath) { Get-Content $toolkitPath | ConvertFrom-Json } else { $null }
$envConfig = if (Test-Path $envConfigPath) { Get-Content $envConfigPath | ConvertFrom-Json } else { $null }
$demoIds = if (Test-Path $demoIdsPath) { Get-Content $demoIdsPath | ConvertFrom-Json } else { $null }

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Otis EMEA CCaaS Demo - Hero Cases & Extended Data" -ForegroundColor Cyan
Write-Host "  Environment: $($envConfig.environment.name)" -ForegroundColor DarkGray
Write-Host "  URL: $($envConfig.environment.url)" -ForegroundColor DarkGray
Write-Host "  Action: $Action" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Connect to Dataverse
Write-Host "Connecting to Dataverse..." -ForegroundColor Yellow
Connect-Dataverse

# Track created records
$createdRecords = @{
    heroCases = @()
    activities = @()
    knowledgeArticles = @()
    agentScripts = @()
    macros = @()
    quickResponses = @()
}

# ============================================================
# HELPER: Find Account by Name
# ============================================================
function Get-AccountId {
    param([string]$AccountName)
    
    # First check demoIds
    if ($demoIds -and $demoIds.accounts) {
        $match = $demoIds.accounts | Where-Object { $_.name -eq $AccountName }
        if ($match) { return $match.id }
    }
    
    # Otherwise query D365
    $escapedName = $AccountName -replace "'", "''"
    $result = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$escapedName'" -Select "accountid" -Top 1
    if ($result -and $result.Count -gt 0) {
        return $result[0].accountid
    }
    return $null
}

# ============================================================
# HELPER: Find Contact by Name
# ============================================================
function Get-ContactId {
    param([string]$FirstName, [string]$LastName)
    
    # First check demoIds
    if ($demoIds -and $demoIds.contacts) {
        $match = $demoIds.contacts | Where-Object { $_.name -like "*$FirstName*$LastName*" }
        if ($match) { return $match.id }
    }
    
    # Otherwise query D365
    $result = Invoke-DataverseGet -EntitySet "contacts" `
        -Filter "firstname eq '$FirstName' and lastname eq '$LastName'" `
        -Select "contactid" -Top 1
    if ($result -and $result.Count -gt 0) {
        return $result[0].contactid
    }
    return $null
}

# ============================================================
# HERO CASES - Rich Demo Cases with Full Context
# ============================================================
function Provision-HeroCases {
    if (-not $heroCases) {
        Write-Host "Hero cases file not found. Skipping." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n>>> Provisioning Hero Cases..." -ForegroundColor Green
    
    # Map priority names to D365 priority codes
    $priorityMap = @{
        "Critical" = 1
        "High" = 2
        "Normal" = 3
        "Low" = 4
    }
    
    # Map case origin
    $originMap = @{
        "Phone" = 1
        "Email" = 2
        "Web" = 3
        "Chat" = 2483 # May vary by environment
        "Portal" = 2483
    }
    
    foreach ($case in $heroCases.heroCases) {
        Write-Host "`n  Creating Hero Case: $($case.title)" -ForegroundColor Cyan
        
        # Find account
        $accountId = Get-AccountId -AccountName $case.account.name
        if (-not $accountId) {
            Write-Host "    Warning: Account '$($case.account.name)' not found" -ForegroundColor DarkYellow
        }
        
        # Find contact
        $contactId = Get-ContactId -FirstName $case.contact.firstName -LastName $case.contact.lastName
        if (-not $contactId) {
            Write-Host "    Warning: Contact '$($case.contact.firstName) $($case.contact.lastName)' not found" -ForegroundColor DarkYellow
        }
        
        # Build case data
        $caseDescription = @"
$($case.description)

--- Account Context ---
Tier: $($case.account.tier)
Contract: $($case.account.contractType)
Total Units: $($case.account.totalUnits)
SLA Response: $($case.account.slaResponseTime)
Annual Contract Value: $($case.account.annualContractValue)

--- Equipment ---
Unit: $($case.equipment.unitNumber)
Serial: $($case.equipment.serialNumber)
Model: $($case.equipment.model)
Location: $($case.equipment.location)
Floors: $($case.equipment.floors)
Last Maintenance: $($case.equipment.lastMaintenanceDate)

--- Contact Preferences ---
Preferred Channel: $($case.contact.preferredChannel)
Direct Phone: $($case.contact.phone)
Email: $($case.contact.email)

[HERO CASE: $($case.id) - $($case.demoNotes)]
"@
        
        $caseData = @{
            title = $case.title
            description = $caseDescription
            prioritycode = $priorityMap[$case.priority]
            caseorigincode = if ($originMap[$case.origin]) { $originMap[$case.origin] } else { 1 }
        }
        
        if ($accountId) {
            $caseData["customerid_account@odata.bind"] = "/accounts($accountId)"
        }
        if ($contactId) {
            $caseData["primarycontactid@odata.bind"] = "/contacts($contactId)"
        }
        
        # Create case
        $escapedTitle = $case.title -replace "'", "''"
        $caseId = Find-OrCreate-Record `
            -EntitySet "incidents" `
            -Filter "title eq '$escapedTitle'" `
            -IdField "incidentid" `
            -Body $caseData `
            -DisplayName $case.title
        
        $script:createdRecords.heroCases += @{
            id = $caseId
            heroId = $case.id
            title = $case.title
            account = $case.account.name
        }
        
        Write-Host "    Case created: $caseId" -ForegroundColor Gray
        
        # Create timeline activities
        if ($case.timeline -and $case.timeline.Count -gt 0) {
            Write-Host "    Creating timeline activities..." -ForegroundColor Gray
            Provision-CaseActivities -CaseId $caseId -Timeline $case.timeline -AccountId $accountId -ContactId $contactId
        }
    }
    
    Write-Host "`n  Hero Cases complete: $($heroCases.heroCases.Count) processed" -ForegroundColor Green
}

# ============================================================
# CASE ACTIVITIES - Phone Calls, Emails, Notes
# ============================================================
function Provision-CaseActivities {
    param(
        [string]$CaseId,
        [array]$Timeline,
        [string]$AccountId,
        [string]$ContactId
    )
    
    foreach ($activity in $Timeline) {
        switch ($activity.type) {
            "Phone Call" {
                $phoneData = @{
                    subject = $activity.subject
                    description = $activity.notes
                    directioncode = if ($activity.direction -eq "Inbound") { $false } else { $true }
                    actualdurationminutes = if ($activity.duration) {
                        # Parse duration like "00:02:45" to minutes
                        $parts = $activity.duration -split ":"
                        [int]$parts[0] * 60 + [int]$parts[1]
                    } else { 5 }
                    "regardingobjectid_incident@odata.bind" = "/incidents($CaseId)"
                }
                
                $phoneId = Invoke-DataversePost -EntitySet "phonecalls" -Body $phoneData
                Write-Host "      + Phone call: $($activity.subject)" -ForegroundColor DarkGray
                
                $script:createdRecords.activities += @{
                    type = "phonecall"
                    id = $phoneId
                    caseId = $CaseId
                }
            }
            "Email" {
                $emailData = @{
                    subject = $activity.subject
                    description = if ($activity.body) { $activity.body } else { $activity.notes }
                    directioncode = if ($activity.direction -eq "Inbound") { $false } else { $true }
                    "regardingobjectid_incident@odata.bind" = "/incidents($CaseId)"
                }
                
                $emailId = Invoke-DataversePost -EntitySet "emails" -Body $emailData
                Write-Host "      + Email: $($activity.subject)" -ForegroundColor DarkGray
                
                $script:createdRecords.activities += @{
                    type = "email"
                    id = $emailId
                    caseId = $CaseId
                }
            }
            "Note" {
                $noteData = @{
                    subject = $activity.subject
                    notetext = $activity.notes
                    "objectid_incident@odata.bind" = "/incidents($CaseId)"
                }
                
                $noteId = Invoke-DataversePost -EntitySet "annotations" -Body $noteData
                Write-Host "      + Note: $($activity.subject)" -ForegroundColor DarkGray
                
                $script:createdRecords.activities += @{
                    type = "annotation"
                    id = $noteId
                    caseId = $CaseId
                }
            }
            "Chat" {
                # Create chat as a note with transcript
                $transcript = ""
                if ($activity.transcript) {
                    foreach ($msg in $activity.transcript) {
                        $transcript += "[$($msg.role)]: $($msg.message)`n"
                    }
                }
                
                $noteData = @{
                    subject = "Chat Session - $($activity.timestamp)"
                    notetext = "Chat Duration: $($activity.duration)`n`n--- Transcript ---`n$transcript"
                    "objectid_incident@odata.bind" = "/incidents($CaseId)"
                }
                
                $noteId = Invoke-DataversePost -EntitySet "annotations" -Body $noteData
                Write-Host "      + Chat transcript saved as note" -ForegroundColor DarkGray
                
                $script:createdRecords.activities += @{
                    type = "annotation"
                    id = $noteId
                    caseId = $CaseId
                }
            }
        }
    }
}

# ============================================================
# KNOWLEDGE ARTICLES
# ============================================================
function Provision-KnowledgeArticles {
    if (-not $kbArticles) {
        Write-Host "Knowledge articles file not found. Skipping." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n>>> Provisioning Knowledge Articles..." -ForegroundColor Green
    Write-Host "  Note: KB articles require proper workflow for publishing" -ForegroundColor DarkYellow
    
    foreach ($article in $kbArticles.knowledgeArticles) {
        Write-Host "  Creating: $($article.title)" -ForegroundColor Gray
        
        # Build article content from sections
        $content = "<h2>$($article.summary)</h2>`n"
        foreach ($section in $article.content.sections) {
            $sectionContent = $section.content -replace "`n", "<br/>"
            $content += "<h3>$($section.title)</h3>`n<p>$sectionContent</p>`n"
        }
        
        $articleData = @{
            title = $article.title
            content = $content
            description = $article.summary
            keywords = ($article.keywords -join ", ")
            articlepublicnumber = $article.articleNumber
        }
        
        try {
            $escapedTitle = $article.title -replace "'", "''"
            $articleId = Find-OrCreate-Record `
                -EntitySet "knowledgearticles" `
                -Filter "title eq '$escapedTitle'" `
                -IdField "knowledgearticleid" `
                -Body $articleData `
                -DisplayName $article.title
            
            $script:createdRecords.knowledgeArticles += @{
                id = $articleId
                articleNumber = $article.articleNumber
                title = $article.title
            }
            
            Write-Host "    Created: $($article.articleNumber)" -ForegroundColor DarkGray
        }
        catch {
            Write-Host "    Warning: Could not create KB article (may need different permissions)" -ForegroundColor DarkYellow
            Write-Host "    Error: $_" -ForegroundColor DarkRed
        }
    }
    
    Write-Host "`n  Knowledge Articles complete" -ForegroundColor Green
    Write-Host "  Note: Publish articles in KB Management to make them available to Copilot" -ForegroundColor Yellow
}

# ============================================================
# AGENT SCRIPTS
# ============================================================
function Provision-AgentScripts {
    if (-not $toolkit) {
        Write-Host "Productivity toolkit file not found. Skipping." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n>>> Provisioning Agent Scripts..." -ForegroundColor Green
    Write-Host "  Note: Agent Scripts require Customer Service workspace app profile setup" -ForegroundColor DarkYellow
    
    foreach ($script in $toolkit.agentScripts) {
        Write-Host "  Script: $($script.name)" -ForegroundColor Gray
        
        # Build steps description
        $stepsText = ""
        foreach ($step in $script.steps) {
            $stepsText += "Step $($step.order): $($step.name)`n"
            $stepsText += "  Type: $($step.type)`n"
            if ($step.instruction) { $stepsText += "  Instruction: $($step.instruction)`n" }
            if ($step.textTemplate) { $stepsText += "  Template: $($step.textTemplate)`n" }
            $stepsText += "`n"
        }
        
        # Agent scripts are complex - log for manual creation
        Write-Host "    Trigger: $($script.trigger)" -ForegroundColor DarkGray
        Write-Host "    Steps: $($script.steps.Count)" -ForegroundColor DarkGray
        
        $script:createdRecords.agentScripts += @{
            id = $script.id
            name = $script.name
            trigger = $script.trigger
            stepsCount = $script.steps.Count
            status = "Pending manual creation"
        }
    }
    
    Write-Host "`n  Agent Scripts logged for manual setup" -ForegroundColor Yellow
    Write-Host "  Setup path: Customer Service admin center > Agent experience > Productivity > Agent scripts" -ForegroundColor DarkYellow
}

# ============================================================
# MACROS
# ============================================================
function Provision-Macros {
    if (-not $toolkit) {
        Write-Host "Productivity toolkit file not found. Skipping." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n>>> Provisioning Macros..." -ForegroundColor Green
    Write-Host "  Note: Macros require Customer Service workspace app profile setup" -ForegroundColor DarkYellow
    
    foreach ($macro in $toolkit.macros) {
        Write-Host "  Macro: $($macro.name)" -ForegroundColor Gray
        Write-Host "    Description: $($macro.description)" -ForegroundColor DarkGray
        Write-Host "    Actions: $($macro.actions.Count)" -ForegroundColor DarkGray
        
        $script:createdRecords.macros += @{
            id = $macro.id
            name = $macro.name
            description = $macro.description
            actionsCount = $macro.actions.Count
            icon = $macro.icon
            status = "Pending manual creation"
        }
    }
    
    Write-Host "`n  Macros logged for manual setup" -ForegroundColor Yellow
    Write-Host "  Setup path: Customer Service admin center > Agent experience > Productivity > Macros" -ForegroundColor DarkYellow
}

# ============================================================
# QUICK RESPONSES
# ============================================================
function Provision-QuickResponses {
    if (-not $toolkit) {
        Write-Host "Productivity toolkit file not found. Skipping." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n>>> Provisioning Quick Responses..." -ForegroundColor Green
    
    foreach ($qr in $toolkit.quickResponses) {
        Write-Host "  Quick Response: $($qr.name)" -ForegroundColor Gray
        
        # Quick responses can be created in D365
        $qrData = @{
            name = $qr.name
            message = $qr.message
        }
        
        if ($qr.tags) {
            $qrData.description = "Tags: $($qr.tags -join ', ')"
        }
        
        try {
            $escapedName = $qr.name -replace "'", "''"
            $qrId = Find-OrCreate-Record `
                -EntitySet "msdyn_cannedmessages" `
                -Filter "msdyn_title eq '$escapedName'" `
                -IdField "msdyn_cannedmessageid" `
                -Body @{
                    msdyn_title = $qr.name
                    msdyn_message = $qr.message
                } `
                -DisplayName $qr.name
            
            $script:createdRecords.quickResponses += @{
                id = $qrId
                name = $qr.name
                status = "Created"
            }
            
            Write-Host "    Created" -ForegroundColor DarkGray
        }
        catch {
            Write-Host "    Could not create (may need Omnichannel)" -ForegroundColor DarkYellow
            $script:createdRecords.quickResponses += @{
                name = $qr.name
                status = "Pending manual creation"
            }
        }
    }
    
    Write-Host "`n  Quick Responses complete" -ForegroundColor Green
}

# ============================================================
# CLEANUP
# ============================================================
function Invoke-Cleanup {
    Write-Host "`n>>> WARNING: This will delete Hero Cases and activities!" -ForegroundColor Red
    $confirm = Read-Host "Type 'DELETE' to confirm"
    
    if ($confirm -ne "DELETE") {
        Write-Host "Cleanup cancelled." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Cleaning up hero case data..." -ForegroundColor Yellow
    
    # Delete hero cases
    if ($heroCases) {
        foreach ($case in $heroCases.heroCases) {
            Write-Host "  Deleting hero case: $($case.title)" -ForegroundColor Gray
            $escapedTitle = $case.title -replace "'", "''"
            $existing = Invoke-DataverseGet -EntitySet "incidents" -Filter "title eq '$escapedTitle'" -Select "incidentid" -Top 1
            if ($existing -and $existing.Count -gt 0) {
                Invoke-DataverseDelete -EntitySet "incidents" -Id $existing[0].incidentid
                Write-Host "    Deleted" -ForegroundColor DarkRed
            }
        }
    }
    
    Write-Host "Cleanup complete." -ForegroundColor Green
}

# ============================================================
# MAIN EXECUTION
# ============================================================
switch ($Action) {
    "All" {
        Provision-HeroCases
        Provision-KnowledgeArticles
        Provision-AgentScripts
        Provision-Macros
        Provision-QuickResponses
    }
    "HeroCases" { Provision-HeroCases }
    "KnowledgeArticles" { Provision-KnowledgeArticles }
    "AgentScripts" { Provision-AgentScripts }
    "Macros" { Provision-Macros }
    "QuickResponses" { Provision-QuickResponses }
    "Cleanup" { Invoke-Cleanup }
}

# Export results
$exportPath = Join-Path $scriptDir "data\hero-cases-provisioned.json"
$createdRecords | ConvertTo-Json -Depth 5 | Set-Content $exportPath -Force

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Provisioning Complete" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Results exported to: $exportPath" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  Hero Cases:         $($createdRecords.heroCases.Count)" -ForegroundColor Gray
Write-Host "  Activities:         $($createdRecords.activities.Count)" -ForegroundColor Gray
Write-Host "  Knowledge Articles: $($createdRecords.knowledgeArticles.Count)" -ForegroundColor Gray
Write-Host "  Agent Scripts:      $($createdRecords.agentScripts.Count) (manual setup required)" -ForegroundColor Gray
Write-Host "  Macros:             $($createdRecords.macros.Count) (manual setup required)" -ForegroundColor Gray
Write-Host "  Quick Responses:    $($createdRecords.quickResponses.Count)" -ForegroundColor Gray
Write-Host ""

# Manual setup instructions
Write-Host "NEXT STEPS - Manual Configuration Required:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. KNOWLEDGE ARTICLES" -ForegroundColor Cyan
Write-Host "   - Go to: Customer Service Hub > Knowledge Articles" -ForegroundColor Gray
Write-Host "   - Review and publish each article" -ForegroundColor Gray
Write-Host "   - Enable for Copilot in article settings" -ForegroundColor Gray
Write-Host ""
Write-Host "2. AGENT SCRIPTS" -ForegroundColor Cyan
Write-Host "   - Go to: Customer Service admin center > Agent experience > Productivity > Agent scripts" -ForegroundColor Gray
Write-Host "   - Create scripts based on productivity-toolkit.json" -ForegroundColor Gray
Write-Host "   - Associate with app profile" -ForegroundColor Gray
Write-Host ""
Write-Host "3. MACROS" -ForegroundColor Cyan
Write-Host "   - Go to: Customer Service admin center > Agent experience > Productivity > Macros" -ForegroundColor Gray
Write-Host "   - Create macros based on productivity-toolkit.json" -ForegroundColor Gray
Write-Host ""
Write-Host "4. SLA CONFIGURATION" -ForegroundColor Cyan
Write-Host "   - Go to: Customer Service admin center > Service terms > SLA" -ForegroundColor Gray
Write-Host "   - Create SLAs based on sla-definitions.json" -ForegroundColor Gray
Write-Host "   - Associate with entitlements" -ForegroundColor Gray
Write-Host ""
