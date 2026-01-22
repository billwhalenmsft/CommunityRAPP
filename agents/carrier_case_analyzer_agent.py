"""
Agent: CarrierCaseAnalyzerAgent
Purpose: Extracts key issue details from case text using AI
Customer: Carrier
AI Model: Azure OpenAI GPT-4o
Demo Mode: Uses stubbed responses - replace with live AI calls for production

This agent performs:
- Issue type classification
- Urgency detection
- Entity extraction (products, serial numbers, symptoms)
- Customer sentiment analysis
- Key information summarization
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# =============================================================================
# CONFIGURATION
# =============================================================================
ANALYZER_CONFIG = {
    "use_mock_data": True,  # Set to False when Azure OpenAI is configured
    "model": "gpt-4o",
    "temperature": 0.3,  # Lower temperature for consistent extraction
    "max_tokens": 2000
}

# Issue type classifications for Carrier
ISSUE_TYPES = [
    "HVAC",           # Heating, ventilation, air conditioning issues
    "Controls",       # i-Vu, BMS integration, thermostats
    "Parts",          # Parts orders, availability, replacements
    "Installation",   # New installation issues
    "Warranty",       # Warranty claims, coverage questions
    "Maintenance",    # Preventive maintenance, service contracts
    "Other"           # Catch-all
]

# Common Carrier product patterns for extraction
PRODUCT_PATTERNS = {
    "rooftop_units": r"(?:48|50)X[A-Z]\s*\d*",  # 48XC, 50XC, etc.
    "split_systems": r"38[A-Z]{2,3}\s*\d*",     # 38AUD, 38AUZ, etc.
    "chillers": r"(?:19|23|30)[A-Z]{2}\s*\d*",  # 19XR, 23XR, 30RB, etc.
    "controls": r"i-Vu|ComfortVIEW|Infinity",
    "serial_pattern": r"\b\d{4}[A-Z]\d{4,6}\b", # e.g., 2419G12345
    "error_codes": r"E\d{2,3}|Error\s*\d{2,3}|Code\s*[A-Z]?\d{2,3}"
}


class CarrierCaseAnalyzerAgent(BasicAgent):
    """
    Analyzes case text to extract key information using AI.

    Extraction capabilities:
    - Issue type classification
    - Urgency/severity detection
    - Product identification (models, serial numbers)
    - Symptom extraction
    - Customer sentiment analysis
    - Key entity extraction (locations, contacts, dates)

    Demo Mode: Returns intelligent mock analysis
    Production: Uses Azure OpenAI GPT-4o for extraction
    """

    def __init__(self):
        self.name = 'CarrierCaseAnalyzer'
        self.metadata = {
            "name": self.name,
            "description": "Analyzes case text to extract issue type, urgency, product details, and key entities using AI. Part of the Carrier Case Triage Agent Swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Analysis action to perform",
                        "enum": [
                            "analyze_case_text",
                            "classify_issue_type",
                            "detect_urgency",
                            "extract_product_references",
                            "identify_customer_sentiment",
                            "full_analysis"
                        ]
                    },
                    "case_subject": {
                        "type": "string",
                        "description": "Case subject line"
                    },
                    "case_description": {
                        "type": "string",
                        "description": "Full case description text"
                    },
                    "case_comments": {
                        "type": "array",
                        "description": "Array of case comment texts",
                        "items": {"type": "string"}
                    },
                    "include_sentiment": {
                        "type": "boolean",
                        "description": "Include sentiment analysis",
                        "default": True
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = ANALYZER_CONFIG

    def perform(self, **kwargs) -> str:
        """Execute case analysis."""
        action = kwargs.pop('action', 'full_analysis')

        try:
            if self.config["use_mock_data"]:
                result = self._handle_mock_request(action, **kwargs)
            else:
                result = self._handle_live_request(action, **kwargs)

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"CarrierCaseAnalyzer error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "status": "failed"
            }, indent=2)

    def _handle_mock_request(self, action: str, **kwargs) -> Dict:
        """Handle request with intelligent mock responses."""
        case_subject = kwargs.get('case_subject', '')
        case_description = kwargs.get('case_description', '')
        full_text = f"{case_subject}\n{case_description}"

        if action == "full_analysis" or action == "analyze_case_text":
            return self._mock_full_analysis(case_subject, case_description)
        
        elif action == "classify_issue_type":
            return self._mock_classify_issue(full_text)
        
        elif action == "detect_urgency":
            return self._mock_detect_urgency(full_text)
        
        elif action == "extract_product_references":
            return self._mock_extract_products(full_text)
        
        elif action == "identify_customer_sentiment":
            return self._mock_sentiment_analysis(full_text)
        
        else:
            return {
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _mock_full_analysis(self, subject: str, description: str) -> Dict:
        """Generate comprehensive mock analysis."""
        full_text = f"{subject}\n{description}".lower()
        
        # Detect issue type based on keywords
        issue_type = "Other"
        if any(w in full_text for w in ["cooling", "heating", "hvac", "temperature", "air", "rooftop", "unit"]):
            issue_type = "HVAC"
        elif any(w in full_text for w in ["control", "bms", "i-vu", "thermostat", "bacnet"]):
            issue_type = "Controls"
        elif any(w in full_text for w in ["part", "replace", "order"]):
            issue_type = "Parts"
        elif any(w in full_text for w in ["warranty", "coverage", "claim"]):
            issue_type = "Warranty"
        elif any(w in full_text for w in ["maintenance", "service contract", "preventive"]):
            issue_type = "Maintenance"
        elif any(w in full_text for w in ["install", "commission"]):
            issue_type = "Installation"

        # Detect urgency
        urgency_score = 0.5  # Default medium
        urgency_factors = []
        
        if any(w in full_text for w in ["urgent", "emergency", "asap", "critical", "down"]):
            urgency_score = 0.9
            urgency_factors.append("Explicit urgency language detected")
        if any(w in full_text for w in ["safety", "hazard", "danger"]):
            urgency_score = 1.0
            urgency_factors.append("Safety concern mentioned")
        if any(w in full_text for w in ["production", "manufacturing", "operations stopped"]):
            urgency_score = max(urgency_score, 0.85)
            urgency_factors.append("Production/business impact")
        if any(w in full_text for w in ["hospital", "medical", "healthcare"]):
            urgency_score = max(urgency_score, 0.9)
            urgency_factors.append("Healthcare facility - critical environment")
        
        # Map score to level
        if urgency_score >= 0.9:
            urgency_level = "Critical"
        elif urgency_score >= 0.7:
            urgency_level = "High"
        elif urgency_score >= 0.4:
            urgency_level = "Medium"
        else:
            urgency_level = "Low"

        # Extract products using regex
        products = self._extract_products_regex(f"{subject}\n{description}")
        
        # Extract error codes
        error_codes = re.findall(PRODUCT_PATTERNS["error_codes"], f"{subject}\n{description}", re.IGNORECASE)
        
        # Mock symptoms extraction
        symptoms = []
        symptom_keywords = {
            "not cooling": "Unit not cooling",
            "not heating": "Unit not heating",
            "warm air": "Blowing warm air",
            "noise": "Unusual noise",
            "vibration": "Vibration issue",
            "leak": "Possible leak",
            "error": "Error code displayed",
            "won't start": "Unit won't start",
            "short cycling": "Short cycling"
        }
        for keyword, symptom in symptom_keywords.items():
            if keyword in full_text:
                symptoms.append(symptom)

        # Sentiment analysis
        sentiment_score = 0.5  # Neutral
        if any(w in full_text for w in ["frustrated", "angry", "unacceptable", "disappointed"]):
            sentiment_score = 0.2
        elif any(w in full_text for w in ["thank", "appreciate", "please"]):
            sentiment_score = 0.7
        
        if sentiment_score < 0.4:
            sentiment = "Negative"
        elif sentiment_score > 0.6:
            sentiment = "Positive"
        else:
            sentiment = "Neutral"

        # Customer ask extraction
        customer_ask = "Resolution needed"
        if "quote" in full_text:
            customer_ask = "Requesting quote"
        elif "repair" in full_text or "fix" in full_text:
            customer_ask = "Requesting repair"
        elif "replace" in full_text:
            customer_ask = "Requesting replacement"
        elif "schedule" in full_text or "visit" in full_text:
            customer_ask = "Requesting service visit"

        return {
            "action": "full_analysis",
            "status": "success",
            "source": "mock_data",
            "analysis": {
                "issue_type": issue_type,
                "sub_category": self._get_subcategory(issue_type, full_text),
                "urgency": {
                    "level": urgency_level,
                    "score": urgency_score,
                    "factors": urgency_factors if urgency_factors else ["Standard priority"]
                },
                "products": {
                    "models": products.get("models", []),
                    "serial_numbers": products.get("serials", []),
                    "error_codes": error_codes
                },
                "symptoms": symptoms if symptoms else ["Issue requires further analysis"],
                "customer_ask": customer_ask,
                "sentiment": {
                    "classification": sentiment,
                    "score": sentiment_score,
                    "note": "Based on language analysis"
                },
                "key_entities": {
                    "locations": self._extract_locations(f"{subject}\n{description}"),
                    "equipment_mentioned": products.get("models", []),
                    "contacts_mentioned": []
                },
                "confidence_score": 0.85
            },
            "processing_time_ms": 234,
            "model_used": "mock_analysis"
        }

    def _mock_classify_issue(self, text: str) -> Dict:
        """Mock issue classification."""
        text_lower = text.lower()
        
        classifications = []
        for issue_type in ISSUE_TYPES:
            score = 0.1
            if issue_type.lower() in text_lower:
                score = 0.9
            classifications.append({"type": issue_type, "confidence": score})
        
        # Sort by confidence
        classifications.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "action": "classify_issue_type",
            "status": "success",
            "source": "mock_data",
            "primary_classification": classifications[0]["type"],
            "confidence": classifications[0]["confidence"],
            "all_classifications": classifications
        }

    def _mock_detect_urgency(self, text: str) -> Dict:
        """Mock urgency detection."""
        text_lower = text.lower()
        
        urgency_indicators = []
        base_score = 0.5
        
        urgent_keywords = {
            "emergency": 0.4,
            "urgent": 0.3,
            "asap": 0.3,
            "critical": 0.3,
            "down": 0.2,
            "stopped": 0.2,
            "safety": 0.4,
            "production": 0.2
        }
        
        for keyword, boost in urgent_keywords.items():
            if keyword in text_lower:
                base_score = min(1.0, base_score + boost)
                urgency_indicators.append(f"Keyword detected: {keyword}")
        
        if base_score >= 0.9:
            level = "Critical"
        elif base_score >= 0.7:
            level = "High"
        elif base_score >= 0.4:
            level = "Medium"
        else:
            level = "Low"

        return {
            "action": "detect_urgency",
            "status": "success",
            "source": "mock_data",
            "urgency_level": level,
            "urgency_score": base_score,
            "indicators": urgency_indicators if urgency_indicators else ["No urgent indicators detected"],
            "recommended_sla_hours": {"Critical": 2, "High": 4, "Medium": 24, "Low": 72}.get(level, 24)
        }

    def _mock_extract_products(self, text: str) -> Dict:
        """Mock product extraction."""
        products = self._extract_products_regex(text)
        error_codes = re.findall(PRODUCT_PATTERNS["error_codes"], text, re.IGNORECASE)
        
        return {
            "action": "extract_product_references",
            "status": "success",
            "source": "mock_data",
            "products": {
                "models_found": products.get("models", []),
                "serial_numbers": products.get("serials", []),
                "error_codes": error_codes,
                "product_lines": products.get("product_lines", [])
            },
            "extraction_confidence": 0.9 if products.get("models") or products.get("serials") else 0.5
        }

    def _mock_sentiment_analysis(self, text: str) -> Dict:
        """Mock sentiment analysis."""
        text_lower = text.lower()
        
        positive_words = ["thank", "appreciate", "great", "excellent", "happy", "pleased"]
        negative_words = ["frustrated", "angry", "disappointed", "unacceptable", "terrible", "poor"]
        
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)
        
        if negative_count > positive_count:
            sentiment = "Negative"
            score = 0.3 - (negative_count * 0.1)
        elif positive_count > negative_count:
            sentiment = "Positive"
            score = 0.7 + (positive_count * 0.1)
        else:
            sentiment = "Neutral"
            score = 0.5
        
        score = max(0.0, min(1.0, score))

        return {
            "action": "identify_customer_sentiment",
            "status": "success",
            "source": "mock_data",
            "sentiment": sentiment,
            "sentiment_score": score,
            "positive_indicators": [w for w in positive_words if w in text_lower],
            "negative_indicators": [w for w in negative_words if w in text_lower],
            "recommendation": "Prioritize response" if sentiment == "Negative" else "Standard handling"
        }

    def _extract_products_regex(self, text: str) -> Dict:
        """Extract product information using regex patterns."""
        models = []
        serials = []
        product_lines = []
        
        # Extract model numbers
        for pattern_name, pattern in PRODUCT_PATTERNS.items():
            if pattern_name in ["rooftop_units", "split_systems", "chillers", "controls"]:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    models.extend(matches)
                    if pattern_name == "rooftop_units":
                        product_lines.append("Rooftop Units")
                    elif pattern_name == "split_systems":
                        product_lines.append("Split Systems")
                    elif pattern_name == "chillers":
                        product_lines.append("Chillers")
                    elif pattern_name == "controls":
                        product_lines.append("Controls")
        
        # Extract serial numbers
        serial_matches = re.findall(PRODUCT_PATTERNS["serial_pattern"], text)
        serials.extend(serial_matches)
        
        return {
            "models": list(set(models)),
            "serials": list(set(serials)),
            "product_lines": list(set(product_lines))
        }

    def _extract_locations(self, text: str) -> List[str]:
        """Extract location mentions from text."""
        locations = []
        location_keywords = ["building", "floor", "room", "facility", "plant", "warehouse", "office"]
        
        for keyword in location_keywords:
            pattern = rf"{keyword}\s*[A-Za-z0-9\-]+"
            matches = re.findall(pattern, text, re.IGNORECASE)
            locations.extend(matches)
        
        return list(set(locations))

    def _get_subcategory(self, issue_type: str, text: str) -> str:
        """Get subcategory based on issue type and text."""
        subcategories = {
            "HVAC": {
                "cooling": "Cooling Issue",
                "heating": "Heating Issue",
                "noise": "Noise/Vibration",
                "startup": "Startup Problem",
                "default": "General HVAC"
            },
            "Controls": {
                "bacnet": "BACnet Integration",
                "thermostat": "Thermostat Issue",
                "i-vu": "i-Vu System",
                "default": "Controls General"
            }
        }
        
        if issue_type in subcategories:
            for keyword, subcat in subcategories[issue_type].items():
                if keyword in text:
                    return subcat
            return subcategories[issue_type].get("default", issue_type)
        
        return issue_type

    def _handle_live_request(self, action: str, **kwargs) -> Dict:
        """
        Handle request using live Azure OpenAI.
        
        Production Implementation:
        1. Use Azure OpenAI SDK
        2. Implement structured output parsing
        3. Add retry logic for API failures
        """
        # TODO: Implement live Azure OpenAI integration
        #
        # from openai import AzureOpenAI
        #
        # client = AzureOpenAI(
        #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        #     api_key=os.getenv("AZURE_OPENAI_KEY"),
        #     api_version="2024-02-01"
        # )
        #
        # system_prompt = """You are a case triage analyst for Carrier HVAC systems.
        # Analyze the customer case and extract:
        # 1. Issue type (HVAC, Controls, Parts, Installation, Warranty, Maintenance, Other)
        # 2. Urgency level and factors
        # 3. Product references (models, serial numbers, error codes)
        # 4. Symptoms described
        # 5. Customer sentiment
        # 6. What the customer is asking for
        #
        # Return structured JSON output."""
        #
        # response = client.chat.completions.create(
        #     model=self.config["model"],
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": f"Subject: {subject}\n\nDescription: {description}"}
        #     ],
        #     temperature=self.config["temperature"],
        #     response_format={"type": "json_object"}
        # )
        
        return {
            "action": action,
            "status": "not_implemented",
            "message": "Live Azure OpenAI integration not yet configured. Set use_mock_data=True for demo."
        }
