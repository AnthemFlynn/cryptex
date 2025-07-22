"""
Test Helper Utilities

Common utilities and helper functions used across the test suite.
Provides consistent testing patterns and reduces code duplication.
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

import pytest

from cryptex_ai import TemporalIsolationEngine, protect_secrets

from .secret_samples import get_sample_secret


class FunctionExecutionCapture:
    """Captures what a decorated function actually receives and returns."""

    def __init__(self):
        self.received_args = None
        self.received_kwargs = None
        self.return_value = None
        self.exception = None

    def capture_execution(self, *args, **kwargs):
        """Capture function execution details."""
        self.received_args = args
        self.received_kwargs = kwargs
        return self

    def set_return_value(self, value: Any):
        """Set what the function should return."""
        self.return_value = value
        return self

    def should_raise(self, exception: Exception):
        """Set exception the function should raise."""
        self.exception = exception
        return self


def create_test_function_with_capture() -> tuple[Callable, FunctionExecutionCapture]:
    """Create a test function that captures its execution."""
    capture = FunctionExecutionCapture()

    def test_function(*args, **kwargs):
        capture.capture_execution(*args, **kwargs)
        if capture.exception:
            raise capture.exception
        return capture.return_value or f"executed with {args} {kwargs}"

    return test_function, capture


def assert_function_received_real_values(
    capture: FunctionExecutionCapture,
    expected_args: tuple,
    expected_kwargs: dict | None = None,
):
    """Assert that function received the expected real values."""
    expected_kwargs = expected_kwargs or {}

    assert capture.received_args == expected_args, (
        f"Function should receive real args. Expected: {expected_args}, Got: {capture.received_args}"
    )

    assert capture.received_kwargs == expected_kwargs, (
        f"Function should receive real kwargs. Expected: {expected_kwargs}, Got: {capture.received_kwargs}"
    )


def assert_result_is_sanitized(result: Any, original_secrets: list[str]):
    """Assert that the result is properly sanitized."""
    result_str = str(result)

    for secret in original_secrets:
        assert secret not in result_str, (
            f"Secret '{secret}' should not appear in sanitized result: {result_str}"
        )

    # Should contain at least one placeholder
    assert "{{" in result_str, f"Result should contain placeholders: {result_str}"


def create_mock_engine() -> Mock:
    """Create a mock TemporalIsolationEngine for testing."""
    mock_engine = Mock(spec=TemporalIsolationEngine)

    # Mock sanitize_for_ai to return sanitized data
    mock_sanitized_data = Mock()
    mock_sanitized_data.data = "{{MOCK_PLACEHOLDER}}"
    mock_engine.sanitize_for_ai.return_value = mock_sanitized_data

    # Mock sanitize_traceback
    mock_engine.sanitize_traceback.return_value = None

    return mock_engine


def verify_secret_pattern_detection(secret_type: str, should_detect: bool = True):
    """Verify that a secret pattern is detected correctly."""
    from cryptex_ai.core.engine import TemporalIsolationEngine
    from cryptex_ai.patterns import get_all_patterns

    engine = TemporalIsolationEngine(patterns=get_all_patterns())
    sample_secret = get_sample_secret(secret_type)

    # Test detection
    detected_secrets = pytest.asyncio.run(
        engine._detect_secrets_in_string(sample_secret)
    )

    if should_detect:
        assert len(detected_secrets) > 0, (
            f"Secret type '{secret_type}' should be detected in '{sample_secret}'"
        )

        # Verify the correct pattern was matched
        pattern_names = [s.pattern_name for s in detected_secrets]
        assert secret_type in pattern_names, (
            f"Expected pattern '{secret_type}' not found in detected patterns: {pattern_names}"
        )
    else:
        pattern_names = [s.pattern_name for s in detected_secrets]
        assert secret_type not in pattern_names, (
            f"Pattern '{secret_type}' should not be detected in '{sample_secret}'"
        )


def create_decorated_function(
    secret_types: list[str], base_function: Callable | None = None
):
    """Create a function decorated with protect_secrets."""
    if base_function is None:

        def base_function(*args, **kwargs):
            return f"Result: {args} {kwargs}"

    return protect_secrets(secret_types)(base_function)


class TestSecretValidator:
    """Helper for validating secret protection behavior."""

    @staticmethod
    def validate_protection_workflow(
        secret_types: list[str],
        test_secrets: dict[str, str],
        function_logic: Callable | None = None,
    ):
        """Validate complete protection workflow."""
        # Create function with capture
        if function_logic is None:
            test_function, capture = create_test_function_with_capture()
        else:
            capture = FunctionExecutionCapture()

            def test_function(*args, **kwargs):
                capture.capture_execution(*args, **kwargs)
                return function_logic(*args, **kwargs)

        # Decorate function
        decorated_function = protect_secrets(secret_types)(test_function)

        # Execute with test secrets
        secret_values = list(test_secrets.values())
        result = decorated_function(*secret_values)

        # Validate function received real values
        assert_function_received_real_values(capture, tuple(secret_values))

        # Validate result is sanitized
        assert_result_is_sanitized(result, secret_values)

        return result, capture
