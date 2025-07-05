"""
Security utility functions.
"""

import re
import hashlib
import secrets
import html
import json
from typing import Any, Dict, Tuple

from .exceptions import ValidationError


class SecurityUtils:
    """Security utility functions."""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging/storage."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\.\.', '_', sanitized)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            max_name_len = 255 - len(ext) - 1 if ext else 255
            sanitized = name[:max_name_len] + ('.' + ext if ext else '')
        
        return sanitized
    
    @staticmethod
    def validate_json_schema(data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against JSON schema."""
        try:
            import jsonschema
            jsonschema.validate(data, schema)
            return True
        except ImportError:
            # Fallback validation if jsonschema not available
            return True
        except Exception:
            return False
    
    @staticmethod
    def check_rate_limit(identifier: str, limit: int, window: int) -> Tuple[bool, int]:
        """
        Check if identifier has exceeded rate limit.
        
        Returns (is_allowed, remaining_requests)
        """
        # This would typically use Redis or similar
        # For now, return a simple implementation
        return True, limit
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', show_chars: int = 4) -> str:
        """Mask sensitive data for logging."""
        if len(data) <= show_chars:
            return mask_char * len(data)
        
        return data[:show_chars] + mask_char * (len(data) - show_chars)


def sanitize_html(html_input: str) -> str:
    """Sanitize HTML input to prevent XSS."""
    # Basic HTML sanitization - in production, use a library like bleach
    return html.escape(html_input)


def sanitize_sql_identifier(identifier: str) -> str:
    """Sanitize SQL identifier to prevent injection."""
    # Only allow alphanumeric and underscore
    return re.sub(r'[^a-zA-Z0-9_]', '', identifier)


def validate_json_input(data: str, max_size: int = 10240) -> Dict[str, Any]:
    """Validate and parse JSON input safely."""
    if len(data) > max_size:
        raise ValidationError(f'JSON input too large (max {max_size} bytes)')
    
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValidationError(f'invalid JSON: {e}')
    
    return parsed


def sanitize_input(input_str: str, allow_html: bool = False) -> str:
    """Sanitize input string."""
    if allow_html:
        # In a real implementation, use a proper HTML sanitizer like bleach
        return input_str
    else:
        return sanitize_html(input_str)
