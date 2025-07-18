"""
Basic integration tests moved from original test_basic.py

Note: This file will be deprecated once proper unit tests are in place.
These tests verify basic functionality and imports work correctly.
"""

import pytest

from cryptex_ai import SecretManager, protect_secrets, secure_session


class TestBasicIntegration:
    """Basic integration tests for core functionality."""

    def test_imports(self):
        """Test that basic imports work."""
        assert protect_secrets is not None
        assert secure_session is not None
        assert SecretManager is not None

    def test_version(self):
        """Test that version is accessible."""
        import cryptex_ai

        assert hasattr(cryptex_ai, "__version__")
        assert cryptex_ai.__version__ == "0.3.1"

    @pytest.mark.asyncio
    async def test_secret_manager_init(self):
        """Test SecretManager initialization."""
        manager = SecretManager()
        await manager.initialize()
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_secure_session(self):
        """Test secure_session context manager."""
        async with secure_session() as session:
            assert isinstance(session, SecretManager)

    def test_protect_secrets_decorator(self):
        """Test protect_secrets decorator basic functionality."""

        @protect_secrets(["api_key"])
        def sync_function(data: str) -> str:
            return f"processed: {data}"

        result = sync_function("test")
        assert result == "processed: test"

    @pytest.mark.asyncio
    async def test_protect_secrets_async(self):
        """Test protect_secrets decorator with async functions."""

        @protect_secrets(["api_key"])
        async def async_function(data: str) -> str:
            return f"processed: {data}"

        result = await async_function("test")
        assert result == "processed: test"
