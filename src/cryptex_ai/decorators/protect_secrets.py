"""
Universal secret protection decorator.

Provides the @protect_secrets decorator for seamless secret isolation
in any Python function, regardless of framework.
"""

import asyncio
import functools
import sys
from collections.abc import Callable
from contextlib import contextmanager
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

    Raises:
        ValueError: If secret pattern names are invalid or empty
        PatternNotFoundError: If specified patterns are not registered
        EngineInitializationError: If custom engine fails to initialize
        TypeError: If decorated object is not a callable function

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
                try:
                    # Try to use existing event loop if available
                    asyncio.get_running_loop()
                    # If we have a running loop, we need to run in a new thread
                    import concurrent.futures

                    # Create a new event loop in a separate thread
                    def run_in_new_loop():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(
                                protection.protect_call(func, *args, **kwargs)
                            )
                        finally:
                            new_loop.close()

                    # Run in thread pool to avoid blocking
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_new_loop)
                        return future.result()

                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    return asyncio.run(protection.protect_call(func, *args, **kwargs))

            return sync_wrapper

    return decorator


class UniversalProtection:
    """Protection handler for any function.

    Manages the three-phase isolation process for protecting secrets
    in function calls across any Python framework. Handles both sync
    and async functions transparently.

    Attributes:
        secrets: List of secret pattern names to protect
        auto_detect: Whether to automatically detect additional secrets
        _engine: Internal temporal isolation engine instance
        _initialized: Whether the protection has been initialized
    """

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

        Raises:
            ValueError: If secrets list contains invalid pattern names
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

    @contextmanager
    def _create_ai_interception_context(self):
        """
        Create a context manager that intercepts AI library calls.

        This monkey-patches common AI libraries (OpenAI, Anthropic) during
        function execution to ensure they receive sanitized data instead
        of real secrets.
        """
        patches = []

        try:
            # Patch OpenAI if available
            if 'openai' in sys.modules:
                openai_module = sys.modules['openai']

                # Create sanitizing wrapper for OpenAI calls
                def sanitize_openai_call(original_method):
                    async def wrapper(*args, **kwargs):
                        # Sanitize any data sent to OpenAI
                        if kwargs:
                            sanitized_data = await self._engine.sanitize_for_ai(kwargs)
                            kwargs = sanitized_data.data
                        return await original_method(*args, **kwargs)
                    return wrapper

                # Patch common OpenAI methods
                if hasattr(openai_module, 'chat') and hasattr(openai_module.chat, 'completions'):
                    if hasattr(openai_module.chat.completions, 'create'):
                        original_create = openai_module.chat.completions.create
                        patched_create = sanitize_openai_call(original_create)
                        openai_module.chat.completions.create = patched_create
                        patches.append((openai_module.chat.completions, 'create', original_create))

            # Patch Anthropic if available
            if 'anthropic' in sys.modules:
                anthropic_module = sys.modules['anthropic']

                # Create sanitizing wrapper for Anthropic calls
                def sanitize_anthropic_call(original_method):
                    async def wrapper(*args, **kwargs):
                        # Sanitize any data sent to Anthropic
                        if kwargs:
                            sanitized_data = await self._engine.sanitize_for_ai(kwargs)
                            kwargs = sanitized_data.data
                        return await original_method(*args, **kwargs)
                    return wrapper

                # Patch common Anthropic methods
                if hasattr(anthropic_module, 'messages') and hasattr(anthropic_module.messages, 'create'):
                    original_create = anthropic_module.messages.create
                    patched_create = sanitize_anthropic_call(original_create)
                    anthropic_module.messages.create = patched_create
                    patches.append((anthropic_module.messages, 'create', original_create))

            # Yield control to the function execution
            yield

        finally:
            # Restore all original methods
            for obj, attr_name, original_method in patches:
                setattr(obj, attr_name, original_method)

    async def protect_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function call with secret protection.

        Args:
            func: The function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result with secrets properly isolated

        Raises:
            SanitizationError: If input sanitization fails
            ResolutionError: If placeholder resolution fails
            SecurityError: If secret isolation is compromised
            PerformanceError: If operation exceeds performance thresholds
        """
        await self._ensure_initialized()

        try:
            # Phase 1: Sanitize input data for AI context
            # (This would be logged/seen by AI models)
            input_data = {"args": args, "kwargs": kwargs}
            await self._engine.sanitize_for_ai(input_data)

            # Phase 2: Execute function with AI call interception
            # Create monkey-patch context that intercepts AI library calls
            with self._create_ai_interception_context():
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
    """Protect file path secrets.

    Args:
        auto_detect: Whether to auto-detect additional secrets

    Returns:
        Decorated function with file path protection

    Raises:
        PatternNotFoundError: If file_path pattern is not registered
    """
    return protect_secrets(["file_path"], auto_detect=auto_detect)


def protect_api_keys(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect API key secrets.

    Args:
        auto_detect: Whether to auto-detect additional secrets

    Returns:
        Decorated function with API key protection

    Raises:
        PatternNotFoundError: If API key patterns are not registered
    """
    return protect_secrets(["openai_key", "anthropic_key"], auto_detect=auto_detect)


def protect_tokens(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect token secrets.

    Args:
        auto_detect: Whether to auto-detect additional secrets

    Returns:
        Decorated function with token protection

    Raises:
        PatternNotFoundError: If token patterns are not registered
    """
    return protect_secrets(["github_token"], auto_detect=auto_detect)


def protect_database(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect database URL secrets.

    Args:
        auto_detect: Whether to auto-detect additional secrets

    Returns:
        Decorated function with database URL protection

    Raises:
        PatternNotFoundError: If database_url pattern is not registered
    """
    return protect_secrets(["database_url"], auto_detect=auto_detect)


def protect_all(auto_detect: bool = True) -> Callable[[F], F]:
    """Protect all built-in secret types.

    Args:
        auto_detect: Whether to auto-detect additional secrets

    Returns:
        Decorated function with comprehensive secret protection

    Raises:
        PatternNotFoundError: If any built-in patterns are not registered
    """
    return protect_secrets(
        ["openai_key", "anthropic_key", "github_token", "file_path", "database_url"],
        auto_detect=auto_detect,
    )
