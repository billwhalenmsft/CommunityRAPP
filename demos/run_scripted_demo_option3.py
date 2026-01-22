"""
ScriptedDemoAgent Demo Runner - Option 3
Shows how the ScriptedDemoAgent works with the Carrier demo
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load settings
settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local.settings.json')
with open(settings_path, 'r') as f:
    for k, v in json.load(f).get('Values', {}).items():
        if v:
            os.environ[k] = v

from agents.scripted_demo_agent import ScriptedDemoAgent

def main():
    print("="*70)
    print("OPTION 3: ScriptedDemoAgent")
    print("="*70)
    print()
    
    agent = ScriptedDemoAgent()
    
    # Step 1: List demos
    print("📋 Step 1: List Available Demos")
    print("-"*50)
    result = json.loads(agent.perform(action='list_demos'))
    demos = result.get('available_demos', [])
    print(f"Found {len(demos)} demos total\n")
    
    carrier_demos = [d for d in demos if 'carrier' in d.lower()]
    print("Carrier-related demos:")
    for d in carrier_demos:
        print(f"  • {d}")
    
    input("\n➤ Press Enter to load the interactive demo...")
    
    # Step 2: Load demo
    print("\n📂 Step 2: Load Demo Structure")
    print("-"*50)
    demo_name = "carrier_case_triage_interactive_demo"
    result = json.loads(agent.perform(action='load_demo', demo_name=demo_name))
    
    if result.get('status') == 'success':
        # The load_demo response includes fields directly, not nested in demo_data
        print(f"✅ Loaded: {result.get('demo_name', demo_name)}")
        print(f"   Description: {result.get('description', 'N/A')[:60]}...")
        print(f"   Steps: {result.get('total_steps', 0)}")
        print(f"   Trigger phrases: {result.get('trigger_phrases', [])[:3]}")
        
        # For conversation flow, we need to read the full demo
        full_demo = agent._read_demo_file(demo_name)
        if full_demo:
            agents = full_demo.get('agents_utilized', [])
            print(f"\n   Agents ({len(agents)}):")
            for a in agents:
                if isinstance(a, dict):
                    print(f"     {a.get('icon','')} {a.get('name','')}: {a.get('purpose','')[:40]}...")
                else:
                    print(f"     • {a}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown')}")
        return
    
    input("\n➤ Press Enter to run through the conversation flow...")
    
    # Step 3: Walk through conversation
    print("\n💬 Step 3: Conversation Flow")
    print("-"*50)
    
    # Get the full demo data including conversation_flow
    full_demo = agent._read_demo_file(demo_name) or {}
    flow = full_demo.get('conversation_flow', [])
    
    if not flow:
        print("No conversation flow found in demo!")
        return
        
    for i, step in enumerate(flow, 1):
        print(f"\n{'='*60}")
        print(f"[Step {step.get('step_number', i)}/{len(flow)}] {step.get('title', 'Step')}")
        print(f"{'='*60}")
        
        user_msg = step.get('user_message', '')
        print(f"\n👤 User: \"{user_msg}\"")
        
        # Get response from agent
        print("\n🤖 Calling ScriptedDemoAgent.perform(action='respond')...")
        raw_response = agent.perform(
            action='respond',
            demo_name=demo_name,
            user_input=user_msg
        )
        
        # Response could be JSON or plain text
        try:
            response = json.loads(raw_response)
            if response.get('status') == 'success':
                agent_text = response.get('response', '')
            elif response.get('status') == 'error':
                print(f"   Error: {response.get('error', 'Unknown')}")
                agent_text = None
            else:
                # Treat as formatted text response
                agent_text = raw_response
        except json.JSONDecodeError:
            # Plain text response (legacy format)
            agent_text = raw_response
        
        if agent_text:
            # Truncate for display
            lines = agent_text.split('\n')[:15]
            print("\n🤖 Agent Response:")
            for line in lines:
                print(f"   {line}")
            if len(agent_text.split('\n')) > 15:
                print("   ...")
        
        if i < len(flow):
            input("\n➤ Press Enter for next step...")
    
    print("\n" + "="*70)
    print("✅ SCRIPTED DEMO COMPLETE!")
    print("="*70)
    print("""
The ScriptedDemoAgent:
1. Loads demo JSON from Azure File Storage (or local demos folder)
2. Matches user input against trigger_phrases
3. Returns the canned agent_response for that step
4. Can also call real agents dynamically if configured

This is perfect for:
- Consistent, repeatable demos
- Training scenarios  
- Sales presentations
- Conference booth demos

To use in the RAPP chat UI, just say:
  "carrier demo" or "show me case triage"
""")


if __name__ == "__main__":
    main()
