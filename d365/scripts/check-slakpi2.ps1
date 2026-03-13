$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$out = @()

# Find entity sets - check slakpiinstance directly
$r = (Invoke-WebRequest -Uri "$b/EntityDefinitions(LogicalName='slakpiinstance')?`$select=LogicalName,EntitySetName" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
$out += "slakpiinstance entity set: $($r.EntitySetName)"

# Check attributes on slaitem that contain 'kpi'
$r2 = (Invoke-WebRequest -Uri "$b/EntityDefinitions(LogicalName='slaitem')/Attributes?`$select=LogicalName,AttributeType" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
$kpiAttrs = $r2.value | Where-Object { $_.LogicalName -match 'kpi' }
$out += "`nSLA Item attributes with 'kpi': $($kpiAttrs.Count)"
$kpiAttrs | ForEach-Object { $out += "  $($_.LogicalName) ($($_.AttributeType))" }

# Also get all required attributes on slaitem
$requiredAttrs = $r2.value | Where-Object { $_.LogicalName -match 'sla' }
$out += "`nSLA Item attributes with 'sla': $($requiredAttrs.Count)"
$requiredAttrs | ForEach-Object { $out += "  $($_.LogicalName) ($($_.AttributeType))" }

# Check msdyn_slakpi entity set
try {
    $r3 = (Invoke-WebRequest -Uri "$b/msdyn_slakpis?`$top=5&`$select=msdyn_slakpiid,msdyn_name" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
    $out += "`nmsdyn_slakpis records: $($r3.value.Count)"
    $r3.value | ForEach-Object { $out += "  $($_.msdyn_name) | id=$($_.msdyn_slakpiid)" }
} catch {
    $out += "`nmsdyn_slakpis error: $($_.ErrorDetails.Message)"
}

$out | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\slakpi-meta.txt" -Encoding utf8
Write-Host "Output in data\slakpi-meta.txt"
