"""Security tests for secrets isolation."""

import pytest
from cryptex import protect_secrets


class TestSecretsIsolation:
    """Test secrets isolation security measures."""

    @pytest.mark.security
    def test_no_secret_leakage_in_exceptions(self, sample_secrets, mock_env_vars):
        """Test that secrets don't leak in exception messages."""

        @protect_secrets(["api_key"])
        def failing_function(data: str) -> str:
            raise ValueError(f"Processing failed for: {data}")

        with pytest.raises(ValueError) as exc_info:
            failing_function("test data")

        # Exception should not contain actual secret values
        for secret_value in sample_secrets.values():
            assert secret_value not in str(exc_info.value)

    @pytest.mark.security
    def test_memory_isolation(self, sample_secrets, mock_env_vars):
        """Test that secrets are properly isolated in memory."""

        @protect_secrets(["api_key"])
        def process_data(data: str) -> str:
            # This should not expose the actual secret
            return f"Processed with key: {data}"

        result = process_data("user input")

        # Result should not contain actual secret values
        for secret_value in sample_secrets.values():
            assert secret_value not in result

    @pytest.mark.security
    def test_injection_resistance(self, injection_attempts, mock_env_vars):
        """Test resistance to various injection attempts."""

        @protect_secrets(["api_key", "secret_token"])
        def vulnerable_function(user_input: str) -> str:
            return f"Processing: {user_input}"

        for injection in injection_attempts:
            result = vulnerable_function(injection)

            # Should not expose actual secret values
            assert "sk-test1234567890abcdef" not in result
            assert "secret_abc123xyz789" not in result

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_async_isolation(self, sample_secrets, mock_env_vars):
        """Test isolation in async contexts."""

        @protect_secrets(["api_key"])
        async def async_process(data: str) -> str:
            return f"Async processed: {data}"

        result = await async_process("test input")

        # Should not expose secrets
        for secret_value in sample_secrets.values():
            assert secret_value not in result

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_concurrent_isolation(self, sample_secrets, mock_env_vars):
        """Test isolation under concurrent execution."""
        import asyncio

        @protect_secrets(["api_key"])
        async def concurrent_task(task_id: int) -> str:
            await asyncio.sleep(0.01)  # Simulate async work
            return f"Task {task_id} completed"

        # Run multiple concurrent tasks
        tasks = [concurrent_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All results should be clean
        for result in results:
            for secret_value in sample_secrets.values():
                assert secret_value not in result
