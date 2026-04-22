# configure_bot.ps1
# Populates the Ascend SAP PR Agent in Copilot Studio with:
#   - Custom welcome message (ConversationStart topic)
#   - 6 custom SAP PR topics (Create PR, Get Status, Approve/Reject, Cancel, Vendor, Reminder)
# Uses Dataverse Web API via az login token.
# Run from: customers/ascend/solution/
# Requires: az login with access to org6feab6b5.crm.dynamics.com

param(
    [string]$OrgUrl = "https://org6feab6b5.crm.dynamics.com",
    [string]$BotName = "Ascend SAP PR Agent",
    [switch]$SkipTopicsCreate
)

# ── Auth ──────────────────────────────────────────────────────────────────────
Write-Host "[auth] Getting token..." -ForegroundColor Cyan
$token = az account get-access-token --resource $OrgUrl --query accessToken -o tsv 2>&1
if ($LASTEXITCODE -ne 0) { Write-Error "az login required. Run: az login"; exit 1 }

$Headers = @{
    Authorization      = "Bearer $token"
    "Content-Type"     = "application/json; charset=utf-8"
    Accept             = "application/json"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
    Prefer             = "return=representation"
}

# ── Find bot ──────────────────────────────────────────────────────────────────
Write-Host "[find] Looking up bot '$BotName'..." -ForegroundColor Cyan
$bots = Invoke-RestMethod "$OrgUrl/api/data/v9.2/bots?`$filter=name eq '$BotName'&`$select=botid,name,schemaname" -Headers $Headers
if ($bots.value.Count -eq 0) { Write-Error "Bot '$BotName' not found. Run add_flows_and_bot.ps1 first."; exit 1 }
$BotId  = $bots.value[0].botid
$BotSch = $bots.value[0].schemaname
Write-Host "  Found: $BotName (id=$BotId, schema=$BotSch)" -ForegroundColor Green

# ── Patch bot description ─────────────────────────────────────────────────────
Write-Host "[patch] Updating bot description..." -ForegroundColor Cyan
$desc = "SAP ECC 6.0 Purchase Requisition lifecycle agent for Ascend Performance Materials. " +
        "Create, approve, track, and cancel PRs via Microsoft Teams - powered by Dataverse " +
        "(demo) or SAP ERP connector (production)."
$patchBody = @{ description = $desc } | ConvertTo-Json
try {
    Invoke-RestMethod "$OrgUrl/api/data/v9.2/bots($BotId)" -Method PATCH -Headers $Headers -Body $patchBody | Out-Null
    Write-Host "  Description updated" -ForegroundColor Green
} catch { Write-Host "  WARN: $($_.Exception.Message)" -ForegroundColor Yellow }

# ── List existing components ───────────────────────────────────────────────────
Write-Host "[components] Listing existing bot components..." -ForegroundColor Cyan
$comps = Invoke-RestMethod "$OrgUrl/api/data/v9.2/botcomponents?`$filter=_parentbotid_value eq $BotId&`$select=botcomponentid,name,schemaname,componenttype" -Headers $Headers
Write-Host "  Found $($comps.value.Count) components:"
$comps.value | ForEach-Object { Write-Host "    - $($_.name) | $($_.schemaname) | type=$($_.componenttype)" }

# ── Helper: upsert a topic component ─────────────────────────────────────────
function Set-BotTopic {
    param([string]$SchemaName, [string]$DisplayName, [string]$Description, [string]$Content)
    $existing = $comps.value | Where-Object { $_.schemaname -eq $SchemaName }
    $body = if ($existing) {
        @{ name = $DisplayName; description = $Description; content = $Content } | ConvertTo-Json -Depth 2
    } else {
        @{ name = $DisplayName; schemaname = $SchemaName; description = $Description; content = $Content; componenttype = 9; language = 1033; "parentbotid@odata.bind" = "/bots($BotId)" } | ConvertTo-Json -Depth 2
    }
    try {
        if ($existing) {
            Invoke-RestMethod "$OrgUrl/api/data/v9.2/botcomponents($($existing[0].botcomponentid))" -Method PATCH -Headers $Headers -Body $body | Out-Null
            Write-Host "    Updated: $DisplayName" -ForegroundColor Green
        } else {
            $r = Invoke-RestMethod "$OrgUrl/api/data/v9.2/botcomponents" -Method POST -Headers $Headers -Body $body
            Write-Host "    Created: $DisplayName (id=$($r.botcomponentid))" -ForegroundColor Green
        }
    } catch {
        $msg = ($_.ErrorDetails.Message | ConvertFrom-Json -EA SilentlyContinue)?.error?.message ?? $_.Exception.Message
        Write-Host "    WARN [$DisplayName]: $msg" -ForegroundColor Yellow
    }
}

# ── Update ConversationStart topic ────────────────────────────────────────────
Write-Host "`n[topics] Configuring topics..." -ForegroundColor Cyan
$convStartComp = $comps.value | Where-Object { $_.schemaname -like "*ConversationStart*" }
$convStartSchema = if ($convStartComp) { $convStartComp[0].schemaname } else { "$BotSch.topic.ConversationStart" }

$convStartContent = "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnConversationStart`n  id: main`n  actions:`n    - kind: SendActivity`n      id: welcomeMsg`n      activity:`n        text: Welcome to the Ascend SAP Procurement Assistant! I manage your full SAP ECC 6.0 Purchase Requisition lifecycle from Microsoft Teams. I can help: Create a PR, Check PR status, Approve or reject PRs, Cancel a PR, Look up vendors, and Send approval reminders. Try: I need to raise a PR for 50K of industrial equipment or Show me my pending approvals"

Set-BotTopic -SchemaName $convStartSchema -DisplayName "Conversation Start" -Description "Ascend welcome message" -Content $convStartContent

if (-not $SkipTopicsCreate) {

    Set-BotTopic -SchemaName "ascend_SAP_PR_Agent_20260421115513.topic.SAPCreatePR" -DisplayName "SAP Create PR" -Description "Guides user through creating a SAP Purchase Requisition (writes to EBAN + EBKN)." -Content "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnRecognizedIntent`n  id: main`n  intent:`n    displayName: SAP Create PR`n    triggerQueries:`n      - I need to raise a purchase requisition`n      - create a PR`n      - I need to buy`n      - raise a PR`n      - new purchase req`n      - I want to order`n      - create purchase requisition`n      - I need to procure`n      - submit a PR`n  actions:`n    - kind: Question`n      id: askDescription`n      alwaysPrompt: false`n      variable: init:Topic.ItemDescription`n      prompt: What item or service do you need? (This becomes EBAN.TXZ01)`n      entity: StringPrebuiltEntity`n    - kind: Question`n      id: askVendor`n      alwaysPrompt: false`n      variable: init:Topic.VendorName`n      prompt: Which vendor? I will verify they are approved in SAP LFA1.`n      entity: StringPrebuiltEntity`n    - kind: Question`n      id: askAmount`n      alwaysPrompt: false`n      variable: init:Topic.Amount`n      prompt: What is the total value in USD?`n      entity: MoneyPrebuiltEntity`n    - kind: Question`n      id: askCostCenter`n      alwaysPrompt: false`n      variable: init:Topic.CostCenter`n      prompt: Which cost center? (e.g. CC1001 Texas City Ops, CC1002 R and D)`n      entity: StringPrebuiltEntity`n    - kind: Question`n      id: askConfirm`n      alwaysPrompt: false`n      variable: init:Topic.Confirmed`n      prompt: Confirm submission of PR for {Topic.Amount} from {Topic.VendorName} charged to {Topic.CostCenter}?`n      entity: BooleanPrebuiltEntity`n    - kind: ConditionGroup`n      id: checkConfirm`n      conditions:`n        - id: ifYes`n          condition: =Topic.Confirmed = true`n          actions:`n            - kind: SendActivity`n              id: successMsg`n              activity:`n                text: PR submitted to SAP! Your requisition has been created and routed to the appropriate approver based on your DoA level.`n      elseActions:`n        - kind: SendActivity`n          id: cancelMsg`n          activity:`n            text: PR cancelled. Let me know if you would like to try again."

    Set-BotTopic -SchemaName "ascend_SAP_PR_Agent_20260421115513.topic.SAPGetPRStatus" -DisplayName "SAP Get PR Status" -Description "Look up PR status by number, list user PRs, or show pending approvals." -Content "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnRecognizedIntent`n  id: main`n  intent:`n    displayName: SAP Get PR Status`n    triggerQueries:`n      - check PR status`n      - what is the status of PR`n      - status of my PR`n      - show my PRs`n      - list my purchase requisitions`n      - pending approvals`n      - what PRs are waiting for my approval`n      - show me open PRs`n      - where is my PR`n  actions:`n    - kind: Question`n      id: askPRNumber`n      alwaysPrompt: false`n      variable: init:Topic.PRNumber`n      prompt: What is the PR number (BANFN)? Or say list to see all your open PRs, or approvals to see your approval queue.`n      entity: StringPrebuiltEntity`n    - kind: SendActivity`n      id: lookingUp`n      activity:`n        text: Looking up PR {Topic.PRNumber} in SAP EBAN..."

    Set-BotTopic -SchemaName "ascend_SAP_PR_Agent_20260421115513.topic.SAPApproveRejectPR" -DisplayName "SAP Approve Reject PR" -Description "Approve or reject a purchase requisition - updates EBAN release indicator (FRGST)." -Content "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnRecognizedIntent`n  id: main`n  intent:`n    displayName: SAP Approve Reject PR`n    triggerQueries:`n      - approve PR`n      - reject PR`n      - I approve`n      - I reject`n      - approve purchase requisition`n      - approve the PR`n      - deny PR`n  actions:`n    - kind: Question`n      id: askPRNumber`n      alwaysPrompt: false`n      variable: init:Topic.PRNumber`n      prompt: Which PR number (BANFN) would you like to approve or reject?`n      entity: StringPrebuiltEntity`n    - kind: Question`n      id: askDecision`n      alwaysPrompt: false`n      variable: init:Topic.ApprovalDecision`n      prompt: Approve or reject PR {Topic.PRNumber}?`n      entity:`n        kind: EmbeddedEntity`n        definition:`n          kind: ClosedListEntity`n          items:`n            - id: Approve`n              displayName: Approve`n            - id: Reject`n              displayName: Reject`n    - kind: SendActivity`n      id: decisionConfirmed`n      activity:`n        text: Decision recorded in SAP EBAN. PR {Topic.PRNumber} has been {Topic.ApprovalDecision}d. The release indicator (FRGST) has been updated."

    Set-BotTopic -SchemaName "ascend_SAP_PR_Agent_20260421115513.topic.SAPCancelEditPR" -DisplayName "SAP Cancel Edit PR" -Description "Cancel or edit a Purchase Requisition - updates EBAN deletion indicator." -Content "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnRecognizedIntent`n  id: main`n  intent:`n    displayName: SAP Cancel Edit PR`n    triggerQueries:`n      - cancel PR`n      - cancel purchase requisition`n      - delete PR`n      - cancel my PR`n      - I want to cancel`n      - edit PR`n      - modify PR`n      - change PR`n  actions:`n    - kind: Question`n      id: askPRNumber`n      alwaysPrompt: false`n      variable: init:Topic.PRNumber`n      prompt: Which PR number (BANFN) would you like to cancel or edit?`n      entity: StringPrebuiltEntity`n    - kind: Question`n      id: askReason`n      alwaysPrompt: false`n      variable: init:Topic.CancelReason`n      prompt: What is the reason? (This is logged in the SAP audit trail)`n      entity: StringPrebuiltEntity`n    - kind: SendActivity`n      id: cancelConfirmed`n      activity:`n        text: PR {Topic.PRNumber} has been updated in SAP EBAN. The deletion indicator has been set and the requester notified."

    Set-BotTopic -SchemaName "ascend_SAP_PR_Agent_20260421115513.topic.SAPVendorLookup" -DisplayName "SAP Vendor Lookup" -Description "Look up a vendor in the SAP vendor master (LFA1) to verify approval status." -Content "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnRecognizedIntent`n  id: main`n  intent:`n    displayName: SAP Vendor Lookup`n    triggerQueries:`n      - vendor lookup`n      - is this vendor approved`n      - check vendor`n      - search for vendor`n      - approved supplier`n      - is Siemens approved`n      - find vendor`n      - vendor search`n      - is this supplier in SAP`n  actions:`n    - kind: Question`n      id: askVendorName`n      alwaysPrompt: false`n      variable: init:Topic.VendorSearchName`n      prompt: Which vendor would you like to look up in the SAP vendor master (LFA1)?`n      entity: StringPrebuiltEntity`n    - kind: SendActivity`n      id: vendorResult`n      activity:`n        text: Searching SAP LFA1 for {Topic.VendorSearchName}. Results will show vendor status and any purchasing blocks."

    Set-BotTopic -SchemaName "ascend_SAP_PR_Agent_20260421115513.topic.SAPSendReminder" -DisplayName "SAP Send Reminder" -Description "Send an approval reminder to the approver for a pending PR." -Content "kind: AdaptiveDialog`nbeginDialog:`n  kind: OnRecognizedIntent`n  id: main`n  intent:`n    displayName: SAP Send Reminder`n    triggerQueries:`n      - send reminder`n      - remind approver`n      - follow up on PR`n      - chase the approver`n      - PR has not been approved yet`n      - escalate PR`n      - reminder for PR`n  actions:`n    - kind: Question`n      id: askPRNumber`n      alwaysPrompt: false`n      variable: init:Topic.PRNumber`n      prompt: Which PR number (BANFN) needs a reminder sent to the approver?`n      entity: StringPrebuiltEntity`n    - kind: SendActivity`n      id: reminderSent`n      activity:`n        text: Reminder sent! The approver for PR {Topic.PRNumber} has been notified. If they have not responded in 48 hours, let me know and I can escalate."

} # end -not SkipTopicsCreate

# ── Summary ────────────────────────────────────────────────────────────────────
Write-Host "`n════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "Bot configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS in Copilot Studio UI:" -ForegroundColor Yellow
Write-Host "  1. Open: https://copilotstudio.microsoft.com" -ForegroundColor White
Write-Host "  2. Switch to environment: Mfg Gold Template (org6feab6b5)" -ForegroundColor White
Write-Host "  3. Find agent: '$BotName'" -ForegroundColor White
Write-Host "  4. Go to Overview -> Instructions -> paste from:" -ForegroundColor White
Write-Host "     customers/ascend/copilot-studio/agent_instructions.md" -ForegroundColor Cyan
Write-Host "  5. Actions tab -> connect the 6 Power Automate flows" -ForegroundColor White
Write-Host "  6. Publish -> Test -> Deploy to Teams" -ForegroundColor White
Write-Host "════════════════════════════════════════" -ForegroundColor Magenta

