"""
Demo Simulator - Power Platform Integration
============================================
Generates Power Automate flow definitions and provides utilities
for simulating customer interactions during D365 demos.

Simulation Channels:
- Email: Power Automate + Outlook/Graph connector
- Chat: Power Automate Desktop (PAD) browser automation
- Voice: Azure Communication Services + Text-to-Speech

The HTML Demo Execution Guide calls HTTP-triggered flows
via JavaScript fetch() when the SE clicks simulation buttons.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimulationScript:
    """A scripted simulation action."""
    channel: str  # email, chat, voice
    delay_seconds: int  # delay before execution
    sender_name: str
    sender_identifier: str  # email, phone, chat ID
    message: str
    subject: Optional[str] = None  # for email
    sentiment: str = "neutral"  # neutral, angry, happy
    attachments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DemoSimulator:
    """
    Generates Power Platform resources for demo simulation.
    
    Usage:
        simulator = DemoSimulator(config)
        
        # Generate flow definitions
        email_flow = simulator.generate_email_flow_definition()
        chat_flow = simulator.generate_chat_pad_definition()
        voice_flow = simulator.generate_voice_flow_definition()
        
        # Generate HTML control panel
        control_html = simulator.generate_control_panel_html()
    """
    
    def __init__(self, demo_config: Dict[str, Any]):
        """
        Initialize with demo configuration.
        
        Args:
            demo_config: Configuration containing:
                - customer_name: Customer/company name
                - brands: List of brand names
                - demo_story: Story with characters, scenarios
                - environment: D365 environment details
                - simulation: Simulation-specific config (emails, flows)
        """
        self.config = demo_config
        self.customer_name = demo_config.get("customer_name", "Demo Customer")
        self.brands = demo_config.get("brands", ["Product"])
        self.demo_story = demo_config.get("demo_story", {})
        self.environment = demo_config.get("environment", {})
        self.simulation_config = demo_config.get("simulation", {})
        
        # Build scripts from story characters
        self.scripts = self._build_simulation_scripts()
    
    def _build_simulation_scripts(self) -> List[SimulationScript]:
        """Build simulation scripts from demo story."""
        scripts = []
        characters = self.demo_story.get("characters", [])
        
        for char in characters:
            channel = char.get("channel", "phone")
            name = char.get("name", "Customer")
            scenario = char.get("scenario", "general inquiry")
            account = char.get("account", "")
            sentiment = char.get("sentiment", "neutral")
            
            if channel == "email":
                scripts.append(SimulationScript(
                    channel="email",
                    delay_seconds=0,
                    sender_name=name,
                    sender_identifier=char.get("email", f"{name.lower().replace(' ', '.')}@example.com"),
                    subject=self._generate_email_subject(scenario, sentiment),
                    message=self._generate_email_body(name, account, scenario, sentiment),
                    sentiment=sentiment
                ))
            
            elif channel == "chat":
                scripts.append(SimulationScript(
                    channel="chat",
                    delay_seconds=0,
                    sender_name=name,
                    sender_identifier=char.get("email", ""),
                    message=self._generate_chat_message(name, scenario),
                    sentiment=sentiment
                ))
            
            elif channel == "phone":
                scripts.append(SimulationScript(
                    channel="voice",
                    delay_seconds=0,
                    sender_name=name,
                    sender_identifier=char.get("phone", "+1-555-0100"),
                    message=self._generate_voice_script(name, account, scenario),
                    sentiment=sentiment
                ))
        
        # Add default scripts if none from characters
        if not scripts:
            scripts = self._generate_default_scripts()
        
        return scripts
    
    def _generate_email_subject(self, scenario: str, sentiment: str) -> str:
        """Generate email subject based on scenario and sentiment."""
        subjects = {
            ("order inquiry", "neutral"): "Question about my order",
            ("order inquiry", "angry"): "URGENT - Order Issue - Need Immediate Response",
            ("product question", "neutral"): "Product specification question",
            ("warranty", "neutral"): "Warranty coverage inquiry",
            ("rma", "neutral"): "Return request - PO #98765",
            ("complaint", "angry"): "UNACCEPTABLE - Product Failure - Escalate Immediately",
        }
        key = (scenario.lower(), sentiment)
        return subjects.get(key, f"Support Request - {scenario.title()}")
    
    def _generate_email_body(self, name: str, account: str, scenario: str, sentiment: str) -> str:
        """Generate email body content."""
        if sentiment == "angry":
            return f"""To whom it may concern,

This is UNACCEPTABLE. We have been waiting for a resolution for too long and I am FURIOUS about the lack of response.

Our operations have been impacted and if we don't get a resolution immediately, I will be speaking with our ATTORNEY about damages.

I need a callback TODAY.

{name}
{account}"""
        
        elif scenario == "order inquiry":
            return f"""Hello,

I'm reaching out regarding a recent order we placed. Can you please provide an update on the status?

Our PO number is 98765.

Thank you,
{name}
{account}"""
        
        elif scenario == "rma":
            return f"""Hello Support Team,

We received our shipment today but unfortunately one of the items arrived damaged in transit. The packaging was crushed and the unit is dented.

Please provide an RMA number so we can return this item for replacement.

Photos attached.

Thank you,
{name}
{account}"""
        
        else:
            return f"""Hello,

I have a question regarding {scenario}.

Could someone please assist?

Best regards,
{name}
{account}"""
    
    def _generate_chat_message(self, name: str, scenario: str) -> str:
        """Generate initial chat message."""
        messages = {
            "order inquiry": "Hi, I need help checking on a recent order. The order number is ORD-78421.",
            "product question": "Hello, I have a question about product specifications for model XYZ-500.",
            "general inquiry": "Hi, I need some assistance please.",
            "escalation": "I've been waiting too long. I need to speak with a supervisor.",
        }
        return messages.get(scenario, f"Hi, I need help with {scenario}.")
    
    def _generate_voice_script(self, name: str, account: str, scenario: str) -> str:
        """Generate voice TTS script."""
        return f"""Hi, this is {name.split()[0]} calling from {account}. 
I need help with {scenario}. 
Can you assist me with this?"""
    
    def _generate_default_scripts(self) -> List[SimulationScript]:
        """Generate default simulation scripts."""
        brand = self.brands[0] if self.brands else "Product"
        
        return [
            SimulationScript(
                channel="email",
                delay_seconds=0,
                sender_name="Patricia Hayes",
                sender_identifier="p.hayes@facilitygroup.com",
                subject="URGENT - Product Failure - Need Immediate Response",
                message=self._generate_email_body("Patricia Hayes", "Facility Management Group", "complaint", "angry"),
                sentiment="angry"
            ),
            SimulationScript(
                channel="chat",
                delay_seconds=0,
                sender_name="Rachel Chen",
                sender_identifier="r.chen@metrosupply.com",
                message="Hi, I need help with my recent order. The order number is ORD-78421.",
                sentiment="neutral"
            ),
            SimulationScript(
                channel="voice",
                delay_seconds=0,
                sender_name="Marcus Thompson",
                sender_identifier="+1-555-0123",
                message=f"Hi, this is Marcus calling from Metro Facility Services. I need help with a service request for one of our {brand} units.",
                sentiment="neutral"
            )
        ]
    
    # =========================================
    # POWER AUTOMATE FLOW GENERATION
    # =========================================
    
    def generate_email_flow_definition(self) -> Dict[str, Any]:
        """
        Generate Power Automate Cloud Flow definition for email simulation.
        
        Flow: HTTP Trigger → Send Email (Outlook) → Response
        
        Returns OpenAPI/Logic Apps flow definition that can be imported.
        """
        email_script = next((s for s in self.scripts if s.channel == "email"), None)
        
        if not email_script:
            email_script = self._generate_default_scripts()[0]
        
        # Get D365 support email (where to send the customer email)
        support_email = self.simulation_config.get("support_email", 
                       self.environment.get("support_email", "support@yourorg.onmicrosoft.com"))
        
        flow_definition = {
            "name": f"Demo Simulator - Send Customer Email ({self.customer_name})",
            "description": f"Simulates an incoming customer email for {self.customer_name} demo. Triggered from Demo Execution Guide.",
            "trigger": {
                "type": "Request",
                "kind": "Http",
                "inputs": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "body": {"type": "string"},
                            "sentiment": {"type": "string"},
                            "sender_name": {"type": "string"},
                            "sender_email": {"type": "string"}
                        }
                    }
                }
            },
            "actions": {
                "Send_Email": {
                    "type": "ApiConnection",
                    "inputs": {
                        "host": {
                            "connection": {
                                "name": "@parameters('$connections')['office365']['connectionId']"
                            }
                        },
                        "method": "post",
                        "path": "/v2/Mail",
                        "body": {
                            "To": support_email,
                            "Subject": "@{coalesce(triggerBody()?['subject'], '" + email_script.subject + "')}",
                            "Body": "<p>@{coalesce(triggerBody()?['body'], '" + email_script.message.replace('\n', '<br>') + "')}</p>",
                            "From": "@{coalesce(triggerBody()?['sender_email'], '" + email_script.sender_identifier + "')}",
                            "Importance": "High" if email_script.sentiment == "angry" else "Normal"
                        }
                    }
                },
                "Response": {
                    "type": "Response",
                    "kind": "Http",
                    "inputs": {
                        "statusCode": 200,
                        "body": {
                            "status": "success",
                            "message": "Email sent to D365 queue",
                            "timestamp": "@{utcNow()}"
                        }
                    },
                    "runAfter": {
                        "Send_Email": ["Succeeded"]
                    }
                }
            },
            "parameters": {
                "$connections": {
                    "defaultValue": {},
                    "type": "Object"
                }
            },
            "_metadata": {
                "customer": self.customer_name,
                "channel": "email",
                "default_script": asdict(email_script),
                "support_email": support_email
            }
        }
        
        return flow_definition
    
    def generate_chat_pad_definition(self) -> Dict[str, Any]:
        """
        Generate Power Automate Desktop (PAD) flow definition for chat simulation.
        
        PAD Flow: Launch Browser → Navigate to Portal → Click Chat Widget → Type Messages
        
        Returns PAD-compatible definition.
        """
        chat_script = next((s for s in self.scripts if s.channel == "chat"), None)
        
        if not chat_script:
            chat_script = SimulationScript(
                channel="chat",
                delay_seconds=0,
                sender_name="Demo Customer",
                sender_identifier="customer@demo.com",
                message="Hi, I need help with my order.",
                sentiment="neutral"
            )
        
        portal_url = self.simulation_config.get("portal_url",
                     self.environment.get("portal_url", "https://yourorg.powerappsportals.com"))
        
        # PAD uses Robin scripting language
        pad_script = f'''
# Demo Simulator - Chat Simulation
# Customer: {self.customer_name}
# Character: {chat_script.sender_name}

# Launch browser and navigate to portal
WebAutomation.LaunchEdge Url: "{portal_url}" WindowState: WebAutomation.BrowserWindowState.Maximized BrowserInstance=> Browser

# Wait for page load
WAIT 3

# Find and click chat widget (common selectors)
WebAutomation.Click BrowserInstance: Browser Selector: "button[aria-label*='chat'], div[class*='chat-widget'], iframe[title*='chat']" ClickType: WebAutomation.ClickType.LeftClick

# Wait for chat to open
WAIT 2

# Type initial message
SET MessageToSend TO "{chat_script.message}"
WebAutomation.PopulateTextField BrowserInstance: Browser Selector: "textarea[placeholder*='message'], input[type='text'][class*='chat']" Text: MessageToSend Mode: WebAutomation.PopulateMode.Replace

# Send message (Enter key)
MouseAndKeyboard.SendKeys TextToSend: "{{Return}}" DelayBetweenKeystrokes: 10

# Log completion
Display.ShowMessageDialog.ShowMessage Title: "Demo Simulation" Message: "Chat message sent: %MessageToSend%" Icon: Display.Icon.Information Buttons: Display.Buttons.OK
'''
        
        return {
            "name": f"Demo Simulator - Chat ({self.customer_name})",
            "description": f"PAD flow to simulate customer chat for {self.customer_name} demo",
            "type": "power_automate_desktop",
            "script": pad_script,
            "variables": {
                "portal_url": portal_url,
                "message": chat_script.message,
                "sender_name": chat_script.sender_name
            },
            "_metadata": {
                "customer": self.customer_name,
                "channel": "chat",
                "default_script": asdict(chat_script)
            }
        }
    
    def generate_voice_flow_definition(self) -> Dict[str, Any]:
        """
        Generate Power Automate Cloud Flow for voice call simulation.
        
        Flow: HTTP Trigger → Azure Communication Services (Call) → Text-to-Speech
        
        Requires: Azure Communication Services connector in Power Automate
        """
        voice_script = next((s for s in self.scripts if s.channel == "voice"), None)
        
        if not voice_script:
            voice_script = SimulationScript(
                channel="voice",
                delay_seconds=0,
                sender_name="Demo Customer",
                sender_identifier="+1-555-0100",
                message="Hi, this is a customer calling for support. I need help with my account.",
                sentiment="neutral"
            )
        
        # Voice channel number to call
        voice_channel_number = self.simulation_config.get("voice_channel_number",
                              self.environment.get("voice_channel_number", "+1-555-0000"))
        
        # ACS connection string would be in environment
        acs_connection = self.simulation_config.get("acs_connection_name", "AzureCommunicationServices")
        
        flow_definition = {
            "name": f"Demo Simulator - Voice Call ({self.customer_name})",
            "description": f"Simulates incoming customer phone call for {self.customer_name} demo using Azure Communication Services.",
            "trigger": {
                "type": "Request",
                "kind": "Http",
                "inputs": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "script": {"type": "string"},
                            "caller_name": {"type": "string"},
                            "caller_number": {"type": "string"}
                        }
                    }
                }
            },
            "actions": {
                "Initialize_Script": {
                    "type": "InitializeVariable",
                    "inputs": {
                        "variables": [{
                            "name": "voiceScript",
                            "type": "string",
                            "value": "@{coalesce(triggerBody()?['script'], '" + voice_script.message + "')}"
                        }]
                    }
                },
                "Place_Call_ACS": {
                    "type": "ApiConnection",
                    "inputs": {
                        "host": {
                            "connection": {
                                "name": f"@parameters('$connections')['{acs_connection}']['connectionId']"
                            }
                        },
                        "method": "post",
                        "path": "/calling/callConnections",
                        "body": {
                            "targets": [{
                                "phoneNumber": {
                                    "value": voice_channel_number
                                }
                            }],
                            "sourceCallerIdNumber": {
                                "value": "@{coalesce(triggerBody()?['caller_number'], '" + voice_script.sender_identifier + "')}"
                            },
                            "callIntelligenceOptions": {
                                "cognitiveServicesEndpoint": "@parameters('cognitiveServicesEndpoint')"
                            }
                        }
                    },
                    "runAfter": {
                        "Initialize_Script": ["Succeeded"]
                    }
                },
                "Play_TTS_Message": {
                    "type": "ApiConnection",
                    "inputs": {
                        "host": {
                            "connection": {
                                "name": f"@parameters('$connections')['{acs_connection}']['connectionId']"
                            }
                        },
                        "method": "post",
                        "path": "/calling/callConnections/@{body('Place_Call_ACS')?['callConnectionId']}/play",
                        "body": {
                            "playSources": [{
                                "kind": "text",
                                "text": {
                                    "text": "@variables('voiceScript')",
                                    "sourceLocale": "en-US",
                                    "voiceKind": "Female"
                                }
                            }],
                            "playTo": ["all"]
                        }
                    },
                    "runAfter": {
                        "Place_Call_ACS": ["Succeeded"]
                    }
                },
                "Response": {
                    "type": "Response",
                    "kind": "Http",
                    "inputs": {
                        "statusCode": 200,
                        "body": {
                            "status": "success",
                            "message": "Voice call initiated",
                            "callId": "@{body('Place_Call_ACS')?['callConnectionId']}",
                            "timestamp": "@{utcNow()}"
                        }
                    },
                    "runAfter": {
                        "Play_TTS_Message": ["Succeeded"]
                    }
                }
            },
            "parameters": {
                "$connections": {
                    "defaultValue": {},
                    "type": "Object"
                },
                "cognitiveServicesEndpoint": {
                    "defaultValue": "",
                    "type": "String"
                }
            },
            "_metadata": {
                "customer": self.customer_name,
                "channel": "voice",
                "voice_channel_number": voice_channel_number,
                "default_script": asdict(voice_script),
                "requirements": [
                    "Azure Communication Services resource",
                    "Azure Cognitive Services (Speech) resource",
                    "Phone number provisioned in ACS",
                    "D365 Voice Channel configured"
                ]
            }
        }
        
        return flow_definition
    
    # =========================================
    # HTML CONTROL PANEL GENERATION
    # =========================================
    
    def generate_control_panel_html(self, flow_urls: Dict[str, str] = None) -> str:
        """
        Generate HTML control panel with simulation buttons.
        
        Args:
            flow_urls: Dict with keys 'email', 'chat', 'voice' containing 
                      Power Automate HTTP trigger URLs
        
        Returns:
            HTML string for embedding in demo execution guide
        """
        flow_urls = flow_urls or {}
        
        # Get scripts for button labels
        email_script = next((s for s in self.scripts if s.channel == "email"), None)
        chat_script = next((s for s in self.scripts if s.channel == "chat"), None)
        voice_script = next((s for s in self.scripts if s.channel == "voice"), None)
        
        email_label = f"📧 Send Email from {email_script.sender_name}" if email_script else "📧 Send Customer Email"
        chat_label = f"💬 Start Chat as {chat_script.sender_name}" if chat_script else "💬 Start Customer Chat"
        voice_label = f"📞 Call as {voice_script.sender_name}" if voice_script else "📞 Simulate Incoming Call"
        
        # Default placeholder URLs
        email_url = flow_urls.get("email", "YOUR_EMAIL_FLOW_URL")
        chat_url = flow_urls.get("chat", "YOUR_CHAT_FLOW_URL")
        voice_url = flow_urls.get("voice", "YOUR_VOICE_FLOW_URL")
        
        return f'''
    <!-- DEMO SIMULATION CONTROL PANEL -->
    <div class="simulation-panel" id="simPanel">
        <div class="sim-header" onclick="toggleSimPanel()">
            <span>🎮 Demo Simulation Controls</span>
            <span class="sim-toggle" id="simToggle">▼</span>
        </div>
        <div class="sim-body" id="simBody">
            <p class="sim-description">Click buttons to trigger simulated customer interactions via Power Automate.</p>
            
            <div class="sim-buttons">
                <button class="sim-btn email-btn" onclick="triggerSimulation('email')" title="Sends email to D365 queue">
                    {email_label}
                </button>
                <button class="sim-btn chat-btn" onclick="triggerSimulation('chat')" title="Triggers PAD to start chat">
                    {chat_label}
                </button>
                <button class="sim-btn voice-btn" onclick="triggerSimulation('voice')" title="Places call to Voice Channel">
                    {voice_label}
                </button>
            </div>
            
            <div class="sim-sequence">
                <label><input type="checkbox" id="autoSequence"> Auto-sequence (email → wait 2min → chat → wait 2min → call)</label>
                <button class="sim-btn sequence-btn" onclick="runFullSequence()" title="Run all simulations in order">
                    🎬 Run Full Demo Sequence
                </button>
            </div>
            
            <div class="sim-status" id="simStatus">
                Ready
            </div>
            
            <details class="sim-config">
                <summary>⚙️ Flow Configuration</summary>
                <div class="sim-config-body">
                    <label>Email Flow URL:</label>
                    <input type="text" id="emailFlowUrl" value="{email_url}" placeholder="Power Automate HTTP URL">
                    
                    <label>Chat Flow URL (or PAD trigger):</label>
                    <input type="text" id="chatFlowUrl" value="{chat_url}" placeholder="Power Automate HTTP URL">
                    
                    <label>Voice Flow URL:</label>
                    <input type="text" id="voiceFlowUrl" value="{voice_url}" placeholder="Power Automate HTTP URL">
                    
                    <button onclick="saveFlowConfig()" class="sim-save-btn">💾 Save Configuration</button>
                </div>
            </details>
        </div>
    </div>
'''
    
    def generate_control_panel_styles(self) -> str:
        """Generate CSS styles for the simulation control panel."""
        return '''
    /* Simulation Control Panel Styles */
    .simulation-panel {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 380px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        z-index: 9999;
        font-family: 'Segoe UI', sans-serif;
        color: #fff;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .simulation-panel.collapsed .sim-body {
        display: none;
    }
    
    .sim-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: rgba(255,255,255,0.1);
        cursor: pointer;
        font-weight: 600;
    }
    
    .sim-header:hover {
        background: rgba(255,255,255,0.15);
    }
    
    .sim-toggle {
        transition: transform 0.3s;
    }
    
    .simulation-panel.collapsed .sim-toggle {
        transform: rotate(-90deg);
    }
    
    .sim-body {
        padding: 16px;
    }
    
    .sim-description {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.7);
        margin-bottom: 16px;
    }
    
    .sim-buttons {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 16px;
    }
    
    .sim-btn {
        padding: 12px 16px;
        border: none;
        border-radius: 8px;
        font-size: 0.95rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }
    
    .sim-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .sim-btn:active {
        transform: translateY(0);
    }
    
    .sim-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
    }
    
    .email-btn {
        background: linear-gradient(135deg, #0078D4 0%, #005A9E 100%);
        color: white;
    }
    
    .chat-btn {
        background: linear-gradient(135deg, #107C10 0%, #0B5C0B 100%);
        color: white;
    }
    
    .voice-btn {
        background: linear-gradient(135deg, #D83B01 0%, #A52A00 100%);
        color: white;
    }
    
    .sequence-btn {
        background: linear-gradient(135deg, #5C2D91 0%, #3B1D5E 100%);
        color: white;
        width: 100%;
        text-align: center;
        margin-top: 8px;
    }
    
    .sim-sequence {
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 12px;
        margin-bottom: 12px;
    }
    
    .sim-sequence label {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.8);
        margin-bottom: 8px;
    }
    
    .sim-status {
        background: rgba(0,0,0,0.2);
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #4CAF50;
    }
    
    .sim-status.error {
        color: #f44336;
    }
    
    .sim-status.pending {
        color: #FFC107;
    }
    
    .sim-config {
        margin-top: 12px;
        font-size: 0.85rem;
    }
    
    .sim-config summary {
        cursor: pointer;
        color: rgba(255,255,255,0.7);
        padding: 8px 0;
    }
    
    .sim-config-body {
        padding: 12px;
        background: rgba(0,0,0,0.2);
        border-radius: 6px;
        margin-top: 8px;
    }
    
    .sim-config-body label {
        display: block;
        margin-bottom: 4px;
        color: rgba(255,255,255,0.7);
        font-size: 0.8rem;
    }
    
    .sim-config-body input {
        width: 100%;
        padding: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 4px;
        background: rgba(255,255,255,0.1);
        color: white;
        font-size: 0.85rem;
        margin-bottom: 12px;
    }
    
    .sim-save-btn {
        background: #0078D4;
        width: 100%;
        text-align: center;
    }
'''
    
    def generate_control_panel_script(self) -> str:
        """Generate JavaScript for simulation control panel."""
        # Get default scripts for payloads
        email_script = next((s for s in self.scripts if s.channel == "email"), None)
        chat_script = next((s for s in self.scripts if s.channel == "chat"), None)
        voice_script = next((s for s in self.scripts if s.channel == "voice"), None)
        
        email_payload = json.dumps(asdict(email_script)) if email_script else "{}"
        chat_payload = json.dumps(asdict(chat_script)) if chat_script else "{}"
        voice_payload = json.dumps(asdict(voice_script)) if voice_script else "{}"
        
        return f'''
    <script>
        // Demo Simulation Control Panel Script
        
        // Default payloads from demo story
        const defaultPayloads = {{
            email: {email_payload},
            chat: {chat_payload},
            voice: {voice_payload}
        }};
        
        // Load saved flow URLs from localStorage
        function loadFlowConfig() {{
            const saved = localStorage.getItem('demoSimFlowConfig');
            if (saved) {{
                const config = JSON.parse(saved);
                document.getElementById('emailFlowUrl').value = config.email || '';
                document.getElementById('chatFlowUrl').value = config.chat || '';
                document.getElementById('voiceFlowUrl').value = config.voice || '';
            }}
        }}
        
        // Save flow URLs to localStorage
        function saveFlowConfig() {{
            const config = {{
                email: document.getElementById('emailFlowUrl').value,
                chat: document.getElementById('chatFlowUrl').value,
                voice: document.getElementById('voiceFlowUrl').value
            }};
            localStorage.setItem('demoSimFlowConfig', JSON.stringify(config));
            updateStatus('Configuration saved!', 'success');
        }}
        
        // Toggle panel collapse
        function toggleSimPanel() {{
            document.getElementById('simPanel').classList.toggle('collapsed');
        }}
        
        // Update status display
        function updateStatus(message, type = 'success') {{
            const status = document.getElementById('simStatus');
            status.textContent = message;
            status.className = 'sim-status ' + type;
        }}
        
        // Trigger a simulation
        async function triggerSimulation(channel) {{
            const urlInput = document.getElementById(channel + 'FlowUrl');
            const url = urlInput ? urlInput.value : '';
            
            if (!url || url.includes('YOUR_')) {{
                updateStatus('⚠️ Configure ' + channel + ' flow URL first', 'error');
                return;
            }}
            
            updateStatus('🔄 Triggering ' + channel + ' simulation...', 'pending');
            
            // Disable button during call
            const buttons = document.querySelectorAll('.sim-btn');
            buttons.forEach(btn => btn.disabled = true);
            
            try {{
                const payload = defaultPayloads[channel] || {{}};
                
                const response = await fetch(url, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(payload)
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    updateStatus('✅ ' + channel.charAt(0).toUpperCase() + channel.slice(1) + ' triggered successfully!', 'success');
                }} else {{
                    throw new Error('HTTP ' + response.status);
                }}
            }} catch (error) {{
                updateStatus('❌ Failed: ' + error.message, 'error');
            }} finally {{
                buttons.forEach(btn => btn.disabled = false);
            }}
        }}
        
        // Run full sequence
        async function runFullSequence() {{
            updateStatus('🎬 Starting full demo sequence...', 'pending');
            
            const sequence = ['email', 'chat', 'voice'];
            const delays = [0, 120000, 120000]; // 0, 2min, 2min
            
            for (let i = 0; i < sequence.length; i++) {{
                if (i > 0) {{
                    updateStatus('⏳ Waiting 2 minutes before ' + sequence[i] + '...', 'pending');
                    await new Promise(resolve => setTimeout(resolve, delays[i]));
                }}
                await triggerSimulation(sequence[i]);
            }}
            
            updateStatus('🎉 Full sequence complete!', 'success');
        }}
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', loadFlowConfig);
    </script>
'''
    
    def get_full_control_panel(self, flow_urls: Dict[str, str] = None) -> str:
        """Get complete control panel with styles and scripts."""
        return (
            f"<style>{self.generate_control_panel_styles()}</style>\n"
            f"{self.generate_control_panel_html(flow_urls)}\n"
            f"{self.generate_control_panel_script()}"
        )


    # =========================================
    # DEMO ACTION PANEL (Extended Controls)
    # =========================================

    def generate_demo_action_panel(self, config: Dict[str, Any] = None) -> str:
        """
        Generate a full demo action panel with:
        - Simulation buttons (email, chat, voice) — original
        - D365 action buttons (notification, create case, SLA breach)
        - RAPP agent buttons (AI triage, analysis)
        - Configurable endpoint switching (Local / Azure Function / Power Automate)

        Args:
            config: Optional overrides with keys:
                - rapp_function_url: Azure Function base URL
                - rapp_function_key: Function auth key
                - flow_urls: Dict of Power Automate HTTP URLs per action
                - customer_name: Customer context for payloads
                - default_mode: 'local', 'azure', or 'power_automate'

        Returns:
            Complete HTML string (styles + markup + script) for embedding.
        """
        config = config or {}
        customer = config.get("customer_name", self.customer_name)
        default_mode = config.get("default_mode", "power_automate")
        rapp_url = config.get("rapp_function_url", "https://rapp-ov4bzgynnlvii.azurewebsites.net")
        rapp_key = config.get("rapp_function_key", "")
        flow_urls = config.get("flow_urls", {})

        # Build the panel HTML
        html = self._action_panel_styles()
        html += self._action_panel_html(customer, default_mode, rapp_url, rapp_key, flow_urls)
        html += self._action_panel_script(customer, default_mode, rapp_url, rapp_key, flow_urls)
        return html

    def _action_panel_styles(self) -> str:
        """CSS for the demo action panel."""
        return '''
<style>
    /* ===== Demo Action Panel ===== */
    .action-panel {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 420px;
        max-height: 90vh;
        overflow-y: auto;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        z-index: 9999;
        font-family: 'Segoe UI', sans-serif;
        color: #fff;
        transition: all 0.3s ease;
    }
    .action-panel.collapsed .ap-body { display: none; }
    .ap-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 16px; background: rgba(255,255,255,0.1);
        cursor: pointer; font-weight: 600; font-size: 0.95rem;
    }
    .ap-header:hover { background: rgba(255,255,255,0.15); }
    .ap-toggle { transition: transform 0.3s; }
    .action-panel.collapsed .ap-toggle { transform: rotate(-90deg); }
    .ap-body { padding: 16px; }
    .ap-section { margin-bottom: 16px; }
    .ap-section-title {
        font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;
        color: rgba(255,255,255,0.5); margin-bottom: 8px; padding-bottom: 4px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .ap-buttons { display: flex; flex-direction: column; gap: 8px; }
    .ap-btn {
        padding: 10px 14px; border: none; border-radius: 8px;
        font-size: 0.9rem; font-weight: 500; cursor: pointer;
        transition: all 0.2s; text-align: left; color: #fff;
    }
    .ap-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .ap-btn:active { transform: translateY(0); }
    .ap-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .ap-btn.sim-email { background: linear-gradient(135deg, #0078D4, #005A9E); }
    .ap-btn.sim-chat { background: linear-gradient(135deg, #107C10, #0B5C0B); }
    .ap-btn.sim-voice { background: linear-gradient(135deg, #D83B01, #A52A00); }
    .ap-btn.act-notify { background: linear-gradient(135deg, #FFB900, #E6A800); color: #1a1a2e; }
    .ap-btn.act-case { background: linear-gradient(135deg, #0078D4, #005A9E); }
    .ap-btn.act-sla-warn { background: linear-gradient(135deg, #FF8C00, #CC7000); }
    .ap-btn.act-sla-breach { background: linear-gradient(135deg, #E81123, #C50F1F); }
    .ap-btn.act-triage { background: linear-gradient(135deg, #5C2D91, #3B1D5E); }
    .ap-btn.act-sequence { background: linear-gradient(135deg, #5C2D91, #3B1D5E); width: 100%; text-align: center; }
    /* Mode Selector */
    .ap-mode-selector {
        display: flex; gap: 4px; margin-bottom: 12px;
        background: rgba(0,0,0,0.3); border-radius: 8px; padding: 4px;
    }
    .ap-mode-btn {
        flex: 1; padding: 6px 8px; border: none; border-radius: 6px;
        font-size: 0.75rem; font-weight: 600; cursor: pointer;
        background: transparent; color: rgba(255,255,255,0.6); transition: all 0.2s;
    }
    .ap-mode-btn.active { background: #0078D4; color: #fff; }
    .ap-mode-btn:hover:not(.active) { background: rgba(255,255,255,0.1); }
    /* Status */
    .ap-status {
        background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px;
        font-size: 0.85rem; color: #4CAF50; margin-top: 12px;
    }
    .ap-status.error { color: #f44336; }
    .ap-status.pending { color: #FFC107; }
    /* Config */
    .ap-config { margin-top: 12px; font-size: 0.85rem; }
    .ap-config summary { cursor: pointer; color: rgba(255,255,255,0.7); padding: 8px 0; }
    .ap-config-body {
        padding: 12px; background: rgba(0,0,0,0.2);
        border-radius: 6px; margin-top: 8px;
    }
    .ap-config-body label {
        display: block; margin-bottom: 4px; color: rgba(255,255,255,0.7); font-size: 0.8rem;
    }
    .ap-config-body input, .ap-config-body select {
        width: 100%; padding: 8px; border: 1px solid rgba(255,255,255,0.2);
        border-radius: 4px; background: rgba(255,255,255,0.1);
        color: white; font-size: 0.85rem; margin-bottom: 12px; box-sizing: border-box;
    }
    .ap-save-btn {
        background: #0078D4; width: 100%; text-align: center;
        padding: 8px; border: none; border-radius: 6px; color: #fff;
        font-weight: 600; cursor: pointer;
    }
    .ap-save-btn:hover { background: #106EBE; }
    /* Log area */
    .ap-log {
        max-height: 120px; overflow-y: auto; font-family: 'Cascadia Code', monospace;
        font-size: 0.75rem; line-height: 1.4; background: rgba(0,0,0,0.3);
        padding: 8px; border-radius: 6px; margin-top: 8px; color: rgba(255,255,255,0.7);
    }
    .ap-log .log-success { color: #4CAF50; }
    .ap-log .log-error { color: #f44336; }
    .ap-log .log-info { color: #64B5F6; }
</style>
'''

    def _action_panel_html(self, customer: str, default_mode: str,
                           rapp_url: str, rapp_key: str,
                           flow_urls: Dict[str, str]) -> str:
        """HTML markup for the panel."""
        # Get script labels
        email_script = next((s for s in self.scripts if s.channel == "email"), None)
        chat_script = next((s for s in self.scripts if s.channel == "chat"), None)
        voice_script = next((s for s in self.scripts if s.channel == "voice"), None)

        email_label = f"Send Email from {email_script.sender_name}" if email_script else "Send Customer Email"
        chat_label = f"Start Chat as {chat_script.sender_name}" if chat_script else "Start Customer Chat"
        voice_label = f"Call as {voice_script.sender_name}" if voice_script else "Simulate Incoming Call"

        mode_local = "active" if default_mode == "local" else ""
        mode_azure = "active" if default_mode == "azure" else ""
        mode_pa = "active" if default_mode == "power_automate" else ""

        return f'''
<!-- DEMO ACTION PANEL -->
<div class="action-panel" id="actionPanel">
    <div class="ap-header" onclick="toggleActionPanel()">
        <span>&#127918; Demo Action Panel &mdash; {customer}</span>
        <span class="ap-toggle" id="apToggle">&#9660;</span>
    </div>
    <div class="ap-body" id="apBody">
        <!-- MODE SELECTOR -->
        <div class="ap-mode-selector">
            <button class="ap-mode-btn {mode_local}" data-mode="local" onclick="setMode('local')"
                title="Calls localhost:7071 (func start must be running)">&#128187; Local</button>
            <button class="ap-mode-btn {mode_azure}" data-mode="azure" onclick="setMode('azure')"
                title="Calls deployed Azure Function App">&#9729;&#65039; Azure Fn</button>
            <button class="ap-mode-btn {mode_pa}" data-mode="power_automate" onclick="setMode('power_automate')"
                title="Calls Power Automate HTTP-triggered flows">&#9889; Power Automate</button>
        </div>

        <!-- SIMULATION -->
        <div class="ap-section">
            <div class="ap-section-title">Channel Simulation</div>
            <div class="ap-buttons">
                <button class="ap-btn sim-email" onclick="fireAction('sim_email')">&#128231; {email_label}</button>
                <button class="ap-btn sim-chat" onclick="fireAction('sim_chat')">&#128172; {chat_label}</button>
                <button class="ap-btn sim-voice" onclick="fireAction('sim_voice')">&#128222; {voice_label}</button>
            </div>
        </div>

        <!-- D365 ACTIONS -->
        <div class="ap-section">
            <div class="ap-section-title">D365 Actions</div>
            <div class="ap-buttons">
                <button class="ap-btn act-notify" onclick="fireAction('send_notification')">&#128276; Entrapment Alert</button>
                <button class="ap-btn act-case" onclick="fireAction('create_case')">&#128203; Create Entrapment Case</button>
                <button class="ap-btn act-sla-warn" onclick="fireAction('sla_warning')">&#9888;&#65039; Marriott SLA Warning</button>
                <button class="ap-btn act-sla-breach" onclick="fireAction('sla_breach')">&#128680; Marriott SLA Breach</button>
            </div>
        </div>

        <!-- RAPP AGENT ACTIONS -->
        <div class="ap-section">
            <div class="ap-section-title">RAPP Agent Actions</div>
            <div class="ap-buttons">
                <button class="ap-btn act-triage" onclick="fireAction('ai_triage')">&#129302; Triage Canary Wharf Door Issue</button>
                <button class="ap-btn act-sequence" onclick="runDemoSequence()">&#127916; Run Full Demo Sequence</button>
            </div>
        </div>

        <!-- STATUS -->
        <div class="ap-status" id="apStatus">Ready</div>

        <!-- LOG -->
        <div class="ap-log" id="apLog"></div>

        <!-- CONFIG -->
        <details class="ap-config">
            <summary>&#9881;&#65039; Endpoint Configuration</summary>
            <div class="ap-config-body">
                <label>RAPP Function App URL:</label>
                <input type="text" id="cfgRappUrl" value="{rapp_url}" placeholder="https://your-func.azurewebsites.net">

                <label>Function Key:</label>
                <input type="password" id="cfgRappKey" value="{rapp_key}" placeholder="Function auth key">

                <label>Local Dev URL:</label>
                <input type="text" id="cfgLocalUrl" value="http://localhost:7071" placeholder="http://localhost:7071">

                <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                <label style="font-weight:600;">Power Automate Flow URLs:</label>

                <label>Email Flow:</label>
                <input type="text" id="cfgFlowEmail" value="{flow_urls.get('email', '')}" placeholder="Power Automate HTTP URL">

                <label>Chat Flow:</label>
                <input type="text" id="cfgFlowChat" value="{flow_urls.get('chat', '')}" placeholder="Power Automate HTTP URL">

                <label>Voice Flow:</label>
                <input type="text" id="cfgFlowVoice" value="{flow_urls.get('voice', '')}" placeholder="Power Automate HTTP URL">

                <label>Notification Flow:</label>
                <input type="text" id="cfgFlowNotify" value="{flow_urls.get('notification', '')}" placeholder="Power Automate HTTP URL">

                <label>Create Case Flow:</label>
                <input type="text" id="cfgFlowCase" value="{flow_urls.get('create_case', '')}" placeholder="Power Automate HTTP URL">

                <label>SLA Breach Flow:</label>
                <input type="text" id="cfgFlowSla" value="{flow_urls.get('sla_breach', '')}" placeholder="Power Automate HTTP URL">

                <button class="ap-save-btn" onclick="saveActionConfig()">&#128190; Save Configuration</button>
            </div>
        </details>
    </div>
</div>
'''

    def _action_panel_script(self, customer: str, default_mode: str,
                             rapp_url: str, rapp_key: str,
                             flow_urls: Dict[str, str]) -> str:
        """JavaScript for the demo action panel."""
        # Build default payloads from scripts
        email_script = next((s for s in self.scripts if s.channel == "email"), None)
        chat_script = next((s for s in self.scripts if s.channel == "chat"), None)
        voice_script = next((s for s in self.scripts if s.channel == "voice"), None)

        email_payload = json.dumps(asdict(email_script)) if email_script else "{}"
        chat_payload = json.dumps(asdict(chat_script)) if chat_script else "{}"
        voice_payload = json.dumps(asdict(voice_script)) if voice_script else "{}"

        return f'''
<script>
(function() {{
    "use strict";

    // ── State ───────────────────────────────────────────
    let currentMode = "{default_mode}";
    const STORAGE_KEY = "demoActionPanelConfig";

    // ── Action Definitions ──────────────────────────────
    // Each action defines payloads per mode.
    const ACTIONS = {{
        // Channel simulations — use trigger system (existing)
        sim_email: {{
            label: "Email Simulation",
            local:  {{ method: "POST", path: "/api/trigger/manual/sim_email", body: {email_payload} }},
            azure:  {{ method: "POST", path: "/api/trigger/manual/sim_email", body: {email_payload} }},
            power_automate: {{ flowKey: "email", body: {email_payload} }}
        }},
        sim_chat: {{
            label: "Chat Simulation",
            local:  {{ method: "POST", path: "/api/trigger/manual/sim_chat", body: {chat_payload} }},
            azure:  {{ method: "POST", path: "/api/trigger/manual/sim_chat", body: {chat_payload} }},
            power_automate: {{ flowKey: "chat", body: {chat_payload} }}
        }},
        sim_voice: {{
            label: "Voice Simulation",
            local:  {{ method: "POST", path: "/api/trigger/manual/sim_voice", body: {voice_payload} }},
            azure:  {{ method: "POST", path: "/api/trigger/manual/sim_voice", body: {voice_payload} }},
            power_automate: {{ flowKey: "voice", body: {voice_payload} }}
        }},
        // D365 actions — use dedicated /api/demo/* endpoints (fast, direct)
        // Wired to Otis EMEA hero accounts & demo scenarios
        send_notification: {{
            label: "🔔 Entrapment Alert",
            local:  {{ method: "POST", path: "/api/demo/notification",
                       body: {{ scenario: "NewCase",
                               recipient_email: "admin@D365DemoTSCE30330346.onmicrosoft.com",
                               case_title: "ENTRAPMENT - Riverside Medical Centre Elevator 3",
                               customer: "Riverside Medical Centre" }} }},
            azure:  {{ method: "POST", path: "/api/demo/notification",
                       body: {{ scenario: "NewCase",
                               recipient_email: "admin@D365DemoTSCE30330346.onmicrosoft.com",
                               case_title: "ENTRAPMENT - Riverside Medical Centre Elevator 3",
                               customer: "Riverside Medical Centre" }} }},
            power_automate: {{ flowKey: "notification",
                              body: {{ scenario: "NewCase",
                                      recipient_email: "admin@D365DemoTSCE30330346.onmicrosoft.com",
                                      case_title: "ENTRAPMENT - Riverside Medical Centre Elevator 3",
                                      customer: "Riverside Medical Centre" }} }}
        }},
        create_case: {{
            label: "📋 Create Entrapment Case",
            local:  {{ method: "POST", path: "/api/demo/create-case",
                       body: {{ title: "Entrapment - Passenger stuck in Elevator 3",
                               customer_name: "Riverside Medical Centre", priority: 1, origin: "phone",
                               description: "Patient transport staff trapped in Elevator 3 between floors 2 and 3. Bed elevator essential for patient movement. Hospital security on scene." }} }},
            azure:  {{ method: "POST", path: "/api/demo/create-case",
                       body: {{ title: "Entrapment - Passenger stuck in Elevator 3",
                               customer_name: "Riverside Medical Centre", priority: 1, origin: "phone",
                               description: "Patient transport staff trapped in Elevator 3 between floors 2 and 3. Bed elevator essential for patient movement. Hospital security on scene." }} }},
            power_automate: {{ flowKey: "create_case",
                              body: {{ title: "Entrapment - Passenger stuck in Elevator 3",
                                      customer_name: "Riverside Medical Centre", priority: 1, origin: 1 }} }}
        }},
        sla_warning: {{
            label: "⚠️ SLA Warning — Marriott Billing",
            local:  {{ method: "POST", path: "/api/demo/sla-breach",
                       body: {{ breach_type: "warning", send_notification: true,
                               case_number: "CAS-19129-N0B2P3" }} }},
            azure:  {{ method: "POST", path: "/api/demo/sla-breach",
                       body: {{ breach_type: "warning", send_notification: true,
                               case_number: "CAS-19129-N0B2P3" }} }},
            power_automate: {{ flowKey: "sla_breach",
                              body: {{ breach_type: "warning", send_notification: true }} }}
        }},
        sla_breach: {{
            label: "🚨 SLA Breach — Marriott Billing",
            local:  {{ method: "POST", path: "/api/demo/sla-breach",
                       body: {{ breach_type: "violated", send_notification: true,
                               case_number: "CAS-19129-N0B2P3" }} }},
            azure:  {{ method: "POST", path: "/api/demo/sla-breach",
                       body: {{ breach_type: "violated", send_notification: true,
                               case_number: "CAS-19129-N0B2P3" }} }},
            power_automate: {{ flowKey: "sla_breach",
                              body: {{ breach_type: "violated", send_notification: true }} }}
        }},
        ai_triage: {{
            label: "🤖 AI Triage — Canary Wharf Door Issue",
            local:  {{ method: "POST", path: "/api/demo/ai-triage",
                       body: {{ action: "triage_case", customer: "Canary Wharf Tower",
                               case_title: "Recurring Door Issue - Tower A Elevator 12" }} }},
            azure:  {{ method: "POST", path: "/api/demo/ai-triage",
                       body: {{ action: "triage_case", customer: "Canary Wharf Tower",
                               case_title: "Recurring Door Issue - Tower A Elevator 12" }} }},
            power_automate: null  // No PA flow for AI — falls back to Azure
        }}
    }};

    // ── Helpers ──────────────────────────────────────────
    function $(id) {{ return document.getElementById(id); }}

    function appendLog(msg, type) {{
        const log = $("apLog");
        const ts = new Date().toLocaleTimeString();
        const cls = type === "error" ? "log-error" : type === "success" ? "log-success" : "log-info";
        log.innerHTML += '<div class="' + cls + '">[' + ts + '] ' + msg + '</div>';
        log.scrollTop = log.scrollHeight;
    }}

    function setStatus(msg, type) {{
        const s = $("apStatus");
        s.textContent = msg;
        s.className = "ap-status " + (type || "");
    }}

    // ── Mode Selector ───────────────────────────────────
    window.setMode = function(mode) {{
        currentMode = mode;
        document.querySelectorAll(".ap-mode-btn").forEach(b => {{
            b.classList.toggle("active", b.dataset.mode === mode);
        }});
        const labels = {{ local: "Local (localhost:7071)", azure: "Azure Function App", power_automate: "Power Automate" }};
        setStatus("Mode: " + labels[mode]);
        appendLog("Switched to " + labels[mode], "info");
        saveActionConfig();
    }};

    // ── Toggle Panel ────────────────────────────────────
    window.toggleActionPanel = function() {{
        $("actionPanel").classList.toggle("collapsed");
    }};

    // ── Fire Action ─────────────────────────────────────
    window.fireAction = async function(actionKey) {{
        const action = ACTIONS[actionKey];
        if (!action) {{ setStatus("Unknown action: " + actionKey, "error"); return; }}

        const mode = currentMode;
        let spec = action[mode];

        // Fallback: if PA has no flow for this action, try Azure
        if (!spec && mode === "power_automate") {{
            spec = action.azure;
            appendLog(action.label + ": no PA flow, falling back to Azure", "info");
        }}

        if (!spec) {{ setStatus("No config for " + actionKey + " in " + mode, "error"); return; }}

        setStatus("Firing " + action.label + "...", "pending");
        appendLog("→ " + action.label + " [" + mode + "]", "info");

        // Disable all buttons during call
        document.querySelectorAll(".ap-btn").forEach(b => b.disabled = true);

        try {{
            let url, headers = {{ "Content-Type": "application/json" }}, body = spec.body;

            if (mode === "power_automate" && spec.flowKey) {{
                // Use Power Automate flow URL from config
                const flowUrlMap = {{
                    email: $("cfgFlowEmail")?.value,
                    chat: $("cfgFlowChat")?.value,
                    voice: $("cfgFlowVoice")?.value,
                    notification: $("cfgFlowNotify")?.value,
                    create_case: $("cfgFlowCase")?.value,
                    sla_breach: $("cfgFlowSla")?.value
                }};
                url = flowUrlMap[spec.flowKey];
                if (!url) {{
                    throw new Error("Configure " + spec.flowKey + " flow URL in settings");
                }}
            }} else {{
                // Local or Azure — build URL from base + path
                const base = (mode === "local")
                    ? ($("cfgLocalUrl")?.value || "http://localhost:7071")
                    : ($("cfgRappUrl")?.value || "{rapp_url}");
                url = base + spec.path;
                const key = $("cfgRappKey")?.value || "{rapp_key}";
                if (key) {{ url += (url.includes("?") ? "&" : "?") + "code=" + encodeURIComponent(key); }}
            }}

            const resp = await fetch(url, {{
                method: spec.method || "POST",
                headers: headers,
                body: JSON.stringify(body)
            }});

            if (resp.ok) {{
                const result = await resp.json().catch(() => ({{}}));
                setStatus("\\u2705 " + action.label + " succeeded", "");
                appendLog("\\u2705 " + action.label + ": " + (result.message || result.status || "OK"), "success");
            }} else {{
                throw new Error("HTTP " + resp.status + " " + resp.statusText);
            }}
        }} catch (err) {{
            setStatus("\\u274c " + action.label + " failed: " + err.message, "error");
            appendLog("\\u274c " + action.label + ": " + err.message, "error");
        }} finally {{
            document.querySelectorAll(".ap-btn").forEach(b => b.disabled = false);
        }}
    }};

    // ── Demo Sequence ───────────────────────────────────
    window.runDemoSequence = async function() {{
        setStatus("Running full demo sequence...", "pending");
        appendLog("\\u25b6 Starting demo sequence", "info");

        const steps = [
            {{ action: "create_case", delay: 0 }},
            {{ action: "send_notification", delay: 3000 }},
            {{ action: "sim_email", delay: 5000 }},
            {{ action: "sla_warning", delay: 60000 }},
            {{ action: "sla_breach", delay: 120000 }},
            {{ action: "ai_triage", delay: 5000 }}
        ];

        for (let i = 0; i < steps.length; i++) {{
            if (steps[i].delay > 0) {{
                const sec = Math.round(steps[i].delay / 1000);
                setStatus("Waiting " + sec + "s before " + steps[i].action + "...", "pending");
                await new Promise(r => setTimeout(r, steps[i].delay));
            }}
            await fireAction(steps[i].action);
        }}

        setStatus("\\ud83c\\udf89 Demo sequence complete!", "");
        appendLog("\\u2705 Full sequence finished", "success");
    }};

    // ── Config Persistence ──────────────────────────────
    window.saveActionConfig = function() {{
        const cfg = {{
            mode: currentMode,
            rappUrl: $("cfgRappUrl")?.value,
            rappKey: $("cfgRappKey")?.value,
            localUrl: $("cfgLocalUrl")?.value,
            flows: {{
                email: $("cfgFlowEmail")?.value,
                chat: $("cfgFlowChat")?.value,
                voice: $("cfgFlowVoice")?.value,
                notification: $("cfgFlowNotify")?.value,
                create_case: $("cfgFlowCase")?.value,
                sla_breach: $("cfgFlowSla")?.value
            }}
        }};
        localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
        appendLog("Configuration saved", "info");
    }};

    function loadActionConfig() {{
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        try {{
            const cfg = JSON.parse(raw);
            if (cfg.mode) setMode(cfg.mode);
            if (cfg.rappUrl && $("cfgRappUrl")) $("cfgRappUrl").value = cfg.rappUrl;
            if (cfg.rappKey && $("cfgRappKey")) $("cfgRappKey").value = cfg.rappKey;
            if (cfg.localUrl && $("cfgLocalUrl")) $("cfgLocalUrl").value = cfg.localUrl;
            if (cfg.flows) {{
                if (cfg.flows.email && $("cfgFlowEmail")) $("cfgFlowEmail").value = cfg.flows.email;
                if (cfg.flows.chat && $("cfgFlowChat")) $("cfgFlowChat").value = cfg.flows.chat;
                if (cfg.flows.voice && $("cfgFlowVoice")) $("cfgFlowVoice").value = cfg.flows.voice;
                if (cfg.flows.notification && $("cfgFlowNotify")) $("cfgFlowNotify").value = cfg.flows.notification;
                if (cfg.flows.create_case && $("cfgFlowCase")) $("cfgFlowCase").value = cfg.flows.create_case;
                if (cfg.flows.sla_breach && $("cfgFlowSla")) $("cfgFlowSla").value = cfg.flows.sla_breach;
            }}
            appendLog("Config loaded from localStorage", "info");
        }} catch(e) {{ /* ignore bad config */ }}
    }}

    // ── Init ────────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", loadActionConfig);
}})();
</script>
'''


def generate_copilot_studio_customer_agent() -> Dict[str, Any]:
    """
    Generate Copilot Studio agent YAML for a "Customer Simulator" agent.
    
    This agent can be used from a mobile device to simulate being the customer
    during a demo, sending scripted messages to the chat channel.
    """
    return {
        "name": "Demo Customer Simulator",
        "description": "Acts as a simulated customer for D365 Customer Service demos. Use from mobile device to send scripted messages.",
        "instructions": """You are a customer simulator for demos. When the user says a command like:
- "angry email" → Generate and send an angry customer email
- "order inquiry" → Ask about an order
- "escalate" → Request to speak with a supervisor
- "warranty question" → Ask about warranty coverage

Generate realistic customer messages based on the command. Use provided context about the customer name and account.""",
        "topics": [
            {
                "name": "Email Simulation",
                "trigger_phrases": ["send email", "angry email", "urgent email", "email simulation"],
                "actions": ["Generate email content", "Trigger email flow via HTTP"]
            },
            {
                "name": "Chat Simulation", 
                "trigger_phrases": ["start chat", "chat as customer", "portal chat"],
                "actions": ["Open portal in browser", "Type scripted messages"]
            },
            {
                "name": "Voice Script",
                "trigger_phrases": ["call script", "voice script", "what do I say"],
                "actions": ["Display voice script for human to read", "Optionally trigger TTS call"]
            }
        ],
        "knowledge": {
            "demo_scripts": "Loaded from demo execution guide",
            "customer_personas": "Marcus, Patricia, Rachel - with their scenarios"
        }
    }
