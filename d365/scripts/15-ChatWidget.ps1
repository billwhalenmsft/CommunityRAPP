<#
.SYNOPSIS
    Injects the Omnichannel chat widget into the Power Pages portal content snippet.
.DESCRIPTION
    Updates the "Chat Widget Code" content snippet with a styled Omnichannel
    Live Chat widget that matches Zurn Elkay branding.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Connect-Dataverse

# Chat Widget Code content snippet for the Zurn Elkay portal
$snippetId = "04a44fed-1418-f111-8341-7ced8dceb26a"

# Verify the snippet exists
Write-Host "Verifying Chat Widget Code snippet..." -ForegroundColor Cyan
$existing = Invoke-DataverseGet -EntitySet "adx_contentsnippets" `
    -Filter "adx_contentsnippetid eq $snippetId" `
    -Select "adx_contentsnippetid,adx_name"

if (-not $existing -or $existing.Count -eq 0) {
    Write-Error "Content snippet $snippetId not found."
    return
}
$snippet = $existing[0]
Write-Host "  Found: $($snippet.adx_name)" -ForegroundColor Green

# Widget HTML with brand-matched CSS + the Omnichannel script
$widgetHtml = @"
<style>
/* Zurn Elkay chat widget branding */
.Microsoft_Omnichannel_LCWidget_Chat_Button,
#oclcw-chatbutton,
[data-lcw-id="oc-lcw-chat-button"] {
  background-color: #002855 !important;
  border-radius: 28px !important;
  box-shadow: 0 4px 16px rgba(0,40,85,0.35) !important;
  transition: transform 0.2s, box-shadow 0.2s !important;
}
[data-lcw-id="oc-lcw-chat-button"]:hover {
  transform: scale(1.08) !important;
  box-shadow: 0 6px 24px rgba(0,40,85,0.45) !important;
}
</style>
<script
  id="Microsoft_Omnichannel_LCWidget"
  src="https://oc-cdn-ocprod.azureedge.net/livechatwidget/scripts/LiveChatBootstrapper.js"
  data-app-id="a020344c-ad6b-42e7-ae44-44da4511ceee"
  data-lcw-version="prod"
  data-org-id="ec7cba3a-1c59-ef11-bfdf-002248282223"
  data-org-url="https://m-ec7cba3a-1c59-ef11-bfdf-002248282223.us.omnichannelengagementhub.com"
  data-color-override="#002855"
  data-font-family-override="'Segoe UI', sans-serif"
></script>
"@

Write-Host "Updating Chat Widget Code snippet..." -ForegroundColor Cyan
$body = @{ adx_value = $widgetHtml }
$result = Invoke-DataversePatch `
    -EntitySet "adx_contentsnippets" `
    -RecordId ([guid]$snippetId) `
    -Body $body

if ($result) {
    Write-Host "Chat Widget Code snippet updated successfully." -ForegroundColor Green
} else {
    Write-Warning "Patch returned no content. Verifying update..."
    $verify = Invoke-DataverseGet -EntitySet "adx_contentsnippets($snippetId)" `
        -Select "adx_contentsnippetid,adx_value"
    if ($verify.adx_value -and $verify.adx_value.Length -gt 100) {
        Write-Host "Verified - snippet value is $($verify.adx_value.Length) chars." -ForegroundColor Green
    } else {
        Write-Warning "Snippet value appears empty or short."
    }
}

Write-Host ""
Write-Host "Done. Clear portal cache to see the chat widget:" -ForegroundColor Yellow
Write-Host "  https://zurnelkaycustomercare.powerappsportals.com/_services/about" -ForegroundColor Cyan
Write-Host ""
Write-Host "For best appearance, also configure in Customer Service Admin Center:" -ForegroundColor Yellow
Write-Host "  1. Chat widget color theme -> #002855 (navy)" -ForegroundColor White
Write-Host "  2. Widget title -> 'Zurn Elkay Support'" -ForegroundColor White
Write-Host "  3. Agent display name / avatar" -ForegroundColor White
Write-Host "  4. Pre-chat survey (name, account, product line)" -ForegroundColor White
