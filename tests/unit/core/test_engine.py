"""
Unit Tests for TemporalIsolationEngine

Tests the core temporal isolation engine in isolation.
Focuses on engine-specific functionality without dependencies.

Test Coverage:
- Engine initialization and configuration
- Secret detection algorithms
- Sanitization logic
- Placeholder generation
- Cache management
- Performance monitoring
"""

import asyncio
from unittest.mock import patch

import pytest

from cryptex_ai.core.engine import SanitizedData, SecretPattern, TemporalIsolationEngine
from cryptex_ai.core.exceptions import PerformanceError, SanitizationError
from tests.fixtures.secret_samples import (
    get_expected_placeholder,
    get_sample_secret,
)


class TestTemporalIsolationEngineInitialization:
    """Test engine initialization and configuration."""

    def test_engine_initializes_with_default_patterns(self):
        """Test engine initializes with default patterns."""
        engine = TemporalIsolationEngine()

        assert len(engine.patterns) > 0
        assert any(p.name == "openai_key" for p in engine.patterns)
        assert any(p.name == "database_url" for p in engine.patterns)

    def test_engine_initializes_with_custom_patterns(self):
        """Test engine accepts custom patterns."""
        custom_pattern = SecretPattern(
            name="test_pattern",
            pattern=r"test-[0-9]{4}",
            placeholder_template="{{TEST_PLACEHOLDER}}",
            description="Test pattern",
        )

        engine = TemporalIsolationEngine(patterns=[custom_pattern])

        assert len(engine.patterns) == 1
        assert engine.patterns[0].name == "test_pattern"

    def test_engine_configuration_parameters(self):
        """Test engine configuration parameters."""
        engine = TemporalIsolationEngine(
            max_cache_size=500, max_cache_age=1800, max_data_size=5 * 1024 * 1024
        )

        assert engine._max_cache_size == 500
        assert engine._max_cache_age == 1800
        assert engine._max_data_size == 5 * 1024 * 1024


class TestSecretDetection:
    """Test secret detection algorithms."""

    @pytest.mark.asyncio
    async def test_detect_openai_key(self):
        """Test OpenAI key detection."""
        engine = TemporalIsolationEngine()
        sample_key = get_sample_secret("openai_key")

        detected = await engine._detect_secrets_in_string(sample_key)

        assert len(detected) == 1
        assert detected[0].pattern_name == "openai_key"
        assert detected[0].value == sample_key

    @pytest.mark.asyncio
    async def test_detect_database_url(self):
        """Test database URL detection."""
        engine = TemporalIsolationEngine()
        sample_url = get_sample_secret("database_url")

        detected = await engine._detect_secrets_in_string(sample_url)

        assert len(detected) == 1
        assert detected[0].pattern_name == "database_url"
        assert detected[0].value == sample_url

    @pytest.mark.asyncio
    async def test_detect_multiple_secrets(self):
        """Test detection of multiple secrets in text."""
        engine = TemporalIsolationEngine()
        text = f"API key: {get_sample_secret('openai_key')}, DB: {get_sample_secret('database_url')}"

        detected = await engine._detect_secrets(text)

        assert len(detected) == 2
        pattern_names = {s.pattern_name for s in detected}
        assert "openai_key" in pattern_names
        assert "database_url" in pattern_names

    @pytest.mark.asyncio
    async def test_no_false_positives(self):
        """Test that non-secrets are not detected."""
        engine = TemporalIsolationEngine()
        non_secret = "just a regular string with no secrets"

        detected = await engine._detect_secrets_in_string(non_secret)

        assert len(detected) == 0


class TestSanitization:
    """Test sanitization logic."""

    @pytest.mark.asyncio
    async def test_sanitize_string_with_secrets(self):
        """Test string sanitization."""
        engine = TemporalIsolationEngine()
        secret = get_sample_secret("openai_key")
        text = f"Using API key: {secret}"

        result = await engine.sanitize_for_ai(text)

        assert isinstance(result, SanitizedData)
        assert secret not in result.data
        assert get_expected_placeholder("openai_key") in result.data
        assert secret in result.placeholders.values()

    @pytest.mark.asyncio
    async def test_sanitize_dict_with_secrets(self):
        """Test dictionary sanitization."""
        engine = TemporalIsolationEngine()
        secret = get_sample_secret("openai_key")
        data = {"api_key": secret, "user": "john"}

        result = await engine.sanitize_for_ai(data)

        assert result.data["user"] == "john"  # Non-secret unchanged
        assert secret not in str(result.data["api_key"])  # Secret sanitized
        assert get_expected_placeholder("openai_key") in str(result.data["api_key"])

    @pytest.mark.asyncio
    async def test_sanitize_nested_data(self):
        """Test nested data structure sanitization."""
        engine = TemporalIsolationEngine()
        secret = get_sample_secret("openai_key")
        data = {"config": {"api": {"key": secret}, "debug": True}}

        result = await engine.sanitize_for_ai(data)

        assert result.data["config"]["debug"] is True  # Non-secret unchanged
        assert secret not in str(result.data)  # Secret removed
        assert len(result.placeholders) > 0  # Placeholders recorded

    @pytest.mark.asyncio
    async def test_sanitize_empty_data(self):
        """Test sanitization of empty/None data."""
        engine = TemporalIsolationEngine()

        result_none = await engine.sanitize_for_ai(None)
        result_empty = await engine.sanitize_for_ai("")

        assert result_none.data is None
        assert result_empty.data == ""
        assert len(result_none.placeholders) == 0
        assert len(result_empty.placeholders) == 0


class TestPlaceholderGeneration:
    """Test placeholder generation logic."""

    def test_generate_placeholder_consistent_format(self):
        """Test placeholder format consistency."""
        engine = TemporalIsolationEngine()

        placeholder = engine._generate_placeholder(
            "test-secret", "test_pattern", "{{TEST_PLACEHOLDER}}"
        )

        assert placeholder == "{{TEST_PLACEHOLDER}}"
        assert placeholder.startswith("{{")
        assert placeholder.endswith("}}")

    def test_generate_placeholder_uses_template(self):
        """Test placeholder uses provided template."""
        engine = TemporalIsolationEngine()

        placeholder = engine._generate_placeholder(
            "secret-value", "custom_pattern", "{{CUSTOM_SECRET}}"
        )

        assert placeholder == "{{CUSTOM_SECRET}}"


class TestCacheManagement:
    """Test cache management functionality."""

    @pytest.mark.asyncio
    async def test_cache_context_storage(self):
        """Test context caching."""
        engine = TemporalIsolationEngine(max_cache_size=10)
        secret = get_sample_secret("openai_key")

        result = await engine.sanitize_for_ai(secret)

        # Verify context is cached
        cached_context = engine._get_cached_context(result.context_id)
        assert cached_context is not None
        assert cached_context.context_id == result.context_id

    @pytest.mark.asyncio
    async def test_cache_size_limit(self):
        """Test cache size enforcement."""
        engine = TemporalIsolationEngine(max_cache_size=2)

        # Add 3 contexts (exceeds limit)
        for i in range(3):
            await engine.sanitize_for_ai(f"secret-{i}")

        # Cache should not exceed size limit
        stats = engine.get_cache_stats()
        assert stats["cached_contexts"] <= 2

    def test_clear_context(self):
        """Test manual context clearing."""
        engine = TemporalIsolationEngine()
        context_id = "test-context-id"

        # Manually add to cache
        from cryptex_ai.core.engine import SanitizedData

        test_data = SanitizedData(data="test", context_id=context_id)
        engine._cache_context(context_id, test_data)

        # Verify it exists then clear it
        assert engine._get_cached_context(context_id) is not None
        cleared = engine.clear_context(context_id)
        assert cleared is True
        assert engine._get_cached_context(context_id) is None


class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self):
        """Test performance metrics are tracked."""
        engine = TemporalIsolationEngine()
        initial_metrics = engine.get_performance_metrics()

        await engine.sanitize_for_ai(get_sample_secret("openai_key"))

        final_metrics = engine.get_performance_metrics()
        assert (
            final_metrics["sanitization_calls"] > initial_metrics["sanitization_calls"]
        )
        assert final_metrics["secrets_detected"] > initial_metrics["secrets_detected"]

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    async def test_performance_threshold_violation(self):
        """Test performance threshold violations."""
        engine = TemporalIsolationEngine()

        # Mock slow sanitization with async coroutine
        async def slow_detect_secrets(data):
            await asyncio.sleep(0.006)  # Sleep for 6ms to exceed 5ms threshold
            return []  # Return empty list of detected secrets

        with patch.object(engine, "_detect_secrets", side_effect=slow_detect_secrets):
            try:
                await engine.sanitize_for_ai("test data")
                # If we get here, the performance error wasn't raised
                pytest.fail("Expected PerformanceError was not raised")
            except PerformanceError:
                # This is what we expect
                pass

    def test_reset_performance_metrics(self):
        """Test performance metrics reset."""
        engine = TemporalIsolationEngine()

        # Generate some metrics
        engine._update_sanitization_metrics(10.0, 2)
        initial_metrics = engine.get_performance_metrics()
        assert initial_metrics["sanitization_calls"] > 0

        # Reset and verify
        engine.reset_performance_metrics()
        reset_metrics = engine.get_performance_metrics()
        assert reset_metrics["sanitization_calls"] == 0


class TestInputValidation:
    """Test input validation and error handling."""

    @pytest.mark.asyncio
    async def test_oversized_input_rejection(self):
        """Test rejection of oversized input."""
        engine = TemporalIsolationEngine(max_data_size=100)  # Very small limit
        large_data = "x" * 1000  # Exceeds limit

        with pytest.raises(SanitizationError) as exc_info:
            await engine.sanitize_for_ai(large_data)

        assert "exceeds maximum limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_malformed_data_handling(self):
        """Test handling of malformed data."""
        engine = TemporalIsolationEngine()

        # Should not raise exceptions for unusual but valid data
        result = await engine.sanitize_for_ai([1, 2, {"key": None}])
        assert result.data is not None
