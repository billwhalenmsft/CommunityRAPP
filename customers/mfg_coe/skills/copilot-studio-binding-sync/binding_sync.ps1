# Reference implementation — Copilot Studio Binding Sync
# Usage: .\binding_sync.ps1 -OrgUrl "https://orgXXX.crm.dynamics.com" -BotId "<guid>" [-DryRun]
#
# Diagnoses and fixes topic↔flow binding drift in a Copilot Studio agent.
# See SKILL.md for full procedure.

param(
  [Parameter(Mandatory)][string]$OrgUrl,
  [Parameter(Mandatory)][string]$BotId,
  [string]$TopicNameLike = "",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Token = az account get-access-token --resource $OrgUrl --query accessToken -o tsv
$Hdr = @{
  Authorization      = "Bearer $Token"
  Accept             = "application/json"
  "Content-Type"     = "application/json"
  "OData-MaxVersion" = "4.0"
  "OData-Version"    = "4.0"
  "If-Match"         = "*"
}

# 1. List all botcomponents in this bot
$filter = "_parentbotid_value eq $BotId and componenttype eq 9"
if ($TopicNameLike) { $filter += " and contains(name,'$TopicNameLike')" }
$topics = (Invoke-RestMethod "$OrgUrl/api/data/v9.2/botcomponents?`$filter=$filter&`$select=botcomponentid,name,data" -Headers $Hdr).value

Write-Host "Found $($topics.Count) topic(s) to inspect" -ForegroundColor Cyan

# 2. Find a working baseline (first topic that has InvokeFlowAction and parses cleanly)
$baseline = $topics | Where-Object { $_.data -match "InvokeFlowAction" } | Select-Object -First 1
if (-not $baseline) { throw "No topic with InvokeFlowAction found — cannot detect schema variant" }
$schemaVariant = if ($baseline.data -match "alwaysPrompt|init:Topic") { "v1" } else { "v2" }
Write-Host "Detected schema variant: $schemaVariant (baseline: $($baseline.name))" -ForegroundColor Yellow

# 3. For each topic, extract InvokeFlowAction blocks and find issues
$issues = @()
foreach ($t in $topics) {
  $unprefixedLiterals = [regex]::Matches($t.data, '(?m)^\s+(\w+):\s+"([^"=][^"]*)"') |
    Where-Object { $_.Groups[2].Value -notmatch '^\s*$' }

  foreach ($m in $unprefixedLiterals) {
    $issues += [pscustomobject]@{
      Topic    = $t.name
      Severity = "warn"
      Issue    = "Unprefixed string literal — '$($m.Groups[1].Value): `"$($m.Groups[2].Value)`"' should be '=`"$($m.Groups[2].Value)`"'"
    }
  }

  $hasV1Markers = $t.data -match "alwaysPrompt|init:Topic|allowInterruption: true"
  $hasV2Markers = $t.data -match "interruptionPolicy:|kind: TextPrebuiltEntity"
  if ($hasV1Markers -and $hasV2Markers) {
    $issues += [pscustomobject]@{ Topic = $t.name; Severity = "error"; Issue = "Mixed v1+v2 schema variants" }
  }
  if ($schemaVariant -eq "v1" -and $hasV2Markers -and -not $hasV1Markers) {
    $issues += [pscustomobject]@{ Topic = $t.name; Severity = "error"; Issue = "Uses v2 schema but baseline is v1 — convert" }
  }
}

# 4. Report
if ($issues.Count -eq 0) {
  Write-Host "✅ No issues detected" -ForegroundColor Green
} else {
  Write-Host "`n=== Issues found: $($issues.Count) ===" -ForegroundColor Red
  $issues | Format-Table -AutoSize -Wrap
}

if ($DryRun) {
  Write-Host "`n(Dry run — no changes applied. Re-run without -DryRun to fix.)" -ForegroundColor Yellow
  return
}

# 5. Fix loop (placeholder — actual rewrite logic per-topic is domain-specific;
#    the CoE Python port should pull each topic's flow output schema from PA REST
#    and regenerate the InvokeFlowAction block matching the detected variant.)
Write-Host "`n[NOT IMPLEMENTED in PS reference] Apply fixes via PATCH botcomponents.data" -ForegroundColor Yellow
Write-Host "See SKILL.md → Procedure step 7-9 for the algorithm. Use the Python port in coe_runner.py."

# 6. Verification PATCH headers (for documentation):
# Invoke-RestMethod "$OrgUrl/api/data/v9.2/botcomponents($id)" -Method Patch -Headers $Hdr `
#   -Body (@{ data = $newYaml } | ConvertTo-Json)
