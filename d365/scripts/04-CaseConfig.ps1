<#
.SYNOPSIS
    Step 04 - Configure Case Subjects, Categories, and Business Rules
.DESCRIPTION
    Creates the subject tree, case origin mappings, and documents the
    tier-based priority logic for Zurn Elkay Customer Service.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "04" "Configure Case Subjects & Categories"
Connect-Dataverse

# ============================================================
# 1. Subject Tree
# ============================================================
Write-Host "Creating subject tree..." -ForegroundColor Yellow

# Root subjects for the two brands
$zurnRootId = Find-OrCreate-Record `
    -EntitySet "subjects" `
    -Filter "title eq 'Zurn'" `
    -IdField "subjectid" `
    -Body @{ title = "Zurn"; description = "Zurn Industries product and service subjects" } `
    -DisplayName "Zurn (root subject)"

$elkayRootId = Find-OrCreate-Record `
    -EntitySet "subjects" `
    -Filter "title eq 'Elkay'" `
    -IdField "subjectid" `
    -Body @{ title = "Elkay"; description = "Elkay Manufacturing product and service subjects" } `
    -DisplayName "Elkay (root subject)"

# Zurn sub-subjects
$zurnSubjects = @(
    @{ title = "Order Management";      desc = "Order placement, order status, order changes, cancellations" },
    @{ title = "Logistics & Shipping";  desc = "Shipping status, freight claims, delivery issues, next day air requests" },
    @{ title = "Technical Support";     desc = "Product troubleshooting, installation guidance, winterization, specifications" },
    @{ title = "Warranty & Returns";    desc = "Warranty claims, RMA requests, product returns, defective product reports" },
    @{ title = "Pricing & Quotes";      desc = "Price inquiries, quote requests, discount approvals, price list questions" },
    @{ title = "Product Information";   desc = "Spec sheets, submittals, CAD files, product selection assistance" },
    @{ title = "Backflow / Wilkins";    desc = "Wilkins backflow preventers - tech support, sizing, compliance, repairs" },
    @{ title = "Drainage";             desc = "Floor drains, trench drains, roof drains - specifications and troubleshooting" },
    @{ title = "Quality / Recall";      desc = "Product quality issues, recall notifications, safety concerns" }
)

foreach ($s in $zurnSubjects) {
    Find-OrCreate-Record `
        -EntitySet "subjects" `
        -Filter "title eq '$($s.title)' and _parentsubject_value eq '$zurnRootId'" `
        -IdField "subjectid" `
        -Body @{
            title       = $s.title
            description = $s.desc
            "parentsubject@odata.bind" = "/subjects($zurnRootId)"
        } `
        -DisplayName "Zurn > $($s.title)"
}

# Elkay sub-subjects
$elkaySubjects = @(
    @{ title = "Order Management";      desc = "Order placement, status, changes, cancellations" },
    @{ title = "Logistics & Shipping";  desc = "Shipping, freight, delivery" },
    @{ title = "Technical Support";     desc = "Troubleshooting, installation, winterization for Elkay products" },
    @{ title = "Warranty & Returns";    desc = "Warranty claims, returns, defective products" },
    @{ title = "Pricing & Quotes";      desc = "Price inquiries, quotes" },
    @{ title = "Hydration Products";    desc = "Bottle fillers, drinking fountains, water coolers - tech support and specs" },
    @{ title = "Sinks & Fixtures";      desc = "Stainless steel sinks, faucets, accessories" },
    @{ title = "Filters & Replacement"; desc = "Water Sentry filters, replacement parts, maintenance" }
)

foreach ($s in $elkaySubjects) {
    Find-OrCreate-Record `
        -EntitySet "subjects" `
        -Filter "title eq '$($s.title)' and _parentsubject_value eq '$elkayRootId'" `
        -IdField "subjectid" `
        -Body @{
            title       = $s.title
            description = $s.desc
            "parentsubject@odata.bind" = "/subjects($elkayRootId)"
        } `
        -DisplayName "Elkay > $($s.title)"
}

# ============================================================
# 2. Verify Case Origin values
# ============================================================
Write-Host "`nVerifying case origin option set values..." -ForegroundColor Yellow

# Case origins are a global option set (caseorigincode):
#   1 = Phone, 2 = Email, 3 = Web, 2483 = Facebook, 3986 = Twitter
# These are OOB and should already exist. Just document them.
Write-Host "  Phone = 1 (OOB)" -ForegroundColor DarkGray
Write-Host "  Email = 2 (OOB)" -ForegroundColor DarkGray
Write-Host "  Web   = 3 (OOB)" -ForegroundColor DarkGray

# ============================================================
# 3. Document Tier-based Priority Logic
# ============================================================
Write-Host "`nTier-based Priority Mapping (for reference):" -ForegroundColor Yellow

$tierMap = @"

  Customer Tier  |  Base Priority  |  With Hot Word  |  D365 Priority
  ---------------+-----------------+-----------------+----------------
  Tier 1         |  8,000          |  10,000         |  1 (High)
  Tier 2         |  6,000          |  10,000         |  2 (Normal)
  Tier 3         |  10,000         |  10,000         |  2 (Normal)
  Tier 4         |  1,000          |  10,000         |  3 (Low)
  
  Hot Words: Urgent, Next Day Air, Emergency, Recall, Safety, Legal
  
  Priority field (prioritycode): 1=High, 2=Normal, 3=Low
  
  NOTE: The AIP lookup (ERP integration) determines customer tier.
  In the demo, tier is stored on the Account (accountclassificationcode).
  A Power Automate flow should read the tier on case creation and set priority.

"@
Write-Host $tierMap -ForegroundColor Cyan

# Save the mapping for reference
$tierMap | Out-File "$scriptDir\..\data\tier-priority-mapping.txt" -Encoding utf8

# ============================================================
# Summary
# ============================================================
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Case Configuration Complete" -ForegroundColor Green
Write-Host " Zurn subjects  : $($zurnSubjects.Count) categories" -ForegroundColor White
Write-Host " Elkay subjects : $($elkaySubjects.Count) categories" -ForegroundColor White
Write-Host " Tier mapping documented in data\tier-priority-mapping.txt" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Green
