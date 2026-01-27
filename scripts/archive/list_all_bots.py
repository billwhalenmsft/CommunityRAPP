"""
List all bots in the environment to see what's available.
"""

import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.copilot_studio_api import CopilotStudioClient

def list_all_bots():
    """List all bots in the environment."""
    
    client = CopilotStudioClient(
        environment_url='https://org6feab6b5.crm.dynamics.com',
    )
    client.authenticate()
    
    # Get all bots
    bots_url = f"{client.api_base_url}/bots?$select=botid,name,schemaname,statecode"
    headers = client.headers
    
    response = requests.get(bots_url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    bots = response.json().get('value', [])
    
    print(f"\nFound {len(bots)} bots:\n")
    print("=" * 80)
    
    for bot in bots:
        name = bot.get('name', 'N/A')
        bot_id = bot.get('botid', 'N/A')
        schema = bot.get('schemaname', 'N/A')
        state = "Active" if bot.get('statecode') == 0 else "Inactive"
        
        print(f"Name: {name}")
        print(f"  ID: {bot_id}")
        print(f"  Schema: {schema}")
        print(f"  State: {state}")
        print("-" * 80)

if __name__ == "__main__":
    list_all_bots()
