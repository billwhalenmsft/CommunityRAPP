<#
.SYNOPSIS
  Patch script — adds the missing erac_accountid (Cedent) lookup to all 5 ERAC custom tables.
  Provision-EracCustomTables.ps1 fails to create these via embedded lookup metadata in
  RelationshipDefinitions, so this uses the CreateOneToMany action which is more reliable.
#>
[CmdletBinding()]
param(
    [string]$Org = "https://org6feab6b5.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM"
)

$ErrorActionPreference = "Stop"

$tok = az account get-access-token --resource $Org --query accessToken -o tsv
if (-not $tok) { throw "Could not get token. Run 'az login'." }
$base = "$Org/api/data/v9.2"
$h = @{
    Authorization     = "Bearer $tok"
    Accept            = "application/json"
    "Content-Type"    = "application/json; charset=utf-8"
    "OData-Version"   = "4.0"
    "OData-MaxVersion"= "4.0"
    "MSCRM.SolutionUniqueName" = $SolutionUniqueName
}

$tables = @(
    @{ name="erac_partnershiprating"; rel="erac_partnershiprating_account" },
    @{ name="erac_riskassessment";    rel="erac_riskassessment_account"    },
    @{ name="erac_treaty";            rel="erac_treaty_account"            },
    @{ name="erac_reserveadequacy";   rel="erac_reserveadequacy_account"   },
    @{ name="erac_dispute";           rel="erac_dispute_account"           }
)

Write-Host "=== Add ERAC table → account lookups ===" -ForegroundColor Cyan
Write-Host "Org: $Org" -ForegroundColor Gray
Write-Host ""

foreach ($t in $tables) {
    Write-Host "[$($t.name)] " -NoNewline
    # Check if relationship already exists
    try {
        $existing = Invoke-RestMethod -Method Get -Uri "$base/EntityDefinitions(LogicalName='$($t.name)')/ManyToOneRelationships?`$filter=ReferencedEntity eq 'account'&`$select=SchemaName" -Headers $h
        if ($existing.value.Count -gt 0) {
            Write-Host "already has account lookup ($($existing.value[0].SchemaName)) — skipping" -ForegroundColor DarkGray
            continue
        }
    } catch {}

    $body = @{
        "@odata.type"             = "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
        SchemaName                = $t.rel
        ReferencedEntity          = "account"
        ReferencedAttribute       = "accountid"
        ReferencingEntity         = $t.name
        CascadeConfiguration      = @{
            Assign="NoCascade"; Delete="RemoveLink"; Merge="NoCascade";
            Reparent="NoCascade"; Share="NoCascade"; Unshare="NoCascade"; RollupView="NoCascade"
        }
        Lookup = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
            SchemaName    = "erac_AccountId"
            DisplayName   = @{
                "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels   = @(@{ "@odata.type"="Microsoft.Dynamics.CRM.LocalizedLabel"; Label="Cedent"; LanguageCode=1033 })
            }
            Description   = @{
                "@odata.type"     = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels   = @(@{ "@odata.type"="Microsoft.Dynamics.CRM.LocalizedLabel"; Label="Parent cedent account"; LanguageCode=1033 })
            }
            RequiredLevel = @{ Value="None" }
        }
    } | ConvertTo-Json -Depth 20 -Compress

    $hPost = $h.Clone()
    $hPost["MSCRM.SolutionUniqueName"] = $SolutionUniqueName

    $maxRetry = 4
    for ($i=1; $i -le $maxRetry; $i++) {
        try {
            $r = Invoke-RestMethod -Method Post -Uri "$base/RelationshipDefinitions" -Headers $hPost -Body $body
            Write-Host "✓ created $($t.rel)" -ForegroundColor Green
            break
        } catch {
            $msg = $_.ErrorDetails.Message
            if ($msg -match '0x80071151|PublishAll') {
                Write-Host "↳ publish in flight, waiting 15s (attempt $i)..." -ForegroundColor Yellow
                Start-Sleep -Seconds 15
            } elseif ($msg -match 'already exists') {
                Write-Host "✓ already exists" -ForegroundColor DarkGreen
                break
            } else {
                Write-Host "✗ FAILED: $msg" -ForegroundColor Red
                break
            }
        }
        if ($i -eq $maxRetry) { Write-Host "✗ gave up after $maxRetry attempts" -ForegroundColor Red }
    }
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "=== Publishing customizations ===" -ForegroundColor Cyan
try {
    $pubBody = '{"ParameterXml":"<importexportxml><entities>' + (($tables | ForEach-Object { "<entity>$($_.name)</entity>" }) -join '') + '</entities></importexportxml>"}'
    Invoke-RestMethod -Method Post -Uri "$base/PublishXml" -Headers $h -Body $pubBody | Out-Null
    Write-Host "✓ Published" -ForegroundColor Green
} catch { Write-Host "✗ Publish failed: $($_.ErrorDetails.Message)" -ForegroundColor Red }

Write-Host ""
Write-Host "✅ Done." -ForegroundColor Green
