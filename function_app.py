import azure.functions as func
import logging
import json
import os
import importlib
import importlib.util
import inspect
import sys
import re
import subprocess
from agents.basic_agent import BasicAgent
import uuid
from openai import AzureOpenAI, APIError as OpenAIAPIError, RateLimitError, AuthenticationError, APITimeoutError, BadRequestError
from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    AzureCliCredential,
    get_bearer_token_provider
)
from datetime import datetime
import time
import threading
from utils.azure_file_storage import safe_json_loads
from utils.storage_factory import get_storage_manager
from utils.result import Result, Success, Failure, AgentLoadError, APIError, partition_results
from utils.agent_registry import build_registry, format_registry_summary


# =============================================================================
# PERFORMANCE & RESILIENCE OPTIMIZATIONS
# =============================================================================
# These module-level singletons avoid expensive re-initialization on each request,
# dramatically reducing cold start times and improving response latency.
# =============================================================================

# Singleton OpenAI client - created once, reused across requests
_openai_client = None
_openai_client_lock = threading.Lock()
_openai_client_created_at = None
OPENAI_CLIENT_TTL_SECONDS = 30 * 60  # 30 minutes to match storage TTL

# Cached agents - loaded once, refreshed periodically
_cached_agents = None
_cached_agents_lock = threading.Lock()
_cached_agents_created_at = None
AGENTS_CACHE_TTL_SECONDS = 5 * 60  # 5 minutes - agents change less frequently

# Request timeout for OpenAI API calls (in seconds)
OPENAI_REQUEST_TIMEOUT = 45  # Allows time for complex agent chains while staying under 60s


def _get_openai_client():
    """
    Get or create a singleton OpenAI client with TTL refresh.
    
    This dramatically improves performance by:
    1. Avoiding credential acquisition on every request
    2. Reusing HTTP connections
    3. Automatic refresh before token expiration
    """
    global _openai_client, _openai_client_created_at
    
    with _openai_client_lock:
        # Check if we need to create or refresh the client
        needs_refresh = (
            _openai_client is None or
            _openai_client_created_at is None or
            (time.time() - _openai_client_created_at) >= OPENAI_CLIENT_TTL_SECONDS
        )
        
        if needs_refresh:
            logging.info("Creating/refreshing OpenAI client singleton")
            api_key = os.environ.get('AZURE_OPENAI_API_KEY')
            
            if api_key:
                # API key authentication (simplest)
                logging.info("Using API key authentication for Azure OpenAI")
                _openai_client = AzureOpenAI(
                    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
                    api_key=api_key,
                    api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2025-01-01-preview'),
                    timeout=OPENAI_REQUEST_TIMEOUT,
                    max_retries=2
                )
            else:
                # Entra ID authentication
                if os.environ.get('WEBSITE_INSTANCE_ID'):
                    credential = ManagedIdentityCredential()
                    logging.info("Using ManagedIdentityCredential for Azure deployment")
                else:
                    credential = ChainedTokenCredential(
                        ManagedIdentityCredential(),
                        AzureCliCredential()
                    )
                    logging.info("Using ChainedTokenCredential for local development")
                
                token_provider = get_bearer_token_provider(
                    credential,
                    "https://cognitiveservices.azure.com/.default"
                )
                
                _openai_client = AzureOpenAI(
                    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
                    azure_ad_token_provider=token_provider,
                    api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2025-01-01-preview'),
                    timeout=OPENAI_REQUEST_TIMEOUT,
                    max_retries=2
                )
            
            _openai_client_created_at = time.time()
        
        return _openai_client


def _get_cached_agents(user_guid=None, force_refresh=False):
    """
    Get agents with caching to avoid reloading on every request.
    
    This significantly reduces cold start and request latency by:
    1. Loading agents once and caching them
    2. Only refreshing when TTL expires or forced
    3. Using thread-safe access
    """
    global _cached_agents, _cached_agents_created_at
    
    with _cached_agents_lock:
        needs_refresh = (
            force_refresh or
            _cached_agents is None or
            _cached_agents_created_at is None or
            (time.time() - _cached_agents_created_at) >= AGENTS_CACHE_TTL_SECONDS
        )
        
        if needs_refresh:
            logging.info("Loading/refreshing agents cache")
            _cached_agents = load_agents_from_folder(user_guid)
            _cached_agents_created_at = time.time()
            # Build and persist the agent registry on cache refresh
            try:
                registry = build_registry(_cached_agents)
                logging.info(format_registry_summary(registry))
            except Exception as e:
                logging.warning(f"Agent registry build failed (non-blocking): {e}")
        
        return _cached_agents.copy()  # Return a copy to prevent mutation


def _reset_openai_client():
    """
    Reset the OpenAI client singleton.
    
    Call this when authentication fails to force credential refresh on next request.
    """
    global _openai_client, _openai_client_created_at
    with _openai_client_lock:
        _openai_client = None
        _openai_client_created_at = None
        logging.info("OpenAI client cache reset - will refresh on next request")


def _reset_agents_cache():
    """
    Reset the agents cache.
    
    Call this when agents need to be reloaded (e.g., after deployment updates).
    """
    global _cached_agents, _cached_agents_created_at
    with _cached_agents_lock:
        _cached_agents = None
        _cached_agents_created_at = None
        logging.info("Agents cache reset - will reload on next request")


# =============================================================================
# AUTO-DEPENDENCY INSTALLATION
# =============================================================================
# Global feature: When an agent fails to load due to a missing package,
# automatically attempt to install it and retry loading.
# =============================================================================

# Common package name mappings (import name -> pip package name)
PACKAGE_NAME_MAP = {
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'sklearn': 'scikit-learn',
    'yaml': 'pyyaml',
    'docx': 'python-docx',
    'pptx': 'python-pptx',
    'bs4': 'beautifulsoup4',
    'dateutil': 'python-dateutil',
}

# Track packages we've already tried to install this session (avoid infinite loops)
_install_attempted = set()


def _extract_missing_package(error_message: str) -> str:
    """Extract the missing package name from an ImportError message."""
    # Pattern: "No module named 'package_name'" or "No module named 'package.submodule'"
    match = re.search(r"No module named ['\"]([^'\"\.]+)", error_message)
    if match:
        import_name = match.group(1)
        # Map to pip package name if different
        return PACKAGE_NAME_MAP.get(import_name, import_name)

    # Pattern: "cannot import name 'X' from 'package'"
    match = re.search(r"cannot import name .+ from ['\"]([^'\"]+)", error_message)
    if match:
        import_name = match.group(1).split('.')[0]
        return PACKAGE_NAME_MAP.get(import_name, import_name)

    return None


def auto_install_package(package_name: str) -> bool:
    """
    Attempt to install a package using pip.
    Returns True if installation succeeded, False otherwise.

    This is a global utility that any agent can use to self-heal missing dependencies.
    """
    if not package_name:
        return False

    # Avoid infinite install loops
    if package_name in _install_attempted:
        logging.warning(f"Already attempted to install {package_name} this session, skipping")
        return False

    _install_attempted.add(package_name)

    logging.info(f"Auto-installing missing package: {package_name}")
    try:
        # Use subprocess to run pip install
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_name, '--quiet', '--disable-pip-version-check'],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode == 0:
            logging.info(f"Successfully auto-installed: {package_name}")
            # Clear the module cache to allow re-import
            if package_name in sys.modules:
                del sys.modules[package_name]
            return True
        else:
            logging.error(f"Failed to install {package_name}: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"Timeout installing {package_name}")
        return False
    except Exception as e:
        logging.error(f"Error installing {package_name}: {e}")
        return False


def _try_import_with_auto_install(import_func, max_retries: int = 2):
    """
    Wrapper that attempts an import, and if it fails with ImportError,
    tries to auto-install the missing package and retry.

    Args:
        import_func: A callable that performs the import (e.g., lambda: importlib.import_module('x'))
        max_retries: Maximum number of install+retry attempts

    Returns:
        The imported module if successful

    Raises:
        ImportError: If import fails after all retries
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return import_func()
        except ImportError as e:
            last_error = e
            error_msg = str(e)

            # Only try to install on first failure (not on retries of same package)
            if attempt < max_retries:
                package_name = _extract_missing_package(error_msg)
                if package_name and auto_install_package(package_name):
                    logging.info(f"Retrying import after installing {package_name}")
                    continue

            # If we get here, either no package found or install failed
            break

    raise last_error

# Default GUID to use when no specific user GUID is provided
# INTENTIONALLY INVALID UUID FORMAT - This is a security feature, not a bug!
#
# Design Decision: The GUID "c0p110t0" contains non-hex characters ('p', 'l')
# which spells "copilot" visually. This deliberate invalidity serves as a
# database insertion guardrail:
#
# 1. PREVENTS ACCIDENTAL PERSISTENCE: Any database with UUID column validation
#    will reject this value, preventing placeholder data from polluting
#    production user tables
#
# 2. CLEAR MARKER: When seen in logs/debugging, instantly recognizable as
#    "no real user context" rather than a legitimate user ID
#
# 3. FAILS LOUDLY: UUID parsing libraries will reject it, surfacing issues
#    early rather than silently storing garbage data
#
# 4. MEMORY ISOLATION: Local/shared memory contexts treat this specially,
#    ensuring default sessions don't create spurious user directories
#
# If you need a valid UUID for testing, generate one properly.
# This default exists solely for anonymous/unauthenticated sessions.
DEFAULT_USER_GUID = "c0p110t0-aaaa-bbbb-cccc-123456789abc"

def ensure_string_content(message):
    """
    Ensures message content is converted to a string regardless of input type.
    Handles all edge cases including None, undefined, or missing content.
    """
    # Handle None or non-dict messages
    if message is None:
        return {"role": "user", "content": ""}
        
    if not isinstance(message, dict):
        # Convert whatever we have to string
        return {"role": "user", "content": str(message) if message is not None else ""}
    
    # Create a copy to avoid modifying the original
    message = message.copy()
    
    # Ensure we have a role
    if 'role' not in message:
        message['role'] = 'user'
    
    # Handle content - check if it exists and is not None
    if 'content' in message:
        content = message['content']
        # Convert to string, handling None case
        message['content'] = str(content) if content is not None else ''
    else:
        # No content key at all
        message['content'] = ''
    
    return message

def ensure_string_function_args(function_call):
    """
    Ensures function call arguments are properly stringified.
    Handles None and edge cases.
    """
    if not function_call:
        return None
    
    # Check if function_call has arguments attribute
    if not hasattr(function_call, 'arguments'):
        return None
        
    if function_call.arguments is None:
        return None
        
    if isinstance(function_call.arguments, (dict, list)):
        return json.dumps(function_call.arguments)
    
    return str(function_call.arguments)

def build_cors_response(origin):
    """
    Builds CORS response headers.
    Safely handles None origin.
    """
    return {
        "Access-Control-Allow-Origin": str(origin) if origin else "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "86400",
    }

def _load_single_agent_local(file: str) -> Result[BasicAgent, AgentLoadError]:
    """Load a single agent from local agents/ folder. Returns Result.

    If loading fails due to a missing package (ImportError), automatically
    attempts to install the package and retry loading.
    """
    module_name = file[:-3]

    def do_import():
        return importlib.import_module(f'agents.{module_name}')

    try:
        # Use auto-install wrapper for import
        module = _try_import_with_auto_install(do_import)

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BasicAgent) and obj is not BasicAgent:
                agent_instance = obj()
                return Success(agent_instance)
        return Failure(AgentLoadError(file, 'local', 'no_class', 'No BasicAgent subclass found'))
    except SyntaxError as e:
        return Failure(AgentLoadError(file, 'local', 'syntax', str(e)))
    except ImportError as e:
        # ImportError after auto-install attempts failed
        return Failure(AgentLoadError(file, 'local', 'import', f'{str(e)} (auto-install attempted)'))
    except Exception as e:
        return Failure(AgentLoadError(file, 'local', 'instantiation', str(e)))


def _load_single_agent_azure(file_name: str, file_content: str, source: str) -> Result[BasicAgent, AgentLoadError]:
    """Load a single agent from Azure storage content. Returns Result.

    If loading fails due to a missing package (ImportError), automatically
    attempts to install the package and retry loading.
    """
    temp_dir = f"/tmp/{source}"
    temp_file = f"{temp_dir}/{file_name}"
    module_name = file_name[:-3]

    def do_load_module():
        """Inner function that handles module loading - can be retried after auto-install."""
        os.makedirs(temp_dir, exist_ok=True)
        with open(temp_file, 'w') as f:
            f.write(file_content)

        if temp_dir not in sys.path:
            sys.path.append(temp_dir)

        # For multi_agents, set up package structure
        if source == 'multi_agents':
            parent_dir = "/tmp"
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            import types
            if 'multi_agents' not in sys.modules:
                multi_agents_module = types.ModuleType('multi_agents')
                sys.modules['multi_agents'] = multi_agents_module
            spec = importlib.util.spec_from_file_location(f"multi_agents.{module_name}", temp_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"multi_agents.{module_name}"] = module
        else:
            spec = importlib.util.spec_from_file_location(module_name, temp_file)
            module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        return module

    try:
        # Use auto-install wrapper for module loading
        module = _try_import_with_auto_install(do_load_module)

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BasicAgent) and obj is not BasicAgent:
                agent_instance = obj()
                os.remove(temp_file)
                return Success(agent_instance)

        os.remove(temp_file)
        return Failure(AgentLoadError(file_name, source, 'no_class', 'No BasicAgent subclass found'))

    except SyntaxError as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return Failure(AgentLoadError(file_name, source, 'syntax', str(e)))
    except ImportError as e:
        # ImportError after auto-install attempts failed
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return Failure(AgentLoadError(file_name, source, 'import', f'{str(e)} (auto-install attempted)'))
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return Failure(AgentLoadError(file_name, source, 'instantiation', str(e)))


def load_agents_from_folder(user_guid=None):
    """
    Load agents from local folder and Azure storage.
    Uses Result type to track all failures and log a summary.
    """
    agents_directory = os.path.join(os.path.dirname(__file__), "agents")
    files_in_agents_directory = os.listdir(agents_directory)
    agent_files = [f for f in files_in_agents_directory if f.endswith(".py") and f not in ["__init__.py", "basic_agent.py"]]

    declared_agents = {}
    all_errors: list[AgentLoadError] = []

    # Load local agents
    for file in agent_files:
        result = _load_single_agent_local(file)
        if result.is_success:
            declared_agents[result.value.name] = result.value
        else:
            all_errors.append(result.error)

    storage_manager = get_storage_manager()

    # Load enabled agents list for this GUID
    enabled_agents = None
    if user_guid:
        try:
            agent_config_path = f"agent_config/{user_guid}"
            agent_config_content = storage_manager.read_file(agent_config_path, 'enabled_agents.json')
            if agent_config_content:
                enabled_agents = json.loads(agent_config_content)
        except Exception as e:
            logging.info(f"No agent config found for GUID {user_guid}, loading all agents: {str(e)}")

    # Load agents from Azure 'agents' folder
    try:
        azure_agent_files = storage_manager.list_files('agents')
        for file in azure_agent_files:
            if not file.name.endswith('_agent.py'):
                continue
            if enabled_agents is not None and file.name not in enabled_agents:
                continue

            file_content = storage_manager.read_file('agents', file.name)
            if file_content is None:
                all_errors.append(AgentLoadError(file.name, 'azure', 'file_read', 'Could not read file content'))
                continue

            result = _load_single_agent_azure(file.name, file_content, 'agents')
            if result.is_success:
                declared_agents[result.value.name] = result.value
            else:
                all_errors.append(result.error)

    except Exception as e:
        logging.error(f"Error listing agents from Azure File Share: {str(e)}")

    # Load multi-agents from Azure 'multi_agents' folder
    try:
        multi_agent_files = storage_manager.list_files('multi_agents')
        for file in multi_agent_files:
            if not file.name.endswith('_agent.py'):
                continue
            if enabled_agents is not None and file.name not in enabled_agents:
                continue

            file_content = storage_manager.read_file('multi_agents', file.name)
            if file_content is None:
                all_errors.append(AgentLoadError(file.name, 'multi_agents', 'file_read', 'Could not read file content'))
                continue

            result = _load_single_agent_azure(file.name, file_content, 'multi_agents')
            if result.is_success:
                declared_agents[result.value.name] = result.value
                logging.info(f"Loaded multi-agent: {result.value.name}")
            else:
                all_errors.append(result.error)

    except Exception as e:
        logging.error(f"Error listing multi-agents from Azure File Share: {str(e)}")

    # Log summary of all errors (not hidden in individual try/catch blocks)
    if all_errors:
        logging.warning(f"Agent loading completed with {len(all_errors)} error(s):")
        for error in all_errors:
            logging.error(f"  - {error}")

    logging.info(f"Successfully loaded {len(declared_agents)} agent(s): {list(declared_agents.keys())}")
    return declared_agents

class Assistant:
    def __init__(self, declared_agents):
        self.config = {
            'assistant_name': str(os.environ.get('ASSISTANT_NAME', 'BusinessInsightBot')),
            'characteristic_description': str(os.environ.get('CHARACTERISTIC_DESCRIPTION', 'helpful business assistant'))
        }

        # Use the singleton OpenAI client for better performance
        # This avoids re-authenticating and creating connections on every request
        self.client = _get_openai_client()

        self.known_agents = self.reload_agents(declared_agents)
        
        # Set the default user GUID instead of None
        self.user_guid = DEFAULT_USER_GUID
        
        # Image data from request (injected for vision-enabled agents)
        self.image_base64 = None
        
        self.shared_memory = None
        self.user_memory = None
        self.storage_manager = get_storage_manager()

        # Initialize with the default user GUID memory
        self._initialize_context_memory(DEFAULT_USER_GUID)

    def _check_first_message_for_guid(self, conversation_history):
        """Check if the first message contains only a GUID"""
        if not conversation_history or len(conversation_history) == 0:
            return None
            
        first_message = conversation_history[0]
        if first_message.get('role') == 'user':
            content = first_message.get('content')
            if content is None:
                return None
            content = str(content).strip()
            guid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            if guid_pattern.match(content):
                return content
        return None

    def _initialize_context_memory(self, user_guid=None):
        """Initialize context memory with separate shared and user-specific memories"""
        try:
            context_memory_agent = self.known_agents.get('ContextMemory')
            if not context_memory_agent:
                self.shared_memory = "No shared context memory available."
                self.user_memory = "No specific context memory available."
                return

            # Always get shared memories with full_recall=True to ensure complete context
            self.storage_manager.set_memory_context(None)  # Reset to shared context
            self.shared_memory = str(context_memory_agent.perform(full_recall=True))

            # If user_guid provided, get user-specific memories with full_recall=True
            # If no user_guid is provided, fall back to the default GUID
            if not user_guid:
                user_guid = DEFAULT_USER_GUID

            self.storage_manager.set_memory_context(user_guid)
            self.user_memory = str(context_memory_agent.perform(user_guid=user_guid, full_recall=True))

        except Exception as e:
            logging.warning(f"Error initializing context memory: {str(e)}")
            self.shared_memory = "Context memory initialization failed."
            self.user_memory = "Context memory initialization failed."

    def _extract_demo_state_from_history(self, conversation_history):
        """
        Extract active demo state from conversation history (stateless approach).
        Returns: (demo_name, current_step, demo_steps_list) or (None, 0, None)
        """
        if not conversation_history:
            return None, 0, None

        # Look backwards through conversation for the most recent demo-related system message
        for message in reversed(conversation_history):
            if message.get('role') == 'system':
                content = str(message.get('content', ''))

                # Check for demo completion or exit
                if 'DemoCompletion' in content or 'Demo finished' in content or 'DemoExit' in content:
                    return None, 0, None

                # Check for demo activation or continuation
                # Format: "Performed Bot_342_Morning_Greeting_Demo and got result: Demo activated - Step 1 of 5"
                # Format: "Performed Bot_342_Morning_Greeting_Demo and got result: Step 2 of 5 - ..."
                match = re.search(r'Performed (\S+) and got result:.*Step (\d+) of (\d+)', content)
                if match:
                    demo_name = match.group(1)
                    current_step = int(match.group(2))
                    total_steps = int(match.group(3))

                    # Load the demo data to get all steps
                    try:
                        demo_content = self.storage_manager.read_file('demos', f'{demo_name}.json')
                        if demo_content:
                            demo_data = json.loads(demo_content)
                            demo_steps = demo_data.get('conversation_flow', [])
                            logging.info(f"Extracted demo state from history: {demo_name}, step {current_step}/{len(demo_steps)}")
                            return demo_name, current_step, demo_steps
                    except Exception as e:
                        logging.error(f"Error loading demo {demo_name}: {str(e)}")
                        return None, 0, None

        return None, 0, None

    def extract_user_guid(self, text):
        """Try to extract a GUID from user input, but only if it's the entire message"""
        if text is None:
            return None

        text_str = str(text).strip()

        # Only match if the entire message is just a GUID
        guid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        match = guid_pattern.match(text_str)
        if match:
            return match.group(0)

        # Also allow labeled GUIDs for explicit behavior
        labeled_guid_pattern = re.compile(r'^guid[:=\s]+([0-9a-f-]{36})$', re.IGNORECASE)
        match = labeled_guid_pattern.match(text_str)
        if match:
            return match.group(1)

        return None

    def check_demo_trigger(self, user_message):
        """Check if user message matches any demo trigger phrases (stateless)"""
        try:
            # List all demo files
            demo_files = self.storage_manager.list_files('demos')

            user_message_lower = user_message.lower().strip()

            for file in demo_files:
                if not file.name.endswith('.json'):
                    continue

                try:
                    # Read demo file
                    demo_content = self.storage_manager.read_file('demos', file.name)
                    if not demo_content:
                        continue

                    demo_data = json.loads(demo_content)
                    trigger_phrases = demo_data.get('trigger_phrases', [])

                    # Check if user message matches any trigger phrase
                    for phrase in trigger_phrases:
                        if phrase.lower().strip() == user_message_lower:
                            # Found a match!
                            demo_name = file.name.replace('.json', '')
                            conversation_flow = demo_data.get('conversation_flow', [])

                            logging.info(f"Triggered demo: {demo_name} with {len(conversation_flow)} steps")

                            return {
                                'triggered': True,
                                'demo_name': demo_name,
                                'demo_data': demo_data,
                                'conversation_flow': conversation_flow
                            }

                except Exception as e:
                    logging.error(f"Error checking demo {file.name}: {str(e)}")
                    continue

            return {'triggered': False}

        except Exception as e:
            logging.error(f"Error in check_demo_trigger: {str(e)}")
            return {'triggered': False}

    def _uses_tools_api(self):
        """
        Determine if the current model uses the tools API or legacy functions API.

        Legacy Functions API (older models):
        - gpt-35-turbo, gpt-4, gpt-4-turbo

        Tools API (GPT-4o and newer):
        - gpt-4o, gpt-4o-mini, gpt-5.1-chat, o1, o1-mini, o3-mini, and all future models

        Strategy: Default to tools API (newer), only use legacy for known older models.
        """
        deployment_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-deployment').lower()

        # Models that use the LEGACY functions API (older models only)
        legacy_models = ['gpt-35', 'gpt-4-turbo', 'gpt-4-32k']

        # Check if it's a legacy model (but NOT gpt-4o which contains 'gpt-4')
        # gpt-4o and gpt-4o-mini should use tools API
        if 'gpt-4o' in deployment_name:
            return True  # gpt-4o, gpt-4o-mini use tools API

        # Check for legacy models
        for legacy in legacy_models:
            if legacy in deployment_name:
                return False  # Use legacy functions API

        # Check if it's plain "gpt-4" without "o" (legacy)
        if 'gpt-4' in deployment_name and 'gpt-4o' not in deployment_name:
            return False  # Plain gpt-4 uses legacy

        # Default to tools API for all other/newer models (gpt-5, o1, o3, etc.)
        return True

    def get_agent_metadata_tools(self):
        """Convert agent metadata to tools format for GPT-4o/GPT-5.1+ compatibility"""
        tools = []
        for agent in self.known_agents.values():
            if hasattr(agent, 'metadata'):
                tool = {
                    "type": "function",
                    "function": agent.metadata
                }
                tools.append(tool)
        return tools

    def get_agent_metadata_functions(self):
        """Get agent metadata in legacy functions format for GPT-3.5/GPT-4"""
        functions = []
        for agent in self.known_agents.values():
            if hasattr(agent, 'metadata'):
                functions.append(agent.metadata)
        return functions

    def reload_agents(self, agent_objects):
        known_agents = {}
        if isinstance(agent_objects, dict):
            for agent_name, agent in agent_objects.items():
                if hasattr(agent, 'name'):
                    known_agents[agent.name] = agent
                else:
                    known_agents[str(agent_name)] = agent
        elif isinstance(agent_objects, list):
            for agent in agent_objects:
                if hasattr(agent, 'name'):
                    known_agents[agent.name] = agent
        else:
            logging.warning(f"Unexpected agent_objects type: {type(agent_objects)}")
        return known_agents

    def prepare_messages(self, conversation_history):
        if not isinstance(conversation_history, list):
            conversation_history = []
            
        messages = []
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        # System message
        system_message = {
            "role": "system",
            "content": f"""
<identity>
You are a Microsoft Copilot assistant named {str(self.config.get('assistant_name', 'Assistant'))}, operating within Microsoft Teams.
</identity>

<shared_memory_output>
These are memories accessible by all users of the system:
{str(self.shared_memory)}
</shared_memory_output>

<specific_memory_output>
These are memories specific to the current conversation:
{str(self.user_memory)}
</specific_memory_output>

<context_instructions>
- <shared_memory_output> represents common knowledge shared across all conversations
- <specific_memory_output> represents specific context for the current conversation
- Apply specific context with higher precedence than shared context
- Synthesize information from both contexts for comprehensive responses
</context_instructions>

<agent_usage>
IMPORTANT: You must be honest and accurate about agent usage:
- NEVER pretend or imply you've executed an agent when you haven't actually called it
- NEVER say "using my agent" unless you are actually making a function call to that agent
- NEVER fabricate success messages about data operations that haven't occurred
- If you need to perform an action and don't have the necessary agent, say so directly
- When a user requests an action, either:
  1. Call the appropriate agent and report actual results, or
  2. Say "I don't have the capability to do that" and suggest an alternative
  3. If no details are provided besides the request to run an agent, infer the necessary input parameters by "reading between the lines" of the conversation context so far
- ALWAYS trust the tool schema provided - if a parameter is defined in the schema, USE IT
</agent_usage>

<project_tracker_note>
The ProjectTracker agent supports ALL of these update fields:
- step_notes: Object like {{"1": "note for step 1", "2": "note for step 2"}}
- step_checklists: Object like {{"1": {{"item1": true}}}}
- step_decisions: Object like {{"1": "PASS", "2": "COMPLETE"}}
These ARE valid parameters. Use them when users want to save notes or decisions.
</project_tracker_note>

<response_format>
CRITICAL: You must structure your response in TWO distinct parts separated by the delimiter |||VOICE|||

1. FIRST PART (before |||VOICE|||): Your full formatted response
   - Use **bold** for emphasis
   - Use `code blocks` for technical content
   - Apply --- for horizontal rules to separate sections
   - Utilize > for important quotes or callouts
   - Format code with ```language syntax highlighting
   - Create numbered lists with proper indentation
   - Add personality when appropriate
   - Apply # ## ### headings for clear structure

2. SECOND PART (after |||VOICE|||): A concise voice response
   - Maximum 1-2 sentences
   - Pure conversational English with NO formatting
   - Extract only the most critical information
   - Sound like a colleague speaking casually over a cubicle wall
   - Be natural and conversational, not robotic
   - Focus on the key takeaway or action item
   - Example: "I found those Q3 sales figures - revenue's up 12 percent from last quarter." or "Sure, I'll pull up that customer data for you right now."

EXAMPLE FORMAT:
Here's the detailed analysis you requested:

**Key Findings:**
- Revenue increased by 12%
- Customer satisfaction scores improved

|||VOICE|||
Revenue's up 12 percent and customers are happier - looking good for Q3.
</response_format>
"""
        }
        messages.append(ensure_string_content(system_message))
        
        # Process conversation history - skip first message if it's just a GUID
        guid_only_first_message = self._check_first_message_for_guid(conversation_history)
        start_idx = 1 if guid_only_first_message else 0
        
        for i in range(start_idx, len(conversation_history)):
            messages.append(ensure_string_content(conversation_history[i]))
            
        return messages
    
    def get_openai_api_call(self, messages) -> Result:
        """
        Make OpenAI API call with typed error handling.
        Returns Result[response, APIError] instead of raising exceptions.
        """
        deployment_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-deployment')
        use_tools_api = self._uses_tools_api()

        try:
            if use_tools_api:
                # GPT-4o, GPT-5.1+ use the tools API format
                tools = self.get_agent_metadata_tools()
                # Log ProjectTracker metadata for debugging
                for tool in tools:
                    if tool.get('function', {}).get('name') == 'ProjectTracker':
                        props = tool.get('function', {}).get('parameters', {}).get('properties', {})
                        logging.info(f"ProjectTracker properties: {list(props.keys())}")
                if tools:
                    response = self.client.chat.completions.create(
                        model=deployment_name,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto"
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=deployment_name,
                        messages=messages
                    )
            else:
                # GPT-3.5, GPT-4 use the legacy functions API format
                functions = self.get_agent_metadata_functions()
                if functions:
                    response = self.client.chat.completions.create(
                        model=deployment_name,
                        messages=messages,
                        functions=functions,
                        function_call="auto"
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=deployment_name,
                        messages=messages
                    )
            return Success(response)

        except RateLimitError as e:
            logging.warning(f"Rate limit hit: {e}")
            return Failure(APIError('rate_limit', str(e), 429, retryable=True))
        except AuthenticationError as e:
            logging.error(f"Auth error: {e}")
            return Failure(APIError('auth', str(e), 401, retryable=False))
        except APITimeoutError as e:
            logging.warning(f"Timeout: {e}")
            return Failure(APIError('timeout', str(e), 408, retryable=True))
        except BadRequestError as e:
            logging.error(f"Bad request: {e}")
            return Failure(APIError('invalid_request', str(e), 400, retryable=False))
        except OpenAIAPIError as e:
            status = getattr(e, 'status_code', 500)
            retryable = status >= 500
            logging.error(f"OpenAI API error ({status}): {e}")
            return Failure(APIError('server', str(e), status, retryable=retryable))
        except Exception as e:
            logging.error(f"Unexpected error in OpenAI API call: {e}")
            return Failure(APIError('unknown', str(e), None, retryable=False))
    
    def parse_response_with_voice(self, content):
        """Parse the response to extract formatted and voice parts"""
        if not content:
            return "", ""
        
        # Split by the delimiter
        parts = content.split("|||VOICE|||")
        
        if len(parts) >= 2:
            # We have both parts
            formatted_response = parts[0].strip()
            voice_response = parts[1].strip()
        else:
            # No voice delimiter found, generate a simple voice response
            formatted_response = content.strip()
            # Extract a simple summary for voice
            sentences = formatted_response.split('.')
            if sentences:
                voice_response = sentences[0].strip() + "."
                # Remove any formatting from voice response
                voice_response = re.sub(r'\*\*|`|#|>|---|[\U00010000-\U0010ffff]|[\u2600-\u26FF]|[\u2700-\u27BF]', '', voice_response)
                voice_response = re.sub(r'\s+', ' ', voice_response).strip()
            else:
                voice_response = "I've completed your request."
        
        return formatted_response, voice_response

    def get_response(self, prompt, conversation_history, max_retries=3, retry_delay=2):
        # Check if this is a first-time initialization with just a GUID
        # or if a GUID is in the conversation history or current prompt
        guid_from_history = self._check_first_message_for_guid(conversation_history)
        guid_from_prompt = self.extract_user_guid(prompt)

        target_guid = guid_from_history or guid_from_prompt

        # Set or update the memory context if we have a GUID that's different from current
        if target_guid and target_guid != self.user_guid:
            self.user_guid = target_guid
            self._initialize_context_memory(self.user_guid)
            logging.info(f"User GUID updated to: {self.user_guid}")
        elif not self.user_guid:
            # If for some reason we don't have a user_guid, set it to the default
            self.user_guid = DEFAULT_USER_GUID
            self._initialize_context_memory(self.user_guid)
            logging.info(f"Using default User GUID: {self.user_guid}")

        # Ensure prompt is string
        prompt = str(prompt) if prompt is not None else ""

        # Skip processing if the prompt is just a GUID and we've already set the context
        if guid_from_prompt and prompt.strip() == guid_from_prompt and self.user_guid == guid_from_prompt:
            formatted = "I've successfully loaded your conversation memory. How can I assist you today?"
            voice = "I've loaded your memory - what can I help you with?"
            return formatted, voice, ""

        # Extract demo state from conversation history (stateless)
        active_demo, current_step, demo_steps = self._extract_demo_state_from_history(conversation_history)

        # Check for "exit demo" command
        if prompt.lower().strip() in ['exit demo', 'stop demo', 'end demo', 'cancel demo']:
            if active_demo:
                formatted = f"How can I help you?"
                voice = "What can I help you with?"
                return formatted, voice, f"Performed DemoExit and got result: {active_demo} terminated by user"
            else:
                formatted = "How can I help you?"
                voice = "What can I help you with?"
                return formatted, voice, ""

        # Check for demo trigger FIRST (before any LLM processing)
        trigger_result = self.check_demo_trigger(prompt)
        if trigger_result.get('triggered'):
            demo_data = trigger_result.get('demo_data', {})
            demo_name = trigger_result.get('demo_name', '')
            conversation_flow = trigger_result.get('conversation_flow', [])

            # Demo just triggered - call ScriptedDemoAgent for step 1 canned response
            total_steps = len(conversation_flow)

            # Call ScriptedDemoAgent to get the canned response for step 1
            scripted_demo_agent = self.known_agents.get('ScriptedDemo')
            if scripted_demo_agent:
                try:
                    canned_response = scripted_demo_agent.perform(
                        action='respond',
                        demo_name=demo_name,
                        user_input=prompt,
                        user_guid=self.user_guid
                    )

                    # Return clean canned response without demo meta-information
                    formatted = canned_response

                    # Extract voice from the canned response
                    voice_sentences = canned_response.split('.')[:2]
                    voice = '.'.join(voice_sentences).strip()
                    voice = re.sub(r'\*\*|`|#|>|---|[\U00010000-\U0010ffff]|[\u2600-\u26FF]|[\u2700-\u27BF]', '', voice)
                    voice = re.sub(r'\s+', ' ', voice).strip()

                    return formatted, voice, f"Performed {demo_name} and got result: Demo activated - Step 1 of {total_steps}"

                except Exception as e:
                    logging.error(f"Error calling ScriptedDemoAgent on trigger: {str(e)}")
                    # Fall back to generic activation message
                    formatted = f"I apologize, but I encountered an error retrieving the demo response. Let me help you with that request."
                    voice = f"I encountered an error, but let me help you with that."
                    return formatted, voice, f"Performed {demo_name} and got result: Demo activated - Step 1 (Error)"
            else:
                # ScriptedDemoAgent not available - use generic message
                formatted = f"Let me help you with that!"
                voice = f"Let me help you with that."
                return formatted, voice, f"Performed {demo_name} and got result: Demo activated - Step 1 of {total_steps}"

        # Check if we're in an active demo (continuing a scripted conversation)
        if active_demo and demo_steps:
            # We're continuing an active demo - call ScriptedDemoAgent to get canned response
            next_step_num = current_step + 1
            total_steps = len(demo_steps)

            if next_step_num > total_steps:
                # Demo is complete
                formatted = f"How else can I help you today?"
                voice = "What else can I help you with?"
                return formatted, voice, f"Performed DemoCompletion and got result: {active_demo} finished successfully"

            logging.info(f"Continuing demo {active_demo}: step {next_step_num}/{total_steps}")

            # Call ScriptedDemoAgent to get the canned response
            scripted_demo_agent = self.known_agents.get('ScriptedDemo')
            if scripted_demo_agent:
                try:
                    # Call the agent with the user input
                    canned_response = scripted_demo_agent.perform(
                        action='respond',
                        demo_name=active_demo,
                        user_input=prompt,
                        user_guid=self.user_guid
                    )

                    # Return clean canned response without demo meta-information
                    formatted = canned_response

                    # Extract voice from the canned response (first sentence or two)
                    voice_sentences = canned_response.split('.')[:2]
                    voice = '.'.join(voice_sentences).strip()
                    # Remove markdown formatting from voice
                    voice = re.sub(r'\*\*|`|#|>|---|[\U00010000-\U0010ffff]|[\u2600-\u26FF]|[\u2700-\u27BF]', '', voice)
                    voice = re.sub(r'\s+', ' ', voice).strip()

                    agent_log = f"Performed {active_demo} and got result: Step {next_step_num} of {total_steps} - Returned canned response"
                    return formatted, voice, agent_log

                except Exception as e:
                    logging.error(f"Error calling ScriptedDemoAgent: {str(e)}")
                    # Fall back to generic response
                    formatted = f"I apologize, but I encountered an error. Let me help you with that."
                    voice = "Sorry, I hit an error. Let me help you with that."
                    return formatted, voice, f"Performed {active_demo} and got result: Error - {str(e)}"
            else:
                # ScriptedDemoAgent not loaded
                formatted = "I'm sorry, I'm unable to access the demo script right now. How else can I help you?"
                voice = "The demo script isn't available right now. How else can I help?"
                return formatted, voice, "Performed DemoError and got result: ScriptedDemo agent not found"
        
        messages = self.prepare_messages(conversation_history)

        # Check if prompt is already the last user message in conversation_history to avoid duplicates
        # This can happen when the caller (e.g., Copilot Studio/Teams) includes the current message in history
        last_user_msg = None
        for msg in reversed(conversation_history):
            if msg.get('role') == 'user':
                last_user_msg = str(msg.get('content', '')).strip()
                break

        # Only append prompt if it's not already the last user message
        if last_user_msg != prompt.strip():
            messages.append(ensure_string_content({"role": "user", "content": prompt}))

        agent_logs = []
        retry_count = 0
        needs_follow_up = False

        use_tools_api = self._uses_tools_api()

        while retry_count < max_retries:
            # Make API call - returns Result[response, APIError]
            api_result = self.get_openai_api_call(messages)

            # Handle API failure
            if api_result.is_failure:
                error = api_result.error
                retry_count += 1
                if error.retryable and retry_count < max_retries:
                    logging.warning(f"Retryable API error ({retry_count}/{max_retries}): {error}")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Non-retryable error or max retries reached
                    logging.error(f"API call failed: {error}")
                    error_msg = f"I encountered an error: {error.error_type}"
                    if error.error_type == 'rate_limit':
                        error_msg = "I'm experiencing high demand right now. Please try again in a moment."
                    elif error.error_type == 'auth':
                        error_msg = "There's an authentication issue. Please contact support."
                    return error_msg, "Something went wrong - try again.", ""

            # Success - extract response
            response = api_result.value
            assistant_msg = response.choices[0].message
            msg_contents = assistant_msg.content or ""  # Ensure content is never None

            # Check for function/tool calls based on API format
            has_function_call = False
            agent_name = None
            json_data = "{}"
            tool_call_id = None

            if use_tools_api:
                # GPT-4o, GPT-5.1+ format: tool_calls
                if assistant_msg.tool_calls:
                    has_function_call = True
                    tool_call = assistant_msg.tool_calls[0]
                    agent_name = str(tool_call.function.name)
                    json_data = tool_call.function.arguments or "{}"
                    tool_call_id = tool_call.id
            else:
                # Legacy format: function_call
                if assistant_msg.function_call:
                    has_function_call = True
                    agent_name = str(assistant_msg.function_call.name)
                    json_data = assistant_msg.function_call.arguments or "{}"

            # If no function call, return the response
            if not has_function_call:
                formatted_response, voice_response = self.parse_response_with_voice(msg_contents)
                return formatted_response, voice_response, "\n".join(map(str, agent_logs))

            # Get the agent
            agent = self.known_agents.get(agent_name)
            if not agent:
                return f"Agent '{agent_name}' does not exist", "I couldn't find that agent.", ""

            logging.info(f"JSON data before parsing: {json_data}")

            try:
                agent_parameters = safe_json_loads(json_data)

                # Sanitize parameters - ensure none are undefined or None
                sanitized_parameters = {}
                for key, value in agent_parameters.items():
                    if value is None:
                        sanitized_parameters[key] = ""  # Convert None to empty string
                    else:
                        sanitized_parameters[key] = value

                # Add user_guid to agent parameters if agent accepts it
                # Always use the current user_guid (which might be the default)
                if agent_name in ['ManageMemory', 'ContextMemory']:
                    sanitized_parameters['user_guid'] = self.user_guid

                # Inject image_base64 from request body if the agent expects it
                # OpenAI can't pass actual base64 data, so we substitute it here
                if self.image_base64 and 'image_base64' in agent_parameters:
                    sanitized_parameters['image_base64'] = self.image_base64

                # Always perform agent call - no caching
                result = agent.perform(**sanitized_parameters)

                # Ensure result is a string
                if result is None:
                    result = "Agent completed successfully"
                else:
                    result = str(result)

                agent_logs.append(f"Performed {agent_name} and got result: {result}")

            except Exception as e:
                return f"Error parsing parameters: {str(e)}", "I hit an error processing that.", ""

            # Add the assistant message and result to conversation based on API format
            if use_tools_api:
                # GPT-4o, GPT-5.1+ format: tool_calls and tool role
                messages.append({
                    "role": "assistant",
                    "content": msg_contents if msg_contents else None,
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": agent_name,
                                "arguments": json_data
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result
                })
            else:
                # Legacy format: function_call and function role
                messages.append({
                    "role": "assistant",
                    "content": msg_contents if msg_contents else None,
                    "function_call": {
                        "name": agent_name,
                        "arguments": json_data
                    }
                })
                messages.append({
                    "role": "function",
                    "name": agent_name,
                    "content": result
                })

            # EVALUATION: Check if we need a follow-up function call
            try:
                result_json = json.loads(result)
                # Look for error indicators or incomplete data flags
                needs_follow_up = False
                if isinstance(result_json, dict):
                    # Check for error indicators
                    if result_json.get('error') or result_json.get('status') == 'incomplete':
                        needs_follow_up = True
                    # Check for specific indicators that another action is needed
                    if result_json.get('requires_additional_action') == True:
                        needs_follow_up = True
            except:
                # If we can't parse the result as JSON, assume no follow-up needed
                needs_follow_up = False

            # If we don't need a follow-up, get the final response and return
            if not needs_follow_up:
                final_result = self.get_openai_api_call(messages)
                if final_result.is_failure:
                    logging.error(f"Final API call failed: {final_result.error}")
                    return "I completed the action but couldn't generate a summary.", "Action completed.", "\n".join(map(str, agent_logs))
                final_msg = final_result.value.choices[0].message
                final_content = final_msg.content or ""  # Ensure content is never None
                formatted_response, voice_response = self.parse_response_with_voice(final_content)
                return formatted_response, voice_response, "\n".join(map(str, agent_logs))

            # Continue loop for follow-up
            retry_count += 1

        return "Service temporarily unavailable. Please try again later.", "Service is down - try again later.", ""

app = func.FunctionApp()


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================
# This endpoint enables:
# 1. Azure warm-up triggers to keep the function "hot"
# 2. Power Automate health checks before main requests
# 3. Load balancer health probes
# 4. Monitoring and alerting systems
# =============================================================================

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for monitoring and warm-up.
    
    Call this endpoint:
    - Before making main API calls to ensure the function is warm
    - From Azure Monitor or custom health checks
    - From Power Automate as a pre-flight check
    
    Query Parameters:
        deep (optional): If "true", performs a deeper health check including
                        OpenAI client initialization and agent loading.
    
    Returns:
        200 OK with health status JSON
        500 with error details if unhealthy
    """
    start_time = time.time()
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    
    # Build response allowing CORS preflight
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "checks": {}
    }
    
    try:
        # Basic check - always performed
        health_status["checks"]["basic"] = {
            "status": "pass",
            "message": "Function app is responding"
        }
        
        # Deep health check if requested
        deep_check = req.params.get('deep', '').lower() == 'true'
        
        if deep_check:
            # Check OpenAI client can be initialized
            try:
                client = _get_openai_client()
                health_status["checks"]["openai_client"] = {
                    "status": "pass",
                    "message": "OpenAI client initialized successfully",
                    "client_age_seconds": round(time.time() - (_openai_client_created_at or time.time()), 2)
                }
            except Exception as e:
                health_status["checks"]["openai_client"] = {
                    "status": "fail",
                    "message": f"OpenAI client initialization failed: {str(e)}"
                }
                health_status["status"] = "degraded"
            
            # Check agent loading
            try:
                agents = _get_cached_agents()
                health_status["checks"]["agents"] = {
                    "status": "pass",
                    "message": f"Loaded {len(agents)} agents",
                    "cache_age_seconds": round(time.time() - (_cached_agents_created_at or time.time()), 2) if _cached_agents_created_at else 0
                }
            except Exception as e:
                health_status["checks"]["agents"] = {
                    "status": "fail",
                    "message": f"Agent loading failed: {str(e)}"
                }
                health_status["status"] = "degraded"
            
            # Check storage connectivity
            try:
                storage = get_storage_manager()
                if storage:
                    health_status["checks"]["storage"] = {
                        "status": "pass",
                        "message": "Storage manager initialized"
                    }
                else:
                    health_status["checks"]["storage"] = {
                        "status": "warn",
                        "message": "Storage manager not configured (running locally)"
                    }
            except Exception as e:
                health_status["checks"]["storage"] = {
                    "status": "fail", 
                    "message": f"Storage check failed: {str(e)}"
                }
                health_status["status"] = "degraded"
        
        # Calculate response time
        health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return func.HttpResponse(
            json.dumps(health_status, indent=2),
            status_code=200,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return func.HttpResponse(
            json.dumps(health_status, indent=2),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


# =============================================================================
# EVENT-DRIVEN TRIGGERS
# =============================================================================
# These endpoints enable agents to be triggered by external events:
# - Webhooks from external systems (Salesforce, ServiceNow, etc.)
# - Timer triggers for scheduled tasks
# - Manual triggers for testing
# 
# Compatible with Copilot Studio event triggers - payloads can be sent
# TO Copilot Studio agents or received FROM Copilot Studio flows.
# =============================================================================

# Initialize trigger system
_trigger_router = None
_trigger_registry = None

def _get_trigger_system():
    """Get or initialize the trigger system components"""
    global _trigger_router, _trigger_registry
    
    if _trigger_router is None:
        try:
            from utils.triggers import TriggerRouter, TriggerRegistry, get_trigger_registry, get_trigger_router
            
            # Initialize registry and load configs
            _trigger_registry = get_trigger_registry()
            triggers_dir = os.path.join(os.path.dirname(__file__), 'triggers')
            if os.path.exists(triggers_dir):
                _trigger_registry.load_from_directory(triggers_dir)
            
            # Initialize router with RAPP agent executor
            _trigger_router = get_trigger_router()
            _trigger_router.set_agent_executor(_execute_agent_for_trigger)
            
            logging.info(f"Trigger system initialized with {len(_trigger_registry.get_all())} triggers")
        except Exception as e:
            logging.error(f"Failed to initialize trigger system: {e}")
            return None, None
    
    return _trigger_router, _trigger_registry


def _execute_agent_for_trigger(agent_name: str, action: str, parameters: dict) -> str:
    """Execute a RAPP agent for a trigger - bridges trigger system to agent execution"""
    try:
        agents = _get_cached_agents()
        
        if agent_name not in agents:
            raise ValueError(f"Agent not found: {agent_name}")
        
        agent = agents[agent_name]
        result = agent.perform(**parameters)
        return str(result)
    except Exception as e:
        logging.error(f"Agent execution failed for trigger: {e}")
        raise


@app.route(route="trigger/webhook/{source}", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def webhook_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Webhook endpoint for external event triggers.
    
    This endpoint receives webhooks from external systems (Salesforce, ServiceNow, etc.)
    and routes them to the appropriate RAPP agents based on configured triggers.
    
    URL Pattern: /api/trigger/webhook/{source}
    
    Query Parameters:
        event (optional): Event type (e.g., "case.created"). Can also be in headers.
    
    Headers:
        X-Event-Type: Event type if not in query params
        X-Signature: Webhook signature for validation (if configured)
    
    Body:
        JSON payload from the webhook source
    
    Example:
        POST /api/trigger/webhook/salesforce?event=case.created
        {
            "case_id": "12345",
            "priority": "High",
            "subject": "HVAC system failure"
        }
    
    Copilot Studio Integration:
        This endpoint is compatible with Power Automate HTTP triggers.
        You can configure a Power Automate flow in Copilot Studio to call this
        endpoint, allowing Copilot Studio to trigger RAPP agents.
    """
    import asyncio
    
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)
    
    try:
        router, registry = _get_trigger_system()
        if not router:
            return func.HttpResponse(
                json.dumps({"error": "Trigger system not initialized"}),
                status_code=500,
                mimetype="application/json",
                headers=cors_headers
            )
        
        # Extract parameters
        source = req.route_params.get('source', 'unknown')
        event_type = (
            req.params.get('event') or 
            req.headers.get('X-Event-Type') or 
            req.headers.get('X-GitHub-Event') or  # GitHub webhook header
            'default'
        )
        
        # Parse body
        try:
            payload = req.get_json()
        except ValueError:
            payload = {"raw_body": req.get_body().decode('utf-8', errors='replace')}
        
        # Get client IP for validation
        client_ip = (
            req.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
            req.headers.get('X-Real-IP') or
            'unknown'
        )
        
        # Route the webhook
        event = await router.route_webhook(
            source=source,
            event_type=event_type,
            payload=payload,
            headers=dict(req.headers),
            client_ip=client_ip
        )
        
        # Return result
        status_code = 200 if event.status.value == 'success' else 500
        
        return func.HttpResponse(
            json.dumps({
                "event_id": event.id,
                "status": event.status.value,
                "trigger_name": event.trigger_name,
                "agent_response": event.agent_response,
                "error": event.error_message
            }),
            status_code=status_code,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"Webhook trigger error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


@app.route(route="trigger/manual/{trigger_name}", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def manual_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Manually trigger an agent action for testing.
    
    URL Pattern: /api/trigger/manual/{trigger_name}
    
    Body:
        Optional JSON payload to pass to the trigger
    
    Example:
        POST /api/trigger/manual/daily_ci_report
        {"force_full_report": true}
    """
    import asyncio
    
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)
    
    try:
        router, registry = _get_trigger_system()
        if not router:
            return func.HttpResponse(
                json.dumps({"error": "Trigger system not initialized"}),
                status_code=500,
                mimetype="application/json",
                headers=cors_headers
            )
        
        trigger_name = req.route_params.get('trigger_name')
        
        try:
            payload = req.get_json()
        except ValueError:
            payload = {}
        
        event = await router.route_manual(trigger_name, payload)
        
        status_code = 200 if event.status.value == 'success' else 500
        
        return func.HttpResponse(
            json.dumps({
                "event_id": event.id,
                "status": event.status.value,
                "trigger_name": event.trigger_name,
                "agent_response": event.agent_response,
                "error": event.error_message
            }),
            status_code=status_code,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"Manual trigger error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


@app.route(route="triggers", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def list_triggers(req: func.HttpRequest) -> func.HttpResponse:
    """
    List all configured triggers.
    
    Returns:
        JSON array of trigger configurations
    """
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)
    
    try:
        router, registry = _get_trigger_system()
        if not registry:
            return func.HttpResponse(
                json.dumps({"error": "Trigger system not initialized", "triggers": []}),
                status_code=200,
                mimetype="application/json",
                headers=cors_headers
            )
        
        triggers = registry.list_triggers()
        
        return func.HttpResponse(
            json.dumps({"triggers": triggers, "count": len(triggers)}),
            status_code=200,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"List triggers error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e), "triggers": []}),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


@app.route(route="triggers/stats", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def trigger_stats(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get trigger execution statistics.
    
    Returns:
        JSON with trigger stats (total events, success rate, by-trigger breakdown)
    """
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)
    
    try:
        router, registry = _get_trigger_system()
        if not router:
            return func.HttpResponse(
                json.dumps({"error": "Trigger system not initialized"}),
                status_code=200,
                mimetype="application/json",
                headers=cors_headers
            )
        
        stats = router.get_stats()
        
        return func.HttpResponse(
            json.dumps(stats),
            status_code=200,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"Trigger stats error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


# =============================================================================
# COPILOT STUDIO INBOUND TRIGGER
# =============================================================================
# This endpoint receives events FROM Copilot Studio flows.
# When an event trigger fires in Copilot Studio, it can call this endpoint
# to execute RAPP agents as part of the Copilot Studio workflow.
# =============================================================================

@app.route(route="trigger/copilot-studio", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def copilot_studio_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Receive trigger events from Copilot Studio.
    
    This endpoint allows Copilot Studio event triggers and Power Automate flows
    to invoke RAPP agents. The payload format matches Copilot Studio's event
    trigger output format.
    
    Expected Payload Format:
    {
        "trigger_name": "salesforce_case_created",  // Or use agent + action directly
        "agent": "carrier_case_triage_orchestrator",
        "action": "triage_case",
        "parameters": {
            "case_id": "12345",
            ...
        },
        "copilot_studio_context": {
            "conversation_id": "...",
            "activity_id": "...",
            "bot_id": "..."
        }
    }
    
    Returns:
        JSON response that can be used in Copilot Studio flow
    """
    import asyncio
    
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)
    
    try:
        payload = req.get_json()
        
        # Option 1: Use a configured trigger
        if 'trigger_name' in payload:
            router, registry = _get_trigger_system()
            if router:
                event = await router.route_manual(
                    payload['trigger_name'],
                    payload.get('parameters', {})
                )
                
                return func.HttpResponse(
                    json.dumps({
                        "status": event.status.value,
                        "response": event.agent_response,
                        "error": event.error_message,
                        "copilot_studio_format": {
                            "type": "event",
                            "name": "rapp.response",
                            "value": {
                                "success": event.status.value == 'success',
                                "message": event.agent_response or event.error_message
                            }
                        }
                    }),
                    status_code=200,
                    mimetype="application/json",
                    headers=cors_headers
                )
        
        # Option 2: Direct agent invocation
        if 'agent' in payload and 'action' in payload:
            agent_name = payload['agent']
            action = payload['action']
            parameters = payload.get('parameters', {})
            parameters['action'] = action
            
            response = _execute_agent_for_trigger(agent_name, action, parameters)
            
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "response": response,
                    "copilot_studio_format": {
                        "type": "event",
                        "name": "rapp.response",
                        "value": {
                            "success": True,
                            "message": response
                        }
                    }
                }),
                status_code=200,
                mimetype="application/json",
                headers=cors_headers
            )
        
        return func.HttpResponse(
            json.dumps({"error": "Missing trigger_name or agent/action in payload"}),
            status_code=400,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"Copilot Studio trigger error: {e}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": str(e),
                "copilot_studio_format": {
                    "type": "event",
                    "name": "rapp.error",
                    "value": {
                        "success": False,
                        "message": str(e)
                    }
                }
            }),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


# =============================================================================
# DEMO ACTION ENDPOINTS
# =============================================================================
# Lightweight endpoints for the Demo Action Panel buttons.
# These run locally with `func start` and work with the deployed Function App.
# Each endpoint handles one demo action directly — no agent routing overhead.
# =============================================================================

def _find_agent(name_hint: str):
    """Find an agent by name with case-insensitive/partial matching."""
    agents = _get_cached_agents()
    # Exact match
    if name_hint in agents:
        return agents[name_hint]
    # Case-insensitive
    lower = name_hint.lower()
    for k, v in agents.items():
        if k.lower() == lower:
            return v
    # Partial (underscore-separated tokens match)
    tokens = set(lower.replace("-", "_").split("_"))
    for k, v in agents.items():
        agent_tokens = set(k.lower().replace("-", "_").split("_"))
        if tokens.issubset(agent_tokens) or agent_tokens.issubset(tokens):
            return v
    return None


@app.route(route="demo/notification", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
def demo_notification(req: func.HttpRequest) -> func.HttpResponse:
    """Send a D365 in-app toast notification. Used by Demo Action Panel."""
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)

    try:
        payload = req.get_json()
        scenario = payload.get("scenario", "NewCase")
        recipient = payload.get("recipient_email", "admin@D365DemoTSCE30330346.onmicrosoft.com")
        case_title = payload.get("case_title", "ENTRAPMENT - Riverside Medical Centre Elevator 3")
        customer = payload.get("customer", "Riverside Medical Centre")

        # Use Dataverse API directly for speed
        try:
            from d365.utils.dataverse_auth import get_dataverse_session
            org_url = "https://orgecbce8ef.crm.dynamics.com"
            session = get_dataverse_session(org_url)

            # Lookup the recipient systemuser
            safe_email = recipient.replace("'", "''")
            users_resp = session.get(
                f"{org_url}/api/data/v9.2/systemusers",
                params={"$filter": f"internalemailaddress eq '{safe_email}'",
                        "$select": "systemuserid,fullname", "$top": 1}
            )
            users = users_resp.json().get("value", [])
            if not users:
                # Fallback — get first enabled user
                users_resp = session.get(
                    f"{org_url}/api/data/v9.2/systemusers",
                    params={"$filter": "isdisabled eq false",
                            "$select": "systemuserid,fullname", "$top": 1,
                            "$orderby": "createdon asc"}
                )
                users = users_resp.json().get("value", [])
            if not users:
                return func.HttpResponse(
                    json.dumps({"status": "error", "message": "No systemuser found for notification"}),
                    status_code=404, mimetype="application/json", headers=cors_headers
                )

            user_id = users[0]["systemuserid"]
            user_name = users[0].get("fullname", "Agent")

            # Map scenario to icon/toast
            icon_map = {"NewCase": 100000001, "SLAWarning": 100000003,
                        "SLABreach": 100000002, "Escalation": 100000004}
            icon = icon_map.get(scenario, 100000001)

            body_text = f"{customer}: {case_title}"
            notif_body = {
                "title": f"[{scenario}] {customer}",
                "body": body_text,
                "icontype": icon,
                "toasttype": 200000000,  # Timed toast
                "ownerid@odata.bind": f"/systemusers({user_id})"
            }

            resp = session.post(f"{org_url}/api/data/v9.2/appnotifications", notif_body)
            resp.raise_for_status()

            result = f"Toast sent to {user_name}: {body_text}"
        except ImportError:
            result = "Dataverse auth module not available. Run: az login"

        return func.HttpResponse(
            json.dumps({"status": "success", "message": result, "scenario": scenario}),
            status_code=200, mimetype="application/json", headers=cors_headers
        )
    except Exception as e:
        logging.error(f"Demo notification error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500, mimetype="application/json", headers=cors_headers
        )


@app.route(route="demo/create-case", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
def demo_create_case(req: func.HttpRequest) -> func.HttpResponse:
    """Create a D365 case. Used by Demo Action Panel."""
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)

    try:
        payload = req.get_json()
        title = payload.get("title", "Entrapment - Passenger stuck in Elevator 3")
        customer_name = payload.get("customer_name", "Riverside Medical Centre")
        priority = payload.get("priority", 1)
        origin_raw = payload.get("origin", "phone")
        description = payload.get("description", "Patient transport staff trapped in Elevator 3 between floors 2 and 3. Bed elevator essential for patient movement. Hospital security on scene.")

        # Map string origin names to Dataverse codes
        origin_map = {"phone": 1, "email": 2, "web": 3, "teams": 2483, "iot": 192350000}
        if isinstance(origin_raw, str) and not origin_raw.isdigit():
            origin_code = origin_map.get(origin_raw.lower(), 3)
        else:
            origin_code = int(origin_raw)
        priority = int(priority)

        # Use Dataverse API directly for speed
        try:
            from d365.utils.dataverse_auth import get_dataverse_session
            org_url = "https://orgecbce8ef.crm.dynamics.com"
            session = get_dataverse_session(org_url)

            # Lookup account — try exact match, then contains, then first available
            safe_name = customer_name.replace("'", "''")
            accounts = []
            for filt in [f"name eq '{safe_name}'", f"contains(name,'{safe_name}')"]:
                acct_resp = session.get(
                    f"{org_url}/api/data/v9.2/accounts",
                    params={"$filter": filt, "$select": "accountid,name,description", "$top": 1}
                )
                accounts = acct_resp.json().get("value", [])
                if accounts:
                    break
            if not accounts:
                acct_resp = session.get(
                    f"{org_url}/api/data/v9.2/accounts",
                    params={"$select": "accountid,name,description", "$top": 1}
                )
                accounts = acct_resp.json().get("value", [])

            # Derive tier from account description or payload
            # cr377_tierlevel: 192350000=Tier1, 192350001=Tier2, 192350002=Tier3, 192350003=Tier4
            tier_map = {1: 192350000, 2: 192350001, 3: 192350002, 4: 192350003}
            tier_value = None
            explicit_tier = payload.get("tier")
            if explicit_tier is not None:
                tier_value = tier_map.get(int(explicit_tier))
            elif accounts:
                acct_desc = (accounts[0].get("description") or "").lower()
                # Check explicit "Tier: N" first
                for t in [1, 2, 3, 4]:
                    if f"tier: {t}" in acct_desc or f"tier {t}" in acct_desc:
                        tier_value = tier_map[t]
                        break
                # Fallback: derive from contract type
                if tier_value is None:
                    if "premium" in acct_desc:
                        tier_value = tier_map[1]
                    elif "full maintenance" in acct_desc:
                        tier_value = tier_map[2]
                    elif "basic" in acct_desc:
                        tier_value = tier_map[3]

            case_body = {
                "title": title,
                "description": description or f"Demo case created via Action Panel at {datetime.utcnow().isoformat()}Z",
                "prioritycode": priority,
                "caseorigincode": origin_code,
            }
            if accounts:
                case_body["customerid_account@odata.bind"] = f"/accounts({accounts[0]['accountid']})"
            if tier_value is not None:
                case_body["cr377_tierlevel"] = tier_value

            resp = session.post(f"{org_url}/api/data/v9.2/incidents", case_body)
            resp.raise_for_status()

            # Get the created case ID from the response
            case_id = resp.headers.get("OData-EntityId", "").split("(")[-1].rstrip(")")

            # Fetch the ticket number
            if case_id:
                detail = session.get(f"{org_url}/api/data/v9.2/incidents({case_id})", params={"$select": "ticketnumber,title"})
                detail_data = detail.json()
                ticket = detail_data.get("ticketnumber", "")
            else:
                ticket = ""

            result = f"Case created: {ticket} — {title}"
            return func.HttpResponse(
                json.dumps({"status": "success", "message": result, "case_id": case_id, "case_number": ticket}),
                status_code=200, mimetype="application/json", headers=cors_headers
            )
        except ImportError:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Dataverse auth module not available. Run: az login"}),
                status_code=500, mimetype="application/json", headers=cors_headers
            )

    except Exception as e:
        logging.error(f"Demo create case error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500, mimetype="application/json", headers=cors_headers
        )


@app.route(route="demo/sla-breach", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
def demo_sla_breach(req: func.HttpRequest) -> func.HttpResponse:
    """Simulate SLA breach on a case. Used by Demo Action Panel."""
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)

    try:
        payload = req.get_json()
        breach_type = payload.get("breach_type", "violated")
        case_number = payload.get("case_number", "")
        case_id = payload.get("case_id", "")
        send_notification = payload.get("send_notification", True)

        try:
            from d365.utils.dataverse_auth import get_dataverse_session
            org_url = "https://orgecbce8ef.crm.dynamics.com"
            session = get_dataverse_session(org_url)

            # Find the case
            if case_id:
                filter_str = f"incidentid eq {case_id}"
            elif case_number:
                filter_str = f"ticketnumber eq '{case_number}'"
            else:
                # Get the most recent active case
                filter_str = "statecode eq 0"

            resp = session.get(
                f"{org_url}/api/data/v9.2/incidents",
                params={
                    "$filter": filter_str,
                    "$select": "incidentid,ticketnumber,title,_ownerid_value,prioritycode",
                    "$top": 1,
                    "$orderby": "createdon desc"
                }
            )
            cases = resp.json().get("value", [])
            if not cases:
                return func.HttpResponse(
                    json.dumps({"status": "error", "message": "No matching case found"}),
                    status_code=404, mimetype="application/json", headers=cors_headers
                )

            case = cases[0]
            cid = case["incidentid"]
            ticket = case.get("ticketnumber", "")

            # Update case to high priority with breach note
            note = "*** SLA BREACHED ***" if breach_type == "violated" else "SLA Warning - approaching deadline"
            session.patch(
                f"{org_url}/api/data/v9.2/incidents({cid})",
                {"prioritycode": 1, "description": f"{note}\n[Demo simulation at {datetime.utcnow().isoformat()}Z]"}
            )

            notif_msg = ""
            if send_notification:
                owner_id = case.get("_ownerid_value", "")
                if owner_id:
                    icon = 100000002 if breach_type == "violated" else 100000003
                    title = "SLA BREACHED" if breach_type == "violated" else "SLA Warning"
                    body_text = f"Case {ticket} ({case.get('title', '')}) {'has BREACHED SLA' if breach_type == 'violated' else 'is approaching SLA deadline'}"
                    session.post(f"{org_url}/api/data/v9.2/appnotifications", {
                        "title": title,
                        "body": body_text,
                        "icontype": icon,
                        "toasttype": 200000000,
                        "ownerid@odata.bind": f"/systemusers({owner_id})"
                    })
                    notif_msg = " + notification sent"

            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": f"SLA {breach_type} on {ticket}{notif_msg}",
                    "case_number": ticket, "case_id": cid, "breach_type": breach_type
                }),
                status_code=200, mimetype="application/json", headers=cors_headers
            )
        except ImportError:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Dataverse auth module not available. Run: az login"}),
                status_code=500, mimetype="application/json", headers=cors_headers
            )

    except Exception as e:
        logging.error(f"Demo SLA breach error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500, mimetype="application/json", headers=cors_headers
        )


@app.route(route="demo/ai-triage", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
def demo_ai_triage(req: func.HttpRequest) -> func.HttpResponse:
    """Run AI triage on a case via the triage orchestrator agent. Used by Demo Action Panel."""
    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)
    if req.method == 'OPTIONS':
        return func.HttpResponse(status_code=200, headers=cors_headers)

    try:
        payload = req.get_json()

        agent = _find_agent("carrier_case_triage_orchestrator")
        if not agent:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Triage agent not loaded"}),
                status_code=404, mimetype="application/json", headers=cors_headers
            )

        result = agent.perform(
            action=payload.get("action", "triage_case"),
            **{k: v for k, v in payload.items() if k != "action"}
        )
        return func.HttpResponse(
            json.dumps({"status": "success", "message": str(result)[:2000]}),
            status_code=200, mimetype="application/json", headers=cors_headers
        )
    except Exception as e:
        logging.error(f"Demo AI triage error: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500, mimetype="application/json", headers=cors_headers
        )


@app.route(route="businessinsightbot_function", auth_level=func.AuthLevel.FUNCTION)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    origin = req.headers.get('origin')
    cors_headers = build_cors_response(origin)

    if req.method == 'OPTIONS':
        return func.HttpResponse(
            status_code=200,
            headers=cors_headers
        )

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON in request body",
            status_code=400,
            headers=cors_headers
        )

    if not req_body:
        return func.HttpResponse(
            "Missing JSON payload in request body",
            status_code=400,
            headers=cors_headers
        )

    # Ensure user_input is string, handle None case
    user_input = req_body.get('user_input')
    if user_input is None:
        user_input = ""
    else:
        user_input = str(user_input)
    
    # Ensure conversation_history is list and contents are properly formatted
    conversation_history = req_body.get('conversation_history', [])
    if not isinstance(conversation_history, list):
        conversation_history = []
    
    # Extract user_guid if provided in the request
    user_guid = req_body.get('user_guid')

    # Extract image_base64 if provided (for vision-enabled agents like MachineWalkaround)
    image_base64 = req_body.get('image_base64')

    # Skip validation if input is just a GUID to load memory
    is_guid_only = re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', user_input.strip(), re.IGNORECASE)

    # Validate user input for non-GUID requests
    if not is_guid_only and not user_input.strip():
        return func.HttpResponse(
            json.dumps({
                "error": "Missing or empty user_input in JSON payload"
            }),
            status_code=400,
            mimetype="application/json",
            headers=cors_headers
        )

    try:
        # Use cached agents for better performance (avoids reloading on every request)
        agents = _get_cached_agents(user_guid)
        # Create a new Assistant instance for each request
        assistant = Assistant(agents)
        
        # Set user_guid if provided in the request or found in input
        if user_guid:
            assistant.user_guid = user_guid
            assistant._initialize_context_memory(user_guid)
        elif is_guid_only:
            assistant.user_guid = user_input.strip()
            assistant._initialize_context_memory(user_input.strip())
        # Otherwise, the default GUID will be used (already set in __init__)
            
        # Pass image_base64 to the assistant so vision agents can use it
        if image_base64:
            assistant.image_base64 = image_base64

        assistant_response, voice_response, agent_logs = assistant.get_response(
            user_input, conversation_history)

        # Include GUID and voice response in output
        response = {
            "assistant_response": str(assistant_response),
            "voice_response": str(voice_response),
            "agent_logs": str(agent_logs),
            "user_guid": assistant.user_guid  # Return the GUID in use (could be default or provided)
        }

        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json",
            headers=cors_headers
        )
    except Exception as e:
        error_str = str(e)

        # Check for authentication/authorization errors and reset credential caches
        # This handles cases where cached credentials have expired (e.g., overnight idle)
        auth_error_indicators = [
            'AuthenticationError', 'AuthorizationFailure', 'AuthenticationFailed',
            '401', '403', 'token', 'credential', 'Unauthorized', 'invalid_api_key'
        ]
        
        if any(auth_err in error_str for auth_err in auth_error_indicators):
            logging.warning(f"Auth error detected, resetting all caches: {error_str}")
            
            # Reset OpenAI client cache
            _reset_openai_client()
            
            # Reset storage manager
            try:
                from utils.storage_factory import reset_storage_manager
                reset_storage_manager()
                logging.info("All credential caches reset - next request will use fresh credentials")
            except Exception as reset_err:
                logging.error(f"Failed to reset storage manager: {reset_err}")
        
        # Check for timeout errors and provide helpful response
        if any(timeout_err in error_str for timeout_err in ['timeout', 'Timeout', 'timed out']):
            error_response = {
                "error": "Request timed out",
                "details": "The request took too long to process. Please try again with a simpler query.",
                "suggestion": "Try breaking your request into smaller parts."
            }
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=408,
                mimetype="application/json",
                headers=cors_headers
            )

        error_response = {
            "error": "Internal server error",
            "details": error_str
        }
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )