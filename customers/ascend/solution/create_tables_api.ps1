#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates all 8 Ascend SAP emulation Dataverse tables via Web API.
    Bypasses solution import XML format issues entirely.

.DESCRIPTION
    Uses the Dataverse Metadata REST API to create custom entities and attributes
    directly — no solution ZIP, no customizations.xml format problems.

    Prerequisites:
      - Azure CLI installed and logged in: az login
      - PowerShell 7+ recommended (works on 5.1 too)

.PARAMETER OrgUrl
    Your Power Platform environment URL.
    Example: https://contoso.crm.dynamics.com
    Find it: make.powerapps.com → Settings → Session details → Instance URL

.PARAMETER DeleteExisting
    If specified, deletes any existing ascend_* tables first (cleanup of failed imports).
    USE WITH CAUTION — permanently deletes table and all data.

.EXAMPLE
    .\create_tables_api.ps1 -OrgUrl "https://yourorg.crm.dynamics.com"
    .\create_tables_api.ps1 -OrgUrl "https://yourorg.crm.dynamics.com" -DeleteExisting
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$OrgUrl,

    [switch]$DeleteExisting
)

$OrgUrl = $OrgUrl.TrimEnd('/')
$ApiBase = "$OrgUrl/api/data/v9.2"

# ── Auth ──────────────────────────────────────────────────────────────────────
Write-Host "`n[auth] Getting token via Azure CLI..." -ForegroundColor Cyan
try {
    $tokenJson = az account get-access-token --resource $OrgUrl 2>&1
    if ($LASTEXITCODE -ne 0) { throw "az CLI error: $tokenJson" }
    $token = ($tokenJson | ConvertFrom-Json).accessToken
    Write-Host "[auth] ✅ Token acquired" -ForegroundColor Green
} catch {
    Write-Host "[auth] ❌ Failed: $_" -ForegroundColor Red
    Write-Host "       Run: az login  then retry." -ForegroundColor Yellow
    exit 1
}

$Headers = @{
    "Authorization"    = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
    "Accept"           = "application/json"
}

# ── Helpers ───────────────────────────────────────────────────────────────────
function Invoke-DV {
    param([string]$Method, [string]$Path, [object]$Body = $null)
    $uri = "$ApiBase/$Path"
    $params = @{ Uri=$uri; Method=$Method; Headers=$Headers; ErrorAction="Stop" }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 20 -Compress) }
    try {
        return Invoke-RestMethod @params
    } catch {
        $msg = $_.ErrorDetails.Message
        if ($msg) {
            $err = $msg | ConvertFrom-Json -ErrorAction SilentlyContinue
            throw ($err.error.message ?? $msg)
        }
        throw $_
    }
}

function Label($text) {
    return @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                "Label"        = $text
                "LanguageCode" = 1033
            }
        )
        "UserLocalizedLabel" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
            "Label"        = $text
            "LanguageCode" = 1033
        }
    }
}

function EmptyLabel() {
    return @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        "LocalizedLabels" = @()
    }
}

function StringAttr($schema, $display, $maxLen=100, $required="None") {
    return @{
        "@odata.type"   = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        "AttributeType" = "String"
        "SchemaName"    = $schema
        "LogicalName"   = $schema.ToLower()
        "MaxLength"     = $maxLen
        "RequiredLevel" = @{ "Value" = $required; "CanBeChanged" = $true; "ManagedPropertyLogicalName" = "canmodifyrequirementlevelsettings" }
        "DisplayName"   = Label $display
        "Description"   = EmptyLabel
    }
}

function DecimalAttr($schema, $display) {
    return @{
        "@odata.type"   = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
        "AttributeType" = "Decimal"
        "SchemaName"    = $schema
        "LogicalName"   = $schema.ToLower()
        "Precision"     = 2
        "MinValue"      = 0.0
        "MaxValue"      = 1000000000.0
        "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true; "ManagedPropertyLogicalName" = "canmodifyrequirementlevelsettings" }
        "DisplayName"   = Label $display
        "Description"   = EmptyLabel
    }
}

function DateAttr($schema, $display) {
    return @{
        "@odata.type"   = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
        "AttributeType" = "DateTime"
        "SchemaName"    = $schema
        "LogicalName"   = $schema.ToLower()
        "Format"        = "DateOnly"
        "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true; "ManagedPropertyLogicalName" = "canmodifyrequirementlevelsettings" }
        "DisplayName"   = Label $display
        "Description"   = EmptyLabel
    }
}

function BoolAttr($schema, $display) {
    return @{
        "@odata.type"   = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
        "AttributeType" = "Boolean"
        "SchemaName"    = $schema
        "LogicalName"   = $schema.ToLower()
        "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true; "ManagedPropertyLogicalName" = "canmodifyrequirementlevelsettings" }
        "DisplayName"   = Label $display
        "Description"   = EmptyLabel
        "OptionSet"     = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata"
            "TrueOption"  = @{ "Value" = 1; "Label" = Label "Yes" }
            "FalseOption" = @{ "Value" = 0; "Label" = Label "No" }
        }
    }
}

# ── Entity definitions ────────────────────────────────────────────────────────
# Each entry: [SchemaName, DisplaySingular, DisplayPlural, idField, nameLabel, @(extra attrs)]

$Entities = @(
    @{
        Schema       = "ascend_sapvendor"
        Display      = "SAP Vendor"
        DisplayPlural = "SAP Vendors"
        IdField      = "ascend_sapvendorid"
        NameLabel    = "Vendor Name"
        ExtraAttrs   = @(
            (StringAttr "ascend_lifnr"     "Vendor Number (LIFNR)" 12)
            (StringAttr "ascend_bukrs"     "Company Code (BUKRS)"   4)
            (StringAttr "ascend_ekorg"     "Purchasing Org (EKORG)"  4)
            (StringAttr "ascend_land1"     "Country (LAND1)"         3)
            (StringAttr "ascend_waers"     "Currency (WAERS)"        5)
            (StringAttr "ascend_datasource" "Data Source"           100)
        )
    },
    @{
        Schema       = "ascend_sappurchaserequisition"
        Display      = "SAP Purchase Requisition"
        DisplayPlural = "SAP Purchase Requisitions"
        IdField      = "ascend_sappurchaserequisitionid"
        NameLabel    = "PR Number"
        ExtraAttrs   = @(
            (StringAttr  "ascend_banfn"       "PR Number (BANFN)"     10)
            (StringAttr  "ascend_bnfpo"       "PR Item (BNFPO)"        5)
            (StringAttr  "ascend_txz01"       "Short Text (TXZ01)"   100)
            (StringAttr  "ascend_matnr"       "Material (MATNR)"      40)
            (DecimalAttr "ascend_menge"       "Quantity (MENGE)")
            (StringAttr  "ascend_meins"       "Unit (MEINS)"           3)
            (StringAttr  "ascend_werks"       "Plant (WERKS)"          4)
            (StringAttr  "ascend_kostl"       "Cost Center (KOSTL)"   10)
            (StringAttr  "ascend_sakto"       "GL Account (SAKTO)"    10)
            (StringAttr  "ascend_lifnr"       "Vendor (LIFNR)"        12)
            (StringAttr  "ascend_bsart"       "PR Type (BSART)"        4)
            (StringAttr  "ascend_statu"       "Status (STATU)"        20)
            (DateAttr    "ascend_badat"       "Request Date (BADAT)")
            (DateAttr    "ascend_lfdat"       "Delivery Date (LFDAT)")
            (StringAttr  "ascend_ernam"       "Created By (ERNAM)"    40)
            (DecimalAttr "ascend_preis"       "Price (PREIS)")
            (StringAttr  "ascend_peinh"       "Price Unit (PEINH)"    10)
            (StringAttr  "ascend_datasource"  "Data Source"          100)
        )
    },
    @{
        Schema       = "ascend_sappraccountassignment"
        Display      = "SAP PR Account Assignment"
        DisplayPlural = "SAP PR Account Assignments"
        IdField      = "ascend_sappraccountassignmentid"
        NameLabel    = "Assignment Name"
        ExtraAttrs   = @(
            (StringAttr "ascend_banfn"       "PR Number"              10)
            (StringAttr "ascend_bnfpo"       "PR Item"                 5)
            (StringAttr "ascend_knttp"       "Account Cat (KNTTP)"     1)
            (StringAttr "ascend_kostl"       "Cost Center (KOSTL)"    10)
            (StringAttr "ascend_sakto"       "GL Account (SAKTO)"     10)
            (StringAttr "ascend_aufnr"       "Order Number (AUFNR)"   12)
            (StringAttr "ascend_datasource"  "Data Source"           100)
        )
    },
    @{
        Schema       = "ascend_sapmaterialgroup"
        Display      = "SAP Material Group"
        DisplayPlural = "SAP Material Groups"
        IdField      = "ascend_sapmaterialgroupid"
        NameLabel    = "Material Group Name"
        ExtraAttrs   = @(
            (StringAttr "ascend_matkl"       "Material Group (MATKL)"   9)
            (StringAttr "ascend_wgbez"       "Description (WGBEZ)"    100)
            (StringAttr "ascend_datasource"  "Data Source"            100)
        )
    },
    @{
        Schema       = "ascend_sapcostcenter"
        Display      = "SAP Cost Center"
        DisplayPlural = "SAP Cost Centers"
        IdField      = "ascend_sapcostcenterid"
        NameLabel    = "Cost Center Name"
        ExtraAttrs   = @(
            (StringAttr "ascend_kostl"       "Cost Center (KOSTL)"    10)
            (StringAttr "ascend_bukrs"       "Company Code (BUKRS)"    4)
            (StringAttr "ascend_msehi"       "Currency"                5)
            (StringAttr "ascend_verak"       "Manager"                40)
            (StringAttr "ascend_datasource"  "Data Source"           100)
        )
    },
    @{
        Schema       = "ascend_sapglaccount"
        Display      = "SAP GL Account"
        DisplayPlural = "SAP GL Accounts"
        IdField      = "ascend_sapglaccountid"
        NameLabel    = "GL Account Name"
        ExtraAttrs   = @(
            (StringAttr "ascend_saknr"       "GL Account (SAKNR)"    10)
            (StringAttr "ascend_bukrs"       "Company Code (BUKRS)"   4)
            (StringAttr "ascend_txt50"       "Description (TXT50)"  100)
            (StringAttr "ascend_gvtyp"       "P&L Category (GVTYP)"   1)
            (StringAttr "ascend_datasource"  "Data Source"          100)
        )
    },
    @{
        Schema       = "ascend_sapcontract"
        Display      = "SAP Contract"
        DisplayPlural = "SAP Contracts"
        IdField      = "ascend_sapcontractid"
        NameLabel    = "Contract Name"
        ExtraAttrs   = @(
            (StringAttr  "ascend_ebeln"       "Contract Number (EBELN)"  10)
            (StringAttr  "ascend_lifnr"       "Vendor (LIFNR)"           12)
            (StringAttr  "ascend_bukrs"       "Company Code (BUKRS)"      4)
            (StringAttr  "ascend_ekorg"       "Purchasing Org (EKORG)"    4)
            (DecimalAttr "ascend_kdatb"       "Value (KDATB)")
            (DateAttr    "ascend_guebg"       "Valid From (GUEBG)")
            (DateAttr    "ascend_gueen"       "Valid To (GUEEN)")
            (StringAttr  "ascend_datasource"  "Data Source"             100)
        )
    },
    @{
        Schema       = "ascend_sapreleasestrategy"
        Display      = "SAP Release Strategy"
        DisplayPlural = "SAP Release Strategies"
        IdField      = "ascend_sapreleasestrategyid"
        NameLabel    = "Release Strategy Name"
        ExtraAttrs   = @(
            (StringAttr  "ascend_frggr"       "Release Group (FRGGR)"    2)
            (StringAttr  "ascend_frgsx"       "Release Strategy (FRGSX)"  4)
            (DecimalAttr "ascend_minval"      "Min Value")
            (DecimalAttr "ascend_maxval"      "Max Value")
            (StringAttr  "ascend_approver1"   "Approver 1"              100)
            (StringAttr  "ascend_approver2"   "Approver 2"              100)
            (StringAttr  "ascend_datasource"  "Data Source"             100)
        )
    }
)

# ── Optional cleanup ──────────────────────────────────────────────────────────
if ($DeleteExisting) {
    Write-Host "`n[cleanup] Checking for existing ascend_* entities..." -ForegroundColor Cyan
    try {
        $existing = Invoke-DV GET "EntityDefinitions?`$filter=startswith(SchemaName,'ascend_')&`$select=SchemaName,MetadataId"
        foreach ($ent in $existing.value) {
            Write-Host "  Deleting $($ent.SchemaName)..." -NoNewline
            try {
                Invoke-DV DELETE "EntityDefinitions($($ent.MetadataId))"
                Write-Host " ✓" -ForegroundColor Green
            } catch {
                Write-Host " ✗ $_" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "  (none found or query error: $_)" -ForegroundColor Yellow
    }
    Write-Host "[cleanup] Done. Waiting 5s for propagation..." -ForegroundColor Cyan
    Start-Sleep 5
}

# ── Create entities ───────────────────────────────────────────────────────────
Write-Host "`n[create] Creating $($Entities.Count) Dataverse entities..." -ForegroundColor Cyan
$created = 0; $skipped = 0; $failed = 0

foreach ($e in $Entities) {
    $schema = $e.Schema
    Write-Host "`n  [$schema]" -ForegroundColor White

    # Check if already exists
    try {
        $check = Invoke-DV GET "EntityDefinitions(LogicalName='$($schema.ToLower())')?`$select=SchemaName"
        Write-Host "    ⏭  Already exists — skipping entity creation (will add missing columns)" -ForegroundColor Yellow
        $alreadyExists = $true
    } catch {
        $alreadyExists = $false
    }

    if (-not $alreadyExists) {
        # Build entity creation body
        $body = @{
            "@odata.type"      = "Microsoft.Dynamics.CRM.EntityMetadata"
            "SchemaName"       = $schema
            "DisplayName"      = Label $e.Display
            "DisplayCollectionName" = Label $e.DisplayPlural
            "Description"      = EmptyLabel
            "OwnershipType"    = "UserOwned"
            "HasActivities"    = $false
            "HasNotes"         = $false
            "IsActivity"       = $false
            "Attributes"       = @(
                @{
                    "@odata.type"   = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
                    "AttributeType" = "String"
                    "SchemaName"    = "ascend_name"
                    "LogicalName"   = "ascend_name"
                    "MaxLength"     = 100
                    "IsPrimaryName" = $true
                    "RequiredLevel" = @{ "Value" = "ApplicationRequired"; "CanBeChanged" = $false; "ManagedPropertyLogicalName" = "canmodifyrequirementlevelsettings" }
                    "DisplayName"   = Label $e.NameLabel
                    "Description"   = EmptyLabel
                }
            )
        }

        Write-Host "    Creating entity + primary name field..." -NoNewline
        try {
            Invoke-DV POST "EntityDefinitions" $body | Out-Null
            Write-Host " ✓" -ForegroundColor Green
            $created++
            # Brief pause — entity creation is async on the platform side
            Start-Sleep -Milliseconds 500
        } catch {
            Write-Host " ✗ $_" -ForegroundColor Red
            $failed++
            continue
        }
    } else {
        $skipped++
    }

    # Add extra attributes (skip if they exist)
    foreach ($attr in $e.ExtraAttrs) {
        $attrSchema = $attr.SchemaName
        Write-Host "    + $attrSchema..." -NoNewline
        try {
            Invoke-DV POST "EntityDefinitions(LogicalName='$($schema.ToLower())')/Attributes" $attr | Out-Null
            Write-Host " ✓" -ForegroundColor Green
        } catch {
            $errMsg = $_.ToString()
            if ($errMsg -match "already exists|0x80044335|duplicate") {
                Write-Host " (exists)" -ForegroundColor DarkGray
            } else {
                Write-Host " ✗ $errMsg" -ForegroundColor Red
            }
        }
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n" + ("=" * 60)
Write-Host "DONE"
Write-Host "  Created:  $created"
Write-Host "  Skipped:  $skipped  (already existed)"
Write-Host "  Failed:   $failed"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. make.powerapps.com → Tables — verify ascend_* tables appear"
Write-Host "  2. Import sample data: Tables → [table] → Import data → upload CSV"
Write-Host "     CSVs are in: customers/ascend/solution/sample_data/"
Write-Host ""
if ($failed -gt 0) {
    Write-Host "Retry failed entities by running again — idempotent, skips existing." -ForegroundColor Yellow
}
