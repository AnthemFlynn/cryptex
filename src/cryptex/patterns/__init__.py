"""
Pattern management system for Cryptex.

This module provides a clean, extensible API for managing secret patterns
following SOLID principles and Python best practices.
"""

from .base import DEFAULT_PATTERNS, BaseSecretPattern, SecretPattern
from .registry import PatternRegistry, get_registry

# Global registry instance
_registry = get_registry()

# Public API functions
def register_pattern(
    name: str,
    regex: str,
    placeholder: str,
    description: str = "",
) -> None:
    """
    Register a secret pattern.

    Args:
        name: Unique pattern name
        regex: Regular expression pattern
        placeholder: Template for sanitized output
        description: Optional description

    Raises:
        ValueError: If parameters are invalid
    """
    if not name or not name.strip():
        raise ValueError("Pattern name cannot be empty")

    if not placeholder or not placeholder.strip():
        raise ValueError("Placeholder cannot be empty")

    # The registry will validate the regex pattern
    _registry.register(name, regex, placeholder, description)


def unregister_pattern(name: str) -> bool:
    """Remove a custom pattern."""
    return _registry.unregister(name)


def get_pattern(name: str) -> SecretPattern | None:
    """Get a pattern by name."""
    return _registry.get(name)


def get_all_patterns() -> list[SecretPattern]:
    """Get all available patterns."""
    return _registry.get_all()


def list_patterns() -> list[str]:
    """List all pattern names."""
    return _registry.list_names()


def clear_custom_patterns() -> None:
    """Clear all custom patterns."""
    _registry.clear_custom()


def register_patterns(**patterns) -> None:
    """Register multiple patterns at once."""
    for name, (regex, placeholder) in patterns.items():
        register_pattern(name, regex, placeholder)


# Convenience access to registry
def get_pattern_registry() -> PatternRegistry:
    """Get the global pattern registry."""
    return _registry


__all__ = [
    # Base classes
    "SecretPattern",
    "BaseSecretPattern",
    "DEFAULT_PATTERNS",

    # Registry
    "PatternRegistry",
    "get_pattern_registry",

    # Public API
    "register_pattern",
    "unregister_pattern",
    "get_pattern",
    "get_all_patterns",
    "list_patterns",
    "clear_custom_patterns",
    "register_patterns",
]
