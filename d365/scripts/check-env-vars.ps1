$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization" = "Bearer $token"; "Accept" = "application/json"; "OData-Version" = "4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# Get publishers
Write-Host "=== Publishers ==="
$r = Invoke-WebRequest -Uri "$b/publishers?`$select=friendlyname,uniquename,customizationprefix&`$top=20" -Headers $h -UseBasicParsing
$pubs = @(($r.Content | ConvertFrom-Json).value)
$pubs | ForEach-Object { Write-Host "  $($_.friendlyname) | unique=$($_.uniquename) | prefix=$($_.customizationprefix)" }

# Get existing environment variable definitions  
Write-Host "`n=== Existing Environment Variables ==="
$r2 = Invoke-WebRequest -Uri "$b/environmentvariabledefinitions?`$select=schemaname,displayname,type&`$orderby=schemaname&`$top=50" -Headers $h -UseBasicParsing
$evs = @(($r2.Content | ConvertFrom-Json).value)
Write-Host "Total env vars: $($evs.Count)"
$evs | ForEach-Object { Write-Host "  $($_.schemaname) | $($_.displayname) | type=$($_.type)" }

# Check for the specific missing ones
Write-Host "`n=== Missing Variables (bw_ prefixed) ==="
$missing = @('bw_SPEECH_REGION', 'bw_SPEECH_KEY', 'bw_CopilotStudioTenantID', 'bw_AzureSpeechKey', 'bw_AzureOpenAIModel', 'bw_AzureOpenAIDeploymentName', 'bw_AzureOpenAIAPIKey', 'bw_AZURE_SPEECH_REGION', 'bw_AZURE_OPENAI_ENDPOINT')
foreach ($m in $missing) {
    $found = $evs | Where-Object { $_.schemaname -eq $m }
    if ($found) { Write-Host "  EXISTS: $m" } else { Write-Host "  MISSING: $m" }
}
