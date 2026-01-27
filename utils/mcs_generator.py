"""
MCS Generator - Generates Copilot Studio agents in MCS format.

This module provides utilities for:
1. Generating MCS-format agent configurations from Python agent definitions
2. Deploying agents to Copilot Studio via API with correct topic states
3. Creating local MCS files for Copilot Studio CLI import

The MCS format is the native file format used by Copilot Studio CLI.
"""

import os
import json
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class MCSGenerator:
    """
    Generates Copilot Studio agent configurations in MCS format.
    
    This generator creates agents with the correct topic configuration to avoid
    the "I'm sorry, I'm not sure how to help" issue by:
    1. Disabling Fallback, End of Conversation, and other problematic topics
    2. Setting up a Main topic that catches all messages
    3. Configuring the GPT component with proper instructions
    """
    
    # Topics that should be ACTIVE
    ACTIVE_TOPICS = [
        "Conversation Start",
        "On Error"
    ]
    
    # Topics that should be DISABLED (Inactive)
    DISABLED_TOPICS = [
        "Fallback",
        "End of Conversation",
        "Multiple Topics Matched",
        "Escalate",
        "Greeting",
        "Goodbye",
        "Thank you",
        "Start Over",
        "Reset Conversation",
        "Sign in",
        "Lesson 1",
        "Lesson 2",
        "Lesson 3"
    ]
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the MCS Generator.
        
        Args:
            template_dir: Path to MCS templates directory
        """
        if template_dir is None:
            # Default to templates/mcs in the project root
            project_root = Path(__file__).parent.parent
            template_dir = project_root / "templates" / "mcs"
        
        self.template_dir = Path(template_dir)
    
    def generate_schema_name(self, name: str, prefix: str = "rapp") -> str:
        """
        Generate a valid schema name from an agent name.
        
        Args:
            name: Agent display name
            prefix: Schema name prefix
            
        Returns:
            Valid schema name (alphanumeric with underscores)
        """
        # Remove special characters, replace spaces with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        clean_name = clean_name.replace(' ', '_')
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        return f"{prefix}_{clean_name}_{timestamp}"
    
    def escape_for_yaml(self, text: str) -> str:
        """Escape text for embedding in YAML strings."""
        if not text:
            return ""
        # Escape backslashes first, then quotes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\r\\n')
        return text
    
    def generate_agent_mcs_yml(
        self,
        name: str,
        instructions: str,
        conversation_starters: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate agent.mcs.yml content.
        
        Args:
            name: Agent display name
            instructions: Agent instructions/system prompt
            conversation_starters: List of {title, text} dicts
            
        Returns:
            YAML content for agent.mcs.yml
        """
        starters = conversation_starters or []
        
        yaml_content = f"""kind: GptComponentMetadata
displayName: {name}
instructions: |
{self._indent_text(instructions, 2)}
"""
        
        if starters:
            yaml_content += "conversationStarters:\n"
            for starter in starters:
                yaml_content += f'  - title: "{starter.get("title", "")}"\n'
                yaml_content += f'    text: "{starter.get("text", "")}"\n'
        
        return yaml_content
    
    def generate_settings_mcs_yml(
        self,
        name: str,
        schema_name: str,
        auth_mode: str = "Integrated",
        channels: List[str] = None
    ) -> str:
        """
        Generate settings.mcs.yml content.
        
        Args:
            name: Agent display name
            schema_name: Agent schema name
            auth_mode: Authentication mode
            channels: List of channel IDs
            
        Returns:
            YAML content for settings.mcs.yml
        """
        channels = channels or ["MsTeams"]
        
        yaml_content = f"""displayName: {name}
schemaName: {schema_name}
authenticationMode: {auth_mode}

gPTSettings:
  defaultSchemaName: {schema_name}.gpt.default

# AI Settings - CRITICAL for generative AI to work
# Without useModelKnowledge: true, agent will say "Sorry, I am not able to find a related topic"
aISettings:
  useModelKnowledge: true
  isSemanticSearchEnabled: true
  isFileAnalysisEnabled: true
  contentModeration: Medium
  optInUseLatestModels: true
  generativeAnswersEnabled: true
  boostedConversationsEnabled: true

# Use generative orchestration for better query handling
settings:
  orchestrationType: Generative

channels:
"""
        for channel in channels:
            yaml_content += f"  - channelId: {channel}\n"
        
        return yaml_content
    
    def generate_bot_definition(
        self,
        name: str,
        schema_name: str,
        instructions: str,
        conversation_starters: List[Dict[str, str]] = None,
        publisher: str = "DefaultPublisher",
        bot_id: str = None,
        flow_id: str = None,
        is_sub_agent: bool = False
    ) -> Dict[str, Any]:
        """
        Generate complete botdefinition.json content.
        
        Args:
            name: Agent display name
            schema_name: Agent schema name
            instructions: Agent instructions
            conversation_starters: List of {title, text} dicts
            publisher: Publisher unique name
            bot_id: Bot ID (generated if not provided)
            flow_id: Power Automate flow ID for RAPP backend
            is_sub_agent: If True, agent is a sub-agent (more topics disabled)
            
        Returns:
            Bot definition dictionary
        """
        bot_id = bot_id or str(uuid.uuid4())
        starters = conversation_starters or []
        
        # Generate component IDs
        gpt_id = str(uuid.uuid4())
        conv_start_id = str(uuid.uuid4())
        on_error_id = str(uuid.uuid4())
        fallback_id = str(uuid.uuid4())
        end_conv_id = str(uuid.uuid4())
        escalate_id = str(uuid.uuid4())
        multi_topics_id = str(uuid.uuid4())
        greeting_id = str(uuid.uuid4())
        goodbye_id = str(uuid.uuid4())
        
        # Build conversation starters YAML
        starters_yaml = ""
        for starter in starters:
            starters_yaml += f"  - title: {starter.get('title', '')}\r\n"
            starters_yaml += f"    text: {starter.get('text', '')}\r\n"
        
        # Escape instructions for embedding
        escaped_instructions = self.escape_for_yaml(instructions)
        
        components = [
            # GPT Component (Active)
            {
                "$kind": "GptComponent",
                "displayName": name,
                "id": gpt_id,
                "parentBotId": bot_id,
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Active",
                "status": "Active",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.gpt.default",
                "metadata": f"kind: GptComponentMetadata\r\ndisplayName: {name}\r\ninstructions: |\r\n{self._indent_text(escaped_instructions, 2)}\r\nconversationStarters:\r\n{starters_yaml}"
            },
            # Conversation Start (Active)
            {
                "$kind": "DialogComponent",
                "displayName": "Conversation Start",
                "id": conv_start_id,
                "parentBotId": bot_id,
                "description": "Initializes conversation variables.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Active",
                "status": "Active",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.ConversationStart",
                "dialog": 'kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnConversationStart\r\n  id: main\r\n  actions:\r\n    - kind: SetVariable\r\n      id: setVariable_initHistory\r\n      variable: Global.VarConversationHistory\r\n      value: "\\"[]\\""\r\n'
            },
            # On Error (Active)
            {
                "$kind": "DialogComponent",
                "displayName": "On Error",
                "id": on_error_id,
                "parentBotId": bot_id,
                "description": "Handles errors gracefully.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Active",
                "status": "Active",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.OnError",
                "dialog": "kind: AdaptiveDialog\r\nstartBehavior: UseLatestPublishedContentAndCancelOtherTopics\r\nbeginDialog:\r\n  kind: OnError\r\n  id: main\r\n  actions:\r\n    - kind: SendActivity\r\n      id: sendMessage_error\r\n      activity: I encountered an issue processing your request. Please try again.\r\n"
            },
            # Fallback (DISABLED)
            {
                "$kind": "DialogComponent",
                "displayName": "Fallback",
                "id": fallback_id,
                "parentBotId": bot_id,
                "description": "DISABLED - Would cause 'I'm sorry' messages.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Inactive",
                "status": "Inactive",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.Fallback",
                "dialog": "kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnUnknownIntent\r\n  id: main\r\n  actions: []\r\n"
            },
            # End of Conversation (DISABLED)
            {
                "$kind": "DialogComponent",
                "displayName": "End of Conversation",
                "id": end_conv_id,
                "parentBotId": bot_id,
                "description": "DISABLED - Would interrupt flow with surveys.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Inactive",
                "status": "Inactive",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.EndofConversation",
                "dialog": "kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnSystemRedirect\r\n  id: main\r\n  actions: []\r\n"
            },
            # Escalate (DISABLED)
            {
                "$kind": "DialogComponent",
                "displayName": "Escalate",
                "id": escalate_id,
                "parentBotId": bot_id,
                "description": "DISABLED - Not needed for RAPP agents.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Inactive",
                "status": "Inactive",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.Escalate",
                "dialog": "kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnEscalate\r\n  id: main\r\n  actions: []\r\n"
            },
            # Multiple Topics Matched (DISABLED)
            {
                "$kind": "DialogComponent",
                "displayName": "Multiple Topics Matched",
                "id": multi_topics_id,
                "parentBotId": bot_id,
                "description": "DISABLED - Would cause clarification prompts.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Inactive",
                "status": "Inactive",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.MultipleTopicsMatched",
                "dialog": "kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnSelectIntent\r\n  id: main\r\n  actions: []\r\n"
            },
            # Greeting (DISABLED)
            {
                "$kind": "DialogComponent",
                "displayName": "Greeting",
                "id": greeting_id,
                "parentBotId": bot_id,
                "description": "DISABLED - Can conflict with generative AI.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Inactive",
                "status": "Inactive",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.Greeting",
                "dialog": "kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnRecognizedIntent\r\n  id: main\r\n  intent:\r\n    displayName: Greeting\r\n    triggerQueries:\r\n      - Hello\r\n      - Hi\r\n  actions: []\r\n"
            },
            # Goodbye (DISABLED)
            {
                "$kind": "DialogComponent",
                "displayName": "Goodbye",
                "id": goodbye_id,
                "parentBotId": bot_id,
                "description": "DISABLED - Can trigger unwanted responses.",
                "shareContext": {"$kind": "ContentShareContext"},
                "state": "Inactive",
                "status": "Inactive",
                "publisherUniqueName": publisher,
                "schemaName": f"{schema_name}.topic.Goodbye",
                "dialog": "kind: AdaptiveDialog\r\nbeginDialog:\r\n  kind: OnRecognizedIntent\r\n  id: main\r\n  intent:\r\n    displayName: Goodbye\r\n    triggerQueries:\r\n      - Bye\r\n      - Goodbye\r\n  actions: []\r\n"
            }
        ]
        
        # Build entity
        entity = {
            "$kind": "BotEntity",
            "displayName": name,
            "schemaName": schema_name,
            "cdsBotId": bot_id,
            "accessControlPolicy": "GroupMembership",
            "authenticationMode": "Integrated",
            "authenticationTrigger": "Always",
            "configuration": {
                "$kind": "BotConfiguration",
                "channels": [
                    {"$kind": "ChannelDefinition", "channelId": "MsTeams"}
                ],
                "gPTSettings": {
                    "$kind": "GPTSettings",
                    "defaultSchemaName": f"{schema_name}.gpt.default"
                },
                "isLightweightBot": False,
                "aISettings": {
                    "$kind": "AISettings",
                    "useModelKnowledge": True,  # CRITICAL: Enables AI to handle unmatched queries
                    "isSemanticSearchEnabled": True,
                    "isFileAnalysisEnabled": True,
                    "contentModeration": "Medium",
                    "optInUseLatestModels": True,
                    "generativeAnswersEnabled": True,
                    "boostedConversationsEnabled": True
                },
                "settings": {
                    "orchestrationType": "Generative"
                }
            },
            "language": 1033,
            "runtimeProvider": "PowerVirtualAgents",
            "state": "Active",
            "status": 1
        }
        
        return {
            "$kind": "BotDefinition",
            "components": components,
            "entity": entity
        }
    
    def _indent_text(self, text: str, spaces: int) -> str:
        """Indent text by specified number of spaces."""
        if not text:
            return ""
        indent = " " * spaces
        lines = text.split('\n')
        return '\n'.join(indent + line for line in lines)
    
    def save_mcs_files(
        self,
        output_dir: str,
        name: str,
        instructions: str,
        conversation_starters: List[Dict[str, str]] = None,
        schema_name: str = None
    ) -> str:
        """
        Save complete MCS file structure to disk.
        
        Args:
            output_dir: Output directory path
            name: Agent display name
            instructions: Agent instructions
            conversation_starters: List of {title, text} dicts
            schema_name: Schema name (generated if not provided)
            
        Returns:
            Path to output directory
        """
        output_path = Path(output_dir)
        schema_name = schema_name or self.generate_schema_name(name)
        
        # Create directories
        (output_path / "topics").mkdir(parents=True, exist_ok=True)
        (output_path / ".mcs").mkdir(parents=True, exist_ok=True)
        
        # Generate and save agent.mcs.yml
        agent_yml = self.generate_agent_mcs_yml(name, instructions, conversation_starters)
        (output_path / "agent.mcs.yml").write_text(agent_yml, encoding='utf-8')
        
        # Generate and save settings.mcs.yml
        settings_yml = self.generate_settings_mcs_yml(name, schema_name)
        (output_path / "settings.mcs.yml").write_text(settings_yml, encoding='utf-8')
        
        # Generate and save botdefinition.json
        bot_def = self.generate_bot_definition(
            name=name,
            schema_name=schema_name,
            instructions=instructions,
            conversation_starters=conversation_starters
        )
        (output_path / ".mcs" / "botdefinition.json").write_text(
            json.dumps(bot_def, indent=2),
            encoding='utf-8'
        )
        
        # Save topic files (simplified versions)
        topic_templates = {
            "ConversationStart.mcs.yml": self._generate_conversation_start_topic(),
            "OnError.mcs.yml": self._generate_on_error_topic(),
            "Fallback.mcs.yml": self._generate_fallback_topic(),
        }
        
        for filename, content in topic_templates.items():
            (output_path / "topics" / filename).write_text(content, encoding='utf-8')
        
        return str(output_path)
    
    def _generate_conversation_start_topic(self) -> str:
        """Generate ConversationStart topic content."""
        return """# Conversation Start - ACTIVE
kind: AdaptiveDialog
beginDialog:
  kind: OnConversationStart
  id: main
  actions:
    - kind: SetVariable
      id: setVariable_initHistory
      variable: Global.VarConversationHistory
      value: "\"[]\""
"""
    
    def _generate_on_error_topic(self) -> str:
        """Generate OnError topic content."""
        return """# On Error - ACTIVE
kind: AdaptiveDialog
startBehavior: UseLatestPublishedContentAndCancelOtherTopics
beginDialog:
  kind: OnError
  id: main
  actions:
    - kind: SendActivity
      id: sendMessage_error
      activity: I encountered an issue processing your request. Please try again.
"""
    
    def _generate_fallback_topic(self) -> str:
        """Generate Fallback topic content (DISABLED)."""
        return """# Fallback - DISABLED
# This topic should remain inactive to prevent "I'm sorry" messages
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions: []
"""


# Export for easy importing
__all__ = ['MCSGenerator']
