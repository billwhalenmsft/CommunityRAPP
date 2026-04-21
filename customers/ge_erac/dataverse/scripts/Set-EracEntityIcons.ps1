<#
.SYNOPSIS
    Bind ERAC SVG icon web resources to their custom entities (sets IconVectorName).
    Without this, entity icons disappear in the runtime MDA navigation even though
    the web resources exist.

.DESCRIPTION
    For each ERAC custom entity, PATCHes the EntityDefinition with the matching
    erac_icon_* SVG web resource as IconVectorName, then publishes all entities.

    Mapping:
      erac_treaty             → erac_icon_treaty
      erac_reserveadequacy    → erac_icon_reserve
      erac_partnershiprating  → erac_icon_prr
      erac_riskassessment     → erac_icon_risk
      erac_dispute            → erac_icon_dispute
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$token = (az account get-access-token --resource $Org | ConvertFrom-Json).accessToken
$H = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

$mapping = @(
    @{ entity="erac_treaty";            icon="erac_icon_treaty"  },
    @{ entity="erac_reserveadequacy";   icon="erac_icon_reserve" },
    @{ entity="erac_partnershiprating"; icon="erac_icon_prr"     },
    @{ entity="erac_riskassessment";    icon="erac_icon_risk"    },
    @{ entity="erac_dispute";           icon="erac_icon_dispute" }
)

Write-Host "=== BIND ENTITY ICONS ===" -ForegroundColor Cyan

foreach ($m in $mapping) {
    Write-Host "`n[$($m.entity)] → $($m.icon)"

    # Verify web resource exists
    $wrLookup = Invoke-RestMethod "$Org/api/data/v9.2/webresourceset?`$filter=name eq '$($m.icon)'&`$select=webresourceid,webresourcetype" -Headers $H
    if (-not $wrLookup.value -or $wrLookup.value.Count -eq 0) {
        Write-Warning "  ✗ Web resource '$($m.icon)' NOT FOUND — skipping"
        continue
    }
    $wrType = $wrLookup.value[0].webresourcetype
    Write-Host "  ✓ Web resource found (type=$wrType, id=$($wrLookup.value[0].webresourceid))"

    # PATCH the EntityDefinition
    $body = @{ IconVectorName = $m.icon } | ConvertTo-Json
    try {
        Invoke-WebRequest "$Org/api/data/v9.2/EntityDefinitions(LogicalName='$($m.entity)')" `
            -Method PATCH -Headers $H -Body $body -UseBasicParsing -TimeoutSec 60 | Out-Null
        Write-Host "  ✓ Bound IconVectorName" -ForegroundColor Green
    } catch {
        $code = try { $_.Exception.Response.StatusCode.value__ } catch { 0 }
        $msg  = try { $_.ErrorDetails.Message } catch { $_.Exception.Message }
        if ($code -le 204) {
            Write-Host "  ✓ Bound IconVectorName" -ForegroundColor Green
        } else {
            Write-Warning "  ✗ PATCH $code : $($msg.Substring(0,[Math]::Min(300,$msg.Length)))"
        }
    }
}

# Publish all entities
Write-Host "`n=== PUBLISH ===" -ForegroundColor Cyan
$entityList = ($mapping | ForEach-Object { "<entity>$($_.entity)</entity>" }) -join ""
$publishXml = "<importexportxml><entities>$entityList</entities></importexportxml>"
try {
    Invoke-WebRequest "$Org/api/data/v9.2/PublishXml" `
        -Method POST -Headers $H -Body (@{ ParameterXml = $publishXml } | ConvertTo-Json) `
        -UseBasicParsing -TimeoutSec 120 | Out-Null
    Write-Host "  ✓ Published 5 entities" -ForegroundColor Green
} catch {
    Write-Warning "  Publish: $($_.Exception.Message)"
}

# Verify
Write-Host "`n=== VERIFY ===" -ForegroundColor Cyan
foreach ($m in $mapping) {
    $meta = Invoke-RestMethod "$Org/api/data/v9.2/EntityDefinitions(LogicalName='$($m.entity)')?`$select=LogicalName,IconVectorName" -Headers $H
    "  {0,-25} IconVectorName = {1}" -f $meta.LogicalName, $meta.IconVectorName
}

Write-Host "`n✅ Icon binding complete." -ForegroundColor Green
Write-Host "   Hard-refresh the MDA in the browser (Ctrl+Shift+R) to see icons in the nav." -ForegroundColor Cyan
