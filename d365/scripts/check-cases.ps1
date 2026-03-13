$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$out = @()

# Get all our cases (ones that contain Zurn/Elkay related titles)
$titles = @('Ferguson','Hajoca','Winsupply','HD Supply','Wolseley','Consolidated Supply','Pacific Plumbing','Midwest Pipe','Southern Pipe','Gateway Supply','ABC Plumbing','Metro Building','Lakeside Parts','Greenfield SD','City of Mesa','Marriott Milwaukee','Homeowner','Johnson Residence','URGENT','EMERGENCY')

$allCases = @()
foreach ($t in @('Ferguson','Hajoca','Winsupply','Wolseley','Consolidated','Pacific','Midwest','Southern','Gateway','Greenfield','Marriott','Homeowner','URGENT','EMERGENCY','Lakeside','Metro Building','ABC Plumbing','HD Supply','City of Mesa')) {
    $f = [System.Uri]::EscapeDataString("contains(title,'$t')")
    $r = ((Invoke-WebRequest -Uri "$b/incidents?`$filter=$f&`$select=title,statecode,statuscode,prioritycode&`$top=20" -Headers $h -UseBasicParsing).Content | ConvertFrom-Json).value
    foreach ($c in $r) {
        if ($allCases.title -notcontains $c.title) { $allCases += $c }
    }
}

$out += "Total Zurn/Elkay Cases: $($allCases.Count)"
$active = @($allCases | Where-Object { $_.statecode -eq 0 })
$resolved = @($allCases | Where-Object { $_.statecode -eq 1 })
$cancelled = @($allCases | Where-Object { $_.statecode -eq 2 })
$out += "Active: $($active.Count) | Resolved: $($resolved.Count) | Cancelled: $($cancelled.Count)"

$out += "`n--- Active Cases ---"
$active | ForEach-Object { $out += "  [$($_.prioritycode)] $($_.title)" }

$out += "`n--- Resolved Cases ---"
$resolved | ForEach-Object { $out += "  $($_.title)" }

$out | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\cases-status.txt" -Encoding utf8
Write-Host "Output in data\cases-status.txt"
