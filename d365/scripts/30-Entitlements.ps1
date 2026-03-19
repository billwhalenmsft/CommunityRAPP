<#
.SYNOPSIS
    Step 30 - Provision Entitlements for Otis Signature Service Plans
.DESCRIPTION
    Creates D365 Entitlement records for each service account based on
    their Signature Service plan tier from demo-data.json.

    Entitlements define what coverage the customer gets when work orders
    or cases are created:
      - Signature Service Premium → 100% coverage, 2hr SLA
      - Signature Service Plus    → 100% maint / 50% callback, 4hr SLA
      - Signature Service         → 50% coverage, 8hr SLA
      - On-Call Only              → 0% coverage (T&M), 24hr SLA

    Each entitlement is linked to the customer account and can be
    referenced by Field Service work orders and CS cases.

.PARAMETER Customer
    Customer folder name under customers/ (e.g. "otis")

.PARAMETER Cleanup
    If set, deactivates and deletes entitlements created by this script

.EXAMPLE
    .\30-Entitlements.ps1 -Customer otis
    .\30-Entitlements.ps1 -Customer otis -Cleanup
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Customer,

    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "30" "Entitlements (Signature Service Plans)"
Connect-Dataverse

# ============================================================
# Load customer demo data
# ============================================================
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$demoDataPath = Join-Path $repoRoot "customers\$Customer\d365\config\demo-data.json"

if (-not (Test-Path $demoDataPath)) {
    Write-Error "Demo data not found at: $demoDataPath"
    return
}

$demoData = Get-Content $demoDataPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "Loaded demo data for: $($demoData._metadata.customer)" -ForegroundColor Cyan

# ============================================================
# Build service plan lookup from demo-data.json
# ============================================================
$servicePlans = @{}
foreach ($plan in $demoData.products.serviceContracts) {
    $servicePlans[$plan.name] = $plan
}

# ============================================================
# Entitlement type mapping
#   0 = Amount of hours, 1 = Number of cases, 2 = Coverage dates
# ============================================================
$entitlementType = 0  # 0=Cases, 1=Hours, 192350000=Work Orders

# SLA KPI instance type for entitlements
$slaKpiMap = @{
    "Signature Service Premium" = 120     # 2 hours in minutes
    "Signature Service Plus"    = 240     # 4 hours in minutes
    "Signature Service"         = 480     # 8 hours in minutes
    "On-Call Only"              = 1440    # 24 hours in minutes
}

# ============================================================
# Resolve accounts → GUID cache
# ============================================================
$accountCache = @{}

function Get-AccountId {
    param([string]$AccountNumber)

    if ($accountCache.ContainsKey($AccountNumber)) {
        return $accountCache[$AccountNumber]
    }

    $escapedNum = $AccountNumber -replace "'", "''"
    $found = Invoke-DataverseGet -EntitySet "accounts" `
        -Filter "accountnumber eq '$escapedNum'" `
        -Select "accountid,name" -Top 1

    if ($found -and $found.Count -gt 0) {
        $id = [guid]$found[0].accountid
        $accountCache[$AccountNumber] = $id
        return $id
    }

    Write-Warning "Account not found: $AccountNumber"
    return $null
}

# ============================================================
# Cleanup mode
# ============================================================
if ($Cleanup) {
    Write-Host "`nCleaning up entitlements..." -ForegroundColor Yellow

    $existing = @(Invoke-DataverseGet -EntitySet "entitlements" `
        -Filter "startswith(name,'Otis Signature')" `
        -Select "entitlementid,name,statecode")

    foreach ($ent in $existing) {
        $id = $ent.entitlementid
        Write-Host "  Deleting: $($ent.name) ($id)" -ForegroundColor Red

        # Deactivate first if active (statecode = 1 is active)
        if ($ent.statecode -eq 1) {
            try {
                Invoke-DataversePatch -EntitySet "entitlements" -RecordId ([guid]$id) -Body @{ statecode = 0 }
            } catch {
                Write-Warning "  Could not deactivate $id : $_"
            }
        }

        try {
            Invoke-DataverseDelete -EntitySet "entitlements" -RecordId ([guid]$id)
        } catch {
            Write-Warning "  Could not delete $id : $_"
        }
    }

    Write-Host "Cleanup complete." -ForegroundColor Green
    return
}

# ============================================================
# Create entitlements per account
# ============================================================
$accounts = $demoData.serviceAccounts.accounts
$created = 0
$skipped = 0

Write-Host "`nProvisioning entitlements for $($accounts.Count) accounts..." -ForegroundColor Cyan

foreach ($acct in $accounts) {
    $contractName = $acct.contract
    $plan = $servicePlans[$contractName]

    if (-not $plan) {
        Write-Warning "  No service plan found for contract '$contractName' on $($acct.name)"
        $skipped++
        continue
    }

    $accountId = Get-AccountId -AccountNumber $acct.accountNumber
    if (-not $accountId) {
        $skipped++
        continue
    }

    $entitlementName = "Otis Signature - $($acct.name)"
    $durationMonths = if ($plan.entitlement.durationMonths) { $plan.entitlement.durationMonths } else { 36 }
    $startDate = (Get-Date).AddMonths(-6).ToString("yyyy-MM-dd")
    $endDate = (Get-Date).AddMonths($durationMonths - 6).ToString("yyyy-MM-dd")

    # Build entitlement body (case-based for Customer Service)
    $body = @{
        "name"                                     = $entitlementName
        "description"                              = "$contractName - $($plan.entitlement.description)"
        "allocationtypecode"                        = $entitlementType
        "startdate"                                = $startDate
        "enddate"                                  = $endDate
        "customerid_account@odata.bind"            = "/accounts($accountId)"
        "msdyn_percentdiscount"                    = [double]$plan.entitlement.discountPercent
    }

    $entId = Find-OrCreate-Record `
        -EntitySet "entitlements" `
        -Filter "name eq '$($entitlementName -replace "'","''")'" `
        -IdField "entitlementid" `
        -Body $body `
        -DisplayName $entitlementName

    if ($entId) {
        $created++
        Write-Host "  [OK] $entitlementName  [$contractName]  ($startDate -> $endDate)" -ForegroundColor Green

        # Activate the entitlement (statecode=1 = Active)
        try {
            Invoke-DataversePatch -EntitySet "entitlements" -RecordId ([guid]$entId) -Body @{ statecode = 1 }
            Write-Host "    -> Activated" -ForegroundColor DarkGreen
        } catch {
            Write-Host "    -> Activation skipped (may already be active or require approval)" -ForegroundColor DarkYellow
        }
    } else {
        Write-Warning "  [FAIL] Failed to create entitlement for $($acct.name)"
        $skipped++
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Entitlements Created: $created" -ForegroundColor Green
Write-Host "  Skipped / Errors:    $skipped" -ForegroundColor $(if ($skipped -gt 0) { "Yellow" } else { "Green" })
Write-Host ("=" * 60) -ForegroundColor Cyan

# ============================================================
# Save output for reference
# ============================================================
$outputDir = Join-Path $repoRoot "customers\$Customer\d365\data"
if (-not (Test-Path $outputDir)) { New-Item -Path $outputDir -ItemType Directory -Force | Out-Null }

$summary = @{
    step       = 30
    script     = "30-Entitlements.ps1"
    customer   = $Customer
    created    = $created
    skipped    = $skipped
    timestamp  = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    plans      = @($servicePlans.Values | ForEach-Object {
        @{ name = $_.name; code = $_.code; sla = $_.slaResponse; tier = $_.tier }
    })
}

$summary | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outputDir "30-entitlements-output.json") -Encoding UTF8
Write-Host "Output saved to: customers\$Customer\d365\data\30-entitlements-output.json" -ForegroundColor DarkGray
