<#
.SYNOPSIS
  Remove irrelevant forms and public views from the ERAC Lite CRM app module.
  Non-destructive — components remain in the env, just unregistered from THIS app.

.DESCRIPTION
  - Only acts on Main forms (type=2) and public views (querytype=0)
  - Leaves system views (Lookup=64, AdvFind=1, Associated=2, QuickFind=4, etc.) untouched
  - Uses RemoveAppComponents action — reversible via App Designer
#>
param(
    [string]$Org         = "https://org6feab6b5.crm.dynamics.com",
    [string]$AppModuleId = "76da30a5-a23d-f111-bec6-70a8a59a411e"
)

$tok = az account get-access-token --resource $Org --query accessToken -o tsv
$H   = @{
    Authorization     = "Bearer $tok"
    Accept            = "application/json"
    "Content-Type"    = "application/json"
    "OData-Version"   = "4.0"
    "OData-MaxVersion"= "4.0"
}
$base = "$Org/api/data/v9.2"

# Per-entity keep lists. Anything else (Main forms or public views) gets removed from the app.
$keep = @{
    'account' = @{
        forms = @('ERAC Cedent 360')
        views = @('ERAC Cedents — Active','ERAC Cedents — All','All Accounts','Active Accounts')
    }
    'contact' = @{
        forms = @('Contact')
        views = @('ERAC Contacts — Active','Active Contacts','All Contacts')
    }
    'task' = @{
        forms = @('Task')
        views = @('All Tasks','My Tasks')
    }
    'appointment' = @{
        forms = @('Appointment')
        views = @('All Appointments','My Appointments','My Completed Appointments','My Draft Appointments')
    }
    # ERAC custom tables — keep their single 'Information' form + all curated views
    'erac_treaty'           = @{ forms = @('Information'); views = '*' }
    'erac_reserveadequacy'  = @{ forms = @('Information'); views = '*' }
    'erac_partnershiprating'= @{ forms = @('Information'); views = '*' }
    'erac_riskassessment'   = @{ forms = @('Information'); views = '*' }
    'erac_dispute'          = @{ forms = @('Information'); views = '*' }
}

$toRemove = New-Object System.Collections.Generic.List[object]

foreach ($entity in $keep.Keys) {
    $cfg = $keep[$entity]

    # Main forms (type=2) — only consider Active ones
    $forms = (Invoke-RestMethod -Uri "$base/systemforms?`$filter=objecttypecode eq '$entity' and type eq 2 and formactivationstate eq 1&`$select=formid,name" -Headers $H).value
    foreach ($f in $forms) {
        if ($cfg.forms -ne '*' -and $cfg.forms -notcontains $f.name) {
            $toRemove.Add(@{ entity=$entity; type='form'; id=$f.formid; name=$f.name })
        }
    }

    # Public views (querytype=0) only
    if ($cfg.views -ne '*') {
        $views = (Invoke-RestMethod -Uri "$base/savedqueries?`$filter=returnedtypecode eq '$entity' and querytype eq 0 and statecode eq 0&`$select=savedqueryid,name" -Headers $H).value
        foreach ($v in $views) {
            if ($cfg.views -notcontains $v.name) {
                $toRemove.Add(@{ entity=$entity; type='view'; id=$v.savedqueryid; name=$v.name })
            }
        }
    }
}

Write-Host "`n=== PRUNE PLAN ===" -ForegroundColor Cyan
Write-Host "Total components to remove: $($toRemove.Count)" -ForegroundColor Yellow
$toRemove | Group-Object entity | ForEach-Object {
    "  [$($_.Name)] $($_.Count) items"
    $_.Group | ForEach-Object { "      - [$($_.type)] $($_.name)" }
}

if ($toRemove.Count -eq 0) {
    Write-Host "Nothing to do." -ForegroundColor Green
    return
}

Write-Host "`n=== EXECUTING (RemoveAppComponents) ===" -ForegroundColor Cyan

# Batch in groups of 25 to be safe
$batch = New-Object System.Collections.Generic.List[object]
$totalDone = 0
foreach ($item in $toRemove) {
    $odataType = if ($item.type -eq 'form') { '#Microsoft.Dynamics.CRM.systemform' } else { '#Microsoft.Dynamics.CRM.savedquery' }
    $idField   = if ($item.type -eq 'form') { 'formid' }                              else { 'savedqueryid' }
    $batch.Add(@{ '@odata.type'=$odataType; $idField=$item.id })

    if ($batch.Count -ge 25) {
        $body = @{ AppId=$AppModuleId; Components=$batch.ToArray() } | ConvertTo-Json -Depth 5 -Compress
        try {
            Invoke-RestMethod -Uri "$base/RemoveAppComponents" -Method POST -Headers $H -Body $body | Out-Null
            $totalDone += $batch.Count
            Write-Host "  ✓ Removed batch of $($batch.Count) (running total: $totalDone)" -ForegroundColor Green
        } catch {
            Write-Warning "  ✗ Batch failed: $($_.Exception.Message)"
        }
        $batch.Clear()
    }
}
if ($batch.Count -gt 0) {
    $body = @{ AppId=$AppModuleId; Components=$batch.ToArray() } | ConvertTo-Json -Depth 5 -Compress
    try {
        Invoke-RestMethod -Uri "$base/RemoveAppComponents" -Method POST -Headers $H -Body $body | Out-Null
        $totalDone += $batch.Count
        Write-Host "  ✓ Removed final batch of $($batch.Count) (total: $totalDone)" -ForegroundColor Green
    } catch {
        Write-Warning "  ✗ Final batch failed: $($_.Exception.Message)"
    }
}

# Publish the app
Write-Host "`n=== PUBLISH ===" -ForegroundColor Cyan
try {
    $pubBody = @{ ParameterXml = "<importexportxml><appmodules><appmodule>{$AppModuleId}</appmodule></appmodules></importexportxml>" } | ConvertTo-Json -Compress
    Invoke-RestMethod -Uri "$base/PublishXml" -Method POST -Headers $H -Body $pubBody | Out-Null
    Write-Host "  ✓ App republished" -ForegroundColor Green
} catch {
    Write-Warning "  Publish failed (non-fatal): $($_.Exception.Message)"
}

Write-Host "`n✅ Pruning complete. Hard-refresh ERAC Lite CRM (Ctrl+F5)." -ForegroundColor Green
