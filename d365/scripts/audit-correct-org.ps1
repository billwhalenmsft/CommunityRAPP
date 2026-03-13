<#
.SYNOPSIS
    Audits all Zurn Elkay demo data in orgecbce8ef (Master CE Mfg) to see what exists.
#>

$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv)
if (-not $token) { Write-Host "ERROR: Could not get token for orgecbce8ef" -ForegroundColor Red; exit 1 }
$h = @{ Authorization = "Bearer $token"; Accept = "application/json" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AUDIT: orgecbce8ef.crm.dynamics.com" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- Org identity ---
Write-Host ""
Write-Host "=== Organization ===" -ForegroundColor Cyan
try {
    $org = Invoke-RestMethod -Uri "$b/organizations?`$select=name" -Headers $h -UseBasicParsing
    Write-Host "  Org Name: $($org.value[0].name)"
} catch { Write-Host "  ERROR getting org info: $_" -ForegroundColor Red }

# --- Accounts ---
Write-Host ""
Write-Host "=== Accounts ===" -ForegroundColor Cyan
$acctNames = @('Zurn Industries', 'Elkay Manufacturing', 'Ferguson Enterprises', 'HD Supply', 'Winsupply', 'F.W. Webb', 'Core & Main', 'ABC Supply', 'State Industrial', 'R.L. Deppmann', 'Eastern Industrial', 'Midwest Mechanical', 'Greenville School District', 'City of Milwaukee', 'Hilton Hotels', 'Amazon Fulfillment', 'Cedar Valley Medical', 'Riverside Community College', 'Oak Park Mall Management', 'Pine Creek Golf Club')
$foundAccts = 0
$missingAccts = @()
foreach ($n in $acctNames) {
    $enc = [System.Uri]::EscapeDataString("name eq '$($n.Replace("'","''"))'")
    try {
        $a = Invoke-RestMethod -Uri "$b/accounts?`$select=name,accountid&`$filter=$enc" -Headers $h -UseBasicParsing
        if ($a.value.Count -gt 0) {
            Write-Host "  FOUND: $n (x$($a.value.Count))" -ForegroundColor Green
            $foundAccts++
        } else {
            Write-Host "  MISSING: $n" -ForegroundColor Red
            $missingAccts += $n
        }
    } catch { Write-Host "  ERROR checking $n" -ForegroundColor Red }
}
Write-Host "  Summary: $foundAccts found, $($missingAccts.Count) missing"

# --- Contacts ---
Write-Host ""
Write-Host "=== Contacts ===" -ForegroundColor Cyan
$contactEmails = @('lisa.kume@zurnindustries.com', 'mark.jensen@zurnindustries.com', 'tom.harrison@fergusonenterprises.com', 'sarah.chen@fergusonenterprises.com', 'james.wright@hdsupply.com', 'maria.gonzalez@hdsupply.com', 'robert.kim@winsupply.com', 'jennifer.patel@fwwebb.com', 'david.nguyen@coreandmain.com', 'michael.brown@abcsupply.com', 'amanda.taylor@stateindustrial.com', 'kevin.moore@rldeppmann.com', 'patricia.lee@easternindustrial.com', 'steven.clark@midwestmechanical.com', 'john.murphy@greenschools.edu', 'carol.adams@milwaukee.gov', 'richard.baker@hilton.com', 'susan.martinez@amazon.com', 'daniel.wilson@cedarvalleymed.org', 'laura.thompson@riversidecc.edu', 'brian.johnson@oakparkmall.com', 'nancy.davis@pinecreekgolf.com', 'mike.rodriguez@elkayusa.com')
$foundContacts = 0
$missingContacts = @()
foreach ($e in $contactEmails) {
    $enc = [System.Uri]::EscapeDataString("emailaddress1 eq '$e'")
    try {
        $c = Invoke-RestMethod -Uri "$b/contacts?`$select=fullname,emailaddress1&`$filter=$enc" -Headers $h -UseBasicParsing
        if ($c.value.Count -gt 0) {
            $foundContacts++
        } else {
            Write-Host "  MISSING: $e" -ForegroundColor Red
            $missingContacts += $e
        }
    } catch {}
}
Write-Host "  Found: $foundContacts, Missing: $($missingContacts.Count)"
if ($foundContacts -gt 0) { Write-Host "  (found contacts exist)" -ForegroundColor Green }

# --- Products ---
Write-Host ""
Write-Host "=== Products ===" -ForegroundColor Cyan
foreach ($prefix in @('ZN-', 'EK-', 'WK-')) {
    $enc = [System.Uri]::EscapeDataString("startswith(productnumber,'$prefix')")
    try {
        $p = Invoke-RestMethod -Uri "$b/products?`$select=productnumber,name,statecode&`$filter=$enc&`$orderby=productnumber" -Headers $h -UseBasicParsing
        foreach ($prod in $p.value) {
            $st = if ($prod.statecode -eq 0) { 'Draft' }elseif ($prod.statecode -eq 1) { 'Active/Published' }else { $prod.statecode }
            Write-Host "  $($prod.productnumber) | $($prod.name) | $st" -ForegroundColor $(if ($prod.statecode -eq 1) { 'Green' }else { 'Yellow' })
        }
    } catch {}
}

# --- Queues ---
Write-Host ""
Write-Host "=== Zurn/Elkay Queues ===" -ForegroundColor Cyan
try {
    $q = Invoke-RestMethod -Uri "$b/queues?`$select=name,queueid&`$filter=contains(name,'Zurn') or contains(name,'Elkay')&`$orderby=name" -Headers $h -UseBasicParsing
    Write-Host "  Count: $($q.value.Count)"
    foreach ($qi in $q.value) { Write-Host "  $($qi.name)" }
} catch { Write-Host "  ERROR: $_" -ForegroundColor Red }

# --- Subjects ---
Write-Host ""
Write-Host "=== Subjects (Zurn/Elkay parented) ===" -ForegroundColor Cyan
try {
    $sub = Invoke-RestMethod -Uri "$b/subjects?`$select=title,subjectid,_parentsubject_value&`$orderby=title" -Headers $h -UseBasicParsing
    $zurnId = ($sub.value | Where-Object { $_.title -eq 'Zurn' -and -not $_._parentsubject_value }).subjectid
    $elkayId = ($sub.value | Where-Object { $_.title -eq 'Elkay' -and -not $_._parentsubject_value }).subjectid
    
    $zurnSubs = @($sub.value | Where-Object { $_._parentsubject_value -eq $zurnId })
    $elkaySubs = @($sub.value | Where-Object { $_._parentsubject_value -eq $elkayId })
    
    Write-Host "  Zurn (root): $(if($zurnId){'EXISTS'}else{'MISSING'})"
    if ($zurnSubs.Count -gt 0) { foreach ($s in $zurnSubs) { Write-Host "    - $($s.title)" } }
    Write-Host "  Elkay (root): $(if($elkayId){'EXISTS'}else{'MISSING'})"
    if ($elkaySubs.Count -gt 0) { foreach ($s in $elkaySubs) { Write-Host "    - $($s.title)" } }
    Write-Host "  Total subjects in system: $($sub.value.Count)"
} catch { Write-Host "  ERROR: $_" -ForegroundColor Red }

# --- SLA ---
Write-Host ""
Write-Host "=== SLA ===" -ForegroundColor Cyan
try {
    $sla = Invoke-RestMethod -Uri "$b/slas?`$select=name,statecode,statuscode,slaid" -Headers $h -UseBasicParsing
    Write-Host "  Total SLAs: $($sla.value.Count)"
    foreach ($s in $sla.value) {
        $st = switch ($s.statecode) { 0 { 'Draft' } 1 { 'Active' } default { $s.statecode } }
        $isZurn = if ($s.name -match 'Zurn|Elkay') { '  <<<' }else { '' }
        Write-Host "  $($s.name) | $st$isZurn"
    }
} catch { Write-Host "  ERROR: $_" -ForegroundColor Red }

# --- Cases ---
Write-Host ""
Write-Host "=== Cases (Zurn/Elkay related) ===" -ForegroundColor Cyan
$caseKeywords = @('Zurn', 'Elkay', 'Flush', 'Sensor', 'Backflow', 'Drain', 'Wilkins', 'AquaVantage', 'AquaSense', 'Ferguson', 'HD Supply', 'Winsupply')
$totalCases = 0
foreach ($kw in $caseKeywords) {
    $enc = [System.Uri]::EscapeDataString("contains(title,'$kw')")
    try {
        $cases = Invoke-RestMethod -Uri "$b/incidents?`$select=title&`$filter=$enc&`$top=100" -Headers $h -UseBasicParsing
        if ($cases.value.Count -gt 0) { $totalCases += $cases.value.Count }
    } catch {}
}
Write-Host "  Cases matching Zurn/Elkay keywords: $totalCases (may include duplicates across keywords)"

# Also get total case count
try {
    $allCases = Invoke-RestMethod -Uri "$b/incidents?`$select=incidentid&`$top=1" -Headers $h -UseBasicParsing
    # Try count
    $countUri = "$b/incidents?`$count=true&`$select=incidentid&`$top=0"
    $countResp = Invoke-RestMethod -Uri $countUri -Headers $h -UseBasicParsing
    if ($countResp.'@odata.count') { Write-Host "  Total cases in env: $($countResp.'@odata.count')" }
} catch {}

# --- Knowledge Articles ---
Write-Host ""
Write-Host "=== Knowledge Articles ===" -ForegroundColor Cyan
$kbTitles = @(
    'How to Place a Zurn Product Order Through Your Distribution Partner',
    'Distribution Network Sourcing: Stock Availability and Fulfillment',
    'Pricing, Quotes and Distributor Discount Tiers',
    'Troubleshooting Zurn AquaVantage and E-Z Flush Valve Issues',
    'Zurn AquaSense Sensor Faucet: Installation and Troubleshooting',
    'Wilkins Backflow Preventer Maintenance and Testing Guide',
    'Winterization Procedures for Zurn Plumbing Products',
    'Zurn Floor, Roof and Trench Drain Troubleshooting',
    'Case Creation Guide: Phone, Email and Web Form Intake',
    'Request Prioritization: Tier Assignment and Hot-Word Escalation',
    'Zurn Warranty Policy and RMA Process',
    'Quality and Recall Notification Procedures',
    'Rep Network Support: Ensuring Right Stock in Right Place',
    'Routing Cases to Reps: Customer Type and Territory Assignment',
    'SLA Targets and Response Time Standards'
)
$foundKb = 0
$missingKb = @()
foreach ($t in $kbTitles) {
    $enc = [System.Uri]::EscapeDataString("title eq '$($t.Replace("'","''"))'")
    try {
        $ka = Invoke-RestMethod -Uri "$b/knowledgearticles?`$select=title,statecode&`$filter=$enc" -Headers $h -UseBasicParsing
        if ($ka.value.Count -gt 0) {
            $st = switch ($ka.value[0].statecode) { 0 { 'Draft' } 1 { 'Approved' } 3 { 'Published' } default { $ka.value[0].statecode } }
            Write-Host "  FOUND ($st): $t" -ForegroundColor Green
            $foundKb++
        } else {
            Write-Host "  MISSING: $t" -ForegroundColor Red
            $missingKb += $t
        }
    } catch {}
}
Write-Host "  Summary: $foundKb found, $($missingKb.Count) missing"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AUDIT COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
