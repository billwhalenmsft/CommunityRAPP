"""
D365 Demo Data Generator
========================
Uses GPT-4o to generate realistic, contextual demo data for Dynamics 365 Customer Service.

This utility generates:
- Service accounts (manufacturers, distributors, end-users)
- Contacts with realistic names, titles, phone numbers
- Demo cases with industry-specific scenarios
- Knowledge base articles with relevant content
- Products with SKUs and pricing

All data is tailored to the customer's industry, region, and use case.
"""

import json
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Azure OpenAI imports
try:
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Industry-specific templates for data generation
INDUSTRY_TEMPLATES = {
    "elevator_service": {
        "account_types": ["Building Management", "Property Developer", "Facilities Company", "Hospital", "Shopping Center", "Office Complex"],
        "job_titles": ["Facilities Manager", "Building Superintendent", "Property Manager", "Maintenance Director", "Operations Manager"],
        "case_prefixes": ["Elevator", "Escalator", "Lift", "Unit"],
        "product_categories": ["Passenger Elevators", "Freight Elevators", "Escalators", "Moving Walkways", "Service Contracts"],
        "kb_topics": ["Safety Procedures", "Maintenance Schedules", "Emergency Protocols", "Modernization Options", "Service Level Agreements"]
    },
    "plumbing_manufacturing": {
        "account_types": ["Plumbing Distributor", "Contractor", "Wholesale Supply", "Commercial Builder", "Municipal Water Authority"],
        "job_titles": ["Purchasing Manager", "Operations Director", "Branch Manager", "Procurement Specialist", "Technical Sales Rep"],
        "case_prefixes": ["Order", "Product", "Shipment", "Technical", "Warranty"],
        "product_categories": ["Flush Valves", "Faucets", "Drainage Products", "Hydration Stations", "Commercial Sinks"],
        "kb_topics": ["Installation Guides", "Product Specifications", "Warranty Policies", "Order Processing", "Returns & Exchanges"]
    },
    "hvac": {
        "account_types": ["HVAC Contractor", "Building Services", "Property Management", "Industrial Facility", "Healthcare Campus"],
        "job_titles": ["HVAC Technician", "Maintenance Supervisor", "Energy Manager", "Facilities Director", "Service Coordinator"],
        "case_prefixes": ["Unit", "System", "Installation", "Maintenance", "Emergency"],
        "product_categories": ["Air Handlers", "Chillers", "Boilers", "Thermostats", "Ductwork"],
        "kb_topics": ["Maintenance Best Practices", "Energy Efficiency", "Refrigerant Handling", "System Diagnostics", "Warranty Coverage"]
    },
    "medical_devices": {
        "account_types": ["Hospital", "Clinic", "Medical Center", "Research Lab", "Outpatient Facility"],
        "job_titles": ["Biomedical Engineer", "Clinical Director", "Procurement Manager", "Department Head", "Equipment Coordinator"],
        "case_prefixes": ["Device", "Equipment", "Calibration", "Service", "Compliance"],
        "product_categories": ["Diagnostic Equipment", "Patient Monitors", "Surgical Instruments", "Imaging Systems", "Lab Equipment"],
        "kb_topics": ["Calibration Procedures", "Regulatory Compliance", "Preventive Maintenance", "Troubleshooting Guides", "Training Materials"]
    },
    "telecommunications": {
        "account_types": ["Enterprise Client", "SMB Customer", "Government Agency", "Educational Institution", "Healthcare Provider"],
        "job_titles": ["IT Director", "Network Administrator", "Telecom Manager", "CTO", "Infrastructure Lead"],
        "case_prefixes": ["Network", "Service", "Billing", "Equipment", "Outage"],
        "product_categories": ["Business Lines", "Internet Services", "Cloud Solutions", "Security Services", "Unified Communications"],
        "kb_topics": ["Network Configuration", "Troubleshooting Guides", "Billing Policies", "Service Upgrades", "Security Best Practices"]
    },
    "other": {
        "account_types": ["Corporate Client", "SMB Customer", "Enterprise Account", "Partner Organization", "Vendor"],
        "job_titles": ["Account Manager", "Operations Director", "Procurement Lead", "Business Analyst", "Customer Success Manager"],
        "case_prefixes": ["Service", "Support", "Order", "Technical", "General"],
        "product_categories": ["Standard Products", "Premium Services", "Support Plans", "Add-ons", "Accessories"],
        "kb_topics": ["Getting Started", "FAQs", "Policies", "Best Practices", "Troubleshooting"]
    }
}

# Regional phone number formats
PHONE_FORMATS = {
    "NA": {"format": "+1-{area}-{prefix}-{line}", "area_codes": ["212", "310", "312", "415", "617", "713", "404", "206", "303", "602"]},
    "EMEA": {"format": "+44-{area}-{number}", "area_codes": ["20", "121", "161", "131", "141", "113", "151", "115", "117", "118"]},
    "APAC": {"format": "+61-{area}-{number}", "area_codes": ["2", "3", "7", "8"]},
    "LATAM": {"format": "+52-{area}-{number}", "area_codes": ["55", "33", "81", "664"]},
    "Global": {"format": "+1-555-{prefix}-{line}", "area_codes": ["555"]}
}

# Name pools by region
NAMES = {
    "NA": {
        "first": ["James", "Sarah", "Michael", "Jennifer", "David", "Emily", "Robert", "Jessica", "William", "Ashley", "John", "Amanda", "Richard", "Stephanie", "Thomas", "Nicole"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson"]
    },
    "EMEA": {
        "first": ["Oliver", "Charlotte", "George", "Sophie", "Harry", "Emma", "Jack", "Isabella", "William", "Mia", "James", "Amelia", "Thomas", "Olivia", "Alexander", "Grace"],
        "last": ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Roberts", "Johnson", "Walker", "Wright", "Thompson", "White", "Hughes"]
    },
    "APAC": {
        "first": ["Wei", "Yuki", "Raj", "Mei", "Akira", "Priya", "Chen", "Sakura", "Amit", "Lin", "Kenji", "Ananya", "Jun", "Aiko", "Sanjay", "Hana"],
        "last": ["Wang", "Tanaka", "Patel", "Kim", "Suzuki", "Singh", "Li", "Yamamoto", "Sharma", "Zhang", "Sato", "Kumar", "Chen", "Watanabe", "Gupta", "Park"]
    },
    "LATAM": {
        "first": ["Carlos", "Maria", "Juan", "Ana", "Luis", "Sofia", "Miguel", "Isabella", "Jose", "Valentina", "Diego", "Camila", "Alejandro", "Laura", "Fernando", "Gabriela"],
        "last": ["Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Hernandez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes", "Cruz"]
    },
    "Global": {
        "first": ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Quinn", "Avery", "Parker", "Cameron", "Drew", "Reese", "Skyler", "Dakota", "Sage"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Martin", "Lee", "Clark"]
    }
}


class D365DataGenerator:
    """Generates realistic demo data for D365 Customer Service using GPT-4o."""

    def __init__(self):
        """Initialize with Azure OpenAI if available."""
        self.client = None
        self.deployment_name = None

        if OPENAI_AVAILABLE:
            try:
                endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

                if endpoint:
                    # Try token-based auth first
                    try:
                        credential = DefaultAzureCredential()
                        token_provider = get_bearer_token_provider(
                            credential,
                            "https://cognitiveservices.azure.com/.default"
                        )
                        self.client = AzureOpenAI(
                            azure_endpoint=endpoint,
                            azure_ad_token_provider=token_provider,
                            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
                        )
                    except Exception:
                        # Fall back to API key
                        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
                        if api_key:
                            self.client = AzureOpenAI(
                                azure_endpoint=endpoint,
                                api_key=api_key,
                                api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
                            )

                    self.deployment_name = deployment
                    logger.info(f"D365DataGenerator initialized with Azure OpenAI: {deployment}")
            except Exception as e:
                logger.warning(f"Could not initialize Azure OpenAI: {e}")

    def generate_full_demo_data(
        self,
        customer_name: str,
        industry: str,
        brands: List[str],
        region: str = "NA",
        tiers: List[str] = None,
        case_types: List[str] = None,
        hero_scenario: Dict[str, Any] = None,
        hot_words: List[str] = None,
        account_count: Dict[str, int] = None,
        case_count: int = 20,
        kb_article_count: int = 10,
        channels: List[str] = None,
        pain_points: List[str] = None
    ) -> Dict[str, Any]:
        """Generate complete demo data set."""

        # Defaults
        tiers = tiers or ["Premium", "Standard", "Basic"]
        case_types = case_types or ["support", "inquiry", "complaint"]
        hot_words = hot_words or ["urgent", "emergency", "safety"]
        account_count = account_count or {"manufacturers": 1, "distributors": 5, "end_users": 10}
        channels = channels or ["phone"]

        # Get industry template
        template = INDUSTRY_TEMPLATES.get(industry, INDUSTRY_TEMPLATES["other"])

        # Generate all data
        accounts = self._generate_accounts(customer_name, brands, region, template, account_count, tiers)
        contacts = self._generate_contacts(accounts, region, template)
        cases = self._generate_cases(accounts, contacts, template, case_types, tiers, hot_words, case_count, hero_scenario, channels)
        kb_articles = self._generate_kb_articles(industry, brands, template, kb_article_count, pain_points)
        products = self._generate_products(brands, template)

        return {
            "serviceAccounts": {"accounts": accounts},
            "contacts": {"contacts": contacts},
            "demoCases": {"cases": cases},
            "kbArticles": {"articles": kb_articles},
            "products": {"products": products},
            "activities": self.generate_timeline_activities(
                contacts=contacts,
                accounts=accounts,
                cases=cases,
                days_back=90,
                agent_name=hero_scenario.get("agent_name", "Demo Agent") if hero_scenario else "Demo Agent"
            ),
            "_generated": True,
            "_generatedAt": datetime.now().isoformat(),
            "_generator": "D365DataGenerator",
            "_config": {
                "customer": customer_name,
                "industry": industry,
                "brands": brands,
                "region": region,
                "tiers": tiers
            }
        }

    def _generate_accounts(
        self,
        customer_name: str,
        brands: List[str],
        region: str,
        template: Dict,
        account_count: Dict[str, int],
        tiers: List[str]
    ) -> List[Dict]:
        """Generate service accounts."""
        accounts = []
        account_number = 1000

        # Manufacturer accounts (one per brand)
        for brand in brands[:account_count.get("manufacturers", 1)]:
            accounts.append({
                "name": f"{brand} Corporate",
                "accountNumber": f"MFG-{account_number}",
                "type": "Manufacturer",
                "tier": "Platinum" if "Platinum" in tiers else tiers[0],
                "address": self._generate_address(region),
                "phone": self._generate_phone(region),
                "industry": template.get("account_types", ["Corporate"])[0]
            })
            account_number += 1

        # Distributor accounts
        distributor_names = [
            f"{brands[0]} National Supply",
            f"{brands[0]} Regional Distribution",
            f"Metro {brands[0]} Partners",
            f"Allied {brands[0]} Wholesale",
            f"Premier {brands[0]} Group"
        ]
        for i in range(min(account_count.get("distributors", 5), len(distributor_names))):
            tier_idx = i % len(tiers)
            accounts.append({
                "name": distributor_names[i],
                "accountNumber": f"DIST-{account_number}",
                "type": "Distributor",
                "tier": tiers[tier_idx],
                "address": self._generate_address(region),
                "phone": self._generate_phone(region),
                "industry": "Distribution"
            })
            account_number += 1

        # End-user accounts
        for i in range(account_count.get("end_users", 10)):
            account_type = random.choice(template.get("account_types", ["Customer"]))
            tier_idx = i % len(tiers)
            city = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"])
            accounts.append({
                "name": f"{city} {account_type}",
                "accountNumber": f"CUST-{account_number}",
                "type": "End User",
                "tier": tiers[tier_idx],
                "address": self._generate_address(region),
                "phone": self._generate_phone(region),
                "industry": account_type
            })
            account_number += 1

        return accounts

    def _generate_contacts(
        self,
        accounts: List[Dict],
        region: str,
        template: Dict
    ) -> List[Dict]:
        """Generate contacts linked to accounts."""
        contacts = []
        names = NAMES.get(region, NAMES["NA"])
        titles = template.get("job_titles", ["Manager"])

        for account in accounts:
            # 1-2 contacts per account
            num_contacts = random.randint(1, 2)
            for _ in range(num_contacts):
                first = random.choice(names["first"])
                last = random.choice(names["last"])
                title = random.choice(titles)

                contacts.append({
                    "firstName": first,
                    "lastName": last,
                    "title": title,
                    "account": account["name"],
                    "email": f"{first.lower()}.{last.lower()}@{account['name'].lower().replace(' ', '')}.com",
                    "phone": self._generate_phone(region),
                    "mobile": self._generate_phone(region)
                })

        return contacts

    def _generate_cases(
        self,
        accounts: List[Dict],
        contacts: List[Dict],
        template: Dict,
        case_types: List[str],
        tiers: List[str],
        hot_words: List[str],
        case_count: int,
        hero_scenario: Optional[Dict],
        channels: List[str]
    ) -> List[Dict]:
        """Generate demo cases."""
        cases = []
        prefixes = template.get("case_prefixes", ["Service"])
        priorities = {"High": 1, "Normal": 2, "Low": 3}

        # Hero case first if specified
        if hero_scenario:
            hero_contact = next((c for c in contacts if hero_scenario.get("customer_name") in f"{c['firstName']} {c['lastName']}"), contacts[0] if contacts else None)
            cases.append({
                "title": hero_scenario.get("case_title", "Priority Support Request"),
                "description": hero_scenario.get("description", "Hero demo scenario"),
                "account": hero_contact["account"] if hero_contact else accounts[0]["name"],
                "contact": f"{hero_contact['firstName']} {hero_contact['lastName']}" if hero_contact else "",
                "priority": "High",
                "status": "Active",
                "channel": channels[0] if channels else "phone",
                "isHeroCase": True,
                "demoUse": "Main demo scenario - show full customer context"
            })

        # Generate remaining cases
        for i in range(case_count - (1 if hero_scenario else 0)):
            account = random.choice(accounts)
            account_contacts = [c for c in contacts if c["account"] == account["name"]]
            contact = random.choice(account_contacts) if account_contacts else None

            prefix = random.choice(prefixes)
            case_type = random.choice(case_types)
            priority = random.choice(list(priorities.keys()))
            channel = random.choice(channels)

            # Occasionally include hot words
            description = f"{prefix} {case_type} request"
            if random.random() < 0.2 and hot_words:
                hot_word = random.choice(hot_words)
                description = f"URGENT: {description} - {hot_word} situation"
                priority = "High"

            cases.append({
                "title": f"{prefix} {case_type.title()} - {account['name'][:30]}",
                "description": description,
                "account": account["name"],
                "contact": f"{contact['firstName']} {contact['lastName']}" if contact else "",
                "priority": priority,
                "status": random.choice(["Active", "Active", "Active", "On Hold", "Waiting"]),
                "channel": channel,
                "tier": account.get("tier", tiers[0]),
                "demoUse": f"Show {case_type} handling for {account.get('tier', 'standard')} tier"
            })

        return cases

    def _generate_kb_articles(
        self,
        industry: str,
        brands: List[str],
        template: Dict,
        kb_article_count: int,
        pain_points: Optional[List[str]]
    ) -> List[Dict]:
        """Generate knowledge base articles."""
        articles = []
        topics = template.get("kb_topics", ["General Information"])
        brand = brands[0] if brands else "Product"

        # If we have Azure OpenAI, generate richer content
        if self.client and self.deployment_name:
            try:
                prompt = f"""Generate {kb_article_count} knowledge base article titles and brief summaries for a {industry} company called {brand}.
                Topics should cover: {', '.join(topics)}
                {f"Address these customer pain points: {', '.join(pain_points)}" if pain_points else ""}

                Return as JSON array with objects containing: title, summary, category, keywords (array)
                Example: [{{"title": "...", "summary": "...", "category": "...", "keywords": ["...", "..."]}}]"""

                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": "You are a technical writer creating knowledge base articles. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )

                content = response.choices[0].message.content
                # Parse JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                generated = json.loads(content)
                for item in generated[:kb_article_count]:
                    articles.append({
                        "title": item.get("title", f"{brand} Knowledge Article"),
                        "summary": item.get("summary", ""),
                        "category": item.get("category", topics[0]),
                        "keywords": item.get("keywords", []),
                        "status": "Published"
                    })
                return articles
            except Exception as e:
                logger.warning(f"GPT-4o KB generation failed, using templates: {e}")

        # Fallback: template-based generation
        for i, topic in enumerate(topics[:kb_article_count]):
            articles.append({
                "title": f"{brand} {topic}",
                "summary": f"Information about {topic.lower()} for {brand} products and services.",
                "category": topic,
                "keywords": [brand.lower(), topic.lower().replace(" ", "-")],
                "status": "Published"
            })

        return articles

    def _generate_products(
        self,
        brands: List[str],
        template: Dict
    ) -> List[Dict]:
        """Generate product catalog."""
        products = []
        categories = template.get("product_categories", ["Standard Product"])
        sku_counter = 1000

        for brand in brands:
            for category in categories:
                products.append({
                    "name": f"{brand} {category}",
                    "sku": f"{brand[:3].upper()}-{sku_counter}",
                    "category": category,
                    "brand": brand,
                    "price": round(random.uniform(50, 5000), 2),
                    "description": f"Premium {category.lower()} from {brand}"
                })
                sku_counter += 1

        return products

    def _generate_phone(self, region: str) -> str:
        """Generate a phone number for the region."""
        fmt = PHONE_FORMATS.get(region, PHONE_FORMATS["NA"])
        area = random.choice(fmt["area_codes"])

        if region == "NA":
            return fmt["format"].format(
                area=area,
                prefix=str(random.randint(200, 999)),
                line=str(random.randint(1000, 9999))
            )
        elif region == "EMEA":
            return fmt["format"].format(
                area=area,
                number=str(random.randint(10000000, 99999999))
            )
        else:
            return f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

    def _generate_address(self, region: str) -> Dict[str, str]:
        """Generate an address for the region."""
        if region == "NA":
            cities = [
                ("New York", "NY", "10001"),
                ("Los Angeles", "CA", "90001"),
                ("Chicago", "IL", "60601"),
                ("Houston", "TX", "77001"),
                ("Phoenix", "AZ", "85001")
            ]
            city, state, zip_code = random.choice(cities)
            return {
                "line1": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['Street', 'Avenue', 'Boulevard', 'Drive'])}",
                "city": city,
                "state": state,
                "postalCode": zip_code,
                "country": "USA"
            }
        elif region == "EMEA":
            cities = [
                ("London", "SW1A 1AA"),
                ("Manchester", "M1 1AA"),
                ("Birmingham", "B1 1AA"),
                ("Edinburgh", "EH1 1AA"),
                ("Dublin", "D01 F5P2")
            ]
            city, postal = random.choice(cities)
            return {
                "line1": f"{random.randint(1, 200)} {random.choice(['High', 'King', 'Queen', 'Church', 'Market'])} Street",
                "city": city,
                "postalCode": postal,
                "country": "United Kingdom"
            }
        else:
            return {
                "line1": f"{random.randint(100, 9999)} Business Park Drive",
                "city": "Metro City",
                "postalCode": "12345",
                "country": "Country"
            }

    # ============================================
    # ACTIVITY / TIMELINE DATA GENERATION
    # ============================================

    def generate_timeline_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        days_back: int = 90,
        agent_name: str = "Demo Agent",
        activity_counts: Dict[str, int] = None
    ) -> Dict[str, List[Dict]]:
        """
        Generate a rich timeline of activities for demo purposes.

        This creates realistic activity history including:
        - Inbound/outbound emails
        - Agent notes
        - Phone call logs
        - Tasks (follow-ups, escalations)
        - Appointments (site visits, callbacks)
        - Social posts (internal notes)

        Args:
            contacts: List of contact records
            accounts: List of account records
            cases: List of case records
            days_back: How many days of history to generate
            agent_name: Name of the demo agent
            activity_counts: Dict specifying count per activity type

        Returns:
            Dict with keys: emails, notes, phone_calls, tasks, appointments, posts
        """
        counts = activity_counts or {
            "emails": 15,
            "notes": 10,
            "phone_calls": 8,
            "tasks": 6,
            "appointments": 3,
            "posts": 5
        }

        activities = {
            "emails": self._generate_email_activities(contacts, accounts, cases, counts.get("emails", 15), days_back, agent_name),
            "notes": self._generate_note_activities(contacts, accounts, cases, counts.get("notes", 10), days_back, agent_name),
            "phoneCalls": self._generate_phone_call_activities(contacts, accounts, cases, counts.get("phone_calls", 8), days_back, agent_name),
            "tasks": self._generate_task_activities(contacts, accounts, cases, counts.get("tasks", 6), days_back, agent_name),
            "appointments": self._generate_appointment_activities(contacts, accounts, cases, counts.get("appointments", 3), days_back, agent_name),
            "posts": self._generate_post_activities(contacts, accounts, cases, counts.get("posts", 5), days_back, agent_name),
            "_meta": {
                "generatedAt": datetime.now().isoformat(),
                "daysBack": days_back,
                "totalActivities": sum(counts.values())
            }
        }

        return activities

    def _generate_email_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        count: int,
        days_back: int,
        agent_name: str
    ) -> List[Dict]:
        """Generate email activity records."""
        emails = []
        now = datetime.now()

        email_subjects_inbound = [
            "Question about my order",
            "Follow-up on our conversation",
            "Urgent: Need immediate assistance",
            "RE: Service request update",
            "Order status inquiry",
            "Product specification question",
            "Warranty coverage question",
            "Invoice discrepancy",
            "Return request",
            "Thank you for your help!"
        ]

        email_subjects_outbound = [
            "RE: Question about your order",
            "Your service request update",
            "Order confirmation and next steps",
            "Following up on your inquiry",
            "Resolution summary",
            "Requested documentation attached",
            "Schedule confirmation",
            "Credit memo details",
            "Return label and instructions",
            "Thank you for your business"
        ]

        for i in range(count):
            contact = random.choice(contacts) if contacts else None
            case = random.choice(cases) if cases else None
            account_name = contact["account"] if contact else (accounts[0]["name"] if accounts else "Demo Account")

            is_inbound = random.choice([True, True, False])  # 2/3 inbound
            days_ago = random.randint(1, days_back)
            activity_date = now - timedelta(days=days_ago, hours=random.randint(8, 17), minutes=random.randint(0, 59))

            if is_inbound:
                sender = f"{contact['firstName']} {contact['lastName']}" if contact else "Customer"
                sender_email = contact.get("email", "customer@example.com") if contact else "customer@example.com"
                recipient = agent_name
                recipient_email = f"{agent_name.lower().replace(' ', '.')}@company.com"
                subject = random.choice(email_subjects_inbound)
                direction = "Incoming"
            else:
                sender = agent_name
                sender_email = f"{agent_name.lower().replace(' ', '.')}@company.com"
                recipient = f"{contact['firstName']} {contact['lastName']}" if contact else "Customer"
                recipient_email = contact.get("email", "customer@example.com") if contact else "customer@example.com"
                subject = random.choice(email_subjects_outbound)
                direction = "Outgoing"

            emails.append({
                "subject": subject,
                "from": sender,
                "fromEmail": sender_email,
                "to": recipient,
                "toEmail": recipient_email,
                "direction": direction,
                "dateTime": activity_date.isoformat(),
                "regarding": case["title"] if case else f"General inquiry - {account_name}",
                "account": account_name,
                "contact": f"{contact['firstName']} {contact['lastName']}" if contact else None,
                "body": self._generate_email_body(subject, sender, recipient, is_inbound),
                "status": "Completed",
                "demoNote": f"{'Inbound' if is_inbound else 'Outbound'} email - {days_ago} days ago"
            })

        # Sort by date (newest first)
        emails.sort(key=lambda x: x["dateTime"], reverse=True)
        return emails

    def _generate_email_body(self, subject: str, sender: str, recipient: str, is_inbound: bool) -> str:
        """Generate realistic email body content."""
        if is_inbound:
            bodies = [
                f"Hi,\n\nI wanted to follow up on {subject.lower()}. Can you please provide an update?\n\nThanks,\n{sender}",
                f"Hello,\n\nI need some assistance. {subject}.\n\nPlease let me know what the next steps are.\n\nBest regards,\n{sender}",
                f"Good afternoon,\n\nI'm reaching out regarding {subject.lower()}. This is becoming urgent for our operations.\n\nPlease advise.\n\n{sender}",
                f"Hi team,\n\n{subject}. We'd appreciate a quick response.\n\nThank you,\n{sender}"
            ]
        else:
            bodies = [
                f"Hi {recipient.split()[0]},\n\nThank you for reaching out. I'm happy to help with {subject.lower()}.\n\nI've reviewed your account and here's what I found...\n\nPlease let me know if you have any questions.\n\nBest regards,\n{sender}",
                f"Hello {recipient.split()[0]},\n\nThank you for your patience. Regarding {subject.lower()}, I've completed the requested action.\n\nYou should see the update reflected within 24 hours.\n\nBest,\n{sender}",
                f"Hi,\n\nI wanted to follow up on our conversation. As discussed, I've processed {subject.lower()}.\n\nAttached is the documentation for your records.\n\nThanks,\n{sender}"
            ]
        return random.choice(bodies)

    def _generate_note_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        count: int,
        days_back: int,
        agent_name: str
    ) -> List[Dict]:
        """Generate note/annotation activity records."""
        notes = []
        now = datetime.now()

        note_subjects = [
            "Call summary",
            "Customer escalation details",
            "Follow-up required",
            "Resolution notes",
            "Account review notes",
            "Technical troubleshooting steps",
            "Credit approval notes",
            "Manager consultation",
            "Customer sentiment update",
            "SLA exception documentation"
        ]

        note_bodies = [
            "Spoke with customer. They confirmed the issue has been resolved. Closing case.",
            "Customer escalated due to repeated delays. Offered expedited shipping at no charge. They accepted.",
            "Technical issue requires engineering review. Escalating to Tier 2 support.",
            "Credit request submitted for $250.00. Manager approved. Processing today.",
            "Customer mentioned they're evaluating competitors. Flagging for account management follow-up.",
            "Performed remote diagnostics. Issue isolated to configuration setting. Provided instructions.",
            "Customer extremely satisfied with resolution. Potential reference account.",
            "Multi-department coordination required. Scheduling call with logistics and sales.",
            "Warranty verified. Replacement unit authorized under standard coverage.",
            "SLA breach imminent. Prioritizing for immediate resolution."
        ]

        for i in range(count):
            contact = random.choice(contacts) if contacts else None
            case = random.choice(cases) if cases else None
            account_name = contact["account"] if contact else (accounts[0]["name"] if accounts else "Demo Account")

            days_ago = random.randint(1, days_back)
            activity_date = now - timedelta(days=days_ago, hours=random.randint(8, 17), minutes=random.randint(0, 59))

            notes.append({
                "subject": random.choice(note_subjects),
                "noteText": random.choice(note_bodies),
                "createdBy": agent_name,
                "dateTime": activity_date.isoformat(),
                "regarding": case["title"] if case else f"Account: {account_name}",
                "account": account_name,
                "contact": f"{contact['firstName']} {contact['lastName']}" if contact else None,
                "isDocument": False,
                "demoNote": f"Agent note - {days_ago} days ago"
            })

        notes.sort(key=lambda x: x["dateTime"], reverse=True)
        return notes

    def _generate_phone_call_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        count: int,
        days_back: int,
        agent_name: str
    ) -> List[Dict]:
        """Generate phone call activity records."""
        calls = []
        now = datetime.now()

        call_subjects = [
            "Initial support call",
            "Follow-up call",
            "Escalation callback",
            "Order status update",
            "Technical support call",
            "Billing inquiry",
            "Service scheduling call",
            "Customer satisfaction follow-up"
        ]

        for i in range(count):
            contact = random.choice(contacts) if contacts else None
            case = random.choice(cases) if cases else None
            account_name = contact["account"] if contact else (accounts[0]["name"] if accounts else "Demo Account")

            is_inbound = random.choice([True, True, False])  # 2/3 inbound
            days_ago = random.randint(1, days_back)
            activity_date = now - timedelta(days=days_ago, hours=random.randint(8, 17), minutes=random.randint(0, 59))
            duration_minutes = random.randint(3, 25)

            calls.append({
                "subject": random.choice(call_subjects),
                "direction": "Incoming" if is_inbound else "Outgoing",
                "from": contact.get("phone", "555-0100") if contact and is_inbound else agent_name,
                "to": agent_name if is_inbound else (contact.get("phone", "555-0100") if contact else "555-0100"),
                "dateTime": activity_date.isoformat(),
                "duration": duration_minutes,
                "durationDisplay": f"{duration_minutes} minutes",
                "regarding": case["title"] if case else f"Account: {account_name}",
                "account": account_name,
                "contact": f"{contact['firstName']} {contact['lastName']}" if contact else None,
                "outcome": random.choice(["Resolved", "Follow-up required", "Escalated", "Information provided", "Voicemail left"]),
                "description": f"{'Received' if is_inbound else 'Made'} call regarding customer inquiry. Duration: {duration_minutes} min.",
                "status": "Completed",
                "demoNote": f"{'Inbound' if is_inbound else 'Outbound'} call - {days_ago} days ago"
            })

        calls.sort(key=lambda x: x["dateTime"], reverse=True)
        return calls

    def _generate_task_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        count: int,
        days_back: int,
        agent_name: str
    ) -> List[Dict]:
        """Generate task activity records."""
        tasks = []
        now = datetime.now()

        task_subjects = [
            "Follow up with customer",
            "Process credit request",
            "Schedule site visit",
            "Review warranty claim",
            "Coordinate with logistics",
            "Update customer records",
            "Prepare quote",
            "Escalation review"
        ]

        for i in range(count):
            contact = random.choice(contacts) if contacts else None
            case = random.choice(cases) if cases else None
            account_name = contact["account"] if contact else (accounts[0]["name"] if accounts else "Demo Account")

            days_ago = random.randint(1, days_back)
            due_in_days = random.randint(-5, 10)  # Some overdue, some future
            created_date = now - timedelta(days=days_ago)
            due_date = now + timedelta(days=due_in_days)

            status = "Open" if due_in_days > 0 else random.choice(["Completed", "Open", "Cancelled"])
            priority = random.choice(["High", "Normal", "Low"])

            tasks.append({
                "subject": random.choice(task_subjects),
                "owner": agent_name,
                "createdOn": created_date.isoformat(),
                "dueDate": due_date.date().isoformat(),
                "regarding": case["title"] if case else f"Account: {account_name}",
                "account": account_name,
                "contact": f"{contact['firstName']} {contact['lastName']}" if contact else None,
                "priority": priority,
                "status": status,
                "percentComplete": 100 if status == "Completed" else random.randint(0, 75),
                "description": f"Task assigned from customer interaction. Priority: {priority}",
                "demoNote": f"Task - Due {'in ' + str(due_in_days) + ' days' if due_in_days > 0 else str(abs(due_in_days)) + ' days overdue' if due_in_days < 0 else 'today'}"
            })

        tasks.sort(key=lambda x: x["dueDate"])
        return tasks

    def _generate_appointment_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        count: int,
        days_back: int,
        agent_name: str
    ) -> List[Dict]:
        """Generate appointment activity records."""
        appointments = []
        now = datetime.now()

        appointment_subjects = [
            "On-site service visit",
            "Customer review meeting",
            "Technical consultation",
            "Product demonstration",
            "Quarterly business review",
            "Installation planning"
        ]

        for i in range(count):
            contact = random.choice(contacts) if contacts else None
            case = random.choice(cases) if cases else None
            account_name = contact["account"] if contact else (accounts[0]["name"] if accounts else "Demo Account")

            # Mix of past and future appointments
            days_offset = random.randint(-days_back, 14)
            start_date = now + timedelta(days=days_offset, hours=random.randint(9, 15))
            duration_hours = random.choice([1, 1.5, 2, 4])
            end_date = start_date + timedelta(hours=duration_hours)

            is_past = days_offset < 0
            status = "Completed" if is_past else random.choice(["Scheduled", "Confirmed"])

            appointments.append({
                "subject": random.choice(appointment_subjects),
                "location": contact["account"] if contact else "Customer site",
                "startTime": start_date.isoformat(),
                "endTime": end_date.isoformat(),
                "duration": f"{duration_hours} hour{'s' if duration_hours > 1 else ''}",
                "organizer": agent_name,
                "attendees": [f"{contact['firstName']} {contact['lastName']}"] if contact else ["Customer"],
                "regarding": case["title"] if case else f"Account: {account_name}",
                "account": account_name,
                "contact": f"{contact['firstName']} {contact['lastName']}" if contact else None,
                "status": status,
                "isOnline": random.choice([True, False]),
                "description": f"{'Virtual' if random.choice([True, False]) else 'On-site'} meeting with customer.",
                "demoNote": f"Appointment - {'Past' if is_past else 'Upcoming'}"
            })

        appointments.sort(key=lambda x: x["startTime"])
        return appointments

    def _generate_post_activities(
        self,
        contacts: List[Dict],
        accounts: List[Dict],
        cases: List[Dict],
        count: int,
        days_back: int,
        agent_name: str
    ) -> List[Dict]:
        """Generate timeline post/social activity records (internal notes visible on timeline)."""
        posts = []
        now = datetime.now()

        post_texts = [
            "Resolved customer issue - great feedback received!",
            "Escalation handled successfully. Customer satisfied with outcome.",
            "Coordinated with sales team on account strategy.",
            "Training session completed on new product line.",
            "Process improvement suggestion submitted.",
            "Customer reference call completed - willing to be a reference!",
            "Complex case resolved after multi-team collaboration.",
            "Proactive outreach completed for at-risk account."
        ]

        for i in range(count):
            contact = random.choice(contacts) if contacts else None
            case = random.choice(cases) if cases else None
            account_name = contact["account"] if contact else (accounts[0]["name"] if accounts else "Demo Account")

            days_ago = random.randint(1, days_back)
            activity_date = now - timedelta(days=days_ago, hours=random.randint(8, 17), minutes=random.randint(0, 59))

            posts.append({
                "text": random.choice(post_texts),
                "author": agent_name,
                "dateTime": activity_date.isoformat(),
                "regarding": case["title"] if case else f"Account: {account_name}",
                "account": account_name,
                "type": random.choice(["Status Update", "Auto Post", "User Post"]),
                "likes": random.randint(0, 5),
                "comments": random.randint(0, 2),
                "demoNote": f"Timeline post - {days_ago} days ago"
            })

        posts.sort(key=lambda x: x["dateTime"], reverse=True)
        return posts
