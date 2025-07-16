"""Core functionality for Cryptex secrets isolation."""

from .api import protect_secrets, secure_session
from .exceptions import (
    ConfigError,
    CryptexError,
    SecurityError,
)
from .manager import SecretManager

__all__ = [
    "protect_secrets",
    "secure_session",
    "SecretManager",
    "CryptexError",
    "SecurityError",
    "ConfigError",
]
