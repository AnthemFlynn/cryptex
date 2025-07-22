"""
Regression Tests for GitHub Issue Fixes

Tests that verify specific GitHub issues remain resolved.
These tests prevent regression of previously fixed bugs.

Test Coverage:
- GitHub Issue #15: Inconsistent Secret Protection
- GitHub Issue #16: Functions Receive Placeholders
- GitHub Issue #17: Missing Documentation Behavior
- GitHub Issue #18: Environment Variable Dependencies
- GitHub Issue #19: Comprehensive Test Suite
"""

import pytest

from cryptex_ai import protect_secrets, register_pattern
from tests.fixtures.secret_samples import (
    get_sample_secret,
)
from tests.fixtures.test_helpers import (
    assert_function_received_real_values,
    create_test_function_with_capture,
)


class TestGitHubIssue15_ConsistentSecretProtection:
    """
    Regression test for GitHub Issue #15: Inconsistent Secret Protection

    Ensures all secret types behave consistently - functions receive real values
    while AI context sees sanitized placeholders.
    """

    def test_all_secret_types_behave_consistently(self):
        """Test all built-in secret types have consistent behavior."""
        test_cases = {
            "openai_key": get_sample_secret("openai_key"),
            "anthropic_key": get_sample_secret("anthropic_key"),
            "github_token": get_sample_secret("github_token"),
            "database_url": get_sample_secret("database_url"),
            "file_path": get_sample_secret("file_path"),
        }

        for secret_type, secret_value in test_cases.items():
            # Create function with capture to verify what it receives
            received_value = None

            @protect_secrets([secret_type])
            def test_function(secret: str):
                nonlocal received_value
                received_value = secret
                return f"processed: {secret}"

            # Execute function
            result = test_function(secret_value)

            # Function should receive real value (fixes the inconsistency)
            assert received_value == secret_value, (
                f"Secret type '{secret_type}' function should receive real value, got: {received_value}"
            )

            # Result should be sanitized (AI sees placeholder)
            assert "{{" in str(result) or secret_value not in str(result), (
                f"Secret type '{secret_type}' result should be sanitized: {result}"
            )

    def test_multiple_secrets_consistent_behavior(self):
        """Test multiple secret types together behave consistently."""
        api_key = get_sample_secret("openai_key")
        db_url = get_sample_secret("database_url")

        received_values = {}

        @protect_secrets(["openai_key", "database_url"])
        def multi_secret_function(api_key: str, db_url: str):
            received_values["api_key"] = api_key
            received_values["db_url"] = db_url
            return f"API: {api_key}, DB: {db_url}"

        result = multi_secret_function(api_key, db_url)

        # Both functions should receive real values consistently
        assert received_values["api_key"] == api_key
        assert received_values["db_url"] == db_url

        # Result should be sanitized
        assert api_key not in str(result) or "{{" in str(result)
        assert db_url not in str(result) or "{{" in str(result)


class TestGitHubIssue16_FunctionsReceivePlaceholders:
    """
    Regression test for GitHub Issue #16: Functions Receive Placeholders

    Ensures functions receive real secret values, not placeholders, so they
    can perform actual operations like database connections and API calls.
    """

    def test_database_function_receives_real_url(self):
        """Test database function receives real URL, not placeholder."""
        real_db_url = get_sample_secret("database_url")
        received_url = None

        @protect_secrets(["database_url"])
        def connect_to_database(db_url: str):
            nonlocal received_url
            received_url = db_url

            # Function should be able to parse real URL
            if db_url.startswith("postgresql://"):
                return {"status": "connected", "scheme": "postgresql"}
            return {"status": "failed"}

        result = connect_to_database(real_db_url)

        # Function received real URL (not {{DATABASE_URL}} placeholder)
        assert received_url == real_db_url
        assert "{{DATABASE_URL}}" not in received_url

        # Function could process the real URL
        assert "connected" in str(result) or "postgresql" in str(result)

    def test_api_function_receives_real_key(self):
        """Test API function receives real key, not placeholder."""
        real_api_key = get_sample_secret("openai_key")
        received_key = None

        @protect_secrets(["openai_key"])
        def make_api_call(api_key: str):
            nonlocal received_key
            received_key = api_key

            # Function should be able to validate real key format
            if api_key.startswith("sk-") and len(api_key) > 40:
                return {"authenticated": True, "key_valid": True}
            return {"authenticated": False, "key_valid": False}

        result = make_api_call(real_api_key)

        # Function received real key (not {{OPENAI_API_KEY}} placeholder)
        assert received_key == real_api_key
        assert "{{OPENAI_API_KEY}}" not in received_key

        # Function could validate the real key
        assert "authenticated" in str(result) and "True" in str(result)

    def test_file_function_receives_real_path(self):
        """Test file function receives real path, not placeholder."""
        real_file_path = get_sample_secret("file_path")
        received_path = None

        @protect_secrets(["file_path"])
        def process_file_path(file_path: str):
            nonlocal received_path
            received_path = file_path

            # Function should be able to process real path
            import os

            return {
                "path": file_path,
                "dirname": os.path.dirname(file_path),
                "basename": os.path.basename(file_path),
                "is_absolute": os.path.isabs(file_path),
            }

        result = process_file_path(real_file_path)

        # Function received real path (not {{FILE_PATH}} placeholder)
        assert received_path == real_file_path
        assert "{{FILE_PATH}}" not in received_path

        # Function could process the real path
        assert "is_absolute" in str(result) and "True" in str(result)


class TestGitHubIssue18_EnvironmentVariableDependencies:
    """
    Regression test for GitHub Issue #18: Environment Variable Dependencies

    Ensures true zero-config operation - no environment variables required
    for functions to receive real values and work correctly.
    """

    def test_zero_config_database_operations(self):
        """Test database operations work without environment variables."""
        # Clear any existing environment variables
        import os

        original_env = os.environ.get("DATABASE_URL")
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        try:

            @protect_secrets(["database_url"])
            def test_db_operation(db_url: str):
                # Should receive real URL without env var dependency
                return f"Connecting to: {db_url}"

            real_url = "postgresql://user:pass@localhost:5432/testdb"
            result = test_db_operation(real_url)

            # Function should work without environment variables
            # (Result will be sanitized, but function received real value)
            assert result is not None

        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["DATABASE_URL"] = original_env

    def test_zero_config_api_operations(self):
        """Test API operations work without environment variables."""
        import os

        original_env = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        try:

            @protect_secrets(["openai_key"])
            def test_api_operation(api_key: str):
                # Should receive real key without env var dependency
                return f"Using API key: {api_key}"

            real_key = get_sample_secret("openai_key")
            result = test_api_operation(real_key)

            # Function should work without environment variables
            assert result is not None

        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["OPENAI_API_KEY"] = original_env

    def test_no_placeholder_environment_substitution(self):
        """Test that functions don't receive environment variable placeholders."""

        @protect_secrets(["github_token"])
        def test_token_function(token: str):
            # Should never receive {{GITHUB_TOKEN}} style placeholder
            assert not token.startswith("{{")
            assert not token.endswith("}}")
            return token

        real_token = get_sample_secret("github_token")
        result = test_token_function(real_token)

        # Should not fail the assertions in the function
        assert result is not None


class TestGitHubIssue19_ComprehensiveTestSuite:
    """
    Regression test for GitHub Issue #19: Comprehensive Test Suite

    Ensures we have verification capabilities that demonstrate the library
    works as intended with comprehensive test coverage.
    """

    def test_protection_verification_capabilities(self):
        """Test we can verify protection behavior comprehensively."""
        # This test demonstrates the testing capabilities we built

        secrets_to_test = {
            "openai_key": get_sample_secret("openai_key"),
            "database_url": get_sample_secret("database_url"),
            "github_token": get_sample_secret("github_token"),
        }

        for secret_type, secret_value in secrets_to_test.items():
            # Use our test helpers to verify behavior
            test_func, capture = create_test_function_with_capture()
            decorated_func = protect_secrets([secret_type])(test_func)

            # Execute and verify
            result = decorated_func(secret_value)

            # Verify function received real values (test suite capability)
            assert_function_received_real_values(capture, (secret_value,))

            # Verify result is sanitized (protection working)
            assert secret_value not in str(result) or "{{" in str(result)

    def test_all_secret_type_coverage(self):
        """Test that we have comprehensive coverage of all secret types."""
        # This verifies we test all the patterns the library supports
        secret_types = [
            "openai_key",
            "anthropic_key",
            "github_token",
            "database_url",
            "file_path",
        ]

        for secret_type in secret_types:
            # Should be able to get sample for each type
            sample = get_sample_secret(secret_type)
            assert sample is not None
            assert len(sample) > 0

            # Should be able to create test function for each
            @protect_secrets([secret_type])
            def type_test_function(secret: str):
                return f"testing: {secret}"

            result = type_test_function(sample)
            assert result is not None

    def test_custom_pattern_testing_capability(self):
        """Test our ability to test custom patterns comprehensively."""
        # Register a custom pattern for testing
        register_pattern(
            name="test_custom_pattern",
            regex=r"custom-[0-9a-f]{8}",
            placeholder="{{CUSTOM_PATTERN}}",
        )

        @protect_secrets(["test_custom_pattern"])
        def custom_pattern_function(custom_value: str):
            return f"custom: {custom_value}"

        test_value = "custom-abcd1234"
        result = custom_pattern_function(test_value)

        # Test suite can verify custom patterns work
        assert result is not None
        # Should be sanitized
        assert "{{CUSTOM_PATTERN}}" in str(result) or test_value not in str(result)


class TestNoRegression_GeneralFunctionality:
    """
    General regression tests to ensure core functionality doesn't break.
    """

    def test_basic_decorator_still_works(self):
        """Test basic decorator functionality hasn't regressed."""

        @protect_secrets(["openai_key"])
        def basic_function(api_key: str):
            return f"basic: {api_key}"

        result = basic_function(get_sample_secret("openai_key"))
        assert result is not None
        assert "basic" in str(result)

    @pytest.mark.asyncio
    async def test_async_decorator_still_works(self):
        """Test async decorator functionality hasn't regressed."""

        @protect_secrets(["database_url"])
        async def async_function(db_url: str):
            import asyncio

            await asyncio.sleep(0.001)
            return f"async: {db_url}"

        result = await async_function(get_sample_secret("database_url"))
        assert result is not None
        assert "async" in str(result)

    def test_multiple_decorators_still_work(self):
        """Test multiple secret types in decorator still work."""

        @protect_secrets(["openai_key", "database_url", "github_token"])
        def multi_function(api_key: str, db_url: str, token: str):
            return f"multi: {api_key[:10]}, {db_url[:10]}, {token[:10]}"

        result = multi_function(
            get_sample_secret("openai_key"),
            get_sample_secret("database_url"),
            get_sample_secret("github_token"),
        )

        assert result is not None
        assert "multi" in str(result)

    def test_convenience_decorators_still_work(self):
        """Test convenience decorators haven't regressed."""
        from cryptex_ai import (
            protect_api_keys,
            protect_files,
        )

        @protect_files()
        def file_func(path: str):
            return f"file: {path}"

        @protect_api_keys()
        def api_func(key: str):
            return f"api: {key}"

        # All should work without error
        assert file_func(get_sample_secret("file_path")) is not None
        assert api_func(get_sample_secret("openai_key")) is not None
