"""
RAPP Trigger Router
==================
Routes incoming trigger events to the appropriate agents.
Handles retry logic, error handling, and notifications.

Copilot Studio Integration:
- Can route events TO Copilot Studio agents via Direct Line API
- Can receive events FROM Copilot Studio via webhook
- Trigger payloads are compatible with both platforms
"""

import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

from .trigger_models import (
    TriggerConfig,
    TriggerEvent,
    TriggerPayload,
    TriggerStatus,
    TriggerType,
    WebhookTrigger
)
from .trigger_registry import TriggerRegistry, get_trigger_registry

logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for trigger notifications"""
    teams_webhook_url: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)
    

class TriggerRouter:
    """
    Routes trigger events to agents and handles the execution lifecycle.
    
    Features:
    - Webhook event processing
    - Timer trigger scheduling
    - Copilot Studio integration (send/receive)
    - Retry logic with exponential backoff
    - Success/failure notifications
    - Event history tracking
    
    Usage:
        router = TriggerRouter(agent_executor)
        
        # Process a webhook event
        result = await router.route_webhook(
            source="salesforce",
            event_type="case.created",
            payload={"case_id": "12345", ...}
        )
        
        # Process a timer event
        result = await router.route_timer("daily_ci_report")
    """
    
    def __init__(self, agent_executor: Callable = None):
        """
        Initialize the trigger router.
        
        Args:
            agent_executor: Function to execute agents. 
                           Signature: (agent_name: str, action: str, parameters: dict) -> str
                           If None, will use the default RAPP executor.
        """
        self.registry = get_trigger_registry()
        self.agent_executor = agent_executor
        self.event_history: List[TriggerEvent] = []
        self.max_history_size = 1000
        
        # Copilot Studio integration
        self.copilot_studio_token: Optional[str] = None
        self.copilot_studio_base_url: Optional[str] = None
        
        # Notification config
        self.notifications = NotificationConfig(
            teams_webhook_url=os.environ.get("TEAMS_WEBHOOK_URL"),
            email_from=os.environ.get("NOTIFICATION_EMAIL_FROM"),
            email_to=os.environ.get("NOTIFICATION_EMAIL_TO", "").split(",")
        )
    
    def set_agent_executor(self, executor: Callable):
        """Set the agent executor function"""
        self.agent_executor = executor
    
    async def route_webhook(
        self,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None,
        client_ip: str = None
    ) -> TriggerEvent:
        """
        Route an incoming webhook event to the appropriate agent(s).
        
        Args:
            source: The webhook source (e.g., "salesforce", "servicenow")
            event_type: The event type (e.g., "case.created", "ticket.updated")
            payload: The webhook payload data
            headers: HTTP headers from the request
            client_ip: Client IP address for validation
            
        Returns:
            TriggerEvent with processing results
        """
        headers = headers or {}
        
        # Find matching triggers
        triggers = self.registry.get_webhooks_for_source(source, event_type)
        
        if not triggers:
            # Check for catch-all trigger
            triggers = self.registry.get_webhooks_for_source(source)
        
        if not triggers:
            logger.warning(f"No triggers found for {source}/{event_type}")
            event = TriggerEvent(
                trigger_name=f"{source}/{event_type}",
                trigger_type=TriggerType.WEBHOOK,
                status=TriggerStatus.FAILED,
                error_message=f"No triggers configured for {source}/{event_type}"
            )
            self._record_event(event)
            return event
        
        # Process each matching trigger
        results = []
        for trigger in triggers:
            if not trigger.enabled:
                continue
                
            # Validate request
            if isinstance(trigger, WebhookTrigger):
                signature = headers.get("X-Signature") or headers.get("X-Hub-Signature-256")
                if not trigger.validate_request(headers, json.dumps(payload).encode(), signature, client_ip):
                    logger.warning(f"Webhook validation failed for trigger: {trigger.name}")
                    continue
            
            # Check filters
            if not trigger.evaluate_filters(payload):
                logger.debug(f"Payload filtered out by trigger: {trigger.name}")
                continue
            
            # Create trigger event
            event = TriggerEvent(
                trigger_name=trigger.name,
                trigger_type=TriggerType.WEBHOOK,
                payload=trigger.build_payload(payload),
                target_agent=trigger.target_agent,
                target_action=trigger.target_action,
                status=TriggerStatus.PROCESSING
            )
            
            # Route to agent
            result = await self._execute_trigger(trigger, event)
            results.append(result)
        
        # Return the first result (or create a summary if multiple)
        if results:
            return results[0] if len(results) == 1 else self._summarize_results(results)
        
        # No triggers matched after filtering
        event = TriggerEvent(
            trigger_name=f"{source}/{event_type}",
            trigger_type=TriggerType.WEBHOOK,
            status=TriggerStatus.FAILED,
            error_message="No triggers matched after filtering"
        )
        self._record_event(event)
        return event
    
    async def route_timer(self, trigger_name: str) -> TriggerEvent:
        """
        Route a timer trigger event.
        Called by Azure Functions timer trigger.
        
        Args:
            trigger_name: Name of the timer trigger to execute
            
        Returns:
            TriggerEvent with processing results
        """
        trigger = self.registry.get(trigger_name)
        
        if not trigger:
            event = TriggerEvent(
                trigger_name=trigger_name,
                trigger_type=TriggerType.TIMER,
                status=TriggerStatus.FAILED,
                error_message=f"Timer trigger not found: {trigger_name}"
            )
            self._record_event(event)
            return event
        
        if not trigger.enabled:
            event = TriggerEvent(
                trigger_name=trigger_name,
                trigger_type=TriggerType.TIMER,
                status=TriggerStatus.FAILED,
                error_message=f"Timer trigger is disabled: {trigger_name}"
            )
            self._record_event(event)
            return event
        
        # Build payload for timer (no external data)
        timer_payload = TriggerPayload(
            message=trigger.message_template or f"Scheduled trigger: {trigger_name}",
            body={
                "trigger_name": trigger_name,
                "triggered_at": datetime.utcnow().isoformat()
            },
            metadata={
                "trigger_type": "timer",
                "trigger_name": trigger_name
            }
        )
        
        event = TriggerEvent(
            trigger_name=trigger_name,
            trigger_type=TriggerType.TIMER,
            payload=timer_payload,
            target_agent=trigger.target_agent,
            target_action=trigger.target_action,
            status=TriggerStatus.PROCESSING
        )
        
        return await self._execute_trigger(trigger, event)
    
    async def route_manual(
        self,
        trigger_name: str,
        payload: Dict[str, Any] = None
    ) -> TriggerEvent:
        """
        Manually trigger an agent action.
        Useful for testing triggers.
        
        Args:
            trigger_name: Name of the trigger to execute
            payload: Optional payload data
            
        Returns:
            TriggerEvent with processing results
        """
        trigger = self.registry.get(trigger_name)
        
        if not trigger:
            event = TriggerEvent(
                trigger_name=trigger_name,
                trigger_type=TriggerType.MANUAL,
                status=TriggerStatus.FAILED,
                error_message=f"Trigger not found: {trigger_name}"
            )
            self._record_event(event)
            return event
        
        # Build payload
        trigger_payload = trigger.build_payload(payload or {})
        
        event = TriggerEvent(
            trigger_name=trigger_name,
            trigger_type=TriggerType.MANUAL,
            payload=trigger_payload,
            target_agent=trigger.target_agent,
            target_action=trigger.target_action,
            status=TriggerStatus.PROCESSING
        )
        
        return await self._execute_trigger(trigger, event)
    
    async def _execute_trigger(
        self,
        trigger: TriggerConfig,
        event: TriggerEvent
    ) -> TriggerEvent:
        """Execute a trigger and handle retries"""
        event.processed_at = datetime.utcnow()
        
        while event.attempt_count < trigger.max_retries:
            event.attempt_count += 1
            
            try:
                # Route to Copilot Studio if enabled
                if trigger.copilot_studio_enabled and trigger.copilot_studio_bot_id:
                    response = await self._send_to_copilot_studio(trigger, event.payload)
                else:
                    # Route to RAPP agent
                    response = await self._execute_agent(trigger, event.payload)
                
                event.agent_response = response
                event.status = TriggerStatus.SUCCESS
                event.completed_at = datetime.utcnow()
                
                # Send success notifications
                await self._send_notifications(trigger.on_success, event)
                
                break
                
            except Exception as e:
                logger.error(f"Trigger execution failed (attempt {event.attempt_count}): {e}")
                event.error_message = str(e)
                
                if event.attempt_count < trigger.max_retries:
                    event.status = TriggerStatus.RETRYING
                    # Exponential backoff
                    delay = trigger.retry_delay_seconds * (2 ** (event.attempt_count - 1))
                    await asyncio.sleep(delay)
                else:
                    event.status = TriggerStatus.FAILED
                    event.completed_at = datetime.utcnow()
                    
                    # Send failure notifications
                    await self._send_notifications(trigger.on_failure, event)
        
        self._record_event(event)
        return event
    
    async def _execute_agent(
        self,
        trigger: TriggerConfig,
        payload: TriggerPayload
    ) -> str:
        """Execute a RAPP agent with the trigger payload"""
        if not self.agent_executor:
            raise RuntimeError("No agent executor configured")
        
        # Build parameters from trigger config and payload
        parameters = {
            **trigger.parameters,
            "action": trigger.target_action,
            "_trigger_payload": payload.to_dict()
        }
        
        # Merge payload body into parameters
        for key, value in payload.body.items():
            if key not in parameters:
                parameters[key] = value
        
        # Execute the agent
        response = self.agent_executor(
            trigger.target_agent,
            trigger.target_action,
            parameters
        )
        
        return response
    
    async def _send_to_copilot_studio(
        self,
        trigger: TriggerConfig,
        payload: TriggerPayload
    ) -> str:
        """
        Send a trigger event to a Copilot Studio agent.
        Uses the Direct Line API to send activities to the bot.
        """
        if not trigger.copilot_studio_bot_id:
            raise ValueError("Copilot Studio bot ID not configured")
        
        # Get or refresh token
        token = await self._get_copilot_studio_token(trigger)
        
        # Build Copilot Studio activity
        activity = payload.to_copilot_studio_format()
        
        # Send via Direct Line
        base_url = trigger.copilot_studio_environment_url or os.environ.get("DATAVERSE_ENVIRONMENT_URL")
        
        async with aiohttp.ClientSession() as session:
            # Start conversation
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Send activity to bot
            url = f"{base_url}/api/botmanagement/v1/bots/{trigger.copilot_studio_bot_id}/directline/conversations"
            
            async with session.post(url, headers=headers, json={"activity": activity}) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise RuntimeError(f"Copilot Studio API error: {resp.status} - {error}")
                
                result = await resp.json()
                return result.get("response", "Activity sent to Copilot Studio")
    
    async def _get_copilot_studio_token(self, trigger: TriggerConfig) -> str:
        """Get authentication token for Copilot Studio"""
        # Try to use existing token or get from environment
        if self.copilot_studio_token:
            return self.copilot_studio_token
        
        # Try environment variable
        token = os.environ.get("COPILOT_STUDIO_TOKEN")
        if token:
            return token
        
        # Use Azure Identity to get token
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://api.powerplatform.com/.default")
            self.copilot_studio_token = token.token
            return token.token
        except Exception as e:
            logger.error(f"Failed to get Copilot Studio token: {e}")
            raise
    
    async def _send_notifications(
        self,
        notification_configs: List[Dict[str, Any]],
        event: TriggerEvent
    ):
        """Send notifications based on trigger configuration"""
        for config in notification_configs:
            try:
                notification_type = config.get("type")
                
                if notification_type == "teams":
                    await self._send_teams_notification(config, event)
                elif notification_type == "email":
                    await self._send_email_notification(config, event)
                elif notification_type == "webhook":
                    await self._send_webhook_notification(config, event)
                    
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    async def _send_teams_notification(
        self,
        config: Dict[str, Any],
        event: TriggerEvent
    ):
        """Send a Teams notification via webhook"""
        webhook_url = config.get("webhook_url") or self.notifications.teams_webhook_url
        if not webhook_url:
            return
        
        # Build adaptive card
        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Large",
                            "weight": "Bolder",
                            "text": f"🔔 Trigger: {event.trigger_name}",
                            "color": "Good" if event.status == TriggerStatus.SUCCESS else "Attention"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Status", "value": event.status.value},
                                {"title": "Agent", "value": event.target_agent},
                                {"title": "Action", "value": event.target_action},
                                {"title": "Time", "value": event.completed_at.isoformat() if event.completed_at else "N/A"}
                            ]
                        }
                    ]
                }
            }]
        }
        
        if event.error_message:
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": f"Error: {event.error_message}",
                "color": "Attention",
                "wrap": True
            })
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=card) as resp:
                if resp.status not in (200, 202):
                    logger.error(f"Teams notification failed: {resp.status}")
    
    async def _send_email_notification(
        self,
        config: Dict[str, Any],
        event: TriggerEvent
    ):
        """Send an email notification via Microsoft Graph"""
        # TODO: Implement email notification via Graph API
        pass
    
    async def _send_webhook_notification(
        self,
        config: Dict[str, Any],
        event: TriggerEvent
    ):
        """Send a notification to a custom webhook"""
        webhook_url = config.get("url")
        if not webhook_url:
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=event.to_dict()) as resp:
                if resp.status not in (200, 201, 202):
                    logger.error(f"Webhook notification failed: {resp.status}")
    
    def _record_event(self, event: TriggerEvent):
        """Record a trigger event in history"""
        self.event_history.append(event)
        
        # Trim history if needed
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    def _summarize_results(self, events: List[TriggerEvent]) -> TriggerEvent:
        """Summarize multiple trigger results into one"""
        success_count = sum(1 for e in events if e.status == TriggerStatus.SUCCESS)
        
        return TriggerEvent(
            trigger_name=f"multi-trigger ({len(events)} triggers)",
            trigger_type=events[0].trigger_type if events else TriggerType.WEBHOOK,
            status=TriggerStatus.SUCCESS if success_count == len(events) else TriggerStatus.FAILED,
            agent_response=f"{success_count}/{len(events)} triggers succeeded"
        )
    
    def get_history(
        self,
        trigger_name: str = None,
        status: TriggerStatus = None,
        limit: int = 100
    ) -> List[TriggerEvent]:
        """Get trigger event history with optional filtering"""
        events = self.event_history
        
        if trigger_name:
            events = [e for e in events if e.trigger_name == trigger_name]
        
        if status:
            events = [e for e in events if e.status == status]
        
        return events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trigger statistics"""
        total = len(self.event_history)
        success = sum(1 for e in self.event_history if e.status == TriggerStatus.SUCCESS)
        failed = sum(1 for e in self.event_history if e.status == TriggerStatus.FAILED)
        
        by_trigger = {}
        for event in self.event_history:
            if event.trigger_name not in by_trigger:
                by_trigger[event.trigger_name] = {"total": 0, "success": 0, "failed": 0}
            by_trigger[event.trigger_name]["total"] += 1
            if event.status == TriggerStatus.SUCCESS:
                by_trigger[event.trigger_name]["success"] += 1
            elif event.status == TriggerStatus.FAILED:
                by_trigger[event.trigger_name]["failed"] += 1
        
        return {
            "total_events": total,
            "success": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "by_trigger": by_trigger
        }


# Global router instance
_router = None

def get_trigger_router() -> TriggerRouter:
    """Get the global trigger router instance"""
    global _router
    if _router is None:
        _router = TriggerRouter()
    return _router
