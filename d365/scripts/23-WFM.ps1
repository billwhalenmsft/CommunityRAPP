<#
.SYNOPSIS
    Configures Workforce Management - shift activity types, time-off types,
    shift plans, and time-off requests for the Zurn Elkay demo.
.DESCRIPTION
    Step 23: Provisions WFM reference data so supervisors can demonstrate
    scheduling, forecasting, adherence, bidding, and swapping features.

    Prerequisites:
      - WFM enabled in CS Admin Center (Schedule management, Shift-based routing,
        Forecast volume, Capacity planning, Bidding, Swapping, Representative calendar)
      - Steps 01-22 complete (accounts, contacts, queues, bookable resources)
.NOTES
    Idempotent - safe to re-run. Uses Find-OrCreate-Record for all entities.
#>

param(
    [string]$CustomerPath = (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') 'customers') 'Zurn')
)

# -- Bootstrap ----------------------------------------------------------------
Import-Module (Join-Path $PSScriptRoot 'DataverseHelper.psm1') -Force
Connect-Dataverse

$dataDir = Join-Path $CustomerPath 'data'
if (-not (Test-Path $dataDir)) { New-Item -Path $dataDir -ItemType Directory -Force | Out-Null }

# ============================================================================
# 23A - Shift Activity Types
# ============================================================================
Write-StepHeader "23A" "Creating Shift Activity Types"

$shiftActivityTypes = @(
    @{
        Name        = "Case Work"
        Description = "Active case handling - emails, phone calls, and chat sessions"
        Color       = "#2196F3"   # blue
        DarkColor   = "#64B5F6"
        Duration    = 0           # variable
        Assignment  = 192350000   # Assignable
    },
    @{
        Name        = "Break"
        Description = "Paid 15-minute break"
        Color       = "#4CAF50"   # green
        DarkColor   = "#81C784"
        Duration    = 15
        Assignment  = 192350001   # Non Assignable
    },
    @{
        Name        = "Lunch"
        Description = "Unpaid 60-minute lunch period"
        Color       = "#FF9800"   # orange
        DarkColor   = "#FFB74D"
        Duration    = 60
        Assignment  = 192350001   # Non Assignable
    },
    @{
        Name        = "Training"
        Description = "Product training, system updates, or compliance modules"
        Color       = "#9C27B0"   # purple
        DarkColor   = "#CE93D8"
        Duration    = 60
        Assignment  = 192350001   # Non Assignable
    },
    @{
        Name        = "Team Meeting"
        Description = "Daily standup or weekly team sync"
        Color       = "#607D8B"   # grey-blue
        DarkColor   = "#90A4AE"
        Duration    = 30
        Assignment  = 192350001   # Non Assignable
    },
    @{
        Name        = "Coaching"
        Description = "1:1 coaching session with supervisor"
        Color       = "#00BCD4"   # cyan
        DarkColor   = "#4DD0E1"
        Duration    = 30
        Assignment  = 192350001   # Non Assignable
    }
)

$activityTypeIds = @{}
foreach ($sat in $shiftActivityTypes) {
    $body = @{
        msdyn_name                  = $sat.Name
        msdyn_description           = $sat.Description
        msdyn_color                 = $sat.Color
        msdyn_darkthemecolor        = $sat.DarkColor
        msdyn_shiftassignmentstatus = $sat.Assignment
    }
    if ($sat.Duration -gt 0) {
        $body["msdyn_duration"] = $sat.Duration
    }

    $id = Find-OrCreate-Record `
        -EntitySet "msdyn_shiftactivitytypes" `
        -Filter "msdyn_name eq '$($sat.Name)'" `
        -IdField "msdyn_shiftactivitytypeid" `
        -Body $body `
        -DisplayName $sat.Name

    $activityTypeIds[$sat.Name] = $id
    Write-Host "    $($sat.Name) => $id" -ForegroundColor DarkGray
}

# ============================================================================
# 23B - Time Off Types
# ============================================================================
Write-StepHeader "23B" "Creating Time Off Types"

$timeOffTypes = @(
    @{ Name = "Vacation"; Color = "#4CAF50"; DarkColor = "#81C784"; Description = "Planned vacation / PTO" }
    @{ Name = "Sick Leave"; Color = "#F44336"; DarkColor = "#EF9A9A"; Description = "Unplanned sick day" }
    @{ Name = "Personal"; Color = "#FF9800"; DarkColor = "#FFB74D"; Description = "Personal day" }
    @{ Name = "Company Holiday"; Color = "#2196F3"; DarkColor = "#64B5F6"; Description = "Scheduled company holiday" }
    @{ Name = "Jury Duty"; Color = "#607D8B"; DarkColor = "#90A4AE"; Description = "Court-mandated jury service" }
    @{ Name = "Bereavement"; Color = "#795548"; DarkColor = "#A1887F"; Description = "Family bereavement leave" }
    @{ Name = "Training Off-site"; Color = "#9C27B0"; DarkColor = "#CE93D8"; Description = "Off-site training or conference" }
)

$timeOffTypeIds = @{}
foreach ($tot in $timeOffTypes) {
    $id = Find-OrCreate-Record `
        -EntitySet "msdyn_timeofftypes" `
        -Filter "msdyn_name eq '$($tot.Name)'" `
        -IdField "msdyn_timeofftypeid" `
        -Body @{
        msdyn_name           = $tot.Name
        msdyn_description    = $tot.Description
        msdyn_color          = $tot.Color
        msdyn_darkthemecolor = $tot.DarkColor
    } `
        -DisplayName $tot.Name

    $timeOffTypeIds[$tot.Name] = $id
    Write-Host "    $($tot.Name) => $id" -ForegroundColor DarkGray
}

# ============================================================================
# 23C - Shift Plans
# ============================================================================
Write-StepHeader "23C" "Creating Shift Plans"

# Central Time (US) = timezone index 20
$centralTimeZone = 20

# Shift plans run for the current month + next month to give a demo window
$today = Get-Date
$planStart = Get-Date -Year $today.Year -Month $today.Month -Day 1
$planEnd = $planStart.AddMonths(2).AddDays(-1)
$planStartStr = $planStart.ToString("yyyy-MM-ddT00:00:00Z")
$planEndStr = $planEnd.ToString("yyyy-MM-ddT00:00:00Z")

# Build a JSON array of shift activity IDs for the activities block on each plan
# Each shift gets: Case Work (core), Break AM, Lunch, Break PM
$caseWorkId = $activityTypeIds["Case Work"]
$breakId = $activityTypeIds["Break"]
$lunchId = $activityTypeIds["Lunch"]
$meetingId = $activityTypeIds["Team Meeting"]

$shiftPlans = @(
    @{
        Name        = "Zurn Elkay Morning Shift"
        Description = "Early shift covering 6:00 AM - 2:00 PM CT - high-volume email processing"
        StartTime   = "1900-01-01T06:00:00Z"
        EndTime     = "1900-01-01T14:00:00Z"
        Recurrence  = "2,3,4,5,6"   # Mon-Fri
        Staff       = 4
    },
    @{
        Name        = "Zurn Elkay Day Shift"
        Description = "Core business hours 8:00 AM - 5:00 PM CT - full channel coverage"
        StartTime   = "1900-01-01T08:00:00Z"
        EndTime     = "1900-01-01T17:00:00Z"
        Recurrence  = "2,3,4,5,6"   # Mon-Fri
        Staff       = 6
    },
    @{
        Name        = "Zurn Elkay Afternoon Shift"
        Description = "Late shift covering 2:00 PM - 10:00 PM CT - West Coast and late callbacks"
        StartTime   = "1900-01-01T14:00:00Z"
        EndTime     = "1900-01-01T22:00:00Z"
        Recurrence  = "2,3,4,5,6"   # Mon-Fri
        Staff       = 3
    },
    @{
        Name        = "Zurn Elkay Staggered Shift"
        Description = "Overlap shift 7:00 AM - 3:00 PM CT - bridges morning and day shift transitions"
        StartTime   = "1900-01-01T07:00:00Z"
        EndTime     = "1900-01-01T15:00:00Z"
        Recurrence  = "2,3,4,5,6"   # Mon-Fri
        Staff       = 2
    },
    @{
        Name        = "Zurn Elkay Weekend Shift"
        Description = "Weekend coverage 8:00 AM - 2:00 PM CT - emergency and critical cases only"
        StartTime   = "1900-01-01T08:00:00Z"
        EndTime     = "1900-01-01T14:00:00Z"
        Recurrence  = "1,7"          # Sun, Sat
        Staff       = 2
    }
)

$shiftPlanIds = @{}
foreach ($sp in $shiftPlans) {
    $body = @{
        msdyn_name             = $sp.Name
        msdyn_description      = $sp.Description
        msdyn_starttime        = $sp.StartTime
        msdyn_endtime          = $sp.EndTime
        msdyn_fromdate         = $planStartStr
        msdyn_todate           = $planEndStr
        msdyn_shifttype        = 1     # Manual
        msdyn_status           = 1     # Draft (will publish after assignment)
        msdyn_requiredstaff    = $sp.Staff
        msdyn_timezone         = $centralTimeZone
        msdyn_weeklyrecurrence = $sp.Recurrence
    }

    $id = Find-OrCreate-Record `
        -EntitySet "msdyn_shiftplans" `
        -Filter "msdyn_name eq '$($sp.Name)'" `
        -IdField "msdyn_shiftplanid" `
        -Body $body `
        -DisplayName $sp.Name

    $shiftPlanIds[$sp.Name] = $id
    Write-Host "    $($sp.Name) => $id" -ForegroundColor DarkGray
}

# ============================================================================
# 23D - Time Off Requests (realistic PTO for demo)
# ============================================================================
Write-StepHeader "23D" "Creating Time Off Requests"

# Map bookable resource names to IDs (all 14 user-type bookable resources)
$agents = @{
    "Alan Steiner"     = "cd790c0f-e2c6-ef11-b8e8-7c1e524805ed"
    "Alex Baker"       = "ac09c606-df1b-f111-8342-7c1e52143136"
    "Alicia Thomber"   = "5a9babd0-df1b-f111-8341-6045bda80a72"
    "Bill Technician"  = "807fccd7-d454-ef11-a317-6045bdd67169"
    "Claudia Mazzanti" = "2fb621cd-e01b-f111-8342-7c1e52143136"
    "David So"         = "063dcf90-b53a-ee11-bdf4-000d3a3386ed"
    "Enrico Cattaneo"  = "df3c0609-745c-4bc6-b9b3-4ce4d751adf6"
    "Jamie Reding"     = "69a777f7-df1b-f111-8341-7c1e525aaad4"
    "Markus Long"      = "8b348d13-2a5b-ef11-bfe2-6045bdeeb65d"
    "Molly Clark"      = "1a96a5f3-df1b-f111-8341-6045bda80a72"
    "Renee Lo"         = "9c348d13-2a5b-ef11-bfe2-6045bdeeb65d"
    "Riley Ramirez"    = "431c56f5-df1b-f111-8342-7ced8d18cb3b"
    "Spencer Low"      = "2fdef173-52d5-f011-8543-6045bded8e22"
    "Tyler Stein"      = "77bbbfce-e01b-f111-8341-6045bda80a72"
}

# Create realistic time-off requests relative to today
$timeOffRequests = @(
    @{
        Agent     = "Renee Lo"
        Name      = "Renee Lo - Vacation"
        StartDays = 5    # 5 days from today
        EndDays   = 9    # 4-day vacation
    },
    @{
        Agent     = "Markus Long"
        Name      = "Markus Long - Training"
        StartDays = 3
        EndDays   = 3    # 1-day off-site training
    },
    @{
        Agent     = "Alan Steiner"
        Name      = "Alan Steiner - Personal Day"
        StartDays = 7
        EndDays   = 7    # 1-day personal
    },
    @{
        Agent     = "Enrico Cattaneo"
        Name      = "Enrico Cattaneo - Sick Leave"
        StartDays = -1   # yesterday (shows recent adherence impact)
        EndDays   = 0    # through today
    },
    @{
        Agent     = "David So"
        Name      = "David So - Vacation"
        StartDays = 12
        EndDays   = 16   # week-long vacation
    }
)

$timeOffRequestIds = @{}
foreach ($tor in $timeOffRequests) {
    $agentBrId = $agents[$tor.Agent]
    if (-not $agentBrId) {
        Write-Warning "Agent $($tor.Agent) not found in bookable resources - skipping"
        continue
    }

    $startDate = (Get-Date).AddDays($tor.StartDays)
    $endDate = (Get-Date).AddDays($tor.EndDays)
    $startStr = $startDate.ToString("yyyy-MM-ddT08:00:00Z")
    $endStr = $endDate.ToString("yyyy-MM-ddT17:00:00Z")

    $body = @{
        msdyn_name                  = $tor.Name
        msdyn_starttime             = $startStr
        msdyn_endtime               = $endStr
        "msdyn_resource@odata.bind" = "/bookableresources($agentBrId)"
    }

    $id = Find-OrCreate-Record `
        -EntitySet "msdyn_timeoffrequests" `
        -Filter "msdyn_name eq '$($tor.Name)'" `
        -IdField "msdyn_timeoffrequestid" `
        -Body $body `
        -DisplayName $tor.Name

    $timeOffRequestIds[$tor.Name] = $id
    Write-Host "    $($tor.Name) => $id" -ForegroundColor DarkGray
}

# ============================================================================
# 23E - Export IDs
# ============================================================================
Write-StepHeader "23E" "Exporting WFM record IDs"

$output = @{
    shiftActivityTypes = @{}
    timeOffTypes       = @{}
    shiftPlans         = @{}
    timeOffRequests    = @{}
    agents             = $agents
    planWindow         = @{
        start = $planStartStr
        end   = $planEndStr
    }
}

foreach ($key in $activityTypeIds.Keys) { $output.shiftActivityTypes[$key] = "$($activityTypeIds[$key])" }
foreach ($key in $timeOffTypeIds.Keys) { $output.timeOffTypes[$key] = "$($timeOffTypeIds[$key])" }
foreach ($key in $shiftPlanIds.Keys) { $output.shiftPlans[$key] = "$($shiftPlanIds[$key])" }
foreach ($key in $timeOffRequestIds.Keys) { $output.timeOffRequests[$key] = "$($timeOffRequestIds[$key])" }

$outputPath = Join-Path $dataDir 'wfm-ids.json'
$output | ConvertTo-Json -Depth 3 | Out-File $outputPath -Encoding utf8
Write-Host "Exported WFM IDs to $outputPath" -ForegroundColor Green

# ============================================================================
# 23F - Assign Agents to Shift Plans (bookable resource bookings)
# ============================================================================
Write-StepHeader "23F" "Assigning Agents to Shift Plans"

$assignScript = Join-Path $PSScriptRoot 'assign-shifts.ps1'
if (Test-Path $assignScript) {
    Write-Host "Running assign-shifts.ps1 to create shift bookings..." -ForegroundColor Cyan
    & $assignScript
    Write-Host "Shift assignment complete." -ForegroundColor Green
} else {
    Write-Warning "assign-shifts.ps1 not found at $assignScript - run it manually to assign agents to shifts"
}

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Step 23 Complete - Workforce Management" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Shift Activity Types : $($activityTypeIds.Count)" -ForegroundColor White
Write-Host "  Time Off Types       : $($timeOffTypeIds.Count)" -ForegroundColor White
Write-Host "  Shift Plans          : $($shiftPlanIds.Count)" -ForegroundColor White
Write-Host "  Time Off Requests    : $($timeOffRequestIds.Count)" -ForegroundColor White
Write-Host "  Agents               : $($agents.Count)" -ForegroundColor White
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Verify shift assignments in CS Admin Center > Workforce Management > Schedule Management" -ForegroundColor Yellow
Write-Host "  2. Publish shift plans if not already published (Draft -> Published)" -ForegroundColor Yellow
Write-Host "  3. Configure Forecast Volume for case/conversation channels" -ForegroundColor Yellow
Write-Host ""
