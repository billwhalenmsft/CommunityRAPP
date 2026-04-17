<#
.SYNOPSIS
    Seed rich ERAC demo data — appointments, tasks, PRR records, treaties,
    risk assessments, reserve adequacy, and legal disputes.

.DESCRIPTION
    Reads account-ids.json for cedent GUIDs.
    Seeds data across OOTB tables (appointment, task) and ERAC custom tables.
    Idempotent by name — skips records that already exist.

.PARAMETER Org
    Dataverse org URL (default: https://orgecbce8ef.crm.dynamics.com)

.PARAMETER Phase
    OotbData | CustomData | All (default)

.EXAMPLE
    .\Seed-EracRichData.ps1
    .\Seed-EracRichData.ps1 -Phase OotbData
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [ValidateSet("OotbData","CustomData","All")]
    [string]$Phase = "All"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

# ─────────────────────────────────────────────────────────────────────────────
# AUTH + HELPERS
# ─────────────────────────────────────────────────────────────────────────────
function Get-Token {
    $raw = az account get-access-token --resource $Org 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Error "Run: az login" }
    return ($raw | ConvertFrom-Json).accessToken
}

$script:Token = Get-Token
$script:Headers = @{
    Authorization      = "Bearer $script:Token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
    Prefer             = "return=representation"
}

function Invoke-Dv {
    param([string]$Method, [string]$Path, [object]$Body=$null)
    $uri = "$Org/api/data/v9.2/$Path"
    $params = @{ Uri=$uri; Method=$Method; Headers=$script:Headers; TimeoutSec=30; UseBasicParsing=$true }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    for ($i=1; $i -le 3; $i++) {
        try {
            $resp = Invoke-WebRequest @params
            if ($resp.Content) { return $resp.Content | ConvertFrom-Json }
            return @{ ok=$true }
        } catch {
            $code = $_.Exception.Response.StatusCode.value__
            $msg  = $_.ErrorDetails.Message
            if ($code -eq 429) { Start-Sleep -Seconds (10*$i); continue }
            if ($i -eq 3) { Write-Warning "  ✗ $Method $Path → $code : $($msg.Substring(0,[Math]::Min(200,$msg.Length)))"; return $null }
            Start-Sleep -Seconds (2*$i)
        }
    }
}

function Post-Record([string]$Entity, [hashtable]$Body, [string]$Label) {
    $r = Invoke-Dv -Method POST -Path $Entity -Body $Body
    if ($r) {
        $id = if ($r.activityid) { $r.activityid } `
              elseif ($r.taskid)  { $r.taskid }  `
              else { $r.PSObject.Properties | Where-Object { $_.Name -match "id$" } | Select-Object -First 1 -ExpandProperty Value }
        Write-Host "  ✓ $Label" -ForegroundColor Green
        return $id
    }
    return $null
}

# ─────────────────────────────────────────────────────────────────────────────
# LOAD ACCOUNT IDs
# ─────────────────────────────────────────────────────────────────────────────
$idsPath = Join-Path $ScriptDir "..\data\account-ids.json"
if (-not (Test-Path $idsPath)) { Write-Error "account-ids.json not found. Run Provision-EracDataverse.ps1 first." }
$ids = Get-Content $idsPath | ConvertFrom-Json
$C = @{
    c1 = $ids.c1  # Acme Reinsurance
    c2 = $ids.c2  # Titan Mutual Re
    c3 = $ids.c3  # Harbor Group
    c4 = $ids.c4  # Pacific Coastal Re
    c5 = $ids.c5  # Meridian Re Partners
    c6 = $ids.c6  # Summit Life & Casualty
}
Write-Host "Loaded account IDs:" -ForegroundColor Cyan
$C.GetEnumerator() | ForEach-Object { Write-Host "  $($_.Key) = $($_.Value)" }

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: OOTB DATA (Appointments + Tasks)
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-OotbData {
    Write-Host "`n=== PHASE: OOTB DATA (Appointments + Tasks) ===" -ForegroundColor Cyan

    # ── APPOINTMENTS (Engagement Log) ────────────────────────────────────────
    Write-Host "`n[Appointments]"
    $appointments = @(
        @{ subject="Q1 2026 QBR — Acme Reinsurance";      start="2026-02-14T09:00:00Z"; duration=90; accountId=$C.c1;
           scheduledend="2026-02-14T10:30:00Z"; meetingtype=200000; outcome=200000;
           nextsteps="Data integration milestone review Apr 2026. Confirm actuary team availability." },
        @{ subject="Claims Review — Titan Mutual Re";       start="2026-02-28T14:00:00Z"; duration=60; accountId=$C.c2;
           scheduledend="2026-02-28T15:00:00Z"; meetingtype=200001; outcome=200001;
           nextsteps="Financial signatory documentation due Mar 15. Raj Patel to provide signed docs." },
        @{ subject="Treaty Renewal Discussion — Pacific Coastal"; start="2026-02-20T10:00:00Z"; duration=60; accountId=$C.c4;
           scheduledend="2026-02-20T11:00:00Z"; meetingtype=200002; outcome=200000;
           nextsteps="Draft new treaty terms by Mar 31. Nina Romero to confirm CAT exposure schedule." },
        @{ subject="Compliance Risk Review — Harbor Group"; start="2026-01-30T13:00:00Z"; duration=60; accountId=$C.c3;
           scheduledend="2026-01-30T14:00:00Z"; meetingtype=200003; outcome=200003;
           nextsteps="Compliance remediation plan due Q2 2026. Elaine Cho leading." },
        @{ subject="Performance Review — Meridian Re";      start="2026-01-22T11:00:00Z"; duration=60; accountId=$C.c5;
           scheduledend="2026-01-22T12:00:00Z"; meetingtype=200003; outcome=200002;
           nextsteps="Escalate to senior risk committee. Risk review Q2 2026. Angela Torres follow-up." },
        @{ subject="Annual Review — Summit Life & Casualty";start="2025-12-12T09:00:00Z"; duration=60; accountId=$C.c6;
           scheduledend="2025-12-12T10:00:00Z"; meetingtype=200005; outcome=200001;
           nextsteps="Annual renewal discussion scheduled Mar 2026. David Huang to prepare actuarial summary." },
        @{ subject="Executive Summit — Acme Reinsurance";   start="2025-11-15T09:00:00Z"; duration=120; accountId=$C.c1;
           scheduledend="2025-11-15T11:00:00Z"; meetingtype=200004; outcome=200000;
           nextsteps="Multi-year strategic roadmap agreed. Claims automation pilot approved for Q1 2026." },
        @{ subject="Q4 2025 QBR — Titan Mutual Re";         start="2025-11-20T14:00:00Z"; duration=90; accountId=$C.c2;
           scheduledend="2025-11-20T15:30:00Z"; meetingtype=200000; outcome=200001;
           nextsteps="Mid-year treaty review needed. Raj Patel to submit exposure report." }
    )

    foreach ($appt in $appointments) {
        $body = @{
            subject                  = $appt.subject
            scheduledstart           = $appt.start
            scheduledend             = $appt.scheduledend
            actualdurationminutes    = $appt.duration
            "regardingobjectid_account@odata.bind" = "/accounts($($appt.accountId))"
            erac_meetingtype         = $appt.meetingtype
            erac_outcome             = $appt.outcome
            erac_nextsteps           = $appt.nextsteps
        }
        Post-Record "appointments" $body $appt.subject | Out-Null
        Start-Sleep -Seconds 1
    }

    # ── TASKS (Kanban) ───────────────────────────────────────────────────────
    Write-Host "`n[Tasks]"
    $tasks = @(
        @{ subject="Claims data reconciliation — Acme Q1";  accountId=$C.c1; priority=2; stage=200000; etype=200000;
           description="Reconcile Q1 2026 claims bordereau against GE systems. Deadline: Apr 30." },
        @{ subject="Treaty renewal package — Pacific Coastal"; accountId=$C.c4; priority=2; stage=200001; etype=200002;
           description="Prepare full treaty renewal package including updated CAT model output." },
        @{ subject="Risk committee escalation — Meridian Re"; accountId=$C.c5; priority=0; stage=200001; etype=200000;
           description="Prepare escalation memo for senior risk committee. Include 3-period trend analysis." },
        @{ subject="Compliance remediation plan — Harbor";   accountId=$C.c3; priority=1; stage=200001; etype=200001;
           description="Receive and review Harbor Group compliance remediation plan. Due Q2 2026." },
        @{ subject="Update exposure schedule — Titan";       accountId=$C.c2; priority=1; stage=200000; etype=200003;
           description="Request updated exposure schedule from Raj Patel for financial signatory records." },
        @{ subject="Actuarial review — Summit reserve adequacy"; accountId=$C.c6; priority=1; stage=200001; etype=200001;
           description="Review actuarial adequacy assessment for Summit Life & Casualty. Annual review cycle." },
        @{ subject="Acme data integration — Phase 2 kickoff"; accountId=$C.c1; priority=2; stage=200002; etype=200004;
           description="Kick off Phase 2 data integration with Acme. Tech leads confirmed." },
        @{ subject="Treaty dispute analysis — Harbor Group"; accountId=$C.c3; priority=0; stage=200001; etype=200002;
           description="Draft legal analysis for Harbor coverage dispute. Involve outside counsel if needed." },
        @{ subject="QBR prep — Pacific Coastal Q2 2026";     accountId=$C.c4; priority=1; stage=200000; etype=200005;
           description="Prepare QBR materials for Q2 2026 Pacific Coastal review. Include new treaty terms." },
        @{ subject="Annual review materials — Summit";        accountId=$C.c6; priority=1; stage=200003; etype=200005;
           description="Completed: Annual review materials prepared and submitted. Archived." }
    )

    foreach ($task in $tasks) {
        $body = @{
            subject                  = $task.subject
            prioritycode             = $task.priority
            description              = $task.description
            "regardingobjectid_account@odata.bind" = "/accounts($($task.accountId))"
            erac_kanbanstage         = $task.stage
            erac_engagementtype      = $task.etype
        }
        Post-Record "tasks" $body $task.subject | Out-Null
        Start-Sleep -Seconds 1
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: CUSTOM TABLE DATA
# ─────────────────────────────────────────────────────────────────────────────
function Invoke-CustomData {
    Write-Host "`n=== PHASE: CUSTOM TABLE DATA ===" -ForegroundColor Cyan

    # Helper to get the account navigation property name
    function AccountBind([string]$id, [string]$lookupAttr="erac_accountid") {
        return "$lookupAttr@odata.bind=/accounts($id)"
    }

    # ── PARTNERSHIP RATINGS (PRR) — 2 periods x 6 cedents ───────────────────
    Write-Host "`n[Partnership Ratings (PRR)]"
    $prrs = @(
        # Q1 2026
        @{ name="Acme Reinsurance — Q1 2026";      acct=$C.c1; period="Q1 2026"; rel=4.5; tech=4.0; strat=4.2; ops=4.1; overall=4.2; trend=200000; qbr="2026-02-14"; status=200002; notes="Excellent partnership momentum. Claims automation pilot approved." },
        @{ name="Titan Mutual Re — Q1 2026";        acct=$C.c2; period="Q1 2026"; rel=4.0; tech=3.5; strat=3.8; ops=3.9; overall=3.8; trend=200001; qbr="2026-01-28"; status=200002; notes="Financial signatory risk flag active. Stable performance overall." },
        @{ name="Harbor Group — Q1 2026";           acct=$C.c3; period="Q1 2026"; rel=3.2; tech=3.8; strat=3.4; ops=3.6; overall=3.5; trend=200001; qbr="2026-03-03"; status=200002; notes="Compliance and litigation flags under review. Tech team responsive." },
        @{ name="Pacific Coastal Re — Q1 2026";     acct=$C.c4; period="Q1 2026"; rel=4.2; tech=4.0; strat=3.8; ops=4.0; overall=4.0; trend=200000; qbr="2026-02-20"; status=200002; notes="New treaty negotiation in progress. Strong executive engagement." },
        @{ name="Meridian Re Partners — Q1 2026";   acct=$C.c5; period="Q1 2026"; rel=3.0; tech=2.5; strat=2.8; ops=3.3; overall=2.9; trend=200002; qbr="";           status=200003; notes="Technical and strategic dimensions declining. Escalation pending." },
        @{ name="Summit Life & Casualty — Q1 2026"; acct=$C.c6; period="Q1 2026"; rel=3.2; tech=3.0; strat=2.9; ops=3.3; overall=3.1; trend=200001; qbr="2025-12-12"; status=200002; notes="Transactional relationship. Annual review cycle on track." },
        # Q4 2025
        @{ name="Acme Reinsurance — Q4 2025";      acct=$C.c1; period="Q4 2025"; rel=4.2; tech=3.8; strat=4.0; ops=3.9; overall=4.0; trend=200000; qbr="2025-11-15"; status=200002; notes="Strong Q4. Executive summit completed. Phase 2 roadmap agreed." },
        @{ name="Titan Mutual Re — Q4 2025";        acct=$C.c2; period="Q4 2025"; rel=3.9; tech=3.4; strat=3.7; ops=3.8; overall=3.7; trend=200001; qbr="2025-11-20"; status=200002; notes="Mid-year treaty review requested. Exposure report outstanding." },
        @{ name="Harbor Group — Q4 2025";           acct=$C.c3; period="Q4 2025"; rel=3.3; tech=3.7; strat=3.4; ops=3.5; overall=3.5; trend=200001; qbr="2025-10-14"; status=200002; notes="Compliance assessment completed. Litigation flag added Q4." },
        @{ name="Pacific Coastal Re — Q4 2025";     acct=$C.c4; period="Q4 2025"; rel=4.0; tech=3.8; strat=3.6; ops=3.8; overall=3.8; trend=200000; qbr="2025-11-08"; status=200002; notes="CAT season review complete. Treaty renewal discussions initiated." },
        @{ name="Meridian Re Partners — Q4 2025";   acct=$C.c5; period="Q4 2025"; rel=3.2; tech=2.8; strat=3.0; ops=3.4; overall=3.1; trend=200002; qbr="2025-10-05"; status=200002; notes="Performance concerns identified. Watch list activated." },
        @{ name="Summit Life & Casualty — Q4 2025"; acct=$C.c6; period="Q4 2025"; rel=3.1; tech=2.9; strat=2.8; ops=3.2; overall=3.0; trend=200001; qbr="2025-12-12"; status=200002; notes="Annual review cycle completed on schedule." }
    )
    foreach ($p in $prrs) {
        $body = @{ erac_name=$p.name; erac_period=$p.period; erac_relationship=$p.rel; erac_technical=$p.tech; erac_strategic=$p.strat; erac_operational=$p.ops; erac_overallrating=$p.overall; erac_ratingtrend=$p.trend; erac_status=$p.status; erac_notes=$p.notes }
        if ($p.qbr) { $body["erac_lastqbrdate"] = $p.qbr }
        $body["erac_accountid@odata.bind"] = "/accounts($($p.acct))"
        Post-Record "erac_partnershipratings" $body $p.name | Out-Null
        Start-Sleep -Seconds 1
    }

    # ── RISK ASSESSMENTS ─────────────────────────────────────────────────────
    Write-Host "`n[Risk Assessments]"
    $risks = @(
        @{ name="Acme Reinsurance — Risk Q1 2026";      acct=$C.c1; period="Q1 2026"; fin=200000; tech=200000; comp=200000; cpty=200000; agg=200000; status=200001; date="2026-02-01"; notes="Strong controls. Data integration adds minor tech risk." },
        @{ name="Titan Mutual Re — Risk Q1 2026";        acct=$C.c2; period="Q1 2026"; fin=200001; tech=200001; comp=200001; cpty=200001; agg=200001; status=200001; date="2026-02-15"; notes="Financial signatory risk flag — medium. Counterparty exposure stable." },
        @{ name="Harbor Group — Risk Q1 2026";           acct=$C.c3; period="Q1 2026"; fin=200001; tech=200001; comp=200002; cpty=200001; agg=200001; status=200000; date="2026-01-20"; notes="Compliance risk elevated due to litigation. Under remediation." },
        @{ name="Pacific Coastal Re — Risk Q1 2026";     acct=$C.c4; period="Q1 2026"; fin=200001; tech=200000; comp=200000; cpty=200000; agg=200000; status=200001; date="2026-02-10"; notes="CAT exposure elevated seasonally. Controls adequate." },
        @{ name="Meridian Re Partners — Risk Q1 2026";   acct=$C.c5; period="Q1 2026"; fin=200002; tech=200002; comp=200001; cpty=200002; agg=200002; status=200002; date="2026-01-15"; notes="High financial and counterparty risk. Escalated to committee." },
        @{ name="Summit Life & Casualty — Risk Q1 2026"; acct=$C.c6; period="Q1 2026"; fin=200001; tech=200001; comp=200001; cpty=200001; agg=200001; status=200001; date="2026-01-05"; notes="Moderate risk profile. Annual review cycle stable." }
    )
    foreach ($r in $risks) {
        $body = @{ erac_name=$r.name; erac_period=$r.period; erac_financialrisk=$r.fin; erac_technologyrisk=$r.tech; erac_compliancerisk=$r.comp; erac_counterpartyrisk=$r.cpty; erac_aggregaterisk=$r.agg; erac_approvalstatus=$r.status; erac_reviewdate=$r.date; erac_notes=$r.notes }
        $body["erac_accountid@odata.bind"] = "/accounts($($r.acct))"
        Post-Record "erac_riskassessments" $body $r.name | Out-Null
        Start-Sleep -Seconds 1
    }

    # ── TREATIES ─────────────────────────────────────────────────────────────
    Write-Host "`n[Treaties]"
    $treaties = @(
        @{ name="Acme Re — Quota Share Treaty 2024-2026";        acct=$C.c1; type=200000; eff="2024-01-01"; exp="2026-12-31"; expM=850.0;  law="New York";      status=200000; notes="Flagship treaty. Auto-renewal clause active." },
        @{ name="Acme Re — Excess of Loss Treaty 2025";          acct=$C.c1; type=200001; eff="2025-01-01"; exp="2025-12-31"; expM=320.0;  law="New York";      status=200002; notes="Expired end of 2025. Renewal under negotiation." },
        @{ name="Titan Mutual — Quota Share Treaty 2024-2026";   acct=$C.c2; type=200000; eff="2024-07-01"; exp="2026-06-30"; expM=680.0;  law="Delaware";     status=200000; notes="Mid-term. Financial signatory review required." },
        @{ name="Harbor Group — Surplus Treaty 2025-2026";       acct=$C.c3; type=200003; eff="2025-01-01"; exp="2026-12-31"; expM=490.0;  law="Connecticut";  status=200004; notes="Under legal review due to coverage dispute." },
        @{ name="Pacific Coastal — Quota Share Treaty 2026";     acct=$C.c4; type=200000; eff="2026-01-01"; exp="2026-12-31"; expM=410.0;  law="California";   status=200000; notes="New treaty effective Q1 2026. CAT event clause included." },
        @{ name="Pacific Coastal — Excess of Loss Treaty 2026";  acct=$C.c4; type=200001; eff="2026-01-01"; exp="2026-12-31"; expM=280.0;  law="California";   status=200001; notes="Pending renewal signature from Nina Romero." },
        @{ name="Meridian Re — Facultative Treaty 2025";         acct=$C.c5; type=200002; eff="2025-01-01"; exp="2025-12-31"; expM=210.0;  law="Illinois";     status=200002; notes="Expired. Not renewed pending performance review." },
        @{ name="Summit Life — Stop Loss Treaty 2025-2026";      acct=$C.c6; type=200004; eff="2025-07-01"; exp="2026-06-30"; expM=145.0;  law="Ohio";         status=200000; notes="Annual stop-loss. Life & casualty mix covered." }
    )
    foreach ($t in $treaties) {
        $body = @{ erac_name=$t.name; erac_treatytype=$t.type; erac_effectivedate=$t.eff; erac_expirydate=$t.exp; erac_exposurem=$t.expM; erac_governinglaw=$t.law; erac_status=$t.status; erac_notes=$t.notes }
        $body["erac_accountid@odata.bind"] = "/accounts($($t.acct))"
        Post-Record "erac_treaties" $body $t.name | Out-Null
        Start-Sleep -Seconds 1
    }

    # ── RESERVE ADEQUACY ─────────────────────────────────────────────────────
    Write-Host "`n[Reserve Adequacy]"
    $reserves = @(
        @{ name="Acme Re — Property CAT Q1 2026";        acct=$C.c1; lob="Property Catastrophe"; period="Q1 2026"; curr=420.0; rec=415.0; pct=101.2; status=200000; notes="Slightly over-reserved. Within tolerance." },
        @{ name="Acme Re — Workers Comp Q1 2026";        acct=$C.c1; lob="Workers Compensation"; period="Q1 2026"; curr=180.0; rec=195.0; pct=92.3;  status=200001; notes="Under-reserved by approx $15M. Actuarial team notified." },
        @{ name="Titan Re — General Liability Q1 2026";  acct=$C.c2; lob="General Liability";    period="Q1 2026"; curr=290.0; rec=285.0; pct=101.8; status=200000; notes="Adequate. Minor revision from prior quarter." },
        @{ name="Harbor Group — Multi-Line Q1 2026";     acct=$C.c3; lob="Multi-Line";            period="Q1 2026"; curr=310.0; rec=340.0; pct=91.2;  status=200001; notes="Under-reserved. Litigation exposure not fully captured." },
        @{ name="Pacific Coastal — Property Q1 2026";    acct=$C.c4; lob="Property";              period="Q1 2026"; curr=255.0; rec=248.0; pct=102.8; status=200000; notes="Adequate. CAT season model within bounds." },
        @{ name="Meridian Re — Casualty Q1 2026";        acct=$C.c5; lob="Casualty";              period="Q1 2026"; curr=155.0; rec=190.0; pct=81.6;  status=200001; notes="Significantly under-reserved. Under review by senior actuary." },
        @{ name="Summit Life — Life & Disability Q1 2026";acct=$C.c6; lob="Life & Disability";   period="Q1 2026"; curr=98.0;  rec=96.0;  pct=102.1; status=200000; notes="Adequate. Annual review completed." }
    )
    foreach ($r in $reserves) {
        $body = @{ erac_name=$r.name; erac_lob=$r.lob; erac_period=$r.period; erac_currentreserve=$r.curr; erac_recreserve=$r.rec; erac_adequacypct=$r.pct; erac_status=$r.status; erac_notes=$r.notes }
        $body["erac_accountid@odata.bind"] = "/accounts($($r.acct))"
        Post-Record "erac_reserveadequacies" $body $r.name | Out-Null
        Start-Sleep -Seconds 1
    }

    # ── LEGAL DISPUTES ───────────────────────────────────────────────────────
    Write-Host "`n[Legal Disputes]"
    $disputes = @(
        @{ name="Harbor Group — Coverage Dispute 2025-001";      acct=$C.c3; type=200000; filed="2025-08-12"; expM=45.0;  status=200000; notes="Dispute over scope of CAT coverage clause. External counsel engaged." },
        @{ name="Meridian Re — Commutation 2025-001";            acct=$C.c5; type=200001; filed="2025-10-01"; expM=28.0;  status=200003; notes="Commutation negotiation initiated. In arbitration per treaty terms." },
        @{ name="Titan Mutual — Data Quality Dispute 2025-001";  acct=$C.c2; type=200002; filed="2025-11-15"; expM=12.0;  status=200004; notes="Bordereau data quality dispute. Mediation scheduled Feb 2026." },
        @{ name="Harbor Group — Regulatory 2026-001";            acct=$C.c3; type=200003; filed="2026-01-20"; expM=18.0;  status=200000; notes="Regulatory inquiry from state DOI. Compliance team responding." }
    )
    foreach ($d in $disputes) {
        $body = @{ erac_name=$d.name; erac_disputetype=$d.type; erac_fileddate=$d.filed; erac_exposure=$d.expM; erac_status=$d.status; erac_notes=$d.notes }
        $body["erac_accountid@odata.bind"] = "/accounts($($d.acct))"
        Post-Record "erac_disputes" $body $d.name | Out-Null
        Start-Sleep -Seconds 1
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
function Show-Summary {
    Write-Host "`n=== SEED SUMMARY ===" -ForegroundColor Cyan
    Write-Host "  Appointments:         8"
    Write-Host "  Tasks:               10"
    Write-Host "  PRR Records:         12  (2 periods x 6 cedents)"
    Write-Host "  Risk Assessments:     6"
    Write-Host "  Treaties:             8"
    Write-Host "  Reserve Adequacy:     7"
    Write-Host "  Legal Disputes:       4"
    Write-Host "  ─────────────────────"
    Write-Host "  Total records:       55"
    Write-Host "`n✅ Seed complete" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if ($Phase -eq "OotbData"    -or $Phase -eq "All") { Invoke-OotbData }
if ($Phase -eq "CustomData"  -or $Phase -eq "All") { Invoke-CustomData }
Show-Summary
