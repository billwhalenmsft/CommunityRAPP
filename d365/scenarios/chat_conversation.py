"""
Chat Conversation Scenario Module
=================================
Generates chat/digital messaging demo script with bot greeting,
self-service attempt, and escalation to live agent.
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


def _get_chatter_info(config: Dict[str, Any]) -> Dict[str, str]:
    """Get chat customer info from story characters."""
    demo_story = config.get("demo_story", {})
    characters = demo_story.get("characters", [])
    
    # Find chat character
    for char in characters:
        if char.get("channel") == "chat":
            return {
                "name": char.get("name", "Rachel Chen"),
                "account": char.get("account", "Metro Supply"),
                "scenario": char.get("scenario", "order inquiry")
            }
    
    # Default
    return {
        "name": "Rachel Chen",
        "account": "Metro Supply",
        "scenario": "order inquiry"
    }


@register_scenario("chat_conversation", "chat-demo-script.md")
def generate_chat_script(config: Dict[str, Any], customer_name: str) -> str:
    """Generate chat/bot escalation demo script."""
    brands = _brand_str(config)
    agent_name = _get_agent_name(config)
    chatter = _get_chatter_info(config)
    
    lines = [
        f"# {brands} — Chat / Digital Messaging Demo Script",
        "",
        f"> **Customer**: {customer_name}",
        "> **Channel**: Web Chat (Portal → Copilot Studio → Live Agent)",
        f"> **Agent Persona**: {agent_name}",
        f"> **Chat Customer**: {chatter['name']} ({chatter['account']})",
        "",
        "---",
        "",
        "## Scenario Overview",
        "",
        "**Story**: Customer visits the self-service portal, starts a chat with the bot, ",
        "and escalates to a live agent when they need help with a complex request.",
        "",
        "**Key Demo Points:**",
        "- Seamless bot → human handoff",
        "- Full conversation context transfers to agent",
        "- No customer repetition",
        "- Guided actions for complex workflows",
        "",
        "---",
        "",
        "## Pre-Chat Setup",
        "",
        "### Environment Checklist",
        "- [ ] Portal open in a browser tab (incognito for clean experience)",
        "- [ ] Agent logged into Customer Service Workspace",
        "- [ ] Chat channel presence set to **Available**",
        "- [ ] Chat capacity configured for agent",
        "",
        "---",
        "",
        "## Act 1: Customer Visits Portal",
        "",
        "**Action**: Open the customer self-service portal in browser.",
        "",
        "💬 **Talk Track:**",
        f'> "Let me show you the customer\'s perspective. A {chatter["account"]} employee ',
        f'> visits the {brands} support portal to get help."',
        "",
        "**What to Show:**",
        "- Portal home page with knowledge base",
        "- Chat widget in bottom-right corner",
        '- "Chat with us" button or bubble',
        "",
        "---",
        "",
        "## Act 2: Bot Greeting & Self-Service Attempt",
        "",
        "**Action**: Click the chat widget to start a conversation.",
        "",
        f"**Bot**: \"Hello! Welcome to {brands} support. I'm your virtual assistant. How can I help you today?\"",
        "",
        f"**{chatter['name']}**: \"I need help with my recent order.\"",
        "",
        "**Bot**: \"I'd be happy to help with your order. Can you provide your order number?\"",
        "",
        f"**{chatter['name']}**: \"It's ORD-78421.\"",
        "",
        "**Bot**: \"I found your order. Here's the status:",
        "- Order #ORD-78421",
        "- Status: In Transit",
        "- Expected Delivery: Tomorrow by 5 PM",
        "",
        "Is there something specific you need help with?\"",
        "",
        "💬 **Talk Track:**",
        '> "The bot can handle simple queries like order status lookup. It\'s connected ',
        '> to our backend systems and can retrieve real-time information. Many customers ',
        '> get their answers here without needing a live agent."',
        "",
        "---",
        "",
        "## Act 3: Escalation to Live Agent",
        "",
        f"**{chatter['name']}**: \"Actually, I need to speak with someone about modifying this order. One of the items isn't right.\"",
        "",
        "**Bot**: \"I understand you need help modifying your order. Let me connect you with a support specialist who can assist with that.\"",
        "",
        "*Bot transfers to live agent queue with full conversation context.*",
        "",
        "💬 **Talk Track:**",
        '> "The customer needs help beyond what the bot can do. Watch how the handoff works."',
        "",
        "---",
        "",
        "## Act 4: Agent Receives Chat",
        "",
        "**Switch to Agent View**",
        "",
        "**What to Show (Agent Workspace):**",
        "- Chat notification arrives with context preview",
        "- Bot conversation transcript visible immediately",
        "- Customer identified and account loaded",
        "- Order details already shown",
        "",
        "💬 **Talk Track:**",
        '> "As the agent, I receive the chat with full context. I can see everything the ',
        f'> customer discussed with the bot — the order number, what they\'re trying to do. ',
        f'> {chatter["name"]} doesn\'t have to repeat anything."',
        "",
        "**Agent Response:**",
        f'> "Hi {chatter["name"].split()[0]}, I can see you need help modifying order ORD-78421. ',
        '> I have the details right here. Let me pull up the order modification tool."',
        "",
        "---",
        "",
        "## Act 5: Resolution with Guided Actions",
        "",
        "**What to Show:**",
        "- Agent opens the Order Management custom page from side pane",
        "- Order details displayed with editable line items",
        "- Modification workflow with validation",
        "- Real-time updates visible to customer",
        "",
        "💬 **Talk Track:**",
        '> "I have guided actions built right into my workspace. This Order Management tool ',
        '> lets me quickly view and modify orders without leaving the conversation. ',
        '> Everything is connected."',
        "",
        "**Agent**: \"I've updated the quantity on line 3. You should see the new order total reflected. Anything else?\"",
        "",
        f"**{chatter['name']}**: \"That's perfect, thank you!\"",
        "",
        "---",
        "",
        "## Key Points to Emphasize",
        "",
        "### Bot → Human Handoff",
        "| Before (Manual) | After (D365 Omnichannel) |",
        "|-----------------|--------------------------|",
        "| Customer repeats everything | Full context transfers automatically |",
        "| Agent asks for order # again | Order already loaded in agent view |",
        "| 2-3 minute context gathering | **Instant context** |",
        "",
        "### What Makes This Different:",
        "- **Conversational AI** handles routine queries (order status, hours, FAQs)",
        "- **Seamless escalation** when complexity requires human expertise",
        "- **Guided actions** (custom pages) embedded in agent workspace",
        "- **Unified history** — this chat appears in customer timeline alongside calls and emails",
        "",
    ]
    
    return "\n".join(lines)


def get_chat_demo_section(config: Dict[str, Any], customer_name: str,
                          hero_contact: Dict = None, hero_account: Dict = None) -> str:
    """Generate HTML content for chat scenario section in demo execution guide."""
    brands = _brand_str(config)
    chatter = _get_chatter_info(config)
    
    contact_name = chatter['name']
    account_name = hero_account.get("name", chatter['account']) if hero_account else chatter['account']
    
    return f'''
    <div class="step-block chat-step">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Open the Portal in a browser tab. Start a chat conversation as a customer.
        </div>
    </div>

    <div class="chat-line">
        <span class="chat-label">{contact_name} (Customer Chat)</span>
        "Hi, I need help with a recent order."
    </div>

    <div class="step-block">
        <span class="step-label show">Show</span>
        <div class="step-text">
            <ul>
                <li>Chat bot initial greeting and triage</li>
                <li>Bot retrieves order status</li>
                <li>Escalation to live agent</li>
                <li>Context transfer (no repeat information)</li>
            </ul>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"Notice how the chat transferred to me with full context. {contact_name.split()[0]} didn't have to repeat anything. I can see they're from {account_name} and what they've already discussed with the bot."</p>
        </div>
    </div>

    <div class="callout success">
        <strong>Key Value:</strong> No customer repetition. Bot conversation history transfers seamlessly to the agent.
    </div>
    '''
