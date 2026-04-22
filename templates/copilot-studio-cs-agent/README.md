# Customer Service Self-Service Agent — Reusable Template

## What This Is

A **golden base agent** for D365 Customer Service demos that can be deployed to any customer's Copilot Studio environment. It handles the universal self-service flows that apply to virtually every product-support demo.

## Core Capabilities (Built-In)

| Topic | Flow | Applies To |
|-------|------|------------|
| **Product Troubleshoot** | Serial → issue type (power/software/connectivity/performance) → guided diagnostics → resolve or escalate | Any product company |
| **Warranty Check** | Serial → warranty info → next steps (specialist, extended, return) | Any company with warranties |
| **Product Registration** | Serial + purchase date + installer type → escalate to complete | Any product company |
| **Escalate** | Direct transfer to live agent with full context | Universal |
| **Fallback** | Retry twice → capability menu → escalate on 3rd failure | Universal |

## How to Use for a New Customer

### Quick Start (5 minutes)
1. **Create agent** in Copilot Studio using the `agent.mcs.yml` instructions
2. **Connect knowledge** — add Dataverse knowledge articles as a knowledge source
3. **Connect to Omnichannel** — add the bot to a chat workstream
4. **Embed on portal** — add chat widget to Power Pages

### Customization Checklist

When adapting for a specific customer, update these areas:

| Area | What to Change | Example |
|------|---------------|---------|
| **Agent Instructions** | Add company name, brand list, product types, serial prefix patterns, customer tiers | Navico: "SIM- = Simrad, LWR- = Lowrance..." |
| **Safety Keywords** | Add industry-specific safety/escalation triggers | Marine: "Man Overboard, Navigation Failure" |
| **Welcome Message** | Brand the greeting in ConversationStart.mcs.yml | "Welcome to Navico Group Support!" |
| **Troubleshoot Steps** | Add product-specific diagnostic steps per issue type | NMEA 2000 backbone checks for marine |
| **Warranty Details** | Update coverage periods, contract types, tier definitions | "2 years standard, 5 years extended" |
| **KB Article References** | List the customer's specific KB article numbers in instructions | "KA-01268: Fault Diagnosis..." |
| **Conversation Starters** | Update to match customer terminology | "Check certification status" for B2B |
| **Additional Topics** | Add customer-specific topics as needed | Certification for Navico, Compliance for Otis |

### Customer-Specific Additions

These topics are NOT in the base template because they're industry-specific. Add them when needed:

| Optional Topic | When to Add | Example Customer |
|---------------|-------------|-----------------|
| **Certification Inquiry** | B2B customers with dealer/partner cert programs | Navico, Zurn |
| **Order Status** | Customers with distribution/order management | Zurn Elkay |
| **Service Scheduling** | Field service customers | Otis, Lennox |
| **Compliance Check** | Regulated industries | Otis (elevator codes), Healthcare |
| **Parts Ordering** | Customers with replacement parts catalogs | Sub-Zero, Milwaukee |

## File Structure

```
templates/copilot-studio-cs-agent/
├── agent.mcs.yml                          # Agent definition + instructions
├── topics/
│   ├── ConversationStart.mcs.yml          # Welcome greeting
│   ├── ProductTroubleshoot.mcs.yml        # Guided diagnostics (universal)
│   ├── WarrantyCheck.mcs.yml              # Warranty lookup + next steps
│   ├── ProductRegistration.mcs.yml        # Registration intake
│   ├── Escalate.mcs.yml                   # Live agent handoff
│   └── Fallback.mcs.yml                   # Unknown intent handler
└── README.md                              # This file
```

## Customer Implementations

| Customer | Location | Additions Over Base |
|----------|----------|-------------------|
| **Navico** | `customers/navico/d365/copilot-studio/` | Certification topic, NMEA 2000 diagnostics, marine safety override, 5-brand context, System Assembly Assurance |
| **Zurn Elkay** | `customers/zurnelkay/d365/demo-assets/copilot-studio-setup.md` | Product-specific troubleshooting (flush valves, drains, faucets), order management |
| **Otis** | `customers/otis/d365/copilot-studio/` | Entrapment response, SLA-tier routing, healthcare protocols |

## Architecture

```
Customer (Power Pages Portal)
    |
    v
Chat Widget (Omnichannel)
    |
    v
Copilot Studio Agent (this template)
    |-- Generative answers from KB articles
    |-- Guided troubleshooting topics
    |-- Serial-based warranty lookup
    |-- Product registration intake
    |
    v (escalate)
Omnichannel Routing
    |-- Customer tier-based queue assignment
    |-- Skills matching
    |-- Capacity check
    |
    v
CSR (Customer Service Workspace)
    |-- Full bot transcript visible
    |-- Customer 360 context
    |-- Copilot Agent Assist (KB, intent, suggestions)
    |-- Case auto-created with chat context
```

## Deployment Options

1. **Manual (browser)** — Create agent in Copilot Studio web editor, paste instructions and recreate topics
2. **VS Code Extension** — Clone the agent locally, copy these YAML files, push back via extension
3. **API (bulk)** — Use `scripts/deploy_to_copilot_studio.py` for programmatic deployment
