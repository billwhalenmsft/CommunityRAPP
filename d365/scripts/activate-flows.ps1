$orgUrl = "https://orgecbce8ef.crm.dynamics.com"
$apiUrl = "$orgUrl/api/data/v9.2"
$token = az account get-access-token --resource $orgUrl --query accessToken -o tsv
$headers = @{
    Authorization      = "Bearer $token"
    Accept             = "application/json"
    "Content-Type"     = "application/json; charset=utf-8"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

# Query inactive QEA/KM flows
$filter = "(contains(name,'QEA') or contains(name,'Knowledge Harvest') or contains(name,'Expire evaluation') or contains(name,'AI Evaluation')) and statecode eq 0"
$uri = "$apiUrl/workflows?`$filter=$filter&`$select=workflowid,name"
$inactive = (Invoke-RestMethod -Uri $uri -Headers $headers).value

Write-Host "Found $($inactive.Count) inactive flow(s):" -ForegroundColor Cyan
foreach ($flow in $inactive) {
    Write-Host "  Activating: $($flow.name)" -NoNewline
    try {
        $body = '{"statecode":1,"statuscode":2}'
        Invoke-RestMethod -Uri "$apiUrl/workflows($($flow.workflowid))" -Method Patch -Headers $headers -Body $body
        Write-Host " -> Done" -ForegroundColor Green
    } catch {
        $detail = if ($_.ErrorDetails.Message) { ($_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue).error.message } else { $_.Exception.Message }
        Write-Host " -> FAILED: $detail" -ForegroundColor Red
    }
}

# Verify all flows are now active
Write-Host "`nVerifying all QEA/KM flows:" -ForegroundColor Cyan
$allFilter = "contains(name,'QEA') or contains(name,'Knowledge Harvest') or contains(name,'Expire evaluation') or contains(name,'AI Evaluation')"
$allFlows = (Invoke-RestMethod -Uri "$apiUrl/workflows?`$filter=$allFilter&`$select=workflowid,name,statecode,statuscode" -Headers $headers).value
foreach ($f in $allFlows) {
    $status = if ($f.statecode -eq 1) { "ACTIVE" } else { "OFF" }
    $color = if ($f.statecode -eq 1) { "Green" } else { "Red" }
    Write-Host "  [$status] $($f.name)" -ForegroundColor $color
}
