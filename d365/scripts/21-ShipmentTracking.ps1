<#
.SYNOPSIS
    Step 21 - Add Tracking Number columns and seed data for Shipment Tracker
.DESCRIPTION
    Creates bw_TrackingNumber and bw_CarrierCode custom columns on the
    Sales Order entity. Seeds realistic tracking numbers on demo orders.

    Customer-driven path: reads salesOrders[].tracking from
    customers/{Customer}/d365/config/demo-data.json

    Legacy fallback: if no -Customer specified or no salesOrders section,
    seeds Zurn/Ferguson hardcoded order data.

.PARAMETER Customer
    Customer folder name (e.g. "navico", "zurnelkay"). Defaults to "zurnelkay".

.NOTES
    Run AFTER 20-OrderMgmt.ps1 (orders must exist).
    Publisher prefix: bw (Bill Whalen - Solution Engineering)
#>
param(
    [string]$Customer = "zurnelkay"
)

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
# 3. Build tracking data — customer-driven or legacy fallback
# ============================================================
$trackingData = $null

$demoDataPath = Join-Path $scriptDir "..\..\customers\$Customer\d365\config\demo-data.json"
if (Test-Path $demoDataPath) {
    $demoJson = Get-Content $demoDataPath -Raw | ConvertFrom-Json
    if ($demoJson.salesOrders -and $demoJson.salesOrders.orders) {
        $trackingData = $demoJson.salesOrders.orders | Where-Object { $_.tracking } | ForEach-Object {
            @{
                OrderNumber    = $_.orderNumber
                TrackingNumber = $_.tracking.trackingNumber
                CarrierCode    = if ($_.tracking.carrierCode) { $_.tracking.carrierCode } else { "fedex" }
                Note           = "$($_.account) — $($_.tracking.carrier) ($($_.tracking.status))"
            }
        }
        Write-Host "  Loaded $($trackingData.Count) orders from $Customer demo-data.json" -ForegroundColor Cyan
    }
}

if (-not $trackingData) {
    Write-Host "  No customer tracking data found — using Zurn/Ferguson legacy data" -ForegroundColor DarkYellow
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
}

# ============================================================
# 4. Seed tracking numbers on demo orders
# ============================================================
Write-Host "`n--- Seeding tracking numbers on demo orders ---" -ForegroundColor Yellow

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
        Write-Host "  $($t.OrderNumber): NOT FOUND - run 20-OrderMgmt.ps1 -Customer $Customer first" -ForegroundColor Red
    }
}

# ============================================================
# 5. Export tracking data
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
