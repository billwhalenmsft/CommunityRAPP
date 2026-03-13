<#
.SYNOPSIS
    Finds and removes duplicate records in orgecbce8ef.crm.dynamics.com
.DESCRIPTION
    Scans accounts, contacts, subjects, queues, products, SLAs, cases, 
    and knowledge articles for duplicates. Keeps the record that contacts/cases 
    reference (or the older record if no references), deletes the rest.
#>

$ErrorActionPreference = "Continue"

$token = az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv
$h = @{ Authorization = "Bearer $token"; Accept = "application/json" }
$base = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

function DV-Get([string]$url) {
    $r = Invoke-RestMethod -Uri $url -Headers $h -UseBasicParsing
    return $r.value
}

function DV-Delete([string]$url) {
    Invoke-RestMethod -Uri $url -Method Delete -Headers $h -UseBasicParsing
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Magenta
Write-Host "  DUPLICATE RECORD CLEANUP - orgecbce8ef.crm.dynamics.com" -ForegroundColor Magenta
Write-Host ("=" * 70) -ForegroundColor Magenta
Write-Host ""

$totalDeleted = 0

# ============================================================
# 1. DUPLICATE ACCOUNTS
# ============================================================
Write-Host "--- ACCOUNTS ---" -ForegroundColor Cyan
$acctNames = @(
    "Zurn Industries","Elkay Manufacturing","Ferguson Enterprises",
    "Hajoca Corporation","Winsupply Inc.","HD Supply",
    "Wolseley Industrial Group","Consolidated Supply Co.",
    "Pacific Plumbing Supply","Midwest Pipe & Supply",
    "Southern Pipe & Supply","Gateway Supply Company",
    "ABC Plumbing Wholesale","Metro Building Supply",
    "Lakeside Plumbing Parts","Greenfield School District",
    "City of Mesa Water Dept","Marriott Downtown Milwaukee",
    "Johnson Residence","ABC Supply"
)

foreach ($n in $acctNames) {
    $safe = $n -replace "'","''"
    $filter = [System.Uri]::EscapeDataString("name eq '$safe'")
    $accts = DV-Get "$base/accounts?`$filter=$filter&`$select=name,accountid,createdon"
    if ($accts.Count -gt 1) {
        Write-Host "  DUPLICATE: $n ($($accts.Count) records)" -ForegroundColor Red

        # Find which account has contacts linked to it
        $keepId = $null
        foreach ($a in $accts) {
            $cFilter = [System.Uri]::EscapeDataString("_parentcustomerid_value eq '$($a.accountid)'")
            $contacts = DV-Get "$base/contacts?`$filter=$cFilter&`$select=contactid&`$top=1"
            if ($contacts.Count -gt 0) {
                $keepId = $a.accountid
                break
            }
        }
        # If no contacts reference any, keep the oldest
        if (-not $keepId) {
            $keepId = ($accts | Sort-Object createdon | Select-Object -First 1).accountid
        }

        foreach ($a in $accts) {
            if ($a.accountid -ne $keepId) {
                Write-Host "    Deleting: $($a.accountid) (created $($a.createdon))" -ForegroundColor Yellow
                try {
                    # First reassign any cases pointing to this account
                    $caseFilter = [System.Uri]::EscapeDataString("_customerid_value eq '$($a.accountid)'")
                    $cases = DV-Get "$base/incidents?`$filter=$caseFilter&`$select=incidentid,title"
                    foreach ($case in $cases) {
                        Write-Host "      Reassigning case: $($case.title)" -ForegroundColor DarkGray
                        $patchBody = @{ "customerid_account@odata.bind" = "/accounts($keepId)" } | ConvertTo-Json
                        Invoke-RestMethod -Uri "$base/incidents($($case.incidentid))" -Method Patch -Headers (@{ Authorization = "Bearer $token"; Accept = "application/json"; "Content-Type" = "application/json" }) -Body ([System.Text.Encoding]::UTF8.GetBytes($patchBody)) -UseBasicParsing
                    }
                    # Reassign contacts
                    $contFilter = [System.Uri]::EscapeDataString("_parentcustomerid_value eq '$($a.accountid)'")
                    $conts = DV-Get "$base/contacts?`$filter=$contFilter&`$select=contactid,fullname"
                    foreach ($cont in $conts) {
                        Write-Host "      Reassigning contact: $($cont.fullname)" -ForegroundColor DarkGray
                        $patchBody = @{ "parentcustomerid_account@odata.bind" = "/accounts($keepId)" } | ConvertTo-Json
                        Invoke-RestMethod -Uri "$base/contacts($($cont.contactid))" -Method Patch -Headers (@{ Authorization = "Bearer $token"; Accept = "application/json"; "Content-Type" = "application/json" }) -Body ([System.Text.Encoding]::UTF8.GetBytes($patchBody)) -UseBasicParsing
                    }
                    DV-Delete "$base/accounts($($a.accountid))"
                    $totalDeleted++
                    Write-Host "    Deleted." -ForegroundColor Green
                } catch {
                    Write-Warning "    Failed to delete $($a.accountid): $($_.Exception.Message)"
                }
            } else {
                Write-Host "    Keeping:  $($a.accountid) (has references)" -ForegroundColor DarkGray
            }
        }
    }
}

# ============================================================
# 2. DUPLICATE CONTACTS
# ============================================================
Write-Host "`n--- CONTACTS ---" -ForegroundColor Cyan
$emails = @(
    "lisa.kume@zurnelkay.com","chad.didriksen@zurnelkay.com",
    "darin.volpe@zurnelkay.com","mike.schmidt@zurnelkay.com",
    "steve.krupp@zurnelkay.com","tom.harrison@ferguson.com",
    "rachel.chen@ferguson.com","mark.sullivan@hajoca.com",
    "karen.ostrowski@winsupply.com","james.morales@hdsupply.com",
    "sarah.tremblay@wolseley.com","david.park@consupply.com",
    "linda.nguyen@pacificps.com","brian.kowalski@midwestpipe.com",
    "angela.foster@southernpipe.com","eric.hammond@gatewaysupply.com",
    "tony.reeves@abcplumbing.com","carmen.diaz@metrobldg.com",
    "ryan.brooks@lakesideparts.com","pkelley@greenfieldsd.edu",
    "mgutierrez@mesaaz.gov","kevin.strand@marriott.com",
    "rjohnson247@gmail.com"
)

foreach ($email in $emails) {
    $filter = [System.Uri]::EscapeDataString("emailaddress1 eq '$email'")
    $contacts = DV-Get "$base/contacts?`$filter=$filter&`$select=contactid,fullname,emailaddress1,createdon"
    if ($contacts.Count -gt 1) {
        Write-Host "  DUPLICATE: $email ($($contacts.Count) records)" -ForegroundColor Red
        # Keep oldest
        $sorted = $contacts | Sort-Object createdon
        $keepId = $sorted[0].contactid
        for ($i = 1; $i -lt $sorted.Count; $i++) {
            $c = $sorted[$i]
            Write-Host "    Deleting: $($c.contactid) ($($c.fullname), created $($c.createdon))" -ForegroundColor Yellow
            try {
                # Reassign cases referencing this contact
                $caseFilter = [System.Uri]::EscapeDataString("_primarycontactid_value eq '$($c.contactid)'")
                $cases = DV-Get "$base/incidents?`$filter=$caseFilter&`$select=incidentid,title"
                foreach ($case in $cases) {
                    Write-Host "      Reassigning case contact: $($case.title)" -ForegroundColor DarkGray
                    $patchBody = @{ "primarycontactid@odata.bind" = "/contacts($keepId)" } | ConvertTo-Json
                    Invoke-RestMethod -Uri "$base/incidents($($case.incidentid))" -Method Patch -Headers (@{ Authorization = "Bearer $token"; Accept = "application/json"; "Content-Type" = "application/json" }) -Body ([System.Text.Encoding]::UTF8.GetBytes($patchBody)) -UseBasicParsing
                }
                DV-Delete "$base/contacts($($c.contactid))"
                $totalDeleted++
                Write-Host "    Deleted." -ForegroundColor Green
            } catch {
                Write-Warning "    Failed to delete contact $($c.contactid): $($_.Exception.Message)"
            }
        }
        Write-Host "    Keeping:  $keepId ($($sorted[0].fullname))" -ForegroundColor DarkGray
    }
}

# ============================================================
# 3. DUPLICATE SUBJECTS
# ============================================================
Write-Host "`n--- SUBJECTS ---" -ForegroundColor Cyan
$subjNames = @(
    "Zurn","Elkay","Order Management","Logistics & Shipping",
    "Technical Support","Warranty & Returns","Pricing & Quotes",
    "Product Information","Backflow / Wilkins","Drainage",
    "Quality / Recall","Hydration Products","Sinks & Fixtures",
    "Filters & Replacement"
)

foreach ($s in $subjNames) {
    $safe = $s -replace "'","''"
    $filter = [System.Uri]::EscapeDataString("title eq '$safe'")
    $subjs = DV-Get "$base/subjects?`$filter=$filter&`$select=subjectid,title,createdon,_parentsubject_value"
    if ($subjs.Count -gt 1) {
        Write-Host "  DUPLICATE: $s ($($subjs.Count) records)" -ForegroundColor Red
        # Keep the one with children/references, or oldest
        $keepId = ($subjs | Sort-Object createdon | Select-Object -First 1).subjectid
        foreach ($subj in $subjs) {
            if ($subj.subjectid -ne $keepId) {
                Write-Host "    Deleting: $($subj.subjectid)" -ForegroundColor Yellow
                try {
                    DV-Delete "$base/subjects($($subj.subjectid))"
                    $totalDeleted++
                    Write-Host "    Deleted." -ForegroundColor Green
                } catch {
                    Write-Warning "    Failed: $($_.Exception.Message)"
                }
            } else {
                Write-Host "    Keeping:  $($subj.subjectid)" -ForegroundColor DarkGray
            }
        }
    }
}

# ============================================================
# 4. DUPLICATE QUEUES
# ============================================================
Write-Host "`n--- QUEUES ---" -ForegroundColor Cyan
$queueNames = @(
    "Apps-Eng-CB Email","Commercial Email","Consumer","Drainage",
    "eCommerce","General Support","Install Care","PVF/Hydro Retail",
    "Zurn Phone - Tier 1","Zurn Phone - General","Zurn Phone - Tech Support",
    "Zurn Phone - Backflow/Wilkins","Elkay Hydration Support",
    "Elkay Sinks & Fixtures","Elkay General Support","Elkay Orders",
    "Elkay Phone - General","Elkay Phone - Tech"
)

foreach ($q in $queueNames) {
    $safe = $q -replace "'","''"
    $filter = [System.Uri]::EscapeDataString("name eq '$safe'")
    $queues = DV-Get "$base/queues?`$filter=$filter&`$select=queueid,name,createdon"
    if ($queues.Count -gt 1) {
        Write-Host "  DUPLICATE: $q ($($queues.Count) records)" -ForegroundColor Red
        $sorted = $queues | Sort-Object createdon
        $keepId = $sorted[0].queueid
        for ($i = 1; $i -lt $sorted.Count; $i++) {
            Write-Host "    Deleting: $($sorted[$i].queueid)" -ForegroundColor Yellow
            try {
                DV-Delete "$base/queues($($sorted[$i].queueid))"
                $totalDeleted++
                Write-Host "    Deleted." -ForegroundColor Green
            } catch {
                Write-Warning "    Failed: $($_.Exception.Message)"
            }
        }
        Write-Host "    Keeping:  $keepId" -ForegroundColor DarkGray
    }
}

# ============================================================
# 5. DUPLICATE PRODUCTS
# ============================================================
Write-Host "`n--- PRODUCTS ---" -ForegroundColor Cyan
$prodNumbers = @(
    "ZN-AV-1001","ZN-EZ-1002","ZN-UR-1003","ZN-SF-2001","ZN-AS-2002",
    "ZN-FD-3001","ZN-TD-3002","ZN-RD-3003","WK-RP-4001","WK-DC-4002",
    "EK-BF-5001","EK-WC-5002","EK-DF-5003","EK-SS-6001","EK-UM-6002","EK-FL-6003"
)

foreach ($pn in $prodNumbers) {
    $filter = [System.Uri]::EscapeDataString("productnumber eq '$pn'")
    $prods = DV-Get "$base/products?`$filter=$filter&`$select=productid,name,productnumber,createdon"
    if ($prods.Count -gt 1) {
        Write-Host "  DUPLICATE: $pn ($($prods.Count) records)" -ForegroundColor Red
        $sorted = $prods | Sort-Object createdon
        $keepId = $sorted[0].productid
        for ($i = 1; $i -lt $sorted.Count; $i++) {
            Write-Host "    Deleting: $($sorted[$i].productid) ($($sorted[$i].name))" -ForegroundColor Yellow
            try {
                DV-Delete "$base/products($($sorted[$i].productid))"
                $totalDeleted++
                Write-Host "    Deleted." -ForegroundColor Green
            } catch {
                Write-Warning "    Failed: $($_.Exception.Message)"
            }
        }
        Write-Host "    Keeping:  $keepId" -ForegroundColor DarkGray
    }
}

# ============================================================
# 6. DUPLICATE CASES (same title)
# ============================================================
Write-Host "`n--- CASES (duplicate titles) ---" -ForegroundColor Cyan
$filter = [System.Uri]::EscapeDataString("contains(title,'Zurn') or contains(title,'Elkay') or contains(title,'Ferguson') or contains(title,'Hajoca') or contains(title,'Winsupply') or contains(title,'HD Supply') or contains(title,'Wolseley') or contains(title,'Consolidated') or contains(title,'Pacific') or contains(title,'Midwest') or contains(title,'Southern') or contains(title,'Gateway') or contains(title,'ABC') or contains(title,'Metro') or contains(title,'Lakeside') or contains(title,'Greenfield') or contains(title,'Mesa') or contains(title,'Marriott') or contains(title,'Homeowner') or contains(title,'URGENT') or contains(title,'EMERGENCY')")
$allCases = DV-Get "$base/incidents?`$filter=$filter&`$select=incidentid,title,createdon,statecode&`$orderby=title,createdon"

# Group by title
$caseGroups = @{}
foreach ($c in $allCases) {
    if (-not $caseGroups.ContainsKey($c.title)) {
        $caseGroups[$c.title] = @()
    }
    $caseGroups[$c.title] += $c
}

foreach ($title in $caseGroups.Keys) {
    $group = $caseGroups[$title]
    if ($group.Count -gt 1) {
        Write-Host "  DUPLICATE CASE: $($title.Substring(0, [Math]::Min(60, $title.Length)))... ($($group.Count) records)" -ForegroundColor Red
        $sorted = $group | Sort-Object createdon
        $keepId = $sorted[0].incidentid
        for ($i = 1; $i -lt $sorted.Count; $i++) {
            $c = $sorted[$i]
            Write-Host "    Deleting: $($c.incidentid) (created $($c.createdon))" -ForegroundColor Yellow
            try {
                DV-Delete "$base/incidents($($c.incidentid))"
                $totalDeleted++
                Write-Host "    Deleted." -ForegroundColor Green
            } catch {
                Write-Warning "    Failed: $($_.Exception.Message)"
            }
        }
        Write-Host "    Keeping:  $keepId" -ForegroundColor DarkGray
    }
}

# ============================================================
# 7. DUPLICATE KNOWLEDGE ARTICLES  
# ============================================================
Write-Host "`n--- KNOWLEDGE ARTICLES ---" -ForegroundColor Cyan
$filter = [System.Uri]::EscapeDataString("contains(title,'Zurn') or contains(title,'Elkay') or contains(title,'Wilkins') or contains(title,'Backflow') or contains(title,'Distributor') or contains(title,'Warranty') or contains(title,'SLA')")
$kbs = DV-Get "$base/knowledgearticles?`$filter=$filter&`$select=knowledgearticleid,title,createdon,articlepublicnumber&`$orderby=title,createdon"

$kbGroups = @{}
foreach ($kb in $kbs) {
    if (-not $kbGroups.ContainsKey($kb.title)) {
        $kbGroups[$kb.title] = @()
    }
    $kbGroups[$kb.title] += $kb
}

foreach ($title in $kbGroups.Keys) {
    $group = $kbGroups[$title]
    if ($group.Count -gt 1) {
        Write-Host "  DUPLICATE KB: $($title.Substring(0, [Math]::Min(55, $title.Length)))... ($($group.Count) records)" -ForegroundColor Red
        $sorted = $group | Sort-Object createdon
        $keepId = $sorted[0].knowledgearticleid
        for ($i = 1; $i -lt $sorted.Count; $i++) {
            Write-Host "    Deleting: $($sorted[$i].knowledgearticleid)" -ForegroundColor Yellow
            try {
                DV-Delete "$base/knowledgearticles($($sorted[$i].knowledgearticleid))"
                $totalDeleted++
                Write-Host "    Deleted." -ForegroundColor Green
            } catch {
                Write-Warning "    Failed: $($_.Exception.Message)"
            }
        }
        Write-Host "    Keeping:  $keepId" -ForegroundColor DarkGray
    }
}

# ============================================================
# 8. DUPLICATE SLAs
# ============================================================
Write-Host "`n--- SLAs ---" -ForegroundColor Cyan
$filter = [System.Uri]::EscapeDataString("contains(name,'Zurn')")
$slas = DV-Get "$base/slas?`$filter=$filter&`$select=slaid,name,createdon"
if ($slas.Count -gt 1) {
    Write-Host "  DUPLICATE SLA: Zurn Elkay Standard SLA ($($slas.Count) records)" -ForegroundColor Red
    $sorted = $slas | Sort-Object createdon
    $keepId = $sorted[0].slaid
    for ($i = 1; $i -lt $sorted.Count; $i++) {
        Write-Host "    Deleting: $($sorted[$i].slaid)" -ForegroundColor Yellow
        try {
            DV-Delete "$base/slas($($sorted[$i].slaid))"
            $totalDeleted++
            Write-Host "    Deleted." -ForegroundColor Green
        } catch {
            Write-Warning "    Failed: $($_.Exception.Message)"
        }
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Magenta
Write-Host "  CLEANUP COMPLETE" -ForegroundColor Magenta
Write-Host "  Total records deleted: $totalDeleted" -ForegroundColor White
Write-Host ("=" * 70) -ForegroundColor Magenta
Write-Host ""
