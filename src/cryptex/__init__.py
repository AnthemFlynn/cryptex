"""
Cryptex - Temporal Isolation Engine for AI/LLM Applications

Bulletproof secrets isolation middleware for FastMCP servers and FastAPI applications.
Implements three-phase security architecture: Sanitization → AI Processing → Secret Resolution.

## Core Concept

Cryptex provides middleware that ensures:
- **AI/LLM Context**: Sees safe placeholders like `{RESOLVE:API_KEY:abc123}` or `/{USER_HOME}/...`
- **Tool/Endpoint Execution**: Gets real values for actual operations
- **Temporal Isolation**: Secrets exist in different forms at different times

## Quick Start

### FastMCP Integration
```python
from fastmcp import FastMCPServer
from cryptex.fastmcp import setup_cryptex_protection

server = FastMCPServer()
setup_cryptex_protection(server, config_path="cryptex.toml")

@server.tool()
@cryptex(secrets=["api_key", "file_paths"])
async def my_tool(file_path: str, api_key: str) -> str:
    # AI sees placeholders, tool gets real values
    return process_file(file_path, api_key)
```

### FastAPI Integration
```python
from fastapi import FastAPI
from cryptex.fastapi import setup_cryptex_protection

app = FastAPI()
setup_cryptex_protection(app, config_path="cryptex.toml")

@app.post("/api/process")
@cryptex(secrets=["api_key"])
async def process_data(data: dict, api_key: str):
    # Request/response sanitized, endpoint gets real values
    return await external_api_call(data, api_key)
```

## Features

- **Zero-code middleware**: Automatic protection for all tools/endpoints
- **Decorator-based**: Fine-grained control with `@cryptex` decorator
- **Performance optimized**: <5ms sanitization, <10ms resolution
- **Framework agnostic**: Works with FastMCP, FastAPI, Django, Flask
- **Enterprise ready**: Audit logging, metrics, compliance features
"""

__version__ = "0.1.0"
__author__ = "Cryptex Team"
__email__ = "team@cryptex-ai.com"

# Core components
from .core.engine import TemporalIsolationEngine, SecretPattern, SanitizedData, ResolvedData
from .core.exceptions import CryptexError, SecurityError, ConfigError, CodenameError
from .config import CryptexConfig, SecurityPolicy, PerformanceConfig, ConfigurationLoader, CodenameConfig

# Main Cryptex decorator
from .decorators import cryptex

# Convenience decorators for backward compatibility
from .decorators import (
    protect_tool, protect_file_tool, protect_api_tool, protect_database_tool,
    protect_endpoint, protect_auth_endpoint, protect_database_endpoint,
    protect_external_api_endpoint, protect_file_endpoint
)

# Middleware integrations
try:
    from .fastmcp import setup_cryptex_protection as setup_fastmcp_protection
    from .fastmcp import FastMCPCryptexMiddleware
    _FASTMCP_AVAILABLE = True
except ImportError:
    _FASTMCP_AVAILABLE = False

try:
    from .fastapi import setup_cryptex_protection as setup_fastapi_protection  
    from .fastapi import CryptexMiddleware as FastAPICryptexMiddleware
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

# Convenience functions
async def setup_protection(framework, **kwargs):
    """
    Universal setup function for any supported framework.
    
    Args:
        framework: FastMCP server, FastAPI app, or other supported framework
        **kwargs: Configuration arguments
        
    Returns:
        Protection instance for monitoring
    """
    # Detect framework type and delegate to appropriate setup function
    framework_name = type(framework).__name__.lower()
    
    if 'fastmcp' in framework_name or 'mcp' in framework_name:
        if not _FASTMCP_AVAILABLE:
            raise ImportError("FastMCP integration not available. Install FastMCP.")
        return await setup_fastmcp_protection(framework, **kwargs)
    
    elif 'fastapi' in framework_name or hasattr(framework, 'add_middleware'):
        if not _FASTAPI_AVAILABLE:
            raise ImportError("FastAPI integration not available. Install FastAPI.")
        return setup_fastapi_protection(framework, **kwargs)
    
    else:
        raise ValueError(f"Unsupported framework: {type(framework)}. "
                        "Supported: FastMCP servers, FastAPI applications")

__all__ = [
    # Core components
    "TemporalIsolationEngine",
    "SecretPattern", 
    "SanitizedData",
    "ResolvedData",
    "CryptexConfig",
    "CodenameConfig",  # Legacy alias
    "SecurityPolicy",
    "PerformanceConfig", 
    "ConfigurationLoader",
    "CryptexError",
    "CodenameError",  # Legacy alias
    "SecurityError",
    "ConfigError",
    
    # Main Cryptex decorator
    "cryptex",
    
    # Legacy decorators for backward compatibility
    "protect_tool",
    "protect_file_tool",
    "protect_api_tool", 
    "protect_database_tool",
    "protect_endpoint",
    "protect_auth_endpoint",
    "protect_database_endpoint",
    "protect_external_api_endpoint", 
    "protect_file_endpoint",
    
    # Universal setup
    "setup_protection"
]

# Add framework-specific exports if available
if _FASTMCP_AVAILABLE:
    __all__.extend([
        "setup_fastmcp_protection",
        "FastMCPCryptexMiddleware"
    ])

if _FASTAPI_AVAILABLE:
    __all__.extend([
        "setup_fastapi_protection", 
        "FastAPICryptexMiddleware"
    ])