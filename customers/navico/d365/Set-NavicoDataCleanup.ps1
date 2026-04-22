<#
.SYNOPSIS
    Navico Demo Data Cleanup — create missing contacts, link them to accounts,
    and enrich cases with all missing fields (casetypecode, primarycontactid, etc.)
.PARAMETER Action
    Contacts  — create 3 missing contacts + link all 8 accounts to primary contacts
    Cases     — patch all demo cases with full field data
    All       — run both (default)
#>

[CmdletBinding()]
param(
    [ValidateSet("All","Contacts","Cases")]
    [string]$Action = "All"
)

$ErrorActionPreference = "Stop"
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperPath = Join-Path $scriptDir "..\..\..\d365\scripts\DataverseHelper.psm1"
Import-Module $helperPath -Force

$demoDataPath = Join-Path $scriptDir "config\demo-data.json"
$demoData     = Get-Content $demoDataPath -Raw | ConvertFrom-Json

Connect-Dataverse

# ============================================================
# Lookup caches
# ============================================================
$script:accountCache = @{}
$script:contactCache = @{}

function Get-AccountId([string]$Name) {
    if ($script:accountCache.ContainsKey($Name)) { return $script:accountCache[$Name] }
    $esc = $Name -replace "'","''"
    $r = Invoke-DataverseGet -EntitySet "accounts" -Filter "name eq '$esc'" -Select "accountid" -Top 1
    if ($r -and $r.Count -gt 0) {
        $script:accountCache[$Name] = $r[0].accountid
        return $r[0].accountid
    }
    return $null
}

function Get-ContactId([string]$FullName) {
    if ($script:contactCache.ContainsKey($FullName)) { return $script:contactCache[$FullName] }
    $parts = $FullName.Trim() -split ' ',2
    $fn = $parts[0]; $ln = if ($parts.Count -gt 1) { $parts[1] } else { "" }
    $r = Invoke-DataverseGet -EntitySet "contacts" `
        -Filter "firstname eq '$fn' and lastname eq '$ln'" `
        -Select "contactid,fullname" -Top 1
    if ($r -and $r.Count -gt 0) {
        $script:contactCache[$FullName] = $r[0].contactid
        return $r[0].contactid
    }
    return $null
}

# ============================================================
# SECTION 1 — Create missing contacts + link all accounts
# ============================================================
function Provision-Contacts {
    Write-Host "`n=====================================================================" -ForegroundColor Cyan
    Write-Host "  SECTION 1 — Contacts & Primary Contact Links" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Cyan

    $created = 0; $skipped = 0; $linked = 0; $linkSkip = 0

    foreach ($c in $demoData.contacts.contacts) {
        $fullName = "$($c.firstName) $($c.lastName)"
        Write-Host "`n  Contact: $fullName ($($c.account))" -ForegroundColor Yellow

        # Find account
        $accountId = Get-AccountId -Name $c.account
        if (-not $accountId) {
            Write-Host "    WARNING: Account '$($c.account)' not found — skipping" -ForegroundColor DarkYellow
            continue
        }

        # Check if contact already exists
        $existingId = Get-ContactId -FullName $fullName
        if ($existingId) {
            Write-Host "    EXISTS: $fullName ($existingId)" -ForegroundColor DarkGray
            $skipped++
        }
        else {
            # Create contact
            $body = @{
                firstname    = $c.firstName
                lastname     = $c.lastName
                jobtitle     = $c.title
                telephone1   = $c.phone
                mobilephone  = $c.mobile
                emailaddress1 = $c.email
                description  = $c.demoRole
                "parentcustomerid_account@odata.bind" = "/accounts($accountId)"
            }

            $headers = Get-DataverseHeaders
            $apiUrl  = Get-DataverseApiUrl
            try {
                $result = Invoke-RestMethod -Uri "$apiUrl/contacts" -Method Post `
                    -Headers $headers -Body ($body | ConvertTo-Json) `
                    -ContentType "application/json" -TimeoutSec 30
                # Fetch the new contactid
                $newId = Get-ContactId -FullName $fullName
                Write-Host "    CREATED: $fullName" -ForegroundColor Green
                $created++
                $existingId = $newId
            }
            catch {
                Write-Host "    FAILED creating $fullName : $($_.Exception.Message)" -ForegroundColor Red
                continue
            }
        }

        # Now ensure this contact is set as primary on the account
        $account = Invoke-DataverseGet -EntitySet "accounts" `
            -Filter "accountid eq $accountId" `
            -Select "accountid,name,_primarycontactid_value" -Top 1

        if ($account -and $account.Count -gt 0 -and $account[0]._primarycontactid_value -eq $existingId) {
            Write-Host "    PRIMARY LINK: already set" -ForegroundColor DarkGray
            $linkSkip++
        }
        else {
            $headers  = Get-DataverseHeaders
            $apiUrl   = Get-DataverseApiUrl
            $patchUrl = "$apiUrl/accounts($accountId)"
            $patchBody = @{ "primarycontactid@odata.bind" = "/contacts($existingId)" } | ConvertTo-Json
            try {
                Invoke-RestMethod -Uri $patchUrl -Method Patch -Headers $headers `
                    -Body $patchBody -ContentType "application/json" -TimeoutSec 30
                Write-Host "    PRIMARY LINK: $($c.account) → $fullName" -ForegroundColor Green
                $linked++
            }
            catch {
                Write-Host "    FAILED linking primary contact: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }

    Write-Host ""
    Write-Host "  Contacts created : $created"   -ForegroundColor White
    Write-Host "  Contacts skipped : $skipped"   -ForegroundColor DarkGray
    Write-Host "  Primary links set: $linked"    -ForegroundColor White
    Write-Host "  Links unchanged  : $linkSkip"  -ForegroundColor DarkGray
}

# ============================================================
# SECTION 2 — Enrich cases with full field data
# ============================================================
function Update-Cases {
    Write-Host "`n=====================================================================" -ForegroundColor Cyan
    Write-Host "  SECTION 2 — Case Data Enrichment" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Cyan

    # casetypecode: 1=Question, 2=Problem, 3=Request
    $caseTypeMap = @{
        "Technical Support" = 2   # Problem
        "Warranty Claim"    = 3   # Request
        "RMA - Exchange"    = 3   # Request
        "RMA - Repair"      = 3   # Request
        "RMA - Credit"      = 3   # Request
        "RMA - OBS"         = 3   # Request
        "Certification"     = 3   # Request
        "Billing"           = 1   # Question
    }

    # prioritycode: 1=High, 2=Normal, 3=Low
    $priorityMap = @{ "High"=1; "Normal"=2; "Low"=3 }

    # caseorigincode
    $originMap = @{ "Phone"=1; "Email"=2; "Web"=3; "Chat"=2483; "Portal"=3986 }

    $updated = 0; $skipped = 0; $failed = 0

    foreach ($case in $demoData.demoCases.cases) {
        Write-Host "`n  Case: $($case.title)" -ForegroundColor Yellow

        # Look up case by title
        $escapedTitle = $case.title -replace "'","''"
        $existing = Invoke-DataverseGet -EntitySet "incidents" `
            -Filter "title eq '$escapedTitle'" `
            -Select "incidentid,title,casetypecode,prioritycode,caseorigincode,_primarycontactid_value,_customerid_value" `
            -Top 1

        if (-not $existing -or $existing.Count -eq 0) {
            Write-Host "    NOT FOUND in D365 — skipping" -ForegroundColor DarkYellow
            $skipped++
            continue
        }

        $incidentId = $existing[0].incidentid
        Write-Host "    Found: $incidentId" -ForegroundColor DarkGray

        # Build patch body with all enrichment fields
        $patch = @{}

        # casetypecode
        $typeCode = if ($caseTypeMap.ContainsKey($case.caseType)) { $caseTypeMap[$case.caseType] } else { 2 }
        if ($existing[0].casetypecode -ne $typeCode) {
            $patch["casetypecode"] = $typeCode
        }

        # prioritycode (re-set to ensure correct)
        $priorityCode = if ($priorityMap.ContainsKey($case.priority)) { $priorityMap[$case.priority] } else { 2 }
        if ($existing[0].prioritycode -ne $priorityCode) {
            $patch["prioritycode"] = $priorityCode
        }

        # caseorigincode
        $originCode = if ($originMap.ContainsKey($case.channel)) { $originMap[$case.channel] } else { 3 }
        if ($existing[0].caseorigincode -ne $originCode) {
            $patch["caseorigincode"] = $originCode
        }

        # primarycontactid — link contact if not already set
        if ($case.contact -and -not $existing[0]._primarycontactid_value) {
            $contactId = Get-ContactId -FullName $case.contact
            if ($contactId) {
                $patch["primarycontactid@odata.bind"] = "/contacts($contactId)"
                Write-Host "    Linking contact: $($case.contact)" -ForegroundColor DarkGray
            } else {
                Write-Host "    WARNING: Contact '$($case.contact)' not found" -ForegroundColor DarkYellow
            }
        }

        # customerid — link account if not already set
        if ($case.account -and -not $existing[0]._customerid_value) {
            $accountId = Get-AccountId -Name $case.account
            if ($accountId) {
                $patch["customerid_account@odata.bind"] = "/accounts($accountId)"
                Write-Host "    Linking account: $($case.account)" -ForegroundColor DarkGray
            }
        }

        if ($patch.Count -eq 0) {
            Write-Host "    UNCHANGED — all fields already populated" -ForegroundColor DarkGray
            $skipped++
            continue
        }

        # Apply patch
        $headers  = Get-DataverseHeaders
        $apiUrl   = Get-DataverseApiUrl
        $patchUrl = "$apiUrl/incidents($incidentId)"
        try {
            Invoke-RestMethod -Uri $patchUrl -Method Patch -Headers $headers `
                -Body ($patch | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
            $fieldList = ($patch.Keys -join ", ")
            Write-Host "    UPDATED: [$fieldList]" -ForegroundColor Green
            $updated++
        }
        catch {
            Write-Host "    FAILED: $($_.Exception.Message)" -ForegroundColor Red
            $failed++
        }
    }

    Write-Host ""
    Write-Host "  Cases updated  : $updated"  -ForegroundColor White
    Write-Host "  Cases unchanged: $skipped"  -ForegroundColor DarkGray
    Write-Host "  Cases failed   : $failed"   -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "White" })
}

# ============================================================
# MAIN
# ============================================================
switch ($Action) {
    "All"      { Provision-Contacts; Update-Cases }
    "Contacts" { Provision-Contacts }
    "Cases"    { Update-Cases }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Navico Data Cleanup Complete" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
