"""Utility functions and helpers for WakeDock."""

from .validation import (
    validate_service_name, validate_domain, validate_port,
    validate_image_name, sanitize_string, validate_email
)
from .formatting import FormattingUtils

# Create aliases for common formatting functions
format_bytes = FormattingUtils.format_bytes
format_duration = FormattingUtils.format_duration
format_timestamp = FormattingUtils.format_timestamp
truncate_string = FormattingUtils.truncate_string

# Note: slugify is not implemented, using sanitize_name instead
def slugify(text: str) -> str:
    return FormattingUtils.sanitize_name(text)
# Import docker_utils class and create aliases for the functions
from .docker_utils import DockerUtils

# Create aliases for docker utility functions
def parse_image_tag(image_name: str):
    """Parse Docker image tag from image name"""
    if ':' in image_name:
        return image_name.split(':', 1)
    return image_name, 'latest'

def build_container_name(service_name: str, prefix: str = 'wakedock'):
    """Build container name from service name"""
    return f"{prefix}-{service_name}"

def extract_port_mappings(ports_config):
    """Extract port mappings from configuration"""
    return DockerUtils().parse_container_ports(ports_config)

def validate_docker_config(config: dict):
    """Validate Docker configuration"""
    return DockerUtils().validate_service_config(config)
# Import network functions with fallback stubs
import socket

def resolve_hostname(hostname: str):
    """Resolve hostname to IP address"""
    try:
        return socket.gethostbyname(hostname)
    except:
        return None

def is_port_available(port: int, host: str = 'localhost') -> bool:
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0
    except:
        return False

def get_free_port(start_port: int = 8000, end_port: int = 9000) -> int:
    """Get a free port in the specified range"""
    for port in range(start_port, end_port):
        if is_port_available(port):
            return port
    raise RuntimeError(f"No free port found in range {start_port}-{end_port}")

async def check_url_accessible(url: str, timeout: int = 5) -> bool:
    """Check if a URL is accessible"""
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url) as response:
                return response.status < 400
    except:
        return False

__all__ = [
    # Validation
    "validate_service_name",
    "validate_domain", 
    "validate_port",
    "validate_image_name",
    "sanitize_string",
    "validate_email",
    
    # Formatting
    "format_bytes",
    "format_duration",
    "format_timestamp", 
    "truncate_string",
    "slugify",
    
    # Docker utilities
    "parse_image_tag",
    "build_container_name",
    "extract_port_mappings",
    "validate_docker_config",
    
    # Network utilities
    "is_port_available",
    "get_free_port",
    "check_url_accessible",
    "resolve_hostname"
]
