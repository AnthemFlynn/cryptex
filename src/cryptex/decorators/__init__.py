"""Decorators for Cryptex middleware integration."""

# Main Cryptex decorator
from .cryptex import (
    cryptex,
    cryptex_api,
    cryptex_auth,
    cryptex_database,
    cryptex_endpoint,
    cryptex_file,
    cryptex_tool,
)
from .fastapi import (
    FastAPIEndpointProtection,
    FastAPIEndpointRegistry,
    get_endpoint_registry,
    protect_auth_endpoint,
    protect_database_endpoint,
    protect_endpoint,
    protect_external_api_endpoint,
    protect_file_endpoint,
    register_protected_endpoint,
)

# Legacy decorators for backward compatibility
from .mcp import (
    MCPToolProtection,
    MCPToolRegistry,
    get_tool_registry,
    protect_api_tool,
    protect_database_tool,
    protect_file_tool,
    protect_tool,
    register_protected_tool,
)

__all__ = [
    # Main Cryptex decorator
    "cryptex",
    "cryptex_tool",
    "cryptex_endpoint",
    "cryptex_file",
    "cryptex_api",
    "cryptex_database",
    "cryptex_auth",
    # Legacy MCP decorators
    "protect_tool",
    "protect_file_tool",
    "protect_api_tool",
    "protect_database_tool",
    "MCPToolProtection",
    "MCPToolRegistry",
    "get_tool_registry",
    "register_protected_tool",
    # Legacy FastAPI decorators
    "protect_endpoint",
    "protect_auth_endpoint",
    "protect_database_endpoint",
    "protect_external_api_endpoint",
    "protect_file_endpoint",
    "FastAPIEndpointProtection",
    "FastAPIEndpointRegistry",
    "get_endpoint_registry",
    "register_protected_endpoint",
]
