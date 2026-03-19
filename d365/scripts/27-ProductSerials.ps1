<#
.SYNOPSIS
    Step 27 - Provision Product Serials (Serial Warranty Lookup)
.DESCRIPTION
    Creates cr74e_productserial records from a customer's demo-data.json.
    Works with any customer that defines a "productSerials" section with
    distributor-grouped serial items.

    Each serial item generates a Product Serial record with:
      - cr74e_serialnumber    (Serial ID, e.g. "ZRN-2024-10100")
      - cr74e_productname     (Product Name, e.g. "Zurn AquaVantage AV Flush Valve")
      - cr74e_warrantystart   (Warranty Start date)
      - cr74e_warrantyend     (Warranty End date)
      - cr74e_originalordernumber (Order Number, e.g. "PO-94820")
      - cr74e_customer        (Customer-type column, bound to distributor account)

    Designed to be called from the shared 00-Setup.ps1 orchestrator or
    run standalone for any customer.

.PARAMETER Customer
    Customer folder name under customers/ (e.g. "zurnelkay")

.PARAMETER Cleanup
    If set, removes all Product Serials created by this script

.EXAMPLE
    .\27-ProductSerials.ps1 -Customer zurnelkay
    .\27-ProductSerials.ps1 -Customer zurnelkay -Cleanup
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

Write-StepHeader "27" "Product Serials (Serial Warranty Lookup)"
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

$demoData = Get-Content $demoDataPath -Raw | ConvertFrom-Json
Write-Host "Loaded demo data for: $($demoData._metadata.customer)" -ForegroundColor Cyan

if (-not $demoData.productSerials) {
    Write-Host "No productSerials section in demo-data.json — nothing to do." -ForegroundColor Yellow
    return
}

# ============================================================
# Resolve distributor accounts → GUID cache
# ============================================================
$accountCache = @{}

function Get-AccountIdByName {
    param([string]$AccountName)

    if ($accountCache.ContainsKey($AccountName)) {
        return $accountCache[$AccountName]
    }

    $escapedName = $AccountName -replace "'", "''"
    $found = Invoke-DataverseGet -EntitySet "accounts" `
        -Filter "name eq '$escapedName'" `
        -Select "accountid,name" -Top 1

    if ($found -and $found.Count -gt 0) {
        $id = [guid]$found[0].accountid
        $accountCache[$AccountName] = $id
        return $id
    }
    return $null
}

# ============================================================
# CLEANUP
# ============================================================
if ($Cleanup) {
    Write-Host "Removing Product Serials for $Customer..." -ForegroundColor Red
    $confirm = Read-Host "Type 'DELETE' to confirm"
    if ($confirm -ne "DELETE") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        return
    }

    foreach ($group in $demoData.productSerials.serials) {
        Write-Host "  Deleting serials for: $($group.customer)" -ForegroundColor Gray
        foreach ($item in $group.items) {
            $escapedSerial = $item.serialNumber -replace "'", "''"
            $existing = Invoke-DataverseGet -EntitySet "cr74e_productserials" `
                -Filter "cr74e_serialnumber eq '$escapedSerial'" `
                -Select "cr74e_productserialid,cr74e_serialnumber" -Top 1

            if ($existing -and $existing.Count -gt 0) {
                Invoke-DataverseDelete -EntitySet "cr74e_productserials" -Id ([guid]$existing[0].cr74e_productserialid)
                Write-Host "    Deleted: $($item.serialNumber)" -ForegroundColor DarkRed
            }
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
    return
}

# ============================================================
# PROVISION
# ============================================================
$totalCreated = 0
$totalSkipped = 0
$totalFailed  = 0

$groups = $demoData.productSerials.serials
Write-Host "Processing $($groups.Count) distributor groups..." -ForegroundColor Yellow

foreach ($group in $groups) {
    $customerName = $group.customer
    $accountId = Get-AccountIdByName -AccountName $customerName

    if (-not $accountId) {
        Write-Host "`n  SKIP GROUP: Account '$customerName' not found in Dataverse" -ForegroundColor DarkYellow
        continue
    }

    Write-Host "`n  Distributor: $customerName" -ForegroundColor Cyan

    foreach ($item in $group.items) {
        # Check for existing serial
        $escapedSerial = $item.serialNumber -replace "'", "''"
        $existing = Invoke-DataverseGet -EntitySet "cr74e_productserials" `
            -Filter "cr74e_serialnumber eq '$escapedSerial'" `
            -Select "cr74e_productserialid" -Top 1

        if ($existing -and $existing.Count -gt 0) {
            Write-Host "    EXISTS: $($item.serialNumber)" -ForegroundColor DarkGray
            $totalSkipped++
            continue
        }

        # cr74e_customer is a Customer-type (polymorphic) field.
        # Navigation property for account binding: cr74e_Customer_account
        $body = @{
            cr74e_serialnumber       = $item.serialNumber
            cr74e_productname        = $item.productName
            cr74e_originalordernumber = $item.orderNumber
            cr74e_warrantystart      = "$($item.warrantyStart)T00:00:00Z"
            cr74e_warrantyend        = "$($item.warrantyEnd)T00:00:00Z"
            "cr74e_Customer_account@odata.bind" = "/accounts($accountId)"
        }

        $result = Invoke-DataversePost -EntitySet "cr74e_productserials" -Body $body
        if ($result) {
            Write-Host "    CREATED: $($item.serialNumber)  ($($item.productName))" -ForegroundColor Green
            $totalCreated++
        }
        else {
            Write-Host "    FAILED: $($item.serialNumber)" -ForegroundColor Red
            $totalFailed++
        }
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Product Serials Provisioning Complete" -ForegroundColor Green
Write-Host "  Customer: $($demoData._metadata.customer)" -ForegroundColor Gray
Write-Host "  Created:  $totalCreated" -ForegroundColor Gray
Write-Host "  Skipped:  $totalSkipped (already existed)" -ForegroundColor Gray
Write-Host "  Failed:   $totalFailed" -ForegroundColor Gray
Write-Host ("=" * 60) -ForegroundColor Green
