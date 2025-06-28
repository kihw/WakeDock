"""
Notification templates for formatting messages across different channels.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from jinja2 import Template, Environment, FileSystemLoader
import os

from .types import Notification, NotificationType, NotificationPriority


@dataclass
class NotificationTemplate:
    """A template for formatting notifications."""
    
    name: str
    title_template: str
    message_template: str
    channel_specific: Dict[str, Dict[str, str]]  # channel -> {title, message}
    variables: Dict[str, Any]
    
    def render_title(self, notification: Notification, channel: str = 'default') -> str:
        """Render the notification title."""
        template_str = self.channel_specific.get(channel, {}).get('title', self.title_template)
        template = Template(template_str)
        
        context = {
            'notification': notification,
            'metadata': notification.metadata,
            **self.variables,
            **notification.variables
        }
        
        return template.render(**context)
    
    def render_message(self, notification: Notification, channel: str = 'default') -> str:
        """Render the notification message."""
        template_str = self.channel_specific.get(channel, {}).get('message', self.message_template)
        template = Template(template_str)
        
        context = {
            'notification': notification,
            'metadata': notification.metadata,
            **self.variables,
            **notification.variables
        }
        
        return template.render(**context)


class TemplateManager:
    """Manages notification templates."""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir
        self.templates: Dict[str, NotificationTemplate] = {}
        self.jinja_env = None
        
        if template_dir and os.path.exists(template_dir):
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Load default templates
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default notification templates."""
        
        # Service Started Template
        self.templates['service_started'] = NotificationTemplate(
            name='service_started',
            title_template='🟢 Service Started: {{ metadata.service_name }}',
            message_template='Service "{{ metadata.service_name }}" has been started successfully.',
            channel_specific={
                'email': {
                    'title': '[WakeDock] Service Started: {{ metadata.service_name }}',
                    'message': '''
                    <p>The service <strong>{{ metadata.service_name }}</strong> has been started successfully.</p>
                    
                    {% if metadata.container_id %}
                    <p><strong>Container ID:</strong> {{ metadata.container_id }}</p>
                    {% endif %}
                    
                    {% if metadata.metrics %}
                    <h3>Service Metrics:</h3>
                    <ul>
                        {% for key, value in metadata.metrics.items() %}
                        <li>{{ key }}: {{ value }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    '''
                },
                'slack': {
                    'title': '🟢 Service Started',
                    'message': 'Service `{{ metadata.service_name }}` is now running'
                },
                'discord': {
                    'title': '🟢 Service Started',
                    'message': 'Service **{{ metadata.service_name }}** is now running'
                }
            },
            variables={}
        )
        
        # Service Failed Template
        self.templates['service_failed'] = NotificationTemplate(
            name='service_failed',
            title_template='🔴 Service Failed: {{ metadata.service_name }}',
            message_template='Service "{{ metadata.service_name }}" has failed{% if metadata.error_code %} with error: {{ metadata.error_code }}{% endif %}.',
            channel_specific={
                'email': {
                    'title': '[WakeDock] ALERT: Service Failed: {{ metadata.service_name }}',
                    'message': '''
                    <div style="border-left: 5px solid #dc2626; padding-left: 15px;">
                        <h2>⚠️ Service Failure Alert</h2>
                        <p>The service <strong>{{ metadata.service_name }}</strong> has failed and requires immediate attention.</p>
                        
                        {% if metadata.error_code %}
                        <p><strong>Error Code:</strong> <code>{{ metadata.error_code }}</code></p>
                        {% endif %}
                        
                        {% if metadata.stack_trace %}
                        <details>
                            <summary>Error Details</summary>
                            <pre>{{ metadata.stack_trace }}</pre>
                        </details>
                        {% endif %}
                        
                        {% if metadata.container_id %}
                        <p><strong>Container ID:</strong> {{ metadata.container_id }}</p>
                        {% endif %}
                        
                        <p><strong>Action Required:</strong> Please check the service logs and restart if necessary.</p>
                        <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    </div>
                    '''
                },
                'slack': {
                    'title': '🔴 Service Failed',
                    'message': 'Service `{{ metadata.service_name }}` has failed{% if metadata.error_code %} ({{ metadata.error_code }}){% endif %}'
                }
            },
            variables={}
        )
        
        # Health Check Failed Template
        self.templates['health_check_failed'] = NotificationTemplate(
            name='health_check_failed',
            title_template='⚠️ Health Check Failed: {{ metadata.service_name }}',
            message_template='Health check failed for service "{{ metadata.service_name }}". Service may be unresponsive.',
            channel_specific={
                'email': {
                    'title': '[WakeDock] Health Check Failed: {{ metadata.service_name }}',
                    'message': '''
                    <p>Health check has failed for service <strong>{{ metadata.service_name }}</strong>.</p>
                    <p>The service may be unresponsive or experiencing issues.</p>
                    
                    {% if metadata.metrics %}
                    <h3>Current Metrics:</h3>
                    <ul>
                        {% for key, value in metadata.metrics.items() %}
                        <li>{{ key }}: {{ value }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    <p><strong>Recommended Action:</strong> Check service logs and consider restarting the service.</p>
                    <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    '''
                }
            },
            variables={}
        )
        
        # Resource Warning Template
        self.templates['resource_warning'] = NotificationTemplate(
            name='resource_warning',
            title_template='⚠️ Resource Warning: {{ metadata.service_name }}',
            message_template='Service "{{ metadata.service_name }}" is using high resources{% if metadata.metrics.cpu_percent %} (CPU: {{ metadata.metrics.cpu_percent }}%){% endif %}{% if metadata.metrics.memory_percent %} (Memory: {{ metadata.metrics.memory_percent }}%){% endif %}.',
            channel_specific={
                'email': {
                    'title': '[WakeDock] Resource Warning: {{ metadata.service_name }}',
                    'message': '''
                    <p>Service <strong>{{ metadata.service_name }}</strong> is consuming high resources:</p>
                    
                    {% if metadata.metrics %}
                    <ul>
                        {% if metadata.metrics.cpu_percent %}
                        <li><strong>CPU Usage:</strong> {{ metadata.metrics.cpu_percent }}%</li>
                        {% endif %}
                        {% if metadata.metrics.memory_percent %}
                        <li><strong>Memory Usage:</strong> {{ metadata.metrics.memory_percent }}%</li>
                        {% endif %}
                        {% if metadata.metrics.disk_usage %}
                        <li><strong>Disk Usage:</strong> {{ metadata.metrics.disk_usage }}</li>
                        {% endif %}
                    </ul>
                    {% endif %}
                    
                    <p><strong>Action:</strong> Monitor the service and consider scaling or optimization.</p>
                    <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    '''
                }
            },
            variables={}
        )
        
        # Security Alert Template
        self.templates['security_breach'] = NotificationTemplate(
            name='security_breach',
            title_template='🚨 SECURITY ALERT: {{ notification.title }}',
            message_template='Security breach detected: {{ notification.message }}',
            channel_specific={
                'email': {
                    'title': '[WakeDock] CRITICAL SECURITY ALERT',
                    'message': '''
                    <div style="border: 3px solid #dc2626; background-color: #fef2f2; padding: 20px;">
                        <h1 style="color: #dc2626;">🚨 CRITICAL SECURITY ALERT</h1>
                        <p><strong>Security breach detected:</strong> {{ notification.message }}</p>
                        
                        {% if metadata.ip_address %}
                        <p><strong>Source IP:</strong> {{ metadata.ip_address }}</p>
                        {% endif %}
                        
                        {% if metadata.user_agent %}
                        <p><strong>User Agent:</strong> {{ metadata.user_agent }}</p>
                        {% endif %}
                        
                        {% if metadata.session_id %}
                        <p><strong>Session ID:</strong> {{ metadata.session_id }}</p>
                        {% endif %}
                        
                        <p style="color: #dc2626;"><strong>IMMEDIATE ACTION REQUIRED</strong></p>
                        <ul>
                            <li>Review access logs immediately</li>
                            <li>Check for unauthorized access</li>
                            <li>Consider revoking affected sessions</li>
                            <li>Update security measures as needed</li>
                        </ul>
                        
                        <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    </div>
                    '''
                },
                'slack': {
                    'title': '🚨 SECURITY ALERT',
                    'message': 'CRITICAL: Security breach detected - {{ notification.message }}'
                }
            },
            variables={}
        )
        
        # System Startup Template
        self.templates['system_startup'] = NotificationTemplate(
            name='system_startup',
            title_template='🚀 WakeDock System Started',
            message_template='WakeDock system has started successfully.',
            channel_specific={
                'email': {
                    'title': '[WakeDock] System Started',
                    'message': '''
                    <h2>🚀 WakeDock System Started</h2>
                    <p>The WakeDock system has started successfully.</p>
                    
                    {% if metadata.metrics %}
                    <h3>System Status:</h3>
                    <ul>
                        {% for key, value in metadata.metrics.items() %}
                        <li>{{ key }}: {{ value }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    <p>All services are initializing and will be available shortly.</p>
                    <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    '''
                }
            },
            variables={}
        )
        
        # Backup Completed Template
        self.templates['backup_completed'] = NotificationTemplate(
            name='backup_completed',
            title_template='✅ Backup Completed',
            message_template='System backup completed successfully.',
            channel_specific={
                'email': {
                    'title': '[WakeDock] Backup Completed',
                    'message': '''
                    <h2>✅ Backup Completed Successfully</h2>
                    <p>The scheduled system backup has completed successfully.</p>
                    
                    {% if metadata.metrics %}
                    <h3>Backup Details:</h3>
                    <ul>
                        {% if metadata.metrics.backup_size %}
                        <li><strong>Backup Size:</strong> {{ metadata.metrics.backup_size }}</li>
                        {% endif %}
                        {% if metadata.metrics.duration %}
                        <li><strong>Duration:</strong> {{ metadata.metrics.duration }}</li>
                        {% endif %}
                        {% if metadata.metrics.files_backed_up %}
                        <li><strong>Files Backed Up:</strong> {{ metadata.metrics.files_backed_up }}</li>
                        {% endif %}
                    </ul>
                    {% endif %}
                    
                    <p>Your data is secure and backed up.</p>
                    <p><em>Time: {{ notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') }}</em></p>
                    '''
                }
            },
            variables={}
        )
    
    def get_template(self, template_name: str) -> Optional[NotificationTemplate]:
        """Get a template by name."""
        return self.templates.get(template_name)
    
    def register_template(self, template: NotificationTemplate):
        """Register a new template."""
        self.templates[template.name] = template
    
    def load_template_from_file(self, template_name: str, file_path: str):
        """Load a template from a file."""
        if not self.jinja_env:
            raise ValueError("No template directory configured")
        
        template = self.jinja_env.get_template(file_path)
        # TODO: Parse template file and create NotificationTemplate
    
    def format_notification(self, notification: Notification, channel: str = 'default') -> tuple[str, str]:
        """Format a notification using its template."""
        template_name = notification.template or notification.type.value
        template = self.get_template(template_name)
        
        if not template:
            # Use default formatting
            return notification.title, notification.message
        
        title = template.render_title(notification, channel)
        message = template.render_message(notification, channel)
        
        return title, message
    
    def list_templates(self) -> list[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def validate_template(self, template: NotificationTemplate) -> bool:
        """Validate a template."""
        try:
            # Test rendering with dummy data
            from .types import Notification, NotificationType, NotificationPriority, NotificationMetadata
            
            dummy_notification = Notification(
                id="test",
                type=NotificationType.CUSTOM,
                priority=NotificationPriority.NORMAL,
                title="Test Title",
                message="Test Message",
                metadata=NotificationMetadata(
                    service_name="test-service",
                    metrics={"cpu_percent": 50, "memory_percent": 30}
                )
            )
            
            template.render_title(dummy_notification)
            template.render_message(dummy_notification)
            
            return True
        except Exception:
            return False
