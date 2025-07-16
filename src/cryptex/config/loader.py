"""
Configuration system for Cryptex middleware.

Supports TOML configuration files and environment variable integration
for flexible middleware deployment configuration.
"""

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.engine import SecretPattern


@dataclass
class SecurityPolicy:
    """Security policy configuration for middleware."""

    enforcement_mode: str = "strict"  # strict, permissive, audit_only
    block_exposure: bool = True
    max_placeholder_age: int = 3600  # seconds
    audit_logging: bool = True
    auto_detect_secrets: bool = True

    def __post_init__(self):
        """Validate policy configuration."""
        valid_modes = {"strict", "permissive", "audit_only"}
        if self.enforcement_mode not in valid_modes:
            raise ValueError(
                f"Invalid enforcement_mode: {self.enforcement_mode}. Must be one of {valid_modes}"
            )


@dataclass
class PerformanceConfig:
    """Performance configuration for middleware."""

    cache_size: int = 10000
    sanitization_timeout_ms: int = 5
    resolution_timeout_ms: int = 10
    batch_size: int = 100
    enable_streaming: bool = True

    def __post_init__(self):
        """Validate performance configuration."""
        if self.cache_size < 0:
            raise ValueError("cache_size must be non-negative")
        if self.sanitization_timeout_ms <= 0:
            raise ValueError("sanitization_timeout_ms must be positive")
        if self.resolution_timeout_ms <= 0:
            raise ValueError("resolution_timeout_ms must be positive")


@dataclass
class MiddlewareConfig:
    """Middleware-specific configuration."""

    auto_protect_endpoints: bool = True
    auto_protect_tools: bool = True
    inject_context_headers: bool = True
    response_sanitization: bool = True
    error_sanitization: bool = True


@dataclass
class CryptexConfig:
    """Complete configuration for Cryptex middleware."""

    secret_patterns: list[SecretPattern] = field(default_factory=list)
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    middleware: MiddlewareConfig = field(default_factory=MiddlewareConfig)
    custom_settings: dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def from_toml(cls, config_path: str | Path) -> "CryptexConfig":
        """
        Load configuration from TOML file.

        Args:
            config_path: Path to TOML configuration file

        Returns:
            CryptexConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse TOML configuration: {e}") from e

        return await cls._from_dict(config_data)

    @classmethod
    async def from_env(cls, prefix: str = "CRYPTEX_") -> "CryptexConfig":
        """
        Load configuration from environment variables.

        Args:
            prefix: Prefix for environment variables

        Returns:
            CryptexConfig instance with environment-based settings
        """
        config_data = {}

        # Extract environment variables with the prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()
                config_data[config_key] = value

        return await cls._from_dict(config_data)

    @classmethod
    async def from_dict(cls, config_data: dict[str, Any]) -> "CryptexConfig":
        """
        Create configuration from dictionary.

        Args:
            config_data: Configuration dictionary

        Returns:
            CryptexConfig instance
        """
        return await cls._from_dict(config_data)

    @classmethod
    async def _from_dict(cls, config_data: dict[str, Any]) -> "CryptexConfig":
        """Internal method to create config from dictionary."""
        # Parse secret patterns
        secret_patterns = []
        secrets_config = config_data.get("secrets", {})

        if "patterns" in secrets_config:
            for pattern_data in secrets_config["patterns"]:
                try:
                    pattern = SecretPattern.from_dict(pattern_data)
                    secret_patterns.append(pattern)
                except Exception as e:
                    raise ValueError(f"Invalid secret pattern configuration: {e}") from e

        # Parse security policy
        security_data = config_data.get("security", {})
        security_policy = SecurityPolicy(
            enforcement_mode=security_data.get("enforcement_mode", "strict"),
            block_exposure=security_data.get("block_exposure", True),
            max_placeholder_age=security_data.get("max_placeholder_age", 3600),
            audit_logging=security_data.get("audit_logging", True),
            auto_detect_secrets=security_data.get("auto_detect_secrets", True),
        )

        # Parse performance config
        performance_data = config_data.get("performance", {})
        performance = PerformanceConfig(
            cache_size=performance_data.get("cache_size", 10000),
            sanitization_timeout_ms=performance_data.get("sanitization_timeout_ms", 5),
            resolution_timeout_ms=performance_data.get("resolution_timeout_ms", 10),
            batch_size=performance_data.get("batch_size", 100),
            enable_streaming=performance_data.get("enable_streaming", True),
        )

        # Parse middleware config
        middleware_data = config_data.get("middleware", {})
        middleware = MiddlewareConfig(
            auto_protect_endpoints=middleware_data.get("auto_protect_endpoints", True),
            auto_protect_tools=middleware_data.get("auto_protect_tools", True),
            inject_context_headers=middleware_data.get("inject_context_headers", True),
            response_sanitization=middleware_data.get("response_sanitization", True),
            error_sanitization=middleware_data.get("error_sanitization", True),
        )

        # Store any custom settings
        custom_settings = {
            k: v
            for k, v in config_data.items()
            if k not in {"secrets", "security", "performance", "middleware"}
        }

        config = cls(
            secret_patterns=secret_patterns,
            security_policy=security_policy,
            performance=performance,
            middleware=middleware,
            custom_settings=custom_settings,
        )

        # Validate configuration automatically
        config.validate_and_raise()

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            "secrets": {
                "patterns": [
                    {
                        "name": pattern.name,
                        "pattern": pattern.pattern.pattern,
                        "template": pattern.placeholder_template,
                        "description": pattern.description,
                    }
                    for pattern in self.secret_patterns
                ]
            },
            "security": {
                "enforcement_mode": self.security_policy.enforcement_mode,
                "block_exposure": self.security_policy.block_exposure,
                "max_placeholder_age": self.security_policy.max_placeholder_age,
                "audit_logging": self.security_policy.audit_logging,
                "auto_detect_secrets": self.security_policy.auto_detect_secrets,
            },
            "performance": {
                "cache_size": self.performance.cache_size,
                "sanitization_timeout_ms": self.performance.sanitization_timeout_ms,
                "resolution_timeout_ms": self.performance.resolution_timeout_ms,
                "batch_size": self.performance.batch_size,
                "enable_streaming": self.performance.enable_streaming,
            },
            "middleware": {
                "auto_protect_endpoints": self.middleware.auto_protect_endpoints,
                "auto_protect_tools": self.middleware.auto_protect_tools,
                "inject_context_headers": self.middleware.inject_context_headers,
                "response_sanitization": self.middleware.response_sanitization,
                "error_sanitization": self.middleware.error_sanitization,
            },
            **self.custom_settings,
        }

    def merge_with_env(self, prefix: str = "CRYPTEX_") -> "CryptexConfig":
        """
        Merge current configuration with environment variables.

        Args:
            prefix: Environment variable prefix

        Returns:
            New CryptexConfig with environment overrides
        """
        # Convert current config to dict
        config_dict = self.to_dict()

        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()

                # Handle nested keys like CRYPTEX_SECURITY_ENFORCEMENT_MODE
                key_parts = config_key.split("_")
                current_dict = config_dict

                # Navigate to the correct nested dictionary
                for part in key_parts[:-1]:
                    if part not in current_dict:
                        current_dict[part] = {}
                    current_dict = current_dict[part]

                # Set the value (with type conversion)
                final_key = key_parts[-1]
                current_dict[final_key] = _convert_env_value(value)

        # Create new config from merged dictionary
        return self.__class__.from_dict(config_dict)

    def validate(self) -> list[str]:
        """
        Validate the configuration comprehensively.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate secret patterns
        pattern_names = set()
        for i, pattern in enumerate(self.secret_patterns):
            # Check for duplicate names
            if pattern.name in pattern_names:
                errors.append(
                    f"Duplicate secret pattern name: '{pattern.name}' (pattern #{i + 1})"
                )
            pattern_names.add(pattern.name)

            # Validate pattern name
            if not pattern.name or not pattern.name.strip():
                errors.append(f"Pattern #{i + 1} has empty or invalid name")
            elif not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", pattern.name):
                errors.append(
                    f"Pattern name '{pattern.name}' contains invalid characters. Use alphanumeric and underscore only."
                )

            # Test pattern compilation and validate regex
            try:
                compiled_pattern = re.compile(pattern.pattern.pattern)

                # Warn about overly broad patterns
                if pattern.pattern.pattern in [".*", ".+", ".*?", ".+?"]:
                    errors.append(
                        f"Pattern '{pattern.name}' is too broad and will match everything"
                    )

                # Test with empty string (shouldn't match)
                if compiled_pattern.match(""):
                    errors.append(
                        f"Pattern '{pattern.name}' matches empty string - consider using anchors"
                    )

            except re.error as e:
                errors.append(f"Invalid regex in pattern '{pattern.name}': {e}")

            # Validate placeholder template
            if (
                not pattern.placeholder_template
                or not pattern.placeholder_template.strip()
            ):
                errors.append(
                    f"Pattern '{pattern.name}' has empty placeholder template"
                )

        # Validate minimum required patterns
        if not self.secret_patterns:
            errors.append(
                "No secret patterns defined. At least one pattern is recommended."
            )

        # Check for common security patterns
        pattern_types = {p.name.lower() for p in self.secret_patterns}
        recommended_patterns = {"api_key", "openai_key", "file_path", "database_url"}
        missing_recommended = recommended_patterns - pattern_types
        if missing_recommended:
            errors.append(
                f"Consider adding patterns for: {', '.join(missing_recommended)}"
            )

        # Validate security policy
        try:
            # Additional security validation beyond __post_init__
            if self.security_policy.max_placeholder_age < 60:
                errors.append(
                    "max_placeholder_age should be at least 60 seconds for proper operation"
                )
            if self.security_policy.max_placeholder_age > 86400:  # 24 hours
                errors.append(
                    "max_placeholder_age over 24 hours may pose security risks"
                )

            SecurityPolicy(**self.security_policy.__dict__)
        except ValueError as e:
            errors.append(f"Invalid security policy: {e}")

        # Validate performance config
        try:
            # Additional performance validation beyond __post_init__
            if self.performance.cache_size > 100000:
                errors.append("cache_size over 100,000 may consume excessive memory")
            if self.performance.sanitization_timeout_ms > 50:
                errors.append(
                    "sanitization_timeout_ms over 50ms may impact performance"
                )
            if self.performance.resolution_timeout_ms > 100:
                errors.append("resolution_timeout_ms over 100ms may impact performance")
            if self.performance.batch_size > 1000:
                errors.append("batch_size over 1000 may cause memory issues")

            PerformanceConfig(**self.performance.__dict__)
        except ValueError as e:
            errors.append(f"Invalid performance config: {e}")

        # Validate middleware config consistency
        if (
            not self.middleware.auto_protect_tools
            and not self.middleware.auto_protect_endpoints
        ):
            errors.append(
                "Both auto_protect_tools and auto_protect_endpoints are disabled - no protection will be applied"
            )

        if not self.middleware.response_sanitization:
            errors.append(
                "response_sanitization is disabled - secrets may leak in responses"
            )

        if not self.middleware.error_sanitization:
            errors.append(
                "error_sanitization is disabled - secrets may leak in error messages"
            )

        return errors

    def validate_and_raise(self) -> None:
        """
        Validate configuration and raise ConfigError if invalid.

        Raises:
            ConfigError: If configuration is invalid
        """
        from ..core.exceptions import ConfigError

        errors = self.validate()
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise ConfigError(error_message, details={"validation_errors": errors})


def _convert_env_value(value: str) -> str | int | float | bool:
    """Convert environment variable string to appropriate type."""
    # Try boolean conversion
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    elif value.lower() in ("false", "no", "0", "off"):
        return False

    # Try integer conversion
    try:
        return int(value)
    except ValueError:
        pass

    # Try float conversion
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value


class ConfigurationLoader:
    """Utility class for loading configurations from various sources."""

    @staticmethod
    async def load_with_fallbacks(
        config_paths: list[str | Path], env_prefix: str = "CRYPTEX_"
    ) -> CryptexConfig:
        """
        Load configuration with fallback strategy.

        Tries configuration files in order, then falls back to environment variables.

        Args:
            config_paths: List of configuration file paths to try
            env_prefix: Environment variable prefix

        Returns:
            CryptexConfig instance

        Raises:
            ValueError: If no valid configuration is found
        """
        # Try config files in order
        for config_path in config_paths:
            config_path = Path(config_path)
            if config_path.exists():
                try:
                    config = await CryptexConfig.from_toml(config_path)
                    # Merge with environment variables for overrides
                    return config.merge_with_env(env_prefix)
                except Exception:
                    continue  # Try next config file

        # Fall back to environment variables
        try:
            return await CryptexConfig.from_env(env_prefix)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from any source: {e}") from e

    @staticmethod
    async def create_default_config(output_path: str | Path) -> None:
        """
        Create a default configuration file.

        Args:
            output_path: Path where to write the default configuration
        """
        default_config = """# Cryptex Configuration File
# This file configures secret isolation for Cryptex middleware

[secrets]
# Define patterns for automatic secret detection
patterns = [
    { name = "openai_key", pattern = "sk-[a-zA-Z0-9]{48}", template = "{{OPENAI_API_KEY}}", description = "OpenAI API key" },
    { name = "anthropic_key", pattern = "sk-ant-[a-zA-Z0-9-]{95}", template = "{{ANTHROPIC_API_KEY}}", description = "Anthropic API key" },
    { name = "github_token", pattern = "ghp_[a-zA-Z0-9]{36}", template = "{{GITHUB_TOKEN}}", description = "GitHub personal access token" },
    { name = "file_path", pattern = "/(?:Users|home)/[^/\\s]+(?:/[^/\\s]*)*", template = "/{USER_HOME}/...", description = "User file system paths" },
    { name = "database_url", pattern = "(?:postgres|mysql|redis|mongodb)://[^\\s]+", template = "{{DATABASE_URL}}", description = "Database connection URLs" },
]

[security]
# Security policy configuration
enforcement_mode = "strict"  # strict, permissive, audit_only
block_exposure = true
max_placeholder_age = 3600  # seconds
audit_logging = true
auto_detect_secrets = true

[performance]
# Performance tuning
cache_size = 10000
sanitization_timeout_ms = 5
resolution_timeout_ms = 10
batch_size = 100
enable_streaming = true

[middleware]
# Middleware behavior configuration
auto_protect_endpoints = true
auto_protect_tools = true
inject_context_headers = true
response_sanitization = true
error_sanitization = true
"""

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(default_config)
