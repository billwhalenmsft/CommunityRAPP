<#
.SYNOPSIS
    Otis EMEA CCaaS Demo - D365 Data Provisioning
.DESCRIPTION
    Creates Otis-specific demo data for Contact Center telephony demo.
    - Service Accounts (buildings with Otis elevators)
    - Contacts (facilities managers)
    - Products (elevator models, service contracts)
    - Demo Cases (entrapment, out of service, maintenance)

.PARAMETER Action
    What to provision: All, Accounts, Contacts, Products, Cases, Cleanup

.EXAMPLE
    .\Provision-OtisDemo.ps1 -Action All
    .\Provision-OtisDemo.ps1 -Action Accounts
    .\Provision-OtisDemo.ps1 -Action Cleanup
#>

[CmdletBinding()]
param(
    [ValidateSet("All", "Accounts", "Contacts", "Products", "Cases", "Cleanup")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Script is at customers/otis/d365/ - go up 3 levels to repo root
$projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))

# Import Dataverse helper
$helperPath = Join-Path $projectRoot "d365\scripts\DataverseHelper.psm1"
if (Test-Path $helperPath) {
    Import-Module $helperPath -Force
} else {
    throw "DataverseHelper.psm1 not found at: $helperPath"
}

# Load Otis demo data
$demoDataPath = Join-Path $scriptDir "config\demo-data.json"
if (-not (Test-Path $demoDataPath)) {
    throw "Demo data not found at: $demoDataPath"
}
$demoData = Get-Content $demoDataPath | ConvertFrom-Json

# Load environment config
$envConfigPath = Join-Path $scriptDir "config\environment.json"
$envConfig = Get-Content $envConfigPath | ConvertFrom-Json

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Otis EMEA CCaaS Demo - Data Provisioning" -ForegroundColor Cyan
Write-Host "  Environment: $($envConfig.environment.name)" -ForegroundColor DarkGray
Write-Host "  URL: $($envConfig.environment.url)" -ForegroundColor DarkGray
Write-Host "  Action: $Action" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Connect to Dataverse
Write-Host "Connecting to Dataverse..." -ForegroundColor Yellow
Connect-Dataverse

# Track created records for export
$createdRecords = @{
    accounts = @()
    contacts = @()
    products = @()
    cases = @()
}

# ============================================================
# ACCOUNTS - Service Accounts (Buildings)
# ============================================================
function Provision-Accounts {
    Write-Host "`n>>> Provisioning Service Accounts..." -ForegroundColor Green
    
    foreach ($account in $demoData.serviceAccounts.accounts) {
        Write-Host "  Creating: $($account.name)" -ForegroundColor Gray
        
        $accountData = @{
            name = $account.name
            accountnumber = $account.accountNumber
            description = "Tier: $($account.tier)`nType: $($account.type)`nContract: $($account.contract)`nTotal Units: $($account.totalUnits)"
            telephone1 = $account.phone
            address1_line1 = $account.address.line1
            address1_city = $account.address.city
            address1_postalcode = $account.address.postalCode
            address1_country = $account.address.country
        }
        
        $accountId = Find-OrCreate-Record `
            -EntitySet "accounts" `
            -Filter "accountnumber eq '$($account.accountNumber)'" `
            -IdField "accountid" `
            -Body $accountData `
            -DisplayName $account.name
        
        $script:createdRecords.accounts += @{
            id = $accountId
            name = $account.name
            accountNumber = $account.accountNumber
            tier = $account.tier
        }
    }
    
    Write-Host "  Accounts complete: $($demoData.serviceAccounts.accounts.Count) processed" -ForegroundColor Green
}

# ============================================================
# CONTACTS - Facilities Managers
# ============================================================
function Provision-Contacts {
    Write-Host "`n>>> Provisioning Contacts..." -ForegroundColor Green
    
    foreach ($contact in $demoData.contacts.contacts) {
        Write-Host "  Creating: $($contact.firstName) $($contact.lastName)" -ForegroundColor Gray
        
        # Find parent account
        $parentAccount = $script:createdRecords.accounts | Where-Object { $_.name -eq $contact.account }
        $parentAccountId = $null
        if ($parentAccount) {
            $parentAccountId = $parentAccount.id
        } else {
            # Try to find account in D365
            $escapedName = $contact.account -replace "'", "''"
            $existingAccounts = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$escapedName'" -Select "accountid" -Top 1
            if ($existingAccounts -and $existingAccounts.Count -gt 0) {
                $parentAccountId = $existingAccounts[0].accountid
            }
        }
        
        $contactData = @{
            firstname = $contact.firstName
            lastname = $contact.lastName
            jobtitle = $contact.title
            telephone1 = $contact.phone
            mobilephone = $contact.mobile
            emailaddress1 = $contact.email
        }
        
        if ($parentAccountId) {
            $contactData["parentcustomerid_account@odata.bind"] = "/accounts($parentAccountId)"
        }
        
        $contactId = Find-OrCreate-Record `
            -EntitySet "contacts" `
            -Filter "emailaddress1 eq '$($contact.email)'" `
            -IdField "contactid" `
            -Body $contactData `
            -DisplayName "$($contact.firstName) $($contact.lastName)"
        
        $script:createdRecords.contacts += @{
            id = $contactId
            name = "$($contact.firstName) $($contact.lastName)"
            email = $contact.email
            account = $contact.account
            phone = $contact.phone
        }
    }
    
    Write-Host "  Contacts complete: $($demoData.contacts.contacts.Count) processed" -ForegroundColor Green
}

# ============================================================
# PRODUCTS - Elevator Models & Service Contracts
# ============================================================
function Provision-Products {
    Write-Host "`n>>> Skipping Products (requires D365 Unit Schedule/Price List setup)..." -ForegroundColor Yellow
    Write-Host "  Note: Products can be added manually in D365 if needed" -ForegroundColor DarkYellow
    # Products in D365 require unit schedules and price lists
    # For telephony demo, we primarily need accounts, contacts, and cases
}

# ============================================================
# CASES - Demo Cases
# ============================================================
function Provision-Cases {
    Write-Host "`n>>> Provisioning Demo Cases..." -ForegroundColor Green
    
    # Map priority names to D365 priority codes
    $priorityMap = @{
        "Critical" = 1
        "High" = 2
        "Normal" = 3
        "Low" = 4
    }
    
    foreach ($case in $demoData.demoCases.cases) {
        Write-Host "  Creating case: $($case.title)" -ForegroundColor Gray
        
        # Find customer account
        $customerAccount = $script:createdRecords.accounts | Where-Object { $_.name -eq $case.account }
        if (-not $customerAccount) {
            $escapedAccountName = $case.account -replace "'", "''"
            $existingAccounts = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$escapedAccountName'" -Select "accountid" -Top 1
            if ($existingAccounts -and $existingAccounts.Count -gt 0) {
                $customerAccount = @{ id = $existingAccounts[0].accountid }
            }
        }
        
        # Find contact
        $contactRecord = $null
        if ($case.contact) {
            $contactName = $case.contact
            $contactRecord = $script:createdRecords.contacts | Where-Object { $_.name -like "*$contactName*" }
        }
        
        $caseData = @{
            title = $case.title
            description = "$($case.description)`n`nEquipment: $($case.equipment)`n`n[Demo: $($case.demoUse)]"
            prioritycode = $priorityMap[$case.priority]
            caseorigincode = 1  # Phone
        }
        
        if ($customerAccount -and $customerAccount.id) {
            $caseData["customerid_account@odata.bind"] = "/accounts($($customerAccount.id))"
        } else {
            Write-Host "    Warning: Account not found for '$($case.account)' - creating case without customer" -ForegroundColor DarkYellow
        }
        
        if ($contactRecord -and $contactRecord.id) {
            $caseData["primarycontactid@odata.bind"] = "/contacts($($contactRecord.id))"
        }
        
        # Escape single quotes in title for OData filter
        $escapedTitle = $case.title -replace "'", "''"
        
        $caseId = Find-OrCreate-Record `
            -EntitySet "incidents" `
            -Filter "title eq '$escapedTitle'" `
            -IdField "incidentid" `
            -Body $caseData `
            -DisplayName $case.title
        
        $script:createdRecords.cases += @{
            id = $caseId
            title = $case.title
            account = $case.account
            priority = $case.priority
        }
    }
    
    Write-Host "  Cases complete: $($demoData.demoCases.cases.Count) processed" -ForegroundColor Green
}

# ============================================================
# CLEANUP - Remove demo data
# ============================================================
function Invoke-Cleanup {
    Write-Host "`n>>> WARNING: This will delete Otis demo data!" -ForegroundColor Red
    $confirm = Read-Host "Type 'DELETE' to confirm"
    
    if ($confirm -ne "DELETE") {
        Write-Host "Cleanup cancelled." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Cleaning up demo data..." -ForegroundColor Yellow
    
    # Delete cases first (they reference accounts/contacts)
    foreach ($case in $demoData.demoCases.cases) {
        Write-Host "  Deleting case: $($case.title)" -ForegroundColor Gray
        $escapedTitle = $case.title -replace "'", "''"
        $existing = Invoke-DataverseGet -EntitySet "incidents" -Filter "title eq '$escapedTitle'" -Select "incidentid" -Top 1
        if ($existing -and $existing.Count -gt 0) {
            Invoke-DataverseDelete -EntitySet "incidents" -Id $existing[0].incidentid
            Write-Host "    Deleted" -ForegroundColor DarkRed
        }
    }
    
    # Delete contacts
    foreach ($contact in $demoData.contacts.contacts) {
        Write-Host "  Deleting contact: $($contact.firstName) $($contact.lastName)" -ForegroundColor Gray
        $existing = Invoke-DataverseGet -EntitySet "contacts" -Filter "emailaddress1 eq '$($contact.email)'" -Select "contactid" -Top 1
        if ($existing -and $existing.Count -gt 0) {
            Invoke-DataverseDelete -EntitySet "contacts" -Id $existing[0].contactid
            Write-Host "    Deleted" -ForegroundColor DarkRed
        }
    }
    
    # Delete accounts
    foreach ($account in $demoData.serviceAccounts.accounts) {
        Write-Host "  Deleting account: $($account.name)" -ForegroundColor Gray
        $existing = Invoke-DataverseGet -EntitySet "accounts" -Filter "accountnumber eq '$($account.accountNumber)'" -Select "accountid" -Top 1
        if ($existing -and $existing.Count -gt 0) {
            Invoke-DataverseDelete -EntitySet "accounts" -Id $existing[0].accountid
            Write-Host "    Deleted" -ForegroundColor DarkRed
        }
    }
    
    Write-Host "Cleanup complete." -ForegroundColor Green
}

# ============================================================
# MAIN EXECUTION
# ============================================================
switch ($Action) {
    "All" {
        Provision-Accounts
        Provision-Contacts
        Provision-Products
        Provision-Cases
    }
    "Accounts" { Provision-Accounts }
    "Contacts" { Provision-Contacts }
    "Products" { Provision-Products }
    "Cases" { Provision-Cases }
    "Cleanup" { Invoke-Cleanup }
}

# Export created record IDs
$exportPath = Join-Path $scriptDir "data\otis-demo-ids.json"
$exportDir = Split-Path $exportPath -Parent
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir -Force | Out-Null
}

$createdRecords | ConvertTo-Json -Depth 5 | Set-Content $exportPath -Force
Write-Host "`nRecord IDs exported to: $exportPath" -ForegroundColor Cyan

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Otis Demo Provisioning Complete!" -ForegroundColor Green
Write-Host "  Accounts: $($createdRecords.accounts.Count)" -ForegroundColor Gray
Write-Host "  Contacts: $($createdRecords.contacts.Count)" -ForegroundColor Gray
Write-Host "  Products: $($createdRecords.products.Count)" -ForegroundColor Gray
Write-Host "  Cases: $($createdRecords.cases.Count)" -ForegroundColor Gray
Write-Host ("=" * 60) -ForegroundColor Green
