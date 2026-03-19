# Otis — RMA / Return / Credit Demo Script

> **Customer**: Otis Elevator Company
> **Scenario**: Return Merchandise Authorization (RMA) Request
> **Agent Persona**: Agent
> **Connected System**: ERP

---

## Scenario Overview

**Customer Request**: "I need to return a product. It arrived damaged / defective / wrong item."

**What to Demonstrate:**
- Guided RMA initiation workflow
- Photo/document attachment for damage claims
- Automatic credit calculation
- Replacement order creation
- Return label generation

---

## Pre-Demo Setup

### Ensure You Have:
- [ ] RMA custom page / guided action available
- [ ] Sample order with delivered items eligible for return
- [ ] Return reason picklist populated
- [ ] Credit limit/authorization rules configured

---

## Act 1: Return Request

**Customer**: "Hi, I received my order but one of the items was damaged in shipping. The box was crushed. I need to return it."

**Action**: Locate the order and open the **RMA / Returns** custom page.

💬 **Talk Track:**
> "I'm sorry to hear that. Let me pull up your order and start the return process 
> right away. I have a guided workflow for this."

---

## Act 2: RMA Initiation

**What to Show (RMA Form):**

| Field | Value |
|-------|-------|
| Order Number | ORD-78421 |
| Item to Return | Widget A - Line 1 |
| Return Reason | Damaged in Transit |
| Quantity | 1 |
| Original Cost | $125.00 |

**Action:**
1. Select the item to return
2. Choose return reason from picklist
3. Enter damage description

💬 **Talk Track:**
> "I'm selecting the damaged item from your order. The system shows this is 
> within the return window. What would you prefer — a replacement or a credit?"

---

## Act 3: Photo Attachment (Optional)

**Customer**: "I took photos of the damage."

**Action**: Attach photos to the RMA case.

**What to Show:**
- Drag-and-drop attachment capability
- Photo preview in case view
- Notes field for additional details

💬 **Talk Track:**
> "Perfect — photos help us process this faster. I'm attaching them to your case. 
> For visible damage claims, this usually gets auto-approved."

---

## Act 4: Credit/Replacement Options

**What to Show (Resolution Options):**

| Option | Description |
|--------|-------------|
| **Credit** | $125.00 credit to account |
| **Replacement** | Ship new item, no charge |
| **Exchange** | Different product at price adjustment |

**Customer**: "I'd like a replacement shipped."

**Action:**
1. Select "Replacement" option
2. Confirm shipping address
3. Submit RMA

---

## Act 5: Automatic Processing (Hero Moment)

**What Happens Automatically:**

1. ✅ RMA Number Generated: RMA-2024-00456
2. ✅ Credit/Replacement Order Created in ERP
3. ✅ Return Shipping Label Generated
4. ✅ Email Sent to Customer with Label
5. ✅ Case Updated with RMA Reference

💬 **Talk Track:**
> "Your RMA has been approved. Here's what just happened automatically: 
> I generated an RMA number, created a replacement order, and sent you a 
> prepaid return label by email. You should have it already."

---

## Post-Return: Credit Integration

**What to Show (if time permits):**
- Credit memo created in ERP
- GL posting for inventory adjustment
- Customer account balance updated
- Defective inventory flagged for QA

💬 **Talk Track:**
> "When the item is returned, the credit automatically posts to ERP. 
> The defective unit gets flagged for QA review. Complete loop — no manual steps."

---

## Key Points to Emphasize

### Without This Workflow:
| Old Way | New Way |
|---------|---------|
| Agent logs into ERP to create RMA | Guided action in case view |
| Manual return label (warehouse) | Auto-generated with submission |
| "Credit will be applied in 3-5 days" | Instant credit with return receipt |
| No visibility once RMA submitted | Status tracked in case timeline |

### Business Value:
- **70% faster RMA processing**
- **Reduced return lag** with instant labels
- **Better customer experience** — one call resolution
- **Audit trail** for every return
