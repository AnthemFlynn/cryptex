"""Core security tests that don't require external dependencies."""

import asyncio
import re

import pytest

from cryptex_ai.core.engine import SecretPattern, TemporalIsolationEngine
from cryptex_ai.core.exceptions import SanitizationError


class TestCoreSecurityFeatures:
    """Test core security features."""

    @pytest.mark.asyncio
    async def test_basic_sanitization(self):
        """Test basic secret sanitization."""
        engine = TemporalIsolationEngine()

        data = {"api_key": "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234"}
        result = await engine.sanitize_for_ai(data)

        assert result.data != data
        assert "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234" not in str(
            result.data
        )
        assert "{{OPENAI_API_KEY}}" in str(result.data)

    @pytest.mark.asyncio
    async def test_input_validation_success(self):
        """Test successful input validation."""
        engine = TemporalIsolationEngine(max_string_length=100)

        data = {"message": "Hello world"}
        result = await engine.sanitize_for_ai(data)

        assert result.data == data

    @pytest.mark.asyncio
    async def test_input_validation_failure(self):
        """Test input validation failure."""
        engine = TemporalIsolationEngine(max_string_length=50)

        data = {"message": "x" * 100}  # Exceeds limit

        with pytest.raises(SanitizationError) as exc_info:
            await engine.sanitize_for_ai(data)

        assert "exceeds maximum limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_traceback_sanitization(self):
        """Test traceback sanitization."""
        engine = TemporalIsolationEngine()

        try:
            raise ValueError(
                "Error with sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
            )
        except ValueError as e:
            sanitized = await engine.sanitize_traceback(e)

            # Should not contain the API key
            assert "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234" not in str(
                sanitized
            )

    def test_pattern_compilation(self):
        """Test pattern compilation."""
        engine = TemporalIsolationEngine()

        # Should have compiled patterns
        assert len(engine._compiled_patterns) > 0
        assert "openai_key" in engine._compiled_patterns
        assert "anthropic_key" in engine._compiled_patterns

    def test_add_remove_patterns(self):
        """Test adding and removing patterns."""
        engine = TemporalIsolationEngine()
        initial_count = len(engine._compiled_patterns)

        # Add pattern
        pattern = SecretPattern(
            name="test_pattern",
            pattern=re.compile(r"test_\d+"),
            placeholder_template="{{TEST_SECRET}}",
            description="Test pattern",
        )
        engine.add_pattern(pattern)

        assert len(engine._compiled_patterns) == initial_count + 1
        assert "test_pattern" in engine._compiled_patterns

        # Remove pattern
        removed = engine.remove_pattern("test_pattern")
        assert removed is True
        assert len(engine._compiled_patterns) == initial_count
        assert "test_pattern" not in engine._compiled_patterns

    def test_cache_operations(self):
        """Test cache operations with reader-writer locks."""
        engine = TemporalIsolationEngine()

        # Test cache stats (uses read lock)
        stats = engine.get_cache_stats()
        assert isinstance(stats, dict)
        assert "cached_contexts" in stats

        # Test cache clearing (uses write lock)
        cleared = engine.clear_all_contexts()
        assert cleared >= 0

    @pytest.mark.asyncio
    async def test_nested_data_validation(self):
        """Test validation of nested data structures."""
        engine = TemporalIsolationEngine(max_string_length=20)

        nested_data = {
            "level1": {"level2": ["short", "x" * 30]}  # Second string exceeds limit
        }

        with pytest.raises(SanitizationError) as exc_info:
            await engine.sanitize_for_ai(nested_data)

        assert "String at root.level1.level2[1]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_performance_validation(self):
        """Test that security features don't severely impact performance."""
        import time

        engine = TemporalIsolationEngine()

        # Test data with secrets
        test_data = {
            "api_key": "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234",
            "message": "Process this data",
        }

        start_time = time.time()
        result = await engine.sanitize_for_ai(test_data)
        duration = time.time() - start_time

        # Should complete quickly (under 100ms)
        assert duration < 0.1
        assert result.data is not None
        assert "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234" not in str(
            result.data
        )


class TestSecurityIntegration:
    """Test security feature integration."""

    @pytest.mark.asyncio
    async def test_full_security_pipeline(self):
        """Test complete security pipeline."""
        engine = TemporalIsolationEngine(
            max_data_size=1024, max_string_length=512, max_cache_size=100
        )

        # Test with various secret types
        test_data = {
            "openai_key": "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234",
            "anthropic_key": "sk-ant-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567abc890def123ghi456jkl789mno012pqr345stu678vwx901",
            "github_token": "ghp_abc123def456ghi789jkl012mno345pqr678stu",
            "file_path": "/Users/sensitive/project/secrets.txt",
            "database_url": "postgres://user:pass@localhost/db",
            "message": "Process this data",
        }

        # Sanitize
        result = await engine.sanitize_for_ai(test_data)

        # Verify all secrets are replaced
        result_str = str(result.data)
        assert "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234" not in result_str
        assert (
            "sk-ant-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567abc890def123ghi456jkl789mno012pqr345stu678vwx901"
            not in result_str
        )
        assert "ghp_abc123def456ghi789jkl012mno345pqr678stu" not in result_str
        assert "/Users/sensitive/project/secrets.txt" not in result_str
        assert "postgres://user:pass@localhost/db" not in result_str

        # Verify placeholders are present
        assert "{{OPENAI_API_KEY}}" in result_str
        assert "{{ANTHROPIC_API_KEY}}" in result_str
        assert "{{GITHUB_TOKEN}}" in result_str
        assert "{RESOLVE:FILE_PATH:" in result_str  # Uses hash-based placeholder
        assert "{{DATABASE_URL}}" in result_str

        # Verify non-secret data is unchanged
        assert result.data["message"] == "Process this data"

        # Test resolution
        resolved = await engine.resolve_for_execution(result.data, result.context_id)
        assert (
            resolved.data["openai_key"]
            == "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        )
        assert resolved.resolved_count >= 4  # Should have resolved multiple secrets

    @pytest.mark.asyncio
    async def test_concurrent_security_operations(self):
        """Test security under concurrent operations."""
        engine = TemporalIsolationEngine()

        async def sanitize_data(data_id: int):
            data = {
                "id": data_id,
                "secret": f"sk-{data_id:048d}",  # Different secret per task
            }
            result = await engine.sanitize_for_ai(data)
            return result

        # Run concurrent sanitization
        tasks = [sanitize_data(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Verify all results are properly sanitized
        for i, result in enumerate(results):
            assert result.data["id"] == i
            assert f"sk-{i:048d}" not in str(result.data)
            assert "{{OPENAI_API_KEY}}" in str(result.data)

    def test_security_error_handling(self):
        """Test error handling in security operations."""
        engine = TemporalIsolationEngine()

        # Test invalid pattern removal
        removed = engine.remove_pattern("nonexistent_pattern")
        assert removed is False

        # Test cache operations
        context_existed = engine.clear_context("nonexistent_context")
        assert context_existed is False

        # Test stats access
        stats = engine.get_cache_stats()
        assert isinstance(stats, dict)
        assert stats["cached_contexts"] >= 0
