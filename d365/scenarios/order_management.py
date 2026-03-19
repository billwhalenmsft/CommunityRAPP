"""
Order Management Scenario Module
================================
Generates order lookup and modification demo script.
Shows the custom page/guided action for order management.
"""

from typing import Dict, Any, List
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


def _get_erp_system(config: Dict[str, Any]) -> str:
    """Get ERP system name."""
    return config.get("demo", {}).get("erp_system", "ERP")


@register_scenario("order_management", "order-management-script.md")
def generate_order_script(config: Dict[str, Any], customer_name: str) -> str:
    """Generate order management demo script."""
    brands = _brand_str(config)
    agent_name = _get_agent_name(config)
    erp_system = _get_erp_system(config)
    
    lines = [
        f"# {brands} — Order Management Demo Script",
        "",
        f"> **Customer**: {customer_name}",
        "> **Scenario**: Order Lookup, Modification, and Status Update",
        f"> **Agent Persona**: {agent_name}",
        f"> **Connected System**: {erp_system}",
        "",
        "---",
        "",
        "## Scenario Overview",
        "",
        '**Customer Request**: "I need to check on my order and possibly make a change."',
        "",
        "**What to Demonstrate:**",
        "- Real-time order lookup from within the case",
        "- Order details without system switching",
        "- Modification capability (quantity, address, line items)",
        "- Audit trail of changes",
        "",
        "---",
        "",
        "## Pre-Demo Setup",
        "",
        "### Ensure You Have:",
        "- [ ] Sample order visible in Order Management custom page",
        f"- [ ] {erp_system} integration active (or mock data)",
        "- [ ] Customer record with related orders",
        "",
        "---",
        "",
        "## Act 1: Customer Asks About Order",
        "",
        '**Customer**: "Hi, I need to check on order number ORD-78421. Can you tell me what the status is?"',
        "",
        "**Action**: From the case form, open the **Order Management** custom page.",
        "",
        "💬 **Talk Track:**",
        '> "Let me look that up for you. I have our Order Management tool right here ',
        f'> in my workspace — it\'s connected to our {erp_system} in real-time."',
        "",
        "---",
        "",
        "## Act 2: Show Order Details",
        "",
        "**What to Show (Order Management Page):**",
        "",
        "| Order Header | Value |",
        "|--------------|-------|",
        "| Order Number | ORD-78421 |",
        "| Order Date | [Recent date] |",
        "| Status | In Production / Shipped |",
        "| Requested Delivery | [Future date] |",
        "| Ship-To Address | Customer address |",
        "",
        "**Line Items Section:**",
        "",
        "| Line | Product | Qty | Unit Price | Status |",
        "|------|---------|-----|------------|--------|",
        "| 1 | Widget A | 10 | $125.00 | Shipped |",
        "| 2 | Component B | 25 | $45.00 | In Production |",
        "| 3 | Accessory C | 5 | $22.00 | Open |",
        "",
        "💬 **Talk Track:**",
        '> "I can see your complete order right here. Line 1 has already shipped, ',
        '> Line 2 is in production, and Line 3 is still open. Is there something ',
        '> specific you\'d like to change?"',
        "",
        "---",
        "",
        "## Act 3: Order Modification",
        "",
        '**Customer**: "Actually, can we increase the quantity on Line 3 from 5 to 10?"',
        "",
        '**Agent**: "Let me check if that\'s available..."',
        "",
        "**Action:**",
        "1. Click **Modify** on Line 3",
        "2. Update quantity from 5 to 10",
        "3. Show real-time availability check",
        "4. Click **Save Changes**",
        "",
        "💬 **Talk Track:**",
        '> "I\'m updating the quantity now. The system is checking inventory availability ',
        f'> in real-time against our {erp_system}... Good news, we have stock. The order ',
        '> total has been updated. You\'ll receive a confirmation email shortly."',
        "",
        "---",
        "",
        "## Act 4: Audit Trail",
        "",
        "**What to Show:**",
        "- Order history/timeline showing the change",
        "- Who made the change and when",
        "- Previous value → New value",
        "",
        "💬 **Talk Track:**",
        '> "Every change is tracked with a full audit trail. I can see exactly when ',
        '> modifications were made, by whom, and what the original values were. This ',
        '> helps with compliance and dispute resolution."',
        "",
        "---",
        "",
        "## Key Points to Emphasize",
        "",
        "### Without This Tool:",
        "| Old Way | New Way |",
        "|---------|---------|",
        f'| "Let me log into {erp_system}..." | Order visible in case view |',
        "| 3+ minute context switch | Instant lookup |",
        "| Manual change → email confirmation | Integrated modification + auto email |",
        "| No audit trail in CRM | Full history in timeline |",
        "",
        "### Business Value:",
        "- **60% faster** order inquiries",
        "- **Zero system switching** for common tasks",
        "- **Complete audit trail** for compliance",
        "- **Real-time data** via API integration",
        "",
    ]
    
    return "\n".join(lines)


def get_order_demo_section(config: Dict[str, Any], customer_name: str,
                           hero_contact: Dict = None, hero_account: Dict = None) -> str:
    """Generate HTML section for order management in execution guide."""
    erp_system = _get_erp_system(config)
    
    return f'''
    <div class="step-block order-step">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Open the <strong>Order Management</strong> custom page from the side pane.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label do">Do</span>
        <div class="step-text">
            Search for an order (ORD-78421). Show order header and line items.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"I can look up any order right from here — it's connected to our {erp_system} 
            in real-time. I don't have to switch systems or ask the customer to wait."</p>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label do">Do</span>
        <div class="step-text">
            <strong>Hero Moment:</strong> Modify a line item quantity. Show the change being saved.
        </div>
    </div>

    <div class="callout success">
        <strong>Key Value:</strong> Real-time order lookup and modification without leaving the case. 
        Changes sync back to {erp_system} automatically.
    </div>
    '''
