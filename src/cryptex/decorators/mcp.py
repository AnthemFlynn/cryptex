"""
FastMCP tool protection decorators.

Provides @protect_tool decorator for seamless secret isolation in FastMCP tools.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from ..config.loader import ConfigurationLoader, CryptexConfig
from ..core.engine import TemporalIsolationEngine

F = TypeVar("F", bound=Callable[..., Any])


class MCPToolProtection:
    """Protection handler for FastMCP tools."""

    def __init__(
        self,
        engine: TemporalIsolationEngine,
        config: CryptexConfig,
        secrets: list[str],
        auto_detect: bool = True,
    ):
        """
        Initialize tool protection.

        Args:
            engine: Temporal isolation engine
            config: Cryptex configuration
            secrets: List of secret names to protect
            auto_detect: Whether to auto-detect additional secrets
        """
        self.engine = engine
        self.config = config
        self.secrets = secrets
        self.auto_detect = auto_detect

    async def protect_tool_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a tool call with secret protection.

        Args:
            func: The tool function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool result with secrets properly isolated
        """
        try:
            # Phase 1: Sanitize input arguments for AI context
            (
                sanitized_args,
                sanitized_kwargs,
                context_id,
            ) = await self._sanitize_arguments(args, kwargs)

            # Phase 2: Execute tool with real values
            if asyncio.iscoroutinefunction(func):
                result = await func(
                    *args, **kwargs
                )  # Use original args with real secrets
            else:
                result = func(*args, **kwargs)

            # Phase 3: Sanitize response to prevent secret leakage
            sanitized_result = await self.engine.sanitize_response(result, context_id)

            return sanitized_result

        except Exception as e:
            # Sanitize error messages to prevent secret exposure
            sanitized_error = await self._sanitize_error(
                e, context_id if "context_id" in locals() else None
            )
            raise sanitized_error

    async def _sanitize_arguments(
        self, args: tuple, kwargs: dict
    ) -> tuple[tuple, dict, str]:
        """Sanitize function arguments and return context for tracking."""
        # Combine args and kwargs into a single data structure for processing
        all_args = {"args": args, "kwargs": kwargs}

        # Sanitize for AI consumption
        sanitized_data = await self.engine.sanitize_for_ai(all_args)

        return (
            sanitized_data.data["args"],
            sanitized_data.data["kwargs"],
            sanitized_data.context_id,
        )

    async def _sanitize_error(
        self, error: Exception, context_id: str | None
    ) -> Exception:
        """Sanitize error messages to prevent secret leakage."""
        error_message = str(error)

        if context_id:
            sanitized_message = await self.engine.sanitize_response(
                error_message, context_id
            )
        else:
            # Fallback: create new sanitization context for error
            sanitized_data = await self.engine.sanitize_for_ai(error_message)
            sanitized_message = sanitized_data.data

        # Create new exception with sanitized message
        sanitized_error = type(error)(sanitized_message)

        # Preserve traceback if possible
        if hasattr(error, "__traceback__"):
            sanitized_error.__traceback__ = error.__traceback__

        return sanitized_error


def protect_tool(
    secrets: list[str] | None = None,
    config_path: str | None = None,
    config: CryptexConfig | None = None,
    auto_detect: bool = True,
    engine: TemporalIsolationEngine | None = None,
) -> Callable[[F], F]:
    """
    Decorator to protect FastMCP tools with automatic secret isolation.

    This decorator enables seamless secret protection for FastMCP tools:
    - AI/LLM sees sanitized placeholders
    - Tool execution gets real secret values
    - Responses are sanitized before returning to AI

    Args:
        secrets: List of secret names/patterns to protect
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_detect: Whether to auto-detect secrets beyond specified list
        engine: Pre-configured TemporalIsolationEngine instance

    Returns:
        Decorated function with automatic secret protection

    Example:
        ```python
        @protect_tool(secrets=["api_key", "file_paths"])
        async def read_file_tool(file_path: str) -> str:
            # AI sees: read_file_tool("/{USER_HOME}/documents/file.txt")
            # Tool executes: with real path "/Users/john/documents/file.txt"
            with open(file_path, 'r') as f:
                return f.read()

        @protect_tool(secrets=["openai_key"])
        async def ai_completion_tool(prompt: str, api_key: str) -> str:
            # AI sees: ai_completion_tool("Hello", "{{API_KEY}}")
            # Tool executes: with real API key "sk-real-key..."
            return await openai_api_call(prompt, api_key)
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Initialize protection components
            protection = await _get_or_create_protection(
                secrets or [], config_path, config, auto_detect, engine
            )

            # Execute with protection
            return await protection.protect_tool_call(func, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we need to run the async protection in an event loop
            return asyncio.run(async_wrapper(*args, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


async def _get_or_create_protection(
    secrets: list[str],
    config_path: str | None,
    config: CryptexConfig | None,
    auto_detect: bool,
    engine: TemporalIsolationEngine | None,
) -> MCPToolProtection:
    """Get or create protection components."""
    # Load configuration
    if config is None:
        if config_path:
            config = await CryptexConfig.from_toml(config_path)
        else:
            # Try to load from default locations
            config = await ConfigurationLoader.load_with_fallbacks(
                ["cryptex.toml", "config/cryptex.toml", ".cryptex.toml"]
            )

    # Create engine if not provided
    if engine is None:
        engine = TemporalIsolationEngine(config.secret_patterns)

    return MCPToolProtection(engine, config, secrets, auto_detect)


class MCPToolRegistry:
    """Registry for tracking protected FastMCP tools."""

    def __init__(self):
        self._protected_tools: dict[str, MCPToolProtection] = {}
        self._tool_configs: dict[str, dict] = {}

    def register_tool(
        self,
        tool_name: str,
        protection: MCPToolProtection,
        metadata: dict | None = None,
    ) -> None:
        """Register a protected tool."""
        self._protected_tools[tool_name] = protection
        self._tool_configs[tool_name] = metadata or {}

    def get_tool_protection(self, tool_name: str) -> MCPToolProtection | None:
        """Get protection for a specific tool."""
        return self._protected_tools.get(tool_name)

    def list_protected_tools(self) -> list[str]:
        """List all protected tool names."""
        return list(self._protected_tools.keys())

    def get_protection_stats(self) -> dict:
        """Get statistics about protected tools."""
        return {
            "total_protected_tools": len(self._protected_tools),
            "tools": list(self._protected_tools.keys()),
            "configurations": self._tool_configs,
        }


# Global registry instance
_tool_registry = MCPToolRegistry()


def register_protected_tool(
    tool_name: str, protection: MCPToolProtection, metadata: dict | None = None
) -> None:
    """Register a protected tool in the global registry."""
    _tool_registry.register_tool(tool_name, protection, metadata)


def get_tool_registry() -> MCPToolRegistry:
    """Get the global tool registry."""
    return _tool_registry


# Convenience decorators for common use cases


def protect_file_tool(config_path: str | None = None) -> Callable[[F], F]:
    """Convenience decorator for file operation tools."""
    return protect_tool(
        secrets=["file_paths", "home_directory"],
        config_path=config_path,
        auto_detect=True,
    )


def protect_api_tool(
    api_secrets: list[str] | None = None, config_path: str | None = None
) -> Callable[[F], F]:
    """Convenience decorator for API-calling tools."""
    default_secrets = ["api_key", "openai_key", "anthropic_key", "github_token"]
    secrets = (api_secrets or []) + default_secrets

    return protect_tool(secrets=secrets, config_path=config_path, auto_detect=True)


def protect_database_tool(config_path: str | None = None) -> Callable[[F], F]:
    """Convenience decorator for database tools."""
    return protect_tool(
        secrets=["database_url", "db_password", "connection_string"],
        config_path=config_path,
        auto_detect=True,
    )
