"""Main API entry points for Cryptex."""

import asyncio
from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, TypeVar

from .manager import SecretManager

F = TypeVar("F", bound=Callable[..., Any])


def protect_secrets(
    secrets: list[str],
    paths: list[str] | None = None,
    config_path: str | None = None,
) -> Callable[[F], F]:
    """
    Decorator to protect secrets in function arguments and return values.

    This is the primary API for Cryptex - it automatically sanitizes secrets
    before AI processing and resolves them during execution.

    Args:
        secrets: List of secret keys to protect
        paths: Optional list of file paths to protect
        config_path: Optional path to configuration file

    Returns:
        Decorated function with automatic secret protection

    Example:
        @protect_secrets(['api_key', 'database_url'])
        async def ai_powered_function(user_input: str) -> str:
            # AI sees: api_key="{RESOLVE:API_KEY:abc123}"
            # Execution gets: api_key="sk-real-key"
            return await ai_workflow(user_input)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # TODO: Implement actual secret protection logic
            # For now, just pass through - will be implemented in sanitization-1 task
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # TODO: Implement actual secret protection logic
            # For now, just pass through - will be implemented in sanitization-1 task
            return func(*args, **kwargs)

        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


@asynccontextmanager
async def secure_session(config_path: str | None = None):
    """
    Context manager for fine-grained secret isolation control.

    Provides direct access to sanitization and resolution operations
    for cases where decorator-based protection is insufficient.

    Args:
        config_path: Optional path to configuration file

    Yields:
        SecretManager instance for manual secret operations

    Example:
        async with secure_session() as session:
            sanitized_data = await session.sanitize_for_ai(raw_data)
            ai_result = await ai_function(sanitized_data)
            resolved_result = await session.resolve_secrets(ai_result)
    """
    manager = SecretManager(config_path=config_path)
    try:
        await manager.initialize()
        yield manager
    finally:
        await manager.cleanup()
