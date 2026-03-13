# Order Modification Wizard — Setup Instructions

> **Format**: Power Apps pa.yaml **SchemaV3** (the only active schema).
> Reference: https://go.microsoft.com/fwlink/?linkid=2299600

---

## Quick Start — Which Approach?

| If you have… | Do this |
|---|---|
| **Git integration** (Power Platform → Git repo) | Drop each `.pa.yaml` file into `Src/` and sync |
| **Code View** (right-click control → View code) | Create each screen, then **paste controls** one at a time from the `Children:` array |
| **Neither** | Use the YAML as a manual build recipe (see "Manual Build" below) |

---

## App-Level Configuration

| Setting | Value |
|---------|-------|
| **App Name** | Order Modification Wizard |
| **Width** | 380 |
| **Height** | 800 |
| **Where** | Settings → Display |

### App.OnStart Formula

Paste into **App** → **OnStart** property:
```
Set(varSelectedOrder, Blank());
Set(varAgentNotes, "");
Set(varTimelineAdded, false);
ClearCollect(colCancelledLines, Blank());
ClearCollect(colDateChanges, Blank());
```

### Data Sources to Add

Click **Data** (cylinder icon in left rail) → **+ Add data** → **Dataverse** → add each:

| # | Display Name | Logical Name |
|---|-------------|--------------|
| 1 | Sales Orders | `salesorder` |
| 2 | Sales Order Products | `salesorderdetail` |
| 3 | Accounts | `account` |
| 4 | Notes | `annotation` |
| 5 | Cases | `incident` |
| 6 | Products | `product` |
| 7 | Price List Items | `productpricelevel` |

**For Quick Quote — Save feature** (optional, adds D365 Quote creation):

| # | Display Name | Logical Name |
|---|-------------|--------------|
| 8 | Quotes | `quote` |
| 9 | Quote Products | `quotedetail` |
| 10 | Price Lists | `pricelevel` |
**For Return / RMA** (requires "Credit Memo and RMA" table in the org — publisher `cra1f`):

| # | Display Name | Logical Name |
|---|-------------|--|
| 11 | Credit Memo and RMAs | `cra1f_creditmemoandrma` |

**For Warranty Lookup** (requires "Warranty and Claim Operations" solution installed):

| # | Display Name | Logical Name |
|---|-------------|--|
| 12 | Product Serials | `cr74e_productserial` |
| 13 | Warranty Claims | `cr74e_warrantyclaim` |

> **Note:** The "Warranty and Claim Operations" solution (publisher prefix `cr74e`) must be present
> in the environment before adding these data sources.
**Custom Connector** (for Shipment Tracker):

| # | Connector | Source |
|---|-----------|--------|
| 6 | ShipEngine | Custom connector — see "ShipEngine Setup" below |

### Screens to Create (in order)

1. `scrHome` — rename the default Screen1
2. `scrOrderLookup` — Insert → New screen → Blank
3. `scrOrderLineManagement` — Insert → New screen → Blank
4. `scrReview` — Insert → New screen → Blank
5. `scrConfirmation` — Insert → New screen → Blank
6. `scrShipmentTracker` — Insert → New screen → Blank
7. `scrQuickQuote` — Insert → New screen → Blank
8. `scrQuoteReview` — Insert → New screen → Blank
9. `scrReturnRMA` — Insert → New screen → Blank
10. `scrWarrantyLookup` — Insert → New screen → Blank

---

## SchemaV3 Format Reference

The old `As` syntax (`lblFoo As label:`) is **retired**. The current format uses:

```yaml
Screens:
  scrName:
    Properties:
      Fill: =RGBA(250, 250, 250, 1)
    Children:
      - controlName:
          Control: ControlType
          Properties:
            Text: ="Hello"
            X: =0
            Y: =0
```

### Control Type Mapping

| What you want | `Control:` value | Notes |
|---|---|---|
| Label | `Label` | |
| Button | `Classic/Button` | |
| Rectangle | `Rectangle` | |
| Icon | `Classic/Icon` | Set `Icon:` property to e.g. `=Icon.Search` |
| Gallery (vertical blank) | `Gallery` | No Variant needed — custom Children define the template |
| Text input | `Classic/TextInput` | |
| Date picker | `Classic/DatePicker` | |
| Checkbox | `Classic/CheckBox` | |
| HTML text | `HtmlViewer` | |

### Key Syntax Rules

1. **All property values start with `=`** — even simple numbers: `X: =16`
2. **Formulas with `#` or `:` MUST use multiline** (`|-`) notation:
   ```yaml
   Text: |-
     ="$" & Text(value, "#,##0.00")
   ```
   Single-line `Text: ="$" & Text(value, "#,##0.00")` will fail because YAML treats `#` as a comment.
3. **Children are arrays** — each child starts with `- controlName:`
4. **Gallery template controls** go under the gallery's `Children:` array
5. **YAML comments** (`#`) are stripped by Power Apps — use `//` inside formulas

### Verifying Control Types

If a control type name fails, insert one manually in the designer, then:
1. Right-click the control → **View code**
2. Note the exact `Control:` value Power Apps generated
3. Use that value in your YAML

---

## Pasting via Code View

Code View paste works for **individual controls** into an existing screen.

1. Create the screen manually → rename it
2. Set screen-level properties (Fill, OnVisible) in the properties panel
3. Right-click the screen in the tree view → **Paste code**
4. Paste ONE control block at a time from the `Children:` array

**Example — pasting a single control:**
```yaml
rectTopBar:
  Control: Rectangle
  Properties:
    X: =0
    Y: =0
    Width: =Parent.Width
    Height: =6
    Fill: =RGBA(0, 120, 212, 1)
```

For a gallery WITH template controls, paste the whole gallery block (it includes its Children):
```yaml
galOrders:
  Control: Gallery
  Properties:
    Items: |-
      =Filter('Sales Orders', 'Status Reason' = 'Status Reason (Sales Orders)'.Active)
    X: =0
    Y: =110
    Width: =Parent.Width
    Height: =Parent.Height - 110
    TemplateSize: =90
  Children:
    - lblOrderId:
        Control: Label
        Properties:
          Text: =ThisItem.'Order ID'
          X: =24
          Y: =12
```

---

## Manual Build (YAML as Recipe)

If Code View isn't available, use each `.pa.yaml` file as a control-by-control guide:

| YAML Pattern | Designer Action |
|---|---|
| `- lblFoo:` / `Control: Label` | Insert → Label → rename to `lblFoo` |
| `- btnBar:` / `Control: Classic/Button` | Insert → Button → rename to `btnBar` |
| `- galX:` / `Control: Gallery` | Insert → Vertical gallery (blank) → rename |
| `- chkY:` / `Control: Classic/CheckBox` | Insert → Input → Checkbox → rename |
| `- dpZ:` / `Control: Classic/DatePicker` | Insert → Input → Date picker → rename |
| `- txtA:` / `Control: Classic/TextInput` | Insert → Input → Text input → rename |
| `- htmlB:` / `Control: HtmlViewer` | Insert → HTML text → rename |
| `- rectC:` / `Control: Rectangle` | Insert → Rectangle → rename |
| `- icoD:` / `Control: Classic/Icon` | Insert → Icon → choose type → rename |
| `Properties: > X: =16` | Select control → set **X** to `16` in formula bar |
| `Properties: > Items: =Filter(...)` | Select gallery → set **Items** in formula bar |
| `Properties: > OnSelect: =Navigate(...)` | Select control → set **OnSelect** in formula bar |
| `Children:` under a gallery | Click INTO the gallery template area, then insert controls |

---

## Variable Reference

| Variable | Type | Set By | Used By |
|----------|------|--------|---------|
| `varSelectedOrder` | Record (Sales Order) | Screen 1 gallery OnSelect | Screens 2, 3, 4, 5 |
| `colCancelledLines` | Collection (Sales Order Products) | Screen 2 checkboxes | Screens 2, 3, 4 |
| `colDateChanges` | Collection (custom table) | Screen 2 date pickers | Screen 3 |
| `varAgentNotes` | Text | Screen 3 Submit button | Screen 4 |
| `varTimelineAdded` | Boolean | Screen 4 Timeline button | Screen 4 |
| `varTrackingResult` | Record (ShipEngine response) | Screen 5 Track button | Screen 5 |
| `varTrackingError` | Text | Screen 5 Track button | Screen 5 |
| `varTrackingLoading` | Boolean | Screen 5 Track button | Screen 5 |
| `colTrackingEvents` | Collection (tracking events) | Screen 5 Track button | Screen 5 gallery |
| `varQuoteAccount` | Record (Account) | Screen 6 Review button | Screens 6, 7 |
| `varQuoteBrand` | Text | Screen 6 Review button | Screens 6, 7 |
| `varQuoteSaved` | Boolean | Screen 7 Save button | Screen 7 |
| `varQuoteError` | Text | Screen 7 Save button | Screen 7 |
| `varQuoteNumber` | Text | Screen 7 Save button | Screen 7 |
| `varSavedQuote` | Record (Quote) | Screen 7 Save button | Screen 7 |
| `varTempPrice` | Number | Screen 6 product picker | Screen 6 |
| `colQuoteLines` | Collection (quote lines) | Screen 6 Add Line button | Screens 6, 7 |

---

## After Building All 8 Screens

1. **Save** (Ctrl+S)
2. **Publish** the Custom Page
3. Register in the productivity pane (see `custom-page-build-guide.md` Step 5)
4. Test with the Ferguson PO #94820 case

---

## Files in This Folder

| File | Screen | Controls |
|---|---|---|
| `00-scrHome.pa.yaml` | Home / Launcher | 5 tool tiles + initialization |
| `01-scrOrderLookup.pa.yaml` | Order Lookup | 6 screen + 5 gallery template |
| `02-scrLineManagement.pa.yaml` | Line Management (scrOrderLineManagement) | 13 screen + 7 gallery template |
| `03-scrReview.pa.yaml` | Review & Confirm | 13 controls |
| `04-scrConfirmation.pa.yaml` | Confirmation | 14 controls |
| `05-scrShipmentTracker.pa.yaml` | Shipment Tracker | 18 screen + 4 gallery template |
| `06-scrQuickQuote.pa.yaml` | Quick Quote (Product Picker) | 22 screen + 4 gallery template |
| `07-scrQuoteReview.pa.yaml` | Quote Review & Save | 18 screen + 3 gallery template |
| `08-scrReturnRMA.pa.yaml` | Return / RMA | 11 controls |
| `09-scrWarrantyLookup.pa.yaml` | Warranty Lookup | 20 controls |
| `shipengine-connector.swagger.json` | — | Custom connector definition |

---

## ShipEngine Custom Connector Setup

### 1. Get a ShipEngine API Key

1. Sign up at [app.shipengine.com](https://app.shipengine.com/)
2. Navigate to **API Keys** → copy your API key

### 2. Import the Custom Connector

1. Go to [make.powerapps.com](https://make.powerapps.com/) → **Custom connectors**
2. Click **+ New custom connector** → **Import an OpenAPI file**
3. Name: `ShipEngine`
4. Upload `shipengine-connector.swagger.json` from this folder
5. On the **Security** tab, verify **API Key** auth with header name `API-Key`
6. Click **Create connector**

### 3. Create a Connection

1. Go to **Connections** → **+ New connection**
2. Select **ShipEngine** → paste your API key → **Create**

### 4. Add to Custom Page

1. In the Custom Page editor, click **Data** → **+ Add data**
2. Search for **ShipEngine** → select it
3. The connector appears as a data source for `ShipEngine.GetTrackingInfo()`

### 5. Refresh Sales Orders Data Source

After running `scripts/21-ShipmentTracking.ps1`, refresh the **Sales Orders** data source
in the Custom Page editor so the new columns (`Tracking Number`, `Carrier Code`) appear.

---

## Backlog

Items planned for future implementation:

### 1. Quick Quote — Save to D365 via Power Automate

Screen 07 (`scrQuoteReview`) currently cannot `Patch()` directly to the `Quotes` / `Quote Products` tables
due to required fields injected by the **Project Operations** solution (e.g., `msdyn_ordertype`).
The workaround is to build a **Power Automate cloud flow** that the Custom Page calls, which creates
the Quote and Quote Products server-side with all required fields pre-populated.

**Steps:**
- Create a cloud flow triggered by an HTTP request (from Power Apps)
- Accept inputs: Account ID, Brand, line items (product, qty, unit price)
- Flow creates the Quote header with `msdyn_ordertype` set, then creates Quote Products
- Return the Quote Number to the Custom Page
- Update `btnSaveQuote.OnSelect` on Screen 07 to call the flow instead of direct `Patch()`

### 2. Portal — Warranty, Claims & RMA Display

Add customer-facing views in the Power Pages portal to surface warranty and service data:

- **Warranty Information**: Allow customers/distributors to look up product warranty status
  by serial number (reads from `cr74e_productserial`). Show product name, warranty start/end,
  and active/expired status.
- **Claims History**: Display a list of warranty claims filed by the logged-in customer
  (reads from `cr74e_warrantyclaim`). Show claim number, date, status, description, and
  settlement amount where applicable.
- **RMA Status**: Let customers check the status of return/credit memo requests
  (reads from `cra1f_creditmemoandrma`). Show RMA number, product, quantity, reason,
  and current processing status.
- **File New Claim**: Portal form to submit a new warranty claim (creates record in
  `cr74e_warrantyclaim`) with serial number lookup, description, and contact info.
