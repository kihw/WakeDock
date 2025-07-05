"""
Custom validation exceptions.
"""


class ValidationError(Exception):
    """Custom validation error."""
    pass


class SecurityValidationError(ValidationError):
    """Security-specific validation error."""
    pass


class InputSanitizationError(ValidationError):
    """Input sanitization error."""
    pass
