$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$out = @()

# Search by product number prefix
$f = [System.Uri]::EscapeDataString("contains(productnumber,'ZN-') or contains(productnumber,'EK-') or contains(productnumber,'WK-')")
$r = (Invoke-WebRequest -Uri "$b/products?`$filter=$f&`$select=name,productid,productnumber,statecode&`$top=20" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
$out += "Products by number (ZN-/EK-/WK-): $($r.value.Count)"
$r.value | ForEach-Object { $out += "  $($_.productnumber) | $($_.name) | state=$($_.statecode) | id=$($_.productid)" }

# Also search by name
$f2 = [System.Uri]::EscapeDataString("contains(name,'Flush Valve') or contains(name,'ezH2O') or contains(name,'Wilkins') or contains(name,'Elkay sink') or contains(name,'Hydration')")
$r2 = (Invoke-WebRequest -Uri "$b/products?`$filter=$f2&`$select=name,productid,productnumber,statecode&`$top=20" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json
$out += "`nProducts by name keywords: $($r2.value.Count)"
$r2.value | ForEach-Object { $out += "  $($_.productnumber) | $($_.name) | state=$($_.statecode) | id=$($_.productid)" }

$out | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\product-check.txt" -Encoding utf8
Write-Host "Output written to data\product-check.txt"
