"""
Common utility functions for WakeDock
"""

import re
import json
import yaml
import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path


class DataFormatter:
    """Utility class for data formatting and conversion"""
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable format"""
        if bytes_value == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        value = float(bytes_value)
        
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(value)} {units[unit_index]}"
        else:
            return f"{value:.1f} {units[unit_index]}"
    
    @staticmethod
    def parse_bytes(size_string: str) -> int:
        """Parse human readable size to bytes"""
        if not size_string:
            return 0
        
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4,
            'PB': 1024**5
        }
        
        # Extract number and unit
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([A-Z]{1,2})$', size_string.upper().strip())
        if not match:
            # Try just number (assume bytes)
            try:
                return int(float(size_string))
            except ValueError:
                return 0
        
        value, unit = match.groups()
        try:
            return int(float(value) * units.get(unit, 1))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format seconds to human readable duration"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"
    
    @staticmethod
    def format_timestamp(dt: datetime, format_type: str = "iso") -> str:
        """Format datetime to string"""
        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "human":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "relative":
            now = datetime.now()
            diff = now - dt
            
            if diff.total_seconds() < 60:
                return "just now"
            elif diff.total_seconds() < 3600:
                minutes = int(diff.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif diff.total_seconds() < 86400:
                hours = int(diff.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(diff.total_seconds() / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return dt.strftime(format_type)


class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-safe slug"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @staticmethod
    def generate_random_string(length: int = 32, use_symbols: bool = False) -> str:
        """Generate cryptographically secure random string"""
        chars = string.ascii_letters + string.digits
        if use_symbols:
            chars += "!@#$%^&*"
        
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def mask_sensitive(value: str, visible_chars: int = 4) -> str:
        """Mask sensitive string values"""
        if len(value) <= visible_chars * 2:
            return '*' * len(value)
        
        return value[:visible_chars] + '*' * (len(value) - visible_chars * 2) + value[-visible_chars:]
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix


class HashUtils:
    """Hashing and cryptographic utilities"""
    
    @staticmethod
    def md5_hash(text: str) -> str:
        """Generate MD5 hash of text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    @staticmethod
    def sha256_hash(text: str) -> str:
        """Generate SHA256 hash of text"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    @staticmethod
    def file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file checksum"""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()


class ConfigUtils:
    """Configuration file utilities"""
    
    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save data to YAML file"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
        """Save data to JSON file"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)


class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def is_valid_docker_image(image: str) -> bool:
        """Validate Docker image name format"""
        # Basic Docker image name validation
        pattern = r'^(?:[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*)?(?::[a-z0-9][a-z0-9._-]*)?$'
        return bool(re.match(pattern, image.lower()))
    
    @staticmethod
    def is_valid_subdomain(subdomain: str) -> bool:
        """Validate subdomain format"""
        if not subdomain or len(subdomain) > 63:
            return False
        
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return bool(re.match(pattern, subdomain.lower()))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for filesystem"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized.strip('.')


class RetryUtils:
    """Retry logic utilities"""
    
    @staticmethod
    async def async_retry(func, max_attempts: int = 3, delay: float = 1.0, 
                         backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
        """Async retry with exponential backoff"""
        import asyncio
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except exceptions as e:
                last_exception = e
                if attempt == max_attempts - 1:
                    break
                
                wait_time = delay * (backoff_factor ** attempt)
                await asyncio.sleep(wait_time)
        
        raise last_exception
    
    @staticmethod
    def sync_retry(func, max_attempts: int = 3, delay: float = 1.0,
                  backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
        """Synchronous retry with exponential backoff"""
        import time
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt == max_attempts - 1:
                    break
                
                wait_time = delay * (backoff_factor ** attempt)
                time.sleep(wait_time)
        
        raise last_exception
