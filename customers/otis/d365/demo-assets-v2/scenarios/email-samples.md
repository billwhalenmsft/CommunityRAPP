# Otis — Email Demo Samples

> **Customer**: Otis Elevator Company
> **Channel**: Email → Case Auto-Creation
> **Support Inbox**: support@company.com

---

## How Email-to-Case Works

1. Customer sends email to support inbox
2. D365 automatically creates a case
3. AI analyzes sentiment and extracts key info
4. Case routes to appropriate queue based on content
5. Hot words trigger priority escalation

---

## Email 1: Standard Inquiry

### Email Details

| Field | Value |
|-------|-------|
| From | David Park <dpark@metroplex.com> |
| To | support@company.com |
| Subject | Question about product specifications |
| Account | Metroplex Industries |

### Email Body

```
Hello,

I'm looking at your product catalog and have a question about the specifications
for model XYZ-500. The datasheet mentions it supports up to 1000 PSI, but I need
to verify this will work for our industrial application.

Can you also confirm lead time for orders of 50+ units?

Thanks,
David Park
Metroplex Industries
```

### Expected Behavior
- Case created with **Normal Priority**
- Sentiment: **Neutral**
- Category: Product Inquiry
- Routes to: Standard Queue

---

## Email 2: URGENT / High-Sentiment

### Email Details

| Field | Value |
|-------|-------|
| From | Patricia Hayes <p.hayes@facilitygroup.com> |
| To | support@company.com |
| Subject | URGENT - Product Failure / Possible Safety Issue |
| Account | Facility Management Group |

### Email Body (with Hot Words)

```
To whom it may concern,

This is UNACCEPTABLE. We installed your equipment last month and it has already
failed during a critical operation. Our team had to shut down the entire line.

I am FURIOUS about this. We've been a loyal customer for 15 years and this is
how we're treated? If we don't get a resolution immediately, I will be speaking
with our ATTORNEY about damages.

I need a callback TODAY.

Patricia Hayes
Operations Director
Facility Management Group
```

### Expected Behavior
- Case created with **HIGH Priority**
- Sentiment: **Negative** (flagged)
- Hot words detected: UNACCEPTABLE, FURIOUS, ATTORNEY
- Routes to: Escalation Queue
- Supervisor notification triggered

---

## Email 3: RMA / Return Request

### Email Details

| Field | Value |
|-------|-------|
| From | Shipping Coordinator <receiving@metroplexindustries.com> |
| To | support@company.com |
| Subject | Request for Return Authorization - PO #98765 |
| Account | Metroplex Industries |

### Email Body

```
Hello Support Team,

We received our shipment today (PO #98765) but unfortunately one of the items
arrived damaged in transit. The packaging was crushed and the unit is dented.

Please provide an RMA number so we can return this item for replacement.

Photos attached.

Thank you,
Receiving Department
Metroplex Industries
```

### Expected Behavior
- Case created with **Normal Priority**
- Case Type: **Return/RMA**
- Sentiment: **Neutral** (factual tone)
- Routes to: RMA Queue
- Related PO extracted: #98765

---

## Hot Words List

These words trigger priority escalation:

- Entrapment
- Trapped
- Emergency
- Safety Hazard
- Fire
- Stuck

---

## Demo Talk Track

💬 **For Standard Email:**
> "Here's a typical product inquiry email. Watch how D365 automatically creates 
> a case, extracts the key information, and routes it to the right queue based on content."

💬 **For Urgent Email:**
> "Now let's look at an urgent email with strong language. Watch how the system 
> detects the negative sentiment and hot words like 'attorney' and 'unacceptable'. 
> This immediately escalates to a priority queue and alerts a supervisor."

💬 **Key Point:**
> "AI analyzes every incoming email for sentiment and keywords, ensuring urgent 
> issues get immediate attention while routine queries follow standard workflow."
