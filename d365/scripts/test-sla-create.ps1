$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization" = "Bearer $token"; "Accept" = "application/json"; "OData-Version" = "4.0"; "Content-Type" = "application/json; charset=utf-8"; "Prefer" = "return=representation" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$body = @{
    name             = 'Zurn Elkay Standard SLA'
    description      = 'Zurn Elkay CS SLA. First Response: 4h, Resolution: 8h business hours.'
    applicablefrom   = 'createdon'
    objecttypecode   = 112
    primaryentityotc = 112
    slaversion       = 100000001
} | ConvertTo-Json -Depth 5

try {
    $r = Invoke-WebRequest -Uri "$b/slas" -Method Post -Headers $h -Body $body -UseBasicParsing -ErrorAction Stop
    Write-Host "SUCCESS - Status: $($r.StatusCode)"
    $parsed = $r.Content | ConvertFrom-Json
    Write-Host "SLA ID: $($parsed.slaid)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) {
        Write-Host "DETAILS: $($_.ErrorDetails.Message)"
    }
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $reader.BaseStream.Position = 0
        $responseBody = $reader.ReadToEnd()
        Write-Host "RESPONSE BODY: $responseBody"
    }
}
