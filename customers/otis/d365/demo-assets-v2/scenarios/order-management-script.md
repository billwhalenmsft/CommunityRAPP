# Otis — Order Management Demo Script

> **Customer**: Otis Elevator Company
> **Scenario**: Order Lookup, Modification, and Status Update
> **Agent Persona**: Agent
> **Connected System**: ERP

---

## Scenario Overview

**Customer Request**: "I need to check on my order and possibly make a change."

**What to Demonstrate:**
- Real-time order lookup from within the case
- Order details without system switching
- Modification capability (quantity, address, line items)
- Audit trail of changes

---

## Pre-Demo Setup

### Ensure You Have:
- [ ] Sample order visible in Order Management custom page
- [ ] ERP integration active (or mock data)
- [ ] Customer record with related orders

---

## Act 1: Customer Asks About Order

**Customer**: "Hi, I need to check on order number ORD-78421. Can you tell me what the status is?"

**Action**: From the case form, open the **Order Management** custom page.

💬 **Talk Track:**
> "Let me look that up for you. I have our Order Management tool right here 
> in my workspace — it's connected to our ERP in real-time."

---

## Act 2: Show Order Details

**What to Show (Order Management Page):**

| Order Header | Value |
|--------------|-------|
| Order Number | ORD-78421 |
| Order Date | [Recent date] |
| Status | In Production / Shipped |
| Requested Delivery | [Future date] |
| Ship-To Address | Customer address |

**Line Items Section:**

| Line | Product | Qty | Unit Price | Status |
|------|---------|-----|------------|--------|
| 1 | Widget A | 10 | $125.00 | Shipped |
| 2 | Component B | 25 | $45.00 | In Production |
| 3 | Accessory C | 5 | $22.00 | Open |

💬 **Talk Track:**
> "I can see your complete order right here. Line 1 has already shipped, 
> Line 2 is in production, and Line 3 is still open. Is there something 
> specific you'd like to change?"

---

## Act 3: Order Modification

**Customer**: "Actually, can we increase the quantity on Line 3 from 5 to 10?"

**Agent**: "Let me check if that's available..."

**Action:**
1. Click **Modify** on Line 3
2. Update quantity from 5 to 10
3. Show real-time availability check
4. Click **Save Changes**

💬 **Talk Track:**
> "I'm updating the quantity now. The system is checking inventory availability 
> in real-time against our ERP... Good news, we have stock. The order 
> total has been updated. You'll receive a confirmation email shortly."

---

## Act 4: Audit Trail

**What to Show:**
- Order history/timeline showing the change
- Who made the change and when
- Previous value → New value

💬 **Talk Track:**
> "Every change is tracked with a full audit trail. I can see exactly when 
> modifications were made, by whom, and what the original values were. This 
> helps with compliance and dispute resolution."

---

## Key Points to Emphasize

### Without This Tool:
| Old Way | New Way |
|---------|---------|
| "Let me log into ERP..." | Order visible in case view |
| 3+ minute context switch | Instant lookup |
| Manual change → email confirmation | Integrated modification + auto email |
| No audit trail in CRM | Full history in timeline |

### Business Value:
- **60% faster** order inquiries
- **Zero system switching** for common tasks
- **Complete audit trail** for compliance
- **Real-time data** via API integration
