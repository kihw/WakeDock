"""
WakeDock CLI commands.
Command-line interface for managing WakeDock services and configurations.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import click
import yaml
import logging

from ..config import get_settings
from ..core.orchestrator import DockerOrchestrator
from ..core.caddy import caddy_manager
from ..core.monitoring import MonitoringService

logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """WakeDock - Docker service orchestration and management."""
    
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose


@cli.group()
@click.pass_context
def service(ctx):
    """Manage services."""
    pass


@service.command('list')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def list_services(ctx, format: str):
    """List all services."""
    async def _list():
        orchestrator = DockerOrchestrator()
        services = await orchestrator.list_services()
        
        if format == 'json':
            click.echo(json.dumps(services, indent=2, default=str))
        elif format == 'yaml':
            click.echo(yaml.dump(services, default_flow_style=False))
        else:
            # Table format
            if not services:
                click.echo("No services found.")
                return
            
            click.echo(f"{'ID':<20} {'Name':<15} {'Status':<10} {'Subdomain':<20} {'Last Accessed'}")
            click.echo("-" * 80)
            for service in services:
                last_accessed = service.get('last_accessed')
                if last_accessed:
                    last_accessed = last_accessed.strftime('%Y-%m-%d %H:%M')
                else:
                    last_accessed = 'Never'
                
                click.echo(
                    f"{service['id']:<20} {service['name']:<15} "
                    f"{service['status']:<10} {service['subdomain']:<20} {last_accessed}"
                )
    
    asyncio.run(_list())


@service.command('show')
@click.argument('service_id')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']), default='yaml')
@click.pass_context
def show_service(ctx, service_id: str, format: str):
    """Show detailed service information."""
    async def _show():
        orchestrator = DockerOrchestrator()
        service = await orchestrator.get_service(service_id)
        
        if not service:
            click.echo(f"Service {service_id} not found.", err=True)
            sys.exit(1)
        
        if format == 'json':
            click.echo(json.dumps(service, indent=2, default=str))
        else:
            click.echo(yaml.dump(service, default_flow_style=False))
    
    asyncio.run(_show())


@service.command('start')
@click.argument('service_id')
@click.option('--wait', '-w', is_flag=True, help='Wait for service to be healthy')
@click.pass_context
def start_service(ctx, service_id: str, wait: bool):
    """Start a service."""
    async def _start():
        orchestrator = DockerOrchestrator()
        
        try:
            result = await orchestrator.wake_service(service_id)
            if result:
                click.echo(f"✅ Service {service_id} started successfully.")
                
                if wait:
                    click.echo("Waiting for service to be healthy...")
                    # Wait for health check
                    import time
                    max_wait = 60  # 60 seconds
                    waited = 0
                    while waited < max_wait:
                        service = await orchestrator.get_service(service_id)
                        if service and service.get('status') == 'running':
                            click.echo("✅ Service is healthy.")
                            break
                        time.sleep(2)
                        waited += 2
                    else:
                        click.echo("⚠️ Service started but health check timed out.")
            else:
                click.echo(f"❌ Failed to start service {service_id}.", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error starting service: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_start())


@service.command('stop')
@click.argument('service_id')
@click.pass_context
def stop_service(ctx, service_id: str):
    """Stop a service."""
    async def _stop():
        orchestrator = DockerOrchestrator()
        
        try:
            result = await orchestrator.sleep_service(service_id)
            if result:
                click.echo(f"✅ Service {service_id} stopped successfully.")
            else:
                click.echo(f"❌ Failed to stop service {service_id}.", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error stopping service: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_stop())


@service.command('restart')
@click.argument('service_id')
@click.pass_context
def restart_service(ctx, service_id: str):
    """Restart a service."""
    async def _restart():
        orchestrator = DockerOrchestrator()
        
        try:
            # Stop first
            await orchestrator.sleep_service(service_id)
            click.echo(f"🔄 Service {service_id} stopped.")
            
            # Then start
            result = await orchestrator.wake_service(service_id)
            if result:
                click.echo(f"✅ Service {service_id} restarted successfully.")
            else:
                click.echo(f"❌ Failed to restart service {service_id}.", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error restarting service: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_restart())


@service.command('logs')
@click.argument('service_id')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--tail', '-t', default=100, help='Number of lines to show from end')
@click.pass_context
def service_logs(ctx, service_id: str, follow: bool, tail: int):
    """Show service logs."""
    async def _logs():
        orchestrator = DockerOrchestrator()
        service = await orchestrator.get_service(service_id)
        
        if not service:
            click.echo(f"Service {service_id} not found.", err=True)
            sys.exit(1)
        
        container_id = service.get('container_id')
        if not container_id:
            click.echo(f"Service {service_id} is not running.", err=True)
            sys.exit(1)
        
        try:
            if orchestrator.client:
                container = orchestrator.client.containers.get(container_id)
                
                if follow:
                    for line in container.logs(stream=True, follow=True, tail=tail):
                        click.echo(line.decode('utf-8').rstrip())
                else:
                    logs = container.logs(tail=tail).decode('utf-8')
                    click.echo(logs)
            else:
                click.echo("Docker client not available.", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error getting logs: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_logs())


@cli.group()
def config():
    """Configuration management."""
    pass


@config.command('show')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']), default='yaml')
def show_config(format: str):
    """Show current configuration."""
    settings = get_settings()
    
    # Convert to dict for serialization
    config_dict = settings.dict()
    
    if format == 'json':
        click.echo(json.dumps(config_dict, indent=2, default=str))
    else:
        click.echo(yaml.dump(config_dict, default_flow_style=False))


@config.command('validate')
@click.option('--config-file', '-c', help='Path to configuration file to validate')
def validate_config(config_file: Optional[str]):
    """Validate configuration."""
    try:
        if config_file:
            # Validate specific file
            config_path = Path(config_file)
            if not config_path.exists():
                click.echo(f"Configuration file {config_file} not found.", err=True)
                sys.exit(1)
            
            # Try to load and validate
            with open(config_path) as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Validate using Pydantic model
            try:
                from ..config import Settings
                Settings(**config_data)
                click.echo(f"✅ Configuration file {config_file} is valid.")
            except ImportError:
                # Fallback to basic validation
                if isinstance(config_data, dict):
                    click.echo(f"✅ Configuration file {config_file} has valid syntax.")
                else:
                    click.echo(f"❌ Configuration file {config_file} is invalid: not a valid dict", err=True)
                    sys.exit(1)
            except Exception as e:
                click.echo(f"❌ Configuration file {config_file} validation failed: {e}", err=True)
                sys.exit(1)
        else:
            # Validate current configuration
            settings = get_settings()
            click.echo("✅ Current configuration is valid.")
    
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}", err=True)
        sys.exit(1)


@cli.group()
def caddy():
    """Caddy proxy management."""
    pass


@caddy.command('reload')
def reload_caddy():
    """Reload Caddy configuration."""
    async def _reload():
        try:
            success = await caddy_manager.reload_config()
            if success:
                click.echo("✅ Caddy configuration reloaded successfully.")
            else:
                click.echo("❌ Failed to reload Caddy configuration.", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error reloading Caddy: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_reload())


@caddy.command('status')
def caddy_status():
    """Show Caddy status."""
    async def _status():
        try:
            status = await caddy_manager.get_status()
            click.echo(f"Caddy Status: {status}")
        except Exception as e:
            click.echo(f"❌ Error getting Caddy status: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_status())


@cli.group()
def system():
    """System management."""
    pass


@system.command('status')
def system_status():
    """Show system status."""
    async def _status():
        try:
            orchestrator = DockerOrchestrator()
            monitoring = MonitoringService()
            
            # Get services status
            services = await orchestrator.list_services()
            running_count = len([s for s in services if s.get('status') == 'running'])
            
            # Get system metrics
            metrics = await monitoring.get_system_metrics()
            
            click.echo("=== WakeDock System Status ===")
            click.echo(f"Services: {len(services)} total, {running_count} running")
            click.echo(f"Docker: {'✅ Connected' if orchestrator.client else '❌ Not connected'}")
            
            if metrics:
                click.echo(f"CPU Usage: {metrics.get('cpu_percent', 'N/A')}%")
                click.echo(f"Memory Usage: {metrics.get('memory_percent', 'N/A')}%")
                click.echo(f"Disk Usage: {metrics.get('disk_percent', 'N/A')}%")
        
        except Exception as e:
            click.echo(f"❌ Error getting system status: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_status())


@system.command('health')
def health_check():
    """Perform health check."""
    async def _health():
        try:
            orchestrator = DockerOrchestrator()
            
            # Check Docker connection
            if not orchestrator.client:
                click.echo("❌ Docker connection failed")
                sys.exit(1)
            
            # Check services
            services = await orchestrator.list_services()
            unhealthy_services = []
            
            for service in services:
                if service.get('status') == 'running':
                    # Check service health using Docker health check
                    try:
                        container_id = service.get('id')
                        if container_id:
                            container = orchestrator.client.containers.get(container_id)
                            health_state = container.attrs.get('State', {}).get('Health', {})
                            
                            if health_state:
                                health_status = health_state.get('Status', 'unknown')
                                if health_status not in ['healthy', 'starting']:
                                    unhealthy_services.append(service)
                                    click.echo(f"⚠️ Service {service.get('name', 'unknown')} is {health_status}")
                            else:
                                # No health check configured, assume healthy if running
                                click.echo(f"ℹ️ Service {service.get('name', 'unknown')} running (no health check configured)")
                    except Exception as e:
                        click.echo(f"⚠️ Could not check health for service {service.get('name', 'unknown')}: {e}")
                        unhealthy_services.append(service)
            
            if unhealthy_services:
                click.echo(f"⚠️ {len(unhealthy_services)} unhealthy services found")
                for service in unhealthy_services:
                    click.echo(f"  - {service['name']}")
                sys.exit(1)
            else:
                click.echo("✅ All systems healthy")
        
        except Exception as e:
            click.echo(f"❌ Health check failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_health())


if __name__ == '__main__':
    cli()
