$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization" = "Bearer $token"; "Accept" = "application/json"; "OData-Version" = "4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# Check valid slaversion values
$url = "$b/EntityDefinitions(LogicalName='sla')/Attributes(LogicalName='slaversion')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?`$expand=OptionSet"
$r = (Invoke-WebRequest -Uri $url -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
$out = @("=== SLA Version Option Set ===")
$r.OptionSet.Options | ForEach-Object {
    $out += "  Value: $($_.Value) | Label: $($_.Label.UserLocalizedLabel.Label)"
}

# Check existing SLAs for reference
$slas = ((Invoke-WebRequest -Uri "$b/slas?`$select=name,slaversion,statecode&`$top=5" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
$out += "`n=== Existing SLAs ==="
$slas | ForEach-Object { $out += "  $($_.name) | ver=$($_.slaversion) | state=$($_.statecode)" }

$out | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\sla-check.txt" -Encoding utf8
Write-Host "Output written to data\sla-check.txt"
