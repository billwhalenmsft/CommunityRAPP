# assign-shifts.ps1 - Create bookable resource bookings to assign agents to shift plans
# This script creates individual activity bookings for each agent-shift-date combination

param(
    [switch]$WhatIf
)

# --- Auth ---
# Uses $base and $ph from the caller's session (set by terminal or parent script)
if (-not $base -or -not $ph) {
    $org = "https://orgecbce8ef.crm.dynamics.com"
    $base = "$org/api/data/v9.2"
    $token = (az account get-access-token --resource $org --query accessToken -o tsv)
    if (-not $token) { throw "Failed to get access token. Run 'az login' first." }
    $h = @{ Authorization = "Bearer $token"; "OData-MaxVersion" = "4.0"; "OData-Version" = "4.0" }
    $ph = $h + @{ "Content-Type" = "application/json" }
    Write-Host "Acquired fresh token" -ForegroundColor Gray
} else {
    Write-Host "Using existing session auth" -ForegroundColor Gray
}

# --- Constants ---
$bookingStatusRef = "/bookingstatuses(0adbf4e6-86cc-4db0-9dbb-51b7d1ed4020)"
$setupMetaRef = "/msdyn_bookingsetupmetadatas(4beb9fdb-48e9-453f-b008-5862ff902c5d)"

# Activity type IDs
$ACT = @{
    CaseWork    = "b18a7088-ab1a-f111-8341-6045bda80a72"
    Break       = "b38a7088-ab1a-f111-8341-6045bda80a72"
    Lunch       = "b48a7088-ab1a-f111-8341-6045bda80a72"
    Training    = "b58a7088-ab1a-f111-8341-6045bda80a72"
    TeamMeeting = "b68a7088-ab1a-f111-8341-6045bda80a72"
    Coaching    = "a8f0748e-ab1a-f111-8341-6045bda80a72"
}

$ACT_NAME = @{
    CaseWork    = "Case Work"
    Break       = "Break"
    Lunch       = "Lunch"
    Training    = "Training"
    TeamMeeting = "Team Meeting"
    Coaching    = "Coaching"
}

# Shift plan IDs
$SHIFT = @{
    Morning   = "abf0748e-ab1a-f111-8341-6045bda80a72"
    Day       = "da8d5195-ab1a-f111-8342-7ced8d18c8d7"
    Afternoon = "9718b59c-ab1a-f111-8341-6045bda80a72"
    Staggered = "19e841a2-ab1a-f111-8342-7ced8d18c8d7"
    Weekend   = "992cc7a3-ab1a-f111-8341-6045bda80a72"
}

# --- Activity patterns per shift (UTC offsets from midnight) ---
# Each entry: @(startHour, startMin, endHour, endMin, activityKey)
# Times are UTC. Timezone 20 = Central (CST=UTC-6; after Mar 8 CDT=UTC-5, but we keep UTC-6 to match existing bookings)

# Day Shift: 14:00-23:00 UTC (8AM-5PM CT), 9h = 540m
$DayPattern = @(
    @(14, 0, 15, 0, "CaseWork"),     # 60m
    @(15, 0, 16, 0, "CaseWork"),     # 60m
    @(16, 0, 16, 15, "Break"),        # 15m
    @(16, 15, 17, 15, "CaseWork"),     # 60m
    @(17, 15, 17, 45, "TeamMeeting"),  # 30m
    @(17, 45, 18, 0, "Break"),        # 15m
    @(18, 0, 19, 0, "Lunch"),        # 60m
    @(19, 0, 20, 0, "CaseWork"),     # 60m
    @(20, 0, 21, 0, "CaseWork"),     # 60m
    @(21, 0, 22, 0, "CaseWork"),     # 60m
    @(22, 0, 23, 0, "CaseWork")      # 60m
)

# Morning Shift: 12:00-20:00 UTC (6AM-2PM CT), 8h = 480m
$MorningPattern = @(
    @(12, 0, 13, 0, "CaseWork"),     # 60m
    @(13, 0, 14, 0, "CaseWork"),     # 60m
    @(14, 0, 14, 15, "Break"),        # 15m
    @(14, 15, 14, 45, "Coaching"),     # 30m
    @(14, 45, 15, 45, "Lunch"),        # 60m
    @(15, 45, 16, 15, "TeamMeeting"),  # 30m
    @(16, 15, 17, 15, "CaseWork"),     # 60m
    @(17, 15, 18, 45, "CaseWork"),     # 90m
    @(18, 45, 20, 0, "CaseWork")      # 75m
)

# Afternoon Shift: 20:00-04:00 UTC (2PM-10PM CT), 8h = 480m
# NOTE: Crosses midnight UTC - endtime date = startdate + 1
$AfternoonPattern = @(
    @(20, 0, 21, 0, "CaseWork"),     # 60m
    @(21, 0, 22, 0, "CaseWork"),     # 60m
    @(22, 0, 22, 15, "Break"),        # 15m
    @(22, 15, 23, 15, "CaseWork"),     # 60m
    @(23, 15, 0, 15, "Lunch"),        # 60m  (crosses midnight)
    @(0, 15, 1, 15, "Training"),     # 60m  (next day)
    @(1, 15, 2, 15, "CaseWork"),     # 60m
    @(2, 15, 3, 15, "CaseWork"),     # 60m
    @(3, 15, 4, 0, "CaseWork")      # 45m
)

# Staggered Shift: 13:00-21:00 UTC (7AM-3PM CT), 8h = 480m
$StaggeredPattern = @(
    @(13, 0, 14, 0, "CaseWork"),     # 60m
    @(14, 0, 15, 0, "CaseWork"),     # 60m
    @(15, 0, 15, 15, "Break"),        # 15m
    @(15, 15, 15, 45, "Coaching"),     # 30m
    @(15, 45, 16, 45, "Lunch"),        # 60m
    @(16, 45, 17, 45, "CaseWork"),     # 60m
    @(17, 45, 18, 45, "CaseWork"),     # 60m
    @(18, 45, 19, 45, "CaseWork"),     # 60m
    @(19, 45, 21, 0, "CaseWork")      # 75m
)

# Weekend Shift: 14:00-20:00 UTC (8AM-2PM CT), 6h = 360m
$WeekendPattern = @(
    @(14, 0, 15, 0, "CaseWork"),     # 60m
    @(15, 0, 16, 0, "CaseWork"),     # 60m
    @(16, 0, 16, 15, "Break"),        # 15m
    @(16, 15, 17, 15, "Lunch"),        # 60m
    @(17, 15, 18, 15, "CaseWork"),     # 60m
    @(18, 15, 19, 15, "CaseWork"),     # 60m
    @(19, 15, 20, 0, "CaseWork")      # 45m
)

# --- Agent-to-shift assignments ---
# BR IDs for each agent
$BR = @{
    ReneeLo         = "9c348d13-2a5b-ef11-bfe2-6045bdeeb65d"
    AliciaThomber   = "5a9babd0-df1b-f111-8341-6045bda80a72"
    MollyClark      = "1a96a5f3-df1b-f111-8341-6045bda80a72"
    SpencerLow      = "2fdef173-52d5-f011-8543-6045bded8e22"
    AlanSteiner     = "cd790c0f-e2c6-ef11-b8e8-7c1e524805ed"
    BillTechnician  = "807fccd7-d454-ef11-a317-6045bdd67169"
    MarkusLong      = "8b348d13-2a5b-ef11-bfe2-6045bdeeb65d"
    DavidSo         = "063dcf90-b53a-ee11-bdf4-000d3a3386ed"
    TylerStein      = "77bbbfce-e01b-f111-8341-6045bda80a72"
    JamieReding     = "69a777f7-df1b-f111-8341-7c1e525aaad4"
    ClaudiaMazzanti = "2fb621cd-e01b-f111-8342-7c1e52143136"
    EnricoCattaneo  = "df3c0609-745c-4bc6-b9b3-4ce4d751adf6"
    AlexBaker       = "ac09c606-df1b-f111-8342-7c1e52143136"
    RileyRamirez    = "431c56f5-df1b-f111-8342-7ced8d18cb3b"
}

# Assignments: ShiftName -> @(agentKey1, agentKey2, ...)
# Alan Steiner + Bill Technician already have Day shift bookings - SKIP
$Assignments = @{
    Morning   = @("ReneeLo", "AliciaThomber", "MollyClark", "SpencerLow")
    Day       = @("MarkusLong", "DavidSo", "TylerStein")   # Alan+Bill already exist
    Afternoon = @("JamieReding", "ClaudiaMazzanti", "EnricoCattaneo")
    Staggered = @("AlexBaker", "RileyRamirez")
    Weekend   = @("TylerStein", "RileyRamirez")            # overlap with weekday
}

$Patterns = @{
    Morning   = $MorningPattern
    Day       = $DayPattern
    Afternoon = $AfternoonPattern
    Staggered = $StaggeredPattern
    Weekend   = $WeekendPattern
}

# --- Dates ---
# Weekdays: Mon-Fri for 2 weeks starting March 2, 2026
$weekdays = @("2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06",
    "2026-03-09", "2026-03-10", "2026-03-11", "2026-03-12", "2026-03-13")
# Weekends: Sat+Sun in same range
$weekends = @("2026-03-01", "2026-03-07", "2026-03-08", "2026-03-14")

$ShiftDates = @{
    Morning   = $weekdays
    Day       = $weekdays
    Afternoon = $weekdays
    Staggered = $weekdays
    Weekend   = $weekends
}

# --- Helper: build datetime string ---
function Get-BookingTime($dateStr, $hour, $minute, $crossesMidnight) {
    $d = [datetime]::ParseExact($dateStr, "yyyy-MM-dd", $null)
    if ($crossesMidnight) { $d = $d.AddDays(1) }
    return $d.ToString("yyyy-MM-dd") + "T" + ("{0:D2}" -f $hour) + ":" + ("{0:D2}" -f $minute) + ":00Z"
}

# --- Main loop ---
$totalCreated = 0
$totalFailed = 0
$errorLog = @()

foreach ($shiftName in @("Morning", "Day", "Afternoon", "Staggered", "Weekend")) {
    $shiftPlanId = $SHIFT[$shiftName]
    $pattern = $Patterns[$shiftName]
    $agents = $Assignments[$shiftName]
    $dates = $ShiftDates[$shiftName]
    
    Write-Host "`n=== $shiftName Shift ===" -ForegroundColor Cyan
    Write-Host "  Plan: $shiftPlanId | Agents: $($agents.Count) | Dates: $($dates.Count) | Activities: $($pattern.Count)"
    Write-Host "  Total bookings: $($agents.Count * $dates.Count * $pattern.Count)"
    
    foreach ($agentKey in $agents) {
        $brId = $BR[$agentKey]
        Write-Host "  Agent: $agentKey ($brId)" -ForegroundColor Yellow
        
        foreach ($dateStr in $dates) {
            foreach ($entry in $pattern) {
                $startH = $entry[0]; $startM = $entry[1]; $endH = $entry[2]; $endM = $entry[3]; $actKey = $entry[4]
                $actId = $ACT[$actKey]
                $actName = $ACT_NAME[$actKey]
                
                # Handle afternoon shift crossing midnight
                $startCrosses = $false
                $endCrosses = $false
                if ($shiftName -eq "Afternoon") {
                    if ($startH -lt 20) { $startCrosses = $true }  # 0-4 AM = next day
                    if ($endH -lt 20) { $endCrosses = $true }
                    # Fix: only hours 0-4 are next day
                    if ($startH -ge 20) { $startCrosses = $false }
                    if ($endH -ge 20 -or $endH -eq 0) { 
                        if ($endH -eq 0) { $endCrosses = $true }
                        else { $endCrosses = $false }
                    }
                    if ($startH -ge 0 -and $startH -lt 5) { $startCrosses = $true }
                    if ($endH -ge 0 -and $endH -lt 5) { $endCrosses = $true }
                }
                
                $startTime = Get-BookingTime $dateStr $startH $startM $startCrosses
                $endTime = Get-BookingTime $dateStr $endH $endM $endCrosses
                $duration = ([datetime]$endTime - [datetime]$startTime).TotalMinutes
                
                $body = @{
                    "Resource@odata.bind"                     = "/bookableresources($brId)"
                    "msdyn_shiftplan@odata.bind"              = "/msdyn_shiftplans($shiftPlanId)"
                    "msdyn_shiftactivitytype@odata.bind"      = "/msdyn_shiftactivitytypes($actId)"
                    "BookingStatus@odata.bind"                = $bookingStatusRef
                    "msdyn_BookingSetupMetadataId@odata.bind" = $setupMetaRef
                    bookingtype                               = 1
                    msdyn_effort                              = 1.0
                    msdyn_worklocation                        = 690970002
                    msdyn_bookingmethod                       = 690970003
                    msdyn_traveltimecalculationtype           = 192350000
                    msdyn_quickNoteAction                     = 100000000
                    name                                      = $actName
                    duration                                  = [int]$duration
                    starttime                                 = $startTime
                    endtime                                   = $endTime
                } | ConvertTo-Json
                
                if ($WhatIf) {
                    Write-Host "    [WHATIF] $dateStr $($startTime.Substring(11,5))-$($endTime.Substring(11,5)) $actName ($([int]$duration)m)"
                } else {
                    try {
                        Invoke-RestMethod "$base/bookableresourcebookings" -Method POST -Headers $ph -Body $body -ErrorAction Stop | Out-Null
                        $totalCreated++
                    } catch {
                        $totalFailed++
                        $errMsg = $_.Exception.Message
                        if ($_.Exception.Response) {
                            try {
                                $stream = $_.Exception.Response.GetResponseStream()
                                $reader = New-Object System.IO.StreamReader($stream)
                                $reader.BaseStream.Position = 0
                                $errMsg = $reader.ReadToEnd()
                            } catch {}
                        }
                        $errorLog += "$agentKey $dateStr $actName : $errMsg"
                        if ($totalFailed -eq 1) {
                            Write-Host "    FIRST ERROR: $errMsg" -ForegroundColor Red
                        }
                    }
                }
            }
            # Brief pause every date to avoid throttling
            if (-not $WhatIf) { Start-Sleep -Milliseconds 200 }
        }
        Write-Host "    Progress: Created=$totalCreated Failed=$totalFailed"
    }
}

Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
Write-Host "Total Created: $totalCreated"
Write-Host "Total Failed: $totalFailed"

if ($errorLog.Count -gt 0) {
    Write-Host "`nErrors:" -ForegroundColor Red
    $errorLog | ForEach-Object { Write-Host "  $_" }
}
