<#
.SYNOPSIS
    Step 11 - Consolidate Routing + Hot Word Classification
.DESCRIPTION
    Consolidates routing into the QS_Customer Service workstream created
    by the Guided Channel Setup, adding Zurn Elkay business rules:

    Hot Word Detection Rules (highest priority - route to Tier 1):
      1. Title contains 'urgent'     -> Zurn Phone - Tier 1
      2. Title contains 'emergency'  -> Zurn Phone - Tier 1
      3. Title contains 'recall'     -> Zurn Phone - Tier 1
      4. Title contains 'safety'     -> Zurn Phone - Tier 1
      5. Title contains 'legal'      -> Zurn Phone - Tier 1
      6. Title contains 'next day air' -> Zurn Phone - Tier 1

    Brand/Product Routing Rules:
      7.  Phone + High Priority -> Zurn Phone - Tier 1
      8.  Phone (any)           -> Zurn Phone - General
      9.  Email + hydration     -> Elkay Hydration Support
      10. Email + sink          -> Elkay Sinks & Fixtures
      11. Email + drain         -> Drainage
      12. Email + commercial    -> Commercial Email
      13. Fallback              -> General Support

    Also:
      - Updates ARC rule to allow unknown senders
      - Deactivates the old Zurn Elkay Case Routing workstream
      - Cleans up orphaned rule items from old workstream

    NOTES:
      - Uses the QS-format ruleset XML for route-to-queue evaluation
      - hit-policy="first" for first-match evaluation
      - Hot word rules are evaluated before brand/product rules
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "11" "Consolidate Routing + Hot Word Classification"
Connect-Dataverse

# ============================================================
# Load queue IDs
# ============================================================
Write-Host "Loading queue IDs..." -ForegroundColor Yellow
$queueData = Get-Content "$scriptDir\..\data\queue-ids.json" | ConvertFrom-Json
$queueMap = @{}
$queueData.PSObject.Properties | ForEach-Object { $queueMap[$_.Name] = $_.Value }
Write-Host "  Loaded $($queueMap.Count) queues" -ForegroundColor DarkGray

$requiredQueues = @(
    'General Support',
    'Zurn Phone - Tier 1',
    'Zurn Phone - General',
    'Elkay Hydration Support',
    'Elkay Sinks & Fixtures',
    'Drainage',
    'Commercial Email'
)
$missing = $requiredQueues | Where-Object { -not $queueMap.ContainsKey($_) }
if ($missing.Count -gt 0) {
    Write-Warning "Missing queues: $($missing -join ', '). Run 05-Queues.ps1 first."
    exit 1
}

# ============================================================
# 1. Identify QS_Customer Service workstream and ruleset
# ============================================================
Write-Host "`nLocating QS_Customer Service workstream..." -ForegroundColor Yellow

$qsWsName = "QS_Customer Service_Case workstream"
$qsWs = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
    -Filter "msdyn_name eq '$qsWsName'" `
    -Select "msdyn_liveworkstreamid,msdyn_name" -Top 1

if (-not $qsWs -or $qsWs.Count -eq 0) {
    Write-Error "QS_Customer Service workstream not found. Run the Guided Channel Setup first."
    exit 1
}
$qsWsId = $qsWs[0].msdyn_liveworkstreamid
Write-Host "  Found: $qsWsName ($qsWsId)" -ForegroundColor Green

$qsRsName = "QS_Customer Service_Ruleset name"
$qsRs = Invoke-DataverseGet -EntitySet "msdyn_decisionrulesets" `
    -Filter "msdyn_name eq '$qsRsName'" `
    -Select "msdyn_decisionrulesetid,msdyn_name,msdyn_uniquename" -Top 1

if (-not $qsRs -or $qsRs.Count -eq 0) {
    Write-Warning "QS_Customer Service ruleset not found. Creating one..."
    $qsRsId = $null
} else {
    $qsRsId = $qsRs[0].msdyn_decisionrulesetid
    Write-Host "  Ruleset: $qsRsName ($qsRsId)" -ForegroundColor Green
}

# ============================================================
# 2. Build consolidated route-to-queue rules
# ============================================================
Write-Host "`nBuilding consolidated routing rules..." -ForegroundColor Yellow

# Hot words from Zurn Elkay business rules
$hotWords = @('urgent', 'emergency', 'recall', 'safety', 'legal', 'next day air')
$tier1QueueId = $queueMap['Zurn Phone - Tier 1']

# Helper to generate a rule XML block
function New-RouteRuleXml {
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
        # Fallback rule - no conditions
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

$allRuleXmls = @()

# -- Hot Word Rules (evaluated first) --
foreach ($hw in $hotWords) {
    $safeName = "Hot Word - " + (Get-Culture).TextInfo.ToTitleCase($hw)
    $condXml = @"
        <condition operator="contains">
          <lhs type="attribute">incident.title</lhs>
          <rhs type="staticvalue">$hw</rhs>
        </condition>
"@
    $allRuleXmls += New-RouteRuleXml -RuleName $safeName -QueueId $tier1QueueId -ConditionsXml $condXml
}

# -- Phone + High Priority -> Tier 1 --
$allRuleXmls += New-RouteRuleXml -RuleName "Phone - Tier 1 Priority" `
    -QueueId $tier1QueueId `
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

# -- Phone general -> Zurn Phone General --
$allRuleXmls += New-RouteRuleXml -RuleName "Phone - Zurn General" `
    -QueueId $queueMap['Zurn Phone - General'] `
    -ConditionsXml @"
        <condition operator="equals">
          <lhs type="attribute">incident.caseorigincode</lhs>
          <rhs type="staticvalue">1</rhs>
        </condition>
"@

# -- Email + hydration -> Elkay Hydration --
$allRuleXmls += New-RouteRuleXml -RuleName "Email - Elkay Hydration" `
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

# -- Email + sink -> Elkay Sinks --
$allRuleXmls += New-RouteRuleXml -RuleName "Email - Elkay Sinks and Fixtures" `
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

# -- Email + drain -> Drainage --
$allRuleXmls += New-RouteRuleXml -RuleName "Email - Drainage" `
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

# -- Email + commercial -> Commercial Email --
$allRuleXmls += New-RouteRuleXml -RuleName "Email - Commercial" `
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

# -- Fallback -> General Support --
$allRuleXmls += New-RouteRuleXml -RuleName "Fallback - General Support" `
    -QueueId $queueMap['General Support']

$fullRulesetXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<decision hit-policy="first" version="1">
  <rules>
$($allRuleXmls -join "`n")
  </rules>
</decision>
"@

Write-Host "  Built $($allRuleXmls.Count) rules (6 hot word + 2 phone + 4 email + 1 fallback)" -ForegroundColor Green

# ============================================================
# 3. Update the QS decision ruleset with consolidated rules
# ============================================================
Write-Host "`nUpdating QS decision ruleset definition..." -ForegroundColor Yellow

if ($qsRsId) {
    $patchOk = Invoke-DataversePatch -EntitySet "msdyn_decisionrulesets" `
        -RecordId ([guid]$qsRsId) `
        -Body @{ msdyn_rulesetdefinition = $fullRulesetXml }
    if ($patchOk) {
        Write-Host "  Updated ruleset: $qsRsName" -ForegroundColor Green
    } else {
        Write-Warning "Failed to update ruleset definition"
    }
} else {
    # Create new ruleset
    $uniqueName = "ze_consolidated_rules_" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    $newRsBody = @{
        msdyn_name              = $qsRsName
        msdyn_uniquename        = $uniqueName
        msdyn_description       = "Consolidated route-to-queue rules for Zurn Elkay (hot words + brand/product routing)."
        msdyn_rulesetdefinition = $fullRulesetXml
        msdyn_rulesettype       = 192350000
        msdyn_authoringmode     = 192350000
    }
    $qsRsId = Find-OrCreate-Record `
        -EntitySet "msdyn_decisionrulesets" `
        -Filter "msdyn_name eq '$qsRsName'" `
        -IdField "msdyn_decisionrulesetid" `
        -Body $newRsBody `
        -DisplayName $qsRsName
    if ($qsRsId) {
        Write-Host "  Created ruleset: $qsRsName ($qsRsId)" -ForegroundColor Green
    }
}

# ============================================================
# 4. Create route-to-queue rule items on QS workstream
# ============================================================
Write-Host "`nCreating route-to-queue rule items on QS workstream..." -ForegroundColor Yellow

$routeRules = @(
    # Hot word rules - priority 1-6 (evaluated first)
    @{ Name = "Hot Word - Urgent";       Queue = "Zurn Phone - Tier 1"; Priority = "1" }
    @{ Name = "Hot Word - Emergency";    Queue = "Zurn Phone - Tier 1"; Priority = "2" }
    @{ Name = "Hot Word - Recall";       Queue = "Zurn Phone - Tier 1"; Priority = "3" }
    @{ Name = "Hot Word - Safety";       Queue = "Zurn Phone - Tier 1"; Priority = "4" }
    @{ Name = "Hot Word - Legal";        Queue = "Zurn Phone - Tier 1"; Priority = "5" }
    @{ Name = "Hot Word - Next Day Air"; Queue = "Zurn Phone - Tier 1"; Priority = "6" }
    # Phone rules
    @{ Name = "Phone - Tier 1 Priority"; Queue = "Zurn Phone - Tier 1"; Priority = "10" }
    @{ Name = "Phone - Zurn General";    Queue = "Zurn Phone - General"; Priority = "20" }
    # Email product rules
    @{ Name = "Email - Elkay Hydration";        Queue = "Elkay Hydration Support"; Priority = "30" }
    @{ Name = "Email - Elkay Sinks and Fixtures"; Queue = "Elkay Sinks & Fixtures"; Priority = "40" }
    @{ Name = "Email - Drainage";               Queue = "Drainage"; Priority = "50" }
    @{ Name = "Email - Commercial";             Queue = "Commercial Email"; Priority = "60" }
    # Fallback
    @{ Name = "Fallback - General";             Queue = "General Support"; Priority = "100" }
)

# Check existing rule items on QS workstream
$existingItems = Invoke-DataverseGet -EntitySet "msdyn_ocruleitems" `
    -Filter "_msdyn_liveworkstream_value eq $qsWsId" `
    -Select "msdyn_name,msdyn_ocruleitemid"
$existingNames = @()
if ($existingItems) { $existingNames = $existingItems | ForEach-Object { $_.msdyn_name } }

$ruleCreated = 0
foreach ($rule in $routeRules) {
    $qId = $queueMap[$rule.Queue]
    if (-not $qId) {
        Write-Warning "Queue not found: $($rule.Queue)"
        continue
    }

    if ($existingNames -contains $rule.Name) {
        Write-Host "  Already exists: $($rule.Name)" -ForegroundColor DarkGray
        $ruleCreated++
        continue
    }

    $body = @{
        msdyn_name                          = $rule.Name
        msdyn_priority                      = $rule.Priority
        "msdyn_liveworkstream@odata.bind"   = "/msdyn_liveworkstreams($qsWsId)"
        "msdyn_cdsqueueassignid@odata.bind" = "/queues($qId)"
    }

    try {
        $result = Invoke-DataversePost -EntitySet "msdyn_ocruleitems" -Body $body
        if ($result) {
            Write-Host "  Created: $($rule.Name) -> $($rule.Queue)" -ForegroundColor Green
            $ruleCreated++
        } else {
            Write-Host "  Failed: $($rule.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Error creating $($rule.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host "  $ruleCreated / $($routeRules.Count) route-to-queue rules configured" -ForegroundColor Green

# ============================================================
# 5. Update ARC rule - allow unknown senders
# ============================================================
Write-Host "`nUpdating ARC rule..." -ForegroundColor Yellow

$arcRuleName = "QS_Customer Service_ARC_Rule"
$arcRules = Invoke-DataverseGet -EntitySet "convertrules" `
    -Filter "name eq '$arcRuleName'" `
    -Select "convertruleid,name,statecode,allowunknownsender" -Top 1

if ($arcRules -and $arcRules.Count -gt 0) {
    $arcId = $arcRules[0].convertruleid
    $currentUnknown = $arcRules[0].allowunknownsender

    if ($currentUnknown -eq $true) {
        Write-Host "  ARC already allows unknown senders" -ForegroundColor DarkGray
    } else {
        # ARC rule must be deactivated to update, then reactivated
        # Deactivate first
        Write-Host "  Deactivating ARC rule to update..." -ForegroundColor DarkGray
        try {
            $deactBody = @{
                statecode  = 0
                statuscode = 1
            }
            Invoke-DataversePatch -EntitySet "convertrules" -RecordId ([guid]$arcId) -Body $deactBody | Out-Null

            # Update the setting
            $updateBody = @{
                allowunknownsender = $true
            }
            $patchOk = Invoke-DataversePatch -EntitySet "convertrules" -RecordId ([guid]$arcId) -Body $updateBody
            if ($patchOk) {
                Write-Host "  Set allowunknownsender = True" -ForegroundColor Green
            }

            # Reactivate
            $reactBody = @{
                statecode  = 1
                statuscode = 2
            }
            Invoke-DataversePatch -EntitySet "convertrules" -RecordId ([guid]$arcId) -Body $reactBody | Out-Null
            Write-Host "  ARC rule reactivated" -ForegroundColor Green
        } catch {
            Write-Warning "ARC update failed: $($_.Exception.Message)"
            Write-Host "  You may need to update allowunknownsender manually in the admin center." -ForegroundColor Yellow
        }
    }
} else {
    Write-Warning "ARC rule '$arcRuleName' not found"
}

# ============================================================
# 6. Clean up old Zurn Elkay workstream
# ============================================================
Write-Host "`nCleaning up old Zurn Elkay Case Routing workstream..." -ForegroundColor Yellow

$oldWsName = "Zurn Elkay Case Routing"
$oldWs = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
    -Filter "msdyn_name eq '$oldWsName'" `
    -Select "msdyn_liveworkstreamid,msdyn_name,statecode" -Top 1

if ($oldWs -and $oldWs.Count -gt 0) {
    $oldWsId = $oldWs[0].msdyn_liveworkstreamid
    Write-Host "  Found: $oldWsName ($oldWsId)" -ForegroundColor DarkGray

    # Delete rule items from old workstream
    $oldRules = Invoke-DataverseGet -EntitySet "msdyn_ocruleitems" `
        -Filter "_msdyn_liveworkstream_value eq $oldWsId" `
        -Select "msdyn_ocruleitemid,msdyn_name"

    if ($oldRules -and $oldRules.Count -gt 0) {
        foreach ($or in $oldRules) {
            $delOk = Invoke-DataverseDelete -EntitySet "msdyn_ocruleitems" -RecordId ([guid]$or.msdyn_ocruleitemid)
            if ($delOk) {
                Write-Host "    Deleted rule item: $($or.msdyn_name)" -ForegroundColor DarkGray
            }
        }
        Write-Host "  Removed $($oldRules.Count) rule items from old workstream" -ForegroundColor Green
    } else {
        Write-Host "  No rule items to clean up" -ForegroundColor DarkGray
    }

    # Deactivate the old workstream
    try {
        $deactOk = Invoke-DataversePatch -EntitySet "msdyn_liveworkstreams" `
            -RecordId ([guid]$oldWsId) `
            -Body @{ statecode = 1; statuscode = 2 }
        if ($deactOk) {
            Write-Host "  Deactivated: $oldWsName" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Could not deactivate old workstream (may already be inactive or in use): $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Old workstream not found (already cleaned up)" -ForegroundColor DarkGray
}

# Also handle the plain "Case workstream" if it exists and isn't the QS one
$plainWs = Invoke-DataverseGet -EntitySet "msdyn_liveworkstreams" `
    -Filter "msdyn_name eq 'Case workstream'" `
    -Select "msdyn_liveworkstreamid,msdyn_name,statecode,createdon" -Top 1

if ($plainWs -and $plainWs.Count -gt 0) {
    $plainCreated = $plainWs[0].createdon
    Write-Host "  Note: 'Case workstream' also exists (created $plainCreated) - leaving as-is" -ForegroundColor Yellow
}

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Consolidated Routing Configured" -ForegroundColor Green
Write-Host " Target Workstream     : $qsWsName" -ForegroundColor White
Write-Host " Decision Ruleset      : $qsRsName" -ForegroundColor White
Write-Host " Route-to-Queue Rules  : $ruleCreated (6 hot word + 7 brand/product)" -ForegroundColor White
Write-Host " ARC Unknown Senders   : Enabled" -ForegroundColor White
Write-Host " Old Workstream        : Deactivated" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green

Write-Host "`n  Hot Word Detection Rules:" -ForegroundColor Cyan
Write-Host "    1. 'urgent'      -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    2. 'emergency'   -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    3. 'recall'      -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    4. 'safety'      -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    5. 'legal'       -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    6. 'next day air'-> Zurn Phone - Tier 1" -ForegroundColor White

Write-Host "`n  Brand/Product Routing Rules:" -ForegroundColor Cyan
Write-Host "    7.  Phone + High Priority -> Zurn Phone - Tier 1" -ForegroundColor White
Write-Host "    8.  Phone (any)           -> Zurn Phone - General" -ForegroundColor White
Write-Host "    9.  Email + 'hydration'   -> Elkay Hydration Support" -ForegroundColor White
Write-Host "    10. Email + 'sink'        -> Elkay Sinks & Fixtures" -ForegroundColor White
Write-Host "    11. Email + 'drain'       -> Drainage" -ForegroundColor White
Write-Host "    12. Email + 'commercial'  -> Commercial Email" -ForegroundColor White
Write-Host "    13. Fallback              -> General Support" -ForegroundColor White

# Export IDs
$exportData = @{
    TargetWorkstreamId    = $qsWsId.ToString()
    TargetWorkstreamName  = $qsWsName
    DecisionRulesetId     = if ($qsRsId) { $qsRsId.ToString() } else { "N/A" }
    ArcRuleId             = if ($arcId) { $arcId.ToString() } else { "N/A" }
    RulesConfigured       = $ruleCreated
    HotWords              = $hotWords
    OldWorkstreamId       = if ($oldWsId) { $oldWsId.ToString() } else { "N/A" }
    OldWorkstreamStatus   = "Deactivated"
}
$exportData | ConvertTo-Json -Depth 3 | Out-File "$scriptDir\..\data\classification-ids.json" -Encoding utf8
Write-Host "`nClassification IDs saved to data\classification-ids.json" -ForegroundColor DarkGray

# ============================================================
# Manual verification steps
# ============================================================
Write-Host "`n--- VERIFY IN D365 ---" -ForegroundColor Magenta
Write-Host @"

  1. Open Customer Service admin center
  2. Navigate to Customer Support > Workstreams
  3. Open 'QS_Customer Service_Case workstream'
  4. Check Route-to-queue section - should show 13 rules
  5. Verify hot word rules appear first (priority 1-6)

  TEST EMAIL-TO-CASE:
    a. Send email to customerservice@D365DemoTSCE30330346.onmicrosoft.com
       Subject: 'URGENT - Defective faucet valve'
       -> Should create case, route to Zurn Phone - Tier 1

    b. Send email with Subject: 'Hydration station maintenance'
       -> Should create case, route to Elkay Hydration Support

    c. Send email with Subject: 'General product inquiry'
       -> Should create case, route to General Support (fallback)

  OPTIONAL ENHANCEMENT: Create a Power Automate flow to:
    - Trigger on case creation
    - Check title for hot words (urgent/emergency/recall/safety/legal/next day air)
    - Set prioritycode = 1 (High) when detected
    - This gives you priority boost in addition to queue routing

"@ -ForegroundColor Yellow
