<#
.SYNOPSIS
    Step 10 - Configure Unified Routing for Zurn Elkay Demo
.DESCRIPTION
    Creates a Record-type workstream for case routing with simplified
    route-to-queue rules based on case origin (email/phone) and brand.

    Workstreams created:
      - Zurn Elkay Case Routing (Record/Case channel)

    Route-to-queue rules (evaluated first-match):
      1. Phone + High Priority -> Zurn Phone - Tier 1
      2. Phone (any)          -> Zurn Phone - General
      3. Email + hydration    -> Elkay Hydration Support
      4. Email + sink         -> Elkay Sinks & Fixtures
      5. Email + drain        -> Drainage
      6. Email + commercial   -> Commercial Email
      7. Fallback             -> General Support

    NOTES on Unified Routing API:
      - Navigation property names are case-sensitive (capital I in Id)
      - Routing contract entity is msdyn_decisioncontract (not msdyn_routingcontract)
      - Decision ruleset requires msdyn_uniquename field
      - msdyn_authoringmode only accepts 192350000
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "10" "Configure Unified Routing"
Connect-Dataverse

# ============================================================
# Load queue IDs
# ============================================================
Write-Host "Loading queue IDs..." -ForegroundColor Yellow
$queueData = Get-Content "$scriptDir\..\data\queue-ids.json" | ConvertFrom-Json
$queueMap = @{}
$queueData.PSObject.Properties | ForEach-Object { $queueMap[$_.Name] = $_.Value }

Write-Host "  Loaded $($queueMap.Count) queues" -ForegroundColor DarkGray

# Verify key queues exist
$requiredQueues = @('General Support', 'Zurn Phone - Tier 1', 'Zurn Phone - General', 'Elkay Hydration Support', 'Elkay Sinks & Fixtures', 'Drainage', 'Commercial Email')
$missing = $requiredQueues | Where-Object { -not $queueMap.ContainsKey($_) }
if ($missing.Count -gt 0) {
    Write-Warning "Missing queues: $($missing -join ', '). Run 05-Queues.ps1 first."
    exit 1
}

# ============================================================
# Look up master entity routing config for Case
# ============================================================
Write-Host "Looking up Case routing hub..." -ForegroundColor Yellow
$merc = Invoke-DataverseGet -EntitySet "msdyn_masterentityroutingconfigurations" `
    -Filter "msdyn_entitylogicalname eq 'incident'" `
    -Select "msdyn_masterentityroutingconfigurationid,msdyn_name" -Top 1

$mercId = $null
if ($merc -and $merc.Count -gt 0) {
    $mercId = $merc[0].msdyn_masterentityroutingconfigurationid
    Write-Host "  Case routing hub: $($merc[0].msdyn_name) ($mercId)" -ForegroundColor DarkGray
} else {
    Write-Warning "Case routing hub not found. Unified Routing may not be enabled."
}

# ============================================================
# Look up the routing contract (entity: msdyn_decisioncontract)
# Cannot query msdyn_decisioncontracts directly; get from a
# reference record-type workstream instead.
# ============================================================
Write-Host "Looking up routing contract..." -ForegroundColor Yellow
$recordContract = $null

$refWs = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
    -Filter "msdyn_streamsource eq 192350000" `
    -Select "msdyn_liveworkstreamid,msdyn_name,_msdyn_routingcontractid_value" -Top 1

if ($refWs -and $refWs.Count -gt 0 -and $refWs[0]._msdyn_routingcontractid_value) {
    $recordContract = $refWs[0]._msdyn_routingcontractid_value
    Write-Host "  Routing contract (from ref workstream): $recordContract" -ForegroundColor DarkGray
} else {
    Write-Host "  No existing record workstream to reference." -ForegroundColor Yellow
}

# ============================================================
# 1. Create the Workstream
# ============================================================
# NOTE: Workstream creation requires precise OData navigation
# property names. Key nav properties (case-sensitive):
#   msdyn_defaultqueue@odata.bind -> /queues(guid)
#   msdyn_masterentityroutingconfigurationId@odata.bind -> /msdyn_masterentityroutingconfigurations(guid)
#   msdyn_routingcontractid@odata.bind -> /msdyn_decisioncontracts(guid)
# ============================================================
Write-Host "`nCreating workstream..." -ForegroundColor Yellow

$defaultQueueId = $queueMap['General Support']
$workstreamName = "Zurn Elkay Case Routing"

# Check if already exists
$existingWs = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
    -Filter "msdyn_name eq '$workstreamName'" `
    -Select "msdyn_liveworkstreamid" -Top 1

if ($existingWs -and $existingWs.Count -gt 0) {
    $wsId = $existingWs[0].msdyn_liveworkstreamid
    Write-Host "  Already exists: $workstreamName ($wsId)" -ForegroundColor DarkGray
} else {
    $wsBody = @{
        msdyn_name                                    = $workstreamName
        msdyn_streamsource                            = 192350000     # Record
        msdyn_mode                                    = 717210001     # Push (non-persistent)
        msdyn_capacityrequired                        = 30
        msdyn_capacityformat                          = 192350000     # Unit-based
        msdyn_workdistributionmode                    = 192350000     # Push
        msdyn_notification                            = 100000001     # Desktop notifications
        msdyn_isdefault                               = $false
        msdyn_direction                               = 0             # Inbound
        msdyn_conversationmode                        = 192350000
        msdyn_allowedpresences                        = "192360000,192360001,192360002,192360003,192360004"
        msdyn_enableagentaffinity                     = $false
        msdyn_enableautomatedmessages                 = $true
        msdyn_enableselectingfrompushbasedworkstreams = $true
        msdyn_autocloseafterinactivity                = 0
        msdyn_notificationtemplate_incoming_auth      = "msdyn_entityrouting_assigned"
        msdyn_sessiontemplate_default                 = "msdyn_entityrouting_session"
        msdyn_screenpoptimeout_optionSet              = 120
        "msdyn_defaultqueue@odata.bind"               = "/queues($defaultQueueId)"
    }

    # Nav property names are CASE-SENSITIVE (capital I in Id)
    if ($mercId) {
        $wsBody["msdyn_masterentityroutingconfigurationId@odata.bind"] = "/msdyn_masterentityroutingconfigurations($mercId)"
    }
    if ($recordContract) {
        $wsBody["msdyn_routingcontractid@odata.bind"] = "/msdyn_decisioncontracts($recordContract)"
    }

    $headers = Get-DataverseHeaders
    $apiUrl = Get-DataverseApiUrl
    $json = $wsBody | ConvertTo-Json -Depth 5
    $resp = Invoke-WebRequest -Uri "${apiUrl}msdyn_liveworkstreams" -Method Post `
        -Headers $headers -Body $json -ContentType "application/json" -UseBasicParsing
    $entityId = $resp.Headers["OData-EntityId"]
    if ($entityId -match '\(([0-9a-f-]+)\)') { $wsId = $Matches[1] }
    else { Write-Error "Failed to parse workstream ID from response."; exit 1 }
}

if (-not $wsId) {
    Write-Error "Failed to create workstream."
    exit 1
}
Write-Host "  Workstream: $workstreamName ($wsId)" -ForegroundColor Green

# ============================================================
# 2. Create Route-to-Queue Decision Ruleset
# ============================================================
Write-Host "`nCreating route-to-queue decision ruleset..." -ForegroundColor Yellow

$rulesetName = "Zurn Elkay Route to Queue Rules"

# Build the XML ruleset definition
# hit-policy="first" means first matching rule wins
# Conditions use incident entity fields:
#   - caseorigincode: 1=Phone, 2=Email, 3=Web
#   - For tier routing we use the customer account's accountnumber field

function New-RuleXml {
    param(
        [string]$RuleName,
        [string]$QueueId,
        [string]$ConditionsXml = ""
    )
    $ruleId = [guid]::NewGuid().ToString()
    if ($ConditionsXml) {
        return @"
    <rule id="$ruleId" name="$RuleName">
      <logical operator="AND">
$ConditionsXml
      </logical>
      <action>
        <setattribute>
          <lhs type="attribute">assign_to.queue</lhs>
          <rhs type="staticvalue">{$QueueId}</rhs>
        </setattribute>
      </action>
    </rule>
"@
    } else {
        # Unconditional rule (fallback)
        return @"
    <rule id="$ruleId" name="$RuleName">
      <action>
        <setattribute>
          <lhs type="attribute">assign_to.queue</lhs>
          <rhs type="staticvalue">{$QueueId}</rhs>
        </setattribute>
      </action>
    </rule>
"@
    }
}

# Build condition blocks
$phoneCondition = @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">1</rhs>
        </condition>
"@

$emailCondition = @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">2</rhs>
        </condition>
"@

# Build the full ruleset XML
$rules = @()

# Rule 1: Phone + Tier 1 accounts -> Zurn Phone Tier 1
$rules += New-RuleXml -RuleName "Phone - Tier 1 Priority" `
    -QueueId $queueMap['Zurn Phone - Tier 1'] `
    -ConditionsXml @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">1</rhs>
        </condition>
        <condition operator="equals">
          <lhs type="attribute">incident.prioritycode</lhs>
          <rhs type="staticvalue">1</rhs>
        </condition>
"@

# Rule 2: Phone general -> Zurn Phone General
$rules += New-RuleXml -RuleName "Phone - Zurn General" `
    -QueueId $queueMap['Zurn Phone - General'] `
    -ConditionsXml $phoneCondition

# Rule 3: Email + title contains hydration/bottle/fountain -> Elkay Hydration
$rules += New-RuleXml -RuleName "Email - Elkay Hydration" `
    -QueueId $queueMap['Elkay Hydration Support'] `
    -ConditionsXml @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">2</rhs>
        </condition>
        <condition operator="contains">
          <lhs type="attribute">incident.title</lhs>
          <rhs type="staticvalue">hydration</rhs>
        </condition>
"@

# Rule 4: Email + title contains sink/faucet -> Elkay Sinks
$rules += New-RuleXml -RuleName "Email - Elkay Sinks and Fixtures" `
    -QueueId $queueMap['Elkay Sinks & Fixtures'] `
    -ConditionsXml @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">2</rhs>
        </condition>
        <condition operator="contains">
          <lhs type="attribute">incident.title</lhs>
          <rhs type="staticvalue">sink</rhs>
        </condition>
"@

# Rule 5: Email + title contains drain -> Drainage
$rules += New-RuleXml -RuleName "Email - Drainage" `
    -QueueId $queueMap['Drainage'] `
    -ConditionsXml @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">2</rhs>
        </condition>
        <condition operator="contains">
          <lhs type="attribute">incident.title</lhs>
          <rhs type="staticvalue">drain</rhs>
        </condition>
"@

# Rule 6: Email + title contains commercial/backflow -> Commercial Email
$rules += New-RuleXml -RuleName "Email - Commercial" `
    -QueueId $queueMap['Commercial Email'] `
    -ConditionsXml @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">2</rhs>
        </condition>
        <condition operator="contains">
          <lhs type="attribute">incident.title</lhs>
          <rhs type="staticvalue">commercial</rhs>
        </condition>
"@

# Rule 7: Fallback -> General Support
$rules += New-RuleXml -RuleName "Fallback - General Support" `
    -QueueId $queueMap['General Support']

$rulesetXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<decision hit-policy="first" version="1">
  <rules>
$($rules -join "`n")
  </rules>
</decision>
"@

# Create or update the decision ruleset
# NOTE: msdyn_uniquename is REQUIRED, msdyn_authoringmode only accepts 192350000
$drsBody = @{
    msdyn_name              = $rulesetName
    msdyn_uniquename        = "ze_route_to_queue_rules"
    msdyn_description       = "Route-to-queue rules for Zurn Elkay cases. First-match policy based on case origin and title keywords."
    msdyn_rulesetdefinition = $rulesetXml
    msdyn_rulesettype       = 192350000
    msdyn_authoringmode     = 192350000
}

$escapedRulesetName = $rulesetName.Replace("'", "''")
$drsId = Find-OrCreate-Record `
    -EntitySet "msdyn_decisionrulesets" `
    -Filter "msdyn_name eq '$escapedRulesetName'" `
    -IdField "msdyn_decisionrulesetid" `
    -Body $drsBody `
    -DisplayName $rulesetName

if ($drsId) {
    Write-Host "  Decision ruleset: $rulesetName ($drsId)" -ForegroundColor Green
    # Update the definition if record already existed
    Invoke-DataversePatch -EntitySet "msdyn_decisionrulesets" -RecordId ([guid]$drsId) -Body @{ msdyn_rulesetdefinition = $rulesetXml }
    Write-Host "  Ruleset definition updated" -ForegroundColor DarkGray
} else {
    Write-Warning "Failed to create decision ruleset"
}

# ============================================================
# 3. Create Entity Routing Configuration (links workstream to entity)
# ============================================================
Write-Host "`nConfiguring entity routing..." -ForegroundColor Yellow

$ercName = "Zurn Elkay Case Entity Routing"
$ercBody = @{
    msdyn_name          = $ercName
    msdyn_entity        = "incident"
    msdyn_entitysetname = "incidents"
}

$ercId = Find-OrCreate-Record `
    -EntitySet "msdyn_entityroutingconfigurations" `
    -Filter "msdyn_name eq '$ercName'" `
    -IdField "msdyn_entityroutingconfigurationid" `
    -Body $ercBody `
    -DisplayName $ercName

if ($ercId) {
    Write-Host "  Entity routing config: $ercName ($ercId)" -ForegroundColor Green

    # Link ERC to workstream (nav property is case-sensitive: capital I in Id)
    $patchResult = Invoke-DataversePatch -EntitySet "msdyn_liveworkstreams" `
        -RecordId ([guid]$wsId) `
        -Body @{
        "msdyn_entityroutingconfigurationId@odata.bind" = "/msdyn_entityroutingconfigurations($ercId)"
    }
    if ($patchResult) {
        Write-Host "  Linked entity routing config to workstream" -ForegroundColor DarkGray
    }
} else {
    Write-Warning "Failed to create entity routing configuration"
}

# ============================================================
# 4. Create route-to-queue rule items (msdyn_ocruleitem)
#    These are individual rule records linked to the workstream.
#    Priority determines evaluation order (lower = first).
# ============================================================
Write-Host "`nCreating route-to-queue rule items..." -ForegroundColor Yellow

$routeRules = @(
    @{ Name = "Phone - Tier 1 Priority"; Queue = "Zurn Phone - Tier 1"; Priority = "10" }
    @{ Name = "Phone - Zurn General"; Queue = "Zurn Phone - General"; Priority = "20" }
    @{ Name = "Email - Elkay Hydration"; Queue = "Elkay Hydration Support"; Priority = "30" }
    @{ Name = "Email - Elkay Sinks"; Queue = "Elkay Sinks & Fixtures"; Priority = "40" }
    @{ Name = "Email - Drainage"; Queue = "Drainage"; Priority = "50" }
    @{ Name = "Email - Commercial"; Queue = "Commercial Email"; Priority = "60" }
    @{ Name = "Fallback - General"; Queue = "General Support"; Priority = "100" }
)

# Check which route-to-queue items already exist on this workstream
$existingItems = Invoke-DataverseGet -EntitySet "msdyn_ocruleitems" `
    -Filter "_msdyn_liveworkstream_value eq $wsId" `
    -Select "msdyn_name,msdyn_ocruleitemid"
$existingNames = @()
if ($existingItems) { $existingNames = $existingItems | ForEach-Object { $_.msdyn_name } }

$ruleCreated = 0
foreach ($rule in $routeRules) {
    $qId = $queueMap[$rule.Queue]
    if (-not $qId) { Write-Warning "Queue not found: $($rule.Queue)"; continue }

    if ($existingNames -contains $rule.Name) {
        Write-Host "  Already exists: $($rule.Name)" -ForegroundColor DarkGray
        $ruleCreated++
        continue
    }

    $body = @{
        msdyn_name                          = $rule.Name
        msdyn_priority                      = $rule.Priority
        "msdyn_liveworkstream@odata.bind"   = "/msdyn_liveworkstreams($wsId)"
        "msdyn_cdsqueueassignid@odata.bind" = "/queues($qId)"
    }
    $headers = Get-DataverseHeaders
    $apiUrl = Get-DataverseApiUrl
    $json = $body | ConvertTo-Json -Depth 5
    try {
        $resp = Invoke-WebRequest -Uri "${apiUrl}msdyn_ocruleitems" -Method Post `
            -Headers $headers -Body $json -ContentType "application/json" -UseBasicParsing
        Write-Host "  Created: $($rule.Name) -> $($rule.Queue)" -ForegroundColor Green
        $ruleCreated++
    } catch {
        Write-Host "  Failed: $($rule.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host "  $ruleCreated route-to-queue rules configured" -ForegroundColor Green

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Unified Routing Configured" -ForegroundColor Green
Write-Host " Workstream          : $workstreamName" -ForegroundColor White
Write-Host " Default Queue       : General Support" -ForegroundColor White
Write-Host " Route-to-Queue Rules: $ruleCreated (6 conditional + 1 fallback)" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

Write-Host "`n  Route-to-Queue Rules:" -ForegroundColor Cyan
Write-Host "    1. Phone + High Priority  -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    2. Phone (any)            -> Zurn Phone - General" -ForegroundColor White
Write-Host "    3. Email + 'hydration'    -> Elkay Hydration Support" -ForegroundColor White
Write-Host "    4. Email + 'sink'         -> Elkay Sinks & Fixtures" -ForegroundColor White
Write-Host "    5. Email + 'drain'        -> Drainage" -ForegroundColor White
Write-Host "    6. Email + 'commercial'   -> Commercial Email" -ForegroundColor White
Write-Host "    7. Fallback               -> General Support" -ForegroundColor White

# Export
$routedQueueNames = $routeRules | ForEach-Object { $_.Queue }
$exportData = @{
    WorkstreamId          = $wsId.ToString()
    WorkstreamName        = $workstreamName
    DecisionRulesetId     = if ($drsId) { $drsId.ToString() } else { "N/A" }
    EntityRoutingConfigId = if ($ercId) { $ercId.ToString() } else { "N/A" }
    DefaultQueue          = "General Support"
    RouteToQueueRules     = $ruleCreated
    RoutedQueues          = $routedQueueNames
}
$exportData | ConvertTo-Json -Depth 3 | Out-File "$scriptDir\..\data\routing-ids.json" -Encoding utf8
Write-Host "`nRouting IDs saved to data\routing-ids.json" -ForegroundColor DarkGray

# ============================================================
# Manual steps reminder
# ============================================================
Write-Host "`n--- VERIFY IN D365 ---" -ForegroundColor Magenta
Write-Host @"

  1. Open Customer Service admin center
  2. Navigate to Customer Support > Workstreams
  3. Find 'Zurn Elkay Case Routing' workstream
  4. Click into it - verify:
     a. Type = Record (Case)
     b. Default queue = General Support
     c. Route-to-queue rules are visible
  5. To test: Create a case with origin=Phone, priority=High
     - It should route to 'Zurn Phone - Tier 1'
  6. Create a case with origin=Email, title contains 'drain'
     - It should route to 'Drainage' queue

  NOTE: You may need to manually activate the workstream
  and turn on Unified Routing for the Case entity in
  Admin Center > Customer Support > Routing if not already done.

"@ -ForegroundColor Yellow
