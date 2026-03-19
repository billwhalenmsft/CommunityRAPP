"""
Warranty Scenario Module
========================
Generates warranty lookup and claim demo script showing
warranty verification, claim processing, and service options.
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


def _get_warranty_terms(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get warranty terms from config."""
    return config.get("demo", {}).get("warranty", {
        "standard_years": 2,
        "extended_years": 5,
        "labor_coverage": True,
        "parts_coverage": True
    })


@register_scenario("warranty", "warranty-script.md")
def generate_warranty_script(config: Dict[str, Any], customer_name: str) -> str:
    """Generate warranty lookup and claim demo script."""
    brands = _brand_str(config)
    agent_name = _get_agent_name(config)
    warranty = _get_warranty_terms(config)
    
    lines = [
        f"# {brands} — Warranty Lookup & Claims Demo Script",
        "",
        f"> **Customer**: {customer_name}",
        "> **Scenario**: Warranty Verification and Claim Processing",
        f"> **Agent Persona**: {agent_name}",
        "",
        "---",
        "",
        "## Scenario Overview",
        "",
        '**Customer Request**: "I have a product that stopped working. Is it still under warranty?"',
        "",
        "**What to Demonstrate:**",
        "- Instant warranty lookup by serial number",
        "- Coverage verification (parts, labor, dates)",
        "- Claim initiation workflow",
        "- Service options (repair, replace, on-site)",
        "",
        "---",
        "",
        "## Pre-Demo Setup",
        "",
        "### Ensure You Have:",
        "- [ ] Sample product with warranty registration",
        "- [ ] Warranty lookup custom page available",
        "- [ ] Coverage details populated (start/end dates)",
        "- [ ] Service option picklist configured",
        "",
        "---",
        "",
        "## Act 1: Warranty Inquiry",
        "",
        '**Customer**: "I bought a unit about a year ago and it just stopped working. Do I need to pay for repairs?"',
        "",
        f"**{agent_name}**: \"Let me look up your warranty status. Do you have the serial number?\"",
        "",
        '**Customer**: "It\'s SN-ABC-123456."',
        "",
        "**Action**: Open the **Warranty Lookup** tool and search by serial number.",
        "",
        "💬 **Talk Track:**",
        '> "I can check warranty status instantly using the serial number. ',
        '> Let me look that up for you..."',
        "",
        "---",
        "",
        "## Act 2: Warranty Status Display",
        "",
        "**What to Show (Warranty Details Panel):**",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| Serial Number | SN-ABC-123456 |",
        "| Product | Industrial Widget Pro |",
        "| Purchase Date | [13 months ago] |",
        f"| Standard Warranty | {warranty.get('standard_years', 2)} Years |",
        f"| Extended Warranty | {warranty.get('extended_years', 'N/A')} |",
        "| Coverage End Date | [11 months from now] |",
        "| **Status** | ✅ **ACTIVE** |",
        "",
        "**Coverage Details:**",
        "",
        f"| Parts | {'✅ Covered' if warranty.get('parts_coverage', True) else '❌ Not Covered'} |",
        f"| Labor | {'✅ Covered' if warranty.get('labor_coverage', True) else '❌ Not Covered'} |",
        "| On-Site Service | ✅ Available |",
        "| Shipping (In/Out) | ✅ Prepaid |",
        "",
        "💬 **Talk Track:**",
        '> "Great news — your product is still under the original warranty for another ',
        '> 11 months. Parts and labor are both covered. Let me help you get this resolved."',
        "",
        "---",
        "",
        "## Act 3: Service Options",
        "",
        f"**{agent_name}**: \"Since you're covered, here are your options...\"",
        "",
        "**Service Options Panel:**",
        "",
        "| Option | Description | Estimated Time |",
        "|--------|-------------|----------------|",
        "| **Depot Repair** | Ship to service center | 7-10 business days |",
        "| **On-Site Service** | Technician visits you | 2-3 business days |",
        "| **Advance Exchange** | We ship replacement first | 1-2 business days |",
        "",
        "💬 **Talk Track:**",
        '> "You can ship it to us for repair, we can send a technician to you, ',
        '> or since this is a common issue, I can send a replacement unit today ',
        '> and you ship the defective one back."',
        "",
        "---",
        "",
        "## Act 4: Claim Initiation (Hero Moment)",
        "",
        '**Customer**: "The advance exchange sounds great. Let\'s do that."',
        "",
        "**Action**: Initiate warranty claim with advance exchange option.",
        "",
        "**What to Show (Claim Form):**",
        "1. Defect type selection (dropdown)",
        "2. Symptom description (free text)",
        "3. Service option: Advance Exchange",
        "4. Shipping address confirmation",
        "5. **Submit Claim** button",
        "",
        "**Automatic Actions on Submit:**",
        "- ✅ Warranty Claim # Generated: WC-2024-007891",
        "- ✅ Replacement Order Created",
        "- ✅ Return Shipping Label Generated",
        "- ✅ Customer Email with Tracking Info",
        "- ✅ Hold Placed on Customer Account (released on return receipt)",
        "",
        "💬 **Talk Track:**",
        '> "Done — I\'ve initiated the advance exchange. Your replacement ships today. ',
        '> You\'ll get an email with the tracking number and a return label for the ',
        '> defective unit. Just drop it off at any UPS location within 10 days."',
        "",
        "---",
        "",
        "## Act 5: Warranty Expiration Scenario (Alternative)",
        "",
        "**What if warranty is expired?**",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| Coverage End Date | [6 months ago] |",
        "| **Status** | ❌ **EXPIRED** |",
        "",
        "**Options to Present:**",
        "",
        "1. **Out-of-Warranty Repair**: $175 flat rate",
        "2. **Extended Warranty Purchase**: $99/year (covers future issues)",
        "3. **Trade-In / Upgrade**: 15% discount on new model",
        "",
        "💬 **Talk Track (Expired):**",
        '> "I see the warranty expired 6 months ago, but let me check our options. ',
        '> We have a flat-rate repair at $175. Or, since your model is a few years old, ',
        '> you might consider upgrading — I can offer 15% off the new model."',
        "",
        "---",
        "",
        "## Key Points to Emphasize",
        "",
        "### Without This Integration:",
        "| Old Way | New Way |",
        "|---------|---------|",
        '| "Let me check with our warranty department..." | Instant lookup by serial |',
        '| Customer waits on hold for verification | Coverage displayed in seconds |',
        '| Manual claim form (fax, email, portal) | One-click claim initiation |',
        '| Separate call to schedule service | Service options shown immediately |',
        "",
        "### Business Value:",
        "- **Warranty inquiries**: Resolved in < 5 minutes",
        "- **Advance exchange**: Higher NPS vs. depot repair",
        "- **Upsell opportunity**: Extended warranty, upgrades for expired units",
        "- **Reduced fraud**: Serial validation with purchase history",
        "",
    ]
    
    return "\n".join(lines)


def get_warranty_demo_section(config: Dict[str, Any], customer_name: str,
                              hero_contact: Dict = None, hero_account: Dict = None) -> str:
    """Generate HTML section for warranty demo in execution guide."""
    warranty = _get_warranty_terms(config)
    
    return f'''
    <div class="step-block warranty-step">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Open the <strong>Warranty Lookup</strong> tool. Search by serial number.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"Let me check your warranty status. I just need the serial number... 
            Great, I can see your product is still under the {warranty.get('standard_years', 2)}-year warranty."</p>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Display warranty details:
            <ul>
                <li>Coverage dates (start/end)</li>
                <li>Parts coverage: ✅ Covered</li>
                <li>Labor coverage: ✅ Covered</li>
                <li>Warranty status: <strong>ACTIVE</strong></li>
            </ul>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Display service options: Depot Repair, On-Site Service, Advance Exchange.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label do">Do</span>
        <div class="step-text">
            <strong>Hero Moment:</strong> Initiate a warranty claim with Advance Exchange. 
            Show automatic generation of replacement order and return label.
        </div>
    </div>

    <div class="callout success">
        <strong>Key Value:</strong> Warranty verification and claim in one call. 
        No transfers, no callbacks, no manual forms.
    </div>
    '''
