<#
.SYNOPSIS
    Adds a Tier Level field to the Account entity and populates demo accounts.
.DESCRIPTION
    Creates a choice (option set) column on the Account entity for Service Tier Level,
    then populates all 10 Otis demo accounts with their correct tier values.
    
    Uses the same option values as the existing Case cr377_tierlevel field:
      192350000 = Tier 1 - Premium Service
      192350001 = Tier 2 - Full Maintenance  
      192350002 = Tier 3 - Basic Maintenance
      192350003 = Tier 4 - On-Call Only

    PREREQUISITES:
      - az login completed
      - System Administrator or System Customizer role
      - DataverseHelper.psm1 in parent scripts folder

.EXAMPLE
    .\Add-AccountTierField.ps1
    .\Add-AccountTierField.ps1 -SkipFieldCreation   # Only populate data
    .\Add-AccountTierField.ps1 -UseServiceLevel      # Map to built-in accountclassificationcode instead
#>

[CmdletBinding()]
param(
    [switch]$SkipFieldCreation,
    [switch]$UseServiceLevel
)

# ── Load helper ────────────────────────────────────────────────
$helperPath = Join-Path $PSScriptRoot "..\..\..\..\d365\scripts\DataverseHelper.psm1"
if (-not (Test-Path $helperPath)) {
    $helperPath = Join-Path $PSScriptRoot "..\..\..\d365\scripts\DataverseHelper.psm1"
}
if (-not (Test-Path $helperPath)) {
    Write-Error "Cannot find DataverseHelper.psm1. Run from customers/otis/d365/scripts/ directory."
    exit 1
}
Import-Module $helperPath -Force
Connect-Dataverse

$apiUrl = Get-DataverseApiUrl
$headers = Get-DataverseHeaders

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Account Tier Level — Field Creation & Data Population" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Tier option values (matching Case cr377_tierlevel)
$TIER_VALUES = @{
    1 = 192350000  # Tier 1 - Premium Service
    2 = 192350001  # Tier 2 - Full Maintenance
    3 = 192350002  # Tier 3 - Basic Maintenance
    4 = 192350003  # Tier 4 - On-Call Only
}

$FIELD_NAME = "cr377_tierlevel"  # Same logical name as on Case entity

# ============================================================
# Step 1: Create the Tier Level field on Account
# ============================================================
if (-not $SkipFieldCreation -and -not $UseServiceLevel) {
    Write-Host "Step 1: Creating Tier Level field on Account entity..." -ForegroundColor Yellow
    
    # Check if field already exists
    $checkUrl = "${apiUrl}EntityDefinitions(LogicalName='account')/Attributes(LogicalName='$FIELD_NAME')"
    $fieldExists = $false
    try {
        $existing = Invoke-RestMethod -Uri $checkUrl -Method Get -Headers $headers -ErrorAction Stop
        if ($existing) {
            Write-Host "  Field '$FIELD_NAME' already exists on Account. Skipping creation." -ForegroundColor DarkGray
            $fieldExists = $true
        }
    } catch {
        # 404 = field doesn't exist, which is expected
        if ($_.Exception.Response.StatusCode -ne 404) {
            Write-Warning "  Error checking field: $($_.Exception.Message)"
        }
    }
    
    if (-not $fieldExists) {
        # Create the choice field via Metadata API
        $fieldDefinition = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
            SchemaName = "cr377_TierLevel"
            DisplayName = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels = @(
                    @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        Label = "Tier Level"
                        LanguageCode = 1033
                    }
                )
            }
            Description = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels = @(
                    @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        Label = "Service tier level for SLA routing and prioritization"
                        LanguageCode = 1033
                    }
                )
            }
            RequiredLevel = @{
                Value = "None"
                CanBeChanged = $true
            }
            OptionSet = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.OptionSetMetadata"
                IsGlobal = $false
                OptionSetType = "Picklist"
                Options = @(
                    @{
                        Value = 192350000
                        Label = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            LocalizedLabels = @(
                                @{
                                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                    Label = "Tier 1 - Premium Service"
                                    LanguageCode = 1033
                                }
                            )
                        }
                    },
                    @{
                        Value = 192350001
                        Label = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            LocalizedLabels = @(
                                @{
                                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                    Label = "Tier 2 - Full Maintenance"
                                    LanguageCode = 1033
                                }
                            )
                        }
                    },
                    @{
                        Value = 192350002
                        Label = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            LocalizedLabels = @(
                                @{
                                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                    Label = "Tier 3 - Basic Maintenance"
                                    LanguageCode = 1033
                                }
                            )
                        }
                    },
                    @{
                        Value = 192350003
                        Label = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            LocalizedLabels = @(
                                @{
                                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                    Label = "Tier 4 - On-Call Only"
                                    LanguageCode = 1033
                                }
                            )
                        }
                    }
                )
            }
        }
        
        $metadataUrl = "${apiUrl}EntityDefinitions(LogicalName='account')/Attributes"
        $jsonBody = $fieldDefinition | ConvertTo-Json -Depth 15
        
        try {
            $response = Invoke-WebRequest -Uri $metadataUrl -Method Post `
                -Headers $headers -Body $jsonBody -UseBasicParsing -ErrorAction Stop
            Write-Host "  Created field: $FIELD_NAME on Account entity" -ForegroundColor Green
        } catch {
            $errMsg = $_.ErrorDetails.Message
            if ($errMsg -match "already exists") {
                Write-Host "  Field already exists (different schema check path)." -ForegroundColor DarkGray
            } else {
                Write-Warning "  Failed to create field via API: $($_.Exception.Message)"
                Write-Host "  $errMsg" -ForegroundColor Red
                Write-Host ""
                Write-Host "  MANUAL ALTERNATIVE:" -ForegroundColor Yellow
                Write-Host "    1. Go to make.powerapps.com > Tables > Account > Columns" -ForegroundColor DarkGray
                Write-Host "    2. + New column: 'Tier Level', Type: Choice" -ForegroundColor DarkGray
                Write-Host "    3. Add options:" -ForegroundColor DarkGray
                Write-Host "       192350000 = Tier 1 - Premium Service" -ForegroundColor DarkGray
                Write-Host "       192350001 = Tier 2 - Full Maintenance" -ForegroundColor DarkGray
                Write-Host "       192350002 = Tier 3 - Basic Maintenance" -ForegroundColor DarkGray
                Write-Host "       192350003 = Tier 4 - On-Call Only" -ForegroundColor DarkGray
                Write-Host "    4. Save, then re-run with -SkipFieldCreation" -ForegroundColor DarkGray
                Write-Host ""
            }
        }
        
        # Publish the Account entity to make the field available
        Write-Host "  Publishing Account entity customizations..." -ForegroundColor DarkGray
        $publishBody = @{
            ParameterXml = "<importexportxml><entities><entity>account</entity></entities></importexportxml>"
        }
        try {
            $publishUrl = "${apiUrl}PublishXml"
            $publishJson = $publishBody | ConvertTo-Json
            Invoke-RestMethod -Uri $publishUrl -Method Post -Headers $headers -Body $publishJson -ErrorAction Stop
            Write-Host "  Published successfully." -ForegroundColor Green
        } catch {
            Write-Warning "  Publish may have failed: $($_.Exception.Message)"
            Write-Host "  You may need to publish manually in the solution." -ForegroundColor DarkGray
        }
    }
} elseif ($UseServiceLevel) {
    Write-Host "Step 1: Using built-in accountclassificationcode field instead." -ForegroundColor Yellow
    $FIELD_NAME = "accountclassificationcode"
    # Map: 1=Default Value → we'll use custom mapping below
    Write-Host "  NOTE: accountclassificationcode has limited default options." -ForegroundColor DarkGray
    Write-Host "  You may need to add custom options to this global option set." -ForegroundColor DarkGray
} else {
    Write-Host "Step 1: SKIPPED (field creation). Using existing field." -ForegroundColor Yellow
}

# ============================================================
# Step 2: Populate Tier Level for Demo Accounts
# ============================================================
Write-Host "`nStep 2: Populating Tier Level for Otis demo accounts..." -ForegroundColor Yellow

# Otis demo accounts from otis-demo-ids.json
$demoAccounts = @(
    @{ Name = "Westfield London Shopping Centre"; Id = "a41d8f61-241f-f111-8341-6045bda80a72"; Tier = 1 }
    @{ Name = "Canary Wharf Tower";               Id = "6414e566-241f-f111-8342-6045bdedc552"; Tier = 1 }
    @{ Name = "Riverside Medical Centre";          Id = "f05e7b68-241f-f111-8342-7ced8d18cb3b"; Tier = 1 }
    @{ Name = "Birmingham New Street Station";     Id = "47af366a-241f-f111-8341-7c1e5218592b"; Tier = 1 }
    @{ Name = "The Shard London";                  Id = "7a105f6f-241f-f111-8342-6045bdedc552"; Tier = 1 }
    @{ Name = "Marriott Hotel Manchester";         Id = "6ba085c6-241f-f111-8341-7c1e5218592b"; Tier = 2 }
    @{ Name = "Parkview Residential Tower";        Id = "1255f4c5-241f-f111-8341-7ced8dd8e369"; Tier = 2 }
    @{ Name = "Crown Shopping Centre";             Id = "709d0ec5-241f-f111-8342-7ced8d18c8d7"; Tier = 2 }
    @{ Name = "Metro Office Park";                 Id = "ec1962c8-241f-f111-8341-7ced8d18ce4d"; Tier = 3 }
    @{ Name = "Greenfield School";                 Id = "666559c8-241f-f111-8342-7c1e520a58a1"; Tier = 3 }
)

$successCount = 0
$failCount = 0

foreach ($acct in $demoAccounts) {
    $tierValue = $TIER_VALUES[$acct.Tier]
    $tierLabel = switch ($acct.Tier) {
        1 { "Tier 1 - Premium" }
        2 { "Tier 2 - Full Maint" }
        3 { "Tier 3 - Basic" }
        4 { "Tier 4 - On-Call" }
    }
    
    $body = @{
        $FIELD_NAME = $tierValue
    }
    
    $result = Invoke-DataversePatch -EntitySet "accounts" -RecordId $acct.Id -Body $body
    if ($result) {
        Write-Host "  ✓ $($acct.Name) → $tierLabel ($tierValue)" -ForegroundColor Green
        $successCount++
    } else {
        Write-Warning "  ✗ $($acct.Name) — FAILED"
        $failCount++
    }
}

Write-Host "`n  Results: $successCount succeeded, $failCount failed" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

# ============================================================
# Step 3: Verify Data
# ============================================================
Write-Host "`nStep 3: Verifying account tier data..." -ForegroundColor Yellow

$verifyAccounts = Invoke-DataverseGet -EntitySet "accounts" `
    -Filter "contains(accountnumber,'OTIS-UK')" `
    -Select "name,accountnumber,$FIELD_NAME"

if ($verifyAccounts) {
    Write-Host ""
    Write-Host "  Account                           | Number      | Tier Level" -ForegroundColor White
    Write-Host "  ----------------------------------|-------------|-------------------" -ForegroundColor DarkGray
    foreach ($a in $verifyAccounts) {
        $tierDisplay = switch ($a.$FIELD_NAME) {
            192350000 { "Tier 1 - Premium" }
            192350001 { "Tier 2 - Full Maint" }
            192350002 { "Tier 3 - Basic" }
            192350003 { "Tier 4 - On-Call" }
            default   { "(not set)" }
        }
        $name = $a.name.PadRight(35)
        $num = ($a.accountnumber ?? "N/A").PadRight(13)
        Write-Host "  $name| $num| $tierDisplay" -ForegroundColor DarkGray
    }
}

# ============================================================
# Step 4: Form Instructions
# ============================================================
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Next Steps — Add Tier Level to Account Form" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  The field is populated in data. To show it on the Account form:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Go to: make.powerapps.com > Solutions > Default Solution" -ForegroundColor DarkGray
Write-Host "  2. Tables > Account > Forms > 'Account' (Main form)" -ForegroundColor DarkGray
Write-Host "  3. Add the 'Tier Level' column to the ACCOUNT INFORMATION section" -ForegroundColor DarkGray
Write-Host "     (place it near 'Category' or 'Industry', above 'Description')" -ForegroundColor DarkGray
Write-Host "  4. Save and Publish the form" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  This ensures Tier Level is visible:" -ForegroundColor White
Write-Host "    - On the Account form directly" -ForegroundColor DarkGray
Write-Host "    - In the Customer Summary panel (after accepting a call)" -ForegroundColor DarkGray
Write-Host "    - In the quick view if configured" -ForegroundColor DarkGray
Write-Host ""
