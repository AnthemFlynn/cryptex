"""Configuration management for Cryptex middleware."""

from .loader import (
    CryptexConfig,
    SecurityPolicy,
    PerformanceConfig,
    MiddlewareConfig,
    ConfigurationLoader
)

# Legacy alias for backward compatibility
CodenameConfig = CryptexConfig

__all__ = [
    "CryptexConfig",
    "CodenameConfig",  # Legacy alias
    "SecurityPolicy", 
    "PerformanceConfig",
    "MiddlewareConfig",
    "ConfigurationLoader"
]