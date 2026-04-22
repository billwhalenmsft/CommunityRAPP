<#
.SYNOPSIS
  Loads sample data from CSVs into Dataverse ascend_* tables via the Web API.
.PARAMETER OrgUrl
  Your Power Platform org URL, e.g. https://org6feab6b5.crm.dynamics.com
.PARAMETER CsvFolder
  Path to the folder containing sample_data CSVs (defaults to sibling sample_data/ folder).
.EXAMPLE
  .\load_sample_data.ps1 -OrgUrl "https://org6feab6b5.crm.dynamics.com"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$OrgUrl,

    [string]$CsvFolder = "$PSScriptRoot\sample_data"
)

$ErrorActionPreference = "Stop"

# ── Table → OData collection name ────────────────────────────────────────────
$tableMap = @{
    "ascend_sapvendor_data"               = "ascend_sapvendors"
    "ascend_sappurchaserequisition_data"  = "ascend_sappurchaserequisitions"
    "ascend_sappraccountassignment_data"  = "ascend_sappraccountassignments"
    "ascend_sapmaterialgroup_data"        = "ascend_sapmaterialgroups"
    "ascend_sapcostcenter_data"           = "ascend_sapcostcenters"
    "ascend_sapglaccount_data"            = "ascend_sapglaccounts"
    "ascend_sapcontract_data"             = "ascend_sapcontracts"
    "ascend_sapreleasestrategy_data"      = "ascend_sapreleasestrategies"
}

# CSV baseName → Dataverse entity LogicalName
$entityMap = @{
    "ascend_sapvendor_data"               = "ascend_sapvendor"
    "ascend_sappurchaserequisition_data"  = "ascend_sappurchaserequisition"
    "ascend_sappraccountassignment_data"  = "ascend_sappraccountassignment"
    "ascend_sapmaterialgroup_data"        = "ascend_sapmaterialgroup"
    "ascend_sapcostcenter_data"           = "ascend_sapcostcenter"
    "ascend_sapglaccount_data"            = "ascend_sapglaccount"
    "ascend_sapcontract_data"             = "ascend_sapcontract"
    "ascend_sapreleasestrategy_data"      = "ascend_sapreleasestrategy"
}

# ── Per-table CSV column → table column remappings ───────────────────────────
# Use when CSV column names differ from table column names
$columnRemap = @{
    "ascend_sapcontract_data" = @{
        "ascend_kdatb" = "ascend_guebg"   # CSV date-from → table DateTime column
        "ascend_kdate" = "ascend_gueen"   # CSV date-to   → table DateTime column
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────────
Write-Host "[auth] Getting token via Azure CLI..."
$tokenJson = az account get-access-token --resource $OrgUrl --query "{token:accessToken}" -o json 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "az account get-access-token failed. Run 'az login' first.`n$tokenJson"
}
$token = ($tokenJson | ConvertFrom-Json).token
Write-Host "[auth] ✅ Token acquired`n"

$headers = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json;IEEE754Compatible=true"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

# ── Load each CSV ─────────────────────────────────────────────────────────────
$totalCreated = 0
$totalFailed  = 0

foreach ($csvFile in Get-ChildItem -Path $CsvFolder -Filter "*.csv") {
    $baseName     = $csvFile.BaseName   # e.g. ascend_sapvendor_data
    $collection   = $tableMap[$baseName]
    $entityName   = $entityMap[$baseName]
    if (-not $collection) {
        Write-Host "  [skip] $($csvFile.Name) — no table mapping, skipping"
        continue
    }

    # Discover valid writable columns and their types for this table
    $attrResp = Invoke-RestMethod "$OrgUrl/api/data/v9.2/EntityDefinitions(LogicalName='$entityName')/Attributes?`$select=LogicalName,IsValidForCreate,AttributeType" -Headers $headers
    $validCols = $attrResp.value | Where-Object { $_.IsValidForCreate -eq $true } | ForEach-Object { $_.LogicalName }
    $validColSet = @{}
    foreach ($c in $validCols) { $validColSet[$c] = $true }

    # Build type map: logicalName → AttributeType (for proper coercion)
    $typeMap = @{}
    foreach ($a in $attrResp.value) { $typeMap[$a.LogicalName] = $a.AttributeType }
    $numericTypes = @("Integer","BigInt","Decimal","Double","Money")

    $endpoint = "$OrgUrl/api/data/v9.2/$collection"
    $rows     = Import-Csv -Path $csvFile.FullName
    $created  = 0
    $failed   = 0

    Write-Host "  [$baseName]  →  $collection  ($($rows.Count) rows)"

    foreach ($row in $rows) {
        # Build body — only include columns that exist in the table
        $remap = $columnRemap[$baseName]
        $body = @{}
        foreach ($prop in $row.PSObject.Properties) {
            $col = $prop.Name.Trim()
            # Apply per-table column rename if defined
            if ($remap -and $remap.ContainsKey($col)) { $col = $remap[$col] }
            # Skip columns not present in the table
            if (-not $validColSet.ContainsKey($col)) { continue }
            if ([string]::IsNullOrWhiteSpace($prop.Value)) { continue }

            $val = $prop.Value.Trim()

            # Type coercion based on actual Dataverse column type
            if ($val -eq "true")  { $body[$col] = $true;  continue }
            if ($val -eq "false") { $body[$col] = $false; continue }

            $colType = $typeMap[$col]
            if ($colType -eq "DateTime") {
                # Send ISO date strings as-is — Dataverse accepts yyyy-MM-dd
                $body[$col] = $val; continue
            }
            if ($numericTypes -contains $colType) {
                # With IEEE754Compatible=true, Decimal/Money send as string; Integer stays number
                if ($colType -eq "Decimal" -or $colType -eq "Money") {
                    $body[$col] = $val   # send as string literal
                } else {
                    try {
                        if ($val -match '\.') { $body[$col] = [double]$val }
                        else                  { $body[$col] = [long]$val }
                    } catch { $body[$col] = $val }
                }
                continue
            }

            $body[$col] = $val
        }

        # The primary name field for all tables is ascend_name
        # If not already set, derive from the most meaningful column
        if (-not $body.ContainsKey("ascend_name") -or [string]::IsNullOrWhiteSpace($body["ascend_name"])) {
            # Use the first non-empty string column that looks like an ID
            $idCols = @("ascend_ebeln","ascend_banfn","ascend_lifnr","ascend_kostl","ascend_saknr","ascend_frggr","ascend_matkl")
            foreach ($ic in $idCols) {
                if ($body.ContainsKey($ic) -and $body[$ic]) {
                    $body["ascend_name"] = [string]$body[$ic]
                    break
                }
            }
        }

        $bodyJson = $body | ConvertTo-Json -Compress

        try {
            $response = Invoke-RestMethod -Uri $endpoint -Method POST `
                -Headers $headers -Body $bodyJson
            $created++
            Write-Host "    ✓ $($body["ascend_name"])" -ForegroundColor Green
        }
        catch {
            $failed++
            $errMsg = $_.ErrorDetails.Message
            if ($errMsg -and $errMsg.Length -gt 200) { $errMsg = $errMsg.Substring(0,200) }
            Write-Host "    ✗ $($body["ascend_name"]) — $errMsg" -ForegroundColor Red
        }
    }

    Write-Host "    → Created: $created  Failed: $failed`n"
    $totalCreated += $created
    $totalFailed  += $failed
}

Write-Host "============================================================"
Write-Host "DONE  Total created: $totalCreated   Total failed: $totalFailed"
if ($totalFailed -eq 0) {
    Write-Host "`nAll sample data loaded! Next:"
    Write-Host "  1. Activate 6 Power Automate flows"
    Write-Host "  2. Set env var: ascend_DemoMode = true"
    Write-Host "  3. Publish Copilot Studio agent to Teams"
}
