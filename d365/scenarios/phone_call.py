"""
Phone Call Scenario Module
==========================
Generates inbound phone call demo script with screen pop, customer context,
Copilot assistance, and call wrap-up.
"""

from typing import Dict, Any
from d365.scenarios import register_scenario


def _brand_str(config: Dict[str, Any]) -> str:
    """Get brand string from config."""
    demo = config.get("demo", {})
    brands = demo.get("brands", config.get("customer", {}).get("brands", ["Customer"]))
    return " / ".join(brands) if brands else "Customer"


def _get_agent_name(config: Dict[str, Any]) -> str:
    """Get agent persona name."""
    demo_story = config.get("demo_story", {})
    agent_persona = demo_story.get("agent_persona", {})
    return agent_persona.get("name", "Agent")


def _get_caller_info(config: Dict[str, Any], demo_data: Dict[str, Any] = None) -> Dict[str, str]:
    """Get hero caller information."""
    demo_reqs = config.get("demo_requirements", {})
    hero = demo_reqs.get("hero_scenario", {})
    
    return {
        "name": hero.get("customer_name", "Sarah Mitchell"),
        "phone": hero.get("customer_phone", "+1-555-0147"),
        "company": hero.get("customer_company", "Empire State Building"),
        "title": hero.get("customer_title", "Facilities Manager"),
        "issue": hero.get("case_title", "product issue")
    }


@register_scenario("phone_call", "phone-call-script.md")
def generate_phone_script(config: Dict[str, Any], customer_name: str) -> str:
    """Generate inbound phone call demo script."""
    brands = _brand_str(config)
    agent_name = _get_agent_name(config)
    caller = _get_caller_info(config)
    
    discovery = config.get("discovery", {})
    pain_points = discovery.get("pain_points", [])
    
    demo_reqs = config.get("demo_requirements", {})
    tiers = demo_reqs.get("tiers", [{"name": "Premium"}])
    top_tier = tiers[0].get("name", "Premium") if tiers else "Premium"
    
    # Build hot words section
    hot_words = demo_reqs.get("hot_words", ["urgent", "emergency", "safety"])
    hot_words_str = ", ".join(hot_words[:5])

    lines = [
        f"# {brands} — Inbound Phone Call Demo Script",
        "",
        f"> **Customer**: {customer_name}",
        f"> **Channel**: Phone (D365 Voice / Azure Communication Services)",
        f"> **Agent Persona**: {agent_name}",
        f"> **Hero Caller**: {caller['name']} ({caller['title']}, {caller['company']})",
        "",
        "---",
        "",
        "## Pre-Call Setup",
        "",
        "### Environment Checklist",
        "- [ ] Agent logged into Customer Service Workspace",
        "- [ ] Omnichannel presence set to **Available** (green)",
        "- [ ] Phone channel enabled in agent's capacity profile",
        "- [ ] Secondary phone ready for demo call",
        "- [ ] This script open on second monitor",
        "",
        "### D365 Verification",
        f"- [ ] Hero account ({caller['company']}) exists and shows as **{top_tier}** tier",
        f"- [ ] Hero contact ({caller['name']}) has phone number: `{caller['phone']}`",
        "- [ ] At least one open case visible on account timeline",
        "",
        "---",
        "",
        "## Call Flow",
        "",
        "### 1. 📞 Call Arrives — Screen Pop Hero Moment",
        "",
        f"*Your secondary phone calls the Voice Channel number. D365 shows incoming call.*",
        "",
        "**What to Show:**",
        "- Incoming call notification with caller ID",
        f"- **Screen Pop**: Customer recognized as {caller['name']} from {caller['company']}",
        f"- Tier indicator: **{top_tier}** prominently displayed",
        "- Open cases visible immediately",
        "- Recent interaction timeline",
        "",
        "💬 **Talk Track:**",
        f'> "{caller["name"]} calls in. Before I even answer, I can see everything — ',
        f'> their account, {caller["company"]}, is a {top_tier} customer. I see their open cases, ',
        '> recent interactions, and contact history. No asking for account numbers."',
        "",
        "**Voice Line (You as Agent):**",
        f'> "Thank you for calling {brands} support, this is {agent_name}. ',
        f'> I see you\'re calling from {caller["company"]}. How can I help you today?"',
        "",
        f"**Voice Line (Caller - {caller['name']}):**",
        f'> "Hi {agent_name}, we have a {caller["issue"]}. Can you help?"',
        "",
        "---",
        "",
        "### 2. 🔍 Customer Context Review",
        "",
        "**What to Show:**",
        "- Customer 360 pane with full account context",
        "- SLA entitlement and timer visibility",
        "- Recent orders/cases in timeline",
        "- Contact details and preferences",
        "",
        "💬 **Talk Track:**",
        f'> "Notice I didn\'t have to ask {caller["name"]} for any account information. ',
        '> The system recognized them instantly. I can see their service history, ',
        f'> their {top_tier} SLA coverage, and any open issues."',
        "",
        "**Key Value Points:**",
        "- ⏱️ Saved 30-45 seconds by not asking for account number",
        "- 📊 Complete context before saying hello",
        "- 🎯 Tier-based priority immediately visible",
        "",
        "---",
        "",
        "### 3. 🤖 Copilot Assistance",
        "",
        "**What to Show:**",
        "- Real-time transcription running",
        "- Copilot panel with suggested KB articles",
        "- Sentiment analysis indicator",
        "- Suggested next actions",
        "",
        "💬 **Talk Track:**",
        '> "As we talk, Copilot is listening and suggesting relevant knowledge articles. ',
        '> I can see a sentiment indicator — it helps me gauge how the conversation is going. ',
        '> The AI is augmenting my work, not replacing it."',
        "",
        "**Demonstrate:**",
        "1. Click Copilot panel to expand",
        '2. Show suggested KB article: "This article matches what they\'re describing"',
        "3. Point out real-time transcription",
        "",
        "---",
        "",
        "### 4. 📋 Case Creation / Update",
        "",
        "**What to Show:**",
        "- Create new case (or open existing)",
        "- Case form pre-populated with caller context",
        "- SLA timer starting automatically",
        "- Copilot draft response",
        "",
        "💬 **Talk Track:**",
        f'> "Let me create a case for this issue. Notice the case is already linked to ',
        f'> {caller["company"]}, and our {top_tier} SLA has automatically started. ',
        '> Copilot is drafting notes based on our conversation."',
        "",
        "---",
        "",
        "### 5. ✅ Resolution & Wrap-Up",
        "",
        "**Voice Line (You as Agent):**",
        '> "I\'ve logged this and our team will follow up within your SLA window. ',
        '> Is there anything else I can help with today?"',
        "",
        f"**Voice Line (Caller - {caller['name']}):**",
        '> "No, that was great. Thank you!"',
        "",
        "**What to Show:**",
        "- Agent clicks **Resolve Case** or schedules follow-up",
        "- Copilot auto-fills resolution notes from transcript",
        "- Case disposition captured",
        "- Post-call survey triggered (optional)",
        "",
        "---",
        "",
        "## Key Points to Emphasize",
        "",
    ]
    
    # Add pain point connections if available
    if pain_points:
        lines.append("### Pain Points Addressed:")
        for pain in pain_points[:4]:
            lines.append(f"- ✅ **{pain}** → Screen pop + Copilot solves this")
    
    lines.extend([
        "",
        "### Value Metrics:",
        "| Metric | Before | After |",
        "|--------|--------|-------|",
        "| Time to identify customer | 30-60 sec | **Instant** |",
        "| Context gathering | Manual lookup | **Pre-loaded** |",
        "| Note-taking | Manual typing | **AI-transcribed** |",
        "| KB search | Agent-driven | **AI-suggested** |",
        "",
        "### Hot Words Configured:",
        f"*These words trigger priority escalation: {hot_words_str}*",
        "",
    ])
    
    return "\n".join(lines)


# Demo section content for HTML guides
def get_phone_demo_section(config: Dict[str, Any], customer_name: str, 
                           hero_contact: Dict = None, hero_account: Dict = None) -> str:
    """Generate HTML content for phone scenario section in demo execution guide."""
    brands = _brand_str(config)
    agent_name = _get_agent_name(config)
    caller = _get_caller_info(config)
    
    contact_name = f"{hero_contact.get('firstName', caller['name'].split()[0])} {hero_contact.get('lastName', caller['name'].split()[-1] if ' ' in caller['name'] else '')}" if hero_contact else caller['name']
    account_name = hero_account.get("name", caller['company']) if hero_account else caller['company']
    tier = hero_account.get("tier", "Premium") if hero_account else "Premium"
    
    return f'''
    <div class="demo-gold">
        <strong>🌟 HERO MOMENT:</strong> The incoming call immediately shows complete customer context without any searching.
    </div>

    <div class="step-block">
        <span class="step-label prep">Prep</span>
        <div class="step-text">
            Ensure Voice Channel status is "Available". Have your secondary phone ready to call in.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"Now watch what happens when a call comes in..."</p>
        </div>
    </div>

    <div class="step-block voice-step">
        <span class="step-label click">Action</span>
        <div class="step-text">
            <strong>Trigger incoming call from secondary phone.</strong><br>
            Call the Voice Channel number. D365 will show the incoming call notification.
        </div>
    </div>

    <div class="voice-line">
        <span class="voice-label">{contact_name} (Caller)</span>
        "Hi, this is {contact_name.split()[0]} from {account_name}. I need help with an issue."
    </div>

    <div class="step-block">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Point out the <strong>screen pop</strong>:
            <ul style="margin-top:8px;">
                <li>Customer name and account automatically identified</li>
                <li>Tier level: <span class="tier-pill t1">{tier}</span></li>
                <li>Open cases visible immediately</li>
                <li>Recent interaction history</li>
                <li>Account details and contact information</li>
            </ul>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"Notice I didn't have to ask who's calling or search for anything. The system recognized {contact_name.split()[0]} instantly and pulled up their complete context. I can see they're a {tier} customer, their open cases, and recent interactions — all before I even say hello."</p>
        </div>
    </div>

    <div class="callout roi">
        <strong>Value Point:</strong> Agents save 30-45 seconds per call by eliminating "Can I have your account number?" Multiply by thousands of calls per day.
    </div>
    '''
