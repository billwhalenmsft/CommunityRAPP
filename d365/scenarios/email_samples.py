"""
Email Samples Scenario Module
=============================
Generates sample email templates for email-to-case demos,
showing how emails auto-create cases with sentiment analysis.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from d365.scenarios import register_scenario


def _brand_str(config: Dict[str, Any]) -> str:
    """Get brand string from config."""
    demo = config.get("demo", {})
    brands = demo.get("brands", config.get("customer", {}).get("brands", ["Customer"]))
    return " / ".join(brands) if brands else "Customer"


def _get_support_email(config: Dict[str, Any]) -> str:
    """Get support email from config."""
    return config.get("demo", {}).get("support_email", "support@company.com")


def _get_email_characters(config: Dict[str, Any]) -> List[Dict]:
    """Get email-related characters from story."""
    demo_story = config.get("demo_story", {})
    characters = demo_story.get("characters", [])
    
    email_chars = [c for c in characters if c.get("channel") == "email"]
    
    if not email_chars:
        # Default email charcters
        return [
            {
                "name": "Patricia Hayes",
                "email": "p.hayes@facilitygroup.com",
                "account": "Facility Management Group",
                "scenario": "product quality complaint",
                "sentiment": "angry"
            },
            {
                "name": "David Park",
                "email": "dpark@metroplex.com",
                "account": "Metroplex Industries",
                "scenario": "standard inquiry",
                "sentiment": "neutral"
            }
        ]
    return email_chars


def _get_hot_words(config: Dict[str, Any]) -> List[str]:
    """Get hot words for sentiment flagging."""
    demo = config.get("demo", {})
    return demo.get("hot_words", [
        "escalate",
        "attorney",
        "lawyer",
        "lawsuit",
        "cancel",
        "terminating",
        "unacceptable",
        "disappointed",
        "furious"
    ])


@register_scenario("email_samples", "email-samples.md")
def generate_email_samples(config: Dict[str, Any], customer_name: str) -> str:
    """Generate sample emails for email-to-case demos."""
    brands = _brand_str(config)
    support_email = _get_support_email(config)
    hot_words = _get_hot_words(config)
    email_chars = _get_email_characters(config)
    
    # Find urgent and standard emails
    urgent_char = next((c for c in email_chars if c.get("sentiment") == "angry"), None)
    standard_char = next((c for c in email_chars if c.get("sentiment") != "angry"), None)
    
    if not urgent_char:
        urgent_char = {
            "name": "Patricia Hayes",
            "email": "p.hayes@facilitygroup.com",
            "account": "Facility Management Group"
        }
    
    if not standard_char:
        standard_char = {
            "name": "David Park",
            "email": "dpark@metroplex.com",
            "account": "Metroplex Industries"
        }
    
    lines = [
        f"# {brands} — Email Demo Samples",
        "",
        f"> **Customer**: {customer_name}",
        "> **Channel**: Email → Case Auto-Creation",
        f"> **Support Inbox**: {support_email}",
        "",
        "---",
        "",
        "## How Email-to-Case Works",
        "",
        "1. Customer sends email to support inbox",
        "2. D365 automatically creates a case",
        "3. AI analyzes sentiment and extracts key info",
        "4. Case routes to appropriate queue based on content",
        "5. Hot words trigger priority escalation",
        "",
        "---",
        "",
        "## Email 1: Standard Inquiry",
        "",
        "### Email Details",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| From | {standard_char['name']} <{standard_char.get('email', 'email@example.com')}> |",
        f"| To | {support_email} |",
        f"| Subject | Question about product specifications |",
        f"| Account | {standard_char.get('account', 'Example Corp')} |",
        "",
        "### Email Body",
        "",
        "```",
        "Hello,",
        "",
        "I'm looking at your product catalog and have a question about the specifications",
        "for model XYZ-500. The datasheet mentions it supports up to 1000 PSI, but I need",
        "to verify this will work for our industrial application.",
        "",
        "Can you also confirm lead time for orders of 50+ units?",
        "",
        "Thanks,",
        f"{standard_char['name']}",
        f"{standard_char.get('account', 'Example Corp')}",
        "```",
        "",
        "### Expected Behavior",
        "- Case created with **Normal Priority**",
        "- Sentiment: **Neutral**",
        "- Category: Product Inquiry",
        "- Routes to: Standard Queue",
        "",
        "---",
        "",
        "## Email 2: URGENT / High-Sentiment",
        "",
        "### Email Details",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| From | {urgent_char['name']} <{urgent_char.get('email', 'p.hayes@facilitygroup.com')}> |",
        f"| To | {support_email} |",
        f"| Subject | URGENT - Product Failure / Possible Safety Issue |",
        f"| Account | {urgent_char.get('account', 'Facility Management Group')} |",
        "",
        "### Email Body (with Hot Words)",
        "",
        "```",
        "To whom it may concern,",
        "",
        "This is UNACCEPTABLE. We installed your equipment last month and it has already",
        "failed during a critical operation. Our team had to shut down the entire line.",
        "",
        "I am FURIOUS about this. We've been a loyal customer for 15 years and this is",
        "how we're treated? If we don't get a resolution immediately, I will be speaking",
        "with our ATTORNEY about damages.",
        "",
        "I need a callback TODAY.",
        "",
        f"{urgent_char['name']}",
        f"Operations Director",
        f"{urgent_char.get('account', 'Facility Management Group')}",
        "```",
        "",
        "### Expected Behavior",
        "- Case created with **HIGH Priority**",
        "- Sentiment: **Negative** (flagged)",
        "- Hot words detected: UNACCEPTABLE, FURIOUS, ATTORNEY",
        "- Routes to: Escalation Queue",
        "- Supervisor notification triggered",
        "",
        "---",
        "",
        "## Email 3: RMA / Return Request",
        "",
        "### Email Details",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| From | Shipping Coordinator <receiving@{standard_char.get('account', 'Example Corp').replace(' ', '').lower()}.com> |",
        f"| To | {support_email} |",
        f"| Subject | Request for Return Authorization - PO #98765 |",
        f"| Account | {standard_char.get('account', 'Example Corp')} |",
        "",
        "### Email Body",
        "",
        "```",
        "Hello Support Team,",
        "",
        "We received our shipment today (PO #98765) but unfortunately one of the items",
        "arrived damaged in transit. The packaging was crushed and the unit is dented.",
        "",
        "Please provide an RMA number so we can return this item for replacement.",
        "",
        "Photos attached.",
        "",
        "Thank you,",
        "Receiving Department",
        f"{standard_char.get('account', 'Example Corp')}",
        "```",
        "",
        "### Expected Behavior",
        "- Case created with **Normal Priority**",
        "- Case Type: **Return/RMA**",
        "- Sentiment: **Neutral** (factual tone)",
        "- Routes to: RMA Queue",
        "- Related PO extracted: #98765",
        "",
        "---",
        "",
        "## Hot Words List",
        "",
        "These words trigger priority escalation:",
        "",
    ]
    
    # Add hot words as bullet list
    for word in hot_words:
        lines.append(f"- {word}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Demo Talk Track",
        "",
        "💬 **For Standard Email:**",
        '> "Here\'s a typical product inquiry email. Watch how D365 automatically creates ',
        "> a case, extracts the key information, and routes it to the right queue based on content.\"",
        "",
        "💬 **For Urgent Email:**",
        "> \"Now let's look at an urgent email with strong language. Watch how the system ",
        "> detects the negative sentiment and hot words like 'attorney' and 'unacceptable'. ",
        "> This immediately escalates to a priority queue and alerts a supervisor.\"",
        "",
        "💬 **Key Point:**",
        '> "AI analyzes every incoming email for sentiment and keywords, ensuring urgent ',
        "> issues get immediate attention while routine queries follow standard workflow.\"",
        "",
    ])
    
    return "\n".join(lines)


def get_email_demo_section(config: Dict[str, Any], customer_name: str,
                           hero_contact: Dict = None, hero_account: Dict = None) -> str:
    """Generate HTML section for email demo in execution guide."""
    hot_words = _get_hot_words(config)
    hot_words_html = ", ".join([f'<code>{w}</code>' for w in hot_words[:5]])
    
    return f'''
    <div class="step-block email-step">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Open an email case in the agent workspace. Show how the email was auto-converted to a case.
        </div>
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"When customers send emails to our support inbox, D365 automatically creates a case. 
            The AI analyzes the message for sentiment and key words."</p>
        </div>
    </div>

    <div class="step-block">
        <span class="step-label show">Show</span>
        <div class="step-text">
            Point out:
            <ul>
                <li>Email attached to case</li>
                <li>Sentiment indicator (Negative/Neutral/Positive)</li>
                <li>Extracted information (PO numbers, product references)</li>
                <li>Case category auto-assigned</li>
            </ul>
        </div>
    </div>

    <div class="callout warning">
        <strong>Hot Words:</strong> {hot_words_html} — These trigger priority escalation and supervisor alerts.
    </div>

    <div class="step-block">
        <span class="step-label say">Say</span>
        <div class="talk-track">
            <p>"Notice the priority was automatically set to High because the email contained words like 
            'attorney' and 'unacceptable'. A supervisor was notified immediately."</p>
        </div>
    </div>
    '''
