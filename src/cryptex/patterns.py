"""
Pattern Registration API for Cryptex.

This module provides a minimal API for registering custom secret patterns.
95% of users need zero configuration - built-in defaults handle common cases.
5% of users can register custom patterns programmatically.

No config files, no parsing, no external dependencies.
Pure code-based configuration for maximum security and simplicity.
"""

import re
import threading
from typing import Pattern

from .core.engine import SecretPattern

# Global pattern registry (thread-safe)
_pattern_registry: dict[str, SecretPattern] = {}
_registry_lock = threading.RLock()


def register_pattern(
    name: str, 
    regex: str | Pattern[str], 
    placeholder: str,
    description: str = ""
) -> None:
    """
    Register a custom secret pattern.
    
    This is for advanced users who need patterns beyond the excellent built-in defaults.
    Most users (95%) should use built-in patterns: openai_key, anthropic_key, 
    github_token, file_path, database_url.
    
    Args:
        name: Unique pattern name (e.g., "my_api_key")
        regex: Regular expression pattern (string or compiled Pattern)
        placeholder: Template for sanitized output (e.g., "{{MY_API_KEY}}")
        description: Optional description of what this pattern detects
        
    Example:
        >>> register_pattern(
        ...     name="slack_token",
        ...     regex=r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
        ...     placeholder="{{SLACK_TOKEN}}",
        ...     description="Slack bot token"
        ... )
        >>> 
        >>> @protect_tool(secrets=["slack_token"])
        >>> async def my_tool(token: str): ...
        
    Raises:
        ValueError: If pattern name already exists or regex is invalid
    """
    if not name or not name.strip():
        raise ValueError("Pattern name cannot be empty")
    
    if not placeholder or not placeholder.strip():
        raise ValueError("Placeholder cannot be empty")
    
    # Compile regex to validate it
    if isinstance(regex, str):
        try:
            compiled_pattern = re.compile(regex)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e
    else:
        compiled_pattern = regex
    
    with _registry_lock:
        if name in _pattern_registry:
            raise ValueError(f"Pattern '{name}' already registered")
        
        pattern = SecretPattern(
            name=name,
            pattern=compiled_pattern,
            placeholder_template=placeholder,
            description=description
        )
        
        _pattern_registry[name] = pattern


def unregister_pattern(name: str) -> bool:
    """
    Remove a custom pattern from the registry.
    
    Args:
        name: Pattern name to remove
        
    Returns:
        True if pattern was found and removed, False otherwise
        
    Note:
        Cannot unregister built-in patterns (openai_key, etc.)
    """
    with _registry_lock:
        if name in _pattern_registry:
            del _pattern_registry[name]
            return True
        return False


def list_patterns() -> list[str]:
    """
    List all available pattern names.
    
    Returns:
        List of pattern names (built-ins + custom registered patterns)
        
    Example:
        >>> patterns = list_patterns()
        >>> print(patterns)
        ['openai_key', 'anthropic_key', 'github_token', 'file_path', 'database_url', 'my_custom_pattern']
    """
    from .core.engine import TemporalIsolationEngine
    
    # Get built-in pattern names
    engine = TemporalIsolationEngine()
    builtin_names = [p.name for p in engine.patterns]
    
    # Get custom pattern names
    with _registry_lock:
        custom_names = list(_pattern_registry.keys())
    
    return sorted(builtin_names + custom_names)


def get_pattern(name: str) -> SecretPattern | None:
    """
    Get a pattern by name.
    
    Args:
        name: Pattern name to retrieve
        
    Returns:
        SecretPattern instance or None if not found
    """
    # Check custom patterns first
    with _registry_lock:
        if name in _pattern_registry:
            return _pattern_registry[name]
    
    # Check built-in patterns
    from .core.engine import TemporalIsolationEngine
    engine = TemporalIsolationEngine()
    for pattern in engine.patterns:
        if pattern.name == name:
            return pattern
    
    return None


def get_all_patterns() -> list[SecretPattern]:
    """
    Get all available patterns (built-ins + custom).
    
    Returns:
        List of all SecretPattern instances
    """
    from .core.engine import TemporalIsolationEngine
    
    # Get built-in patterns
    engine = TemporalIsolationEngine()
    all_patterns = list(engine.patterns)
    
    # Add custom patterns
    with _registry_lock:
        all_patterns.extend(_pattern_registry.values())
    
    return all_patterns


def clear_custom_patterns() -> None:
    """
    Remove all custom registered patterns.
    
    Built-in patterns are unaffected.
    Useful for testing or dynamic reconfiguration.
    """
    with _registry_lock:
        _pattern_registry.clear()


# Convenience function for bulk registration
def register_patterns(**patterns: tuple[str, str]) -> None:
    """
    Register multiple patterns at once.
    
    Args:
        **patterns: Keyword arguments where key=pattern_name, 
                   value=(regex, placeholder) tuple
                   
    Example:
        >>> register_patterns(
        ...     slack_token=(r"xoxb-[0-9-a-zA-Z]{51}", "{{SLACK_TOKEN}}"),
        ...     discord_token=(r"[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}", "{{DISCORD_TOKEN}}")
        ... )
    """
    for name, (regex, placeholder) in patterns.items():
        register_pattern(name, regex, placeholder)