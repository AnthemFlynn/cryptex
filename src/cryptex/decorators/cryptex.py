"""
Main Cryptex decorator - universal protection for FastMCP tools and FastAPI endpoints.

Provides the @cryptex decorator that automatically detects context and applies
appropriate protection for FastMCP tools or FastAPI endpoints.
"""

import inspect
from collections.abc import Callable
from types import FrameType
from typing import Any, TypeVar

from ..config.loader import CryptexConfig
from ..core.engine import TemporalIsolationEngine
from .fastapi import protect_endpoint
from .mcp import protect_tool

F = TypeVar("F", bound=Callable[..., Any])


def cryptex(
    secrets: list[str] | None = None,
    config_path: str | None = None,
    config: CryptexConfig | None = None,
    auto_detect: bool = True,
    engine: TemporalIsolationEngine | None = None,
    framework: str | None = None,
) -> Callable[[F], F]:
    """
    Universal Cryptex decorator for temporal isolation protection.

    This is the main decorator that automatically detects whether it's being used
    on a FastMCP tool or FastAPI endpoint and applies appropriate protection.

    Args:
        secrets: List of secret names/patterns to protect
        config_path: Path to TOML configuration file
        config: Pre-loaded CryptexConfig instance
        auto_detect: Whether to auto-detect secrets beyond specified list
        engine: Pre-configured TemporalIsolationEngine instance
        framework: Explicit framework specification ("fastmcp" or "fastapi").
                  If None, auto-detection will be used.

    Returns:
        Decorated function with automatic secret protection

    Examples:
        ```python
        # FastMCP tool (auto-detected)
        @server.tool()
        @cryptex(secrets=["api_key", "file_paths"])
        async def read_file_tool(file_path: str, api_key: str) -> str:
            # AI sees placeholders, tool gets real values
            return process_file(file_path, api_key)

        # FastMCP tool (explicit)
        @server.tool()
        @cryptex(secrets=["api_key"], framework="fastmcp")
        async def explicit_mcp_tool(api_key: str) -> str:
            return call_api(api_key)

        # FastAPI endpoint (auto-detected)
        @app.post("/api/process")
        @cryptex(secrets=["api_key"])
        async def process_data(data: dict, api_key: str):
            # Request/response sanitized, endpoint gets real values
            return await external_api_call(data, api_key)

        # FastAPI endpoint (explicit - recommended for reliability)
        @app.get("/secure")
        @cryptex(secrets=["database_url"], framework="fastapi")
        async def secure_endpoint(database_url: str):
            return query_database(database_url)
        ```
    """

    def decorator(func: F) -> F:
        # Use explicit framework if provided, otherwise auto-detect
        if framework:
            context = framework.lower()
            if context not in ["fastmcp", "fastapi"]:
                raise ValueError(
                    f"Unsupported framework '{framework}'. Supported: 'fastmcp', 'fastapi'"
                )
        else:
            # Auto-detect framework context
            frame = inspect.currentframe()
            try:
                context = _detect_framework_context(frame, func)
            except Exception as e:
                # If detection fails, log warning and default to fastmcp
                import logging

                logging.getLogger(__name__).warning(
                    f"Framework auto-detection failed: {e}. Defaulting to FastMCP. "
                    "Consider specifying framework explicitly: @cryptex(framework='fastmcp')"
                )
                context = "fastmcp"

        if context == "fastmcp":
            # Apply FastMCP tool protection
            return protect_tool(
                secrets=secrets,
                config_path=config_path,
                config=config,
                auto_detect=auto_detect,
                engine=engine,
            )(func)

        elif context == "fastapi":
            # Apply FastAPI endpoint protection
            return protect_endpoint(
                secrets=secrets,
                config_path=config_path,
                config=config,
                auto_detect=auto_detect,
                engine=engine,
            )(func)

        else:
            # Default to FastMCP tool protection for unknown contexts
            return protect_tool(
                secrets=secrets,
                config_path=config_path,
                config=config,
                auto_detect=auto_detect,
                engine=engine,
            )(func)

    return decorator


def _detect_framework_context(frame: FrameType | None, func: Callable) -> str:
    """
    Detect the framework context by analyzing the call stack and function metadata.

    Args:
        frame: Current frame from inspect.currentframe()
        func: The function being decorated

    Returns:
        Framework context: "fastmcp", "fastapi", or "unknown"

    Raises:
        RuntimeError: If framework detection encounters an error
    """
    try:
        # First check: Analyze import context - safer than stack inspection
        calling_module = _get_calling_module()
        if calling_module:
            if "fastapi" in calling_module.lower():
                return "fastapi"
            elif "mcp" in calling_module.lower():
                return "fastmcp"

        # Second check: Function annotations and metadata for FastAPI patterns
        if hasattr(func, "__annotations__"):
            annotations = func.__annotations__

            # Look for FastAPI-specific patterns in annotations
            for _param_name, annotation in annotations.items():
                annotation_str = str(annotation)
                if any(
                    fastapi_indicator in annotation_str.lower()
                    for fastapi_indicator in [
                        "header",
                        "query",
                        "path",
                        "body",
                        "depends",
                        "fastapi",
                    ]
                ):
                    return "fastapi"

        # Third check: Function metadata
        if hasattr(func, "__dict__"):
            func_dict = func.__dict__
            if any(
                key.startswith("_fastapi") or "route" in key.lower()
                for key in func_dict.keys()
            ):
                return "fastapi"

        # Fourth check: Limited stack analysis (safer approach)
        if frame:
            context = _analyze_call_stack_safely(frame, max_depth=5)
            if context != "unknown":
                return context

        # If we can't detect the context, return unknown
        return "unknown"

    except Exception as e:
        raise RuntimeError(f"Framework detection failed: {e}") from e


def _get_calling_module() -> str | None:
    """Get the module name of the calling code (safer than stack inspection)."""
    try:
        # Get the stack frame 3 levels up (cryptex -> decorator -> user code)
        frame = inspect.currentframe()
        for _ in range(3):
            if frame:
                frame = frame.f_back

        if frame and frame.f_globals:
            return frame.f_globals.get("__name__", "")
    except Exception:
        pass
    return None


def _analyze_call_stack_safely(frame: FrameType, max_depth: int = 5) -> str:
    """
    Safely analyze call stack for framework indicators.

    Uses limited depth and proper error handling to avoid issues.
    """
    current_frame = frame
    stack_depth = 0

    while current_frame and stack_depth < max_depth:
        try:
            frame_locals = current_frame.f_locals
            frame_globals = current_frame.f_globals

            # Check for FastMCP indicators in locals
            for var_name, var_value in frame_locals.items():
                if var_value is not None:
                    try:
                        class_name = type(var_value).__name__.lower()
                        if any(
                            mcp_indicator in var_name.lower()
                            for mcp_indicator in ["mcp", "server", "tool"]
                        ) and ("mcp" in class_name or "server" in class_name):
                            return "fastmcp"

                        # Check for FastAPI indicators
                        if any(
                            fastapi_indicator in var_name.lower()
                            for fastapi_indicator in ["app", "fastapi", "router"]
                        ) and ("fastapi" in class_name or "router" in class_name):
                            return "fastapi"
                    except (AttributeError, TypeError):
                        continue

            # Check module names in globals
            module_name = frame_globals.get("__name__", "")
            if "fastapi" in module_name.lower():
                return "fastapi"
            elif "mcp" in module_name.lower():
                return "fastmcp"

            current_frame = current_frame.f_back
            stack_depth += 1

        except (AttributeError, KeyError, TypeError):
            # Move to next frame on any error
            if current_frame:
                current_frame = current_frame.f_back
            stack_depth += 1

    return "unknown"


# Alias decorators for specific use cases
def cryptex_tool(
    secrets: list[str] | None = None, config_path: str | None = None, **kwargs
) -> Callable[[F], F]:
    """
    Explicit Cryptex decorator for FastMCP tools.

    This is equivalent to @cryptex but specifically for FastMCP tools,
    bypassing context detection.
    """
    return protect_tool(secrets=secrets, config_path=config_path, **kwargs)


def cryptex_endpoint(
    secrets: list[str] | None = None, config_path: str | None = None, **kwargs
) -> Callable[[F], F]:
    """
    Explicit Cryptex decorator for FastAPI endpoints.

    This is equivalent to @cryptex but specifically for FastAPI endpoints,
    bypassing context detection.
    """
    return protect_endpoint(secrets=secrets, config_path=config_path, **kwargs)


# Convenience decorators with common secret patterns
def cryptex_file(config_path: str | None = None) -> Callable[[F], F]:
    """Cryptex decorator for file operations."""
    return cryptex(
        secrets=["file_paths", "home_directory", "project_dir"],
        config_path=config_path,
        auto_detect=True,
    )


def cryptex_api(config_path: str | None = None) -> Callable[[F], F]:
    """Cryptex decorator for API operations."""
    return cryptex(
        secrets=["api_key", "openai_key", "anthropic_key", "github_token"],
        config_path=config_path,
        auto_detect=True,
    )


def cryptex_database(config_path: str | None = None) -> Callable[[F], F]:
    """Cryptex decorator for database operations."""
    return cryptex(
        secrets=["database_url", "db_password", "connection_string"],
        config_path=config_path,
        auto_detect=True,
    )


def cryptex_auth(config_path: str | None = None) -> Callable[[F], F]:
    """Cryptex decorator for authentication operations."""
    return cryptex(
        secrets=["api_key", "auth_token", "jwt_secret", "oauth_secret"],
        config_path=config_path,
        auto_detect=True,
    )
