# Navico Self-Service Assistant — Prompting & Testing Guide

> Use this guide to test the agent in Copilot Studio or demo it live. Each scenario includes the exact prompts to type and what you should see.

---

## Quick Test — All Topics in 5 Minutes

| # | Type This | Expected Response |
|---|-----------|-------------------|
| 1 | *(start conversation)* | Welcome to **Navico Group Support** with 6 capability options |
| 2 | `My Simrad screen won't turn on` | Asks for serial number → power diagnostics |
| 3 | `SIM-2024-NSX-10042` | Asks what type of issue → provides power diagnostic steps |
| 4 | `No that didn't help` | Offers to connect with live agent, passes serial + context |
| 5 | *(start over)* | |
| 6 | `Is my product still under warranty?` | Asks for serial → shows warranty info → offers next steps |
| 7 | *(start over)* | |
| 8 | `I want to register my new Lowrance` | Asks serial → purchase date → installer type → escalates to complete |
| 9 | *(start over)* | |
| 10 | `What's my dealer certification status?` | Offers: check/enroll/renew/learn |
| 11 | *(start over)* | |
| 12 | `I want to talk to someone` | Transfers to live agent with context |

---

## Scenario 1: Product Troubleshooting (Power Issue)

**Story:** A B2B customer's Simrad NSX won't power on.

```
You:    My Simrad NSX 3007 isn't turning on
Agent:  [Asks for serial number]

You:    SIM-2024-NSX-10042
Agent:  [Asks what type of issue - power/software/connectivity/other]

You:    Power issue
Agent:  [5-step power diagnostic: check power supply, inspect wiring, check fuses, 
         hard reset, disconnect peripherals]

You:    I tried all of that but it still won't turn on
Agent:  [Offers to connect with specialist, passes serial + issue type + steps attempted]
```

---

## Scenario 2: Firmware Recovery

**Story:** A customer's unit is bricked after a firmware update.

```
You:    Firmware update bricked my Lowrance HDS
Agent:  [Asks for serial number]

You:    LWR-2024-HDS-88821
Agent:  [Asks issue type]

You:    Firmware problem
Agent:  [Recovery steps: hard reset → physical buttons → SD card recovery → factory reset]

You:    The SD card recovery worked!
Agent:  [Glad I could help! Asks if anything else needed]
```

---

## Scenario 3: Connectivity / NMEA 2000

**Story:** A B&G customer's instruments aren't talking to each other.

```
You:    My B&G instruments aren't showing data on my MFD
Agent:  [Asks for serial number]

You:    BG-2024-TRI2-20011
Agent:  [Asks issue type]

You:    Connectivity
Agent:  [Diagnostics by connection type: NMEA 2000 backbone power, terminators, 
         T-connectors, fuse; Ethernet cables; WiFi range]

You:    It's a NMEA 2000 issue - the backbone has no power
Agent:  [More specific guidance on backbone power troubleshooting]
```

---

## Scenario 4: Warranty Check

**Story:** A customer wants to know if their product is covered.

```
You:    Is my Lowrance still under warranty?
Agent:  [Asks for serial number]

You:    LWR-2024-HDS-88821
Agent:  [Shows warranty info: standard = 2 years, what's covered/not covered]
        [Offers 3 options: connect with specialist, extended warranty, start a return]

You:    I'd like to learn about extended warranty options
Agent:  [Explains: Extended Warranty, Premium Service, Fleet Coverage]
        [Offers to connect with specialist to discuss]
```

---

## Scenario 5: RMA Request

**Story:** A customer needs to return a defective unit.

```
You:    I need to return my Simrad radar for a replacement
Agent:  [Asks for serial number]

You:    SIM-2024-NSX-10042
Agent:  [Shows warranty info, then offers next steps]

You:    I want to start a return
Agent:  [Explains 4 RMA types: Exchange, Credit, Repair, OBS]
        [Transfers to specialist for actual processing with serial + context]
```

---

## Scenario 6: Product Registration

**Story:** A dealer just installed a new system and needs to register it.

```
You:    I need to register a new Simrad NSX we just installed
Agent:  [Asks for serial number]

You:    SIM-2024-NSX-10055
Agent:  [Asks for purchase date]

You:    Last week, April 7th
Agent:  [Asks: professionally installed or self-installed?]

You:    Professional - I'm a certified installer
Agent:  [Acknowledges System Assembly Assurance qualification]
        [Transfers to specialist to complete registration + verify certification]
```

**B2C version:**
```
You:    I want to register my new Lowrance fish finder
Agent:  [Same flow but without System Assembly Assurance]

You:    I installed it myself
Agent:  [Summary: serial, date, self-installed]
        [Transfers to complete: create asset, activate 2-year warranty, send confirmation]
```

---

## Scenario 7: Certification Inquiry (B2B)

**Story:** A dealer wants to check their certification status.

```
You:    What's my certification status?
Agent:  [Offers 4 options: check status, enroll, renew, learn about program]

You:    Check my status
Agent:  [Explains they'll connect with specialist to look up Contact record]
        [Transfers to agent]
```

**Enrollment version:**
```
You:    How do I get certified as a Navico installer?
Agent:  [Offers options]

You:    I want to enroll
Agent:  [Explains 3 levels: Basic (80%), Advanced (85%), Expert (90%)]
        [Directs to Navico Certification Portal]
        [Explains: exam creates a tracked case, certification updates contact record]
```

**Renewal version:**
```
You:    My certification is about to expire
Agent:  [Offers options]

You:    Renew
Agent:  [Explains: Basic/Advanced = 12 months, Expert = 24 months]
        [60-day renewal notice, 90-day grace period]
        [Warns: expired certs may affect support tier]
```

---

## Scenario 8: Safety Escalation

**Story:** A customer reports a safety-critical situation.

```
You:    My navigation system failed while I'm at sea
Agent:  [IMMEDIATE escalation — does NOT attempt troubleshooting]
        [Acknowledges urgency, advises emergency services if needed]
        [Transfers to live agent with URGENT priority]
```

**Other safety triggers to test:**
- `Man overboard equipment isn't working`
- `My vessel's navigation has completely failed`
- `We're lost at sea and the GPS is down`

---

## Scenario 9: Escalation

**Story:** Customer just wants a human.

```
You:    I want to talk to a real person
Agent:  [Transfers immediately with conversation context]
        [Agent sees full transcript]
```

**Other escalation triggers:**
- `Connect me to a live agent`
- `Can I speak to a representative?`
- `This isn't helping, I need a specialist`
- `Talk to tech support`

---

## Scenario 10: Fallback (Unknown Intent)

**Story:** Testing what happens when the agent doesn't understand.

```
You:    asdfghjkl
Agent:  [Shows capability menu: troubleshoot, warranty, RMA, registration, certification]

You:    blah blah blah
Agent:  [Shows capability menu again]

You:    still not making sense
Agent:  [Apologizes and transfers to live agent after 3rd failure]
```

---

## Demo Tips

### Setting the Scene
> *"Navico currently uses an Optimizely portal with no self-service or AI capabilities. Their ServiceTarget Q&A system is outdated. What you're about to see is an AI-powered self-service agent that handles 60% of their support volume — troubleshooting, warranty, and registration — without a human."*

### Key Moments to Highlight

1. **Serial number intelligence** — "Notice the agent asks for the serial number first. That one data point identifies the brand, product, warranty status, and customer tier."

2. **Guided diagnostics** — "Instead of a static FAQ, the agent walks through step-by-step troubleshooting customized to the issue type."

3. **Graceful escalation** — "When the bot can't resolve it, it transfers to a live agent with FULL context — serial number, issue type, every step already tried. The customer never repeats themselves."

4. **B2B awareness** — "The same agent handles a Platinum Expert dealer checking certification and a consumer asking about warranty. Different tone, same platform."

5. **Safety override** — "Marine electronics are safety-critical. Watch what happens when I mention a navigation failure at sea — immediate escalation, no troubleshooting. You can't mess with safety."

6. **KB-powered** — "The agent answers from the same knowledge articles your CSRs use. One source of truth, consistent answers whether it's self-service or agent-assisted."

### Conversation Starters (Pre-Built)
The agent has 5 quick-start buttons when the chat opens:
- 🔧 Troubleshoot my product
- 📋 Check warranty status
- 🔄 Request a return or exchange
- 📝 Register my product
- 🎓 Certification status
