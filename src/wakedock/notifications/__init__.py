"""
WakeDock Notifications Module

This module provides a comprehensive notification system for WakeDock,
supporting multiple notification channels including email, webhooks, 
Slack, Discord, and more.
"""

from .manager import NotificationManager
from .channels import (
    EmailChannel,
    WebhookChannel,
    SlackChannel,
    DiscordChannel,
    TeamsChannel
)
from .types import (
    NotificationType,
    NotificationPriority,
    Notification,
    NotificationResult
)
from .templates import NotificationTemplate, TemplateManager

__all__ = [
    'NotificationManager',
    'EmailChannel',
    'WebhookChannel',
    'SlackChannel',
    'DiscordChannel',
    'TeamsChannel',
    'NotificationType',
    'NotificationPriority',
    'Notification',
    'NotificationResult',
    'NotificationTemplate',
    'TemplateManager'
]
