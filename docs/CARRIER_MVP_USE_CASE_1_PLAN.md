# Carrier MVP Use Case 1: Internal Customer Service Case Triage Agent

## Status: ✅ COMPLETE

**All 7 agents built and ready for demo!**

## Strategic Context

**Customer:** Carrier  
**Competitive Situation:** Salesforce (Agentforce) has been engaged since July 2025 with rapid prototyping  
**Opportunity:** Demonstrate Microsoft AI Agent superiority through faster time-to-value  
**Timeline:** MVP ready for demo

---

## Integration Configuration

| Integration | Status | Endpoint |
|-------------|--------|----------|
| **Salesforce** | ✅ Active | `https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com/` |
| Product API | 🔶 Stubbed | `[FUTURE: Internal product lookup]` |
| Install Base API | 🔶 Stubbed | `[FUTURE: Customer install base data]` |
| Warranty API | 🔶 Stubbed | `[FUTURE: Warranty status check]` |
| Service History API | 🔶 Stubbed | `[FUTURE: Past service records]` |  

---

## Problem Statement

Customer service cases in Salesforce often sit untriaged for days, increasing SLA risk and driving unnecessary call volume. Agents spend significant time manually reading cases, extracting context, and deciding next steps.

### Current Pain Points
| Pain Point | Business Impact |
|------------|-----------------|
| Cases sit untriaged for days | SLA breaches, customer dissatisfaction |
| Manual case reading | Agent time wasted on intake vs resolution |
| Missing context extraction | Inconsistent case handling |
| No proactive enrichment | Repeated customer callbacks for info |
| No recommended actions | Slower resolution times |

---

## Solution: AI Agent Swarm Architecture

We will build a **6-agent swarm** that works together to automate case triage:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CASE TRIAGE ORCHESTRATOR                            │
│                    (Coordinates all agent activities)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   SALESFORCE  │           │    CASE       │           │   PRODUCT     │
│    MONITOR    │──────────▶│   ANALYZER    │──────────▶│   ENRICHMENT  │
│     AGENT     │           │    AGENT      │           │     AGENT     │
└───────────────┘           └───────────────┘           └───────────────┘
        │                             │                             │
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  ATTACHMENT   │           │   SUMMARY     │           │  SALESFORCE   │
│   PROCESSOR   │           │  GENERATOR    │           │    WRITER     │
│     AGENT     │           │    AGENT      │           │     AGENT     │
└───────────────┘           └───────────────┘           └───────────────┘
```

---

## Agent Inventory

### Agent 1: Case Triage Orchestrator Agent
**File:** `carrier_case_triage_orchestrator_agent.py`  
**Demo:** `carrier_case_triage_orchestrator_agent.json`

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Coordinates the entire case triage workflow |
| **Trigger** | Scheduled (every 5 min) or on-demand |
| **Inputs** | Time window, priority filter, case queue |
| **Outputs** | Orchestration status, processed case count |
| **Calls** | All other agents in sequence |

**Actions:**
- `start_triage_cycle` - Begin a new triage cycle for cases
- `get_cycle_status` - Check current triage cycle progress
- `process_single_case` - Triage a specific case ID
- `get_triage_metrics` - Get triage performance metrics
- `configure_triage_rules` - Update triage configuration

---

### Agent 2: Salesforce Case Monitor Agent
**File:** `carrier_sf_case_monitor_agent.py`  
**Demo:** `carrier_sf_case_monitor_agent.json`

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Monitors newly created and aging Salesforce cases |
| **Trigger** | Called by Orchestrator |
| **Inputs** | Time window, case status filters |
| **Outputs** | List of cases needing triage |
| **Integrations** | Salesforce REST API |

**Actions:**
- `get_new_cases` - Retrieve cases created in last N minutes
- `get_aging_cases` - Find cases approaching SLA breach
- `get_untriaged_cases` - Find cases without triage data
- `get_case_details` - Get full case record with attachments
- `get_case_history` - Retrieve case update history

**Key Queries:**
```sql
-- New cases needing triage
SELECT Id, CaseNumber, Subject, Description, CreatedDate, Status, Priority
FROM Case 
WHERE CreatedDate > :lastCheckTime 
  AND TriageStatus__c = null
  
-- Aging cases at SLA risk
SELECT Id, CaseNumber, Subject, SLA_Deadline__c, CreatedDate
FROM Case
WHERE Status NOT IN ('Closed', 'Resolved')
  AND SLA_Deadline__c < :slaWarningTime
```

---

### Agent 3: Case Analyzer Agent
**File:** `carrier_case_analyzer_agent.py`  
**Demo:** `carrier_case_analyzer_agent.json`

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Extracts key issue details from case text |
| **Trigger** | Called by Orchestrator for each case |
| **Inputs** | Case subject, description, comments |
| **Outputs** | Extracted entities, issue type, urgency |
| **AI Model** | GPT-4o for text analysis |

**Actions:**
- `analyze_case_text` - Extract entities and intent from case text
- `classify_issue_type` - Determine case category (HVAC, Controls, Parts, etc.)
- `detect_urgency` - Assess true urgency beyond stated priority
- `extract_product_references` - Find product models, serial numbers
- `identify_customer_sentiment` - Gauge customer frustration level

**Extraction Schema:**
```json
{
  "issue_type": "HVAC | Controls | Parts | Installation | Warranty | Other",
  "sub_category": "string",
  "product_mentioned": ["model numbers", "serial numbers"],
  "symptoms": ["list of described symptoms"],
  "customer_ask": "what the customer wants",
  "urgency_indicators": ["downtime", "safety", "production impact"],
  "calculated_urgency": "Critical | High | Medium | Low",
  "sentiment_score": 0.0-1.0,
  "key_entities": {
    "location": "string",
    "equipment": "string",
    "contact": "string"
  }
}
```

---

### Agent 4: Attachment Processor Agent
**File:** `carrier_attachment_processor_agent.py`  
**Demo:** `carrier_attachment_processor_agent.json`

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Extracts information from case attachments |
| **Trigger** | Called by Orchestrator if attachments exist |
| **Inputs** | Attachment IDs, file types |
| **Outputs** | Extracted text, images analyzed, document summaries |
| **AI Model** | GPT-4o Vision for images, Document Intelligence for docs |

**Actions:**
- `process_attachments` - Process all attachments for a case
- `extract_image_info` - Analyze images (error codes, equipment photos)
- `extract_document_text` - OCR and parse PDFs/documents
- `analyze_error_codes` - Identify error codes from photos
- `summarize_attachments` - Create unified attachment summary

**Supported File Types:**
| Type | Processing Method |
|------|------------------|
| Images (jpg, png) | GPT-4o Vision analysis |
| PDF | Azure Document Intelligence |
| Excel/CSV | Pandas parsing |
| Word docs | Document extraction |
| Text files | Direct text read |

---

### Agent 5: Product Enrichment Agent
**File:** `carrier_product_enrichment_agent.py`  
**Demo:** `carrier_product_enrichment_agent.json`

> ⚠️ **STATUS: STUBBED** - This agent uses mock data until internal APIs are available

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Enriches case with product/install base metadata |
| **Trigger** | Called by Orchestrator after case analysis |
| **Inputs** | Product references, customer account ID |
| **Outputs** | Product details, warranty status, install history |
| **Integrations** | 🔶 STUBBED - Internal product APIs, install base database |

**Actions:**
- `lookup_product` - Get product details by model/serial *(stubbed with mock data)*
- `get_install_base` - Retrieve customer's installed equipment *(stubbed)*
- `check_warranty_status` - Determine warranty coverage *(stubbed)*
- `get_service_history` - Find past service records for equipment *(stubbed)*
- `get_known_issues` - Check for known issues with product model *(stubbed)*

**Stub Configuration:**
```python
# Future API endpoints - configure when available
PRODUCT_API_CONFIG = {
    "product_lookup_url": "[FUTURE: https://api.carrier.com/products/v1/lookup]",
    "install_base_url": "[FUTURE: https://api.carrier.com/installbase/v1/query]",
    "warranty_url": "[FUTURE: https://api.carrier.com/warranty/v1/status]",
    "service_history_url": "[FUTURE: https://api.carrier.com/service/v1/history]",
    "use_mock_data": True  # Set to False when APIs are available
}
```

**Enrichment Data (Mock Response):**
```json
{
  "product": {
    "model": "string",
    "serial": "string",
    "product_line": "string",
    "install_date": "date",
    "age_years": 0.0
  },
  "warranty": {
    "status": "Active | Expired | Extended",
    "expiry_date": "date",
    "coverage_type": "string"
  },
  "service_history": [
    {
      "date": "date",
      "issue": "string",
      "resolution": "string"
    }
  ],
  "known_issues": [
    {
      "bulletin_id": "string",
      "description": "string",
      "recommended_action": "string"
    }
  ],
  "customer_context": {
    "account_tier": "Premium | Standard",
    "contract_type": "string",
    "total_installed_units": 0
  },
  "_meta": {
    "source": "MOCK_DATA",
    "note": "Replace with live API when available"
  }
}
```

---

### Agent 6: Summary Generator Agent
**File:** `carrier_summary_generator_agent.py`  
**Demo:** `carrier_summary_generator_agent.json`

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Creates structured summary and recommended next action |
| **Trigger** | Called by Orchestrator after enrichment |
| **Inputs** | All extracted data from previous agents |
| **Outputs** | Structured summary, recommended action, priority |
| **AI Model** | GPT-4o for summary generation |

**Actions:**
- `generate_triage_summary` - Create comprehensive case summary
- `recommend_next_action` - Determine best next step
- `assign_priority` - Calculate final priority based on all data
- `suggest_routing` - Recommend which team/queue should handle
- `estimate_resolution_time` - Predict time to resolve

**Summary Template:**
```
=== CASE TRIAGE SUMMARY ===

CASE: [CaseNumber]
CUSTOMER: [AccountName] ([AccountTier])

ISSUE SUMMARY:
[2-3 sentence summary of the problem]

PRODUCT: [Model] | Serial: [Serial]
WARRANTY: [Status] (Expires: [Date])
INSTALL AGE: [X] years

KEY FINDINGS:
• [Extracted finding 1]
• [Extracted finding 2]
• [Extracted finding 3]

URGENCY FACTORS:
• [Factor 1]
• [Factor 2]

RECOMMENDED ACTION:
[Specific action to take]

SUGGESTED ROUTING: [Team/Queue]
PRIORITY: [Critical/High/Medium/Low]
EST. RESOLUTION TIME: [X hours/days]

=== END TRIAGE ===
```

---

### Agent 7: Salesforce Writer Agent
**File:** `carrier_sf_writer_agent.py`  
**Demo:** `carrier_sf_writer_agent.json`

| Attribute | Description |
|-----------|-------------|
| **Purpose** | Writes triage results back to Salesforce |
| **Trigger** | Called by Orchestrator after summary |
| **Inputs** | Triage summary, recommended action, case ID |
| **Outputs** | Update confirmation, case field updates |
| **Integrations** | Salesforce REST API |

**Actions:**
- `update_case_triage` - Write triage summary to case
- `set_case_priority` - Update case priority field
- `add_case_comment` - Add internal comment with findings
- `update_custom_fields` - Set custom triage fields
- `route_case` - Assign to recommended queue/owner

**Salesforce Fields Updated:**
| Field | Value |
|-------|-------|
| `Triage_Summary__c` | Generated summary text |
| `Triage_Status__c` | "Completed" |
| `Triage_Date__c` | Current timestamp |
| `AI_Recommended_Action__c` | Next action text |
| `AI_Priority__c` | Calculated priority |
| `AI_Routing_Suggestion__c` | Suggested queue |
| `AI_Confidence__c` | Confidence score |

---

## Implementation Plan

### Phase 1: Foundation (Day 1-2)
| Task | Agent | Priority |
|------|-------|----------|
| Create agent file structure | All | P0 |
| Build Salesforce Monitor Agent | Agent 2 | P0 |
| Build Salesforce Writer Agent | Agent 7 | P0 |
| Test Salesforce connectivity | Agent 2, 7 | P0 |

### Phase 2: Core Analysis (Day 3-4)
| Task | Agent | Priority |
|------|-------|----------|
| Build Case Analyzer Agent | Agent 3 | P0 |
| Build Attachment Processor Agent | Agent 4 | P0 |
| Test text extraction | Agent 3 | P0 |
| Test image/document processing | Agent 4 | P1 |

### Phase 3: Enrichment & Summary (Day 5-6)
| Task | Agent | Priority |
|------|-------|----------|
| Build Product Enrichment Agent | Agent 5 | P1 |
| Build Summary Generator Agent | Agent 6 | P0 |
| Mock product API integration | Agent 5 | P1 |
| Test end-to-end summary | Agent 6 | P0 |

### Phase 4: Orchestration (Day 7)
| Task | Agent | Priority |
|------|-------|----------|
| Build Orchestrator Agent | Agent 1 | P0 |
| Wire all agents together | Agent 1 | P0 |
| End-to-end testing | All | P0 |

### Phase 5: Demo Prep (Day 8)
| Task | Agent | Priority |
|------|-------|----------|
| Create demo JSON files | All | P0 |
| Build demo script | All | P0 |
| Create sample cases | All | P0 |
| Rehearse demo flow | All | P0 |

---

## Demo Scenarios

### Scenario 1: New Case Triage (Happy Path)
```
User: "Run triage on new cases"

→ Orchestrator finds 5 new cases
→ For each case:
  → Monitor retrieves case details + attachments
  → Analyzer extracts issue type, urgency, entities
  → Attachment Processor analyzes 2 photos (error code visible)
  → Enrichment finds product under warranty with known issue
  → Summary Generator creates structured triage
  → Writer updates Salesforce with summary + routing

Result: 5 cases triaged in 45 seconds (vs 15 min manual)
```

### Scenario 2: Aging Case Alert
```
User: "Show me cases at SLA risk"

→ Monitor finds 3 cases approaching SLA breach
→ Each case gets emergency triage
→ Urgency calculation factors in SLA deadline
→ Priority elevated to Critical
→ Immediate routing to senior technician queue

Result: Proactive SLA breach prevention
```

### Scenario 3: Complex Case with Attachments
```
User: "Triage case 00012345"

→ Case has 4 attachments: 2 photos, 1 PDF manual, 1 error log
→ Attachment Processor:
  - Photo 1: Error code E47 detected
  - Photo 2: Physical damage visible on condenser
  - PDF: Extracts troubleshooting steps
  - Log: Identifies recurring fault pattern
→ Enrichment: E47 has known fix (service bulletin SB-2025-034)
→ Summary includes all findings + specific repair recommendation

Result: Deep analysis without human reading time
```

---

## Integration Architecture

```
                            ┌──────────────────────┐
                            │    Azure Functions   │
                            │   (RAPP Platform)    │
                            └──────────────────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               │                       │                       │
               ▼                       ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │    Salesforce    │    │   Azure OpenAI   │    │  Product APIs    │
    │    REST API      │    │    (GPT-4o)      │    │   (STUBBED)      │
    └──────────────────┘    └──────────────────┘    └──────────────────┘
    │                       │                       │
    │ ACTIVE ✅             │ ACTIVE ✅             │ FUTURE 🔶
    │                       │                       │
    │ Instance:             │                       │ Stubbed for:
    │ empathetic-bear-      │ - Text analysis      │ - Product lookup
    │ vanmxr-dev-ed         │ - Image analysis     │ - Warranty check
    │                       │ - Summary generation │ - Service history
    │ - Case queries        │                       │ - Install base
    │ - Case updates        │                       │
    │ - Attachment fetch    │                       │
```

### Salesforce Connection Details

| Setting | Value |
|---------|-------|
| Instance URL | `https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com/` |
| API Version | `v59.0` (recommended) |
| Auth Method | OAuth 2.0 JWT Bearer or Username-Password Flow |
| Environment | Developer Edition |

---

## Salesforce Configuration Required

### Custom Fields on Case Object
| Field API Name | Type | Description |
|----------------|------|-------------|
| `Triage_Summary__c` | Long Text Area (32K) | AI-generated triage summary |
| `Triage_Status__c` | Picklist | null, In Progress, Completed |
| `Triage_Date__c` | DateTime | When triage was completed |
| `AI_Recommended_Action__c` | Text Area (1000) | Recommended next step |
| `AI_Priority__c` | Picklist | Critical, High, Medium, Low |
| `AI_Routing_Suggestion__c` | Text (255) | Suggested queue/team |
| `AI_Confidence__c` | Percent | Model confidence score |
| `AI_Issue_Type__c` | Picklist | Classified issue category |

### Connected App Setup

**Salesforce Instance:** `https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com/`

**Authentication Options:**

| Method | Use Case | Setup |
|--------|----------|-------|
| Username-Password Flow | Development/Testing | Simplest, use security token |
| OAuth 2.0 JWT Bearer | Production | Server-to-server, no user interaction |
| OAuth 2.0 Web Server | Interactive apps | User-initiated login |

**For Development (Recommended):**
```
SF_INSTANCE_URL=https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com
SF_USERNAME=your-username@example.com
SF_PASSWORD=your-password
SF_SECURITY_TOKEN=your-security-token
SF_API_VERSION=v59.0
```

**Scopes Required:** `api`, `refresh_token`, `offline_access`

**Permission Sets for Case Object:**
- Read: Case, CaseComment, Attachment, ContentDocument
- Write: Case (specific fields), CaseComment
- Create: CaseComment

---

## Success Metrics

| Metric | Current State | Target | Measurement |
|--------|---------------|--------|-------------|
| Time to triage | 15-30 min | < 2 min | Triage_Date - CreatedDate |
| SLA breach rate | 12% | < 5% | Cases breached / Total cases |
| Triage consistency | Variable | 95% | Summary completeness score |
| Agent resolution focus | 40% | 70% | Time on resolution vs intake |
| Call volume (info requests) | High | -30% | Call logs before/after |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Salesforce API limits | Batch queries, caching, off-peak scheduling |
| Incorrect triage | Confidence scores + human review queue for low confidence |
| Attachment processing failures | Graceful degradation, flag for manual review |
| Product API unavailability | **Using stubbed mock data** - proceed without live enrichment |
| Model hallucination | Grounded prompts, fact extraction only, no speculation |

---

## Agent Build Order

Building agents in this order ensures each can be tested independently:

| Order | Agent | Reason |
|-------|-------|--------|
| 1 | Salesforce Case Monitor | Foundation - get data first |
| 2 | Salesforce Writer | Foundation - close the loop |
| 3 | Case Analyzer | Core - text extraction |
| 4 | Summary Generator | Core - generate output |
| 5 | Attachment Processor | Enhancement - handles files |
| 6 | Product Enrichment | Enhancement - adds context |
| 7 | Orchestrator | Last - coordinates all |

---

## Files to Create

### Agent Files (Python)
```
agents/
├── carrier_case_triage_orchestrator_agent.py
├── carrier_sf_case_monitor_agent.py
├── carrier_case_analyzer_agent.py
├── carrier_attachment_processor_agent.py
├── carrier_product_enrichment_agent.py
├── carrier_summary_generator_agent.py
└── carrier_sf_writer_agent.py
```

### Demo Files (JSON)
```
demos/
├── carrier_case_triage_orchestrator_agent.json
├── carrier_sf_case_monitor_agent.json
├── carrier_case_analyzer_agent.json
├── carrier_attachment_processor_agent.json
├── carrier_product_enrichment_agent.json
├── carrier_summary_generator_agent.json
├── carrier_sf_writer_agent.json
└── carrier_case_triage_demo.json (end-to-end demo)
```

---

## Approval Checklist

- [ ] Architecture reviewed with Carrier stakeholders
- [ ] Salesforce custom fields approved for creation
- [ ] Product API access confirmed
- [ ] Azure OpenAI capacity confirmed
- [ ] Demo date scheduled
- [ ] Success metrics agreed

---

## Next Steps

1. **Review this plan** and provide feedback
2. **Confirm Salesforce access** credentials for development
3. **Identify sample cases** for testing
4. **Start Agent 1**: Salesforce Case Monitor Agent
5. **Iterate** through agent build order

---

*Document created: January 20, 2026*  
*Last updated: January 20, 2026*  
*Author: GitHub Copilot*
