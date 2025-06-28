"""
Data formatting utilities for WakeDock
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import humanize


class FormattingUtils:
    """Utility class for data formatting"""
    
    @staticmethod
    def format_bytes(bytes_value: int, binary: bool = True) -> str:
        """Format bytes into human-readable format
        
        Args:
            bytes_value: Number of bytes
            binary: Use binary (1024) or decimal (1000) units
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        if bytes_value == 0:
            return "0 B"
        
        base = 1024 if binary else 1000
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'] if not binary else ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
        
        unit_index = 0
        size = float(bytes_value)
        
        while size >= base and unit_index < len(units) - 1:
            size /= base
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """Format duration in seconds into human-readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "2h 30m 15s")
        """
        if seconds < 0:
            return "0s"
        
        seconds = int(seconds)
        
        if seconds == 0:
            return "0s"
        
        units = [
            ('d', 86400),  # days
            ('h', 3600),   # hours
            ('m', 60),     # minutes
            ('s', 1)       # seconds
        ]
        
        parts = []
        for unit_name, unit_seconds in units:
            if seconds >= unit_seconds:
                unit_count = seconds // unit_seconds
                seconds %= unit_seconds
                parts.append(f"{unit_count}{unit_name}")
        
        return ' '.join(parts)
    
    @staticmethod
    def format_uptime(seconds: Union[int, float]) -> str:
        """Format uptime in seconds into human-readable format
        
        Args:
            seconds: Uptime in seconds
            
        Returns:
            Formatted string (e.g., "2 days, 3 hours")
        """
        if seconds <= 0:
            return "Not running"
        
        try:
            return humanize.naturaldelta(timedelta(seconds=int(seconds)))
        except:
            # Fallback if humanize is not available
            return FormattingUtils.format_duration(seconds)
    
    @staticmethod
    def format_timestamp(timestamp: Union[str, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format timestamp into human-readable format
        
        Args:
            timestamp: Timestamp as string or datetime object
            format_str: Format string for output
            
        Returns:
            Formatted timestamp string
        """
        if isinstance(timestamp, str):
            try:
                # Try to parse ISO format with timezone
                if timestamp.endswith('Z'):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(timestamp)
            except ValueError:
                return timestamp  # Return original if can't parse
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return str(timestamp)
        
        return dt.strftime(format_str)
    
    @staticmethod
    def format_relative_time(timestamp: Union[str, datetime]) -> str:
        """Format timestamp as relative time (e.g., "2 hours ago")
        
        Args:
            timestamp: Timestamp as string or datetime object
            
        Returns:
            Relative time string
        """
        if isinstance(timestamp, str):
            try:
                if timestamp.endswith('Z'):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(timestamp)
                # Convert to naive datetime for comparison
                dt = dt.replace(tzinfo=None)
            except ValueError:
                return timestamp
        elif isinstance(timestamp, datetime):
            dt = timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp
        else:
            return str(timestamp)
        
        try:
            return humanize.naturaltime(dt)
        except:
            # Fallback calculation
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
                days = diff.days
                return f"{days} day{'s' if days != 1 else ''} ago"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Format a decimal value as percentage
        
        Args:
            value: Decimal value (0.0 to 1.0 or 0 to 100)
            decimal_places: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        # If value is between 0 and 1, assume it's a decimal percentage
        if 0 <= value <= 1:
            percentage = value * 100
        else:
            percentage = value
        
        return f"{percentage:.{decimal_places}f}%"
    
    @staticmethod
    def format_cpu_usage(usage: float) -> str:
        """Format CPU usage percentage
        
        Args:
            usage: CPU usage as percentage
            
        Returns:
            Formatted CPU usage string with color indication
        """
        formatted = FormattingUtils.format_percentage(usage)
        
        # Add status indication
        if usage < 50:
            status = "low"
        elif usage < 80:
            status = "medium"
        else:
            status = "high"
        
        return f"{formatted} ({status})"
    
    @staticmethod
    def format_memory_usage(used: int, total: int) -> str:
        """Format memory usage
        
        Args:
            used: Used memory in bytes
            total: Total memory in bytes
            
        Returns:
            Formatted memory usage string
        """
        if total == 0:
            return "0 / 0"
        
        used_formatted = FormattingUtils.format_bytes(used)
        total_formatted = FormattingUtils.format_bytes(total)
        percentage = (used / total) * 100
        
        return f"{used_formatted} / {total_formatted} ({percentage:.1f}%)"
    
    @staticmethod
    def format_json(data: Any, indent: int = 2) -> str:
        """Format data as pretty-printed JSON
        
        Args:
            data: Data to format
            indent: Indentation level
            
        Returns:
            Formatted JSON string
        """
        try:
            return json.dumps(data, indent=indent, default=str, ensure_ascii=False)
        except TypeError:
            return str(data)
    
    @staticmethod
    def format_list(items: List[Any], separator: str = ", ", max_items: int = 5) -> str:
        """Format a list of items as a string
        
        Args:
            items: List of items to format
            separator: Separator between items
            max_items: Maximum number of items to show before truncating
            
        Returns:
            Formatted list string
        """
        if not items:
            return "None"
        
        str_items = [str(item) for item in items]
        
        if len(str_items) <= max_items:
            return separator.join(str_items)
        else:
            shown_items = str_items[:max_items]
            remaining = len(str_items) - max_items
            return separator.join(shown_items) + f" and {remaining} more"
    
    @staticmethod
    def format_port_list(ports: List[Dict[str, Any]]) -> str:
        """Format a list of port mappings
        
        Args:
            ports: List of port dictionaries
            
        Returns:
            Formatted port string
        """
        if not ports:
            return "No ports exposed"
        
        port_strings = []
        for port in ports:
            container_port = port.get('container_port')
            host_port = port.get('host_port')
            protocol = port.get('protocol', 'tcp')
            
            if host_port:
                port_strings.append(f"{host_port}:{container_port}/{protocol}")
            else:
                port_strings.append(f"{container_port}/{protocol}")
        
        return ", ".join(port_strings)
    
    @staticmethod
    def format_labels(labels: Dict[str, str], max_length: int = 100) -> str:
        """Format container labels for display
        
        Args:
            labels: Dictionary of labels
            max_length: Maximum length of output string
            
        Returns:
            Formatted labels string
        """
        if not labels:
            return "No labels"
        
        # Filter out internal labels
        display_labels = {k: v for k, v in labels.items() if not k.startswith('wakedock.')}
        
        if not display_labels:
            return "No custom labels"
        
        label_strings = [f"{k}={v}" for k, v in display_labels.items()]
        joined = ", ".join(label_strings)
        
        if len(joined) <= max_length:
            return joined
        else:
            return joined[:max_length - 3] + "..."
    
    @staticmethod
    def format_status(status: str) -> str:
        """Format container status with appropriate styling
        
        Args:
            status: Container status
            
        Returns:
            Formatted status string
        """
        status_lower = status.lower()
        
        status_map = {
            'running': 'Running ✅',
            'stopped': 'Stopped ⏹️',
            'paused': 'Paused ⏸️',
            'restarting': 'Restarting 🔄',
            'exited': 'Exited ❌',
            'dead': 'Dead 💀',
            'created': 'Created 🆕'
        }
        
        return status_map.get(status_lower, status.title())
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize a name for use in URLs or file names
        
        Args:
            name: Name to sanitize
            
        Returns:
            Sanitized name
        """
        # Remove or replace invalid characters
        sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '-', name)
        # Remove multiple consecutive dashes
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing dashes
        sanitized = sanitized.strip('-')
        
        return sanitized.lower()
    
    @staticmethod
    def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """Truncate a string to a maximum length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated
            
        Returns:
            Truncated string
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_command(command: Union[str, List[str]]) -> str:
        """Format a command for display
        
        Args:
            command: Command as string or list
            
        Returns:
            Formatted command string
        """
        if isinstance(command, list):
            return " ".join(command)
        elif isinstance(command, str):
            return command
        else:
            return str(command)


# Global instance for easy access
formatting_utils = FormattingUtils()
