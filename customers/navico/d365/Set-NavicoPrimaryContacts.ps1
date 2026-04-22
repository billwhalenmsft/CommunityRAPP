<#
.SYNOPSIS
    Links primary contacts to Navico demo accounts in D365.
.DESCRIPTION
    Looks up each contact and account by name, then PATCHes the account's
    primarycontactid to link the appropriate primary contact.
#>

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperPath = Join-Path $scriptDir "..\..\..\d365\scripts\DataverseHelper.psm1"
Import-Module $helperPath -Force

Connect-Dataverse

# Contact → Account mapping (from demo-data.json)
$mappings = @(
    @{ FirstName="Jake";      LastName="Harrington"; AccountName="Atlantic Marine Supply Co." },
    @{ FirstName="Christine"; LastName="Delacroix";  AccountName="Euro Marine Distributors" },
    @{ FirstName="Mike";      LastName="Torres";     AccountName="Freshwater Fishing Depot" },
    @{ FirstName="Ryan";      LastName="Kowalski";   AccountName="Pacific Coast Marine Group" },
    @{ FirstName="Lars";      LastName="Eriksson";   AccountName="Nordic Marine Supply" }
)

$updated = 0; $skipped = 0; $failed = 0

foreach ($m in $mappings) {
    Write-Host "`nProcessing: $($m.FirstName) $($m.LastName) → $($m.AccountName)" -ForegroundColor Cyan

    # Look up contact
    $contact = Invoke-DataverseGet -EntitySet "contacts" `
        -Filter "firstname eq '$($m.FirstName)' and lastname eq '$($m.LastName)'" `
        -Select "contactid,fullname" -Top 1

    if (-not $contact -or $contact.Count -eq 0) {
        Write-Host "  MISSING CONTACT: $($m.FirstName) $($m.LastName)" -ForegroundColor Red
        $failed++
        continue
    }
    $contactId = $contact[0].contactid
    Write-Host "  Contact found: $($contact[0].fullname) ($contactId)" -ForegroundColor DarkGray

    # Look up account
    $escapedName = $m.AccountName -replace "'", "''"
    $account = Invoke-DataverseGet -EntitySet "accounts" `
        -Filter "name eq '$escapedName'" `
        -Select "accountid,name,_primarycontactid_value" -Top 1

    if (-not $account -or $account.Count -eq 0) {
        Write-Host "  MISSING ACCOUNT: $($m.AccountName)" -ForegroundColor Red
        $failed++
        continue
    }
    $accountId = $account[0].accountid
    Write-Host "  Account found: $($account[0].name) ($accountId)" -ForegroundColor DarkGray

    # Already linked?
    if ($account[0]._primarycontactid_value -and $account[0]._primarycontactid_value -eq $contactId) {
        Write-Host "  UNCHANGED: Primary contact already set" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    # PATCH account to set primarycontactid
    $headers  = Get-DataverseHeaders
    $apiUrl   = Get-DataverseApiUrl
    $patchUrl = "$apiUrl/accounts($accountId)"
    $body     = @{ "primarycontactid@odata.bind" = "/contacts($contactId)" } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri $patchUrl -Method Patch -Headers $headers `
            -Body $body -ContentType "application/json" -TimeoutSec 30
        Write-Host "  UPDATED: Primary contact → $($m.FirstName) $($m.LastName)" -ForegroundColor Green
        $updated++
    }
    catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Primary Contacts Linked" -ForegroundColor Green
Write-Host "  Updated : $updated" -ForegroundColor White
Write-Host "  Skipped : $skipped (already set)" -ForegroundColor White
Write-Host "  Failed  : $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "White" })
Write-Host ("=" * 60) -ForegroundColor Green
