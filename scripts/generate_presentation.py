"""
Generate full Zurn Elkay CI System presentation
Based on zurnelkay_ci_demo_guide.html content
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.powerpoint_generator_agent_v2 import PowerPointGeneratorAgentV2
from agents.architecture_diagram_agent import ArchitectureDiagramAgent
import json

def generate_architecture_diagram():
    """Generate the architecture diagram for the presentation."""
    agent = ArchitectureDiagramAgent()
    result = agent.perform(
        action='create_diagram',
        customer='Zurn Elkay',
        title='zurnelkay_ci_architecture',
        style='microsoft',
        nodes=[
            {'id': 'orchestrator', 'label': 'CI Orchestrator\\n(Level 0)', 'type': 'function_app'},
            {'id': 'synthesizer', 'label': 'Cross-BU Synthesizer\\n(Level 2)', 'type': 'function_app'},
            {'id': 'drains', 'label': 'Drains CI\\nAgent', 'type': 'function_app'},
            {'id': 'wilkins', 'label': 'Wilkins CI\\nAgent', 'type': 'function_app'},
            {'id': 'drinking', 'label': 'Drinking Water\\nCI Agent', 'type': 'function_app'},
            {'id': 'sinks', 'label': 'Sinks CI\\nAgent', 'type': 'function_app'},
            {'id': 'brass', 'label': 'Commercial Brass\\nCI Agent', 'type': 'function_app'},
            {'id': 'cosmos', 'label': 'Intelligence\\nDatabase', 'type': 'cosmosdb'},
            {'id': 'openai', 'label': 'Azure OpenAI\\nGPT-4', 'type': 'openai'}
        ],
        connections=[
            {'from': 'orchestrator', 'to': 'synthesizer', 'label': 'coordinates'},
            {'from': 'synthesizer', 'to': 'drains'},
            {'from': 'synthesizer', 'to': 'wilkins'},
            {'from': 'synthesizer', 'to': 'drinking'},
            {'from': 'synthesizer', 'to': 'sinks'},
            {'from': 'synthesizer', 'to': 'brass'},
            {'from': 'drains', 'to': 'cosmos'},
            {'from': 'wilkins', 'to': 'cosmos'},
            {'from': 'drinking', 'to': 'cosmos'},
            {'from': 'sinks', 'to': 'cosmos'},
            {'from': 'brass', 'to': 'cosmos'},
            {'from': 'orchestrator', 'to': 'openai'}
        ]
    )
    data = json.loads(result)
    return data.get('path', '')

def main():
    # Try to use existing architecture diagram, or skip if generation fails
    arch_diagram_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "arch_diagrams", "zurn_elkay", "architecture_diagram.png"
    )
    
    if not os.path.exists(arch_diagram_path):
        try:
            print("Generating architecture diagram...")
            arch_diagram_path = generate_architecture_diagram()
            print(f"Architecture diagram: {arch_diagram_path}")
        except Exception as e:
            print(f"Warning: Could not generate architecture diagram: {e}")
            arch_diagram_path = ""
    else:
        print(f"Using existing architecture diagram: {arch_diagram_path}")
    
    agent = PowerPointGeneratorAgentV2()
    
    slides = [
        # 1. Title Slide
        {'type': 'title', 'title': 'Zurn Elkay CI System', 'subtitle': 'AI-Powered Competitive Intelligence Platform'},
        
        # 2. Agenda
        {'type': 'content', 'title': 'Agenda', 'content': [
            'Executive Overview & The Challenge',
            'System Architecture (7 Agents)',
            'The Agent Deep Dive',
            'Demo Flow (30-45 min)',
            'Business Value & ROI',
            'Q&A'
        ]},
        
        # 3. Executive Overview Section
        {'type': 'section', 'title': 'Executive Overview'},
        
        # 4. The Challenge - Before/After Style
        {'type': 'before_after', 'title': 'The Challenge: Before vs After', 'items': [
            {'before': 'Manual research takes 2-3 weeks per quarter', 'after': 'Automated analysis in hours'},
            {'before': '5 BUs using 5 different methodologies', 'after': 'One unified framework across all BUs'},
            {'before': 'Missing cross-portfolio moves by parent cos', 'after': 'Automatic parent company detection'},
            {'before': 'Inconsistent source attribution', 'after': 'Every item sourced with confidence score'},
            {'before': 'Manual roll-up for executive briefings', 'after': 'CEO-ready briefings on demand'}
        ]},
        
        # 5. Value Cards - Key Benefits
        {'type': 'value_cards', 'title': 'Key Value Delivered', 'cards': [
            {'icon': '⏱️', 'title': 'Time Savings', 'description': 'Quarterly analysis completed in hours', 
             'before': 'Weeks', 'after': 'Hours'},
            {'icon': '📊', 'title': 'Consistency', 'description': 'Single framework for all 5 BUs',
             'before': '5 Methods', 'after': '1 Standard'},
            {'icon': '🔗', 'title': 'Cross-BU Visibility', 'description': 'Parent company coordination detection',
             'before': 'Siloed', 'after': 'Enterprise View'}
        ]},
        
        # 6. Metric Boxes - Impact Stats
        {'type': 'metric_boxes', 'title': 'By The Numbers', 'metrics': [
            {'value': '7', 'label': 'AI Agents', 'description': 'Working in coordination', 'color': 'ms_blue'},
            {'value': '5', 'label': 'Business Units', 'description': 'Unified coverage', 'color': 'ms_green'},
            {'value': '44', 'label': 'Unit Tests', 'description': '100% passing', 'color': 'ms_orange'}
        ]},
        
        # 7. Architecture Section
        {'type': 'section', 'title': 'System Architecture'},
        
        # 8. Architecture Diagram
        {'type': 'image', 'title': 'Three-Tier Agent Architecture', 
         'image_path': arch_diagram_path,
         'caption': 'Level 0: Orchestrator | Level 2: Synthesizer | Level 1: 5 BU-Specific Agents'},
        
        # 9. Architecture Explanation
        {'type': 'content', 'title': 'How the Tiers Work Together', 'content': [
            'Level 0 (Orchestrator): Coordinates workflows, validates quality, manages errors',
            'Level 2 (Synthesizer): Aggregates all 5 BU reports, detects cross-BU patterns',
            'Level 1 (5 BU Agents): Category-specific intelligence gathering',
            'Cosmos DB: Stores all intelligence with versioning',
            'Azure OpenAI: Powers analysis and synthesis'
        ]},
        
        # 10. The 7 Agents Section
        {'type': 'section', 'title': 'The 7 Agents'},
        
        # 11. Agent Cards Overview
        {'type': 'agent_cards', 'title': 'Meet The 7 Agents', 'agents': [
            {'name': 'CI Orchestrator', 'level': 0, 'description': 'Coordinates workflows, validates quality, manages errors', 'competitors': []},
            {'name': 'Cross-BU Synthesizer', 'level': 2, 'description': 'Aggregates all BU reports, detects cross-BU patterns', 'competitors': []},
            {'name': 'Drains CI Agent', 'level': 1, 'description': 'Core Spec Drains, Siteworks, FOG Separation', 'competitors': ['JR Smith', 'Watts', 'MiFab']},
            {'name': 'Wilkins CI Agent', 'level': 1, 'description': 'Backflow Prevention, PRVs, TMVs', 'competitors': ['Watts', 'Caleffi', 'Apollo']},
            {'name': 'Drinking Water Agent', 'level': 1, 'description': 'Bottle Fillers, Filtration, NSF tracking', 'competitors': ['Elkay', 'Oasis', '3M']},
            {'name': 'Sinks CI Agent', 'level': 1, 'description': 'Healthcare & ADA sinks, Infection control', 'competitors': ['Just Mfg', 'T&S', 'Kohler']},
            {'name': 'Commercial Brass Agent', 'level': 1, 'description': 'Flush Valves, Faucets, Touchless', 'competitors': ['Sloan', 'Kohler', 'TOTO']}
        ]},
        
        # 12. Level 1 Agents Detail - Drains & Wilkins
        {'type': 'two_column', 'title': 'Level 1: Drains & Wilkins Agents',
         'left': {'title': 'Drains CI Agent', 'content': [
             'Core Spec Drains analysis',
             'Siteworks & FOG Separation',
             'Key Competitors:',
             '  • JR Smith, Watts',
             '  • MiFab, Schier'
         ]},
         'right': {'title': 'Wilkins CI Agent', 'content': [
             'Backflow Prevention & PRVs',
             'TMVs with digital innovation focus',
             'Key Competitors:',
             '  • Watts, Caleffi',
             '  • Honeywell, Apollo'
         ]}
        },
        
        # 13. Level 1 Agents - Drinking Water & Sinks
        {'type': 'two_column', 'title': 'Level 1: Drinking Water & Sinks Agents',
         'left': {'title': 'Drinking Water CI Agent', 'content': [
             'Bottle Fillers & Filtration',
             'NSF certification tracking',
             'Key Competitors:',
             '  • Elkay, Oasis',
             '  • Halsey Taylor, 3M/Cuno'
         ]},
         'right': {'title': 'Sinks CI Agent', 'content': [
             'Healthcare & ADA sinks',
             'Infection control focus',
             'Key Competitors:',
             '  • Just Mfg, T&S Brass',
             '  • Kohler, Bradley'
         ]}
        },
        
        # 14. Level 1 Agent - Commercial Brass
        {'type': 'content', 'title': 'Level 1: Commercial Brass CI Agent', 'content': [
            'Products: Flush Valves, Faucets, Touchless Solutions',
            'Focus: Platform strategy tracking (Sloan Connect, Kohler Portfolio)',
            'Key Competitors: Sloan, Kohler, Bradley, TOTO',
            'Specialty: Digital integration and IoT capabilities',
            'Tracks: Sensor technology, water efficiency innovations'
        ]},
        
        # 15. Demo Flow Section
        {'type': 'section', 'title': 'Demo Flow'},
        
        # 16. Demo Process Flow
        {'type': 'process_flow', 'title': 'Demo Flow Overview (30-45 min)', 'steps': [
            {'title': 'Opening', 'description': 'Context & challenges', 'duration': '2 min'},
            {'title': 'Architecture', 'description': 'Three-tier overview', 'duration': '3 min'},
            {'title': 'Drains Demo', 'description': 'Live quarterly analysis', 'duration': '8 min'},
            {'title': 'Other BUs', 'description': 'Wilkins, Drinking, Sinks, Brass', 'duration': '18 min'},
            {'title': 'Synthesis', 'description': 'Cross-BU aggregation', 'duration': '5 min'},
            {'title': 'Close', 'description': 'Value summary & Q&A', 'duration': '5 min'}
        ]},
        
        # 17. Demo Steps Part 1
        {'type': 'content', 'title': 'Demo Flow: Part 1 (15 min)', 'content': [
            '1. Opening & Context (2 min) - Three challenges overview',
            '2. Architecture Overview (3 min) - Three-tier structure explained',
            '3. Drains Deep Dive (8 min) - Run quarterly analysis live',
            '   • Show output structure',
            '   • Demonstrate parent company coordination check'
        ]},
        
        # 18. Demo Steps Part 2
        {'type': 'content', 'title': 'Demo Flow: Part 2 (14 min)', 'content': [
            '4. Wilkins - Digital Focus (5 min) - Smart valve comparison',
            '5. Drinking Water (4 min) - NSF certification verification',
            '6. Sinks - Healthcare (4 min) - Morris Group detection demo',
            '7. Commercial Brass (5 min) - Platform strategy tracking'
        ]},
        
        # 19. Demo Steps Part 3
        {'type': 'content', 'title': 'Demo Flow: Part 3 (10 min)', 'content': [
            '8. Cross-BU Synthesis (5 min)',
            '   • Enterprise aggregation',
            '   • Cross-BU pattern detection',
            '   • Executive briefing generation',
            '9. Orchestrator & Closing (5 min)',
            '   • System health check',
            '   • Value summary & Q&A'
        ]},
        
        # 20. Business Value Section
        {'type': 'section', 'title': 'Business Value'},
        
        # 21. Value Comparison (visual version)
        {'type': 'value_cards', 'title': 'The Transformation', 'cards': [
            {'icon': '📅', 'title': 'Time to Insight', 'description': 'Quarterly competitive analysis', 
             'before': '2-3 Weeks', 'after': 'Hours'},
            {'icon': '🎯', 'title': 'Quality & Coverage', 'description': 'Consistent framework across all BUs', 
             'before': 'Inconsistent', 'after': 'Enterprise-wide'},
            {'icon': '🔍', 'title': 'Parent Co. Tracking', 'description': 'Cross-portfolio coordination detection', 
             'before': 'Manual', 'after': 'Automatic'},
            {'icon': '📋', 'title': 'Source Attribution', 'description': 'Every intelligence item traced', 
             'before': 'Scattered', 'after': '100% Sourced'}
        ]},
        
        # 22. Parent Companies Tracked
        {'type': 'content', 'title': 'Parent Companies We Track', 'content': [
            'Watts Water Technologies - Largest multi-BU competitor (Drains, Wilkins, Drinking Water, Brass)',
            'Morris Group - Just Mfg + T&S Brass bundled solutions',
            'Lixil - Global brand with American Standard',
            'Geberit - European premium positioning',
            'Aalberts - Caleffi acquisition play'
        ]},
        
        # 23. Q&A Section
        {'type': 'section', 'title': 'Q&A'},
        
        # 24. Anticipated Questions
        {'type': 'content', 'title': 'Anticipated Questions', 'content': [
            'How do we keep competitor lists current? → Simple config updates, no code changes',
            'Adding data sources? → API integration ready (trade pubs, internal DBs)',
            'Power BI integration? → Structured JSON output, CSV exports available',
            'Real-time vs quarterly? → System supports both modes',
            'Confidence levels? → Built-in High/Medium/Low calibration per source'
        ]},
        
        # 25. Closing
        {'type': 'title', 'title': 'Thank You', 'subtitle': 'Zurn Elkay CI System | 7 Agents | 5 Business Units | Built with RAPP Framework'}
    ]
    
    result = agent.perform(
        action='create_presentation',
        template='PowerpointTemplateBlue',
        customer='Zurn Elkay',
        title='Zurn Elkay CI System',
        output_filename='zurn_elkay_ci_full_presentation',
        slides=slides
    )
    
    print(json.dumps(json.loads(result), indent=2))

if __name__ == "__main__":
    main()
