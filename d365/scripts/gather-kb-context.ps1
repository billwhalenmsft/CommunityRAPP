$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv)
$h = @{ Authorization = "Bearer $token"; Accept = "application/json" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

Write-Host "=== Zurn Products ===" -ForegroundColor Cyan
$zp = Invoke-RestMethod -Uri "$b/products?`$select=name,productnumber,description,statuscode&`$filter=startswith(productnumber,'ZN-') or startswith(productnumber,'WK-')&`$orderby=productnumber" -Headers $h -UseBasicParsing
foreach($p in $zp.value){ Write-Host "  $($p.productnumber) | $($p.name) | $($p.description)" }

Write-Host ""
Write-Host "=== Elkay Products ===" -ForegroundColor Cyan
$ep = Invoke-RestMethod -Uri "$b/products?`$select=name,productnumber,description,statuscode&`$filter=startswith(productnumber,'EK-')&`$orderby=productnumber" -Headers $h -UseBasicParsing
foreach($p in $ep.value){ Write-Host "  $($p.productnumber) | $($p.name) | $($p.description)" }

Write-Host ""
Write-Host "=== Accounts (Distributor/Rep/End-User) ===" -ForegroundColor Cyan
$names = @('Ferguson','HD Supply','Winsupply','F.W. Webb','Core & Main','ABC Supply','State Industrial','R.L. Deppmann','Eastern Industrial','Midwest Mechanical','Zurn','Elkay')
foreach($n in $names){
    $enc = [System.Uri]::EscapeDataString("name eq '$n' or startswith(name,'$n')")
    try {
        $a = Invoke-RestMethod -Uri "$b/accounts?`$select=name,accountid,customertypecode&`$filter=contains(name,'$n')&`$top=3" -Headers $h -UseBasicParsing
        foreach($ac in $a.value){ 
            $typ = switch($ac.customertypecode){ 1{'Customer'} 2{'Prospect'} 3{'Vendor'} 4{'Partner'} 5{'Competitor'} 6{'Consultant'} 11{'Distributor'} 12{'Rep/Agent'} default{$ac.customertypecode} }
            Write-Host "  $($ac.name) | Type=$typ | ID=$($ac.accountid)" 
        }
    } catch {}
}

Write-Host ""
Write-Host "=== Subjects ===" -ForegroundColor Cyan
$sub = Invoke-RestMethod -Uri "$b/subjects?`$select=title,subjectid&`$orderby=title" -Headers $h -UseBasicParsing
foreach($s in $sub.value){ Write-Host "  $($s.title)" }

Write-Host ""
Write-Host "=== KB Article Entity Check ===" -ForegroundColor Cyan
try {
    $ka = Invoke-RestMethod -Uri "$b/knowledgearticles?`$select=title,articlepublicnumber,statecode&`$top=5" -Headers $h -UseBasicParsing
    Write-Host "  Existing articles: $($ka.value.Count) (sample)"
    foreach($k in $ka.value){ 
        $st = switch($k.statecode){ 0{'Draft'} 1{'Approved'} 2{'Scheduled'} 3{'Published'} 4{'Expired'} 5{'Archived'} default{$k.statecode} }
        Write-Host "    $($k.title) | State=$st" 
    }
    # Get total count
    $total = Invoke-RestMethod -Uri "$b/knowledgearticles?`$select=knowledgearticleid&`$count=true" -Headers $h -UseBasicParsing
    Write-Host "  Total articles in system: $($total.'@odata.count')"
} catch { Write-Host "  Error: $_" }

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
