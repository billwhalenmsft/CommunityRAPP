"""
Copilot Studio API Client
Provides programmatic access to create and manage Copilot Studio agents via Dataverse Web API.

This module enables deploying transpiled RAPP agents directly to Copilot Studio
without manual configuration in the UI.

Authentication:
- Uses Azure AD authentication via MSAL
- Requires an app registration with Dataverse permissions
- Supports both interactive and service principal auth

Dataverse Tables Used:
- bot: The Copilot/Agent entity
- botcomponent: Topics, variables, skills, etc.
- bot_botcomponent: Many-to-many relationship linking components to bots
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any

# Azure Identity for authentication
try:
    from azure.identity import (
        DefaultAzureCredential,
        InteractiveBrowserCredential,
        ClientSecretCredential,
        AzureCliCredential,
        TokenCachePersistenceOptions
    )
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False

# MSAL for token acquisition (alternative auth method)
try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False

# HTTP client
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Dataverse API version
DATAVERSE_API_VERSION = "v9.2"

# Bot component types (from Dataverse schema)
# CRITICAL: Type 15 is the Custom GPT component - REQUIRED for agents to work!
COMPONENT_TYPES = {
    "topic": 0,
    "skill": 1,
    "bot_variable": 2,
    "bot_entity": 3,
    "dialog": 4,
    "trigger": 5,
    "language_understanding": 6,
    "language_generation": 7,
    "dialog_schema": 8,
    "topic_v2": 9,  # Modern topics
    "bot_translations_v2": 10,  # Bot translations - NOT for instructions!
    "bot_entity_v2": 11,
    "bot_variable_v2": 12,
    "skill_v2": 13,
    "file_attachment": 14,
    "custom_gpt": 15,  # Custom GPT - THIS IS FOR INSTRUCTIONS!
    "knowledge_source": 16,
    "external_trigger": 17,
    "copilot_settings": 18,
    "test_case": 19
}

# Authentication modes
AUTH_MODES = {
    "unspecified": 0,
    "none": 1,
    "integrated": 2,
    "custom_azure_ad": 3,
    "generic_oauth2": 4
}

# Bot languages (subset - full list in Dataverse schema)
BOT_LANGUAGES = {
    "en-us": 1033,
    "en-gb": 2057,
    "es-es": 3082,
    "fr-fr": 1036,
    "de-de": 1031,
    "pt-br": 1046,
    "ja-jp": 1041,
    "zh-cn": 2052
}


class CopilotStudioAPIError(Exception):
    """Custom exception for Copilot Studio API errors."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class CopilotStudioClient:
    """
    Client for interacting with Copilot Studio via Dataverse Web API.
    
    Enables programmatic creation and management of:
    - Agents (bots)
    - Topics
    - Variables
    - Knowledge sources
    - And more...
    
    Example:
        client = CopilotStudioClient(
            environment_url="https://org.crm.dynamics.com",
            tenant_id="your-tenant-id",
            client_id="your-app-client-id"
        )
        await client.authenticate()
        
        # Create an agent
        bot_id = await client.create_agent(
            name="My Agent",
            description="A helpful agent",
            instructions="You are a helpful assistant..."
        )
        
        # Create a topic for the agent
        topic_id = await client.create_topic(
            bot_id=bot_id,
            name="Greeting",
            trigger_phrases=["hello", "hi", "hey"],
            content="Welcome message topic content..."
        )
    """
    
    def __init__(
        self,
        environment_url: str = None,
        tenant_id: str = None,
        client_id: str = None,
        client_secret: str = None,
        use_interactive_auth: bool = True
    ):
        """
        Initialize the Copilot Studio client.
        
        Args:
            environment_url: Dataverse environment URL (e.g., https://org.crm.dynamics.com)
            tenant_id: Azure AD tenant ID
            client_id: App registration client ID
            client_secret: App registration client secret (for service principal auth)
            use_interactive_auth: Use interactive browser auth if no secret provided
        """
        self.environment_url = environment_url or os.environ.get("DATAVERSE_ENVIRONMENT_URL")
        self.tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID")
        self.client_id = client_id or os.environ.get("COPILOT_STUDIO_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("COPILOT_STUDIO_CLIENT_SECRET")
        self.use_interactive_auth = use_interactive_auth
        
        self._access_token = None
        self._token_expires_at = None
        
        # Validate requirements
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library is required: pip install requests")
        
        if not self.environment_url:
            raise ValueError("environment_url is required (or set DATAVERSE_ENVIRONMENT_URL)")
    
    @property
    def api_base_url(self) -> str:
        """Get the Dataverse Web API base URL."""
        return f"{self.environment_url.rstrip('/')}/api/data/{DATAVERSE_API_VERSION}"
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        if not self._access_token:
            raise CopilotStudioAPIError("Not authenticated. Call authenticate() first.")
        
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Prefer": "return=representation"
        }
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    def authenticate(self) -> bool:
        """
        Authenticate to Dataverse/Power Platform.
        
        Returns:
            bool: True if authentication successful
        """
        scope = f"{self.environment_url}/.default"
        
        if self.client_secret and MSAL_AVAILABLE:
            # Service principal authentication
            return self._authenticate_service_principal(scope)
        elif AZURE_IDENTITY_AVAILABLE:
            # DefaultAzureCredential or interactive
            return self._authenticate_azure_identity(scope)
        elif MSAL_AVAILABLE:
            # MSAL interactive authentication
            return self._authenticate_msal_interactive(scope)
        else:
            raise CopilotStudioAPIError(
                "No authentication method available. Install azure-identity or msal."
            )
    
    def _authenticate_service_principal(self, scope: str) -> bool:
        """Authenticate using service principal (client credentials)."""
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_for_client(scopes=[scope])
        
        if "access_token" in result:
            self._access_token = result["access_token"]
            logger.info("Authenticated via service principal")
            return True
        else:
            error = result.get("error_description", "Unknown error")
            raise CopilotStudioAPIError(f"Service principal auth failed: {error}")
    
    def _authenticate_azure_identity(self, scope: str) -> bool:
        """Authenticate using Azure Identity library with caching."""
        try:
            if self.client_secret:
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                token = credential.get_token(scope)
                self._access_token = token.token
                logger.info("Authenticated via service principal")
                return True
            
            # Try Azure CLI first (uses existing az login session - no prompts!)
            try:
                credential = AzureCliCredential(tenant_id=self.tenant_id)
                token = credential.get_token(scope)
                self._access_token = token.token
                logger.info("Authenticated via Azure CLI (cached session)")
                return True
            except Exception as cli_error:
                logger.debug(f"Azure CLI auth not available: {cli_error}")
            
            # Fall back to interactive browser with token caching
            if self.use_interactive_auth:
                # Enable persistent token cache to avoid repeated logins
                cache_options = TokenCachePersistenceOptions(
                    name="copilot_studio_cache",
                    allow_unencrypted_storage=True  # Required on some systems
                )
                credential = InteractiveBrowserCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    cache_persistence_options=cache_options
                )
            else:
                credential = DefaultAzureCredential()
            
            token = credential.get_token(scope)
            self._access_token = token.token
            logger.info("Authenticated via Azure Identity")
            return True
        except Exception as e:
            raise CopilotStudioAPIError(f"Azure Identity auth failed: {e}")
    
    def _authenticate_msal_interactive(self, scope: str) -> bool:
        """Authenticate using MSAL interactive browser flow."""
        app = msal.PublicClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        # Try cache first
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent([scope], account=accounts[0])
            if result and "access_token" in result:
                self._access_token = result["access_token"]
                logger.info("Authenticated via cached token")
                return True
        
        # Interactive auth
        result = app.acquire_token_interactive(scopes=[scope])
        
        if "access_token" in result:
            self._access_token = result["access_token"]
            logger.info("Authenticated via interactive browser")
            return True
        else:
            error = result.get("error_description", "Unknown error")
            raise CopilotStudioAPIError(f"Interactive auth failed: {error}")
    
    # =========================================================================
    # BOT (AGENT) OPERATIONS
    # =========================================================================
    
    def create_agent(
        self,
        name: str,
        schema_name: str = None,
        description: str = "",
        instructions: str = None,
        system_prompt: str = None,
        language: str = "en-us",
        authentication_mode: str = "none",
        **kwargs
    ) -> str:
        """
        Create a new Copilot Studio agent with GPT instructions.
        
        Args:
            name: Display name of the agent
            schema_name: Unique schema name (auto-generated if not provided)
            description: Agent description (used in GPT component)
            instructions: AI instructions/system prompt for the agent
            system_prompt: Alias for instructions (for RAPP compatibility)
            language: Primary language (e.g., "en-us")
            authentication_mode: Authentication mode ("none", "integrated", etc.)
            
        Returns:
            str: The bot ID (GUID)
        """
        schema_name = schema_name or self._generate_schema_name(name)
        language_code = BOT_LANGUAGES.get(language.lower(), 1033)
        auth_mode = AUTH_MODES.get(authentication_mode, 1)
        
        # Combine instructions from multiple sources
        agent_instructions = instructions or system_prompt or kwargs.get('systemPrompt', '')
        if not agent_instructions and description:
            # Fall back to description as a basic instruction
            agent_instructions = f"You are {name}. {description}"
        
        # Get web browsing setting (default True for better functionality)
        enable_web_browsing = kwargs.get('web_browsing', kwargs.get('webBrowsing', True))
        
        # Build bot configuration with AI settings
        # CRITICAL: useModelKnowledge MUST be True for generative AI to work!
        # Generate a unique GPT component suffix to avoid schema collisions
        gpt_suffix = uuid.uuid4().hex[:8]
        
        bot_configuration = {
            "$kind": "BotConfiguration",
            "gPTSettings": {
                "$kind": "GPTSettings",
                "defaultSchemaName": f"{schema_name}.gpt.{gpt_suffix}",
                "isGPTGenerated": True
            },
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
                "orchestrationType": "Generative"  # Use generative orchestration
            }
        }
        
        # Note: The bot entity does NOT have a 'description' field
        # Instructions are stored in a GPT botcomponent (type 15)
        bot_data = {
            "name": name,
            "schemaname": schema_name,
            "language": language_code,
            "authenticationmode": auth_mode,
            "runtimeprovider": 0,  # Power Virtual Agents
            "authenticationtrigger": 0,  # As Needed
            "statecode": 0,  # Active
            "statuscode": 1,  # Active
            "configuration": json.dumps(bot_configuration)  # CRITICAL: Include AI settings
        }
        
        # Add optional fields that exist on the bot entity
        for key in ["template", "origin", "iconbase64"]:
            if key in kwargs:
                bot_data[key] = kwargs[key]
        
        response = requests.post(
            f"{self.api_base_url}/bots",
            headers=self.headers,
            json=bot_data
        )
        
        bot_id = None
        if response.status_code in [200, 201, 204]:
            # Extract bot ID from response or OData-EntityId header
            if response.text:
                result = response.json()
                bot_id = result.get("botid")
            else:
                # Parse from OData-EntityId header
                entity_id = response.headers.get("OData-EntityId", "")
                if entity_id:
                    # Format: https://org.crm.dynamics.com/api/data/v9.2/bots(guid)
                    import re
                    match = re.search(r'bots\(([^)]+)\)', entity_id)
                    if match:
                        bot_id = match.group(1)
            
            if not bot_id:
                raise CopilotStudioAPIError("Bot created but could not extract ID")
            
            # CRITICAL: Create GPT component with instructions
            # This is REQUIRED for the agent to function in Copilot Studio!
            if agent_instructions:
                try:
                    self.create_gpt_component(
                        bot_id=bot_id,
                        name=f"{name} - Instructions",
                        instructions=agent_instructions,
                        description=description,
                        bot_schema_name=schema_name,
                        gpt_suffix=gpt_suffix
                    )
                    logger.info(f"Created GPT component with instructions for bot {bot_id}")
                except Exception as gpt_error:
                    logger.error(f"Failed to create GPT component: {gpt_error}")
                    # Don't fail agent creation, but log the issue
            
            return bot_id
        else:
            raise CopilotStudioAPIError(
                f"Failed to create agent: {response.text}",
                status_code=response.status_code,
                response=response.json() if response.text else None
            )
    
    def create_gpt_component(
        self,
        bot_id: str,
        name: str,
        instructions: str,
        description: str = "",
        web_browsing: bool = False,
        code_interpreter: bool = False,
        bot_schema_name: str = None,
        gpt_suffix: str = None
    ) -> str:
        """
        Create a Custom GPT component for an agent (componenttype 15).
        
        This is CRITICAL - without a GPT component, agents cannot:
        - Use AI/generative capabilities
        - Be published
        - Function properly in Copilot Studio
        
        The GPT component stores instructions in the 'data' field as YAML format.
        
        Args:
            bot_id: Parent bot ID
            name: Component display name
            instructions: The AI instructions/system prompt
            description: Optional description
            web_browsing: Enable web browsing capability
            code_interpreter: Enable code interpreter capability
            bot_schema_name: Optional bot schema name (will be retrieved if not provided)
            
        Returns:
            str: The component ID
        """
        # Schema name must be unique across the environment.
        # Using a UUID suffix avoids collisions when recreating agents.
        if not bot_schema_name:
            bot = self.get_agent(bot_id)
            bot_schema_name = bot.get('schemaname', self._generate_schema_name(name))
        
        suffix = gpt_suffix or uuid.uuid4().hex[:8]
        schema_name = f"{bot_schema_name}.gpt.{suffix}"
        
        # Build GPT component data as YAML (this is what working agents use)
        # Format based on analysis of working agents like "D365 Sales Agent - Research"
        gpt_data_yaml = f"""kind: GptComponentMetadata
instructions: |-
{self._indent_text(instructions, 2)}
responseInstructions:
gptCapabilities:
  webBrowsing: {'true' if web_browsing else 'false'}
  codeInterpreter: {'true' if code_interpreter else 'false'}
aISettings:
  model:
    kind: CurrentModels
displayName: {name}
"""
        
        component_data = {
            "name": name,
            "schemaname": schema_name,
            "componenttype": 15,  # Custom GPT - CORRECT TYPE!
            "data": gpt_data_yaml,  # Instructions go in 'data' as YAML
            "parentbotid@odata.bind": f"/bots({bot_id})",
            "statecode": 0,
            "statuscode": 1
        }
        
        response = requests.post(
            f"{self.api_base_url}/botcomponents",
            headers=self.headers,
            json=component_data
        )
        
        if response.status_code in [200, 201, 204]:
            if response.text:
                result = response.json()
                component_id = result.get("botcomponentid")
            else:
                entity_id = response.headers.get("OData-EntityId", "")
                import re
                match = re.search(r'botcomponents\(([^)]+)\)', entity_id)
                component_id = match.group(1) if match else None
            
            if component_id:
                # Associate component with bot
                self._associate_component_to_bot(bot_id, component_id)
                logger.info(f"Created Custom GPT component {component_id} for bot {bot_id}")
                return component_id
            
            raise CopilotStudioAPIError("GPT component created but could not extract ID")
        else:
            raise CopilotStudioAPIError(
                f"Failed to create GPT component: {response.text}",
                status_code=response.status_code
            )
    
    def _indent_text(self, text: str, spaces: int) -> str:
        """Indent each line of text by specified number of spaces."""
        indent = " " * spaces
        lines = text.split("\n")
        return "\n".join(indent + line for line in lines)
    
    def get_agent(self, bot_id: str) -> Dict:
        """Get an agent by ID."""
        response = requests.get(
            f"{self.api_base_url}/bots({bot_id})",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise CopilotStudioAPIError(
                f"Failed to get agent: {response.text}",
                status_code=response.status_code
            )
    
    def update_agent_configuration(
        self,
        bot_id: str,
        enable_generative_ai: bool = True,
        enable_web_browsing: bool = True,
        enable_semantic_search: bool = True
    ) -> bool:
        """
        Update an agent's configuration to enable generative AI capabilities.
        
        This is CRITICAL for agents to work properly. Without these settings,
        agents will show "Sorry, I am not able to find a related topic" errors.
        
        Args:
            bot_id: The bot ID to update
            enable_generative_ai: Enable useModelKnowledge (REQUIRED for AI to work)
            enable_web_browsing: Enable web browsing capability
            enable_semantic_search: Enable semantic search
            
        Returns:
            bool: True if update succeeded
        """
        # Get current configuration
        bot = self.get_agent(bot_id)
        config_str = bot.get('configuration', '{}')
        
        try:
            config = json.loads(config_str) if isinstance(config_str, str) else config_str
        except:
            config = {}
        
        # Ensure aISettings exists with correct values
        if 'aISettings' not in config:
            config['aISettings'] = {"$kind": "AISettings"}
        
        # CRITICAL settings for generative AI to work
        config['aISettings']['useModelKnowledge'] = enable_generative_ai
        config['aISettings']['isSemanticSearchEnabled'] = enable_semantic_search
        config['aISettings']['isFileAnalysisEnabled'] = True
        config['aISettings']['contentModeration'] = config['aISettings'].get('contentModeration', 'Medium')
        config['aISettings']['optInUseLatestModels'] = True
        config['aISettings']['generativeAnswersEnabled'] = enable_generative_ai
        config['aISettings']['boostedConversationsEnabled'] = enable_generative_ai
        
        # Ensure gPTSettings has isGPTGenerated flag
        if 'gPTSettings' in config:
            config['gPTSettings']['isGPTGenerated'] = True
        
        # Set orchestration type
        if 'settings' not in config:
            config['settings'] = {}
        config['settings']['orchestrationType'] = 'Generative'
        
        # Update the bot
        new_config_str = json.dumps(config)
        
        response = requests.patch(
            f"{self.api_base_url}/bots({bot_id})",
            headers=self.headers,
            json={"configuration": new_config_str}
        )
        
        if response.status_code in [200, 204]:
            logger.info(f"Updated agent configuration for {bot_id} - generative AI enabled")
            return True
        else:
            raise CopilotStudioAPIError(
                f"Failed to update agent configuration: {response.text}",
                status_code=response.status_code
            )
    
    def list_agents(self, filter_query: str = None) -> List[Dict]:
        """List agents, optionally filtered."""
        url = f"{self.api_base_url}/bots"
        if filter_query:
            url += f"?$filter={filter_query}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            raise CopilotStudioAPIError(
                f"Failed to list agents: {response.text}",
                status_code=response.status_code
            )
    
    def delete_agent(self, bot_id: str) -> bool:
        """Delete an agent."""
        response = requests.delete(
            f"{self.api_base_url}/bots({bot_id})",
            headers=self.headers
        )
        
        if response.status_code == 204:
            return True
        else:
            raise CopilotStudioAPIError(
                f"Failed to delete agent: {response.text}",
                status_code=response.status_code
            )
    
    def publish_agent(self, bot_id: str) -> Dict:
        """
        Publish an agent using the PvaPublish action.
        
        Args:
            bot_id: The bot ID (GUID) to publish
            
        Returns:
            Dict with publish status/job information
        """
        # PvaPublish is a bound action on the bot entity
        url = f"{self.api_base_url}/bots({bot_id})/Microsoft.Dynamics.CRM.PvaPublish"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={}  # Empty body - action takes no parameters
        )
        
        if response.status_code in [200, 202, 204]:
            # 200 = immediate success with response
            # 202 = accepted (async)
            # 204 = success with no content
            if response.content:
                try:
                    return response.json()
                except:
                    return {"Status": "Published", "StatusCode": response.status_code}
            else:
                return {"Status": "Published", "StatusCode": response.status_code}
        else:
            raise CopilotStudioAPIError(
                f"Failed to publish agent: {response.text}",
                status_code=response.status_code
            )
    
    def provision_agent(self, bot_id: str) -> Dict:
        """
        Provision an agent using the PvaProvision action.
        This may be required before publishing newly created agents.
        
        Args:
            bot_id: The bot ID (GUID) to provision
            
        Returns:
            Dict with provision status
        """
        url = f"{self.api_base_url}/bots({bot_id})/Microsoft.Dynamics.CRM.PvaProvision"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={}
        )
        
        if response.status_code in [200, 202, 204]:
            if response.content:
                try:
                    return response.json()
                except:
                    return {"Status": "Provisioned", "StatusCode": response.status_code}
            else:
                return {"Status": "Provisioned", "StatusCode": response.status_code}
        else:
            raise CopilotStudioAPIError(
                f"Failed to provision agent: {response.text}",
                status_code=response.status_code
            )
    
    # =========================================================================
    # BOT COMPONENT (TOPIC) OPERATIONS
    # =========================================================================
    
    def create_topic(
        self,
        bot_id: str,
        name: str,
        trigger_phrases: List[str] = None,
        content: str = None,
        schema_name: str = None,
        description: str = "",
        component_type: str = "topic_v2"
    ) -> str:
        """
        Create a topic for an agent.
        
        Args:
            bot_id: Parent bot ID
            name: Topic display name
            trigger_phrases: List of trigger phrases
            content: Topic content (YAML or JSON depending on format)
            schema_name: Unique schema name
            description: Topic description
            component_type: Component type (default: topic_v2)
            
        Returns:
            str: The topic component ID
        """
        schema_name = schema_name or self._generate_schema_name(name)
        comp_type = COMPONENT_TYPES.get(component_type, 9)
        
        # Build topic content structure
        topic_content = self._build_topic_content(
            name=name,
            trigger_phrases=trigger_phrases or [],
            description=description
        )
        
        component_data = {
            "name": name,
            "schemaname": schema_name,
            "description": description,
            "componenttype": comp_type,
            "content": json.dumps(topic_content) if isinstance(topic_content, dict) else topic_content,
            "parentbotid@odata.bind": f"/bots({bot_id})",
            "statecode": 0,
            "statuscode": 1
        }
        
        response = requests.post(
            f"{self.api_base_url}/botcomponents",
            headers=self.headers,
            json=component_data
        )
        
        if response.status_code in [200, 201, 204]:
            if response.text:
                result = response.json()
                component_id = result.get("botcomponentid")
            else:
                entity_id = response.headers.get("OData-EntityId", "")
                import re
                match = re.search(r'botcomponents\(([^)]+)\)', entity_id)
                component_id = match.group(1) if match else None
            
            if component_id:
                # Associate topic with bot
                self._associate_component_to_bot(bot_id, component_id)
                return component_id
            
            raise CopilotStudioAPIError("Topic created but could not extract ID")
        else:
            raise CopilotStudioAPIError(
                f"Failed to create topic: {response.text}",
                status_code=response.status_code
            )
    
    def _build_topic_content(
        self,
        name: str,
        trigger_phrases: List[str],
        description: str = ""
    ) -> Dict:
        """Build the topic content structure."""
        # This is a simplified topic structure
        # Full Copilot Studio topics have more complex YAML/JSON structures
        return {
            "kind": "AdaptiveDialog",
            "id": f"topic_{self._to_snake_case(name)}",
            "displayName": name,
            "description": description,
            "triggers": [
                {
                    "kind": "OnRecognizedIntent",
                    "intent": self._to_snake_case(name),
                    "triggerQueries": trigger_phrases
                }
            ],
            "actions": [
                {
                    "kind": "SendMessage",
                    "message": f"You triggered the {name} topic."
                }
            ]
        }
    
    def _associate_component_to_bot(self, bot_id: str, component_id: str) -> bool:
        """Associate a bot component with a bot via the bot_botcomponent relationship."""
        # Use the associate endpoint
        association_data = {
            "@odata.id": f"{self.api_base_url}/botcomponents({component_id})"
        }
        
        response = requests.post(
            f"{self.api_base_url}/bots({bot_id})/bot_botcomponent/$ref",
            headers=self.headers,
            json=association_data
        )
        
        if response.status_code in [200, 201, 204]:
            return True
        else:
            logger.warning(f"Failed to associate component: {response.text}")
            return False
    
    def get_agent_topics(self, bot_id: str) -> List[Dict]:
        """Get all topics for an agent."""
        # Query components linked to this bot
        response = requests.get(
            f"{self.api_base_url}/bots({bot_id})/bot_botcomponent?"
            f"$filter=componenttype eq 9 or componenttype eq 0",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            raise CopilotStudioAPIError(
                f"Failed to get topics: {response.text}",
                status_code=response.status_code
            )
    
    # =========================================================================
    # DEPLOYMENT HELPER
    # =========================================================================
    
    def deploy_transpiled_agent(
        self,
        agent_manifest: Dict,
        topics: List[Dict],
        flows: List[Dict] = None
    ) -> Dict:
        """
        Deploy a transpiled RAPP agent to Copilot Studio.
        
        Args:
            agent_manifest: Agent definition from transpiler
            topics: List of topic definitions
            flows: List of flow definitions (for future use with Power Automate API)
            
        Returns:
            Dict with deployment results including bot_id and topic_ids
        """
        results = {
            "status": "success",
            "bot_id": None,
            "topic_ids": [],
            "gpt_component_id": None,
            "errors": []
        }
        
        try:
            # Extract instructions from manifest
            # Check multiple possible sources in order of priority
            instructions = (
                agent_manifest.get("instructions") or
                agent_manifest.get("systemPrompt") or
                agent_manifest.get("system_prompt") or
                agent_manifest.get("description", "")
            )
            
            # Create the agent WITH instructions (GPT component created automatically)
            # The create_agent method now includes proper AI settings configuration
            bot_id = self.create_agent(
                name=agent_manifest.get("displayName", agent_manifest.get("name")),
                description=agent_manifest.get("description", ""),
                instructions=instructions,
                language=agent_manifest.get("primaryLanguage", "en-us"),
                web_browsing=agent_manifest.get("webBrowsing", True)
            )
            results["bot_id"] = bot_id
            logger.info(f"Created agent with instructions and AI settings: {bot_id}")
            
            # Ensure AI settings are correctly configured (belt and suspenders)
            try:
                self.update_agent_configuration(
                    bot_id=bot_id,
                    enable_generative_ai=True,
                    enable_web_browsing=agent_manifest.get("webBrowsing", True),
                    enable_semantic_search=True
                )
                logger.info(f"Verified AI settings for agent: {bot_id}")
            except Exception as config_error:
                logger.warning(f"Could not verify AI settings: {config_error}")
                results["errors"].append(f"AI settings verification: {str(config_error)}")
            
            # Create topics
            for topic in topics:
                try:
                    trigger_phrases = []
                    if "triggers" in topic:
                        for trigger in topic.get("triggers", []):
                            trigger_phrases.extend(trigger.get("triggerQueries", []))
                    
                    topic_id = self.create_topic(
                        bot_id=bot_id,
                        name=topic.get("displayName", topic.get("name", "Unknown")),
                        trigger_phrases=trigger_phrases,
                        description=topic.get("description", ""),
                        content=json.dumps(topic)
                    )
                    results["topic_ids"].append(topic_id)
                    logger.info(f"Created topic: {topic_id}")
                except Exception as e:
                    results["errors"].append(f"Topic {topic.get('name')}: {str(e)}")
                    logger.error(f"Failed to create topic: {e}")
            
            # Note: Power Automate flows require a separate API
            if flows:
                results["flow_note"] = "Flow creation requires Power Automate API (not yet implemented)"
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"Deployment failed: {e}")
        
        return results
    
    # =========================================================================
    # SYSTEM TOPIC CREATION (REQUIRED FOR AGENT TO WORK IN CS UI)
    # =========================================================================

    def create_system_topics(self, bot_id: str, bot_schema_name: str = None) -> List[str]:
        """
        Create all required system topics for an agent.
        
        Copilot Studio agents REQUIRE these system topics to function properly.
        Without them, opening the agent in the CS UI fails with
        "We ran into a problem creating your agent".
        
        Args:
            bot_id: The bot ID
            bot_schema_name: Bot schema name (will be retrieved if not provided)
            
        Returns:
            List of created component IDs
        """
        if not bot_schema_name:
            bot = self.get_agent(bot_id)
            bot_schema_name = bot.get('schemaname', '')

        system_topics = self._get_system_topic_definitions(bot_schema_name)
        created_ids = []

        for topic_def in system_topics:
            try:
                component_data = {
                    "name": topic_def["name"],
                    "schemaname": topic_def["schemaname"],
                    "componenttype": 9,  # topic_v2
                    "data": topic_def["data"],
                    "parentbotid@odata.bind": f"/bots({bot_id})",
                    "statecode": 0,
                    "statuscode": 1
                }

                response = requests.post(
                    f"{self.api_base_url}/botcomponents",
                    headers=self.headers,
                    json=component_data
                )

                if response.status_code in [200, 201, 204]:
                    comp_id = None
                    if response.text:
                        result = response.json()
                        comp_id = result.get("botcomponentid")
                    else:
                        entity_id = response.headers.get("OData-EntityId", "")
                        import re
                        match = re.search(r'botcomponents\(([^)]+)\)', entity_id)
                        comp_id = match.group(1) if match else None

                    if comp_id:
                        self._associate_component_to_bot(bot_id, comp_id)
                        created_ids.append(comp_id)
                        logger.info(f"Created system topic: {topic_def['name']}")
                else:
                    logger.warning(f"Failed to create {topic_def['name']}: {response.text[:200]}")
            except Exception as e:
                logger.warning(f"Error creating {topic_def['name']}: {e}")

        return created_ids

    def create_instructions_component(self, bot_id: str, name: str, instructions: str,
                                       description: str = "", bot_schema_name: str = None) -> str:
        """
        Create a type 10 (bot_translations_v2) instructions component.
        
        This stores the instructions in a JSON 'content' field and is the
        component type that Copilot Studio reads for the Overview page display.
        
        Args:
            bot_id: Parent bot ID
            name: Component display name
            instructions: The agent instructions text
            description: Agent description
            bot_schema_name: Bot schema name
            
        Returns:
            str: Component ID
        """
        if not bot_schema_name:
            bot = self.get_agent(bot_id)
            bot_schema_name = bot.get('schemaname', '')

        schema_name = f"rapp_gpt_{bot_schema_name.replace('rapp_', '')}_Instructions_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        content = json.dumps({
            "kind": "Gpt",
            "gptParameters": {
                "content": instructions,
                "name": f"{name} - Instructions",
                "description": description
            }
        })

        component_data = {
            "name": f"{name} - Instructions",
            "schemaname": schema_name[:100],
            "componenttype": 10,  # bot_translations_v2
            "content": content,
            "parentbotid@odata.bind": f"/bots({bot_id})",
            "statecode": 0,
            "statuscode": 1
        }

        response = requests.post(
            f"{self.api_base_url}/botcomponents",
            headers=self.headers,
            json=component_data
        )

        if response.status_code in [200, 201, 204]:
            comp_id = None
            if response.text:
                comp_id = response.json().get("botcomponentid")
            else:
                entity_id = response.headers.get("OData-EntityId", "")
                import re
                match = re.search(r'botcomponents\(([^)]+)\)', entity_id)
                comp_id = match.group(1) if match else None

            if comp_id:
                self._associate_component_to_bot(bot_id, comp_id)
                return comp_id
            raise CopilotStudioAPIError("Instructions component created but could not extract ID")
        else:
            raise CopilotStudioAPIError(
                f"Failed to create instructions component: {response.text}",
                status_code=response.status_code
            )

    def _get_system_topic_definitions(self, bot_schema: str) -> List[Dict]:
        """Return the minimum set of system topic definitions required by Copilot Studio."""
        return [
            {
                "name": "Conversation Start",
                "schemaname": f"{bot_schema}.topic.ConversationStart",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnConversationStart\n"
                    "  id: main\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_welcome\n"
                    "      activity:\n"
                    "        text:\n"
                    "          - Hello, I'm {System.Bot.Name}. How can I help?\n"
                    "        speak:\n"
                    "          - Hello, I'm {System.Bot.Name}. How can I help you today?\n"
                )
            },
            {
                "name": "Greeting",
                "schemaname": f"{bot_schema}.topic.Greeting",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Greeting\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Good afternoon\n"
                    "      - Good morning\n"
                    "      - Hello\n"
                    "      - Hey\n"
                    "      - Hi\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_greet\n"
                    "      activity:\n"
                    "        text:\n"
                    "          - Hello, how can I help you today?\n"
                    "        speak:\n"
                    "          - Hello, how can I help?\n"
                    "    - kind: CancelAllDialogs\n"
                    "      id: cancelAllDialogs_01\n"
                )
            },
            {
                "name": "Goodbye",
                "schemaname": f"{bot_schema}.topic.Goodbye",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Goodbye\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Bye\n"
                    "      - Goodbye\n"
                    "      - See you later\n"
                    "      - Take care\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_bye\n"
                    "      activity:\n"
                    "        text:\n"
                    "          - Goodbye! Have a great day.\n"
                    "    - kind: CancelAllDialogs\n"
                    "      id: cancelAllDialogs_02\n"
                )
            },
            {
                "name": "Escalate",
                "schemaname": f"{bot_schema}.topic.Escalate",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "startBehavior: CancelOtherTopics\n"
                    "beginDialog:\n"
                    "  kind: OnEscalate\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Escalate\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Talk to a person\n"
                    "      - Talk to representative\n"
                    "      - Customer service\n"
                    "      - I need help from a person\n"
                    "      - Chat with a human\n"
                    "      - Connect me to a representative\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_escalate\n"
                    "      conversationOutcome: Escalated\n"
                    "      activity: |-\n"
                    "        Escalating to a representative is not currently configured.\n"
                )
            },
            {
                "name": "Fallback",
                "schemaname": f"{bot_schema}.topic.Fallback",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnUnknownIntent\n"
                    "  id: main\n"
                    "  actions:\n"
                    "    - kind: ConditionGroup\n"
                    "      id: conditionGroup_fallback\n"
                    "      conditions:\n"
                    "        - id: conditionItem_retry\n"
                    "          condition: =System.FallbackCount < 3\n"
                    "          actions:\n"
                    "            - kind: SendActivity\n"
                    "              id: sendMessage_retry\n"
                    "              activity: I'm sorry, I'm not sure how to help with that. Can you try rephrasing?\n"
                    "      elseActions:\n"
                    "        - kind: BeginDialog\n"
                    "          id: escalate_fallback\n"
                    "          dialog: " + bot_schema + ".topic.Escalate\n"
                )
            },
            {
                "name": "On Error",
                "schemaname": f"{bot_schema}.topic.OnError",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnError\n"
                    "  id: main\n"
                    "  actions:\n"
                    "    - kind: SetVariable\n"
                    "      id: setVariable_timestamp\n"
                    "      variable: init:Topic.CurrentTime\n"
                    "      value: =Text(Now(), DateTimeFormat.UTC)\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_error\n"
                    "      activity:\n"
                    "        text:\n"
                    "          - |-\n"
                    "            An error has occurred.\n"
                    "            Error code: {System.Error.Code}\n"
                    "            Conversation Id: {System.Conversation.Id}\n"
                    "            Time (UTC): {Topic.CurrentTime}.\n"
                    "        speak:\n"
                    "          - An error has occurred, please try again.\n"
                    "    - kind: CancelAllDialogs\n"
                    "      id: cancelAll_error\n"
                )
            },
            {
                "name": "End of Conversation",
                "schemaname": f"{bot_schema}.topic.EndofConversation",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: End of Conversation\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - That's all\n"
                    "      - I'm done\n"
                    "      - No more questions\n"
                    "      - That's it\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_end\n"
                    "      activity: Thank you! If you need anything else, just ask.\n"
                    "    - kind: CancelAllDialogs\n"
                    "      id: cancelAll_end\n"
                )
            },
            {
                "name": "Thank you",
                "schemaname": f"{bot_schema}.topic.ThankYou",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Thank you\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Thank you\n"
                    "      - Thanks\n"
                    "      - Appreciate it\n"
                    "      - Thank you so much\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_thanks\n"
                    "      activity: You're welcome! Is there anything else?\n"
                )
            },
            {
                "name": "Start Over",
                "schemaname": f"{bot_schema}.topic.StartOver",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Start Over\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Start over\n"
                    "      - Restart\n"
                    "      - Begin again\n"
                    "      - New topic\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_restart\n"
                    "      activity: Sure, let's start over. How can I help you?\n"
                    "    - kind: CancelAllDialogs\n"
                    "      id: cancelAll_restart\n"
                )
            },
            {
                "name": "Reset Conversation",
                "schemaname": f"{bot_schema}.topic.ResetConversation",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Reset Conversation\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Reset\n"
                    "      - Clear conversation\n"
                    "  actions:\n"
                    "    - kind: CancelAllDialogs\n"
                    "      id: cancelAll_reset\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_reset\n"
                    "      activity: Conversation has been reset. How can I help?\n"
                )
            },
            {
                "name": "Multiple Topics Matched",
                "schemaname": f"{bot_schema}.topic.MultipleTopicsMatched",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnChooseTopicIntent\n"
                    "  id: main\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_multi\n"
                    "      activity: I found a few topics that might help. Which one would you like?\n"
                )
            },
            {
                "name": "Sign in",
                "schemaname": f"{bot_schema}.topic.Signin",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Sign in\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Sign in\n"
                    "      - Log in\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_signin\n"
                    "      activity: Sign in is not configured for this agent.\n"
                )
            },
            {
                "name": "Lesson 1 - A simple topic",
                "schemaname": f"{bot_schema}.topic.Lesson1",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Lesson 1\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Lesson 1\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_l1\n"
                    "      activity: This is a simple topic.\n"
                )
            },
            {
                "name": "Lesson 2 - A simple topic with a condition and variable",
                "schemaname": f"{bot_schema}.topic.Lesson2",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Lesson 2\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Lesson 2\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_l2\n"
                    "      activity: This is a topic with a condition.\n"
                )
            },
            {
                "name": "Lesson 3 - A topic with a condition, variables and a pre-built entity",
                "schemaname": f"{bot_schema}.topic.Lesson3",
                "data": (
                    "kind: AdaptiveDialog\n"
                    "beginDialog:\n"
                    "  kind: OnRecognizedIntent\n"
                    "  id: main\n"
                    "  intent:\n"
                    "    displayName: Lesson 3\n"
                    "    includeInOnSelectIntent: false\n"
                    "    triggerQueries:\n"
                    "      - Lesson 3\n"
                    "  actions:\n"
                    "    - kind: SendActivity\n"
                    "      id: sendMessage_l3\n"
                    "      activity: This is a topic with conditions and entities.\n"
                )
            }
        ]

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _generate_schema_name(self, name: str) -> str:
        """Generate a valid schema name from a display name."""
        # Schema names must be alphanumeric with underscores
        import re
        schema = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        schema = re.sub(r'_+', '_', schema)
        schema = schema.strip('_')
        
        # Add prefix to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"rapp_{schema}_{timestamp}"[:100]
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return re.sub(r'[^a-z0-9_]', '_', s2.lower())


# =============================================================================
# CONFIGURATION HELPER
# =============================================================================

def get_deployment_config() -> Dict[str, str]:
    """
    Get deployment configuration from environment or prompt user.
    
    Returns:
        Dict with environment_url, tenant_id, client_id
    """
    config = {
        "environment_url": os.environ.get("DATAVERSE_ENVIRONMENT_URL"),
        "tenant_id": os.environ.get("AZURE_TENANT_ID"),
        "client_id": os.environ.get("COPILOT_STUDIO_CLIENT_ID"),
        "client_secret": os.environ.get("COPILOT_STUDIO_CLIENT_SECRET")
    }
    
    missing = [k for k, v in config.items() if not v and k != "client_secret"]
    
    if missing:
        logger.warning(f"Missing configuration: {', '.join(missing)}")
        logger.info("Set environment variables or provide values when initializing CopilotStudioClient")
    
    return config


def create_app_registration_instructions() -> str:
    """Generate instructions for creating the required Azure AD app registration."""
    return """
# Azure AD App Registration for Copilot Studio Deployment

To deploy agents programmatically, you need an Azure AD app registration with Dataverse permissions.

## Steps:

1. **Go to Azure Portal** → Azure Active Directory → App registrations → New registration

2. **Register the app:**
   - Name: "RAPP Copilot Studio Deployer"
   - Supported account types: Single tenant (or multi-tenant if needed)
   - Redirect URI: Web → https://localhost (for interactive auth)

3. **Configure API Permissions:**
   - Add permission → APIs my organization uses → Dataverse/Dynamics CRM
   - Select: user_impersonation (Delegated) or Application permissions as needed
   - Grant admin consent

4. **Create a client secret** (for service principal auth):
   - Certificates & secrets → New client secret
   - Copy the secret value (shown only once)

5. **Note down:**
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret (if using service principal)

6. **Set environment variables:**
   ```
   DATAVERSE_ENVIRONMENT_URL=https://yourorg.crm.dynamics.com
   AZURE_TENANT_ID=your-tenant-id
   COPILOT_STUDIO_CLIENT_ID=your-client-id
   COPILOT_STUDIO_CLIENT_SECRET=your-secret  # Optional for interactive auth
   ```

7. **Grant Dataverse permissions:**
   - In Power Platform admin center, add the app as an application user
   - Assign appropriate security role (e.g., System Customizer)

## Usage:

```python
from utils.copilot_studio_api import CopilotStudioClient

client = CopilotStudioClient()
client.authenticate()

# Create agent
bot_id = client.create_agent(
    name="My Agent",
    description="Created via RAPP Transpiler"
)
```
"""
