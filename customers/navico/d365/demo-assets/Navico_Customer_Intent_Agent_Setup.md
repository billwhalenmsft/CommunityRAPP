# Navico — Customer Intent Agent Setup Guide

> **What it is:** The Customer Intent Agent in D365 Customer Service uses AI to detect what the customer is asking about (their "intent") and surfaces next-best-action guidance, KB articles, and suggested replies to the CSR in real-time.
>
> **Why it matters for Navico:** With 17 brands, 37 CSRs, and a 52/48 split between technical support and warranty/RMA, automatically detecting whether someone is calling about a firmware issue vs. requesting an RMA vs. asking about a product spec dramatically reduces triage time.

---

## Prerequisites

Before configuring the Customer Intent Agent:

- [x] Omnichannel routing enabled (Script 10)
- [x] Classification rules configured (Script 11)
- [x] KB articles published (Provision-NavicoHeroCases.ps1 -Action KnowledgeArticles)
- [x] Cases with timeline data exist (for AI discovery to analyze)
- [ ] Customer Intent Agent feature enabled in D365 Admin Center

---

## Step 1: Enable Customer Intent Agent

1. Go to **Customer Service Admin Center** → **Agent experience** → **Productivity**
2. Find **Customer Intent Agent** → click **Manage**
3. Toggle **Enable Customer Intent Agent** = **On**
4. Under **Manage intent discovery setup**:
   - Select data sources: **Conversations** (voice + chat + email)
   - Time range: **Last 2 months** (the first run analyzes historical data; after that it runs daily)
   - Click **Run** to start the initial discovery

> ⏱ The first discovery run takes 15-30 minutes. It will analyze existing cases and conversations to auto-discover intent groups and individual intents.

---

## Step 2: Review & Approve Discovered Intent Groups

After discovery completes, go to **Manage intent groups and intents**.

The AI will likely discover groups similar to these. Review and rename/approve as needed:

### Navico Intent Groups

| Intent Group | Description | Brands Covered |
|-------------|-------------|----------------|
| **Technical Support & Troubleshooting** | Intents related to product diagnostics, firmware issues, connectivity problems, and technical specifications | Simrad, Lowrance, B&G, C-MAP |
| **Warranty & RMA Processing** | Intents related to warranty validation, RMA requests (Exchange, Credit, Repair, OBS), and return logistics | All brands |
| **Product Information & Orders** | Intents related to product specifications, pricing, availability, order status, and product registration | All brands |
| **Certification & Training** | Intents related to dealer/distributor certification programs, training access, and skill validation | All brands (B2B focused) |

For each group, click **Edit** and add the descriptions above.

---

## Step 3: Configure Individual Intents

> ⚠️ **Manual Setup Required:** Intents must be created through the D365 Admin Center UI (Customer Intent Agent → Manage intents → New). API-created intents do not render in the UI due to a known Dynamics platform limitation.

For each discovered intent (or create manually if not discovered), configure these tabs:

### General Tab
- **Name** — clear, action-oriented
- **Intent Group** — assign to the right group
- **Line of Business** — Default LOB
- **Review Status** — set to **Approved**
- **Use in AI Agent** — set to **Yes**

### Attributes Tab
Attributes are data points the AI should extract from the conversation when it detects this intent. Think of them as "slots" to fill — the AI will ask follow-up questions to gather any missing attributes.

**Navico Attributes to Create** (create these under Admin Center → Customer Intent Agent → Manage → Attributes before linking them to intents):

| Attribute Name | Description | Used By Intents |
|---------------|-------------|-----------------|
| Serial number | Product serial number (e.g., SIM-2024-NSX-10042) | All intents |
| Brand | Navico brand: Simrad, Lowrance, B&G, C-MAP, Northstar | All intents |
| Product model | Specific product model (e.g., NSX 3007, HDS Live 9) | Technical, Warranty, Registration |
| Firmware version | Current firmware version installed on the unit | Firmware update, Diagnostics |
| Customer tier | Account tier: Platinum Expert, Platinum, Gold, Silver | Warranty, RMA intents |
| RMA type | Exchange, Credit, Repair, or OBS | RMA intents only |
| Warranty status | Active or Expired | Warranty validation, RMA intents |
| Connection type | NMEA 2000, Ethernet, WiFi, Bluetooth | Connectivity intent |
| Invoice/PO number | Purchase reference for credit requests | RMA Credit |
| Installer certification | Whether the installer is Navico-certified | Product registration, Certification |

### Knowledge Articles Tab
Link the KB articles that Copilot Agent Assist should surface when this intent is detected. Select **Add** and search for the article by number or title.

**Existing Navico KB Articles in System:**

| KB Number | Title | Link To Intents |
|-----------|-------|-----------------|
| KA-01262 | Simrad NSX Touchscreen Unresponsive After Firmware Update — Recovery Steps | Firmware update issue, Diagnose product fault |
| KA-01263 | B&G Triton2 Wind Instrument — Calibrating Apparent Wind Angle | Connectivity/networking, Product specification |
| KA-01264 | Lowrance HDS Live — Unit Not Powering On: Diagnostics & Warranty Claim Process | Diagnose product fault, Validate warranty, RMA Exchange |
| KA-01265 | RMA Process Overview — Exchange, Credit, Repair, OBS | All RMA intents, Validate warranty |

> 💡 **Tip:** Each intent can have multiple KB articles linked. When the CSR opens a case, Copilot will surface the most relevant article from the linked set based on conversation context.

### Technical Support & Troubleshooting Intents

#### 1. Diagnose product fault / not powering on
- **Group:** Technical Support & Troubleshooting
- **Description:** Customer reports a product that won't power on, displays an error, or is otherwise non-functional. Requires serial number validation and guided troubleshooting.
- **Agent Instructions:**
```
When a customer reports a product fault or power issue:
1. Ask for the serial number and product model
2. Look up the serial in Customer Assets to confirm warranty status
3. Identify the brand from the serial prefix (SIM- = Simrad, LWR- = Lowrance, BG- = B&G)
4. Check if there are known firmware issues for this model (reference KB articles)
5. Walk through the Fault Diagnostic checklist:
   - Power supply / battery voltage check
   - Wiring and connections
   - Software/firmware version
   - Factory reset if appropriate
6. If troubleshooting does not resolve: offer RMA (Exchange or Repair based on warranty)
7. For Platinum Expert accounts: escalate to brand-specific Tier 4 specialist
8. Always capture: serial, firmware version, symptoms, steps attempted
```

#### 2. Firmware update issue
- **Group:** Technical Support & Troubleshooting
- **Description:** Customer experiencing problems after or during a firmware update — unresponsive screen, feature regression, update failure.
- **Agent Instructions:**
```
When a customer reports a firmware issue:
1. Confirm the product model and current firmware version
2. Check if the reported firmware version has known issues (reference KB-SIM-0042 for Simrad NSX v3.8.1 touchscreen freeze)
3. Guide through recovery steps:
   a. Hard reset (hold power 15 seconds)
   b. Navigate via physical controls to Settings → Factory Reset
   c. If unit has SD card: check for corrupted update file
4. If recovery fails: initiate RMA Exchange (pre-approved for known firmware defects)
5. Log the firmware version and symptoms for engineering trend analysis
6. For fleet accounts (multiple units affected): escalate to Tier 4 specialist immediately
```

#### 3. Connectivity / networking issue (NMEA 2000, Ethernet)
- **Group:** Technical Support & Troubleshooting
- **Description:** Customer reporting issues with device connectivity — NMEA 2000 network, Ethernet, WiFi, or Bluetooth connections between Navico products.
- **Agent Instructions:**
```
When a customer reports a connectivity issue:
1. Identify which devices are involved and the connection type (NMEA 2000, Ethernet, WiFi)
2. Check if all devices are from the same brand family or cross-brand
3. For NMEA 2000: verify backbone power, check T-connector fuse, confirm terminators present
4. For Ethernet: verify cable integrity, check switch configuration
5. Reference the Fault Diagnostic Map — Networking section for step-by-step
6. Check if a recent firmware update changed network settings
7. If multi-device: determine if the issue is one device or network-wide
8. Escalate to Tier 3+ if the issue involves cross-brand integration (e.g., Simrad MFD with B&G instruments)
```

#### 4. Product specification / compatibility inquiry
- **Group:** Technical Support & Troubleshooting
- **Description:** Customer asking about product specifications, compatibility between products, or system requirements for installation.
- **Agent Instructions:**
```
When a customer asks about product specs or compatibility:
1. Identify the specific products involved
2. Reference the product catalog and compatibility matrix
3. For new installations: recommend the full system diagram (MFD + Radar + Autopilot + Sonar + GPS)
4. For upgrades: check what existing equipment they have and confirm compatibility
5. For B2B distributors: check if they need bulk pricing or if this should route to Sales
6. Provide downloadable spec sheets or direct links where available
7. If the question is about OEM integration: route to the OEM Partner support queue
```

### Warranty & RMA Processing Intents

#### 5. Validate warranty status
- **Group:** Warranty & RMA Processing
- **Description:** Customer wants to confirm if their product is still under warranty. Requires serial number lookup.
- **Agent Instructions:**
```
When a customer asks about warranty status:
1. Request the serial number
2. Look up the serial in Customer Assets
3. Report: warranty start date, end date, and status (Active/Expired)
4. If expired: inform about extended warranty options or out-of-warranty repair pricing
5. If active: confirm what the warranty covers (parts, labor, shipping)
6. For B2B accounts: check if they have an active Entitlement (service contract) that extends beyond standard warranty
7. Document the inquiry on the case record
```

#### 6. Request RMA — Exchange
- **Group:** Warranty & RMA Processing
- **Description:** Customer requesting a product exchange under warranty. The defective unit is returned and a replacement is shipped.
- **Agent Instructions:**
```
When a customer requests an RMA Exchange:
1. Validate warranty status (serial lookup)
2. Confirm the fault — what is wrong with the unit?
3. Check if the issue has been troubleshot (reference case timeline for prior steps)
4. If Tier 1/2 CSR: submit for Tier 4 Technical Specialist approval
5. If Tier 4/pre-approved: create the RMA record:
   - RMA Type: Exchange
   - Original Serial: [from case]
   - Replacement Serial: [generated]
   - Shipping: based on customer tier (Platinum = overnight, Gold = standard)
6. Send prepaid return label
7. Set follow-up: confirm replacement received + defective unit returned within 10 business days
```

#### 7. Request RMA — Repair
- **Group:** Warranty & RMA Processing
- **Description:** Customer requesting repair of a product. Unit is shipped to a Navico repair center and returned after repair.
- **Agent Instructions:**
```
When a customer requests an RMA Repair:
1. Validate warranty and serial
2. Create inbound repair request:
   - RMA Type: Repair
   - Ship-to: nearest Navico repair center
   - Expected turnaround: 10-15 business days
3. Provide prepaid shipping label and packing instructions
4. Set case status to "Waiting for Return"
5. Track: inbound scan → diagnostic → repair → QA → outbound ship
6. Notify customer at each stage via email
```

#### 8. Request RMA — Credit
- **Group:** Warranty & RMA Processing
- **Description:** Customer requesting a credit/refund instead of a replacement. Routes to finance for approval.
- **Agent Instructions:**
```
When a customer requests a credit:
1. Validate warranty and serial
2. Determine reason for credit (defective, not as described, cancellation)
3. Credit requests route to Finance & Admin team (not logistics)
4. Capture: invoice number, PO number, amount, reason
5. If amount > $1000 or out-of-warranty: requires manager approval
6. Set case to "Pending Finance Review"
7. Expected processing: 5-10 business days after approval
```

### Product Information & Orders Intents

#### 9. Product registration
- **Group:** Product Information & Orders
- **Description:** Customer wants to register a product for warranty activation. Consumer registration qualifies the user for specific support levels.
- **Agent Instructions:**
```
When a customer wants to register a product:
1. Collect: serial number, purchase date, proof of purchase, installer details (if applicable)
2. Verify the serial is not already registered to another account
3. Create/update Customer Asset record with registration details
4. For B2C consumers: registration activates standard warranty
5. For B2B/certified installers: registration may qualify for extended support tiers
6. System Assembly Assurance: if registering a full system, verify installer certification
7. Confirm registration via email with warranty details
```

#### 10. Certification / training inquiry
- **Group:** Certification & Training
- **Description:** Distributor or dealer asking about certification programs, training availability, or certification status updates.
- **Agent Instructions:**
```
When a customer asks about certification or training:
1. Identify: are they requesting new certification or checking existing status?
2. For new certification:
   - Direct to Navico certification portal (launched April 2026)
   - Explain: tests are delivered through the portal
   - Certification request → creates a case → tracks completion → updates contact record
3. For status check: look up contact record for bw_certifications field
4. For expired certifications: inform about renewal process
5. Note: certified installers get elevated support access and priority routing
6. For B2B accounts: show account-level certification count and suggest gaps
```

---

## Step 4: Link Existing KB Articles & Create SOPs

### Already in the System
These KB articles already exist in D365 and should be linked to intents via the **Knowledge articles** tab on each intent:

| KB Number | Title | Primary Intent(s) |
|-----------|-------|--------------------|
| **KA-01262** | Simrad NSX Touchscreen Unresponsive After Firmware Update — Recovery Steps | Firmware update issue |
| **KA-01263** | B&G Triton2 Wind Instrument — Calibrating Apparent Wind Angle | Connectivity/networking, Product specification |
| **KA-01264** | Lowrance HDS Live — Unit Not Powering On: Diagnostics & Warranty Claim Process | Diagnose product fault, Validate warranty |
| **KA-01265** | RMA Process Overview — Exchange, Credit, Repair, OBS | All RMA intents |

### SOP Articles (✅ Created & Published)

These 10 SOP articles have been created in D365 Knowledge Management and are ready to link to intents:

| Intent | KB Number | Article Title |
|--------|-----------|---------------|
| Diagnose product fault | **KA-01268** | SOP: Navico Product Fault Diagnosis Procedure |
| Firmware update issue | **KA-01273** | SOP: Firmware Update Recovery Steps |
| Connectivity / networking | **KA-01270** | SOP: NMEA 2000 and Ethernet Troubleshooting |
| Product specification | **KA-01271** | SOP: Product Compatibility and Specification Lookup |
| Validate warranty | **KA-01272** | SOP: Warranty Status Validation Process |
| RMA — Exchange | **KA-01274** | SOP: RMA Exchange Processing (Warranty) |
| RMA — Repair | **KA-01280** | SOP: RMA Repair Center Processing |
| RMA — Credit | **KA-01276** | SOP: Credit and Refund Request Processing |
| Product registration | **KA-01277** | SOP: Product Registration and Warranty Activation |
| Certification inquiry | **KA-01278** | SOP: Dealer Certification Program Guide |

> 💡 **To link:** Open each intent in D365 Admin Center → **Knowledge articles** tab → **Add** → search by KA number above.

---

## Step 5: Configure Agent Instructions (Per Intent Group)

In the Customer Intent Agent settings, add **Agent Instructions** for each intent group:

### Technical Support Group — Agent Instructions
```
You are handling a technical support intent for Navico Group marine electronics.

Key context:
- Navico brands: Simrad (blue-water/commercial), Lowrance (freshwater fishing), B&G (sailing/racing), C-MAP (cartography), Northstar (legacy)
- 17 total brands but 5 core brands handle 95% of support volume
- Serial number prefixes identify brand: SIM- = Simrad, LWR- = Lowrance, BG- = B&G, CMAP- = C-MAP, NST- = Northstar
- Customer tiers: Platinum Expert → Platinum → Gold → Silver → Registered
- Platinum Expert accounts (Tier 1 distributors) get priority routing and escalation
- Products interconnect via NMEA 2000 and Ethernet — issues may span multiple devices
- Hot words for immediate escalation: Safety, Man Overboard, Navigation Failure, Lost at Sea, Vessel Down
- 52% of all cases are technical support — this is the highest-volume intent group
- CSR skill tiers: Tier 1 (general) → Tier 2 (brand-trained) → Tier 3 (specialist) → Tier 4 (product expert)
- Known firmware issues list is maintained internally — always check before diagnosing

When responding:
1. Identify the brand from the serial prefix
2. Check customer tier to set priority and SLA:
   - Platinum Expert: 2-hour response, direct Tier 4 access
   - Platinum/Gold: 4-hour response, Tier 2 start
   - Silver/Registered: 8-hour response, Tier 1 start
   - B2C unregistered: 24-hour response, Tier 1 queue
3. Reference the appropriate diagnostic checklist based on issue type:
   - Product fault / not powering on → power supply, wiring, hard reset, factory reset (KA-01268)
   - Firmware issue → hard reset, physical buttons, SD card recovery, known bugs list (KA-01273)
   - Connectivity / networking → NMEA 2000 backbone, Ethernet cables, firmware alignment (KA-01270)
   - Specification / compatibility → product catalog, cross-brand matrix (KA-01271)
4. For multi-device issues: determine if brand-specific or cross-brand — cross-brand goes to Tier 3+
5. For fleet accounts (multiple vessels affected): escalate immediately to Tier 4
6. Capture on every case: serial, firmware version, symptoms described, all steps attempted
7. If troubleshooting resolves: document resolution, close case, send NPS survey
8. If unresolved and under warranty: initiate RMA (reference Warranty & RMA group instructions)
9. If safety-related: escalate immediately regardless of tier — do NOT attempt standard troubleshooting

Reference KB articles:
- KA-01268: SOP: Navico Product Fault Diagnosis Procedure
- KA-01273: SOP: Firmware Update Recovery Steps
- KA-01270: SOP: NMEA 2000 and Ethernet Troubleshooting
- KA-01271: SOP: Product Compatibility and Specification Lookup
- KA-01262: Simrad NSX Touchscreen Unresponsive After Firmware Update
- KA-01263: B&G Triton2 Wind Instrument — Calibrating Apparent Wind Angle
- KA-01264: Lowrance HDS Live — Unit Not Powering On
```

### Warranty & RMA Group — Agent Instructions
```
You are handling a warranty or RMA intent for Navico Group marine electronics.

Key context:
- 4 RMA types: Exchange (swap unit), Credit (refund), Repair (ship to repair center), OBS (Onboard Support Request)
- Technical Specialist (TS) must validate before RMA approval
- Warranty lookup by serial number in Customer Assets
- Platinum Expert accounts may have Entitlements that extend beyond standard warranty
- TS reviews evidence, validates fault, then submits to ERP for fulfillment
- Credit RMAs go to Finance team, not logistics
- Repair workflow: inbound scan → diagnostic → repair → QA check → outbound ship
- ERP systems: Oracle (US), Dynamics AX (EMEA) — RMA fulfillment routes to the appropriate ERP
- Repair centers: US = Tulsa, OK / EMEA = Egersund, Norway

When responding:
1. Always start with serial number and warranty validation
2. Determine the appropriate RMA type based on customer preference and situation
3. For Exchange: route to TS for pre-approval if not already validated
4. For Repair: identify the nearest repair center based on customer region
5. For Credit: capture invoice/PO details and route to Finance — NOT logistics
6. Confirm processing timeline based on customer tier:
   - Platinum Expert: overnight exchange, 5-7 day repair
   - Platinum/Gold: 2-3 day exchange, 10-15 day repair
   - Silver/Registered: standard ground exchange, 10-15 day repair
7. For out-of-warranty requests: provide repair pricing or suggest trade-in/upgrade
8. If the same serial has had 3+ RMAs in 12 months: flag for quality escalation
9. Always document the RMA type, reason code, and approval path on the case

Reference KB articles:
- KA-01265: RMA Process Overview — Exchange, Credit, Repair, OBS
- KA-01274: SOP: RMA Exchange Processing (Warranty)
- KA-01280: SOP: RMA Repair Center Processing
- KA-01276: SOP: Credit and Refund Request Processing
- KA-01272: SOP: Warranty Status Validation Process
```

### Product Information & Orders Group — Agent Instructions
```
You are handling a product information, ordering, or registration intent for Navico Group marine electronics.

Key context:
- Navico Group has 17 brands, with 5 core brands covering 95% of business:
  * Simrad — blue-water cruising, commercial fishing, superyachts
  * Lowrance — freshwater fishing, bass boats, kayak fishing
  * B&G — sailing, racing, performance cruising
  * C-MAP — cartography across all segments
  * Northstar — legacy navigation systems (limited new product)
- Customer base has two main segments:
  * B2B: Tier 1 distributors (direct), Tier 2 distributors (dealer locator), OEM partners, certified installers
  * B2C: End consumers who purchase through retail or online
- Product registration is critical — it activates warranty, qualifies support level, and enables System Assembly Assurance
- System Assembly Assurance: when a certified installer registers a full system (MFD + radar + autopilot + instruments), it validates professional installation and qualifies for enhanced warranty
- Cross-brand compatibility: all Navico brands share NMEA 2000 data and Ethernet radar/sonar, but MFD screen sharing is same-brand only
- C-MAP charts work across all Navico MFDs

When responding:
1. Identify whether the inquiry is B2B or B2C — this changes the workflow significantly
2. For product specifications: reference the product catalog and compatibility matrix
3. For new installations: recommend the full system diagram (MFD + Radar + Autopilot + Sonar + GPS)
4. For compatibility questions: check NMEA 2000 and Ethernet support across devices
5. For product registration:
   - Collect serial number, purchase date, proof of purchase, and installer details
   - Verify the serial is not already registered to another account
   - Create/update Customer Asset record with warranty dates
   - For certified installer registrations: set System Assembly Assurance flag
6. For B2B pricing/availability questions: route to Sales team — do NOT provide pricing from support
7. For OEM integration inquiries: route to OEM Partner support queue
8. For order status questions: check the ERP system (Oracle for US, Dynamics AX for EMEA)

Reference KB articles:
- KA-01271: SOP: Product Compatibility and Specification Lookup
- KA-01277: SOP: Product Registration and Warranty Activation
```

### Certification & Training Group — Agent Instructions
```
You are handling a certification or training intent for Navico Group's dealer and distributor network. This is primarily a B2B intent — most certification inquiries come from dealers, distributors, and professional installers.

Key context:
- Navico runs a Dealer Certification Program with 3 levels:
  * Basic Certified — online training + basic exam → dealer pricing, standard support
  * Advanced Certified — product-specific training + hands-on → priority support, advanced exchange
  * Expert Certified — multi-brand training + field assessment + annual renewal → Tier 4 direct access, System Assembly Assurance authority, beta firmware access
- Certification portal launched April 2026 — tests and training delivered through the portal
- Certification requests create a case in D365 that tracks completion
- Passing scores: 80% Basic, 85% Advanced, 90% Expert
- Failed tests have a 7-day waiting period before retake
- Certifications expire: 12 months (Basic/Advanced), 24 months (Expert)
- Renewal notifications sent 60 days before expiration
- If lapsed beyond 90-day grace period: full re-certification required
- Certified installers get elevated support access and priority routing in D365
- Contact record stores certification level and date
- Account record stores total certified personnel count

When responding:
1. Determine if the caller is requesting NEW certification or checking EXISTING status
2. For new certification:
   - Direct to the Navico Certification Portal
   - Explain: tests are delivered through the portal, certification request creates a tracked case
   - Explain the 3 levels and benefits of each
3. For status check:
   - Look up the Contact record → Certifications field
   - Check expiration dates — are any approaching renewal?
   - For account-level overview: show certified personnel count and identify gaps
4. For expired certifications:
   - Within 90-day grace period: can still renew with shortened exam
   - Past 90-day grace: full re-certification required
   - Warn: expiration may affect account support tier and dealer program access
5. For certification removal/revocation: requires Regional Manager approval — escalate
6. Always notify the contact AND the account admin when certification status changes

Reference KB articles:
- KA-01278: SOP: Dealer Certification Program Guide
```

---

## Step 6: Link Intents to Connectors (Optional)

For advanced automation, you can link intents to Power Automate connectors:

| Intent | Connector Action |
|--------|-----------------|
| Validate warranty | Auto-lookup serial → return warranty status card |
| Product registration | Auto-create Customer Asset record |
| RMA — Exchange | Auto-generate RMA record + trigger ERP order |
| Certification inquiry | Auto-lookup contact certification status |

This is optional for the demo but shows the art of the possible.

---

## Step 7: Verify in Live Demo

1. Open a case linked to serial `SIM-2024-NSX-10042` (Simrad NSX hero case)
2. The Customer Intent Agent should detect **"Diagnose product fault"** intent
3. Copilot Agent Assist panel should surface:
   - The intent classification ("Technical Support > Product Fault")
   - Suggested KB article: SOP: Navico Product Fault Diagnosis Procedure
   - Suggested next steps from the agent instructions
4. Open Christine's B&G email case — should detect **"Connectivity / networking issue"** or **"Technical Support"**
5. Open Mike Torres' Lowrance case — should detect **"Validate warranty"** + **"RMA"** dual intent

---

## Automation Script (Future)

> ⚠️ **Known Limitation:** API-created intents (`POST msdyn_intents`) do not render in the D365 Admin Center UI. Until Microsoft fixes this, intents must be created manually through the UI. The scripts below can still be used for KB article creation and publishing.

The Zurn implementation uses `d365/scripts/22-CustomerIntentAgent.ps1` which:
- Creates KB articles (SOPs) for each intent
- Publishes KB articles

A Navico-specific version (`customers/navico/d365/Configure-NavicoIntentAgent.ps1`) should be built to automate KB article creation (Steps 4) while intents themselves are created manually (Steps 2-3).

---

## Quick Reference: Intent → Brand → Escalation Path

| Customer Says... | Detected Intent | Brand | Route To |
|-------------------|----------------|-------|----------|
| "My Simrad screen won't turn on" | Diagnose product fault | Simrad | Simrad queue → Tier 2 |
| "I need to return my Lowrance for a refund" | RMA — Credit | Lowrance | Finance team |
| "B&G wind sensor readings are wrong on 3 boats" | Connectivity/networking | B&G | B&G queue → Tier 4 (fleet) |
| "Is my Halo radar still under warranty?" | Validate warranty | Simrad | Auto-lookup → response |
| "I want to register my new chartplotter" | Product registration | (from serial) | Registration workflow |
| "How do I get certified as an installer?" | Certification inquiry | All | Certification portal link |
| "Firmware update bricked my NSX" | Firmware update issue | Simrad | Simrad queue → Tier 3+ |
