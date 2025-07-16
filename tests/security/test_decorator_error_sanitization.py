"""
Test decorator error sanitization to ensure no secret leakage in decorated function exceptions.

This test validates that the @cryptex decorator properly sanitizes errors from decorated
functions, ensuring secrets never leak back to AI context.
"""

import pytest

from cryptex.config.loader import CryptexConfig
from cryptex.core.engine import TemporalIsolationEngine
from cryptex.decorators.mcp import protect_tool


class TestDecoratorErrorSanitization:
    """Test error sanitization in decorators."""

    @pytest.mark.asyncio
    async def test_mcp_tool_error_sanitization(self):
        """Test that MCP tool decorator sanitizes errors containing secrets."""
        
        # Create minimal config and engine for testing
        config = CryptexConfig()
        engine = TemporalIsolationEngine()
        
        @protect_tool(secrets=["api_key"], config=config, engine=engine)
        async def failing_tool(api_key: str, message: str) -> str:
            # This tool will fail with an error containing the real API key
            raise ValueError(f"API call failed with key {api_key}: {message}")
        
        # Test with a secret that should be sanitized
        test_api_key = "sk-test-secret-that-should-not-appear-in-errors"
        
        with pytest.raises(ValueError) as exc_info:
            await failing_tool(api_key=test_api_key, message="connection timeout")
        
        error_message = str(exc_info.value)
        
        # Verify the secret was sanitized from the error message
        assert test_api_key not in error_message, f"Secret '{test_api_key}' found in error: {error_message}"
        assert "{SANITIZED:API_KEY}" in error_message, f"Expected sanitized placeholder in error: {error_message}"

    @pytest.mark.asyncio
    async def test_mcp_tool_multiple_secrets_sanitization(self):
        """Test that multiple secret types are sanitized from errors."""
        
        config = CryptexConfig()
        engine = TemporalIsolationEngine()
        
        @protect_tool(secrets=["api_key", "database_url"], config=config, engine=engine)
        async def failing_multi_secret_tool(api_key: str, database_url: str) -> str:
            # This will fail with multiple secrets in the error
            raise ConnectionError(f"Failed to connect with {api_key} to {database_url}")
        
        test_api_key = "sk-another-test-key-for-multi-secret"
        test_db_url = "postgresql://user:secret@localhost/testdb"
        
        with pytest.raises(ConnectionError) as exc_info:
            await failing_multi_secret_tool(api_key=test_api_key, database_url=test_db_url)
        
        error_message = str(exc_info.value)
        
        # Verify both secrets were sanitized
        assert test_api_key not in error_message
        assert "secret@localhost" not in error_message  # Password part of URL
        assert "{SANITIZED:API_KEY}" in error_message
        assert "{SANITIZED:DATABASE_URL}" in error_message

    @pytest.mark.asyncio
    async def test_mcp_tool_preserves_error_type_and_traceback(self):
        """Test that error sanitization preserves exception type and traceback."""
        
        config = CryptexConfig()
        engine = TemporalIsolationEngine()
        
        @protect_tool(secrets=["api_key"], config=config, engine=engine)
        async def custom_error_tool(api_key: str) -> str:
            raise CustomTestError(f"Custom failure with {api_key}")
        
        class CustomTestError(Exception):
            pass
        
        test_api_key = "sk-custom-error-test-key"
        
        with pytest.raises(CustomTestError) as exc_info:
            await custom_error_tool(api_key=test_api_key)
        
        # Verify error type is preserved
        assert isinstance(exc_info.value, CustomTestError)
        
        # Verify traceback is preserved
        assert exc_info.value.__traceback__ is not None
        
        # Verify secret is sanitized but message structure is preserved
        error_message = str(exc_info.value)
        assert test_api_key not in error_message
        assert "Custom failure with" in error_message

    def test_mcp_tool_handles_sync_function_errors(self):
        """Test error sanitization works for synchronous decorated functions."""
        
        config = CryptexConfig()
        engine = TemporalIsolationEngine()
        
        @protect_tool(secrets=["api_key"], config=config, engine=engine)
        def sync_failing_tool(api_key: str) -> str:
            # Sync function that fails with secret in error
            raise RuntimeError(f"Sync error with key: {api_key}")
        
        test_api_key = "sk-sync-function-test-key"
        
        with pytest.raises(RuntimeError) as exc_info:
            # This will run in its own event loop since sync functions use asyncio.run()
            sync_failing_tool(api_key=test_api_key)
        
        error_message = str(exc_info.value)
        assert test_api_key not in error_message
        assert "{SANITIZED:API_KEY}" in error_message

    @pytest.mark.asyncio
    async def test_error_sanitization_with_no_secrets_in_error(self):
        """Test that normal errors without secrets pass through unchanged."""
        
        config = CryptexConfig()
        engine = TemporalIsolationEngine()
        
        @protect_tool(secrets=["api_key"], config=config, engine=engine)
        async def normal_error_tool(api_key: str, data: str) -> str:
            # Error that doesn't contain any secrets
            raise ValueError(f"Invalid data format: {data}")
        
        test_data = "malformed-json-data"
        
        with pytest.raises(ValueError) as exc_info:
            await normal_error_tool(api_key="sk-test", data=test_data)
        
        error_message = str(exc_info.value)
        
        # Normal error message should pass through unchanged
        assert f"Invalid data format: {test_data}" == error_message