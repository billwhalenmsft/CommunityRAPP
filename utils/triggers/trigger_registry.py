"""
RAPP Trigger Registry
====================
Manages trigger configurations loaded from YAML/JSON files.
Supports hot-reloading of trigger configurations.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .trigger_models import (
    TriggerConfig,
    TriggerType,
    WebhookTrigger,
    TimerTrigger,
    QueueTrigger,
    DataverseTrigger,
    FilterCondition
)

logger = logging.getLogger(__name__)


class TriggerConfigHandler(FileSystemEventHandler):
    """File system event handler for trigger config hot-reloading"""
    
    def __init__(self, registry: 'TriggerRegistry'):
        self.registry = registry
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"Trigger config modified: {event.src_path}")
            self.registry.reload()
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"New trigger config: {event.src_path}")
            self.registry.reload()
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"Trigger config deleted: {event.src_path}")
            self.registry.reload()


class TriggerRegistry:
    """
    Registry for managing trigger configurations.
    
    Loads triggers from:
    1. triggers/ directory (YAML/JSON files)
    2. Environment variables
    3. Programmatic registration
    
    Example usage:
        registry = TriggerRegistry()
        registry.load_from_directory("triggers/")
        
        # Get a specific trigger
        trigger = registry.get("salesforce_case_created")
        
        # Get all webhook triggers
        webhooks = registry.get_by_type(TriggerType.WEBHOOK)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._triggers: Dict[str, TriggerConfig] = {}
        self._config_directory: Optional[Path] = None
        self._observer: Optional[Observer] = None
        self._last_reload: Optional[datetime] = None
        self._initialized = True
    
    def load_from_directory(self, directory: str, watch: bool = False) -> int:
        """
        Load all trigger configurations from a directory.
        
        Args:
            directory: Path to directory containing trigger config files
            watch: If True, watch for file changes and auto-reload
            
        Returns:
            Number of triggers loaded
        """
        self._config_directory = Path(directory)
        
        if not self._config_directory.exists():
            logger.warning(f"Trigger directory does not exist: {directory}")
            self._config_directory.mkdir(parents=True, exist_ok=True)
            return 0
        
        count = 0
        for file_path in self._config_directory.glob("**/*"):
            if file_path.suffix in (".yaml", ".yml", ".json"):
                try:
                    loaded = self._load_file(file_path)
                    count += loaded
                except Exception as e:
                    logger.error(f"Error loading trigger config {file_path}: {e}")
        
        self._last_reload = datetime.utcnow()
        logger.info(f"Loaded {count} triggers from {directory}")
        
        # Set up file watching if requested
        if watch and self._observer is None:
            self._start_watching()
        
        return count
    
    def _load_file(self, file_path: Path) -> int:
        """Load triggers from a single file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix == '.json':
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        
        if data is None:
            return 0
        
        # Handle both single trigger and list of triggers
        triggers = data if isinstance(data, list) else [data]
        
        count = 0
        for trigger_data in triggers:
            trigger = self._parse_trigger(trigger_data)
            if trigger:
                self._triggers[trigger.name] = trigger
                count += 1
        
        return count
    
    def _parse_trigger(self, data: Dict[str, Any]) -> Optional[TriggerConfig]:
        """Parse a trigger configuration from dict data"""
        try:
            trigger_type = TriggerType(data.get("trigger_type", "webhook"))
            
            # Parse filters
            filters = []
            for f in data.get("filters", []):
                filters.append(FilterCondition(
                    field=f["field"],
                    operator=f["operator"],
                    value=f.get("value")
                ))
            data["filters"] = filters
            
            # Create appropriate trigger type
            if trigger_type == TriggerType.WEBHOOK:
                return WebhookTrigger(
                    name=data["name"],
                    description=data.get("description", ""),
                    enabled=data.get("enabled", True),
                    target_agent=data.get("target_agent", ""),
                    target_action=data.get("target_action", ""),
                    parameters=data.get("parameters", {}),
                    message_template=data.get("message_template", ""),
                    body_mapping=data.get("body_mapping", {}),
                    filters=filters,
                    on_success=data.get("on_success", []),
                    on_failure=data.get("on_failure", []),
                    max_retries=data.get("max_retries", 3),
                    retry_delay_seconds=data.get("retry_delay_seconds", 60),
                    copilot_studio_enabled=data.get("copilot_studio_enabled", False),
                    copilot_studio_bot_id=data.get("copilot_studio_bot_id"),
                    copilot_studio_environment_url=data.get("copilot_studio_environment_url"),
                    secret_key=data.get("secret_key"),
                    allowed_ips=data.get("allowed_ips", []),
                    required_headers=data.get("required_headers", {}),
                    source=data.get("source", "custom"),
                    event_type=data.get("event_type", "")
                )
            
            elif trigger_type == TriggerType.TIMER:
                return TimerTrigger(
                    name=data["name"],
                    description=data.get("description", ""),
                    enabled=data.get("enabled", True),
                    target_agent=data.get("target_agent", ""),
                    target_action=data.get("target_action", ""),
                    parameters=data.get("parameters", {}),
                    message_template=data.get("message_template", ""),
                    filters=filters,
                    on_success=data.get("on_success", []),
                    on_failure=data.get("on_failure", []),
                    schedule=data.get("schedule", ""),
                    timezone=data.get("timezone", "UTC"),
                    run_on_startup=data.get("run_on_startup", False)
                )
            
            elif trigger_type == TriggerType.QUEUE:
                return QueueTrigger(
                    name=data["name"],
                    description=data.get("description", ""),
                    enabled=data.get("enabled", True),
                    target_agent=data.get("target_agent", ""),
                    target_action=data.get("target_action", ""),
                    parameters=data.get("parameters", {}),
                    message_template=data.get("message_template", ""),
                    filters=filters,
                    queue_name=data.get("queue_name", ""),
                    connection_string_setting=data.get("connection_string_setting", ""),
                    batch_size=data.get("batch_size", 1),
                    visibility_timeout_seconds=data.get("visibility_timeout_seconds", 300)
                )
            
            elif trigger_type == TriggerType.DATAVERSE:
                return DataverseTrigger(
                    name=data["name"],
                    description=data.get("description", ""),
                    enabled=data.get("enabled", True),
                    target_agent=data.get("target_agent", ""),
                    target_action=data.get("target_action", ""),
                    parameters=data.get("parameters", {}),
                    message_template=data.get("message_template", ""),
                    filters=filters,
                    copilot_studio_enabled=True,  # Always enabled for Dataverse
                    copilot_studio_bot_id=data.get("copilot_studio_bot_id"),
                    table_name=data.get("table_name", ""),
                    change_type=data.get("change_type", "create"),
                    filter_expression=data.get("filter_expression", ""),
                    select_columns=data.get("select_columns", [])
                )
            
            else:
                # Generic trigger
                return TriggerConfig.from_dict(data)
                
        except Exception as e:
            logger.error(f"Error parsing trigger: {e}")
            return None
    
    def _start_watching(self):
        """Start watching the config directory for changes"""
        if self._config_directory and self._config_directory.exists():
            self._observer = Observer()
            handler = TriggerConfigHandler(self)
            self._observer.schedule(handler, str(self._config_directory), recursive=True)
            self._observer.start()
            logger.info(f"Watching trigger directory for changes: {self._config_directory}")
    
    def stop_watching(self):
        """Stop watching for file changes"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
    
    def reload(self):
        """Reload all triggers from the config directory"""
        if self._config_directory:
            self._triggers.clear()
            self.load_from_directory(str(self._config_directory))
    
    def register(self, trigger: TriggerConfig):
        """Register a trigger programmatically"""
        self._triggers[trigger.name] = trigger
        logger.info(f"Registered trigger: {trigger.name}")
    
    def unregister(self, name: str) -> bool:
        """Unregister a trigger by name"""
        if name in self._triggers:
            del self._triggers[name]
            logger.info(f"Unregistered trigger: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[TriggerConfig]:
        """Get a trigger by name"""
        return self._triggers.get(name)
    
    def get_all(self) -> List[TriggerConfig]:
        """Get all registered triggers"""
        return list(self._triggers.values())
    
    def get_enabled(self) -> List[TriggerConfig]:
        """Get all enabled triggers"""
        return [t for t in self._triggers.values() if t.enabled]
    
    def get_by_type(self, trigger_type: TriggerType) -> List[TriggerConfig]:
        """Get all triggers of a specific type"""
        return [t for t in self._triggers.values() if t.trigger_type == trigger_type]
    
    def get_by_agent(self, agent_name: str) -> List[TriggerConfig]:
        """Get all triggers targeting a specific agent"""
        return [t for t in self._triggers.values() if t.target_agent == agent_name]
    
    def get_webhooks_for_source(self, source: str, event_type: str = None) -> List[WebhookTrigger]:
        """Get webhook triggers for a specific source (e.g., 'salesforce')"""
        triggers = []
        for t in self._triggers.values():
            if isinstance(t, WebhookTrigger) and t.source == source:
                if event_type is None or t.event_type == event_type:
                    triggers.append(t)
        return triggers
    
    def list_triggers(self) -> List[Dict[str, Any]]:
        """List all triggers with summary info"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "type": t.trigger_type.value,
                "enabled": t.enabled,
                "target_agent": t.target_agent,
                "target_action": t.target_action,
                "copilot_studio_enabled": t.copilot_studio_enabled
            }
            for t in self._triggers.values()
        ]
    
    def export_for_copilot_studio(self) -> List[Dict[str, Any]]:
        """
        Export triggers in Copilot Studio-compatible format.
        Used by the transpiler when deploying agents to Copilot Studio.
        """
        exports = []
        for trigger in self._triggers.values():
            if trigger.copilot_studio_enabled:
                if isinstance(trigger, DataverseTrigger):
                    exports.append(trigger.to_copilot_studio_trigger())
                else:
                    # For non-Dataverse triggers, create a Power Automate flow definition
                    exports.append({
                        "type": "PowerAutomate",
                        "name": trigger.name,
                        "description": trigger.description,
                        "trigger_type": trigger.trigger_type.value,
                        "target_agent": trigger.target_agent,
                        "message_template": trigger.message_template
                    })
        return exports


# Global registry instance
_registry = None

def get_trigger_registry() -> TriggerRegistry:
    """Get the global trigger registry instance"""
    global _registry
    if _registry is None:
        _registry = TriggerRegistry()
    return _registry
