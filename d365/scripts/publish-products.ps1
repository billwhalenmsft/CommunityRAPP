$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
if (-not $token) { Write-Host "FAILED to get token"; exit 1 }
$h = @{ "Authorization" = "Bearer $token"; "Accept" = "application/json"; "OData-Version" = "4.0"; "Content-Type" = "application/json" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# Get our products by product number prefix (ZN-, EK-, WK-)
$f = [System.Uri]::EscapeDataString("contains(productnumber,'ZN-') or contains(productnumber,'EK-') or contains(productnumber,'WK-')")
$r = Invoke-WebRequest -Uri "$b/products?`$filter=$f&`$select=name,productid,productnumber,statecode&`$top=20" -Headers $h -UseBasicParsing
$products = ($r.Content | ConvertFrom-Json).value

Write-Host "Found $($products.Count) Zurn/Elkay products" -ForegroundColor Cyan

$published = 0
$failed = 0
$alreadyActive = 0
foreach ($p in $products) {
    if ($p.statecode -ne 0) { $alreadyActive++; continue }
    try {
        $publishUrl = "$b/products($($p.productid))/Microsoft.Dynamics.CRM.PublishProductHierarchy"
        Invoke-WebRequest -Uri $publishUrl -Method Post -Headers $h -UseBasicParsing -ErrorAction Stop | Out-Null
        Write-Host "  Published: $($p.name)" -ForegroundColor Green
        $published++
    } catch {
        $errMsg = $_.ErrorDetails.Message
        if ($errMsg -match "published|active|already") {
            Write-Host "  Already active: $($p.name)" -ForegroundColor DarkGray
        } else {
            Write-Host "  FAILED: $($p.name) - $($_.Exception.Message)" -ForegroundColor Red
            $failed++
        }
    }
}

Write-Host "`nPublished: $published | Already active: $alreadyActive | Failed: $failed" -ForegroundColor Cyan
