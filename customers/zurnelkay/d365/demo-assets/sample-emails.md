# Sample Email Threads for Zurn Elkay D365 Customer Service Demo

Use these emails to demonstrate the **email-to-case** flow in Dynamics 365 Customer Service.
Copy/paste the **Inbound** email to send to the queue mailbox, then use the **Agent Reply** and **Customer Follow-up** messages to show the back-and-forth conversation updating the case timeline.

---

## Scenario 1: Distributor Order Issue (Tier 1 — Ferguson)

> **Use case:** A Tier 1 distributor reports a shipment discrepancy. Shows case creation from email, agent response, customer confirmation.

### Email 1 — Inbound (creates case)

| Field | Value |
|-------|-------|
| **From** | mike.reynolds@ferguson.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | PO #91447 — Wrong flush valve models shipped |

```
Hi Zurn Team,

We received shipment for PO #91447 today at our Houston distribution center and the contents don't match our order. We ordered 48 units of the Zurn AquaVantage AV flush valve (P/N Z6000-AV) but received 48 units of the Z6000-WS1 instead.

We have a contractor job starting Monday that depends on these valves. Can you please expedite the correct product and provide a return label for the wrong shipment?

Order details:
- PO #91447
- Ship-to: Ferguson Houston DC, 4200 Gulf Freeway, Houston TX 77023
- Original order date: 02/24/2026
- Qty: 48 ea Z6000-AV AquaVantage flush valves

Please advise on next steps ASAP.

Thanks,
Mike Reynolds
Ferguson Enterprises — Commercial Division
Phone: (713) 555-0184
```

### Email 2 — Agent Reply

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | mike.reynolds@ferguson.com |
| **Subject** | RE: PO #91447 — Wrong flush valve models shipped [Case #ZRN-2026-1042] |

```
Hi Mike,

Thank you for contacting Zurn Customer Service. I've looked into PO #91447 and confirmed the shipping error on our end — the warehouse pulled the Z6000-WS1 instead of the Z6000-AV.

Here's what we're doing to fix this:

1. **Replacement shipment** — 48x Z6000-AV shipping today via Next Day Air from our Paso Robles facility. Tracking will be sent to this email once it ships.
2. **Return label** — I've attached a prepaid UPS return label for the 48x Z6000-WS1. Please have them ready for pickup; UPS will be scheduled for tomorrow.
3. **Credit** — No charge for the expedited shipping given this was our error.

Your replacement should arrive by Friday morning. Will that work for the Monday job start?

Best regards,
Sarah Chen
Zurn Customer Service — Commercial Team
Case #ZRN-2026-1042
```

### Email 3 — Customer Follow-up

| Field | Value |
|-------|-------|
| **From** | mike.reynolds@ferguson.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | RE: PO #91447 — Wrong flush valve models shipped [Case #ZRN-2026-1042] |

```
Sarah,

Friday delivery works. Appreciate the fast turnaround.

One more thing — can you confirm the Z6000-AV units are the current revision with the 1.28 GPF dual-flush option? The contractor spec calls for that specifically.

Thanks,
Mike
```

### Email 4 — Agent Final Reply

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | mike.reynolds@ferguson.com |
| **Subject** | RE: PO #91447 — Wrong flush valve models shipped [Case #ZRN-2026-1042] |

```
Hi Mike,

Confirmed — the replacement Z6000-AV units are the current revision (Rev. C, manufactured January 2026) with the 1.28/1.1 GPF dual-flush capability. They meet the ADA and WaterSense specs your contractor needs.

Tracking number: 1Z999AA10123456784 (UPS Next Day Air)
Estimated delivery: Friday, February 28 by 10:30 AM

I'll keep this case open until you confirm receipt. Let me know if anything else comes up.

Best,
Sarah Chen
Zurn Customer Service
```

---

## Scenario 2: Urgent / Hot Word — Emergency Backflow Failure (Tier 2 — Hajoca)

> **Use case:** A hot-word email ("EMERGENCY") triggers high-priority case creation. Demonstrates priority escalation and urgent handling.

### Email 1 — Inbound (creates case — hot word: EMERGENCY)

| Field | Value |
|-------|-------|
| **From** | tom.garcia@hajoca.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | EMERGENCY — Wilkins 975XL backflow preventer failed at hospital site |

```
Zurn/Wilkins Team — EMERGENCY

We have a critical situation. A Wilkins 975XL 4" backflow preventer (installed 14 months ago) failed at Mercy General Hospital in Philadelphia. The check valve is not holding and the city water authority has issued a 48-hour compliance notice.

The hospital cannot lose water service. We need:
1. Replacement 975XL 4" unit or repair kit shipped IMMEDIATELY
2. Technical guidance on whether a field repair is possible vs. full replacement
3. Warranty status confirmation (unit was purchased through Hajoca PO #H-78234)

This is a life-safety situation at a hospital. Please escalate accordingly.

Tom Garcia
Hajoca Corporation — Philadelphia Branch
Emergency line: (215) 555-0291
```

### Email 2 — Agent Reply (escalated)

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | tom.garcia@hajoca.com |
| **CC** | wilkins.techsupport@zurnelkay.com |
| **Subject** | RE: EMERGENCY — Wilkins 975XL backflow preventer failed at hospital site [Case #ZRN-2026-1108] |

```
Tom,

This has been escalated to Priority 1. Here's our response:

**Immediate Actions:**
1. **Replacement unit** — A Wilkins 975XL 4" (P/N 114-975XL) is shipping NOW via emergency same-day air freight from our Erie, PA warehouse. ETA: tonight by 8 PM.
2. **Field tech** — I've contacted our Wilkins technical team. Dan Moretti (Wilkins Field Engineer, Mid-Atlantic) will call you within 30 minutes at (215) 555-0291 to walk through the situation. He can be on-site tomorrow morning if needed.
3. **Warranty** — PO #H-78234 is confirmed under warranty (purchased 01/2025, 5-year warranty applies). Full replacement at no cost.

**Interim Guidance:**
If the facility needs to maintain service before the replacement arrives, the 975XL has an isolation bypass configuration. Dan can advise on whether that's appropriate for this installation.

We take hospital life-safety situations extremely seriously. I'm personally monitoring this case and will be available until resolution.

James Walker
Zurn Customer Service — Backflow/Wilkins Team (Escalation Lead)
Direct: (814) 555-0347
Case #ZRN-2026-1108
```

### Email 3 — Customer Follow-up

| Field | Value |
|-------|-------|
| **From** | tom.garcia@hajoca.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | RE: EMERGENCY — Wilkins 975XL backflow preventer failed at hospital site [Case #ZRN-2026-1108] |

```
James,

Dan called and we have a plan. He's going on-site at 7 AM tomorrow. The replacement unit arrived at our branch at 7:45 PM — great job getting that out so fast.

Dan suspects the first check module may have debris fouling. He'll do a full tear-down inspection of the failed unit so we can determine root cause.

Will send an update after the install tomorrow.

Tom
```

---

## Scenario 3: Elkay Product Technical Support (Tier 2 — Winsupply)

> **Use case:** Standard technical inquiry about an Elkay product. Shows a conversational back-and-forth with troubleshooting steps.

### Email 1 — Inbound (creates case)

| Field | Value |
|-------|-------|
| **From** | jessica.huang@winsupply.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | ezH2O Liv bottle filler not dispensing — model?"?"?"?"?"??"? |

```
Hi Elkay Support,

One of our end customers (a school district) is reporting that a recently installed Elkay ezH2O Liv bottle filler (model LBWD06WHK) is not dispensing water. The unit powers on and the sensor light activates, but no water comes out.

Installation was completed last week by a licensed plumber. Water supply is confirmed on.

Can you provide troubleshooting steps? The school wants this resolved before students return from break next Monday.

Details:
- Model: LBWD06WHK (White, non-filtered)
- Install date: 02/21/2026
- Location: Ridgewood Elementary, Dayton OH
- Purchased via: Winsupply Dayton, PO #WS-44891

Thanks,
Jessica Huang
Winsupply — Dayton Branch
(937) 555-0163
```

### Email 2 — Agent Reply (troubleshooting)

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | jessica.huang@winsupply.com |
| **Subject** | RE: ezH2O Liv bottle filler not dispensing — model LBWD06WHK [Case #ELK-2026-0387] |

```
Hi Jessica,

Thanks for reaching out. This sounds like it could be one of a few common installation items. Please have the plumber check the following:

**Step 1 — Inlet strainer**
The LBWD06WHK has a small inlet strainer where the supply line connects. Construction debris or pipe dope can clog it on new installs. Remove the supply line and check/clean the strainer screen.

**Step 2 — Flow control valve**
Inside the unit there's a manual flow control valve (small flathead screw on the solenoid). Confirm it's in the OPEN position (counter-clockwise).

**Step 3 — Solenoid test**
With the unit powered on, place a bottle in the sensor zone. You should hear a click from the solenoid. If no click, check the wiring harness connector between the sensor board and solenoid — it sometimes comes loose during shipping.

If none of those resolve it, let me know and we'll set up a warranty replacement. The unit is well within the 5-year parts warranty.

Best,
Maria Santos
Elkay Customer Service — Hydration Products
Case #ELK-2026-0387
```

### Email 3 — Customer Follow-up

| Field | Value |
|-------|-------|
| **From** | jessica.huang@winsupply.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | RE: ezH2O Liv bottle filler not dispensing — model LBWD06WHK [Case #ELK-2026-0387] |

```
Maria,

It was the inlet strainer — packed with pipe tape fragments. Plumber cleaned it out and the unit is dispensing perfectly now. Bottle counter is working too.

Thanks for the quick help. You can close this case.

Jessica
```

### Email 4 — Agent Close

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | jessica.huang@winsupply.com |
| **Subject** | RE: ezH2O Liv bottle filler not dispensing — model LBWD06WHK [Case #ELK-2026-0387] |

```
Glad to hear it, Jessica! That's the most common culprit on new installs.

I'm closing out case #ELK-2026-0387 as resolved. If anything else comes up with this unit or any other Elkay products, don't hesitate to reach out.

Have a great rest of your week!

Maria Santos
Elkay Customer Service
```

---

## Scenario 4: Warranty / RMA Claim (Tier 3 — Gateway Supply)

> **Use case:** A warranty claim requiring an RMA. Good for showing case status progression (Active → On Hold → Resolved).

### Email 1 — Inbound (creates case)

| Field | Value |
|-------|-------|
| **From** | carlos.mendez@gatewaysupply.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | Warranty claim — Elkay Lustertone sink rusting after 8 months |

```
Hi Zurn Elkay Team,

I need to file a warranty claim for one of our customers. They purchased an Elkay Lustertone Classic undermount sink (model ELUH2816) through our branch 8 months ago, and it's showing visible rust spots along the drain cutout and near one of the mounting clips.

This is a stainless steel sink that should not be rusting. The customer is a residential homeowner and the sink is used in a standard kitchen application — no harsh chemicals or commercial use.

I've attached 3 photos showing the rust. (See attached: rust-1.jpg, rust-2.jpg, rust-3.jpg)

Customer info:
- End user: Robert & Lisa Kim, 445 Oak Street, Portland OR
- Purchased: 06/2025 via Gateway Supply Portland, Invoice #GW-19982
- Model: ELUH2816 (Lustertone Classic, 18-gauge 304 SS)

Please advise on the RMA process and whether this is a warranty replacement or repair.

Carlos Mendez
Gateway Supply — Portland Branch
(503) 555-0221
```

### Email 2 — Agent Reply (RMA initiated)

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | carlos.mendez@gatewaysupply.com |
| **Subject** | RE: Warranty claim — Elkay Lustertone sink rusting after 8 months [Case #ELK-2026-0412] |

```
Hi Carlos,

I've reviewed the photos and this appears to be a manufacturing defect — surface contamination during production can cause localized corrosion on stainless steel. This is absolutely covered under the Elkay Limited Lifetime Warranty for the Lustertone line.

**RMA Details:**
- RMA #: RMA-ELK-2026-0412
- Replacement model: ELUH2816 (same model, new unit)
- Ship-to: Gateway Supply Portland, or direct to end customer — your preference

**Next steps:**
1. Please confirm the ship-to address.
2. I'll process the replacement shipment (standard ground, 5-7 business days).
3. The defective sink does NOT need to be returned — the photos are sufficient documentation.

Let me know the preferred delivery address and I'll get this moving.

Kevin Park
Zurn Elkay Customer Service — Warranty Claims
Case #ELK-2026-0412
```

### Email 3 — Customer Follow-up

| Field | Value |
|-------|-------|
| **From** | carlos.mendez@gatewaysupply.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | RE: Warranty claim — Elkay Lustertone sink rusting after 8 months [Case #ELK-2026-0412] |

```
Kevin,

Please ship directly to the end customer:
Robert Kim
445 Oak Street
Portland, OR 97205

They'll have a plumber ready to do the swap. Appreciate not requiring the return — makes it much easier for the homeowner.

Carlos
```

### Email 4 — Agent Final Reply

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | carlos.mendez@gatewaysupply.com |
| **Subject** | RE: Warranty claim — Elkay Lustertone sink rusting after 8 months [Case #ELK-2026-0412] |

```
Carlos,

Replacement ELUH2816 is shipping today to Mr. Kim's address.

Tracking: 1Z999AA10198765432 (UPS Ground)
Estimated delivery: March 9-11, 2026

I've placed this case on hold pending delivery confirmation. Once Mr. Kim confirms receipt and install, let me know and I'll close it out. If you don't reach out, I'll follow up in 2 weeks.

Thanks,
Kevin Park
Zurn Elkay Customer Service
```

---

## Scenario 5: Recall / Safety Hot Word (Tier 1 — HD Supply)

> **Use case:** Email containing "recall" and "safety" hot words. Good for showing priority boost to 10,000 and immediate escalation workflow.

### Email 1 — Inbound (creates case — hot words: RECALL, SAFETY)

| Field | Value |
|-------|-------|
| **From** | david.oconnor@hdsupply.com |
| **To** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **Subject** | SAFETY concern — Possible recall on Zurn Z5795 flush valve? |

```
Zurn Team,

We've had 3 separate contractor reports in the last 2 weeks about Zurn Z5795 sensor-operated flush valves activating unexpectedly and continuously — causing flooding in restrooms at commercial sites.

Affected locations:
1. Hilton Garden Inn, Charlotte NC — 4 units continuously flushing, water damage to ceiling below
2. Duke Energy HQ, Charlotte NC — 2 units, intermittent phantom flushing
3. Atrium Health Clinic, Concord NC — 1 unit, continuous flush for 6+ hours overnight

Is there an active recall or safety bulletin on the Z5795 or its sensor module? Our contractors are asking whether they should shut down the water supply to these units until there's a fix.

This is a safety and property damage concern. Please respond urgently.

David O'Connor
HD Supply Facilities Maintenance — Southeast Region
(704) 555-0156
```

### Email 2 — Agent Reply (escalated)

| Field | Value |
|-------|-------|
| **From** | customerservice@D365DemoTSCE30330346.onmicrosoft.com |
| **To** | david.oconnor@hdsupply.com |
| **CC** | quality.engineering@zurnelkay.com |
| **Subject** | RE: SAFETY concern — Possible recall on Zurn Z5795 flush valve? [Case #ZRN-2026-1155] |

```
David,

Thank you for reporting this — we take safety concerns very seriously and this case has been escalated to our Quality Engineering team.

**Current Status:**
There is NO active recall on the Z5795 at this time. However, we are aware of a sensor module firmware issue (affecting units manufactured between September and November 2025) that can cause phantom activation in certain conditions — specifically when the sensor is exposed to reflected infrared from high-gloss tile or mirrors within 18 inches.

**Immediate Recommendation:**
The units do NOT need to be shut down, but the contractors should:
1. Check the sensor range — it may be set to maximum. Reduce to minimum (short-range mode).
2. Verify the sensor lens is clean and dry.
3. Check if any reflective surfaces were recently installed nearby.

**Resolution:**
We have an updated sensor module (P/N P6900-S-KIT) that resolves this issue. I'm sending **10 kits to your Charlotte branch at no charge** — enough to cover the 7 affected units plus spares. Estimated delivery: 3-4 business days.

Our Quality team may follow up for additional site information as part of their investigation.

Rachel Torres
Zurn Customer Service — Quality & Recall Liaison
Case #ZRN-2026-1155 (Priority: Critical)
```

---

## Quick Reference: Which Queue to Send Each Email To

| Scenario | Queue | Brand |
|----------|-------|-------|
| 1 — Ferguson flush valve | Commercial Email | Zurn |
| 2 — Hajoca backflow emergency | Commercial Email (or Apps-Eng-CB) | Zurn |
| 3 — Winsupply Elkay bottle filler | Elkay Hydration Support | Elkay |
| 4 — Gateway Elkay sink warranty | Elkay Sinks & Fixtures | Elkay |
| 5 — HD Supply recall/safety | Commercial Email | Zurn |

## Demo Tips

1. **Send Email 1 to the queue mailbox** — wait for automatic case creation (may take 1-2 minutes depending on server-side sync).
2. **Open the case** in the Customer Service workspace — show the email on the timeline.
3. **Reply from within D365** using the Email 2 content — this demonstrates the agent composing a response directly on the case.
4. **Send Email 3 as another inbound** — shows it threading onto the existing case timeline.
5. **Resolve the case** after the final reply to show the full lifecycle.

For the **hot-word scenarios** (2 and 5), point out how the priority was automatically boosted and the case landed in the right queue based on the email content.
