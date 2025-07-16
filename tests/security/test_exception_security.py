"""
Security tests for exception handling to ensure no secret exposure.
Tests the requirements from GitHub Issue #6.
"""

import json
import pytest

from cryptex.core.exceptions import (
    CryptexError,
    SecurityError,
    SanitizationError,
    ResolutionError,
    PatternError,
    ContextError,
    IsolationError,
    invalid_pattern_error,
    security_breach_error,
    context_not_found_error,
)


class TestExceptionSecurity:
    """Test that exceptions don't expose secrets in any representation."""

    def test_exception_string_representations_no_secrets(self):
        """Test that exception string representations don't expose secrets."""
        # Real-looking secrets for testing
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        github_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz123456"
        
        test_cases = [
            CryptexError(
                f"Processing failed with key: {openai_secret}",
                context_id="test-context",
                details={"api_key": openai_secret, "token": github_token}
            ),
            SecurityError(
                f"Security violation detected for key {openai_secret}",
                details={"secret_value": openai_secret}
            ),
            SanitizationError(
                f"Failed to sanitize secret: {openai_secret}",
                pattern_name="openai_key",
                details={"input_data": {"key": openai_secret}}
            ),
            ResolutionError(
                f"Could not resolve placeholder for {openai_secret}",
                placeholder="{{OPENAI_API_KEY}}",
                details={"resolved_value": openai_secret}
            ),
            PatternError(
                f"Pattern failed to match secret: {openai_secret}",
                pattern_name="github_token",
                details={"test_input": github_token}
            ),
        ]
        
        for exception in test_cases:
            # Test string representation
            str_repr = str(exception)
            assert openai_secret not in str_repr, f"Secret found in str({exception.__class__.__name__})"
            assert github_token not in str_repr, f"GitHub token found in str({exception.__class__.__name__})"
            
            # Test repr
            repr_str = repr(exception)
            assert openai_secret not in repr_str, f"Secret found in repr({exception.__class__.__name__})"
            assert github_token not in repr_str, f"GitHub token found in repr({exception.__class__.__name__})"
            
            # Test to_dict serialization
            dict_repr = exception.to_dict()
            dict_str = json.dumps(dict_repr, default=str)
            assert openai_secret not in dict_str, f"Secret found in to_dict({exception.__class__.__name__})"
            assert github_token not in dict_str, f"GitHub token found in to_dict({exception.__class__.__name__})"

    def test_convenience_functions_no_secrets(self):
        """Test convenience functions don't expose secrets."""
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        
        # Test convenience functions
        test_exceptions = [
            invalid_pattern_error("test_pattern", f"regex with {openai_secret}", "invalid syntax"),
            security_breach_error(f"breach involving {openai_secret}", "test-context"),
            context_not_found_error(f"context-{openai_secret}"),
        ]
        
        for exception in test_exceptions:
            str_repr = str(exception)
            assert openai_secret not in str_repr, f"Secret found in convenience function str: {str_repr}"
            
            dict_repr = exception.to_dict()
            dict_str = json.dumps(dict_repr, default=str)
            assert openai_secret not in dict_str, f"Secret found in convenience function dict: {dict_str}"

    def test_exception_chaining_no_secrets(self):
        """Test exception chaining doesn't expose secrets."""
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        
        try:
            # Create a nested exception scenario
            try:
                raise ValueError(f"Inner error with secret: {openai_secret}")
            except ValueError as inner:
                raise SecurityError(
                    "Outer security error",
                    details={"inner_error": str(inner)},
                    cause=inner
                )
        except SecurityError as outer:
            # Check if secret is exposed through chaining
            str_repr = str(outer)
            assert openai_secret not in str_repr, f"Secret found in chained exception str: {str_repr}"
            
            dict_repr = outer.to_dict()
            dict_str = json.dumps(dict_repr, default=str)
            assert openai_secret not in dict_str, f"Secret found in chained exception dict: {dict_str}"

    def test_sanitization_patterns(self):
        """Test that specific secret patterns are properly sanitized."""
        test_cases = [
            ("sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234", "[OPENAI_KEY_REDACTED]"),
            ("sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234", "[OPENAI_PROJECT_KEY_REDACTED]"),
            ("sk-ant-abc123def456ghi789jkl012mno345pqr678stu901vwx234", "[ANTHROPIC_KEY_REDACTED]"),
            ("ghp_1234567890abcdefghijklmnopqrstuvwxyz123456", "[GITHUB_TOKEN_REDACTED]"),
            ("gho_1234567890abcdefghijklmnopqrstuvwxyz123456", "[GITHUB_OAUTH_REDACTED]"),
        ]
        
        for secret, expected_replacement in test_cases:
            error = CryptexError(f"Error with secret: {secret}")
            assert expected_replacement in str(error), f"Secret not properly sanitized: {secret}"
            assert secret not in str(error), f"Original secret still present: {secret}"

    def test_details_sanitization(self):
        """Test that sensitive details are properly sanitized."""
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        
        sensitive_details = {
            "secret_value": openai_secret,
            "api_key": openai_secret,
            "token": openai_secret,
            "password": "secret123",
            "resolved_value": openai_secret,
            "pattern_string": f"pattern with {openai_secret}",
            "input_data": {"nested_secret": openai_secret},
            "safe_field": "this should remain",
        }
        
        error = CryptexError("Test error", details=sensitive_details)
        dict_repr = error.to_dict()
        
        # Check that sensitive fields are redacted
        assert dict_repr["details"]["secret_value"] == "[REDACTED]"
        assert dict_repr["details"]["api_key"] == "[REDACTED]"
        assert dict_repr["details"]["token"] == "[REDACTED]"
        assert dict_repr["details"]["password"] == "[REDACTED]"
        assert dict_repr["details"]["resolved_value"] == "[REDACTED]"
        assert dict_repr["details"]["pattern_string"] == "[REDACTED]"
        assert dict_repr["details"]["input_data"] == "[REDACTED]"
        
        # Check that safe fields remain
        assert dict_repr["details"]["safe_field"] == "this should remain"
        
        # Ensure no secrets in the entire serialized output
        dict_str = json.dumps(dict_repr, default=str)
        assert openai_secret not in dict_str, "Secret found in sanitized details"

    def test_context_id_sanitization(self):
        """Test that context_id is sanitized when it contains secrets."""
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        context_with_secret = f"context-{openai_secret}"
        
        error = CryptexError("Test error", context_id=context_with_secret)
        dict_repr = error.to_dict()
        
        # Ensure context_id is sanitized
        assert openai_secret not in dict_repr["context_id"], "Secret found in context_id"
        assert "[OPENAI_PROJECT_KEY_REDACTED]" in dict_repr["context_id"], "Context ID not properly sanitized"

    def test_cause_sanitization(self):
        """Test that exception cause is sanitized."""
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        
        try:
            raise ValueError(f"Inner error with secret: {openai_secret}")
        except ValueError as inner:
            outer = SecurityError("Outer error", cause=inner)
            dict_repr = outer.to_dict()
            
            # Ensure cause is sanitized
            assert openai_secret not in dict_repr["cause"], "Secret found in sanitized cause"
            assert "[OPENAI_PROJECT_KEY_REDACTED]" in dict_repr["cause"], "Cause not properly sanitized"


# Additional integration tests for real-world scenarios
class TestExceptionSecurityIntegration:
    """Integration tests for exception security in realistic scenarios."""

    def test_logging_safety(self):
        """Test that exceptions are safe for logging systems."""
        import logging
        import io
        
        # Create a string buffer to capture log output
        log_buffer = io.StringIO()
        handler = logging.StreamHandler(log_buffer)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        
        try:
            raise SecurityError(
                f"Security breach with key: {openai_secret}",
                details={"api_key": openai_secret}
            )
        except SecurityError as e:
            # Log the exception
            logger.error("Exception occurred: %s", str(e))
            logger.error("Exception details: %s", e.to_dict())
        
        # Check that no secrets are in the log output
        log_output = log_buffer.getvalue()
        assert openai_secret not in log_output, "Secret found in log output"
        assert "[OPENAI_PROJECT_KEY_REDACTED]" in log_output, "Message not properly sanitized in logs"

    def test_json_serialization_safety(self):
        """Test that exceptions are safe for JSON serialization."""
        openai_secret = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        
        error = CryptexError(
            f"JSON test with secret: {openai_secret}",
            context_id=f"ctx-{openai_secret}",
            details={"secret_value": openai_secret, "nested": {"api_key": openai_secret}}
        )
        
        # Test that it can be safely serialized to JSON
        json_str = json.dumps(error.to_dict(), default=str)
        
        # Verify no secrets in the JSON
        assert openai_secret not in json_str, "Secret found in JSON serialization"
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["error_type"] == "CryptexError"
        assert parsed["details"]["secret_value"] == "[REDACTED]"
        assert parsed["details"]["nested"] == "[REDACTED]"