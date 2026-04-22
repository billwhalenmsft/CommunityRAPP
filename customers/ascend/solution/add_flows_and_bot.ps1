<#
.SYNOPSIS
  Creates 6 Power Automate flows + 1 Copilot Studio bot in the Dataverse org
  and adds them all to the AscendProcurementAgent solution.

.REQUIREMENTS
  - az login completed with access to org6feab6b5.crm.dynamics.com
  - Run from repo root or any directory; flow JSONs are resolved from script location
#>

$OrgUrl       = "https://org6feab6b5.crm.dynamics.com"
$SolutionName = "AscendProcurementAgent"
$PublisherPrefix = "ascend"
$Timestamp    = Get-Date -Format "yyyyMMddHHmmss"

$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WorkflowsDir = Join-Path $ScriptDir "solution_src\Workflows"

# ── Auth ──────────────────────────────────────────────────────────────────────
Write-Host "`n🔑 Getting access token..." -ForegroundColor Cyan
$Token   = (az account get-access-token --resource $OrgUrl --query "accessToken" -o tsv)
$Headers = @{
    "Authorization"    = "Bearer $Token"
    "Content-Type"     = "application/json"
    "OData-Version"    = "4.0"
    "OData-MaxVersion" = "4.0"
    "Prefer"           = "return=representation"
}

# ── Helpers ───────────────────────────────────────────────────────────────────
function Add-ToSolution {
    param($ComponentId, $ComponentType, $Description)
    $body = @{
        ComponentId            = $ComponentId
        ComponentType          = $ComponentType
        SolutionUniqueName     = $SolutionName
        AddRequiredComponents  = $false
        DoNotIncludeSubcomponents = $false
    } | ConvertTo-Json

    try {
        Invoke-RestMethod "$OrgUrl/api/data/v9.2/AddSolutionComponent" `
            -Method Post -Headers $Headers -Body $body | Out-Null
        Write-Host "  ✅ Added to solution: $Description" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not add $Description to solution: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Fix-SwitchCases {
    # Power Automate requires each Switch case object to have a "case" property
    # equal to the key name. Recursively fix all Switch actions.
    param([hashtable]$Actions)
    if (-not $Actions) { return $Actions }

    foreach ($actionName in @($Actions.Keys)) {
        $action = $Actions[$actionName]
        if ($action -is [PSCustomObject]) {
            $action = ConvertTo-Hashtable $action
            $Actions[$actionName] = $action
        }

        if ($action.type -eq "Switch" -and $action.cases) {
            $cases = $action.cases
            if ($cases -is [PSCustomObject]) { $cases = ConvertTo-Hashtable $cases }
            $newCases = @{}
            foreach ($caseName in @($cases.Keys)) {
                $caseObj = $cases[$caseName]
                if ($caseObj -is [PSCustomObject]) { $caseObj = ConvertTo-Hashtable $caseObj }
                if (-not $caseObj.ContainsKey("case")) {
                    $caseObj["case"] = $caseName
                }
                if ($caseObj.ContainsKey("actions") -and $caseObj.actions) {
                    $innerActions = $caseObj.actions
                    if ($innerActions -is [PSCustomObject]) { $innerActions = ConvertTo-Hashtable $innerActions }
                    $caseObj.actions = Fix-SwitchCases -Actions $innerActions
                }
                $newCases[$caseName] = $caseObj
            }
            $action.cases = $newCases
        }

        # Recurse into nested actions (if/else, foreach, etc.)
        foreach ($subKey in @("actions","else","runAfter")) {
            if ($action.ContainsKey($subKey) -and $action[$subKey]) {
                if ($subKey -eq "actions" -and $action[$subKey] -is [hashtable]) {
                    $action[$subKey] = Fix-SwitchCases -Actions $action[$subKey]
                } elseif ($subKey -eq "else" -and $action[$subKey].actions) {
                    $elseActions = $action[$subKey].actions
                    if ($elseActions -is [PSCustomObject]) { $elseActions = ConvertTo-Hashtable $elseActions }
                    $action[$subKey].actions = Fix-SwitchCases -Actions $elseActions
                }
            }
        }
    }
    return $Actions
}

function ConvertTo-Hashtable {
    param([PSCustomObject]$obj)
    $ht = @{}
    foreach ($prop in $obj.PSObject.Properties) {
        if ($prop.Value -is [PSCustomObject]) {
            $ht[$prop.Name] = ConvertTo-Hashtable $prop.Value
        } elseif ($prop.Value -is [System.Collections.IEnumerable] -and $prop.Value -isnot [string]) {
            $ht[$prop.Name] = $prop.Value
        } else {
            $ht[$prop.Name] = $prop.Value
        }
    }
    return $ht
}

function Build-FlowClientData {
    param($FlowDefinition)
    # Wrap Logic App JSON in Power Automate clientdata envelope
    # schemaVersion must be at the TOP LEVEL (not inside properties)
    $clientData = @{
        properties = @{
            connectionReferences = @{
                shared_commondataserviceforapps = @{
                    runtimeSource = "embedded"
                    connection    = @{
                        connectionReferenceLogicalName = "msdyn_sharedcommondataserviceforapps"
                    }
                    api           = @{ name = "shared_commondataserviceforapps" }
                }
            }
            templateName = ""
            definition   = $FlowDefinition
        }
        schemaVersion = "1.0.0.0"
    }
    return ($clientData | ConvertTo-Json -Depth 20 -Compress)
}

# ── 1. Create 6 Power Automate flows ─────────────────────────────────────────
Write-Host "`n🔄 Creating Power Automate flows..." -ForegroundColor Cyan

$FlowFiles = @(
    @{ File = "flow_sap_create_pr.json";      UniqueSuffix = "sap_create_pr"      }
    @{ File = "flow_sap_approve_pr.json";     UniqueSuffix = "sap_approve_pr"     }
    @{ File = "flow_sap_cancel_pr.json";      UniqueSuffix = "sap_cancel_pr"      }
    @{ File = "flow_sap_get_pr_status.json";  UniqueSuffix = "sap_get_pr_status"  }
    @{ File = "flow_sap_vendor_lookup.json";  UniqueSuffix = "sap_vendor_lookup"  }
    @{ File = "flow_sap_send_reminder.json";  UniqueSuffix = "sap_send_reminder"  }
)

$CreatedFlows = @()

foreach ($ff in $FlowFiles) {
    $filePath = Join-Path $WorkflowsDir $ff.File
    if (-not (Test-Path $filePath)) {
        Write-Host "  ⚠️  File not found: $filePath" -ForegroundColor Yellow
        continue
    }

    $flowDef     = Get-Content $filePath -Raw | ConvertFrom-Json
    $displayName = $flowDef.metadata.flowDisplayName
    $uniqueName  = "${PublisherPrefix}_$($ff.UniqueSuffix)"

    Write-Host "  Creating: $displayName" -ForegroundColor White

    # Check if flow already exists
    $existing = Invoke-RestMethod `
        "$OrgUrl/api/data/v9.2/workflows?`$filter=uniquename eq '$uniqueName'&`$select=workflowid,name" `
        -Headers $Headers
    
    if ($existing.value.Count -gt 0) {
        $wfId = $existing.value[0].workflowid
        Write-Host "  ⏭️  Already exists (id=$wfId) — skipping create" -ForegroundColor DarkGray
        $CreatedFlows += @{ Id = $wfId; Name = $displayName; UniqueName = $uniqueName }
        continue
    }

    # Build the flow definition with required PA parameters
    $actionsRaw = $flowDef.actions
    if ($actionsRaw -is [PSCustomObject]) { $actionsRaw = ConvertTo-Hashtable $actionsRaw }
    $fixedActions = Fix-SwitchCases -Actions $actionsRaw

    $defObj = [ordered]@{
        '$schema'      = "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#"
        contentVersion = "1.0.0.0"
        parameters     = @{
            '$connections'    = @{ defaultValue = @{}; type = "Object" }
            '$authentication' = @{ defaultValue = @{}; type = "SecureObject" }
        }
        triggers       = $flowDef.triggers
        actions        = $fixedActions
        outputs        = @{}
    }

    $clientDataJson = Build-FlowClientData -FlowDefinition $defObj

    $wfBody = @{
        name           = $displayName
        uniquename     = $uniqueName
        category       = 5          # Modern Flow
        type           = 1          # Definition
        primaryentity  = "none"
        clientdata     = $clientDataJson
        statecode      = 0
        statuscode     = 1
    } | ConvertTo-Json -Depth 3

    try {
        $result = Invoke-RestMethod "$OrgUrl/api/data/v9.2/workflows" `
            -Method Post -Headers $Headers -Body $wfBody
        $wfId = $result.workflowid
        Write-Host "  ✅ Created flow: $displayName (id=$wfId)" -ForegroundColor Green
        $CreatedFlows += @{ Id = $wfId; Name = $displayName; UniqueName = $uniqueName }
    } catch {
        $errBody = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        Write-Host "  ❌ Failed to create $displayName : $($errBody.error.message)" -ForegroundColor Red
    }
}

# ── 2. Create Copilot Studio bot ──────────────────────────────────────────────
Write-Host "`n🤖 Creating Copilot Studio bot..." -ForegroundColor Cyan

$BotName       = "Ascend SAP PR Agent"
$BotSchemaName = "${PublisherPrefix}_SAP_PR_Agent_${Timestamp}"

# Check if already exists
$existingBot = Invoke-RestMethod `
    "$OrgUrl/api/data/v9.2/bots?`$filter=name eq '$BotName'&`$select=botid,name,schemaname" `
    -Headers $Headers

$BotId = $null
if ($existingBot.value.Count -gt 0) {
    $BotId = $existingBot.value[0].botid
    Write-Host "  ⏭️  Bot already exists: $BotName (id=$BotId)" -ForegroundColor DarkGray
} else {
    $botBody = @{
        name           = $BotName
        schemaname     = $BotSchemaName
        language       = 1033        # en-US
        template       = "default-2.0.1"
    } | ConvertTo-Json

    try {
        $botResult = Invoke-RestMethod "$OrgUrl/api/data/v9.2/bots" `
            -Method Post -Headers $Headers -Body $botBody
        $BotId = $botResult.botid
        Write-Host "  ✅ Created bot: $BotName (id=$BotId)" -ForegroundColor Green
    } catch {
        $errBody = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        Write-Host "  ❌ Failed to create bot: $($errBody.error.message)" -ForegroundColor Red
    }
}

# ── 3. Add flows + bot to solution ───────────────────────────────────────────
Write-Host "`n📦 Adding components to solution '$SolutionName'..." -ForegroundColor Cyan

foreach ($flow in $CreatedFlows) {
    Add-ToSolution -ComponentId $flow.Id -ComponentType 29 -Description "Flow: $($flow.Name)"
}

if ($BotId) {
    Add-ToSolution -ComponentId $BotId -ComponentType 10185 -Description "Bot: $BotName"
}

# ── 4. Summary ────────────────────────────────────────────────────────────────
Write-Host "`n════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ DONE — AscendProcurementAgent solution now contains:" -ForegroundColor Green
Write-Host "   • 8 Dataverse tables (previously added)"
Write-Host "   • $($CreatedFlows.Count) Power Automate flows"
if ($BotId) { Write-Host "   • 1 Copilot Studio bot (Ascend SAP PR Agent)" }
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Open Power Automate → Solutions → AscendProcurementAgent → Cloud Flows"
Write-Host "     • Add the Dataverse connection to each flow"
Write-Host "     • Turn each flow ON"
Write-Host "  2. Open Copilot Studio → Open 'Ascend SAP PR Agent'"
Write-Host "     • Add topics from transpiled/ YAML files"
Write-Host "     • Connect flows as actions in each topic"
Write-Host "     • Publish to Teams channel"
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
