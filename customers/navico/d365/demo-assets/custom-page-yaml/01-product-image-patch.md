# Product Image on Equipment Screen — Setup Guide

## How it works

The Equipment & Warranty screen (`scrEquipWarranty`) has an `imgUnitPhoto` control
with this formula:

```powerfx
If(
    !IsBlank(varEWSelectedUnit.Product)
    && !IsBlank(varEWSelectedUnit.Product.'Entity Image'),
    varEWSelectedUnit.Product.'Entity Image',
    // fallback to brand logo
    varEWSelectedUnit.bw_brandlogourl
)
```

When a customer asset has a **Product** lookup set AND that Product record has an
**Entity Image** uploaded, the image automatically displays. Otherwise it falls back
to the brand logo URL.

---

## Step 1 — Save product images

Save product photos to:
```
customers/navico/d365/demo-assets/product-images/
```

**Naming convention:** Use the product number as the filename:
| File                    | Product                              |
|-------------------------|--------------------------------------|
| `SIM-NSX-3007.jpg`     | Simrad NSX 3007 Chartplotter         |
| `SIM-NSX-3009.jpg`     | Simrad NSX 3009 Chartplotter         |
| `SIM-GO9.jpg`          | Simrad GO9 XSE                       |
| `SIM-HALO-20.jpg`      | Simrad Halo 20 Pulse Radar           |
| `SIM-AP44.jpg`         | Simrad AP44 Autopilot Controller     |
| `SIM-RS90S.jpg`        | Simrad RS90S VHF Radio               |
| `LWR-HDS9-LIVE.jpg`    | Lowrance HDS-9 Live                  |
| `LWR-HDS-LIVE9.jpg`    | Lowrance HDS Live 9                  |
| `LWR-HDS-LIVE12.jpg`   | Lowrance HDS Live 12                 |
| `LWR-ELT-FS9.jpg`      | Lowrance Elite FS 9                  |
| `LWR-ELITE-FS7.jpg`    | Lowrance Elite FS 7                  |
| `LWR-HOOK-REV7.jpg`    | Lowrance Hook Reveal 7               |
| `LWR-ACTGT-2.jpg`      | Lowrance ActiveTarget 2 Live Sonar   |
| `CMAP-GENESIS-1Y.jpg`  | C-MAP Genesis Chart Subscription     |

**Image tips:**
- Product-on-white-background photos work best
- JPG or PNG, ideally 400×400 px or larger
- Dataverse Entity Image auto-thumbnails to 144×144 for the table list view

**Where to get images:**
- Right-click → Save Image from simrad-yachting.com, lowrance.com, bandg.com product pages
- Google Images search: `"Simrad NSX 3007" product photo white background`

---

## Step 2 — Upload to Dataverse

Run the upload script:
```powershell
.\Upload-ProductImages.ps1         # Upload all images
.\Upload-ProductImages.ps1 -DryRun # Preview without uploading
```

The script matches filenames to product numbers and uploads the image to the
Product record's `entityimage` column via Dataverse API PATCH.

---

## Step 3 — Update Canvas App formula (one-time)

In Power Apps Studio, update `imgUnitPhoto.Image` on `scrEquipWarranty` to use
the brand logo as fallback instead of the Otis logo:

```powerfx
If(
    !IsBlank(varEWSelectedUnit.Product)
    && !IsBlank(varEWSelectedUnit.Product.'Entity Image'),
    varEWSelectedUnit.Product.'Entity Image',
    If(
        !IsBlank(varEWSelectedUnit.bw_brandlogourl),
        varEWSelectedUnit.bw_brandlogourl,
        "navico-logo"
    )
)
```

This gives a 3-tier fallback:
1. **Product photo** (if Entity Image uploaded) — shows the actual unit
2. **Brand logo** (if bw_brandlogourl set) — shows Simrad/Lowrance/B&G logo
3. **Navico logo** (final fallback) — generic Navico Group logo

---

## Verification

After uploading images, open case `CAS-19621-V9B9H0` → Service Toolkit → Equipment.
Select serial `SIM-2024-NSX-10042`. The detail panel should show the Simrad NSX 3007
product photo instead of the brand logo.
