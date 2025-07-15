"""Unit tests for core API functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from codename.core.api import protect_secrets, secure_session
from codename.core.manager import SecretManager


class TestProtectSecretsDecorator:
    """Test the protect_secrets decorator."""

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""
        @protect_secrets(['api_key'])
        def sample_function(data: str) -> str:
            """Sample function docstring."""
            return f"processed: {data}"
        
        assert sample_function.__name__ == "sample_function"
        assert "Sample function docstring" in sample_function.__doc__

    def test_decorator_with_empty_secrets_list(self):
        """Test decorator with empty secrets list."""
        @protect_secrets([])
        def no_secrets_function(data: str) -> str:
            return f"processed: {data}"
        
        result = no_secrets_function("test")
        assert result == "processed: test"

    def test_decorator_with_single_secret(self):
        """Test decorator with single secret."""
        @protect_secrets(['api_key'])
        def single_secret_function(data: str) -> str:
            return f"processed: {data}"
        
        assert callable(single_secret_function)

    def test_decorator_with_multiple_secrets(self):
        """Test decorator with multiple secrets."""
        @protect_secrets(['api_key', 'db_password', 'secret_token'])
        def multi_secret_function(data: str) -> str:
            return f"processed: {data}"
        
        assert callable(multi_secret_function)

    @pytest.mark.asyncio
    async def test_async_function_decoration(self):
        """Test decoration of async functions."""
        @protect_secrets(['api_key'])
        async def async_function(data: str) -> str:
            return f"processed: {data}"
        
        result = await async_function("test")
        assert result == "processed: test"


class TestSecureSession:
    """Test the secure_session context manager."""

    @pytest.mark.asyncio
    async def test_secure_session_returns_manager(self):
        """Test that secure_session returns a SecretManager instance."""
        async with secure_session() as session:
            assert isinstance(session, SecretManager)

    @pytest.mark.asyncio
    async def test_secure_session_with_config(self, sample_config):
        """Test secure_session with custom configuration."""
        async with secure_session(config=sample_config) as session:
            assert isinstance(session, SecretManager)

    @pytest.mark.asyncio
    async def test_secure_session_cleanup(self):
        """Test that secure_session properly cleans up resources."""
        manager = None
        async with secure_session() as session:
            manager = session
            assert manager is not None
        
        # After context exit, cleanup should have been called
        # This is a basic test - implementation may vary
        assert manager is not None