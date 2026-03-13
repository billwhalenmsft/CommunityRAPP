# Order Management Custom Page -- Build Guide

## Overview
A 4-screen Power Apps **Custom Page** embedded in the D365 Customer Service **productivity pane** (side panel). The agent clicks a tool in the pane while on a case, and a guided wizard walks them through order modifications -- the D365 equivalent of Salesforce's Lightning Flow for Service.

### What It Replaces
| Salesforce | D365 Equivalent (This Build) |
|---|---|
| Screen Flow in Utility Bar | Custom Page in Productivity Pane |
| Lightning Flow for Service | Canvas app + Dataverse connector |
| Process Builder automation | Power Automate cloud flow |

### Demo Scenario
During the **phone call** with Mike Reynolds (Ferguson), the agent uses this Custom Page to:
1. Pull up PO #94820
2. Cancel lines 4 & 5 (drinking fountains + stainless sinks)
3. Expedite lines 1-3 from March 15 → March 10
4. Confirm changes and generate a summary

---

## Reference Data

| Item | Value |
|------|-------|
| PO #94820 order ID | `e624146a-a718-f111-8342-7c1e520a58a1` |
| Ferguson account ID | `ee8604af-8912-f111-8342-000d3a316172` |
| Elkay Price List | `6cfa0c6e-8d12-f111-8407-7c1e520a58a1` |
| Line 1 - Bottle Fillers (EK-BF-5001) | 120 × $1,150 = $138,000 |
| Line 2 - Wall Coolers (EK-WC-5002) | 60 × $780 = $46,800 |
| Line 3 - Filters (EK-FL-6003) | 200 × $29.50 = $5,900 |
| Line 4 - Drinking Fountains (EK-DF-5003) | 25 × $1,450 = $36,250 ← CANCEL |
| Line 5 - Stainless Sinks (EK-SS-6001) | 40 × $780 = $31,200 ← CANCEL |
| Original delivery | 2026-03-15 |
| Requested delivery | 2026-03-10 |

---

## Step 1: Create the Custom Page

### 1.1 Open Power Apps Maker Portal
1. Go to https://make.powerapps.com
2. Select the environment: **orgecbce8ef** (the D365 CS org)
3. Click **Solutions** → open or create a solution (e.g., "Zurn Elkay Demo Components")
4. Click **+ New** → **App** → **Page** (Custom Page)
5. Name: **Order Modification Wizard**
6. Choose **Start with a blank page** (we'll build all 4 screens)

### 1.2 Set Page Dimensions
Custom Pages in the productivity pane render in a narrow side panel:
- Width: **380** (matches productivity pane width)
- Height: **800** (or flexible)
- Go to **Settings** (⚙️) → **Display** → set Width=380, Height=800

---

## Step 2: Build the Screens

### Screen 1: Order Lookup

**Purpose**: Agent selects which order to modify. Auto-filters to the current customer's open orders.

#### Controls to Add:
1. **Label** — Screen title: "Order Modification"
2. **Label** — Subtitle: "Select the order to modify"
3. **Gallery** — `galOrders`
   - **Items**: 
     ```
     Filter(
         'Sales Orders',
         'Status Reason' = 'Status Reason (Sales Orders)'.Active
     )
     ```
     > For the demo, show all active orders. In production, you'd filter by the case's customer account.
   - **Template fields**:
     - `ThisItem.'Order ID'` (bold, e.g., "PO-94820")
     - `ThisItem.Name` (description line)
     - `"$" & Text(ThisItem.'Total Amount', "#,##0.00")` (right-aligned)
     - `Text(ThisItem.'Date Delivered', "MMM d, yyyy")` (delivery date)
   - **OnSelect**: `Set(varSelectedOrder, ThisItem); Navigate(scrLineManagement)`
4. **Rectangle** — Blue accent bar at top

#### Data Source:
- Add **Sales Orders** (salesorder) from Dataverse connector

---

### Screen 2: Line Management (`scrLineManagement`)

**Purpose**: Show all line items for the selected order. Agent can mark lines for cancellation and adjust delivery dates.

#### Controls:
1. **Label** — `"PO " & varSelectedOrder.'Order ID'` (shows "PO PO-94820")
2. **Label** — Customer name: `varSelectedOrder.'Customer (Account)'.'Account Name'`
3. **Gallery** — `galLineItems`
   - **Items**:
     ```
     Filter(
         'Sales Order Products',
         'Sales Order'.'Sales Order' = varSelectedOrder.'Sales Order'
     )
     ```
   - **Template** (each row):
     - **Label**: `"Ln " & ThisItem.'Line Item Number'` (left pill)
     - **Label**: `ThisItem.'Product Description'` (product name, bold)
     - **Label**: `ThisItem.Quantity & " × $" & Text(ThisItem.'Price Per Unit', "#,##0.00")` (qty × price)
     - **Label**: `"$" & Text(ThisItem.'Extended Amount', "#,##0.00")` (right-aligned total)
     - **Checkbox** — `chkCancel`: "Cancel this line"
       - **OnCheck**: `Collect(colCancelledLines, ThisItem)`
       - **OnUncheck**: `Remove(colCancelledLines, ThisItem)`
     - **DatePicker** — `dpDelivery`: sets new delivery date per line
       - **DefaultDate**: `ThisItem.'Ship To: Requested Delivery Date'`
       - **OnChange**: `Collect(colDateChanges, {LineId: ThisItem.'Sales Order Detail', NewDate: dpDelivery.SelectedDate})`

4. **Label** — Running totals footer:
   ```
   "Cancelling " & CountRows(colCancelledLines) & " lines = -$" & 
   Text(Sum(colCancelledLines, 'Extended Amount'), "#,##0.00")
   ```

5. **Button** — "Review Changes" → `Navigate(scrReview)`
6. **Button** — "← Back" → `Navigate(scrOrderLookup)`

#### Collections (initialized in `OnVisible`):
```
ClearCollect(colCancelledLines, Blank());
ClearCollect(colDateChanges, Blank());
```

---

### Screen 3: Review & Confirm (`scrReview`)

**Purpose**: Summary of all changes before submitting. Shows delta.

#### Controls:
1. **Label** — "Review Changes" (title)
2. **Label** — `"PO " & varSelectedOrder.'Order ID' & " — " & varSelectedOrder.Name`
3. **HTML Text** — Change summary (shows lines being cancelled with red strikethrough, date changes in blue)
   ```
   "<h3>Lines to Cancel</h3>" & 
   Concat(colCancelledLines, 
       "<div style='color:red;text-decoration:line-through'>Ln " & 'Line Item Number' & " — " & 'Product Description' & " ($" & Text('Extended Amount', "#,##0.00") & ")</div>"
   ) &
   "<h3>Delivery Date Changes</h3>" &
   "<div>New delivery: March 10, 2026 (was March 15)</div>" &
   "<h3>Impact</h3>" &
   "<div>Lines cancelled: " & CountRows(colCancelledLines) & "</div>" &
   "<div>Credit amount: <b>$" & Text(Sum(colCancelledLines, 'Extended Amount'), "#,##0.00") & "</b></div>"
   ```

4. **Text Input** — `txtAgentNotes`: placeholder "Add notes for the customer..."
5. **Button** — "Submit Changes" (accent color)
   - **OnSelect**:
     ```
     // Cancel the selected lines (set quantitycancelled = quantity)
     ForAll(
         colCancelledLines,
         Patch(
             'Sales Order Products',
             ThisRecord,
             { 'Quantity Cancelled': ThisRecord.Quantity }
         )
     );
     // Update delivery dates on remaining lines
     ForAll(
         Filter('Sales Order Products', 
             'Sales Order'.'Sales Order' = varSelectedOrder.'Sales Order',
             !('Sales Order Detail' in colCancelledLines.'Sales Order Detail')
         ),
         Patch(
             'Sales Order Products',
             ThisRecord,
             { 'Ship To: Requested Delivery Date': Date(2026, 3, 10) }
         )
     );
     // Navigate to confirmation
     Navigate(scrConfirmation);
     ```
   > **Simplified for demo**: In production, you'd call a Power Automate flow for the submit action to handle FNO integration, email notifications, and approval workflows.

6. **Button** — "← Back" → `Navigate(scrLineManagement)`

---

### Screen 4: Confirmation (`scrConfirmation`)

**Purpose**: Success confirmation with next actions.

#### Controls:
1. **Icon** — Green checkmark (large, centered)
2. **Label** — "Order Updated Successfully" (large text)
3. **Label** — `"PO " & varSelectedOrder.'Order ID' & " has been modified"`
4. **Label** — Summary: `CountRows(colCancelledLines) & " lines cancelled | Delivery updated to March 10, 2026"`
5. **Label** — `"Credit: $" & Text(Sum(colCancelledLines, 'Extended Amount'), "#,##0.00")`
6. **Button** — "Add to Case Timeline"
   - **OnSelect**: Create a timeline note on the case with the modification summary
     ```
     Patch(
         Notes,
         Defaults(Notes),
         {
             Subject: "Order Modification - PO " & varSelectedOrder.'Order ID',
             'Note Text': "Cancelled " & CountRows(colCancelledLines) & " lines. Credit: $" & Text(Sum(colCancelledLines, 'Extended Amount'), "#,##0.00") & ". Delivery expedited to March 10, 2026. Agent notes: " & txtAgentNotes.Text,
             'Regarding (Cases)': LookUp(Cases, 'Case Title' = "Ferguson PO #94820 - Order modification request")
         }
     );
     Notify("Note added to case timeline", NotificationType.Success);
     ```
7. **Button** — "Draft Confirmation Email"
   - For demo: `Launch("mailto:mike.reynolds@ferguson.com?subject=PO%2094820%20Modification%20Confirmation")`
8. **Button** — "Start New Modification" → `Navigate(scrOrderLookup)`

---

## Step 3: Add Data Sources

In the Custom Page editor, add these Dataverse tables:
1. **Sales Orders** (`salesorder`)
2. **Sales Order Products** (`salesorderdetail`)
3. **Accounts** (`account`)
4. **Notes** (`annotation`) — for timeline posting
5. **Cases** (`incident`) — for case context

Click **Data** (cylinder icon) → **+ Add data** → **Dataverse** → search and add each.

---

## Step 4: Add to Solution & Publish

1. Save the Custom Page (Ctrl+S)
2. **Publish** the Custom Page
3. Ensure it's in your solution (Solutions → your solution → verify the Custom Page appears)

---

## Step 5: Register in the Productivity Pane

This is the critical step that makes the Custom Page appear as a tool in the CS agent's side panel.

### 5.1 Open Customer Service Admin Center
1. Go to https://orgecbce8ef.crm.dynamics.com
2. Navigate to **Customer Service admin center** (via the app selector)
3. In the left nav: **Workspaces** → **Agent experience profiles**

### 5.2 Create or Edit the Agent Experience Profile
1. Open the profile used by your demo agents (or create a new one: "Zurn Elkay Demo Profile")
2. Under the **Productivity pane** section, click **Edit**
3. Ensure the productivity pane is **Enabled**

### 5.3 Add the Custom Page as a Productivity Pane Tool
1. In the profile, go to **Channel provider** or **Third party tools** section
2. Click **+ Add tool** (or **Manage**)
3. Select **Custom Page** as the tool type
4. Choose **Order Modification Wizard** from the page list
5. Configure:
   - **Label**: "Order Modification"
   - **Icon**: Use a built-in icon (e.g., clipboard, shopping cart, or document)
   - **Show on**: Case entity form (so it appears when an agent opens a case)
   - **Position**: Add alongside Copilot, KB Search, Smart Assist

### 5.4 Alternative: Use App Side Panes API (Programmatic)

If the admin UI doesn't support custom page tools directly, use the **Client API** approach:

1. Create a **Ribbon/Command Bar button** on the Case form:
   - Label: "📋 Modify Order"
   - Command: JavaScript that opens the Custom Page in a side pane

2. JavaScript (add as a web resource):
```javascript
function openOrderModificationWizard(formContext) {
    var pageInput = {
        pageType: "custom",
        name: "cr8d7_ordmodwizard_8a1b2",  // Replace with your Custom Page unique name
        entityName: "incident",
        recordId: formContext.data.entity.getId()
    };
    var navigationOptions = {
        target: 2,  // 2 = side dialog
        width: { value: 400, unit: "px" },
        position: 1  // 1 = side pane
    };
    Xrm.Navigation.navigateTo(pageInput, navigationOptions);
}
```

3. Register the button using Ribbon Workbench or a solution XML customization on the Case form command bar.

### 5.5 Alternative: Agent Script Action

1. Add an **Agent Script** step of type "Macro"
2. Macro action: Open Custom Page (side pane)
3. This way the guided walk-through (Agent Script) can include "Process order modification" as a step that opens the wizard

---

## Step 6: Test the Flow

### Test Sequence (mirrors the phone call demo):
1. Open a case for Ferguson (e.g., "Ferguson PO #94820 - Order modification request")
2. Click the **Order Modification** tool in the productivity pane (right side)
3. Screen 1: See PO-94820 in the list → click it
4. Screen 2: Check the "Cancel" box on Line 4 (Drinking Fountains) and Line 5 (Stainless Sinks)
5. Screen 2: Change delivery date to March 10 for lines 1-3
6. Screen 2: See running total: "Cancelling 2 lines = -$67,450"
7. Click "Review Changes"
8. Screen 3: See red strikethrough on cancelled lines, new delivery date, credit amount
9. Add agent note: "Per Mike Reynolds call - Fort Worth scope reduction"
10. Click "Submit Changes"
11. Screen 4: Green checkmark, "Order Updated Successfully"
12. Click "Add to Case Timeline" → note appears in case timeline
13. Click "Draft Confirmation Email" → opens email to Mike

### Expected Data Changes After Submit:
| Line | Before | After |
|------|--------|-------|
| Ln 1 EK-BF-5001 | 120 × $1,150, Mar 15 | 120 × $1,150, **Mar 10** |
| Ln 2 EK-WC-5002 | 60 × $780, Mar 15 | 60 × $780, **Mar 10** |
| Ln 3 EK-FL-6003 | 200 × $29.50, Mar 15 | 200 × $29.50, **Mar 10** |
| Ln 4 EK-DF-5003 | 25 × $1,450, Mar 15 | **CANCELLED** (qty_cancelled = 25) |
| Ln 5 EK-SS-6001 | 40 × $780, Mar 15 | **CANCELLED** (qty_cancelled = 40) |
| **Credit** | | **$67,450** |

---

## Demo Talking Points

When showing this to Zurn Elkay:

1. **"This replaces the Salesforce Screen Flow"** — Same guided experience, same side panel position, but built natively on Power Platform with direct Dataverse access.

2. **"No code deployment needed"** — The Custom Page is built in the maker portal and deployed through solutions. No Apex triggers, no Visual Force pages, no deployment pipelines.

3. **"Context-aware"** — The wizard knows which case the agent is on and can auto-filter orders to the customer. In SF, this required custom Lightning components.

4. **"Extensible"** — Add approval workflows with Power Automate, connect to FNO for fulfillment, add AI Builder for order anomaly detection — all low-code.

5. **"Same experience as Copilot"** — The Order Modification wizard sits right next to Copilot and Smart Assist in the productivity pane. Agents don't leave their workspace.

---

## Simplified Demo-Day Shortcut

If you run out of time building the full Custom Page, use this **minimal viable approach**:

1. Create a single-screen Custom Page with just a gallery showing PO #94820's line items
2. Add checkboxes for cancel and a submit button
3. Skip the date picker and review screen
4. This takes ~30 minutes instead of ~2 hours

The key demo point is the **productivity pane embedding** — showing that D365 has the same side-panel guided process capability as Salesforce's Utility Bar flows.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Custom Page not showing in pane | Verify it's published and added to the Agent Experience Profile |
| "No orders found" in gallery | Check Data Source is added; verify Sales Orders table has data |
| Can't patch Sales Order Products | Ensure the Custom Page has Dataverse connection with sufficient privileges |
| Productivity pane empty | Enable the pane in Agent Experience Profile → Productivity Pane toggle ON |
| Custom Page too wide | Set display width to 380px in Custom Page settings |
| Changes not reflecting | Click refresh on the Sales Order form; Dataverse patches are async |
