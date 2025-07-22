"""
Unit Tests for protect_secrets Decorator

Tests the @protect_secrets decorator in isolation.
Focuses on decorator-specific functionality and behavior.

Test Coverage:
- Decorator initialization and configuration
- Function wrapping (sync and async)
- Parameter validation
- Error handling and edge cases
- Integration with UniversalProtection class
"""

import asyncio

import pytest

from cryptex_ai.decorators.protect_secrets import (
    UniversalProtection,
    protect_all,
    protect_api_keys,
    protect_database,
    protect_files,
    protect_secrets,
    protect_tokens,
)
from tests.fixtures.secret_samples import get_sample_secret
from tests.fixtures.test_helpers import create_test_function_with_capture


class TestProtectSecretsDecorator:
    """Test the main @protect_secrets decorator."""

    def test_decorator_with_no_arguments(self):
        """Test decorator can be called without arguments."""

        @protect_secrets()
        def test_function(data: str) -> str:
            return f"processed: {data}"

        result = test_function("test data")
        assert "processed: test data" in str(result)

    def test_decorator_with_secret_types(self):
        """Test decorator accepts secret type list."""

        @protect_secrets(["openai_key", "database_url"])
        def test_function(api_key: str, db_url: str) -> str:
            return f"API: {api_key}, DB: {db_url}"

        # Function should be wrapped without error
        assert hasattr(test_function, "__wrapped__")

    def test_decorator_with_auto_detect_disabled(self):
        """Test decorator with auto-detection disabled."""

        @protect_secrets(["openai_key"], auto_detect=False)
        def test_function(api_key: str) -> str:
            return f"Using: {api_key}"

        # Should wrap successfully
        assert callable(test_function)

    def test_decorator_with_custom_engine(self):
        """Test decorator accepts custom engine."""
        from cryptex_ai.core.engine import TemporalIsolationEngine

        custom_engine = TemporalIsolationEngine()

        @protect_secrets(["openai_key"], engine=custom_engine)
        def test_function(api_key: str) -> str:
            return api_key

        # Should wrap successfully
        assert callable(test_function)

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""

        @protect_secrets(["openai_key"])
        def example_function(api_key: str) -> str:
            """Example function docstring."""
            return api_key

        # Should preserve name and docstring
        assert example_function.__name__ == "example_function"
        assert "Example function docstring" in example_function.__doc__


class TestAsyncFunctionDecorating:
    """Test decorator behavior with async functions."""

    @pytest.mark.asyncio
    async def test_async_function_decoration(self):
        """Test decorating async functions."""

        @protect_secrets(["openai_key"])
        async def async_function(api_key: str) -> str:
            return f"async result: {api_key}"

        result = await async_function(get_sample_secret("openai_key"))
        assert "async result" in str(result)

    @pytest.mark.asyncio
    async def test_async_function_with_await(self):
        """Test async function with internal awaits."""

        @protect_secrets(["openai_key"])
        async def async_function_with_await(api_key: str) -> str:
            await asyncio.sleep(0.001)  # Simulate async work
            return f"completed: {api_key}"

        result = await async_function_with_await(get_sample_secret("openai_key"))
        assert "completed" in str(result)


class TestSyncFunctionDecorating:
    """Test decorator behavior with sync functions."""

    def test_sync_function_decoration(self):
        """Test decorating sync functions."""

        @protect_secrets(["database_url"])
        def sync_function(db_url: str) -> str:
            return f"connected to: {db_url}"

        result = sync_function(get_sample_secret("database_url"))
        assert "connected to" in str(result)

    def test_sync_function_with_blocking_operations(self):
        """Test sync function with blocking operations."""
        import time

        @protect_secrets(["openai_key"])
        def blocking_function(api_key: str) -> str:
            time.sleep(0.001)  # Simulate blocking work
            return f"processed: {api_key}"

        result = blocking_function(get_sample_secret("openai_key"))
        assert "processed" in str(result)


class TestUniversalProtectionClass:
    """Test the UniversalProtection class directly."""

    def test_universal_protection_initialization(self):
        """Test UniversalProtection class initialization."""
        protection = UniversalProtection(
            engine=None, secrets=["openai_key"], auto_detect=True
        )

        assert protection.secrets == ["openai_key"]
        assert protection.auto_detect is True
        assert protection._engine is None
        assert protection._initialized is False

    @pytest.mark.asyncio
    async def test_ensure_initialized_creates_engine(self):
        """Test that _ensure_initialized creates engine when needed."""
        protection = UniversalProtection(
            engine=None, secrets=["openai_key"], auto_detect=True
        )

        await protection._ensure_initialized()

        assert protection._engine is not None
        assert protection._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_with_existing_engine(self):
        """Test _ensure_initialized with pre-provided engine."""
        from cryptex_ai.core.engine import TemporalIsolationEngine

        existing_engine = TemporalIsolationEngine()

        protection = UniversalProtection(
            engine=existing_engine, secrets=["openai_key"], auto_detect=True
        )

        await protection._ensure_initialized()

        assert protection._engine is existing_engine
        assert protection._initialized is True

    @pytest.mark.asyncio
    async def test_protect_call_with_sync_function(self):
        """Test protect_call method with sync function."""
        test_function, capture = create_test_function_with_capture()
        capture.set_return_value("sync result")

        protection = UniversalProtection(
            engine=None, secrets=["openai_key"], auto_detect=False
        )

        result = await protection.protect_call(test_function, "arg1", "arg2")

        # Function should have been called with real arguments
        assert capture.received_args == ("arg1", "arg2")
        assert "sync result" in str(result)

    @pytest.mark.asyncio
    async def test_protect_call_with_async_function(self):
        """Test protect_call method with async function."""

        async def async_function(arg1: str, arg2: str) -> str:
            return f"async: {arg1}, {arg2}"

        protection = UniversalProtection(
            engine=None, secrets=["openai_key"], auto_detect=False
        )

        result = await protection.protect_call(async_function, "test1", "test2")

        assert "async: test1, test2" in str(result)


class TestConvenienceDecorators:
    """Test convenience decorator functions."""

    def test_protect_files_decorator(self):
        """Test protect_files convenience decorator."""

        @protect_files()
        def file_function(file_path: str) -> str:
            return f"processing: {file_path}"

        result = file_function(get_sample_secret("file_path"))
        assert "processing" in str(result)

    def test_protect_api_keys_decorator(self):
        """Test protect_api_keys convenience decorator."""

        @protect_api_keys()
        def api_function(api_key: str) -> str:
            return f"using: {api_key}"

        result = api_function(get_sample_secret("openai_key"))
        assert "using" in str(result)

    def test_protect_tokens_decorator(self):
        """Test protect_tokens convenience decorator."""

        @protect_tokens()
        def token_function(token: str) -> str:
            return f"authenticated: {token}"

        result = token_function(get_sample_secret("github_token"))
        assert "authenticated" in str(result)

    def test_protect_database_decorator(self):
        """Test protect_database convenience decorator."""

        @protect_database()
        def db_function(db_url: str) -> str:
            return f"connected: {db_url}"

        result = db_function(get_sample_secret("database_url"))
        assert "connected" in str(result)

    def test_protect_all_decorator(self):
        """Test protect_all convenience decorator."""

        @protect_all()
        def comprehensive_function(api_key: str, db_url: str) -> str:
            return f"API: {api_key}, DB: {db_url}"

        result = comprehensive_function(
            get_sample_secret("openai_key"), get_sample_secret("database_url")
        )
        assert "API:" in str(result) and "DB:" in str(result)


class TestErrorHandling:
    """Test error handling in decorator."""

    def test_decorator_with_invalid_secret_types(self):
        """Test decorator behavior with invalid secret types."""

        # Should not raise during decoration
        @protect_secrets(["nonexistent_pattern"])
        def test_function(data: str) -> str:
            return data

        # Should still be callable (validation happens at runtime)
        assert callable(test_function)

    def test_decorator_with_empty_secret_list(self):
        """Test decorator with empty secrets list."""

        @protect_secrets([])
        def test_function(data: str) -> str:
            return data

        result = test_function("test")
        assert "test" in str(result)

    @pytest.mark.asyncio
    async def test_function_that_raises_exception(self):
        """Test decorated function that raises exception."""

        @protect_secrets(["openai_key"])
        def failing_function(api_key: str) -> str:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function(get_sample_secret("openai_key"))

    @pytest.mark.asyncio
    async def test_async_function_that_raises_exception(self):
        """Test decorated async function that raises exception."""

        @protect_secrets(["openai_key"])
        async def failing_async_function(api_key: str) -> str:
            raise RuntimeError("Async test error")

        with pytest.raises(RuntimeError, match="Async test error"):
            await failing_async_function(get_sample_secret("openai_key"))


class TestEventLoopHandling:
    """Test event loop handling in sync functions."""

    def test_sync_function_in_existing_event_loop(self):
        """Test sync function decoration when event loop exists."""

        @protect_secrets(["openai_key"])
        def sync_in_loop(api_key: str) -> str:
            return f"processed: {api_key}"

        # This test runs in pytest's event loop
        result = sync_in_loop(get_sample_secret("openai_key"))
        assert "processed" in str(result)

    def test_sync_function_without_event_loop(self):
        """Test sync function when no event loop is running."""

        # This is harder to test directly since pytest runs in event loop
        # But the decorator should handle both cases gracefully
        @protect_secrets(["database_url"])
        def standalone_function(db_url: str) -> str:
            return f"standalone: {db_url}"

        result = standalone_function(get_sample_secret("database_url"))
        assert "standalone" in str(result)
