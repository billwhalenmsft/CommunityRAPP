"""
Agent: ProductRegistrationAgent
Purpose: Handles product registration, warranty activation, and registration history
Data Sources: Product Database, Warranty System, Dealer Portal API
Demo Mode: Uses stubbed data - replace with live API calls for production

Integration Points:
- Product Database: Product catalog and serial number validation
- Warranty System: Warranty activation upon registration
- Dealer Portal API: Registration submission and history

Production Implementation Notes:
1. Implement serial number format validation per product line
2. Add duplicate registration detection
3. Integrate with warranty activation workflow
4. Support bulk registration via CSV upload
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# =============================================================================
# STUBBED DATA - Mirrors Product Registration System API Structure
# Production: Replace with actual API calls to Product Database and Warranty System
#
# Registration API Response Structure:
#   registration_id, serial_number, product_id, dealer_id, purchase_date,
#   registration_date, warranty_activated, warranty_end_date
# =============================================================================
STUBBED_REGISTRATION_DATA = {
    "registration_history": [
        {
            "registration_id": "REG-2024-001234",
            "serial_number": "XR-78456",
            "product_id": "PRD-COMP-500",
            "product_name": "Industrial Compressor XR-500",
            "dealer_id": "ACC-001234",
            "purchase_date": "2024-06-15",
            "registration_date": "2024-06-18",
            "registration_method": "online_portal",
            "warranty_activated": True,
            "warranty_end_date": "2027-06-15",
            "status": "confirmed"
        },
        {
            "registration_id": "REG-2024-001235",
            "serial_number": "DS-34521",
            "product_id": "PRD-DIAG-PRO",
            "product_name": "Diagnostic Scanner Pro",
            "dealer_id": "ACC-001234",
            "purchase_date": "2024-08-20",
            "registration_date": "2024-08-22",
            "registration_method": "online_portal",
            "warranty_activated": True,
            "warranty_end_date": "2026-08-20",
            "status": "confirmed"
        }
    ],
    "pending_auto_registration": [
        {
            "order_id": "ORD-2026-08471",
            "products": [
                {"product_name": "Brake Rotor Set - Premium", "serial_pending": True},
                {"product_name": "Ceramic Brake Pad Kit", "serial_pending": True},
                {"product_name": "Wheel Bearing Assembly", "serial_pending": True}
            ],
            "auto_register_on": "delivery_confirmation",
            "estimated_delivery": "2026-01-08"
        }
    ],
    "product_catalog": {
        "PRD-COMP-500": {
            "name": "Industrial Compressor XR-500",
            "category": "Air Compressors",
            "serial_format": "XR-NNNNN",
            "warranty_period_months": 36,
            "warranty_type": "full",
            "registration_required_days": 30
        },
        "PRD-DIAG-PRO": {
            "name": "Diagnostic Scanner Pro",
            "category": "Diagnostic Equipment",
            "serial_format": "DS-NNNNN",
            "warranty_period_months": 24,
            "warranty_type": "parts_only",
            "registration_required_days": 30
        },
        "PRD-TORQUE-PRO": {
            "name": "Torque Wrench Pro",
            "category": "Hand Tools",
            "serial_format": "TW-YYYY-NNNNN",
            "warranty_period_months": 24,
            "warranty_type": "full",
            "registration_required_days": 30
        }
    },
    "registration_methods": [
        {
            "method": "quick_register",
            "name": "Quick Register",
            "description": "Share model + serial number directly",
            "estimated_time": "30 seconds",
            "fields_required": ["product_model", "serial_number", "purchase_date"]
        },
        {
            "method": "qr_scan",
            "name": "Scan QR Code",
            "description": "Use phone camera on product QR code",
            "estimated_time": "15 seconds",
            "fields_required": ["qr_code_data"]
        },
        {
            "method": "receipt_upload",
            "name": "Receipt Upload",
            "description": "Upload photo of purchase receipt for auto-extraction",
            "estimated_time": "45 seconds",
            "fields_required": ["receipt_image"]
        },
        {
            "method": "auto_registration",
            "name": "Auto-Registration",
            "description": "Products from dealer orders auto-register on delivery",
            "estimated_time": "Automatic",
            "fields_required": []
        }
    ],
    "registration_benefits": [
        "Warranty activation (required within 30 days of purchase)",
        "Recall notifications and safety alerts",
        "Software and firmware update notifications",
        "Trade-in value tracking and upgrade offers",
        "Priority support access"
    ]
}


class ProductRegistrationAgent(BasicAgent):
    """
    Handles product registration, warranty activation, and registration history.

    Integration Points:
    - Product Database: Catalog lookup and serial validation
    - Warranty System: Automatic warranty activation
    - Dealer Portal API: Registration submission

    Demo Mode: Returns stubbed data
    Production: Connect to live product and warranty APIs
    """

    def __init__(self):
        self.name = 'ProductRegistration'
        self.metadata = {
            "name": self.name,
            "description": "Handles product registration, warranty activation, and provides registration history. Supports quick registration, QR scanning, and receipt upload.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'get_registration_options' for methods, 'register_product' to register, 'get_registration_history' for past registrations",
                        "enum": ["get_registration_options", "register_product", "get_registration_history", "validate_serial"]
                    },
                    "dealer_id": {
                        "type": "string",
                        "description": "The dealer account ID"
                    },
                    "serial_number": {
                        "type": "string",
                        "description": "Product serial number"
                    },
                    "product_model": {
                        "type": "string",
                        "description": "Product model name or ID"
                    },
                    "purchase_date": {
                        "type": "string",
                        "description": "Date of purchase (YYYY-MM-DD)"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute product registration logic with stubbed data."""
        action = kwargs.get('action', 'get_registration_options')
        dealer_id = kwargs.get('dealer_id', 'ACC-001234')
        serial_number = kwargs.get('serial_number')
        product_model = kwargs.get('product_model')
        purchase_date = kwargs.get('purchase_date')

        try:
            if action == 'get_registration_options':
                result = self._get_registration_options()
            elif action == 'register_product':
                result = self._register_product(dealer_id, serial_number, product_model, purchase_date)
            elif action == 'get_registration_history':
                result = self._get_registration_history(dealer_id)
            elif action == 'validate_serial':
                result = self._validate_serial(serial_number, product_model)
            else:
                result = {"error": f"Unknown action: {action}"}

            return json.dumps(result, indent=2)

        except Exception as e:
            logging.error(f"ProductRegistrationAgent error: {e}")
            return json.dumps({"error": str(e), "demo_mode": True})

    def _get_registration_options(self) -> Dict:
        """
        Get available registration methods and benefits.

        Production Implementation:
            1. Return registration methods based on dealer capabilities
            2. Check for any pending auto-registrations
        """
        return {
            "status": "success",
            "registration_methods": STUBBED_REGISTRATION_DATA["registration_methods"],
            "benefits": STUBBED_REGISTRATION_DATA["registration_benefits"],
            "pending_auto_registration": STUBBED_REGISTRATION_DATA["pending_auto_registration"],
            "source": "Product Database + Registration API",
            "demo_mode": True
        }

    def _register_product(self, dealer_id: str, serial_number: str, product_model: str, purchase_date: str) -> Dict:
        """
        Register a new product.

        Production Implementation:
            1. Validate serial number format
            2. Check for duplicate registration
            3. Verify product exists in catalog
            4. Create registration record
            5. Trigger warranty activation
        """
        # Demo mode: Simulate successful registration
        registration_id = f"REG-2026-{datetime.now().strftime('%H%M%S')}"
        warranty_end = (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d')

        return {
            "status": "success",
            "message": "Product registered successfully",
            "registration": {
                "registration_id": registration_id,
                "serial_number": serial_number or "TW-2026-45678",
                "product_model": product_model or "Torque Wrench Pro",
                "dealer_id": dealer_id,
                "purchase_date": purchase_date or datetime.now().strftime('%Y-%m-%d'),
                "registration_date": datetime.now().strftime('%Y-%m-%d'),
                "warranty_activated": True,
                "warranty_end_date": warranty_end
            },
            "next_steps": [
                "Warranty is now active",
                "You'll receive recall notifications via email",
                "Track this product in your registration history"
            ],
            "source": "Product Database + Warranty System",
            "demo_mode": True
        }

    def _get_registration_history(self, dealer_id: str) -> Dict:
        """
        Get registration history for dealer.

        Production Implementation:
            1. Query registration database by dealer ID
            2. Include warranty status for each
            3. Flag any pending registrations
        """
        return {
            "status": "success",
            "registrations": STUBBED_REGISTRATION_DATA["registration_history"],
            "pending_auto_registration": STUBBED_REGISTRATION_DATA["pending_auto_registration"],
            "total_registered": len(STUBBED_REGISTRATION_DATA["registration_history"]),
            "source": "Registration Database",
            "demo_mode": True
        }

    def _validate_serial(self, serial_number: str, product_model: str) -> Dict:
        """
        Validate serial number format for product.

        Production Implementation:
            1. Look up product in catalog
            2. Validate serial format against pattern
            3. Check if serial already registered
        """
        return {
            "status": "success",
            "valid": True,
            "serial_number": serial_number or "TW-2026-45678",
            "product_model": product_model or "Torque Wrench Pro",
            "already_registered": False,
            "format_valid": True,
            "source": "Product Database",
            "demo_mode": True
        }


# =============================================================================
# MODULE TEST
# =============================================================================
if __name__ == "__main__":
    agent = ProductRegistrationAgent()

    print("=== Testing ProductRegistrationAgent ===\n")

    print("1. Registration Options:")
    result = agent.perform(action="get_registration_options")
    print(result)
    print()

    print("2. Register Product:")
    result = agent.perform(
        action="register_product",
        serial_number="TW-2026-45678",
        product_model="Torque Wrench Pro",
        purchase_date="2026-01-06"
    )
    print(result)
