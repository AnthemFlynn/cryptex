"""
Unit Tests for Pattern Registry

Tests the PatternRegistry class in isolation.
Focuses on pattern registration, retrieval, and management functionality.

Test Coverage:
- Pattern registration and unregistration
- Pattern retrieval and listing
- Thread safety
- Default pattern loading
- Error handling and validation
"""

import threading

import pytest

from cryptex_ai.patterns.base import DEFAULT_PATTERNS
from cryptex_ai.patterns.registry import PatternRegistry, get_registry


class TestPatternRegistryInitialization:
    """Test pattern registry initialization."""

    def test_registry_initializes_with_default_patterns(self):
        """Test registry loads default patterns on initialization."""
        registry = PatternRegistry()

        # Should have default patterns
        assert len(registry.get_all()) > 0

        # Check for specific default patterns
        pattern_names = registry.list_names()
        assert "openai_key" in pattern_names
        assert "database_url" in pattern_names
        assert "github_token" in pattern_names

    def test_registry_contains_all_default_patterns(self):
        """Test registry contains all DEFAULT_PATTERNS."""
        registry = PatternRegistry()
        pattern_names = registry.list_names()

        for default_pattern in DEFAULT_PATTERNS:
            assert default_pattern.name in pattern_names


class TestPatternRegistration:
    """Test pattern registration functionality."""

    def test_register_new_pattern(self):
        """Test registering a new pattern."""
        registry = PatternRegistry()
        initial_count = len(registry.get_all())

        registry.register(
            name="test_pattern",
            pattern=r"test-[0-9]{4}",
            placeholder_template="{{TEST_PATTERN}}",
            description="Test pattern for unit tests",
        )

        # Should have one more pattern
        assert len(registry.get_all()) == initial_count + 1

        # Pattern should be retrievable
        pattern = registry.get("test_pattern")
        assert pattern is not None
        assert pattern.name == "test_pattern"
        assert pattern.placeholder_template == "{{TEST_PATTERN}}"

    def test_register_pattern_with_compiled_regex(self):
        """Test registering pattern with pre-compiled regex."""
        import re

        registry = PatternRegistry()
        compiled_pattern = re.compile(r"compiled-[a-z]+")

        registry.register(
            name="compiled_pattern",
            pattern=compiled_pattern,
            placeholder_template="{{COMPILED}}",
            description="Pre-compiled pattern",
        )

        pattern = registry.get("compiled_pattern")
        assert pattern is not None
        assert pattern.pattern == compiled_pattern

    def test_register_duplicate_pattern_raises_error(self):
        """Test that registering duplicate pattern names raises error."""
        registry = PatternRegistry()

        # Register first pattern
        registry.register(
            name="duplicate_test",
            pattern=r"test-\d+",
            placeholder_template="{{TEST}}",
        )

        # Attempting to register same name should raise ValueError
        with pytest.raises(ValueError, match="already registered"):
            registry.register(
                name="duplicate_test",
                pattern=r"different-pattern",
                placeholder_template="{{DIFFERENT}}",
            )

    def test_register_pattern_with_invalid_regex(self):
        """Test registering pattern with invalid regex."""
        registry = PatternRegistry()

        # Invalid regex should raise ValueError during registration
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            registry.register(
                name="invalid_pattern",
                pattern=r"[invalid-regex-[",  # Invalid regex
                placeholder_template="{{INVALID}}",
            )


class TestPatternRetrieval:
    """Test pattern retrieval functionality."""

    def test_get_existing_pattern(self):
        """Test retrieving an existing pattern."""
        registry = PatternRegistry()

        pattern = registry.get("openai_key")

        assert pattern is not None
        assert pattern.name == "openai_key"
        assert "{{OPENAI_API_KEY}}" in pattern.placeholder_template

    def test_get_nonexistent_pattern(self):
        """Test retrieving a non-existent pattern."""
        registry = PatternRegistry()

        pattern = registry.get("nonexistent_pattern")

        assert pattern is None

    def test_get_all_patterns(self):
        """Test getting all patterns."""
        registry = PatternRegistry()

        all_patterns = registry.get_all()

        assert len(all_patterns) > 0
        assert all(hasattr(p, "name") for p in all_patterns)
        assert all(hasattr(p, "pattern") for p in all_patterns)

    def test_list_pattern_names(self):
        """Test listing pattern names."""
        registry = PatternRegistry()

        names = registry.list_names()

        assert len(names) > 0
        assert isinstance(names, list)
        assert all(isinstance(name, str) for name in names)
        # Should be sorted
        assert names == sorted(names)

    def test_pattern_membership_check(self):
        """Test __contains__ method."""
        registry = PatternRegistry()

        assert "openai_key" in registry
        assert "nonexistent_pattern" not in registry

    def test_pattern_iteration(self):
        """Test __iter__ method."""
        registry = PatternRegistry()

        patterns = list(registry)

        assert len(patterns) > 0
        assert all(hasattr(p, "name") for p in patterns)

    def test_pattern_count(self):
        """Test __len__ method."""
        registry = PatternRegistry()
        initial_count = len(registry)

        registry.register(
            name="count_test",
            pattern=r"count-\d+",
            placeholder_template="{{COUNT}}",
        )

        assert len(registry) == initial_count + 1


class TestPatternUnregistration:
    """Test pattern unregistration functionality."""

    def test_unregister_existing_pattern(self):
        """Test unregistering an existing pattern."""
        registry = PatternRegistry()

        # Register a pattern first
        registry.register(
            name="temp_pattern",
            pattern=r"temp-\d+",
            placeholder_template="{{TEMP}}",
        )

        assert "temp_pattern" in registry

        # Unregister it
        result = registry.unregister("temp_pattern")

        assert result is True
        assert "temp_pattern" not in registry

    def test_unregister_nonexistent_pattern(self):
        """Test unregistering a non-existent pattern."""
        registry = PatternRegistry()

        result = registry.unregister("nonexistent_pattern")

        assert result is False

    def test_unregister_default_pattern(self):
        """Test unregistering a default pattern."""
        registry = PatternRegistry()

        assert "openai_key" in registry

        result = registry.unregister("openai_key")

        assert result is True
        assert "openai_key" not in registry


class TestPatternClearingOperations:
    """Test pattern clearing operations."""

    def test_clear_all_patterns(self):
        """Test clearing all patterns and reloading defaults."""
        registry = PatternRegistry()

        # Add a custom pattern
        registry.register(
            name="custom_pattern",
            pattern=r"custom-\d+",
            placeholder_template="{{CUSTOM}}",
        )

        initial_count = len(DEFAULT_PATTERNS)
        assert len(registry) == initial_count + 1

        # Clear all
        registry.clear_all()

        # Should only have default patterns
        assert len(registry) == initial_count
        assert "custom_pattern" not in registry
        assert "openai_key" in registry  # Default should be reloaded

    def test_clear_custom_patterns_only(self):
        """Test clearing only custom patterns."""
        registry = PatternRegistry()
        initial_count = len(registry)

        # Add custom patterns
        registry.register("custom1", r"c1-\d+", "{{C1}}")
        registry.register("custom2", r"c2-\d+", "{{C2}}")

        assert len(registry) == initial_count + 2

        # Clear custom patterns only
        registry.clear_custom()

        # Should be back to initial count
        assert len(registry) == initial_count
        assert "custom1" not in registry
        assert "custom2" not in registry
        assert "openai_key" in registry  # Default should remain


class TestThreadSafety:
    """Test thread safety of pattern registry operations."""

    def test_concurrent_registration(self):
        """Test concurrent pattern registration is thread-safe."""
        registry = PatternRegistry()
        results = {}

        def register_pattern(thread_id: int):
            try:
                registry.register(
                    name=f"thread_pattern_{thread_id}",
                    pattern=rf"thread-{thread_id}-\d+",
                    placeholder_template=f"{{{{THREAD_{thread_id}}}}}",
                )
                results[thread_id] = "success"
            except Exception as e:
                results[thread_id] = f"error: {e}"

        # Create multiple threads registering patterns
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_pattern, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert all(result == "success" for result in results.values())
        assert len(results) == 5

        # All patterns should be registered
        for i in range(5):
            assert f"thread_pattern_{i}" in registry

    def test_concurrent_read_operations(self):
        """Test concurrent read operations are thread-safe."""
        registry = PatternRegistry()
        results = []

        def read_patterns():
            # Multiple read operations
            names = registry.list_names()
            all_patterns = registry.get_all()
            pattern = registry.get("openai_key")
            contains_check = "openai_key" in registry

            results.append(
                {
                    "names_count": len(names),
                    "all_patterns_count": len(all_patterns),
                    "pattern_found": pattern is not None,
                    "contains_check": contains_check,
                }
            )

        # Create multiple reader threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=read_patterns)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should return consistent results
        assert len(results) == 10
        first_result = results[0]
        assert all(r == first_result for r in results)

    def test_concurrent_mixed_operations(self):
        """Test mixed read/write operations are thread-safe."""
        registry = PatternRegistry()
        operation_results = []

        def mixed_operations(thread_id: int):
            try:
                # Register a pattern
                registry.register(
                    name=f"mixed_{thread_id}",
                    pattern=rf"mixed-{thread_id}-\d+",
                    placeholder_template=f"{{{{MIXED_{thread_id}}}}}",
                )

                # Read operations
                names = registry.list_names()
                pattern = registry.get(f"mixed_{thread_id}")

                # Unregister
                unregistered = registry.unregister(f"mixed_{thread_id}")

                operation_results.append(
                    {
                        "thread_id": thread_id,
                        "registered": True,
                        "found_in_names": f"mixed_{thread_id}" in names,
                        "retrieved_pattern": pattern is not None,
                        "unregistered": unregistered,
                    }
                )
            except Exception as e:
                operation_results.append({"thread_id": thread_id, "error": str(e)})

        # Create mixed operation threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=mixed_operations, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len(operation_results) == 5
        assert all("error" not in result for result in operation_results)


class TestGlobalRegistryAccess:
    """Test global registry singleton access."""

    def test_get_registry_returns_singleton(self):
        """Test get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_global_registry_persistence(self):
        """Test global registry maintains state across calls."""
        registry = get_registry()
        initial_count = len(registry)

        # Register a pattern
        registry.register(
            name="global_test",
            pattern=r"global-\d+",
            placeholder_template="{{GLOBAL}}",
        )

        # Get registry again
        registry2 = get_registry()

        # Should have the same pattern
        assert len(registry2) == initial_count + 1
        assert "global_test" in registry2

        # Clean up
        registry.unregister("global_test")
