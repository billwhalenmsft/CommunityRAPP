$ErrorActionPreference = "SilentlyContinue"
$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
$ErrorActionPreference = "Stop"
$h = @{ "Authorization"="Bearer $token"; "Accept"="application/json"; "OData-Version"="4.0" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

function DvGet($url) {
    $r = Invoke-WebRequest -Uri $url -Headers $h -UseBasicParsing
    return @(($r.Content | ConvertFrom-Json).value)
}

$out = @{}

# ACCOUNTS - by name
Write-Host "Accounts..."
$acctNames = @('Zurn Industries','Elkay Manufacturing','Ferguson Enterprises','Hajoca Corporation','Winsupply Inc.','HD Supply','Wolseley Industrial Group','Consolidated Supply Co.','Pacific Plumbing Supply','Midwest Pipe and Supply','Southern Pipe and Supply','Gateway Supply Company','ABC Plumbing Wholesale','Metro Building Supply','Lakeside Plumbing Parts','Greenfield School District','City of Mesa Water Dept','Marriott Downtown Milwaukee','Johnson Residence')
$accts = @()
foreach ($n in $acctNames) {
    $ne = $n.Replace("'","''")
    $f = [System.Uri]::EscapeDataString("name eq '$ne'")
    $r = @(DvGet "$b/accounts?`$filter=$f&`$select=name,accountnumber,description,telephone1,address1_city,address1_stateorprovince&`$top=3")
    if ($r.Count -gt 0) { $accts += $r[0] }
}
$out.accounts = $accts
Write-Host "  Found: $($accts.Count)"

# CONTACTS - by email
Write-Host "Contacts..."
$emails = @('lisa.kume@zurn.com','chad.didriksen@zurn.com','darin.volpe@zurn.com','mike.schmidt@zurn.com','steve.krupp@zurn.com','tom.harrison@ferguson.com','rachel.chen@ferguson.com','mark.sullivan@hajoca.com','karen.ostrowski@winsupply.com','james.morales@hdsupply.com','sarah.tremblay@wolseley.com','david.park@consupply.com','linda.nguyen@pacificps.com','brian.kowalski@midwestpipe.com','angela.foster@southernpipe.com','eric.hammond@gatewaysupply.com','tony.reeves@abcplumbing.com','carmen.diaz@metrobldg.com','ryan.brooks@lakesideparts.com','pkelley@greenfieldsd.edu','mgutierrez@mesaaz.gov','kevin.strand@marriott.com','rjohnson247@gmail.com')
$contacts = @()
$acctNameCache = @{}
foreach ($e in $emails) {
    $f = [System.Uri]::EscapeDataString("emailaddress1 eq '$e'")
    $r = @(DvGet "$b/contacts?`$filter=$f&`$select=fullname,jobtitle,emailaddress1,telephone1,_parentcustomerid_value&`$top=1")
    if ($r.Count -gt 0) {
        $c = $r[0]
        # Resolve account name from _parentcustomerid_value
        $acctName = ""
        if ($c._parentcustomerid_value) {
            $aid = $c._parentcustomerid_value
            if ($acctNameCache.ContainsKey($aid)) {
                $acctName = $acctNameCache[$aid]
            } else {
                try {
                    $ar = Invoke-WebRequest -Uri "$b/accounts($aid)?`$select=name" -Headers $h -UseBasicParsing
                    $acctName = ($ar.Content | ConvertFrom-Json).name
                    $acctNameCache[$aid] = $acctName
                } catch { $acctName = "" }
            }
        }
        $c | Add-Member -NotePropertyName 'accountName' -NotePropertyValue $acctName -Force
        $contacts += $c
    }
}
$out.contacts = $contacts
Write-Host "  Found: $($contacts.Count)"

# PRODUCTS
Write-Host "Products..."
$products = @(DvGet "$b/products?`$filter=contains(productnumber,'ZN-') or contains(productnumber,'EK-') or contains(productnumber,'WK-')&`$select=name,productnumber,description,statecode,price&`$orderby=productnumber&`$top=50")
$out.products = $products
Write-Host "  Found: $($products.Count)"

# QUEUES
Write-Host "Queues..."
$queues = @(DvGet "$b/queues?`$filter=contains(name,'Zurn') or contains(name,'Elkay')&`$select=name,emailaddress,description&`$orderby=name&`$top=30")
$out.queues = $queues
Write-Host "  Found: $($queues.Count)"

# SUBJECTS
Write-Host "Subjects..."
$subjects = @(DvGet "$b/subjects?`$select=title,description,_parentsubject_value&`$orderby=title&`$top=100")
$zeSubs = @($subjects | Where-Object { $_.title -match 'Zurn|Elkay|Backflow|Drainage|Flush|Faucet|Hydration|Bottle|Cooler|Sink|Filter|Water|Plumbing' })
$out.subjects = $zeSubs
Write-Host "  Found: $($zeSubs.Count)"

# SLA
Write-Host "SLA..."
$slas = @(DvGet "$b/slas?`$filter=contains(name,'Zurn')&`$select=name,description,statecode,slaversion&`$top=5")
$out.slas = $slas
if ($slas.Count -gt 0) {
    $slaId = $slas[0].slaid
    $slaItems = @(DvGet "$b/slaitems?`$filter=_slaid_value eq $slaId&`$select=name,description,failureafter,warnafter&`$top=10")
    $out.slaItems = $slaItems
} else { $out.slaItems = @() }
Write-Host "  SLAs: $($slas.Count), Items: $($out.slaItems.Count)"

# PRICE LISTS
Write-Host "Price Lists..."
$priceLists = @(DvGet "$b/pricelevels?`$filter=contains(name,'Zurn') or contains(name,'Elkay')&`$select=name,description,statecode&`$top=10")
$out.priceLists = $priceLists
Write-Host "  Found: $($priceLists.Count)"

# CASES
Write-Host "Cases..."
$allCases = @()
foreach ($t in @('Ferguson','Hajoca','Winsupply','Wolseley','Consolidated','Pacific','Midwest','Southern','Gateway','Greenfield','Marriott','Homeowner','URGENT','EMERGENCY','Lakeside','Metro Building','ABC Plumbing','HD Supply','City of Mesa','Johnson')) {
    $f = [System.Uri]::EscapeDataString("contains(title,'$t')")
    try {
        $r = @(DvGet "$b/incidents?`$filter=$f&`$select=title,statecode,statuscode,prioritycode,caseorigincode,ticketnumber,createdon&`$top=50")
        foreach ($c in $r) {
            $found = $false; foreach ($e in $allCases) { if ($e.incidentid -eq $c.incidentid) { $found = $true; break } }
            if (-not $found) { $allCases += $c }
        }
    } catch {}
}
$out.cases = $allCases
Write-Host "  Found: $($allCases.Count)"

# CALENDAR
Write-Host "Calendar..."
$cals = @(DvGet "$b/calendars?`$filter=contains(name,'Zurn')&`$select=name,description&`$top=5")
$out.calendars = $cals
Write-Host "  Found: $($cals.Count)"

$out | ConvertTo-Json -Depth 5 | Out-File "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo\data\report-data.json" -Encoding utf8
Write-Host "`nAll data saved to data\report-data.json"
