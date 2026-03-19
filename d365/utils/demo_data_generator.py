"""
D365 Demo Data Generator
========================
Uses GPT-4o to generate realistic D365 demo data from customer inputs.

Takes a demo_inputs.json file and generates:
- environment.json (D365 environment configuration)
- demo-data.json (accounts, contacts, products, cases, KB articles, etc.)

Usage:
    from d365.utils.demo_data_generator import D365DemoDataGenerator
    
    generator = D365DemoDataGenerator()
    result = generator.generate_from_inputs("customers/otis/d365/config/demo-inputs.json")
"""

import json
import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logger = logging.getLogger(__name__)

# US phone number area codes by region for realistic data
US_AREA_CODES = {
    "northeast": ["212", "617", "215", "412", "216"],
    "southeast": ["404", "305", "704", "615", "919"],
    "midwest": ["312", "313", "614", "816", "952"],
    "southwest": ["214", "713", "602", "480", "512"],
    "west": ["415", "310", "206", "303", "702"]
}

# UK phone formats for EMEA
UK_AREA_CODES = ["020", "0121", "0161", "0113", "0131"]


class D365DemoDataGenerator:
    """Generates D365 demo data using GPT-4o from structured inputs."""
    
    def __init__(self):
        """Initialize with Azure OpenAI client."""
        self.client = self._get_openai_client()
        self.model = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        
    def _get_openai_client(self) -> AzureOpenAI:
        """Create Azure OpenAI client with token auth."""
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not set")
            
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        
        return AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        )
    
    def generate_from_inputs(self, inputs_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate full D365 demo data from inputs file.
        
        Args:
            inputs_path: Path to demo-inputs.json file
            output_dir: Directory for output files (defaults to same as inputs)
            
        Returns:
            Dict with generated environment.json and demo-data.json content
        """
        inputs_path = Path(inputs_path)
        if not inputs_path.exists():
            raise FileNotFoundError(f"Inputs file not found: {inputs_path}")
            
        with open(inputs_path, "r", encoding="utf-8") as f:
            inputs = json.load(f)
            
        output_dir = Path(output_dir) if output_dir else inputs_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating demo data for: {inputs['customer']['name']}")
        
        # Generate environment.json
        environment = self._generate_environment(inputs)
        env_path = output_dir / "environment.json"
        with open(env_path, "w", encoding="utf-8") as f:
            json.dump(environment, f, indent=2)
        logger.info(f"Generated: {env_path}")
        
        # Generate demo-data.json with all entities
        demo_data = self._generate_demo_data(inputs)
        data_path = output_dir / "demo-data-generated.json"
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(demo_data, f, indent=2)
        logger.info(f"Generated: {data_path}")
        
        return {
            "environment": environment,
            "demo_data": demo_data,
            "files_created": [str(env_path), str(data_path)]
        }
    
    def _generate_environment(self, inputs: Dict) -> Dict:
        """Generate environment.json from inputs."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        discovery = inputs.get("discovery_context", {})
        
        # Build tier configurations
        tiers = {}
        tier_names = demo_req.get("customer_tiers", ["Premium", "Standard", "Basic"])
        for i, tier in enumerate(tier_names):
            tier_key = tier.lower().replace(" ", "_")
            tiers[tier_key] = {
                "name": tier,
                "priority": i + 1,
                "slaMultiplier": 1.0 + (i * 0.5),  # Premium=1x, Standard=1.5x, Basic=2x
                "features": self._get_tier_features(i)
            }
        
        return {
            "environment": {
                "name": f"{customer['name']} Demo",
                "url": "https://orgecbce8ef.crm.dynamics.com",  # Default org
                "type": "sandbox"
            },
            "demo": {
                "customer": customer["name"],
                "industry": customer["industry"],
                "brands": customer.get("brands", [customer["name"]]),
                "region": customer.get("region", "NA"),
                "customerTiers": tiers,
                "hotWords": demo_req.get("hot_words", ["Urgent", "Emergency"]),
                "channels": discovery.get("channels", ["phone"]),
                "useCase": discovery.get("use_case", "case_management")
            },
            "sla": {
                "firstResponseMinutes": demo_req.get("sla_settings", {}).get("first_response_minutes", 240),
                "resolutionMinutes": demo_req.get("sla_settings", {}).get("resolution_minutes", 480)
            },
            "provisioning": {
                "accountCount": demo_req.get("account_count", 15),
                "contactCount": demo_req.get("contact_count", 20),
                "caseCount": demo_req.get("case_count", 50),
                "kbArticleCount": demo_req.get("kb_article_count", 15)
            },
            "metadata": {
                "generatedAt": datetime.utcnow().isoformat(),
                "generatedBy": "D365DemoDataGenerator",
                "inputsFile": "demo-inputs.json"
            }
        }
    
    def _get_tier_features(self, tier_index: int) -> List[str]:
        """Get features for a tier based on index (0=highest)."""
        all_features = [
            "24/7 Support",
            "Priority Routing",
            "Dedicated Agent",
            "SLA Guarantee",
            "Quarterly Reviews",
            "Annual Inspection",
            "Remote Monitoring",
            "Preventive Maintenance"
        ]
        # Higher tiers get more features
        return all_features[:8 - (tier_index * 2)]
    
    def _generate_demo_data(self, inputs: Dict) -> Dict:
        """Generate all demo data entities using GPT-4o."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        discovery = inputs.get("discovery_context", {})
        use_us_phones = inputs.get("output_options", {}).get("use_us_phone_numbers", True)
        
        # Generate accounts
        accounts = self._generate_accounts(inputs)
        
        # Generate contacts linked to accounts
        contacts = self._generate_contacts(inputs, accounts)
        
        # Get products from inputs or generate
        products = inputs.get("products", [])
        if not products:
            products = self._generate_products(inputs)
        
        # Generate cases
        cases = self._generate_cases(inputs, accounts, contacts)
        
        # Generate KB articles
        kb_articles = self._generate_kb_articles(inputs)
        
        # Generate queues
        queues = self._generate_queues(inputs)
        
        # Generate SLAs
        slas = self._generate_slas(inputs)
        
        return {
            "customer": {
                "name": customer["name"],
                "industry": customer["industry"],
                "generatedAt": datetime.utcnow().isoformat()
            },
            "serviceAccounts": {
                "description": f"Service accounts for {customer['name']} demo",
                "accounts": accounts
            },
            "contacts": {
                "description": "Contacts linked to service accounts",
                "contacts": contacts
            },
            "products": {
                "description": f"{customer['name']} products and services",
                "products": products
            },
            "demoCases": {
                "description": "Demo support cases across tiers and types",
                "cases": cases
            },
            "knowledgeArticles": {
                "description": "Knowledge base articles for demo",
                "articles": kb_articles
            },
            "queues": {
                "description": "Support queues by tier and channel",
                "queues": queues
            },
            "slas": {
                "description": "Service level agreements by tier",
                "slas": slas
            }
        }
    
    def _generate_accounts(self, inputs: Dict) -> List[Dict]:
        """Generate realistic accounts using GPT-4o."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        count = demo_req.get("account_count", 15)
        tiers = demo_req.get("customer_tiers", ["Premium", "Standard", "Basic"])
        region = customer.get("region", "NA")
        industry = customer.get("industry", "manufacturing")
        
        prompt = f"""Generate {count} realistic company account names for a {industry} demo.
        
Context:
- Customer: {customer['name']}
- Industry: {industry}
- Region: {region}
- Hero customer: {demo_req.get('hero_scenario', {}).get('customer_name', 'Major Corp')}

Requirements:
1. Mix of company types: large enterprises, mid-market, small businesses
2. Industry-appropriate names (buildings, facilities for elevator; manufacturers, distributors for plumbing)
3. Include the hero customer name exactly as specified
4. Realistic names for the {region} region

Return a JSON array of objects with:
- name: Company name
- type: "enterprise" | "mid-market" | "small-business"
- tier: One of {json.dumps(tiers)}
- industry_context: Brief description of why they'd use {customer['name']}

Example:
[
  {{"name": "Canary Wharf Group", "type": "enterprise", "tier": "Premium", "industry_context": "Major London commercial complex with 50+ elevators"}}
]

Return ONLY the JSON array, no markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        try:
            accounts_raw = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback to basic generation
            accounts_raw = self._generate_fallback_accounts(count, tiers, customer)
        
        # Enrich with additional fields
        region_key = "northeast" if region in ["EMEA", "NA"] else "west"
        accounts = []
        for i, acc in enumerate(accounts_raw):
            account_num = f"{customer['name'][:3].upper()}-{1000 + i}"
            phone = self._generate_phone(region, region_key)
            
            accounts.append({
                "name": acc["name"],
                "accountNumber": account_num,
                "tier": acc.get("tier", tiers[i % len(tiers)]),
                "type": acc.get("type", "mid-market"),
                "phone": phone,
                "address": self._generate_address(region),
                "industryContext": acc.get("industry_context", ""),
                "totalUnits": random.randint(5, 100) if industry == "elevator_service" else None,
                "contract": f"{acc.get('tier', tiers[0])} Service Contract"
            })
        
        return accounts
    
    def _generate_contacts(self, inputs: Dict, accounts: List[Dict]) -> List[Dict]:
        """Generate contacts linked to accounts."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        count = demo_req.get("contact_count", 20)
        region = customer.get("region", "NA")
        hero = demo_req.get("hero_scenario", {})
        
        # Job titles appropriate for the industry
        titles = self._get_industry_titles(customer.get("industry", "manufacturing"))
        
        prompt = f"""Generate {count} realistic contact names for a {customer['industry']} demo.

Context:
- Companies: {[a['name'] for a in accounts[:5]]}...
- Region: {region}
- Hero contact: {hero.get('contact_name', 'Sarah Mitchell')} at {hero.get('customer_name', accounts[0]['name'])}

Requirements:
1. Diverse, realistic names appropriate for {region} region
2. Include the hero contact name exactly as specified
3. Mix of genders and backgrounds

Return a JSON array with firstName, lastName only:
[{{"firstName": "Sarah", "lastName": "Mitchell"}}]

Return ONLY the JSON array, no markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        try:
            names = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            names = self._generate_fallback_names(count)
        
        # Build full contact records
        use_us_phones = inputs.get("output_options", {}).get("use_us_phone_numbers", True)
        contacts = []
        for i, name in enumerate(names):
            account = accounts[i % len(accounts)]
            title = titles[i % len(titles)]
            first = name.get("firstName", f"Contact{i}")
            last = name.get("lastName", "Demo")
            
            phone_region = "NA" if use_us_phones else region
            
            contacts.append({
                "firstName": first,
                "lastName": last,
                "title": title,
                "account": account["name"],
                "email": f"{first.lower()}.{last.lower()}@{self._domain_from_name(account['name'])}",
                "phone": self._generate_phone(phone_region, "northeast"),
                "mobile": self._generate_phone(phone_region, "northeast"),
                "isPrimary": i == 0 or (hero.get("contact_name", "").lower() in f"{first} {last}".lower())
            })
        
        return contacts
    
    def _generate_cases(self, inputs: Dict, accounts: List[Dict], contacts: List[Dict]) -> List[Dict]:
        """Generate demo cases."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        count = demo_req.get("case_count", 50)
        case_types = demo_req.get("case_types", ["support_request", "inquiry", "complaint"])
        hero = demo_req.get("hero_scenario", {})
        tiers = demo_req.get("customer_tiers", ["Premium", "Standard", "Basic"])
        
        prompt = f"""Generate {count} realistic support case titles for a {customer['industry']} contact center demo.

Context:
- Customer: {customer['name']}
- Case types: {case_types}
- Hero case: "{hero.get('title', 'Priority Support Request')}"

Requirements:
1. Mix of case types: {case_types}
2. Include the hero case title exactly
3. Realistic scenarios for {customer['industry']} industry
4. Mix of priorities and urgencies

Return a JSON array with:
- title: Case title
- type: One of {case_types}
- priority: "Critical" | "High" | "Normal" | "Low"
- description: 1-2 sentence description

Return ONLY the JSON array, no markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        try:
            cases_raw = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            cases_raw = self._generate_fallback_cases(count, case_types, hero)
        
        # Enrich cases with account/contact links
        cases = []
        for i, case in enumerate(cases_raw):
            account_idx = i % len(accounts)
            contact = next((c for c in contacts if c["account"] == accounts[account_idx]["name"]), contacts[i % len(contacts)])
            
            # Determine if this is the hero case
            is_hero = hero.get("title", "").lower() in case.get("title", "").lower()
            
            cases.append({
                "title": case["title"],
                "type": case.get("type", case_types[i % len(case_types)]),
                "priority": hero.get("priority", "High") if is_hero else case.get("priority", "Normal"),
                "description": case.get("description", "Support request requiring attention."),
                "account": hero.get("customer_name") if is_hero else accounts[account_idx]["name"],
                "contact": hero.get("contact_name") if is_hero else f"{contact['firstName']} {contact['lastName']}",
                "tier": accounts[account_idx]["tier"],
                "equipment": f"Unit-{random.randint(100, 999)}",
                "demoUse": "Hero Scenario" if is_hero else f"Tier {accounts[account_idx]['tier']} example",
                "isHero": is_hero
            })
        
        return cases
    
    def _generate_kb_articles(self, inputs: Dict) -> List[Dict]:
        """Generate knowledge base articles."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        count = demo_req.get("kb_article_count", 15)
        case_types = demo_req.get("case_types", ["support"])
        
        prompt = f"""Generate {count} knowledge base article titles and summaries for a {customer['industry']} support team.

Context:
- Customer: {customer['name']}
- Case types they handle: {case_types}
- Products: {[p.get('name', p) for p in inputs.get('products', [])[:5]]}

Requirements:
1. Mix of troubleshooting guides, FAQs, policies, procedures
2. Relevant to the case types: {case_types}
3. Practical articles agents would use during calls

Return a JSON array with:
- title: Article title
- category: "Troubleshooting" | "FAQ" | "Policy" | "Procedure" | "Product Info"
- summary: 2-3 sentence summary
- keywords: Array of search keywords

Return ONLY the JSON array, no markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        try:
            articles_raw = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            articles_raw = self._generate_fallback_kb(count, customer)
        
        articles = []
        for i, art in enumerate(articles_raw):
            articles.append({
                "title": art["title"],
                "articleNumber": f"KB-{customer['name'][:3].upper()}-{1000 + i}",
                "category": art.get("category", "FAQ"),
                "summary": art.get("summary", "Knowledge article for support agents."),
                "keywords": art.get("keywords", [customer["name"], "support"]),
                "status": "Published"
            })
        
        return articles
    
    def _generate_queues(self, inputs: Dict) -> List[Dict]:
        """Generate support queues."""
        customer = inputs["customer"]
        demo_req = inputs.get("demo_requirements", {})
        tiers = demo_req.get("customer_tiers", ["Premium", "Standard", "Basic"])
        channels = inputs.get("discovery_context", {}).get("channels", ["phone"])
        brands = customer.get("brands", [customer["name"]])
        
        queues = []
        queue_num = 1
        
        # Queues by tier
        for tier in tiers:
            queues.append({
                "name": f"{tier} Support",
                "queueNumber": f"Q-{queue_num:03d}",
                "type": "tier",
                "tier": tier,
                "description": f"Queue for {tier} tier customers"
            })
            queue_num += 1
        
        # Queues by channel
        for channel in channels:
            queues.append({
                "name": f"{channel.title()} Support",
                "queueNumber": f"Q-{queue_num:03d}",
                "type": "channel",
                "channel": channel,
                "description": f"Queue for {channel} channel"
            })
            queue_num += 1
        
        # Brand queues if multiple brands
        if len(brands) > 1:
            for brand in brands:
                queues.append({
                    "name": f"{brand} Support",
                    "queueNumber": f"Q-{queue_num:03d}",
                    "type": "brand",
                    "brand": brand,
                    "description": f"Queue for {brand} product support"
                })
                queue_num += 1
        
        # Emergency queue
        queues.append({
            "name": "Emergency Response",
            "queueNumber": f"Q-{queue_num:03d}",
            "type": "priority",
            "description": "High-priority emergency cases"
        })
        
        return queues
    
    def _generate_slas(self, inputs: Dict) -> List[Dict]:
        """Generate SLA configurations."""
        demo_req = inputs.get("demo_requirements", {})
        tiers = demo_req.get("customer_tiers", ["Premium", "Standard", "Basic"])
        base_response = demo_req.get("sla_settings", {}).get("first_response_minutes", 240)
        base_resolution = demo_req.get("sla_settings", {}).get("resolution_minutes", 480)
        
        slas = []
        for i, tier in enumerate(tiers):
            multiplier = 1.0 + (i * 0.5)  # Premium=1x, Standard=1.5x, Basic=2x
            slas.append({
                "name": f"{tier} SLA",
                "tier": tier,
                "firstResponseMinutes": int(base_response * multiplier),
                "resolutionMinutes": int(base_resolution * multiplier),
                "businessHours": i > 0,  # Premium = 24/7, others = business hours
                "escalationEnabled": i == 0  # Only Premium has auto-escalation
            })
        
        return slas
    
    # =========================================================================
    # Helper methods
    # =========================================================================
    
    def _generate_phone(self, region: str, region_key: str) -> str:
        """Generate a realistic phone number."""
        if region in ["EMEA"]:
            # But if use_us_phones is true, this won't be called for contacts
            area = random.choice(UK_AREA_CODES)
            return f"+44 {area} {random.randint(100, 999)} {random.randint(1000, 9999)}"
        else:
            area = random.choice(US_AREA_CODES.get(region_key, US_AREA_CODES["northeast"]))
            return f"+1 ({area}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
    
    def _generate_address(self, region: str) -> Dict:
        """Generate a realistic address."""
        if region == "EMEA":
            return {
                "line1": f"{random.randint(1, 200)} {random.choice(['High Street', 'King Street', 'Queen Street', 'Victoria Road', 'Church Lane'])}",
                "city": random.choice(["London", "Manchester", "Birmingham", "Leeds", "Edinburgh"]),
                "postalCode": f"{random.choice(['EC', 'WC', 'SW', 'NW', 'SE'])}{random.randint(1, 9)} {random.randint(1, 9)}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}",
                "country": "United Kingdom"
            }
        else:
            return {
                "line1": f"{random.randint(100, 9999)} {random.choice(['Main', 'Broadway', 'Market', 'Oak', 'Park'])} {random.choice(['Street', 'Avenue', 'Boulevard', 'Drive'])}",
                "city": random.choice(["New York", "Chicago", "Houston", "Phoenix", "Seattle", "Denver"]),
                "state": random.choice(["NY", "IL", "TX", "AZ", "WA", "CO"]),
                "postalCode": f"{random.randint(10000, 99999)}",
                "country": "United States"
            }
    
    def _get_industry_titles(self, industry: str) -> List[str]:
        """Get job titles appropriate for an industry."""
        base_titles = ["Director of Operations", "Facilities Manager", "Building Manager", "Operations Manager"]
        
        industry_titles = {
            "elevator_service": ["Building Superintendent", "Facilities Director", "Property Manager", "Chief Engineer"],
            "plumbing_manufacturing": ["Purchasing Manager", "Procurement Director", "Operations Director", "Branch Manager"],
            "hvac": ["Maintenance Director", "Facilities Coordinator", "Building Engineer", "Property Administrator"],
            "manufacturing": ["Plant Manager", "Production Director", "Operations VP", "Supply Chain Manager"]
        }
        
        return industry_titles.get(industry, base_titles) + base_titles
    
    def _domain_from_name(self, company_name: str) -> str:
        """Create email domain from company name."""
        clean = company_name.lower().replace(" ", "").replace(",", "").replace(".", "")
        clean = ''.join(c for c in clean if c.isalnum())[:15]
        return f"{clean}.com"
    
    def _generate_fallback_accounts(self, count: int, tiers: List[str], customer: Dict) -> List[Dict]:
        """Fallback account generation if GPT fails."""
        accounts = []
        for i in range(count):
            accounts.append({
                "name": f"{customer['name']} Customer {i+1}",
                "type": ["enterprise", "mid-market", "small-business"][i % 3],
                "tier": tiers[i % len(tiers)],
                "industry_context": f"Customer using {customer['name']} services"
            })
        return accounts
    
    def _generate_fallback_names(self, count: int) -> List[Dict]:
        """Fallback name generation."""
        first_names = ["James", "Sarah", "Michael", "Emma", "David", "Lisa", "Robert", "Jennifer", "William", "Maria"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor"]
        return [{"firstName": first_names[i % len(first_names)], "lastName": last_names[i % len(last_names)]} for i in range(count)]
    
    def _generate_fallback_cases(self, count: int, case_types: List[str], hero: Dict) -> List[Dict]:
        """Fallback case generation."""
        cases = []
        if hero.get("title"):
            cases.append({"title": hero["title"], "type": case_types[0], "priority": hero.get("priority", "High"), "description": hero.get("description", "Priority case")})
        for i in range(count - len(cases)):
            cases.append({
                "title": f"Support Case {i+1}",
                "type": case_types[i % len(case_types)],
                "priority": ["Normal", "High", "Low", "Critical"][i % 4],
                "description": "Support request requiring attention."
            })
        return cases
    
    def _generate_fallback_kb(self, count: int, customer: Dict) -> List[Dict]:
        """Fallback KB article generation."""
        return [
            {"title": f"{customer['name']} Support Guide {i+1}", "category": "FAQ", "summary": "Support documentation.", "keywords": ["support"]}
            for i in range(count)
        ]


# Convenience function for direct usage
def generate_demo_data(inputs_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Generate D365 demo data from inputs file."""
    generator = D365DemoDataGenerator()
    return generator.generate_from_inputs(inputs_path, output_dir)
