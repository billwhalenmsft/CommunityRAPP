# Quality Management — Evaluation Criteria & Plan Setup Guide

> **Reusable for all discrete manufacturing demos.** This guide defines a standard evaluation criteria and two evaluation plans designed for manufacturing customer service operations. The criteria tie to common manufacturing service priorities: tiered customer models, product knowledge accuracy, escalation/safety handling, SLA compliance, and AI tool adoption.

---

## Prerequisites

Before creating criteria and plans, confirm:

- [ ] Quality Evaluation Agent is enabled in Copilot Service admin center
- [ ] Connection references are configured (Dataverse + Copilot Studio)
- [ ] All 6 QEA/KM flows are active (Knowledge Harvest Trigger V2, AI Evaluation Flow for Conversation, Expire evaluations, QEA On Demand, QEA Simulation, QEA Simulation B)
- [ ] Microsoft Copilot credits are set up (pay-as-you-go)
- [ ] User has Quality Administrator or Quality Manager role

---

## Evaluation Criteria: Manufacturing Service Quality Standard

### How to Create

1. In Copilot Service workspace → **Evaluation criteria** → **New**
2. Fill in **Criteria details**, **Sections**, and **Questions** as specified below
3. **Save** → **Publish**
4. Optionally run a **Simulation** to validate against recent cases

---

### Criteria Details

| Field | Value |
|-------|-------|
| **Criteria name** | Manufacturing Service Quality Standard |
| **Description** | Standard quality evaluation criteria for discrete manufacturing customer service. Evaluates agent performance across customer handling, technical accuracy, process compliance, resolution quality, communication, and tool adoption. |
| **Criteria scoring** | On |
| **Language** | English |

### Form-Level Instructions

> Paste this into the **Add form level instructions** field:

```
Evaluate the agent's performance on this customer service interaction for a discrete manufacturing company. The company serves distributors, contractors, and end-users through email and phone channels with a tiered customer model (Tier 1 = Strategic / highest priority through Tier 4 = Basic). 

Agents are expected to: verify customer identity, reference product knowledge, follow escalation procedures for safety and compliance terms (hot words: Urgent, Emergency, Recall, Safety, Legal, Next Day Air), meet SLA targets, document resolutions thoroughly, and leverage AI tools (Copilot, knowledge base) where available. 

Score based on what is observable in the case notes, conversation transcript, and case metadata. If a question does not apply to the interaction, select the neutral or "Not applicable" option.
```

---

### Section 1: Customer Identification & Account Handling

| Field | Value |
|-------|-------|
| **Section name** | Customer Identification & Account Handling |
| **Description** | Evaluates whether the agent properly identified the customer, verified account details, and recognized the customer's service tier and entitlement status. |
| **Section weight (%)** | 15 |

#### Q1: Did the agent verify the customer's identity and account?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent confirmed the customer name, account, and contact information at the beginning of the interaction. Look for evidence in case notes or conversation transcript. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent confirmed customer identity, account name, and/or contact details. |
| **No** | Agent did not verify customer identity or account information before proceeding. |

#### Q2: Did the agent identify the customer's service tier or priority level?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent acknowledged or acted upon the customer's tier level (e.g., Strategic, Key, Standard, Basic). This may be evident from routing priority, SLA handling, or explicit mention in notes. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent acknowledged or acted on the customer's service tier (e.g., prioritized a Tier 1 account, followed standard process for Tier 3). |
| **No** | No evidence that the agent recognized or acted on the customer's service tier. |

#### Q3: Did the agent check entitlement or warranty status when relevant?

| Field | Value |
|-------|-------|
| **Answer type** | Choose from list |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | If the interaction involved a product issue, return request, or warranty claim, the agent should have checked the customer's entitlement or warranty status. Select "Not applicable" if the interaction did not require entitlement verification. |

| Answer Option | Instructions |
|---------------|-------------|
| **Verified entitlement** | Agent checked and confirmed the customer's entitlement, warranty, or service agreement status. |
| **Did not verify (should have)** | The interaction warranted an entitlement check but the agent did not perform one. |
| **Not applicable** | The interaction did not involve product issues, returns, or warranty claims. |

---

### Section 2: Technical Accuracy & Product Knowledge

| Field | Value |
|-------|-------|
| **Section name** | Technical Accuracy & Product Knowledge |
| **Description** | Evaluates the agent's product knowledge, accuracy of technical information provided, and appropriate use of knowledge articles and documentation. |
| **Section weight (%)** | 25 |

#### Q1: Did the agent demonstrate accurate product knowledge?

| Field | Value |
|-------|-------|
| **Answer type** | Multiple choice |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Evaluate whether the agent correctly referenced product names, part numbers, specifications, compatibility information, or technical procedures. Look for accuracy in the information provided to the customer. |

| Answer Option | Instructions |
|---------------|-------------|
| **Demonstrated strong product knowledge** | Agent referenced specific product details, specs, or part numbers accurately and confidently. |
| **Adequate product knowledge** | Agent provided generally correct information but lacked specificity or depth. |
| **Product knowledge gaps observed** | Agent provided incorrect product information or could not answer basic product questions. |
| **Unable to assess** | The interaction did not require product-specific knowledge. |

#### Q2: Did the agent reference relevant knowledge articles or documentation?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent searched for and referenced internal knowledge articles, technical documentation, or standard operating procedures. Evidence includes KB article links in case notes, Copilot suggestions accepted, or documented references to procedures. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent referenced or linked at least one knowledge article, technical document, or SOP during the interaction. |
| **No** | No evidence that the agent consulted the knowledge base or referenced documentation. |

#### Q3: Was the technical diagnosis or troubleshooting approach appropriate?

| Field | Value |
|-------|-------|
| **Answer type** | Multiple choice |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | For technical issues, evaluate whether the agent followed a logical troubleshooting sequence, asked the right questions, and worked toward identifying the correct root cause. Consider whether the agent gathered sufficient information before proposing a solution. |

| Answer Option | Instructions |
|---------------|-------------|
| **Systematic and thorough diagnosis** | Agent followed a logical troubleshooting process, asked appropriate clarifying questions, and correctly identified the issue. |
| **Adequate diagnosis** | Agent made a reasonable attempt at diagnosis but missed some steps or questions. |
| **Incomplete or incorrect diagnosis** | Agent jumped to conclusions, skipped key troubleshooting steps, or arrived at an incorrect diagnosis. |
| **No diagnosis required** | The interaction did not involve a technical issue requiring diagnosis (e.g., order status inquiry). |

#### Q4: Did the agent provide accurate part numbers, specs, or compatibility info?

| Field | Value |
|-------|-------|
| **Answer type** | Choose from list |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | If the customer asked about specific parts, replacement components, or product compatibility, evaluate whether the agent's response was accurate. Select "Not applicable" if no specific part or specification information was requested. |

| Answer Option | Instructions |
|---------------|-------------|
| **Accurate information provided** | Agent provided correct part numbers, specifications, or compatibility information. |
| **Inaccurate information provided** | Agent provided incorrect part numbers, specs, or compatibility data. |
| **Not applicable** | No specific part or specification information was requested during the interaction. |

---

### Section 3: Process Compliance & Escalation Handling

| Field | Value |
|-------|-------|
| **Section name** | Process Compliance & Escalation Handling |
| **Description** | Evaluates adherence to standard operating procedures, proper handling of escalation triggers (hot words, safety terms), and compliance with organizational policies. |
| **Section weight (%)** | 20 |

#### Q1: Did the agent follow the standard case handling procedure?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Evaluate whether the agent followed the expected workflow: greeting, verification, issue capture, investigation, resolution, documentation, and closure. Check that required fields were populated and case notes are complete. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent followed the standard case handling workflow and populated required fields. |
| **No** | Agent skipped key process steps, left required fields empty, or deviated from the expected workflow. |

#### Q2: Were escalation triggers (hot words) handled appropriately?

| Field | Value |
|-------|-------|
| **Answer type** | Choose from list |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the interaction contained priority keywords such as "urgent", "emergency", "recall", "safety", "legal", or "next day air". If present, verify the agent escalated or adjusted priority per the hot word policy. If no triggers were present, select "No escalation triggers present". |

| Answer Option | Instructions |
|---------------|-------------|
| **Correctly identified and escalated** | Agent detected the escalation keyword and took appropriate action (priority boost, supervisor notification, or tier escalation). |
| **Missed an escalation trigger** | An escalation trigger was present in the interaction but the agent did not escalate or adjust priority. |
| **Escalated unnecessarily** | Agent escalated when no trigger or business justification existed. |
| **No escalation triggers present** | The interaction did not contain any escalation keywords or scenarios requiring escalation. |

#### Q3: Did the agent route or escalate to the correct team?

| Field | Value |
|-------|-------|
| **Answer type** | Choose from list |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | If the case required escalation to a specialist, supervisor, or different team, evaluate whether the agent chose the correct destination. Consider brand alignment (correct product team), skill requirements, and tier-based routing rules. |

| Answer Option | Instructions |
|---------------|-------------|
| **Correctly routed or escalated** | Agent escalated to the appropriate team, specialist, or supervisor based on the issue type and routing rules. |
| **Routed to wrong team** | Agent escalated but sent the case to the wrong team or specialist. |
| **Should have escalated but did not** | The issue warranted escalation but the agent attempted to resolve it beyond their capability. |
| **No routing change needed** | The agent was the appropriate owner and no escalation was required. |

#### Q4: Were safety, recall, or compliance concerns addressed per policy?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | If the interaction involved safety concerns, product recalls, regulatory issues, or compliance-sensitive topics, check that the agent followed the required procedures (documentation, notifications, escalation to appropriate team). Answer "Yes" if no safety/compliance topics were involved or if they were handled correctly. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | No safety/compliance issues were involved, OR the agent handled them correctly per policy. |
| **No** | Safety, recall, or compliance concerns were present but the agent did not follow the required procedures. |

---

### Section 4: Resolution Effectiveness

| Field | Value |
|-------|-------|
| **Section name** | Resolution Effectiveness |
| **Description** | Evaluates the quality of the resolution provided, root cause identification, documentation completeness, and follow-up actions. |
| **Section weight (%)** | 20 |

#### Q1: How effectively was the customer's issue resolved?

| Field | Value |
|-------|-------|
| **Answer type** | Multiple choice |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Evaluate the final outcome of the interaction. "Fully resolved on first contact" means the customer's issue was completely addressed in a single interaction. "Resolved with follow-up" means the issue is resolved but required or scheduled additional actions. |

| Answer Option | Instructions |
|---------------|-------------|
| **Fully resolved on first contact** | Customer's issue was completely addressed in this interaction with no further action needed. |
| **Resolved with follow-up needed** | Issue is being addressed but requires scheduled follow-up (e.g., replacement shipment, engineering review, callback). |
| **Partially resolved** | Some aspects of the customer's issue were addressed but significant items remain open. |
| **Not resolved** | The customer's issue was not addressed or the agent was unable to provide a solution. |
| **Case still in progress** | The case is still actively being worked and resolution has not yet been attempted. |

#### Q2: Did the agent identify the root cause of the issue?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent documented the underlying cause of the customer's problem, not just the symptom. Root cause analysis helps prevent recurrence and builds the knowledge base. For non-technical inquiries (e.g., order status), answer "Yes" if the agent identified the reason for the inquiry. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent identified and documented the root cause or underlying reason for the customer's issue. |
| **No** | Agent resolved the symptom but did not identify or document the root cause. |

#### Q3: Was the case documentation thorough and complete?

| Field | Value |
|-------|-------|
| **Answer type** | Multiple choice |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Evaluate the completeness of case notes, resolution description, and any attached documentation. Good documentation should enable another agent to understand the issue, what was tried, and how it was resolved without needing to contact the customer again. |

| Answer Option | Instructions |
|---------------|-------------|
| **Comprehensive documentation** | Case notes include issue description, troubleshooting steps, root cause, resolution, and any follow-up details. Another agent could pick up this case without additional context. |
| **Adequate documentation** | Key information is present but some details are missing or could be more thorough. |
| **Incomplete documentation** | Significant gaps in case notes — missing resolution details, troubleshooting steps, or customer communication history. |
| **No documentation** | Agent did not document the interaction in case notes. |

#### Q4: Were follow-up actions clearly defined and assigned?

| Field | Value |
|-------|-------|
| **Answer type** | Choose from list |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | If the resolution requires follow-up (e.g., replacement shipment, engineering review, customer callback, RMA processing), check that the next steps are documented with clear ownership and timelines. |

| Answer Option | Instructions |
|---------------|-------------|
| **Follow-up documented and assigned** | Next steps are documented with clear ownership, timeline, and expected outcome. |
| **Follow-up needed but not documented** | Additional actions are required but the agent did not document them or assign ownership. |
| **No follow-up required** | The case was fully resolved and no follow-up actions are needed. |

---

### Section 5: Communication & Professionalism

| Field | Value |
|-------|-------|
| **Section name** | Communication & Professionalism |
| **Description** | Evaluates the clarity, professionalism, and customer-centricity of the agent's communication throughout the interaction. |
| **Section weight (%)** | 10 |

#### Q1: Was the agent's communication clear and professional?

| Field | Value |
|-------|-------|
| **Answer type** | Multiple choice |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Evaluate the overall quality of the agent's written or verbal communication. Consider grammar, tone, clarity of explanations, and appropriate use of technical language for the audience. |

| Answer Option | Instructions |
|---------------|-------------|
| **Excellent** | Communication was clear, professional, and polished. Technical concepts were explained appropriately for the audience. |
| **Good** | Professional communication with minor issues (e.g., small grammar errors, slightly unclear phrasing). |
| **Needs improvement** | Communication was unclear, overly technical for the audience, or lacked professionalism. |
| **Poor** | Communication quality was a significant issue — confusing, rude, or unprofessional. |

#### Q2: Did the agent demonstrate empathy and active listening?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent acknowledged the customer's frustration or concern, paraphrased the issue to confirm understanding, and showed genuine interest in helping. Look for phrases that demonstrate empathy such as "I understand your concern" or "Let me make sure I have this right". |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent demonstrated empathy, acknowledged the customer's situation, and confirmed understanding before proceeding. |
| **No** | Agent was transactional — no evidence of empathy, acknowledgment, or active listening. |

#### Q3: Did the agent summarize and set expectations before closing?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Before ending the interaction, the agent should summarize what was discussed, what actions were taken, and what the customer can expect next (including timelines). Check for evidence of a clear closing summary. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent summarized the interaction, confirmed the resolution or next steps, and set clear expectations. |
| **No** | Agent ended the interaction without summarizing or setting expectations. |

---

### Section 6: Tool Adoption & Efficiency

| Field | Value |
|-------|-------|
| **Section name** | Tool Adoption & Efficiency |
| **Description** | Evaluates the agent's use of available tools and AI capabilities to improve efficiency and service quality. |
| **Section weight (%)** | 10 |

#### Q1: Did the agent leverage Copilot or AI assistance?

| Field | Value |
|-------|-------|
| **Answer type** | Choose from list |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent used Copilot features such as case summarization, suggested knowledge articles, draft responses, or sentiment analysis. Evaluate whether the AI assistance improved the interaction quality or efficiency. |

| Answer Option | Instructions |
|---------------|-------------|
| **Used Copilot effectively** | Agent used Copilot for summaries, KB suggestions, or drafts, and the AI assistance visibly improved quality or speed. |
| **Used Copilot with limited benefit** | Agent engaged Copilot features but the output was not meaningfully incorporated into the interaction. |
| **Did not use available AI tools** | No evidence that the agent used Copilot or AI assistance when it would have been beneficial. |
| **Not applicable** | The interaction was too brief or simple to warrant AI tool usage. |

#### Q2: Did the agent use the knowledge base search effectively?

| Field | Value |
|-------|-------|
| **Answer type** | Yes/No |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Check if the agent searched the knowledge base for relevant articles before providing a response. Evidence includes KB article references in case notes, linked articles, or documented search attempts. |

| Answer | Instructions |
|--------|-------------|
| **Yes** | Agent searched the knowledge base and referenced or linked relevant articles. |
| **No** | No evidence that the agent consulted the knowledge base when it would have been appropriate. |

#### Q3: Was the overall interaction handled efficiently?

| Field | Value |
|-------|-------|
| **Answer type** | Multiple choice |
| **AI response enabled** | ✅ Yes |
| **Scoring enabled** | ✅ Yes |
| **Question instructions** | Consider the overall handling time relative to the issue complexity. An efficient interaction uses available tools, avoids unnecessary transfers, and reaches resolution without excessive back-and-forth. |

| Answer Option | Instructions |
|---------------|-------------|
| **Highly efficient** | Resolved quickly and appropriately using available tools. Minimal unnecessary steps. |
| **Acceptable efficiency** | Reasonable handling time for the complexity of the issue. |
| **Below average** | Unnecessary delays, rework, or excessive transfers. The interaction took longer than it should have. |
| **Unable to assess** | Insufficient data to evaluate efficiency (e.g., case still in progress). |

---

### Section Weight Summary

| # | Section | Weight | Questions |
|---|---------|--------|-----------|
| 1 | Customer Identification & Account Handling | 15% | 3 |
| 2 | Technical Accuracy & Product Knowledge | 25% | 4 |
| 3 | Process Compliance & Escalation Handling | 20% | 4 |
| 4 | Resolution Effectiveness | 20% | 4 |
| 5 | Communication & Professionalism | 10% | 3 |
| 6 | Tool Adoption & Efficiency | 10% | 3 |
| **Total** | | **100%** | **21** |

---

## Evaluation Plans

After publishing the criteria, create the following evaluation plans.

---

### Plan 1: Daily Case Quality Review

> **Purpose**: Automatically evaluate resolved cases daily using the Quality Evaluation Agent.

| Field | Value |
|-------|-------|
| **Plan name** | Daily Case Quality Review |
| **Description** | Evaluates all resolved cases on a daily cadence using AI agent scoring against the Manufacturing Service Quality Standard. |
| **Record type** | Cases |

**Frequency:**

| Field | Value |
|-------|-------|
| **Frequency type** | Recurring |
| **Occurrence** | Daily |
| **Start date** | *(today)* |
| **End date** | *(6 months from today)* |

**Conditions:**

| Condition | Operator | Value |
|-----------|----------|-------|
| Case Status | Equals | Resolved |

**Assign evaluation:**

| Field | Value |
|-------|-------|
| **Evaluation criteria** | Manufacturing Service Quality Standard |
| **Evaluation method** | AI agent |
| **Due date** | 3 days |

**Steps:**
1. Copilot Service workspace → **Evaluation plans** → **New**
2. Fill in the fields above
3. **Save** → **Activate plan**

---

### Plan 2: Conversation Quality Review

> **Purpose**: Automatically evaluate every closed conversation (live chat, voice) using the Quality Evaluation Agent.

| Field | Value |
|-------|-------|
| **Plan name** | Conversation Quality Review |
| **Description** | Evaluates closed conversations across all channels using AI agent scoring against the Manufacturing Service Quality Standard. |
| **Record type** | Conversations |

**Frequency:**

| Field | Value |
|-------|-------|
| **Frequency type** | Trigger |
| **Occurrence** | Closed conversation |
| **Start date** | *(today)* |
| **End date** | *(6 months from today)* |

**Conditions:**

| Condition | Operator | Value |
|-----------|----------|-------|
| Conversation status | Equals | Closed |
| Channel type | Contains data | *(any)* |

**Assign evaluation:**

| Field | Value |
|-------|-------|
| **Evaluation criteria** | Manufacturing Service Quality Standard |
| **Evaluation method** | AI agent |
| **Due date** | 3 days |

**Steps:**
1. Copilot Service workspace → **Evaluation plans** → **New**
2. Fill in the fields above
3. **Save** → **Activate plan**

---

## Post-Setup: Run a Simulation

After publishing the criteria, validate with a simulation before activating the plans:

1. Go to **Evaluation criteria** → select **Manufacturing Service Quality Standard**
2. Select **Create Simulation**
3. Set **Record Type** = Case (or Conversation)
4. Add **Conditions** (e.g., Case Status = Resolved)
5. **Save** → **Run Simulation**
6. Review the **Simulation Results** tab — the QEA agent evaluates the 25 most recent matching records
7. Review scoring accuracy and adjust question/answer instructions if needed
8. Re-publish criteria if changes were made

> **Note**: Each simulation run consumes Microsoft Copilot credits.

---

## How This Maps to Manufacturing Service Priorities

| Business Priority | Criteria Section | Key Questions |
|-------------------|------------------|---------------|
| **Tiered customer model** (80-20 analysis, ERP-driven) | Section 1: Customer Identification | Q2 (tier recognition), Q3 (entitlement check) |
| **Product knowledge & accuracy** (complex product lines) | Section 2: Technical Accuracy | Q1 (product knowledge), Q4 (part numbers/specs) |
| **Hot word escalation** (Urgent, Recall, Safety, Legal) | Section 3: Process Compliance | Q2 (hot word handling), Q4 (safety/recall) |
| **SLA compliance** (4-hr first response, 8-hr resolution) | Section 4: Resolution Effectiveness | Q1 (resolution quality), Q3 (documentation) |
| **Skills-based routing accuracy** | Section 3: Process Compliance | Q3 (correct team routing) |
| **AI tool adoption** (Copilot, KB) | Section 6: Tool Adoption | Q1 (Copilot usage), Q2 (KB search) |
| **Knowledge base improvement** (internal KB build-out) | Section 2: Technical Accuracy | Q2 (KB article reference) |
| **Replacing Salesforce** (native QM vs. SF + 3rd-party QA) | *Entire criteria* | Demonstrates native QM capability without add-on products |
| **New hire ramp-up** (reduce tribal knowledge dependency) | Section 4: Resolution Effectiveness | Q2 (root cause), Q3 (documentation completeness) |
| **Distributor/contractor relationships** | Section 5: Communication | Q1 (professionalism), Q2 (empathy), Q3 (expectations) |

---

## Demo Talk Track (for Section 4d in the demo script)

> "Let me show you what quality management looks like natively in the platform. We've built a **Manufacturing Service Quality Standard** — six sections, 21 questions, all weighted and scored by the Quality Evaluation Agent automatically. It covers the things that matter to your business: Is the agent verifying account tier? Are they catching hot words like 'recall' or 'safety' and escalating correctly? Are they using the knowledge base and Copilot? Is the documentation thorough enough for another agent to pick up the case?
>
> The system evaluates every resolved case daily and every closed conversation in real-time — no random sampling, no manual spreadsheets. And here's the kicker vs. Salesforce: this is all native. In Service Cloud, this would require Einstein AI plus a third-party quality assurance tool like Playvox or MaestroQA. Here, it's one platform, one data model, one set of criteria that the AI agent scores against automatically."

---

## Customization Notes for Other Customers

When reusing for a different manufacturing customer:

1. **Form-level instructions**: Update the hot word list and tier labels to match the customer's config in `environment.json`
2. **Section weights**: Adjust based on customer priorities (e.g., a customer focused on compliance might increase Section 3 to 25% and reduce Section 6 to 5%)
3. **Question instructions**: Swap in customer-specific terminology (e.g., product line names, escalation team names)
4. **Evaluation plan conditions**: Adjust based on the customer's active channels (e.g., remove conversation plan if no omnichannel)
5. **Everything else stays the same** — the 6 sections and 21 questions are designed to be universally applicable to discrete manufacturing service operations
