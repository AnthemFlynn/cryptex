"""Exception classes for Cryptex."""


class CryptexError(Exception):
    """Base exception for all Cryptex errors."""
    pass


class SecurityError(CryptexError):
    """Raised when security validation fails."""
    pass


class ConfigError(CryptexError):
    """Raised when configuration is invalid."""
    pass


class SanitizationError(CryptexError):
    """Raised when sanitization fails."""
    pass


class ResolutionError(CryptexError):
    """Raised when secret resolution fails."""
    pass


class IsolationError(CryptexError):
    """Raised when temporal isolation is compromised."""
    pass


# Legacy aliases for backward compatibility
CodenameError = CryptexError