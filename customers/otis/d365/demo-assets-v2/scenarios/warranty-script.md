# Otis — Warranty Lookup & Claims Demo Script

> **Customer**: Otis Elevator Company
> **Scenario**: Warranty Verification and Claim Processing
> **Agent Persona**: Agent

---

## Scenario Overview

**Customer Request**: "I have a product that stopped working. Is it still under warranty?"

**What to Demonstrate:**
- Instant warranty lookup by serial number
- Coverage verification (parts, labor, dates)
- Claim initiation workflow
- Service options (repair, replace, on-site)

---

## Pre-Demo Setup

### Ensure You Have:
- [ ] Sample product with warranty registration
- [ ] Warranty lookup custom page available
- [ ] Coverage details populated (start/end dates)
- [ ] Service option picklist configured

---

## Act 1: Warranty Inquiry

**Customer**: "I bought a unit about a year ago and it just stopped working. Do I need to pay for repairs?"

**Agent**: "Let me look up your warranty status. Do you have the serial number?"

**Customer**: "It's SN-ABC-123456."

**Action**: Open the **Warranty Lookup** tool and search by serial number.

💬 **Talk Track:**
> "I can check warranty status instantly using the serial number. 
> Let me look that up for you..."

---

## Act 2: Warranty Status Display

**What to Show (Warranty Details Panel):**

| Field | Value |
|-------|-------|
| Serial Number | SN-ABC-123456 |
| Product | Industrial Widget Pro |
| Purchase Date | [13 months ago] |
| Standard Warranty | 2 Years |
| Extended Warranty | N/A |
| Coverage End Date | [11 months from now] |
| **Status** | ✅ **ACTIVE** |

**Coverage Details:**

| Parts | ✅ Covered |
| Labor | ✅ Covered |
| On-Site Service | ✅ Available |
| Shipping (In/Out) | ✅ Prepaid |

💬 **Talk Track:**
> "Great news — your product is still under the original warranty for another 
> 11 months. Parts and labor are both covered. Let me help you get this resolved."

---

## Act 3: Service Options

**Agent**: "Since you're covered, here are your options..."

**Service Options Panel:**

| Option | Description | Estimated Time |
|--------|-------------|----------------|
| **Depot Repair** | Ship to service center | 7-10 business days |
| **On-Site Service** | Technician visits you | 2-3 business days |
| **Advance Exchange** | We ship replacement first | 1-2 business days |

💬 **Talk Track:**
> "You can ship it to us for repair, we can send a technician to you, 
> or since this is a common issue, I can send a replacement unit today 
> and you ship the defective one back."

---

## Act 4: Claim Initiation (Hero Moment)

**Customer**: "The advance exchange sounds great. Let's do that."

**Action**: Initiate warranty claim with advance exchange option.

**What to Show (Claim Form):**
1. Defect type selection (dropdown)
2. Symptom description (free text)
3. Service option: Advance Exchange
4. Shipping address confirmation
5. **Submit Claim** button

**Automatic Actions on Submit:**
- ✅ Warranty Claim # Generated: WC-2024-007891
- ✅ Replacement Order Created
- ✅ Return Shipping Label Generated
- ✅ Customer Email with Tracking Info
- ✅ Hold Placed on Customer Account (released on return receipt)

💬 **Talk Track:**
> "Done — I've initiated the advance exchange. Your replacement ships today. 
> You'll get an email with the tracking number and a return label for the 
> defective unit. Just drop it off at any UPS location within 10 days."

---

## Act 5: Warranty Expiration Scenario (Alternative)

**What if warranty is expired?**

| Field | Value |
|-------|-------|
| Coverage End Date | [6 months ago] |
| **Status** | ❌ **EXPIRED** |

**Options to Present:**

1. **Out-of-Warranty Repair**: $175 flat rate
2. **Extended Warranty Purchase**: $99/year (covers future issues)
3. **Trade-In / Upgrade**: 15% discount on new model

💬 **Talk Track (Expired):**
> "I see the warranty expired 6 months ago, but let me check our options. 
> We have a flat-rate repair at $175. Or, since your model is a few years old, 
> you might consider upgrading — I can offer 15% off the new model."

---

## Key Points to Emphasize

### Without This Integration:
| Old Way | New Way |
|---------|---------|
| "Let me check with our warranty department..." | Instant lookup by serial |
| Customer waits on hold for verification | Coverage displayed in seconds |
| Manual claim form (fax, email, portal) | One-click claim initiation |
| Separate call to schedule service | Service options shown immediately |

### Business Value:
- **Warranty inquiries**: Resolved in < 5 minutes
- **Advance exchange**: Higher NPS vs. depot repair
- **Upsell opportunity**: Extended warranty, upgrades for expired units
- **Reduced fraud**: Serial validation with purchase history
