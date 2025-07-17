"""
Base classes and interfaces for pattern management.

This module defines the abstractions for secret patterns, following
SOLID principles and providing a clean extension point for custom patterns.
"""

import re
from re import Pattern as RePattern
from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretPattern(Protocol):
    """
    Protocol defining the interface for secret patterns.

    This protocol ensures all pattern implementations have consistent
    behavior while allowing for different concrete implementations.
    """

    name: str
    pattern: RePattern[str]
    placeholder_template: str
    description: str

    def match(self, text: str) -> bool:
        """Check if the pattern matches the given text."""
        ...

    def substitute(self, text: str) -> str:
        """Replace matches with placeholder template."""
        ...


class BaseSecretPattern:
    """
    Abstract base class for secret patterns.

    Provides common functionality while enforcing the contract
    for concrete pattern implementations.
    """

    def __init__(
        self,
        name: str,
        pattern: str | RePattern[str],
        placeholder_template: str,
        description: str = "",
    ):
        """
        Initialize a secret pattern.

        Args:
            name: Unique identifier for the pattern
            pattern: Regular expression pattern (string or compiled)
            placeholder_template: Template for sanitized output
            description: Human-readable description
        """
        self.name = name
        self.placeholder_template = placeholder_template
        self.description = description

        # Compile pattern if string
        if isinstance(pattern, str):
            try:
                self.pattern = re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e
        else:
            self.pattern = pattern

    def match(self, text: str) -> bool:
        """Check if the pattern matches the given text."""
        return bool(self.pattern.search(text))

    def substitute(self, text: str) -> str:
        """Replace matches with placeholder template."""
        return self.pattern.sub(self.placeholder_template, text)

    def __str__(self) -> str:
        return f"SecretPattern(name='{self.name}', pattern='{self.pattern.pattern}')"

    def __repr__(self) -> str:
        return (
            f"SecretPattern(name='{self.name}', "
            f"pattern='{self.pattern.pattern}', "
            f"placeholder='{self.placeholder_template}')"
        )


# Default pattern definitions - these are just patterns, not "special"
DEFAULT_PATTERNS = [
    BaseSecretPattern(
        name="openai_key",
        pattern=r"sk-[a-zA-Z0-9]{48}",
        placeholder_template="{{OPENAI_API_KEY}}",
        description="OpenAI API key"
    ),
    BaseSecretPattern(
        name="anthropic_key",
        pattern=r"sk-ant-[a-zA-Z0-9-]{40,}",
        placeholder_template="{{ANTHROPIC_API_KEY}}",
        description="Anthropic API key"
    ),
    BaseSecretPattern(
        name="github_token",
        pattern=r"ghp_[a-zA-Z0-9]{36}",
        placeholder_template="{{GITHUB_TOKEN}}",
        description="GitHub personal access token"
    ),
    BaseSecretPattern(
        name="file_path",
        pattern=r"(/[^/\s]+)+/?",
        placeholder_template="/{USER_HOME}/.../{filename}",
        description="File system path"
    ),
    BaseSecretPattern(
        name="database_url",
        pattern=r"(?:postgresql|mysql|sqlite|redis)://[^\s]+",
        placeholder_template="{{DATABASE_URL}}",
        description="Database connection URL"
    ),
]
