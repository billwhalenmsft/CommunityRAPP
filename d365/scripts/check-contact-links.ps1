$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# Email -> expected account name mapping
$contactMap = @(
    @{ email='lisa.kume@zurn.com';           acct='Zurn Industries' },
    @{ email='chad.didriksen@zurn.com';      acct='Zurn Industries' },
    @{ email='darin.volpe@zurn.com';         acct='Zurn Industries' },
    @{ email='mike.schmidt@zurn.com';        acct='Zurn Industries' },
    @{ email='steve.krupp@zurn.com';         acct='Zurn Industries' },
    @{ email='tom.harrison@ferguson.com';    acct='Ferguson Enterprises' },
    @{ email='rachel.chen@ferguson.com';     acct='Ferguson Enterprises' },
    @{ email='mark.sullivan@hajoca.com';     acct='Hajoca Corporation' },
    @{ email='karen.ostrowski@winsupply.com'; acct='Winsupply Inc.' },
    @{ email='james.morales@hdsupply.com';   acct='HD Supply' },
    @{ email='sarah.tremblay@wolseley.com';  acct='Wolseley Industrial Group' },
    @{ email='david.park@consupply.com';     acct='Consolidated Supply Co.' },
    @{ email='linda.nguyen@pacificps.com';   acct='Pacific Plumbing Supply' },
    @{ email='brian.kowalski@midwestpipe.com'; acct='Midwest Pipe and Supply' },
    @{ email='angela.foster@southernpipe.com'; acct='Southern Pipe and Supply' },
    @{ email='eric.hammond@gatewaysupply.com'; acct='Gateway Supply Company' },
    @{ email='tony.reeves@abcplumbing.com';  acct='ABC Plumbing Wholesale' },
    @{ email='carmen.diaz@metrobldg.com';    acct='Metro Building Supply' },
    @{ email='ryan.brooks@lakesideparts.com'; acct='Lakeside Plumbing Parts' },
    @{ email='pkelley@greenfieldsd.edu';     acct='Greenfield School District' },
    @{ email='mgutierrez@mesaaz.gov';        acct='City of Mesa Water Dept' },
    @{ email='kevin.strand@marriott.com';    acct='Marriott Downtown Milwaukee' },
    @{ email='rjohnson247@gmail.com';        acct='Johnson Residence' }
)

Write-Host "Checking contact-to-account links..."
Write-Host ""

$linked = 0
$unlinked = 0
$notFound = 0
$unlinkedList = @()

foreach ($c in $contactMap) {
    $f = [System.Uri]::EscapeDataString("emailaddress1 eq '$($c.email)'")
    $r = Invoke-WebRequest -Uri "$b/contacts?`$filter=$f&`$select=fullname,contactid,_parentcustomerid_value&`$top=1" -Headers $h -UseBasicParsing
    $v = @(($r.Content | ConvertFrom-Json).value)
    if ($v.Count -gt 0) {
        if ($v[0]._parentcustomerid_value) {
            Write-Host "  OK    | $($v[0].fullname) -> linked" -ForegroundColor Green
            $linked++
        } else {
            Write-Host "  MISS  | $($v[0].fullname) -> NO ACCOUNT (should be: $($c.acct))" -ForegroundColor Yellow
            $unlinked++
            $unlinkedList += @{ contactId=$v[0].contactid; fullname=$v[0].fullname; acctName=$c.acct; email=$c.email }
        }
    } else {
        Write-Host "  GONE  | $($c.email) -> not found in environment" -ForegroundColor Red
        $notFound++
    }
}

Write-Host ""
Write-Host "Summary: Linked=$linked | Unlinked=$unlinked | Not Found=$notFound"

# Save unlinked for fix script
$unlinkedList | ConvertTo-Json -Depth 3 | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\unlinked-contacts.json" -Encoding utf8
Write-Host "Unlinked contacts saved to data\unlinked-contacts.json"
