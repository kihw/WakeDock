"""
Notification Manager - Central coordinator for all notification activities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import uuid
from collections import defaultdict, deque

from .types import (
    Notification,
    NotificationResult,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
    NotificationRule,
    NotificationPreferences,
    NotificationQueue,
    NotificationStats
)
from .channels import (
    BaseNotificationChannel,
    EmailChannel,
    WebhookChannel,
    SlackChannel,
    DiscordChannel,
    TeamsChannel
)
from .templates import TemplateManager
from ..config import get_settings

logger = logging.getLogger(__name__)


class NotificationManager:
    """Central manager for all notification activities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.max_queue_size = config.get('max_queue_size', 1000)
        self.batch_size = config.get('batch_size', 10)
        self.processing_interval = config.get('processing_interval', 5)  # seconds
        
        # Components
        self.channels: Dict[NotificationChannel, BaseNotificationChannel] = {}
        self.template_manager = TemplateManager(config.get('template_dir'))
        
        # State
        self.queue: deque[NotificationQueue] = deque()
        self.processing = False
        self.rules: Dict[str, NotificationRule] = {}
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.stats = NotificationStats()
        
        # Rate limiting and throttling
        self.rate_limits: Dict[str, deque] = defaultdict(deque)  # user_id -> timestamps
        self.cooldowns: Dict[str, datetime] = {}  # rule_id -> last_sent
        
        # Background task
        self._processor_task: Optional[asyncio.Task] = None
        
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Initialize notification channels based on configuration."""
        channels_config = self.config.get('channels', {})
        
        # Email channel
        if 'email' in channels_config:
            self.channels[NotificationChannel.EMAIL] = EmailChannel(channels_config['email'])
        
        # Webhook channel
        if 'webhook' in channels_config:
            self.channels[NotificationChannel.WEBHOOK] = WebhookChannel(channels_config['webhook'])
        
        # Slack channel
        if 'slack' in channels_config:
            self.channels[NotificationChannel.SLACK] = SlackChannel(channels_config['slack'])
        
        # Discord channel
        if 'discord' in channels_config:
            self.channels[NotificationChannel.DISCORD] = DiscordChannel(channels_config['discord'])
        
        # Teams channel
        if 'teams' in channels_config:
            self.channels[NotificationChannel.TEAMS] = TeamsChannel(channels_config['teams'])
    
    async def start(self):
        """Start the notification manager."""
        if not self.enabled:
            logger.info("Notification manager is disabled")
            return
        
        logger.info("Starting notification manager")
        
        # Validate channel configurations
        for channel_type, channel in self.channels.items():
            if await channel.validate_config():
                logger.info(f"{channel_type.value} channel configured successfully")
            else:
                logger.warning(f"{channel_type.value} channel configuration validation failed")
        
        # Start background processor
        self._processor_task = asyncio.create_task(self._process_queue())
        logger.info("Notification manager started")
    
    async def stop(self):
        """Stop the notification manager."""
        logger.info("Stopping notification manager")
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Notification manager stopped")
    
    async def send_notification(self, notification: Notification) -> List[NotificationResult]:
        """Send a notification through configured channels."""
        if not self.enabled:
            return []
        
        # Generate ID if not provided
        if not notification.id:
            notification.id = str(uuid.uuid4())
        
        # Apply rules and filters
        if not self._should_send_notification(notification):
            logger.debug(f"Notification {notification.id} filtered out by rules")
            return []
        
        # Apply templates
        self._apply_template(notification)
        
        # Determine channels and recipients
        channels_to_use = notification.channels or self._get_default_channels(notification)
        recipients = self._get_recipients(notification)
        
        if not channels_to_use:
            logger.warning(f"No channels configured for notification {notification.id}")
            return []
        
        results = []
        
        if notification.immediate:
            # Send immediately
            for channel_type in channels_to_use:
                if channel_type in self.channels:
                    result = await self._send_to_channel(notification, channel_type)
                    results.append(result)
        else:
            # Queue for batch processing
            await self._queue_notification(notification)
        
        # Update statistics
        self._update_stats(results)
        
        return results
    
    async def _send_to_channel(self, notification: Notification, 
                              channel_type: NotificationChannel) -> NotificationResult:
        """Send notification to a specific channel."""
        channel = self.channels[channel_type]
        
        try:
            # Apply channel-specific formatting
            title, message = self.template_manager.format_notification(
                notification, channel_type.value
            )
            
            # Update notification with formatted content
            formatted_notification = notification.copy()
            formatted_notification.title = title
            formatted_notification.message = message
            
            # Send through channel
            result = await channel.send(formatted_notification)
            
            if result.success:
                logger.info(f"Notification {notification.id} sent via {channel_type.value}")
            else:
                logger.error(f"Failed to send notification {notification.id} via {channel_type.value}: {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.id} via {channel_type.value}: {e}")
            return NotificationResult(
                notification_id=notification.id,
                channel=channel_type,
                success=False,
                message=f"Error: {str(e)}",
                error_code="SEND_ERROR"
            )
    
    async def _queue_notification(self, notification: Notification):
        """Queue a notification for batch processing."""
        if len(self.queue) >= self.max_queue_size:
            # Remove oldest notification if queue is full
            self.queue.popleft()
            logger.warning("Notification queue full, dropping oldest notification")
        
        # Calculate priority score
        priority_scores = {
            NotificationPriority.EMERGENCY: 1000,
            NotificationPriority.CRITICAL: 800,
            NotificationPriority.HIGH: 600,
            NotificationPriority.NORMAL: 400,
            NotificationPriority.LOW: 200
        }
        
        priority_score = priority_scores.get(notification.priority, 400)
        
        # Add delay if specified
        scheduled_at = datetime.utcnow()
        if notification.delay_seconds > 0:
            scheduled_at += timedelta(seconds=notification.delay_seconds)
        
        queued_notification = NotificationQueue(
            notification=notification,
            scheduled_at=scheduled_at,
            priority_score=priority_score
        )
        
        # Insert in priority order
        inserted = False
        for i, item in enumerate(self.queue):
            if queued_notification.priority_score > item.priority_score:
                self.queue.insert(i, queued_notification)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(queued_notification)
        
        logger.debug(f"Notification {notification.id} queued for processing")
    
    async def _process_queue(self):
        """Background task to process queued notifications."""
        while True:
            try:
                if not self.queue:
                    await asyncio.sleep(self.processing_interval)
                    continue
                
                current_time = datetime.utcnow()
                processed = 0
                
                # Process notifications in batches
                while self.queue and processed < self.batch_size:
                    queued_notification = self.queue[0]
                    
                    # Check if it's time to send
                    if queued_notification.scheduled_at > current_time:
                        break
                    
                    # Remove from queue
                    self.queue.popleft()
                    
                    # Process notification
                    await self._process_queued_notification(queued_notification)
                    processed += 1
                
                if processed > 0:
                    logger.debug(f"Processed {processed} notifications from queue")
                
                await asyncio.sleep(self.processing_interval)
                
            except Exception as e:
                logger.error(f"Error in notification processor: {e}")
                await asyncio.sleep(self.processing_interval)
    
    async def _process_queued_notification(self, queued_notification: NotificationQueue):
        """Process a single queued notification."""
        notification = queued_notification.notification
        
        try:
            queued_notification.status = "processing"
            queued_notification.attempts += 1
            queued_notification.last_attempt = datetime.utcnow()
            
            # Send to all configured channels
            channels_to_use = notification.channels or self._get_default_channels(notification)
            
            results = []
            for channel_type in channels_to_use:
                if channel_type in self.channels:
                    result = await self._send_to_channel(notification, channel_type)
                    results.append(result)
            
            # Check if all sends were successful
            if all(result.success for result in results):
                queued_notification.status = "sent"
                notification.sent_at = datetime.utcnow()
            else:
                # Some sends failed, check if we should retry
                if queued_notification.attempts < notification.max_retries:
                    # Reschedule for retry
                    retry_delay = min(60 * queued_notification.attempts, 300)  # Max 5 minutes
                    queued_notification.next_attempt = datetime.utcnow() + timedelta(seconds=retry_delay)
                    queued_notification.scheduled_at = queued_notification.next_attempt
                    queued_notification.status = "pending"
                    
                    # Re-queue for retry
                    self.queue.append(queued_notification)
                    logger.info(f"Rescheduling notification {notification.id} for retry in {retry_delay} seconds")
                else:
                    queued_notification.status = "failed"
                    notification.failed_at = datetime.utcnow()
                    logger.error(f"Notification {notification.id} failed after {queued_notification.attempts} attempts")
            
            # Update statistics
            self._update_stats(results)
            
        except Exception as e:
            logger.error(f"Error processing queued notification {notification.id}: {e}")
            queued_notification.status = "failed"
    
    def _should_send_notification(self, notification: Notification) -> bool:
        """Check if notification should be sent based on rules and filters."""
        # Check if notification type is enabled globally
        disabled_types = self.config.get('disabled_types', [])
        if notification.type.value in disabled_types:
            return False
        
        # Apply notification rules
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if self._matches_rule(notification, rule):
                # Check rate limiting
                if not self._check_rate_limit(rule, notification):
                    return False
                
                # Check cooldown
                if not self._check_cooldown(rule):
                    return False
                
                # Update cooldown
                if rule.cooldown_minutes:
                    self.cooldowns[rule.id] = datetime.utcnow()
                
                return True
        
        # Default behavior if no rules match
        return True
    
    def _matches_rule(self, notification: Notification, rule: NotificationRule) -> bool:
        """Check if notification matches a rule."""
        # Check event types
        if rule.event_types and notification.type not in rule.event_types:
            return False
        
        # Check priority levels
        if rule.priority_levels and notification.priority not in rule.priority_levels:
            return False
        
        # Check service patterns
        if rule.service_patterns and notification.metadata and notification.metadata.service_name:
            import re
            service_name = notification.metadata.service_name
            
            matches_pattern = False
            for pattern in rule.service_patterns:
                if re.match(pattern, service_name):
                    matches_pattern = True
                    break
            
            if not matches_pattern:
                return False
        
        return True
    
    def _check_rate_limit(self, rule: NotificationRule, notification: Notification) -> bool:
        """Check if notification passes rate limiting."""
        if not rule.rate_limit:
            return True
        
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        
        # Get rate limit key (could be rule-based or user-based)
        rate_key = f"rule:{rule.id}"
        
        # Clean old entries
        while self.rate_limits[rate_key] and self.rate_limits[rate_key][0] < hour_ago:
            self.rate_limits[rate_key].popleft()
        
        # Check if limit exceeded
        if len(self.rate_limits[rate_key]) >= rule.rate_limit:
            return False
        
        # Add current timestamp
        self.rate_limits[rate_key].append(current_time)
        return True
    
    def _check_cooldown(self, rule: NotificationRule) -> bool:
        """Check if notification passes cooldown period."""
        if not rule.cooldown_minutes:
            return True
        
        last_sent = self.cooldowns.get(rule.id)
        if not last_sent:
            return True
        
        cooldown_until = last_sent + timedelta(minutes=rule.cooldown_minutes)
        return datetime.utcnow() >= cooldown_until
    
    def _apply_template(self, notification: Notification):
        """Apply template to notification if specified."""
        if notification.template:
            template = self.template_manager.get_template(notification.template)
            if template:
                # Templates will be applied per-channel during sending
                pass
    
    def _get_default_channels(self, notification: Notification) -> List[NotificationChannel]:
        """Get default channels for a notification based on priority."""
        channels = []
        
        # Add channels based on priority
        if notification.priority in [NotificationPriority.EMERGENCY, NotificationPriority.CRITICAL]:
            # Critical notifications go to all channels
            channels.extend(self.channels.keys())
        elif notification.priority == NotificationPriority.HIGH:
            # High priority goes to email and primary chat
            if NotificationChannel.EMAIL in self.channels:
                channels.append(NotificationChannel.EMAIL)
            if NotificationChannel.SLACK in self.channels:
                channels.append(NotificationChannel.SLACK)
            elif NotificationChannel.DISCORD in self.channels:
                channels.append(NotificationChannel.DISCORD)
        else:
            # Normal and low priority go to default channel
            default_channel = self.config.get('default_channel', 'email')
            if default_channel == 'email' and NotificationChannel.EMAIL in self.channels:
                channels.append(NotificationChannel.EMAIL)
            elif default_channel == 'webhook' and NotificationChannel.WEBHOOK in self.channels:
                channels.append(NotificationChannel.WEBHOOK)
        
        return channels
    
    def _get_recipients(self, notification: Notification) -> List[str]:
        """Get recipients for a notification."""
        recipients = list(notification.recipients)
        
        # Add group recipients
        for group in notification.groups:
            group_recipients = self.config.get('groups', {}).get(group, [])
            recipients.extend(group_recipients)
        
        return list(set(recipients))  # Remove duplicates
    
    def _update_stats(self, results: List[NotificationResult]):
        """Update notification statistics."""
        for result in results:
            self.stats.total_sent += 1
            
            if result.success:
                self.stats.total_delivered += 1
            else:
                self.stats.total_failed += 1
            
            # Update channel-specific stats
            if result.channel == NotificationChannel.EMAIL:
                self.stats.email_sent += 1
            elif result.channel == NotificationChannel.WEBHOOK:
                self.stats.webhook_sent += 1
            elif result.channel == NotificationChannel.SLACK:
                self.stats.slack_sent += 1
            elif result.channel == NotificationChannel.DISCORD:
                self.stats.discord_sent += 1
        
        # Update error rate
        total = self.stats.total_sent
        if total > 0:
            self.stats.error_rate = self.stats.total_failed / total
        
        self.stats.last_updated = datetime.utcnow()
    
    # Management methods
    
    def add_rule(self, rule: NotificationRule):
        """Add a notification rule."""
        self.rules[rule.id] = rule
        logger.info(f"Added notification rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove a notification rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed notification rule: {rule_id}")
    
    def update_preferences(self, user_id: str, preferences: NotificationPreferences):
        """Update user notification preferences."""
        self.preferences[user_id] = preferences
        logger.info(f"Updated notification preferences for user: {user_id}")
    
    def get_stats(self) -> NotificationStats:
        """Get notification statistics."""
        # Update pending count
        self.stats.total_pending = len(self.queue)
        return self.stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information."""
        return {
            'queue_size': len(self.queue),
            'max_queue_size': self.max_queue_size,
            'processing': self.processing,
            'next_processing': min(
                (item.scheduled_at for item in self.queue),
                default=None
            )
        }
    
    async def flush_queue(self):
        """Process all queued notifications immediately."""
        logger.info("Flushing notification queue")
        
        while self.queue:
            queued_notification = self.queue.popleft()
            await self._process_queued_notification(queued_notification)
        
        logger.info("Notification queue flushed")
    
    async def test_channels(self) -> Dict[str, bool]:
        """Test all configured channels."""
        results = {}
        
        for channel_type, channel in self.channels.items():
            try:
                result = await channel.validate_config()
                results[channel_type.value] = result
            except Exception as e:
                logger.error(f"Error testing {channel_type.value} channel: {e}")
                results[channel_type.value] = False
        
        return results
