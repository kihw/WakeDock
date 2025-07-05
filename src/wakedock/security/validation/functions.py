"""
Simple validation functions for backward compatibility.
"""

from .config import SecurityConfig
from .exceptions import ValidationError
from .types import ServiceName, DockerImage, Email, FilePath, Password
from .utils import sanitize_html


def validate_service_name(name: str) -> bool:
    """Validate service name using simple boolean return."""
    try:
        ServiceName.validate(name)
        return True
    except ValidationError:
        return False


def validate_docker_image(image: str) -> bool:
    """Validate Docker image name using simple boolean return."""
    try:
        DockerImage.validate(image)
        return True
    except ValidationError:
        return False


def validate_email(email: str) -> bool:
    """Validate email address using simple boolean return."""
    try:
        Email.validate(email)
        return True
    except ValidationError:
        return False


def validate_path(path: str) -> bool:
    """Validate file path using simple boolean return."""
    try:
        FilePath.validate(path)
        return True
    except ValidationError:
        return False


def validate_password_strength(password: str) -> dict:
    """Validate password strength and return detailed feedback."""
    try:
        Password.validate(password)
        return {
            "is_valid": True,
            "score": 100,
            "requirements": {
                "min_length": True,
                "uppercase": True,
                "lowercase": True,
                "numbers": True,
                "special_chars": True
            },
            "is_common": False
        }
    except ValidationError as e:
        # Analyze what requirements are met
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        # Check if it's a common password
        is_common = any(blocked in password.lower() for blocked in SecurityConfig.PASSWORD_BLACKLIST)
        
        # Calculate score
        score = 0
        if len(password) >= SecurityConfig.MIN_PASSWORD_LENGTH:
            score += 25
        if has_upper:
            score += 20
        if has_lower:
            score += 20
        if has_digit:
            score += 20
        if has_special:
            score += 15
        
        return {
            "is_valid": False,
            "score": score,
            "requirements": {
                "min_length": len(password) >= SecurityConfig.MIN_PASSWORD_LENGTH,
                "uppercase": has_upper,
                "lowercase": has_lower,
                "numbers": has_digit,
                "special_chars": has_special
            },
            "is_common": is_common,
            "error": str(e)
        }
