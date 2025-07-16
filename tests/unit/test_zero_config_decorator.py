"""
Test zero-config decorator behavior.

These tests validate that decorators work without any configuration files
or explicit configuration, using sensible defaults from the engine.
"""

import pytest

from cryptex.decorators.mcp import protect_tool


class TestZeroConfigDecorator:
    """Test that decorators work with zero configuration."""

    @pytest.mark.asyncio
    async def test_decorator_works_without_config(self):
        """Test that @protect_tool works without any configuration."""
        
        @protect_tool(secrets=["openai_key"])
        async def test_tool(api_key: str) -> str:
            return f"Using key: {api_key}"
        
        # Use a proper OpenAI key pattern (sk- + 48 chars)
        fake_key = "sk-" + "x" * 48
        result = await test_tool(fake_key)
        
        # The result should be sanitized
        assert fake_key not in result
        assert "{{" in result or "API_KEY" in result

    @pytest.mark.asyncio
    async def test_decorator_with_real_openai_pattern(self):
        """Test decorator with a real OpenAI API key pattern."""
        
        @protect_tool(secrets=["openai_key"])
        async def ai_tool(openai_key: str) -> str:
            return f"Making AI call with: {openai_key}"
        
        # Use a realistic OpenAI key pattern
        fake_key = "sk-" + "x" * 48
        result = await ai_tool(fake_key)
        
        # Should be sanitized
        assert fake_key not in result
        assert "{{" in result

    @pytest.mark.asyncio
    async def test_decorator_multiple_secrets(self):
        """Test decorator with multiple secret types."""
        
        @protect_tool(secrets=["api_key", "file_path"])
        async def multi_secret_tool(api_key: str, file_path: str) -> str:
            return f"API: {api_key}, File: {file_path}"
        
        fake_key = "sk-" + "y" * 48
        fake_path = "/Users/testuser/secret.txt"
        
        result = await multi_secret_tool(fake_key, fake_path)
        
        # Both should be sanitized
        assert fake_key not in result
        assert fake_path not in result

    def test_sync_decorator_works_without_config(self):
        """Test that sync functions also work without config."""
        
        @protect_tool(secrets=["api_key"])
        def sync_tool(api_key: str) -> str:
            return f"Sync processing: {api_key}"
        
        fake_key = "sk-" + "z" * 48
        result = sync_tool(fake_key)
        
        # Should be sanitized
        assert fake_key not in result