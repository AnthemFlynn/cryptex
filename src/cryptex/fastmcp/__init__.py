"""FastMCP integration for Cryptex middleware."""

from .middleware import (
    FastMCPCodenameMiddleware,  # Legacy alias
    FastMCPCryptexMiddleware,
    MCPRequest,
    MCPResponse,
    MCPServerProtection,
    create_protected_server,
    setup_codename_protection,  # Legacy alias
    setup_cryptex_protection,
)

__all__ = [
    "FastMCPCryptexMiddleware",
    "FastMCPCodenameMiddleware",  # Legacy alias
    "MCPServerProtection",
    "MCPRequest",
    "MCPResponse",
    "setup_cryptex_protection",
    "setup_codename_protection",  # Legacy alias
    "create_protected_server",
]
