<#
.SYNOPSIS
    Step 07 - Create Demo Cases
.DESCRIPTION
    Creates ~50 sample cases across all tiers, brands, channels, and subjects.
    Includes cases with hot words, various priorities, and different statuses.
    References accounts, contacts, products, and queues created by prior scripts.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "07" "Create Demo Cases"
Connect-Dataverse

# ============================================================
# Load reference data from prior steps
# ============================================================
$accountIdsFile = "$scriptDir\..\data\account-ids.json"
$queueIdsFile = "$scriptDir\..\data\queue-ids.json"
$productIdsFile = "$scriptDir\..\data\product-ids.json"

if (-not (Test-Path $accountIdsFile)) { throw "Run 01-Accounts.ps1 first." }
if (-not (Test-Path $queueIdsFile)) { Write-Warning "Queue IDs file not found - cases won't be assigned to queues." }

$accountIds = Get-Content $accountIdsFile | ConvertFrom-Json

# Helper to look up an account ID by name
function Get-AcctId([string]$name) {
    foreach ($group in @("Manufacturers", "Distributors", "EndUsers")) {
        $g = $accountIds.$group
        if ($g.PSObject.Properties.Name -contains $name) { return $g.$name }
    }
    return $null
}

# Helper to look up a contact ID by email
function Get-ContactId([string]$email) {
    $c = Invoke-DataverseGet -EntitySet "contacts" -Filter "emailaddress1 eq '$email'" -Select "contactid" -Top 1
    if ($c) { return $c[0].contactid }
    return $null
}

# Helper to look up a subject by title
function Get-SubjectId([string]$title) {
    $s = Invoke-DataverseGet -EntitySet "subjects" -Filter "title eq '$title'" -Select "subjectid" -Top 1
    if ($s) { return $s[0].subjectid }
    return $null
}

# ============================================================
# Case Priority mapping
#   1 = High, 2 = Normal, 3 = Low
# Case Origin
#   1 = Phone, 2 = Email, 3 = Web
# Case Status
#   statecode: 0 = Active, 1 = Resolved, 2 = Cancelled
#   statuscode: 1 = In Progress, 2 = On Hold, 3 = Waiting for Details,
#               4 = Researching, 5 = Problem Solved, 1000 = Information Provided
# ============================================================

$cases = @(
    # ===================== TIER 1 - Strategic Distributors =====================
    # Ferguson - Urgent email with hot word
    @{
        title = "URGENT - Ferguson PO #82991 - Incorrect flush valve shipment"
        desc = "Ferguson received 200 units of ZN-AV-1001 but ordered ZN-EZ-1002. Need immediate resolution - Next Day Air replacement required. Customer threatening to switch vendors."
        acct = "Ferguson Enterprises"; contact = "tom.harrison@ferguson.com"
        origin = 2; priority = 1; subject = "Order Management"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 0; statusReason = 1
        hotword = $true
    },
    @{
        title = "Ferguson - Bulk pricing request for Q2 hydration products"
        desc = "Rachel Chen requesting updated pricing for 500+ Elkay EZH2O bottle filling stations for a national rollout across FM facilities."
        acct = "Ferguson Enterprises"; contact = "rachel.chen@ferguson.com"
        origin = 2; priority = 1; subject = "Pricing & Quotes"; brand = "Elkay"
        queue = "Elkay Orders"; status = 0; statusReason = 1
    },
    @{
        title = "Ferguson - Wilkins 975XL backflow preventer sizing question"
        desc = "Tom Harrison needs help sizing backflow preventers for a 6-inch main. Municipal code requires RPZ. Need tech specs and sizing charts."
        acct = "Ferguson Enterprises"; contact = "tom.harrison@ferguson.com"
        origin = 1; priority = 1; subject = "Backflow / Wilkins"; brand = "Zurn"
        queue = "Zurn Phone - Backflow/Wilkins"; status = 0; statusReason = 4
    },

    # Hajoca - Phone support
    @{
        title = "Hajoca - AquaSense faucet not activating after install"
        desc = "Branch in Ardmore reports sensor faucet ZN-SF-2001 not activating. Installed per spec. Battery is new. Need troubleshooting guidance."
        acct = "Hajoca Corporation"; contact = "mark.sullivan@hajoca.com"
        origin = 1; priority = 1; subject = "Technical Support"; brand = "Zurn"
        queue = "Zurn Phone - Tech Support"; status = 0; statusReason = 4
    },
    @{
        title = "Hajoca - Return authorization for damaged trench drains"
        desc = "Shipment of Z886 trench drains arrived with cracked grates. 12 units affected. Requesting RMA and replacement shipment."
        acct = "Hajoca Corporation"; contact = "mark.sullivan@hajoca.com"
        origin = 2; priority = 1; subject = "Warranty & Returns"; brand = "Zurn"
        queue = "General Support"; status = 0; statusReason = 1
    },

    # Winsupply
    @{
        title = "Winsupply - Product spec sheets needed for bid package"
        desc = "Karen Ostrowski needs submittals and spec sheets for AquaVantage flush valves and AquaSpec faucets for a school district bid."
        acct = "Winsupply Inc."; contact = "karen.ostrowski@winsupply.com"
        origin = 2; priority = 1; subject = "Product Information"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 1; statusReason = 5
    },

    # ===================== TIER 2 - Key Distributors =====================
    # HD Supply
    @{
        title = "HD Supply - Order #HD-44210 status inquiry"
        desc = "James Morales checking status of large order placed 2 weeks ago. 50x Elkay sinks and 30x bottle fillers. Customer says they haven't received tracking."
        acct = "HD Supply"; contact = "james.morales@hdsupply.com"
        origin = 1; priority = 2; subject = "Order Management"; brand = "Elkay"
        queue = "Elkay Orders"; status = 0; statusReason = 3
    },
    @{
        title = "HD Supply - Lustertone sink installation template request"
        desc = "Need cutout templates for Elkay DLRS3322 drop-in sink for a multi-family project. 200 units being installed."
        acct = "HD Supply"; contact = "james.morales@hdsupply.com"
        origin = 2; priority = 2; subject = "Product Information"; brand = "Elkay"
        queue = "Elkay Sinks & Fixtures"; status = 1; statusReason = 5
    },

    # Wolseley
    @{
        title = "Wolseley - Cross-border shipping delays on Zurn drainage products"
        desc = "Sarah Tremblay reports 3-week delay on Z415 floor drains shipped to Ontario warehouse. Need freight status and ETA."
        acct = "Wolseley Industrial Group"; contact = "sarah.tremblay@wolseley.com"
        origin = 2; priority = 2; subject = "Logistics & Shipping"; brand = "Zurn"
        queue = "General Support"; status = 0; statusReason = 1
    },

    # Consolidated Supply
    @{
        title = "Consolidated Supply - Winterization guidance for bottle fillers"
        desc = "David Park requesting winterization procedures for outdoor Elkay EZH2O units installed at a Portland park district. Freeze risk."
        acct = "Consolidated Supply Co."; contact = "david.park@consupply.com"
        origin = 2; priority = 2; subject = "Technical Support"; brand = "Elkay"
        queue = "Elkay Hydration Support"; status = 0; statusReason = 4
    },
    @{
        title = "Consolidated Supply - Replacement filter bulk order"
        desc = "Requesting quote for 300x EWF3000 Water Sentry filters. Annual maintenance contract for municipal accounts."
        acct = "Consolidated Supply Co."; contact = "david.park@consupply.com"
        origin = 2; priority = 2; subject = "Pricing & Quotes"; brand = "Elkay"
        queue = "Elkay Orders"; status = 0; statusReason = 1
    },

    # ===================== TIER 3 - Standard Distributors =====================
    # Pacific Plumbing
    @{
        title = "Pacific Plumbing - Roof drain compatibility question"
        desc = "Linda Nguyen asking if Zurn Z100 roof drain is compatible with TPO roofing membrane. Need spec verification."
        acct = "Pacific Plumbing Supply"; contact = "linda.nguyen@pacificps.com"
        origin = 1; priority = 2; subject = "Technical Support"; brand = "Zurn"
        queue = "Zurn Phone - Tech Support"; status = 1; statusReason = 5
    },

    # Midwest Pipe
    @{
        title = "Midwest Pipe - Order discrepancy - wrong quantities received"
        desc = "Brian Kowalski ordered 50 ZN-AS-2002 faucets, received 35. Short-shipped. Need remaining 15 sent ASAP."
        acct = "Midwest Pipe & Supply"; contact = "brian.kowalski@midwestpipe.com"
        origin = 2; priority = 2; subject = "Order Management"; brand = "Zurn"
        queue = "Commercial Email"; status = 0; statusReason = 1
    },
    @{
        title = "Midwest Pipe - AquaSpec faucet aerator replacement part number"
        desc = "Customer asking for the correct replacement aerator part number for Z86300 AquaSpec faucet. Need 2.2 GPM version."
        acct = "Midwest Pipe & Supply"; contact = "brian.kowalski@midwestpipe.com"
        origin = 1; priority = 2; subject = "Product Information"; brand = "Zurn"
        queue = "Zurn Phone - General"; status = 1; statusReason = 5
    },

    # Southern Pipe
    @{
        title = "Southern Pipe - Warranty claim on flush valve solenoid"
        desc = "Angela Foster reports AquaVantage flush valve solenoid failure within 12 months of install. 5 units at a hospital. Requesting warranty replacement."
        acct = "Southern Pipe & Supply"; contact = "angela.foster@southernpipe.com"
        origin = 2; priority = 2; subject = "Warranty & Returns"; brand = "Zurn"
        queue = "General Support"; status = 0; statusReason = 4
    },
    @{
        title = "URGENT - Southern Pipe - Recall inquiry on flush valve model"
        desc = "Angela Foster received notice about potential safety recall. Needs confirmation whether ZN-AV-1001 batch from March 2025 is affected."
        acct = "Southern Pipe & Supply"; contact = "angela.foster@southernpipe.com"
        origin = 2; priority = 1; subject = "Quality / Recall"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 0; statusReason = 1
        hotword = $true
    },

    # Gateway
    @{
        title = "Gateway Supply - Elkay cooler making noise after 6 months"
        desc = "Eric Hammond reports EZS8L cooler at a church is vibrating loudly. Unit is 6 months old. Under warranty."
        acct = "Gateway Supply Company"; contact = "eric.hammond@gatewaysupply.com"
        origin = 1; priority = 2; subject = "Technical Support"; brand = "Elkay"
        queue = "Elkay Phone - Tech"; status = 0; statusReason = 4
    },

    # ===================== TIER 4 - Basic Distributors =====================
    # ABC Plumbing
    @{
        title = "ABC Plumbing - General product catalog request"
        desc = "Tony Reeves requesting latest Zurn catalog and price list. New to carrying Zurn products."
        acct = "ABC Plumbing Wholesale"; contact = "tony.reeves@abcplumbing.com"
        origin = 2; priority = 3; subject = "Product Information"; brand = "Zurn"
        queue = "General Support"; status = 1; statusReason = 5
    },

    # Metro Building
    @{
        title = "Metro Building - Account setup and first order assistance"
        desc = "Carmen Diaz wants to open a wholesale account and place first order for Elkay sinks. Need credit application process."
        acct = "Metro Building Supply"; contact = "carmen.diaz@metrobldg.com"
        origin = 3; priority = 3; subject = "Order Management"; brand = "Elkay"
        queue = "Elkay General Support"; status = 0; statusReason = 1
    },

    # Lakeside
    @{
        title = "Lakeside Parts - Return policy question"
        desc = "Ryan Brooks asking about return policy for slow-moving Zurn floor drain inventory. Stock has been sitting 18 months."
        acct = "Lakeside Plumbing Parts"; contact = "ryan.brooks@lakesideparts.com"
        origin = 2; priority = 3; subject = "Warranty & Returns"; brand = "Zurn"
        queue = "General Support"; status = 1; statusReason = 5
    },

    # ===================== END USERS =====================
    # School District
    @{
        title = "Greenfield SD - Drinking fountain not cooling"
        desc = "Facilities director reports Elkay bi-level fountain in gym not producing cold water. Students complaining. Unit is 3 years old."
        acct = "Greenfield School District"; contact = "pkelley@greenfieldsd.edu"
        origin = 1; priority = 2; subject = "Technical Support"; brand = "Elkay"
        queue = "Elkay Phone - Tech"; status = 0; statusReason = 4
    },
    @{
        title = "Greenfield SD - Quote request for bottle fillers in all buildings"
        desc = "Pat Kelley wants to install EZH2O bottle fillers in 8 school buildings. Need quote for 24 units plus installation guidance."
        acct = "Greenfield School District"; contact = "pkelley@greenfieldsd.edu"
        origin = 2; priority = 2; subject = "Pricing & Quotes"; brand = "Elkay"
        queue = "Elkay Hydration Support"; status = 0; statusReason = 1
    },

    # Municipality
    @{
        title = "City of Mesa - Backflow preventer compliance question"
        desc = "Maria Gutierrez needs to verify that Wilkins 975XL meets Arizona state backflow prevention code for municipal water supply."
        acct = "City of Mesa Water Dept"; contact = "mgutierrez@mesaaz.gov"
        origin = 2; priority = 2; subject = "Backflow / Wilkins"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 0; statusReason = 4
    },

    # Commercial
    @{
        title = "Marriott Milwaukee - Sensor faucet battery replacement program"
        desc = "Kevin Strand asking about bulk battery replacement schedule for 150 AquaSense sensor faucets across property."
        acct = "Marriott Downtown Milwaukee"; contact = "kevin.strand@marriott.com"
        origin = 2; priority = 3; subject = "Technical Support"; brand = "Zurn"
        queue = "Commercial Email"; status = 1; statusReason = 5
    },

    # Homeowner
    @{
        title = "Homeowner - Flush valve running continuously"
        desc = "Robert Johnson reports Zurn flush valve in home continuously running. Model unknown. Asking for troubleshooting steps."
        acct = "Johnson Residence"; contact = "rjohnson247@gmail.com"
        origin = 1; priority = 3; subject = "Technical Support"; brand = "Zurn"
        queue = "Consumer"; status = 0; statusReason = 4
    },
    @{
        title = "Homeowner - Winterization question for outdoor Elkay bottle filler"
        desc = "Robert Johnson installed Elkay bottle filler outside. Winter approaching. Wants to know how to winterize to prevent freeze damage."
        acct = "Johnson Residence"; contact = "rjohnson247@gmail.com"
        origin = 3; priority = 3; subject = "Technical Support"; brand = "Elkay"
        queue = "Consumer"; status = 1; statusReason = 5
    },

    # ===================== ADDITIONAL VARIETY =====================
    @{
        title = "Ferguson - Next Day Air request for Wilkins double check valves"
        desc = "Tom Harrison needs 20x WK-DC-4002 shipped Next Day Air to a jobsite. Inspector arriving Friday. URGENT."
        acct = "Ferguson Enterprises"; contact = "tom.harrison@ferguson.com"
        origin = 2; priority = 1; subject = "Logistics & Shipping"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 0; statusReason = 1
        hotword = $true
    },
    @{
        title = "HD Supply - Elkay undermount sink scratched on delivery"
        desc = "ELUH3120R sink received with deep scratches on basin. James Morales requesting replacement and freight claim process."
        acct = "HD Supply"; contact = "james.morales@hdsupply.com"
        origin = 2; priority = 2; subject = "Warranty & Returns"; brand = "Elkay"
        queue = "Elkay Sinks & Fixtures"; status = 0; statusReason = 1
    },
    @{
        title = "Winsupply - Floor drain strainer finish options"
        desc = "Karen Ostrowski needs to know available grate/strainer finishes for Z415 floor drain. Architect specified oil-rubbed bronze."
        acct = "Winsupply Inc."; contact = "karen.ostrowski@winsupply.com"
        origin = 2; priority = 1; subject = "Product Information"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 0; statusReason = 3
    },
    @{
        title = "Pacific Plumbing - eCommerce order payment failed"
        desc = "Linda Nguyen placed online order but payment wasn't processed. Order shows pending. Needs resolution."
        acct = "Pacific Plumbing Supply"; contact = "linda.nguyen@pacificps.com"
        origin = 3; priority = 2; subject = "Order Management"; brand = "Zurn"
        queue = "eCommerce"; status = 0; statusReason = 1
    },
    @{
        title = "Gateway Supply - Bottle filler counter reset procedure"
        desc = "Eric Hammond asking how to reset the green ticker/bottle counter on EZH2O unit for building management reporting."
        acct = "Gateway Supply Company"; contact = "eric.hammond@gatewaysupply.com"
        origin = 2; priority = 2; subject = "Hydration Products"; brand = "Elkay"
        queue = "Elkay Hydration Support"; status = 1; statusReason = 5
    },
    @{
        title = "Consolidated Supply - Drainage product lead time inquiry"
        desc = "David Park asking for current lead times on Z886 trench drain systems. Has a large municipal project starting in 6 weeks."
        acct = "Consolidated Supply Co."; contact = "david.park@consupply.com"
        origin = 1; priority = 2; subject = "Drainage"; brand = "Zurn"
        queue = "Zurn Phone - General"; status = 0; statusReason = 1
    },
    @{
        title = "EMERGENCY - Hajoca - Water damage from failed backflow preventer"
        desc = "Wilkins 975XL RPZ failure causing flooding at customer site. Need emergency tech support and replacement parts. Potential liability."
        acct = "Hajoca Corporation"; contact = "mark.sullivan@hajoca.com"
        origin = 1; priority = 1; subject = "Backflow / Wilkins"; brand = "Zurn"
        queue = "Zurn Phone - Backflow/Wilkins"; status = 0; statusReason = 1
        hotword = $true
    },
    @{
        title = "City of Mesa - Zurn roof drain spec for flat-roof water treatment facility"
        desc = "Maria Gutierrez needs Z100 roof drain specs and sizing for a new 50,000 sq ft flat-roof facility. Architect requires submittals."
        acct = "City of Mesa Water Dept"; contact = "mgutierrez@mesaaz.gov"
        origin = 2; priority = 2; subject = "Drainage"; brand = "Zurn"
        queue = "Apps-Eng-CB Email"; status = 0; statusReason = 4
    },
    @{
        title = "Wolseley - Elkay filter replacement schedule recommendation"
        desc = "Sarah Tremblay wants recommended replacement schedule for EWF3000 filters in high-traffic locations (airports, hospitals)."
        acct = "Wolseley Industrial Group"; contact = "sarah.tremblay@wolseley.com"
        origin = 2; priority = 2; subject = "Filters & Replacement"; brand = "Elkay"
        queue = "Elkay Hydration Support"; status = 1; statusReason = 5
    },
    @{
        title = "Metro Building - Elkay sink rough-in dimensions"
        desc = "Carmen Diaz needs rough-in and cutout dimensions for DLRS3322 sink. Countertop fabricator needs measurements before Thursday."
        acct = "Metro Building Supply"; contact = "carmen.diaz@metrobldg.com"
        origin = 1; priority = 3; subject = "Sinks & Fixtures"; brand = "Elkay"
        queue = "Elkay Phone - General"; status = 0; statusReason = 3
    },
    @{
        title = "ABC Plumbing - Zurn AquaSpec faucet leaking at base"
        desc = "Tony Reeves has a plumber customer reporting AquaSpec faucet leaking at swivel base. Installed 3 months ago. Under warranty?"
        acct = "ABC Plumbing Wholesale"; contact = "tony.reeves@abcplumbing.com"
        origin = 1; priority = 3; subject = "Technical Support"; brand = "Zurn"
        queue = "Zurn Phone - General"; status = 0; statusReason = 4
    }
)

# ============================================================
# Create cases
# ============================================================
Write-Host "Creating $($cases.Count) demo cases..." -ForegroundColor Yellow

$caseCount = 0
$casesToResolve = @()

foreach ($c in $cases) {
    # Always create cases as Active first (statecode=0)
    $caseBody = @{
        title          = $c.title
        description    = $c.desc
        caseorigincode = $c.origin
        prioritycode   = $c.priority
    }

    # Link to account
    $acctId = Get-AcctId $c.acct
    if ($acctId) {
        $caseBody["customerid_account@odata.bind"] = "/accounts($acctId)"
    }

    # Link to contact
    if ($c.contact) {
        $contactId = Get-ContactId $c.contact
        if ($contactId) {
            $caseBody["primarycontactid@odata.bind"] = "/contacts($contactId)"
        }
    }

    # Link to subject
    if ($c.subject) {
        $subjectId = Get-SubjectId $c.subject
        if ($subjectId) {
            $caseBody["subjectid@odata.bind"] = "/subjects($subjectId)"
        }
    }

    # Check for existing case with same title
    $safeTitle = $c.title -replace "'", "''"
    $existing = Invoke-DataverseGet -EntitySet "incidents" -Filter "title eq '$safeTitle'" -Select "incidentid,statecode" -Top 1

    if ($existing -and $existing.Count -gt 0) {
        Write-Host "  Exists: $($c.title.Substring(0, [Math]::Min(60, $c.title.Length)))..." -ForegroundColor DarkGray
        # If the case should be resolved and it's still active, queue it for resolution
        if ($c.status -eq 1 -and $existing[0].statecode -eq 0) {
            $casesToResolve += @{ id = $existing[0].incidentid; title = $c.title }
        }
    } else {
        try {
            $result = Invoke-DataversePost -EntitySet "incidents" -Body $caseBody
            if ($result) {
                $caseCount++
                $icon = if ($c.hotword) { "[HOT]" } else { "" }
                Write-Host "  Created: $icon $($c.title)" -ForegroundColor Green

                # If this case should be resolved, queue it for resolution
                if ($c.status -eq 1) {
                    $newId = $null
                    if ($result.incidentid) {
                        $newId = $result.incidentid
                    } elseif ($result -is [string] -and $result -match '[0-9a-fA-F\-]{36}') {
                        $newId = $result
                    }
                    if ($newId) {
                        $casesToResolve += @{ id = $newId; title = $c.title }
                    }
                }
            }
        } catch {
            Write-Warning "  FAILED to create case: $($c.title) - $($_.Exception.Message)"
        }
    }
}

# ============================================================
# Resolve cases that should be in Resolved state
# ============================================================
if ($casesToResolve.Count -gt 0) {
    Write-Host "`nResolving $($casesToResolve.Count) cases..." -ForegroundColor Yellow
    foreach ($cr in $casesToResolve) {
        try {
            $closeBody = @{
                IncidentResolution = @{
                    "incidentid@odata.bind" = "/incidents($($cr.id))"
                    subject                 = "Problem Solved"
                }
                Status             = 5  # Problem Solved
            }
            Invoke-DataversePost -EntitySet "CloseIncident" -Body $closeBody
            Write-Host "  Resolved: $($cr.title.Substring(0, [Math]::Min(60, $cr.title.Length)))..." -ForegroundColor Cyan
        } catch {
            Write-Warning "  Could not resolve case '$($cr.title)': $_"
        }
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Demo Cases Created" -ForegroundColor Green
Write-Host " Total cases created : $caseCount" -ForegroundColor White
Write-Host " Total defined       : $($cases.Count)" -ForegroundColor White
$hotCount = ($cases | Where-Object { $_.hotword }).Count
$emailCount = ($cases | Where-Object { $_.origin -eq 2 }).Count
$phoneCount = ($cases | Where-Object { $_.origin -eq 1 }).Count
$webCount = ($cases | Where-Object { $_.origin -eq 3 }).Count
Write-Host " Hot word cases      : $hotCount" -ForegroundColor White
Write-Host " Email / Phone / Web : $emailCount / $phoneCount / $webCount" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green
