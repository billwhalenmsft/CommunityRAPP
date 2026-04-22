<#
.SYNOPSIS
    ABC Supply Savage Branch — Field Service Configuration
    Provisions: Incident Types, Inspection Templates, Work Order Types,
                Service Territories, Characteristics (Tech Skills)

.DESCRIPTION
    Idempotent. Uses DataverseHelper.psm1 for auth (pac CLI token).
    Must be run BEFORE work orders / cases are created.

.PARAMETER Action
    IncidentTypes | InspectionTemplates | WorkOrderTypes | Territories |
    Characteristics | ServiceTasks | Resources | WorkOrders | All

.EXAMPLE
    .\Provision-ABCSupplyFieldService.ps1 -Action All
    .\Provision-ABCSupplyFieldService.ps1 -Action IncidentTypes
    .\Provision-ABCSupplyFieldService.ps1 -Action WorkOrders
    .\Provision-ABCSupplyFieldService.ps1 -Action Resources
#>

[CmdletBinding()]
param(
    [ValidateSet("IncidentTypes","InspectionTemplates","WorkOrderTypes","Territories","Characteristics","ServiceTasks","Resources","WorkOrders","All")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"

# ── Import DataverseHelper (shared module) ────────────────────────
$repoRoot   = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$helperPath = Join-Path $repoRoot "d365\scripts\DataverseHelper.psm1"

if (Test-Path $helperPath) {
    Import-Module $helperPath -Force
    Write-Host "DataverseHelper loaded from: $helperPath" -ForegroundColor DarkGray
} else {
    # Fallback — inline token function using az CLI
    Write-Warning "DataverseHelper not found at $helperPath — using inline az CLI auth"

    $script:OrgUrl  = "https://orgecbce8ef.crm.dynamics.com"
    $script:ApiBase = "$($script:OrgUrl)/api/data/v9.2"

    function Connect-Dataverse {
        $token = (az account get-access-token --resource $script:OrgUrl --query accessToken -o tsv 2>$null)
        if (-not $token) { Write-Error "Run 'az login' first."; exit 1 }
        $script:Headers = @{
            "Authorization"    = "Bearer $token"
            "OData-MaxVersion" = "4.0"
            "OData-Version"    = "4.0"
            "Content-Type"     = "application/json"
            "Prefer"           = "return=representation"
        }
        Write-Host "  Connected to $($script:OrgUrl)" -ForegroundColor Green
    }

    function Invoke-DataverseRequest {
        param([string]$Method, [string]$Url, [hashtable]$Body = $null)
        $params = @{ Method=$Method; Uri=$Url; Headers=$script:Headers; TimeoutSec=30 }
        if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
        return Invoke-RestMethod @params
    }

    function Find-OrCreate-Record {
        param([string]$EntitySet, [string]$Filter, [string]$IdField, [hashtable]$Body, [string]$DisplayName)
        $existing = (Invoke-DataverseRequest -Method GET -Url "$($script:ApiBase)/$EntitySet`?`$filter=$Filter&`$select=$IdField").value | Select-Object -First 1
        if ($existing) {
            Write-Host "    [SKIP] $DisplayName" -ForegroundColor DarkGray
            return $existing.$IdField
        }
        $resp = Invoke-DataverseRequest -Method POST -Url "$($script:ApiBase)/$EntitySet" -Body $Body
        Write-Host "    [CREATE] $DisplayName → $($resp.$IdField)" -ForegroundColor Green
        return $resp.$IdField
    }
}

$DataDir = "$PSScriptRoot\..\..\data"
if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Force -Path $DataDir | Out-Null }

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Cyan
Write-Host "  ABC Supply — Field Service Configuration" -ForegroundColor Cyan
Write-Host "  Action: $Action" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Cyan

Connect-Dataverse

$ApiBase = if ($script:ApiUrl) { $script:ApiUrl } else { $script:ApiBase }

# ─────────────────────────────────────────────────────────────────
# HELPER: inline Find-OrCreate when DataverseHelper is loaded
# ─────────────────────────────────────────────────────────────────
function Upsert-FSRecord {
    param([string]$EntitySet, [string]$FilterField, [string]$FilterValue, [string]$IdField, [hashtable]$Body, [string]$DisplayName)
    try {
        $enc = [System.Web.HttpUtility]::UrlEncode($FilterValue)
        $resp = Invoke-DataverseRequest -Method GET -Url "$ApiBase/$EntitySet`?`$filter=$FilterField eq '$enc'&`$select=$IdField" -ErrorAction SilentlyContinue
        $existing = $resp.value | Select-Object -First 1
    } catch { $existing = $null }

    if ($existing) {
        Write-Host "  [SKIP] $DisplayName" -ForegroundColor DarkGray
        return $existing.$IdField
    }
    $created = Invoke-DataverseRequest -Method POST -Url "$ApiBase/$EntitySet" -Body $Body
    Write-Host "  [CREATE] $DisplayName → $($created.$IdField)" -ForegroundColor Green
    return $created.$IdField
}

# ─────────────────────────────────────────────────────────────────
# 1. INCIDENT TYPES
#    msdyn_incidenttype — defines the work category, estimated duration
#    ABC uses mostly write-in, so types are broad + flexible
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","IncidentTypes") {
    Write-Host "`n  ── Field Service Incident Types ──" -ForegroundColor Yellow

    $incidentTypes = @(
        @{
            msdyn_name              = "Window Repair — Seal / Weatherstrip"
            msdyn_description       = "Seal failure, water intrusion, or weatherstrip replacement. Most common warranty claim type."
            msdyn_estimatedduration = 180
        },
        @{
            msdyn_name              = "Window Repair — Mechanism / Hardware"
            msdyn_description       = "Operator mechanism, balance spring, locking hardware, or hinge failure. Often parts-in-stock job."
            msdyn_estimatedduration = 120
        },
        @{
            msdyn_name              = "Window Repair — Glass / IG Unit"
            msdyn_description       = "Broken glass, failed insulated glass unit, or foggy/condensation between panes."
            msdyn_estimatedduration = 240
        },
        @{
            msdyn_name              = "Screen Replacement"
            msdyn_description       = "Window or door screen replacement — may be single unit or multi-unit project."
            msdyn_estimatedduration = 90
        },
        @{
            msdyn_name              = "Door Repair — Sliding / Patio"
            msdyn_description       = "Sliding patio door track, roller, latch, or weatherstrip issue."
            msdyn_estimatedduration = 150
        },
        @{
            msdyn_name              = "Door Repair — Entry / Hinged"
            msdyn_description       = "Entry door adjustment, hinge repair, or threshold replacement."
            msdyn_estimatedduration = 120
        },
        @{
            msdyn_name              = "Measurement Assessment"
            msdyn_description       = "Tech visits site to take measurements for parts order or custom fabrication. No repair performed."
            msdyn_estimatedduration = 60
        },
        @{
            msdyn_name              = "Parts Installation — Ordered Parts"
            msdyn_description       = "Installation of previously ordered parts that have arrived at warehouse."
            msdyn_estimatedduration = 120
        },
        @{
            msdyn_name              = "Warranty Assessment"
            msdyn_description       = "Tech assesses whether issue qualifies as manufacturer defect for warranty claim."
            msdyn_estimatedduration = 90
        },
        @{
            msdyn_name              = "Odd Jobs — Misc Repair"
            msdyn_description       = "Miscellaneous window/door task not covered by standard types. Includes screens, caulking, trim."
            msdyn_estimatedduration = 60
        }
    )

    $itIds = @{}
    foreach ($it in $incidentTypes) {
        $id = Upsert-FSRecord `
            -EntitySet    "msdyn_incidenttypes" `
            -FilterField  "msdyn_name" `
            -FilterValue  $it.msdyn_name `
            -IdField      "msdyn_incidenttypeid" `
            -Body         $it `
            -DisplayName  $it.msdyn_name
        if ($id) { $itIds[$it.msdyn_name] = $id }
    }

    $itIds | ConvertTo-Json | Set-Content "$DataDir\incident_type_ids.json"
    Write-Host "  Incident Type IDs saved → $DataDir\incident_type_ids.json" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────
# 2. INSPECTION TEMPLATES
#    msdyn_inspectiontemplate → msdyn_inspectionquestion
#    Two templates: Standard Service Checklist + Seal/Water Assessment
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","InspectionTemplates") {
    Write-Host "`n  ── Inspection Templates ──" -ForegroundColor Yellow

    # Template 1 — Standard Service Completion Checklist
    $template1Name = "ABC Supply — Standard Service Completion Checklist"
    $t1Id = Upsert-FSRecord `
        -EntitySet   "msdyn_inspectiontemplates" `
        -FilterField "msdyn_name" `
        -FilterValue $template1Name `
        -IdField     "msdyn_inspectiontemplateid" `
        -Body        @{ msdyn_name=$template1Name; msdyn_description="7-point completion checklist for all ABC Supply window and door service visits. Required for every work order." } `
        -DisplayName $template1Name

    if ($t1Id) {
        $t1Questions = @(
            @{ msdyn_name="Frame Condition";              msdyn_questiontype=192350001; msdyn_description="No cracks, warping, or damage to frame?";               msdyn_order=10 },
            @{ msdyn_name="Glass / IG Unit Condition";   msdyn_questiontype=192350001; msdyn_description="No scratches, cracks, or seal failure in glass unit?";   msdyn_order=20 },
            @{ msdyn_name="Seal / Weatherstrip";         msdyn_questiontype=192350001; msdyn_description="Seal and weatherstrip intact, properly seated?";          msdyn_order=30 },
            @{ msdyn_name="Hardware Operation";          msdyn_questiontype=192350001; msdyn_description="All locks, hinges, operators, or rollers function correctly?"; msdyn_order=40 },
            @{ msdyn_name="Installation Plumb & Level";  msdyn_questiontype=192350001; msdyn_description="Window or door is plumb, level, and square in opening?"; msdyn_order=50 },
            @{ msdyn_name="Interior Trim / Finish";      msdyn_questiontype=192350001; msdyn_description="No damage to interior trim or finish from installation?"; msdyn_order=60 },
            @{ msdyn_name="Customer Walkthrough Done";   msdyn_questiontype=192350001; msdyn_description="Completed walkthrough with customer — satisfaction confirmed?"; msdyn_order=70 }
        )
        foreach ($q in $t1Questions) {
            $qBody = $q + @{ "msdyn_inspectiontemplateid@odata.bind" = "/msdyn_inspectiontemplates($t1Id)" }
            Upsert-FSRecord `
                -EntitySet   "msdyn_inspectionquestions" `
                -FilterField "msdyn_name" `
                -FilterValue $q.msdyn_name `
                -IdField     "msdyn_inspectionquestionid" `
                -Body        $qBody `
                -DisplayName "  Q: $($q.msdyn_name)"
        }
    }

    # Template 2 — Seal Failure / Water Intrusion Assessment
    $template2Name = "ABC Supply — Seal Failure / Water Intrusion Assessment"
    $t2Id = Upsert-FSRecord `
        -EntitySet   "msdyn_inspectiontemplates" `
        -FilterField "msdyn_name" `
        -FilterValue $template2Name `
        -IdField     "msdyn_inspectiontemplateid" `
        -Body        @{ msdyn_name=$template2Name; msdyn_description="Assessment checklist for window seal failures and water intrusion. Determines warranty eligibility and parts needed." } `
        -DisplayName $template2Name

    if ($t2Id) {
        $t2Questions = @(
            @{ msdyn_name="Water Intrusion Location";       msdyn_questiontype=192350002; msdyn_description="Describe exact location of water intrusion (corner, sill, frame, sash?)";    msdyn_order=10 },
            @{ msdyn_name="Visible Seal Damage";            msdyn_questiontype=192350001; msdyn_description="Is seal damage visible without disassembly?";                                 msdyn_order=20 },
            @{ msdyn_name="Installation Age (years)";       msdyn_questiontype=192350002; msdyn_description="How many years since window was installed?";                                  msdyn_order=30 },
            @{ msdyn_name="Warranty Status";                msdyn_questiontype=192350001; msdyn_description="Does installation age fall within manufacturer warranty period (0-2 yr)?";   msdyn_order=40 },
            @{ msdyn_name="Serial Number Captured";         msdyn_questiontype=192350001; msdyn_description="Was manufacturer serial number captured from sticker on sash or frame?";     msdyn_order=50 },
            @{ msdyn_name="Pre-Work Photo Taken";           msdyn_questiontype=192350001; msdyn_description="Pre-work photo captured showing damage location and extent?";                msdyn_order=60 },
            @{ msdyn_name="Custom Measurement Required";    msdyn_questiontype=192350001; msdyn_description="Does the seal replacement require custom sizing (lead time 3-4 wks)?";       msdyn_order=70 },
            @{ msdyn_name="Parts Order Notes";              msdyn_questiontype=192350002; msdyn_description="Note exact part number, size, or special requirements for parts order:";     msdyn_order=80 }
        )
        foreach ($q in $t2Questions) {
            $qBody = $q + @{ "msdyn_inspectiontemplateid@odata.bind" = "/msdyn_inspectiontemplates($t2Id)" }
            Upsert-FSRecord `
                -EntitySet   "msdyn_inspectionquestions" `
                -FilterField "msdyn_name" `
                -FilterValue $q.msdyn_name `
                -IdField     "msdyn_inspectionquestionid" `
                -Body        $qBody `
                -DisplayName "  Q: $($q.msdyn_name)"
        }
    }

    Write-Host "  ✅ Inspection templates created. Publish manually in Field Service UI before demo." -ForegroundColor Yellow
}

# ─────────────────────────────────────────────────────────────────
# 3. WORK ORDER TYPES
#    msdyn_workordertype — categorizes work orders in Field Service
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","WorkOrderTypes") {
    Write-Host "`n  ── Work Order Types ──" -ForegroundColor Yellow

    $woTypes = @(
        @{ msdyn_name="Service — Window Repair";       msdyn_description="Standard window repair service visit.";           msdyn_taxable=$false },
        @{ msdyn_name="Service — Door Repair";         msdyn_description="Standard door repair service visit.";             msdyn_taxable=$false },
        @{ msdyn_name="Service — Screen Replacement";  msdyn_description="Window or door screen replacement.";              msdyn_taxable=$false },
        @{ msdyn_name="Warranty — Assessment";         msdyn_description="Warranty assessment — determine manufacturer vs installer liability."; msdyn_taxable=$false },
        @{ msdyn_name="Warranty — Parts Install";      msdyn_description="Installation of parts covered under manufacturer warranty."; msdyn_taxable=$false },
        @{ msdyn_name="Measurement — Pre-Order";       msdyn_description="Site measurement visit before placing parts or custom order."; msdyn_taxable=$false },
        @{ msdyn_name="Misc — Odd Jobs";               msdyn_description="Miscellaneous work not classified above. Includes caulking, trim, and general tasks."; msdyn_taxable=$false }
    )

    $wotIds = @{}
    foreach ($wot in $woTypes) {
        $id = Upsert-FSRecord `
            -EntitySet   "msdyn_workordertypes" `
            -FilterField "msdyn_name" `
            -FilterValue $wot.msdyn_name `
            -IdField     "msdyn_workordertypeid" `
            -Body        $wot `
            -DisplayName $wot.msdyn_name
        if ($id) { $wotIds[$wot.msdyn_name] = $id }
    }

    $wotIds | ConvertTo-Json | Set-Content "$DataDir\work_order_type_ids.json"
    Write-Host "  Work Order Type IDs saved → $DataDir\work_order_type_ids.json" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────
# 4. SERVICE TERRITORIES
#    msdyn_territory — geographic dispatch zones for south metro
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Territories") {
    Write-Host "`n  ── Service Territories ──" -ForegroundColor Yellow

    $territories = @(
        @{ name="South Metro — Primary";    description="Primary dispatch zone: Savage, Shakopee, Prior Lake, Burnsville, Apple Valley, Lakeville. All 3 techs cover." },
        @{ name="South Metro — Extended";   description="Extended coverage: Eden Prairie, Minnetonka, Chaska, Jordan. Derek Olson primary." },
        @{ name="South Minneapolis Suburbs"; description="South Minneapolis corridor: Bloomington, Richfield, Edina, Eden Prairie fringe." }
    )

    $terrIds = @{}
    foreach ($t in $territories) {
        $id = Upsert-FSRecord `
            -EntitySet   "territories" `
            -FilterField "name" `
            -FilterValue $t.name `
            -IdField     "territoryid" `
            -Body        @{ name=$t.name; description=$t.description } `
            -DisplayName $t.name
        if ($id) { $terrIds[$t.name] = $id }
    }

    $terrIds | ConvertTo-Json | Set-Content "$DataDir\territory_ids.json"
    Write-Host "  Territory IDs saved → $DataDir\territory_ids.json" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────
# 5. CHARACTERISTICS (Tech Skills)
#    msdyn_characteristic — skill categories for resource scheduling
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Characteristics") {
    Write-Host "`n  ── Characteristics (Tech Skills) ──" -ForegroundColor Yellow

    $skills = @(
        @{ msdyn_name="Window Installation & Repair";  msdyn_description="Qualified to perform window installation and all repair types." },
        @{ msdyn_name="Door Installation & Repair";    msdyn_description="Qualified to perform door installation and all repair types." },
        @{ msdyn_name="Screen Fabrication";            msdyn_description="Able to measure, cut, and install replacement screens." },
        @{ msdyn_name="Seal & Weatherstrip";           msdyn_description="Certified for seal assessment and weatherstrip replacement." },
        @{ msdyn_name="IG Unit / Glass Replacement";   msdyn_description="Qualified for insulated glass unit replacement." },
        @{ msdyn_name="Warranty Assessment";           msdyn_description="Certified to assess manufacturer warranty eligibility." },
        @{ msdyn_name="Measurement Specialist";        msdyn_description="Trained in precision measurement for custom orders and bid work." },
        @{ msdyn_name="Odd Jobs — General";            msdyn_description="General handyman tasks — caulking, trim, misc. Chris Paulson primary." }
    )

    $charIds = @{}
    foreach ($sk in $skills) {
        $id = Upsert-FSRecord `
            -EntitySet   "msdyn_characteristics" `
            -FilterField "msdyn_name" `
            -FilterValue $sk.msdyn_name `
            -IdField     "msdyn_characteristicid" `
            -Body        @{ msdyn_name=$sk.msdyn_name; msdyn_description=$sk.msdyn_description; msdyn_characteristictype=1 } `
            -DisplayName $sk.msdyn_name
        if ($id) { $charIds[$sk.msdyn_name] = $id }
    }

    $charIds | ConvertTo-Json | Set-Content "$DataDir\characteristic_ids.json"
    Write-Host "  Characteristic IDs saved → $DataDir\characteristic_ids.json" -ForegroundColor DarkGray

    # Associate skills to bookable resources (techs)
    # Note: bookableresources must already exist (created via D365 user setup or manual)
    Write-Host "`n  NOTE: To assign characteristics to Derek Olson / Sam Rivera / Chris Paulson:" -ForegroundColor Yellow
    Write-Host "  Field Service → Resources → select tech → Characteristics tab → Add skill" -ForegroundColor White
    Write-Host "  Or run: Provision-ABCSupplyExtended.ps1 -Action TierLogic after techs are bookable resources" -ForegroundColor White
}

# ─────────────────────────────────────────────────────────────────
# 6. SERVICE TASK TYPES
#    msdyn_servicetasktype — reusable task templates linked to incident types
#    These auto-populate the WO service tasks checklist when an incident type is applied
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","ServiceTasks") {
    Write-Host "`n  ── Service Task Types (msdyn_servicetasktypes) ──" -ForegroundColor Yellow

    $taskTypes = @(
        @{ msdyn_name="Capture Pre-Work Photo";       msdyn_description="Photograph existing condition before any work begins. Required on every visit."; msdyn_estimatedduration=5  },
        @{ msdyn_name="Check Frame Condition";        msdyn_description="Inspect frame for cracks, warping, or physical damage. Document findings.";    msdyn_estimatedduration=10 },
        @{ msdyn_name="Check Glass / IG Unit";        msdyn_description="Inspect glass for scratches, cracks, chips, or seal failure (fogging).";        msdyn_estimatedduration=5  },
        @{ msdyn_name="Check Seal / Weatherstrip";    msdyn_description="Verify perimeter seal and weatherstrip are intact and properly seated.";          msdyn_estimatedduration=5  },
        @{ msdyn_name="Check Hardware Operation";     msdyn_description="Test locks, hinges, operators, and sliding mechanisms through full range.";       msdyn_estimatedduration=5  },
        @{ msdyn_name="Verify Plumb and Level";       msdyn_description="Confirm window/door is plumb and level with appropriate tools.";                  msdyn_estimatedduration=5  },
        @{ msdyn_name="Check Interior Trim/Finish";   msdyn_description="Verify no damage to interior trim caused by installation or repair work.";        msdyn_estimatedduration=5  },
        @{ msdyn_name="Document Serial Number";       msdyn_description="Locate and record manufacturer serial number from sticker on sash or frame.";     msdyn_estimatedduration=5  },
        @{ msdyn_name="Measure Window/Door Opening";  msdyn_description="Take precise measurements for parts order or replacement quote.";                  msdyn_estimatedduration=15 },
        @{ msdyn_name="Log Parts Used";               msdyn_description="Record all parts consumed during this work order in the mobile app.";             msdyn_estimatedduration=5  },
        @{ msdyn_name="Record Drive Time";            msdyn_description="Log actual drive time from previous location to this job site.";                   msdyn_estimatedduration=1  },
        @{ msdyn_name="Customer Walkthrough";         msdyn_description="Walk customer through completed work and confirm satisfaction. Required on every visit."; msdyn_estimatedduration=10 },
        @{ msdyn_name="Capture Post-Work Photo";      msdyn_description="Photograph completed work from same angle as pre-work photo. Required.";           msdyn_estimatedduration=5  }
    )

    $taskTypeIds = @{}
    foreach ($tt in $taskTypes) {
        $id = Upsert-FSRecord `
            -EntitySet   "msdyn_servicetasktypes" `
            -FilterField "msdyn_name" `
            -FilterValue $tt.msdyn_name `
            -IdField     "msdyn_servicetasktypeid" `
            -Body        $tt `
            -DisplayName $tt.msdyn_name
        if ($id) { $taskTypeIds[$tt.msdyn_name] = $id }
    }

    $taskTypeIds | ConvertTo-Json | Set-Content "$DataDir\servicetasktype_ids.json"
    Write-Host "  Service Task Type IDs saved → $DataDir\servicetasktype_ids.json" -ForegroundColor DarkGray

    # Link task types to incident types
    Write-Host "`n  Linking service tasks to incident types..." -ForegroundColor Yellow

    $itIds = @{}
    $loadedIT = Get-Content "$DataDir\incident_type_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedIT) { $loadedIT.PSObject.Properties | ForEach-Object { $itIds[$_.Name] = $_.Value } }

    # Map: Incident Type Name → ordered list of task names
    $incidentTaskMap = @{
        "Window Repair — Seal / Weatherstrip" = @(
            "Document Serial Number","Capture Pre-Work Photo","Check Frame Condition",
            "Check Seal / Weatherstrip","Check Glass / IG Unit","Log Parts Used",
            "Capture Post-Work Photo","Customer Walkthrough"
        )
        "Window Repair — Mechanism / Hardware" = @(
            "Capture Pre-Work Photo","Check Hardware Operation","Log Parts Used",
            "Capture Post-Work Photo","Customer Walkthrough"
        )
        "Window Repair — Glass / IG Unit" = @(
            "Document Serial Number","Capture Pre-Work Photo","Check Glass / IG Unit",
            "Verify Plumb and Level","Log Parts Used","Capture Post-Work Photo","Customer Walkthrough"
        )
        "Screen Replacement" = @(
            "Capture Pre-Work Photo","Measure Window/Door Opening","Log Parts Used",
            "Capture Post-Work Photo","Customer Walkthrough"
        )
        "Door Repair — Sliding / Patio" = @(
            "Capture Pre-Work Photo","Check Hardware Operation","Check Seal / Weatherstrip",
            "Log Parts Used","Capture Post-Work Photo","Customer Walkthrough"
        )
        "Measurement Assessment" = @(
            "Capture Pre-Work Photo","Check Frame Condition","Check Glass / IG Unit",
            "Check Seal / Weatherstrip","Check Hardware Operation","Verify Plumb and Level",
            "Measure Window/Door Opening","Document Serial Number"
        )
        "Warranty Assessment" = @(
            "Document Serial Number","Capture Pre-Work Photo","Check Frame Condition",
            "Check Glass / IG Unit","Check Seal / Weatherstrip","Check Hardware Operation",
            "Verify Plumb and Level","Capture Post-Work Photo","Customer Walkthrough"
        )
    }

    foreach ($itName in $incidentTaskMap.Keys) {
        $itId = $itIds[$itName]
        if (-not $itId) { Write-Warning "  Incident type not found: $itName — run IncidentTypes first"; continue }

        $sortOrder = 10
        foreach ($taskName in $incidentTaskMap[$itName]) {
            $ttId = $taskTypeIds[$taskName]
            if (-not $ttId) { Write-Warning "  Task type missing: $taskName"; continue }

            $linkBody = @{
                msdyn_name      = $taskName
                msdyn_sortorder = $sortOrder
                "msdyn_incidenttype@odata.bind"    = "/msdyn_incidenttypes($itId)"
                "msdyn_tasktype@odata.bind"        = "/msdyn_servicetasktypes($ttId)"
            }
            try {
                Invoke-DataverseRequest -Method POST -Url "$ApiBase/msdyn_incidenttypeservicetasks" -Body $linkBody | Out-Null
                Write-Host "    [LINK] $itName → $($sortOrder / 10). $taskName" -ForegroundColor DarkGray
            } catch {
                Write-Warning "    Task link failed ($taskName → $itName): $($_.Exception.Message)"
            }
            $sortOrder += 10
        }
    }
}

# ─────────────────────────────────────────────────────────────────
# 7. BOOKABLE RESOURCES (Field Techs as Generic Resources)
#    Creates techs as Generic-type bookable resources so they appear
#    on the Schedule Board without requiring licensed D365 user accounts.
#    Characteristics are linked here. Territory assignment is manual (UI).
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","Resources") {
    Write-Host "`n  ── Bookable Resources (Field Techs) ──" -ForegroundColor Yellow

    $charIds = @{}
    $loadedC = Get-Content "$DataDir\characteristic_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedC) { $loadedC.PSObject.Properties | ForEach-Object { $charIds[$_.Name] = $_.Value } }

    $resources = @(
        @{
            name   = "Derek Olson"
            skills = @("Window Installation & Repair","Door Installation & Repair","Seal & Weatherstrip","Warranty Assessment","Measurement Specialist")
        },
        @{
            name   = "Sam Rivera"
            skills = @("Window Installation & Repair","Door Installation & Repair","IG Unit / Glass Replacement")
        },
        @{
            name   = "Chris Paulson"
            skills = @("Screen Fabrication","Odd Jobs — General")
        }
    )

    $resourceIds = @{}
    foreach ($r in $resources) {
        # resourcetype 5 = Generic (no D365 user required — appears on Schedule Board)
        $id = Upsert-FSRecord `
            -EntitySet   "bookableresources" `
            -FilterField "name" `
            -FilterValue $r.name `
            -IdField     "bookableresourceid" `
            -Body        @{
                name              = $r.name
                resourcetype      = 5
                msdyn_startlocation = 690970000   # Resource Address
                msdyn_endlocation   = 690970000
            } `
            -DisplayName "Resource: $($r.name)"

        if ($id) {
            $resourceIds[$r.name] = $id

            foreach ($skill in $r.skills) {
                $charId = $charIds[$skill]
                if (-not $charId) { Write-Warning "  Characteristic not found: $skill — run Characteristics first"; continue }
                try {
                    $charBody = @{
                        "bookableresourceid@odata.bind" = "/bookableresources($id)"
                        "characteristicid@odata.bind"   = "/msdyn_characteristics($charId)"
                        ratingvalue                     = $null
                    }
                    Invoke-DataverseRequest -Method POST -Url "$ApiBase/bookableresourcecharacteristics" -Body $charBody | Out-Null
                    Write-Host "    [SKILL] $($r.name) ← $skill" -ForegroundColor DarkGray
                } catch {
                    Write-Warning "    Skill link failed ($skill): $($_.Exception.Message)"
                }
            }
        }
    }

    $resourceIds | ConvertTo-Json | Set-Content "$DataDir\resource_ids.json"
    Write-Host "  Resource IDs saved → $DataDir\resource_ids.json" -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  MANUAL STEPS after Resources are created:" -ForegroundColor Yellow
    Write-Host "  1. Set working hours for each tech: FS → Resources → select tech → Work Hours → M-F 7:30am-5:00pm" -ForegroundColor White
    Write-Host "  2. Set start/end location: 4020 Eagle Creek Blvd, Savage, MN 55378" -ForegroundColor White
    Write-Host "  3. Assign territory 'South Metro — Primary' to all 3 techs" -ForegroundColor White
    Write-Host "  4. Verify all 3 appear in Schedule Board → Resources pane" -ForegroundColor White
}

# ─────────────────────────────────────────────────────────────────
# 8. FIELD SERVICE WORK ORDERS (msdyn_workorders)
#    IMPORTANT: These are SEPARATE from CS Cases (incidents).
#    D365 Field Service uses msdyn_workorders as its primary entity.
#    Cases link to work orders via msdyn_servicerequest lookup.
#    Without these, the Schedule Board will be EMPTY.
# ─────────────────────────────────────────────────────────────────
if ($Action -in "All","WorkOrders") {
    Write-Host "`n  ── Field Service Work Orders (msdyn_workorders) ──" -ForegroundColor Yellow
    Write-Host "  Note: These are DIFFERENT from CS cases. Schedule Board uses msdyn_workorders." -ForegroundColor DarkGray

    # Load previously created IDs
    $accountIds = @{}
    $loadedA = Get-Content "$DataDir\account_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedA) { $loadedA.PSObject.Properties | ForEach-Object { $accountIds[$_.Name] = $_.Value } }

    $contactIds = @{}
    $loadedC = Get-Content "$DataDir\contact_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedC) { $loadedC.PSObject.Properties | ForEach-Object { $contactIds[$_.Name] = $_.Value } }

    $wotIds = @{}
    $loadedWOT = Get-Content "$DataDir\work_order_type_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedWOT) { $loadedWOT.PSObject.Properties | ForEach-Object { $wotIds[$_.Name] = $_.Value } }

    $itIds = @{}
    $loadedIT = Get-Content "$DataDir\incident_type_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedIT) { $loadedIT.PSObject.Properties | ForEach-Object { $itIds[$_.Name] = $_.Value } }

    $caseIds = @{}
    $loadedCS = Get-Content "$DataDir\case_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedCS) { $loadedCS.PSObject.Properties | ForEach-Object { $caseIds[$_.Name] = $_.Value } }

    $heroCaseIds = @{}
    $loadedHero = Get-Content "$DataDir\hero_case_ids.json" -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($loadedHero) { $loadedHero.PSObject.Properties | ForEach-Object { $heroCaseIds[$_.Name] = $_.Value } }

    $allCaseIds = $caseIds + $heroCaseIds

    # FS Work Order system status codes:
    #   690970000 = Unscheduled  690970001 = Scheduled
    #   690970002 = In Progress  690970003 = Completed  690970004 = Posted  690970005 = Canceled
    $fsWorkOrders = @(
        @{
            name         = "WO-2026-001 — Seal Failure / Water Intrusion (Parts Pending)"
            account      = "Andersen Exteriors Savage"
            contact      = "Mike Bergstrom"
            woType       = "Warranty — Assessment"
            incidentType = "Window Repair — Seal / Weatherstrip"
            status       = 690970002   # In Progress — waiting on parts
            priority     = 1           # High
            instructions = "HOMEOWNER: Sarah Kowalski, 14832 Birchwood Ave, Prior Lake MN. Casement seal failure — water intrusion at frame corner. Manufacturer warranty claim submitted. Replacement seal kit ordered (PART-SEAL-AND-400). ETA 12-14 business days. WO ON HOLD pending parts arrival. Josh will text homeowner when parts confirmed."
            address      = "14832 Birchwood Ave, Prior Lake, MN 55372"
            duration     = 120
            caseLink     = "Andersen 400 Casement — Seal Failure / Water Intrusion"
        },
        @{
            name         = "WO-2026-002 — Pella Slider Operator Failure (Scheduled Thu)"
            account      = "Pella Pro Contractors MN"
            contact      = "Tyler Schroeder"
            woType       = "Service — Window Repair"
            incidentType = "Window Repair — Mechanism / Hardware"
            status       = 690970001   # Scheduled
            priority     = 2           # Normal
            instructions = "HOMEOWNER: James Paulsen, 3821 Burning Tree Ln, Burnsville MN. Pella Impervia slider operator stripped — window cannot lock. PART-OPR-MEC IN STOCK at Savage warehouse. Derek Olson scheduled Thursday 10:00am. Homeowner confirmed via SMS. Estimated 90 min. Pick up part before leaving warehouse."
            address      = "3821 Burning Tree Ln, Burnsville, MN 55337"
            duration     = 90
            caseLink     = "Pella Impervia Slider — Operator Mechanism Failure"
        },
        @{
            name         = "WO-2026-003 — Screen Replacement 12-Unit (Completed)"
            account      = "Prairie Windows & Doors"
            contact      = "Debra Haugen"
            woType       = "Service — Screen Replacement"
            incidentType = "Screen Replacement"
            status       = 690970003   # Completed
            priority     = 3           # Low
            instructions = "12 window screens replaced at Prairie Windows & Doors Shakopee. Sam Rivera completed Tue Apr 8. All 12 units done, pre/post photos captured, parts logged. Completion report emailed to Debra Haugen and Tyler Schroeder (sales rep). Customer signed off."
            address      = "4455 Market Blvd, Shakopee, MN 55379"
            duration     = 180
            caseLink     = "Screen Replacement — 12-Unit Prairie Windows Project"
        },
        @{
            name         = "WO-2026-004 — Balance Spring Failure (Unscheduled — Demo Dispatch)"
            account      = "Andersen Exteriors Savage"
            contact      = "Mike Bergstrom"
            woType       = "Service — Window Repair"
            incidentType = "Window Repair — Mechanism / Hardware"
            status       = 690970000   # Unscheduled — DEMO: drag to Schedule Board
            priority     = 2           # Normal
            instructions = "HOMEOWNER: TBD — same ABC Supply Savage account (confirm address with Mike). Master bedroom casement won't stay open — balance spring broken. PART-BAL-KIT IN STOCK at Savage warehouse. Quick 75-min job. Possibly combine with WO-2026-001 followup if Derek is in Prior Lake area. DEMO: use Schedule Optimization to assign and show AI-suggested time slot."
            address      = "Confirm with Mike Bergstrom — Prior Lake area"
            duration     = 75
            caseLink     = "Casement Window — Balance Spring Broken / Won't Stay Open"
        }
    )

    $woIds = @{}
    foreach ($wo in $fsWorkOrders) {
        $existing = $null
        try {
            $enc = [System.Web.HttpUtility]::UrlEncode($wo.name)
            $existing = (Invoke-DataverseRequest -Method GET `
                -Url "$ApiBase/msdyn_workorders?`$filter=msdyn_name eq '$enc'&`$select=msdyn_workorderid" `
                -ErrorAction SilentlyContinue).value | Select-Object -First 1
        } catch {}

        if ($existing) {
            Write-Host "  [SKIP] Work Order exists: $($wo.name.Substring(0,[Math]::Min(55,$wo.name.Length)))..." -ForegroundColor DarkGray
            $woIds[$wo.name] = $existing.msdyn_workorderid
            continue
        }

        $body = @{
            msdyn_name              = $wo.name
            msdyn_instructions      = $wo.instructions
            msdyn_priority          = $wo.priority
            msdyn_systemstatus      = $wo.status
            msdyn_estimatedduration = $wo.duration
        }

        # Lookups (bind only if ID exists)
        $acctId = $accountIds[$wo.account]
        $ctcId  = $contactIds[$wo.contact]
        $wotId  = $wotIds[$wo.woType]
        $itId   = $itIds[$wo.incidentType]
        $caseId = $allCaseIds[$wo.caseLink]

        if ($acctId) { $body["msdyn_serviceaccount@odata.bind"]       = "/accounts($acctId)" }
        if ($ctcId)  { $body["msdyn_reportedbycontact@odata.bind"]    = "/contacts($ctcId)" }
        if ($wotId)  { $body["msdyn_workordertype@odata.bind"]         = "/msdyn_workordertypes($wotId)" }
        if ($itId)   { $body["msdyn_primaryincidenttype@odata.bind"]   = "/msdyn_incidenttypes($itId)" }
        if ($caseId) { $body["msdyn_servicerequest@odata.bind"]        = "/incidents($caseId)" }

        try {
            $resp = Invoke-DataverseRequest -Method POST -Url "$ApiBase/msdyn_workorders" -Body $body
            $shortName = $wo.name.Substring(0,[Math]::Min(55,$wo.name.Length))
            Write-Host "  [CREATE] Work Order: $shortName..." -ForegroundColor Green
            Write-Host "           ID: $($resp.msdyn_workorderid)" -ForegroundColor DarkGray
            $woIds[$wo.name] = $resp.msdyn_workorderid
        } catch {
            Write-Warning "  Work Order FAILED: $($wo.name) — $($_.Exception.Message)"
        }
    }

    $woIds | ConvertTo-Json | Set-Content "$DataDir\fieldservice_wo_ids.json"
    Write-Host "  FS Work Order IDs saved → $DataDir\fieldservice_wo_ids.json" -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "  MANUAL STEPS for Schedule Board demo prep:" -ForegroundColor Yellow
    Write-Host "  1. Open Field Service → Schedule Board" -ForegroundColor White
    Write-Host "     Verify WO-2026-002 (Pella Slider) appears as scheduled on Derek Thu 10am" -ForegroundColor DarkGray
    Write-Host "  2. WO-2026-004 (Balance Spring) should be in Unscheduled Work Orders panel" -ForegroundColor White
    Write-Host "     DEMO: drag it onto Derek's timeline or use Schedule Optimization" -ForegroundColor DarkGray
    Write-Host "  3. WO-2026-001 (Seal Failure) should show status 'In Progress — Parts Pending'" -ForegroundColor White
    Write-Host "  4. WO-2026-003 (Screens) should show status 'Completed' with completion summary" -ForegroundColor White
}

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor Green
Write-Host "  ABC Supply Field Service Config Complete" -ForegroundColor Green
Write-Host ""
Write-Host "  WHAT WAS PROVISIONED:" -ForegroundColor Yellow
Write-Host "  ✅ Incident Types (10 — window/door repair categories)" -ForegroundColor White
Write-Host "  ✅ Inspection Templates (2 — Service Checklist + Seal Assessment)" -ForegroundColor White
Write-Host "  ✅ Work Order Types (7)" -ForegroundColor White
Write-Host "  ✅ Territories (3 — South Metro coverage zones)" -ForegroundColor White
Write-Host "  ✅ Characteristics / Tech Skills (8)" -ForegroundColor White
Write-Host "  ✅ Service Task Types (13 + linked to incident types)" -ForegroundColor White
Write-Host "  ✅ Bookable Resources (Derek Olson, Sam Rivera, Chris Paulson + skills)" -ForegroundColor White
Write-Host "  ✅ Field Service Work Orders (4 linked to CS cases)" -ForegroundColor White
Write-Host ""
Write-Host "  STILL MANUAL (requires D365 UI):" -ForegroundColor Yellow
Write-Host "   1. Publish Inspection Templates:" -ForegroundColor White
Write-Host "      Field Service Settings → Inspection Templates → select each → Publish" -ForegroundColor DarkGray
Write-Host "   2. Set working hours for each tech (M-F 7:30am-5:00pm):" -ForegroundColor White
Write-Host "      FS → Resources → Derek/Sam/Chris → Work Hours" -ForegroundColor DarkGray
Write-Host "   3. Set start/end location: 4020 Eagle Creek Blvd, Savage MN 55378" -ForegroundColor White
Write-Host "   4. Assign 'South Metro — Primary' territory to all 3 resources" -ForegroundColor White
Write-Host "   5. Schedule WO-2026-002 (Pella Slider) to Derek Thu 10am on Schedule Board" -ForegroundColor White
Write-Host "   6. Verify WO-2026-004 (Balance Spring) shows in Unscheduled WOs panel" -ForegroundColor White
Write-Host ("═" * 60) -ForegroundColor Green
