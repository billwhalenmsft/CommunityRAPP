"""
Agent: WarrantyLookupAgent
Purpose: Checks warranty coverage, expiration dates, and claim eligibility from ERP system
Data Sources: SAP ERP Warranty Module, Product Registration Database
Demo Mode: Uses stubbed data - replace with live API calls for production

Integration Points:
- SAP S/4HANA: Warranty Management module (API_WARRANTY_SRV)
- Product Database: Registration and serial number lookup
- Claims System: Warranty claim eligibility and history

Production Implementation Notes:
1. Replace STUBBED_DATA with SAP OData API calls
2. Implement serial number validation against product database
3. Add claim eligibility rules engine
4. Cache warranty data with appropriate TTL
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# =============================================================================
# STUBBED DATA - Mirrors SAP Warranty Management API Response Structure
# Production: Replace with actual API calls to SAP S/4HANA
#
# SAP API_WARRANTY_SRV Entity Structure:
#   WarrantyContract: ContractID, ProductID, SerialNumber, StartDate, EndDate, CoverageType
#   WarrantyClaim: ClaimID, ContractID, Status, CreatedDate, ResolutionDate
#
# OData Endpoint: /sap/opu/odata/sap/API_WARRANTY_SRV/A_WarrantyContract
# =============================================================================
STUBBED_WARRANTIES = {
    "registered_products": [
        {
            # Mirrors SAP WarrantyContract entity
            "warranty_id": "WRN-2024-78456",
            "serial_number": "XR-78456",
            "product_id": "PRD-COMP-500",
            "product_name": "Industrial Compressor XR-500",
            "product_category": "Air Compressors",
            "purchase_date": "2024-06-15",
            "registration_date": "2024-06-18",
            "warranty_start": "2024-06-15",
            "warranty_end": "2027-06-15",
            "coverage_type": "full",
            "coverage_description": "Full Parts & Labor Coverage",
            "status": "active",
            "days_remaining": 891,
            "extended_eligible": True,
            "extended_price": 299.99,
            "claims_history": []
        },
        {
            "warranty_id": "WRN-2024-34521",
            "serial_number": "DS-34521",
            "product_id": "PRD-DIAG-PRO",
            "product_name": "Diagnostic Scanner Pro",
            "product_category": "Diagnostic Equipment",
            "purchase_date": "2024-08-20",
            "registration_date": "2024-08-22",
            "warranty_start": "2024-08-20",
            "warranty_end": "2026-08-20",
            "coverage_type": "parts_only",
            "coverage_description": "Parts Only Coverage",
            "status": "active",
            "days_remaining": 592,
            "extended_eligible": True,
            "extended_price": 149.99,
            "claims_history": []
        },
        {
            "warranty_id": "WRN-2023-99012",
            "serial_number": "LS-99012",
            "product_id": "PRD-LIFT-9000",
            "product_name": "Lift System 9000",
            "product_category": "Shop Equipment",
            "purchase_date": "2023-03-10",
            "registration_date": "2023-03-12",
            "warranty_start": "2023-03-10",
            "warranty_end": "2026-03-10",
            "coverage_type": "full",
            "coverage_description": "Full Parts & Labor Coverage",
            "status": "active",
            "days_remaining": 428,
            "extended_eligible": True,
            "extended_price": 499.99,
            "claims_history": [
                {
                    "claim_id": "CLM-2024-001",
                    "date": "2024-09-15",
                    "issue": "Hydraulic seal replacement",
                    "status": "resolved",
                    "resolution": "Seal replaced under warranty"
                }
            ]
        },
        {
            "warranty_id": "WRN-2023-45678",
            "serial_number": "PT-45678",
            "product_id": "PRD-PNEU-SET",
            "product_name": "Pneumatic Tool Set Pro",
            "product_category": "Air Tools",
            "purchase_date": "2023-08-15",
            "registration_date": "2023-08-17",
            "warranty_start": "2023-08-15",
            "warranty_end": "2025-08-15",
            "coverage_type": "full",
            "coverage_description": "Full Parts & Labor Coverage",
            "status": "active",
            "days_remaining": 226,
            "expiring_soon": True,
            "extended_eligible": True,
            "extended_price": 89.99,
            "extended_discount": 0.15,
            "claims_history": []
        },
        {
            "warranty_id": "WRN-2023-67890",
            "serial_number": "IW-67890",
            "product_id": "PRD-IMPACT-PRO",
            "product_name": "Impact Wrench Pro",
            "product_category": "Air Tools",
            "purchase_date": "2023-09-20",
            "registration_date": "2023-09-22",
            "warranty_start": "2023-09-20",
            "warranty_end": "2025-09-20",
            "coverage_type": "full",
            "coverage_description": "Full Parts & Labor Coverage",
            "status": "active",
            "days_remaining": 257,
            "expiring_soon": True,
            "extended_eligible": True,
            "extended_price": 79.99,
            "extended_discount": 0.15,
            "claims_history": []
        }
    ],
    "coverage_summary": {
        "total_registered": 8,
        "active_warranties": 8,
        "expiring_90_days": 0,
        "expiring_soon": 2,
        "extended_eligible": 5,
        "total_coverage_value": 15847.00
    },
    "coverage_types": {
        "full": {
            "name": "Full Parts & Labor",
            "parts_covered": True,
            "labor_covered": True,
            "on_site_service": True,
            "loaner_available": True
        },
        "parts_only": {
            "name": "Parts Only",
            "parts_covered": True,
            "labor_covered": False,
            "on_site_service": False,
            "loaner_available": False
        },
        "limited": {
            "name": "Limited Coverage",
            "parts_covered": True,
            "labor_covered": False,
            "on_site_service": False,
            "loaner_available": False,
            "exclusions": ["wear items", "consumables", "damage from misuse"]
        }
    }
}


class WarrantyLookupAgent(BasicAgent):
    """
    Checks warranty coverage, expiration dates, and claim eligibility.

    Integration Points:
    - SAP S/4HANA: Warranty Management module (API_WARRANTY_SRV)
    - Product Database: Serial number validation and product info
    - Claims System: Claim history and eligibility rules

    Demo Mode: Returns stubbed data matching SAP API response structures
    Production: Connect to live SAP OData APIs

    SAP OData Query Examples (for production):
        GET /sap/opu/odata/sap/API_WARRANTY_SRV/A_WarrantyContract
            ?$filter=SerialNumber eq 'XR-78456'
            &$expand=to_Claims

        GET /sap/opu/odata/sap/API_WARRANTY_SRV/A_WarrantyContract
            ?$filter=DealerID eq 'ACC-001234' and Status eq 'active'
    """

    def __init__(self):
        self.name = 'WarrantyLookup'
        self.metadata = {
            "name": self.name,
            "description": "Checks warranty coverage, expiration dates, claim history, and eligibility for extended warranties. Can look up by serial number or show all warranties for a dealer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'get_warranty_status' for all warranties, 'lookup_serial' for specific product, 'check_claim_eligibility' for claim info",
                        "enum": ["get_warranty_status", "lookup_serial", "check_claim_eligibility"]
                    },
                    "dealer_id": {
                        "type": "string",
                        "description": "The dealer account ID"
                    },
                    "serial_number": {
                        "type": "string",
                        "description": "Product serial number to look up"
                    },
                    "product_id": {
                        "type": "string",
                        "description": "Product ID for warranty lookup"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute warranty lookup logic with stubbed data."""
        action = kwargs.get('action', 'get_warranty_status')
        dealer_id = kwargs.get('dealer_id', 'ACC-001234')
        serial_number = kwargs.get('serial_number')

        try:
            if action == 'get_warranty_status':
                result = self._get_warranty_status(dealer_id)
            elif action == 'lookup_serial':
                result = self._lookup_serial(serial_number)
            elif action == 'check_claim_eligibility':
                result = self._check_claim_eligibility(serial_number)
            else:
                result = {"error": f"Unknown action: {action}"}

            return json.dumps(result, indent=2)

        except Exception as e:
            logging.error(f"WarrantyLookupAgent error: {e}")
            return json.dumps({"error": str(e), "demo_mode": True})

    def _get_warranty_status(self, dealer_id: str) -> Dict:
        """
        Get all warranty coverage for a dealer.

        Production Implementation:
            1. Query SAP API_WARRANTY_SRV for dealer's warranties
            2. Calculate days remaining for each
            3. Identify expiring soon items
            4. Check extended warranty eligibility
        """
        # Demo mode: Return stubbed data
        active_warranties = []
        expiring_soon = []

        for product in STUBBED_WARRANTIES["registered_products"]:
            warranty_info = {
                "product": product["product_name"],
                "serial": product["serial_number"],
                "purchased": product["purchase_date"],
                "expires": product["warranty_end"],
                "coverage": product["coverage_type"],
                "days_remaining": product["days_remaining"]
            }
            active_warranties.append(warranty_info)

            if product.get("expiring_soon"):
                expiring_soon.append({
                    "product": product["product_name"],
                    "expires": product["warranty_end"],
                    "days_left": product["days_remaining"],
                    "extend_price": product.get("extended_price"),
                    "discount": product.get("extended_discount", 0)
                })

        return {
            "status": "success",
            "coverage_summary": STUBBED_WARRANTIES["coverage_summary"],
            "active_warranties": active_warranties,
            "expiring_soon": expiring_soon,
            "source": "SAP ERP Warranty + Product Database",
            "demo_mode": True
        }

    def _lookup_serial(self, serial_number: str) -> Dict:
        """
        Look up warranty by serial number.

        Production Implementation:
            1. Query SAP by serial number
            2. Validate serial against product database
            3. Return full warranty details with claims history
        """
        # Demo mode: Find in stubbed data
        for product in STUBBED_WARRANTIES["registered_products"]:
            if product["serial_number"] == serial_number:
                return {
                    "status": "success",
                    "warranty": product,
                    "coverage_details": STUBBED_WARRANTIES["coverage_types"].get(
                        product["coverage_type"], {}
                    ),
                    "source": "SAP Warranty Management",
                    "demo_mode": True
                }

        # Return first product if not found (demo fallback)
        return {
            "status": "success",
            "warranty": STUBBED_WARRANTIES["registered_products"][0],
            "coverage_details": STUBBED_WARRANTIES["coverage_types"]["full"],
            "source": "SAP Warranty Management",
            "demo_mode": True
        }

    def _check_claim_eligibility(self, serial_number: str) -> Dict:
        """
        Check if a product is eligible for warranty claim.

        Production Implementation:
            1. Verify warranty is active
            2. Check claim history for patterns
            3. Validate against exclusions
            4. Return eligibility with next steps
        """
        # Demo mode: Return eligibility info
        for product in STUBBED_WARRANTIES["registered_products"]:
            if product["serial_number"] == serial_number or serial_number is None:
                coverage = STUBBED_WARRANTIES["coverage_types"].get(
                    product["coverage_type"], {}
                )
                return {
                    "status": "success",
                    "eligible": product["status"] == "active",
                    "product": product["product_name"],
                    "serial": product["serial_number"],
                    "warranty_status": product["status"],
                    "days_remaining": product["days_remaining"],
                    "coverage": coverage,
                    "claims_history": product.get("claims_history", []),
                    "claim_options": [
                        {"type": "replacement", "timeline": "2-3 business days"},
                        {"type": "on_site_repair", "timeline": "Schedule appointment"},
                        {"type": "depot_repair", "timeline": "5-7 business days"}
                    ],
                    "source": "SAP Warranty + Claims System",
                    "demo_mode": True
                }

        return {
            "status": "error",
            "message": "Serial number not found",
            "demo_mode": True
        }

    # =========================================================================
    # PRODUCTION IMPLEMENTATION STUBS
    # Uncomment and implement for live SAP integration
    # =========================================================================

    # def _call_sap_warranty_api(self, serial_number: str) -> Dict:
    #     """
    #     Query SAP Warranty Management OData API.
    #
    #     Endpoint: /sap/opu/odata/sap/API_WARRANTY_SRV/A_WarrantyContract
    #     Auth: OAuth 2.0 / SAP Principal Propagation
    #
    #     Example:
    #         import requests
    #         headers = {
    #             "Authorization": f"Bearer {access_token}",
    #             "Accept": "application/json"
    #         }
    #         url = f"{sap_base_url}/sap/opu/odata/sap/API_WARRANTY_SRV/A_WarrantyContract"
    #         params = {"$filter": f"SerialNumber eq '{serial_number}'"}
    #         response = requests.get(url, headers=headers, params=params)
    #         return response.json()
    #     """
    #     pass

    # def _validate_serial_number(self, serial_number: str) -> bool:
    #     """
    #     Validate serial number format and existence in product database.
    #
    #     Returns:
    #         True if valid serial number, False otherwise
    #     """
    #     pass


# =============================================================================
# MODULE TEST - Run directly to verify stubbed data works
# =============================================================================
if __name__ == "__main__":
    agent = WarrantyLookupAgent()

    print("=== Testing WarrantyLookupAgent ===\n")

    # Test warranty status
    print("1. Warranty Status:")
    result = agent.perform(action="get_warranty_status", dealer_id="ACC-001234")
    print(result)
    print()

    # Test serial lookup
    print("2. Serial Lookup:")
    result = agent.perform(action="lookup_serial", serial_number="XR-78456")
    print(result)
    print()

    # Test claim eligibility
    print("3. Claim Eligibility:")
    result = agent.perform(action="check_claim_eligibility", serial_number="LS-99012")
    print(result)
