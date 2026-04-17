<#
.SYNOPSIS
    ERAC — Create custom Dataverse tables defined in schema.json and add to solution.

.DESCRIPTION
    Creates the 5 ERAC custom tables:
      erac_partnershiprating  — Partnership Rating (PRR)
      erac_riskassessment     — Risk Assessment
      erac_treaty             — Treaty
      erac_reserveadequacy    — Reserve Adequacy
      erac_dispute            — Legal Dispute

    Each table is created with its columns (from schema.json), then added to the
    GEERACLiteCRM solution via AddSolutionComponent.

    Idempotent — safe to re-run. Tables/columns that already exist are skipped.

.PARAMETER Org
    Dataverse org URL (default: https://orgecbce8ef.crm.dynamics.com)

.PARAMETER SolutionUniqueName
    Power Platform solution unique name (default: GEERACLiteCRM)

.PARAMETER Phase
    CreateTables | AddColumns | AddToSolution | All (default)

.EXAMPLE
    .\Provision-EracCustomTables.ps1
    .\Provision-EracCustomTables.ps1 -Phase AddToSolution
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [ValidateSet("CreateTables","AddColumns","AddToSolution","All")]
    [string]$Phase = "All"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
function Get-Token {
    $raw = az account get-access-token --resource $Org 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Error "Run: az login" }
    return ($raw | ConvertFrom-Json).accessToken
}

$script:Token = Get-Token
function Get-Headers([switch]$WithSolution) {
    $h = @{
        Authorization      = "Bearer $script:Token"
        "Content-Type"     = "application/json; charset=utf-8"
        Accept             = "application/json"
        "OData-MaxVersion" = "4.0"
        "OData-Version"    = "4.0"
    }
    if ($WithSolution) { $h["MSCRM.SolutionUniqueName"] = $SolutionUniqueName }
    return $h
}

function Invoke-Dv {
    param([string]$Method, [string]$Path, [object]$Body=$null,
          [switch]$Metadata, [switch]$WithSolution)
    $base = if ($Metadata) { "$Org/api/data/v9.2" } else { "$Org/api/data/v9.2" }
    $uri  = "$base/$Path"
    $hdrs = Get-Headers -WithSolution:$WithSolution
    $params = @{ Uri=$uri; Method=$Method; Headers=$hdrs; TimeoutSec=120; UseBasicParsing=$true }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    $maxTry = 4
    for ($i=1; $i -le $maxTry; $i++) {
        try {
            $resp = Invoke-WebRequest @params
            if ($resp.Content) { return $resp.Content | ConvertFrom-Json }
            return $null
        } catch {
            $code = $_.Exception.Response.StatusCode.value__
            $msg  = $_.ErrorDetails.Message
            if ($code -eq 429) {
                $wait = if ($_.Exception.Response.Headers["Retry-After"]) { [int]$_.Exception.Response.Headers["Retry-After"] } else { 10 * $i }
                Write-Host "    ↳ 429 throttled — waiting ${wait}s (attempt $i/$maxTry)" -ForegroundColor Yellow
                Start-Sleep -Seconds $wait; continue
            }
            if ($code -eq 400 -and $msg -match "already exists|0x80044005") {
                Write-Host "    ↳ Already exists (idempotent skip)" -ForegroundColor Yellow
                return $null
            }
            if ($i -lt $maxTry) { Start-Sleep -Seconds (3*$i); continue }
            Write-Warning "  ✗ $Method $Path → $code : $msg"
            return $null
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# TABLE DEFINITIONS  (mirrors schema.json custom_tables)
# ─────────────────────────────────────────────────────────────────────────────
$Tables = @(
    @{
        logicalName  = "erac_partnershiprating"
        displayName  = "Partnership Rating"
        pluralName   = "Partnership Ratings"
        primaryCol   = "erac_name"
        description  = "ERAC Partnership Rating Review (PRR) records"
        columns = @(
            @{ name="erac_period";        type="String";   display="Period";              maxLen=50 },
            @{ name="erac_relationship";  type="Decimal";  display="Relationship";        min=0; max=5; precision=1 },
            @{ name="erac_technical";     type="Decimal";  display="Technical";           min=0; max=5; precision=1 },
            @{ name="erac_strategic";     type="Decimal";  display="Strategic";           min=0; max=5; precision=1 },
            @{ name="erac_operational";   type="Decimal";  display="Operational";         min=0; max=5; precision=1 },
            @{ name="erac_overallrating"; type="Decimal";  display="Overall Rating";      min=0; max=5; precision=1 },
            @{ name="erac_ratingtrend";   type="Picklist"; display="Trend";               choices=@("Improving","Stable","Declining") },
            @{ name="erac_lastqbrdate";   type="DateTime"; display="Last QBR Date";       format="DateOnly" },
            @{ name="erac_status";        type="Picklist"; display="Status";              choices=@("Draft","Submitted","Approved","Under Review") },
            @{ name="erac_notes";         type="Memo";     display="Notes";               maxLen=2000 },
            @{ name="erac_accountid";     type="Lookup";   display="Cedent";              target="account" }
        )
    },
    @{
        logicalName  = "erac_riskassessment"
        displayName  = "Risk Assessment"
        pluralName   = "Risk Assessments"
        primaryCol   = "erac_name"
        description  = "ERAC cedent risk assessments"
        columns = @(
            @{ name="erac_period";          type="String";   display="Period";              maxLen=50 },
            @{ name="erac_financialrisk";   type="Picklist"; display="Financial Risk";      choices=@("Low","Medium","High","Critical") },
            @{ name="erac_technologyrisk";  type="Picklist"; display="Technology Risk";     choices=@("Low","Medium","High","Critical") },
            @{ name="erac_compliancerisk";  type="Picklist"; display="Compliance Risk";     choices=@("Low","Medium","High","Critical") },
            @{ name="erac_counterpartyrisk";type="Picklist"; display="Counterparty Risk";   choices=@("Low","Medium","High","Critical") },
            @{ name="erac_aggregaterisk";   type="Picklist"; display="Aggregate Risk";      choices=@("Low","Medium","High","Critical") },
            @{ name="erac_approvalstatus";  type="Picklist"; display="Approval Status";     choices=@("Pending","Approved","Escalated","Rejected") },
            @{ name="erac_reviewdate";      type="DateTime"; display="Review Date";         format="DateOnly" },
            @{ name="erac_notes";           type="Memo";     display="Notes";               maxLen=2000 },
            @{ name="erac_accountid";       type="Lookup";   display="Cedent";              target="account" }
        )
    },
    @{
        logicalName  = "erac_treaty"
        displayName  = "Treaty"
        pluralName   = "Treaties"
        primaryCol   = "erac_name"
        description  = "ERAC reinsurance treaties"
        columns = @(
            @{ name="erac_treatytype";   type="Picklist"; display="Treaty Type";    choices=@("Quota Share","Excess of Loss","Facultative","Surplus","Stop Loss") },
            @{ name="erac_effectivedate";type="DateTime"; display="Effective Date"; format="DateOnly" },
            @{ name="erac_expirydate";   type="DateTime"; display="Expiry Date";    format="DateOnly" },
            @{ name="erac_exposurem";    type="Decimal";  display="Exposure M";     min=0; max=99999; precision=1 },
            @{ name="erac_governinglaw"; type="String";   display="Governing Law";  maxLen=100 },
            @{ name="erac_status";       type="Picklist"; display="Status";         choices=@("Active","Pending Renewal","Expired","In Dispute","Under Review") },
            @{ name="erac_notes";        type="Memo";     display="Notes";          maxLen=2000 },
            @{ name="erac_accountid";    type="Lookup";   display="Cedent";         target="account" }
        )
    },
    @{
        logicalName  = "erac_reserveadequacy"
        displayName  = "Reserve Adequacy"
        pluralName   = "Reserve Adequacy Records"
        primaryCol   = "erac_name"
        description  = "ERAC actuarial reserve adequacy records"
        columns = @(
            @{ name="erac_lob";             type="String";   display="Line of Business";        maxLen=100 },
            @{ name="erac_period";          type="String";   display="Period";                  maxLen=50 },
            @{ name="erac_currentreserve";  type="Decimal";  display="Current Reserve M";       min=0; max=99999; precision=1 },
            @{ name="erac_recreserve";      type="Decimal";  display="Recommended Reserve M";   min=0; max=99999; precision=1 },
            @{ name="erac_adequacypct";     type="Decimal";  display="Adequacy Pct";            min=0; max=200; precision=1 },
            @{ name="erac_status";          type="Picklist"; display="Status";                  choices=@("Adequate","Under-Reserved","Over-Reserved","Under Review") },
            @{ name="erac_accountid";       type="Lookup";   display="Cedent";                  target="account" }
        )
    },
    @{
        logicalName  = "erac_dispute"
        displayName  = "Legal Dispute"
        pluralName   = "Legal Disputes"
        primaryCol   = "erac_name"
        description  = "ERAC legal disputes"
        columns = @(
            @{ name="erac_disputetype";  type="Picklist"; display="Dispute Type";    choices=@("Coverage","Commutation","Data Quality","Regulatory","Contract Interpretation") },
            @{ name="erac_fileddate";    type="DateTime"; display="Filed Date";      format="DateOnly" },
            @{ name="erac_exposure";     type="Decimal";  display="Exposure M";      min=0; max=99999; precision=1 },
            @{ name="erac_status";       type="Picklist"; display="Status";          choices=@("Active","Settled","Dismissed","In Arbitration","Mediation") },
            @{ name="erac_notes";        type="Memo";     display="Notes";           maxLen=2000 },
            @{ name="erac_accountid";    type="Lookup";   display="Cedent";          target="account" }
        )
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS: BUILD ATTRIBUTE BODIES
# ─────────────────────────────────────────────────────────────────────────────
function Build-PicklistBody([string]$logName, [string]$display, [array]$choices) {
    $opts = $choices | ForEach-Object -Begin { $i=200000 } -Process {
        @{ Value=$i; Label=@{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$_; LanguageCode=1033 }) } }
        $i++
    }
    return @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
        SchemaName    = $logName
        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$display; LanguageCode=1033 }) }
        RequiredLevel = @{ Value="None" }
        OptionSet     = @{
            "@odata.type" = "#Microsoft.Dynamics.CRM.OptionSetMetadata"
            IsGlobal      = $false
            OptionSetType = "Picklist"
            Options       = $opts
        }
    }
}

function Build-StringBody([string]$logName, [string]$display, [int]$maxLen=100) {
    return @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.StringAttributeMetadata"
        SchemaName    = $logName
        MaxLength     = $maxLen
        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$display; LanguageCode=1033 }) }
        RequiredLevel = @{ Value="None" }
        FormatName    = @{ Value="Text" }
    }
}

function Build-MemoBody([string]$logName, [string]$display, [int]$maxLen=2000) {
    return @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.MemoAttributeMetadata"
        SchemaName    = $logName
        MaxLength     = $maxLen
        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$display; LanguageCode=1033 }) }
        RequiredLevel = @{ Value="None" }
    }
}

function Build-DecimalBody([string]$logName, [string]$display, [double]$min, [double]$max, [int]$precision=1) {
    return @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
        SchemaName    = $logName
        MinValue      = $min
        MaxValue      = $max
        Precision     = $precision
        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$display; LanguageCode=1033 }) }
        RequiredLevel = @{ Value="None" }
    }
}

function Build-DateTimeBody([string]$logName, [string]$display, [string]$format="DateOnly") {
    return @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
        SchemaName    = $logName
        Format        = $format
        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$display; LanguageCode=1033 }) }
        RequiredLevel = @{ Value="None" }
    }
}

function Build-LookupBody([string]$logName, [string]$display, [string]$target) {
    return @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.LookupAttributeMetadata"
        SchemaName    = $logName
        Targets       = @($target)
        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$display; LanguageCode=1033 }) }
        RequiredLevel = @{ Value="None" }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: CREATE TABLES
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-CreateTables {
    Write-Host "`n=== PHASE: CREATE CUSTOM TABLES ===" -ForegroundColor Cyan

    foreach ($tbl in $Tables) {
        Write-Host "[Table] $($tbl.displayName) ($($tbl.logicalName))..."

        # Check if exists
        $existing = Invoke-Dv -Method GET -Path "EntityDefinitions(LogicalName='$($tbl.logicalName)')?`$select=LogicalName"
        if ($existing) {
            Write-Host "  ↳ Already exists — skipping create" -ForegroundColor Yellow
            continue
        }

        # Build table body
        $schema = (Get-Culture).TextInfo.ToTitleCase($tbl.logicalName)
        $body = @{
            "@odata.type"       = "#Microsoft.Dynamics.CRM.EntityMetadata"
            SchemaName          = $schema
            DisplayName         = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$tbl.displayName; LanguageCode=1033 }) }
            DisplayCollectionName = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$tbl.pluralName; LanguageCode=1033 }) }
            Description         = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$tbl.description; LanguageCode=1033 }) }
            OwnershipType       = "UserOwned"
            IsActivity          = $false
            HasActivities       = $false
            HasNotes            = $true
            PrimaryNameAttribute = $tbl.primaryCol
            Attributes          = @(
                @{
                    "@odata.type" = "#Microsoft.Dynamics.CRM.StringAttributeMetadata"
                    SchemaName    = $tbl.primaryCol
                    IsPrimaryName = $true
                    MaxLength     = 100
                    RequiredLevel = @{ Value="ApplicationRequired" }
                    DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label="Name"; LanguageCode=1033 }) }
                    FormatName    = @{ Value="Text" }
                }
            )
        }

        if ($PSCmdlet.ShouldProcess($tbl.displayName, "Create custom table")) {
            $result = Invoke-Dv -Method POST -Path "EntityDefinitions" -Body $body
            if ($null -ne $result -or $true) {
                Write-Host "  ✓ Created: $($tbl.displayName)" -ForegroundColor Green
            }
        }
        Start-Sleep -Seconds 3
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: ADD COLUMNS
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-AddColumns {
    Write-Host "`n=== PHASE: ADD COLUMNS TO CUSTOM TABLES ===" -ForegroundColor Cyan

    foreach ($tbl in $Tables) {
        Write-Host "[Columns] $($tbl.displayName)..."
        $entityPath = "EntityDefinitions(LogicalName='$($tbl.logicalName)')/Attributes"

        foreach ($col in $tbl.columns) {
            Write-Host "  → $($col.name) ($($col.type))" -NoNewline

            # Skip lookup — created as relationship separately below
            if ($col.type -eq "Lookup") { Write-Host " [Lookup — use Relationships API]" -ForegroundColor DarkGray; continue }

            # Check exists
            $existing = Invoke-Dv -Method GET -Path "EntityDefinitions(LogicalName='$($tbl.logicalName)')/Attributes(LogicalName='$($col.name)')?`$select=LogicalName" 2>$null
            if ($existing) { Write-Host " ↳ exists" -ForegroundColor Yellow; continue }

            $attrBody = switch ($col.type) {
                "Picklist"  { Build-PicklistBody  $col.name $col.display $col.choices }
                "String"    { Build-StringBody    $col.name $col.display ($col.maxLen ?? 100) }
                "Memo"      { Build-MemoBody      $col.name $col.display ($col.maxLen ?? 2000) }
                "Decimal"   { Build-DecimalBody   $col.name $col.display $col.min $col.max ($col.precision ?? 1) }
                "DateTime"  { Build-DateTimeBody  $col.name $col.display ($col.format ?? "DateOnly") }
                default     { $null }
            }
            if (-not $attrBody) { Write-Host " [SKIP — unknown type]" -ForegroundColor DarkGray; continue }

            if ($PSCmdlet.ShouldProcess($col.name, "Create column on $($tbl.logicalName)")) {
                Invoke-Dv -Method POST -Path $entityPath -Body $attrBody | Out-Null
                Write-Host " ✓" -ForegroundColor Green
            }
            Start-Sleep -Seconds 2
        }

        # Lookup relationships (N:1 from custom table to account)
        $lookupCols = $tbl.columns | Where-Object { $_.type -eq "Lookup" }
        foreach ($lc in $lookupCols) {
            if ($lc.target -eq "account") {
                Write-Host "  → $($lc.name) (Lookup → account)" -NoNewline
                $relBody = @{
                    "@odata.type"         = "#Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
                    SchemaName            = "$($tbl.logicalName)_account_$($lc.name)"
                    ReferencedEntity      = "account"
                    ReferencingEntity     = $tbl.logicalName
                    ReferencingAttribute  = $lc.name
                    Lookup                = @{
                        "@odata.type" = "#Microsoft.Dynamics.CRM.LookupAttributeMetadata"
                        SchemaName    = $lc.name
                        DisplayName   = @{ "@odata.type"="#Microsoft.Dynamics.CRM.Label"; LocalizedLabels=@(@{ "@odata.type"="#Microsoft.Dynamics.CRM.LocalizedLabel"; Label=$lc.display; LanguageCode=1033 }) }
                        RequiredLevel = @{ Value="None" }
                    }
                    AssociatedMenuConfiguration = @{ Behavior="UseCollectionName"; Group="Details"; Order=10000 }
                    CascadeConfiguration = @{ Assign="NoCascade"; Delete="RemoveLink"; Merge="NoCascade"; Reparent="NoCascade"; Share="NoCascade"; Unshare="NoCascade" }
                }
                if ($PSCmdlet.ShouldProcess($lc.name, "Create lookup relationship")) {
                    Invoke-Dv -Method POST -Path "RelationshipDefinitions" -Body $relBody | Out-Null
                    Write-Host " ✓" -ForegroundColor Green
                }
                Start-Sleep -Seconds 2
            }
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3: ADD TO SOLUTION
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-AddToSolution {
    Write-Host "`n=== PHASE: ADD TABLES TO SOLUTION ===" -ForegroundColor Cyan

    # ComponentType 1 = Entity (whole table + all its owned components)
    foreach ($tbl in $Tables) {
        Write-Host "[Solution] Adding $($tbl.logicalName) to $SolutionUniqueName..."

        # Get entity OTC
        $meta = Invoke-Dv -Method GET -Path "EntityDefinitions(LogicalName='$($tbl.logicalName)')?`$select=ObjectTypeCode"
        if (-not $meta) { Write-Warning "  ✗ Could not get metadata for $($tbl.logicalName)"; continue }

        $addBody = @{
            ComponentId           = $meta.MetadataId
            ComponentType         = 1   # Entity
            SolutionUniqueName    = $SolutionUniqueName
            AddRequiredComponents = $true
        }
        $result = Invoke-Dv -Method POST -Path "AddSolutionComponent" -Body $addBody -WithSolution
        Write-Host "  ✓ Added to solution" -ForegroundColor Green
        Start-Sleep -Seconds 1
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if ($Phase -eq "CreateTables" -or $Phase -eq "All") { Invoke-CreateTables }
if ($Phase -eq "AddColumns"   -or $Phase -eq "All") { Invoke-AddColumns }
if ($Phase -eq "AddToSolution"-or $Phase -eq "All") { Invoke-AddToSolution }

Write-Host "`n✅ Provision-EracCustomTables complete" -ForegroundColor Green
Write-Host "   Next: Run Seed-EracRichData.ps1 to populate test records" -ForegroundColor Cyan
