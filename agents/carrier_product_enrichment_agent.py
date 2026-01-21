"""
Agent: CarrierProductEnrichmentAgent
Purpose: Enriches case with product/install base metadata
Customer: Carrier
Status: STUBBED - Uses mock data until internal APIs are available

This agent provides:
- Product lookup by model/serial number
- Install base information for customer accounts
- Warranty status and coverage details
- Service history for equipment
- Known issues and service bulletins

Future API Integration Points (STUBBED):
- Product API: [FUTURE: https://api.carrier.com/products/v1/lookup]
- Install Base API: [FUTURE: https://api.carrier.com/installbase/v1/query]
- Warranty API: [FUTURE: https://api.carrier.com/warranty/v1/status]
- Service History API: [FUTURE: https://api.carrier.com/service/v1/history]
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# =============================================================================
# CONFIGURATION - STUBBED FOR FUTURE API INTEGRATION
# =============================================================================
PRODUCT_API_CONFIG = {
    "product_lookup_url": "[FUTURE: https://api.carrier.com/products/v1/lookup]",
    "install_base_url": "[FUTURE: https://api.carrier.com/installbase/v1/query]",
    "warranty_url": "[FUTURE: https://api.carrier.com/warranty/v1/status]",
    "service_history_url": "[FUTURE: https://api.carrier.com/service/v1/history]",
    "use_mock_data": True  # Set to False when APIs are available
}

# =============================================================================
# STUBBED PRODUCT DATA
# This data simulates what would come from Carrier internal APIs
# =============================================================================
STUBBED_PRODUCTS = {
    "50XC": {
        "model": "50XC",
        "full_name": "Carrier 50XC WeatherMaker Rooftop Unit",
        "product_line": "Rooftop Units",
        "category": "Commercial HVAC",
        "cooling_capacity_tons": "3-25",
        "heating_type": "Gas/Electric",
        "typical_applications": ["Commercial buildings", "Retail", "Light industrial"],
        "support_tier": "Standard",
        "documentation_url": "https://carrier.com/docs/50XC"
    },
    "30RB": {
        "model": "30RB",
        "full_name": "Carrier 30RB AquaSnap Air-Cooled Chiller",
        "product_line": "Chillers",
        "category": "Commercial HVAC",
        "cooling_capacity_tons": "30-180",
        "refrigerant": "R-410A",
        "typical_applications": ["Office buildings", "Hospitals", "Data centers"],
        "support_tier": "Premium",
        "documentation_url": "https://carrier.com/docs/30RB"
    },
    "38AUD": {
        "model": "38AUD",
        "full_name": "Carrier 38AUD Infinity Split System",
        "product_line": "Split Systems",
        "category": "Commercial HVAC",
        "cooling_capacity_tons": "2-5",
        "seer": "Up to 21",
        "typical_applications": ["Small commercial", "Office suites", "Retail"],
        "support_tier": "Standard",
        "documentation_url": "https://carrier.com/docs/38AUD"
    },
    "i-Vu": {
        "model": "i-Vu",
        "full_name": "Carrier i-Vu Building Automation System",
        "product_line": "Controls",
        "category": "Building Automation",
        "protocols": ["BACnet", "Modbus", "LonWorks"],
        "typical_applications": ["Building management", "HVAC control", "Energy management"],
        "support_tier": "Premium",
        "documentation_url": "https://carrier.com/docs/i-Vu"
    }
}

STUBBED_SERIAL_DATABASE = {
    "2419G12345": {
        "serial": "2419G12345",
        "model": "50XC",
        "manufacture_date": "2019-04-15",
        "install_date": "2019-06-15",
        "install_location": "Phoenix, AZ",
        "warranty_start": "2019-06-15",
        "warranty_end": "2024-06-15",
        "extended_warranty_end": None,
        "service_contract": False,
        "age_years": 6.5
    },
    "0918E54321": {
        "serial": "0918E54321",
        "model": "30RB 100",
        "manufacture_date": "2022-01-10",
        "install_date": "2022-03-15",
        "install_location": "Phoenix, AZ",
        "warranty_start": "2022-03-15",
        "warranty_end": "2027-03-15",
        "extended_warranty_end": None,
        "service_contract": True,
        "age_years": 3.8
    },
    "IVU-2023-001": {
        "serial": "IVU-2023-001",
        "model": "i-Vu",
        "manufacture_date": "2023-06-01",
        "install_date": "2023-08-01",
        "install_location": "Phoenix, AZ",
        "warranty_start": "2023-08-01",
        "warranty_end": "2026-08-01",
        "extended_warranty_end": None,
        "service_contract": True,
        "age_years": 2.4
    }
}

STUBBED_SERVICE_HISTORY = {
    "2419G12345": [
        {
            "date": "2024-09-15",
            "type": "Preventive Maintenance",
            "issue": "Scheduled quarterly maintenance",
            "resolution": "Replaced filters, cleaned coils, checked refrigerant",
            "technician": "Mike Johnson",
            "cost": 450.00
        },
        {
            "date": "2023-07-22",
            "type": "Repair",
            "issue": "Unit not cooling - E47 error",
            "resolution": "Found refrigerant leak at service valve, repaired and recharged",
            "technician": "Sarah Chen",
            "cost": 875.00
        },
        {
            "date": "2022-03-10",
            "type": "Preventive Maintenance",
            "issue": "Annual maintenance",
            "resolution": "Full system check, belt replacement, lubrication",
            "technician": "Tom Williams",
            "cost": 525.00
        }
    ],
    "0918E54321": [
        {
            "date": "2024-11-01",
            "type": "Preventive Maintenance",
            "issue": "Quarterly service per contract",
            "resolution": "All checks passed, system operating normally",
            "technician": "Lisa Park",
            "cost": 0.00  # Covered by service contract
        }
    ]
}

STUBBED_KNOWN_ISSUES = {
    "50XC": [
        {
            "bulletin_id": "SB-2024-047",
            "title": "E47 Error - TXV Sensing Bulb",
            "description": "Some 50XC units manufactured 2018-2020 may experience E47 errors due to TXV sensing bulb migration",
            "affected_serials": "Serials starting with 2418-2420",
            "severity": "Medium",
            "recommended_action": "Verify TXV bulb position, secure with thermal mastic if loose"
        },
        {
            "bulletin_id": "SB-2023-112",
            "title": "Condenser Fan Motor Update",
            "description": "Updated condenser fan motor available for improved reliability",
            "affected_serials": "All",
            "severity": "Low",
            "recommended_action": "Consider motor upgrade during next scheduled maintenance"
        }
    ],
    "30RB": [
        {
            "bulletin_id": "SB-2024-089",
            "title": "Compressor Startup Vibration",
            "description": "Some 30RB units may exhibit startup vibration due to compressor mount wear",
            "affected_serials": "Serials with manufacture date 2020-2022",
            "severity": "Medium",
            "recommended_action": "Inspect compressor mounts, replace isolation pads if worn"
        }
    ],
    "i-Vu": [
        {
            "bulletin_id": "SB-2024-015",
            "title": "BACnet Communication Timeout",
            "description": "i-Vu controllers may experience communication timeouts with certain third-party BMS",
            "affected_serials": "Firmware versions 7.0-7.2",
            "severity": "Low",
            "recommended_action": "Update to firmware 7.3 or later"
        }
    ]
}


class CarrierProductEnrichmentAgent(BasicAgent):
    """
    Enriches case data with product and install base information.

    STATUS: STUBBED - Using mock data until internal APIs are available

    Capabilities:
    - Product lookup by model number
    - Serial number validation and details
    - Warranty status determination
    - Service history retrieval
    - Known issues/service bulletin lookup

    Demo Mode: Returns realistic mock data
    Production: Will connect to Carrier internal APIs
    """

    def __init__(self):
        self.name = 'CarrierProductEnrichment'
        self.metadata = {
            "name": self.name,
            "description": "Enriches case with product details, warranty status, service history, and known issues. STUBBED for demo - uses mock data. Part of the Carrier Case Triage Agent Swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Enrichment action to perform",
                        "enum": [
                            "lookup_product",
                            "get_install_base",
                            "check_warranty_status",
                            "get_service_history",
                            "get_known_issues",
                            "full_enrichment"
                        ]
                    },
                    "model": {
                        "type": "string",
                        "description": "Product model number (e.g., 50XC, 30RB)"
                    },
                    "serial": {
                        "type": "string",
                        "description": "Equipment serial number"
                    },
                    "account_id": {
                        "type": "string",
                        "description": "Customer account ID for install base lookup"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = PRODUCT_API_CONFIG

    def perform(self, **kwargs) -> str:
        """Execute product enrichment."""
        action = kwargs.get('action', 'full_enrichment')

        try:
            # Always use mock data until APIs are available
            result = self._handle_mock_request(action, **kwargs)
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"CarrierProductEnrichment error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "status": "failed"
            }, indent=2)

    def _handle_mock_request(self, action: str, **kwargs) -> Dict:
        """Handle request with stubbed data."""
        model = kwargs.get('model', '')
        serial = kwargs.get('serial', '')
        account_id = kwargs.get('account_id', '')

        # Normalize model for lookup
        model_key = self._normalize_model(model)

        if action == "full_enrichment":
            return self._full_enrichment(model_key, serial, account_id)
        
        elif action == "lookup_product":
            return self._lookup_product(model_key)
        
        elif action == "get_install_base":
            return self._get_install_base(account_id)
        
        elif action == "check_warranty_status":
            return self._check_warranty(serial)
        
        elif action == "get_service_history":
            return self._get_service_history(serial)
        
        elif action == "get_known_issues":
            return self._get_known_issues(model_key, serial)
        
        else:
            return {
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _full_enrichment(self, model: str, serial: str, account_id: str) -> Dict:
        """Perform full product enrichment."""
        product_info = STUBBED_PRODUCTS.get(model, {})
        serial_info = STUBBED_SERIAL_DATABASE.get(serial, {})
        service_history = STUBBED_SERVICE_HISTORY.get(serial, [])
        known_issues = STUBBED_KNOWN_ISSUES.get(model, [])

        # Calculate warranty status
        warranty_status = "Unknown"
        warranty_expiry = None
        if serial_info:
            warranty_end = serial_info.get('warranty_end')
            if warranty_end:
                warranty_expiry = warranty_end
                warranty_date = datetime.strptime(warranty_end, '%Y-%m-%d')
                if warranty_date > datetime.now():
                    warranty_status = "Active"
                else:
                    warranty_status = "Expired"
                    # Check extended
                    ext_end = serial_info.get('extended_warranty_end')
                    if ext_end:
                        ext_date = datetime.strptime(ext_end, '%Y-%m-%d')
                        if ext_date > datetime.now():
                            warranty_status = "Extended"
                            warranty_expiry = ext_end

        return {
            "action": "full_enrichment",
            "status": "success",
            "source": "MOCK_DATA",
            "_meta": {
                "note": "This data is STUBBED. Replace with live API when available.",
                "api_endpoints": self.config
            },
            "product": {
                "model": model,
                "full_name": product_info.get('full_name', f"Carrier {model}"),
                "product_line": product_info.get('product_line', 'Unknown'),
                "category": product_info.get('category', 'HVAC'),
                "support_tier": product_info.get('support_tier', 'Standard'),
                "found": bool(product_info)
            },
            "serial_info": {
                "serial": serial,
                "manufacture_date": serial_info.get('manufacture_date'),
                "install_date": serial_info.get('install_date'),
                "install_location": serial_info.get('install_location'),
                "age_years": serial_info.get('age_years'),
                "has_service_contract": serial_info.get('service_contract', False),
                "found": bool(serial_info)
            },
            "warranty": {
                "status": warranty_status,
                "expiry_date": warranty_expiry,
                "coverage_type": "Standard Parts & Labor" if warranty_status == "Active" else None
            },
            "service_history": {
                "total_records": len(service_history),
                "recent_services": service_history[:3],
                "total_service_cost": sum(s.get('cost', 0) for s in service_history)
            },
            "known_issues": {
                "bulletins_found": len(known_issues),
                "issues": known_issues,
                "has_relevant_bulletins": len(known_issues) > 0
            },
            "customer_context": {
                "account_id": account_id,
                "account_tier": "Enterprise" if account_id else "Unknown",
                "contract_type": "Full Service" if serial_info.get('service_contract') else "Time & Materials"
            }
        }

    def _lookup_product(self, model: str) -> Dict:
        """Look up product by model number."""
        product = STUBBED_PRODUCTS.get(model)
        
        if product:
            return {
                "action": "lookup_product",
                "status": "success",
                "source": "MOCK_DATA",
                "model": model,
                "product": product,
                "found": True
            }
        else:
            return {
                "action": "lookup_product",
                "status": "success",
                "source": "MOCK_DATA",
                "model": model,
                "product": None,
                "found": False,
                "message": f"Product model '{model}' not found in database"
            }

    def _get_install_base(self, account_id: str) -> Dict:
        """Get installed equipment for an account."""
        # Mock install base data
        install_base = [
            {
                "serial": "2419G12345",
                "model": "50XC",
                "location": "Building A - Roof",
                "install_date": "2019-06-15",
                "status": "Active"
            },
            {
                "serial": "2420H67890",
                "model": "50XC",
                "location": "Building B - Roof",
                "install_date": "2020-03-22",
                "status": "Active"
            },
            {
                "serial": "0918E54321",
                "model": "30RB 100",
                "location": "Central Plant",
                "install_date": "2022-03-15",
                "status": "Active"
            }
        ]

        return {
            "action": "get_install_base",
            "status": "success",
            "source": "MOCK_DATA",
            "account_id": account_id,
            "equipment_count": len(install_base),
            "install_base": install_base
        }

    def _check_warranty(self, serial: str) -> Dict:
        """Check warranty status for a serial number."""
        serial_info = STUBBED_SERIAL_DATABASE.get(serial)
        
        if not serial_info:
            return {
                "action": "check_warranty_status",
                "status": "success",
                "source": "MOCK_DATA",
                "serial": serial,
                "warranty": {
                    "status": "Unknown",
                    "message": "Serial number not found in database"
                }
            }

        warranty_end = serial_info.get('warranty_end')
        warranty_status = "Unknown"
        days_remaining = None

        if warranty_end:
            warranty_date = datetime.strptime(warranty_end, '%Y-%m-%d')
            if warranty_date > datetime.now():
                warranty_status = "Active"
                days_remaining = (warranty_date - datetime.now()).days
            else:
                warranty_status = "Expired"
                days_remaining = 0

        return {
            "action": "check_warranty_status",
            "status": "success",
            "source": "MOCK_DATA",
            "serial": serial,
            "warranty": {
                "status": warranty_status,
                "start_date": serial_info.get('warranty_start'),
                "end_date": warranty_end,
                "days_remaining": days_remaining,
                "extended_end_date": serial_info.get('extended_warranty_end'),
                "has_service_contract": serial_info.get('service_contract', False)
            }
        }

    def _get_service_history(self, serial: str) -> Dict:
        """Get service history for equipment."""
        history = STUBBED_SERVICE_HISTORY.get(serial, [])

        return {
            "action": "get_service_history",
            "status": "success",
            "source": "MOCK_DATA",
            "serial": serial,
            "history": {
                "total_records": len(history),
                "services": history,
                "total_cost": sum(s.get('cost', 0) for s in history),
                "last_service_date": history[0].get('date') if history else None
            }
        }

    def _get_known_issues(self, model: str, serial: str) -> Dict:
        """Get known issues and service bulletins."""
        issues = STUBBED_KNOWN_ISSUES.get(model, [])
        
        # Filter for relevant issues based on serial if provided
        relevant_issues = []
        for issue in issues:
            # In real implementation, would check serial ranges
            relevant_issues.append(issue)

        return {
            "action": "get_known_issues",
            "status": "success",
            "source": "MOCK_DATA",
            "model": model,
            "serial": serial,
            "known_issues": {
                "bulletins_count": len(relevant_issues),
                "bulletins": relevant_issues,
                "has_critical_bulletins": any(i.get('severity') == 'High' for i in relevant_issues)
            }
        }

    def _normalize_model(self, model: str) -> str:
        """Normalize model number for lookup."""
        if not model:
            return ""
        
        # Remove common variations
        normalized = model.upper().strip()
        
        # Map common variations to canonical names
        model_aliases = {
            "50XC": ["50XC", "50-XC", "50 XC"],
            "30RB": ["30RB", "30-RB", "30 RB", "30RB 100"],
            "38AUD": ["38AUD", "38-AUD", "38 AUD"],
            "i-Vu": ["I-VU", "IVU", "I VU", "CARRIER I-VU"]
        }
        
        for canonical, aliases in model_aliases.items():
            for alias in aliases:
                if alias in normalized:
                    return canonical
        
        return normalized
