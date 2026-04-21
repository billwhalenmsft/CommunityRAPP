<#
.SYNOPSIS
    Create an ERAC-tagged copy of the Account main form, then add the
    Cedent 360 tab to ONLY that copy. Keeps OOTB forms clean.

.DESCRIPTION
    1. Reads the OOTB 'Account' form XML
    2. Creates a new SystemForm named 'ERAC Cedent 360' on the account entity
    3. Adds the form to the GEERACLiteCRM solution
    4. Calls Add-EracCedent360Tab.ps1 -FormName 'ERAC Cedent 360' to inject the tab
    5. Publishes

    After running, set 'ERAC Cedent 360' as the default form for cedent users
    in the App Designer (Forms > set as primary).
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [string]$SourceFormName = "Account",
    [string]$NewFormName = "ERAC Cedent 360",
    [string]$NewFormDescription = "ERAC-customized Account form with Cedent 360 web resource tab. Use this form for reinsurance cedent records."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

$token = (az account get-access-token --resource $Org | ConvertFrom-Json).accessToken
$H = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}

function Invoke-Dv([string]$Method,[string]$Path,[object]$Body=$null,[hashtable]$ExtraHeaders=$null) {
    $hdr = $H.Clone()
    if ($ExtraHeaders) { $ExtraHeaders.GetEnumerator() | ForEach-Object { $hdr[$_.Key] = $_.Value } }
    if ($Method -eq "POST") { $hdr["Prefer"] = "return=representation" }
    $p = @{ Uri="$Org/api/data/v9.2/$Path"; Method=$Method; Headers=$hdr; TimeoutSec=60; UseBasicParsing=$true }
    if ($Body) { $p.Body = ($Body | ConvertTo-Json -Depth 20) }
    try {
        $r = Invoke-WebRequest @p
        if ($r.Content) { return $r.Content | ConvertFrom-Json }
        return @{ ok=$true; statusCode=$r.StatusCode; headers=$r.Headers }
    } catch {
        $code = try { $_.Exception.Response.StatusCode.value__ } catch { 0 }
        $msg  = try { $_.ErrorDetails.Message } catch { $_.Exception.Message }
        Write-Warning "  ✗ $Method $Path → $code : $($msg.Substring(0,[Math]::Min(400,$msg.Length)))"
        return $null
    }
}

Write-Host "=== CLONE ACCOUNT FORM → '$NewFormName' ===" -ForegroundColor Cyan

# ── 1. Check if target already exists (idempotent) ───────────────────────────
$escNew = $NewFormName.Replace("'","''")
$existing = Invoke-Dv GET "systemforms?`$filter=objecttypecode eq 'account' and type eq 2 and name eq '$escNew'&`$select=formid,name"
if ($existing -and $existing.value -and $existing.value.Count -gt 0) {
    $newFormId = $existing.value[0].formid
    Write-Host "  ⏭ Form '$NewFormName' already exists ($newFormId) — will skip clone, just verify tab" -ForegroundColor Yellow
} else {
    # ── 2. Read source form ──────────────────────────────────────────────────
    Write-Host "[1] Reading source form '$SourceFormName'..."
    $escSrc = $SourceFormName.Replace("'","''")
    $src = Invoke-Dv GET "systemforms?`$select=formid,name,formxml,description,objecttypecode,type,isdefault&`$filter=objecttypecode eq 'account' and type eq 2 and name eq '$escSrc'"
    if (-not $src -or -not $src.value -or $src.value.Count -eq 0) {
        Write-Error "Source form '$SourceFormName' not found."
    }
    $srcForm = $src.value[0]
    Write-Host "  ✓ Source: $($srcForm.name) ($($srcForm.formid))"

    # ── 3. Create new form ───────────────────────────────────────────────────
    Write-Host "[2] Creating '$NewFormName'..."
    $body = @{
        name             = $NewFormName
        description      = $NewFormDescription
        formxml          = $srcForm.formxml
        objecttypecode   = "account"
        type             = 2          # Main form
        formactivationstate = 1       # Active
        isdefault        = $false
    }
    $new = Invoke-Dv POST "systemforms" $body -ExtraHeaders @{ "MSCRM.SolutionUniqueName" = $SolutionUniqueName }
    if (-not $new) { Write-Error "Form creation failed." }
    $newFormId = $new.formid
    Write-Host "  ✓ Created '$NewFormName' ($newFormId)" -ForegroundColor Green
}

# ── 4. Add to solution (idempotent — 404 is fine) ────────────────────────────
Write-Host "[3] Adding form to solution..."
Invoke-Dv POST "AddSolutionComponent" @{
    ComponentId           = $newFormId
    ComponentType         = 60
    SolutionUniqueName    = $SolutionUniqueName
    AddRequiredComponents = $false
} | Out-Null

# ── 5. Publish so the new form is visible to the next script ────────────────
Write-Host "[4] Publishing account entity..."
Invoke-Dv POST "PublishXml" @{ ParameterXml = "<importexportxml><entities><entity>account</entity></entities></importexportxml>" } | Out-Null
Write-Host "  ✓ Published" -ForegroundColor Green

# ── 6. Inject the ERAC 360 tab into the new form ─────────────────────────────
Write-Host "[5] Injecting ERAC 360 tab into '$NewFormName'..."
$tabScript = Join-Path $ScriptDir "Add-EracCedent360Tab.ps1"
if (-not (Test-Path $tabScript)) {
    Write-Error "Add-EracCedent360Tab.ps1 not found in $ScriptDir"
}
& $tabScript -FormName $NewFormName -Org $Org -SolutionUniqueName $SolutionUniqueName

Write-Host "`n✅ '$NewFormName' is ready." -ForegroundColor Green
Write-Host @"

NEXT STEPS — set as default for the ERAC app:
  1. In App Designer for 'ERAC Lite CRM v2', open the Account table.
  2. Forms tab → drag '$NewFormName' to the TOP of the form order
     (above 'Account for Interactive experience').
  3. Save & Publish the app.

Now, opening any cedent Account record from the ERAC app will use the
new form with the ERAC 360 tab.

(Optional cleanup) The earlier scripts also added the tab to the OOTB
'Account' and 'Account for Interactive experience' forms. To remove the
tab from those, open each in the form designer and delete the
'ERAC 360' tab manually.
"@ -ForegroundColor Cyan
