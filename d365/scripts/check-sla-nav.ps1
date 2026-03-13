$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$out = @()

# Get existing SLA items from the pre-existing SLA with all details
$existingSla = ((Invoke-WebRequest -Uri "$b/slas?`$filter=statecode eq 1&`$select=slaid,name" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
if ($existingSla.Count -gt 0) {
    $existSlaId = $existingSla[0].slaid
    $out += "Existing SLA: $($existingSla[0].name) ($existSlaId)"
    
    $itemFilter = [System.Uri]::EscapeDataString("_slaid_value eq '$existSlaId'")
    $items = ((Invoke-WebRequest -Uri "$b/slaitems?`$filter=$itemFilter&`$select=name,slaitemid,_msdyn_slakpiid_value,failureafter,warnafter,applicablewhenxml,successconditionsxml" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
    $out += "Items: $($items.Count)"
    $items | ForEach-Object {
        $out += "`n  Name: $($_.name)"
        $out += "  ID: $($_.slaitemid)"
        $out += "  KPI ID: $($_._msdyn_slakpiid_value)"
        $out += "  Failure After: $($_.failureafter)"
        $out += "  Warn After: $($_.warnafter)"
        $out += "  Applicable: $($_.applicablewhenxml)"
        $out += "  Success: $($_.successconditionsxml)"
    }
}

# Check navigation properties for slaitem entity
$nav = ((Invoke-WebRequest -Uri "$b/EntityDefinitions(LogicalName='slaitem')/ManyToOneRelationships?`$select=SchemaName,ReferencedEntityNavigationPropertyName,ReferencingEntityNavigationPropertyName,ReferencedEntity,ReferencingAttribute" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
$kpiNav = $nav | Where-Object { $_.ReferencingAttribute -match 'kpi' -or $_.SchemaName -match 'kpi' }
$out += "`nNavigation properties related to KPI:"
$kpiNav | ForEach-Object {
    $out += "  Schema: $($_.SchemaName) | RefAttr: $($_.ReferencingAttribute) | NavProp: $($_.ReferencingEntityNavigationPropertyName) | RefEntity: $($_.ReferencedEntity)"
}

$out | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\sla-nav.txt" -Encoding utf8
Write-Host "Output in data\sla-nav.txt"
