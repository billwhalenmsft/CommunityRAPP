# Carrier Trailer Prioritization — Phase 1 Call Gameplan

## 📊 Presentation Overview

**File:** `Carrier-Trailer-Prioritization-Gameplan.pptx`

**Purpose:** 30-minute call to confirm Phase 1 completion and lock in data/integration decisions for pilot execution.

**Audience:** Carrier leadership, planners, data governance, TSP liaisons

**Duration:** 30 minutes

---

## 🎯 Call Structure (30 Minutes)

| Segment | Time | Purpose |
|---------|------|---------|
| **Context + Value Brief** | 0–5 min | Frame the business problem and solution impact |
| **Architecture Walk + Demo** | 5–15 min | Review what's built, show Canvas app |
| **Decisions Checklist** | 15–24 min | Work through 4 critical confirmations |
| **Close + Next Steps** | 24–30 min | Agree owners and pilot kickoff timeline |

---

## 🔑 Four Critical Decisions (Slides 16–19)

### Decision 1: Data Ownership & Refresh Cadence
**Question:** Who owns the Monday 6 AM SAP in-transit export?
- **Outcome needed:** Confirm owner + process viability

### Decision 2: SharePoint Supplier Data — Schema Lock
**Question:** Which 3 SharePoint sites, column headers?
- **Outcome needed:** Exact URLs + column header screenshots

### Decision 3: Power BI Backlog Integration (Phase 2)
**Question:** Is Power BI a pilot blocker, or post-pilot nice-to-have?
- **Outcome needed:** Confirm dependency timing

### Decision 4: TSP Scheduling Confirmation
**Question:** Email-based schedule sufficient, or is API integration mandatory?
- **Outcome needed:** Confirm TSP integration scope for pilot

---

## 📦 Deliverables Referenced in Call

| Asset | Location | Purpose |
|-------|----------|---------|
| **Portable Solution ZIP** | `customers/carrier/d365/trailer-prioritization/solution/CarrierTrailerPrioritization.zip` | Import-ready D365 package |
| **Engagement Guide** | `customers/carrier/docs/carrier-trailer-prioritization-engagement-guide.md` | Full requirements + roadmap |
| **Demo Script** | `customers/carrier/demos/carrier_trailer_prioritization_demo.json` | Talking points for walkthrough |
| **README (Full Setup)** | `customers/carrier/d365/trailer-prioritization/README.md` | Technical setup instructions |

---

## ✅ What's Built (Phase 1 Complete)

- ✅ Dataverse model (Trailer, Dock, ScoringConfig, FieldMapping, Supplier)
- ✅ Canvas app (3 screens: Dashboard, Schedule Builder, Comms)
- ✅ Power Automate workflow (Monday 6 AM ingestion + scoring trigger)
- ✅ Scoring engine (OTIF% + revenue + readiness algorithm)
- ✅ Email templates (schedule notification to TSP + Kenco)
- ✅ Portable solution package (ready to import)

---

## 🚀 Pilot Timeline (Proposed)

- **Week 1:** Dry run (scoring offline, no dock assignment)
- **Week 2–4:** Live pilot on Dock 1 only (highest-value trailers)
- **Post-pilot gate:** Confirm SLA improvement, tune weights
- **Rollout:** All docks + all suppliers

---

## 💡 Key Talking Points

**For Executives:**
- Manual process takes 6 hours/week → automate to <1 hour
- Capacity overload causes $50–80K detention costs → prevent with intelligent ranking
- Single source of truth across all inbound sites

**For Planners:**
- Canvas app preserves manual override control
- No loss of auditability (all decisions logged in Dataverse)
- Planner still makes final decisions; system provides ranked suggestions

**For TSPs:**
- Email-based schedule delivery (no system changes required)
- Standardized format across all Carrier sites
- Dock slot assignment reflects actual capacity + readiness

---

## 🛠️ Presentation Customization

Before the call, customize these placeholders:

| Slide | Field | Replace With |
|-------|-------|--------------|
| 16 | `[Carrier owner name]` | Actual data owner name |
| 17–19 | `[Site X name]` | Actual SharePoint site names/URLs |
| 21 | `[Carrier owner]` | Data governance contact |
| 21 | `[Carrier TSP lead]` | TSP liaison name |

---

## 📋 Pre-Call Checklist (5 Minutes Before)

- [ ] Open `Carrier-Trailer-Prioritization-Gameplan.pptx` in presentation mode
- [ ] Test projector/screen sharing
- [ ] Have `CarrierTrailerPrioritization.zip` ready on desktop (to show file size/ready state)
- [ ] Open engagement guide + demo script in browser tabs (for post-call reference)
- [ ] Confirm all 4 call participants are on the call
- [ ] Have the pilot kickoff checklist ready (from slide 23)

---

## 📊 Slides Breakdown

- **Slides 1–3:** Opening + objectives + executive summary
- **Slides 4–7:** Problem context + proposed solution + business impact
- **Slides 8–13:** What's built (architecture + deliverables + pilot scope)
- **Slides 14–19:** Critical decisions (4 confirmation checkpoints)
- **Slides 20–21:** Call timeline + close
- **Slides 22–24:** Follow-up actions + pilot checklist + success metrics
- **Slides 25–27:** Contact info + closing slide
- **Slides 28–31:** Appendix (scoring formula, budget estimate, Phase 2 roadmap)

---

## 🎓 Speaker Notes

Speaker notes are embedded in the markdown (`slides.md`). Open that file if you need detailed talking points for any slide.

---

## 📁 Folder Structure

```
customers/carrier/presentations/trailer-prioritization-gameplan/
├── Carrier-Trailer-Prioritization-Gameplan.pptx  ← Final deliverable
├── slides.md                                      ← Source (markdown)
├── slides.html                                    ← HTML preview
├── architecture.svg                               ← Architecture diagram (optional)
├── call-plan.svg                                  ← Timeline diagram (optional)
├── microsoft-internal.css                         ← Marp theme (Microsoft branding)
├── .marp.json                                     ← Marp config
├── generate.sh                                    ← Build script (if regenerating)
└── README.md                                      ← This file
```

---

## 🔄 Regenerating the PPTX (If You Edit slides.md)

```bash
cd customers/carrier/presentations/trailer-prioritization-gameplan
npx -y @marp-team/marp-cli@latest --allow-local-files --output Carrier-Trailer-Prioritization-Gameplan.pptx slides.md
```

---

## 📞 Questions or Feedback?

If you need to adjust slides after the call:
1. Edit `slides.md` (plain text, easy to modify)
2. Regenerate PPTX using the command above
3. Share updated file with stakeholders

---

**Last updated:** April 14, 2026  
**Presentation status:** Ready for call  
**Next checkpoint:** Confirm 4 decisions + lock pilot scope
