"""
FastAPI endpoint protection decorators.

Provides @protect_endpoint decorator for seamless secret isolation in FastAPI endpoints.
"""

import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union
import asyncio

from ..core.engine import TemporalIsolationEngine
from ..config.loader import CryptexConfig, ConfigurationLoader
from ..config import CodenameConfig  # Legacy alias from config/__init__.py
from ..core.exceptions import SecurityError

F = TypeVar("F", bound=Callable[..., Any])


class FastAPIEndpointProtection:
    """Protection handler for FastAPI endpoints."""
    
    def __init__(self, 
                 engine: TemporalIsolationEngine,
                 config: CryptexConfig,
                 secrets: List[str],
                 auto_detect: bool = True):
        """
        Initialize endpoint protection.
        
        Args:
            engine: Temporal isolation engine
            config: Codename configuration
            secrets: List of secret names to protect
            auto_detect: Whether to auto-detect additional secrets
        """
        self.engine = engine
        self.config = config
        self.secrets = secrets
        self.auto_detect = auto_detect
    
    async def protect_endpoint_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute an endpoint call with secret protection.
        
        Args:
            func: The endpoint function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Endpoint result with secrets properly isolated
        """
        try:
            # Phase 1: Sanitize input for logging/monitoring (but keep real values for execution)
            sanitized_args, sanitized_kwargs, context_id = await self._sanitize_arguments(args, kwargs)
            
            # Phase 2: Execute endpoint with real values
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)  # Use original args with real secrets
            else:
                result = func(*args, **kwargs)
            
            # Phase 3: Sanitize response to prevent secret leakage
            sanitized_result = await self.engine.sanitize_response(result, context_id)
            
            return sanitized_result
            
        except Exception as e:
            # Sanitize error messages to prevent secret exposure
            sanitized_error = await self._sanitize_error(e, context_id if 'context_id' in locals() else None)
            raise sanitized_error
    
    async def _sanitize_arguments(self, args: tuple, kwargs: dict) -> tuple[tuple, dict, str]:
        """Sanitize function arguments for logging while preserving originals for execution."""
        # Combine args and kwargs into a single data structure for processing
        all_args = {
            'args': args,
            'kwargs': kwargs
        }
        
        # Sanitize for logging/monitoring purposes
        sanitized_data = await self.engine.sanitize_for_ai(all_args)
        
        return (
            sanitized_data.data['args'],
            sanitized_data.data['kwargs'], 
            sanitized_data.context_id
        )
    
    async def _sanitize_error(self, error: Exception, context_id: Optional[str]) -> Exception:
        """Sanitize error messages to prevent secret leakage."""
        error_message = str(error)
        
        if context_id:
            sanitized_message = await self.engine.sanitize_response(error_message, context_id)
        else:
            # Fallback: create new sanitization context for error
            sanitized_data = await self.engine.sanitize_for_ai(error_message)
            sanitized_message = sanitized_data.data
        
        # Create new exception with sanitized message
        sanitized_error = type(error)(sanitized_message)
        
        # Preserve traceback if possible
        if hasattr(error, '__traceback__'):
            sanitized_error.__traceback__ = error.__traceback__
        
        return sanitized_error


def protect_endpoint(
    secrets: Optional[List[str]] = None,
    config_path: Optional[str] = None,
    config: Optional[CryptexConfig] = None,
    auto_detect: bool = True,
    engine: Optional[TemporalIsolationEngine] = None
) -> Callable[[F], F]:
    """
    Decorator to protect FastAPI endpoints with automatic secret isolation.
    
    This decorator enables seamless secret protection for FastAPI endpoints:
    - Request/response data is sanitized for logging/monitoring
    - Endpoint execution gets real secret values
    - Responses are sanitized before client sees them
    
    Args:
        secrets: List of secret names/patterns to protect
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_detect: Whether to auto-detect secrets beyond specified list
        engine: Pre-configured TemporalIsolationEngine instance
        
    Returns:
        Decorated function with automatic secret protection
        
    Example:
        ```python
        from fastapi import FastAPI, Header
        from cryptex.decorators.fastapi import protect_endpoint
        
        app = FastAPI()
        
        @app.post("/api/process")
        @protect_endpoint(secrets=["api_key", "database_url"])
        async def process_data(
            data: dict,
            api_key: str = Header(...),
            db_url: str = Header(...)
        ):
            # Endpoint has access to real secret values
            # Logs/monitoring see sanitized placeholders
            # Response is sanitized before returning to client
            result = await process_with_secrets(data, api_key, db_url)
            return {"result": result}
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Initialize protection components
            protection = await _get_or_create_endpoint_protection(
                secrets or [],
                config_path,
                config,
                auto_detect,
                engine
            )
            
            # Execute with protection
            return await protection.protect_endpoint_call(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we need to run the async protection in an event loop
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


async def _get_or_create_endpoint_protection(
    secrets: List[str],
    config_path: Optional[str],
    config: Optional[CryptexConfig],
    auto_detect: bool,
    engine: Optional[TemporalIsolationEngine]
) -> FastAPIEndpointProtection:
    """Get or create endpoint protection components."""
    # Load configuration
    if config is None:
        if config_path:
            config = await CryptexConfig.from_toml(config_path)
        else:
            # Try to load from default locations
            config = await ConfigurationLoader.load_with_fallbacks([
                "cryptex.toml",
                "config/cryptex.toml",
                ".cryptex.toml"
            ])
    
    # Create engine if not provided
    if engine is None:
        engine = TemporalIsolationEngine(config.secret_patterns)
    
    return FastAPIEndpointProtection(engine, config, secrets, auto_detect)


class FastAPIEndpointRegistry:
    """Registry for tracking protected FastAPI endpoints."""
    
    def __init__(self):
        self._protected_endpoints: dict[str, FastAPIEndpointProtection] = {}
        self._endpoint_configs: dict[str, dict] = {}
    
    def register_endpoint(self, 
                         endpoint_path: str, 
                         protection: FastAPIEndpointProtection,
                         metadata: Optional[dict] = None) -> None:
        """Register a protected endpoint."""
        self._protected_endpoints[endpoint_path] = protection
        self._endpoint_configs[endpoint_path] = metadata or {}
    
    def get_endpoint_protection(self, endpoint_path: str) -> Optional[FastAPIEndpointProtection]:
        """Get protection for a specific endpoint."""
        return self._protected_endpoints.get(endpoint_path)
    
    def list_protected_endpoints(self) -> List[str]:
        """List all protected endpoint paths."""
        return list(self._protected_endpoints.keys())
    
    def get_protection_stats(self) -> dict:
        """Get statistics about protected endpoints."""
        return {
            "total_protected_endpoints": len(self._protected_endpoints),
            "endpoints": list(self._protected_endpoints.keys()),
            "configurations": self._endpoint_configs
        }


# Global registry instance
_endpoint_registry = FastAPIEndpointRegistry()


def register_protected_endpoint(endpoint_path: str, 
                              protection: FastAPIEndpointProtection,
                              metadata: Optional[dict] = None) -> None:
    """Register a protected endpoint in the global registry."""
    _endpoint_registry.register_endpoint(endpoint_path, protection, metadata)


def get_endpoint_registry() -> FastAPIEndpointRegistry:
    """Get the global endpoint registry."""
    return _endpoint_registry


# Convenience decorators for common FastAPI use cases

def protect_auth_endpoint(config_path: Optional[str] = None) -> Callable[[F], F]:
    """Convenience decorator for authentication endpoints."""
    return protect_endpoint(
        secrets=["api_key", "auth_token", "jwt_secret", "oauth_secret"],
        config_path=config_path,
        auto_detect=True
    )


def protect_database_endpoint(config_path: Optional[str] = None) -> Callable[[F], F]:
    """Convenience decorator for database-accessing endpoints."""
    return protect_endpoint(
        secrets=["database_url", "db_password", "connection_string"],
        config_path=config_path,
        auto_detect=True
    )


def protect_external_api_endpoint(api_secrets: Optional[List[str]] = None,
                                 config_path: Optional[str] = None) -> Callable[[F], F]:
    """Convenience decorator for endpoints that call external APIs."""
    default_secrets = ["api_key", "openai_key", "anthropic_key", "github_token"]
    secrets = (api_secrets or []) + default_secrets
    
    return protect_endpoint(
        secrets=secrets,
        config_path=config_path,
        auto_detect=True
    )


def protect_file_endpoint(config_path: Optional[str] = None) -> Callable[[F], F]:
    """Convenience decorator for file operation endpoints."""
    return protect_endpoint(
        secrets=["file_paths", "upload_path", "storage_url"],
        config_path=config_path,
        auto_detect=True
    )