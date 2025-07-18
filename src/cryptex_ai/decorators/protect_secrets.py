"""
Universal secret protection decorator.

Provides the @protect_secrets decorator for seamless secret isolation
in any Python function, regardless of framework.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from ..core.engine import TemporalIsolationEngine
from ..patterns import get_all_patterns

F = TypeVar("F", bound=Callable[..., Any])


def protect_secrets(
    secrets: list[str] | None = None,
    auto_detect: bool = True,
    engine: TemporalIsolationEngine | None = None,
) -> Callable[[F], F]:
    """
    Universal decorator for temporal isolation protection.

    Protects any function by sanitizing input secrets for AI context
    while providing real values for function execution.

    Args:
        secrets: List of secret names/patterns to protect (e.g., ["openai_key"])
        auto_detect: Whether to auto-detect additional secrets beyond specified list
        engine: Pre-configured TemporalIsolationEngine instance

    Returns:
        Decorated function with automatic secret protection

    Examples:
        ```python
        # Basic usage - works with any framework
        @protect_secrets(["openai_key"])
        async def ai_function(prompt: str, api_key: str) -> str:
            # AI sees: ai_function("Hello", "{{OPENAI_API_KEY}}")
            # Function gets: real API key for execution
            return await openai_call(prompt, api_key)

        # Multiple secrets
        @protect_secrets(["file_path", "github_token", "database_url"])
        async def process_data(file_path: str, token: str, db_url: str) -> dict:
            # All secrets automatically protected
            with open(file_path, 'r') as f:
                data = f.read()
            result = await github_api_call(data, token)
            await save_to_database(result, db_url)
            return result

        # Custom engine
        engine = TemporalIsolationEngine(max_cache_size=1000)
        @protect_secrets(["openai_key"], engine=engine)
        async def custom_function(api_key: str) -> str:
            return await openai_call(api_key)
        ```
    """
    # Set up defaults
    if secrets is None:
        secrets = []

    def decorator(func: F) -> F:
        # Initialize protection
        protection = UniversalProtection(
            engine=engine,
            secrets=secrets,
            auto_detect=auto_detect,
        )

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                return await protection.protect_call(func, *args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                return asyncio.run(protection.protect_call(func, *args, **kwargs))

            return sync_wrapper

    return decorator


class UniversalProtection:
    """Protection handler for any function."""

    def __init__(
        self,
        engine: TemporalIsolationEngine | None,
        secrets: list[str],
        auto_detect: bool = True,
    ):
        """
        Initialize universal protection.

        Args:
            engine: Temporal isolation engine (created if None)
            secrets: List of secret names to protect
            auto_detect: Whether to auto-detect additional secrets
        """
        self.secrets = secrets
        self.auto_detect = auto_detect
        self._engine = engine
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the protection is initialized."""
        if self._initialized:
            return

        # Create engine if not provided
        if self._engine is None:
            all_patterns = get_all_patterns()
            self._engine = TemporalIsolationEngine(patterns=all_patterns)

        self._initialized = True

    async def protect_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function call with secret protection.

        Args:
            func: The function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result with secrets properly isolated
        """
        await self._ensure_initialized()

        try:
            # Phase 1: Sanitize input data for AI context
            # (This would be logged/seen by AI models)
            input_data = {"args": args, "kwargs": kwargs}
            await self._engine.sanitize_for_ai(input_data)

            # Phase 2: Execute function with original (real) values
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Phase 3: Sanitize result to prevent secret leakage
            if result is not None:
                sanitized_result = await self._engine.sanitize_for_ai(result)
                # Return the sanitized result to prevent secret leakage
                return sanitized_result.data

            return result

        except Exception as e:
            # Sanitize any errors that might contain secrets
            await self._engine.sanitize_traceback(e)
            # Re-raise the original error for normal error handling
            raise e from None


# Convenience decorators for common patterns
def protect_files(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect file path secrets."""
    return protect_secrets(["file_path"], auto_detect=auto_detect)


def protect_api_keys(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect API key secrets."""
    return protect_secrets(["openai_key", "anthropic_key"], auto_detect=auto_detect)


def protect_tokens(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect token secrets."""
    return protect_secrets(["github_token"], auto_detect=auto_detect)


def protect_database(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect database URL secrets."""
    return protect_secrets(["database_url"], auto_detect=auto_detect)


def protect_all(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect all built-in secret types."""
    return protect_secrets(
        ["openai_key", "anthropic_key", "github_token", "file_path", "database_url"],
        auto_detect=auto_detect,
    )
