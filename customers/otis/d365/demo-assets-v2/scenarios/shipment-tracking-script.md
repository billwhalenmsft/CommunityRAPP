# Otis — Shipment Tracking Demo Script

> **Customer**: Otis Elevator Company
> **Scenario**: "Where's My Order?" — Shipment Status Inquiry
> **Agent Persona**: Agent

---

## Scenario Overview

**Customer Request**: "I haven't received my shipment yet. Where is it?"

**What to Demonstrate:**
- Real-time shipment tracking from case
- Carrier integration (FedEx, UPS, etc.)
- Proactive delay notifications
- Exception handling for late/damaged shipments

---

## Pre-Demo Setup

### Ensure You Have:
- [ ] Sample shipment with tracking number
- [ ] Carrier tracking URL configured
- [ ] Timeline showing shipment events

---

## Act 1: Customer Inquiry

**Customer**: "Hi, I placed an order last week and the shipping notification said it would arrive two days ago. It still hasn't shown up."

**Agent**: "I'm sorry about that. Let me look up your shipment right away."

**Action**: Access the shipment tracking from the Order Management page or case timeline.

💬 **Talk Track:**
> "I have shipment tracking integrated right here. Let me pull up the status..."

---

## Act 2: Shipment Status Display

**What to Show (Tracking Panel):**

| Field | Value |
|-------|-------|
| Tracking Number | 1Z999AA10123456784 |
| Carrier | UPS |
| Ship Date | [5 days ago] |
| Estimated Delivery | [2 days ago] |
| Current Status | **Delayed - Weather Exception** |
| Last Location | Chicago Distribution Hub |

**Tracking Events Timeline:**
```
📍 [Today] 8:42 AM - Chicago Hub - Delayed due to weather
📍 [Yesterday] 3:15 PM - Chicago Hub - Arrived at facility
📍 [3 days ago] 9:00 AM - Origin - Shipped
```

💬 **Talk Track:**
> "I can see your package is at the Chicago distribution center. There's been a 
> weather delay — looks like snowstorms in the Midwest. The carrier shows an updated 
> delivery estimate of [tomorrow]."

---

## Act 3: Offer Resolution Options

**Agent**: "I see the delay is beyond the carrier's control, but I want to make this right. I have a few options for you..."

**Options to Present:**

1. **Expedite at No Charge**: Upgrade to overnight once weather clears
2. **Partial Credit**: Shipping refund for the delay
3. **Replacement Ship**: Send new order from alternate warehouse

💬 **Talk Track:**
> "I'm authorized to offer expedited shipping at no extra cost once the weather 
> clears, or I can apply a credit to your account. Which would you prefer?"

---

## Act 4: Proactive Notifications (Hero Moment)

**What to Show:**
- Automated shipment delay notification setup
- Customer communication preferences
- Proactive SMS/Email when status changes

💬 **Talk Track:**
> "I'm also setting up a proactive notification so you'll get an automatic text 
> and email the moment the package is out for delivery. You won't have to call back."

---

## Key Points to Emphasize

### Without This Integration:
| Old Way | New Way |
|---------|---------|
| "You'll need to check the carrier website" | Tracking visible in case view |
| Customer calls back: "Still nothing" | Agent sees delay proactively |
| Manual lookup in carrier portal | Automatic status updates |
| No proactive communication | SMS/Email when status changes |

### Business Impact:
- **"Where's my order?" calls**: #1 volume driver — reduce by 40%
- **Proactive notifications**: Customers informed before they call
- **Carrier integration**: Real-time data, not yesterday's snapshot
