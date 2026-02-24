"""
Transpile the 3 Plumbing Code Intelligence agents to Copilot Studio native format
and create a solution definition for deployment to Mfg Gold Template.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.copilot_studio_transpiler_agent import CopilotStudioTranspilerAgent

def main():
    t = CopilotStudioTranspilerAgent()
    
    agents = [
        "PlumbingCodeSourceMonitor",
        "PlumbingCodeTechExtractor", 
        "PlumbingCodeMonthlySynthesizer"
    ]
    
    results = {}
    
    # Transpile each agent
    for agent_name in agents:
        print(f"\n{'='*60}")
        print(f"Transpiling: {agent_name}")
        print(f"{'='*60}")
        try:
            raw = t.perform(action="transpile", agent_name=agent_name)
            result = json.loads(raw)
            results[agent_name] = result
            print(f"  Status: {result.get('status')}")
            if result.get('status') == 'success':
                print(f"  Output dir: {result.get('output_directory', 'N/A')}")
                print(f"  Files generated: {result.get('files_generated', [])}")
                print(f"  Topics: {result.get('topics_generated', 0)}")
            else:
                print(f"  Error: {result.get('error', 'Unknown')}")
                print(f"  Details: {json.dumps(result, indent=2)[:500]}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            results[agent_name] = {"status": "exception", "error": str(e)}
    
    # Show summary
    print(f"\n{'='*60}")
    print("TRANSPILATION SUMMARY")
    print(f"{'='*60}")
    for agent_name, result in results.items():
        status = result.get('status', 'unknown')
        print(f"  {agent_name}: {status}")
    
    # Create solution definition
    print(f"\n{'='*60}")
    print("Creating Solution Definition")
    print(f"{'='*60}")
    try:
        raw = t.perform(
            action="create_solution",
            solution_name="plumbing_code_intelligence",
            solution_display_name="Plumbing Code Intelligence",
            description="Commercial plumbing code monitoring pipeline with source scanning, technical extraction, and monthly synthesis.",
            agent_names=json.dumps(agents)
        )
        sol_result = json.loads(raw)
        print(f"  Status: {sol_result.get('status')}")
        if sol_result.get('status') == 'success':
            print(f"  Solution file: {sol_result.get('solution_file', 'N/A')}")
        else:
            print(f"  Error: {sol_result.get('error', 'Unknown')}")
            print(f"  Details: {json.dumps(sol_result, indent=2)[:500]}")
    except Exception as e:
        print(f"  EXCEPTION: {e}")

if __name__ == "__main__":
    main()
