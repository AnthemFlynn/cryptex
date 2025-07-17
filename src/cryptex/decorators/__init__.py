"""
Cryptex decorators for universal secret protection.
"""

from .protect_secrets import (
    protect_all,
    protect_api_keys,
    protect_database,
    protect_files,
    protect_secrets,
    protect_tokens,
)

__all__ = [
    "protect_secrets",
    "protect_files",
    "protect_api_keys",
    "protect_tokens",
    "protect_database",
    "protect_all",
]
