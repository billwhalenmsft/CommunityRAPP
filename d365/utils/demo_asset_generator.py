"""
Demo Asset Generator
====================
Generates complete, connected demo assets for D365 Customer Service demos:
- Demo Execution Guide (HTML) - Click-by-click playbook for Solution Engineers
- Pre-flight Checklist
- Hero Records Reference
- Talk Tracks and Scripts
- Data Validation Report

All assets are generated from the input schema and demo data to ensure
the story is coherent, all data references are valid, and the demo flows perfectly.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import scenario modules for section content
try:
    from d365.scenarios.phone_call import get_phone_demo_section
    from d365.scenarios.chat_conversation import get_chat_demo_section
    from d365.scenarios.email_samples import get_email_demo_section
    from d365.scenarios.order_management import get_order_demo_section
    from d365.scenarios.shipment_tracking import get_shipment_demo_section
    from d365.scenarios.rma_return import get_rma_demo_section
    from d365.scenarios.warranty import get_warranty_demo_section
    SCENARIOS_AVAILABLE = True
except ImportError:
    SCENARIOS_AVAILABLE = False

# Import demo simulator for control panel
try:
    from d365.utils.demo_simulator import DemoSimulator
    SIMULATOR_AVAILABLE = True
except ImportError:
    SIMULATOR_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoAssetGenerator:
    """Generates connected demo assets from input schema and demo data."""

    # Demo section templates by use case
    USE_CASE_SECTIONS = {
        "telephony_screen_pop": [
            {"id": "connect", "title": "Connect & Orient", "time": 10, "color": "#0078D4", "purpose": "Build connection, set the frame, brief UI orientation"},
            {"id": "challenges", "title": "Their World Today", "time": 5, "color": "#D83B01", "purpose": "Acknowledge pain points without dwelling"},
            {"id": "screen_pop", "title": "Incoming Call — Screen Pop Hero Moment", "time": 20, "color": "#107C10", "purpose": "HERO: Show instant customer context on incoming call"},
            {"id": "case_handling", "title": "Live Case Resolution", "time": 15, "color": "#107C10", "purpose": "Demonstrate case creation and customer context"},
            {"id": "productivity_toolkit", "title": "Service Toolkit — Guided Actions", "time": 15, "color": "#5C2D91", "purpose": "Agent scripts, macros, and side-pane wizards"},
            {"id": "copilot", "title": "Copilot Assistance", "time": 10, "color": "#5C2D91", "purpose": "AI-powered suggestions and knowledge"},
            {"id": "wrap_up", "title": "Call Wrap-Up & Notes", "time": 5, "color": "#107C10", "purpose": "Show efficient after-call work"},
            {"id": "supervisor", "title": "Supervisor View", "time": 10, "color": "#008575", "purpose": "Dashboards, analytics, agent performance"},
            {"id": "close", "title": "Close & Next Steps", "time": 5, "color": "#005A9E", "purpose": "Summarize value, discuss next steps"}
        ],
        "omnichannel_routing": [
            {"id": "connect", "title": "Connect & Orient", "time": 10, "color": "#0078D4", "purpose": "Build connection, set the frame"},
            {"id": "challenges", "title": "Current Challenges", "time": 5, "color": "#D83B01", "purpose": "Fragmented channels, manual routing"},
            {"id": "email", "title": "Email Arrives — Auto Case Creation", "time": 10, "color": "#107C10", "purpose": "Show email-to-case automation"},
            {"id": "phone", "title": "Phone Call — Intelligent Routing", "time": 20, "color": "#A4262C", "purpose": "Skill-based routing, screen pop"},
            {"id": "chat", "title": "Chat — Bot Triage & Escalation", "time": 15, "color": "#008575", "purpose": "Self-service to agent handoff"},
            {"id": "unified_view", "title": "Unified Customer Timeline", "time": 10, "color": "#107C10", "purpose": "All channels in one view"},
            {"id": "supervisor", "title": "Supervisor Analytics", "time": 10, "color": "#008575", "purpose": "Cross-channel insights"},
            {"id": "close", "title": "Close & Next Steps", "time": 5, "color": "#005A9E", "purpose": "Summarize, next steps"}
        ],
        "case_management": [
            {"id": "connect", "title": "Connect & Orient", "time": 10, "color": "#0078D4", "purpose": "Build connection, UI overview"},
            {"id": "challenges", "title": "Current Pain Points", "time": 5, "color": "#D83B01", "purpose": "Manual processes, no visibility"},
            {"id": "case_queue", "title": "My Active Cases", "time": 10, "color": "#107C10", "purpose": "Queue management, prioritization"},
            {"id": "case_work", "title": "Case Resolution Workflow", "time": 20, "color": "#107C10", "purpose": "Full case lifecycle"},
            {"id": "sla", "title": "SLA Management", "time": 10, "color": "#D83B01", "purpose": "Timer visibility, escalations"},
            {"id": "knowledge", "title": "Knowledge Integration", "time": 10, "color": "#5C2D91", "purpose": "KB search, article linking"},
            {"id": "supervisor", "title": "Manager Dashboards", "time": 10, "color": "#008575", "purpose": "Team performance, metrics"},
            {"id": "close", "title": "Close & Next Steps", "time": 5, "color": "#005A9E", "purpose": "Value summary"}
        ],
        "full_ccaas": [
            {"id": "connect", "title": "Connect & Orient", "time": 10, "color": "#0078D4", "purpose": "Build connection, set the frame"},
            {"id": "challenges", "title": "Their World Today", "time": 5, "color": "#D83B01", "purpose": "Acknowledge pain points"},
            {"id": "email", "title": "Email Channel", "time": 10, "color": "#107C10", "purpose": "Auto case creation, routing"},
            {"id": "phone", "title": "Voice Channel — Screen Pop", "time": 25, "color": "#A4262C", "purpose": "HERO: Incoming call with context"},
            {"id": "chat", "title": "Chat Channel — Bot + Agent", "time": 20, "color": "#008575", "purpose": "Self-service to escalation"},
            {"id": "copilot", "title": "Copilot AI Assistance", "time": 10, "color": "#5C2D91", "purpose": "Suggestions, summaries, KB"},
            {"id": "supervisor", "title": "Care Leader View", "time": 15, "color": "#008575", "purpose": "Dashboards, WFM, QM"},
            {"id": "ai_agents", "title": "AI Agents Reveal", "time": 10, "color": "#5C2D91", "purpose": "Show agent architecture"},
            {"id": "close", "title": "Close & Next Steps", "time": 5, "color": "#005A9E", "purpose": "Summarize value"}
        ]
    }

    def __init__(self):
        """Initialize the generator."""
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def generate_all_assets(
        self,
        customer_name: str,
        inputs: Dict[str, Any],
        demo_data: Dict[str, Any],
        environment_config: Dict[str, Any],
        output_dir: Path
    ) -> Dict[str, str]:
        """Generate all demo assets and return paths to created files."""
        results = {}

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate Demo Execution Guide (HTML)
        guide_path = output_dir / "demo-execution-guide.html"
        guide_html = self.generate_execution_guide(customer_name, inputs, demo_data, environment_config)
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(guide_html)
        results["execution_guide"] = str(guide_path)
        logger.info(f"Generated: {guide_path}")

        # 2. Generate Scenario Scripts (Markdown)
        if SCENARIOS_AVAILABLE:
            scenarios_dir = output_dir / "scenarios"
            scenario_paths = self._generate_scenario_scripts(customer_name, inputs, scenarios_dir)
            results["scenarios"] = scenario_paths
            logger.info(f"Generated {len(scenario_paths)} scenario scripts")

        # 3. Generate Data Validation Report
        validation_path = output_dir / "data-validation-report.html"
        validation_html = self.generate_validation_report(customer_name, demo_data, environment_config)
        with open(validation_path, "w", encoding="utf-8") as f:
            f.write(validation_html)
        results["validation_report"] = str(validation_path)
        logger.info(f"Generated: {validation_path}")

        # 3. Generate Quick Reference Card
        quickref_path = output_dir / "quick-reference.html"
        quickref_html = self.generate_quick_reference(customer_name, inputs, demo_data, environment_config)
        with open(quickref_path, "w", encoding="utf-8") as f:
            f.write(quickref_html)
        results["quick_reference"] = str(quickref_path)
        logger.info(f"Generated: {quickref_path}")

        return results

    def _generate_scenario_scripts(
        self,
        customer_name: str,
        inputs: Dict[str, Any],
        output_dir: Path
    ) -> Dict[str, str]:
        """Generate all scenario scripts as Markdown files."""
        from d365.scenarios import generate_all_scenarios
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build config for scenarios from inputs
        config = {
            "demo": {
                "brands": inputs.get("customer", {}).get("brands", ["Customer"]),
                "support_email": inputs.get("demo_requirements", {}).get("support_email", "support@company.com"),
                "hot_words": inputs.get("demo_requirements", {}).get("hot_words", []),
                "erp_system": inputs.get("customer", {}).get("erp_system", "ERP"),
                "warranty": inputs.get("demo_requirements", {}).get("warranty", {})
            },
            "demo_story": inputs.get("demo_story", {}),
            "customer": inputs.get("customer", {})
        }
        
        # Generate all available scenarios
        paths = generate_all_scenarios(config, customer_name, output_dir)
        
        return {k: str(v) for k, v in paths.items()}

    def generate_execution_guide(
        self,
        customer_name: str,
        inputs: Dict[str, Any],
        demo_data: Dict[str, Any],
        environment_config: Dict[str, Any]
    ) -> str:
        """Generate the main demo execution guide HTML."""
        customer_info = inputs.get("customer", {})
        discovery = inputs.get("discovery", {})
        demo_reqs = inputs.get("demo_requirements", {})
        metadata = inputs.get("metadata", {})

        # Get use case sections
        use_case = discovery.get("use_case", "telephony_screen_pop")
        sections = self.USE_CASE_SECTIONS.get(use_case, self.USE_CASE_SECTIONS["telephony_screen_pop"])

        # Calculate total time
        total_time = sum(s["time"] for s in sections)

        # Build the story
        story = self._build_demo_story(customer_name, inputs, demo_data)

        # Build hero records reference
        hero_records = self._build_hero_records(demo_data)

        # Build preflight checklist
        preflight = self._build_preflight_checklist(environment_config, demo_data)

        # Build section content
        section_html = self._build_sections(sections, story, demo_data, discovery)

        # Get brand colors
        brand_colors = self._get_brand_colors(customer_info.get("industry", "other"))

        # Demo date
        demo_date = metadata.get("demo_date", datetime.now().strftime("%Y-%m-%d"))

        # Persona info
        persona = story.get("agent_persona", {"name": "Agent", "role": "CSR"})

        # Generate simulation control panel and cheat sheet if available
        cheat_sheet_content = ""
        simulation_scripts = ""
        if SIMULATOR_AVAILABLE:
            try:
                simulator = DemoSimulator({
                    "customer_name": customer_name,
                    "brands": customer_info.get("brands", []),
                    "demo_story": inputs.get("demo_story", {}),
                    "environment": environment_config.get("environment", {}),
                    "simulation": inputs.get("simulation", {})
                })
                cheat_sheet_content = self._build_cheat_sheet(
                    simulator, story, demo_data, environment_config
                )
                simulation_scripts = simulator.generate_control_panel_script()
            except Exception as e:
                logger.warning(f"Could not generate simulation panel: {e}")
                cheat_sheet_content = self._build_cheat_sheet_fallback(story, demo_data, environment_config)
                simulation_scripts = ""
        else:
            cheat_sheet_content = self._build_cheat_sheet_fallback(story, demo_data, environment_config)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{customer_info.get("name", customer_name)} — Demo Execution Guide</title>
    {self._get_styles_3col(brand_colors)}
</head>
<body class="three-column">

    <!-- FLOATING RESTORE BUTTONS (appear when panels collapsed) -->
    <button class="nav-restore" id="navRestore" title="Show Navigation">☰</button>
    <button class="cheat-restore" id="cheatRestore" title="Show Controls">🎮</button>

    <!-- LEFT: SIDE NAV (grid-column: 1) -->
    <aside class="side-nav" id="sideNav">
        <div class="side-nav-header">
            <strong>☰ Sections</strong>
            <button class="side-nav-pin" id="navPin" title="Hide Navigation">✕</button>
        </div>
        <div class="side-nav-body" id="navBody"></div>
    </aside>

    <!-- CENTER: MAIN CONTENT (grid-column: 2) -->
    <main class="main-content">
        <!-- HERO -->
        <header class="hero">
            <h1>Demo Execution Guide</h1>
            <p class="subtitle">{customer_info.get("name", customer_name)} — Customer Service — Click-by-Click Playbook</p>
            <div class="meta">
                <span>&#128197; {demo_date} — {total_time} Minutes</span>
                <span>&#127919; {self._get_use_case_tagline(use_case)}</span>
                <span>&#128100; You are <strong>{persona["name"]}</strong> ({persona["role"]})</span>
            </div>
            <div class="hero-badge">Prescriptive — Every Click, Every Word</div>
        </header>

        <div class="container">

            <!-- TIMING BAR -->
            <p class="section-label">Session Timing</p>
            {self._build_timing_bar(sections)}

            <!-- THE STORY -->
            {self._build_story_block(story)}

            <!-- PRE-FLIGHT CHECKLIST -->
            {preflight}

            <!-- DEMO SECTIONS -->
            <p class="section-label">Demo Flow</p>
            {section_html}

        </div>

        <footer>
            <p>Generated by RAPP D365 Demo Orchestration — {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
            <p>For internal use only. Contains demo data and scripts.</p>
        </footer>
    </main>

    <!-- RIGHT: CHEAT SHEET (grid-column: 3) -->
    <aside class="cheat-sheet" id="cheatSheet">
        <div class="cheat-sheet-header">
            <strong>🎮 Controls & Quick Ref</strong>
            <button class="cheat-sheet-toggle" id="cheatToggle" title="Hide Controls">✕</button>
        </div>
        <div class="cheat-sheet-body">
            {cheat_sheet_content}
        </div>
    </aside>

    {self._get_scripts_3col()}
    {simulation_scripts}

</body>
</html>'''
        return html

    def _build_cheat_sheet(
        self,
        simulator,
        story: Dict[str, Any],
        demo_data: Dict[str, Any],
        environment_config: Dict[str, Any]
    ) -> str:
        """Build the right-column cheat sheet with simulation buttons and key data."""
        hero_contact = story.get("hero_contact", {})
        hero_account = story.get("hero_account", {})
        hero_case = story.get("hero_case", {})
        
        env = environment_config.get("environment", {})
        org_url = env.get("url", "https://YOUR_ORG.crm.dynamics.com")
        
        # Get simulation scripts for button labels
        email_script = next((s for s in simulator.scripts if s.channel == "email"), None)
        chat_script = next((s for s in simulator.scripts if s.channel == "chat"), None)
        voice_script = next((s for s in simulator.scripts if s.channel == "voice"), None)
        
        email_label = email_script.sender_name if email_script else "Customer"
        chat_label = chat_script.sender_name if chat_script else "Customer"
        voice_label = voice_script.sender_name if voice_script else "Customer"
        
        return f'''
        <!-- SIMULATION TRIGGERS -->
        <div class="cheat-section">
            <h4>🎬 Simulation Triggers</h4>
            <div class="sim-btn-stack">
                <button class="sim-trigger email" onclick="triggerSimulation('email')" title="Send customer email to D365 queue">
                    📧 Send Email<br><small>from {email_label}</small>
                </button>
                <button class="sim-trigger chat" onclick="triggerSimulation('chat')" title="Start portal chat session">
                    💬 Start Chat<br><small>as {chat_label}</small>
                </button>
                <button class="sim-trigger voice" onclick="triggerSimulation('voice')" title="Trigger incoming call">
                    📞 Incoming Call<br><small>from {voice_label}</small>
                </button>
            </div>
            <div class="sim-status" id="simStatus">Ready</div>
        </div>

        <!-- HERO ACCOUNT -->
        <div class="cheat-section">
            <h4>🏢 Hero Account</h4>
            <div class="cheat-item">
                <span class="cheat-label">Account</span>
                <span class="cheat-value">{hero_account.get("name", "N/A")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Tier</span>
                <span class="cheat-value tier-badge">{hero_account.get("tier", "Standard")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Account #</span>
                <span class="cheat-value mono">{hero_account.get("accountNumber", "N/A")}</span>
            </div>
        </div>

        <!-- HERO CONTACT -->
        <div class="cheat-section">
            <h4>👤 Hero Contact</h4>
            <div class="cheat-item">
                <span class="cheat-label">Name</span>
                <span class="cheat-value">{hero_contact.get("firstName", "")} {hero_contact.get("lastName", "")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Title</span>
                <span class="cheat-value">{hero_contact.get("title", "N/A")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Phone</span>
                <span class="cheat-value mono">{hero_contact.get("phone", "N/A")}</span>
            </div>
        </div>

        <!-- HERO CASE -->
        <div class="cheat-section">
            <h4>📋 Hero Case</h4>
            <div class="cheat-item">
                <span class="cheat-label">Title</span>
                <span class="cheat-value small">{hero_case.get("title", "N/A")[:40]}...</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Priority</span>
                <span class="cheat-value">{hero_case.get("priority", "Normal")}</span>
            </div>
        </div>

        <!-- QUICK LINKS -->
        <div class="cheat-section">
            <h4>🔗 Quick Links</h4>
            <a href="{org_url}" target="_blank" class="cheat-link">D365 Workspace →</a>
            <a href="https://outlook.office.com" target="_blank" class="cheat-link">Outlook →</a>
        </div>

        <!-- FLOW CONFIG -->
        <details class="cheat-config">
            <summary>⚙️ Flow URLs</summary>
            <div class="config-body">
                <label>Email:</label>
                <input type="text" id="emailFlowUrl" placeholder="PA HTTP URL">
                <label>Chat:</label>
                <input type="text" id="chatFlowUrl" placeholder="PA HTTP URL">
                <label>Voice:</label>
                <input type="text" id="voiceFlowUrl" placeholder="PA HTTP URL">
                <button onclick="saveFlowConfig()" class="config-save">💾 Save</button>
            </div>
        </details>
'''

    def _build_cheat_sheet_fallback(
        self,
        story: Dict[str, Any],
        demo_data: Dict[str, Any],
        environment_config: Dict[str, Any]
    ) -> str:
        """Build cheat sheet without simulator (fallback)."""
        hero_contact = story.get("hero_contact", {})
        hero_account = story.get("hero_account", {})
        hero_case = story.get("hero_case", {})
        
        env = environment_config.get("environment", {})
        org_url = env.get("url", "https://YOUR_ORG.crm.dynamics.com")
        
        return f'''
        <!-- HERO ACCOUNT -->
        <div class="cheat-section">
            <h4>🏢 Hero Account</h4>
            <div class="cheat-item">
                <span class="cheat-label">Account</span>
                <span class="cheat-value">{hero_account.get("name", "N/A")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Tier</span>
                <span class="cheat-value tier-badge">{hero_account.get("tier", "Standard")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Account #</span>
                <span class="cheat-value mono">{hero_account.get("accountNumber", "N/A")}</span>
            </div>
        </div>

        <!-- HERO CONTACT -->
        <div class="cheat-section">
            <h4>👤 Hero Contact</h4>
            <div class="cheat-item">
                <span class="cheat-label">Name</span>
                <span class="cheat-value">{hero_contact.get("firstName", "")} {hero_contact.get("lastName", "")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Title</span>
                <span class="cheat-value">{hero_contact.get("title", "N/A")}</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Phone</span>
                <span class="cheat-value mono">{hero_contact.get("phone", "N/A")}</span>
            </div>
        </div>

        <!-- HERO CASE -->
        <div class="cheat-section">
            <h4>📋 Hero Case</h4>
            <div class="cheat-item">
                <span class="cheat-label">Title</span>
                <span class="cheat-value small">{hero_case.get("title", "N/A")[:40]}...</span>
            </div>
            <div class="cheat-item">
                <span class="cheat-label">Priority</span>
                <span class="cheat-value">{hero_case.get("priority", "Normal")}</span>
            </div>
        </div>

        <!-- QUICK LINKS -->
        <div class="cheat-section">
            <h4>🔗 Quick Links</h4>
            <a href="{org_url}" target="_blank" class="cheat-link">D365 Workspace →</a>
            <a href="https://outlook.office.com" target="_blank" class="cheat-link">Outlook →</a>
        </div>
'''

    def _get_styles_3col(self, brand_colors: Dict[str, str]) -> str:
        """Get CSS styles for 3-column layout."""
        return '''
    <style>
        :root {
            --ms-blue: #0078D4;
            --ms-blue-dark: #005A9E;
            --ms-blue-light: #DEECF9;
            --accent-warm: #D83B01;
            --accent-green: #107C10;
            --accent-purple: #5C2D91;
            --accent-teal: #008575;
            --accent-red: #A4262C;
            --bg: #FAFAFA;
            --card-bg: #FFFFFF;
            --text: #323130;
            --text-light: #605E5C;
            --border: #EDEBE9;
            --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            --radius: 12px;
            --nav-width: 280px;
            --cheat-width: 300px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
        
        /* 3-COLUMN LAYOUT */
        body.three-column {
            display: grid;
            grid-template-columns: var(--nav-width) 1fr var(--cheat-width);
            min-height: 100vh;
        }
        body.three-column.nav-collapsed {
            grid-template-columns: 0 1fr var(--cheat-width);
        }
        body.three-column.cheat-collapsed {
            grid-template-columns: var(--nav-width) 1fr 0;
        }
        body.three-column.nav-collapsed.cheat-collapsed {
            grid-template-columns: 0 1fr 0;
        }
        
        /* LEFT NAV - Column 1 */
        .side-nav {
            grid-column: 1;
            position: sticky;
            top: 0;
            height: 100vh;
            background: white;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: width 0.3s, margin 0.3s;
        }
        
        /* CENTER MAIN CONTENT - Column 2 */
        .main-content {
            grid-column: 2;
            min-height: 100vh;
            overflow-y: auto;
            width: 100%;
            max-width: 100%;
        }
        
        /* RIGHT CHEAT SHEET - Column 3 */
        .cheat-sheet {
            grid-column: 3;
            position: sticky;
            top: 0;
            height: 100vh;
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: width 0.3s, margin 0.3s;
        }
        
        body.nav-collapsed .side-nav {
            width: 0;
            margin-left: calc(-1 * var(--nav-width));
        }
        .side-nav-header {
            padding: 16px;
            background: linear-gradient(135deg, var(--ms-blue), var(--ms-blue-dark));
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .side-nav-pin {
            background: none;
            border: 1px solid rgba(255,255,255,0.5);
            color: white;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 0.65rem;
            cursor: pointer;
            text-transform: uppercase;
        }
        .side-nav-body {
            flex: 1;
            overflow-y: auto;
            padding: 8px 0;
        }
        .side-nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            font-size: 0.8rem;
            color: var(--text);
            cursor: pointer;
            border-left: 3px solid transparent;
        }
        .side-nav-item:hover { background: #F3F2F1; }
        .side-nav-item.active { background: var(--ms-blue-light); border-left-color: var(--ms-blue); font-weight: 600; }
        .side-nav-num {
            width: 24px; height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.65rem;
            color: white;
        }
        
        /* CHEAT SHEET COLLAPSE STATE */
        body.cheat-collapsed .cheat-sheet {
            width: 0;
            margin-right: calc(-1 * var(--cheat-width));
        }
        .cheat-sheet-header {
            padding: 14px 16px;
            background: rgba(255,255,255,0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
        }
        .cheat-sheet-toggle {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 1rem;
        }
        .cheat-sheet-body {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }
        .cheat-section {
            margin-bottom: 20px;
        }
        .cheat-section h4 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: rgba(255,255,255,0.6);
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .cheat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            font-size: 0.82rem;
        }
        .cheat-label {
            color: rgba(255,255,255,0.6);
        }
        .cheat-value {
            font-weight: 500;
            text-align: right;
        }
        .cheat-value.mono {
            font-family: 'Consolas', monospace;
            font-size: 0.78rem;
        }
        .cheat-value.small {
            font-size: 0.75rem;
        }
        .cheat-value.tier-badge {
            background: var(--accent-red);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.7rem;
        }
        .cheat-link {
            display: block;
            color: var(--ms-blue-light);
            text-decoration: none;
            padding: 6px 0;
            font-size: 0.82rem;
        }
        .cheat-link:hover {
            text-decoration: underline;
        }
        
        /* SIMULATION BUTTONS */
        .sim-btn-stack {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .sim-trigger {
            padding: 12px 14px;
            border: none;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            text-align: left;
            transition: transform 0.15s, box-shadow 0.15s;
        }
        .sim-trigger:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .sim-trigger:active {
            transform: translateY(0);
        }
        .sim-trigger:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .sim-trigger small {
            display: block;
            font-size: 0.7rem;
            font-weight: 400;
            opacity: 0.8;
            margin-top: 2px;
        }
        .sim-trigger.email {
            background: linear-gradient(135deg, #0078D4 0%, #005A9E 100%);
            color: white;
        }
        .sim-trigger.chat {
            background: linear-gradient(135deg, #107C10 0%, #0B5C0B 100%);
            color: white;
        }
        .sim-trigger.voice {
            background: linear-gradient(135deg, #D83B01 0%, #A52A00 100%);
            color: white;
        }
        .sim-status {
            margin-top: 10px;
            padding: 8px 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
            font-size: 0.78rem;
            color: #4CAF50;
        }
        .sim-status.error { color: #f44336; }
        .sim-status.pending { color: #FFC107; }
        
        /* CONFIG PANEL */
        .cheat-config {
            margin-top: 16px;
            font-size: 0.78rem;
        }
        .cheat-config summary {
            cursor: pointer;
            color: rgba(255,255,255,0.6);
            padding: 6px 0;
        }
        .cheat-config .config-body {
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
            margin-top: 6px;
        }
        .cheat-config label {
            display: block;
            color: rgba(255,255,255,0.5);
            font-size: 0.7rem;
            margin-bottom: 2px;
        }
        .cheat-config input {
            width: 100%;
            padding: 6px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 4px;
            background: rgba(255,255,255,0.08);
            color: white;
            font-size: 0.75rem;
            margin-bottom: 8px;
        }
        .cheat-config .config-save {
            width: 100%;
            padding: 6px;
            background: var(--ms-blue);
            border: none;
            border-radius: 4px;
            color: white;
            cursor: pointer;
            font-size: 0.75rem;
        }
        
        /* HERO & CONTAINER */
        .hero {
            background: linear-gradient(135deg, ''' + brand_colors["primary"] + ''' 0%, ''' + brand_colors["accent"] + ''' 100%);
            color: white;
            padding: 28px 32px 24px;
            text-align: center;
        }
        .hero h1 { font-size: 1.6rem; font-weight: 600; margin-bottom: 4px; }
        .hero .subtitle { font-size: 0.95rem; opacity: 0.92; margin-bottom: 10px; }
        .hero .meta { display: flex; justify-content: center; gap: 20px; font-size: 0.8rem; opacity: 0.88; flex-wrap: wrap; }
        .hero-badge { display: inline-block; background: rgba(255,255,255,0.22); border: 1px solid rgba(255,255,255,0.45); border-radius: 20px; padding: 3px 14px; font-size: 0.68rem; font-weight: 700; margin-top: 10px; text-transform: uppercase; }
        .container { max-width: 900px; margin: 0 auto; padding: 0 24px; }
        .section-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--ms-blue); margin-top: 32px; margin-bottom: 10px; }
        
        /* FLOATING RESTORE BUTTONS */
        .nav-restore {
            position: fixed;
            top: 12px;
            left: 12px;
            z-index: 1001;
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 8px;
            background: var(--ms-blue);
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
            display: none;
        }
        body.nav-collapsed .nav-restore { display: flex; align-items: center; justify-content: center; }
        
        .cheat-restore {
            position: fixed;
            top: 12px;
            right: 12px;
            z-index: 1001;
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
            display: none;
        }
        body.cheat-collapsed .cheat-restore { display: flex; align-items: center; justify-content: center; }
        
        /* NAV TOGGLE (mobile only) */
        .nav-toggle {
            position: fixed;
            top: 12px;
            left: 12px;
            z-index: 1001;
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 6px;
            background: var(--ms-blue);
            color: white;
            font-size: 1.1rem;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            display: none;
        }
        
        /* PREFLIGHT */
        .preflight { background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F2 100%); border-left: 4px solid var(--accent-green); border-radius: 0 var(--radius) var(--radius) 0; padding: 20px 24px; margin: 20px 0; }
        .preflight h3 { font-size: 0.95rem; font-weight: 700; color: var(--accent-green); margin-bottom: 10px; }
        .preflight ul { font-size: 0.84rem; color: #2E5A30; line-height: 1.9; padding-left: 18px; }
        .preflight code { background: rgba(0,0,0,0.08); padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 0.78rem; }
        
        /* EXEC SECTIONS */
        .exec-section { background: var(--card-bg); border-radius: var(--radius); box-shadow: var(--shadow); margin: 16px 0; border-left: 5px solid var(--ms-blue); overflow: hidden; }
        .exec-header { display: flex; align-items: center; gap: 14px; padding: 18px 20px; cursor: pointer; }
        .exec-header:hover { background: rgba(0,120,212,0.03); }
        .exec-number { width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; color: white; flex-shrink: 0; }
        .exec-header-text { flex: 1; }
        .exec-header-text h3 { font-size: 1.05rem; font-weight: 600; margin-bottom: 2px; }
        .exec-header-text .exec-purpose { font-size: 0.8rem; color: var(--text-light); font-style: italic; }
        .exec-time { font-size: 0.72rem; font-weight: 600; color: var(--text-light); background: var(--bg); padding: 3px 10px; border-radius: 20px; }
        .exec-expand { font-size: 1.1rem; color: var(--text-light); transition: transform 0.3s; }
        .exec-section.open .exec-expand { transform: rotate(180deg); }
        .exec-body { max-height: 0; overflow: hidden; transition: max-height 0.5s ease; }
        .exec-section.open .exec-body { max-height: 50000px; }
        .exec-content { padding: 0 20px 24px 72px; }
        
        /* STEP BLOCKS */
        .step-block { margin: 14px 0; padding: 14px 18px; background: #F8F9FA; border-radius: 8px; border-left: 3px solid var(--ms-blue); }
        .step-block.voice-step { border-left-color: var(--accent-red); background: #FFF5F5; }
        .step-block.chat-step { border-left-color: var(--accent-teal); background: #F0FAF9; }
        .step-block.copilot-step { border-left-color: var(--accent-purple); background: #F8F5FD; }
        .step-label { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; }
        .step-label.prep { background: var(--accent-green); }
        .step-label.click { background: var(--ms-blue); }
        .step-label.say { background: var(--accent-warm); }
        .step-label.show { background: var(--accent-teal); }
        .step-label.tip { background: #FFB900; color: #5D4510; }
        .step-label.copilot { background: var(--accent-purple); }
        .step-label.trigger { background: #5C2D91; }
        .step-text { font-size: 0.86rem; line-height: 1.55; }
        .step-text .click-path { font-family: 'Consolas', monospace; background: rgba(0,120,212,0.1); color: var(--ms-blue-dark); padding: 2px 6px; border-radius: 4px; font-size: 0.78rem; }
        
        /* INLINE TRIGGER BUTTON */
        .inline-trigger {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            margin: 8px 0;
            transition: transform 0.15s;
        }
        .inline-trigger:hover { transform: scale(1.02); }
        .inline-trigger.email { background: var(--ms-blue); color: white; }
        .inline-trigger.chat { background: var(--accent-teal); color: white; }
        .inline-trigger.voice { background: var(--accent-red); color: white; }
        
        /* TALK TRACK */
        .talk-track { background: white; border: 1px solid #E0E0E0; border-radius: 8px; padding: 14px 18px; margin: 8px 0; font-style: italic; font-size: 0.84rem; line-height: 1.6; color: #444; position: relative; }
        .talk-track::before { content: '"'; font-size: 2.5rem; color: var(--accent-warm); position: absolute; top: -6px; left: 8px; opacity: 0.5; }
        .talk-track p { padding-left: 20px; }
        
        /* CALLOUTS */
        .callout { border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-size: 0.82rem; }
        .callout.warning { background: #FFF4CE; border-left: 3px solid #FFB900; color: #5D4510; }
        .callout.success { background: #E8F5E9; border-left: 3px solid var(--accent-green); color: #2E5A30; }
        .callout.info { background: var(--ms-blue-light); border-left: 3px solid var(--ms-blue); color: #003A6E; }
        .callout.roi { background: linear-gradient(135deg, #E8F5E9 0%, #F1F8E9 100%); border-left: 4px solid #2E7D32; color: #1B5E20; }
        
        /* VOICE/CHAT LINES */
        .voice-line { background: #FFF5F5; border: 1px solid #E8D0D0; border-radius: 8px; padding: 12px 18px 12px 34px; margin: 8px 0; font-style: italic; font-size: 0.84rem; color: #8B3A3A; position: relative; }
        .voice-line::before { content: '📞'; position: absolute; top: 12px; left: 10px; }
        .voice-line .voice-label { display: block; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: var(--accent-red); font-style: normal; margin-bottom: 3px; }
        .chat-line { background: #F0FAF9; border: 1px solid #C8E6E3; border-radius: 8px; padding: 12px 18px 12px 34px; margin: 8px 0; font-style: italic; font-size: 0.84rem; color: #2D6A65; position: relative; }
        .chat-line::before { content: '💬'; position: absolute; top: 12px; left: 10px; }
        .chat-line .chat-label { display: block; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: var(--accent-teal); font-style: normal; margin-bottom: 3px; }
        
        /* STORY BLOCK */
        .story-block { background: linear-gradient(135deg, #F3F0FF 0%, #FFF8F0 100%); border-left: 4px solid var(--accent-purple); border-radius: 0 var(--radius) var(--radius) 0; padding: 20px 24px; margin: 20px 0; }
        .story-block h3 { font-size: 0.95rem; font-weight: 700; color: var(--accent-purple); margin-bottom: 10px; }
        .story-block dl { margin: 10px 0; }
        .story-block dt { font-weight: 600; margin-top: 5px; font-size: 0.84rem; }
        .story-block dd { font-size: 0.8rem; color: var(--text-light); margin-left: 18px; }
        .story-block ol { margin: 10px 0 10px 18px; font-size: 0.82rem; }
        .story-block .story-note { font-style: italic; font-size: 0.8rem; color: var(--accent-purple); margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(92,45,145,0.15); }
        
        /* DEMO GOLD */
        .demo-gold { background: linear-gradient(135deg, #FFF8E1 0%, #FFFDF5 100%); border-left: 4px solid #FFB900; border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 10px 0; font-size: 0.82rem; }
        .demo-gold strong { color: #856404; }
        
        /* TIMING BAR */
        .timing-bar { display: flex; gap: 0; margin: 24px 0 10px; border-radius: 6px; overflow: hidden; height: 7px; }
        .timing-bar .t-seg { height: 100%; }
        
        /* FOOTER */
        footer { text-align: center; padding: 28px; color: var(--text-light); font-size: 0.76rem; border-top: 1px solid var(--border); margin-top: 40px; }
        
        /* RESPONSIVE */
        @media (max-width: 1200px) {
            body.three-column {
                grid-template-columns: 0 1fr var(--cheat-width);
            }
            .side-nav { position: fixed; left: 0; z-index: 1000; transform: translateX(-100%); }
            .side-nav.open { transform: translateX(0); }
            .nav-toggle { display: block; }
        }
        @media (max-width: 900px) {
            body.three-column {
                grid-template-columns: 1fr;
            }
            .cheat-sheet {
                position: fixed;
                right: 0;
                top: 0;
                z-index: 1000;
                transform: translateX(100%);
            }
            .cheat-sheet.open { transform: translateX(0); }
        }
        @media print {
            body.three-column { display: block; }
            .side-nav, .cheat-sheet, .nav-toggle { display: none !important; }
            .exec-body { max-height: none !important; }
        }
    </style>'''

    def _get_scripts_3col(self) -> str:
        """Get JavaScript for 3-column layout interactivity."""
        return '''
    <script>
        function toggleSection(header) {
            const section = header.parentElement;
            section.classList.toggle('open');
        }

        // Side navigation
        const sideNav = document.getElementById('sideNav');
        const navPin = document.getElementById('navPin');
        const navBody = document.getElementById('navBody');
        const navRestore = document.getElementById('navRestore');
        
        // Cheat sheet
        const cheatSheet = document.getElementById('cheatSheet');
        const cheatToggle = document.getElementById('cheatToggle');
        const cheatRestore = document.getElementById('cheatRestore');

        // Build nav items from sections
        document.querySelectorAll('.exec-section').forEach((section, idx) => {
            const header = section.querySelector('.exec-header-text h3');
            const number = section.querySelector('.exec-number');
            if (header) {
                const item = document.createElement('div');
                item.className = 'side-nav-item';
                item.innerHTML = `<div class="side-nav-num" style="background:${number ? getComputedStyle(number).background : '#0078D4'}">${idx + 1}</div><span>${header.textContent}</span>`;
                item.onclick = () => {
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    section.classList.add('open');
                };
                navBody.appendChild(item);
            }
        });

        // Nav pin/hide
        if (navPin) {
            navPin.onclick = () => {
                document.body.classList.add('nav-collapsed');
            };
        }
        
        // Nav restore (floating button)
        if (navRestore) {
            navRestore.onclick = () => {
                document.body.classList.remove('nav-collapsed');
            };
        }
        
        // Cheat sheet hide
        if (cheatToggle) {
            cheatToggle.onclick = () => {
                document.body.classList.add('cheat-collapsed');
            };
        }
        
        // Cheat sheet restore (floating button)
        if (cheatRestore) {
            cheatRestore.onclick = () => {
                document.body.classList.remove('cheat-collapsed');
            };
        }

        // Open first section by default
        document.querySelector('.exec-section')?.classList.add('open');
        
        // Flow config persistence
        function loadFlowConfig() {
            const saved = localStorage.getItem('demoSimFlowConfig');
            if (saved) {
                try {
                    const config = JSON.parse(saved);
                    if (document.getElementById('emailFlowUrl')) document.getElementById('emailFlowUrl').value = config.email || '';
                    if (document.getElementById('chatFlowUrl')) document.getElementById('chatFlowUrl').value = config.chat || '';
                    if (document.getElementById('voiceFlowUrl')) document.getElementById('voiceFlowUrl').value = config.voice || '';
                } catch (e) {}
            }
        }
        
        function saveFlowConfig() {
            const config = {
                email: document.getElementById('emailFlowUrl')?.value || '',
                chat: document.getElementById('chatFlowUrl')?.value || '',
                voice: document.getElementById('voiceFlowUrl')?.value || ''
            };
            localStorage.setItem('demoSimFlowConfig', JSON.stringify(config));
            updateStatus('Config saved!', 'success');
        }
        
        function updateStatus(message, type = 'success') {
            const status = document.getElementById('simStatus');
            if (status) {
                status.textContent = message;
                status.className = 'sim-status ' + type;
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', loadFlowConfig);
    </script>'''

    def _build_demo_story(
        self,
        customer_name: str,
        inputs: Dict[str, Any],
        demo_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the connected demo story from data, merging customer-provided story elements."""
        customer_info = inputs.get("customer", {})
        demo_reqs = inputs.get("demo_requirements", {})
        hero_scenario = demo_reqs.get("hero_scenario", {})
        demo_story_input = inputs.get("demo_story", {})

        accounts = demo_data.get("serviceAccounts", {}).get("accounts", [])
        contacts = demo_data.get("contacts", {}).get("contacts", [])
        cases = demo_data.get("demoCases", {}).get("cases", [])

        # Use customer-provided agent persona or default
        agent_persona = demo_story_input.get("agent_persona", {"name": "Agent", "role": "CSR"})

        # Find hero account (highest tier or first)
        hero_account = None
        for acc in accounts:
            if acc.get("tier") in ["Platinum", "Premium", "Tier 1", "Strategic"]:
                hero_account = acc
                break
        if not hero_account and accounts:
            hero_account = accounts[0]

        # Find hero contact
        hero_contact = None
        if hero_scenario.get("customer_name"):
            for contact in contacts:
                full_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}"
                if hero_scenario["customer_name"] in full_name:
                    hero_contact = contact
                    break
        if not hero_contact:
            # Find contact linked to hero account
            for contact in contacts:
                if contact.get("account") == hero_account.get("name"):
                    hero_contact = contact
                    break
        if not hero_contact and contacts:
            hero_contact = contacts[0]

        # Find hero case
        hero_case = None
        for case in cases:
            if case.get("isHeroCase"):
                hero_case = case
                break
        if not hero_case and cases:
            hero_case = cases[0]

        # Find secondary contacts for multi-channel story
        secondary_contacts = []
        for contact in contacts:
            if contact != hero_contact and len(secondary_contacts) < 2:
                secondary_contacts.append(contact)

        # Build story characters - use customer-provided characters or auto-generate
        if demo_story_input.get("characters"):
            characters = []
            for char in demo_story_input["characters"]:
                icon = {"phone": "📞", "chat": "💬", "email": "📧", "portal": "🌐"}.get(char.get("channel", "phone"), "👤")
                characters.append({
                    "name": char.get("name", "Customer"),
                    "role": char.get("role", "Contact"),
                    "account": char.get("account", ""),
                    "channel": char.get("channel", "phone"),
                    "icon": icon,
                    "description": char.get("scenario", f"{char.get('channel', 'phone').title()} scenario")
                })
        else:
            characters = []
            if hero_contact:
                characters.append({
                    "name": f"{hero_contact.get('firstName', '')} {hero_contact.get('lastName', '')}",
                    "role": hero_contact.get("title", "Contact"),
                    "account": hero_contact.get("account", ""),
                    "channel": "phone",
                    "icon": "📞",
                    "description": f"Primary caller. {hero_contact.get('title', '')} at {hero_contact.get('account', '')}."
                })

            for i, contact in enumerate(secondary_contacts):
                channel = "chat" if i == 0 else "email"
                icon = "💬" if i == 0 else "📧"
                characters.append({
                    "name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}",
                    "role": contact.get("title", "Contact"),
                    "account": contact.get("account", ""),
                    "channel": channel,
                    "icon": icon,
                    "description": f"{channel.title()} scenario. {contact.get('title', '')}."
                })

        # Story flow
        story_flow = []
        # Use customer-provided story flow if available
        if demo_story_input.get("story_flow"):
            story_flow = demo_story_input["story_flow"]
        else:
            story_flow.append({
                "step": 1,
                "event": f"{hero_contact.get('firstName', 'Customer')} calls",
                "description": f"Incoming call triggers screen pop with full {hero_account.get('name', 'customer')} context"
            })
            if secondary_contacts:
                story_flow.append({
                    "step": 2,
                    "event": f"{secondary_contacts[0].get('firstName', 'Customer')} chats",
                    "description": "Chat bot triages, escalates to agent with context preserved"
                })
            story_flow.append({
                "step": 3,
                "event": "Supervisor reviews",
                "description": "Dashboards show agent performance across all channels"
            })

        # Build key messages (from input or default)
        key_messages = demo_story_input.get("key_messages", [
            "Instant customer context without asking for account numbers",
            "Complete history visible before saying hello",
            "All channels unified in one timeline"
        ])

        return {
            "agent_persona": agent_persona,
            "hero_account": hero_account,
            "hero_contact": hero_contact,
            "hero_case": hero_case,
            "characters": characters,
            "story_flow": story_flow,
            "secondary_contacts": secondary_contacts,
            "key_messages": key_messages,
            "summary": f"This demo tells one connected story centered on {hero_account.get('name', 'the customer')}. "
                       f"All interactions appear in the unified timeline, showing how D365 provides complete context across channels."
        }

    def _build_hero_records(self, demo_data: Dict[str, Any]) -> str:
        """Build the hero records reference section."""
        accounts = demo_data.get("serviceAccounts", {}).get("accounts", [])
        contacts = demo_data.get("contacts", {}).get("contacts", [])
        cases = demo_data.get("demoCases", {}).get("cases", [])

        # Find hero records
        hero_account = accounts[0] if accounts else {}
        hero_contacts = [c for c in contacts if c.get("account") == hero_account.get("name")][:3]
        hero_case = next((c for c in cases if c.get("isHeroCase")), cases[0] if cases else {})

        contacts_rows = ""
        for contact in hero_contacts:
            contacts_rows += f'''
                <tr>
                    <td><strong>{contact.get("firstName", "")} {contact.get("lastName", "")}</strong></td>
                    <td>{contact.get("title", "")}</td>
                    <td>{contact.get("phone", "")}</td>
                    <td>{contact.get("email", "")}</td>
                </tr>'''

        return f'''
        <div class="exec-section" style="border-left-color: #FFB900;">
            <div class="exec-header" onclick="toggleSection(this)">
                <div class="exec-number" style="background: #FFB900; color: #5D4510;">★</div>
                <div class="exec-header-text">
                    <h3>Hero Records — {hero_account.get("name", "Primary Account")}</h3>
                    <div class="exec-purpose">Account, contacts, hero case details</div>
                </div>
                <div class="exec-time">Reference</div>
                <div class="exec-expand">▼</div>
            </div>
            <div class="exec-body">
                <div class="exec-content">

                    <p class="ref-section-title">🏢 Hero Account — {hero_account.get("name", "")}</p>
                    <table class="ref-table">
                        <thead>
                            <tr><th>Field</th><th>Value</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Account Name</td><td><strong>{hero_account.get("name", "")}</strong></td></tr>
                            <tr><td>Account Number</td><td><code>{hero_account.get("accountNumber", "")}</code></td></tr>
                            <tr><td>Customer Tier</td><td><span class="tier-pill t1">{hero_account.get("tier", "Standard")}</span></td></tr>
                            <tr><td>Type</td><td>{hero_account.get("type", "")}</td></tr>
                            <tr><td>Address</td><td>{hero_account.get("address", {}).get("line1", "")}, {hero_account.get("address", {}).get("city", "")}</td></tr>
                            <tr><td>Phone</td><td>{hero_account.get("phone", "")}</td></tr>
                        </tbody>
                    </table>

                    <p class="ref-section-title">👤 Hero Contacts</p>
                    <table class="ref-table">
                        <thead>
                            <tr><th>Name</th><th>Role</th><th>Phone</th><th>Email</th></tr>
                        </thead>
                        <tbody>
                            {contacts_rows}
                        </tbody>
                    </table>

                    <p class="ref-section-title">📋 Hero Case</p>
                    <table class="ref-table">
                        <thead>
                            <tr><th>Field</th><th>Value</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Case Title</td><td><strong>{hero_case.get("title", "")}</strong></td></tr>
                            <tr><td>Priority</td><td>{hero_case.get("priority", "Normal")}</td></tr>
                            <tr><td>Status</td><td>{hero_case.get("status", "Active")}</td></tr>
                            <tr><td>Channel</td><td>{hero_case.get("channel", "Phone")}</td></tr>
                            <tr><td>Demo Use</td><td><em>{hero_case.get("demoUse", "")}</em></td></tr>
                        </tbody>
                    </table>

                </div>
            </div>
        </div>'''

    def _build_preflight_checklist(
        self,
        environment_config: Dict[str, Any],
        demo_data: Dict[str, Any]
    ) -> str:
        """Build the pre-flight checklist section."""
        env = environment_config.get("environment", {})
        org_url = env.get("url", "https://YOUR_ORG.crm.dynamics.com")

        accounts = demo_data.get("serviceAccounts", {}).get("accounts", [])
        hero_account = accounts[0].get("name", "Hero Account") if accounts else "Hero Account"

        return f'''
        <div class="preflight">
            <h3>✅ Pre-Flight Checklist (30 min before demo)</h3>
            <ul>
                <li><strong>Browser tabs open (Edge recommended):</strong></li>
                <li>&emsp;Tab 1: D365 CS Workspace — <code>{org_url}</code></li>
                <li>&emsp;Tab 2: D365 Admin / Omnichannel Real-Time Analytics</li>
                <li>&emsp;Tab 3: Outlook Web — <code>https://outlook.office.com</code></li>
                <li><strong>In D365 Workspace verify:</strong></li>
                <li>&emsp;"My Active Cases" view with tier-level indicators</li>
                <li>&emsp;SLA timers visible on at least 2 cases</li>
                <li>&emsp;Copilot panel accessible (click Copilot icon)</li>
                <li>&emsp;Presence status "Available" (green circle)</li>
                <li><strong>Voice Channel ready:</strong> Status "Available" in Omnichannel panel</li>
                <li><strong>Screen sharing:</strong> Share browser window (not full desktop)</li>
                <li><strong>Notifications silenced:</strong> Focus Assist ON, Teams DND</li>
                <li><strong>Secondary phone ready</strong> for incoming call scenario</li>
                <li><strong>This guide open</strong> on second monitor</li>
                <li><strong>Quick test:</strong> Open {hero_account} account → confirm data visible</li>
            </ul>
        </div>'''

    def _build_quick_urls(self, environment_config: Dict[str, Any]) -> str:
        """Build quick reference URLs section."""
        env = environment_config.get("environment", {})
        org_url = env.get("url", "https://YOUR_ORG.crm.dynamics.com")

        return f'''
        <div class="callout info">
            <strong>Quick Reference URLs</strong><br>
            D365 Org: <span class="url-ref">{org_url}</span><br>
            Outlook: <span class="url-ref">https://outlook.office.com</span>
        </div>'''

    def _build_timing_bar(self, sections: List[Dict]) -> str:
        """Build the visual timing bar."""
        total = sum(s["time"] for s in sections)
        segments = ""
        legend = ""

        for section in sections:
            flex = int((section["time"] / total) * 100)
            segments += f'<div class="t-seg" style="flex:{flex}; background:{section["color"]};" title="{section["title"]} ~{section["time"]} min"></div>'
            legend += f'<span style="color:{section["color"]};">■ {section["title"]} ({section["time"]}m)</span>'

        return f'''
        <div class="timing-bar">
            {segments}
        </div>
        <div style="display:flex; gap:16px; flex-wrap:wrap; font-size:0.72rem; color:var(--text-light); margin-bottom:32px;">
            {legend}
        </div>'''

    def _build_story_block(self, story: Dict[str, Any]) -> str:
        """Build the story overview block."""
        characters_html = ""
        for char in story.get("characters", []):
            characters_html += f'''
                <dt>{char["name"]} {char["icon"]}</dt>
                <dd>{char["description"]}</dd>'''

        flow_html = ""
        for step in story.get("story_flow", []):
            flow_html += f'<li><strong>{step["event"]}</strong> — {step["description"]}</li>'

        return f'''
        <div class="story-block">
            <h3>📖 The Story</h3>
            <p>{story.get("summary", "")}</p>
            <dl>
                {characters_html}
            </dl>
            <ol>
                {flow_html}
            </ol>
            <p class="story-note">Everything connects. All interactions appear in the customer's unified timeline.</p>
        </div>'''

    def _build_sections(
        self,
        sections: List[Dict],
        story: Dict[str, Any],
        demo_data: Dict[str, Any],
        discovery: Dict[str, Any]
    ) -> str:
        """Build the demo flow sections."""
        html = ""
        hero_contact = story.get("hero_contact", {})
        hero_account = story.get("hero_account", {})
        hero_case = story.get("hero_case", {})
        pain_points = discovery.get("pain_points", [])

        for i, section in enumerate(sections):
            is_open = "open" if i == 0 else ""
            section_id = section["id"]

            # Generate section-specific content
            content = self._generate_section_content(
                section_id, hero_contact, hero_account, hero_case, pain_points, story
            )

            html += f'''
        <div class="exec-section {is_open}" style="border-left-color: {section["color"]};">
            <div class="exec-header" onclick="toggleSection(this)">
                <div class="exec-number" style="background: {section["color"]};">{i + 1}</div>
                <div class="exec-header-text">
                    <h3>{section["title"]}</h3>
                    <div class="exec-purpose">{section["purpose"]}</div>
                </div>
                <div class="exec-time">~{section["time"]} min</div>
                <div class="exec-expand">▼</div>
            </div>
            <div class="exec-body">
                <div class="exec-content">
                    {content}
                </div>
            </div>
        </div>'''

        return html

    def _generate_section_content(
        self,
        section_id: str,
        hero_contact: Dict,
        hero_account: Dict,
        hero_case: Dict,
        pain_points: List[str],
        story: Dict
    ) -> str:
        """Generate content for a specific demo section."""
        contact_name = f"{hero_contact.get('firstName', 'Customer')} {hero_contact.get('lastName', '')}"
        account_name = hero_account.get("name", "Customer")
        case_title = hero_case.get("title", "Support Request")

        if section_id == "connect":
            return f'''
                <div class="step-block">
                    <span class="step-label prep">Prep</span>
                    <div class="step-text">
                        Have Tab 1 (D365 Customer Service Workspace) visible. You should be on the
                        <strong>Home</strong> page showing the default dashboard. Copilot panel closed at start.
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        CS Workspace home → point out left nav, session tabs, Copilot panel, multisession concept.
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"Let me show you what a typical day looks like for our customer service team. I handle the {account_name} account — they're one of our most important customers."</p>
                    </div>
                </div>'''

        elif section_id == "challenges":
            pain_html = ""
            for pain in pain_points[:3]:
                pain_html += f"<li>{pain}</li>"

            return f'''
                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"I understand you're currently experiencing some challenges. Let me confirm what I've heard..."</p>
                    </div>
                </div>

                <div class="callout warning">
                    <strong>Key Pain Points to Acknowledge:</strong>
                    <ul style="margin-top:8px;">
                        {pain_html}
                    </ul>
                </div>

                <div class="step-block">
                    <span class="step-label tip">Tip</span>
                    <div class="step-text">
                        Don't dwell on pain — acknowledge and pivot to solution. "Let me show you how D365 addresses this..."
                    </div>
                </div>'''

        elif section_id == "screen_pop":
            return f'''
                <div class="demo-gold">
                    <strong>🌟 HERO MOMENT:</strong> This is the key differentiator. The incoming call immediately shows complete customer context without any searching.
                </div>

                <div class="step-block">
                    <span class="step-label prep">Prep</span>
                    <div class="step-text">
                        Ensure Voice Channel status is "Available". Have your secondary phone ready to call in.
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"Now watch what happens when a call comes in..."</p>
                    </div>
                </div>

                <div class="step-block voice-step">
                    <span class="step-label click">Action</span>
                    <div class="step-text">
                        <strong>Trigger incoming call from secondary phone.</strong><br>
                        Call the Voice Channel number. D365 will show the incoming call notification.
                    </div>
                </div>

                <div class="voice-line">
                    <span class="voice-label">{contact_name} (Caller)</span>
                    "Hi, this is {hero_contact.get('firstName', 'Customer')} from {account_name}. I need help with {case_title}."
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        Point out the <strong>screen pop</strong>:
                        <ul style="margin-top:8px;">
                            <li>Customer name and account automatically identified</li>
                            <li>Tier level: <span class="tier-pill t1">{hero_account.get("tier", "Premium")}</span></li>
                            <li>Open cases visible immediately</li>
                            <li>Recent interaction history</li>
                            <li>Account details and contact information</li>
                        </ul>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"Notice I didn't have to ask who's calling or search for anything. The system recognized {contact_name} instantly and pulled up their complete context. I can see they're a {hero_account.get("tier", "Premium")} customer, their open cases, and recent interactions — all before I even say hello."</p>
                    </div>
                </div>

                <div class="callout roi">
                    <strong>Value Point:</strong> Agents save 30-45 seconds per call by eliminating "Can I have your account number?" Multiply by thousands of calls per day.
                </div>'''

        elif section_id == "case_handling" or section_id == "case_work":
            return f'''
                <div class="step-block">
                    <span class="step-label click">Click</span>
                    <div class="step-text">
                        <span class="click-path">+ New Case</span> or select existing case from timeline
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        <ul>
                            <li>Case form with customer pre-populated</li>
                            <li>SLA timer starting automatically</li>
                            <li>Copilot suggestions appearing</li>
                            <li>Knowledge article recommendations</li>
                        </ul>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"The case is automatically linked to {account_name}, and our SLA timer has started. Notice Copilot is already suggesting relevant knowledge articles and next steps based on the case type."</p>
                    </div>
                </div>'''

        elif section_id == "copilot":
            return f'''
                <div class="step-block copilot-step">
                    <span class="step-label copilot">Copilot</span>
                    <div class="step-text">
                        Click the <strong>Copilot</strong> icon in the command bar to open the Copilot panel.
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        Demonstrate Copilot capabilities:
                        <ul style="margin-top:8px;">
                            <li><strong>Ask a question:</strong> "What is our warranty policy?"</li>
                            <li><strong>Summarize:</strong> "Summarize this case"</li>
                            <li><strong>Draft:</strong> "Draft a response to the customer"</li>
                        </ul>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"Copilot is my AI assistant. I can ask it questions, have it summarize cases, or draft responses. It pulls from our knowledge base and case history to give accurate, contextual answers."</p>
                    </div>
                </div>

                <div class="callout success">
                    <strong>Key Message:</strong> Copilot augments agents — it doesn't replace them. It handles the routine so agents can focus on the relationship.
                </div>'''

        elif section_id == "productivity_toolkit":
            return f'''
                <div class="demo-gold">
                    <strong>🔧 SERVICE TOOLKIT:</strong> The side pane provides guided workflows, macros, and one-click actions that eliminate repetitive tasks and ensure consistency.
                </div>

                <div class="step-block">
                    <span class="step-label click">Click</span>
                    <div class="step-text">
                        Click the <strong>wrench icon (🔧)</strong> in the side pane to open the Service Toolkit.
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        <strong>Service Toolkit Screens:</strong>
                        <ul style="margin-top:8px;">
                            <li><strong>Quick Actions</strong> — One-click macros (Create Work Order, Send ETA Email, etc.)</li>
                            <li><strong>Agent Scripts</strong> — Step-by-step guided workflows</li>
                            <li><strong>Order Management</strong> — View/modify related orders</li>
                            <li><strong>Warranty Lookup</strong> — Serial number verification</li>
                        </ul>
                    </div>
                </div>

                <div class="sub-header" style="margin-top:20px;">📋 AGENT SCRIPT DEMO</div>

                <div class="step-block">
                    <span class="step-label click">Click</span>
                    <div class="step-text">
                        In Service Toolkit, click <span class="click-path">Agent Scripts → Entrapment Response Protocol</span>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        Walk through the script steps:
                        <ol style="margin-top:8px;">
                            <li><strong>Emergency Verification</strong> — Confirm location and status</li>
                            <li><strong>Occupant Status Check</strong> — Medical concerns?</li>
                            <li><strong>Location Confirmation</strong> — Building, elevator #, floor</li>
                            <li><strong>Dispatch Technician</strong> — One-click work order creation</li>
                            <li><strong>Customer Communication</strong> — ETA and follow-up</li>
                        </ol>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"This script guides me through every step of an entrapment call. Notice it even has the exact phrases to say. When I click 'Create Emergency Work Order,' it automatically fills in all the case details — I don't have to re-type anything."</p>
                    </div>
                </div>

                <div class="sub-header" style="margin-top:20px;">⚡ MACRO DEMO</div>

                <div class="step-block">
                    <span class="step-label click">Click</span>
                    <div class="step-text">
                        Click the <span class="click-path">Create Emergency Work Order</span> macro button.
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        The macro:
                        <ul style="margin-top:8px;">
                            <li>Creates a work order with case details pre-filled</li>
                            <li>Sets priority to Emergency</li>
                            <li>Triggers dispatch notification</li>
                            <li>Updates case status automatically</li>
                        </ul>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"What used to take 3-4 minutes of data entry is now a single click. The work order is created, dispatch is notified, and the case is updated — all at once. This is how we reduce average handle time while improving accuracy."</p>
                    </div>
                </div>

                <div class="callout roi">
                    <strong>Value Point:</strong> Macros save 2-4 minutes per case on routine tasks. For a team of 50 agents handling 100 cases/day, that's 160+ hours saved per week.
                </div>'''

        elif section_id == "chat":
            secondary = story.get("secondary_contacts", [{}])[0] if story.get("secondary_contacts") else {}
            chat_name = f"{secondary.get('firstName', 'Customer')} {secondary.get('lastName', '')}"
            chat_account = secondary.get("account", "Customer")

            return f'''
                <div class="step-block chat-step">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        Open the Portal in Tab 3. Log in as a customer persona. Start a chat conversation.
                    </div>
                </div>

                <div class="chat-line">
                    <span class="chat-label">{chat_name} (Customer Chat)</span>
                    "Hi, I need help with a product issue."
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        <ul>
                            <li>Chat bot initial triage</li>
                            <li>Escalation to live agent</li>
                            <li>Context transfer (no repeat information)</li>
                            <li>Customer identified from portal login</li>
                        </ul>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"Notice how the chat transferred to me with full context. The customer didn't have to repeat anything. I can see they're from {chat_account} and what they've already discussed with the bot."</p>
                    </div>
                </div>'''

        elif section_id == "supervisor" or section_id == "supervisor":
            return f'''
                <div class="sub-header leader">👤 Care Leader Perspective</div>

                <div class="step-block">
                    <span class="step-label click">Click</span>
                    <div class="step-text">
                        Navigate to <span class="click-path">Omnichannel Real-Time Analytics</span> (Tab 2)
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label show">Show</span>
                    <div class="step-text">
                        <ul>
                            <li>Real-time dashboard with agent status</li>
                            <li>Queue depth and wait times</li>
                            <li>SLA compliance metrics</li>
                            <li>Agent performance scores</li>
                        </ul>
                    </div>
                </div>

                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"As a supervisor, I have complete visibility into my team's performance. I can see who's available, queue depths, SLA compliance, and individual agent metrics — all in real-time."</p>
                    </div>
                </div>

                <div class="callout info">
                    <strong>Key Dashboards to Show:</strong> Agent status grid, Queue metrics, SLA gauges, Historical trends
                </div>'''

        elif section_id == "close":
            return f'''
                <div class="step-block">
                    <span class="step-label say">Say</span>
                    <div class="talk-track">
                        <p>"Let me summarize what we've seen today:
                        <ul style="margin-top:8px;">
                            <li>Instant customer recognition with screen pop</li>
                            <li>Unified view across all channels</li>
                            <li>AI-powered assistance with Copilot</li>
                            <li>Complete supervisor visibility</li>
                        </ul>
                        What questions do you have? What would you like to explore further?"</p>
                    </div>
                </div>

                <div class="callout success">
                    <strong>Next Steps:</strong>
                    <ul style="margin-top:8px;">
                        <li>Schedule deep-dive on specific capabilities</li>
                        <li>Discuss implementation timeline</li>
                        <li>Identify pilot group</li>
                    </ul>
                </div>'''

        else:
            return f'''
                <div class="step-block">
                    <span class="step-label tip">Tip</span>
                    <div class="step-text">
                        Section content for "{section_id}" - customize based on customer needs.
                    </div>
                </div>'''

    def _get_use_case_tagline(self, use_case: str) -> str:
        """Get a tagline for the use case."""
        taglines = {
            "telephony_screen_pop": "Instant Context, Effortless Service",
            "omnichannel_routing": "Every Channel, One Experience",
            "case_management": "Streamlined Resolution, Happy Customers",
            "full_ccaas": "Complete Contact Center Transformation"
        }
        return taglines.get(use_case, "Customer Service Excellence")

    def _get_brand_colors(self, industry: str) -> Dict[str, str]:
        """Get brand colors based on industry."""
        colors = {
            "elevator_service": {"primary": "#003366", "accent": "#C4A000"},
            "plumbing_manufacturing": {"primary": "#A4262C", "accent": "#0078D4"},
            "hvac": {"primary": "#003B70", "accent": "#FF6B35"},
            "medical_devices": {"primary": "#0078D4", "accent": "#107C10"},
            "telecommunications": {"primary": "#5C2D91", "accent": "#0078D4"},
            "other": {"primary": "#0078D4", "accent": "#107C10"}
        }
        return colors.get(industry, colors["other"])

    def _get_styles(self, brand_colors: Dict[str, str]) -> str:
        """Get the CSS styles for the HTML document."""
        return '''
    <style>
        :root {
            --ms-blue: #0078D4;
            --ms-blue-dark: #005A9E;
            --ms-blue-light: #DEECF9;
            --accent-warm: #D83B01;
            --accent-green: #107C10;
            --accent-purple: #5C2D91;
            --accent-teal: #008575;
            --accent-red: #A4262C;
            --bg: #FAFAFA;
            --card-bg: #FFFFFF;
            --text: #323130;
            --text-light: #605E5C;
            --border: #EDEBE9;
            --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            --radius: 12px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
        .hero { background: linear-gradient(135deg, ''' + brand_colors["primary"] + ''' 0%, ''' + brand_colors["accent"] + ''' 100%); color: white; padding: 50px 40px 40px; text-align: center; }
        .hero h1 { font-size: 2.2rem; font-weight: 600; margin-bottom: 6px; }
        .hero .subtitle { font-size: 1.1rem; opacity: 0.92; margin-bottom: 16px; }
        .hero .meta { display: flex; justify-content: center; gap: 28px; font-size: 0.88rem; opacity: 0.88; flex-wrap: wrap; }
        .hero-badge { display: inline-block; background: rgba(255,255,255,0.22); border: 1px solid rgba(255,255,255,0.45); border-radius: 20px; padding: 4px 18px; font-size: 0.76rem; font-weight: 700; margin-top: 14px; text-transform: uppercase; }
        .container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }
        .section-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--ms-blue); margin-top: 48px; margin-bottom: 12px; }
        .preflight { background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F2 100%); border-left: 4px solid var(--accent-green); border-radius: 0 var(--radius) var(--radius) 0; padding: 24px 28px; margin: 24px 0; }
        .preflight h3 { font-size: 1rem; font-weight: 700; color: var(--accent-green); margin-bottom: 12px; }
        .preflight ul { font-size: 0.88rem; color: #2E5A30; line-height: 2; padding-left: 20px; }
        .preflight code { background: rgba(0,0,0,0.08); padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 0.82rem; }
        .exec-section { background: var(--card-bg); border-radius: var(--radius); box-shadow: var(--shadow); margin: 20px 0; border-left: 5px solid var(--ms-blue); overflow: hidden; }
        .exec-header { display: flex; align-items: center; gap: 16px; padding: 22px 24px; cursor: pointer; }
        .exec-header:hover { background: rgba(0,120,212,0.03); }
        .exec-number { width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; color: white; flex-shrink: 0; }
        .exec-header-text { flex: 1; }
        .exec-header-text h3 { font-size: 1.15rem; font-weight: 600; margin-bottom: 2px; }
        .exec-header-text .exec-purpose { font-size: 0.85rem; color: var(--text-light); font-style: italic; }
        .exec-time { font-size: 0.78rem; font-weight: 600; color: var(--text-light); background: var(--bg); padding: 4px 12px; border-radius: 20px; }
        .exec-expand { font-size: 1.2rem; color: var(--text-light); transition: transform 0.3s; }
        .exec-section.open .exec-expand { transform: rotate(180deg); }
        .exec-body { max-height: 0; overflow: hidden; transition: max-height 0.5s ease; }
        .exec-section.open .exec-body { max-height: 50000px; }
        .exec-content { padding: 0 24px 28px 82px; }
        .step-block { margin: 16px 0; padding: 16px 20px; background: #F8F9FA; border-radius: 8px; border-left: 3px solid var(--ms-blue); }
        .step-block.voice-step { border-left-color: var(--accent-red); background: #FFF5F5; }
        .step-block.chat-step { border-left-color: var(--accent-teal); background: #F0FAF9; }
        .step-block.copilot-step { border-left-color: var(--accent-purple); background: #F8F5FD; }
        .step-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: inline-block; padding: 2px 10px; border-radius: 4px; color: white; }
        .step-label.prep { background: var(--accent-green); }
        .step-label.click { background: var(--ms-blue); }
        .step-label.say { background: var(--accent-warm); }
        .step-label.show { background: var(--accent-teal); }
        .step-label.tip { background: #FFB900; color: #5D4510; }
        .step-label.copilot { background: var(--accent-purple); }
        .step-text { font-size: 0.9rem; line-height: 1.6; }
        .step-text .click-path { font-family: 'Consolas', monospace; background: rgba(0,120,212,0.1); color: var(--ms-blue-dark); padding: 2px 7px; border-radius: 4px; font-size: 0.82rem; }
        .talk-track { background: white; border: 1px solid #E0E0E0; border-radius: 8px; padding: 16px 20px; margin: 10px 0; font-style: italic; font-size: 0.88rem; line-height: 1.65; color: #444; position: relative; }
        .talk-track::before { content: '"'; font-size: 3rem; color: var(--accent-warm); position: absolute; top: -8px; left: 10px; opacity: 0.5; }
        .talk-track p { padding-left: 24px; }
        .sub-header { margin: 28px 0 10px; font-size: 1.02rem; font-weight: 600; color: var(--accent-teal); }
        .callout { border-radius: 8px; padding: 14px 18px; margin: 12px 0; font-size: 0.85rem; }
        .callout.warning { background: #FFF4CE; border-left: 3px solid #FFB900; color: #5D4510; }
        .callout.success { background: #E8F5E9; border-left: 3px solid var(--accent-green); color: #2E5A30; }
        .callout.info { background: var(--ms-blue-light); border-left: 3px solid var(--ms-blue); color: #003A6E; }
        .callout.roi { background: linear-gradient(135deg, #E8F5E9 0%, #F1F8E9 100%); border-left: 4px solid #2E7D32; color: #1B5E20; }
        .callout.roi::before { content: "💰 "; }
        .ref-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.82rem; }
        .ref-table th { background: #F3F2F1; font-weight: 600; text-align: left; padding: 8px 12px; border-bottom: 2px solid #D2D0CE; }
        .ref-table td { padding: 7px 12px; border-bottom: 1px solid var(--border); }
        .ref-table code { font-family: 'Consolas', monospace; font-size: 0.76rem; background: #F0F0F0; padding: 2px 6px; border-radius: 3px; }
        .ref-section-title { font-size: 0.88rem; font-weight: 600; color: var(--accent-teal); margin: 20px 0 6px; }
        .tier-pill { padding: 2px 10px; border-radius: 10px; font-size: 0.72rem; font-weight: 600; color: white; background: #A4262C; }
        .tier-pill.t1 { background: #A4262C; }
        .tier-pill.t2 { background: #D83B01; }
        .tier-pill.t3 { background: #0078D4; }
        .story-block { background: linear-gradient(135deg, #F3F0FF 0%, #FFF8F0 100%); border-left: 4px solid var(--accent-purple); border-radius: 0 var(--radius) var(--radius) 0; padding: 24px 28px; margin: 24px 0; }
        .story-block h3 { font-size: 1rem; font-weight: 700; color: var(--accent-purple); margin-bottom: 12px; }
        .story-block dl { margin: 12px 0; }
        .story-block dt { font-weight: 600; margin-top: 6px; font-size: 0.88rem; }
        .story-block dd { font-size: 0.84rem; color: var(--text-light); margin-left: 20px; }
        .story-block ol { margin: 12px 0 12px 20px; font-size: 0.86rem; }
        .story-block .story-note { font-style: italic; font-size: 0.84rem; color: var(--accent-purple); margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(92,45,145,0.15); }
        .voice-line { background: #FFF5F5; border: 1px solid #E8D0D0; border-radius: 8px; padding: 14px 20px 14px 36px; margin: 10px 0; font-style: italic; font-size: 0.88rem; color: #8B3A3A; position: relative; }
        .voice-line::before { content: '📞'; position: absolute; top: 14px; left: 12px; }
        .voice-line .voice-label { display: block; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; color: var(--accent-red); font-style: normal; margin-bottom: 4px; }
        .chat-line { background: #F0FAF9; border: 1px solid #C8E6E3; border-radius: 8px; padding: 14px 20px 14px 36px; margin: 10px 0; font-style: italic; font-size: 0.88rem; color: #2D6A65; position: relative; }
        .chat-line::before { content: '💬'; position: absolute; top: 14px; left: 12px; }
        .chat-line .chat-label { display: block; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; color: var(--accent-teal); font-style: normal; margin-bottom: 4px; }
        .demo-gold { background: linear-gradient(135deg, #FFF8E1 0%, #FFFDF5 100%); border-left: 4px solid #FFB900; border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 12px 0; font-size: 0.85rem; }
        .demo-gold strong { color: #856404; }
        .url-ref { font-family: 'Consolas', monospace; font-size: 0.78rem; color: var(--ms-blue); }
        .timing-bar { display: flex; gap: 0; margin: 28px 0 12px; border-radius: 8px; overflow: hidden; height: 8px; }
        .timing-bar .t-seg { height: 100%; }
        .nav-toggle { position: fixed; top: 16px; left: 16px; z-index: 10001; width: 40px; height: 40px; border: none; border-radius: 8px; background: var(--ms-blue); color: white; font-size: 1.3rem; cursor: pointer; box-shadow: 0 2px 10px rgba(0,0,0,0.25); }
        .nav-toggle:hover { background: var(--ms-blue-dark); }
        .nav-toggle.open { background: var(--accent-red); }
        .side-nav-backdrop { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 9999; }
        .side-nav-backdrop.visible { display: block; }
        .side-nav { position: fixed; top: 0; left: 0; width: 320px; height: 100vh; background: white; z-index: 10000; transform: translateX(-100%); transition: transform 0.25s ease; display: flex; flex-direction: column; box-shadow: 4px 0 20px rgba(0,0,0,0.15); }
        .side-nav.open { transform: translateX(0); }
        .side-nav-header { padding: 18px 20px 14px; background: linear-gradient(135deg, var(--ms-blue), var(--ms-blue-dark)); color: white; font-size: 0.82rem; display: flex; align-items: center; justify-content: space-between; }
        .side-nav-pin { background: none; border: 1px solid rgba(255,255,255,0.5); color: white; border-radius: 4px; padding: 2px 8px; font-size: 0.68rem; cursor: pointer; text-transform: uppercase; font-weight: 700; }
        .side-nav-pin.pinned { background: rgba(255,255,255,0.25); border-color: white; }
        .side-nav-body { flex: 1; overflow-y: auto; padding: 10px 0; }
        .side-nav-item { display: flex; align-items: center; gap: 10px; padding: 7px 18px; font-size: 0.8rem; color: var(--text); cursor: pointer; border-left: 3px solid transparent; }
        .side-nav-item:hover { background: #F3F2F1; }
        .side-nav-item.active { background: var(--ms-blue-light); border-left-color: var(--ms-blue); font-weight: 600; }
        .side-nav-num { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.68rem; color: white; }
        body.nav-pinned .container { margin-left: 340px; }
        body.nav-pinned .hero { padding-left: 340px; }
        body.nav-pinned .side-nav { box-shadow: 1px 0 3px rgba(0,0,0,0.08); }
        body.nav-pinned .side-nav-backdrop { display: none !important; }
        body.nav-pinned .nav-toggle { left: 330px; }
        footer { text-align: center; padding: 32px; color: var(--text-light); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 48px; }
        @media print { .nav-toggle, .side-nav, .side-nav-backdrop { display: none !important; } body.nav-pinned .container { margin-left: auto; } .exec-body { max-height: none !important; } }
    </style>'''

    def _get_scripts(self) -> str:
        """Get JavaScript for interactivity."""
        return '''
    <script>
        function toggleSection(header) {
            const section = header.parentElement;
            section.classList.toggle('open');
        }

        // Side navigation
        const navToggle = document.getElementById('navToggle');
        const sideNav = document.getElementById('sideNav');
        const navBackdrop = document.getElementById('navBackdrop');
        const navPin = document.getElementById('navPin');
        const navBody = document.getElementById('navBody');

        // Build nav items from sections
        document.querySelectorAll('.exec-section').forEach((section, idx) => {
            const header = section.querySelector('.exec-header-text h3');
            const number = section.querySelector('.exec-number');
            if (header) {
                const item = document.createElement('div');
                item.className = 'side-nav-item';
                item.innerHTML = `<div class="side-nav-num" style="background:${number ? getComputedStyle(number).background : '#0078D4'}">${idx + 1}</div><span>${header.textContent}</span>`;
                item.onclick = () => {
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    if (!document.body.classList.contains('nav-pinned')) {
                        sideNav.classList.remove('open');
                        navBackdrop.classList.remove('visible');
                        navToggle.classList.remove('open');
                    }
                };
                navBody.appendChild(item);
            }
        });

        navToggle.onclick = () => {
            const isOpen = sideNav.classList.toggle('open');
            navBackdrop.classList.toggle('visible', isOpen);
            navToggle.classList.toggle('open', isOpen);
        };

        navBackdrop.onclick = () => {
            sideNav.classList.remove('open');
            navBackdrop.classList.remove('visible');
            navToggle.classList.remove('open');
        };

        navPin.onclick = () => {
            document.body.classList.toggle('nav-pinned');
            navPin.classList.toggle('pinned');
            navPin.textContent = navPin.classList.contains('pinned') ? 'UNPIN' : 'PIN';
            if (document.body.classList.contains('nav-pinned')) {
                sideNav.classList.add('open');
                navBackdrop.classList.remove('visible');
            }
        };

        // Open first section by default
        document.querySelector('.exec-section')?.classList.add('open');
    </script>'''

    def generate_validation_report(
        self,
        customer_name: str,
        demo_data: Dict[str, Any],
        environment_config: Dict[str, Any]
    ) -> str:
        """Generate a data validation report."""
        accounts = demo_data.get("serviceAccounts", {}).get("accounts", [])
        contacts = demo_data.get("contacts", {}).get("contacts", [])
        cases = demo_data.get("demoCases", {}).get("cases", [])
        kb_articles = demo_data.get("kbArticles", {}).get("articles", [])

        # Validation checks
        checks = []

        # Check accounts
        checks.append({
            "category": "Accounts",
            "check": "At least 5 accounts exist",
            "status": "✅" if len(accounts) >= 5 else "❌",
            "details": f"{len(accounts)} accounts found"
        })
        checks.append({
            "category": "Accounts",
            "check": "Hero account has tier assigned",
            "status": "✅" if accounts and accounts[0].get("tier") else "❌",
            "details": f"Tier: {accounts[0].get('tier', 'MISSING') if accounts else 'No accounts'}"
        })

        # Check contacts
        checks.append({
            "category": "Contacts",
            "check": "At least 5 contacts exist",
            "status": "✅" if len(contacts) >= 5 else "❌",
            "details": f"{len(contacts)} contacts found"
        })
        checks.append({
            "category": "Contacts",
            "check": "Contacts linked to accounts",
            "status": "✅" if all(c.get("account") for c in contacts) else "⚠️",
            "details": f"{sum(1 for c in contacts if c.get('account'))}/{len(contacts)} linked"
        })
        checks.append({
            "category": "Contacts",
            "check": "Contacts have phone numbers",
            "status": "✅" if all(c.get("phone") for c in contacts) else "⚠️",
            "details": f"{sum(1 for c in contacts if c.get('phone'))}/{len(contacts)} have phone"
        })

        # Check cases
        checks.append({
            "category": "Cases",
            "check": "At least 10 demo cases exist",
            "status": "✅" if len(cases) >= 10 else "❌",
            "details": f"{len(cases)} cases found"
        })
        checks.append({
            "category": "Cases",
            "check": "Hero case designated",
            "status": "✅" if any(c.get("isHeroCase") for c in cases) else "⚠️",
            "details": "Hero case found" if any(c.get("isHeroCase") for c in cases) else "No hero case designated"
        })
        checks.append({
            "category": "Cases",
            "check": "Cases linked to accounts",
            "status": "✅" if all(c.get("account") for c in cases) else "⚠️",
            "details": f"{sum(1 for c in cases if c.get('account'))}/{len(cases)} linked"
        })

        # Check KB articles
        checks.append({
            "category": "Knowledge",
            "check": "At least 5 KB articles exist",
            "status": "✅" if len(kb_articles) >= 5 else "⚠️",
            "details": f"{len(kb_articles)} articles found"
        })

        # Build HTML
        rows = ""
        for check in checks:
            rows += f'''
            <tr>
                <td>{check["category"]}</td>
                <td>{check["check"]}</td>
                <td style="text-align:center; font-size:1.2rem;">{check["status"]}</td>
                <td>{check["details"]}</td>
            </tr>'''

        passed = sum(1 for c in checks if c["status"] == "✅")
        total = len(checks)
        score_color = "#107C10" if passed == total else "#D83B01" if passed >= total * 0.7 else "#A4262C"

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{customer_name} — Data Validation Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #0078D4; }}
        .score {{ font-size: 2rem; font-weight: 700; color: {score_color}; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #F3F2F1; text-align: left; padding: 12px; font-weight: 600; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #EDEBE9; }}
        tr:hover {{ background: #F9F9F9; }}
    </style>
</head>
<body>
    <h1>📋 Data Validation Report</h1>
    <p><strong>Customer:</strong> {customer_name}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

    <div class="score">Score: {passed}/{total} checks passed</div>

    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Check</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <h2>Summary</h2>
    <ul>
        <li>Accounts: {len(accounts)}</li>
        <li>Contacts: {len(contacts)}</li>
        <li>Cases: {len(cases)}</li>
        <li>KB Articles: {len(kb_articles)}</li>
    </ul>
</body>
</html>'''

    def generate_quick_reference(
        self,
        customer_name: str,
        inputs: Dict[str, Any],
        demo_data: Dict[str, Any],
        environment_config: Dict[str, Any]
    ) -> str:
        """Generate a one-page quick reference card."""
        env = environment_config.get("environment", {})
        accounts = demo_data.get("serviceAccounts", {}).get("accounts", [])
        contacts = demo_data.get("contacts", {}).get("contacts", [])
        cases = demo_data.get("demoCases", {}).get("cases", [])

        hero_account = accounts[0] if accounts else {}
        hero_contacts = [c for c in contacts if c.get("account") == hero_account.get("name")][:3]
        hero_case = next((c for c in cases if c.get("isHeroCase")), cases[0] if cases else {})

        contacts_html = ""
        for c in hero_contacts:
            contacts_html += f"<li><strong>{c.get('firstName', '')} {c.get('lastName', '')}</strong> — {c.get('phone', '')} — {c.get('email', '')}</li>"

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{customer_name} — Quick Reference</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #0078D4; margin-bottom: 8px; }}
        .subtitle {{ color: #605E5C; margin-bottom: 24px; }}
        .card {{ background: #F8F9FA; border-radius: 8px; padding: 20px; margin: 16px 0; border-left: 4px solid #0078D4; }}
        .card h3 {{ margin-top: 0; color: #0078D4; }}
        ul {{ line-height: 1.8; }}
        code {{ background: #E8E8E8; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; }}
        .tier {{ display: inline-block; background: #A4262C; color: white; padding: 2px 10px; border-radius: 10px; font-size: 0.8rem; font-weight: 600; }}
    </style>
</head>
<body>
    <h1>🎯 {customer_name} Demo Quick Reference</h1>
    <p class="subtitle">Print this card and keep it handy during the demo</p>

    <div class="card">
        <h3>🔗 URLs</h3>
        <ul>
            <li><strong>D365 Org:</strong> <code>{env.get("url", "https://YOUR_ORG.crm.dynamics.com")}</code></li>
            <li><strong>Outlook:</strong> <code>https://outlook.office.com</code></li>
        </ul>
    </div>

    <div class="card">
        <h3>🏢 Hero Account</h3>
        <ul>
            <li><strong>Name:</strong> {hero_account.get("name", "")} <span class="tier">{hero_account.get("tier", "")}</span></li>
            <li><strong>Account #:</strong> <code>{hero_account.get("accountNumber", "")}</code></li>
            <li><strong>Phone:</strong> {hero_account.get("phone", "")}</li>
        </ul>
    </div>

    <div class="card">
        <h3>👤 Hero Contacts</h3>
        <ul>
            {contacts_html}
        </ul>
    </div>

    <div class="card">
        <h3>📋 Hero Case</h3>
        <ul>
            <li><strong>Title:</strong> {hero_case.get("title", "")}</li>
            <li><strong>Priority:</strong> {hero_case.get("priority", "")}</li>
            <li><strong>Demo Use:</strong> {hero_case.get("demoUse", "")}</li>
        </ul>
    </div>

    <div class="card" style="border-left-color: #107C10;">
        <h3>✅ Pre-Demo Checklist</h3>
        <ul>
            <li>☐ D365 Workspace open, logged in</li>
            <li>☐ Voice Channel status "Available"</li>
            <li>☐ Secondary phone ready for call-in</li>
            <li>☐ Notifications silenced</li>
            <li>☐ Hero account verified in D365</li>
        </ul>
    </div>
</body>
</html>'''
