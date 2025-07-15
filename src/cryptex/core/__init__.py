"""Core functionality for Cryptex secrets isolation."""

from .api import protect_secrets, secure_session
from .exceptions import (
    CodenameError,
    ConfigError,
    CryptexError,
    SecurityError,
)  # CodenameError is legacy alias
from .manager import SecretManager

__all__ = [
    "protect_secrets",
    "secure_session",
    "SecretManager",
    "CryptexError",
    "CodenameError",  # Legacy alias
    "SecurityError",
    "ConfigError",
]
