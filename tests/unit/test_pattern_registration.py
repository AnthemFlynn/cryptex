"""
Test pattern registration API.

These tests validate the new zero-config architecture with
pattern registration for advanced users.
"""

import re

import pytest

from cryptex.decorators.mcp import protect_tool
from cryptex.patterns import (
    clear_custom_patterns,
    get_all_patterns,
    get_pattern,
    list_patterns,
    register_pattern,
    register_patterns,
    unregister_pattern,
)


class TestPatternRegistration:
    """Test pattern registration API."""

    def setup_method(self):
        """Clear custom patterns before each test."""
        clear_custom_patterns()

    def test_builtin_patterns_available(self):
        """Test that built-in patterns are available."""
        patterns = list_patterns()

        # Should have common built-in patterns
        assert "openai_key" in patterns
        assert "anthropic_key" in patterns
        assert "github_token" in patterns
        assert "file_path" in patterns
        assert "database_url" in patterns

    def test_register_custom_pattern(self):
        """Test registering a custom pattern."""
        initial_count = len(list_patterns())

        register_pattern(
            name="slack_token",
            regex=r"xoxb-[0-9-a-zA-Z]{51}",
            placeholder="{{SLACK_TOKEN}}",
            description="Slack bot token",
        )

        patterns = list_patterns()
        assert len(patterns) == initial_count + 1
        assert "slack_token" in patterns

        # Check pattern details
        pattern = get_pattern("slack_token")
        assert pattern is not None
        assert pattern.name == "slack_token"
        assert pattern.placeholder_template == "{{SLACK_TOKEN}}"
        assert pattern.description == "Slack bot token"

    def test_register_pattern_with_compiled_regex(self):
        """Test registering pattern with pre-compiled regex."""
        compiled_regex = re.compile(r"discord-[a-f0-9]{32}")

        register_pattern(
            name="discord_token", regex=compiled_regex, placeholder="{{DISCORD_TOKEN}}"
        )

        pattern = get_pattern("discord_token")
        assert pattern is not None
        assert pattern.pattern == compiled_regex

    def test_register_pattern_validation(self):
        """Test pattern registration validation."""
        # Empty name should fail
        with pytest.raises(ValueError, match="Pattern name cannot be empty"):
            register_pattern("", r"test", "{{TEST}}")

        # Empty placeholder should fail
        with pytest.raises(ValueError, match="Placeholder cannot be empty"):
            register_pattern("test", r"test", "")

        # Invalid regex should fail
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            register_pattern("test", r"[invalid", "{{TEST}}")

    def test_duplicate_pattern_registration(self):
        """Test that duplicate patterns are rejected."""
        register_pattern("test_pattern", r"test-\d+", "{{TEST}}")

        # Attempting to register same name should fail
        with pytest.raises(
            ValueError, match="Pattern 'test_pattern' already registered"
        ):
            register_pattern("test_pattern", r"other-\d+", "{{OTHER}}")

    def test_unregister_pattern(self):
        """Test pattern unregistration."""
        register_pattern("temp_pattern", r"temp-\d+", "{{TEMP}}")
        assert "temp_pattern" in list_patterns()

        # Unregister should work
        result = unregister_pattern("temp_pattern")
        assert result is True
        assert "temp_pattern" not in list_patterns()

        # Unregistering non-existent pattern should return False
        result = unregister_pattern("nonexistent")
        assert result is False

    def test_bulk_registration(self):
        """Test bulk pattern registration."""
        register_patterns(
            slack_token=(r"xoxb-[0-9-a-zA-Z]{51}", "{{SLACK_TOKEN}}"),
            discord_token=(
                r"[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}",
                "{{DISCORD_TOKEN}}",
            ),
        )

        patterns = list_patterns()
        assert "slack_token" in patterns
        assert "discord_token" in patterns

    def test_get_all_patterns(self):
        """Test retrieving all patterns."""
        register_pattern("custom_test", r"custom-\d+", "{{CUSTOM}}")

        all_patterns = get_all_patterns()
        pattern_names = [p.name for p in all_patterns]

        # Should include built-ins and custom
        assert "openai_key" in pattern_names
        assert "custom_test" in pattern_names

    @pytest.mark.asyncio
    async def test_custom_pattern_with_decorator(self):
        """Test using custom patterns with decorators."""
        # Register custom pattern
        register_pattern(
            name="test_api_key",
            regex=r"testkey-[a-f0-9]{16}",
            placeholder="{{TEST_API_KEY}}",
        )

        # Use in decorator
        @protect_tool(secrets=["test_api_key"])
        async def test_tool(api_key: str) -> str:
            return f"API call with: {api_key}"

        # Test with matching key
        test_key = "testkey-abcdef1234567890"
        result = await test_tool(test_key)

        # Should be sanitized
        assert test_key not in result
        assert "TEST_API_KEY" in result

    @pytest.mark.asyncio
    async def test_mixed_builtin_and_custom_patterns(self):
        """Test using both built-in and custom patterns together."""
        # Register custom pattern
        register_pattern(
            name="custom_token", regex=r"ct-[0-9]{8}", placeholder="{{CUSTOM_TOKEN}}"
        )

        # Use both built-in and custom in decorator
        @protect_tool(secrets=["openai_key", "custom_token"])
        async def mixed_tool(openai_key: str, custom_token: str) -> str:
            return f"OpenAI: {openai_key}, Custom: {custom_token}"

        openai_key = "sk-" + "x" * 48
        custom_token = "ct-12345678"

        result = await mixed_tool(openai_key, custom_token)

        # Both should be sanitized
        assert openai_key not in result
        assert custom_token not in result
        assert "OPENAI_API_KEY" in result
        assert "CUSTOM_TOKEN" in result

    def test_clear_custom_patterns(self):
        """Test clearing all custom patterns."""
        # Register some custom patterns
        register_pattern("temp1", r"temp1-\d+", "{{TEMP1}}")
        register_pattern("temp2", r"temp2-\d+", "{{TEMP2}}")

        patterns_before = list_patterns()
        assert "temp1" in patterns_before
        assert "temp2" in patterns_before

        # Clear custom patterns
        clear_custom_patterns()

        patterns_after = list_patterns()
        assert "temp1" not in patterns_after
        assert "temp2" not in patterns_after

        # Built-ins should still be there
        assert "openai_key" in patterns_after
