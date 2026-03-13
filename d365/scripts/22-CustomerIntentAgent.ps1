<#
.SYNOPSIS
    Configures the Customer Intent Agent -- descriptions, agent instructions, and KB runbooks.
.DESCRIPTION
    Step 22: Adds intent descriptions, Copilot agent instructions, and creates
    prescriptive KB articles (SOPs) for each discovered intent so the Intent Agent
    can surface Next-Best-Action guidance to service representatives.
.NOTES
    Prerequisites: Steps 01-21 complete. Customer Intent Agent already has intents
    discovered (2 groups, 10 intents) and LoB configured.
#>

param(
    [string]$CustomerPath = (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') 'customers') 'Zurn')
)

# -- Bootstrap ----------------------------------------------------------------
Import-Module (Join-Path $PSScriptRoot 'DataverseHelper.psm1') -Force
Connect-Dataverse

$api = Get-DataverseApiUrl
$subjectId = "a17b96ef-8d12-f111-8406-7ced8dceb26a"   # Zurn/Elkay KB subject

# -- Intent Group Definitions --------------------------------------------------
$groupUpdates = @{
    "0f9bdc13-14c7-f011-bbd3-7c1e525a3c6b" = @{
        msdyn_description           = "Intents related to manufacturing quality, production scheduling, material specifications, defect reporting, and process changes for Zurn and Elkay product lines."
        msdyn_intent_description    = "Production and quality intents covering defect triage, inspection requests, process change approvals, production scheduling, and material specification lookups."
        msdyn_intent_agent_settings = @"
You are handling a production and quality intent for Zurn Elkay Water Solutions.

Key context:
- Zurn and Elkay are equal-level brands sharing one service organization
- Primary customers are distributors (not end consumers)
- Customer tiers 1-4 drive priority (Tier 1 = Strategic / highest)
- Products include flush valves, faucets, drains, bottle filling stations, and commercial plumbing fixtures

When responding:
1. Identify the specific product line and SKU involved
2. Check the customer's tier level to determine SLA priority
3. Reference the appropriate KB article for step-by-step guidance
4. For defect reports: always capture batch number, quantity affected, and defect type
5. For inspection requests: determine if this is routine or triggered by a complaint
6. Escalate to engineering if the issue involves a safety concern or potential recall
"@
    }
    "349bdc13-14c7-f011-bbd3-7c1e525a3c6b" = @{
        msdyn_description           = "Intents related to order modifications, delivery logistics, shipment tracking, invoice corrections, and address updates for distributor customers."
        msdyn_intent_description    = "Orders and logistics intents covering order quantity changes, expedited shipping, delivery address updates, shipment tracking, and invoice discrepancy resolution."
        msdyn_intent_agent_settings = @"
You are handling an orders and logistics intent for Zurn Elkay Water Solutions.

Key context:
- Orders flow through distribution partners (Ferguson, HD Supply, Grainger, etc.)
- Customer tiers 1-4 drive priority and SLA (Tier 1 = Strategic / highest)
- Order modifications may require distributor approval depending on fulfillment stage
- Shipments use carriers like FedEx, UPS, and freight carriers for large orders

When responding:
1. Always verify the order number and distributor account first
2. Check order status -- modifications depend on fulfillment stage (Pending, Processing, Shipped)
3. For expedite requests: check tier level -- Tier 1/2 get priority Next Day Air
4. For invoice corrections: gather invoice number, PO number, and discrepancy details
5. Reference the appropriate KB article for step-by-step processing instructions
6. Confirm changes back to the customer with updated timeline
"@
    }
}

# -- Individual Intent Definitions ---------------------------------------------
$intentUpdates = @{
    # --- Orders and logistics group ---
    "076ecb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Change order quantity"
        Description   = "Customer requests to increase or decrease the quantity on an existing order before or during fulfillment."
        AgentSettings = @"
{{text}} {{email}}
When a customer wants to change an order quantity:
1. Ask for the order number and the specific line item(s) to modify
2. Look up the order in the system and verify fulfillment status
3. If status is Pending: process the quantity change directly
4. If status is Processing: check with warehouse -- changes may incur restocking fees
5. If status is Shipped: cannot modify -- offer to create a return/reorder
6. Update the order total and confirm the revised amount with the customer
7. If the quantity increase exceeds available inventory, provide an estimated restock date
Always confirm the updated order summary before closing.
"@
        KBTitle       = "SOP: Processing Order Quantity Changes"
        KBKeywords    = "order, quantity, change, modify, increase, decrease, fulfillment, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Processing Order Quantity Changes</h1>
<h2>Purpose</h2>
<p>Step-by-step procedure for service representatives handling requests to modify order quantities for Zurn and Elkay product orders.</p>

<h2>Prerequisites</h2>
<ul>
<li>Verify caller identity and distributor account</li>
<li>Obtain the order number (SO-XXXXX format)</li>
</ul>

<h2>Procedure</h2>
<h3>Step 1: Look Up the Order</h3>
<p>Navigate to <strong>Sales &gt; Orders</strong> and search by order number. Confirm the customer name and distributor account match the caller.</p>

<h3>Step 2: Check Fulfillment Status</h3>
<table border='1' cellpadding='5'>
<tr><th>Status</th><th>Action</th></tr>
<tr><td><strong>Pending</strong></td><td>Quantity can be modified directly. Proceed to Step 3.</td></tr>
<tr><td><strong>Processing</strong></td><td>Contact warehouse team via internal queue. Changes may incur a restocking fee if items are already picked. Wait for warehouse confirmation before modifying.</td></tr>
<tr><td><strong>Shipped</strong></td><td>Cannot modify. Offer to initiate a return (see SOP: Return/RMA Process) and create a new order for the correct quantity.</td></tr>
<tr><td><strong>Delivered</strong></td><td>Cannot modify. Offer return/reorder process.</td></tr>
</table>

<h3>Step 3: Modify the Order Line</h3>
<ol>
<li>Open the order line item the customer wants to change</li>
<li>Update the <strong>Quantity</strong> field to the new value</li>
<li>Verify the unit price has not changed (check current price list)</li>
<li>Save the order -- the total will recalculate automatically</li>
</ol>

<h3>Step 4: Check Inventory Availability</h3>
<p>If the customer is <em>increasing</em> the quantity, verify inventory availability. If insufficient stock:</p>
<ul>
<li>Provide the estimated restock date from the product record</li>
<li>Offer to split the order: ship available quantity now, backorder the remainder</li>
<li>For Tier 1/2 customers: escalate to supply chain for priority allocation</li>
</ul>

<h3>Step 5: Confirm with Customer</h3>
<p>Read back the updated order summary including: new quantity, updated total, and expected ship date. Send confirmation email to the distributor contact on file.</p>

<h2>Escalation</h2>
<p>Escalate to Order Management supervisor if: order value exceeds 50000 USD, customer disputes restocking fees, or inventory shortage affects a Tier 1 account.</p>
"@
    }
    "136ecb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Expedite urgent order"
        Description   = "Customer requests expedited shipping or production priority for a time-sensitive order."
        AgentSettings = @"
{{text}} {{email}} {{voice}}
When a customer wants to expedite an order:
1. Ask for the order number and required delivery date
2. Check the customer's tier level -- Tier 1/2 customers receive priority expedite at no additional charge
3. Look up the order status and current estimated delivery date
4. If the order has not shipped: request expedited shipping through the logistics team
5. If the order is in production: check with manufacturing on priority scheduling
6. Provide the customer with the updated estimated arrival date and any additional shipping charges
7. For Tier 3/4 customers: quote the expedite fee before processing
Hot words like 'Emergency', 'Next Day Air', 'Urgent' automatically elevate priority.
"@
        KBTitle       = "SOP: Expediting Urgent Orders"
        KBKeywords    = "expedite, urgent, rush, priority, shipping, next day, emergency, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Expediting Urgent Orders</h1>
<h2>Purpose</h2>
<p>Procedure for handling requests to expedite Zurn or Elkay product orders, including priority assessment based on customer tier.</p>

<h2>Priority Assessment</h2>
<table border='1' cellpadding='5'>
<tr><th>Customer Tier</th><th>Expedite Policy</th></tr>
<tr><td><strong>Tier 1 (Strategic)</strong></td><td>Complimentary Next Day Air. Auto-approve. No additional authorization needed.</td></tr>
<tr><td><strong>Tier 2 (Key)</strong></td><td>Complimentary 2-Day shipping. Next Day Air available at 50% discount.</td></tr>
<tr><td><strong>Tier 3 (Standard)</strong></td><td>Expedited shipping at standard carrier rates. Quote before processing.</td></tr>
<tr><td><strong>Tier 4 (Basic)</strong></td><td>Expedited shipping at standard carrier rates plus 25 USD handling fee. Quote before processing.</td></tr>
</table>

<h2>Procedure</h2>
<h3>Step 1: Validate the Request</h3>
<p>Obtain the order number, confirm the distributor account, and ask for the required delivery date.</p>

<h3>Step 2: Check Order Status</h3>
<ul>
<li><strong>Pending/Processing</strong>: Can expedite. Proceed to Step 3.</li>
<li><strong>Shipped</strong>: Contact carrier to upgrade in-transit shipment (FedEx Priority Overnight, UPS Next Day Air). Additional fees apply.</li>
</ul>

<h3>Step 3: Process the Expedite</h3>
<ol>
<li>Open the order record and update the <strong>Shipping Method</strong> field</li>
<li>Add a note: "Expedited per customer request -- [reason]"</li>
<li>For orders in production: create an internal task to the production queue requesting priority scheduling</li>
<li>Update the <strong>Requested Delivery Date</strong> on the order</li>
</ol>

<h3>Step 4: Confirm with Customer</h3>
<p>Provide the updated estimated delivery date, any additional charges (per tier table above), and a tracking number once shipped.</p>

<h2>Escalation</h2>
<p>Escalate to logistics manager if: requested date is within 24 hours, order contains custom/made-to-order items, or carrier cannot meet the requested date.</p>
"@
    }
    "1b6ecb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Request invoice correction"
        Description   = "Customer reports a discrepancy on an invoice -- incorrect pricing, wrong quantities, missing discounts, or billing errors."
        AgentSettings = @"
{{text}} {{email}}
When a customer requests an invoice correction:
1. Ask for the invoice number, PO number, and a description of the discrepancy
2. Pull up the invoice and compare against the original order and price list
3. Common issues: price not matching contracted rate, quantity mismatch, missing volume discount, wrong tax calculation
4. If the error is confirmed: create a credit memo or revised invoice
5. If the invoice is correct: explain the line items and provide supporting documentation
6. For disputed amounts over 5000 USD: escalate to finance team for review
7. Always send the corrected invoice or explanation via email to the billing contact
"@
        KBTitle       = "SOP: Handling Invoice Correction Requests"
        KBKeywords    = "invoice, correction, billing, credit, discrepancy, pricing, discount, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Handling Invoice Correction Requests</h1>
<h2>Purpose</h2>
<p>Step-by-step procedure for resolving invoice discrepancies reported by Zurn and Elkay distributor customers.</p>

<h2>Common Discrepancy Types</h2>
<ul>
<li><strong>Price mismatch</strong>: Invoice price differs from contracted/quoted price</li>
<li><strong>Quantity error</strong>: Invoiced quantity does not match shipped quantity</li>
<li><strong>Missing discount</strong>: Volume discount, promotional pricing, or tier discount not applied</li>
<li><strong>Tax error</strong>: Incorrect tax rate or tax-exempt status not applied</li>
<li><strong>Duplicate charge</strong>: Same line item billed twice</li>
</ul>

<h2>Procedure</h2>
<h3>Step 1: Gather Information</h3>
<p>Collect: invoice number, PO number, the specific line item(s) in question, and the expected vs. actual amount.</p>

<h3>Step 2: Verify the Discrepancy</h3>
<ol>
<li>Open the invoice in the billing system</li>
<li>Cross-reference with the original order (SO number) and the applicable price list</li>
<li>Check the customer's contract for special pricing or volume discounts</li>
<li>For tax issues: verify the customer's tax-exempt certificate is on file and current</li>
</ol>

<h3>Step 3: Resolve</h3>
<table border='1' cellpadding='5'>
<tr><th>Finding</th><th>Action</th></tr>
<tr><td>Error confirmed</td><td>Create a credit memo for the difference. Issue a revised invoice. Note the case with the correction details.</td></tr>
<tr><td>Invoice is correct</td><td>Prepare a detailed explanation with line-item breakdown. Attach supporting price list or contract excerpt. Send to the customer's billing contact.</td></tr>
<tr><td>Disputed amount over 5000 USD</td><td>Escalate to Finance team with full documentation.</td></tr>
</table>

<h3>Step 4: Follow Up</h3>
<p>Send the corrected invoice or explanation to the billing contact via email. Update the case with resolution details and close.</p>

<h2>Escalation</h2>
<p>Escalate to Finance if: disputed amount exceeds 5000 USD, customer claims systemic pricing errors across multiple invoices, or the discrepancy involves a Tier 1 contract rate.</p>
"@
    }
    "fa6dcb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Track raw material shipment"
        Description   = "Customer or internal stakeholder needs status on an inbound raw material or product shipment."
        AgentSettings = @"
{{text}} {{email}} {{voice}}
When someone needs to track a shipment:
1. Ask for the order number or tracking number
2. Look up the shipment in the order record -- check the tracking number and carrier fields
3. Provide the current status: in transit, out for delivery, delivered, or exception
4. If there is a delay or exception: provide the carrier's estimated revised delivery date
5. For missing shipments: initiate a carrier trace request
6. For Tier 1/2 customers with delayed critical shipments: escalate to logistics for intervention
Always include the carrier name and tracking link in your response.
"@
        KBTitle       = "SOP: Tracking Shipments and Handling Delivery Exceptions"
        KBKeywords    = "tracking, shipment, delivery, carrier, FedEx, UPS, freight, delay, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Tracking Shipments and Handling Delivery Exceptions</h1>
<h2>Purpose</h2>
<p>Procedure for tracking Zurn and Elkay product shipments and resolving delivery exceptions.</p>

<h2>Procedure</h2>
<h3>Step 1: Locate the Shipment</h3>
<p>Search by order number (SO-XXXXX) or tracking number. The order record contains the <strong>Tracking Number</strong> and <strong>Carrier</strong> fields.</p>

<h3>Step 2: Check Carrier Status</h3>
<p>Use the tracking number to check status with the carrier:</p>
<ul>
<li><strong>FedEx</strong>: fedex.com/tracking or ShipEngine API</li>
<li><strong>UPS</strong>: ups.com/track or ShipEngine API</li>
<li><strong>Freight carriers</strong>: Contact carrier directly with PRO number</li>
</ul>

<h3>Step 3: Handle Exceptions</h3>
<table border='1' cellpadding='5'>
<tr><th>Exception</th><th>Action</th></tr>
<tr><td><strong>Delayed</strong></td><td>Provide revised ETA from carrier. For Tier 1/2: escalate to logistics for intervention.</td></tr>
<tr><td><strong>Delivery attempted / no one available</strong></td><td>Coordinate redelivery with carrier. Confirm delivery address with customer.</td></tr>
<tr><td><strong>Damaged in transit</strong></td><td>Initiate carrier claim. Offer replacement shipment (see SOP: Return/RMA).</td></tr>
<tr><td><strong>Lost / no scan updates over 48h</strong></td><td>File a carrier trace request. For orders over 1000 USD: ship replacement immediately for Tier 1/2 customers.</td></tr>
</table>

<h3>Step 4: Communicate</h3>
<p>Provide the customer with: carrier name, tracking number, tracking URL, current status, and expected delivery date.</p>

<h2>Escalation</h2>
<p>Escalate to logistics manager if: shipment is lost, delivery is 3+ days late, or the shipment contains hazardous materials.</p>
"@
    }
    "026ecb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Update delivery address"
        Description   = "Customer needs to change the shipping address on an existing order before delivery."
        AgentSettings = @"
{{text}} {{email}}
When a customer needs to update a delivery address:
1. Ask for the order number and the new delivery address
2. Verify the order has not already shipped -- address changes are only possible for Pending/Processing orders
3. If shipped: check if the carrier can redirect (FedEx Address Correction, UPS Intercept) -- fees may apply
4. Validate the new address format and confirm it is a valid commercial delivery location
5. Update the order record and confirm the change back to the customer
6. If the address change moves the delivery to a different region: recalculate shipping charges
"@
        KBTitle       = "SOP: Updating Delivery Address on Orders"
        KBKeywords    = "address, delivery, shipping, update, change, redirect, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Updating Delivery Address on Orders</h1>
<h2>Purpose</h2>
<p>Procedure for modifying the shipping address on Zurn and Elkay product orders.</p>

<h2>Procedure</h2>
<h3>Step 1: Verify Eligibility</h3>
<table border='1' cellpadding='5'>
<tr><th>Order Status</th><th>Address Change?</th></tr>
<tr><td><strong>Pending</strong></td><td>Yes -- update directly in order record.</td></tr>
<tr><td><strong>Processing</strong></td><td>Yes -- update and notify warehouse of the change.</td></tr>
<tr><td><strong>Shipped</strong></td><td>Maybe -- contact carrier for intercept/redirect. FedEx Address Correction fee: approx 19 USD. UPS Intercept fee: approx 16.40 USD.</td></tr>
<tr><td><strong>Delivered</strong></td><td>No -- coordinate return and reship to correct address.</td></tr>
</table>

<h3>Step 2: Validate the New Address</h3>
<ol>
<li>Confirm the full address: street, city, state, ZIP, and attention line</li>
<li>Verify it is a commercial address (residential deliveries may incur surcharges for freight)</li>
<li>Check if the new address is in a different shipping zone -- recalculate shipping cost if needed</li>
</ol>

<h3>Step 3: Update the Order</h3>
<ol>
<li>Open the order record and update <strong>Ship To</strong> address fields</li>
<li>Add a case note: "Address updated per customer request from [old] to [new]"</li>
<li>If shipped: submit carrier redirect request and note the confirmation number</li>
</ol>

<h3>Step 4: Confirm</h3>
<p>Send confirmation email to the customer with the updated delivery address and any revised shipping charges or timeline.</p>
"@
    }
    # --- Production and quality group ---
    "ec6dcb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Provide material specification"
        Description   = "Customer requests technical specifications, material data sheets, or compliance documentation for a Zurn or Elkay product."
        AgentSettings = @"
{{text}} {{email}}
When a customer requests material specifications:
1. Ask which product (model number or product family) they need specs for
2. Check the product record for attached specification documents
3. Common requests: material composition (brass, stainless steel, ABS), lead-free compliance, NSF/ANSI certifications, dimensional drawings
4. If the spec is available in KB articles: share it directly
5. If not available: escalate to engineering for the specific documentation
6. For compliance requests (ADA, NSF 61, NSF 372, Buy America Act): confirm certification status from the product record
Always provide specs in PDF format when possible.
"@
        KBTitle       = "SOP: Providing Product Material Specifications"
        KBKeywords    = "specification, material, datasheet, compliance, NSF, ADA, lead-free, certification, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Providing Product Material Specifications</h1>
<h2>Purpose</h2>
<p>Procedure for handling requests for Zurn and Elkay product specifications, material data sheets, and compliance documentation.</p>

<h2>Common Specification Types</h2>
<ul>
<li><strong>Material composition</strong>: Brass alloy, stainless steel grade, ABS type</li>
<li><strong>Dimensional drawings</strong>: CAD files, installation dimensions</li>
<li><strong>Compliance certifications</strong>: NSF/ANSI 61 (drinking water), NSF 372 (lead-free), ADA compliant, Buy America Act</li>
<li><strong>Performance data</strong>: Flow rates (GPM), pressure ratings (PSI), temperature ranges</li>
<li><strong>Safety data sheets (SDS)</strong>: Chemical composition for plumbing sealants and coatings</li>
</ul>

<h2>Procedure</h2>
<h3>Step 1: Identify the Product</h3>
<p>Get the model number or product family name. Verify against the product catalog to ensure accuracy.</p>

<h3>Step 2: Locate Specifications</h3>
<ol>
<li>Check the <strong>Product</strong> record in Dataverse for attached documents</li>
<li>Search KB articles for existing specification guides</li>
<li>Check the Zurn/Elkay specification library (zurn.com/resources or elkay.com/resources)</li>
</ol>

<h3>Step 3: Deliver to Customer</h3>
<p>Send specifications via email as PDF attachments. Include:</p>
<ul>
<li>Product model number and description</li>
<li>Requested specification document(s)</li>
<li>Applicable certification logos and numbers</li>
<li>Date of last revision</li>
</ul>

<h3>Step 4: Handle Unavailable Specs</h3>
<ol>
<li>Create a task assigned to the Engineering queue</li>
<li>Set priority based on customer tier: Tier 1/2 = High, Tier 3/4 = Normal</li>
<li>Inform the customer of expected turnaround: 1-2 business days for standard, same day for Tier 1</li>
</ol>
"@
    }
    "af6dcb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Report defective batch"
        Description   = "Customer reports a quality defect affecting multiple units from a specific production batch."
        AgentSettings = @"
{{text}} {{email}} {{voice}}
When a customer reports a defective batch:
1. This is HIGH PRIORITY -- capture all details immediately
2. Ask for: batch/lot number, product model, quantity affected, defect description, and when it was discovered
3. Check if there are other reports against the same batch number
4. Create the case with Priority = High (or Critical if safety-related)
5. Trigger the quality hold process: notify QA team immediately
6. For safety-related defects (injury risk, contamination, failure under pressure): escalate to Safety team and flag for potential recall review
7. Request photos or samples from the customer if possible
8. Provide the customer with a case number and expected follow-up timeline
Hot words: Recall, Safety, Legal -- these automatically elevate to maximum priority.
"@
        KBTitle       = "SOP: Defective Batch Reporting and Quality Hold Process"
        KBKeywords    = "defect, batch, quality, recall, safety, hold, inspection, QA, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Defective Batch Reporting and Quality Hold Process</h1>
<h2>Purpose</h2>
<p>Critical procedure for handling reports of defective product batches. Ensures proper documentation, quality hold initiation, and potential recall assessment.</p>

<h2>Priority Classification</h2>
<table border='1' cellpadding='5'>
<tr><th>Severity</th><th>Examples</th><th>Priority</th><th>Response Time</th></tr>
<tr><td><strong>Critical / Safety</strong></td><td>Injury risk, pressure failure, contamination, lead content</td><td>10,000 (Maximum)</td><td>Immediate -- within 1 hour</td></tr>
<tr><td><strong>High</strong></td><td>Functional failure, cosmetic defect affecting over 50 units</td><td>High</td><td>4 business hours (per SLA)</td></tr>
<tr><td><strong>Medium</strong></td><td>Cosmetic defect affecting under 50 units, minor tolerance deviation</td><td>Normal</td><td>8 business hours (per SLA)</td></tr>
</table>

<h2>Procedure</h2>
<h3>Step 1: Capture Defect Details</h3>
<p>Record ALL of the following in the case:</p>
<ul>
<li>Batch/Lot number</li>
<li>Product model number and description</li>
<li>Quantity affected (and total quantity in the customer's inventory from that batch)</li>
<li>Defect description -- be specific (e.g., "hairline crack at valve seat" not "cracked")</li>
<li>Discovery date and method (visual inspection, functional test, customer complaint)</li>
<li>Photos or samples requested/received</li>
</ul>

<h3>Step 2: Check for Related Reports</h3>
<p>Search cases for the same batch number. If other reports exist, link the cases and escalate immediately -- this indicates a systemic issue.</p>

<h3>Step 3: Initiate Quality Hold</h3>
<ol>
<li>Create a task assigned to the <strong>Quality Assurance</strong> queue</li>
<li>Include the batch number, product, and defect details</li>
<li>QA will determine if a production hold is needed for remaining inventory</li>
<li>For safety defects: notify the Safety team immediately via the escalation queue</li>
</ol>

<h3>Step 4: Customer Communication</h3>
<p>Provide the customer with:</p>
<ul>
<li>Case number for tracking</li>
<li>Instructions to isolate affected product (do not install or distribute further)</li>
<li>Expected timeline for QA assessment (typically 24-48 hours)</li>
<li>Replacement or credit options will be communicated after QA review</li>
</ul>

<h2>Escalation</h2>
<p><strong>IMMEDIATE escalation</strong> to Safety team if: injury reported, failure under pressure, contamination, or potential regulatory violation. This may trigger the formal recall assessment process.</p>
"@
    }
    "cc6dcb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Request process change"
        Description   = "Customer or internal stakeholder requests a change to an established manufacturing or fulfillment process."
        AgentSettings = @"
{{text}} {{email}}
When someone requests a process change:
1. Determine the scope: is this a manufacturing process, fulfillment process, or service process change?
2. Ask for: current process description, proposed change, reason for change, and expected impact
3. Process changes require approval -- create a case and route to the appropriate team
4. For manufacturing process changes: route to Engineering queue
5. For fulfillment/logistics changes: route to Operations queue
6. Track the approval workflow and update the customer on status
7. Once approved: update the relevant KB articles and SOPs with the new process
"@
        KBTitle       = "SOP: Processing Change Requests for Manufacturing and Fulfillment"
        KBKeywords    = "process, change, request, manufacturing, approval, engineering, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Processing Change Requests</h1>
<h2>Purpose</h2>
<p>Procedure for handling requests to change established manufacturing, fulfillment, or service processes at Zurn Elkay.</p>

<h2>Change Request Categories</h2>
<ul>
<li><strong>Manufacturing</strong>: Material substitution, tooling change, assembly sequence, quality checkpoint</li>
<li><strong>Fulfillment</strong>: Packaging method, shipping carrier, warehouse procedure</li>
<li><strong>Service</strong>: SLA adjustment, routing rule, escalation procedure</li>
</ul>

<h2>Procedure</h2>
<h3>Step 1: Document the Request</h3>
<p>Create a case capturing: current process, proposed change, business justification, requestor, affected product lines, and estimated impact.</p>

<h3>Step 2: Route for Review</h3>
<table border='1' cellpadding='5'>
<tr><th>Change Type</th><th>Route To</th><th>Approval Level</th></tr>
<tr><td>Manufacturing</td><td>Engineering queue</td><td>Engineering Manager</td></tr>
<tr><td>Fulfillment</td><td>Operations queue</td><td>Operations Supervisor</td></tr>
<tr><td>Service</td><td>Service Management queue</td><td>Service Manager</td></tr>
</table>

<h3>Step 3: Track Approval</h3>
<p>Monitor the case for approval/rejection. Typical turnaround: 3-5 business days for standard changes, 1 day for urgent changes affecting production.</p>

<h3>Step 4: Implement and Document</h3>
<p>Once approved: update affected SOPs, KB articles, and training materials. Notify impacted teams.</p>
"@
    }
    "e26dcb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Request quality inspection"
        Description   = "Customer requests a quality inspection of received product, either as a routine check or in response to a suspected issue."
        AgentSettings = @"
{{text}} {{email}} {{voice}}
When a customer requests a quality inspection:
1. Determine the trigger: routine incoming inspection, suspected defect, or customer complaint
2. Ask for: product model, batch/lot number, quantity to inspect, and specific concerns
3. For routine inspections: provide the standard inspection checklist from KB
4. For suspected defects: escalate to QA team and treat as potential defective batch report
5. If an on-site inspection is needed: coordinate with field service team
6. Provide expected inspection timeline based on type: routine = 2-3 days, triggered = 1 day
"@
        KBTitle       = "SOP: Quality Inspection Requests and Procedures"
        KBKeywords    = "inspection, quality, QA, checklist, defect, incoming, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Quality Inspection Requests and Procedures</h1>
<h2>Purpose</h2>
<p>Procedure for handling quality inspection requests for Zurn and Elkay products.</p>

<h2>Inspection Types</h2>
<table border='1' cellpadding='5'>
<tr><th>Type</th><th>Trigger</th><th>Priority</th><th>Timeline</th></tr>
<tr><td><strong>Routine</strong></td><td>Standard incoming product inspection</td><td>Normal</td><td>2-3 business days</td></tr>
<tr><td><strong>Triggered</strong></td><td>Customer complaint or suspected defect</td><td>High</td><td>1 business day</td></tr>
<tr><td><strong>Regulatory</strong></td><td>Compliance audit or certification renewal</td><td>High</td><td>Per regulatory timeline</td></tr>
</table>

<h2>Procedure</h2>
<h3>Step 1: Create Inspection Request</h3>
<p>Create a case with: product model, batch/lot number, quantity, inspection reason, and any specific test requirements (dimensional, functional, material).</p>

<h3>Step 2: Route to QA</h3>
<p>Assign the case to the Quality Assurance queue. Include:</p>
<ul>
<li>Standard inspection checklist reference (see Quality Control Standards KB article)</li>
<li>Any specific tests the customer has requested</li>
<li>Sample availability -- does the customer need to ship product or is it in our warehouse?</li>
</ul>

<h3>Step 3: Conduct Inspection</h3>
<p>QA performs inspection per the Zurn/Elkay quality control standards. Results documented in the case notes with pass/fail for each checkpoint.</p>

<h3>Step 4: Report Results</h3>
<p>Send inspection report to the customer including: pass/fail status, detailed findings, photos of any defects, and recommended actions.</p>

<h2>Escalation</h2>
<p>If inspection reveals defects: follow the Defective Batch Reporting SOP. If inspection is related to a safety concern: escalate to Safety team immediately.</p>
"@
    }
    "d96dcb19-14c7-f011-bbd2-7ced8dcb20cd" = @{
        Name          = "Schedule production run"
        Description   = "Request to schedule or reschedule a manufacturing production run for a specific Zurn or Elkay product."
        AgentSettings = @"
{{text}} {{email}}
When a production run scheduling request comes in:
1. Ask for: product model, required quantity, requested completion date, and priority
2. Check current production schedule for capacity and conflicts
3. For standard requests: add to the production queue with the requested date
4. For urgent requests (Tier 1/2 customers or stock-out situations): flag as priority and notify production manager
5. Provide the customer with the confirmed production schedule date and estimated ship date
6. If the requested date cannot be met: offer the earliest available slot and explain the delay
"@
        KBTitle       = "SOP: Scheduling and Managing Production Runs"
        KBKeywords    = "production, schedule, manufacturing, capacity, planning, backorder, Zurn, Elkay"
        KBContent     = @"
<h1>SOP: Scheduling and Managing Production Runs</h1>
<h2>Purpose</h2>
<p>Procedure for scheduling, rescheduling, and prioritizing production runs for Zurn and Elkay products.</p>

<h2>Procedure</h2>
<h3>Step 1: Capture Requirements</h3>
<p>Obtain: product model and SKU, quantity required, requested completion date, and business justification (customer order, stock replenishment, etc.).</p>

<h3>Step 2: Check Production Capacity</h3>
<ol>
<li>Review the current production schedule for the relevant product line</li>
<li>Check raw material availability for the requested quantity</li>
<li>Identify any conflicting priority runs</li>
</ol>

<h3>Step 3: Schedule the Run</h3>
<table border='1' cellpadding='5'>
<tr><th>Priority</th><th>Scheduling Rule</th></tr>
<tr><td><strong>Tier 1 customer order</strong></td><td>Priority slot -- can bump Tier 3/4 standard replenishment</td></tr>
<tr><td><strong>Tier 2 customer order</strong></td><td>Next available slot after Tier 1 commitments</td></tr>
<tr><td><strong>Stock replenishment</strong></td><td>Standard queue -- first available production window</td></tr>
<tr><td><strong>Emergency / stock-out</strong></td><td>Expedited -- notify production manager for immediate scheduling</td></tr>
</table>

<h3>Step 4: Confirm and Track</h3>
<p>Update the case with the confirmed production date and expected completion. Notify the requesting party. Monitor progress and update if delays occur.</p>
"@
    }
}

# ==============================================================================
# PART 1 -- Update Intent Group descriptions and agent settings
# ==============================================================================
Write-StepHeader "22A" "Updating intent group descriptions and agent settings"

foreach ($groupId in $groupUpdates.Keys) {
    $grp = $groupUpdates[$groupId]
    $body = @{
        msdyn_description           = $grp.msdyn_description
        msdyn_intent_description    = $grp.msdyn_intent_description
        msdyn_intent_agent_settings = $grp.msdyn_intent_agent_settings
    }

    $result = Invoke-DataversePatch -EntitySet "msdyn_intents" -RecordId ([guid]$groupId) -Body $body
    if ($result) {
        Write-Host "  [OK] Updated group: $groupId" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Failed to update group: $groupId" -ForegroundColor Red
    }
}

# ==============================================================================
# PART 2 -- Update individual intent descriptions and agent settings
# ==============================================================================
Write-StepHeader "22B" "Updating individual intent descriptions and agent settings"

foreach ($intentId in $intentUpdates.Keys) {
    $intent = $intentUpdates[$intentId]
    $body = @{
        msdyn_description           = $intent.Description
        msdyn_intent_description    = $intent.Description
        msdyn_intent_agent_settings = $intent.AgentSettings
    }

    $result = Invoke-DataversePatch -EntitySet "msdyn_intents" -RecordId ([guid]$intentId) -Body $body
    if ($result) {
        Write-Host "  [OK] Updated intent: $($intent.Name)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Failed to update intent: $($intent.Name)" -ForegroundColor Red
    }
}

# ==============================================================================
# PART 3 -- Create KB Articles (prescriptive SOPs for each intent)
# ==============================================================================
Write-StepHeader "22C" "Creating prescriptive KB articles for each intent"

$createdKBs = @()

foreach ($intentId in $intentUpdates.Keys) {
    $intent = $intentUpdates[$intentId]

    # Check if KB already exists
    $escapedTitle = $intent.KBTitle -replace "'", "''"
    $existing = Invoke-DataverseGet -EntitySet "knowledgearticles" `
        -Filter "title eq '$escapedTitle'" -Select "knowledgearticleid,title,statecode" -Top 1

    if ($existing -and $existing.Count -gt 0) {
        $existId = if ($existing -is [array]) { $existing[0].knowledgearticleid } else { $existing.knowledgearticleid }
        Write-Host "  [SKIP] KB already exists: $($intent.KBTitle)" -ForegroundColor Yellow
        $createdKBs += @{ Title = $intent.KBTitle; Id = $existId; Status = "existing" }
        continue
    }

    # Create the KB article
    $kbBody = @{
        title                  = $intent.KBTitle
        keywords               = $intent.KBKeywords
        content                = $intent.KBContent
        "subjectid@odata.bind" = "/subjects($subjectId)"
        description            = "Prescriptive SOP for intent: $($intent.Name)"
    }

    $newKB = Invoke-DataversePost -EntitySet "knowledgearticles" -Body $kbBody
    if ($newKB) {
        $kbId = $newKB.knowledgearticleid
        Write-Host "  [OK] Created KB: $($intent.KBTitle) ($kbId)" -ForegroundColor Green
        $createdKBs += @{ Title = $intent.KBTitle; Id = $kbId; Status = "created" }
    } else {
        Write-Host "  [FAIL] Failed to create KB: $($intent.KBTitle)" -ForegroundColor Red
        $createdKBs += @{ Title = $intent.KBTitle; Id = $null; Status = "failed" }
    }
}

# ==============================================================================
# PART 4 -- Publish KB Articles (Draft -> Published)
# ==============================================================================
Write-StepHeader "22D" "Publishing KB articles"

foreach ($kb in $createdKBs) {
    if ($kb.Status -ne "created" -or -not $kb.Id) { continue }

    $pubResult = Invoke-DataversePatch -EntitySet "knowledgearticles" -RecordId ([guid]$kb.Id) -Body @{
        statecode  = 3
        statuscode = 7
    }
    if ($pubResult) {
        Write-Host "  [OK] Published: $($kb.Title)" -ForegroundColor Green
    } else {
        Write-Host "  [!] Could not publish: $($kb.Title)" -ForegroundColor Yellow
    }
}

# ==============================================================================
# Export results
# ==============================================================================
$outputPath = Join-Path (Join-Path $CustomerPath 'data') 'intent-agent-ids.json'
$createdKBs | ConvertTo-Json -Depth 3 | Out-File $outputPath -Encoding utf8
Write-Host "`n  Results saved to $outputPath" -ForegroundColor Cyan

Write-Host "`n[DONE] Customer Intent Agent configuration complete." -ForegroundColor Green
Write-Host "   - 2 intent groups updated with descriptions + agent instructions"
Write-Host "   - 10 intents updated with descriptions + agent instructions"
Write-Host "   - 10 KB articles created with prescriptive SOPs"

