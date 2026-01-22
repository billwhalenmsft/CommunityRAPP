# Lennox AES Mechanical Services - AI Solution Plan

## Executive Summary

**Customer:** Lennox AES (https://www.aesmech.com/)  
**Industry:** Commercial HVAC Mechanical Services  
**Challenge:** Complex multi-site quoting process for large retail customers (Walmart, Target, etc.)

### Current State Pain Points
1. **Manual Data Entry** - Customer sends Excel with 40-50+ store locations requiring quotes
2. **Repetitive Calculations** - Each store requires individual cost calculations for RTUs, AHUs, labor, materials
3. **Multiple Systems** - Data flows through Excel → SmartSheets → ComputerEase → QuickBooks → D365
4. **Time-Intensive** - Takeoff, pricing, sub quotes, bid compilation takes significant PM time
5. **Error Prone** - Manual transfer between systems introduces data quality risks

### Proposed AI Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AES MECH AI AGENT ECOSYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   EXCEL      │    │   ESTIMATE   │    │   QUOTE      │                  │
│  │   PARSER     │───▶│   CALCULATOR │───▶│   GENERATOR  │                  │
│  │   AGENT      │    │   AGENT      │    │   AGENT      │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                   │                           │
│         │                   ▼                   │                           │
│         │           ┌──────────────┐            │                           │
│         │           │  PRICING     │            │                           │
│         └──────────▶│  DATABASE    │◀───────────┘                           │
│                     │  AGENT       │                                        │
│                     └──────────────┘                                        │
│                            │                                                │
│         ┌──────────────────┼──────────────────┐                            │
│         ▼                  ▼                  ▼                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                    │
│  │  SUBCONTRACT │   │  D365 PROJECT│   │  WORKFLOW    │                    │
│  │  MANAGER     │   │  OPERATIONS  │   │  ORCHESTRATOR│                    │
│  │  AGENT       │   │  AGENT       │   │  AGENT       │                    │
│  └──────────────┘   └──────────────┘   └──────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Business Process Analysis

### Current Workflow (from Process Flow Diagram)

| Swim Lane | Step | System | Pain Point |
|-----------|------|--------|------------|
| **Sales** | Assess opportunity | Manual | Limited visibility |
| **Customer** | Send RFQ with scope | Excel | Unstructured data |
| **PM** | Log bid request | Excel | Manual entry |
| **PM** | Create bid folder | L: Drive | File management overhead |
| **PM** | Review pricing sheet | Excel | Manual calculations |
| **PM** | Takeoff for scope | Excel | Time-intensive |
| **PM** | Create bid sheet | Excel | Repetitive per store |
| **PM** | Request sub quotes | Email | Tracking difficulty |
| **PM** | Transfer to customer template | Excel | Copy/paste errors |
| **Project Admin** | Create job in CE | ComputerEase | Double entry |
| **Accounting** | Setup vendors | ComputerEase | Manual process |

### Target Workflow (AI-Assisted)

| Step | Agent | Automation Level |
|------|-------|------------------|
| Parse customer RFQ Excel | **Excel Parser Agent** | 95% automated |
| Calculate material/labor costs | **Estimate Calculator Agent** | 90% automated |
| Apply pricing rules | **Pricing Database Agent** | 100% automated |
| Request subcontractor quotes | **Subcontractor Manager Agent** | 80% automated |
| Generate customer bid | **Quote Generator Agent** | 90% automated |
| Create D365 project/quote | **D365 Project Ops Agent** | 85% automated |
| Orchestrate workflow | **Workflow Orchestrator Agent** | Full orchestration |

---

## Data Model Analysis

### Input: Customer RFQ Excel Structure

Based on the provided screenshots, the customer Excel contains:

```
Store Info:
├── Store #          (e.g., 547, 767, 956)
├── City             (e.g., Plant City, Melbourne, Ocala)
├── State            (e.g., FL, AL, CO, UT)
└── Drop Ceiling     (Y/N flag)

Scope Items (Quantities):
├── Remove/Replace RTU    (count)
├── Remove/Replace AHU    (count)
├── Remove/Cap RTU        (count)
├── New RTU Cut-in        (count)
├── New AHU Cut-in        (count)
└── Panel Point Reinf.    (count)

Comments (Free text describing additional scope):
├── "2for2 AHU, Add AHU w/ duct, (3) circuits, add gas line"
├── "31 RTUs, (2) SL Demo, (1) Circuit"
├── "11 RTUs, RTU>AHU conversion, Below roof CD, new circuit"
└── ... complex scope descriptions
```

### Pricing Model (from Cost Sheet)

```
Line Items:
├── Equipment:
│   ├── Remove/Replace RTU      $125.00/unit + $11 labor
│   ├── Remove/Replace AHU      $750.00/unit + $24 labor
│   ├── Remove/Cap RTU          $275.00/unit + $5 labor
│   ├── New RTU Cut-in          $1,200.00/unit + $40 labor
│   ├── New AHU Cut-in          $2,000.00/unit + $60 labor
│   ├── Panel Point Reinf.      $25.00/unit + $2 labor
│   └── ... (20+ line items)
│
├── Subcontractor/Rental:
│   ├── Roofer                  Variable
│   ├── Walkpads (Roofery)      Variable
│   ├── Sprinkler               Variable
│   ├── Electrical              Variable
│   ├── Fencing                 $5,500 typical
│   ├── Welding                 Variable
│   ├── Lift                    $5,000 typical
│   ├── Scissor                 $2,500 typical
│   ├── Dumpster                $2,000 typical
│   ├── Crane                   $35,000 (when needed)
│   └── Permit                  $2,500 typical
│
├── Labor:
│   ├── Total Hours             60 typical
│   ├── Wage                    $30.00/hr
│   ├── Fringe                  2.70
│   ├── ST Burden               15.00%
│   ├── OT Burden               0.00%
│   └── Per Diem                $130/day × Crew × Duration
│
└── Margins:
    ├── OH                      25.00%
    ├── Sales Tax               10.00%
    ├── Shortfall               10.00%
    └── Profit                  40.00%
```

### Output: D365 Project Operations Structure

```
Project:
├── Project Number
├── Customer Account (Walmart, Target, etc.)
├── Project Name (Store # + City)
├── Start/End Dates
└── Project Manager

Quote:
├── Quote Header
├── Quote Lines (per scope item)
├── Cost Estimates
├── Pricing (with margins)
└── Approval Status

Resources:
├── Crew Assignments
├── Equipment Bookings
└── Subcontractor POs
```

---

## Agent Specifications

### 1. Excel Parser Agent (`aes_excel_parser_agent`)

**Purpose:** Extract structured data from customer RFQ Excel files

**Capabilities:**
- Parse multi-store project lists
- Extract scope quantities per store
- Interpret comment fields for additional scope
- Validate data completeness
- Flag anomalies or unclear items

**Actions:**
| Action | Description |
|--------|-------------|
| `parse_rfq` | Parse customer RFQ Excel file |
| `extract_stores` | Get list of all stores with basic info |
| `extract_scope` | Get detailed scope for a specific store |
| `interpret_comments` | AI interpretation of comment field |
| `validate_data` | Check for missing/invalid data |

---

### 2. Estimate Calculator Agent (`aes_estimate_calculator_agent`)

**Purpose:** Calculate cost estimates based on scope and pricing rules

**Capabilities:**
- Apply unit pricing to quantities
- Calculate labor hours and costs
- Determine equipment/rental needs
- Apply regional adjustments
- Calculate per diem and travel

**Actions:**
| Action | Description |
|--------|-------------|
| `calculate_store` | Full estimate for one store |
| `calculate_batch` | Estimates for multiple stores |
| `get_material_cost` | Material cost for scope items |
| `get_labor_cost` | Labor cost calculation |
| `get_equipment_needs` | Determine rental equipment |
| `apply_margins` | Apply OH, profit, taxes |

---

### 3. Pricing Database Agent (`aes_pricing_database_agent`)

**Purpose:** Manage and retrieve pricing data

**Capabilities:**
- Store current pricing tables
- Regional price adjustments
- Historical pricing lookups
- Update pricing rules
- Customer-specific pricing

**Actions:**
| Action | Description |
|--------|-------------|
| `get_unit_price` | Get price for a line item |
| `get_labor_rate` | Get labor rate by region |
| `get_rental_rate` | Get equipment rental rates |
| `update_pricing` | Update pricing table |
| `get_customer_pricing` | Customer-specific rates |

---

### 4. Subcontractor Manager Agent (`aes_subcontractor_agent`)

**Purpose:** Manage subcontractor quotes and relationships

**Capabilities:**
- Request quotes from subs
- Track quote responses
- Compare sub pricing
- Store preferred vendors by region
- Generate PO information

**Actions:**
| Action | Description |
|--------|-------------|
| `request_quote` | Send quote request to sub |
| `list_subs` | List subs by trade/region |
| `track_quotes` | Check outstanding quotes |
| `compare_quotes` | Compare received quotes |
| `select_sub` | Select sub for scope item |

---

### 5. Quote Generator Agent (`aes_quote_generator_agent`)

**Purpose:** Generate formatted customer bid documents

**Capabilities:**
- Create summary bid sheets
- Generate detailed breakdowns
- Format per customer template
- Apply discount tiers
- Version control bids

**Actions:**
| Action | Description |
|--------|-------------|
| `generate_summary` | Create bid summary sheet |
| `generate_detail` | Detailed per-store breakdown |
| `apply_discount` | Apply discount percentage |
| `format_for_customer` | Customer-specific format |
| `compare_rounds` | Compare 1st/2nd round bids |

---

### 6. D365 Project Operations Agent (`aes_d365_project_ops_agent`)

**Purpose:** Create and manage projects/quotes in Dynamics 365

**Capabilities:**
- Create projects from estimates
- Generate quote records
- Sync scope items as quote lines
- Update project status
- Export project data

**Actions:**
| Action | Description |
|--------|-------------|
| `create_project` | Create D365 project |
| `create_quote` | Create quote from estimate |
| `add_quote_lines` | Add line items to quote |
| `update_status` | Update project/quote status |
| `sync_estimate` | Sync RAPP estimate to D365 |

---

### 7. Workflow Orchestrator Agent (`aes_workflow_orchestrator_agent`)

**Purpose:** Coordinate the end-to-end bidding process

**Capabilities:**
- Track bid status across stores
- Coordinate agent workflows
- Send notifications
- Manage approvals
- Report on pipeline

**Actions:**
| Action | Description |
|--------|-------------|
| `start_bid` | Initiate new bid process |
| `get_status` | Check bid status |
| `advance_stage` | Move to next workflow stage |
| `notify` | Send notifications |
| `get_pipeline` | View bid pipeline |

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create `aes_pricing_database_agent` with current pricing
- [ ] Create `aes_estimate_calculator_agent` with calculation logic
- [ ] Test with sample store data from screenshots

### Phase 2: Input/Output (Weeks 3-4)
- [ ] Create `aes_excel_parser_agent` for RFQ parsing
- [ ] Create `aes_quote_generator_agent` for bid output
- [ ] End-to-end test: Excel → Estimate → Quote

### Phase 3: Integration (Weeks 5-6)
- [ ] Create `aes_d365_project_ops_agent` for D365 integration
- [ ] Create `aes_subcontractor_agent` for sub management
- [ ] Connect to D365 Project Operations APIs

### Phase 4: Orchestration (Weeks 7-8)
- [ ] Create `aes_workflow_orchestrator_agent`
- [ ] Build approval workflows
- [ ] Dashboard and reporting

---

## Sample Calculations

### Store Example: Store #547 - Plant City, FL

**Scope from Excel:**
- Remove/Replace RTU: 0
- Remove/Replace AHU: 2
- New RTU Cut-in: 0
- New AHU Cut-in: 1
- Panel Points: 0
- Comments: "2for2 AHU, Add AHU w/ duct, (3) circuits, add gas line"

**Cost Calculation:**
```
Materials:
  Remove/Replace AHU (2):     $750 × 2 = $1,500
  New AHU Cut-in (1):         $2,000 × 1 = $2,000
  Circuits (3):               ~$400 × 3 = $1,200
  Gas Line:                   ~$500 = $500
  Material Subtotal:          $5,200

Labor:
  AHU Work: ~24 hrs           $30 × 24 = $720
  Cut-in Work: ~60 hrs        $30 × 60 = $1,800
  Fringe + Burden:            ~$550
  Labor Subtotal:             $3,070

Subcontractor/Rental:
  Lift:                       $5,000
  Dumpster:                   $2,000
  Permit:                     $2,500
  Sub Subtotal:               $9,500

Per Diem/Travel:
  5 crew × 4 days × $130:     $2,600
  Travel:                     $3,000
  Per Diem Subtotal:          $5,600

Subtotals:
  Direct Costs:               $23,370
  OH (25%):                   $5,843
  Sales Tax (10%):            $2,921
  Shortfall (10%):            $3,213
  Profit (40%):               $14,139
  
  TOTAL BID:                  ~$49,486

(Actual bid from sheet: $535,000 - suggests much larger scope in comments)
```

---

## Technical Requirements

### Azure Services
- **Azure Functions** - RAPP agent hosting
- **Azure Cosmos DB** - Pricing database, bid storage
- **Azure Blob Storage** - Excel file storage
- **Azure Logic Apps** - D365 integration workflows
- **Power Automate** - Notification flows

### D365 Integration
- **Dataverse API** - Project/Quote creation
- **Project Operations** - Resource scheduling
- **Finance & Operations** - Customer/Vendor data

### Security
- **Azure AD** - Authentication
- **Key Vault** - API credentials
- **RBAC** - Role-based access

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to create bid (per store) | 2-4 hours | 15-30 minutes |
| Calculation errors | 5-10% | <1% |
| Sub quote turnaround | 3-5 days | 1-2 days |
| D365 data entry time | 30 min/store | Automated |
| Bid cycle time | 2-3 weeks | 1 week |

---

## Next Steps

1. **Discovery Call** - Validate assumptions with AES team
2. **Data Collection** - Gather sample Excel files, pricing sheets
3. **D365 Analysis** - Map Project Operations entities
4. **Prototype** - Build estimate calculator agent first
5. **Pilot** - Test with one small bid (5-10 stores)

---

## Appendix: Pricing Table Reference

| Item | Material/Unit | Labor/Unit | Labor Hours |
|------|---------------|------------|-------------|
| Remove/Replace RTU | $125.00 | $11.00 | 0.37 |
| Remove/Replace AHU | $750.00 | $24.00 | 0.80 |
| Remove/Cap RTU | $275.00 | $5.00 | 0.17 |
| New RTU Cut-in | $1,200.00 | $40.00 | 1.33 |
| New AHU Cut-in | $2,000.00 | $60.00 | 2.00 |
| Panel Point Reinf. | $25.00 | $2.00 | 0.07 |
| Joist Reinforcement | $1,000.00 | $20.00 | 0.67 |
| New Controller | $550.00 | $20.00 | 0.67 |
| Reconnect Line Voltage | $125.00 | $2.00 | 0.07 |
| Reconnect Low Voltage | $100.00 | $2.00 | 0.07 |
| Rewire EMS (1000 points) | $350.00 | $20.00 | 0.67 |
| Reconnect RTU Gas | $400.00 | $4.00 | 0.13 |
| Reconnect AHU Gas | $900.00 | $8.00 | 0.27 |
| New Ductwork (LF) | $50.00 | $1.00 | 0.03 |
| New Grilles (EA) | $65.00 | $1.00 | 0.03 |
| Demo Ductwork (LF) | $5.00 | $0.50 | 0.02 |
| Start-Up | $0.00 | $4.00 | 0.13 |
| Punch-Out | $0.00 | $4.00 | 0.13 |
| Replace DB | $500.00 | $20.00 | 0.67 |
| Replace Fuses/Unit | $150.00 | $1.00 | 0.03 |
| Replace Breakers | $900.00 | $2.00 | 0.07 |
| Skylight Demo | $200.00 | $24.00 | 0.80 |

---

*Document Version: 1.0*  
*Created: January 16, 2026*  
*Author: RAPP AI Solution Architect*
