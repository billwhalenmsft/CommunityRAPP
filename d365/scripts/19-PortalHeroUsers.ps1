<#
.SYNOPSIS
    Step 19 - Provision Hero Portal Users for Zurn Elkay Customer Care portal.
.DESCRIPTION
    Ensures hero contacts exist, links them to the correct accounts, and assigns
    the Power Pages "Authenticated Users" web role for the Zurn Elkay site.

    This script is idempotent and safe to re-run.

.NOTES
    Run with: .\19-PortalHeroUsers.ps1
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Connect-Dataverse

Write-StepHeader "19" "Provision Hero Portal Users"

$apiUrl = Get-DataverseApiUrl
$headers = Get-DataverseHeaders

$siteId = "2dd891fe-1418-f111-8342-7c1e52143136"

# ------------------------------------------------------------
# Load account references
# ------------------------------------------------------------
$accountIdsPath = "$scriptDir\..\data\account-ids.json"
if (-not (Test-Path $accountIdsPath)) {
    throw "Missing data/account-ids.json. Run 01-Accounts.ps1 first."
}
$accountIds = Get-Content $accountIdsPath | ConvertFrom-Json

function Get-AccountIdByName([string]$name) {
    $groups = @("Manufacturers", "Distributors", "EndUsers")
    foreach ($groupName in $groups) {
        $group = $accountIds.$groupName
        if ($group -and ($group.PSObject.Properties.Name -contains $name)) {
            return $group.$name
        }
    }

    $fallback = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$name'" -Select "accountid" -Top 1
    if ($fallback -and $fallback.Count -gt 0) {
        return $fallback[0].accountid
    }
    return $null
}

function Ensure-Contact {
    param(
        [Parameter(Mandatory)][hashtable]$UserDef
    )

    $acctId = Get-AccountIdByName $UserDef.AccountName
    if (-not $acctId) {
        throw "Account not found for '$($UserDef.AccountName)'"
    }

    $body = @{
        firstname                             = $UserDef.FirstName
        lastname                              = $UserDef.LastName
        emailaddress1                         = $UserDef.Email
        telephone1                            = $UserDef.Phone
        jobtitle                              = $UserDef.Title
        "parentcustomerid_account@odata.bind" = "/accounts($acctId)"
    }

    $contactId = Find-OrCreate-Record `
        -EntitySet "contacts" `
        -Filter "emailaddress1 eq '$($UserDef.Email)'" `
        -IdField "contactid" `
        -Body $body `
        -DisplayName "$($UserDef.FirstName) $($UserDef.LastName)"

    # Always enforce account linkage in case contact pre-existed under another account
    Invoke-DataversePatch -EntitySet "contacts" -RecordId $contactId -Body @{
        "parentcustomerid_account@odata.bind" = "/accounts($acctId)"
    } | Out-Null

    return $contactId
}

function Ensure-RoleMembership {
    param(
        [Parameter(Mandatory)][string]$ContactId,
        [Parameter(Mandatory)][string]$RoleId
    )

    $associateUrl = "$apiUrl/contacts($ContactId)/adx_webrole_contact/`$ref"
    $refBody = @{
        "@odata.id" = "$apiUrl/adx_webroles($RoleId)"
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri $associateUrl -Method Post -Headers $headers -Body $refBody -ErrorAction Stop | Out-Null
        return "added"
    } catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $msg = $_.ErrorDetails.Message
        }

        if ($msg -match "matching key values already exists|A record with matching key values already exists") {
            return "exists"
        }

        throw "Role assignment failed: $msg"
    }
}

# ------------------------------------------------------------
# Resolve site role
# ------------------------------------------------------------
$siteRole = Invoke-DataverseGet -EntitySet "adx_webroles" `
    -Filter "_adx_websiteid_value eq $siteId and adx_name eq 'Authenticated Users'" `
    -Select "adx_webroleid,adx_name" `
    -Top 1

if (-not $siteRole -or $siteRole.Count -eq 0) {
    throw "Could not find 'Authenticated Users' web role for site $siteId"
}

$authenticatedRoleId = $siteRole[0].adx_webroleid
Write-Host "Authenticated Users role: $authenticatedRoleId" -ForegroundColor DarkGray

# ------------------------------------------------------------
# Hero users for portal demo
# ------------------------------------------------------------
$heroUsers = @(
    @{ FirstName = "Rachel"; LastName = "Chen";     Email = "rachel.chen@ferguson.com";    Phone = "(757) 555-2002"; Title = "Purchasing Director";               AccountName = "Ferguson Enterprises" },
    @{ FirstName = "Tom";    LastName = "Harrison"; Email = "tom.harrison@ferguson.com";   Phone = "(757) 555-2001"; Title = "Plumbing Category Manager";         AccountName = "Ferguson Enterprises" },
    @{ FirstName = "Mike";   LastName = "Reynolds"; Email = "mike.reynolds@ferguson.com";  Phone = "(713) 555-0184"; Title = "Field Operations Manager";          AccountName = "Ferguson Enterprises" },
    @{ FirstName = "James";  LastName = "Morales";  Email = "james.morales@hdsupply.com";  Phone = "(770) 555-2301"; Title = "Commercial Accounts Manager";       AccountName = "HD Supply" },
    @{ FirstName = "Derek";  LastName = "Lawson";   Email = "derek.lawson@hdsupply.com";   Phone = "(770) 555-2305"; Title = "Facilities Maintenance Supervisor"; AccountName = "HD Supply" }
)

$results = @()
foreach ($user in $heroUsers) {
    Write-Host "" 
    Write-Host "Processing $($user.FirstName) $($user.LastName) <$($user.Email)>" -ForegroundColor Cyan

    $contactId = Ensure-Contact -UserDef $user
    $roleResult = Ensure-RoleMembership -ContactId $contactId -RoleId $authenticatedRoleId

    Write-Host "  Contact: $contactId" -ForegroundColor Green
    if ($roleResult -eq "added") {
        Write-Host "  Web role: added" -ForegroundColor Green
    } else {
        Write-Host "  Web role: already assigned" -ForegroundColor DarkGray
    }

    $results += [pscustomobject]@{
        Name      = "$($user.FirstName) $($user.LastName)"
        Email     = $user.Email
        Account   = $user.AccountName
        ContactId = $contactId
        Role      = $roleResult
    }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Hero Portal Users Ready" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
$results | Format-Table -AutoSize
