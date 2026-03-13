<#
.SYNOPSIS
    Step 25 - Add Service Toolkit OnLoad Handler to Entity Forms
.DESCRIPTION
    Programmatically injects the BW.ServiceToolkit.onLoad event handler
    into the formxml of key entity forms used in Customer Service Workspace.
    This causes the Service Toolkit side pane (Order Modification Wizard)
    to open automatically when agents view these records.

    Target forms:
      - Case for Multisession experience  (incident)
      - Enhanced full case form            (incident)
      - Active Conversation                (msdyn_ocliveworkitem)
      - Phone Call                         (phonecall)
      - Account for Multisession experience(account)

    The script is idempotent: if the handler or library reference already
    exists in a form, that form is skipped.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "25" "Add Service Toolkit OnLoad Handler to Forms"
Connect-Dataverse

# ============================================================
# Configuration
# ============================================================
$LibraryName = "bw_ServiceToolkitLoader"
$FunctionName = "BW.ServiceToolkit.onLoad"

# Forms to modify: @{ DisplayName = FormId }
$targetForms = [ordered]@{
    "Case for Multisession experience"    = "b05c1e9c-94d0-46c1-8968-df49b8f33ec7"
    "Enhanced full case form"             = "cd0d48a0-10c6-ec11-a7b5-000d3a58b83a"
    "Active Conversation"                 = "5fe86453-73ea-4821-b6dd-ddc06e1755a1"
    "Phone Call"                          = "a91390a5-99bb-4d10-9eee-3a5c87f841f1"
    "Account for Multisession experience" = "ff49442f-8c60-4877-bdae-8fe51e6f4636"
}

# Entity logical names for publishing (unique set)
$entitiesToPublish = @("incident", "msdyn_ocliveworkitem", "phonecall", "account")

$modifiedCount = 0

foreach ($formEntry in $targetForms.GetEnumerator()) {
    $formName = $formEntry.Key
    $formId = $formEntry.Value

    Write-Host "`n--- Processing: $formName ($formId) ---" -ForegroundColor Cyan

    # --------------------------------------------------------
    # 1. GET the current formxml
    # --------------------------------------------------------
    $headers = Get-DataverseHeaders
    $apiUrl = "$(Get-DataverseApiUrl)/systemforms($formId)?`$select=formxml"
    try {
        $formRecord = Invoke-RestMethod -Uri $apiUrl -Method Get -Headers $headers -ErrorAction Stop
    } catch {
        Write-Warning "  Could not retrieve form '$formName': $($_.Exception.Message)"
        continue
    }

    $formXml = $formRecord.formxml
    if (-not $formXml) {
        Write-Warning "  formxml is empty for '$formName' - skipping"
        continue
    }

    # --------------------------------------------------------
    # 2. Check if handler already exists (idempotent)
    # --------------------------------------------------------
    if ($formXml -match [regex]::Escape($FunctionName)) {
        Write-Host "  Handler already present - skipping" -ForegroundColor Green
        continue
    }

    # --------------------------------------------------------
    # 3. Parse as XML
    # --------------------------------------------------------
    $xml = [xml]$formXml

    # --------------------------------------------------------
    # 4. Ensure library reference exists in <formLibraries>
    # --------------------------------------------------------
    $libNode = $xml.SelectSingleNode("//formLibraries")
    if (-not $libNode) {
        # Create <formLibraries> element; insert before </form> close
        $libNode = $xml.CreateElement("formLibraries")
        $xml.DocumentElement.AppendChild($libNode) | Out-Null
        Write-Host "  Created <formLibraries> element"
    }

    # Check if library already declared
    $existingLib = $xml.SelectSingleNode("//formLibraries/Library[@name='$LibraryName']")
    if (-not $existingLib) {
        $libElem = $xml.CreateElement("Library")
        $libElem.SetAttribute("name", $LibraryName)
        $libElem.SetAttribute("libraryUniqueId", "{$([guid]::NewGuid())}")
        $libNode.AppendChild($libElem) | Out-Null
        Write-Host "  Added library reference: $LibraryName"
    } else {
        Write-Host "  Library reference already exists"
    }

    # --------------------------------------------------------
    # 5. Find or create the form-level onload event
    # --------------------------------------------------------
    # The form-level <events> block is a direct child of the root <form> element
    # (not nested inside a cell or header). We need to find the correct one.
    # Strategy: look for <events> that contain <event name="onload">
    #           or the top-level <events> after </header>

    $formEvents = $null

    # First, try to find existing form-level events with onload
    $allEvents = $xml.SelectNodes("//events")
    foreach ($evtBlock in $allEvents) {
        $onloadEvt = $evtBlock.SelectSingleNode("event[@name='onload']")
        if ($onloadEvt) {
            $formEvents = $evtBlock
            break
        }
    }

    if (-not $formEvents) {
        # No onload event block found - find form-level events (direct child of root)
        # or create one
        $formEvents = $xml.DocumentElement.SelectSingleNode("events")
        if (-not $formEvents) {
            $formEvents = $xml.CreateElement("events")
            $xml.DocumentElement.AppendChild($formEvents) | Out-Null
            Write-Host "  Created form-level <events> element"
        }
    }

    # Find or create the onload event
    $onloadEvent = $formEvents.SelectSingleNode("event[@name='onload']")
    if (-not $onloadEvent) {
        $onloadEvent = $xml.CreateElement("event")
        $onloadEvent.SetAttribute("name", "onload")
        $onloadEvent.SetAttribute("application", "true")
        $onloadEvent.SetAttribute("active", "true")
        $formEvents.AppendChild($onloadEvent) | Out-Null
        Write-Host "  Created onload event"
    }

    # Find or create the <Handlers> section (not <InternalHandlers>)
    $handlersNode = $onloadEvent.SelectSingleNode("Handlers")
    if (-not $handlersNode) {
        $handlersNode = $xml.CreateElement("Handlers")
        $onloadEvent.AppendChild($handlersNode) | Out-Null
        Write-Host "  Created <Handlers> section"
    }

    # --------------------------------------------------------
    # 6. Inject our handler
    # --------------------------------------------------------
    $handlerElem = $xml.CreateElement("Handler")
    $handlerElem.SetAttribute("functionName", $FunctionName)
    $handlerElem.SetAttribute("libraryName", $LibraryName)
    $handlerElem.SetAttribute("handlerUniqueId", "{$([guid]::NewGuid())}")
    $handlerElem.SetAttribute("enabled", "true")
    $handlerElem.SetAttribute("parameters", "")
    $handlerElem.SetAttribute("passExecutionContext", "true")
    $handlersNode.AppendChild($handlerElem) | Out-Null
    Write-Host "  Injected handler: $FunctionName" -ForegroundColor Yellow

    # --------------------------------------------------------
    # 7. Serialize and PATCH back
    # --------------------------------------------------------
    $sw = New-Object System.IO.StringWriter
    $xw = New-Object System.Xml.XmlTextWriter($sw)
    $xw.Formatting = [System.Xml.Formatting]::None
    $xml.WriteTo($xw)
    $xw.Flush()
    $updatedXml = $sw.ToString()

    # Remove XML declaration if present (Dataverse expects raw formxml)
    $updatedXml = $updatedXml -replace '<\?xml[^?]*\?>', ''

    $patchBody = @{ formxml = $updatedXml } | ConvertTo-Json -Depth 5
    $patchUrl = "$(Get-DataverseApiUrl)/systemforms($formId)"
    try {
        Invoke-RestMethod -Uri $patchUrl -Method Patch -Headers $headers -Body $patchBody -ErrorAction Stop
        Write-Host "  PATCHED formxml successfully" -ForegroundColor Green
        $modifiedCount++
    } catch {
        Write-Warning "  PATCH failed for '$formName': $($_.Exception.Message)"
        if ($_.ErrorDetails.Message) {
            Write-Warning "  Detail: $($_.ErrorDetails.Message)"
        }
    }
}

# ============================================================
# 8. Publish entity customizations
# ============================================================
if ($modifiedCount -gt 0) {
    Write-Host "`n--- Publishing customizations ---" -ForegroundColor Cyan

    $entityXmlParts = $entitiesToPublish | ForEach-Object { "<Entity>$_</Entity>" }
    $publishXml = "<importexportxml><entities>$($entityXmlParts -join '')</entities></importexportxml>"

    $publishBody = @{ ParameterXml = $publishXml } | ConvertTo-Json -Depth 5
    $publishUrl = "$(Get-DataverseApiUrl)/PublishXml"
    $headers = Get-DataverseHeaders

    try {
        Invoke-RestMethod -Uri $publishUrl -Method Post -Headers $headers -Body $publishBody -ErrorAction Stop
        Write-Host "  Published: $($entitiesToPublish -join ', ')" -ForegroundColor Green
    } catch {
        Write-Warning "  PublishXml failed: $($_.Exception.Message)"
        if ($_.ErrorDetails.Message) {
            Write-Warning "  Detail: $($_.ErrorDetails.Message)"
        }
    }
} else {
    Write-Host "`nNo forms modified - nothing to publish." -ForegroundColor Yellow
}

Write-Host "`n=== Step 25 Complete: $modifiedCount form(s) updated ===" -ForegroundColor Green
