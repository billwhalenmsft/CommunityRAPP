$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv)
$h = @{ Authorization = "Bearer $token"; Accept = "application/json" }
$b = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

Write-Host "=== SLA ===" -ForegroundColor Cyan
$sla = Invoke-RestMethod -Uri "$b/slas?`$select=name,statuscode,statecode,slaid" -Headers $h -UseBasicParsing
Write-Host "  Total SLAs: $($sla.value.Count)"
foreach ($s in $sla.value) {
    $st = switch ($s.statecode) { 0 { 'Draft' } 1 { 'Active' } default { $s.statecode } }
    Write-Host "  $($s.name) | State=$st | ID=$($s.slaid)"
}

Write-Host ""
Write-Host "=== SLA KPI Instances (Zurn/Elkay SLA) ===" -ForegroundColor Cyan
$zeSla = $sla.value | Where-Object { $_.name -match 'Zurn|Elkay' }
if ($zeSla) {
    $ki = Invoke-RestMethod -Uri "$b/slakpiinstances?`$select=name,status,_regarding_objectid_value&`$filter=_regarding_objectid_value ne null&`$top=5" -Headers $h -UseBasicParsing
    Write-Host "  KPI Instances (sample): $($ki.value.Count)"
}

Write-Host ""
Write-Host "=== Routing Rules ===" -ForegroundColor Cyan
$rr = Invoke-RestMethod -Uri "$b/routingrules?`$select=name,statuscode,statecode" -Headers $h -UseBasicParsing
Write-Host "  Total: $($rr.value.Count)"
foreach ($r in $rr.value) { Write-Host "  $($r.name) | State=$($r.statecode)" }

Write-Host ""
Write-Host "=== Zurn/Elkay Queues ===" -ForegroundColor Cyan
$q = Invoke-RestMethod -Uri "$b/queues?`$select=name,queuetypecode,emailaddress&`$filter=contains(name,'Zurn') or contains(name,'Elkay')&`$orderby=name" -Headers $h -UseBasicParsing
Write-Host "  Count: $($q.value.Count)"
foreach ($qi in $q.value) { Write-Host "  $($qi.name) | Type=$($qi.queuetypecode)" }

Write-Host ""
Write-Host "=== Existing Workstreams (Key ones) ===" -ForegroundColor Cyan
$ws = Invoke-RestMethod -Uri "$b/msdyn_liveworkstreams?`$select=msdyn_name,msdyn_streamsource,msdyn_liveworkstreamid,statecode" -Headers $h -UseBasicParsing
Write-Host "  Total: $($ws.value.Count)"
$voiceWs = $ws.value | Where-Object { $_.msdyn_streamsource -eq 192440000 -or $_.msdyn_name -match 'Voice|voice|Phone|phone' }
$chatWs = $ws.value | Where-Object { $_.msdyn_streamsource -eq 192350000 -or $_.msdyn_name -match 'chat|Chat|Live' }
$emailWs = $ws.value | Where-Object { $_.msdyn_streamsource -eq 192370000 -or $_.msdyn_name -match 'email|Email' }

Write-Host ""
Write-Host "  --- Voice-related ---"
foreach ($w in $voiceWs) { Write-Host "    $($w.msdyn_name) | Source=$($w.msdyn_streamsource) | ID=$($w.msdyn_liveworkstreamid)" }

Write-Host "  --- Chat-related ---"
foreach ($w in $chatWs) { Write-Host "    $($w.msdyn_name) | Source=$($w.msdyn_streamsource) | ID=$($w.msdyn_liveworkstreamid)" }

Write-Host "  --- Email-related ---"
foreach ($w in $emailWs) { Write-Host "    $($w.msdyn_name) | Source=$($w.msdyn_streamsource) | ID=$($w.msdyn_liveworkstreamid)" }

Write-Host ""
Write-Host "=== Unified Routing Intake Rules ===" -ForegroundColor Cyan
try {
    $ir = Invoke-RestMethod -Uri "$b/msdyn_intakerules?`$select=msdyn_name,statecode&`$top=20" -Headers $h -UseBasicParsing
    Write-Host "  Count: $($ir.value.Count)"
    foreach ($i in $ir.value) { Write-Host "  $($i.msdyn_name) | State=$($i.statecode)" }
} catch { Write-Host "  (entity not found or no data)" }

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
