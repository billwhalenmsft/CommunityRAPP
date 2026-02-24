"""
RAPP Trigger Models
==================
Data models for event-driven triggers, compatible with Copilot Studio's trigger format.

Copilot Studio Compatibility:
- Trigger payloads match Copilot Studio's event trigger format
- Can be called BY Copilot Studio flows or call TO Copilot Studio
- Supports the same JSON payload structure
"""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class TriggerType(Enum):
    """Types of triggers supported by RAPP"""
    WEBHOOK = "webhook"
    TIMER = "timer"  # Scheduled/cron triggers
    QUEUE = "queue"  # Azure Service Bus/Storage Queue
    FILE = "file"  # Blob storage file events
    EMAIL = "email"  # Microsoft Graph email events
    TEAMS = "teams"  # Teams bot/messaging events
    DATAVERSE = "dataverse"  # Copilot Studio native trigger type
    MANUAL = "manual"  # Manually triggered


class TriggerStatus(Enum):
    """Status of a trigger execution"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"


@dataclass
class TriggerPayload:
    """
    Payload sent to an agent when a trigger fires.
    
    Compatible with Copilot Studio's trigger payload format:
    - message: Instructions for the agent (like Copilot Studio's payload message)
    - body: The actual event data (like Copilot Studio's "Use content from Body")
    - metadata: Additional context about the trigger
    
    Example Copilot Studio-compatible payload:
    {
        "message": "A new high-priority case was created. Triage and route appropriately.",
        "body": {
            "case_id": "12345",
            "priority": "High",
            "subject": "HVAC system failure",
            "customer": "Contoso Corp"
        },
        "metadata": {
            "trigger_type": "webhook",
            "source": "salesforce",
            "event": "case.created"
        }
    }
    """
    message: str  # Instructions for the agent (the "prompt" from the trigger)
    body: Dict[str, Any]  # Event data payload
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Copilot Studio compatibility fields
    conversation_id: Optional[str] = None  # For tracking in Copilot Studio
    activity_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        if not self.activity_id:
            self.activity_id = str(uuid.uuid4())
    
    def to_copilot_studio_format(self) -> Dict[str, Any]:
        """
        Convert to Copilot Studio-compatible event trigger format.
        This format can be used to trigger a Copilot Studio agent via Power Automate.
        """
        return {
            "type": "event",
            "name": self.metadata.get("event", "rapp.trigger"),
            "value": {
                "message": self.message,
                "body": self.body,
                "metadata": self.metadata
            },
            "conversation": {
                "id": self.conversation_id
            },
            "from": {
                "id": "rapp-trigger-system",
                "name": "RAPP Event Trigger"
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "body": self.body,
            "metadata": self.metadata,
            "conversation_id": self.conversation_id,
            "activity_id": self.activity_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerPayload':
        return cls(
            message=data.get("message", ""),
            body=data.get("body", {}),
            metadata=data.get("metadata", {}),
            conversation_id=data.get("conversation_id"),
            activity_id=data.get("activity_id")
        )


@dataclass
class TriggerEvent:
    """
    Represents a trigger event that was received.
    Tracks the full lifecycle of trigger processing.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trigger_name: str = ""
    trigger_type: TriggerType = TriggerType.WEBHOOK
    payload: Optional[TriggerPayload] = None
    status: TriggerStatus = TriggerStatus.PENDING
    
    # Timing
    received_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution details
    target_agent: str = ""
    target_action: str = ""
    agent_response: Optional[str] = None
    error_message: Optional[str] = None
    
    # Retry tracking
    attempt_count: int = 0
    max_attempts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger_name": self.trigger_name,
            "trigger_type": self.trigger_type.value,
            "payload": self.payload.to_dict() if self.payload else None,
            "status": self.status.value,
            "received_at": self.received_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "target_agent": self.target_agent,
            "target_action": self.target_action,
            "agent_response": self.agent_response,
            "error_message": self.error_message,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts
        }


@dataclass
class FilterCondition:
    """A single filter condition for trigger evaluation"""
    field: str
    operator: str  # equals, not_equals, contains, in, greater_than, less_than, exists
    value: Union[str, int, float, bool, List[Any], None] = None
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate this condition against the provided data"""
        # Navigate nested fields (e.g., "case.priority" -> data["case"]["priority"])
        field_value = data
        for key in self.field.split("."):
            if isinstance(field_value, dict) and key in field_value:
                field_value = field_value[key]
            else:
                field_value = None
                break
        
        if self.operator == "equals":
            return field_value == self.value
        elif self.operator == "not_equals":
            return field_value != self.value
        elif self.operator == "contains":
            return self.value in str(field_value) if field_value else False
        elif self.operator == "in":
            return field_value in self.value if isinstance(self.value, list) else False
        elif self.operator == "greater_than":
            return field_value > self.value if field_value is not None else False
        elif self.operator == "less_than":
            return field_value < self.value if field_value is not None else False
        elif self.operator == "exists":
            return field_value is not None
        elif self.operator == "not_exists":
            return field_value is None
        
        return False


@dataclass
class TriggerConfig:
    """
    Base configuration for all trigger types.
    Can be loaded from YAML/JSON configuration files.
    """
    name: str
    description: str = ""
    trigger_type: TriggerType = TriggerType.WEBHOOK
    enabled: bool = True
    
    # Target agent configuration
    target_agent: str = ""
    target_action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Payload configuration
    message_template: str = ""  # Template for the agent instructions
    body_mapping: Dict[str, str] = field(default_factory=dict)  # Map event fields to body fields
    
    # Filtering
    filters: List[FilterCondition] = field(default_factory=list)
    
    # Notifications
    on_success: List[Dict[str, Any]] = field(default_factory=list)
    on_failure: List[Dict[str, Any]] = field(default_factory=list)
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    # Copilot Studio integration
    copilot_studio_enabled: bool = False
    copilot_studio_bot_id: Optional[str] = None
    copilot_studio_environment_url: Optional[str] = None
    
    def evaluate_filters(self, event_data: Dict[str, Any]) -> bool:
        """Check if event data passes all filter conditions"""
        if not self.filters:
            return True
        return all(f.evaluate(event_data) for f in self.filters)
    
    def build_payload(self, event_data: Dict[str, Any]) -> TriggerPayload:
        """Build a trigger payload from event data using configured mappings"""
        # Build message from template
        message = self.message_template
        for key, value in event_data.items():
            if isinstance(value, (str, int, float, bool)):
                message = message.replace(f"{{{{{key}}}}}", str(value))
        
        # Build body from mapping or use raw event data
        if self.body_mapping:
            body = {}
            for target_key, source_path in self.body_mapping.items():
                value = event_data
                for key in source_path.split("."):
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                if value is not None:
                    body[target_key] = value
        else:
            body = event_data
        
        return TriggerPayload(
            message=message,
            body=body,
            metadata={
                "trigger_name": self.name,
                "trigger_type": self.trigger_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "enabled": self.enabled,
            "target_agent": self.target_agent,
            "target_action": self.target_action,
            "parameters": self.parameters,
            "message_template": self.message_template,
            "body_mapping": self.body_mapping,
            "filters": [{"field": f.field, "operator": f.operator, "value": f.value} for f in self.filters],
            "on_success": self.on_success,
            "on_failure": self.on_failure,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "copilot_studio_enabled": self.copilot_studio_enabled,
            "copilot_studio_bot_id": self.copilot_studio_bot_id,
            "copilot_studio_environment_url": self.copilot_studio_environment_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerConfig':
        filters = [
            FilterCondition(field=f["field"], operator=f["operator"], value=f.get("value"))
            for f in data.get("filters", [])
        ]
        
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            trigger_type=TriggerType(data.get("trigger_type", "webhook")),
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
            copilot_studio_environment_url=data.get("copilot_studio_environment_url")
        )


@dataclass
class WebhookTrigger(TriggerConfig):
    """Configuration for webhook-based triggers"""
    
    # Webhook-specific settings
    secret_key: Optional[str] = None  # For validating webhook signatures
    allowed_ips: List[str] = field(default_factory=list)  # IP allowlist
    required_headers: Dict[str, str] = field(default_factory=dict)
    
    # Source identification (e.g., "salesforce", "servicenow", "custom")
    source: str = "custom"
    event_type: str = ""  # e.g., "case.created", "ticket.updated"
    
    def __post_init__(self):
        self.trigger_type = TriggerType.WEBHOOK
    
    def validate_request(self, headers: Dict[str, str], body: bytes, 
                        signature: Optional[str] = None, 
                        client_ip: Optional[str] = None) -> bool:
        """Validate an incoming webhook request"""
        # Check IP allowlist
        if self.allowed_ips and client_ip:
            if client_ip not in self.allowed_ips:
                return False
        
        # Check required headers
        for key, expected_value in self.required_headers.items():
            if headers.get(key) != expected_value:
                return False
        
        # Validate signature if secret key is configured
        if self.secret_key and signature:
            import hmac
            import hashlib
            expected_signature = hmac.new(
                self.secret_key.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                return False
        
        return True


@dataclass 
class TimerTrigger(TriggerConfig):
    """Configuration for scheduled/timer triggers"""
    
    # Timer-specific settings (Azure Functions Timer Trigger format)
    schedule: str = ""  # CRON expression: "0 0 8 * * *" = 8am daily
    timezone: str = "UTC"
    
    # Run immediately on startup?
    run_on_startup: bool = False
    
    def __post_init__(self):
        self.trigger_type = TriggerType.TIMER
    
    def get_next_run(self) -> Optional[datetime]:
        """Calculate the next run time based on the schedule"""
        try:
            from croniter import croniter
            cron = croniter(self.schedule, datetime.utcnow())
            return cron.get_next(datetime)
        except ImportError:
            # croniter not installed
            return None


@dataclass
class QueueTrigger(TriggerConfig):
    """Configuration for queue-based triggers (Service Bus, Storage Queue)"""
    
    # Queue-specific settings
    queue_name: str = ""
    connection_string_setting: str = ""  # Name of the setting containing connection string
    
    # Processing settings
    batch_size: int = 1
    visibility_timeout_seconds: int = 300
    
    def __post_init__(self):
        self.trigger_type = TriggerType.QUEUE


@dataclass
class DataverseTrigger(TriggerConfig):
    """
    Configuration for Dataverse triggers - native to Copilot Studio.
    When RAPP is deployed to Copilot Studio, these triggers work natively.
    """
    
    # Dataverse-specific settings
    table_name: str = ""  # e.g., "account", "contact", "incident"
    change_type: str = "create"  # create, update, delete
    filter_expression: str = ""  # OData filter
    select_columns: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.trigger_type = TriggerType.DATAVERSE
    
    def to_copilot_studio_trigger(self) -> Dict[str, Any]:
        """
        Convert to Copilot Studio trigger definition format.
        This can be used when transpiling to Copilot Studio.
        """
        return {
            "type": "Dataverse",
            "kind": "PowerPlatformConnector",
            "inputs": {
                "host": {
                    "connectionName": "shared_commondataserviceforapps"
                },
                "parameters": {
                    "subscriptionRequest/entityName": self.table_name,
                    "subscriptionRequest/changeType": self.change_type,
                    "subscriptionRequest/filterExpression": self.filter_expression
                }
            },
            "metadata": {
                "operationMetadataId": str(uuid.uuid4())
            }
        }
