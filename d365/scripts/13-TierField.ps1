<#
.SYNOPSIS
    Step 13 - Create Tier Level Field with Color-Coded Views
.DESCRIPTION
    Part 1: Creates a Choice (optionset) field 'cr377_tierlevel' on Case with
            color-coded options:
              Tier 1 (red #D13438)    - Strategic customers + hot words
              Tier 2 (orange #CA5010) - Key Account customers
              Tier 3 (blue #0078D4)   - Standard customers
              Tier 4 (gray #6B6B6B)   - Basic customers
    Part 2: Sets tier values on all active cases based on:
            - Hot word in title -> always Tier 1
            - Customer account's entitlement level -> Tier 1-4
            - Fallback -> Tier 3
    Part 3: Updates the hot word JS web resource to also set tier field
    Part 4: Adds cr377_tierlevel column to Active Cases and Enhanced views
    Part 5: Publishes everything
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "13" "Create Tier Level Field with Color-Coded Views"
Connect-Dataverse

$headers = Get-DataverseHeaders
$base = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"
$hotWords = @('urgent', 'emergency', 'recall', 'safety', 'legal', 'next day air')

# ============================================================
# Part 1: Create Tier Level choice field
# ============================================================
Write-Host "`n--- Part 1: Create Tier Level Choice Field ---" -ForegroundColor Cyan

$fieldName = "cr377_tierlevel"

# Check if field already exists
$existCheck = $null
try {
    $existCheck = Invoke-RestMethod -Uri "$base/EntityDefinitions(LogicalName='incident')/Attributes(LogicalName='$fieldName')?`$select=LogicalName" -Headers $headers -ErrorAction SilentlyContinue
} catch {}

if ($existCheck -and $existCheck.LogicalName -eq $fieldName) {
    Write-Host "  Field already exists: $fieldName" -ForegroundColor DarkGray
} else {
    Write-Host "  Creating choice field: $fieldName" -ForegroundColor Yellow

    $fieldDef = @{
        "@odata.type"   = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
        "SchemaName"    = "cr377_TierLevel"
        "DisplayName"   = @{
            "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Tier Level"; "LanguageCode" = 1033 }
            )
        }
        "Description"   = @{
            "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Customer service tier level based on account classification and hot word detection"; "LanguageCode" = 1033 }
            )
        }
        "RequiredLevel" = @{ "Value" = "None" }
        "OptionSet"     = @{
            "@odata.type"   = "Microsoft.Dynamics.CRM.OptionSetMetadata"
            "IsGlobal"      = $false
            "OptionSetType" = "Picklist"
            "Options"       = @(
                @{
                    "Value"       = 192350000
                    "Color"       = "#D13438"
                    "Label"       = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Tier 1"; "LanguageCode" = 1033 }
                        )
                    }
                    "Description" = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Strategic - Highest priority"; "LanguageCode" = 1033 }
                        )
                    }
                },
                @{
                    "Value"       = 192350001
                    "Color"       = "#CA5010"
                    "Label"       = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Tier 2"; "LanguageCode" = 1033 }
                        )
                    }
                    "Description" = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Key Account"; "LanguageCode" = 1033 }
                        )
                    }
                },
                @{
                    "Value"       = 192350002
                    "Color"       = "#0078D4"
                    "Label"       = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Tier 3"; "LanguageCode" = 1033 }
                        )
                    }
                    "Description" = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Standard"; "LanguageCode" = 1033 }
                        )
                    }
                },
                @{
                    "Value"       = 192350003
                    "Color"       = "#6B6B6B"
                    "Label"       = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Tier 4"; "LanguageCode" = 1033 }
                        )
                    }
                    "Description" = @{
                        "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Basic"; "LanguageCode" = 1033 }
                        )
                    }
                }
            )
        }
    }

    $jsonBody = $fieldDef | ConvertTo-Json -Depth 15
    try {
        Invoke-RestMethod `
            -Uri "$base/EntityDefinitions(LogicalName='incident')/Attributes" `
            -Headers @{ Authorization = $headers["Authorization"]; "Content-Type" = "application/json; charset=utf-8"; "OData-Version" = "4.0" } `
            -Method Post `
            -Body $jsonBody
        Write-Host "  Created: $fieldName" -ForegroundColor Green
    } catch {
        $err = $_.ErrorDetails.Message
        if ($err -match "already exists") {
            Write-Host "  Field already exists: $fieldName" -ForegroundColor DarkGray
        } else {
            Write-Host "  Error creating field: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  Detail: $err" -ForegroundColor Red
            throw
        }
    }

    # Publish the field
    Write-Host "  Publishing..." -ForegroundColor Yellow
    $pubBody = @{ ParameterXml = "<importexportxml><entities><entity>incident</entity></entities></importexportxml>" } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/PublishXml" -Headers @{ Authorization = $headers["Authorization"]; "Content-Type" = "application/json"; "OData-Version" = "4.0" } -Method Post -Body $pubBody
    Write-Host "  Published" -ForegroundColor Green
}

# ============================================================
# Part 2: Set Tier Values on Active Cases
# ============================================================
Write-Host "`n--- Part 2: Set Tier Level on Active Cases ---" -ForegroundColor Cyan

# Build customer-to-tier lookup from entitlements
$entResp = Invoke-RestMethod -Uri "$base/entitlements?`$filter=statecode eq 1&`$select=name,_customerid_value" -Headers $headers
$custTierMap = @{}
foreach ($e in $entResp.value) {
    $tier = if ($e.name -match 'Strategic') { 192350000 }
    elseif ($e.name -match 'Key Account') { 192350001 }
    elseif ($e.name -match 'Standard') { 192350002 }
    else { 192350003 }
    $custTierMap[$e._customerid_value] = $tier
}
Write-Host "  Built customer-to-tier map: $($custTierMap.Count) accounts" -ForegroundColor DarkGray

# Get all active cases
$caseResp = Invoke-RestMethod -Uri "$base/incidents?`$filter=statecode eq 0&`$select=title,incidentid,_customerid_value,$fieldName" -Headers $headers
Write-Host "  Active cases: $($caseResp.value.Count)" -ForegroundColor Yellow

$patchH = @{
    "Authorization" = $headers["Authorization"]
    "Content-Type"  = "application/json; charset=utf-8"
    "OData-Version" = "4.0"
    "If-Match"      = "*"
}

$updated = 0; $skipped = 0
foreach ($case in $caseResp.value) {
    $title = if ($case.title) { $case.title.ToLower() } else { "" }

    # Determine tier
    $isHotWord = $false
    foreach ($hw in $hotWords) {
        if ($title.Contains($hw)) { $isHotWord = $true; break }
    }

    if ($isHotWord) {
        $tierVal = 192350000  # Tier 1
    } elseif ($custTierMap.ContainsKey($case._customerid_value)) {
        $tierVal = $custTierMap[$case._customerid_value]
    } else {
        $tierVal = 192350002  # Default Tier 3
    }

    # Only update if different
    $currentVal = $case.$fieldName
    if ($currentVal -eq $tierVal) {
        $skipped++
        continue
    }

    $body = @{ $fieldName = $tierVal } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$base/incidents($($case.incidentid))" -Headers $patchH -Method Patch -Body $body
        $tierLabel = switch ($tierVal) { 192350000 { "Tier 1" } 192350001 { "Tier 2" } 192350002 { "Tier 3" } 192350003 { "Tier 4" } }
        $reason = if ($isHotWord) { "hot word" } else { "customer entitlement" }
        Write-Host "  $tierLabel ($reason): $($case.title.Substring(0,[Math]::Min(55,$case.title.Length)))" -ForegroundColor Green
        $updated++
    } catch {
        Write-Host "  FAILED: $($case.title) -- $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host "  $updated updated, $skipped already set" -ForegroundColor Yellow

# ============================================================
# Part 3: Update Hot Word JS to Also Set Tier Field
# ============================================================
Write-Host "`n--- Part 3: Update JS Web Resource (Tier Field) ---" -ForegroundColor Cyan

$js = @'
var ZurnElkay = ZurnElkay || {};
ZurnElkay.HotWordNotification = function(executionContext) {
    var formContext = executionContext.getFormContext();
    var titleAttr = formContext.getAttribute("title");
    if (!titleAttr) return;
    var criticalWords = ["recall", "safety", "legal", "emergency"];
    var highWords = ["urgent", "next day air"];
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
            var priority = formContext.getAttribute("prioritycode");
            if (priority && priority.getValue() !== 1) {
                priority.setValue(1);
                priority.fireOnChange();
            }
            var escalated = formContext.getAttribute("isescalated");
            if (escalated && !escalated.getValue()) {
                escalated.setValue(true);
            }
            var severity = formContext.getAttribute("severitycode");
            if (severity && severity.getValue() !== 1) {
                severity.setValue(1);
            }
            // Set Tier Level to Tier 1 (192350000)
            var tierLevel = formContext.getAttribute("cr377_tierlevel");
            if (tierLevel && tierLevel.getValue() !== 192350000) {
                tierLevel.setValue(192350000);
            }
        }
    };
    checkHotWords();
    titleAttr.removeOnChange(checkHotWords);
    titleAttr.addOnChange(checkHotWords);
};
'@

$jsBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($js))
$wrId = "6501b107-0618-f111-8341-6045bda80a72"
$wrBody = @{ content = $jsBase64 } | ConvertTo-Json
Invoke-RestMethod -Uri "$base/webresourceset($wrId)" -Headers $patchH -Method Patch -Body $wrBody
Write-Host "  Updated JS web resource" -ForegroundColor Green

# Publish web resource
$pubWrBody = @{ ParameterXml = "<importexportxml><webresources><webresource>{$wrId}</webresource></webresources></importexportxml>" } | ConvertTo-Json
Invoke-RestMethod -Uri "$base/PublishXml" -Headers @{ Authorization = $headers["Authorization"]; "Content-Type" = "application/json"; "OData-Version" = "4.0" } -Method Post -Body $pubWrBody
Write-Host "  Published" -ForegroundColor Green

# ============================================================
# Part 4: Add Tier Level Column to Case Views
# ============================================================
Write-Host "`n--- Part 4: Add Tier Level to Case Views ---" -ForegroundColor Cyan

$targetViews = @(
    @{ id = "00000000-0000-0000-00aa-000010001032"; name = "Active Cases" },
    @{ id = "8e6c9aa8-d371-ec11-8942-000d3a8e5539"; name = "Enhanced Active Cases" },
    @{ id = "00000000-0000-0000-00aa-000010001028"; name = "My Active Cases" }
)

$viewsUpdated = 0
foreach ($viewInfo in $targetViews) {
    $viewId = $viewInfo.id
    $viewName = $viewInfo.name
    Write-Host "  Checking: $viewName" -ForegroundColor White

    try {
        $viewResp = Invoke-RestMethod -Uri "$base/savedqueries($viewId)?`$select=name,fetchxml,layoutxml,layoutjson" -Headers $headers
        $fetchXml = $viewResp.fetchxml
        $layoutXml = $viewResp.layoutxml

        # Check if field already in fetchxml
        if ($fetchXml -match $fieldName) {
            Write-Host "    Already has tier column" -ForegroundColor DarkGray
            continue
        }

        # Add attribute to fetch
        $fetchXml = $fetchXml -replace '</entity>', "  <attribute name='$fieldName' />`n    </entity>"

        # Remove any existing tier cells, then insert exactly one after the title cell
        $layoutXml = $layoutXml -replace "<cell name=['""]$fieldName['""] width=['""]100['""] />\s*", ""
        $tierCell = "<cell name=`"$fieldName`" width=`"100`" />"
        # Insert after the title cell (handles both self-closing quote styles)
        $layoutXml = $layoutXml -replace '(<cell name="title"[^/]*/?>)', "`$1$tierCell"

        # Update the view
        $viewPatch = @{
            fetchxml  = $fetchXml
            layoutxml = $layoutXml
        } | ConvertTo-Json -Depth 5
        Invoke-RestMethod -Uri "$base/savedqueries($viewId)" -Headers $patchH -Method Patch -Body $viewPatch
        Write-Host "    Added tier column" -ForegroundColor Green
        $viewsUpdated++
    } catch {
        Write-Host "    Failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Publish case entity (views + field)
if ($viewsUpdated -gt 0) {
    Write-Host "  Publishing Case entity..." -ForegroundColor Yellow
    $pubBody = @{ ParameterXml = "<importexportxml><entities><entity>incident</entity></entities></importexportxml>" } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/PublishXml" -Headers @{ Authorization = $headers["Authorization"]; "Content-Type" = "application/json"; "OData-Version" = "4.0" } -Method Post -Body $pubBody
    Write-Host "  Published ($viewsUpdated views updated)" -ForegroundColor Green
}

# ============================================================
# Part 5: Add Field to Case Forms
# ============================================================
Write-Host "`n--- Part 5: Add Tier Level to Case Forms ---" -ForegroundColor Cyan
Write-Host "  NOTE: The Tier Level field needs to be added to form layouts" -ForegroundColor Yellow
Write-Host "  manually via the form editor for best placement." -ForegroundColor Yellow
Write-Host "  Recommended: Add to the header or summary section." -ForegroundColor Yellow

# ============================================================
# Summary
# ============================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Tier Level Field Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Field: $fieldName (Choice - 4 color-coded options)" -ForegroundColor White
Write-Host "    Tier 1 (RED)    = Strategic / Hot Word   " -ForegroundColor Red
Write-Host "    Tier 2 (ORANGE) = Key Account            " -ForegroundColor DarkYellow
Write-Host "    Tier 3 (BLUE)   = Standard               " -ForegroundColor Cyan
Write-Host "    Tier 4 (GRAY)   = Basic                  " -ForegroundColor Gray
Write-Host "  Cases Updated: $updated (+ $skipped already set)" -ForegroundColor White
Write-Host "  Views Updated: $viewsUpdated" -ForegroundColor White
Write-Host "  JS Updated: Hot words auto-set Tier 1" -ForegroundColor White
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "--- VERIFY ---" -ForegroundColor Yellow
Write-Host "  1. Open Active Cases view - Tier Level column shows colored pills" -ForegroundColor White
Write-Host "  2. Tier 1 = red pill, Tier 2 = orange, Tier 3 = blue, Tier 4 = gray" -ForegroundColor White
Write-Host "  3. Hot word cases should all show Tier 1 (red)" -ForegroundColor White
Write-Host "  4. Add field to form header for form-level visibility:" -ForegroundColor White
Write-Host "     > Open form editor > drag 'Tier Level' into header row" -ForegroundColor White
Write-Host ""
