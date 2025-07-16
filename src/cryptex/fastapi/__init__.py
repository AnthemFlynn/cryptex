"""FastAPI integration for Cryptex middleware."""

from .middleware import (
    CodenameMiddleware,  # Legacy alias
    CryptexMiddleware,
    FastAPIAppProtection,
    create_protected_app,
    setup_codename_protection,  # Legacy alias
    setup_cryptex_protection,
)

__all__ = [
    "CryptexMiddleware",
    "CodenameMiddleware",  # Legacy alias
    "FastAPIAppProtection",
    "setup_cryptex_protection",
    "setup_codename_protection",  # Legacy alias
    "create_protected_app",
]
