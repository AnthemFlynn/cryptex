"""
FastAPI middleware integration for automatic secret protection.

Provides middleware classes that automatically protect all FastAPI endpoints
and operations without requiring individual decorator usage.
"""

import json
import logging
import time
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from ..config.loader import ConfigurationLoader, CryptexConfig
from ..core.engine import TemporalIsolationEngine

logger = logging.getLogger(__name__)


class CryptexMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic secret protection.

    This middleware intercepts all HTTP requests and responses to provide
    automatic secret isolation for FastAPI applications.
    """

    def __init__(
        self,
        app: ASGIApp,
        config: CryptexConfig | None = None,
        config_path: str | None = None,
        engine: TemporalIsolationEngine | None = None,
        auto_protect: bool = True,
        sanitize_headers: bool = True,
        sanitize_query_params: bool = True,
        sanitize_request_body: bool = True,
        sanitize_response_body: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB default
        max_response_size: int = 10 * 1024 * 1024,  # 10MB default
    ):
        """
        Initialize FastAPI middleware.

        Args:
            app: FastAPI application instance
            config: Pre-loaded CryptexConfig instance
            config_path: Path to TOML configuration file
            engine: Pre-configured TemporalIsolationEngine instance
            auto_protect: Whether to automatically protect all endpoints
            sanitize_headers: Whether to sanitize request/response headers
            sanitize_query_params: Whether to sanitize query parameters
            sanitize_request_body: Whether to sanitize request body
            sanitize_response_body: Whether to sanitize response body
            max_request_size: Maximum request size in bytes (DoS protection)
            max_response_size: Maximum response size in bytes (DoS protection)
        """
        super().__init__(app)
        self.config = config
        self.config_path = config_path
        self.engine = engine
        self.auto_protect = auto_protect
        self.sanitize_headers = sanitize_headers
        self.sanitize_query_params = sanitize_query_params
        self.sanitize_request_body = sanitize_request_body
        self.sanitize_response_body = sanitize_response_body
        self.max_request_size = max_request_size
        self.max_response_size = max_response_size

        self._initialized = False
        self._metrics = {
            "requests_processed": 0,
            "secrets_detected": 0,
            "sanitization_time": 0.0,
            "errors_sanitized": 0,
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
                self.config = await ConfigurationLoader.load_with_fallbacks(
                    ["cryptex.toml", "config/cryptex.toml", ".cryptex.toml"]
                )

        # Create engine
        if self.engine is None:
            self.engine = TemporalIsolationEngine(self.config.secret_patterns)

        self._initialized = True
        logger.info("FastAPI Cryptex middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request/response with secret protection.

        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/handler

        Returns:
            HTTP response with secrets properly protected
        """
        await self.initialize()

        if not self.auto_protect:
            return await call_next(request)

        start_time = time.time()
        context_id = None

        try:
            # Phase 1: Sanitize request for logging/monitoring
            sanitized_request_data, context_id = await self._sanitize_request(request)

            # Phase 2: Execute the actual endpoint with original request
            response = await call_next(
                request
            )  # Use original request with real secrets

            # Phase 3: Sanitize response to prevent secret leakage
            sanitized_response = await self._sanitize_response(response, context_id)

            # Update metrics
            self._update_metrics(start_time)

            return sanitized_response

        except Exception as e:
            # Sanitize error and return error response
            sanitized_error = await self._sanitize_error(e, context_id)
            self._metrics["errors_sanitized"] += 1

            logger.error(f"FastAPI request failed: {sanitized_error}")

            # Return sanitized error response
            return JSONResponse(
                status_code=500,
                content={"error": str(sanitized_error), "type": type(e).__name__},
            )

    async def _sanitize_request(self, request: Request) -> tuple[dict[str, Any], str]:
        """Sanitize HTTP request data for logging/monitoring."""
        request_data = {}

        # Collect request data to sanitize
        if self.sanitize_headers and request.headers:
            request_data["headers"] = dict(request.headers)

        if self.sanitize_query_params and request.query_params:
            request_data["query_params"] = dict(request.query_params)

        if self.sanitize_request_body:
            try:
                # Try to get request body (this might consume the stream)
                body = await request.body()
                if body:
                    # Check request size limit
                    if len(body) > self.max_request_size:
                        raise ValueError(f"Request body size {len(body)} exceeds limit of {self.max_request_size} bytes")

                    try:
                        # Try to parse as JSON
                        request_data["body"] = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, store as string
                        request_data["body"] = body.decode(errors="ignore")
            except Exception:
                # If we can't read body, skip it
                pass

        # Add request metadata
        request_data["method"] = request.method
        request_data["url"] = str(request.url)
        request_data["path"] = request.url.path

        # Sanitize the collected data
        sanitized_data = await self.engine.sanitize_for_ai(request_data)

        return sanitized_data.data, sanitized_data.context_id

    async def _sanitize_response(self, response: Response, context_id: str) -> Response:
        """Sanitize HTTP response to prevent secret leakage."""
        if not self.sanitize_response_body:
            return response

        try:
            # Check if response is JSON
            if (
                hasattr(response, "media_type")
                and response.media_type == "application/json"
            ):
                # Get response body
                if hasattr(response, "body"):
                    body = response.body
                    if body:
                        # Check response size limit
                        if len(body) > self.max_response_size:
                            logger.warning(f"Response body size {len(body)} exceeds limit of {self.max_response_size} bytes")
                            # Return truncated response
                            return Response(
                                content=f"Response truncated - size {len(body)} exceeds limit of {self.max_response_size} bytes",
                                status_code=response.status_code,
                                headers=dict(response.headers),
                                media_type="text/plain",
                            )

                        try:
                            # Parse JSON and sanitize
                            response_data = json.loads(body.decode())
                            sanitized_data = await self.engine.sanitize_response(
                                response_data, context_id
                            )

                            # Create new response with sanitized data
                            return JSONResponse(
                                content=sanitized_data,
                                status_code=response.status_code,
                                headers=dict(response.headers),
                            )
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # If not valid JSON, sanitize as string
                            text_data = body.decode(errors="ignore")
                            sanitized_text = await self.engine.sanitize_response(
                                text_data, context_id
                            )

                            # Return sanitized text response
                            return Response(
                                content=sanitized_text,
                                status_code=response.status_code,
                                headers=dict(response.headers),
                                media_type="text/plain",
                            )

        except Exception as e:
            logger.warning(f"Failed to sanitize response: {e}")

        # Return original response if sanitization fails
        return response

    async def _sanitize_error(
        self, error: Exception, context_id: str | None
    ) -> Exception:
        """Sanitize error messages and traceback to prevent secret exposure."""
        # Use the engine's comprehensive traceback sanitization
        sanitized_error = await self.engine.sanitize_traceback(error)

        return sanitized_error

    def _update_metrics(self, start_time: float) -> None:
        """Update middleware metrics."""
        self._metrics["requests_processed"] += 1

        # Track processing time
        processing_time = time.time() - start_time
        self._metrics["sanitization_time"] += processing_time

    def get_metrics(self) -> dict[str, Any]:
        """Get middleware performance metrics."""
        return {
            **self._metrics,
            "engine_stats": self.engine.get_cache_stats() if self.engine else {},
            "middleware_initialized": self._initialized,
            "auto_protect_enabled": self.auto_protect,
            "sanitization_settings": {
                "sanitize_headers": self.sanitize_headers,
                "sanitize_query_params": self.sanitize_query_params,
                "sanitize_request_body": self.sanitize_request_body,
                "sanitize_response_body": self.sanitize_response_body,
            },
        }


class FastAPIAppProtection:
    """
    Helper class for protecting entire FastAPI applications.

    Provides utilities for applying Cryptex protection to all endpoints
    and operations on a FastAPI application instance.
    """

    def __init__(self, app, middleware: CryptexMiddleware):
        """
        Initialize app protection.

        Args:
            app: FastAPI application instance
            middleware: Cryptex middleware instance
        """
        self.app = app
        self.middleware = middleware

    async def install_protection(self) -> None:
        """Install protection on the FastAPI application."""
        await self.middleware.initialize()

        # Add the middleware to the app
        self.app.add_middleware(
            CryptexMiddleware.__class__, **self._get_middleware_kwargs()
        )

        logger.info("Cryptex protection installed on FastAPI application")

    def _get_middleware_kwargs(self) -> dict[str, Any]:
        """Get middleware initialization kwargs."""
        return {
            "config": self.middleware.config,
            "config_path": self.middleware.config_path,
            "engine": self.middleware.engine,
            "auto_protect": self.middleware.auto_protect,
            "sanitize_headers": self.middleware.sanitize_headers,
            "sanitize_query_params": self.middleware.sanitize_query_params,
            "sanitize_request_body": self.middleware.sanitize_request_body,
            "sanitize_response_body": self.middleware.sanitize_response_body,
        }

    def get_protection_status(self) -> dict[str, Any]:
        """Get status of application protection."""
        return {
            "middleware_metrics": self.middleware.get_metrics(),
            "app_type": type(self.app).__name__,
            "protection_installed": True,
        }


# Convenience functions for easy integration


def setup_cryptex_protection(
    app,
    config_path: str | None = None,
    config: CryptexConfig | None = None,
    auto_protect: bool = True,
    engine: TemporalIsolationEngine | None = None,
    sanitize_headers: bool = True,
    sanitize_query_params: bool = True,
    sanitize_request_body: bool = True,
    sanitize_response_body: bool = True,
) -> FastAPIAppProtection:
    """
    One-line setup for FastAPI application protection.

    Args:
        app: FastAPI application instance
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_protect: Whether to automatically protect all endpoints
        engine: Pre-configured TemporalIsolationEngine instance
        sanitize_headers: Whether to sanitize request/response headers
        sanitize_query_params: Whether to sanitize query parameters
        sanitize_request_body: Whether to sanitize request body
        sanitize_response_body: Whether to sanitize response body

    Returns:
        FastAPIAppProtection instance for monitoring

    Example:
        ```python
        from fastapi import FastAPI
        from cryptex.fastapi import setup_cryptex_protection

        app = FastAPI()

        # One-line setup
        protection = setup_cryptex_protection(
            app,
            config_path="cryptex.toml"
        )

        # All endpoints are now automatically protected
        ```
    """
    # Create middleware
    middleware = CryptexMiddleware(
        app=app,
        config=config,
        config_path=config_path,
        engine=engine,
        auto_protect=auto_protect,
        sanitize_headers=sanitize_headers,
        sanitize_query_params=sanitize_query_params,
        sanitize_request_body=sanitize_request_body,
        sanitize_response_body=sanitize_response_body,
    )

    # Add middleware to app
    app.add_middleware(
        CryptexMiddleware,
        **(
            middleware._get_middleware_kwargs()
            if hasattr(middleware, "_get_middleware_kwargs")
            else {}
        ),
    )

    # Create app protection
    protection = FastAPIAppProtection(app, middleware)

    return protection


def create_protected_app(
    config_path: str | None = None,
    config: CryptexConfig | None = None,
    auto_protect: bool = True,
    **app_kwargs,
):
    """
    Create a FastAPI application with Cryptex protection pre-installed.

    Args:
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_protect: Whether to automatically protect all endpoints
        **app_kwargs: Additional arguments for FastAPI initialization

    Returns:
        Protected FastAPI application instance

    Example:
        ```python
        from cryptex.fastapi import create_protected_app

        # Create app with protection pre-installed
        app = create_protected_app(
            config_path="cryptex.toml",
            title="My Protected API"
        )
        ```
    """
    try:
        from fastapi import FastAPI
    except ImportError:
        raise ImportError(
            "FastAPI is required for create_protected_app. Install with: pip install fastapi"
        ) from None

    # Create FastAPI app
    app = FastAPI(**app_kwargs)

    # Install protection
    setup_cryptex_protection(
        app, config_path=config_path, config=config, auto_protect=auto_protect
    )

    return app


