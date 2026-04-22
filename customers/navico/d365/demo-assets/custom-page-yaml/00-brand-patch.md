# Dynamic Brand Logo — Canvas App YAML Patch
# Service Toolkit Custom Page (`bw_ordermodificationwizard_9400f`)
# Apply in Power Apps Studio by pasting YAML snippets into the screen tree

## Overview

The brand is detected from the serial number passed from the host form
(`varPassedSerial`). Serial number prefixes map to Navico brands:

| Prefix   | Brand      | Accent Color |
|----------|------------|-------------|
| LWR-     | Lowrance   | #CC2200     |
| SIM-     | Simrad     | #003B72     |
| BNG-     | B&G        | #C8102E     |
| CMAP-    | C-MAP      | #006B8F     |
| NST-     | Northstar  | #1B3A6B     |
| (other)  | Navico     | #0B2D4E     |

---

## Step 1 — Add brand detection to `scrHome` OnVisible

Add the following to the **end** of the `scrHome` OnVisible formula (after the
existing `Set(varWarrantyMode, ...)` line):

```powerfx
// --- Navico brand detection from serial prefix ---
Set(
    varBrand,
    Switch(
        true,
        StartsWith(varPassedSerial, "LWR-"),  "Lowrance",
        StartsWith(varPassedSerial, "SIM-"),  "Simrad",
        StartsWith(varPassedSerial, "BNG-"),  "B&G",
        StartsWith(varPassedSerial, "CMAP-"), "C-MAP",
        StartsWith(varPassedSerial, "NST-"),  "Northstar",
        "Navico"
    )
);
Set(
    varBrandColor,
    Switch(
        varBrand,
        "Lowrance",  RGBA(204, 34,   0,  1),
        "Simrad",    RGBA(  0, 59, 114,  1),
        "B&G",       RGBA(200, 16,  46,  1),
        "C-MAP",     RGBA(  0,107, 143,  1),
        "Northstar", RGBA( 27, 58, 107,  1),
        /* default Navico navy */
                     RGBA( 11, 45,  78,  1)
    )
);
Set(varQuoteBrand, varBrand)
```

---

## Step 2 — Update `rectHomeBar` Fill

Change the `Fill` property of the **orange accent bar** at the top:

```powerfix
Fill: =varBrandColor
```

---

## Step 3 — Add `imgBrandLogo` Image control

In the screen tree, add a new **Image** control named `imgBrandLogo`.
Paste this YAML into the screen in Power Apps Studio (Insert → paste YAML):

```yaml
      # -- Brand Logo --
      - imgBrandLogo:
          Control: Image
          Properties:
            X: =16
            Y: =70
            Width: =160
            Height: =32
            Image: =Switch(
                varBrand,
                "Lowrance",  "/WebResources/cr74e_logo_lowrance",
                "Simrad",    "/WebResources/cr74e_logo_simrad",
                "B&G",       "/WebResources/cr74e_logo_bng",
                "C-MAP",     "/WebResources/cr74e_logo_cmap",
                "Northstar", "/WebResources/cr74e_logo_northstar",
                             "/WebResources/cr74e_logo_navico"
            )
            ImagePosition: =ImagePosition.Fit
            BorderThickness: =0
            Visible: =!IsBlank(varBrand)
```

---

## Step 4 — Shift down existing controls

After adding `imgBrandLogo` at Y=70, shift these controls down by **40px**:

| Control           | Old Y | New Y |
|-------------------|-------|-------|
| lblHomeSubtitle   | 50    | 92    |
| lblVersion        | Parent.Height - 28 | (unchanged) |

Update `lblHomeSubtitle`:
```powerfix
Y: =92
```

---

## Step 5 — Make subtitle brand-aware

Update `lblHomeSubtitle` Text:

```powerfix
Text: =varBrand & " — CSR Productivity Tools"
```

---

## Step 6 — Update `varBrand` declarations (App.OnStart or Screen vars)

If you use **App-level variables**, add to App.OnStart:
```powerfix
Set(varBrand, "Navico");
Set(varBrandColor, RGBA(11, 45, 78, 1));
```

If declared at screen level (OnVisible), the Step 1 addition handles initialization.

---

## Where brand detection also helps

- **`scrQuickQuote`**: `varQuoteBrand` is already being set — it will now auto-populate from brand detection rather than being hardcoded to "Zurn"
- **`lblVersion`**: Optionally update to: `="v1.0 | " & varBrand & " Service Toolkit"`
- **`rectHomeBar`** on all screens: Same `varBrandColor` formula applies wherever accent bars exist

---

## Testing

1. Open a Navico Case with serial `SIM-NSX-001234` → should show Simrad logo (blue)
2. Open a Case with serial `BNG-H5000-005678` → should show B&G logo (red)
3. Open a Case with no serial → should show Navico logo (navy)
