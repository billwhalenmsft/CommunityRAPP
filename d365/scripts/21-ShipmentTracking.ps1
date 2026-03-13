<#
.SYNOPSIS
    Step 21 - Add Tracking Number columns and seed data for Shipment Tracker
.DESCRIPTION
    Creates bw_TrackingNumber and bw_CarrierCode custom columns on the
    Sales Order entity. Seeds realistic tracking numbers on the 4 demo
    orders from Step 20. Exports tracking data to data/order-tracking.json.
.NOTES
    Run AFTER 20-OrderMgmt.ps1 (orders must exist).
    Publisher prefix: bw (Bill Whalen - Solution Engineering)
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Write-StepHeader "21" "Shipment Tracking - Custom Columns & Seed Data"
Connect-Dataverse

$api = Get-DataverseApiUrl
$h   = Get-DataverseHeaders

# ============================================================
# Helper: Create a string attribute on an entity (idempotent)
# ============================================================
function Add-StringAttribute {
    param(
        [string]$EntityLogicalName,
        [string]$SchemaName,
        [string]$DisplayName,
        [string]$Description,
        [int]$MaxLength = 100
    )

    $logicalName = $SchemaName.ToLower()

    # Check if attribute already exists
    $exists = $false
    try {
        Invoke-RestMethod -Method GET `
            -Uri "$api/EntityDefinitions(LogicalName='$EntityLogicalName')/Attributes(LogicalName='$logicalName')?`$select=LogicalName" `
            -Headers $h -ErrorAction Stop | Out-Null
        $exists = $true
    } catch { }

    if ($exists) {
        Write-Host "  Column '$logicalName' already exists" -ForegroundColor DarkGray
        return
    }

    $body = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        SchemaName    = $SchemaName
        DisplayName   = @{
            "@odata.type"   = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label         = $DisplayName
                    LanguageCode  = 1033
                }
            )
        }
        Description   = @{
            "@odata.type"   = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label         = $Description
                    LanguageCode  = 1033
                }
            )
        }
        RequiredLevel = @{
            Value        = "None"
            CanBeChanged = $true
        }
        MaxLength     = $MaxLength
        FormatName    = @{ Value = "Text" }
    } | ConvertTo-Json -Depth 5

    $uri = "$api/EntityDefinitions(LogicalName='$EntityLogicalName')/Attributes"

    try {
        Invoke-RestMethod -Method POST -Uri $uri -Headers $h `
            -Body $body -ContentType "application/json" -ErrorAction Stop
        Write-Host "  Created column: $SchemaName ($DisplayName)" -ForegroundColor Green
    } catch {
        $errText = $_.ErrorDetails.Message
        if ($errText -match "already exists") {
            Write-Host "  Column '$SchemaName' already exists (caught on create)" -ForegroundColor DarkGray
        } else {
            Write-Host "  ERROR creating $SchemaName : $errText" -ForegroundColor Red
            throw
        }
    }
}

# ============================================================
# 1. Create custom columns on salesorder entity
# ============================================================
Write-Host "`n--- Creating custom columns on Sales Order ---" -ForegroundColor Yellow

Add-StringAttribute -EntityLogicalName "salesorder" `
    -SchemaName "bw_TrackingNumber" `
    -DisplayName "Tracking Number" `
    -Description "Carrier tracking number for shipment tracking" `
    -MaxLength 100

Add-StringAttribute -EntityLogicalName "salesorder" `
    -SchemaName "bw_CarrierCode" `
    -DisplayName "Carrier Code" `
    -Description "ShipEngine carrier code (e.g., fedex, ups, usps, dhl_express)" `
    -MaxLength 20

# ============================================================
# 2. Publish entity customization
# ============================================================
Write-Host "`n--- Publishing salesorder customizations ---" -ForegroundColor Yellow

$publishBody = @{
    ParameterXml = "<importexportxml><entities><entity>salesorder</entity></entities></importexportxml>"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "$api/PublishXml" `
    -Headers $h -Body $publishBody -ContentType "application/json"
Write-Host "  Published salesorder entity" -ForegroundColor Green

# Brief pause for publish propagation
Start-Sleep -Seconds 5

# ============================================================
# 3. Seed tracking numbers on demo orders
# ============================================================
Write-Host "`n--- Seeding tracking numbers on demo orders ---" -ForegroundColor Yellow

$trackingData = @(
    @{
        OrderNumber    = "PO-94820"
        TrackingNumber = "794644790132456"
        CarrierCode    = "fedex"
        Note           = "Ferguson Houston DC - FedEx Ground (In Transit)"
    },
    @{
        OrderNumber    = "PO-93201"
        TrackingNumber = "1Z999AA10312345678"
        CarrierCode    = "ups"
        Note           = "Ferguson Atlanta DC - UPS Ground (Delivered)"
    },
    @{
        OrderNumber    = "PO-95102"
        TrackingNumber = "611489176518964"
        CarrierCode    = "fedex"
        Note           = "Ferguson Jacksonville DC - FedEx Ground (Label Created)"
    },
    @{
        OrderNumber    = "PO-HD-7845"
        TrackingNumber = "1Z999AA16812345674"
        CarrierCode    = "ups"
        Note           = "HD Supply Atlanta DC - UPS Ground (In Transit)"
    }
)

$trackingExport = @{}

foreach ($t in $trackingData) {
    $order = Invoke-DataverseGet -EntitySet "salesorders" `
        -Filter "ordernumber eq '$($t.OrderNumber)'" `
        -Select "salesorderid,ordernumber" -Top 1

    if ($order -and $order.Count -gt 0) {
        $orderId = $order[0].salesorderid
        $patchBody = @{
            bw_trackingnumber = $t.TrackingNumber
            bw_carriercode    = $t.CarrierCode
        }
        Invoke-DataversePatch -EntitySet "salesorders" -RecordId $orderId -Body $patchBody
        Write-Host "  $($t.OrderNumber): $($t.CarrierCode) / $($t.TrackingNumber)" -ForegroundColor Green
        Write-Host "    ($($t.Note))" -ForegroundColor DarkGray

        $trackingExport[$t.OrderNumber] = @{
            id             = $orderId
            trackingNumber = $t.TrackingNumber
            carrierCode    = $t.CarrierCode
        }
    } else {
        Write-Host "  $($t.OrderNumber): NOT FOUND - run 20-OrderMgmt.ps1 first" -ForegroundColor Red
    }
}

# ============================================================
# 4. Export tracking data
# ============================================================
$trackingExport | ConvertTo-Json -Depth 3 | Out-File "$scriptDir\..\data\order-tracking.json" -Encoding utf8
Write-Host "`nTracking data saved to data\order-tracking.json" -ForegroundColor DarkGray

# ============================================================
# Summary
# ============================================================
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " Shipment Tracking Setup Complete" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Custom columns: bw_trackingnumber, bw_carriercode" -ForegroundColor Cyan
Write-Host "  Orders updated: $($trackingExport.Count) of $($trackingData.Count)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Import ShipEngine custom connector (shipengine-connector.swagger.json)" -ForegroundColor White
Write-Host "  2. Create a connection using your ShipEngine API key" -ForegroundColor White
Write-Host "  3. Add 'ShipEngine' connector as data source in the Custom Page" -ForegroundColor White
Write-Host "  4. Refresh 'Sales Orders' data source to pick up new columns" -ForegroundColor White
Write-Host "  5. Paste 05-scrShipmentTracker.pa.yaml screen" -ForegroundColor White
