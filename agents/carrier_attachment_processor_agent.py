"""
Agent: CarrierAttachmentProcessorAgent
Purpose: Processes case attachments (images, PDFs, documents) to extract information
Customer: Carrier
AI Model: Azure OpenAI GPT-4o Vision for images, Azure Document Intelligence for docs
Demo Mode: Uses stubbed responses - replace with live AI calls for production

This agent handles:
- Image analysis (error codes, equipment photos, damage assessment)
- PDF/document text extraction
- Error code recognition from photos
- Structured data extraction from documents
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

# =============================================================================
# CONFIGURATION
# =============================================================================
PROCESSOR_CONFIG = {
    "use_mock_data": True,  # Set to False when Azure AI is configured
    "vision_model": "gpt-4o",
    "max_image_size_mb": 20,
    "supported_image_types": ["jpg", "jpeg", "png", "gif", "webp"],
    "supported_document_types": ["pdf", "docx", "xlsx", "csv", "txt"]
}

# Common Carrier error codes for recognition
CARRIER_ERROR_CODES = {
    "E47": {
        "description": "Low refrigerant charge or restriction in refrigerant circuit",
        "severity": "High",
        "action": "Check refrigerant levels, inspect for leaks, verify TXV operation"
    },
    "E48": {
        "description": "High head pressure - condenser issue",
        "severity": "Medium",
        "action": "Clean condenser coils, check condenser fan motor, verify airflow"
    },
    "E23": {
        "description": "Compressor overload protection",
        "severity": "High",
        "action": "Check compressor amp draw, verify voltage, inspect wiring"
    },
    "E15": {
        "description": "Indoor fan motor failure",
        "severity": "Medium",
        "action": "Check fan motor, inspect capacitor, verify control board signal"
    },
    "E61": {
        "description": "Communication fault - indoor/outdoor unit",
        "severity": "Medium",
        "action": "Check wiring between units, verify control board, reset system"
    },
    "E72": {
        "description": "Outdoor ambient sensor fault",
        "severity": "Low",
        "action": "Check sensor wiring, replace sensor if faulty"
    }
}


class CarrierAttachmentProcessorAgent(BasicAgent):
    """
    Processes case attachments to extract useful information.

    Capabilities:
    - Image analysis with GPT-4o Vision
    - Error code detection from photos
    - PDF text extraction
    - Document parsing (invoices, service records, manuals)
    - Equipment identification from images

    Demo Mode: Returns intelligent mock extractions
    Production: Uses Azure OpenAI Vision and Document Intelligence
    """

    def __init__(self):
        self.name = 'CarrierAttachmentProcessor'
        self.metadata = {
            "name": self.name,
            "description": "Processes case attachments (images, PDFs, documents) to extract error codes, equipment information, and relevant data. Part of the Carrier Case Triage Agent Swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Processing action to perform",
                        "enum": [
                            "process_attachments",
                            "extract_image_info",
                            "extract_document_text",
                            "analyze_error_codes",
                            "summarize_attachments"
                        ]
                    },
                    "attachments": {
                        "type": "array",
                        "description": "Array of attachment metadata from Salesforce",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Id": {"type": "string"},
                                "Name": {"type": "string"},
                                "ContentType": {"type": "string"},
                                "BodyLength": {"type": "integer"}
                            }
                        }
                    },
                    "attachment_id": {
                        "type": "string",
                        "description": "Single attachment ID for specific processing"
                    },
                    "image_data": {
                        "type": "string",
                        "description": "Base64 encoded image data for analysis"
                    },
                    "document_text": {
                        "type": "string",
                        "description": "Raw document text for processing"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.config = PROCESSOR_CONFIG

    def perform(self, **kwargs) -> str:
        """Execute attachment processing."""
        action = kwargs.pop('action', 'process_attachments')

        try:
            if self.config["use_mock_data"]:
                result = self._handle_mock_request(action, **kwargs)
            else:
                result = self._handle_live_request(action, **kwargs)

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logging.error(f"CarrierAttachmentProcessor error: {str(e)}")
            return json.dumps({
                "error": str(e),
                "action": action,
                "status": "failed"
            }, indent=2)

    def _handle_mock_request(self, action: str, **kwargs) -> Dict:
        """Handle request with mock responses."""
        attachments = kwargs.get('attachments', [])

        if action == "process_attachments":
            return self._mock_process_all(attachments)
        
        elif action == "extract_image_info":
            return self._mock_image_analysis(attachments)
        
        elif action == "extract_document_text":
            return self._mock_document_extraction(attachments)
        
        elif action == "analyze_error_codes":
            return self._mock_error_code_analysis(attachments)
        
        elif action == "summarize_attachments":
            return self._mock_summarize(attachments)
        
        else:
            return {
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    def _mock_process_all(self, attachments: List[Dict]) -> Dict:
        """Process all attachments and return combined results."""
        if not attachments:
            return {
                "action": "process_attachments",
                "status": "success",
                "source": "mock_data",
                "message": "No attachments to process",
                "findings": [],
                "error_codes": [],
                "documents_processed": 0
            }

        results = []
        all_findings = []
        error_codes_found = []
        
        for attachment in attachments:
            file_name = attachment.get('Name', '').lower()
            content_type = attachment.get('ContentType', '').lower()
            
            if any(ext in file_name for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                result = self._analyze_single_image(attachment)
                results.append(result)
                all_findings.extend(result.get('findings', []))
                error_codes_found.extend(result.get('error_codes', []))
                
            elif '.pdf' in file_name or 'pdf' in content_type:
                result = self._analyze_single_document(attachment)
                results.append(result)
                all_findings.extend(result.get('findings', []))
                
            elif '.mp4' in file_name or '.mov' in file_name or 'video' in content_type:
                result = self._analyze_video_stub(attachment)
                results.append(result)
                all_findings.extend(result.get('findings', []))
            
            else:
                results.append({
                    "attachment_id": attachment.get('Id'),
                    "name": attachment.get('Name'),
                    "status": "skipped",
                    "reason": "Unsupported file type"
                })

        return {
            "action": "process_attachments",
            "status": "success",
            "source": "mock_data",
            "attachments_processed": len([r for r in results if r.get('status') == 'processed']),
            "attachments_skipped": len([r for r in results if r.get('status') == 'skipped']),
            "findings": all_findings,
            "error_codes": error_codes_found,
            "detailed_results": results,
            "processing_time_ms": 1234
        }

    def _analyze_single_image(self, attachment: Dict) -> Dict:
        """Analyze a single image attachment."""
        file_name = attachment.get('Name', '').lower()
        
        findings = []
        error_codes = []
        equipment_identified = []
        
        # Mock analysis based on filename hints
        if 'error' in file_name or 'code' in file_name or 'e47' in file_name:
            error_codes.append({
                "code": "E47",
                "confidence": 0.95,
                "location_in_image": "center display panel",
                "details": CARRIER_ERROR_CODES.get("E47", {})
            })
            findings.append("Error code E47 detected on unit display panel")
            findings.append("Display shows low refrigerant warning indicator")
        
        if 'unit' in file_name or 'equipment' in file_name or 'photo' in file_name:
            equipment_identified.append({
                "type": "Rooftop Unit",
                "estimated_model": "50XC series",
                "condition": "Operational with warning indicator",
                "visible_issues": ["Warning light illuminated"]
            })
            findings.append("Rooftop unit identified - appears to be 50XC series")
            findings.append("Unit exterior appears in normal condition")
        
        if 'damage' in file_name:
            findings.append("Physical damage detected on condenser coil fins")
            findings.append("Recommend on-site inspection to assess damage extent")
        
        if 'leak' in file_name:
            findings.append("Possible oil staining visible near compressor - may indicate refrigerant leak")
        
        # Default findings if nothing specific
        if not findings:
            findings.append("Image processed - general equipment photo")
            findings.append("No specific issues or error codes detected in image")

        return {
            "attachment_id": attachment.get('Id'),
            "name": attachment.get('Name'),
            "type": "image",
            "status": "processed",
            "analysis": {
                "description": "HVAC equipment photo analysis",
                "error_codes": error_codes,
                "equipment_identified": equipment_identified,
                "findings": findings,
                "confidence": 0.85
            },
            "error_codes": error_codes
        }

    def _analyze_single_document(self, attachment: Dict) -> Dict:
        """Analyze a single document attachment."""
        file_name = attachment.get('Name', '').lower()
        
        findings = []
        extracted_data = {}
        
        if 'manual' in file_name or 'guide' in file_name:
            findings.append("Service manual/guide document detected")
            findings.append("Contains troubleshooting procedures for error codes")
            extracted_data = {
                "document_type": "Service Manual",
                "relevant_sections": ["Troubleshooting", "Error Codes", "Maintenance"]
            }
        
        elif 'invoice' in file_name or 'receipt' in file_name:
            findings.append("Invoice/receipt document detected")
            extracted_data = {
                "document_type": "Invoice",
                "extracted_fields": {
                    "vendor": "Carrier Parts & Service",
                    "date": "2025-12-01",
                    "total": "$1,247.50"
                }
            }
        
        elif 'config' in file_name or 'bacnet' in file_name:
            findings.append("Configuration document detected")
            findings.append("Contains BACnet/system configuration settings")
            extracted_data = {
                "document_type": "Configuration",
                "settings_found": ["BACnet addresses", "Network parameters"]
            }
        
        else:
            findings.append("Document processed - general attachment")
            extracted_data = {
                "document_type": "General",
                "page_count_estimate": 5
            }

        return {
            "attachment_id": attachment.get('Id'),
            "name": attachment.get('Name'),
            "type": "document",
            "status": "processed",
            "analysis": {
                "extracted_data": extracted_data,
                "findings": findings,
                "text_extracted": True
            },
            "findings": findings
        }

    def _analyze_video_stub(self, attachment: Dict) -> Dict:
        """Handle video attachments (limited processing in demo)."""
        return {
            "attachment_id": attachment.get('Id'),
            "name": attachment.get('Name'),
            "type": "video",
            "status": "processed",
            "analysis": {
                "note": "Video attachment detected",
                "findings": [
                    "Video file attached - may contain audio of equipment noise",
                    "Recommend technician review of video for diagnostic purposes"
                ],
                "duration_estimate": "Unknown",
                "keyframe_analysis": "Not available in demo mode"
            },
            "findings": [
                "Video attachment requires manual review",
                "May contain important diagnostic audio/visual information"
            ]
        }

    def _mock_image_analysis(self, attachments: List[Dict]) -> Dict:
        """Analyze only image attachments."""
        images = [a for a in attachments if self._is_image(a)]
        
        results = [self._analyze_single_image(img) for img in images]
        all_error_codes = []
        for r in results:
            all_error_codes.extend(r.get('error_codes', []))
        
        return {
            "action": "extract_image_info",
            "status": "success",
            "source": "mock_data",
            "images_analyzed": len(images),
            "error_codes_detected": all_error_codes,
            "results": results
        }

    def _mock_document_extraction(self, attachments: List[Dict]) -> Dict:
        """Extract text from document attachments."""
        docs = [a for a in attachments if self._is_document(a)]
        
        results = [self._analyze_single_document(doc) for doc in docs]
        
        return {
            "action": "extract_document_text",
            "status": "success",
            "source": "mock_data",
            "documents_processed": len(docs),
            "results": results
        }

    def _mock_error_code_analysis(self, attachments: List[Dict]) -> Dict:
        """Specifically analyze for error codes in images."""
        images = [a for a in attachments if self._is_image(a)]
        
        all_codes = []
        for img in images:
            result = self._analyze_single_image(img)
            for code in result.get('error_codes', []):
                code_info = {
                    "code": code.get('code'),
                    "source_attachment": img.get('Name'),
                    "confidence": code.get('confidence', 0.8),
                    "meaning": CARRIER_ERROR_CODES.get(code.get('code'), {}).get('description', 'Unknown code'),
                    "severity": CARRIER_ERROR_CODES.get(code.get('code'), {}).get('severity', 'Unknown'),
                    "recommended_action": CARRIER_ERROR_CODES.get(code.get('code'), {}).get('action', 'Consult service manual')
                }
                all_codes.append(code_info)
        
        return {
            "action": "analyze_error_codes",
            "status": "success",
            "source": "mock_data",
            "images_scanned": len(images),
            "error_codes_found": len(all_codes),
            "codes": all_codes,
            "known_codes_database": list(CARRIER_ERROR_CODES.keys())
        }

    def _mock_summarize(self, attachments: List[Dict]) -> Dict:
        """Create summary of all attachments."""
        if not attachments:
            return {
                "action": "summarize_attachments",
                "status": "success",
                "source": "mock_data",
                "summary": "No attachments provided with this case.",
                "attachment_count": 0
            }
        
        images = [a for a in attachments if self._is_image(a)]
        docs = [a for a in attachments if self._is_document(a)]
        videos = [a for a in attachments if self._is_video(a)]
        other = len(attachments) - len(images) - len(docs) - len(videos)
        
        # Process to get findings
        all_results = self._mock_process_all(attachments)
        findings = all_results.get('findings', [])
        error_codes = all_results.get('error_codes', [])
        
        summary_parts = [
            f"Attachment Summary: {len(attachments)} file(s) analyzed",
            f"  - Images: {len(images)}",
            f"  - Documents: {len(docs)}",
            f"  - Videos: {len(videos)}"
        ]
        
        if error_codes:
            codes_str = ", ".join([c.get('code', 'Unknown') for c in error_codes])
            summary_parts.append(f"  - Error codes detected: {codes_str}")
        
        if findings:
            summary_parts.append(f"Key findings: {len(findings)} items extracted")
        
        return {
            "action": "summarize_attachments",
            "status": "success",
            "source": "mock_data",
            "summary": "\n".join(summary_parts),
            "attachment_breakdown": {
                "images": len(images),
                "documents": len(docs),
                "videos": len(videos),
                "other": other
            },
            "key_findings": findings[:5],
            "error_codes": error_codes
        }

    def _is_image(self, attachment: Dict) -> bool:
        """Check if attachment is an image."""
        name = attachment.get('Name', '').lower()
        content_type = attachment.get('ContentType', '').lower()
        return any(ext in name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'image' in content_type

    def _is_document(self, attachment: Dict) -> bool:
        """Check if attachment is a document."""
        name = attachment.get('Name', '').lower()
        content_type = attachment.get('ContentType', '').lower()
        return any(ext in name for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.csv', '.txt']) or 'pdf' in content_type or 'document' in content_type

    def _is_video(self, attachment: Dict) -> bool:
        """Check if attachment is a video."""
        name = attachment.get('Name', '').lower()
        content_type = attachment.get('ContentType', '').lower()
        return any(ext in name for ext in ['.mp4', '.mov', '.avi', '.webm']) or 'video' in content_type

    def _handle_live_request(self, action: str, **kwargs) -> Dict:
        """Handle request using live Azure AI services."""
        # TODO: Implement live processing with:
        # - Azure OpenAI GPT-4o Vision for image analysis
        # - Azure Document Intelligence for PDF extraction
        # - Azure Blob Storage for attachment retrieval
        
        return {
            "action": action,
            "status": "not_implemented",
            "message": "Live Azure AI integration not yet configured."
        }
