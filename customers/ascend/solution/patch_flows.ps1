<#
.SYNOPSIS
  Patches all 6 Ascend PA flows with:
    1. Correct trigger kind = "Agent" (Run a flow from Copilot / When an agent calls a flow)
    2. Full trigger input schema restored from local JSON source files
    3. Correct OpenApiConnection host/apiId + authentication on all actions
    4. $authentication + $connections parameters in definition

  Run this script any time trigger inputs get wiped or trigger kind is wrong.
#>

$OrgUrl = "https://org6feab6b5.crm.dynamics.com"
$DV_API  = "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps"

Write-Host "`n🔑 Getting access token..." -ForegroundColor Cyan
$Token   = (az account get-access-token --resource $OrgUrl --query "accessToken" -o tsv)
$Headers = @{
    "Authorization"    = "Bearer $Token"
    "Content-Type"     = "application/json"
    "OData-Version"    = "4.0"
    "OData-MaxVersion" = "4.0"
    "If-Match"         = "*"
}

# ── Recursive helpers ─────────────────────────────────────────────────────────
function PSObj-To-Hash {
    param($obj)
    if ($obj -is [System.Collections.IDictionary]) { return $obj }
    $ht = [ordered]@{}
    foreach ($p in $obj.PSObject.Properties) {
        $v = $p.Value
        if ($v -is [PSCustomObject])  { $v = PSObj-To-Hash $v }
        elseif ($v -is [System.Collections.IEnumerable] -and $v -isnot [string]) {
            $v = @($v | ForEach-Object {
                if ($_ -is [PSCustomObject]) { PSObj-To-Hash $_ } else { $_ }
            })
        }
        $ht[$p.Name] = $v
    }
    return $ht
}

function Fix-Actions {
    # Recursively:
    #  1. Add apiId + authentication to every OpenApiConnection action
    #  2. Add "case" key to every Switch case entry
    param([System.Collections.IDictionary]$actions)
    if (-not $actions) { return $actions }

    foreach ($name in @($actions.Keys)) {
        $a = $actions[$name]
        if ($a -isnot [System.Collections.IDictionary]) {
            $a = PSObj-To-Hash $a
            $actions[$name] = $a
        }

        $type = $a["type"]

        # ── OpenApiConnection: add apiId + authentication ──
        if ($type -in @("OpenApiConnection","OpenApiConnectionWebhook","OpenApiConnectionNotification")) {
            $inp = $a["inputs"]
            if ($inp -isnot [System.Collections.IDictionary]) { $inp = PSObj-To-Hash $inp; $a["inputs"] = $inp }
            $host_ = $inp["host"]
            if ($host_ -isnot [System.Collections.IDictionary]) { $host_ = PSObj-To-Hash $host_; $inp["host"] = $host_ }
            if (-not $host_["apiId"]) { $host_["apiId"] = $DV_API }
            if (-not $inp["authentication"]) { $inp["authentication"] = "@parameters('`$authentication')" }
        }

        # ── Switch: add "case" to each case entry, recurse ──
        if ($type -eq "Switch" -and $a["cases"]) {
            $cases = $a["cases"]
            if ($cases -isnot [System.Collections.IDictionary]) { $cases = PSObj-To-Hash $cases; $a["cases"] = $cases }
            foreach ($cName in @($cases.Keys)) {
                $c = $cases[$cName]
                if ($c -isnot [System.Collections.IDictionary]) { $c = PSObj-To-Hash $c; $cases[$cName] = $c }
                if (-not $c["case"]) { $c["case"] = $cName }
                if ($c["actions"]) {
                    $ca = $c["actions"]
                    if ($ca -isnot [System.Collections.IDictionary]) { $ca = PSObj-To-Hash $ca; $c["actions"] = $ca }
                    $c["actions"] = Fix-Actions $ca
                }
            }
        }

        # ── If: recurse into actions + else.actions ──
        if ($type -eq "If") {
            if ($a["actions"]) {
                $ia = $a["actions"]
                if ($ia -isnot [System.Collections.IDictionary]) { $ia = PSObj-To-Hash $ia; $a["actions"] = $ia }
                $a["actions"] = Fix-Actions $ia
            }
            if ($a["else"] -and $a["else"]["actions"]) {
                $ea = $a["else"]["actions"]
                if ($ea -isnot [System.Collections.IDictionary]) { $ea = PSObj-To-Hash $ea; $a["else"]["actions"] = $ea }
                $a["else"]["actions"] = Fix-Actions $ea
            }
        }

        # ── Foreach / Until / Scope: recurse into actions ──
        if ($type -in @("Foreach","Until","Scope") -and $a["actions"]) {
            $fa = $a["actions"]
            if ($fa -isnot [System.Collections.IDictionary]) { $fa = PSObj-To-Hash $fa; $a["actions"] = $fa }
            $a["actions"] = Fix-Actions $fa
        }
    }
    return $actions
}

# ── Flow uniquename → local JSON source file mapping ─────────────────────────
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$FlowMap = [ordered]@{
    "ascend_sap_create_pr"     = "$ScriptDir\solution_src\Workflows\flow_sap_create_pr.json"
    "ascend_sap_approve_pr"    = "$ScriptDir\solution_src\Workflows\flow_sap_approve_pr.json"
    "ascend_sap_cancel_pr"     = "$ScriptDir\solution_src\Workflows\flow_sap_cancel_pr.json"
    "ascend_sap_get_pr_status" = "$ScriptDir\solution_src\Workflows\flow_sap_get_pr_status.json"
    "ascend_sap_vendor_lookup" = "$ScriptDir\solution_src\Workflows\flow_sap_vendor_lookup.json"
    "ascend_sap_send_reminder" = "$ScriptDir\solution_src\Workflows\flow_sap_send_reminder.json"
}

Write-Host "`n🔧 Patching flows: trigger kind → Agent, input schema, OpenApiConnection format..." -ForegroundColor Cyan

foreach ($uname in $FlowMap.Keys) {
    $jsonFile = $FlowMap[$uname]
    Write-Host "`n  Flow: $uname" -ForegroundColor White

    if (-not (Test-Path $jsonFile)) {
        Write-Host "    ⚠️  Source JSON not found: $jsonFile — skipping" -ForegroundColor Yellow; continue
    }

    # Load canonical trigger+actions from our source JSON
    $srcDef = Get-Content $jsonFile -Raw | ConvertFrom-Json
    $srcDefHash = PSObj-To-Hash $srcDef

    # Fetch current clientdata from Dataverse (to preserve connection references etc.)
    $resp = Invoke-RestMethod `
        "$OrgUrl/api/data/v9.2/workflows?`$filter=uniquename eq '$uname'&`$select=workflowid,name,clientdata" `
        -Headers $Headers
    if ($resp.value.Count -eq 0) {
        Write-Host "    ⚠️  Not found in Dataverse — skipping" -ForegroundColor Yellow; continue
    }
    $wf   = $resp.value[0]
    $wfId = $wf.workflowid
    Write-Host "    id=$wfId name=$($wf.name)"

    $cd = $wf.clientdata | ConvertFrom-Json
    $cdHash = PSObj-To-Hash $cd

    $def = $cdHash["properties"]["definition"]
    if ($def -isnot [System.Collections.IDictionary]) { $def = PSObj-To-Hash $def; $cdHash["properties"]["definition"] = $def }

    # ── FIX 1: Restore trigger from source JSON (kind=Agent + full input schema) ──
    $srcTriggers = $srcDefHash["triggers"]
    if ($srcTriggers -and $srcTriggers["manual"]) {
        $srcTrigger = $srcTriggers["manual"]
        if ($srcTrigger -isnot [System.Collections.IDictionary]) { $srcTrigger = PSObj-To-Hash $srcTrigger }

        $defTriggers = $def["triggers"]
        if ($defTriggers -isnot [System.Collections.IDictionary]) {
            $defTriggers = [ordered]@{}
            $def["triggers"] = $defTriggers
        }
        $defTrigger = $defTriggers["manual"]
        if ($defTrigger -isnot [System.Collections.IDictionary]) {
            $defTrigger = [ordered]@{}
            $defTriggers["manual"] = $defTrigger
        }

        # Always force kind = Skills (Power Automate's internal value for "Run a flow from Copilot" / "When an agent calls a flow")
        $defTrigger["kind"] = "Agent"
        $defTrigger["type"] = "Request"

        # Restore inputs.schema from source JSON (fixes wiped input params)
        if ($srcTrigger["inputs"] -and $srcTrigger["inputs"]["schema"]) {
            $srcSchema = $srcTrigger["inputs"]["schema"]
            if ($srcSchema -isnot [System.Collections.IDictionary]) { $srcSchema = PSObj-To-Hash $srcSchema }
            $defTriggerInputs = $defTrigger["inputs"]
            if ($defTriggerInputs -isnot [System.Collections.IDictionary]) {
                $defTriggerInputs = [ordered]@{}
                $defTrigger["inputs"] = $defTriggerInputs
            }
            $defTriggerInputs["schema"] = $srcSchema
            Write-Host "    ✓ Trigger: kind=Agent, schema inputs restored" -ForegroundColor DarkGreen
        }
    }

    # ── FIX 2: Fix actions (OpenApiConnection apiId + auth + Switch cases) ──
    $acts = $def["actions"]
    if ($acts -isnot [System.Collections.IDictionary]) { $acts = PSObj-To-Hash $acts; $def["actions"] = $acts }
    $def["actions"] = Fix-Actions $acts

    # ── FIX 3: Ensure $authentication + $connections parameters present ──
    $params = $def["parameters"]
    if ($params -isnot [System.Collections.IDictionary]) { $params = PSObj-To-Hash $params; $def["parameters"] = $params }
    if (-not $params['$authentication']) {
        $params['$authentication'] = [ordered]@{ defaultValue = @{}; type = "SecureObject" }
    }
    if (-not $params['$connections']) {
        $params['$connections'] = [ordered]@{ defaultValue = @{}; type = "Object" }
    }

    # Serialize and PATCH
    $newClientData = $cdHash | ConvertTo-Json -Depth 30 -Compress

    $patchBody = @{ clientdata = $newClientData } | ConvertTo-Json -Depth 2
    try {
        Invoke-RestMethod "$OrgUrl/api/data/v9.2/workflows($wfId)" `
            -Method Patch -Headers $Headers -Body $patchBody | Out-Null
        Write-Host "    ✅ Patched successfully" -ForegroundColor Green
    } catch {
        $err = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        Write-Host "    ❌ Patch failed: $($err.error.message)" -ForegroundColor Red
        Write-Host "    Raw: $($_.Exception.Message)" -ForegroundColor DarkRed
    }
}

Write-Host "`n✅ Done. Flows now use 'Run a flow from Copilot' trigger with full input schema." -ForegroundColor Green
Write-Host "   Next: In Power Automate → open each flow → verify connections → Save → confirm On." -ForegroundColor Cyan
