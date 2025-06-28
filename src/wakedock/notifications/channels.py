"""
Notification channels for sending notifications through various services.
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from .types import Notification, NotificationResult, NotificationChannel
from ..config import get_settings

logger = logging.getLogger(__name__)


class BaseNotificationChannel(ABC):
    """Base class for all notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
    
    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult:
        """Send a notification through this channel."""
        pass
    
    @abstractmethod
    def get_channel_type(self) -> NotificationChannel:
        """Get the channel type."""
        pass
    
    async def validate_config(self) -> bool:
        """Validate the channel configuration."""
        return True
    
    def format_message(self, notification: Notification) -> str:
        """Format the notification message for this channel."""
        return notification.message
    
    def create_result(self, notification: Notification, success: bool, 
                     message: str, response_data: Optional[Dict] = None,
                     error_code: Optional[str] = None) -> NotificationResult:
        """Create a notification result."""
        return NotificationResult(
            notification_id=notification.id,
            channel=self.get_channel_type(),
            success=success,
            message=message,
            response_data=response_data,
            error_code=error_code
        )


class EmailChannel(BaseNotificationChannel):
    """Email notification channel using SMTP."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get('smtp_host', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_username = config.get('smtp_username')
        self.smtp_password = config.get('smtp_password')
        self.use_tls = config.get('use_tls', True)
        self.from_email = config.get('from_email', 'wakedock@localhost')
        self.from_name = config.get('from_name', 'WakeDock')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.EMAIL
    
    async def validate_config(self) -> bool:
        """Validate SMTP configuration."""
        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                timeout=10
            ) as server:
                if self.use_tls:
                    await server.starttls()
                if self.smtp_username and self.smtp_password:
                    await server.login(self.smtp_username, self.smtp_password)
                return True
        except Exception as e:
            logger.error(f"Email configuration validation failed: {e}")
            return False
    
    def format_email_content(self, notification: Notification) -> tuple[str, str]:
        """Format email content (subject, body)."""
        subject = f"[WakeDock] {notification.title}"
        
        # Create HTML body
        html_template = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { background-color: #2563eb; color: white; padding: 20px; }
                .content { padding: 20px; }
                .priority-critical { border-left: 5px solid #dc2626; }
                .priority-high { border-left: 5px solid #ea580c; }
                .priority-normal { border-left: 5px solid #2563eb; }
                .priority-low { border-left: 5px solid #16a34a; }
                .metadata { background-color: #f3f4f6; padding: 10px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ notification.title }}</h1>
                <p>Priority: {{ notification.priority.value.title() }}</p>
                <p>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</p>
            </div>
            <div class="content priority-{{ notification.priority.value }}">
                <p>{{ notification.message }}</p>
                
                {% if notification.metadata %}
                <div class="metadata">
                    <h3>Details:</h3>
                    {% if notification.metadata.service_name %}
                    <p><strong>Service:</strong> {{ notification.metadata.service_name }}</p>
                    {% endif %}
                    {% if notification.metadata.error_code %}
                    <p><strong>Error Code:</strong> {{ notification.metadata.error_code }}</p>
                    {% endif %}
                    {% if notification.metadata.metrics %}
                    <p><strong>Metrics:</strong></p>
                    <ul>
                        {% for key, value in notification.metadata.metrics.items() %}
                        <li>{{ key }}: {{ value }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_body = template.render(notification=notification)
        
        return subject, html_body
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send email notification."""
        if not self.enabled:
            return self.create_result(notification, False, "Email channel disabled")
        
        try:
            subject, html_body = self.format_email_content(notification)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(notification.recipients)
            
            # Add text and HTML parts
            text_part = MIMEText(notification.message, 'plain')
            html_part = MIMEText(html_body, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                timeout=self.timeout
            ) as server:
                if self.use_tls:
                    await server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    await server.login(self.smtp_username, self.smtp_password)
                
                await server.send_message(msg)
            
            return self.create_result(
                notification,
                True,
                f"Email sent to {len(notification.recipients)} recipients"
            )
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return self.create_result(
                notification,
                False,
                f"Failed to send email: {str(e)}",
                error_code="EMAIL_SEND_ERROR"
            )


class WebhookChannel(BaseNotificationChannel):
    """Webhook notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
        self.secret = config.get('secret')
        self.headers = config.get('headers', {})
        self.method = config.get('method', 'POST').upper()
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK
    
    async def validate_config(self) -> bool:
        """Validate webhook configuration."""
        if not self.webhook_url:
            logger.error("Webhook URL is required")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.webhook_url, timeout=5)
                return response.status_code < 500
        except Exception as e:
            logger.error(f"Webhook validation failed: {e}")
            return False
    
    def create_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create webhook payload."""
        payload = {
            'id': notification.id,
            'type': notification.type.value,
            'priority': notification.priority.value,
            'title': notification.title,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat(),
            'data': notification.data
        }
        
        if notification.metadata:
            payload['metadata'] = {
                'service_id': notification.metadata.service_id,
                'service_name': notification.metadata.service_name,
                'container_id': notification.metadata.container_id,
                'error_code': notification.metadata.error_code,
                'metrics': notification.metadata.metrics,
                'tags': notification.metadata.tags
            }
        
        return payload
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send webhook notification."""
        if not self.enabled:
            return self.create_result(notification, False, "Webhook channel disabled")
        
        try:
            payload = self.create_payload(notification)
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'WakeDock/1.0',
                **self.headers
            }
            
            # Add signature if secret is provided
            if self.secret:
                import hmac
                import hashlib
                
                body = json.dumps(payload)
                signature = hmac.new(
                    self.secret.encode(),
                    body.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers['X-WakeDock-Signature'] = f"sha256={signature}"
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=self.method,
                    url=self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                return self.create_result(
                    notification,
                    True,
                    f"Webhook delivered (HTTP {response.status_code})",
                    response_data={'status_code': response.status_code}
                )
                
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return self.create_result(
                notification,
                False,
                f"Failed to send webhook: {str(e)}",
                error_code="WEBHOOK_SEND_ERROR"
            )


class SlackChannel(BaseNotificationChannel):
    """Slack notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
        self.token = config.get('token')
        self.channel = config.get('channel', '#general')
        self.username = config.get('username', 'WakeDock')
        self.icon_emoji = config.get('icon_emoji', ':whale:')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.SLACK
    
    def create_slack_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create Slack-formatted payload."""
        # Color based on priority
        color_map = {
            'emergency': '#8B0000',
            'critical': '#FF0000',
            'high': '#FF8C00',
            'normal': '#36a64f',
            'low': '#808080'
        }
        
        color = color_map.get(notification.priority.value, '#36a64f')
        
        payload = {
            'username': self.username,
            'icon_emoji': self.icon_emoji,
            'channel': self.channel,
            'attachments': [{
                'color': color,
                'title': notification.title,
                'text': notification.message,
                'timestamp': int(notification.timestamp.timestamp()),
                'fields': [
                    {
                        'title': 'Priority',
                        'value': notification.priority.value.title(),
                        'short': True
                    },
                    {
                        'title': 'Type',
                        'value': notification.type.value.replace('_', ' ').title(),
                        'short': True
                    }
                ]
            }]
        }
        
        # Add metadata fields
        if notification.metadata:
            fields = payload['attachments'][0]['fields']
            
            if notification.metadata.service_name:
                fields.append({
                    'title': 'Service',
                    'value': notification.metadata.service_name,
                    'short': True
                })
            
            if notification.metadata.error_code:
                fields.append({
                    'title': 'Error Code',
                    'value': notification.metadata.error_code,
                    'short': True
                })
        
        return payload
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send Slack notification."""
        if not self.enabled:
            return self.create_result(notification, False, "Slack channel disabled")
        
        try:
            payload = self.create_slack_payload(notification)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                return self.create_result(
                    notification,
                    True,
                    f"Slack message sent to {self.channel}"
                )
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return self.create_result(
                notification,
                False,
                f"Failed to send Slack message: {str(e)}",
                error_code="SLACK_SEND_ERROR"
            )


class DiscordChannel(BaseNotificationChannel):
    """Discord notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
        self.username = config.get('username', 'WakeDock')
        self.avatar_url = config.get('avatar_url')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.DISCORD
    
    def create_discord_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create Discord-formatted payload."""
        # Color based on priority
        color_map = {
            'emergency': 0x8B0000,
            'critical': 0xFF0000,
            'high': 0xFF8C00,
            'normal': 0x36a64f,
            'low': 0x808080
        }
        
        color = color_map.get(notification.priority.value, 0x36a64f)
        
        embed = {
            'title': notification.title,
            'description': notification.message,
            'color': color,
            'timestamp': notification.timestamp.isoformat(),
            'fields': [
                {
                    'name': 'Priority',
                    'value': notification.priority.value.title(),
                    'inline': True
                },
                {
                    'name': 'Type',
                    'value': notification.type.value.replace('_', ' ').title(),
                    'inline': True
                }
            ]
        }
        
        # Add metadata fields
        if notification.metadata:
            if notification.metadata.service_name:
                embed['fields'].append({
                    'name': 'Service',
                    'value': notification.metadata.service_name,
                    'inline': True
                })
            
            if notification.metadata.error_code:
                embed['fields'].append({
                    'name': 'Error Code',
                    'value': notification.metadata.error_code,
                    'inline': True
                })
        
        payload = {
            'username': self.username,
            'embeds': [embed]
        }
        
        if self.avatar_url:
            payload['avatar_url'] = self.avatar_url
        
        return payload
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send Discord notification."""
        if not self.enabled:
            return self.create_result(notification, False, "Discord channel disabled")
        
        try:
            payload = self.create_discord_payload(notification)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                return self.create_result(
                    notification,
                    True,
                    "Discord message sent"
                )
                
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return self.create_result(
                notification,
                False,
                f"Failed to send Discord message: {str(e)}",
                error_code="DISCORD_SEND_ERROR"
            )


class TeamsChannel(BaseNotificationChannel):
    """Microsoft Teams notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.TEAMS
    
    def create_teams_payload(self, notification: Notification) -> Dict[str, Any]:
        """Create Teams-formatted payload."""
        # Theme color based on priority
        color_map = {
            'emergency': '8B0000',
            'critical': 'FF0000',
            'high': 'FF8C00',
            'normal': '36a64f',
            'low': '808080'
        }
        
        theme_color = color_map.get(notification.priority.value, '36a64f')
        
        payload = {
            '@type': 'MessageCard',
            '@context': 'http://schema.org/extensions',
            'themeColor': theme_color,
            'summary': notification.title,
            'sections': [{
                'activityTitle': notification.title,
                'activitySubtitle': f"Priority: {notification.priority.value.title()}",
                'text': notification.message,
                'facts': [
                    {
                        'name': 'Type',
                        'value': notification.type.value.replace('_', ' ').title()
                    },
                    {
                        'name': 'Time',
                        'value': notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
                    }
                ]
            }]
        }
        
        # Add metadata facts
        if notification.metadata:
            facts = payload['sections'][0]['facts']
            
            if notification.metadata.service_name:
                facts.append({
                    'name': 'Service',
                    'value': notification.metadata.service_name
                })
            
            if notification.metadata.error_code:
                facts.append({
                    'name': 'Error Code',
                    'value': notification.metadata.error_code
                })
        
        return payload
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send Teams notification."""
        if not self.enabled:
            return self.create_result(notification, False, "Teams channel disabled")
        
        try:
            payload = self.create_teams_payload(notification)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                return self.create_result(
                    notification,
                    True,
                    "Teams message sent"
                )
                
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return self.create_result(
                notification,
                False,
                f"Failed to send Teams message: {str(e)}",
                error_code="TEAMS_SEND_ERROR"
            )
