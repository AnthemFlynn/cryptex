"""Exception classes for Cryptex."""

import re
import time
from typing import Any


class CryptexError(Exception):
    """
    Base exception for all Cryptex errors.

    Provides structured error information and context tracking.
    """

    def __init__(
        self,
        message: str,
        context_id: str | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        """
        Initialize Cryptex error.

        Args:
            message: Human-readable error message
            context_id: Context ID for tracking temporal isolation sessions
            error_code: Machine-readable error code for programmatic handling
            details: Additional error context and debugging information
            cause: Original exception that caused this error
        """
        super().__init__(self._sanitize_message(message))
        self.context_id = context_id
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = time.time()

        # Store original message for debugging (when safe)
        self._original_message = message

    def _sanitize_message(self, message: str) -> str:
        """Sanitize message to remove potential secrets."""
        if not message:
            return message

        # Remove OpenAI API keys
        message = re.sub(r"sk-[a-zA-Z0-9]{48}", "[OPENAI_KEY_REDACTED]", message)
        message = re.sub(
            r"sk-proj-[a-zA-Z0-9]{48}", "[OPENAI_PROJECT_KEY_REDACTED]", message
        )
        message = re.sub(r"sk-ant-[a-zA-Z0-9]{48}", "[ANTHROPIC_KEY_REDACTED]", message)

        # Remove GitHub tokens
        message = re.sub(r"ghp_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN_REDACTED]", message)
        message = re.sub(r"gho_[a-zA-Z0-9]{36}", "[GITHUB_OAUTH_REDACTED]", message)

        # Remove generic API keys (common patterns)
        message = re.sub(
            r"[a-zA-Z0-9]{32,}",
            lambda m: "[KEY_REDACTED]" if len(m.group()) >= 32 else m.group(),
            message,
        )

        # Remove file paths that might contain sensitive info
        message = re.sub(r"/[/\w\-\.]+/[/\w\-\.]+", "/[PATH_REDACTED]", message)

        return message

    def _sanitize_details(self, details: dict[str, Any]) -> dict[str, Any]:
        """Sanitize details dictionary to remove potential secrets."""
        if not details:
            return {}

        sanitized = {}
        sensitive_keys = {
            "secret_value",
            "api_key",
            "token",
            "password",
            "key",
            "auth",
            "resolved_value",
            "placeholder_value",
            "pattern_string",
            "input_data",
            "secret",
            "credential",
            "auth_token",
        }

        for key, value in details.items():
            if key in sensitive_keys:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_message(value)
            elif isinstance(value, dict):
                # Check if nested dict has sensitive keys, if so redact entirely
                if any(k in sensitive_keys for k in value.keys()):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_message(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary format for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "context_id": (
                self._sanitize_message(self.context_id) if self.context_id else None
            ),
            "error_code": self.error_code,
            "details": self._sanitize_details(self.details),
            "timestamp": self.timestamp,
            "cause": self._sanitize_message(str(self.cause)) if self.cause else None,
        }


class SecurityError(CryptexError):
    """Raised when security validation fails."""

    def __init__(self, message: str, security_level: str = "high", **kwargs):
        super().__init__(message, error_code="SECURITY_VIOLATION", **kwargs)
        self.security_level = security_level


class ConfigError(CryptexError):
    """Raised when configuration is invalid (deprecated - no config in zero-config design)."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONFIG_INVALID", **kwargs)


class SanitizationError(CryptexError):
    """Raised when sanitization fails."""

    def __init__(self, message: str, pattern_name: str | None = None, **kwargs):
        super().__init__(message, error_code="SANITIZATION_FAILED", **kwargs)
        self.pattern_name = pattern_name


class ResolutionError(CryptexError):
    """Raised when secret resolution fails."""

    def __init__(self, message: str, placeholder: str | None = None, **kwargs):
        super().__init__(message, error_code="RESOLUTION_FAILED", **kwargs)
        self.placeholder = placeholder


class IsolationError(CryptexError):
    """Raised when temporal isolation is compromised."""

    def __init__(self, message: str, isolation_phase: str | None = None, **kwargs):
        super().__init__(message, error_code="ISOLATION_BREACH", **kwargs)
        self.isolation_phase = (
            isolation_phase  # "sanitization", "processing", "resolution"
        )


class ContextError(CryptexError):
    """Raised when context management fails."""

    def __init__(self, message: str, operation: str | None = None, **kwargs):
        super().__init__(message, error_code="CONTEXT_ERROR", **kwargs)
        self.operation = operation  # "cache", "lookup", "cleanup", etc.


class PatternError(CryptexError):
    """Raised when secret pattern processing fails."""

    def __init__(self, message: str, pattern_name: str | None = None, **kwargs):
        super().__init__(message, error_code="PATTERN_ERROR", **kwargs)
        self.pattern_name = pattern_name


class EngineError(CryptexError):
    """Raised when core engine operations fail."""

    def __init__(self, message: str, operation: str | None = None, **kwargs):
        super().__init__(message, error_code="ENGINE_ERROR", **kwargs)
        self.operation = operation


class MiddlewareError(CryptexError):
    """Raised when middleware operations fail."""

    def __init__(self, message: str, middleware_type: str | None = None, **kwargs):
        super().__init__(message, error_code="MIDDLEWARE_ERROR", **kwargs)
        self.middleware_type = middleware_type  # "fastapi", "fastmcp"


class DecoratorError(CryptexError):
    """Raised when decorator operations fail."""

    def __init__(self, message: str, framework: str | None = None, **kwargs):
        super().__init__(message, error_code="DECORATOR_ERROR", **kwargs)
        self.framework = framework


class PerformanceError(CryptexError):
    """Raised when performance thresholds are exceeded."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        duration: float | None = None,
        threshold: float | None = None,
        **kwargs,
    ):
        super().__init__(message, error_code="PERFORMANCE_THRESHOLD", **kwargs)
        self.operation = operation
        self.duration = duration
        self.threshold = threshold


class FrameworkDetectionError(CryptexError):
    """Raised when framework auto-detection fails."""

    def __init__(
        self, message: str, attempted_frameworks: list[str] | None = None, **kwargs
    ):
        super().__init__(message, error_code="FRAMEWORK_DETECTION_FAILED", **kwargs)
        self.attempted_frameworks = attempted_frameworks or []


# Convenience functions for common error scenarios


def context_not_found_error(context_id: str) -> ContextError:
    """Create a standardized context not found error."""
    return ContextError(
        f"Context {context_id} not found or expired",
        context_id=context_id,
        operation="lookup",
        details={"suggestion": "Check if context has expired or was manually cleared"},
    )


def sanitization_timeout_error(
    duration: float, threshold: float = 5.0
) -> PerformanceError:
    """Create a standardized sanitization timeout error."""
    return PerformanceError(
        f"Sanitization took {duration:.2f}ms, exceeding {threshold}ms threshold",
        operation="sanitization",
        duration=duration,
        threshold=threshold,
        details={
            "suggestion": "Consider optimizing secret patterns or reducing data size"
        },
    )


def resolution_timeout_error(
    duration: float, threshold: float = 10.0
) -> PerformanceError:
    """Create a standardized resolution timeout error."""
    return PerformanceError(
        f"Resolution took {duration:.2f}ms, exceeding {threshold}ms threshold",
        operation="resolution",
        duration=duration,
        threshold=threshold,
        details={"suggestion": "Check if too many placeholders need resolution"},
    )


def invalid_pattern_error(
    pattern_name: str, pattern_string: str, regex_error: str
) -> PatternError:
    """Create a standardized invalid pattern error."""
    return PatternError(
        f"Invalid regex pattern '{pattern_name}': {regex_error}",
        pattern_name=pattern_name,
        details={
            "pattern_string": pattern_string,
            "regex_error": regex_error,
            "suggestion": "Check pattern syntax in configuration",
        },
    )


def security_breach_error(
    breach_type: str, context_id: str | None = None
) -> SecurityError:
    """Create a standardized security breach error."""
    return SecurityError(
        f"Security breach detected: {breach_type}",
        context_id=context_id,
        security_level="critical",
        details={
            "breach_type": breach_type,
            "action": "Operation blocked to prevent secret exposure",
        },
    )
