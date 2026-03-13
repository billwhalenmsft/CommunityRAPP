<#
.SYNOPSIS
    Creates 15 Zurn-specific knowledge articles in D365 Customer Service.
    Articles align with Zurn products, distributor/channel relationships, and use cases.
.NOTES
    Safe to re-run — uses title match to skip existing articles.
#>

# ── Auth ──
$token = (az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv)
$headers = @{
    Authorization      = "Bearer $token"
    Accept             = "application/json"
    "Content-Type"     = "application/json; charset=utf-8"
    "OData-MaxVersion" = "4.0"
    "OData-Version"    = "4.0"
}
$base = "https://orgecbce8ef.crm.dynamics.com/api/data/v9.2"

# ── Subject ID map (orgecbce8ef – Zurn-parented subjects) ──
$subjects = @{
    "Order Management (Zurn)"     = "df5190ef-8d12-f111-8406-7c1e5218592b"
    "Logistics & Shipping (Zurn)" = "908661ec-8d12-f111-8407-7c1e52143136"
    "Pricing & Quotes (Zurn)"     = "27b12eec-8d12-f111-8407-7ced8d18c8d7"
    "Technical Support (Zurn)"    = "1eb12eec-8d12-f111-8407-7ced8d18c8d7"
    "Backflow / Wilkins"          = "e25190ef-8d12-f111-8406-7c1e5218592b"
    "Drainage (Zurn)"             = "a202d2ed-8d12-f111-8407-7ced8dceb433"
    "General"                     = "0afab5dd-b807-ed11-82e4-000d3a3b0334"
    "Warranty & Returns (Zurn)"   = "a17b96ef-8d12-f111-8406-7ced8dceb26a"
    "Quality / Recall (Zurn)"     = "39897eee-8d12-f111-8407-7c1e520a58a1"
}

# ── Article Definitions ──
$articles = @(

    # ═══════════════════════════════════════════
    # 1. ORDER & DISTRIBUTION (3 articles)
    # ═══════════════════════════════════════════

    @{
        title       = "How to Place a Zurn Product Order Through Your Distribution Partner"
        description = "Step-by-step guide for placing Zurn product orders through authorized distribution partners including Ferguson, HD Supply, and Winsupply."
        keywords    = "order, distribution, Ferguson, HD Supply, Winsupply, purchase order, Zurn"
        subjectKey  = "Order Management (Zurn)"
        content     = @"
<h2>Overview</h2>
<p>Zurn Industries sells exclusively through authorized distribution partners. All product orders — whether for flush valves, sensor faucets, drains, or backflow preventers — are placed through your assigned distributor, not directly with Zurn.</p>

<h2>Authorized Distribution Partners</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Distributor</th><th>Specialty</th><th>Coverage</th></tr>
<tr><td><strong>Ferguson Enterprises</strong></td><td>Full Zurn catalog — plumbing, drainage, backflow</td><td>National</td></tr>
<tr><td><strong>HD Supply</strong></td><td>Commercial MRO, flush valves, sensor faucets</td><td>National</td></tr>
<tr><td><strong>Winsupply Inc.</strong></td><td>Regional plumbing wholesale — full Zurn line</td><td>Regional (multi-location)</td></tr>
<tr><td><strong>F.W. Webb</strong></td><td>Northeast plumbing & HVAC wholesale</td><td>Northeast US</td></tr>
<tr><td><strong>Core &amp; Main</strong></td><td>Waterworks, backflow, municipal infrastructure</td><td>National</td></tr>
</table>

<h2>Order Process</h2>
<ol>
<li><strong>Identify your distributor</strong> — Check your account record in D365 to confirm your assigned distributor and customer tier (Tier 1–4).</li>
<li><strong>Request a quote</strong> — Contact your distributor rep or submit via their portal. Reference Zurn product numbers (e.g., ZN-AV-1001 for AquaVantage Flush Valve).</li>
<li><strong>Distributor places PO with Zurn</strong> — Your distributor submits the purchase order to Zurn. Pricing follows your tier-based discount schedule.</li>
<li><strong>Fulfillment</strong> — Orders ship from the nearest Zurn distribution center or direct from the factory for specialty items.</li>
<li><strong>Tracking</strong> — Your distributor provides shipment tracking. For escalations, contact Zurn Customer Service and reference the distributor PO number.</li>
</ol>

<h2>Key Product Numbers for Ordering</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#f0f0f0"><th>Product #</th><th>Description</th></tr>
<tr><td>ZN-AV-1001</td><td>Zurn AquaVantage AV Flush Valve (1.28 GPF)</td></tr>
<tr><td>ZN-EZ-1002</td><td>Zurn AquaSense E-Z Flush Valve Retrofit Kit</td></tr>
<tr><td>ZN-SF-2001</td><td>Zurn AquaSense Sensor Faucet</td></tr>
<tr><td>ZN-FD-3001</td><td>Zurn Z415 Floor Drain</td></tr>
<tr><td>WK-RP-4001</td><td>Wilkins 975XL RPZ Assembly</td></tr>
<tr><td>WK-DC-4002</td><td>Wilkins 350XL Double Check Valve</td></tr>
</table>

<h2>Escalation</h2>
<p>If a distributor cannot fulfill an order within standard lead times, create a case in D365 under <strong>Order Management</strong> and assign to the <strong>Zurn Phone - General</strong> queue. Include the distributor name, PO number, and product SKUs.</p>
"@
    }

    @{
        title       = "Distribution Network Sourcing: Stock Availability and Fulfillment"
        description = "How Zurn's distribution network manages inventory, stock availability, and fulfillment for distributor and end-user orders."
        keywords    = "distribution, sourcing, inventory, stock, fulfillment, rep network, Ferguson, HD Supply, Winsupply"
        subjectKey  = "Logistics & Shipping (Zurn)"
        content     = @"
<h2>Overview</h2>
<p>Zurn's go-to-market model relies on a distributor network supported by manufacturer rep agencies. Understanding this chain is critical for resolving order-related cases efficiently.</p>

<h2>The Distribution Chain</h2>
<p style="font-size:14px; padding:12px; background:#f5f5f5; border-left:4px solid #003B71">
<strong>Zurn Factory</strong> → <strong>Distribution Center</strong> → <strong>Authorized Distributor</strong> (Ferguson, HD Supply, Winsupply, etc.) → <strong>End User</strong> (School District, Municipality, Contractor, Business)
</p>

<h3>Role of the Manufacturer Rep</h3>
<p>Zurn's rep network serves as the field liaison between Zurn and the distributor. Reps:</p>
<ul>
<li>Ensure the <strong>right stock levels</strong> are maintained at distributor warehouses for their territory</li>
<li>Provide <strong>technical guidance</strong> to distributors and specifying engineers</li>
<li>Manage <strong>project-based orders</strong> for large commercial jobs (hospitals, schools, stadiums)</li>
<li>Escalate <strong>supply chain issues</strong> to Zurn regional management</li>
</ul>

<h3>Stock Availability by Product Category</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Category</th><th>Typical Stocking</th><th>Lead Time (Non-Stock)</th></tr>
<tr><td>Flush Valves (ZN-AV, ZN-EZ, ZN-UR)</td><td>Stocked at major distributors</td><td>3–5 business days</td></tr>
<tr><td>Sensor Faucets (ZN-SF, ZN-AS)</td><td>Stocked at major distributors</td><td>5–7 business days</td></tr>
<tr><td>Floor &amp; Roof Drains (ZN-FD, ZN-RD)</td><td>Common sizes stocked; specialty made-to-order</td><td>2–4 weeks</td></tr>
<tr><td>Trench Drains (ZN-TD)</td><td>Made-to-order for most configurations</td><td>3–6 weeks</td></tr>
<tr><td>Backflow Preventers (WK-RP, WK-DC)</td><td>Stocked — high-demand category</td><td>3–5 business days</td></tr>
</table>

<h2>When a Customer Reports "Out of Stock"</h2>
<ol>
<li>Verify which distributor the customer is ordering from</li>
<li>Check if product is a <strong>stock</strong> vs. <strong>made-to-order</strong> item (see table above)</li>
<li>If stock item: escalate to the rep for that territory to check alternative distributor locations</li>
<li>If made-to-order: confirm factory lead time and set customer expectations</li>
<li>Log the case under <strong>Logistics &amp; Shipping</strong> subject with the distributor name in the notes</li>
</ol>

<h2>Rep Territory Assignment</h2>
<p>Cases are routed to reps based on customer type and territory. See the article <em>"Routing Cases to Reps: Customer Type &amp; Territory Assignment"</em> for routing logic details.</p>
"@
    }

    @{
        title       = "Pricing, Quotes and Distributor Discount Tiers"
        description = "How Zurn's tier-based pricing works through distribution, including discount schedules and quote processes."
        keywords    = "pricing, quotes, discount, tier, distributor, multiplier, Zurn, price list"
        subjectKey  = "Pricing & Quotes (Zurn)"
        content     = @"
<h2>Overview</h2>
<p>Zurn uses a <strong>tier-based pricing model</strong> that flows through the distribution channel. Customer tier (1–4) determines discount level, SLA priority, and routing behavior.</p>

<h2>Customer Tier Structure</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Tier</th><th>Customer Profile</th><th>Discount Level</th><th>SLA Priority</th></tr>
<tr style="background:#e8f4e8"><td><strong>Tier 1</strong></td><td>National accounts, strategic distributors (Ferguson national, HD Supply enterprise)</td><td>Highest — negotiated contract pricing</td><td>Highest — priority queue routing</td></tr>
<tr><td><strong>Tier 2</strong></td><td>Regional distributors, large contractors</td><td>Standard distributor discount</td><td>High</td></tr>
<tr><td><strong>Tier 3</strong></td><td>Local distributors, mid-size contractors</td><td>Published price list</td><td>Standard</td></tr>
<tr><td><strong>Tier 4</strong></td><td>Small accounts, one-time buyers</td><td>List price</td><td>Standard</td></tr>
</table>

<h2>How Pricing Flows Through Distribution</h2>
<ol>
<li><strong>Zurn publishes list prices</strong> — Base pricing for all products (see D365 Price Lists)</li>
<li><strong>Distributor receives tier-based discount</strong> — Applied as a multiplier off list price based on their agreement</li>
<li><strong>Distributor sets sell price</strong> — Marks up from their cost to the end user</li>
<li><strong>End user never sees Zurn's distributor cost</strong> — Pricing is channel-protected</li>
</ol>

<h2>Quote Process</h2>
<p>When a customer requests a quote:</p>
<ul>
<li><strong>Distributor customers:</strong> Quotes are generated by the distributor based on their tier pricing. Zurn provides support pricing via the rep.</li>
<li><strong>End users:</strong> Should be directed to their local distributor. Zurn does not quote end users directly.</li>
<li><strong>Project/spec pricing:</strong> For large commercial projects, the rep works with the distributor to provide project-specific pricing through Zurn's bid desk.</li>
</ul>

<h2>When to Create a Pricing Case</h2>
<p>Create a case under <strong>Pricing &amp; Quotes</strong> when:</p>
<ul>
<li>A distributor disputes their tier assignment or discount level</li>
<li>A project quote requires Zurn factory involvement</li>
<li>Pricing discrepancies between the published price list and what the distributor received</li>
<li>A customer requests a tier upgrade based on volume commitment</li>
</ul>
"@
    }

    # ═══════════════════════════════════════════
    # 2. TECHNICAL SUPPORT & TROUBLESHOOTING (5 articles)
    # ═══════════════════════════════════════════

    @{
        title       = "Troubleshooting Zurn AquaVantage and E-Z Flush Valve Issues"
        description = "Common troubleshooting steps for Zurn AquaVantage (ZN-AV-1001), E-Z Flush (ZN-EZ-1002), and Urinal Flush Valve (ZN-UR-1003) products."
        keywords    = "flush valve, AquaVantage, E-Z Flush, ZN-AV-1001, ZN-EZ-1002, ZN-UR-1003, troubleshooting, sensor, urinal"
        subjectKey  = "Technical Support (Zurn)"
        content     = @"
<h2>Applicable Products</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Product #</th><th>Name</th><th>Key Specs</th></tr>
<tr><td>ZN-AV-1001</td><td>Zurn AquaVantage AV Flush Valve</td><td>1.28 GPF, sensor-operated, ADA compliant</td></tr>
<tr><td>ZN-EZ-1002</td><td>Zurn AquaSense E-Z Flush Valve</td><td>Retrofit sensor kit for manual flush valves</td></tr>
<tr><td>ZN-UR-1003</td><td>Zurn ZER6000AV Urinal Flush Valve</td><td>0.5 GPF, sensor-operated, chrome finish</td></tr>
</table>

<h2>Common Issues &amp; Resolution Steps</h2>

<h3>1. Valve Does Not Flush (No Sensor Response)</h3>
<ul>
<li><strong>Check batteries</strong> — Replace with fresh AA lithium batteries. Alkaline batteries may fail in cold environments.</li>
<li><strong>Clean sensor eye</strong> — Wipe the infrared sensor window with a soft cloth. Build-up from hard water or cleaning chemicals can block the sensor.</li>
<li><strong>Verify wiring (hardwired models)</strong> — Ensure 24VAC transformer is powered and connections are secure.</li>
<li><strong>Reset the sensor</strong> — Remove batteries for 30 seconds, reinstall. The sensor recalibrates on power-up.</li>
</ul>

<h3>2. Valve Flushes Continuously (Phantom Flush)</h3>
<ul>
<li><strong>Sensor range</strong> — Reflective surfaces (mirrors, chrome fixtures) within 24 inches can trigger false readings. Adjust sensor range if adjustable.</li>
<li><strong>Diaphragm wear</strong> — A worn diaphragm in the valve body can cause continuous flow. Replace the diaphragm kit (order through distributor).</li>
<li><strong>Water pressure</strong> — Verify incoming pressure is between 20–80 PSI. Pressure outside this range causes erratic operation.</li>
</ul>

<h3>3. Low Flush Volume / Weak Flush</h3>
<ul>
<li><strong>Check the control stop</strong> — Ensure it is fully open.</li>
<li><strong>Inspect the diaphragm</strong> — Debris or mineral build-up restricts flow. Clean or replace.</li>
<li><strong>Verify GPF setting</strong> — AquaVantage is factory set to 1.28 GPF. Confirm the bypass screw has not been adjusted.</li>
</ul>

<h3>4. E-Z Flush Retrofit Not Activating</h3>
<ul>
<li>Confirm the retrofit adapter plate is compatible with the existing valve body</li>
<li>Check that the manual override button functions — if manual works but sensor doesn't, replace the sensor module</li>
<li>Verify the mounting distance from the wall matches installation specs (sensor too close = false triggers)</li>
</ul>

<h2>When to Escalate</h2>
<p>If basic troubleshooting doesn't resolve the issue:</p>
<ul>
<li>Create a case under <strong>Technical Support</strong> subject</li>
<li>For distributor customers: coordinate an RMA through their distributor (Ferguson, HD Supply, etc.)</li>
<li>For warranty claims: see <em>"Zurn Warranty Policy &amp; RMA Process"</em></li>
</ul>
"@
    }

    @{
        title       = "Zurn AquaSense Sensor Faucet: Installation and Troubleshooting"
        description = "Installation guidance and troubleshooting for Zurn AquaSense (ZN-SF-2001) and AquaSpec (ZN-AS-2002) sensor faucets."
        keywords    = "sensor faucet, AquaSense, AquaSpec, ZN-SF-2001, ZN-AS-2002, installation, troubleshooting, faucet"
        subjectKey  = "Technical Support (Zurn)"
        content     = @"
<h2>Applicable Products</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Product #</th><th>Name</th><th>Key Specs</th></tr>
<tr><td>ZN-SF-2001</td><td>Zurn AquaSense Sensor Faucet</td><td>Battery-powered, below-deck mixing valve</td></tr>
<tr><td>ZN-AS-2002</td><td>Zurn Z86300 AquaSpec Faucet</td><td>Commercial centerset, 2.2 GPM aerator</td></tr>
</table>

<h2>Installation Quick Reference</h2>
<h3>ZN-SF-2001 AquaSense Sensor Faucet</h3>
<ol>
<li>Mount faucet body through single-hole deck cutout (1-3/8" minimum)</li>
<li>Connect hot and cold supply lines to the below-deck mixing valve</li>
<li>Set desired temperature using the mixing valve adjustment</li>
<li>Install 4 AA batteries in the battery compartment (below deck)</li>
<li>Turn on supply stops — sensor activates automatically after 5 seconds</li>
</ol>

<h3>ZN-AS-2002 AquaSpec Centerset Faucet</h3>
<ol>
<li>Requires 4-inch centerset mounting (two-hole)</li>
<li>Connect supply lines — includes integral check valves</li>
<li>Aerator is pre-installed at 2.2 GPM (swap to 0.5 GPM for water-saving applications)</li>
</ol>

<h2>Troubleshooting</h2>

<h3>Sensor Faucet Won't Activate</h3>
<ul>
<li>Replace batteries (4 AA lithium recommended)</li>
<li>Clean the sensor lens — hard water deposits block IR signal</li>
<li>Check that supply stops are fully open</li>
<li>Verify the solenoid clicks when hand is placed under spout — if no click, solenoid may need replacement</li>
</ul>

<h3>Water Temperature Issues</h3>
<ul>
<li><strong>Too hot:</strong> Adjust the below-deck mixing valve counterclockwise</li>
<li><strong>Too cold:</strong> Adjust clockwise; verify hot supply is active</li>
<li><strong>Fluctuating:</strong> Check for cross-connection in supply lines; verify check valves are functioning</li>
</ul>

<h3>Low Flow</h3>
<ul>
<li>Remove and clean the aerator — debris accumulation is the #1 cause</li>
<li>Check the inlet strainers on the supply connections</li>
<li>Verify supply pressure is adequate (minimum 20 PSI)</li>
</ul>

<h2>Distributor Support</h2>
<p>For replacement parts or warranty claims, the end user should work through their distributor. Zurn customer service can assist distributors with:</p>
<ul>
<li>Parts identification and cross-referencing</li>
<li>Warranty validation (see <em>"Zurn Warranty Policy &amp; RMA Process"</em>)</li>
<li>Technical escalation for unusual installation scenarios</li>
</ul>
"@
    }

    @{
        title       = "Wilkins Backflow Preventer Maintenance and Testing Guide"
        description = "Maintenance, annual testing requirements, and troubleshooting for Wilkins 975XL RPZ and 350XL Double Check backflow preventers."
        keywords    = "backflow, Wilkins, RPZ, double check, 975XL, 350XL, WK-RP-4001, WK-DC-4002, testing, maintenance, preventer"
        subjectKey  = "Backflow / Wilkins"
        content     = @"
<h2>Applicable Products</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Product #</th><th>Name</th><th>Application</th></tr>
<tr><td>WK-RP-4001</td><td>Wilkins 975XL RPZ Assembly</td><td>High-hazard backflow prevention (chemical plants, irrigation with injectors, boiler feeds)</td></tr>
<tr><td>WK-DC-4002</td><td>Wilkins 350XL Double Check Valve</td><td>Low-to-moderate hazard (fire sprinkler, commercial potable water)</td></tr>
</table>

<h2>Annual Testing Requirements</h2>
<p><strong>Most jurisdictions require annual testing of backflow prevention assemblies.</strong> This is typically performed by a certified backflow tester, not the end user.</p>

<h3>Testing Process</h3>
<ol>
<li><strong>Schedule test</strong> — Coordinate through the local water authority or a certified backflow testing company</li>
<li><strong>Certified tester performs test</strong> — Uses differential pressure gauge to verify check valves and relief valve (RPZ) hold within spec</li>
<li><strong>Test report filed</strong> — Results submitted to local water authority; copy should be retained by building owner</li>
<li><strong>Failed test</strong> — Repair or replacement parts ordered through distributor; re-test required after repair</li>
</ol>

<h2>Distributor &amp; Rep Network Role</h2>
<p>Backflow is a high-touch category where the <strong>rep network</strong> plays a critical role:</p>
<ul>
<li>Reps maintain relationships with <strong>certified testing companies</strong> in their territory</li>
<li>Distributors stock <strong>repair kits</strong> for common models (975XL rubber repair kit, 350XL check module)</li>
<li>For municipalities and water authorities, reps coordinate <strong>large-quantity spec orders</strong> through Core &amp; Main and Ferguson waterworks divisions</li>
</ul>

<h2>Common Issues</h2>

<h3>Relief Valve Discharge (RPZ - 975XL)</h3>
<ul>
<li><strong>Continuous dripping:</strong> Normal if &lt; 1 cup/day (thermal expansion). Excessive flow indicates fouled check valve — clean or replace first check module.</li>
<li><strong>Steady flow from relief port:</strong> First check has failed. Shut down assembly, replace first check rubber kit.</li>
</ul>

<h3>Pressure Drop Across Assembly</h3>
<ul>
<li>Normal drop: 8–12 PSI for 975XL RPZ</li>
<li>Excessive drop: Check for debris in check modules; clean strainer screens</li>
</ul>

<h3>Freeze Damage</h3>
<ul>
<li>Outdoor-installed assemblies <strong>must be winterized</strong> in freeze-prone climates (see <em>"Winterization Procedures for Zurn Plumbing Products"</em>)</li>
<li>Cracked bodies are not repairable — full assembly replacement required</li>
</ul>

<h2>Case Handling</h2>
<p>Backflow cases should be categorized under <strong>Backflow / Wilkins</strong> subject and routed to the <strong>Zurn Phone - Backflow/Wilkins</strong> queue. For warranty claims on assemblies less than 5 years old, initiate the RMA process through the distributor.</p>
"@
    }

    @{
        title       = "Winterization Procedures for Zurn Plumbing Products"
        description = "Seasonal winterization guide for Zurn sensor faucets, floor drains, and Wilkins backflow preventers to prevent freeze damage."
        keywords    = "winterization, freeze, winter, cold weather, frost, drain, backflow, sensor faucet, seasonal"
        subjectKey  = "Technical Support (Zurn)"
        content     = @"
<h2>Overview</h2>
<p>Freeze damage is <strong>not covered under standard warranty</strong>. Proper winterization prevents costly replacements. This guide covers the most freeze-susceptible Zurn products.</p>

<h2>Products Requiring Winterization</h2>

<h3>Wilkins Backflow Preventers (WK-RP-4001, WK-DC-4002)</h3>
<p><strong>Risk Level: HIGH</strong> — Cast body assemblies crack when water freezes inside.</p>
<ol>
<li>Shut off upstream supply valve</li>
<li>Open test cocks to drain water from the assembly body</li>
<li>For RPZ assemblies: ensure relief valve port is clear and draining</li>
<li>If installed outdoors: install an insulated enclosure rated for your climate zone</li>
<li>For seasonal irrigation systems: have a certified tester blow out the line with compressed air before closing</li>
</ol>

<h3>Sensor Faucets (ZN-SF-2001)</h3>
<p><strong>Risk Level: MODERATE</strong> — Below-deck components and solenoid valves are vulnerable in unheated spaces.</p>
<ul>
<li>If building will be unoccupied and unheated: shut off supply and open faucet to drain residual water</li>
<li>Remove batteries to prevent the solenoid from cycling during freeze/thaw</li>
<li>Insulate exposed supply lines beneath the deck</li>
</ul>

<h3>Floor Drains (ZN-FD-3001)</h3>
<p><strong>Risk Level: LOW-MODERATE</strong> — Trap seal can freeze in unheated buildings.</p>
<ul>
<li>Add RV antifreeze (propylene glycol) to the trap to prevent freeze-up</li>
<li>Do NOT use automotive antifreeze (ethylene glycol) — toxic and not code-compliant</li>
<li>Inspect trap primers if installed — a failed primer leaves the trap dry and vulnerable</li>
</ul>

<h2>Seasonal Advisory Program</h2>
<p>Zurn's rep network sends <strong>seasonal winterization advisories</strong> to distributors each fall (typically October). Distributors should share these with their commercial customers. Key messaging:</p>
<ul>
<li>Freeze damage claims are denied under warranty</li>
<li>Replacement assemblies ordered through distribution have standard lead times (see <em>"Distribution Network Sourcing"</em> article)</li>
<li>Preventive winterization is far less expensive than emergency replacement</li>
</ul>

<h2>Case Handling</h2>
<p>For freeze-damage reports: create a case under <strong>Technical Support</strong>, note that the issue is winterization-related, and check the product's install date against warranty coverage. Direct the customer to their distributor for replacement orders.</p>
"@
    }

    @{
        title       = "Zurn Floor, Roof and Trench Drain Troubleshooting"
        description = "Troubleshooting guide for Zurn Z415 Floor Drain, Z100 Roof Drain, and Z886 Trench Drain systems."
        keywords    = "drain, floor drain, roof drain, trench drain, Z415, Z100, Z886, ZN-FD-3001, ZN-RD-3003, ZN-TD-3002, clogged, drainage"
        subjectKey  = "Drainage (Zurn)"
        content     = @"
<h2>Applicable Products</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Product #</th><th>Name</th><th>Application</th></tr>
<tr><td>ZN-FD-3001</td><td>Zurn Z415 Floor Drain</td><td>Commercial/industrial floor drainage — 5" round nickel bronze strainer</td></tr>
<tr><td>ZN-RD-3003</td><td>Zurn Z100 Roof Drain</td><td>15" cast iron roof drain, low-profile dome</td></tr>
<tr><td>ZN-TD-3002</td><td>Zurn Z886 Trench Drain</td><td>Linear trench drain, slotted grate, 8" wide</td></tr>
</table>

<h2>Common Issues</h2>

<h3>Floor Drain (Z415) — Slow Drainage or Odor</h3>
<ul>
<li><strong>Clogged strainer:</strong> Remove the nickel bronze strainer and clear debris. In commercial kitchens, grease build-up is the primary cause.</li>
<li><strong>Sewer odor:</strong> The P-trap has dried out. Pour water into the drain to re-establish the trap seal. Install a trap primer for drains that don't receive regular flow.</li>
<li><strong>Inadequate slope:</strong> Floor drain requires minimum 1/8" per foot slope toward the drain. This is a construction issue, not a product defect.</li>
</ul>

<h3>Roof Drain (Z100) — Ponding Water</h3>
<ul>
<li><strong>Dome clogged:</strong> Clear leaves and debris from the low-profile dome. Seasonal maintenance is critical.</li>
<li><strong>Undersized drain:</strong> Verify drain capacity matches roof area. Z100 serves approximately 4,500 sq ft at 4"/hr rainfall.</li>
<li><strong>Insulation interference:</strong> When roof is re-insulated, verify the drain extension collar is properly sized to match new roof height.</li>
</ul>

<h3>Trench Drain (Z886) — Grate Issues</h3>
<ul>
<li><strong>Grate rocking/noise:</strong> Check that the slotted grate is fully seated in the channel frame. Worn locking tabs may need replacement.</li>
<li><strong>Load rating mismatch:</strong> Verify the grate load class matches the application (pedestrian vs. vehicular). Using a light-duty grate in a drive lane will cause premature failure.</li>
<li><strong>Channel alignment:</strong> For multi-section runs, ensure sections are properly connected and sealed at joints.</li>
</ul>

<h2>Spec Rep Involvement</h2>
<p>Drainage products for commercial construction are typically <strong>specified by engineers</strong> and ordered through the Zurn rep network. When a case involves a new construction project or a product sizing question, route to the assigned spec rep via the <strong>Zurn Phone - Tech Support</strong> queue.</p>

<h2>Replacement Parts</h2>
<p>Strainers, domes, and grate sections are available through distribution. Provide the Zurn catalog number (Z415, Z100, Z886) and the specific accessory part number to the distributor for accurate fulfillment.</p>
"@
    }

    # ═══════════════════════════════════════════
    # 3. CASE INTAKE & CHANNELS (2 articles)
    # ═══════════════════════════════════════════

    @{
        title       = "Case Creation Guide: Phone, Email and Web Form Intake"
        description = "How cases are created in Zurn customer service via phone, email, and web form channels, including distributor vs. end-user handling."
        keywords    = "case creation, intake, phone, email, web form, channels, case management, ticket"
        subjectKey  = "General"
        content     = @"
<h2>Overview</h2>
<p>Every customer interaction — whether from a distributor, rep, or end user — should result in a case record in D365. Cases provide tracking, SLA enforcement, and visibility to management.</p>

<h2>Intake Channels</h2>

<h3>Phone</h3>
<ul>
<li>Agent receives call → creates a case manually or via the productivity pane</li>
<li>System looks up the caller's account to determine <strong>customer tier</strong> (via ERP/AIP integration)</li>
<li>Tier determines priority and queue routing</li>
<li>Phone cases route to brand-specific phone queues:
    <ul>
    <li><strong>Zurn Phone - General</strong>, <strong>Zurn Phone - Tech Support</strong>, <strong>Zurn Phone - Backflow/Wilkins</strong>, <strong>Zurn Phone - Tier 1</strong></li>
    </ul>
</li>
<li><strong>Agent logs the call</strong> — Creates a Phone Call activity linked to the case with notes and duration</li>
</ul>

<h3>Email</h3>
<ul>
<li>Emails sent to monitored mailboxes automatically create cases</li>
<li>Cases route to the corresponding email queue:
    <ul>
    <li><strong>Zurn General Support</strong>, <strong>Elkay General Support</strong></li>
    <li><strong>Elkay Orders</strong>, <strong>Elkay Hydration Support</strong>, <strong>Elkay Sinks &amp; Fixtures</strong></li>
    </ul>
</li>
<li>SLA timer starts when the email is received (not when an agent picks it up)</li>
</ul>

<h3>Web Form</h3>
<ul>
<li>Customer submits a request through the Zurn website contact form</li>
<li>Submission creates a case via Power Automate flow or portal integration</li>
<li>Web form cases default to <strong>Zurn General Support</strong> queue unless the form captures enough data for specialty routing</li>
</ul>

<h2>Distributor vs. End-User Cases</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Aspect</th><th>Distributor Case</th><th>End-User Case</th></tr>
<tr><td>Account lookup</td><td>Matched to distributor account (Ferguson, HD Supply, etc.)</td><td>Matched to end-user account (school district, municipality, etc.)</td></tr>
<tr><td>Priority</td><td>Tier-based from ERP — typically Tier 1 or 2</td><td>Typically Tier 3 or 4 unless flagged by hot word</td></tr>
<tr><td>Resolution path</td><td>Direct support — Zurn acts as the manufacturer partner</td><td>Often redirected through distribution for orders/RMA</td></tr>
<tr><td>Contact</td><td>Distributor buyer or branch manager</td><td>Facility manager, contractor, or homeowner</td></tr>
</table>

<h2>Hot-Word Priority Escalation</h2>
<p>Regardless of tier, cases containing these words in the subject or description are automatically escalated to priority 10,000:</p>
<p style="background:#fff3cd; padding:10px; border:1px solid #ffc107"><strong>Urgent</strong> &bull; <strong>Next Day Air</strong> &bull; <strong>Emergency</strong> &bull; <strong>Recall</strong> &bull; <strong>Safety</strong> &bull; <strong>Legal</strong></p>
"@
    }

    @{
        title       = "Request Prioritization: Tier Assignment and Hot-Word Escalation"
        description = "How cases are prioritized using customer tiers (1-4), ERP-based lookup, and hot-word detection for automatic escalation."
        keywords    = "priority, tier, hot word, escalation, urgent, routing, ERP, AIP, customer tier"
        subjectKey  = "General"
        content     = @"
<h2>Overview</h2>
<p>Zurn uses a multi-factor prioritization system that combines <strong>customer tier</strong>, <strong>case content analysis</strong>, and <strong>channel-based routing</strong> to ensure the most important cases get attention first.</p>

<h2>Tier Assignment</h2>
<p>Customer tier is determined by an ERP lookup (AIP system) when a case is created:</p>

<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Tier</th><th>Profile</th><th>Case Priority</th><th>Queue Routing</th></tr>
<tr style="background:#d4edda"><td><strong>1</strong></td><td>National strategic accounts (Ferguson enterprise, HD Supply national)</td><td>Critical</td><td>Zurn Phone - Tier 1 (dedicated)</td></tr>
<tr><td><strong>2</strong></td><td>Regional distributors, large mechanical contractors</td><td>High</td><td>Brand-specific tech or general queue</td></tr>
<tr><td><strong>3</strong></td><td>Local distributors, mid-size accounts</td><td>Normal</td><td>Brand-specific general queue</td></tr>
<tr><td><strong>4</strong></td><td>Small accounts, one-off inquiries, homeowners</td><td>Low</td><td>General support queue</td></tr>
</table>

<h2>Hot-Word Detection</h2>
<p>When a case is created or updated, the system scans the <strong>title</strong> and <strong>description</strong> fields for hot words. If detected, the case priority is automatically boosted to <strong>10,000</strong> regardless of tier.</p>

<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#dc3545; color:white"><th>Hot Word</th><th>Typical Scenario</th></tr>
<tr><td><strong>Urgent</strong></td><td>Customer explicitly flags a time-sensitive need</td></tr>
<tr><td><strong>Next Day Air</strong></td><td>Expedited shipping request — often from a contractor with a job deadline</td></tr>
<tr><td><strong>Emergency</strong></td><td>Active water damage, safety incident, or system failure</td></tr>
<tr><td><strong>Recall</strong></td><td>Product recall inquiry or affected-product report</td></tr>
<tr><td><strong>Safety</strong></td><td>Safety-related product concern — overheating, contamination risk</td></tr>
<tr><td><strong>Legal</strong></td><td>Legal inquiry or threat — immediately escalate to management</td></tr>
</table>

<h2>Specialty Routing</h2>
<p>Beyond tier and hot words, cases may be routed based on:</p>
<ul>
<li><strong>Email domain:</strong> Emails from known distributor domains route to the distributor's assigned queue</li>
<li><strong>Phone number:</strong> Recognized caller IDs from Tier 1 accounts route to Zurn Phone - Tier 1</li>
<li><strong>Account type:</strong>
    <ul>
    <li><strong>House accounts</strong> — Direct Zurn-managed, route to senior reps</li>
    <li><strong>Specialty accounts</strong> — Niche product focus (backflow, drainage), route to specialty queues</li>
    <li><strong>International</strong> — Route to international support team</li>
    </ul>
</li>
</ul>

<h2>SLA Impact</h2>
<p>Priority and tier directly affect SLA enforcement:</p>
<ul>
<li><strong>First Response:</strong> 4 business hours (all tiers currently — Tier 1 may receive expedited handling)</li>
<li><strong>Resolution:</strong> 8 business hours target</li>
<li>Hot-word cases are monitored on a <strong>separate dashboard</strong> with real-time alerts to supervisors</li>
</ul>
"@
    }

    # ═══════════════════════════════════════════
    # 4. WARRANTY & RETURNS (2 articles)
    # ═══════════════════════════════════════════

    @{
        title       = "Zurn Warranty Policy and RMA Process"
        description = "Zurn standard warranty terms and the Return Merchandise Authorization process through distribution partners."
        keywords    = "warranty, RMA, return, replacement, claim, defect, Zurn, distributor"
        subjectKey  = "Warranty & Returns (Zurn)"
        content     = @"
<h2>Standard Warranty Coverage</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Product Category</th><th>Warranty Period</th><th>Coverage</th></tr>
<tr><td>Flush Valves (AquaVantage, E-Z Flush, Urinal)</td><td>3 years</td><td>Manufacturing defects in materials and workmanship</td></tr>
<tr><td>Sensor Faucets (AquaSense, AquaSpec)</td><td>3 years (electronics: 5 years)</td><td>Sensor module, solenoid, body</td></tr>
<tr><td>Drains (Floor, Roof, Trench)</td><td>1 year</td><td>Casting defects; does not cover installation errors</td></tr>
<tr><td>Backflow Preventers (Wilkins 975XL, 350XL)</td><td>5 years</td><td>Body and check modules; rubber parts are consumable</td></tr>
</table>

<h2>What Is NOT Covered</h2>
<ul>
<li>Freeze damage (see <em>"Winterization Procedures"</em> article)</li>
<li>Normal wear items: batteries, diaphragms, rubber seals, aerators</li>
<li>Damage from misuse, improper installation, or unauthorized modification</li>
<li>Product used outside its rated application (e.g., using a residential product in a commercial high-rise)</li>
</ul>

<h2>RMA Process (Through Distribution)</h2>
<p>Warranty claims are processed <strong>through the original distributor of purchase</strong>:</p>
<ol>
<li><strong>Customer contacts Zurn CS</strong> — Agent creates a case under <strong>Warranty &amp; Returns</strong> subject</li>
<li><strong>Agent validates warranty</strong> — Checks install date, product model, and purchase documentation</li>
<li><strong>RMA issued to distributor</strong> — Zurn issues an RMA number to the distributor (Ferguson, HD Supply, etc.), not directly to the end user</li>
<li><strong>Distributor handles the exchange</strong> — End user returns defective unit to the distributor; distributor ships replacement from stock</li>
<li><strong>Distributor returns to Zurn</strong> — Failed unit shipped back to Zurn under the RMA for analysis</li>
<li><strong>Credit issued</strong> — Zurn credits the distributor's account after inspection</li>
</ol>

<h2>Why RMA Goes Through Distribution</h2>
<p>This process preserves the manufacturer → distributor → end user channel:</p>
<ul>
<li>Distributor maintains the customer relationship</li>
<li>Distributor can provide immediate replacement from local stock (faster than factory ship)</li>
<li>Zurn gets the failed unit back for quality analysis</li>
<li>Financial credit flows through the existing commercial terms</li>
</ul>

<h2>Escalation</h2>
<p>If the distributor disputes a warranty denial, or if the customer insists on direct Zurn handling, escalate to the <strong>Quality / Recall</strong> queue with a supervisor notification.</p>
"@
    }

    @{
        title       = "Quality and Recall Notification Procedures"
        description = "How Zurn handles product quality issues and recall communications through the distribution channel."
        keywords    = "recall, quality, safety, notification, product recall, CPSC, distributor communication"
        subjectKey  = "Quality / Recall (Zurn)"
        content     = @"
<h2>Overview</h2>
<p>Product quality and recall situations require coordinated communication across the entire distribution chain: Zurn → Reps → Distributors → End Users.</p>

<h2>Quality Issue Classification</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#dc3545; color:white"><th>Level</th><th>Description</th><th>Action</th></tr>
<tr><td><strong>Level 1 — Safety Recall</strong></td><td>CPSC-mandated recall; immediate risk to health/safety</td><td>Mandatory customer notification; product stop-sale; free replacement</td></tr>
<tr><td><strong>Level 2 — Voluntary Recall</strong></td><td>Zurn-initiated; product may fail prematurely but no immediate safety risk</td><td>Customer notification; replacement or repair offered</td></tr>
<tr><td><strong>Level 3 — Quality Advisory</strong></td><td>Known issue affecting performance; limited scope</td><td>Advisory bulletin to distributors; extended warranty on affected lot</td></tr>
<tr><td><strong>Level 4 — Internal Monitor</strong></td><td>Elevated warranty return rate; investigation underway</td><td>No external communication; Zurn quality team monitors</td></tr>
</table>

<h2>Recall Communication Chain</h2>
<ol>
<li><strong>Zurn Quality Team</strong> determines recall scope (affected product numbers, serial/lot ranges, date codes)</li>
<li><strong>Zurn notifies reps</strong> — Rep agencies receive the recall bulletin with talking points and affected customer lists</li>
<li><strong>Reps notify distributors</strong> — Distributors pull affected stock, flag affected inventory, and prepare for customer inquiries</li>
<li><strong>Distributors notify end users</strong> — Using purchase records to identify customers who bought affected product</li>
<li><strong>Zurn CS handles inbound</strong> — Cases tagged <strong>Quality / Recall</strong>, hot-word detection triggers priority escalation</li>
</ol>

<h2>Case Handling for Recall Inquiries</h2>
<ul>
<li>Any case mentioning <strong>"recall"</strong> or <strong>"safety"</strong> is automatically escalated (hot-word detection → priority 10,000)</li>
<li>Agent should reference the current active recall list (maintained by Quality team)</li>
<li>Verify if the customer's product is in the affected lot/date range</li>
<li>If affected: initiate RMA through distributor with <strong>no-charge replacement</strong> authorization</li>
<li>If not affected: reassure customer, document the inquiry, and close with resolution notes</li>
</ul>

<h2>Internal Tracking</h2>
<p>All recall-related cases must be tagged with:</p>
<ul>
<li>Subject: <strong>Quality / Recall</strong></li>
<li>Product: the specific affected product</li>
<li>Case notes: lot number, date code, serial number if available</li>
<li>Resolution: state whether product was confirmed affected or not</li>
</ul>
"@
    }

    # ═══════════════════════════════════════════
    # 5. REP & DISTRIBUTION NETWORK (2 articles)
    # ═══════════════════════════════════════════

    @{
        title       = "Rep Network Support: Ensuring Right Stock in Right Place"
        description = "How Zurn's manufacturer rep network works with distributors to manage inventory, stock positioning, and customer support."
        keywords    = "rep network, manufacturer rep, distributor, inventory, stock, territory, channel, Ferguson, HD Supply"
        subjectKey  = "Logistics & Shipping (Zurn)"
        content     = @"
<h2>Overview</h2>
<p>Zurn's manufacturer rep network is the critical link between the factory and the distribution channel. Reps don't take orders directly — they ensure the <strong>right products are stocked at the right distributors</strong> to serve end-user demand in their territory.</p>

<h2>Rep Network Responsibilities</h2>

<h3>Inventory &amp; Stock Management</h3>
<ul>
<li><strong>Stock reviews:</strong> Quarterly meetings with each distributor branch to review sales velocity, stock levels, and upcoming project needs</li>
<li><strong>New product introductions:</strong> When Zurn launches a new product, reps work with distributors to establish initial stocking levels</li>
<li><strong>Seasonal adjustments:</strong> Increase backflow preventer stock before spring testing season; winterization product promotions in fall</li>
<li><strong>Dead stock management:</strong> Identify slow-moving inventory and coordinate returns or transfers between branches</li>
</ul>

<h3>Customer Support</h3>
<ul>
<li><strong>Technical training:</strong> Reps provide product training to distributor counter staff and outside sales teams</li>
<li><strong>End-user visits:</strong> For Tier 1 and 2 accounts, reps make joint calls with the distributor to support key relationships</li>
<li><strong>Specification support:</strong> Rep engineers assist architects/specifiers in selecting the right Zurn products for construction projects</li>
</ul>

<h3>Case Routing to Reps</h3>
<p>Cases are assigned to reps based on:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Factor</th><th>Routing Logic</th></tr>
<tr><td>Territory / geography</td><td>Customer zip code → mapped rep territory</td></tr>
<tr><td>Account type</td><td>House accounts → direct Zurn team; Rep accounts → assigned rep agency</td></tr>
<tr><td>Product specialty</td><td>Backflow cases → reps with Wilkins certification; Drainage → reps with civil/site-work focus</td></tr>
</table>

<h2>Distributor Relationships</h2>
<p>Key distributors and their role in the Zurn channel:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#f0f0f0"><th>Distributor</th><th>Channel Strength</th><th>Rep Interaction</th></tr>
<tr><td><strong>Ferguson Enterprises</strong></td><td>Largest national plumbing distributor — full Zurn catalog</td><td>Regional reps coordinate with local Ferguson branches on stock and promotions</td></tr>
<tr><td><strong>HD Supply</strong></td><td>MRO focus — flush valves and faucets for facility maintenance</td><td>Reps manage national account pricing and branch-level training</td></tr>
<tr><td><strong>Winsupply Inc.</strong></td><td>Locally-owned branches — strong in residential/light commercial</td><td>Reps work branch-by-branch due to independent ownership model</td></tr>
<tr><td><strong>Core &amp; Main</strong></td><td>Waterworks — backflow and municipal infrastructure</td><td>Reps coordinate large municipal bids and spec-driven large orders</td></tr>
</table>

<h2>When CS Agents Need Rep Involvement</h2>
<p>Escalate to the rep when:</p>
<ul>
<li>A distributor reports chronic out-of-stock on a stocked item</li>
<li>A Tier 1 account has a complex project requiring factory coordination</li>
<li>An end user needs product selection guidance beyond standard troubleshooting</li>
<li>A new distributor branch opens in the territory and needs initial stocking recommendations</li>
</ul>
"@
    }

    @{
        title       = "Routing Cases to Reps: Customer Type and Territory Assignment"
        description = "How cases are routed based on customer type (House, Specialty, International), territory mapping, and rep assignment rules."
        keywords    = "routing, rep assignment, territory, house account, specialty, international, customer type, queue"
        subjectKey  = "General"
        content     = @"
<h2>Overview</h2>
<p>Zurn uses a combination of <strong>account type</strong>, <strong>territory mapping</strong>, and <strong>product specialty</strong> to route cases to the correct rep or internal team. Understanding these routing rules helps CS agents get cases to the right person on the first assignment.</p>

<h2>Account Types &amp; Routing</h2>

<h3>House Accounts</h3>
<p>Accounts managed directly by Zurn's internal sales team (not through a rep agency).</p>
<ul>
<li><strong>Examples:</strong> Large national chains, government contracts, OEM customers</li>
<li><strong>Routing:</strong> Cases route to the <strong>Zurn Phone - Tier 1</strong> or <strong>Zurn General Support</strong> queue and are assigned to the internal account manager</li>
<li><strong>SLA:</strong> Tier 1 treatment — highest priority</li>
</ul>

<h3>Rep-Managed Accounts</h3>
<p>The majority of accounts — managed by independent manufacturer rep agencies in their territory.</p>
<ul>
<li><strong>Examples:</strong> Regional distributors, local contractors, mechanical engineers</li>
<li><strong>Routing:</strong> Cases route to the general or tech queue, then assigned to the rep based on territory zip code</li>
<li><strong>SLA:</strong> Tier 2–4 based on account size and volume</li>
</ul>

<h3>Specialty Accounts</h3>
<p>Accounts with niche product focus requiring specialized knowledge.</p>
<ul>
<li><strong>Examples:</strong> Backflow testing companies, commercial kitchen equipment dealers, architectural specification firms</li>
<li><strong>Routing:</strong> Cases route to specialty queues:
    <ul>
    <li>Backflow → <strong>Zurn Phone - Backflow/Wilkins</strong></li>
    <li>Drainage → <strong>Zurn Phone - Tech Support</strong></li>
    </ul>
</li>
</ul>

<h3>International Accounts</h3>
<ul>
<li>Cases from non-US accounts route to the international support queue</li>
<li>May involve export compliance, tariff questions, or product certification differences</li>
<li>Rep network does not typically cover international — handled by Zurn's internal international team</li>
</ul>

<h2>Queue Summary</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>Queue</th><th>Purpose</th><th>Account Types Served</th></tr>
<tr><td>Zurn Phone - Tier 1</td><td>Dedicated line for strategic accounts</td><td>House, Tier 1 distributors</td></tr>
<tr><td>Zurn Phone - General</td><td>General Zurn inquiries</td><td>All Zurn accounts</td></tr>
<tr><td>Zurn Phone - Tech Support</td><td>Technical and installation questions</td><td>All — transferred from general when needed</td></tr>
<tr><td>Zurn Phone - Backflow/Wilkins</td><td>Backflow preventer specialist queue</td><td>Specialty, municipal, water authority</td></tr>
<tr><td>Zurn General Support (email)</td><td>Email inquiries</td><td>All Zurn accounts</td></tr>
<tr><td>Elkay General Support</td><td>Elkay brand inquiries</td><td>Elkay accounts, dual-brand distributors</td></tr>
<tr><td>Elkay Orders / Hydration / Sinks</td><td>Product-specific Elkay queues</td><td>Elkay-focused distributors and end users</td></tr>
</table>

<h2>Daily Operations</h2>
<ul>
<li><strong>Queue management:</strong> Supervisors review unassigned queue items at start of day and mid-day</li>
<li><strong>Dashboard visibility:</strong> Real-time dashboards show queue depth, average wait time, and SLA compliance by queue</li>
<li><strong>Workforce management:</strong> Agent schedules align with queue volume patterns — heavier staffing M–W, lighter Th–F</li>
</ul>
"@
    }

    # ═══════════════════════════════════════════
    # 6. SLA & OPERATIONS (1 article)
    # ═══════════════════════════════════════════

    @{
        title       = "SLA Targets and Response Time Standards"
        description = "Zurn Elkay Customer Service SLA targets, response time tracking, and operational standards for case handling."
        keywords    = "SLA, response time, first response, resolution, business hours, KPI, dashboard, elapsed time"
        subjectKey  = "General"
        content     = @"
<h2>Overview</h2>
<p>Zurn Elkay Customer Service operates under defined Service Level Agreement (SLA) targets to ensure consistent, timely support across all channels and customer tiers.</p>

<h2>SLA Targets</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
<tr style="background:#003B71; color:white"><th>KPI</th><th>Target</th><th>Measurement</th></tr>
<tr><td><strong>First Response Time</strong></td><td>4 business hours</td><td>Time from case creation to first meaningful response (email reply, phone callback, or case note)</td></tr>
<tr><td><strong>Case Resolution Time</strong></td><td>8 business hours</td><td>Total elapsed business hours from case creation to resolution</td></tr>
</table>

<h2>Business Hours</h2>
<p>SLA timers run during business hours only:</p>
<ul>
<li><strong>Monday – Friday:</strong> 8:00 AM – 5:00 PM (local time zone of the handling team)</li>
<li><strong>Excluded:</strong> Weekends and company-observed holidays</li>
<li>Cases created at 4:00 PM Friday have a first response deadline of 11:00 AM Monday</li>
</ul>

<h2>How SLA Is Tracked in D365</h2>
<ol>
<li><strong>SLA timer starts</strong> — Automatically when the case is created</li>
<li><strong>Warning threshold</strong> — At 75% of the target time, a warning indicator appears on the case (yellow)</li>
<li><strong>SLA breach</strong> — If the target time passes without the KPI action, the timer shows red (nearing noncompliant / noncompliant)</li>
<li><strong>Timer pauses</strong> — If the case is placed in a "Waiting" status (e.g., waiting for customer response), the SLA timer pauses</li>
<li><strong>Timer resumes</strong> — When the case returns to active status</li>
</ol>

<h2>Dashboard &amp; Reporting</h2>
<p>Supervisors and managers have access to real-time dashboards showing:</p>
<ul>
<li><strong>SLA Compliance Rate:</strong> % of cases meeting first response and resolution targets</li>
<li><strong>Cases Nearing Breach:</strong> Cases in warning state that need immediate attention</li>
<li><strong>Average Handle Time:</strong> By queue, by agent, by case subject</li>
<li><strong>Queue Depth:</strong> Number of unassigned cases per queue</li>
<li><strong>Volume Trends:</strong> Daily/weekly case creation volume by channel (phone, email, web)</li>
</ul>

<h2>Agent Best Practices</h2>
<ul>
<li><strong>Respond fast, even if you can't resolve:</strong> A quick acknowledgment ("We received your case and are looking into it") satisfies the first response KPI</li>
<li><strong>Set proper status:</strong> If waiting for customer input, change case status to "Waiting" to pause the SLA timer</li>
<li><strong>Log all activities:</strong> Every phone call and email should be logged as an activity on the case — this provides the audit trail for SLA compliance</li>
<li><strong>Use notes:</strong> Add case notes when making progress, even if the case isn't resolved yet — this demonstrates active handling</li>
</ul>
"@
    }

) # end $articles array

# ── Create Articles ──
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating 15 Zurn Knowledge Articles" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$created = 0
$skipped = 0
$failed = 0

foreach ($art in $articles) {
    $title = $art.title
    Write-Host "[$($created + $skipped + $failed + 1)/15] $title" -NoNewline

    # Check if article already exists
    $encTitle = [System.Uri]::EscapeDataString("title eq '$($title.Replace("'","''"))'")
    $check = Invoke-RestMethod -Uri "$base/knowledgearticles?`$select=knowledgearticleid,title,statecode&`$filter=$encTitle" -Headers $headers -UseBasicParsing
    if ($check.value.Count -gt 0) {
        Write-Host " → SKIPPED (already exists)" -ForegroundColor Yellow
        $skipped++
        continue
    }

    # Build the body
    $subjectId = $subjects[$art.subjectKey]
    $body = @{
        title       = $art.title
        description = $art.description
        keywords    = $art.keywords
        content     = $art.content
    }
    if ($subjectId) {
        $body["subjectid@odata.bind"] = "/subjects($subjectId)"
    }

    $json = $body | ConvertTo-Json -Depth 5
    # Fix encoding for PS 5.1
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)

    try {
        $resp = Invoke-RestMethod -Uri "$base/knowledgearticles" -Method Post -Headers $headers -Body $bytes -UseBasicParsing
        Write-Host " → CREATED" -ForegroundColor Green
        $created++
    } catch {
        $err = $_.ErrorDetails.Message
        Write-Host " → FAILED: $err" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Results: Created=$created  Skipped=$skipped  Failed=$failed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── Publish Articles ──
if ($created -gt 0) {
    Write-Host ""
    Write-Host "Publishing newly created articles..." -ForegroundColor Cyan
    
    # Re-query all our articles to get IDs
    $published = 0
    foreach ($art in $articles) {
        $encTitle = [System.Uri]::EscapeDataString("title eq '$($art.title.Replace("'","''"))'")
        $existing = Invoke-RestMethod -Uri "$base/knowledgearticles?`$select=knowledgearticleid,statecode&`$filter=$encTitle" -Headers $headers -UseBasicParsing
        
        foreach ($ka in $existing.value) {
            if ($ka.statecode -eq 0) {
                # Draft → Approved (statecode=1, statuscode=5)
                # Then Approved → Published (statecode=3, statuscode=7)
                try {
                    # Approve
                    $approveBody = @{ statecode = 1; statuscode = 5 } | ConvertTo-Json
                    $approveBytes = [System.Text.Encoding]::UTF8.GetBytes($approveBody)
                    Invoke-RestMethod -Uri "$base/knowledgearticles($($ka.knowledgearticleid))" -Method Patch -Headers $headers -Body $approveBytes -UseBasicParsing | Out-Null
                    
                    # Publish
                    $publishBody = @{ statecode = 3; statuscode = 7 } | ConvertTo-Json
                    $publishBytes = [System.Text.Encoding]::UTF8.GetBytes($publishBody)
                    Invoke-RestMethod -Uri "$base/knowledgearticles($($ka.knowledgearticleid))" -Method Patch -Headers $headers -Body $publishBytes -UseBasicParsing | Out-Null
                    
                    Write-Host "  Published: $($art.title)" -ForegroundColor Green
                    $published++
                } catch {
                    Write-Host "  Publish failed for: $($art.title) - $($_.ErrorDetails.Message)" -ForegroundColor Red
                }
            }
        }
    }
    Write-Host ""
    Write-Host "Published $published articles." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
