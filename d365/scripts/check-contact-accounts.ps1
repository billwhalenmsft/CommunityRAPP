$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

$emails = @('lisa.kume@zurn.com','chad.didriksen@zurn.com','darin.volpe@zurn.com','mike.schmidt@zurn.com','steve.krupp@zurn.com','tom.harrison@ferguson.com','rachel.chen@ferguson.com','mark.sullivan@hajoca.com','karen.ostrowski@winsupply.com','james.morales@hdsupply.com','sarah.tremblay@wolseley.com','david.park@consupply.com','linda.nguyen@pacificps.com','brian.kowalski@midwestpipe.com','angela.foster@southernpipe.com','eric.hammond@gatewaysupply.com','tony.reeves@abcplumbing.com','carmen.diaz@metrobldg.com','ryan.brooks@lakesideparts.com','pkelley@greenfieldsd.edu','mgutierrez@mesaaz.gov','kevin.strand@marriott.com','rjohnson247@gmail.com')

# Collect unique account IDs from contacts
$acctIds = @{}
foreach ($e in $emails) {
    $f = [System.Uri]::EscapeDataString("emailaddress1 eq '$e'")
    $r = Invoke-WebRequest -Uri "$b/contacts?`$filter=$f&`$select=fullname,_parentcustomerid_value&`$top=1" -Headers $h -UseBasicParsing
    $v = @(($r.Content | ConvertFrom-Json).value)
    if ($v.Count -gt 0 -and $v[0]._parentcustomerid_value) {
        $aid = $v[0]._parentcustomerid_value
        if (-not $acctIds.ContainsKey($aid)) { $acctIds[$aid] = @() }
        $acctIds[$aid] += $v[0].fullname
    }
}

Write-Host "Unique account IDs referenced by contacts: $($acctIds.Count)"
Write-Host ""

# Now look up each account
foreach ($aid in $acctIds.Keys) {
    try {
        $r = Invoke-WebRequest -Uri "$b/accounts($aid)?`$select=name,accountid" -Headers $h -UseBasicParsing
        $a = $r.Content | ConvertFrom-Json
        Write-Host "Account: $($a.name) ($aid)"
    } catch {
        Write-Host "MISSING ACCOUNT: $aid" -ForegroundColor Red
    }
    foreach ($cn in $acctIds[$aid]) {
        Write-Host "  -> $cn"
    }
}

# Also check: accounts from our report that DON'T match
$reportAccts = Get-Content "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\report-data.json" -Raw | ConvertFrom-Json
Write-Host "`nReport account IDs:"
foreach ($a in $reportAccts.accounts) {
    $inContacts = $acctIds.ContainsKey($a.accountid)
    $marker = if ($inContacts) { "USED" } else { "----" }
    Write-Host "  $marker | $($a.name) | $($a.accountid)"
}
