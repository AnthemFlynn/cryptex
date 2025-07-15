"""Configuration management for Cryptex middleware."""

from .loader import (
    ConfigurationLoader,
    CryptexConfig,
    MiddlewareConfig,
    PerformanceConfig,
    SecurityPolicy,
)

# Legacy alias for backward compatibility
CodenameConfig = CryptexConfig

__all__ = [
    "CryptexConfig",
    "CodenameConfig",  # Legacy alias
    "SecurityPolicy",
    "PerformanceConfig",
    "MiddlewareConfig",
    "ConfigurationLoader",
]
