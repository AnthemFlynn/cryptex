"""Core functionality for Cryptex secrets isolation."""

from .api import protect_secrets, secure_session
from .manager import SecretManager
from .exceptions import CryptexError, CodenameError, SecurityError, ConfigError  # CodenameError is legacy alias

__all__ = [
    "protect_secrets",
    "secure_session",
    "SecretManager", 
    "CryptexError",
    "CodenameError",  # Legacy alias
    "SecurityError",
    "ConfigError",
]