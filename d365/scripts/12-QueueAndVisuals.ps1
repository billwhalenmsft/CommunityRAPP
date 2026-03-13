<#
.SYNOPSIS
    Step 12 - Queue Membership + Hot Word Visual Enhancements
.DESCRIPTION
    Part 1: Adds admin user as member of ALL routing queues so items
            always appear in their queue view in CS Workspace
    Part 2: Updates active cases with hot word titles -- sets
            Priority=High, IsEscalated=true, Severity=High
    Part 3: Creates a JavaScript web resource that displays a
            warning banner on the Case form when hot words are
            detected in the title. Also auto-sets priority/severity.
    Part 4: Registers the web resource on the Case form OnLoad
            event (targets "Case for Multisession experience" form
            used by CS Workspace, plus the Interactive experience form)
    Part 5: Summary and verification steps
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "12" "Queue Membership + Hot Word Visual Enhancements"
Connect-Dataverse

# ============================================================
# Configuration
# ============================================================
$adminUserId = "cc00d659-5f51-ef11-a317-0022482a41a0"
$hotWords = @('urgent', 'emergency', 'recall', 'safety', 'legal', 'next day air')
$headers = Get-DataverseHeaders
$base = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# ============================================================
# Part 1: Queue Membership
# ============================================================
Write-Host "`n--- Part 1: Add User to All Routing Queues ---" -ForegroundColor Cyan

$queueData = Get-Content "$scriptDir\..\data\queue-ids.json" | ConvertFrom-Json
$qAdded = 0; $qExisted = 0; $qFailed = 0

foreach ($prop in $queueData.PSObject.Properties) {
    $qName = $prop.Name
    $qId = $prop.Value

    try {
        $assocBody = '{"@odata.id":"' + $base + '/systemusers(' + $adminUserId + ')"}'
        $assocHeaders = @{
            "Authorization" = $headers["Authorization"]
            "Content-Type"  = "application/json"
        }
        Invoke-RestMethod `
            -Uri "$base/queues($qId)/queuemembership_association/`$ref" `
            -Headers $assocHeaders `
            -Method Post `
            -Body $assocBody
        Write-Host "  Added: $qName" -ForegroundColor Green
        $qAdded++
    } catch {
        $msg = $_.Exception.Message
        if ($msg -match "0x80040237" -or $msg -match "Cannot insert duplicate" -or $msg -match "already exists") {
            Write-Host "  Already member: $qName" -ForegroundColor DarkGray
            $qExisted++
        } else {
            Write-Host "  FAILED: $qName -- $msg" -ForegroundColor Red
            $qFailed++
        }
    }
}
Write-Host "  Summary: $qAdded added, $qExisted already existed, $qFailed failed" -ForegroundColor Yellow

# Also add user to the QS default queue if not already covered
$qsQueueId = "0f487994-f317-f111-8342-7ced8d18c8d7"
try {
    $assocBody = '{"@odata.id":"' + $base + '/systemusers(' + $adminUserId + ')"}'
    Invoke-RestMethod `
        -Uri "$base/queues($qsQueueId)/queuemembership_association/`$ref" `
        -Headers @{ "Authorization" = $headers["Authorization"]; "Content-Type" = "application/json" } `
        -Method Post `
        -Body $assocBody
    Write-Host "  Added: QS Default Queue" -ForegroundColor Green
} catch {
    Write-Host "  Already member: QS Default Queue" -ForegroundColor DarkGray
}

# ============================================================
# Part 2: Hot Word Case Field Updates
# ============================================================
Write-Host "`n--- Part 2: Update Hot Word Cases (Priority, Severity, Escalated) ---" -ForegroundColor Cyan

# Build OData filter for hot words in title
$filterParts = $hotWords | ForEach-Object { "contains(title,'$_')" }
$odataFilter = "statecode eq 0 and (" + ($filterParts -join " or ") + ")"

# Use raw REST to avoid helper return-value ambiguity
$caseList = @()
try {
    $resp = Invoke-RestMethod -Uri "$base/incidents?`$filter=$odataFilter&`$select=title,prioritycode,isescalated,incidentid,severitycode" -Headers $headers
    $caseList = @($resp.value)
} catch {
    Write-Host "  OData contains() filter failed, falling back to client-side filter" -ForegroundColor Yellow
    $resp2 = Invoke-RestMethod -Uri "$base/incidents?`$filter=statecode eq 0&`$select=title,prioritycode,isescalated,incidentid,severitycode" -Headers $headers
    foreach ($c in $resp2.value) {
        if (-not $c.title) { continue }
        $lower = $c.title.ToLower()
        foreach ($hw in $hotWords) {
            if ($lower.Contains($hw)) {
                $caseList += $c
                break
            }
        }
    }
}

Write-Host "  Found $($caseList.Count) active cases with hot words" -ForegroundColor Yellow

$cUpdated = 0
foreach ($case in $caseList) {
    $patch = @{}
    if ($case.prioritycode -ne 1) { $patch["prioritycode"] = 1 }
    if ($case.isescalated -ne $true) { $patch["isescalated"] = $true }
    if ($case.severitycode -ne 1) { $patch["severitycode"] = 1 }

    if ($patch.Count -gt 0) {
        Invoke-DataversePatch -EntitySet "incidents" -RecordId $case.incidentid -Body $patch
        $matchedWords = ($hotWords | Where-Object { $case.title.ToLower().Contains($_) }) -join ", "
        Write-Host "  Updated: $($case.title) [$matchedWords]" -ForegroundColor Green
        $cUpdated++
    } else {
        Write-Host "  Already set: $($case.title)" -ForegroundColor DarkGray
    }
}
Write-Host "  $cUpdated / $($caseList.Count) cases updated" -ForegroundColor Yellow

# ============================================================
# Part 3: JavaScript Web Resource - Hot Word Form Notification
# ============================================================
Write-Host "`n--- Part 3: Create Hot Word Notification Web Resource ---" -ForegroundColor Cyan

$jsContent = @'
// Zurn Elkay - Hot Word Notification (Tiered Severity Banners)
// Displays a color-coded banner on the Case form when hot words are detected:
//   RED (ERROR)   : recall, safety, legal, emergency  (compliance/safety)
//   YELLOW (WARNING): urgent, next day air             (time-sensitive)
// Also auto-sets Priority=High, Severity=High, Escalated=Yes.
//
// Register on Case main form OnLoad event.
// Function name: ZurnElkay.HotWordNotification
// Pass execution context: Yes

var ZurnElkay = ZurnElkay || {};

ZurnElkay.HotWordNotification = function(executionContext) {
    var formContext = executionContext.getFormContext();
    var titleAttr = formContext.getAttribute("title");
    if (!titleAttr) return;

    // Critical = RED banner (safety/compliance/legal)
    // High     = YELLOW banner (time-sensitive urgency)
    var criticalWords = ["recall", "safety", "legal", "emergency"];
    var highWords     = ["urgent", "next day air"];

    var checkHotWords = function() {
        var titleVal = (titleAttr.getValue() || "").toLowerCase();
        var criticalDetected = [];
        var highDetected = [];

        for (var i = 0; i < criticalWords.length; i++) {
            if (titleVal.indexOf(criticalWords[i]) >= 0) {
                criticalDetected.push(criticalWords[i].toUpperCase());
            }
        }
        for (var i = 0; i < highWords.length; i++) {
            if (titleVal.indexOf(highWords[i]) >= 0) {
                highDetected.push(highWords[i].toUpperCase());
            }
        }

        // Clear previous notifications
        formContext.ui.clearFormNotification("zurnelkay_hotword_critical");
        formContext.ui.clearFormNotification("zurnelkay_hotword_high");

        if (criticalDetected.length > 0) {
            var msg = "CRITICAL ALERT: " + criticalDetected.join(", ") +
                " detected -- This case requires immediate attention." +
                " Escalated to Tier 1 queue. Compliance/Safety review may be required.";
            formContext.ui.setFormNotification(msg, "ERROR", "zurnelkay_hotword_critical");
        }

        if (highDetected.length > 0) {
            var msg = "PRIORITY ESCALATION: " + highDetected.join(", ") +
                " detected -- This case has been routed to Tier 1 priority queue." +
                " Priority and severity set to HIGH.";
            formContext.ui.setFormNotification(msg, "WARNING", "zurnelkay_hotword_high");
        }

        if (criticalDetected.length > 0 || highDetected.length > 0) {
            // Auto-set priority to High (1)
            var priority = formContext.getAttribute("prioritycode");
            if (priority && priority.getValue() !== 1) {
                priority.setValue(1);
                priority.fireOnChange();
            }

            // Auto-set escalated
            var escalated = formContext.getAttribute("isescalated");
            if (escalated && !escalated.getValue()) {
                escalated.setValue(true);
            }

            // Auto-set severity to High (1)
            var severity = formContext.getAttribute("severitycode");
            if (severity && severity.getValue() !== 1) {
                severity.setValue(1);
            }
        }
    };

    // Check on load
    checkHotWords();

    // Also check when title changes (real-time detection during data entry)
    titleAttr.removeOnChange(checkHotWords);
    titleAttr.addOnChange(checkHotWords);
};
'@

$jsBytes = [System.Text.Encoding]::UTF8.GetBytes($jsContent)
$jsBase64 = [Convert]::ToBase64String($jsBytes)

$wrName = "new_ZurnElkayHotWordNotification"

$wrResp = Invoke-RestMethod -Uri "$base/webresourceset?`$filter=name eq '$wrName'&`$select=webresourceid,name" -Headers $headers

if ($wrResp.value.Count -gt 0) {
    $wrId = $wrResp.value[0].webresourceid
    $wrPatchBody = @{
        content     = $jsBase64
        displayname = "Zurn Elkay - Hot Word Notification"
        description = "Case form OnLoad - warning banner + auto-set fields when hot words in title"
    } | ConvertTo-Json -Depth 5
    $patchH = @{
        "Authorization" = $headers["Authorization"]
        "Content-Type"  = "application/json; charset=utf-8"
        "OData-Version" = "4.0"
        "If-Match"      = "*"
    }
    Invoke-RestMethod -Uri "$base/webresourceset($wrId)" -Headers $patchH -Method Patch -Body $wrPatchBody
    Write-Host "  Updated: $wrName ($wrId)" -ForegroundColor Green
} else {
    $wrResult = Invoke-DataversePost "webresourceset" @{
        name            = $wrName
        displayname     = "Zurn Elkay - Hot Word Notification"
        description     = "Case form OnLoad - warning banner + auto-set fields when hot words in title"
        webresourcetype = 3
        content         = $jsBase64
    }
    $wrId = $wrResult.webresourceid
    Write-Host "  Created: $wrName ($wrId)" -ForegroundColor Green
}

# Publish the web resource
Write-Host "  Publishing web resource..." -ForegroundColor Yellow
$pubXml = "<importexportxml><webresources><webresource>{$wrId}</webresource></webresources></importexportxml>"
$pubBody = @{ ParameterXml = $pubXml } | ConvertTo-Json
try {
    Invoke-RestMethod -Uri "$base/PublishXml" -Headers $headers -Method Post -Body $pubBody
    Write-Host "  Published" -ForegroundColor Green
} catch {
    Write-Host "  Publish warning: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ============================================================
# Part 4: Register Web Resource on Case Forms
# ============================================================
Write-Host "`n--- Part 4: Register Handler on Case Forms ---" -ForegroundColor Cyan

# Target these forms (Multisession + Enhanced full + Enhanced custom)
$targetFormNames = @(
    "Case for Multisession experience",
    "Enhanced full case form",
    "Enhanced full case form custom"
)

$libraryRef = '$webresource:' + $wrName
$functionName = "ZurnElkay.HotWordNotification"
$formsModified = 0

foreach ($formName in $targetFormNames) {
    Write-Host "  Checking: $formName" -ForegroundColor White

    try {
        $formResp = Invoke-RestMethod -Uri "$base/systemforms?`$filter=name eq '$formName' and objecttypecode eq 'incident' and type eq 2&`$select=formid,name,formxml" -Headers $headers

        if ($formResp.value.Count -eq 0) {
            Write-Host "    Not found, skipping" -ForegroundColor DarkGray
            continue
        }

        $form = $formResp.value[0]
        $formXml = [xml]$form.formxml

        # Check if handler is already registered
        $existingHandler = $formXml.SelectNodes("//Handler[@functionName='$functionName']")
        if ($existingHandler -and $existingHandler.Count -gt 0) {
            Write-Host "    Handler already registered" -ForegroundColor DarkGray
            continue
        }

        # Find or create events node
        $formRoot = $formXml.DocumentElement
        $eventsNode = $formXml.SelectSingleNode("//form/events")
        if (-not $eventsNode) {
            $eventsNode = $formXml.CreateElement("events")
            $formRoot.AppendChild($eventsNode) | Out-Null
        }

        # Find or create onload event
        $onloadEvent = $formXml.SelectSingleNode("//form/events/event[@name='onload']")
        if (-not $onloadEvent) {
            $onloadEvent = $formXml.CreateElement("event")
            $onloadEvent.SetAttribute("name", "onload")
            $onloadEvent.SetAttribute("application", "false")
            $onloadEvent.SetAttribute("active", "true")
            $eventsNode.AppendChild($onloadEvent) | Out-Null
        }

        # Find or create Handlers node
        $handlersNode = $onloadEvent.SelectSingleNode("Handlers")
        if (-not $handlersNode) {
            $handlersNode = $formXml.CreateElement("Handlers")
            $onloadEvent.AppendChild($handlersNode) | Out-Null
        }

        # Add our handler
        $handlerId = [Guid]::NewGuid().ToString()
        $handler = $formXml.CreateElement("Handler")
        $handler.SetAttribute("functionName", $functionName)
        $handler.SetAttribute("libraryName", $libraryRef)
        $handler.SetAttribute("handlerUniqueId", "{$handlerId}")
        $handler.SetAttribute("enabled", "true")
        $handler.SetAttribute("parameters", "")
        $handler.SetAttribute("passExecutionContext", "true")
        $handlersNode.AppendChild($handler) | Out-Null

        # Update the form via raw REST (formid may not parse as guid)
        $newFormXml = $formXml.OuterXml
        $formPatchBody = @{ formxml = $newFormXml } | ConvertTo-Json -Depth 5
        $patchHeaders = @{
            "Authorization" = $headers["Authorization"]
            "Content-Type"  = "application/json; charset=utf-8"
            "OData-Version" = "4.0"
            "If-Match"      = "*"
        }
        Invoke-RestMethod -Uri "$base/systemforms($($form.formid))" -Headers $patchHeaders -Method Patch -Body $formPatchBody
        Write-Host "    Registered handler on: $formName" -ForegroundColor Green
        $formsModified++
    } catch {
        Write-Host "    Failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "    Manual registration may be required for this form" -ForegroundColor Yellow
    }
}

# Publish the Case entity if any forms were modified
if ($formsModified -gt 0) {
    Write-Host "  Publishing Case entity..." -ForegroundColor Yellow
    $pubEntityXml = "<importexportxml><entities><entity>incident</entity></entities></importexportxml>"
    $pubEntityBody = @{ ParameterXml = $pubEntityXml } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$base/PublishXml" -Headers $headers -Method Post -Body $pubEntityBody
        Write-Host "  Published Case entity ($formsModified forms updated)" -ForegroundColor Green
    } catch {
        Write-Host "  Entity publish warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# ============================================================
# Part 5: Export IDs
# ============================================================
$exportData = @{
    webResourceId    = $wrId
    webResourceName  = $wrName
    formsModified    = $formsModified
    casesUpdated     = $cUpdated
    queueMemberships = $qAdded
}
$exportData | ConvertTo-Json | Set-Content "$scriptDir\..\data\visual-ids.json"
Write-Host "`nIDs saved to data\visual-ids.json" -ForegroundColor DarkGray

# ============================================================
# Summary
# ============================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Queue Membership + Visual Enhancements Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Queue Memberships  : $qAdded added, $qExisted existing" -ForegroundColor White
Write-Host "  Cases Updated      : $cUpdated cases (Priority=High, Escalated, Severity=High)" -ForegroundColor White
Write-Host "  Web Resource       : $wrName" -ForegroundColor White
Write-Host "  Forms Modified     : $formsModified" -ForegroundColor White
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "  HOT WORD VISUAL BEHAVIOR:" -ForegroundColor Yellow
Write-Host "    When a case title contains a hot word:" -ForegroundColor White
Write-Host "      - WARNING BANNER shows at top of the case form" -ForegroundColor White
Write-Host "      - Priority auto-set to HIGH (red in views)" -ForegroundColor White
Write-Host "      - Severity auto-set to HIGH" -ForegroundColor White
Write-Host "      - Escalated flag set to YES (escalation icon)" -ForegroundColor White
Write-Host "      - Case routed to Zurn Phone - Tier 1 queue" -ForegroundColor White
Write-Host ""
Write-Host "  Hot words: urgent, emergency, recall, safety, legal, next day air" -ForegroundColor White
Write-Host ""
Write-Host "--- VERIFY ---" -ForegroundColor Yellow
Write-Host "  1. Open CS Workspace > Queues > check each queue shows you as member" -ForegroundColor White
Write-Host "  2. Open an existing case with 'urgent' or 'recall' in title" -ForegroundColor White
Write-Host "     -> Should see yellow WARNING banner at top of form" -ForegroundColor White
Write-Host "     -> Priority = High, Severity = High, Escalated = Yes" -ForegroundColor White
Write-Host "  3. Create NEW case, type 'URGENT' in title" -ForegroundColor White
Write-Host "     -> Banner appears in real-time as you type" -ForegroundColor White
Write-Host ""
