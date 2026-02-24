# Vermeer Manufacturing - Machine Walkaround AI Assistant

## Solution Architecture & Approach

**Customer:** Vermeer Manufacturing (https://www.vermeer.com/na)  
**Date:** February 2026  
**Status:** Prototype / Discovery

---

## 1. The Problem

Vermeer wants an AI-powered machine walkaround assistant where field technicians or operators can:

- Walk around heavy equipment with a camera (phone/tablet)
- Point the camera at any part of the machine
- Ask questions and get real-time AI answers about what they see
- Perform guided pre-operation inspections, maintenance checks, and safety audits

**Original ask:** Copilot Vision — but that's a **consumer-only** feature (Bing/Edge). Not available as an enterprise API.

**The good news:** We can build something **better** than Copilot Vision using Azure services, because we can customize it with Vermeer's own machine knowledge, manuals, and inspection checklists.

---

## 2. Enterprise "Copilot Vision" — How We Build It

The core insight: **Azure OpenAI GPT-4o (and GPT-4.1/GPT-5) natively support image inputs** via the Chat Completions API. You send a base64-encoded image + a text prompt, and the model analyzes the image and responds conversationally. This is the enterprise equivalent of Copilot Vision.

### What Azure OpenAI Vision Can Do

| Capability | Details |
|---|---|
| **Image understanding** | Identify machine parts, components, labels, wear patterns |
| **OCR on labels/plates** | Read serial numbers, model numbers, warning labels |
| **Damage/wear detection** | Spot fluid leaks, worn belts, cracked hoses, missing guards |
| **Guided inspection** | Walk through a checklist and validate each item visually |
| **Conversational** | Multi-turn — user can ask follow-up questions about the same image |
| **Grounded in context** | System prompt loaded with Vermeer machine manuals and specs |
| **Enterprise-grade** | Data stays within Azure tenant, full compliance and audit trail |

### Key API Pattern

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_version="2024-08-01-preview"
)

response = client.chat.completions.create(
    model="gpt-4o",  # or gpt-4.1, gpt-5
    messages=[
        {
            "role": "system",
            "content": "You are a Vermeer equipment inspection assistant. You help technicians identify machine components, check for wear/damage, and perform walkaround inspections. You have deep knowledge of Vermeer trenchers, brush chippers, stump cutters, and utility equipment."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What component am I looking at and does it show any signs of wear?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,<BASE64_IMAGE_DATA>",
                        "detail": "high"  # high-res for detailed inspection
                    }
                }
            ]
        }
    ],
    max_tokens=1000
)
```

---

## 3. Architecture Options

### Option A: Power Apps + Copilot Studio (Recommended for Fastest Time-to-Value)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER EXPERIENCE                          │
│                                                                 │
│   ┌──────────────┐    ┌──────────────────────────────────────┐  │
│   │  Power Apps   │    │  Copilot Studio (Conversation UI)    │  │
│   │  Canvas App   │    │  - Embedded in Power App             │  │
│   │  - Camera     │    │  - OR standalone in Teams            │  │
│   │  - Gallery    │    │  - Manages dialog flow               │  │
│   │  - Voice      │    │  - Machine knowledge base            │  │
│   └──────┬───────┘    └──────────────┬───────────────────────┘  │
│          │                           │                          │
└──────────┼───────────────────────────┼──────────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                           │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              Power Automate Flow                          │  │
│   │  1. Receive image (base64) + user question               │  │
│   │  2. Call Azure OpenAI GPT-4o Vision API                  │  │
│   │  3. (Optional) Call Azure Computer Vision for OCR        │  │
│   │  4. Return analysis result to Copilot Studio             │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AZURE SERVICES                             │
│                                                                 │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │ Azure OpenAI │  │ Azure CV     │  │ Azure AI Search      │  │
│   │ GPT-4o       │  │ (optional)   │  │ (optional)           │  │
│   │ Vision API   │  │ OCR, Object  │  │ Machine manuals,     │  │
│   │              │  │ Detection    │  │ parts catalogs,      │  │
│   │ THE "EYES"   │  │              │  │ inspection guides    │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Fastest to build — Power Apps Camera control is built-in
- Copilot Studio handles conversation management natively
- No custom code for the front-end
- Vermeer likely already has Power Platform licenses
- Easy to iterate on prompts and flows without code deploys

**Cons:**
- Camera control in Power Apps is capture-only (no live video stream)
- Image quality depends on device camera + Power Apps compression
- Slight latency through Power Automate → Azure OpenAI round-trip
- Less flexible UX than a custom app

**Build Effort:** 2-4 weeks for MVP

---

### Option B: Custom App + Azure Functions (RAPP) — Richer Experience

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER EXPERIENCE                          │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │         Custom Mobile/Web App (React/PWA)                 │  │
│   │  - Live camera feed via getUserMedia API                  │  │
│   │  - Tap-to-capture or periodic frame capture               │  │
│   │  - Voice input/output for hands-free operation            │  │
│   │  - AR overlay annotations (future)                        │  │
│   │  - Guided walkaround checklist UI                         │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS (image + question)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE FUNCTIONS (RAPP)                        │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │         Machine Walkaround Agent                          │  │
│   │  - Receives base64 image + text question                  │  │
│   │  - Forwards to Azure OpenAI GPT-4o Vision                │  │
│   │  - Enriches with RAG from machine knowledge base          │  │
│   │  - Returns analysis + voice response                      │  │
│   │  - Tracks inspection state (checklist progress)           │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │     Copilot Studio (optional orchestrator via Direct Line) │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AZURE SERVICES                             │
│                                                                 │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │ Azure OpenAI │  │ Azure CV     │  │ Azure AI Search      │  │
│   │ GPT-4o/4.1   │  │ Image        │  │ Vermeer knowledge:   │  │
│   │ Vision API   │  │ Analysis 4.0 │  │ - Operator manuals   │  │
│   │              │  │ - OCR        │  │ - Parts catalogs     │  │
│   │              │  │ - Detection  │  │ - Service bulletins   │  │
│   │              │  │              │  │ - Inspection forms    │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│   ┌──────────────┐  ┌──────────────────────────────────────────┐│
│   │ Azure Cosmos │  │ Azure Blob Storage                       ││
│   │ DB (optional)│  │ - Inspection photos with metadata        ││
│   │ - Inspection │  │ - Historical comparison images           ││
│   │   history    │  │ - Machine reference images               ││
│   │ - Machine    │  │                                          ││
│   │   profiles   │  │                                          ││
│   └──────────────┘  └──────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Live camera feed (not just capture)
- Voice input/output for hands-free field use
- AR overlay potential for annotating machine parts
- Full control over UX and performance
- Can work offline with queued sync
- Deeper integration with Vermeer's existing systems

**Cons:**
- More development effort (custom mobile app)
- Requires app distribution (App Store or PWA)
- More infrastructure to manage

**Build Effort:** 6-10 weeks for MVP

---

## 4. Recommended Approach: Phased Delivery

### Phase 1: Prove the Vision (2-3 weeks)
**Goal:** Demonstrate that Azure OpenAI Vision can accurately analyze Vermeer equipment images.

| Deliverable | Details |
|---|---|
| **RAPP Agent Prototype** | Machine Walkaround Agent that accepts image + question, returns analysis |
| **HTML Tester Page** | Simple web page with camera capture + chat interface for demo |
| **System Prompt** | Tuned for Vermeer equipment types (trenchers, chippers, stump cutters, etc.) |
| **Sample Inspection Flow** | 5-point pre-operation checklist with image validation |
| **Demo Recording** | Video walkthrough showing the capability |

**What this proves:**
- Azure OpenAI can identify Vermeer machine components from photos
- The model can detect wear, damage, and safety concerns
- Multi-turn conversation works (follow-up questions about the same image)
- OCR on serial plates and labels works reliably

### Phase 2: Copilot Studio Integration (2-3 weeks)
**Goal:** Wrap the vision capability in a conversational agent that guides the walkaround.

| Deliverable | Details |
|---|---|
| **Copilot Studio Agent** | Walkaround conversation flow with image analysis actions |
| **Power Automate Flows** | Image → Azure OpenAI Vision, OCR extraction, checklist tracking |
| **Knowledge Base** | Upload Vermeer operator manuals for RAG-grounded answers |
| **Teams Channel** | Agent accessible in Microsoft Teams for field technicians |
| **Inspection Templates** | Configurable checklists per machine type |

### Phase 3: Power App or Custom App (3-4 weeks)
**Goal:** Production-ready mobile experience optimized for field use.

| Deliverable | Details |
|---|---|
| **Power Apps Canvas App** (Option A) | Camera + Copilot Studio embedded, offline checklist |
| **OR Custom PWA** (Option B) | React app with live camera, voice I/O, AR annotations |
| **Inspection Reports** | Auto-generated PDF reports with annotated photos |
| **Azure AI Search** | RAG over Vermeer parts catalogs and service bulletins |
| **Cosmos DB** | Inspection history, machine profiles, trend analysis |
| **Admin Dashboard** | Fleet-level inspection analytics and compliance tracking |

### Phase 4: Advanced Features (ongoing)
- **Vision fine-tuning** with Vermeer-specific training images (GPT-4o supports this)
- **AR overlays** marking identified components on live camera feed
- **Predictive maintenance** — compare current images against historical baselines
- **D365 integration** — create work orders directly from inspection findings
- **Offline mode** — capture + queue when out of cell coverage

---

## 5. What Needs to Be Built — Component Breakdown

### 5.1 Azure OpenAI Vision Integration (Core)

| Component | Technology | Purpose |
|---|---|---|
| Vision API calls | Azure OpenAI GPT-4o/4.1 | Analyze equipment images, answer questions |
| System prompt engineering | Prompt design | Vermeer-specific machine knowledge, inspection criteria |
| Image preprocessing | Python/JS | Resize, compress, base64 encode camera frames |
| Multi-turn context | Conversation history | Remember previous images in same walkaround session |

### 5.2 Copilot Studio Agent (Brain)

| Component | Technology | Purpose |
|---|---|---|
| Walkaround topic | Copilot Studio | Guided inspection flow with branching logic |
| Image analysis action | Power Automate + HTTP | Send image to Azure OpenAI, return results |
| Knowledge sources | Copilot Studio Generative AI | Vermeer manuals, specs, safety guidelines |
| Adaptive cards | Copilot Studio | Rich display of inspection results |

### 5.3 Mobile Experience (Eyes)

| Component | Technology | Purpose |
|---|---|---|
| Camera capture | Power Apps Camera control OR getUserMedia | Capture equipment images |
| Voice I/O | Azure Speech Services OR device native | Hands-free operation in the field |
| Checklist UI | Power Apps OR React | Track walkaround progress |
| Photo gallery | Blob Storage + thumbnails | Review captured images per inspection |

### 5.4 Knowledge & Data Layer

| Component | Technology | Purpose |
|---|---|---|
| Machine manuals | Azure AI Search | RAG retrieval of relevant manual sections |
| Parts catalog | Azure AI Search | Identify components and part numbers |
| Inspection history | Cosmos DB | Track inspections per machine over time |
| Reference images | Blob Storage | "Known good" baseline images for comparison |
| Inspection reports | PDF generation | Compliance documentation |

---

## 6. Key Azure Services Required

| Service | SKU | Purpose | Est. Monthly Cost |
|---|---|---|---|
| **Azure OpenAI** | GPT-4o (Standard) | Vision analysis, conversation | $50-200 (usage-based) |
| **Azure AI Search** | Basic | Machine knowledge RAG | $75 |
| **Azure Blob Storage** | Standard | Inspection photos | $5-20 |
| **Cosmos DB** | Serverless | Inspection records | $5-25 |
| **Azure Speech** | Standard | Voice I/O | $10-30 |
| **Power Platform** | Existing licenses | Power Apps + Copilot Studio | Included* |

*Assumes Vermeer has M365/Power Platform licensing. Copilot Studio may require additional licensing.

**Estimated total:** ~$150-350/month for prototype, scaling with usage.

---

## 7. Key Design Decisions

### Why Azure OpenAI Vision, not Azure Computer Vision?

| Feature | Azure OpenAI Vision (GPT-4o) | Azure Computer Vision |
|---|---|---|
| **Conversational** | Yes — natural language Q&A about images | No — returns structured JSON |
| **Contextual understanding** | Understands "is this worn?" in context | Returns generic labels/tags |
| **Multi-turn** | Remembers previous images/questions | Stateless per call |
| **Custom knowledge** | System prompt with Vermeer-specific context | Requires custom model training |
| **OCR** | Built-in, conversational | Better for structured extraction |
| **Best for** | The walkaround assistant (primary) | Supplementary OCR/detection tasks |

**Recommendation:** Use Azure OpenAI GPT-4o Vision as the primary "brain + eyes." Add Azure Computer Vision only if you need specialized OCR or object detection that GPT-4o doesn't handle well enough.

### Why not just Copilot Vision?

| Aspect | Copilot Vision (Consumer) | Our Solution (Enterprise) |
|---|---|---|
| **Availability** | Consumer Bing/Edge only | Azure enterprise tenant |
| **Data residency** | Public cloud, consumer ToS | Azure region, enterprise compliance |
| **Customization** | None | Full — Vermeer manuals, checklists, prompts |
| **Integration** | None | D365, Power Platform, Teams, custom apps |
| **Audit trail** | None | Full logging, inspection records |
| **Offline** | No | Can be designed for offline capture + sync |

**Our enterprise solution is strictly superior for this use case.**

---

## 8. Success Metrics

| Metric | Target |
|---|---|
| Image analysis accuracy | >90% correct identification of machine components |
| Inspection time reduction | 30-50% faster than paper-based walkarounds |
| Defect detection rate | Catches issues missed by visual-only inspection |
| User adoption | >80% of technicians actively using within 90 days |
| Report generation | Automated, zero manual documentation needed |

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Poor image quality in field (dust, lighting) | Use `detail: high` mode; prompt engineering for low-quality images; image preprocessing |
| GPT-4o misidentifies Vermeer-specific components | Fine-tune with Vermeer training images (supported for GPT-4o); RAG with parts catalog |
| Latency in field (slow cellular) | Offline capture mode with queued analysis; edge processing for basic checks |
| Power Apps camera limitations | Phase 3 custom app option for richer camera experience |
| Token costs at scale | Implement image compression; use `detail: low` for screening, `high` only for detailed analysis |

---

## 10. Next Steps

1. **Schedule technical deep-dive** with Vermeer IT to discuss data sources (manuals, parts catalogs, existing inspection forms)
2. **Run Phase 1 prototype** using the RAPP Machine Walkaround Agent (included in this repo)
3. **Capture sample images** of Vermeer equipment for testing
4. **Define inspection checklists** per machine type (trencher, chipper, etc.)
5. **Evaluate Power Platform licensing** at Vermeer
