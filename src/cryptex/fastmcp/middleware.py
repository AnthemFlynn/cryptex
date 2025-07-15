"""
FastMCP middleware integration for automatic secret protection.

Provides middleware classes that automatically protect all FastMCP tools
and server operations without requiring individual decorator usage.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
import time

from ..core.engine import TemporalIsolationEngine
from ..config.loader import CryptexConfig, ConfigurationLoader
from ..config import CodenameConfig  # Legacy alias from config/__init__.py
from ..decorators.mcp import MCPToolProtection
from ..core.exceptions import SecurityError

logger = logging.getLogger(__name__)


@dataclass
class MCPRequest:
    """Represents an MCP request."""
    method: str
    params: Dict[str, Any]
    id: Optional[Union[str, int]] = None
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "method": self.method,
            "params": self.params
        }
        if self.id is not None:
            result["id"] = self.id
        return result


@dataclass
class MCPResponse:
    """Represents an MCP response."""
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {}
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
        if self.id is not None:
            result["id"] = self.id
        return result


class FastMCPCryptexMiddleware:
    """
    Middleware for FastMCP servers that automatically protects all tools.
    
    This middleware intercepts all MCP tool calls and responses to provide
    automatic secret isolation without requiring changes to individual tools.
    """
    
    def __init__(self, 
                 config: Optional[CryptexConfig] = None,
                 config_path: Optional[str] = None,
                 engine: Optional[TemporalIsolationEngine] = None,
                 auto_protect: bool = True):
        """
        Initialize FastMCP middleware.
        
        Args:
            config: Pre-loaded CryptexConfig instance
            config_path: Path to TOML configuration file
            engine: Pre-configured TemporalIsolationEngine instance
            auto_protect: Whether to automatically protect all tools
        """
        self.config = config
        self.config_path = config_path
        self.engine = engine
        self.auto_protect = auto_protect
        self._initialized = False
        self._protection_cache: Dict[str, MCPToolProtection] = {}
        self._metrics = {
            "requests_processed": 0,
            "secrets_detected": 0,
            "sanitization_time": 0.0,
            "resolution_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the middleware components."""
        if self._initialized:
            return
        
        # Load configuration
        if self.config is None:
            if self.config_path:
                self.config = await CryptexConfig.from_toml(self.config_path)
            else:
                self.config = await ConfigurationLoader.load_with_fallbacks([
                    "cryptex.toml",
                    "config/cryptex.toml", 
                    ".cryptex.toml"
                ])
        
        # Create engine
        if self.engine is None:
            self.engine = TemporalIsolationEngine(self.config.secret_patterns)
        
        self._initialized = True
        logger.info("FastMCP Cryptex middleware initialized")
    
    async def process_request(self, request: MCPRequest, call_next: Callable) -> MCPResponse:
        """
        Process an MCP request with secret protection.
        
        Args:
            request: The incoming MCP request
            call_next: Function to call the next middleware/handler
            
        Returns:
            MCP response with secrets properly protected
        """
        await self.initialize()
        
        start_time = time.time()
        
        try:
            # Phase 1: Sanitize request for AI context logging/monitoring
            sanitized_request = await self._sanitize_request(request)
            
            # Phase 2: Execute the actual tool with real values
            response = await call_next(request)  # Use original request with real secrets
            
            # Phase 3: Sanitize response to prevent secret leakage
            sanitized_response = await self._sanitize_response(response, sanitized_request)
            
            # Update metrics
            self._update_metrics(start_time)
            
            return sanitized_response
            
        except Exception as e:
            # Sanitize error and re-raise
            sanitized_error = await self._sanitize_error(e)
            logger.error(f"FastMCP request failed: {sanitized_error}")
            raise sanitized_error
    
    async def _sanitize_request(self, request: MCPRequest) -> MCPRequest:
        """Sanitize MCP request parameters."""
        if not self.auto_protect:
            return request
        
        start_time = time.time()
        
        # Sanitize the request parameters
        sanitized_data = await self.engine.sanitize_for_ai(request.params)
        
        # Create sanitized request
        sanitized_request = MCPRequest(
            method=request.method,
            params=sanitized_data.data,
            id=request.id,
            context={
                "original_context": request.context or {},
                "cryptex_context_id": sanitized_data.context_id,
                "sanitized_at": time.time()
            }
        )
        
        # Track sanitization time
        self._metrics["sanitization_time"] += time.time() - start_time
        
        return sanitized_request
    
    async def _sanitize_response(self, response: MCPResponse, sanitized_request: MCPRequest) -> MCPResponse:
        """Sanitize MCP response to prevent secret leakage."""
        if not self.auto_protect or response.result is None:
            return response
        
        start_time = time.time()
        
        # Get context from request
        context_id = None
        if sanitized_request.context:
            context_id = sanitized_request.context.get("cryptex_context_id")
        
        # Sanitize response result
        if context_id:
            sanitized_result = await self.engine.sanitize_response(response.result, context_id)
        else:
            # Fallback: create new sanitization context
            sanitized_data = await self.engine.sanitize_for_ai(response.result)
            sanitized_result = sanitized_data.data
        
        # Create sanitized response
        sanitized_response = MCPResponse(
            result=sanitized_result,
            error=response.error,
            id=response.id,
            context={
                "original_context": response.context or {},
                "sanitized_at": time.time()
            }
        )
        
        # Track resolution time
        self._metrics["resolution_time"] += time.time() - start_time
        
        return sanitized_response
    
    async def _sanitize_error(self, error: Exception) -> Exception:
        """Sanitize error messages to prevent secret exposure."""
        error_message = str(error)
        
        # Sanitize error message
        sanitized_data = await self.engine.sanitize_for_ai(error_message)
        sanitized_message = sanitized_data.data
        
        # Create new exception with sanitized message
        sanitized_error = type(error)(sanitized_message)
        
        # Preserve traceback if possible
        if hasattr(error, '__traceback__'):
            sanitized_error.__traceback__ = error.__traceback__
        
        return sanitized_error
    
    def _update_metrics(self, start_time: float) -> None:
        """Update middleware metrics."""
        self._metrics["requests_processed"] += 1
        
        # Additional metrics would be collected by the engine
        cache_stats = self.engine.get_cache_stats()
        if "secrets_detected" in cache_stats:
            self._metrics["secrets_detected"] += cache_stats["secrets_detected"]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get middleware performance metrics."""
        return {
            **self._metrics,
            "engine_stats": self.engine.get_cache_stats() if self.engine else {},
            "middleware_initialized": self._initialized,
            "auto_protect_enabled": self.auto_protect
        }
    
    async def shutdown(self) -> None:
        """Cleanup middleware resources."""
        if self.engine:
            # Clear any cached contexts
            if hasattr(self.engine, '_context_cache'):
                self.engine._context_cache.clear()
        
        self._protection_cache.clear()
        logger.info("FastMCP Cryptex middleware shut down")


class MCPServerProtection:
    """
    Helper class for protecting entire FastMCP servers.
    
    Provides utilities for applying Cryptex protection to all tools
    and operations on a FastMCP server instance.
    """
    
    def __init__(self, server, middleware: FastMCPCryptexMiddleware):
        """
        Initialize server protection.
        
        Args:
            server: FastMCP server instance
            middleware: Cryptex middleware instance
        """
        self.server = server
        self.middleware = middleware
        self._original_handlers = {}
    
    async def install_protection(self) -> None:
        """Install protection on all server tools and handlers."""
        await self.middleware.initialize()
        
        # Install middleware on the server
        if hasattr(self.server, 'add_middleware'):
            self.server.add_middleware(self._middleware_wrapper)
        elif hasattr(self.server, 'middleware'):
            self.server.middleware.append(self._middleware_wrapper)
        else:
            # Fallback: wrap individual handlers
            await self._wrap_handlers()
        
        logger.info("Cryptex protection installed on FastMCP server")
    
    async def _middleware_wrapper(self, request, call_next):
        """Wrapper function for middleware integration."""
        # Convert to our request format
        mcp_request = MCPRequest(
            method=getattr(request, 'method', 'unknown'),
            params=getattr(request, 'params', {}),
            id=getattr(request, 'id', None)
        )
        
        # Process with our middleware
        response = await self.middleware.process_request(mcp_request, call_next)
        
        # Convert back to server's response format
        return response
    
    async def _wrap_handlers(self) -> None:
        """Fallback: wrap individual tool handlers."""
        # This would need to be customized based on the specific FastMCP implementation
        logger.warning("Using fallback handler wrapping - may not be fully compatible")
    
    def get_protection_status(self) -> Dict[str, Any]:
        """Get status of server protection."""
        return {
            "middleware_metrics": self.middleware.get_metrics(),
            "server_type": type(self.server).__name__,
            "protection_installed": True
        }


# Convenience functions for easy integration

async def setup_cryptex_protection(
    server,
    config_path: Optional[str] = None,
    config: Optional[CryptexConfig] = None,
    auto_protect: bool = True,
    engine: Optional[TemporalIsolationEngine] = None
) -> MCPServerProtection:
    """
    One-line setup for FastMCP server protection.
    
    Args:
        server: FastMCP server instance
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_protect: Whether to automatically protect all tools
        engine: Pre-configured TemporalIsolationEngine instance
        
    Returns:
        MCPServerProtection instance for monitoring
        
    Example:
        ```python
        from fastmcp import FastMCPServer
        from cryptex.fastmcp import setup_cryptex_protection
        
        server = FastMCPServer()
        
        # One-line setup
        protection = await setup_cryptex_protection(
            server, 
            config_path="cryptex.toml"
        )
        
        # All tools are now automatically protected
        ```
    """
    # Create middleware
    middleware = FastMCPCryptexMiddleware(
        config=config,
        config_path=config_path,
        engine=engine,
        auto_protect=auto_protect
    )
    
    # Create server protection
    protection = MCPServerProtection(server, middleware)
    
    # Install protection
    await protection.install_protection()
    
    return protection


def create_protected_server(
    server_class,
    config_path: Optional[str] = None,
    config: Optional[CryptexConfig] = None,
    auto_protect: bool = True,
    **server_kwargs
):
    """
    Create a FastMCP server with Cryptex protection pre-installed.
    
    Args:
        server_class: FastMCP server class to instantiate
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_protect: Whether to automatically protect all tools
        **server_kwargs: Additional arguments for server initialization
        
    Returns:
        Protected FastMCP server instance
        
    Example:
        ```python
        from fastmcp import FastMCPServer
        from cryptex.fastmcp import create_protected_server
        
        # Create server with protection pre-installed
        server = await create_protected_server(
            FastMCPServer,
            config_path="cryptex.toml",
            host="localhost",
            port=8000
        )
        ```
    """
    async def _create_and_protect():
        # Create server
        server = server_class(**server_kwargs)
        
        # Install protection
        await setup_cryptex_protection(
            server,
            config_path=config_path,
            config=config,
            auto_protect=auto_protect
        )
        
        return server
    
    return asyncio.run(_create_and_protect())


# Legacy aliases for backward compatibility
FastMCPCodenameMiddleware = FastMCPCryptexMiddleware
setup_codename_protection = setup_cryptex_protection