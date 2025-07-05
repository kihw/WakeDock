"""
WakeDock Security Validation Module

DEPRECATED: This module has been refactored into submodules.
Please use: from wakedock.security.validation import *

This file is kept for backward compatibility.
"""

# Import everything from the new modular structure
from .validation import *

# Backward compatibility warning
import warnings
warnings.warn(
    "Direct import from wakedock.security.validation is deprecated. "
    "Use 'from wakedock.security.validation import *' instead.",
    DeprecationWarning,
    stacklevel=2
)
