"""Tests for security improvements implemented in the security-improvements branch."""

import pytest

from cryptex.core.engine import TemporalIsolationEngine
from cryptex.core.exceptions import SanitizationError
from cryptex.fastapi.middleware import CryptexMiddleware
from cryptex.fastmcp.middleware import FastMCPCryptexMiddleware


class TestTracebackSanitization:
    """Test traceback sanitization to prevent information leakage."""

    @pytest.mark.asyncio
    async def test_sanitize_traceback_removes_sensitive_paths(self):
        """Test that traceback sanitization removes sensitive file paths."""
        engine = TemporalIsolationEngine()

        # Create an exception with sensitive file path
        try:
            raise ValueError(
                "Test error from /Users/sensitive/api_key_sk-abc123/script.py"
            )
        except ValueError as e:
            sanitized_error = await engine.sanitize_traceback(e)

            # Should not contain sensitive paths
            assert "/Users/sensitive" not in str(sanitized_error)
            assert "api_key_sk-abc123" not in str(sanitized_error)

    @pytest.mark.asyncio
    async def test_sanitize_traceback_removes_line_numbers(self):
        """Test that traceback sanitization removes line numbers."""
        engine = TemporalIsolationEngine()

        try:
            raise RuntimeError("Error at line 42 in secret_processor.py")
        except RuntimeError as e:
            sanitized_error = await engine.sanitize_traceback(e)
            sanitized_str = str(sanitized_error)

            # Should not contain specific line numbers
            assert "line 42" not in sanitized_str
            assert "line <redacted>" in sanitized_str or "line" not in sanitized_str

    @pytest.mark.asyncio
    async def test_sanitize_traceback_no_traceback(self):
        """Test traceback sanitization when no traceback is present."""
        engine = TemporalIsolationEngine()

        error = ValueError("Simple error")
        sanitized_error = await engine.sanitize_traceback(error)

        # Should return the original error if no traceback
        assert str(sanitized_error) == str(error)


class TestInputValidation:
    """Test input validation and DoS protection."""

    @pytest.mark.asyncio
    async def test_input_size_validation_success(self):
        """Test that normal-sized input passes validation."""
        engine = TemporalIsolationEngine(max_data_size=1024, max_string_length=512)

        normal_data = {"key": "value", "data": "x" * 100}
        result = await engine.sanitize_for_ai(normal_data)

        assert result.data == normal_data

    @pytest.mark.asyncio
    async def test_input_size_validation_failure(self):
        """Test that oversized input fails validation."""
        engine = TemporalIsolationEngine(max_data_size=100, max_string_length=50)

        oversized_data = {"key": "value", "data": "x" * 1000}

        with pytest.raises(SanitizationError) as exc_info:
            await engine.sanitize_for_ai(oversized_data)

        assert "exceeds maximum limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_string_length_validation_failure(self):
        """Test that oversized strings fail validation."""
        engine = TemporalIsolationEngine(max_string_length=50)

        long_string = "x" * 100

        with pytest.raises(SanitizationError) as exc_info:
            await engine.sanitize_for_ai(long_string)

        assert "String at root length" in str(exc_info.value)
        assert "exceeds maximum limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_nested_string_validation(self):
        """Test validation of strings in nested data structures."""
        engine = TemporalIsolationEngine(max_string_length=50)

        nested_data = {"level1": {"level2": ["short", "x" * 100, "also_short"]}}

        with pytest.raises(SanitizationError) as exc_info:
            await engine.sanitize_for_ai(nested_data)

        assert "String at root.level1.level2[1]" in str(exc_info.value)


class TestPatternCompilation:
    """Test regex pattern pre-compilation for performance."""

    def test_patterns_are_compiled_on_init(self):
        """Test that patterns are compiled during initialization."""
        engine = TemporalIsolationEngine()

        # Should have compiled patterns
        assert len(engine._compiled_patterns) > 0

        # Should have patterns for default secret types
        assert "openai_key" in engine._compiled_patterns
        assert "anthropic_key" in engine._compiled_patterns

    def test_add_pattern_compiles_immediately(self):
        """Test that adding a pattern compiles it immediately."""
        import re

        from cryptex.core.engine import SecretPattern

        engine = TemporalIsolationEngine()
        initial_count = len(engine._compiled_patterns)

        new_pattern = SecretPattern(
            name="test_pattern",
            pattern=re.compile(r"test_\d+"),
            placeholder_template="{{TEST_SECRET}}",
            description="Test pattern",
        )

        engine.add_pattern(new_pattern)

        # Should have one more compiled pattern
        assert len(engine._compiled_patterns) == initial_count + 1
        assert "test_pattern" in engine._compiled_patterns

    def test_remove_pattern_removes_compilation(self):
        """Test that removing a pattern removes its compilation."""
        import re

        from cryptex.core.engine import SecretPattern

        engine = TemporalIsolationEngine()

        # Add a pattern
        new_pattern = SecretPattern(
            name="temp_pattern",
            pattern=re.compile(r"temp_\d+"),
            placeholder_template="{{TEMP_SECRET}}",
            description="Temporary pattern",
        )
        engine.add_pattern(new_pattern)

        # Verify it's compiled
        assert "temp_pattern" in engine._compiled_patterns

        # Remove it
        removed = engine.remove_pattern("temp_pattern")

        # Should be removed from compiled patterns
        assert removed is True
        assert "temp_pattern" not in engine._compiled_patterns


class TestReaderWriterLocks:
    """Test reader-writer locks for better concurrency."""

    def test_cache_stats_uses_read_lock(self):
        """Test that cache stats uses read lock for concurrent access."""
        engine = TemporalIsolationEngine()

        # This should not block or cause issues
        stats = engine.get_cache_stats()

        assert isinstance(stats, dict)
        assert "cached_contexts" in stats
        assert "cache_utilization" in stats

    def test_concurrent_cache_operations(self):
        """Test concurrent cache operations work properly."""
        import threading
        import time

        engine = TemporalIsolationEngine()
        results = []

        def read_stats():
            for _ in range(10):
                stats = engine.get_cache_stats()
                results.append(stats["cached_contexts"])
                time.sleep(0.001)

        def clear_cache():
            time.sleep(0.005)
            engine.clear_all_contexts()

        # Start concurrent operations
        reader_thread = threading.Thread(target=read_stats)
        writer_thread = threading.Thread(target=clear_cache)

        reader_thread.start()
        writer_thread.start()

        reader_thread.join()
        writer_thread.join()

        # Should have completed without deadlocks
        assert len(results) == 10


class TestMiddlewareRequestLimits:
    """Test request/response size limits in middleware."""

    def test_fastapi_middleware_request_size_limit(self):
        """Test FastAPI middleware request size limit."""
        from starlette.applications import Starlette

        app = Starlette()
        middleware = CryptexMiddleware(
            app=app,
            max_request_size=100,  # Very small limit for testing
            max_response_size=100,
        )

        # Middleware should have the configured limits
        assert middleware.max_request_size == 100
        assert middleware.max_response_size == 100

    def test_fastmcp_middleware_request_size_limit(self):
        """Test FastMCP middleware request size limit."""
        middleware = FastMCPCryptexMiddleware(
            max_request_size=100, max_response_size=100
        )

        # Should have the configured limits
        assert middleware.max_request_size == 100
        assert middleware.max_response_size == 100

    @pytest.mark.asyncio
    async def test_fastmcp_request_size_validation(self):
        """Test that FastMCP middleware validates request size."""
        from cryptex.fastmcp.middleware import MCPRequest

        middleware = FastMCPCryptexMiddleware(max_request_size=100)
        await middleware.initialize()

        # Create a request with large parameters
        large_request = MCPRequest(
            method="test_method",
            params={"data": "x" * 1000},  # Large data
        )

        with pytest.raises(Exception) as exc_info:
            await middleware._sanitize_request(large_request)

        assert "exceeds limit" in str(exc_info.value)


class TestSecurityFeatureIntegration:
    """Test integration of all security features."""

    @pytest.mark.asyncio
    async def test_engine_with_all_security_features(self):
        """Test engine with all security features enabled."""
        engine = TemporalIsolationEngine(
            max_data_size=1024,
            max_string_length=512,
            max_cache_size=100,
            enable_background_cleanup=True,
        )

        # Test normal operation
        data = {"api_key": "sk-test123", "message": "Hello world"}
        result = await engine.sanitize_for_ai(data)

        assert result.data != data  # Should be sanitized
        assert "sk-test123" not in str(result.data)

        # Test traceback sanitization
        try:
            raise ValueError("Error with sk-test123 in message")
        except ValueError as e:
            sanitized_error = await engine.sanitize_traceback(e)
            assert "sk-test123" not in str(sanitized_error)

    @pytest.mark.asyncio
    async def test_performance_under_security_constraints(self):
        """Test that security features don't severely impact performance."""
        import time

        engine = TemporalIsolationEngine(
            max_data_size=10 * 1024,  # 10KB limit
            max_string_length=1024,  # 1KB string limit
        )

        # Test data within limits
        test_data = {"key": "value", "data": "x" * 512}

        start_time = time.time()
        result = await engine.sanitize_for_ai(test_data)
        duration = time.time() - start_time

        # Should complete quickly even with validation
        assert duration < 0.1  # 100ms max
        assert result.data is not None
