$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# Check SLA KPI Instances
$out = @()
$r = (Invoke-WebRequest -Uri "$b/slakpiinstances?`$select=name,slakpiinstanceid,computedfailuretime,computedwarningtime,status&`$top=10" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
$out += "slakpiinstances: $($r.value.Count)"

# Check the SLA KPI entity (not instances but the definition)
try {
    # Try msdyn_slakpi
    $r2 = (Invoke-WebRequest -Uri "$b/msdyn_slakpis?`$select=msdyn_name,msdyn_slakpiid,msdyn_applicablefrom&`$top=10" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
    $out += "`nmsdyn_slakpis: $($r2.value.Count)"
    $r2.value | ForEach-Object { $out += "  $($_.msdyn_name) | id=$($_.msdyn_slakpiid) | from=$($_.msdyn_applicablefrom)" }
} catch {
    $out += "msdyn_slakpis not found: $($_.Exception.Message)"
}

# Check what attributes are on slaitems
try {
    $meta = (Invoke-WebRequest -Uri "$b/EntityDefinitions(LogicalName='slaitem')/Attributes?`$select=LogicalName,AttributeType&`$filter=contains(LogicalName,'kpi')" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
    $out += "`nSLA Item KPI attributes:"
    $meta.value | ForEach-Object { $out += "  $($_.LogicalName) ($($_.AttributeType))" }
} catch {
    $out += "Could not get SLA item metadata"
}

$out | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\slakpi-check.txt" -Encoding utf8
Write-Host "Output in data\slakpi-check.txt"
