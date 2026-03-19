# RAPP Feature Backlog

**Last Updated:** March 14, 2026  
**Maintained By:** Bill Whalen

---

## 📋 Backlog Overview

| Priority | Feature | Status | Effort | Business Value |
|----------|---------|--------|--------|----------------|
| P0 | [RAPP Studio (No-Code Builder)](#1-rapp-studio-no-code-agent-builder) | 🔵 Planning | XL | ⭐⭐⭐⭐⭐ |
| P1 | [Event-Driven Triggers](#2-event-driven-agent-triggers) | 🔵 Planning | L | ⭐⭐⭐⭐⭐ |
| P1 | [Agent Memory Enhancement](#3-agent-memory-enhancement) | 🔵 Planning | M | ⭐⭐⭐⭐ |
| P1 | [D365 Demo Orchestration](#9-d365-demo-orchestration) | 🟢 **Implemented** | M | ⭐⭐⭐⭐⭐ |
| P2 | [Agent A/B Testing Framework](#4-agent-ab-testing-framework) | 🔵 Planning | L | ⭐⭐⭐⭐ |
| P2 | [Multi-Modal Agent Support](#5-multi-modal-agent-support) | 🔵 Planning | L | ⭐⭐⭐⭐ |
| P2 | [Agent Versioning & Rollback](#6-agent-versioning--rollback) | 🔵 Planning | M | ⭐⭐⭐ |
| P3 | [Self-Improving Agents](#7-self-improving-agents) | 🔵 Planning | XL | ⭐⭐⭐⭐⭐ |
| P2 | [Programmatic Video Generation](#8-programmatic-video-generation) | 🔵 Planning | M | ⭐⭐⭐⭐ |

**Legend:** 🔵 Planning | 🟡 In Progress | 🟢 Complete | ⚪ On Hold

---

## 1. RAPP Studio (No-Code Agent Builder)

### Vision
A web-based application enabling non-technical users to create, configure, and deploy agents through a guided UI — complete with auto-generated demo assets and click-through presentations.

### User Personas
- **Business Analyst** - Understands use case, no coding skills
- **Sales Engineer** - Needs demo assets quickly
- **Customer Success** - Customizes agents for client needs

### Core Features

#### 1.1 Use Case Wizard
```
┌─────────────────────────────────────────────────────────────────┐
│  🧙 RAPP Studio - Create New Agent                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Describe Your Use Case                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ I want to create an agent that monitors our SharePoint    │  │
│  │ site for new RFPs, extracts key requirements, and         │  │
│  │ creates a summary in Teams...                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Detected Capabilities:                                         │
│  ✓ SharePoint Integration                                       │
│  ✓ Document Analysis                                            │
│  ✓ Teams Notifications                                          │
│                                                                 │
│  [Refine] [Generate Agent →]                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.2 Visual Agent Designer
- Drag-and-drop action builder
- Pre-built action templates (CRUD, API calls, AI analysis)
- Parameter configuration with validation
- Live preview of agent behavior

#### 1.3 Integration Marketplace
- Pre-configured connectors: Salesforce, D365, SharePoint, Teams, ServiceNow
- Custom API connector builder
- OAuth flow management

#### 1.4 Demo Asset Generator
Auto-generates presentation-ready materials:

| Asset Type | Description |
|------------|-------------|
| **Click-Through Demo** | Interactive HTML walkthrough with simulated responses |
| **Executive Summary** | 1-pager with value proposition and ROI estimates |
| **Technical Spec** | Architecture diagram, API docs, data flow |
| **PowerPoint** | Customizable slide deck with agent capabilities |
| **Demo Script** | Talking points and Q&A guide |

#### 1.5 Click-Through Demo Engine
```
┌─────────────────────────────────────────────────────────────────┐
│  📽️ Interactive Demo: Customer Service Triage Agent            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Step 3 of 7] - Automatic Case Routing                         │
│                                                                 │
│  User: "Route this case to the appropriate team"                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🤖 Analyzing case #12345...                                │  │
│  │                                                           │  │
│  │ Category: Technical Support - HVAC Systems                │  │
│  │ Urgency: High (SLA breach in 4 hours)                     │  │
│  │ Sentiment: Frustrated                                     │  │
│  │                                                           │  │
│  │ Routing to: Tier 2 HVAC Specialists                       │  │
│  │ Assigned to: @john.smith (available, 87% match)           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [← Previous]  [Show Technical Details]  [Next Step →]          │
└─────────────────────────────────────────────────────────────────┘
```

Features:
- Branching scenarios (happy path, edge cases, error handling)
- Customizable branding (customer logo, colors)
- Exportable as standalone HTML or hosted URL
- Analytics: track which steps users spend time on

### Architecture
```
┌──────────────────────────────────────────────────────────────────────┐
│                         RAPP Studio Frontend                         │
│                    (React/Next.js + TailwindCSS)                     │
├──────────────────────────────────────────────────────────────────────┤
│  Use Case     │  Agent      │  Integration  │  Demo Asset  │ Deploy │
│  Wizard       │  Designer   │  Manager      │  Generator   │ Panel  │
└───────┬───────┴──────┬──────┴───────┬───────┴───────┬──────┴────┬───┘
        │              │              │               │           │
        ▼              ▼              ▼               ▼           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      RAPP Studio API (Azure Functions)               │
├──────────────────────────────────────────────────────────────────────┤
│  /api/wizard/analyze     - NL → Agent config                         │
│  /api/agents/generate    - Create agent assets                       │
│  /api/demos/create       - Generate demo materials                   │
│  /api/deploy/copilot     - Deploy to Copilot Studio                  │
│  /api/deploy/rapp        - Deploy to RAPP Function App               │
└───────┬───────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Existing RAPP Engine                          │
│  • AgentGeneratorAgent    • CopilotStudioTranspiler                  │
│  • Best Practices KB      • MCS Generator                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Best Practices Integration
Incorporate knowledge sources for:
- Agent architecture patterns (orchestrator, specialist, hybrid)
- Prompt engineering guidelines
- Security and compliance checks
- Performance optimization recommendations

### Success Metrics
- Time to first agent: < 30 minutes for non-technical user
- Demo generation time: < 5 minutes
- User satisfaction: > 4.5/5 stars

---

## 2. Event-Driven Agent Triggers

### Vision
Transform agents from request-response to proactive, event-driven automation.

### Trigger Types

| Trigger | Source | Example Use Case |
|---------|--------|------------------|
| **Webhook** | External systems | Salesforce case created → Triage agent |
| **Email** | Microsoft Graph | Customer email → Draft response agent |
| **Schedule** | Azure Timer | Daily 8am → CI report agent |
| **File** | Blob Storage | Contract uploaded → Analysis agent |
| **Teams** | Bot Framework | @mention → Support agent |
| **Queue** | Service Bus | High-priority items → Escalation agent |

### Configuration Schema
```yaml
# triggers/salesforce_case_trigger.yml
trigger:
  name: "New Salesforce Case"
  type: webhook
  source: salesforce
  event: case.created
  
filter:
  - field: "Case.Priority"
    operator: "equals"
    value: "High"
  - field: "Case.Type"
    operator: "in"
    values: ["Technical", "Billing"]

action:
  agent: "carrier_case_triage_orchestrator"
  parameters:
    action: "triage_case"
    case_id: "{{event.Case.Id}}"
    
notifications:
  on_success:
    - type: teams
      channel: "#case-updates"
  on_failure:
    - type: email
      to: "support-ops@company.com"
```

### Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Salesforce │     │   Graph     │     │   Timer     │
│   Webhook   │     │   Events    │     │   Trigger   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Event Router         │
              │   (Azure Functions)    │
              │   - Filter/transform   │
              │   - Route to agent     │
              │   - Retry logic        │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   RAPP Agent Engine    │
              └────────────────────────┘
```

### Implementation Tasks
- [ ] Event Router Azure Function
- [ ] Webhook registration endpoints
- [ ] Microsoft Graph subscription management
- [ ] Timer trigger configuration
- [ ] Dead letter queue for failed events
- [ ] Event history and replay capability

---

## 3. Agent Memory Enhancement

### Current State
RAPP has `ContextMemoryAgent` with:
- ✅ User-specific and shared memory contexts
- ✅ Keyword filtering
- ✅ Timestamp tracking
- ❌ No semantic/vector search
- ❌ No cross-session learning
- ❌ No memory summarization

### Proposed Enhancements

#### 3.1 Semantic Memory (Vector Store)
```python
# Example: Semantic recall
memory.semantic_search(
    query="What did the user say about Watts pricing?",
    top_k=5,
    threshold=0.8
)

# Returns contextually relevant memories, not just keyword matches
```

**Implementation:** Azure AI Search with vector embeddings

#### 3.2 Memory Layers
```
┌─────────────────────────────────────────────────────────────────┐
│                        Memory Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  Short-term: Current conversation context     │
│  │  WORKING     │  - Last N messages                            │
│  │  MEMORY      │  - Active task state                          │
│  └──────────────┘  TTL: Session                                 │
│                                                                 │
│  ┌──────────────┐  Medium-term: Recent interactions             │
│  │  EPISODIC    │  - Summarized conversations                   │
│  │  MEMORY      │  - User preferences learned                   │
│  └──────────────┘  TTL: 30 days                                 │
│                                                                 │
│  ┌──────────────┐  Long-term: Persistent knowledge              │
│  │  SEMANTIC    │  - User profile facts                         │
│  │  MEMORY      │  - Domain knowledge extracted                 │
│  └──────────────┘  TTL: Indefinite                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3 Memory Consolidation
Automatic summarization of episodic memories into semantic facts:

```python
# Before consolidation (episodic)
memories = [
    "User asked about Watts pricing on Jan 5",
    "User compared Watts to Kohler on Jan 8", 
    "User said Watts is too expensive on Jan 12"
]

# After consolidation (semantic)
facts = [
    {"fact": "User is price-sensitive regarding Watts products", "confidence": 0.9},
    {"fact": "User evaluates Watts against Kohler", "confidence": 0.85}
]
```

#### 3.4 Cross-Agent Memory Sharing
Agents can share relevant context:
```python
# CI agent stores insight
memory.store(
    scope="organization",
    category="competitive_intel",
    fact="Watts launched new touchless faucet line Q1 2026",
    source="zurnelkay_drinking_water_ci_agent"
)

# Sales agent retrieves relevant context
context = memory.recall(
    scope="organization",
    categories=["competitive_intel", "pricing"],
    relevant_to="Watts commercial products"
)
```

---

## 4. Agent A/B Testing Framework

### Vision
Systematically test and optimize agent prompts, configurations, and behaviors.

### Experiment Configuration
```yaml
# experiments/ci_prompt_optimization.yml
experiment:
  name: "CI Report Format Test"
  agent: "zurnelkay_ci_orchestrator"
  hypothesis: "Structured bullet format improves user comprehension"
  
variants:
  control:
    weight: 50
    config:
      response_format: "narrative"
      
  treatment:
    weight: 50
    config:
      response_format: "structured_bullets"
      include_confidence_scores: true

metrics:
  primary:
    - name: "user_rating"
      type: "explicit_feedback"
      target: 4.0
      
  secondary:
    - name: "follow_up_questions"
      type: "count"
      direction: "lower_is_better"
    - name: "time_to_action"
      type: "duration"
      
assignment:
  method: "user_id_hash"  # Consistent assignment per user
  
duration:
  start: "2026-02-01"
  end: "2026-02-28"
  min_samples: 100
```

### Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Experiment: CI Report Format Test                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Status: 🟢 Running (Day 12 of 28)                              │
│  Samples: Control: 234 | Treatment: 228                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Primary Metric: User Rating                            │    │
│  │                                                         │    │
│  │  Control:    ████████████░░░░  3.8 avg                  │    │
│  │  Treatment:  █████████████████ 4.3 avg  (+13.2%)        │    │
│  │                                                         │    │
│  │  Statistical Significance: 94% (need 95%)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Recommendation: Continue experiment (6 more days estimated)    │
│                                                                 │
│  [View Details] [Stop Early] [Promote Winner]                   │
└─────────────────────────────────────────────────────────────────┘
```

### Best Practices Integration
- Pre-built experiment templates based on proven patterns
- Guardrails: auto-stop if treatment significantly underperforms
- Prompt optimization suggestions from knowledge base

---

## 5. Multi-Modal Agent Support

### Vision
Agents that process and generate images, documents, audio, and video.

### Supported Modalities

| Input | Processing | Output | Example |
|-------|------------|--------|---------|
| 📸 Image | GPT-4V analysis | Text | Product photo → competitor identification |
| 📄 PDF | Document Intelligence | Text + Tables | Contract → risk summary |
| 🎤 Audio | Whisper transcription | Text | Voice memo → action items |
| 📊 Excel | Structured parsing | Text + Charts | Spreadsheet → insights |
| 🖼️ Diagram | Vision analysis | Text | Architecture diagram → documentation |

### API Extension
```python
# Multi-modal agent request
response = agent.perform(
    action="analyze",
    inputs=[
        {"type": "text", "content": "Compare these two products"},
        {"type": "image", "url": "https://blob.../product_a.jpg"},
        {"type": "image", "url": "https://blob.../product_b.jpg"}
    ],
    output_format="structured_comparison"
)
```

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Modal Input Handler                     │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│  Image   │   PDF    │  Audio   │  Excel   │  Video (frames)    │
│  Handler │  Handler │  Handler │  Handler │  Handler           │
├──────────┴──────────┴──────────┴──────────┴────────────────────┤
│                     Unified Content Extractor                    │
│              (Text, tables, key-value pairs, etc.)              │
├─────────────────────────────────────────────────────────────────┤
│                        RAPP Agent Engine                         │
│                    (GPT-4V for visual tasks)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Agent Versioning & Rollback

### Vision
Git-like version control for agent configurations with instant rollback.

### CLI Commands
```bash
# Publish new version
rapp agent publish zurnelkay_ci --version 2.1.0 --notes "Improved routing accuracy"

# List versions
rapp agent versions zurnelkay_ci
# Output:
# VERSION   DATE         STATUS    NOTES
# 2.1.0     2026-01-27   current   Improved routing accuracy
# 2.0.0     2026-01-15   archived  Added Wilkins BU support
# 1.0.0     2026-01-01   archived  Initial release

# Compare versions
rapp agent diff zurnelkay_ci 2.0.0 2.1.0

# Rollback
rapp agent rollback zurnelkay_ci --to 2.0.0

# Promote from staging to production
rapp agent promote zurnelkay_ci --from staging --to production
```

### Version Metadata
```json
{
  "agent_id": "zurnelkay_ci_orchestrator",
  "version": "2.1.0",
  "created_at": "2026-01-27T15:30:00Z",
  "created_by": "billwhalen@microsoft.com",
  "git_commit": "abc123",
  "config_hash": "sha256:def456...",
  "dependencies": {
    "zurnelkay_drains_ci_agent": ">=1.0.0",
    "zurnelkay_drinking_water_ci_agent": ">=1.0.0"
  },
  "rollback_safe": true,
  "breaking_changes": false,
  "release_notes": "Improved routing accuracy for edge cases"
}
```

### Deployment Environments
```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│   Development  │───▶│    Staging     │───▶│   Production   │
│    v2.2.0-dev  │    │    v2.1.0      │    │    v2.0.0      │
└────────────────┘    └────────────────┘    └────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
    Local testing      Integration tests      Live traffic
    No SLA             Limited traffic        Full SLA
```

---

## 7. Self-Improving Agents

### Vision
Agents that learn from feedback and automatically optimize their performance.

### Feedback Collection
```
┌─────────────────────────────────────────────────────────────────┐
│  Agent Response                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Based on my analysis, Watts has launched 3 new products        │
│  in Q4 2025: the TouchFree Pro series...                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Was this response helpful?                                     │
│                                                                 │
│  [👍 Yes]  [👎 No]  [✏️ Suggest Improvement]                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Learning Pipeline
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Collect    │     │   Analyze    │     │   Optimize   │
│   Feedback   │────▶│   Patterns   │────▶│   Prompts    │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 8. Programmatic Video Generation

### Vision
Automate creation of demo videos, training content, and customer-facing presentations using code-driven video generation tools.

### Use Cases
| Use Case | Description | Output |
|----------|-------------|--------|
| **Demo Videos** | Combine screen recordings with branded overlays | MP4 with intro/outro |
| **Feature Walkthroughs** | Auto-generate from demo execution guides | Narrated video |
| **Customer Onboarding** | Personalized videos with customer branding | Shareable link |
| **Training Content** | Step-by-step tutorials from HTML guides | Video series |
| **Release Highlights** | Changelog to feature showcase | Social-ready clips |

### Technology Options

#### Option A: FFmpeg (CLI-Based)
```bash
# Combine intro + screen recording + outro with text overlays
ffmpeg -i intro.mp4 -i recording.mp4 -i outro.mp4 \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" output.mp4
```

**Pros:**
- Free, open source
- Extremely powerful and flexible
- No external dependencies
- Works offline

**Cons:**
- Steep learning curve
- Complex command syntax
- Limited animation capabilities

#### Option B: Remotion (React-Based)
```typescript
// components/DemoVideo.tsx
import { Composition } from 'remotion';

export const DemoVideo: React.FC<{ customerName: string }> = ({ customerName }) => {
  return (
    <AbsoluteFill>
      <Sequence from={0} durationInFrames={90}>
        <BrandedIntro logo={`/logos/${customerName}.png`} />
      </Sequence>
      <Sequence from={90} durationInFrames={300}>
        <ScreenRecording src="/recordings/demo.webm" />
        <FeatureCallouts data={demoSteps} />
      </Sequence>
      <Sequence from={390} durationInFrames={60}>
        <CallToAction text="Schedule a Demo" />
      </Sequence>
    </AbsoluteFill>
  );
};
```

**Pros:**
- React component model (familiar to web devs)
- Type-safe with TypeScript
- Dynamic data-driven videos
- Rich animation capabilities
- Server-side rendering

**Cons:**
- Requires Node.js runtime
- Steeper initial setup
- Video rendering can be slow

### Proposed Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Video Generation Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐  │
│  │ Demo Guide    │────▶│ Video Script  │────▶│ Render Engine │  │
│  │ (HTML/JSON)   │     │ Generator     │     │ (FFmpeg/      │  │
│  └───────────────┘     └───────────────┘     │  Remotion)    │  │
│                                              └───────┬───────┘  │
│  ┌───────────────┐     ┌───────────────┐             │          │
│  │ Screen        │────▶│ Asset         │─────────────┤          │
│  │ Recordings    │     │ Manager       │             │          │
│  └───────────────┘     └───────────────┘             │          │
│                                                      ▼          │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐  │
│  │ Brand Assets  │────▶│ Template      │────▶│ Final Video   │  │
│  │ (logos,fonts) │     │ Library       │     │ (MP4)         │  │
│  └───────────────┘     └───────────────┘     └───────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Integration with RAPP

#### Demo Guide → Video Pipeline
```python
# Proposed: video_generator_agent.py
class VideoGeneratorAgent(BasicAgent):
    def __init__(self):
        self.name = 'VideoGenerator'
        self.metadata = {
            "name": self.name,
            "description": "Generates demo videos from HTML guides and recordings",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate_from_guide", "create_intro", "add_overlays"]
                    },
                    "guide_path": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "brand_colors": {"type": "object"}
                }
            }
        }

    def perform(self, action, guide_path=None, customer_name=None, **kwargs):
        if action == "generate_from_guide":
            # Parse HTML guide for steps
            # Match to screen recordings
            # Generate video with overlays
            pass
```

### Implementation Phases

#### Phase 1: FFmpeg Foundation (2 weeks)
- [ ] Create FFmpeg wrapper utilities
- [ ] Implement basic video concatenation
- [ ] Add text overlay support
- [ ] Build intro/outro templates
- [ ] Create CLI tool for manual video generation

#### Phase 2: Remotion Integration (3 weeks)
- [ ] Set up Remotion project structure
- [ ] Create reusable video components
- [ ] Build customer branding system
- [ ] Implement demo step visualization
- [ ] Add callout/highlight animations

#### Phase 3: RAPP Integration (2 weeks)
- [ ] Create VideoGeneratorAgent
- [ ] Parse demo execution guides (HTML → JSON)
- [ ] Auto-detect screen recordings
- [ ] Generate video from guide metadata
- [ ] Add to RAPP Studio asset generation

### Customer-Specific Templates

| Customer | Brand Colors | Intro Style | Outro CTA |
|----------|--------------|-------------|------------|
| Otis | Navy #003366, Gold #C4A000 | Elevator animation | "Elevate Your Service" |
| Zurn Elkay | Red #A4262C, Blue #0078D4 | Water flow effect | "Flow With Confidence" |
| Carrier | Blue #003B70, Orange #FF6B35 | HVAC particles | "Cool Innovation" |

### Success Metrics
- Time to create demo video: < 15 minutes (vs. 2+ hours manual)
- Video quality score: Professional grade (1080p, consistent branding)
- Reusability: Templates work across 80%+ of demo scenarios

---

## 9. D365 Demo Orchestration

### Vision
**Turnkey D365 Customer Service demo setup** — provide customer inputs (name, industry, use case, websites) and automatically generate complete demo environments with accounts, contacts, cases, KB articles, queues, SLAs, and more.

### Status: 🟢 **IMPLEMENTED** (March 14, 2026)

### Problem Statement
Setting up a complete D365 Customer Service demo currently requires:
- Manual account/contact creation
- Hardcoded demo data (copied from Zurn)
- Knowledge of 25+ provisioning scripts
- Hours of configuration per customer

**Goal:** Reduce demo prep from hours to minutes with intelligent automation.

### Solution Components

#### 9.1 Input Schema (`d365/schemas/d365_input_schema.json`)
Standardized input format capturing:
```json
{
  "customer": {
    "name": "Otis Elevator",
    "industry": "elevator_service",
    "brands": ["Otis"],
    "region": "EMEA"
  },
  "discovery": {
    "use_case": "telephony_screen_pop",
    "channels": ["phone"],
    "agent_count": 35,
    "pain_points": ["No screen pop", "Manual data lookup"]
  },
  "demo_requirements": {
    "tiers": [
      {"name": "Premium", "sla_first_response_minutes": 60},
      {"name": "Standard", "sla_first_response_minutes": 120}
    ],
    "case_types": ["entrapment", "maintenance"],
    "hero_scenario": {...}
  }
}
```

#### 9.2 Extended D365DemoPrepAgent
New actions in `agents/d365_demo_prep_agent.py`:

| Action | Description |
|--------|-------------|
| `generate_config_from_inputs` | Creates environment.json + demo-data.json from input schema |
| `generate_demo_data` | Uses GPT-4o to generate realistic, contextual demo data |
| `orchestrate_full_setup` | End-to-end: inputs → config → data generation → D365 provisioning |

#### 9.3 GPT-4o Data Generator (`d365/utils/d365_data_generator.py`)
Intelligent demo data generation with:
- **Industry templates** — elevator_service, plumbing_manufacturing, hvac, medical_devices, etc.
- **Regional awareness** — NA/EMEA/APAC phone formats, addresses, naming conventions
- **Tiered accounts** — Platinum/Gold/Silver customers with appropriate SLAs
- **Realistic contacts** — Region-appropriate names, titles, email addresses
- **Contextual cases** — Industry-specific scenarios (entrapment, leaks, outages)
- **KB articles** — GPT-4o generated content relevant to customer's domain

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    D365 Demo Orchestration                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Customer   │────▶│  Input       │────▶│  Config      │     │
│  │   Inputs     │     │  Schema      │     │  Generator   │     │
│  │   (JSON)     │     │  Validation  │     │              │     │
│  └──────────────┘     └──────────────┘     └──────┬───────┘     │
│                                                   │              │
│                                                   ▼              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │  Industry    │────▶│  GPT-4o      │────▶│  demo-data   │     │
│  │  Templates   │     │  Generator   │     │  .json       │     │
│  └──────────────┘     └──────────────┘     └──────┬───────┘     │
│                                                   │              │
│                                                   ▼              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │  PowerShell  │────▶│  Dataverse   │────▶│  D365 Org    │     │
│  │  Scripts     │     │  API         │     │  (Populated) │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Usage Examples

#### Quick Start: Generate Config
```python
# Via RAPP agent
D365DemoPrep action="generate_config_from_inputs" 
  customer_name="acme" 
  d365_org_url="https://org123.crm.dynamics.com"
  inputs={
    "customer": {"name": "ACME Corp", "industry": "manufacturing"},
    "demo_requirements": {"tiers": [{"name": "Gold"}, {"name": "Silver"}]}
  }
```

#### Full Orchestration
```python
# End-to-end setup
D365DemoPrep action="orchestrate_full_setup"
  customer_name="acme"
  d365_org_url="https://org123.crm.dynamics.com"
  inputs={...full input schema...}
  steps_to_run=[1, 2, 3, 7, 8]  # Accounts, Contacts, Products, Cases, KB
```

### Industry Templates

| Industry | Account Types | Case Types | KB Topics |
|----------|--------------|------------|-----------|
| `elevator_service` | Building Mgmt, Property Dev, Hospital | Entrapment, Maintenance, Modernization | Safety, Emergency, SLAs |
| `plumbing_manufacturing` | Distributor, Contractor, Municipal | Order, Warranty, Technical | Installation, Specs, Returns |
| `hvac` | HVAC Contractor, Property Mgmt | System, Maintenance, Emergency | Energy, Diagnostics, Refrigerant |
| `medical_devices` | Hospital, Clinic, Research Lab | Device, Calibration, Compliance | Regulatory, Maintenance, Training |
| `telecommunications` | Enterprise, SMB, Government | Network, Billing, Outage | Configuration, Troubleshooting, Security |

### Files Created

| Path | Purpose |
|------|---------|
| `d365/schemas/d365_input_schema.json` | JSON Schema for customer inputs |
| `d365/utils/d365_data_generator.py` | GPT-4o powered data generator |
| `agents/d365_demo_prep_agent.py` | Extended with 3 new actions |
| `customers/{name}/d365/config/inputs.json` | Saved customer inputs |
| `customers/{name}/d365/config/environment.json` | Generated D365 config |
| `customers/{name}/d365/config/demo-data.json` | GPT-4o generated demo data |

### Success Metrics
| Metric | Before | After |
|--------|--------|-------|
| Time to demo-ready D365 | 4+ hours | < 30 minutes |
| Data realism | Copy/paste from Zurn | Industry-specific, GPT-4o generated |
| Customization effort | Manual edits | Input schema changes |
| Consistency | Varies by person | Standardized templates |

### Future Enhancements
- [ ] Website scraping for product data (`fetch_webpage` integration)
- [ ] Voice-driven input ("Set up a demo for Otis, they're in elevator service...")
- [ ] Copilot Studio agent for non-technical users
- [ ] Integration with RAPP Pipeline for full demo workflow
       │                    │                    │
       ▼                    ▼                    ▼
  • Thumbs up/down    • Cluster similar    • Generate prompt
  • Corrections         failures             variations
  • Time on task      • Identify root      • A/B test
  • Follow-ups          causes             • Promote winner
```

### Automatic Prompt Optimization (DSPy-style)
```python
# System automatically discovers better prompts
optimizer = PromptOptimizer(
    agent="zurnelkay_ci_orchestrator",
    objective="maximize_user_rating",
    constraints={
        "max_tokens": 500,
        "must_include": ["source_citation", "confidence_level"]
    }
)

# Run optimization
optimized_prompt = optimizer.optimize(
    training_examples=feedback_dataset,
    iterations=100
)

# Result: New prompt achieves 15% higher ratings
```

### Guardrails
- Human review required before auto-deploying optimized prompts
- Regression testing against golden dataset
- Rollback if live metrics degrade

---

## 📅 Roadmap

### Q1 2026 (Current)
- [ ] RAPP Studio MVP (Use Case Wizard + Basic Designer)
- [ ] Event-Driven Triggers (Webhook + Timer)
- [ ] Agent Memory Enhancement (Semantic search)

### Q2 2026
- [ ] RAPP Studio Demo Generator
- [ ] Multi-Modal Support (Images + PDFs)
- [ ] A/B Testing Framework

### Q3 2026
- [ ] Click-Through Demo Engine
- [ ] Agent Versioning & Rollback
- [ ] Memory Consolidation

### Q4 2026
- [ ] Self-Improving Agents (Feedback loop)
- [ ] Advanced Multi-Modal (Audio/Video)
- [ ] RAPP Studio GA

---

## 🎯 Success Metrics

| Feature | KPI | Target |
|---------|-----|--------|
| RAPP Studio | Time to first agent | < 30 min |
| Event Triggers | Event processing latency | < 500ms |
| Memory | Relevant recall accuracy | > 90% |
| A/B Testing | Experiment velocity | 10/month |
| Multi-Modal | Document processing time | < 10s |
| Versioning | Rollback time | < 1 min |
| Self-Improving | Monthly prompt improvement | +5% rating |

---

## 📝 Notes

### Natural Language Agent Builder vs GitHub Copilot
**Question:** Is this valuable since GitHub Copilot already does this?

**Answer:** Yes, for different reasons:
1. **Target Audience** - Copilot targets developers; RAPP Studio targets business users
2. **Guided Experience** - Copilot is open-ended; RAPP Studio is structured wizard
3. **Output Quality** - RAPP Studio generates tested, production-ready assets
4. **Demo Assets** - Copilot doesn't generate click-through demos or presentations
5. **Best Practices** - RAPP Studio embeds architectural guidance automatically

Think of it as: **Copilot = Power tool for developers** | **RAPP Studio = Product for business users**

---

*This backlog is a living document. Update as priorities shift.*
