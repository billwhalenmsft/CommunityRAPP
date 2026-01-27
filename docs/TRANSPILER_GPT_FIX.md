# Copilot Studio Transpiler - GPT Component Fix

## Problem
When deploying RAPP agents to Copilot Studio, the agents were missing the GPT component (componenttype 10) which contains the AI instructions/system prompt. This caused:
1. Agents failed to publish with "Something went wrong" errors
2. Agents had no AI capabilities because they lacked instructions
3. All 7 ZE agents were deployed without functioning properly

## Root Cause
The transpiler and API client were NOT creating the GPT component when deploying agents. The bot entity in Dataverse does NOT have a native `description` or `instructions` field - these must be stored in a separate `botcomponent` record with `componenttype = 10`.

## Solution

### 1. Updated `utils/copilot_studio_api.py`

#### Added `create_gpt_component()` method
```python
def create_gpt_component(self, bot_id: str, name: str, instructions: str, description: str = "") -> str:
    """Create a GPT/AI Instructions component for an agent."""
    # Creates componenttype 10 with the instructions
```

#### Updated `create_agent()` method
- Added `instructions` and `system_prompt` parameters
- Now automatically calls `create_gpt_component()` after creating the bot
- Combines instructions from multiple sources (instructions, system_prompt, systemPrompt)

#### Updated `COMPONENT_TYPES` constant
- Clarified that type 10 is "gpt" (GPT/AI Instructions component)
- Added comment explaining this is CRITICAL for agent to function

#### Updated `deploy_transpiled_agent()` method
- Now extracts instructions from manifest (checks `instructions`, `systemPrompt`, `system_prompt`)
- Passes instructions to `create_agent()` which creates the GPT component

### 2. Updated `agents/copilot_studio_transpiler_agent.py`

#### Enhanced `_parse_agent()` method
- Now supports both Python (.py) and JSON (.json) agent files
- Extracts `systemPrompt` from JSON agent definitions
- Prioritizes JSON files (which have full systemPrompt) over Python files

#### Added `_parse_json_agent()` method
- Parses RAPP JSON agent definition files from `demos/` directory
- Extracts the full `systemPrompt` field
- Falls back to building a prompt from description/scope if missing

#### Updated `_find_agent_file()` method
- Changed search priority: JSON files checked FIRST, then Python
- JSON files in `demos/` contain the complete `systemPrompt`

#### Updated `_generate_agent_manifest()` method
- Now includes the full `systemPrompt` in the manifest
- Adds both `instructions` and `systemPrompt` fields for compatibility
- Falls back to description-based instructions if no prompt found

#### Updated `_deploy_solution()` method (in `_deploy_solution`)
- Extracts instructions from manifest before deployment
- Can also load from `instructions.md` file as backup
- Passes instructions to `client.create_agent()` which creates GPT component

## How It Works Now

1. **Transpile** parses agent (prefers JSON) → extracts `systemPrompt` → saves to manifest
2. **Deploy** reads manifest → extracts instructions → calls `create_agent(instructions=...)`
3. **create_agent** creates bot → calls `create_gpt_component()` → associates component
4. **Agent in Copilot Studio** has GPT component with instructions → can publish → works!

## Testing

Run the test script to verify:
```bash
python scripts/test_transpiler_fix.py
```

Expected output:
- `[PASS] systemPrompt extracted successfully!`
- `[PASS] Instructions included in manifest!`
- `[PASS] GPT component type defined!`
- `[PASS] create_gpt_component method exists!`
- `[PASS] create_agent accepts 'instructions' parameter!`

## Re-Deploying Agents

To re-deploy with the fix:

```python
from agents.copilot_studio_transpiler_agent import CopilotStudioTranspilerAgent
import json

t = CopilotStudioTranspilerAgent()

# Option 1: Re-transpile and deploy single agent
result = json.loads(t.perform(action='transpile', agent_name='zurnelkay_drains_ci_agent'))
print(result)

# Then deploy
result = json.loads(t.perform(action='deploy', agent_name='zurnelkay_drains_ci_agent'))
print(result)

# Option 2: Deploy entire Zurn Elkay solution
result = json.loads(t.perform(action='deploy_solution', predefined='zurnelkay'))
print(result)
```

## Files Changed

1. `utils/copilot_studio_api.py`
   - Added `create_gpt_component()` method
   - Updated `create_agent()` to accept and use instructions
   - Updated `deploy_transpiled_agent()` to extract and pass instructions
   - Fixed `COMPONENT_TYPES` to show type 10 is "gpt"

2. `agents/copilot_studio_transpiler_agent.py`
   - Added JSON agent file parsing (`_parse_json_agent()`)
   - Added helper methods for JSON parsing
   - Updated file search to prefer JSON files
   - Updated manifest generation to include systemPrompt
   - Updated deployment to pass instructions

3. New test script: `scripts/test_transpiler_fix.py`
