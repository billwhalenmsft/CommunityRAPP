"""
Machine Walkaround Agent - Vision-Powered Equipment Inspection Assistant

This agent provides an enterprise-grade "Copilot Vision" experience for Vermeer Manufacturing.
It accepts images (base64-encoded) from a camera feed and uses Azure OpenAI GPT-4o Vision
to analyze equipment, identify components, detect wear/damage, and guide walkaround inspections.

Customer: Vermeer Manufacturing (https://www.vermeer.com/na)
Use Case: AI-assisted machine walkaround inspections

Architecture:
    Camera (Power App / Custom App / Web)
        → Image capture (base64)
        → This Agent (Azure Function)
        → Azure OpenAI GPT-4o Vision API
        → Analysis + Guided Response

Usage:
    agent = MachineWalkaroundAgent()
    
    # Analyze an image
    result = agent.perform(
        action="analyze_image",
        image_base64="<base64_encoded_image>",
        question="What component am I looking at? Is there any visible wear?",
        machine_type="trencher"
    )
    
    # Start a guided inspection
    result = agent.perform(
        action="start_inspection",
        machine_type="S925TX Trencher",
        inspection_type="pre_operation"
    )
    
    # Check a specific inspection point with an image
    result = agent.perform(
        action="inspect_checkpoint",
        image_base64="<base64_encoded_image>",
        checkpoint_id="hydraulic_hoses",
        machine_type="trencher"
    )
"""

import json
import os
import logging
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


# ─── Vermeer Machine Knowledge Base ─────────────────────────────────────────
# This would be expanded with real Vermeer data in production.
# In Phase 2+, this gets replaced with Azure AI Search RAG over actual manuals.

VERMEER_MACHINES = {
    "trencher": {
        "name": "Vermeer Trencher",
        "models": ["S925TX", "RTX1250i2", "RTX550", "RT450"],
        "key_components": [
            "Digging chain/boom", "Teeth and sprockets", "Hydraulic hoses and fittings",
            "Engine compartment", "Cooling system/radiator", "Tracks/undercarriage",
            "Operator station/controls", "Crumber assembly", "Spoil auger",
            "Ground drive motors", "Fuel system", "Electrical system"
        ],
        "common_wear_items": [
            "Digging teeth", "Chain links", "Sprocket teeth", "Hydraulic hose fittings",
            "Track pads", "Idler wheels", "Crumber bar", "Belt tension"
        ],
        "safety_items": [
            "ROPS/FOPS structure", "Emergency stop buttons", "Safety decals and guards",
            "Fire extinguisher", "Backup alarm", "Lights and reflectors"
        ]
    },
    "chipper": {
        "name": "Vermeer Brush Chipper",
        "models": ["BC1800XL", "BC2100XL", "BC1500", "BC1000XL"],
        "key_components": [
            "Feed roller assembly", "Chipper disc/drum", "Knives/blades",
            "Feed table/chute", "Discharge chute", "Engine compartment",
            "Hydraulic system", "Control bar/feed system", "Chassis and tires",
            "Tongue and hitch", "Winch (if equipped)"
        ],
        "common_wear_items": [
            "Chipper knives/blades", "Anvil", "Feed roller teeth",
            "Belt tension", "Hydraulic hose condition", "Tire condition"
        ],
        "safety_items": [
            "Feed control bar (bottom and top)", "Emergency stop",
            "Safety curtain/deflector", "Discharge chute direction",
            "Lock pins", "Safety decals"
        ]
    },
    "stump_cutter": {
        "name": "Vermeer Stump Cutter",
        "models": ["SC852", "SC382", "SC60TX", "SC292"],
        "key_components": [
            "Cutting wheel", "Cutting teeth/pockets", "Swing mechanism",
            "Engine compartment", "Hydraulic system", "Operator controls",
            "Chassis/tracks/wheels", "Tongue and hitch (towable models)",
            "Ground drive system", "Sweep mechanism"
        ],
        "common_wear_items": [
            "Cutting teeth", "Tooth pockets", "Cutting wheel",
            "Swing bearing", "Hydraulic hoses", "Track/tire condition"
        ],
        "safety_items": [
            "Operator presence controls", "Emergency stop",
            "Chip guard/curtain", "Safety decals", "Ground clearance"
        ]
    },
    "horizontal_directional_drill": {
        "name": "Vermeer HDD",
        "models": ["D24x40III", "D40x55III", "D100x140III", "D220x300III"],
        "key_components": [
            "Drill rod rack", "Vise/breakout system", "Carriage and thrust",
            "Rotation system", "Mud pump", "Fluid mixing system",
            "Engine compartment", "Operator station", "Anchor system",
            "Tracking system", "Beacon housing"
        ],
        "common_wear_items": [
            "Drill rod threads", "Vise jaws/dies", "Carriage slides",
            "Mud pump components", "Fluid hoses", "Anchor pins"
        ],
        "safety_items": [
            "Bore path clearance", "Utility locates verification",
            "Emergency shutdown", "Fluid containment", "Safety decals"
        ]
    }
}

# ─── Inspection Checklists ──────────────────────────────────────────────────

INSPECTION_CHECKLISTS = {
    "pre_operation": {
        "name": "Pre-Operation Walkaround",
        "description": "Daily pre-operation inspection before starting the machine",
        "checkpoints": [
            {
                "id": "overall_condition",
                "name": "Overall Machine Condition",
                "instruction": "Stand back and take a photo of the entire machine from each side. Look for obvious damage, fluid puddles underneath, or anything out of place.",
                "look_for": ["Visible damage", "Fluid leaks under machine", "Missing panels/guards", "Debris accumulation"],
                "severity": "critical"
            },
            {
                "id": "engine_compartment",
                "name": "Engine Compartment",
                "instruction": "Open the engine compartment and take a photo. Check fluid levels, belt condition, and look for leaks.",
                "look_for": ["Oil level", "Coolant level", "Belt condition and tension", "Hose connections", "Fluid leaks", "Rodent damage"],
                "severity": "critical"
            },
            {
                "id": "hydraulic_system",
                "name": "Hydraulic System",
                "instruction": "Inspect the hydraulic hoses, fittings, and cylinders. Take photos of any hoses that appear worn, bulging, or leaking.",
                "look_for": ["Hose cracks or bulging", "Fitting leaks", "Cylinder rod condition", "Hydraulic fluid level", "Hose routing/chafing"],
                "severity": "critical"
            },
            {
                "id": "undercarriage_tires",
                "name": "Undercarriage / Tires",
                "instruction": "Inspect tracks, wheels, or tires. Check for proper tension, wear, and damage.",
                "look_for": ["Track tension", "Track pad condition", "Tire pressure/condition", "Idler/roller wear", "Debris in undercarriage"],
                "severity": "high"
            },
            {
                "id": "safety_devices",
                "name": "Safety Devices & Decals",
                "instruction": "Check all safety devices: emergency stops, guards, warning decals, lights, and backup alarm.",
                "look_for": ["Emergency stop functionality", "Guard integrity", "Decal legibility", "Light operation", "Backup alarm"],
                "severity": "critical"
            },
            {
                "id": "work_attachment",
                "name": "Work Attachment / Tool",
                "instruction": "Inspect the main work attachment (digging chain, chipper disc, cutting wheel, etc.). Check for wear, damage, and proper mounting.",
                "look_for": ["Teeth/blade condition", "Mounting bolts", "Wear indicators", "Cracks or damage", "Lubrication points"],
                "severity": "high"
            },
            {
                "id": "operator_station",
                "name": "Operator Station",
                "instruction": "Check the operator station: seat, controls, gauges, and visibility.",
                "look_for": ["Seat belt condition", "Control responsiveness", "Gauge readings", "Windshield/visibility", "Fire extinguisher"],
                "severity": "high"
            }
        ]
    },
    "post_operation": {
        "name": "Post-Operation Inspection",
        "description": "End-of-day inspection after shutting down",
        "checkpoints": [
            {
                "id": "post_fluid_check",
                "name": "Fluid Leak Check",
                "instruction": "After shutdown, walk around and look for any new fluid leaks. Take photos of any wet spots.",
                "look_for": ["New fluid puddles", "Dripping hoses/fittings", "Coolant leaks", "Fuel leaks"],
                "severity": "high"
            },
            {
                "id": "post_wear_items",
                "name": "Wear Item Assessment",
                "instruction": "Inspect wear items that may have degraded during today's operation.",
                "look_for": ["Teeth condition", "Belt/chain wear", "Track/tire wear", "Cutting edge wear"],
                "severity": "medium"
            },
            {
                "id": "post_damage",
                "name": "New Damage Check",
                "instruction": "Look for any damage that occurred during operation.",
                "look_for": ["Dents or impacts", "Broken lights", "Bent components", "Missing hardware"],
                "severity": "high"
            },
            {
                "id": "post_cleanup",
                "name": "Machine Cleanliness",
                "instruction": "Document the machine condition for end-of-day. Note any debris that should be cleaned.",
                "look_for": ["Debris accumulation", "Material buildup", "Cooling system blockage", "General cleanliness"],
                "severity": "low"
            }
        ]
    },
    "maintenance": {
        "name": "Scheduled Maintenance Inspection",
        "description": "Detailed inspection during scheduled maintenance intervals",
        "checkpoints": [
            {
                "id": "maint_fluids",
                "name": "All Fluid Levels & Condition",
                "instruction": "Check all fluid levels and condition: engine oil, hydraulic fluid, coolant, fuel, DEF (if applicable).",
                "look_for": ["Fluid levels", "Fluid color/condition", "Contamination", "Filter condition"],
                "severity": "critical"
            },
            {
                "id": "maint_filters",
                "name": "Filters & Filtration",
                "instruction": "Inspect all filters: air, fuel, hydraulic, oil. Take photos showing condition.",
                "look_for": ["Filter restriction", "Damage or bypass", "Seal condition", "Service indicator status"],
                "severity": "high"
            },
            {
                "id": "maint_structural",
                "name": "Structural Integrity",
                "instruction": "Inspect frame, welds, and structural components for cracks or fatigue.",
                "look_for": ["Weld cracks", "Frame damage", "Pin/bushing wear", "Bolt torque indicators"],
                "severity": "critical"
            },
            {
                "id": "maint_electrical",
                "name": "Electrical System",
                "instruction": "Inspect wiring, connections, and electrical components.",
                "look_for": ["Wire chafing", "Connector condition", "Battery terminals", "Fuse condition"],
                "severity": "high"
            }
        ]
    }
}


class MachineWalkaroundAgent(BasicAgent):
    """
    Vision-powered machine walkaround inspection agent for Vermeer Manufacturing.
    
    Uses Azure OpenAI GPT-4o Vision API to analyze equipment images and provide
    intelligent inspection guidance. Acts as an enterprise replacement for 
    consumer Copilot Vision with Vermeer-specific machine knowledge.
    """

    def __init__(self):
        self.name = 'MachineWalkaround'
        self.metadata = {
            "name": self.name,
            "description": (
                "AI-powered machine walkaround inspection assistant for Vermeer equipment. "
                "Analyzes photos of equipment using Azure OpenAI Vision to identify components, "
                "detect wear/damage, guide inspections, and answer questions about machines. "
                "Supports trenchers, brush chippers, stump cutters, and horizontal directional drills. "
                "Use this agent when the user wants to: inspect a machine, analyze an equipment photo, "
                "start a walkaround, check a machine component, or ask about equipment condition."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "analyze_image",
                            "start_inspection",
                            "inspect_checkpoint",
                            "get_checklist",
                            "identify_component",
                            "check_wear",
                            "read_label",
                            "compare_condition",
                            "get_machine_info",
                            "generate_report"
                        ],
                        "description": (
                            "The walkaround action to perform: "
                            "'analyze_image' - General image analysis with optional question; "
                            "'start_inspection' - Begin a guided walkaround inspection; "
                            "'inspect_checkpoint' - Analyze image for a specific checklist item; "
                            "'get_checklist' - Get inspection checklist for a machine type; "
                            "'identify_component' - Identify a machine component from an image; "
                            "'check_wear' - Assess wear condition from an image; "
                            "'read_label' - OCR a serial plate, label, or decal; "
                            "'compare_condition' - Compare current image against expected condition; "
                            "'get_machine_info' - Get information about a Vermeer machine model; "
                            "'generate_report' - Generate inspection summary report"
                        )
                    },
                    "image_base64": {
                        "type": "string",
                        "description": "Base64-encoded image from camera capture. Required for all image analysis actions."
                    },
                    "question": {
                        "type": "string",
                        "description": "User's question about the image or machine. Used with analyze_image, identify_component, etc."
                    },
                    "machine_type": {
                        "type": "string",
                        "enum": ["trencher", "chipper", "stump_cutter", "horizontal_directional_drill"],
                        "description": "Type of Vermeer machine being inspected."
                    },
                    "machine_model": {
                        "type": "string",
                        "description": "Specific Vermeer model number (e.g., 'S925TX', 'BC1800XL')."
                    },
                    "inspection_type": {
                        "type": "string",
                        "enum": ["pre_operation", "post_operation", "maintenance"],
                        "description": "Type of inspection being performed."
                    },
                    "checkpoint_id": {
                        "type": "string",
                        "description": "ID of the specific inspection checkpoint being evaluated."
                    },
                    "inspection_session_id": {
                        "type": "string",
                        "description": "Session ID for tracking multi-step inspection progress."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        """Main entry point — routes to appropriate handler based on action."""
        action = kwargs.get('action', 'analyze_image')
        
        try:
            if action == 'analyze_image':
                return self._analyze_image(**kwargs)
            elif action == 'start_inspection':
                return self._start_inspection(**kwargs)
            elif action == 'inspect_checkpoint':
                return self._inspect_checkpoint(**kwargs)
            elif action == 'get_checklist':
                return self._get_checklist(**kwargs)
            elif action == 'identify_component':
                return self._identify_component(**kwargs)
            elif action == 'check_wear':
                return self._check_wear(**kwargs)
            elif action == 'read_label':
                return self._read_label(**kwargs)
            elif action == 'compare_condition':
                return self._compare_condition(**kwargs)
            elif action == 'get_machine_info':
                return self._get_machine_info(**kwargs)
            elif action == 'generate_report':
                return self._generate_report(**kwargs)
            else:
                return self._format_error(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"MachineWalkaroundAgent error: {str(e)}", exc_info=True)
            return self._format_error(f"Error during {action}: {str(e)}")

    # ─── Core Vision Actions ────────────────────────────────────────────

    def _analyze_image(self, **kwargs) -> str:
        """General-purpose image analysis with optional question."""
        image_base64 = kwargs.get('image_base64', '')
        question = kwargs.get('question', 'What do you see in this image? Identify any equipment components and note any visible issues.')
        machine_type = kwargs.get('machine_type', '')
        
        if not image_base64:
            return self._format_no_image_response(question, machine_type)
        
        # Build the vision prompt
        system_prompt = self._build_system_prompt(machine_type)
        
        # Call Azure OpenAI Vision
        result = self._call_vision_api(system_prompt, question, image_base64)
        return result

    def _identify_component(self, **kwargs) -> str:
        """Identify a specific machine component from an image."""
        image_base64 = kwargs.get('image_base64', '')
        machine_type = kwargs.get('machine_type', '')
        question = kwargs.get('question', '')
        
        prompt = (
            f"Identify the machine component shown in this image. "
            f"Provide: 1) Component name, 2) Its function, 3) What to check during inspection, "
            f"4) Common failure modes. "
        )
        if machine_type and machine_type in VERMEER_MACHINES:
            machine = VERMEER_MACHINES[machine_type]
            prompt += f"This is a {machine['name']}. Known components: {', '.join(machine['key_components'])}. "
        if question:
            prompt += f"User also asks: {question}"
        
        if not image_base64:
            return self._format_no_image_response(prompt, machine_type)
        
        system_prompt = self._build_system_prompt(machine_type)
        return self._call_vision_api(system_prompt, prompt, image_base64)

    def _check_wear(self, **kwargs) -> str:
        """Assess wear condition from an image."""
        image_base64 = kwargs.get('image_base64', '')
        machine_type = kwargs.get('machine_type', '')
        question = kwargs.get('question', '')
        
        prompt = (
            "Analyze this image for signs of wear, damage, or deterioration. "
            "Rate the condition on a scale: ✅ Good / ⚠️ Monitor / 🔶 Service Soon / 🔴 Replace Now. "
            "Specifically look for: cracks, leaks, corrosion, excessive wear, missing components, "
            "loose fittings, and any safety hazards. "
            "Provide actionable recommendations. "
        )
        if machine_type and machine_type in VERMEER_MACHINES:
            machine = VERMEER_MACHINES[machine_type]
            prompt += f"Common wear items for {machine['name']}: {', '.join(machine['common_wear_items'])}. "
        if question:
            prompt += f"User also asks: {question}"
        
        if not image_base64:
            return self._format_no_image_response(prompt, machine_type)
        
        system_prompt = self._build_system_prompt(machine_type)
        return self._call_vision_api(system_prompt, prompt, image_base64)

    def _read_label(self, **kwargs) -> str:
        """OCR a serial plate, label, warning decal, or gauge."""
        image_base64 = kwargs.get('image_base64', '')
        question = kwargs.get('question', '')
        
        prompt = (
            "Read and transcribe all text visible in this image. This may be a serial plate, "
            "model label, warning decal, gauge reading, or other machine marking. "
            "Provide: 1) All text found (exact transcription), 2) Type of label/marking, "
            "3) Any relevant information that can be derived from the text (model info, dates, specs). "
        )
        if question:
            prompt += f"User also asks: {question}"
        
        if not image_base64:
            return ("📋 **Label/OCR Reading**\n\n"
                    "I need an image to read labels and text. Please capture a photo of the "
                    "serial plate, warning decal, or gauge you'd like me to read.\n\n"
                    "**Tips for best results:**\n"
                    "- Hold the camera steady and close to the label\n"
                    "- Ensure good lighting (avoid glare)\n"
                    "- Capture the entire label in frame")
        
        system_prompt = self._build_system_prompt()
        return self._call_vision_api(system_prompt, prompt, image_base64)

    def _compare_condition(self, **kwargs) -> str:
        """Compare current condition against expected baseline."""
        image_base64 = kwargs.get('image_base64', '')
        machine_type = kwargs.get('machine_type', '')
        question = kwargs.get('question', '')
        
        prompt = (
            "Analyze this equipment image and compare the visible condition against what would be "
            "expected for a well-maintained machine. Note any deviations from normal condition. "
            "Consider: cleanliness, alignment, wear patterns, fluid conditions, and structural integrity. "
            "Categorize findings as: Normal / Abnormal / Needs Attention / Safety Concern. "
        )
        if question:
            prompt += f"User also asks: {question}"
        
        if not image_base64:
            return self._format_no_image_response(prompt, machine_type)
        
        system_prompt = self._build_system_prompt(machine_type)
        return self._call_vision_api(system_prompt, prompt, image_base64)

    # ─── Inspection Flow Actions ────────────────────────────────────────

    def _start_inspection(self, **kwargs) -> str:
        """Begin a guided walkaround inspection."""
        machine_type = kwargs.get('machine_type', 'trencher')
        machine_model = kwargs.get('machine_model', '')
        inspection_type = kwargs.get('inspection_type', 'pre_operation')
        
        checklist = INSPECTION_CHECKLISTS.get(inspection_type, INSPECTION_CHECKLISTS['pre_operation'])
        machine = VERMEER_MACHINES.get(machine_type, VERMEER_MACHINES['trencher'])
        
        session_id = f"insp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        model_display = f" ({machine_model})" if machine_model else ""
        
        response = f"# 🔍 {checklist['name']}\n"
        response += f"**Machine:** {machine['name']}{model_display}\n"
        response += f"**Session:** {session_id}\n"
        response += f"**Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
        response += f"_{checklist['description']}_\n\n"
        response += "---\n\n"
        response += f"## Inspection Checkpoints ({len(checklist['checkpoints'])} items)\n\n"
        
        for i, cp in enumerate(checklist['checkpoints'], 1):
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(cp['severity'], "⚪")
            response += f"### {i}. {cp['name']} {severity_icon}\n"
            response += f"📸 **{cp['instruction']}**\n"
            response += f"Look for: {', '.join(cp['look_for'])}\n\n"
        
        response += "---\n\n"
        response += "**📱 How to proceed:**\n"
        response += "1. Point your camera at the first checkpoint area\n"
        response += "2. Take a photo and ask me to inspect it\n"
        response += f"3. Say: *\"Check the {checklist['checkpoints'][0]['name'].lower()}\"* with your photo\n"
        response += f"4. I'll analyze each checkpoint and give you a pass/fail assessment\n\n"
        response += f"**Session ID:** `{session_id}` (reference this for your inspection report)"
        
        return response

    def _inspect_checkpoint(self, **kwargs) -> str:
        """Analyze an image for a specific inspection checkpoint."""
        image_base64 = kwargs.get('image_base64', '')
        checkpoint_id = kwargs.get('checkpoint_id', '')
        machine_type = kwargs.get('machine_type', 'trencher')
        inspection_type = kwargs.get('inspection_type', 'pre_operation')
        
        # Find the checkpoint
        checklist = INSPECTION_CHECKLISTS.get(inspection_type, INSPECTION_CHECKLISTS['pre_operation'])
        checkpoint = None
        for cp in checklist['checkpoints']:
            if cp['id'] == checkpoint_id:
                checkpoint = cp
                break
        
        if not checkpoint:
            # Try fuzzy match
            for cp in checklist['checkpoints']:
                if checkpoint_id.lower() in cp['id'].lower() or checkpoint_id.lower() in cp['name'].lower():
                    checkpoint = cp
                    break
        
        if not checkpoint:
            available = ", ".join([f"`{cp['id']}` ({cp['name']})" for cp in checklist['checkpoints']])
            return f"❓ Checkpoint `{checkpoint_id}` not found.\n\nAvailable checkpoints:\n{available}"
        
        prompt = (
            f"**INSPECTION CHECKPOINT: {checkpoint['name']}**\n\n"
            f"Instructions: {checkpoint['instruction']}\n\n"
            f"Evaluate this image for the following criteria:\n"
            f"- Items to check: {', '.join(checkpoint['look_for'])}\n"
            f"- Severity level: {checkpoint['severity']}\n\n"
            f"Provide your assessment in this format:\n"
            f"1. **Status**: ✅ PASS / ⚠️ CAUTION / 🔴 FAIL\n"
            f"2. **Observations**: What you see in the image\n"
            f"3. **Issues Found**: Any problems detected (or 'None')\n"
            f"4. **Recommendation**: Next steps if any issues found\n"
            f"5. **Confidence**: How confident you are in this assessment (High/Medium/Low)\n"
        )
        
        if not image_base64:
            return (f"📸 **Checkpoint: {checkpoint['name']}**\n\n"
                    f"{checkpoint['instruction']}\n\n"
                    f"I need a photo to evaluate this checkpoint. Please capture an image and send it.")
        
        system_prompt = self._build_system_prompt(machine_type)
        return self._call_vision_api(system_prompt, prompt, image_base64)

    def _get_checklist(self, **kwargs) -> str:
        """Return the inspection checklist for a machine type."""
        machine_type = kwargs.get('machine_type', 'trencher')
        inspection_type = kwargs.get('inspection_type', 'pre_operation')
        
        checklist = INSPECTION_CHECKLISTS.get(inspection_type, INSPECTION_CHECKLISTS['pre_operation'])
        machine = VERMEER_MACHINES.get(machine_type, VERMEER_MACHINES['trencher'])
        
        response = f"# 📋 {checklist['name']} — {machine['name']}\n\n"
        response += f"_{checklist['description']}_\n\n"
        
        for i, cp in enumerate(checklist['checkpoints'], 1):
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(cp['severity'], "⚪")
            response += f"**{i}. {cp['name']}** {severity_icon} `{cp['severity']}`\n"
            response += f"   - {cp['instruction']}\n"
            response += f"   - Check: {', '.join(cp['look_for'])}\n\n"
        
        response += "\n**Legend:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low"
        return response

    # ─── Machine Info Actions ───────────────────────────────────────────

    def _get_machine_info(self, **kwargs) -> str:
        """Return information about a Vermeer machine type."""
        machine_type = kwargs.get('machine_type', '')
        machine_model = kwargs.get('machine_model', '')
        question = kwargs.get('question', '')
        
        if not machine_type and machine_model:
            # Try to determine type from model number
            for mtype, mdata in VERMEER_MACHINES.items():
                if machine_model in mdata['models']:
                    machine_type = mtype
                    break
        
        if not machine_type:
            # List all machine types
            response = "# 🏗️ Supported Vermeer Equipment\n\n"
            for mtype, mdata in VERMEER_MACHINES.items():
                response += f"### {mdata['name']}\n"
                response += f"- **Type key:** `{mtype}`\n"
                response += f"- **Models:** {', '.join(mdata['models'])}\n"
                response += f"- **Key components:** {', '.join(mdata['key_components'][:5])}...\n\n"
            response += "\nSpecify a `machine_type` for detailed information."
            return response
        
        machine = VERMEER_MACHINES.get(machine_type)
        if not machine:
            return f"❓ Unknown machine type: `{machine_type}`. Available: {', '.join(VERMEER_MACHINES.keys())}"
        
        model_display = f" — {machine_model}" if machine_model else ""
        
        response = f"# 🏗️ {machine['name']}{model_display}\n\n"
        response += f"**Available models:** {', '.join(machine['models'])}\n\n"
        response += "## Key Components\n"
        for comp in machine['key_components']:
            response += f"- {comp}\n"
        response += "\n## Common Wear Items\n"
        for item in machine['common_wear_items']:
            response += f"- ⚠️ {item}\n"
        response += "\n## Safety Inspection Points\n"
        for item in machine['safety_items']:
            response += f"- 🛡️ {item}\n"
        
        response += "\n## Available Inspections\n"
        for itype, idata in INSPECTION_CHECKLISTS.items():
            response += f"- **{idata['name']}** (`{itype}`): {len(idata['checkpoints'])} checkpoints\n"
        
        if question:
            response += f"\n---\n\n**Re: your question** — \"{question}\"\n"
            response += "For specific questions about this machine, try an `analyze_image` with a photo, "
            response += "or ask me anything about the components and inspection procedures listed above."
        
        return response

    def _generate_report(self, **kwargs) -> str:
        """Generate an inspection summary report."""
        machine_type = kwargs.get('machine_type', 'trencher')
        machine_model = kwargs.get('machine_model', '')
        inspection_type = kwargs.get('inspection_type', 'pre_operation')
        inspection_session_id = kwargs.get('inspection_session_id', 'N/A')
        
        machine = VERMEER_MACHINES.get(machine_type, VERMEER_MACHINES['trencher'])
        checklist = INSPECTION_CHECKLISTS.get(inspection_type, INSPECTION_CHECKLISTS['pre_operation'])
        
        model_display = f" ({machine_model})" if machine_model else ""
        
        response = f"# 📊 Inspection Report\n\n"
        response += f"| Field | Value |\n|---|---|\n"
        response += f"| **Machine** | {machine['name']}{model_display} |\n"
        response += f"| **Inspection** | {checklist['name']} |\n"
        response += f"| **Session** | {inspection_session_id} |\n"
        response += f"| **Date** | {datetime.now().strftime('%B %d, %Y')} |\n"
        response += f"| **Inspector** | (User) |\n"
        response += f"| **Checkpoints** | {len(checklist['checkpoints'])} |\n\n"
        
        response += "## Checkpoint Summary\n\n"
        response += "| # | Checkpoint | Severity | Status |\n|---|---|---|---|\n"
        for i, cp in enumerate(checklist['checkpoints'], 1):
            response += f"| {i} | {cp['name']} | {cp['severity'].upper()} | ⬜ Pending |\n"
        
        response += "\n---\n"
        response += "\n*Note: In the full implementation, this report would contain the actual inspection results, "
        response += "captured photos, and AI analysis for each checkpoint. Photos would be stored in Azure Blob Storage "
        response += "and the report would be generated as a PDF.*\n"
        response += "\n**To complete this report:**\n"
        response += "1. Use `start_inspection` to begin the walkaround\n"
        response += "2. Use `inspect_checkpoint` with a photo for each checkpoint\n"
        response += "3. Use `generate_report` to create the final summary"
        
        return response

    # ─── Azure OpenAI Vision Integration ────────────────────────────────

    def _call_vision_api(self, system_prompt: str, user_prompt: str, image_base64: str) -> str:
        """
        Call Azure OpenAI GPT-4o Vision API with an image.
        
        In production, this calls the actual Azure OpenAI API.
        For prototype/demo, returns a structured response showing what the API would return.
        """
        try:
            # Try to import and use actual Azure OpenAI
            from openai import AzureOpenAI
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
            api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
            
            if not endpoint:
                return self._format_demo_vision_response(user_prompt)
            
            # Build client — prefer token auth, fall back to API key
            if api_key:
                client = AzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version=api_version
                )
            else:
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default"
                )
                client = AzureOpenAI(
                    azure_ad_token_provider=token_provider,
                    azure_endpoint=endpoint,
                    api_version=api_version
                )
            
            # Determine image MIME type (assume JPEG if unknown)
            mime_type = "image/jpeg"
            if image_base64.startswith("/9j/"):
                mime_type = "image/jpeg"
            elif image_base64.startswith("iVBOR"):
                mime_type = "image/png"
            elif image_base64.startswith("UklGR"):
                mime_type = "image/webp"
            
            # Build the vision request
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.warning("OpenAI library not available — returning demo response")
            return self._format_demo_vision_response(user_prompt)
        except Exception as e:
            logger.error(f"Vision API error: {str(e)}", exc_info=True)
            # Fall back to demo response on API error
            return (f"⚠️ **Vision API Error**\n\n"
                    f"Could not connect to Azure OpenAI Vision API: {str(e)}\n\n"
                    f"**For production use, ensure:**\n"
                    f"- `AZURE_OPENAI_ENDPOINT` is set\n"
                    f"- `AZURE_OPENAI_DEPLOYMENT_NAME` points to a GPT-4o (or newer) deployment\n"
                    f"- The deployment supports image/vision inputs\n\n"
                    f"---\n\n"
                    f"{self._format_demo_vision_response(user_prompt)}")

    def _build_system_prompt(self, machine_type: str = '') -> str:
        """Build the system prompt with Vermeer-specific context."""
        prompt = (
            "You are a Vermeer Manufacturing equipment inspection assistant. "
            "You help field technicians and operators perform machine walkaround inspections "
            "by analyzing photos of equipment and providing expert guidance.\n\n"
            "YOUR CAPABILITIES:\n"
            "- Identify machine components from photos\n"
            "- Detect wear, damage, leaks, and safety hazards\n"
            "- Read serial plates, labels, and gauges via OCR\n"
            "- Guide users through inspection checklists\n"
            "- Provide maintenance recommendations\n"
            "- Rate component condition (Good / Monitor / Service Soon / Replace Now)\n\n"
            "RESPONSE GUIDELINES:\n"
            "- Be specific and actionable in your observations\n"
            "- Always note safety hazards first and prominently\n"
            "- If unsure about something, say so — don't guess on safety-critical items\n"
            "- Use clear condition ratings: ✅ Good / ⚠️ Monitor / 🔶 Service Soon / 🔴 Replace Now\n"
            "- Reference specific parts/components by name when possible\n"
            "- If the image quality is poor or the component isn't clear, ask for a better photo\n\n"
            "VERMEER EQUIPMENT TYPES:\n"
            "- Trenchers (S925TX, RTX1250i2, RTX550, RT450)\n"
            "- Brush Chippers (BC1800XL, BC2100XL, BC1500, BC1000XL)\n"
            "- Stump Cutters (SC852, SC382, SC60TX, SC292)\n"
            "- Horizontal Directional Drills (D24x40III, D40x55III, D100x140III)\n"
        )
        
        if machine_type and machine_type in VERMEER_MACHINES:
            machine = VERMEER_MACHINES[machine_type]
            prompt += (
                f"\nCURRENT MACHINE: {machine['name']}\n"
                f"Key Components: {', '.join(machine['key_components'])}\n"
                f"Common Wear Items: {', '.join(machine['common_wear_items'])}\n"
                f"Safety Items: {', '.join(machine['safety_items'])}\n"
            )
        
        return prompt

    # ─── Helpers ────────────────────────────────────────────────────────

    def _format_no_image_response(self, question: str, machine_type: str = '') -> str:
        """Response when no image is provided."""
        machine = VERMEER_MACHINES.get(machine_type, {})
        machine_name = machine.get('name', 'Vermeer equipment') if machine else 'Vermeer equipment'
        
        response = (
            f"📸 **Image Required**\n\n"
            f"I need a photo to analyze your {machine_name}. "
            f"Please point your camera at the area you'd like me to inspect and capture an image.\n\n"
            f"**Your question:** _{question}_\n\n"
            f"I'll answer this as soon as I can see what you're looking at!\n\n"
            f"**Tips for best results:**\n"
            f"- Get close enough to see detail, but include enough context\n"
            f"- Ensure adequate lighting\n"
            f"- For serial plates/labels, hold camera steady and minimize glare\n"
            f"- For overall condition, step back 4-6 feet from the machine"
        )
        return response

    def _format_demo_vision_response(self, prompt: str) -> str:
        """Demo response showing what the vision API would return."""
        return (
            "🔍 **[DEMO MODE — Vision API Response Preview]**\n\n"
            "In production, Azure OpenAI GPT-4o would analyze the captured image and provide:\n\n"
            "**Component Identification:**\n"
            "- Primary component: [Identified from image]\n"
            "- Sub-components visible: [Listed from image]\n"
            "- Machine location: [Where on the machine this is]\n\n"
            "**Condition Assessment:**\n"
            "- Overall condition: ✅ Good / ⚠️ Monitor / 🔶 Service Soon / 🔴 Replace Now\n"
            "- Wear indicators: [Specific observations from image]\n"
            "- Safety concerns: [Any hazards identified]\n\n"
            "**Recommendations:**\n"
            "- [Specific maintenance actions based on visual analysis]\n"
            "- [Follow-up items to check]\n\n"
            f"---\n*Prompt sent to vision model:* _{prompt[:200]}{'...' if len(prompt) > 200 else ''}_\n\n"
            "**To enable live analysis:**\n"
            "1. Deploy Azure OpenAI with GPT-4o\n"
            "2. Set `AZURE_OPENAI_ENDPOINT` in environment\n"
            "3. Set `AZURE_OPENAI_DEPLOYMENT_NAME` to your GPT-4o deployment\n"
            "4. Ensure the deployment supports vision inputs"
        )

    def _format_error(self, message: str) -> str:
        """Format an error response."""
        return f"❌ **Error:** {message}"
