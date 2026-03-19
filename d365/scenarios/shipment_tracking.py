"""
Shipment Tracking Scenario Module
=================================
Generates "Where's My Order?" demo script showing shipment
tracking integration and proactive notifications.
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


@register_scenario("shipment_tracking", "shipment-tracking-script.md")
def generate_shipment_script(config: Dict[str, Any], customer_name: str) -> str:
    """Generate shipment tracking demo script."""
    brands = _brand_str(config)
    agent_name = _get_agent_name(config)
    
    lines = [
        f"# {brands} — Shipment Tracking Demo Script",
        "",
        f"> **Customer**: {customer_name}",
        "> **Scenario**: \"Where's My Order?\" — Shipment Status Inquiry",
        f"> **Agent Persona**: {agent_name}",
        "",
        "---",
        "",
        "## Scenario Overview",
        "",
        '**Customer Request**: "I haven\'t received my shipment yet. Where is it?"',
        "",
        "**What to Demonstrate:**",
        "- Real-time shipment tracking from case",
        "- Carrier integration (FedEx, UPS, etc.)",
        "- Proactive delay notifications",
        "- Exception handling for late/damaged shipments",
        "",
        "---",
        "",
        "## Pre-Demo Setup",
        "",
        "### Ensure You Have:",
        "- [ ] Sample shipment with tracking number",
        "- [ ] Carrier tracking URL configured",
        "- [ ] Timeline showing shipment events",
        "",
        "---",
        "",
        "## Act 1: Customer Inquiry",
        "",
        '**Customer**: "Hi, I placed an order last week and the shipping notification said it would arrive two days ago. It still hasn\'t shown up."',
        "",
        f"**{agent_name}**: \"I'm sorry about that. Let me look up your shipment right away.\"",
        "",
        "**Action**: Access the shipment tracking from the Order Management page or case timeline.",
        "",
        "💬 **Talk Track:**",
        '> "I have shipment tracking integrated right here. Let me pull up the status..."',
        "",
        "---",
        "",
        "## Act 2: Shipment Status Display",
        "",
        "**What to Show (Tracking Panel):**",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| Tracking Number | 1Z999AA10123456784 |",
        "| Carrier | UPS |",
        "| Ship Date | [5 days ago] |",
        "| Estimated Delivery | [2 days ago] |",
        "| Current Status | **Delayed - Weather Exception** |",
        "| Last Location | Chicago Distribution Hub |",
        "",
        "**Tracking Events Timeline:**",
        "```",
        "📍 [Today] 8:42 AM - Chicago Hub - Delayed due to weather",
        "📍 [Yesterday] 3:15 PM - Chicago Hub - Arrived at facility",
        "📍 [3 days ago] 9:00 AM - Origin - Shipped",
        "```",
        "",
        "💬 **Talk Track:**",
        '> "I can see your package is at the Chicago distribution center. There\'s been a ',
        '> weather delay — looks like snowstorms in the Midwest. The carrier shows an updated ',
        '> delivery estimate of [tomorrow]."',
        "",
        "---",
        "",
        "## Act 3: Offer Resolution Options",
        "",
        f"**{agent_name}**: \"I see the delay is beyond the carrier's control, but I want to make this right. I have a few options for you...\"",
        "",
        "**Options to Present:**",
        "",
        "1. **Expedite at No Charge**: Upgrade to overnight once weather clears",
        "2. **Partial Credit**: Shipping refund for the delay",
        "3. **Replacement Ship**: Send new order from alternate warehouse",
        "",
        "💬 **Talk Track:**",
        '> "I\'m authorized to offer expedited shipping at no extra cost once the weather ',
        '> clears, or I can apply a credit to your account. Which would you prefer?"',
        "",
        "---",
        "",
        "## Act 4: Proactive Notifications (Hero Moment)",
        "",
        "**What to Show:**",
        "- Automated shipment delay notification setup",
        "- Customer communication preferences",
        "- Proactive SMS/Email when status changes",
        "",
        "💬 **Talk Track:**",
        '> "I\'m also setting up a proactive notification so you\'ll get an automatic text ',
        '> and email the moment the package is out for delivery. You won\'t have to call back."',
        "",
        "---",
        "",
        "## Key Points to Emphasize",
        "",
        "### Without This Integration:",
        "| Old Way | New Way |",
        "|---------|---------|",
        '| "You\'ll need to check the carrier website" | Tracking visible in case view |',
        '| Customer calls back: "Still nothing" | Agent sees delay proactively |',
        '| Manual lookup in carrier portal | Automatic status updates |',
        '| No proactive communication | SMS/Email when status changes |',
        "",
        "### Business Impact:",
        "- **\"Where\'s my order?\" calls**: #1 volume driver — reduce by 40%",
        "- **Proactive notifications**: Customers informed before they call",
        "- **Carrier integration**: Real-time data, not yesterday's snapshot",
        "",
    ]
    
    return "\n".join(lines)


def get_shipment_demo_section(config: Dict[str, Any], customer_name: str,
                              hero_contact: Dict = None, hero_account: Dict = None) -> str:
    """Generate HTML section for shipment tracking in execution guide."""
    
    return '''
    <div class="step-block shipment-step">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Open shipment tracking for the order. Show tracking number, carrier, and status timeline.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"I can see the shipment is delayed due to weather. I can track every stop 
            from origin to current location without leaving this screen."</p>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label do">Do</span>
        <div class="step-text">
            Show the resolution options available to the agent:
            <ul>
                <li>Expedite shipment</li>
                <li>Credit/refund shipping</li>
                <li>Ship replacement from alternate warehouse</li>
            </ul>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label show">Show</span>
        <div class="step-text">
            <strong>Hero Moment:</strong> Set up proactive notification so customer 
            gets SMS when package ships.
        </div>
    </div>

    <div class="callout success">
        <strong>Key Value:</strong> "Where's my order?" is the #1 call driver. 
        Real-time tracking + proactive notifications reduce these calls by 40%.
    </div>
    '''
