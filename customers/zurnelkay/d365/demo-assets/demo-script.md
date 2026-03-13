# Zurn / Elkay -- Customer Service Demo Script

> **Source**: Demo Plan Review Meeting (March 4, 2026) + Copilot Notebook
> **Last Updated**: 2026-03-07 (Customer Intent Agent configured -- 10 intents, 10 SOP KB articles)
> **Demo Date**: March 12, 2026 (2 hours)
> **Guiding Principle**: Show differentiation, not feature parity. Best foot forward -- NOT like-for-like with Salesforce.
> **Execution Guide**: See [demo-execution-guide.md](demo-execution-guide.md) for exact records, IDs, navigation paths, and step-by-step presenter cheat sheet.
> **Phone Call Script**: See [phone-call-script.md](phone-call-script.md) for the inbound call dialogue and data reference.
> **Chat Demo Script**: See [chat-demo-script.md](chat-demo-script.md) for the chat scenarios (HD Supply + Ferguson) and bot flow.
> **Copilot Studio Setup**: See [copilot-studio-setup.md](copilot-studio-setup.md) for bot configuration steps.

---

## Key Feedback Applied (from March 4 Review)

| Change | Source | Action |
|--------|--------|--------|
| Remove Transition/Migration section | Mike Schmidt | Removed entirely -- premature |
| Telephony is non-negotiable | Mike Schmidt | Native D365 Voice goes all-in |
| Differentiation over parity | Chad Didriksen | Focus on what SF can't do |
| Add Chat / Digital Messaging | Chad + Benton | Added web chat from portal |
| Guided Actions equivalent | Benton Bullwinkel | Canvas pages / custom pages for serial lookup, returns, order mod |
| Workforce + Quality Management | Mike Schmidt | Added to Care Leader section |
| Tiered routing / skills | Chad + Benton | Show outcomes in agent flow, admin in separate session |
| Agent performance metrics | Benton Bullwinkel | Handle time, wait time, call duration |
| Real-time transcript + Copilot utterances | Benton Bullwinkel | Keep -- agents have this today |
| No admin/config in main demo | Benton + Lisa | Save for separate tech deep dive session |
| Terminology | Lisa Kuhns | "Customer Care Associates" (factory), "Ops Support" (logistics) |
| Platform extensibility brief mention | Mike Schmidt | Power Apps, AppSource, code-first -- just mention, don't deep dive |
| NOT like-for-like | Mike + Benton | Confirmed: show best foot forward |
| Get AIP routing document | Benton | Bill to follow up via email |

---

## Key Personas

| Persona | Role | Focus |
|---------|------|-------|
| **Customer Care Associate** | Frontline agent (factory teams) | Handles inbound customer inquiries across email, phone, and chat |
| **Lisa Kuhns & Michelle Scarrow** | Care Leaders | Visibility into case handling, routing, escalations, service quality |
| **Chad Didriksen, Mike Schmidt, John Kuchinski** | IT / CRM Leaders | Evaluating Microsoft vs Salesforce -- differentiation, integration, workflow |
| **Benton Bullwinkel** | Application Architect | Technical depth -- guided actions, routing, ERP integration, DevOps |
| **Justin Luna** | Salesforce Developer | Technical comparison -- wants to SEE it, not read about it |
| **Shawn Walsh** | Sales Manager | Baseline familiarity with Microsoft Sales features |

> **Note from Justin**: "It would be easier for me to see like a visual demo... This is a lot of verbiage for me" -- Keep it visual, minimize slides.

---

## Planned Follow-Up Sessions

| Session | Audience | Topics |
|---------|----------|--------|
| **Tech Deep Dive: Routing & WEM** | Benton, Chad, Justin | AIP process, case routing rules, skills config, queue management, ERP lookups |
| **Guided Actions Deep Dive** | Benton, Justin | Power Apps canvas pages, custom pages, BPFs -- equivalent of SF screen flows |
| **IT Benefits / Platform** | Mike, Chad, John | Cost reduction, contract consolidation, DevOps pipeline, extensibility |

---

# Part 1 -- Demo Walkthrough

## 1. Connect & Orient (~10 min)

> **Action**: Introductions, brief D365 UI orientation

| | |
|---|---|
| **Context** | Care associates do NOT currently use Dynamics Sales. They have no exposure to the D365 UI. Brief orientation needed before diving in. |
| **What to Say** | "Thank you all for joining. Quick intros -- I'm Bill, solution engineer focused on Power Platform and Dynamics 365. Today is designed around YOUR priorities: Email Integration, Workflow Automation, and Omni-Channel Case Management. But more importantly, we heard from Chad -- you want to see how we're DIFFERENT, not just check boxes. So instead of feature matching, we're going to put you inside the experience and let you feel the difference. Let me do a quick 2-minute orientation on the workspace layout before we dive in." |
| **What to Show** | Quick tour: left nav, session tabs, Copilot panel location, how tabs/sessions work in the multisession workspace. |

---

## 2. Their World Today (~5 min)

> **Action**: Validate challenges, don't belabor

| | |
|---|---|
| **What to Say** | "We've spent time with your teams understanding the current state. Customer Care Associates start their day across Salesforce, ERP screens, Outlook, Teams, and shared drives. Routing involves manual triage. Information is scattered. And your tiered customer model -- where an 80-20 analysis drives who gets priority attention -- requires lookups to external systems that aren't always connected. Does that still ring true? Anything we should add before we jump in?" |
| **Key Points** | Swivel-chair operations, manual routing, disconnected channels, no internal KB, HubSpot chat not connected to care, Genesis telephony doesn't integrate well with SF. |
| **DO NOT** | Spend more than 5 minutes here. The room wants to SEE things, not hear about problems. |

---

## 3. Day in the Life: Customer Care Associate (~80 min)

### 3a. Starting the Day: CS Workspace

> **Action**: Open Customer Service Workspace, show My Active Cases, dashboards

| | |
|---|---|
| **What to Say** | "When a Customer Care Associate logs in, this is their home. No Outlook to open first, no ERP to check, no Salesforce tab. Everything starts here. I can see: my assigned cases with color-coded tier levels, SLA timers that tell me what's about to breach, priority cases that need immediate attention, and my workload across all channels -- email, phone, and chat -- in one view." |
| **Differentiation** | Unified workspace replaces 3-4 separate application windows. SLA timers are live, not report-based. Tier-level pills (Tier 1 red, Tier 2 orange, Tier 3 blue, Tier 4 gray) show customer importance at a glance -- driven by the same ERP data that currently requires manual lookup. |
| **Show** | My Active Cases view with Tier Level column, priority indicators, SLA countdown, case origin icons. |

---

### 3b. Email Case Creation & Copilot

> **Action**: Show inbound email auto-creating a case, Copilot summarization

| | |
|---|---|
| **What to Say** | "Let's walk through what happens when a customer emails the team. This email just came in from a distributor asking about a delayed shipment. In the current world, someone would manually create a case, copy-paste details, search for the customer record, and try to figure out context from the email chain. Here, the system does all of that instantly: it identified the customer, created the case, linked the email thread, populated the issue details, AND applied your routing rules to get it to the right person. Zero manual steps. And watch this -- I ask Copilot to summarize and it gives me the full picture in seconds: what the customer is asking, the history, and suggested next actions." |
| **Differentiation** | Auto-case creation + auto-customer matching + auto-routing vs. manual triage in SF. Copilot summarization eliminates reading entire email chains. |
| **Show** | Inbound email, auto-created case, Copilot summary, suggested response draft. |

---

### 3c. Working the Case: Timeline & Customer 360

> **Action**: Open case timeline, account record, show cross-system data

| | |
|---|---|
| **What to Say** | "Now look at the timeline. Every email, every phone call, every note, every internal chat -- it's all here in one chronological view. And when I click into the customer account, I see the same data that Sales sees. There's no integration to build -- it's the same platform. Previous cases, open orders, products they own, warranty status, their tier classification. This is one of the biggest differentiators: in Dynamics, Sales and Service share the same data natively. There's no connector, no sync, no middleware. It's one platform." |
| **Differentiation** | Unified data platform -- Sales + Service + ERP visibility without integration. SF requires connectors to share data between Sales Cloud and Service Cloud. |
| **Show** | Case timeline, account record with Sales data visible, product/warranty/order info. |

---

### 3d. Knowledge in the Flow of Work

> **Action**: Show knowledge suggestions in Copilot panel and KB search tab

| | |
|---|---|
| **Context** | Per Benton: current KB is customer-facing only (engineering-approved, from Zendesk-to-SF migration). No internal KB for agents. This is a gap they want to fill. We've seeded 10 prescriptive SOP runbooks for common service intents -- the audience will see these surface during the phone call. |
| **What to Say** | "As I'm working this case, the system is already surfacing relevant knowledge articles. Today, your knowledge base is primarily customer-facing -- engineering-approved articles from the help center. But there's a huge opportunity here: an internal knowledge base that helps Customer Care Associates resolve cases faster without having to track down the one person who 'knows the trick.' Notice the system isn't just searching by keyword -- it's reading the case context and proactively suggesting articles the associate might need. You'll see this get even smarter in a moment when we take a live phone call. And when I resolve a case and there ISN'T an article for this issue, the system prompts me to create one -- with Copilot drafting it from my case notes. That goes through an approval workflow and then it's available for the next associate who gets the same question." |
| **DO NOT** | Go deep on KB admin, approval workflows, or the KM agent here. Show it in the flow of work only. Deep dive on KB transition is a separate conversation. |
| **Show** | Copilot suggesting KB articles, KB search tab, brief view of "create article from case" prompt. |

---

### 3e. Teams Collaboration Embedded

> **Action**: Open embedded Teams panel, start a chat from case record

| | |
|---|---|
| **Context** | Chad specifically called this out: "integration with Teams, that's something we don't have with Salesforce." Currently associates go to Teams separately, and those conversations aren't captured in SF. |
| **What to Say** | "Here's something that closes a major gap Chad mentioned. Right now, if an associate needs help, they leave Salesforce, open Teams, find the right person, manually paste case context, and the whole conversation is lost to the case record. In Dynamics, I start a Teams chat FROM the case -- the context comes with me automatically. When the shipping coordinator replies that a part is back-ordered, I click 'Capture to Case' and it logs directly into the timeline. No context switching, no lost information." |
| **Differentiation** | Embedded Teams with auto-capture to case record. SF has no native Teams integration. |
| **Show** | Embedded Teams panel, starting a chat with case context auto-populated, capture to timeline. |

---

### 3f. Handling a Customer Call -- NATIVE VOICE (Non-Negotiable)

> **Action**: Simulate inbound call, screen pop, real-time transcript, Copilot suggestions
> **CRITICAL**: Mike said telephony is non-negotiable. Go all-in here.

| | |
|---|---|
| **What to Say** | "Now let's take a customer call. This is native telephony built into Dynamics -- no third-party integration required. As the call comes in, the system recognizes the caller, pops the customer record, and I immediately see: their account, every open case, recent orders, SLA status, and their tier level. I don't have to ask 'who am I speaking with?' -- I already know. Now watch the right side of the screen as we talk. The real-time transcript is appearing -- and Copilot is listening. [Pause -- let Mike mention the PO modification.] See that? Mike just said he needs to modify the order, and the system immediately surfaced a step-by-step procedure for processing order quantity changes. The associate didn't search for anything -- the system heard the conversation and said 'here's your playbook.' [Pause -- let Mike ask to expedite.] Now he's asking to expedite, and look -- it switched to an expediting procedure that includes tier-based shipping rules. The system isn't just finding keywords. It understands the SERVICE INTENT behind what the customer is saying -- and it adapts in real time as the conversation evolves. This is the difference between a search engine and an intelligent assistant." |
| **Differentiation** | Native telephony with real-time transcript + Copilot utterance-based suggestions. Genesis Cloud doesn't integrate well with SF (Chad's pain point). This replaces Genesis entirely. |
| **Show** | Inbound call simulation, screen pop with full customer 360, real-time transcript, Copilot suggestions appearing based on conversation, sentiment analysis. |

| | |
|---|---|
| **After-Call Wrap-Up** | "And here's where you save massive amounts of time. Wrap-up typically takes 5-10 minutes per interaction -- associates type notes, update fields, log actions. With one click, Copilot drafts the summary from the transcript, logs the actions taken, updates case fields, and drafts the follow-up email. What used to take minutes now takes seconds. Multiply that across every call, every day, across the entire team -- that's a significant productivity gain." |
| **Show** | Copilot auto-summary from transcript, auto-populated case notes, draft follow-up email. |

---

### 3g. Chat / Digital Messaging

> **Action**: Show web chat from a portal, agent receiving chat in workspace

| | |
|---|---|
| **Context** | Currently in HubSpot (marketing), not connected to customer care. Both Chad and Benton confirmed they want to see this. |
| **What to Say** | "You mentioned that chat is currently running through HubSpot for marketing, but customer care doesn't have access to it. In Dynamics, chat is just another channel in the same workspace. A customer visits your portal, starts a chat, and it arrives right here alongside my emails and phone calls. Same routing rules, same capacity management, same customer context. And notice -- the same intelligence we saw on the phone call is working here too. When Derek describes the sensor issue, the system recognizes the intent and starts surfacing relevant procedures and KB articles before the agent even asks. It doesn't matter if the customer calls, emails, or chats -- the system is always listening, always guiding. And because it's the same platform, I can hand off between channels seamlessly -- if a chat needs to become a phone call, the context carries over." |
| **Differentiation** | Unified channel management. Chat, email, phone all in one workspace with shared routing and capacity. Currently scattered across HubSpot/SF/Genesis. |
| **Show** | Portal chat widget, associate receiving chat in workspace, customer identified, knowledge suggestions appearing in real time. |

---

### 3h. Tiered Routing & Skills (Outcomes View)

> **Action**: Show how a case arrived at the right associate -- demonstrate the outcome, not the admin config

| | |
|---|---|
| **Context** | Benton & Chad emphasized: customer tier from ERP, hot words, skills-based routing, 80-20 classification, queue priority, some customers go straight to specific associates. This is CRITICAL but show outcomes in main demo; admin config in tech deep dive. |
| **What to Say** | "Let me show you why this case landed with this specific associate. The system evaluated multiple factors: the customer's tier level -- this is a Tier 1 Strategic account based on your ERP classification -- so they went to the front of the line. The email subject contained the word 'urgent,' which triggered our hot-word detection and escalated the priority. And because this is a hydration product question, it matched an associate with the right product skills. All of that happened automatically in milliseconds. No manual triage, no reading the email and deciding where to route it. And if an associate is already at capacity on phone calls, the system knows not to send them more work until they have bandwidth." |
| **Differentiation** | Intelligent multi-factor routing (tier + keywords + skills + capacity) vs. SF's queue-based or basic skills-based backlog. Unified capacity management across all channels. |
| **Show** | Case routing trace (how it got here), tier level on case record, hot-word banner, associate skills profile, capacity dashboard. |
| **DO NOT** | Open Admin Center or show rule configuration. Say: "In our tech deep dive session, we'll walk through exactly how these rules are set up and how they map to your AIP process." |

---

### 3i. Guided Process Flows (Salesforce "Guided Actions" Equivalent)

> **Action**: Demo the Service Toolkit custom page -- **Order Modification is the main flow**; other tools are bonus if time permits.
> **Execution details**: See [demo-execution-guide.md](demo-execution-guide.md) Section 3i for exact test data, serial numbers, and step-by-step walkthrough.

| | |
|---|---|
| **Context** | Benton's specifically requested feature. In SF, they use "guided actions" (screen flows) -- wizard-like popup panels for tasks like: entering a serial number to add an asset, shipping a carton with dimensions, returning 3 items from an order, order modification by line. These simplify complex operations into step-by-step experiences without exposing full forms. |
| **What to Say** | "Benton, you asked about your guided actions -- those step-by-step wizards that walk associates through complex tasks without exposing complicated forms. Let me show you our equivalent. This is the **Service Toolkit** -- a single custom page in the productivity pane with five tools: Order Update, Shipment Tracker, Quick Quote, Return/RMA, and Warranty Lookup. Each one is a guided wizard. Let me walk you through the Order Modification flow -- and if we have time, I'll show you a few of the others." |
| **Differentiation** | Power Apps custom pages / canvas apps embedded in case forms -- equivalent to SF screen flows but with full access to the Microsoft data platform, ERP integration, and extensibility. Plus: code-first apps coming for more complex scenarios. |

**Main Flow -- Order Modification** (during or after the phone call):

| | |
|---|---|
| **What to Say** | "I'm going to modify Mike's order right here in the side panel. I open the Service Toolkit, select Order Update, and I see PO #94820 with 5 line items. I check 'cancel' on the drinking fountains and the sinks -- that's $67,000 coming off the order. I move the delivery up to March 10 for the three remaining lines. Hit Review -- the system shows me exactly what's changing with strikethrough on the cancelled lines and a credit total. Submit. Done. And with one more click, it posts the change summary to the case timeline and drafts Mike's confirmation email. Four screens, 30 seconds, zero system switching." |
| **Show** | Open Home screen → Order Update → select PO #94820 → cancel 2 lines → change dates → Review → Submit → Add to Timeline → Draft Email. |

**If We Have Time -- Additional Tools** (2-3 min each):

| Tool | Quick Pitch | What to Show |
|------|------------|--------------|
| **Warranty Lookup** | "Agent types a serial number, sees warranty status instantly, files a claim in 2 clicks." | Search `123456ABC` (active warranty, green badge), then `ELK-2023-00471` (expired, red badge). Submit a claim. |
| **Return / RMA** | "Filing an RMA without leaving the case -- product, customer, reason, amount, 30 seconds." | Fill in form for Ferguson / Elkay EZS8L Cooler / freight damage. Submit. |
| **Quick Quote** | "Building a quote during a call -- select the account, add products, review the total." | Pick Ferguson + Elkay brand, add 2 products, review. Mention save is coming via Power Automate. |
| **Shipment Tracker** | "Real-time tracking right in the workspace via a custom connector." | Enter a tracking number, select carrier, show results (requires ShipEngine connector). |

| | |
|---|---|
| **Wrap-up** | "Each of these tools replaces a separate system or manual process. Today your associates switch to ERP for order changes, call the warehouse for tracking, open a different form for RMAs, and look up warranty in yet another system. Here, it's all in one panel, connected to the same case, the same customer, the same data. And because it's built on Power Apps, your team can add new tools or modify existing ones without a full development cycle." |

---

### 3j. Proactive Notifications & Alerts

> **Action**: Show notification examples -- SLA breach approaching, queue wait time alerts

| | |
|---|---|
| **Context** | Benton: "One of the challenges we've had is notifying based on different workflow cases to alert agents." He wants moderated notifications -- "only send the valuable stuff." |
| **What to Say** | "You mentioned notification fatigue is a real concern -- associates get bombarded and start ignoring everything. In Dynamics, notifications are highly configurable. You decide which events matter: SLA breach approaching in 30 minutes? That's a notification. A Tier 1 customer has been waiting in queue for more than 2 minutes? Alert the supervisor. A hot-word case just came in? Push it to attention. But you moderate it -- only the high-value, actionable alerts get through. And for supervisors, the Omnichannel real-time dashboard shows queue health, wait times, and associate availability without needing push notifications at all." |
| **Show** | In-app notification example, SLA warning toast, supervisor dashboard with queue health. |

---

## 4. Care Leader View (~15 min)

> **Action**: Switch to supervisor/manager persona

### 4a. Dashboards & Real-Time Monitoring

| | |
|---|---|
| **What to Say** | "Now let me switch to what Lisa and Michelle would see. This is the Omnichannel real-time analytics dashboard. You can see: case volume by channel, SLA performance across the team, which associates are available versus at capacity, queue wait times, and trend data. Previously, getting this view required pulling reports from Salesforce, ERP, and spreadsheets separately -- often taking days. Here it's real-time." |
| **Show** | Omnichannel Insights, real-time dashboard, agent status grid, SLA compliance chart. |

### 4b. Agent Performance Metrics

| | |
|---|---|
| **Context** | Benton: "How long did the associate spend on the email? How long on the call? How long was the customer waiting? Those timing metrics are equally as important." Currently using multiple tools to get this data. |
| **What to Say** | "Benton asked about performance metrics -- handle time, wait time, call duration. All of that is captured natively because the telephony, email, and chat are all running through the same system. You don't need to pull data from Genesis separately or reconcile reports from multiple tools. One platform, one source of truth for every metric." |
| **Show** | Agent performance report, handle time by channel, average wait time, customer satisfaction trends. |

### 4c. Workforce Management

| | |
|---|---|
| **Context** | Zurn Elkay currently manages scheduling outside Salesforce. The WFM module is fully integrated -- scheduling, forecasting, adherence, shift bidding, and swapping all live inside the same platform that handles routing and case assignment. |
| **What to Say** | "And here's something that's now built right into the platform -- Workforce Management. Let me show you what it looks like when scheduling lives in the same system as your routing engine." |
| **Show** | Navigate to **CS Admin Center > Workforce Management > Schedule Management**. Show the five shift plans: Morning (6am-2pm), Day (8am-5pm), Afternoon (2pm-10pm), Staggered (7am-3pm), and Weekend. |
| **What to Say** | "Each shift plan defines the hours, required staffing, and weekly recurrence. The Day Shift needs 6 agents, the Morning needs 4, and Weekends need 2 for emergency coverage only. Supervisors drag agents onto shifts, and once published, the routing engine knows exactly who's available." |
| **Show** | Open the **Zurn Elkay Day Shift** plan. Point out the time window (8am-5pm CT), Mon-Fri recurrence, and required staff (6). |
| **What to Say** | "Now here's the key differentiator -- shift-based routing is enabled. That means the schedule isn't just a planning document. It directly governs who receives work. If Renee Lo is on PTO, she won't get routed cases, period. The system already knows because her time-off request is right here." |
| **Show** | Navigate to **Time Off Requests**. Show Renee Lo's upcoming vacation, Enrico Cattaneo's sick day, and David So's planned vacation. |
| **What to Say** | "Agents can also bid on open shifts and request swaps directly in the platform -- we've enabled bidding and swapping. That self-service capability reduces the back-and-forth between agents and supervisors." |
| **Show** | Briefly show the **Shift Activity Types**: Case Work (assignable), Break, Lunch, Training, Team Meeting, Coaching (non-assignable). |
| **What to Say** | "Every shift includes structured activities -- breaks, lunch, training, coaching. Assignable time like Case Work is when the agent receives routed items. Non-assignable time like Training or Meetings means the agent is off the routing queue automatically. No manual status toggling." |
| **Competitive Point** | "With Salesforce Service Cloud, WFM typically requires a separate product (Workforce Engagement) or a third-party integration. Here it's native -- same data model, same admin experience, no sync issues between your scheduling tool and your routing engine." |

### 4d. Quality Management

| | |
|---|---|
| **What to Say** | "The last piece of the care leader's toolkit is Quality Management -- your QA process, built into the platform. We've configured something called the **Manufacturing Service Quality Standard**. It's a 21-question evaluation across six weighted sections: Customer Identification, Technical Accuracy, Process Compliance, Resolution Effectiveness, Communication, and Tool Adoption. Each question has AI-response enabled, so the system can auto-score every interaction." |
| **Show** | Navigate to **Customer Service admin center → Quality Management → Evaluation criteria** → open **Manufacturing Service Quality Standard**. Show the 6 sections and scroll through a few questions. Then go to **Evaluation plans** and show the two plans: **Daily Case Quality Review** (recurring/daily for cases) and **Conversation Quality Review** (trigger-based on closed conversations). |
| **What to Say** | "There are two approaches. Manual evaluation -- a supervisor picks a conversation, scores it against these criteria. Or the Quality Management Agent -- an AI agent that automatically scores every interaction and flags the ones that need human review. Instead of randomly sampling 5% of calls, the system tells you which conversations need coaching." |
| **What to Say** | "Lisa, think about your QA process today. How many calls does your team review per week? And how do you decide which ones to review? With the QM Agent, every interaction gets evaluated, and the supervisor's time goes to the conversations that actually need coaching -- not random sampling." |
| **Show (if simulation has run)** | Open a scored evaluation from the simulation results. Walk through the per-section scores, the AI's rationale, and the overall score. Point out how the AI identified specific moments in the transcript. |
| **Competitive Point** | "With Salesforce, quality management typically requires Einstein Conversation Insights as an add-on, plus a third-party QA tool for structured evaluations. Here it's native -- same data, same platform, same admin experience." |

---

## 5. AI Agents -- Outcomes Only (~10 min)

> **Action**: Show agent outcomes, NOT configuration
> Per Benton: "how AI's configured is probably not necessary. Just what would be their best experience."

| | |
|---|---|
| **What to Say** | "Let's talk about what just happened during that phone call and the chat -- because it wasn't magic, and it's important you understand why. Remember when Mike mentioned the order modification and a step-by-step procedure appeared instantly? That's what Microsoft calls the **Intent Agent**. It's not searching your knowledge base by keyword. It's listening to the conversation, understanding the SERVICE INTENT -- 'this customer wants to change an order' -- and delivering a prescriptive runbook: here's step one, here's step two, here's what to check, here's the policy. We tailored it for your world -- your customer tiers, your distributor model, your product lines. So a new hire doesn't need six months of tribal knowledge to handle a complex call. The system gives them the playbook in real time. Now there are two more agents I want you to know about. The **Case Management Agent** watches your queue. If a case has been sitting for 48 hours waiting on a customer response, it sends a follow-up automatically. If a new case matches a pattern it's seen resolved 50 times before, it can suggest the resolution -- or handle it without human intervention. Think about that for your Tier 3 and Tier 4 volume. And the **Knowledge Management Agent** does something your team has been asking for: it watches for patterns. If 15 cases come in about the same bottle filler issue and there's no internal article, it drafts one and sends it for review. Remember how Benton said your KB is customer-facing only? This agent starts building your internal knowledge base automatically from the cases your team is already resolving." |
| **Differentiation** | Three agents that deliver real service outcomes, not chatbot builders. The Intent Agent was pre-configured for Zurn Elkay's top 10 service scenarios with prescriptive SOPs -- SF charges separately for similar capabilities and requires extensive custom prompt engineering. |

---

## 6. Platform Extensibility (~3 min)

> Per Mike: "Just mention it. I don't think we go into any detail."

| | |
|---|---|
| **What to Say** | "One last thing Mike asked us to highlight. Everything you've seen today is the out-of-the-box platform. But the entire application is built on Power Apps and Dataverse -- which means your team can extend, customize, and build on top of it. Need a custom warranty module? Power Apps. Need to connect to a third-party logistics system? Power Automate. Need an app from a partner? AppSource has thousands, just like the AppExchange you know today. And for developers like Justin, code-first options are coming that give you full code-level control when you need it. The key point: this platform grows with you." |
| **DO NOT** | Demo AppSource or Power Apps in detail. Just state the capability and move on. |

---

## 7. Close (~5 min)

| | |
|---|---|
| **What to Say** | "To wrap up -- you asked us to show differentiation, not a checkbox exercise. Here's what we showed today that's different: (1) One platform for Sales and Service -- no connectors, no middleware, no sync issues. (2) Native telephony with real-time transcript and an AI that understands what the customer is asking and instantly gives the associate the right procedure -- replaces Genesis entirely. (3) Chat, email, and phone in the same workspace with unified routing that considers customer tier, keywords, skills, AND associate capacity. (4) Copilot embedded everywhere -- summarizing, suggesting, drafting, guiding -- reducing handle time and wrap-up from minutes to seconds. (5) AI agents that don't just answer questions but actively manage your operation: detecting intent, building knowledge, and automating follow-ups. (6) A platform that your team can extend with Power Apps, Power Automate, and soon code-first development. We have the tech deep dive scheduled to go through routing configuration, the AIP process, and guided action equivalents in detail. Thank you for your time." |

---

## REMOVED from Previous Script

| Section | Reason |
|---------|--------|
| Transition / Migration Planning | Mike: "none of that is relevant unless we make the recommendation and it's approved for funding" |
| Admin Center Configuration | Moved to separate tech deep dive session |
| Part 2 Business Narrative | Consolidated into Part 1 flow -- no need for two versions |

---

## Open Items / Action Items

| Item | Owner | Status |
|------|-------|--------|
| Get AIP routing process document from Benton | Bill | Pending -- email Benton |
| Get guided action screenshots from SF | Bill | Pending -- requested from Benton |
| Review Pulse workflow documentation | Bill | Link provided -- needs access |
| Set up tech deep dive session | Dana/Bill | Not yet scheduled |
| Set up guided actions deep dive | Dana/Bill | Not yet scheduled |
| Confirm Genesis replacement appetite | Dana | Discussed -- "absolutely open to replacing" |
| Review helpcenter.lk.com portal for KB migration scoping | Bill | Not yet started |

---

## Demo Environment Readiness Checklist

| Component | Status | Notes |
|-----------|--------|-------|
| Customer Service Workspace configured | Done | Scripts 00-12 |
| Email auto-case creation & routing | Done | 13 route-to-queue rules |
| Hot-word detection (6 keywords) | Done | Urgent, Emergency, Recall, Safety, Legal, Next Day Air |
| Tier-level field on cases (color-coded) | Done | Script 13 -- Tier 1-4 pills in views |
| Tier-based entitlements | Done | Script 09 -- 13 entitlements across 4 tiers |
| SLAs configured | Done | First response 4hrs, resolution 8hrs |
| Queue membership (18 queues) | Done | Script 12 |
| Knowledge articles (30+) | Done | 20 product/case articles + 10 prescriptive SOP articles for Intent Agent |
| JS hot-word banners on forms | Done | RED (critical) / YELLOW (urgency) |
| Native Voice Channel | Done | Workstream ID: 940cdd5e-b83e-8107-b01c-af6ed452cb25 |
| Chat Channel / Portal widget | Done | Workstream ID: 9bc69cb2-6cd0-b8b5-8fab-da65ba399e94, Portal: zurnelkaycustomercare.powerappsportals.com |
| Service Toolkit custom page (10 screens) | **YAML Ready** | 10 screens built -- paste into Power Apps (see custom-page-yaml/) |
| Demo data: Sales Orders (4 orders) | Done | Ferguson hero order PO-94820 + 3 context orders |
| Demo data: Product Serials (7 records) | Done | Zurn + Elkay, mix active/expired warranties |
| Demo data: Credit Memo / RMA (4 records) | Done | 4 Zurn/Elkay RMAs with reasons, lot numbers, amounts |
| Demo data: Warranty Claims (4 records) | Done | Submitted → Denied, linked to Product Serials |
| ShipEngine custom connector | **TODO** | Import swagger JSON, create connection |
| Quick Quote save (Power Automate) | **BACKLOG** | Requires flow to bypass Project Operations fields |
| Dashboards (supervisor) | Done | Omnichannel Insights + real-time analytics enabled |
| Workforce Management | Done | Script 23 -- 6 shift activity types, 7 time-off types, 5 shift plans (Morning/Day/Afternoon/Staggered/Weekend), 5 time-off requests, 14 agents assigned to shifts (1,196 bookings). All WFM features enabled (forecast, capacity, scheduling, shift-based routing, bidding, swapping). |
| Quality Management | Done | Connection refs fixed, 6 QEA/KM flows activated, QEA + KM agents published, **Manufacturing Service Quality Standard** criteria published (6 sections, 21 questions), 2 evaluation plans published (Daily Case + Conversation trigger) |
| Teams Embedded Chat | Done | Enabled on case form |
| Copilot for CS enabled | Done | Summarization, KB suggestions, drafting |
| Intent Agent (10 intents, 2 groups) | Done | Script 22 -- descriptions, agent instructions, 10 SOP KB articles |
| Case Mgmt / KM Agents | Done | Connection refs fixed, Case Management Agent + Knowledge Harvest Agent flows active |
| Sample data: phone call scenario | Done | Script 17 -- Ferguson hero record, Mike Reynolds contact, 3 orders, phone case with timeline, demo call script |
| Sample data: chat scenario | Done | Script 18 -- HD Supply hero record, Derek Lawson, 2 chat cases, timeline. Copilot Studio bot setup guide ready. |
| Portal branding (Zurn Elkay) | Done | Scripts 14-16 -- Header, Footer, Home, KB page, Chat widget |
| Portal: Warranty/Claims/RMA views | **BACKLOG** | Customer-facing warranty lookup, claims history, RMA status |
| Account 360 canvas app | **TODO** | Order lookup, ERP simulation |
| Simulated phone call script | **BACKLOG** | Programmatic call simulation for live demo -- fake inbound call with transcript |
