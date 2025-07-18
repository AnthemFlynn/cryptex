"""
Pattern registry for managing secret patterns.

This module implements a thread-safe registry for secret patterns,
following the Repository pattern and SOLID principles.
"""

import threading
from collections.abc import Iterator
from re import Pattern as RePattern

from .base import DEFAULT_PATTERNS, BaseSecretPattern, SecretPattern


class PatternRegistry:
    """
    Thread-safe repository for secret patterns.

    Manages all patterns uniformly - no distinction between "built-in" and "custom".
    """

    def __init__(self):
        """Initialize the pattern registry with default patterns."""
        self._patterns: dict[str, SecretPattern] = {}
        self._lock = threading.RLock()

        # Load default patterns
        for pattern in DEFAULT_PATTERNS:
            self._patterns[pattern.name] = pattern

    def register(
        self,
        name: str,
        pattern: str | RePattern[str],
        placeholder_template: str,
        description: str = "",
    ) -> None:
        """
        Register a pattern.

        Args:
            name: Unique pattern name
            pattern: Regular expression pattern
            placeholder_template: Template for sanitized output
            description: Optional description

        Raises:
            ValueError: If pattern name already exists
        """
        with self._lock:
            if name in self._patterns:
                raise ValueError(f"Pattern '{name}' already registered")

            secret_pattern = BaseSecretPattern(
                name=name,
                pattern=pattern,
                placeholder_template=placeholder_template,
                description=description,
            )
            self._patterns[name] = secret_pattern

    def unregister(self, name: str) -> bool:
        """
        Unregister a pattern.

        Args:
            name: Pattern name to remove

        Returns:
            True if pattern was removed, False if not found
        """
        with self._lock:
            if name in self._patterns:
                del self._patterns[name]
                return True
            return False

    def get(self, name: str) -> SecretPattern | None:
        """
        Get a pattern by name.

        Args:
            name: Pattern name to retrieve

        Returns:
            Pattern instance or None if not found
        """
        with self._lock:
            return self._patterns.get(name)

    def get_all(self) -> list[SecretPattern]:
        """
        Get all available patterns.

        Returns:
            List of all patterns
        """
        with self._lock:
            return list(self._patterns.values())

    def list_names(self) -> list[str]:
        """
        List all available pattern names.

        Returns:
            Sorted list of pattern names
        """
        with self._lock:
            return sorted(self._patterns.keys())

    def clear_all(self) -> None:
        """
        Clear all patterns and reload defaults.

        This removes all patterns and reloads the default set.
        """
        with self._lock:
            self._patterns.clear()
            for pattern in DEFAULT_PATTERNS:
                self._patterns[pattern.name] = pattern

    def clear_custom(self) -> None:
        """
        Clear only non-default patterns.

        Keeps the default patterns but removes any added ones.
        """
        default_names = {p.name for p in DEFAULT_PATTERNS}
        with self._lock:
            to_remove = [
                name for name in self._patterns.keys() if name not in default_names
            ]
            for name in to_remove:
                del self._patterns[name]

    def __contains__(self, name: str) -> bool:
        """Check if a pattern exists."""
        with self._lock:
            return name in self._patterns

    def __iter__(self) -> Iterator[SecretPattern]:
        """Iterate over all patterns."""
        return iter(self.get_all())

    def __len__(self) -> int:
        """Get total number of patterns."""
        with self._lock:
            return len(self._patterns)


# Global registry instance
_global_registry = PatternRegistry()


def get_registry() -> PatternRegistry:
    """
    Get the global pattern registry.

    Returns:
        Global PatternRegistry instance
    """
    return _global_registry
